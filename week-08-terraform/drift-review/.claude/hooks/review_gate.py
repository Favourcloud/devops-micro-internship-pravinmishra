#!/usr/bin/env python3.13
"""Exact-string review allowlist. This hook is not a shell parser or sandbox."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / ".review-data/current-report.txt"
COMMANDS = {
    'bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/clean.json --report .review-data/current-report.txt',
    'bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/detected.json --report .review-data/current-report.txt',
    'bash -n "AI Assignment/tf-drift-check.sh"',
    'cat reports/drift-detected-report.txt',
    'cat reports/resolved-report.txt',
    'cat .review-data/current-report.txt',
    'ls -l reports',
}
READ_FILES = {
    "README.md", "CLAUDE.md", "drift-review-summary.md",
    "AI Assignment/tf-drift-check.sh", ".claude/settings.json",
    ".claude/skills/tf-drift-review/SKILL.md", ".claude/hooks/review_gate.py",
    "reports/drift-detected-report.txt", "reports/resolved-report.txt",
    "reports/local-validation.json", ".review-data/current-report.txt",
    "fixtures/clean.json", "fixtures/detected.json", "fixtures/empty.json",
    "lib/evidence.py", "lib/schema.jq", "lib/ingress.jq",
}


def report_state():
    try:
        if REPORT.is_symlink() or not REPORT.is_file() or REPORT.stat().st_size > 10000:
            return "missing or invalid"
        text = REPORT.read_text()
        states = re.findall(r"^Overall Status: (HEALTHY|WARN|FAIL|ERROR)$", text, re.M)
        stamps = re.findall(r"^Timestamp UTC: (.+)$", text, re.M)
        if len(states) != 1 or len(stamps) != 1:
            return "malformed"
        timestamp = datetime.fromisoformat(stamps[0])
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        if age < 0 or age > 900:
            return "stale or future-dated"
        if states[0] == "FAIL":
            return "FAIL"
        if "Mode: FIXTURE\n" in text or "SYNTHETIC FIXTURE" in text:
            return "fixture (never authorization)"
        return "untrusted report (never authorization)"
    except (OSError, ValueError, TypeError):
        return "missing or malformed"


def deny(reason):
    print("DENY: " + reason, file=sys.stderr)
    return 2


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate input key")
        result[key] = value
    return result


def main():
    try:
        raw = sys.stdin.read(65537)
        if len(raw) > 65536:
            return deny("oversized hook input")
        event = json.loads(raw, object_pairs_hook=unique_object)
        if not isinstance(event, dict) or event.get("hook_event_name") != "PreToolUse":
            return deny("invalid hook event")
        cwd = event.get("cwd")
        if not isinstance(cwd, str) or Path(cwd).resolve() != ROOT or Path.cwd().resolve() != ROOT:
            return deny("review must run in the isolated project directory")
        tool, payload = event.get("tool_name"), event.get("tool_input")
        if not isinstance(payload, dict):
            return deny("invalid tool payload")
        if tool == "Bash":
            command = payload.get("command")
            if not isinstance(command, str):
                return deny("missing command")
            # No tokenization, normalization, variable expansion or execution.
            # Whitespace changes, chains, wrappers and substitutions all miss.
            if (command not in COMMANDS or payload.get("run_in_background", False) is not False
                    or set(payload) - {"command", "description", "timeout", "run_in_background"}):
                return deny("read-only exact allowlist; apply/destroy/auto-approve are always forbidden; report=" + report_state())
            if any(key in os.environ for key in ("BASH_ENV", "ENV")):
                return deny("shell startup override present")
            return 0
        if tool in ("Read", "Grep"):
            value = payload.get("file_path" if tool == "Read" else "path")
            if not isinstance(value, str):
                return deny("explicit inspection path required")
            path = Path(value)
            if not path.is_absolute():
                path = ROOT / path
            relative = path.resolve().relative_to(ROOT).as_posix()
            if relative in READ_FILES or (tool == "Grep" and relative in {"fixtures", "lib"}):
                return 0
        return deny("noWrite boundary: only allowlisted Bash, Read and Grep inspection")
    except (OSError, ValueError, TypeError, RecursionError):
        return deny("malformed input; no authorization")


if __name__ == "__main__":
    sys.exit(main())
