"""Read-only review of this lab's saved Terraform JSON plans; never apply or destroy."""
import argparse
import base64
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import sys


AZURE_TYPES = {
    "azurerm_resource_group", "azurerm_virtual_network", "azurerm_subnet",
    "azurerm_public_ip", "azurerm_network_security_group", "azurerm_network_interface",
    "azurerm_network_interface_security_group_association", "azurerm_linux_virtual_machine",
}
ADDRESSES = {kind + ".agent" for kind in AZURE_TYPES} | {"terraform_data.authorization"}
ROOT = Path(__file__).resolve().parent


def validate(plan, inputs, *, destroy=False, now=None):
    """Return fixed error codes; inputs must be this invocation's private approved inputs."""
    errors = []
    now = now or datetime.now(timezone.utc)
    prefix = inputs.get("project_name", "")
    if not re.fullmatch(r"dmi-w10-a1-[a-z0-9-]{4,20}", prefix):
        return ["project_prefix"]
    if not destroy:
        try:
            end = datetime.fromisoformat(inputs["expires_at"].replace("Z", "+00:00"))
            if not 0 < (end - now).total_seconds() <= 86400:
                errors.append("lifetime")
        except (KeyError, ValueError, TypeError):
            errors.append("lifetime")
        if inputs.get("live_execution_approved") is not True:
            errors.append("approval")
    seen = set()
    for resource in plan.get("resource_changes", []):
        address = resource.get("address")
        change = resource.get("change", {})
        actions = change.get("actions")
        if resource.get("mode") == "data":
            if address != "data.azurerm_client_config.current" or actions not in (["read"], ["no-op"], ["delete"] if destroy else []):
                errors.append("unexpected_data")
            continue
        if address not in ADDRESSES or address in seen:
            errors.append("unexpected_resource")
            continue
        seen.add(address)
        if actions != (["delete"] if destroy else ["create"]) or change.get("importing") or resource.get("previous_address") or resource.get("deposed"):
            errors.append("unexpected_action")
        values = change.get("before" if destroy else "after") or {}
        kind = resource.get("type")
        if kind != address.split(".")[0]:
            errors.append("resource_type")
        if destroy and kind in AZURE_TYPES:
            scope = "/subscriptions/" + inputs.get("subscription_id", "") + "/resourceGroups/" + prefix + "-rg"
            resource_id = values.get("id", "").lower()
            if not inputs.get("subscription_id") or not (resource_id == scope.lower() or resource_id.startswith(scope.lower() + "/")):
                errors.append("subscription_ownership")
        if kind in AZURE_TYPES - {"azurerm_network_interface_security_group_association"}:
            if not values.get("name", "").startswith(prefix + "-"):
                errors.append("resource_ownership")
            if kind != "azurerm_resource_group" and values.get("resource_group_name") != prefix + "-rg":
                errors.append("resource_group")
        if destroy:
            if kind == "azurerm_network_interface_security_group_association":
                for key in ("network_interface_id", "network_security_group_id"):
                    if not values.get(key, "").lower().startswith(scope.lower() + "/"):
                        errors.append("association_ownership")
            continue
        if values.get("location", "uksouth") != "uksouth":
            errors.append("location")
        if kind == "azurerm_linux_virtual_machine":
            if values.get("size") != "Standard_D2lds_v6" or values.get("admin_username") != "labadmin" or values.get("disable_password_authentication") is not True or values.get("admin_password") or values.get("identity"):
                errors.append("vm_identity_or_size")
            if values.get("disk_controller_type") != "NVMe" or values.get("secure_boot_enabled") is not True or values.get("vtpm_enabled") is not True:
                errors.append("vm_disk_security")
            diagnostics = values.get("boot_diagnostics", [])
            if len(diagnostics) != 1 or diagnostics[0].get("storage_account_uri") not in (None, ""):
                errors.append("managed_boot_diagnostics")
            if values.get("admin_ssh_key") != [{"username": "labadmin", "public_key": inputs.get("ssh_public_key", "").strip()}]:
                errors.append("ssh_key")
            if values.get("custom_data") != base64.b64encode((ROOT / "cloud-init.yaml").read_bytes()).decode():
                errors.append("bootstrap")
            disks = values.get("os_disk", [])
            if len(disks) != 1 or disks[0].get("disk_size_gb") != 32 or disks[0].get("storage_account_type") != "Standard_LRS":
                errors.append("disk")
            image = values.get("source_image_reference", [])
            if image != [{"publisher": "Canonical", "offer": "0001-com-ubuntu-server-jammy", "sku": "22_04-lts-gen2", "version": inputs.get("image_version")}]:
                errors.append("image")
        if kind == "azurerm_network_security_group":
            rules = {rule.get("name"): rule for rule in values.get("security_rule", [])}
            if set(rules) != {"SSHFromControllerOnly", "DenyOtherInbound"}:
                errors.append("inbound_rules")
                continue
            ssh, deny = rules["SSHFromControllerOnly"], rules["DenyOtherInbound"]
            try:
                network = ipaddress.ip_network(inputs["controller_ipv4_cidr"])
                valid_ip = network.version == 4 and network.prefixlen == 32 and network.network_address.is_global
            except (KeyError, ValueError):
                valid_ip = False
            if not valid_ip or any(ssh.get(k) != v for k, v in {"priority": 100, "direction": "Inbound", "access": "Allow", "protocol": "Tcp", "destination_port_range": "22", "source_address_prefix": inputs.get("controller_ipv4_cidr")}.items()):
                errors.append("ssh_boundary")
            if any(deny.get(k) != v for k, v in {"priority": 200, "direction": "Inbound", "access": "Deny", "protocol": "*", "source_address_prefix": "*", "destination_port_range": "*"}.items()):
                errors.append("deny_boundary")
    if not seen or (seen != ADDRESSES if not destroy else not seen <= ADDRESSES):
        errors.append("resource_set")
    if plan.get("errored") or (not destroy and plan.get("applyable") is False):
        errors.append("invalid_plan")
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--destroy", action="store_true")
    args = parser.parse_args()
    try:
        errors = validate(json.load(sys.stdin), json.loads(args.inputs.read_text()), destroy=args.destroy)
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        print(json.dumps({"valid": False, "errors": ["malformed_input"]}))
        return 2
    print(json.dumps({"valid": not errors, "mode": "destroy" if args.destroy else "create", "errors": errors}))
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
