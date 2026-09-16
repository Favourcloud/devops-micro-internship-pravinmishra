#!/usr/bin/env python3
"""Check an A6 saved plan's resource boundary; never call Terraform or AWS."""

import argparse
import json
from pathlib import Path
import re
import sys

AWS_PROVIDER = "registry.terraform.io/hashicorp/aws"
GATE = "terraform_data.deployment_gate"
VPC = "vpc-0f7b4a0baa38141ca"
WEB = "i-09a4ad0db643b5f0a"
CONSTRAINTS = {
    "aws_lb.public": {
        "name": "dmi-a6-public-alb", "internal": False,
        "load_balancer_type": "application", "ip_address_type": "ipv4",
        "security_groups": ["sg-04ec165a8f60d0229"],
        "subnets": ["subnet-085c9fb75f5d16407", "subnet-094b1c5c548c54e68"],
    },
    "aws_lb_target_group.web": {
        "name": "dmi-a6-web", "vpc_id": VPC, "port": 80,
        "protocol": "HTTP", "target_type": "instance",
    },
    "aws_lb_target_group_attachment.web": {"target_id": WEB, "port": 80},
    "aws_lb_listener.http": {"port": 80, "protocol": "HTTP"},
    "aws_db_instance.replica": {
        "identifier": "dmi-a6-read-replica", "publicly_accessible": False,
        "storage_encrypted": True, "multi_az": False,
        "instance_class": "db.t4g.micro", "storage_type": "gp2",
        "vpc_security_group_ids": ["sg-07c71b323797c692f"],
    },
    GATE: {},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_changes(changes, mode, account_id):
    require(mode in ("create", "cleanup"), "Unknown review mode.")
    require(isinstance(account_id, str) and re.fullmatch(r"[0-9]{12}", account_id),
            "A valid expected account ID must be present in the plan variables.")
    require(isinstance(changes, list), "Missing resource_changes list.")
    seen = set()
    actions_count = 0
    elb_prefix = f"arn:aws:elasticloadbalancing:eu-north-1:{account_id}:"
    db_prefix = f"arn:aws:rds:eu-north-1:{account_id}:db:"

    def arn_prefix(values, field, suffix):
        value = values.get(field)
        require(isinstance(value, str) and value.startswith(elb_prefix + suffix),
                "Cleanup ARN is outside the new capstone resources.")

    for resource in changes:
        require(isinstance(resource, dict), "Malformed resource change.")
        change = resource.get("change")
        require(isinstance(change, dict), "Missing resource change details.")
        actions = change.get("actions")
        if resource.get("mode") == "data":
            require(actions in (["read"], ["no-op"]), "Data sources must be read-only.")
            continue
        address = resource.get("address")
        require(resource.get("mode") == "managed" and address in CONSTRAINTS,
                "Unexpected managed resource; shared resources must never enter this state.")
        require(address not in seen, "Duplicate managed resource address.")
        seen.add(address)
        provider = "terraform.io/builtin/terraform" if address == GATE else AWS_PROVIDER
        require(resource.get("provider_name") == provider, "Unexpected managed-resource provider.")
        require(not resource.get("previous_address") and not change.get("importing"),
                "Imports and moved resource addresses require separate review.")
        allowed_action = "create" if mode == "create" else "delete"
        require(actions in ([allowed_action], ["no-op"]),
                "Updates, replacements or actions outside the selected mode are forbidden.")
        values = change.get("after" if mode == "create" else "before")
        require(isinstance(values, dict), "Missing or unknown resource values.")
        for field, expected in CONSTRAINTS[address].items():
            actual = values.get(field)
            if isinstance(expected, list):
                matches = isinstance(actual, list) and sorted(actual) == sorted(expected)
            elif isinstance(expected, bool):
                matches = actual is expected
            else:
                matches = actual == expected
            require(matches, f"Resource boundary mismatch at {address}.{field}.")
        if address == GATE:
            gate_input = values.get("input")
            require(isinstance(gate_input, dict) and gate_input.get("account_id") == account_id
                    and gate_input.get("vpc_id") == VPC, "Gate account/VPC mismatch.")
        if address == "aws_db_instance.replica":
            require(values.get("replicate_source_db") == db_prefix + "bookreview-db",
                    "Replica must remain linked to the Book Review primary; do not promote it.")
            if mode == "cleanup":
                require(values.get("arn") == db_prefix + "dmi-a6-read-replica",
                        "Cleanup DB ARN is outside the new replica.")
        if mode == "cleanup":
            if address == "aws_lb.public":
                arn_prefix(values, "arn", "loadbalancer/app/dmi-a6-public-alb/")
            elif address == "aws_lb_listener.http":
                arn_prefix(values, "arn", "listener/app/dmi-a6-public-alb/")
                arn_prefix(values, "load_balancer_arn", "loadbalancer/app/dmi-a6-public-alb/")
            elif address == "aws_lb_target_group.web":
                arn_prefix(values, "arn", "targetgroup/dmi-a6-web/")
            elif address == "aws_lb_target_group_attachment.web":
                arn_prefix(values, "target_group_arn", "targetgroup/dmi-a6-web/")
        actions_count += actions == [allowed_action] and address != GATE
    if mode == "create":
        require(seen == set(CONSTRAINTS), "Creation plan must contain exactly the five AWS additions and local gate.")
    return actions_count


def validate_plan(plan, mode):
    require(isinstance(plan, dict), "Plan must be a JSON object.")
    require(str(plan.get("format_version", "")).startswith("1."), "Unsupported plan JSON format.")
    require(plan.get("complete") is True and plan.get("errored") is False,
            "Refuse an incomplete or errored plan; use Terraform 1.13+.")
    require(not plan.get("deferred_changes"), "Deferred changes require separate review.")
    variables = plan.get("variables", {})
    require(isinstance(variables, dict), "Missing plan variables.")
    if mode == "create":
        for name in ("deployment_approved", "runtime_verified"):
            require(variables.get(name, {}).get("value") is True, "Deployment gates remain unapproved.")
        checks = plan.get("checks", [])
        require(isinstance(checks, list) and checks and all(item.get("status") == "pass" for item in checks),
                "All plan-time checks must pass before creation.")
        require(any(item.get("address", {}).get("to_display") == GATE for item in checks),
                "The deployment gate must be present in the plan checks.")
    return validate_changes(plan.get("resource_changes", []), mode,
                            variables.get("expected_account_id", {}).get("value"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="Private JSON from terraform show -json saved.tfplan")
    parser.add_argument("--mode", required=True, choices=("create", "cleanup"))
    args = parser.parse_args()
    try:
        count = validate_plan(json.loads(args.plan.read_text()), args.mode)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        # Never echo raw plan values: plans can contain account IDs and secrets.
        print("REJECTED: invalid plan or resource boundary. Review locally; do not apply.", file=sys.stderr)
        return 1
    print(f"Boundary check passed: {count} AWS {args.mode} action(s). Human plan review is still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
