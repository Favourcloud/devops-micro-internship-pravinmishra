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


def safe_members(archive, *, strip_root=None, max_total=128 * 1024 * 1024,
                 max_file=8 * 1024 * 1024, max_count=20000):
    total, seen = 0, set()
    for count, member in enumerate(archive, 1):
        raw = member.name
        path = PurePosixPath(raw)
        if (count > max_count or raw.startswith("/") or "\\" in raw
                or any(part in ("", ".", "..") for part in raw.rstrip("/").split("/"))
                or not raw or any(ord(c) < 32 for c in raw)
                or not (member.isfile() or member.isdir())
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
