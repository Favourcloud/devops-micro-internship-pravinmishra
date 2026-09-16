#!/usr/bin/env python3
"""Explicit local inventory rendering and approval-gated, fixed ad-hoc actions."""

import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
GROUPS = {"web": ("web1", "web2"), "app": ("app1",), "db": ("db1",)}
HOSTS = {host for hosts in GROUPS.values() for host in hosts}
SSH_OPTIONS = [
    "-o", "StrictHostKeyChecking=yes", "-o", "ForwardAgent=no", "-o", "BatchMode=yes",
    "-o", f"UserKnownHostsFile={LAB / '.local/known_hosts'}", "-o", "GlobalKnownHostsFile=/dev/null",
]
ACTIONS = {
    "ping": ["all", "-m", "ansible.builtin.ping"],
    "uptime": ["all", "-m", "ansible.builtin.command", "-a", "uptime"],
    "install-nginx": ["web", "-m", "ansible.builtin.apt", "-a", "name=nginx state=present update_cache=yes", "--become"],
    "start-nginx": ["web", "-m", "ansible.builtin.service", "-a", "name=nginx state=started enabled=yes", "--become"],
    "install-htop": ["all", "-m", "ansible.builtin.apt", "-a", "name=htop state=present update_cache=yes", "--become"],
    "nginx-status": ["web", "-m", "ansible.builtin.command", "-a", "systemctl is-active nginx"],
}


def validate_ips(values, expected=HOSTS):
    if not isinstance(values, dict) or set(values) != set(expected):
        raise ValueError("Expected exactly the named lab hosts; use terraform output -json public_ips.")
    for value in values.values():
        if not isinstance(value, str):
            raise ValueError("Every output must be a public IPv4 string.")
        try:
            address = ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError as exc:
            raise ValueError("Invalid public IPv4 output.") from exc
        if not address.is_global or address.is_multicast or address.is_reserved:
            raise ValueError("Refusing non-public, documentation, multicast or reserved IPv4 outputs.")
    if len(set(values.values())) != len(values):
        raise ValueError("Each host must have a distinct public IPv4 address.")
    return values


def inventory_text(values, web_only=False):
    groups = {"web": GROUPS["web"]} if web_only else GROUPS
    expected = {host for hosts in groups.values() for host in hosts}
    validate_ips(values, expected)
    lines = ["# LOCAL ONLY: generated from approved Terraform outputs; never commit."]
    for group, hosts in groups.items():
        lines.append(f"[{group}]")
        lines.extend(f"{host} ansible_host={values[host]}" for host in hosts)
        lines.append("")
    lines.extend([
        "[all:vars]", "ansible_user=azureuser", "ansible_connection=ssh",
        "ansible_python_interpreter=/usr/bin/python3", "lab_inventory_configured=true",
        "ansible_ssh_common_args='-o StrictHostKeyChecking=yes -o ForwardAgent=no'", "",
    ])
    return "\n".join(lines)


def render(source, destination, web_only=False):
    if source.stat().st_size > 16384:
        raise ValueError("Output JSON is unexpectedly large.")
    values = validate_ips(json.loads(source.read_text()))
    if web_only:
        values = {host: values[host] for host in GROUPS["web"]}
    text = inventory_text(values, web_only)
    if destination.name != "inventory.local.ini":
        raise ValueError("Output must be named inventory.local.ini; tracked templates are never overwritten.")
    # Exclusive creation also refuses existing files and symlinks.
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(text)


def read_local_inventory(path):
    if path.name != "inventory.local.ini" or path.is_symlink():
        raise ValueError("Use a generated inventory.local.ini, not a template or symlink.")
    text = path.read_text()
    values = dict(re.findall(r"^(web1|web2|app1|db1) ansible_host=([0-9.]+)$", text, re.MULTILINE))
    validate_ips(values)
    if text != inventory_text(values):
        raise ValueError("Inventory differs from the safe renderer output; regenerate from Terraform outputs.")
    return values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("render")
    inventory.add_argument("--outputs", type=Path, required=True)
    inventory.add_argument("--output", type=Path, required=True)
    inventory.add_argument("--web-only", action="store_true")
    adhoc = commands.add_parser("adhoc")
    adhoc.add_argument("action", choices=["ssh-hostnames", *ACTIONS])
    adhoc.add_argument("--inventory", type=Path, required=True)
    for command in (inventory, adhoc):
        command.add_argument("--approved", action="store_true", help="Acknowledge CURRENT cloud/budget/SSH approval, not a grant of permission")
    args = parser.parse_args(argv)
    if not args.approved:
        parser.error("Blocked: obtain renewed scoped approval before passing --approved.")
    try:
        if args.command == "render":
            render(args.outputs, args.output, args.web_only)
            print("Created private local inventory; this does not verify connectivity.")
        else:
            values = read_local_inventory(args.inventory)
            if args.action == "ssh-hostnames":
                for host in sorted(values):
                    print(f"{host}: SSH hostname verification", flush=True)
                    subprocess.run(["ssh", *SSH_OPTIONS, f"azureuser@{values[host]}", "hostname"], check=True)
            else:
                environment = os.environ.copy()
                environment["ANSIBLE_CONFIG"] = str(LAB / "ansible/ansible.cfg")
                environment["ANSIBLE_HOST_KEY_CHECKING"] = "True"
                subprocess.run(
                    ["ansible", "-i", str(args.inventory.resolve()), *ACTIONS[args.action]],
                    cwd=LAB / "ansible", env=environment, check=True,
                )
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Lab command refused or failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
