#!/usr/bin/env python3
"""Emit a name-only HTML change for the reviewed instructor revision."""
import argparse
import hashlib
from pathlib import Path
import sys


SOURCE_SHA256 = "54331bf7a84f7abd39df42228003dcdd6816f9aea0aa3ce799765c108453875a"
MAX_BYTES = 128 * 1024
MARKER = b"        </header>"
INSERTION = b'            <p class="sub">Learner: <strong>Eze Favour</strong></p>\n'


class InvalidSource(ValueError):
    pass


def personalize(content):
    if not isinstance(content, bytes) or len(content) > MAX_BYTES:
        raise InvalidSource("Expected bounded HTML bytes.")
    if hashlib.sha256(content).hexdigest() != SOURCE_SHA256:
        raise InvalidSource("Source differs from the reviewed instructor revision; review it before proceeding.")
    if content.count(MARKER) != 1:
        raise InvalidSource("Expected exactly one reviewed header boundary.")
    return content.replace(MARKER, INSERTION + MARKER, 1)


def read_source(path):
    if path.is_symlink() or not path.is_file():
        raise InvalidSource("Expected a regular, non-symlink source file.")
    if path.stat().st_size > MAX_BYTES:
        raise InvalidSource("Source exceeds the review size limit.")
    with path.open("rb") as stream:
        return stream.read(MAX_BYTES + 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Unchanged index.html from the pinned public instructor commit")
    args = parser.parse_args(argv)
    try:
        result = personalize(read_source(args.source))
    except (InvalidSource, OSError):
        print("Static personalization rejected; no input contents or paths were logged.", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
