"""Render non-secret policy review documents only. No SDK, subprocess, writes or authentication."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from string import Template

ROOT = Path(__file__).resolve().parent
FIELDS = {"account_id", "lease_id", "oidc_issuer", "approved_at", "expires_at"}


def validate_inputs(value):
    if not isinstance(value, dict) or set(value) != FIELDS or not all(isinstance(v, str) for v in value.values()):
        raise ValueError("Supply only the five non-secret review metadata fields.")
    patterns = {
        "account_id": r"[0-9]{12}", "lease_id": r"[a-f0-9]{12}",
        "oidc_issuer": r"https://login\.microsoftonline\.com/[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}/v2\.0",
        "approved_at": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
        "expires_at": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
    }
    if any(re.fullmatch(pattern, value[key]) is None for key, pattern in patterns.items()):
        raise ValueError("Invalid account, lease, issuer or UTC timestamp.")
    try:
        start, end = (datetime.strptime(value[key], "%Y-%m-%dT%H:%M:%SZ") for key in ("approved_at", "expires_at"))
    except ValueError:
        raise ValueError("Invalid UTC date.") from None
    if not timedelta(0) < end - start <= timedelta(hours=24):
        raise ValueError("Keep one fixed window of at most 24 hours.")
    return dict(value)


def render(value):
    inputs = validate_inputs(value)
    base = "arn:aws:iam::" + inputs["account_id"] + ":"
    lease = inputs["lease_id"]
    inputs.update(user_arn=base + "user/dmi-week10-operator",
                  role_arn=base + "role/dmi-w10-cleanup-" + lease,
                  boundary_arn=base + "policy/dmi-w10-cleanup-boundary-" + lease,
                  issuer_arn=base + "oidc-provider/" + inputs["oidc_issuer"].removeprefix("https://"))
    policies = {}
    for name in ("operator-policy", "runtime-boundary"):
        policy = json.loads(Template((ROOT / "aws" / (name + ".json.tftpl")).read_text()).substitute(inputs))
        if len(json.dumps(policy, separators=(",", ":"))) > 6144:
            raise ValueError("Rendered managed policy exceeds IAM's 6144-character quota.")
        policies[name] = policy
    return {"source_only": True, "live_verified": False, "bootstrap_access_enabled": False,
            "operator_arn": inputs["user_arn"], "cleanup_role_arn": inputs["role_arn"],
            "runtime_permissions_boundary_arn": inputs["boundary_arn"], "policies": policies}


def supports_browser_login(version_output):
    match = re.match(r"aws-cli/(\d+)\.(\d+)\.(\d+)(?:\s|$)", version_output)
    return bool(match and int(match[1]) == 2 and (int(match[2]), int(match[3])) >= (32, 0))


def verify_identity(document, account_id, lease_id):
    if not re.fullmatch(r"[0-9]{12}", account_id) or not re.fullmatch(r"[a-f0-9]{12}", lease_id):
        raise ValueError("Invalid expected identity metadata.")
    expected = f"arn:aws:iam::{account_id}:user/dmi-week10-operator"
    if (not isinstance(document, dict) or set(document) != {"Account", "Arn", "UserId"}
            or document["Account"] != account_id or document["Arn"] != expected
            or not isinstance(document["UserId"], str) or not re.fullmatch(r"AIDA[A-Z0-9]{17}", document["UserId"])):
        raise ValueError("The identity is not the exact approved IAM operator.")
    return {"account_id": account_id, "operator_arn": expected, "identity_matches": True,
            "mfa_verified": False, "bootstrap_permissions_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path, help="JSON containing only account_id, lease_id, oidc_issuer, approved_at and expires_at")
    args = parser.parse_args()
    try:
        if args.metadata.is_symlink() or not args.metadata.is_file() or args.metadata.stat().st_size > 4096:
            raise ValueError("Expected a small regular metadata file, not a symlink.")
        result = render(json.loads(args.metadata.read_text()))
    except (ValueError, OSError):
        parser.exit(2, "Invalid non-secret review metadata; no account operation was performed.\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
