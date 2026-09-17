#!/usr/bin/python3
"""Copilot-authored post-edit validator; never accepts command passthrough."""
import hashlib
import types
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def load_guard():
    # Verify before importing project Python. The manifest itself is a protected,
    # human-controlled trust anchor, not cryptographic protection from the host.
    path = ROOT / "hooks/pre_tool_guard.py"
    manifest_path = ROOT / ".claude/trusted-files.json"
    for target in (path, manifest_path):
        current = ROOT
        for part in target.relative_to(ROOT).parts:
            current /= part
            if current.is_symlink():
                raise ValueError("Symlink trust input")
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate manifest key")
            result[key] = value
        return result
    manifest = json.loads(manifest_path.read_text(), object_pairs_hook=unique)
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != manifest["files"]["hooks/pre_tool_guard.py"]:
        raise ValueError("Untrusted hook")
    guard = types.ModuleType("a5_pre_guard")
    guard.__file__ = str(path)
    exec(compile(source, str(path), "exec"), guard.__dict__)
    return guard


def main():
    try:
        guard = load_guard()
        text = sys.stdin.read(2 * 1024 * 1024 + 1)
        guard.require(len(text) <= 2 * 1024 * 1024, "Oversize event")
        event = guard.strict_json(text)
        guard.decide(event, ROOT, expected_event="PostToolUse")
        if event["tool_name"] not in {"Edit", "Write"}:
            return 0
        guard.trust(ROOT, validation=True)
        env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
        for key in ("A5_TERRAFORM_BIN", "A5_PROVIDER_MIRROR"):
            guard.require(bool(os.environ.get(key)), "Missing human-configured tool inputs")
            env[key] = os.environ[key]
        result = subprocess.run(
            ["/usr/bin/python3", "-I", str(ROOT / "scripts/validate_offline.py")],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, timeout=1500, check=False,
        )
        guard.require(result.returncode == 0, "Protected runner failed")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "Protected offline mock validation passed; no cloud/runtime validation."}}))
        return 0
    except Exception:
        print(json.dumps({"decision": "block", "reason": "Offline validation failed or trust is unsealed. The source edit already occurred; do not claim validation success. Human review is required."}))
        print("POST-TOOL VALIDATION FAILED (not a rollback; diagnostics withheld).", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
