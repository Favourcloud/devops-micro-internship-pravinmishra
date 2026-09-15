#!/usr/bin/env python3.13
"""Private evidence lifecycle; never print plan values, paths, or provider errors."""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import sys
import uuid
from datetime import datetime, timezone


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def reject_constant(_):
    raise ValueError("non-JSON constant")


def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def classify(value, family):
    if not isinstance(value, str) or "/" not in value:
        return "unknown"
    try:
        network = ipaddress.ip_network(value, strict=False)
        if network.version != family:
            return "unknown"
        # Only RFC1918 and IPv6 ULA are treated as restricted, not arbitrary
        # special/reserved ranges that ipaddress may label private.
        private = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16") if family == 4 else ("fc00::/7",)
        return "restricted" if any(network.subnet_of(ipaddress.ip_network(n)) for n in private) else "public"
    except ValueError:
        return "unknown"


def collect_cidrs(value, result):
    if isinstance(value, dict):
        for key, item in value.items():
            family = {"cidr_blocks": 4, "ipv6_cidr_blocks": 6, "cidr_ipv4": 4, "cidr_ipv6": 6}.get(key)
            if family:
                for cidr in item if isinstance(item, list) else [item]:
                    if isinstance(cidr, str):
                        result[f"{family}:{cidr}"] = classify(cidr, family)
            collect_cidrs(item, result)
    elif isinstance(value, list):
        for item in value:
            collect_cidrs(item, result)


def main():
    os.umask(0o077)
    command, *args = sys.argv[1:]
    if command == "init":
        output = Path(args[0]).absolute()
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            raise ValueError("report exists or parent missing")
        workspace = output.parent / (".review-run-" + uuid.uuid4().hex)
        workspace.mkdir(mode=0o700)
        print(workspace)
    elif command == "copy":
        source, destination = map(Path, args)
        if not source.is_file() or source.is_symlink():
            raise ValueError("not a regular source")
        with destination.open("xb") as target, source.open("rb") as origin:
            shutil.copyfileobj(origin, target)
    elif command == "prepare":
        source, workspace = Path(args[0]), Path(args[1])
        if not source.is_file() or source.is_symlink() or source.stat().st_size == 0:
            raise ValueError("missing plan")
        plan = read_json(source)
        cidrs = {}
        collect_cidrs(plan, cidrs)
        (workspace / "policy-input.json").write_text(json.dumps({"plan": plan, "cidrs": cidrs}))
        print(hashlib.sha256(source.read_bytes()).hexdigest())
    elif command == "publish":
        workspace, output = Path(args[0]), Path(args[1])
        mode, status, detail, source_hash, plan_exit, deletes, unsafe, http, unknown, changes, outputs, drift = args[2:]
        fixture = mode == "FIXTURE"
        banner = "SYNTHETIC FIXTURE DEMONSTRATION — NOT DEPLOYED INFRASTRUCTURE EVIDENCE" if fixture else "LIVE READ-ONLY PLAN — LIMITED POLICY REVIEW, NOT MUTATION AUTHORIZATION"
        text = f"""{banner}
Reviewer: Eze Favour
Timestamp UTC: {datetime.now(timezone.utc).isoformat(timespec='seconds')}
Mode: {mode}
Overall Status: {status}
Plan provenance: {'explicit offline synthetic JSON input' if fixture else 'new plan/show in a human-authorized trusted Terraform directory'}
Plan SHA256: {source_hash}
Terraform detailed exit code: {plan_exit}
Destructive resource actions: {deletes}
Unsafe public ingress findings: {unsafe}
Public TCP HTTP/HTTPS exceptions requiring review: {http}
Unknown or unsupported evidence findings: {unknown}
Non-no-op resource changes: {changes}
Non-no-op output changes: {outputs}
Refresh drift entries: {drift}
Result: {detail}
Scope: deletes/replacements and supported AWS security-group ingress only.
HEALTHY means no findings or pending changes in this limited evidence, never global safety.
This report never authorizes apply, destroy, or auto-approve.
Raw values, resource identifiers, credentials, paths, and provider logs are intentionally omitted.
{banner}
"""
        candidate = workspace / "sanitized-report.txt"
        candidate.write_text(text)
        # Atomic publication that cannot replace an earlier report, including
        # a dangling symlink or a concurrent writer's evidence.
        os.link(candidate, output)
        print(text, end="")
    elif command == "cleanup":
        workspace = Path(args[0])
        if not workspace.name.startswith(".review-run-") or workspace.is_symlink():
            raise ValueError("invalid workspace")
        shutil.rmtree(workspace)
    else:
        raise ValueError("unsupported helper command")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, RecursionError):
        print("FAIL: evidence operation failed; no safety approval.", file=sys.stderr)
        sys.exit(1)
