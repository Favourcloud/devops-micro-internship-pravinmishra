"""Read-only structural review of supplied bootstrap teardown artifacts; never authorization."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import stat

AWS = {"aws_iam_openid_connect_provider.cleanup", "aws_iam_role.cleanup", "aws_iam_role_policy.canary"}
AZURE = {
    "azurerm_resource_group.control", "azurerm_user_assigned_identity.cleanup",
    "azurerm_federated_identity_credential.cleanup[0]", "azurerm_storage_account.state",
    "azurerm_role_assignment.operator_state", "azurerm_role_definition.discovery",
    "azurerm_role_assignment.discovery", "azurerm_role_definition.canary",
    "azurerm_role_assignment.canary[0]",
} | {f'{kind}.{name}["{container}"]' for kind, name in (
    ("azurerm_storage_container", "private"), ("azurerm_role_assignment", "state")
) for container in ("canary-azure", "canary-aws", "receipts")}
GUARD = "terraform_data.authorization"
FIELDS = {"schema_version", "execution_authorized", "cloud", "lease_id", "source_commit",
          "approved_at", "expires_at", "saved_plan_sha256", "plan_json_sha256",
          "external_custody", "resources"}


class Rejected(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Rejected(code)


def matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def digest(value):
    return hashlib.sha256(value).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result

    def constant(value):
        raise Rejected("non_json_constant")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def utc(value):
    require(matches(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "utc_timestamp")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def metadata(request):
    require(isinstance(request, dict) and set(request) == FIELDS, "request_fields")
    require(type(request["schema_version"]) is int and request["schema_version"] == 1
            and request["execution_authorized"] is False, "review_only")
    require(request["cloud"] in ("aws", "azure"), "cloud")
    require(matches(r"[a-f0-9]{12}", request["lease_id"]), "lease")
    require(matches(r"[a-f0-9]{40}", request["source_commit"]), "source_commit")
    for key in ("saved_plan_sha256", "plan_json_sha256"):
        require(matches(r"[a-f0-9]{64}", request[key]), "artifact_hash")
    start, end = utc(request["approved_at"]), utc(request["expires_at"])
    require(timedelta(0) < end - start <= timedelta(hours=24), "fixed_window")
    custody = request["external_custody"]
    require(isinstance(custody, dict) and set(custody) == {
        "storage_account_resource_id", "state_blob_version", "state_sha256", "restore_receipt_sha256"
    }, "custody_fields")
    account = custody["storage_account_resource_id"]
    pattern = (r"/subscriptions/[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}"
               r"/resourceGroups/([a-zA-Z0-9_.()-]{1,90})/providers/Microsoft.Storage/storageAccounts/[a-z0-9]{3,24}")
    match = re.fullmatch(pattern, account, re.IGNORECASE) if isinstance(account, str) else None
    require(match is not None, "custody_account")
    prefix = "dmi-w10-cleanup-" + request["lease_id"]
    require(match[1].lower() not in {prefix + "-control-rg", prefix + "-canary-rg"}, "circular_custody")
    require(matches(r"[a-zA-Z0-9._:+%-]{1,128}", custody["state_blob_version"]), "custody_version")
    require(all(matches(r"[a-f0-9]{64}", custody[key]) for key in
                ("state_sha256", "restore_receipt_sha256")), "custody_hash")
    allowed = AWS if request["cloud"] == "aws" else AZURE
    require(isinstance(request["resources"], list) and 0 < len(request["resources"]) <= len(allowed), "inventory")
    inventory = {}
    for item in request["resources"]:
        require(isinstance(item, dict) and set(item) == {"address", "id"}, "inventory_fields")
        address, identity = item["address"], item["id"]
        require(isinstance(address, str) and address in allowed and address not in inventory, "inventory_address")
        require(matches(r"[^\s\x00-\x1f\x7f]{1,2048}", identity), "inventory_id")
        require(identity not in inventory.values(), "duplicate_identity")
        require(identity.lower() != account.lower(), "recovery_store_in_scope")
        inventory[address] = identity
    return inventory, start, end


def root_resources(values):
    require(isinstance(values, dict) and isinstance(values.get("root_module"), dict), "root_values")
    root = values["root_module"]
    require(not root.get("child_modules"), "child_module")
    resources = root.get("resources", [])
    require(isinstance(resources, list), "root_resources")
    return resources


def review(request, plan, saved_plan_hash, plan_json_hash):
    inventory, start, end = metadata(request)
    require(saved_plan_hash == request["saved_plan_sha256"] and plan_json_hash == request["plan_json_sha256"], "artifact_mismatch")
    require(isinstance(plan, dict) and plan.get("format_version") == "1.2"
            and plan.get("terraform_version") == "1.13.5", "plan_version")
    require(plan.get("complete") is True and plan.get("errored") is False
            and plan.get("applyable") is True, "incomplete_plan")
    require(not plan.get("deferred_changes") and not plan.get("resource_drift"), "deferred_or_drifted")
    require(start <= utc(plan.get("timestamp")) < end, "plan_outside_window")
    checks = plan.get("checks", [])
    require(isinstance(checks, list) and all(isinstance(item, dict) and item.get("status") == "pass"
                                          for item in checks), "failed_or_unknown_check")
    data_address = "data.aws_caller_identity.current" if request["cloud"] == "aws" else "data.azurerm_client_config.current"
    expected = set(inventory) | {GUARD}
    prior = plan.get("prior_state")
    require(isinstance(prior, dict), "missing_prior_state")
    seen = set()
    prior_ids = {}
    for item in root_resources(prior.get("values")):
        require(isinstance(item, dict) and isinstance(item.get("address"), str), "prior_resource")
        address = item["address"]
        require(address not in seen, "duplicate_prior_resource")
        seen.add(address)
        if item.get("mode") == "data":
            require(address == data_address, "unexpected_data")
            continue
        require(item.get("mode") == "managed" and address in expected
                and item.get("type") == address.split(".")[0], "unexpected_prior_resource")
        values = item.get("values")
        require(isinstance(values, dict), "prior_values")
        require(matches(r"[^\s\x00-\x1f\x7f]{1,2048}", values.get("id"))
                and values["id"] not in prior_ids.values(), "missing_or_duplicate_prior_identity")
        if address == GUARD:
            require(values.get("input") == request["lease_id"], "guard_lease")
        else:
            require(values.get("id") == inventory[address], "prior_identity")
        prior_ids[address] = values.get("id")
    require(set(prior_ids) == expected, "missing_prior_resource")
    for item in root_resources(plan.get("planned_values")):
        require(isinstance(item, dict) and item.get("mode") == "data"
                and item.get("address") == data_address, "remaining_managed_resource")
    changes = plan.get("resource_changes")
    require(isinstance(changes, list), "missing_changes")
    seen, deleted = set(), set()
    for item in changes:
        require(isinstance(item, dict) and isinstance(item.get("address"), str), "change_resource")
        address = item["address"]
        require(address not in seen, "duplicate_change")
        seen.add(address)
        change = item.get("change")
        require(isinstance(change, dict), "change")
        require(not item.get("previous_address") and not item.get("deposed")
                and not item.get("module_address") and not change.get("importing"), "import_move_or_deposed")
        if item.get("mode") == "data":
            require(address == data_address and change.get("actions") in (["read"], ["no-op"], ["delete"]), "unexpected_data")
            continue
        require(item.get("mode") == "managed" and address in expected
                and item.get("type") == address.split(".")[0], "unexpected_change")
        require(change.get("actions") == ["delete"] and "after" in change
                and change["after"] is None and not change.get("after_unknown"), "not_delete_only")
        before = change.get("before")
        require(isinstance(before, dict) and before.get("id") == prior_ids[address], "change_identity")
        if address == GUARD:
            require(before.get("input") == request["lease_id"], "guard_lease")
        deleted.add(address)
    require(deleted == expected, "missing_deletion")
    return {"source_only": True, "structural_review_passed": True, "execution_authorized": False,
            "live_readiness_verified": False, "cloud_deletions_in_supplied_plan": len(inventory),
            "saved_plan_sha256": saved_plan_hash, "plan_json_sha256": plan_json_hash}


def read_regular(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_size <= limit, "regular_file_required")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        require(len(raw) <= limit, "file_too_large")
        return raw
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--plan-json", required=True, type=Path)
    parser.add_argument("--saved-plan", required=True, type=Path)
    args = parser.parse_args()
    try:
        request = strict_json(read_regular(args.request, 65536))
        metadata(request)
        plan_raw = read_regular(args.plan_json, 8 * 1024 * 1024)
        saved_raw = read_regular(args.saved_plan, 8 * 1024 * 1024)
        result = review(request, strict_json(plan_raw), digest(saved_raw), digest(plan_raw))
    except (ValueError, OSError, TypeError, KeyError, OverflowError, RecursionError):
        parser.exit(2, "Review rejected; no authorization or cloud operation occurred.\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
