#!/usr/bin/env python3
"""Bounded, hash-verified upstream inspection; never execute downloaded code."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import urllib.parse
import urllib.request

COMMIT = "84280063bea7ccd5144dafa2b969ec4e2e69ffbb"
ARCHIVE_SHA256 = "ad542ddaed5442ad5a88956558d31996d771527d8880d13c7f80181be3599932"
LOCK_HASHES = {
    "backend/package-lock.json": "c3b734664f209e88975bd674efa84939848c333f3276f1acea1e764bf8b9187a",
    "frontend/package-lock.json": "34b1b92ef2c0a0130e33b1af302e22d22b69cb328ba2f5d3ecc1bdf6f6fb6836",
}


class VerificationError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise VerificationError("redirect denied")


def https_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or parsed.port not in (None, 443) or "\n" in url or "\r" in url):
        raise VerificationError("artifact URL must be plain HTTPS, without credentials")
    return url


def download(url, limit):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(https_url(url), timeout=30) as response:
        if response.status != 200:
            raise VerificationError("download failed")
        content = response.read(limit + 1)
    if len(content) > limit:
        raise VerificationError("download exceeds limit")
    return content


def digest(content):
    return hashlib.sha256(content).hexdigest()


# Exact four symlinks present in the pinned source archive under
# backend/node_modules/.bin/; excluded from selected files and never followed.
# Permitted only when strip_root matches the pinned commit root exactly.
_PINNED_SOURCE_ROOT = "book-review-app-" + COMMIT
_PERMITTED_SYMLINKS = {
    "backend/node_modules/.bin/bcrypt": "../bcryptjs/bin/bcrypt",
    "backend/node_modules/.bin/mime": "../mime/cli.js",
    "backend/node_modules/.bin/semver": "../semver/bin/semver.js",
    "backend/node_modules/.bin/uuid": "../uuid/dist/bin/uuid",
}


def safe_members(archive, *, strip_root=None, max_total=128 * 1024 * 1024,
                 max_file=8 * 1024 * 1024, max_count=20000):
    total, seen = 0, set()
    for count, member in enumerate(archive, 1):
        raw = member.name
        path = PurePosixPath(raw)
        if (count > max_count or raw.startswith("/") or "\\" in raw
                or any(part in ("", ".", "..") for part in raw.rstrip("/").split("/"))
                or not raw or any(ord(c) < 32 for c in raw)

                or member.size < 0 or member.size > max_file
                or member.issparse()):
            raise VerificationError("unsafe archive entry")
        if strip_root:
            if path.parts[0] != strip_root:
                raise VerificationError("unexpected archive root")
            path = PurePosixPath(*path.parts[1:])
        name = str(path)
        if name in seen:
            raise VerificationError("duplicate archive entry")
        seen.add(name)
        if member.issym():
            if (strip_root == _PINNED_SOURCE_ROOT
                    and name in _PERMITTED_SYMLINKS
                    and member.linkname == _PERMITTED_SYMLINKS[name]
                    and member.size == 0):
                # Ignore only these excluded metadata entries; never follow links.
                continue
            raise VerificationError("unsafe archive entry")
        if not (member.isfile() or member.isdir()):
            raise VerificationError("unsafe archive entry")
        if strip_root and name == "." and not member.isdir():
            raise VerificationError("archive root must be a directory")
        total += member.size
        if total > max_total:
            raise VerificationError("archive exceeds expansion limit")
        yield name, member


def load_lock(path=None):
    lock = json.loads(Path(path or Path(__file__).with_name("source-lock.json")).read_text())
    if (lock["commit"] != COMMIT or lock["archive_sha256"] != ARCHIVE_SHA256
            or lock["archive_size"] != 4264317
            or lock["archive_url"] != f"https://codeload.github.com/pravinmishraaws/book-review-app/tar.gz/{COMMIT}"
            or any(lock["files"].get(p) != h for p, h in LOCK_HASHES.items())):
        raise VerificationError("source lock mismatch")
    return lock



# Reviewed dependency-only release; original upstream extraction pins stay unchanged.
RELEASE_ID = '6eb47664d2aa719597d564b75aea9b9798c0e1de0c2856d61e7ec7889aa97b69'
RELEASE_PACKAGE_HASHES = {
    "backend/package.json": "e952a6ea154112e2bc957b6dc80e2099f9a8d5696ed0b7c7ed00ae898ae70824",
    "backend/package-lock.json": "836a87a8b0b983d8a112b59aa89462d5edf5d4ea68e071ea51a569f61ae21afe",
    "frontend/package.json": "86dff8428e5df634434b08d81511b337edac99f0ee93fdfc7e50c2710dd6c74f",
    "frontend/package-lock.json": "4c3a18e0cbbe003dc4ecc99f96a7afae88c24a5b3c41753fa7ca4543791c1788"
}

def load_deployment_lock():
    original = load_lock()
    return {**original, "release_id": RELEASE_ID, "files": {**original["files"], **RELEASE_PACKAGE_HASHES}}


def verify_source(content, lock):
    if len(content) != lock["archive_size"] or digest(content) != lock["archive_sha256"]:
        raise VerificationError("source archive hash mismatch")
    selected = {}
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        for path, member in safe_members(archive, strip_root=lock["root"]):
            if not member.isfile() or path not in lock["files"]:
                continue
            if any(p.startswith(".env") or p in ("node_modules", ".git") for p in PurePosixPath(path).parts):
                raise VerificationError("forbidden source selection")
            value = archive.extractfile(member).read()
            if digest(value) != lock["files"][path]:
                raise VerificationError("source member hash mismatch")
            selected[path] = value
    if set(selected) != set(lock["files"]):
        raise VerificationError("incomplete source archive")
    for path in LOCK_HASHES:
        if json.loads(selected[path])["lockfileVersion"] != 3:
            raise VerificationError("unsupported lockfile")
    return selected


def write_new_tree(files, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise VerificationError("destination must not exist")
    if any(p.is_symlink() for p in destination.parents):
        raise VerificationError("symlink parent denied")
    destination.mkdir(mode=0o700)
    for name, content in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(content)
        path.chmod(0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="verify an already downloaded archive instead of HTTPS")
    parser.add_argument("--extract-to", type=Path, help="future approved build/runtime directory; must not exist")
    args = parser.parse_args()
    try:
        lock = load_lock()
        if args.archive:
            with args.archive.open("rb") as handle:
                content = handle.read(lock["archive_size"] + 1)
        else:
            content = download(lock["archive_url"], lock["archive_size"])
        files = verify_source(content, lock)
        if args.extract_to:
            write_new_tree(files, args.extract_to)
        print(f"verified pinned upstream: {len(files)} unchanged files; no source executed")
        return 0
    except Exception:
        print("upstream verification failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
