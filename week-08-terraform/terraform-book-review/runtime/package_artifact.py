#!/usr/bin/env python3
"""Future operator build-packaging helper. Does not install, build, or execute application code."""
import argparse
import io
import json
from pathlib import Path
import sys
import tarfile

from artifact import MAX_ARCHIVE, MAX_EXPANDED, permitted, verify_artifact
from common import RuntimeFailure, origin
from upstream import COMMIT, digest, load_lock


def package(source, public_origin, versions, output):
    source = Path(source).resolve(strict=True)
    origin(public_origin, "https")
    output = Path(output)
    if output.exists() or output.is_symlink() or source == output or source in output.resolve().parents:
        raise RuntimeFailure("unsafe_artifact_destination")
    lock, files, total = load_lock(), {}, 0
    # npm's .bin links are flattened ONLY when their targets remain within this reviewed build.
    for path in sorted(source.rglob("*")):
        name = path.relative_to(source).as_posix()
        if not permitted(name, lock) or path.is_dir():
            continue
        resolved = path.resolve(strict=True)
        if source not in resolved.parents or not resolved.is_file():
            raise RuntimeFailure("build_link_escapes_source")
        if resolved.stat().st_size > 256 * 1024 * 1024:
            raise RuntimeFailure("build_file_oversized")
        data = resolved.read_bytes()
        total += len(data)
        if total > MAX_EXPANDED or len(files) >= 99999:
            raise RuntimeFailure("build_oversized")
        files[name] = data
    manifest = {"schema_version": 1, "commit": COMMIT, "platform": "ubuntu-24.04-linux-amd64",
                "public_origin": public_origin, "versions": versions,
                "files": {name: digest(data) for name, data in files.items()}}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, data in {**files, "artifact-manifest.json": json.dumps(manifest, sort_keys=True).encode()}.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), 0o644, 0
            archive.addfile(info, io.BytesIO(data))
    content = buffer.getvalue()
    if len(content) > MAX_ARCHIVE:
        raise RuntimeFailure("build_archive_oversized")
    verify_artifact(content, {"public_origin": public_origin, "runtime_artifact_sha256": digest(content)}, versions=versions)
    with output.open("xb") as handle:
        handle.write(content)
    print("runtime_artifact_sha256=" + digest(content))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--public-origin", required=True)
    parser.add_argument("--versions", required=True, type=Path, help="JSON output of approved Linux runtime prerequisite version inspection")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        package(args.source, args.public_origin, json.loads(args.versions.read_text()), args.output)
        return 0
    except Exception:
        print("runtime_artifact_packaging_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
