#!/usr/bin/env python3
"""Verify the operator-pinned Linux build bundle before writing any application files."""
import io
import json
from pathlib import PurePosixPath
import tarfile
from common import RuntimeFailure, require_release
from upstream import COMMIT, digest, load_deployment_lock as load_lock, safe_members, write_new_tree

MAX_ARCHIVE = 512 * 1024 * 1024
MAX_EXPANDED = 1536 * 1024 * 1024


def permitted(path, lock):
    parts = PurePosixPath(path).parts
    if any(p.startswith(".env") or p in (".git", ".npmrc", ".aws", ".ssh") for p in parts):
        return False
    return path in lock["files"] or path.startswith(("backend/node_modules/", "frontend/node_modules/", "frontend/.next/"))


def verify_artifact(content, config, *, versions=None):
    if len(content) > MAX_ARCHIVE or digest(content) != config["runtime_artifact_sha256"]:
        raise RuntimeFailure("runtime_archive_hash_mismatch")
    lock, files = load_lock(), {}
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        for path, member in safe_members(archive, max_total=MAX_EXPANDED, max_file=256 * 1024 * 1024, max_count=100000):
            if not member.isfile():
                continue
            if path != "artifact-manifest.json" and not permitted(path, lock):
                raise RuntimeFailure("runtime_archive_unexpected_file")
            files[path] = archive.extractfile(member).read()
    manifest = json.loads(files.pop("artifact-manifest.json"))
    if (manifest.get("schema_version") != 2 or manifest.get("release_id") != lock["release_id"] or manifest.get("commit") != COMMIT
            or manifest.get("platform") != "ubuntu-24.04-linux-amd64"
            or manifest.get("public_origin") != config["public_origin"]
            or set(manifest.get("files", {})) != set(files)):
        raise RuntimeFailure("runtime_manifest_mismatch")
    if versions is not None and manifest.get("versions") != versions:
        raise RuntimeFailure("runtime_toolchain_mismatch")
    for path, content in files.items():
        if digest(content) != manifest["files"][path]:
            raise RuntimeFailure("runtime_file_hash_mismatch")
    for path, expected in lock["files"].items():
        if path not in files or digest(files[path]) != expected:
            raise RuntimeFailure("reviewed_release_source_modified")
    for path in ("frontend/.next/BUILD_ID", "frontend/.next/required-server-files.json",
                 "frontend/node_modules/next/dist/bin/next", "backend/node_modules/sequelize/package.json",
                 "backend/node_modules/mysql2/package.json"):
        if not files.get(path):
            raise RuntimeFailure("runtime_bundle_incomplete")
    build_config = json.loads(files["frontend/.next/required-server-files.json"])
    if build_config.get("config", {}).get("output") == "export":
        raise RuntimeFailure("static_export_unsupported")
    return files


def install_artifact(content, config, destination, versions):
    require_release(config)
    files = verify_artifact(content, config, versions=versions)
    write_new_tree(files, destination)
