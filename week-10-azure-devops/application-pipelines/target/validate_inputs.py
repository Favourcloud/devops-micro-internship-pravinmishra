"""Read-only validation of public inputs, not host trust or deployment approval."""

import base64
import binascii
import ipaddress
import json
import struct
import sys


FIELDS = {"assignment", "agent_ipv4", "target_ipv4", "deployment_public_key"}
MAX_BYTES = 4096


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def public_ipv4(value):
    if not isinstance(value, str):
        raise ValueError("IPv4 required")
    address = ipaddress.IPv4Address(value)
    if str(address) != value or not address.is_global or address.is_multicast or address.is_reserved:
        raise ValueError("public unicast IPv4 required")
    return address


def validate(data):
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError("unexpected fields")
    if data["assignment"] not in ("week10-a2", "week10-a3"):
        raise ValueError("assignment required")
    if public_ipv4(data["agent_ipv4"]) == public_ipv4(data["target_ipv4"]):
        raise ValueError("separate target required")
    key = data["deployment_public_key"]
    if not isinstance(key, str) or len(key) != 80 or not key.startswith("ssh-ed25519 "):
        raise ValueError("one Ed25519 public key without options or comments required")
    try:
        blob = base64.b64decode(key[12:], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("invalid public key encoding") from error
    prefix = struct.pack(">I", 11) + b"ssh-ed25519" + struct.pack(">I", 32)
    if len(blob) != 51 or not blob.startswith(prefix) or base64.b64encode(blob).decode("ascii") != key[12:]:
        raise ValueError("invalid public key structure")
    if blob[-32:] == bytes(32):
        raise ValueError("unset public key")


def main():
    try:
        if len(sys.argv) != 1:
            raise ValueError("no command arguments accepted")
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("input too large")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        if isinstance(data, dict) and set(data) == {"week10_target"}:
            data = data["week10_target"]
        validate(data)
    except (ValueError, TypeError, UnicodeError, OSError, RecursionError):
        print("target_inputs_invalid", file=sys.stderr)
        return 1
    print("target_input_shape_valid_not_live_verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
