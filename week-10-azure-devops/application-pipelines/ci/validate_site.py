"""Read-only payload checks; stdout is a checksum manifest, never live evidence."""

import argparse
from datetime import date
import hashlib
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import re
import sys


LEARNER = "Eze Favour"
MANIFEST = "dmi-site.sha256"
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_FILES = 500
REACT_ROOT_FILES = {
    "index.html", "asset-manifest.json", "manifest.json", "favicon.ico",
    "robots.txt", "logo192.png", "logo512.png",
}
ASSET = re.compile(
    r"static/(?:js/[A-Za-z0-9_-][A-Za-z0-9._-]*\.js(?:\.LICENSE\.txt)?"
    r"|css/[A-Za-z0-9_-][A-Za-z0-9._-]*\.css"
    r"|media/[A-Za-z0-9_-][A-Za-z0-9._-]*\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff|woff2|ttf|eot))"
)


class InvalidSite(ValueError):
    pass


class Index(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.has_body = False
        self.ignored = []
        self.text = []
        self.scripts = []
        self.stylesheets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "body":
            self.in_body = self.has_body = True
        if tag in {"script", "style", "template", "noscript"}:
            self.ignored.append(tag)
        if tag == "script":
            self.scripts.append(attrs.get("src", ""))
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.stylesheets.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
        if self.ignored and self.ignored[-1] == tag:
            self.ignored.pop()

    def handle_data(self, data):
        if self.in_body and not self.ignored:
            self.text.append(data)


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise InvalidSite("Set the actual deployment date in YYYY-MM-DD format")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise InvalidSite("Deployment date is not a calendar date") from error


def allowed_path(name, kind):
    path = PurePosixPath(name)
    if path.is_absolute() or str(path) != name or any(part.startswith(".") for part in path.parts):
        return False
    if name in {"index.html", MANIFEST}:
        return True
    return kind == "react" and (name in REACT_ROOT_FILES or ASSET.fullmatch(name) is not None)


def validate_payload(files, kind, deployment_date=None, verify_manifest=False):
    if kind not in {"static", "react"}:
        raise InvalidSite("Unknown site kind")
    if not files or len(files) > MAX_FILES or "index.html" not in files:
        raise InvalidSite("Missing index.html or invalid payload file count")
    if any(not allowed_path(name, kind) for name in files):
        raise InvalidSite("Unexpected payload path: sources, secrets and source maps must not be deployed")
    if any(len(data) > MAX_FILE_BYTES for data in files.values()) or sum(map(len, files.values())) > MAX_TOTAL_BYTES:
        raise InvalidSite("Payload exceeds the reviewed size limit")
    try:
        index_text = files["index.html"].decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidSite("index.html must be UTF-8") from error
    index = Index()
    index.feed(index_text)
    index.close()
    if not index.has_body:
        raise InvalidSite("index.html has no HTML body")
    if kind == "static":
        if any(index.scripts) or index.stylesheets:
            raise InvalidSite("This static template deploys one HTML file with inline dependencies, not external assets")
        if LEARNER not in " ".join(" ".join(index.text).split()):
            raise InvalidSite("Add the learner name to the static HTML body")
    else:
        valid_date(deployment_date)
        if "asset-manifest.json" not in files or not index.scripts:
            raise InvalidSite("Expected a Create React App production build, not raw source")
        for reference in index.scripts + index.stylesheets:
            name = reference[1:] if reference.startswith("/") else reference
            if not name.startswith("static/") or name not in files:
                raise InvalidSite("An index asset is missing or is not a local production asset")
        script_names = [reference.lstrip("/") for reference in index.scripts]
        if any(not name.startswith("static/js/") or not name.endswith(".js") for name in script_names):
            raise InvalidSite("Unexpected script reference")
        text = index_text.encode("utf-8") + b"\n" + b"\n".join(
            data for name, data in files.items() if name.startswith("static/js/") and name.endswith(".js")
        )
        if any(placeholder in text for placeholder in (b"Your Full Name", b"DD/MM/YYYY")):
            raise InvalidSite("Instructor personalization placeholders remain")
        if LEARNER.encode() not in text or deployment_date.encode() not in text:
            raise InvalidSite("The production payload does not contain the learner name and configured date")
    expected = "".join(
        "{}  {}\n".format(hashlib.sha256(files[name]).hexdigest(), name)
        for name in sorted(files) if name != MANIFEST
    )
    if verify_manifest:
        if files.get(MANIFEST) != expected.encode("ascii"):
            raise InvalidSite("Checksum manifest is absent, stale or altered")
    elif MANIFEST in files:
        raise InvalidSite("Refusing to replace an existing checksum manifest")
    return expected


def read_payload(root, kind):
    if kind not in {"static", "react"}:
        raise InvalidSite("Unknown site kind")
    if root.is_symlink() or not root.is_dir():
        raise InvalidSite("Payload root must be a real directory")
    files = {}
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise InvalidSite("Symlinks are not permitted in payloads")
        if path.is_dir():
            if kind != "react" or path.relative_to(root).as_posix() not in {"static", "static/js", "static/css", "static/media"}:
                raise InvalidSite("Unexpected payload directory")
            continue
        if not allowed_path(path.relative_to(root).as_posix(), kind):
            raise InvalidSite("Unexpected payload file; refusing to read it")
        if not path.is_file():
            raise InvalidSite("Only regular payload files are permitted")
        if len(files) >= MAX_FILES or path.stat().st_size > MAX_FILE_BYTES:
            raise InvalidSite("Payload exceeds the reviewed size limit")
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        total += len(data)
        if len(data) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise InvalidSite("Payload exceeds the reviewed size limit")
        files[path.relative_to(root).as_posix()] = data
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("static", "react"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--deployment-date")
    parser.add_argument("--verify-manifest", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_payload(read_payload(args.root, args.kind), args.kind, args.deployment_date, args.verify_manifest)
    except (InvalidSite, OSError):
        print("Payload check failed. Review the allowed files, personalization and manifest; no contents were logged.", file=sys.stderr)
        return 1
    if not args.verify_manifest:
        print(result, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
