#!/usr/bin/env python3
"""Capture exact lab IDs locally; verify absence only after explicit live approval."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


# Address: AWS describe operation, ID option, response field, not-found error, ID prefix.
SPECS = {
    "aws_vpc.lab": ("describe-vpcs", "--vpc-ids", "Vpcs", "InvalidVpcID.NotFound", "vpc"),
    "aws_subnet.public": ("describe-subnets", "--subnet-ids", "Subnets", "InvalidSubnetID.NotFound", "subnet"),
    "aws_subnet.private": ("describe-subnets", "--subnet-ids", "Subnets", "InvalidSubnetID.NotFound", "subnet"),
    "aws_internet_gateway.lab": ("describe-internet-gateways", "--internet-gateway-ids", "InternetGateways", "InvalidInternetGatewayID.NotFound", "igw"),
    "aws_route_table.public": ("describe-route-tables", "--route-table-ids", "RouteTables", "InvalidRouteTableID.NotFound", "rtb"),
    "aws_route_table.private": ("describe-route-tables", "--route-table-ids", "RouteTables", "InvalidRouteTableID.NotFound", "rtb"),
    "aws_route_table_association.public": ("describe-route-tables", "--filters", "RouteTables", None, "rtbassoc"),
    "aws_route_table_association.private": ("describe-route-tables", "--filters", "RouteTables", None, "rtbassoc"),
    "aws_security_group.web": ("describe-security-groups", "--group-ids", "SecurityGroups", "InvalidGroup.NotFound", "sg"),
    "aws_key_pair.lab": ("describe-key-pairs", "--key-pair-ids", "KeyPairs", "InvalidKeyPair.NotFound", "key"),
    "aws_instance.web": ("describe-instances", "--instance-ids", "Reservations", "InvalidInstanceID.NotFound", "i"),
    "root_volume": ("describe-volumes", "--volume-ids", "Volumes", "InvalidVolume.NotFound", "vol"),
    "primary_eni": ("describe-network-interfaces", "--network-interface-ids", "NetworkInterfaces", "InvalidNetworkInterfaceID.NotFound", "eni"),
}


def validate_inventory(inventory):
    if set(inventory) != set(SPECS):
        raise ValueError("Inventory must contain all 11 resource addresses plus root_volume and primary_eni")
    for address, value in inventory.items():
        prefix = SPECS[address][4]
        if not isinstance(value, str) or not re.fullmatch(rf"{prefix}-(?:[0-9a-f]{{8}}|[0-9a-f]{{17}})", value):
            raise ValueError(f"Missing or invalid exact resource ID for {address}")
    return inventory


def capture(state):
    root = state.get("values", {}).get("root_module", {})
    resources = {r["address"]: r["values"] for r in root.get("resources", []) if r.get("mode") == "managed"}
    if root.get("child_modules") or set(resources) != set(SPECS) - {"root_volume", "primary_eni"}:
        raise ValueError("Expected exactly this lab's 11 managed resources; capture after a successful apply")
    inventory = {address: values.get("id") for address, values in resources.items()}
    inventory["aws_key_pair.lab"] = resources["aws_key_pair.lab"].get("key_pair_id")
    instance = resources["aws_instance.web"]
    inventory["primary_eni"] = instance.get("primary_network_interface_id")
    roots = instance.get("root_block_device", [])
    inventory["root_volume"] = roots[0].get("volume_id") if len(roots) == 1 else None
    return validate_inventory(inventory)


def check_one(address, resource_id, region):
    operation, option, field, not_found, _ = SPECS[address]
    value = f"Name=association.route-table-association-id,Values={resource_id}" if option == "--filters" else resource_id
    command = ["aws", "ec2", operation, option, value, "--region", region, "--output", "json", "--no-cli-pager"]
    environment = dict(os.environ, AWS_EC2_METADATA_DISABLED="true", AWS_PAGER="")
    result = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)
    if result.returncode:
        # AccessDenied, expired credentials, timeouts and generic failures are NOT absence.
        error = re.search(r"An error occurred \(([^)]+)\)", result.stderr)
        return bool(not_found and error and error.group(1) == not_found)
    items = json.loads(result.stdout)[field]
    if not isinstance(items, list):
        raise ValueError("Unexpected AWS response shape")
    if address == "aws_instance.web":
        instances = [instance for reservation in items for instance in reservation["Instances"]]
        return bool(instances) and all(
            instance["InstanceId"] == resource_id and instance["State"]["Name"] == "terminated"
            for instance in instances
        )
    return not items


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    snapshot = sub.add_parser("capture", help="Read terraform show -json from stdin; output only Region and exact lab IDs (no AWS calls)")
    snapshot.add_argument("--region", required=True)
    verify = sub.add_parser("verify", help="LIVE read-only AWS checks; approval and original account/Region required")
    verify.add_argument("--inventory", required=True, type=Path)
    verify.add_argument("--region", required=True)
    verify.add_argument("--authorized-live-check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[a-z]{2}-[a-z]+-[1-9][0-9]*", args.region):
            raise ValueError("Explicit commercial AWS Region required")
        if args.mode == "capture":
            json.dump({"region": args.region, "resources": capture(json.load(sys.stdin))}, sys.stdout, indent=2)
            print()
            return 0
        if not args.authorized_live_check:
            parser.error("verify requires fresh approval and --authorized-live-check; offline preparation must not run it")
        saved = json.loads(args.inventory.read_text())
        if saved["region"] != args.region:
            raise ValueError("Verification Region must match the captured deployment Region")
        inventory = validate_inventory(saved["resources"])
        success = True
        for address, resource_id in inventory.items():
            absent = check_one(address, resource_id, args.region)
            print(f"{address}: {'absent/terminated' if absent else 'NOT VERIFIED (present or API failure)'}")
            success = success and absent
        return 0 if success else 1
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Cleanup NOT verified: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
