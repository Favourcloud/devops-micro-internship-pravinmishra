#!/usr/bin/env python3
"""Validate A4's non-sensitive manual handoff; never contact a host or cloud API."""

import ipaddress
import json
import re
import sys

MAX_BYTES = 8192
FIELDS = frozenset({"app_public_ip", "backend_ansible_host", "backend_private_ip", "mysql_fqdn"})
PRIVATE_NETWORKS = tuple(ipaddress.IPv4Network(cidr) for cidr in
                         ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
MYSQL_HOST = re.compile(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]\.mysql\.database\.azure\.com")


class HandoffError(ValueError):
    pass


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise HandoffError("duplicate JSON keys are not allowed")
        result[key] = value
    return result


def _constant(_value):
    raise HandoffError("nonstandard JSON constants are not allowed")


def _ipv4(value):
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        raise HandoffError("expected canonical IPv4 addresses") from None
    if str(address) != value:
        raise HandoffError("expected canonical IPv4 addresses")
    return address


def _private(address):
    return any(address in network for network in PRIVATE_NETWORKS)


def _public(address):
    return (address.is_global and not address.is_multicast and not address.is_reserved
            and not address.is_loopback and not address.is_link_local and not address.is_unspecified)


def validate_handoff(document):
    if type(document) is not dict or set(document) != FIELDS:
        raise HandoffError("exactly the four approved handoff fields are required")
    if any(type(value) is not str or not value or len(value) > 253 for value in document.values()):
        raise HandoffError("handoff values must be nonempty bounded strings, not placeholders or objects")
    public = _ipv4(document["app_public_ip"])
    backend = _ipv4(document["backend_private_ip"])
    transport = _ipv4(document["backend_ansible_host"])
    if not _public(public):
        raise HandoffError("frontend must use a globally routable unicast IPv4 address")
    if not _private(backend):
        raise HandoffError("backend private address must be RFC1918 IPv4")
    if not (_public(transport) or _private(transport)):
        raise HandoffError("backend SSH address must be unicast public or RFC1918 IPv4")
    if transport == public:
        raise HandoffError("frontend and backend SSH targets must be distinct")
    if _private(transport) and transport != backend:
        raise HandoffError("direct private SSH must target the backend private address")
    if MYSQL_HOST.fullmatch(document["mysql_fqdn"]) is None:
        raise HandoffError("expected a canonical Azure MySQL server FQDN, not a URL or connection string")
    return {key: document[key] for key in sorted(FIELDS)}


def parse_handoff(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise HandoffError("handoff input must contain between 1 and 8192 bytes")
    try:
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise HandoffError("handoff input must be a small valid UTF-8 JSON object") from None
    return validate_handoff(document)


def inventory(document):
    values = validate_handoff(document)
    return {"all": {
        "children": {
            "frontend": {"hosts": {"epicbook_frontend": {"ansible_host": values["app_public_ip"]}}},
            "backend": {"hosts": {"epicbook_backend": {"ansible_host": values["backend_ansible_host"]}}},
        },
        "vars": {key: values[key] for key in ("backend_private_ip", "mysql_fqdn")},
    }}


def main(argv=None, source=None, output=None, errors=None):
    argv = sys.argv[1:] if argv is None else argv
    source = sys.stdin.buffer if source is None else source
    output = sys.stdout if output is None else output
    errors = sys.stderr if errors is None else errors
    if argv not in ([], ["--inventory"]):
        print("handoff rejected: expected no arguments or --inventory; read JSON from standard input", file=errors)
        return 2
    try:
        values = parse_handoff(source.read(MAX_BYTES + 1))
        result = inventory(values) if argv else values
    except (HandoffError, OSError) as exc:
        message = str(exc) if isinstance(exc, HandoffError) else "could not read handoff input"
        print("handoff rejected: " + message, file=errors)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True), file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
