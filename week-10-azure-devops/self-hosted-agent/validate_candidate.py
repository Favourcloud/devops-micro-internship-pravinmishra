"""Validate supplied A1 facts locally; never discover, execute, register or install."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT_KEYS = {"schema_version", "organization_url", "pool_name", "agent_name", "host", "package"}
HOST_KEYS = {
    "system", "distribution", "version_id", "machine", "uid", "account",
    "privileged_groups", "sudo_allowed", "free_disk_mib", "git_version", "commands",
}
PACKAGE_KEYS = {
    "version", "architecture", "download_url", "sha256", "metadata_url",
    "compatibility_reviewed",
}
COMMANDS = {"bash", "tar", "sha256sum", "uname", "whoami", "df", "systemctl", "git"}
MAX_CANDIDATE_BYTES = 65536


def matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def exact_keys(value, allowed):
    return isinstance(value, dict) and set(value) == allowed


def validate(candidate):
    """Return fixed error codes only; a pass is not live evidence or authorization."""
    if not exact_keys(candidate, ROOT_KEYS):
        return ["candidate.keys"]
    errors = []
    if type(candidate["schema_version"]) is not int or candidate["schema_version"] != 1:
        errors.append("candidate.schema_version")
    if not matches(r"https://dev\.azure\.com/[A-Za-z0-9][A-Za-z0-9-]{0,49}/?", candidate["organization_url"]):
        errors.append("candidate.organization_url")
    for name in ("pool_name", "agent_name"):
        value = candidate[name]
        if not matches(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value) or value.lower() == "default":
            errors.append("candidate." + name)

    host = candidate["host"]
    package = candidate["package"]
    if not exact_keys(host, HOST_KEYS):
        errors.append("host.keys")
    else:
        if host["system"] != "Linux" or host["distribution"] != "ubuntu":
            errors.append("host.os")
        if host["version_id"] not in ("22.04", "24.04"):
            errors.append("host.version_id")
        if host["machine"] not in ("x86_64", "aarch64", "arm64"):
            errors.append("host.machine")
        if type(host["uid"]) is not int or host["uid"] <= 0:
            errors.append("host.uid")
        if host["account"] != "azdoagent":
            errors.append("host.account")
        if host["privileged_groups"] != [] or host["sudo_allowed"] is not False:
            errors.append("host.privilege")
        if type(host["free_disk_mib"]) is not int or host["free_disk_mib"] < 2048:
            errors.append("host.free_disk_mib")
        git_version = host["git_version"]
        if not matches(r"[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}", git_version):
            errors.append("host.git_version")
        elif tuple(map(int, git_version.split("."))) < (2, 9, 0):
            errors.append("host.git_version")
        commands = host["commands"]
        if (not isinstance(commands, list) or not all(isinstance(c, str) for c in commands)
                or len(commands) != len(COMMANDS) or set(commands) != COMMANDS):
            errors.append("host.commands")

    if not exact_keys(package, PACKAGE_KEYS):
        errors.append("package.keys")
    else:
        version = package["version"]
        architecture = package["architecture"]
        valid_version = (matches(r"[1-9][0-9]{0,2}\.[0-9]{1,4}\.[0-9]{1,4}", version)
                         and int(version.split(".")[0]) >= 4)
        valid_architecture = architecture in ("x64", "arm64")
        if not valid_version:
            errors.append("package.version")
        if not valid_architecture:
            errors.append("package.architecture")
        if valid_version and valid_architecture:
            filename = "vsts-agent-linux-{}-{}.tar.gz".format(architecture, version)
            expected_url = "https://download.agent.dev.azure.com/agent/{}/{}".format(version, filename)
            if package["download_url"] != expected_url:
                errors.append("package.download_url")
            expected_metadata = "https://github.com/microsoft/azure-pipelines-agent/releases/tag/v" + version
            if package["metadata_url"] != expected_metadata:
                errors.append("package.metadata_url")
        if not matches(r"[0-9a-f]{64}", package["sha256"]):
            errors.append("package.sha256")
        if package["compatibility_reviewed"] is not True:
            errors.append("package.compatibility_reviewed")
        if exact_keys(host, HOST_KEYS):
            expected_arch = "x64" if host["machine"] == "x86_64" else "arm64"
            if architecture != expected_arch:
                errors.append("package.host_architecture")
    return errors


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def read_candidate(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular file required")
    with path.open("rb") as stream:
        raw = stream.read(MAX_CANDIDATE_BYTES + 1)
    if len(raw) > MAX_CANDIDATE_BYTES:
        raise ValueError("input too large")
    return json.loads(raw, object_pairs_hook=unique_object)


def archive_matches(stream, expected_sha256):
    """Compare bytes only; do not extract or authenticate publisher metadata."""
    if not matches(r"[0-9a-f]{64}", expected_sha256):
        return False
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest() == expected_sha256


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Invalid arguments; values suppressed. Use --help.\n")


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--archive", type=Path, help="Optional existing archive; read/hash only, never extract")
    args = parser.parse_args(argv)
    try:
        candidate = read_candidate(args.candidate)
        errors = validate(candidate)
        if args.archive is not None and not errors:
            if args.archive.is_symlink() or not args.archive.is_file():
                raise ValueError("regular archive required")
            with args.archive.open("rb") as stream:
                if not archive_matches(stream, candidate["package"]["sha256"]):
                    errors.append("archive.sha256_mismatch")
    except (OSError, ValueError, RecursionError):
        print(json.dumps({"status": "invalid_input", "live_verified": False}))
        return 2
    print(json.dumps({
        "status": "invalid_candidate" if errors else "offline_checks_passed",
        "live_verified": False,
        "archive_checksum_matched": args.archive is not None and not errors,
        "errors": errors,
    }, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
