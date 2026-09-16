#!/usr/bin/env python3
"""Render a private inventory from Terraform outputs, never from state or key contents."""

import argparse
import ipaddress
import json
import os
from pathlib import Path
import re


def safe_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute() or not re.fullmatch(r"/[A-Za-z0-9_./-]+", value):
        raise ValueError("SSH paths must be absolute and contain only letters, digits, _, ., / or -")
    if ".." in path.parts:
        raise ValueError("Parent traversal is not allowed in SSH paths")
    return value


def render(outputs: dict, private_key: str, known_hosts: str) -> str:
    try:
        address = ipaddress.IPv4Address(outputs["public_ip"]["value"])
        user = outputs["admin_user"]["value"]
    except (KeyError, TypeError, ipaddress.AddressValueError) as exc:
        raise ValueError("Expected terraform output -json with public_ip and admin_user values") from exc
    if not address.is_global or address.is_multicast or address.is_reserved:
        raise ValueError("public_ip must be a globally routable unicast IPv4 address, not a fixture")
    if user != "ubuntu":
        raise ValueError("Only the reviewed Ubuntu admin user is permitted")
    key = safe_path(private_key)
    hosts = safe_path(known_hosts)
    return (
        "# Generated locally; do not commit. Verify the host fingerprint independently.\n"
        "[web]\n"
        f"epicbook ansible_host={address} ansible_user=ubuntu ansible_connection=ssh "
        f"ansible_python_interpreter=/usr/bin/python3 ansible_ssh_private_key_file={key} "
        f"ansible_ssh_common_args='-o IdentitiesOnly=yes -o StrictHostKeyChecking=yes "
        f"-o UserKnownHostsFile={hosts}'\n"
    )


def write_new(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--private-key", required=True, help="Path only; contents are never read")
    parser.add_argument("--known-hosts", required=True, help="Separately verified project-local known_hosts path")
    parser.add_argument("--destination", type=Path, default=Path("ansible/inventory.local.ini"))
    args = parser.parse_args()
    try:
        outputs = json.loads(args.outputs.read_text(encoding="utf-8"))
        content = render(outputs, args.private_key, args.known_hosts)
        write_new(args.destination, content)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Inventory refused: {exc}\n")
    print(f"Created {args.destination}; no connections made and no private key read.")


if __name__ == "__main__":
    main()
