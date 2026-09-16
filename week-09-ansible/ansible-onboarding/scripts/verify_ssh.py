#!/usr/bin/env python3
"""Check the user's real SSH readiness without reading private-key contents."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def command(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=15, check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write a sanitized result record")
    args = parser.parse_args()
    ssh_dir = Path.home() / ".ssh"
    private = ssh_dir / "dmi_week09_ed25519"
    public = private.with_suffix(".pub")
    fields = public.read_text().split() if public.is_file() else []
    # ssh-add -L returns PUBLIC keys only; never publish them or their comments.
    identities = command("/usr/bin/ssh-add", "-L")
    loaded = identities.returncode == 0 and len(fields) >= 2 and any(
        row.split()[:2] == fields[:2] for row in identities.stdout.splitlines()
    )
    listing = command("/usr/bin/ssh-add", "-l")
    safe_listing = []
    for row in listing.stdout.splitlines():
        match = re.fullmatch(r"(\d+)\s+\S+\s+.*\(([^)]+)\)", row)
        if match:
            safe_listing.append(
                f"{match[1]} [fingerprint redacted] [comment redacted] ({match[2]})"
            )
    configured = command("/usr/bin/ssh", "-G", "dmi-week09-github")
    config = {}
    wanted = {"hostname", "user", "identityfile", "identitiesonly", "stricthostkeychecking", "forwardagent"}
    for row in configured.stdout.splitlines():
        key, _, value = row.partition(" ")
        if key in wanted:
            config.setdefault(key, []).append(value)
    expected = {
        "hostname": ["github.com"],
        "user": ["git"],
        "identityfile": ["~/.ssh/dmi_week09_ed25519"],
        "identitiesonly": ["yes"],
        "stricthostkeychecking": ["true"],
        "forwardagent": ["no"],
    }
    # OpenSSH may normalize booleans differently between supported versions.
    if config.get("stricthostkeychecking") == ["yes"]:
        config["stricthostkeychecking"] = ["true"]
    checks = {
        "public_key_is_ed25519": len(fields) >= 2 and fields[0] == "ssh-ed25519",
        "private_key_file_exists": private.is_file(),
        "private_key_mode_600": private.is_file() and private.stat().st_mode & 0o777 == 0o600,
        "agent_socket_configured": bool(os.environ.get("SSH_AUTH_SOCK")),
        "fresh_key_loaded_in_current_agent": loaded,
        "user_ssh_config_exists": (ssh_dir / "config").is_file(),
        "effective_alias_matches_safe_settings": configured.returncode == 0 and config == expected,
        "known_hosts_exists": (ssh_dir / "known_hosts").is_file(),
    }
    # Only record explicitly public expected config values after comparison.
    safe_config = expected if checks["effective_alias_matches_safe_settings"] else None
    result = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "learner": "Eze Favour",
        "status": "PASS" if all(checks.values()) else "PENDING",
        "checks": checks,
        "ssh_add_l": {"exit_code": listing.returncode, "sanitized_output": safe_listing},
        "ssh_G_dmi_week09_github": safe_config,
        "private_key_contents_read": False,
        "remote_connection_attempted": False,
        "known_host_fingerprint_verified": False,
        "redaction": "Agent fingerprints and comments removed before display. No private paths or public-key bodies recorded.",
        "verifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
