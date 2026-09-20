"""Disabled-by-default A2 saved-plan executor. No bootstrap, login or direct cloud deletion."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parent
WEEK = ROOT.parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


core = module("canary_process_control", ROOT.parent / "worker.py")
inventory = module("a2_inventory", ROOT / "inventory.py")
require, exact, matches = core.require, core.exact_keys, core.matches
AWS = {
    "aws_vpc.target": "vpc", "aws_subnet.target": "subnet",
    "aws_internet_gateway.target": "igw", "aws_route_table.target": "rtb",
    "aws_route_table_association.target": "rtbassoc", "aws_security_group.target": "sg",
    "aws_key_pair.operator": None, "aws_instance.target": "i",
}
AZURE = {
    "azurerm_resource_group.agent": "",
    "azurerm_virtual_network.agent": "/providers/Microsoft.Network/virtualNetworks/",
    "azurerm_subnet.agent": "/providers/Microsoft.Network/virtualNetworks/",
    "azurerm_public_ip.agent": "/providers/Microsoft.Network/publicIPAddresses/",
    "azurerm_network_security_group.agent": "/providers/Microsoft.Network/networkSecurityGroups/",
    "azurerm_network_interface.agent": "/providers/Microsoft.Network/networkInterfaces/",
    "azurerm_network_interface_security_group_association.agent": "/providers/Microsoft.Network/networkInterfaces/",
    "azurerm_linux_virtual_machine.agent": "/providers/Microsoft.Compute/virtualMachines/",
}
GUARD = {"aws": "module.guard.terraform_data.authorization", "azure_agent": "terraform_data.authorization"}
DATA = {"aws": {"data.aws_caller_identity.current", "data.aws_ami.ubuntu"},
        "azure_agent": {"data.azurerm_client_config.current"}}
GATES = {"independent_host_verified", "external_state_restore_verified", "exclusive_writer_verified",
         "scoped_delete_permissions_verified", "bootstrap_recovery_verified", "notifications_verified"}
FIELDS = {"schema_version", "kind", "armed", "cloud", "source_commit", "terraform_sha256", "approval",
          "original_expires_at", "prefix", "identity", "backend", "resources", "auxiliary", "artifacts", "gates"}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def regular(path, limit=32 * 1024 * 1024, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= limit, "unsafe_file")
        if private:
            require(info.st_uid == os.getuid() and not info.st_mode & 0o077, "private_file_required")
        content = stream.read(limit + 1)
        require(len(content) <= limit, "file_too_large")
        return content


def private_directory(path, ancestor):
    require(path.is_absolute() and path.resolve(strict=True) == path
            and path.is_relative_to(ancestor), "isolated_path_required")
    for current in (path, *path.parents):
        info = current.stat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                and not info.st_mode & 0o077, "private_directory_required")
        if current == ancestor:
            break


def window(request, now=None, reserve=0):
    now = now or datetime.now(timezone.utc)
    start = core.utc(request["approval"]["approved_at"])
    end = core.utc(request["approval"]["execute_before"])
    require(start <= now and reserve < (end - now).total_seconds()
            and 0 < (end - start).total_seconds() <= 86400, "cleanup_authority_expired_or_not_started")


def validate_request(request, now=None):
    exact(request, FIELDS)
    require(type(request["schema_version"]) is int and request["schema_version"] == 1
            and request["kind"] == "a2-workload-saved-plan" and type(request["armed"]) is bool, "request_schema")
    if not request["armed"]:
        return "unarmed"
    cloud = request["cloud"]
    require(cloud in GUARD, "a2_only")
    exact(request["approval"], {"approved_at", "execute_before", "receipt_sha256"})
    window(request, now)
    core.utc(request["original_expires_at"])
    exact(request["gates"], GATES)
    require(all(value is True for value in request["gates"].values()), "acceptance_pending")
    require(matches(r"[a-f0-9]{40}", request["source_commit"]) and request["source_commit"] != "0" * 40,
            "source_commit")
    exact(request["artifacts"], {"inputs_sha256"})
    hashes = [request["terraform_sha256"], request["approval"]["receipt_sha256"], *request["artifacts"].values()]
    identity = request["identity"]
    exact(identity, {"azure_subscription_id", "azure_tenant_id", "azure_client_id", "azure_principal_id",
                     "aws_account_id", "aws_role_arn"})
    require(all(matches(core.UUID, identity[key]) for key in identity if key.startswith("azure_")), "azure_identity")
    if cloud == "aws":
        require(matches(r"[0-9]{12}", identity["aws_account_id"])
                and matches(r"arn:aws:iam::" + identity["aws_account_id"]
                            + r":role/dmi-w10-a2-cleanup-[a-z0-9-]{4,32}", identity["aws_role_arn"]), "aws_role")
    else:
        require(identity["aws_account_id"] is None and identity["aws_role_arn"] is None, "unexpected_aws_identity")
    require(matches(r"dmi-w10-a2-[a-z0-9][a-z0-9-]{3,19}" if cloud == "aws"
                    else r"dmi-w10-a1-[a-z0-9-]{4,20}", request["prefix"]), "namespace")
    resources, extra = request["resources"], request["auxiliary"]
    exact(resources, AWS if cloud == "aws" else AZURE)
    if cloud == "aws":
        for address, prefix in AWS.items():
            pattern = prefix + r"-[a-f0-9]{17}" if prefix else request["prefix"] + r"-[a-zA-Z0-9-]{1,80}"
            require(matches(pattern, resources[address]), "resource_id")
        exact(extra, {"root_volume", "primary_eni", "default_route_table", "default_security_group", "default_network_acl"})
        for key, prefix in {"root_volume": "vol", "primary_eni": "eni", "default_route_table": "rtb",
                            "default_security_group": "sg", "default_network_acl": "acl"}.items():
            require(matches(prefix + r"-[a-f0-9]{17}", extra[key]), "auxiliary_id")
        require(len(set([*resources.values(), *extra.values()])) == len(resources) + len(extra), "duplicate_id")
    else:
        group = "/subscriptions/" + identity["azure_subscription_id"] + "/resourceGroups/" + request["prefix"] + "-rg"
        require(resources["azurerm_resource_group.agent"].lower() == group.lower(), "group_ownership")
        for address, suffix in AZURE.items():
            if suffix:
                ending = r"[a-zA-Z0-9-]+/subnets/[a-zA-Z0-9-]+" if address == "azurerm_subnet.agent" else r"[a-zA-Z0-9-]+"
                require(matches((group + suffix).lower() + ending, resources[address].lower()), "resource_ownership")
        require(resources["azurerm_network_interface_security_group_association.agent"].lower()
                == resources["azurerm_network_interface.agent"].lower(), "association_ownership")
        exact(extra, {"os_disk"})
        require(matches((group + "/providers/Microsoft.Compute/disks/").lower() + r"[a-zA-Z0-9-]+",
                        extra["os_disk"].lower()), "disk_ownership")
    backend = request["backend"]
    exact(backend, {"resource_group_name", "storage_account_name", "container_name", "key",
                    "lineage", "serial", "state_sha256", "restore_receipt_sha256"})
    require(matches(r"[a-z][a-z0-9-]{2,60}", backend["resource_group_name"])
            and not backend["resource_group_name"].startswith("dmi-w10-")
            and matches(r"[a-z][a-z0-9]{2,23}", backend["storage_account_name"])
            and not backend["storage_account_name"].startswith("w10cln")
            and matches(r"[a-z][a-z0-9-]{2,62}", backend["container_name"])
            and backend["key"] == request["prefix"] + "/" + cloud + ".tfstate"
            and matches(core.UUID, backend["lineage"])
            and type(backend["serial"]) is int and backend["serial"] >= 1, "independent_backend_required")
    hashes.extend([backend["state_sha256"], backend["restore_receipt_sha256"]])
    require(all(matches(r"[a-f0-9]{64}", value) and value != "0" * 64 for value in hashes), "artifact_hash")
    return "armed"


def flatten(module_value, allowed_children=()):
    require(isinstance(module_value, dict), "module_shape")
    result = {}
    for resource in module_value.get("resources", []):
        address = resource.get("address")
        require(isinstance(address, str) and address not in result, "duplicate_address")
        result[address] = resource
    for child in module_value.get("child_modules", []):
        require(child.get("address") in allowed_children, "foreign_module")
        for address, resource in flatten(child).items():
            require(address not in result, "duplicate_address")
            result[address] = resource
    return result


def validate_checks(checks, cloud, deleted):
    root = WEEK / ("application-pipelines/target/terraform/aws" if cloud == "aws" else "self-hosted-agent/azure-vm")
    variables = {"var." + name for name in re.findall(r'(?m)^variable "([a-z0-9_]+)"', regular(root / "variables.tf").decode())}
    if cloud == "aws":
        variables |= {"module.guard.var." + name for name in re.findall(
            r'(?m)^variable "([a-z0-9_]+)"', regular(root.parent / "guard/main.tf").decode())}
    require(isinstance(checks, list), "check_shape")
    for check in checks:
        address = check.get("address", {})
        allowed = variables if address.get("kind") == "var" else deleted if address.get("kind") == "resource" else set()
        # Terraform deliberately skips creation preconditions/variable checks in a destroy plan.
        require(address.get("to_display") in allowed and check.get("status") in {"pass", "unknown"}, "unexpected_plan_check")


def validate_plan(plan, request):
    cloud = request["cloud"]
    require(plan.get("format_version") == "1.2" and plan.get("terraform_version") == "1.13.5"
            and plan.get("complete") is True and plan.get("errored") is False and plan.get("applyable") is True
            and not plan.get("resource_drift") and not plan.get("deferred_changes"), "incomplete_or_drifted_plan")
    planned_at = core.utc(plan["timestamp"])
    require(core.utc(request["approval"]["approved_at"]) <= planned_at
            < core.utc(request["approval"]["execute_before"]), "plan_outside_cleanup_authority")
    expected = set(request["resources"]) | {GUARD[cloud]}
    allowed_children = ("module.guard",) if cloud == "aws" else ()
    prior = flatten(plan["prior_state"]["values"]["root_module"], allowed_children)
    managed = {address for address, value in prior.items() if value.get("mode") == "managed"}
    require(managed == expected and set(prior) <= expected | DATA[cloud], "prior_state_scope")
    remaining = flatten(plan["planned_values"].get("root_module", {}), allowed_children)
    require(not any(value.get("mode") == "managed" for value in remaining.values())
            and set(remaining) <= DATA[cloud], "remaining_managed_resources")
    seen = set()
    for resource in plan["resource_changes"]:
        address, change = resource["address"], resource["change"]
        require(address not in seen and not resource.get("previous_address") and not resource.get("deposed")
                and not change.get("importing") and not change.get("generated_config"), "move_import_duplicate_or_deposed")
        seen.add(address)
        if resource.get("mode") == "data":
            require(address in DATA[cloud] and change["actions"] in (["read"], ["delete"], ["no-op"]), "foreign_data")
            continue
        require(address in expected and resource.get("mode") == "managed"
                and resource.get("type") == address.split(".")[-2]
                and change["actions"] == ["delete"] and change.get("after") is None
                and change["before"] == prior[address]["values"], "not_exact_destroy")
        before = change["before"]
        if address == GUARD[cloud]:
            value = before["input"]
            if cloud == "aws":
                require(value["assignment"] == "week10-a2" and value["name_prefix"] == request["prefix"]
                        and value["approval"]["expires_at"] == request["original_expires_at"], "guard_ownership")
            else:
                require(value == {"assignment": "week-10-assignment-01", "expires_at": request["original_expires_at"]},
                        "guard_ownership")
            continue
        require(before["id"].lower() == request["resources"][address].lower(), "unapproved_id")
        taggable = cloud == "aws" and address != "aws_route_table_association.target"
        taggable = taggable or (cloud == "azure_agent" and address not in {
            "azurerm_subnet.agent", "azurerm_network_interface_security_group_association.agent"})
        if taggable:
            tags = before.get("tags_all" if cloud == "aws" else "tags", {})
            require(all(tags.get(key) == value for key, value in {
                "assignment": "week10-a2" if cloud == "aws" else "week-10-assignment-01",
                "managed_by": "Terraform", "learner": "Eze Favour",
                "expires_at": request["original_expires_at"]}.items()), "ownership_tags")
        if address == "aws_instance.target":
            disks = before["root_block_device"]
            require(len(disks) == 1 and disks[0]["volume_id"] == request["auxiliary"]["root_volume"]
                    and disks[0]["delete_on_termination"] is True and not before.get("ebs_block_device")
                    and before["primary_network_interface_id"] == request["auxiliary"]["primary_eni"], "implicit_resources")
        if address == "azurerm_linux_virtual_machine.agent":
            require(len(before["os_disk"]) == 1 and before["os_disk"][0]["name"]
                    == request["auxiliary"]["os_disk"].split("/")[-1], "implicit_disk")
    require(seen >= expected and seen <= expected | DATA[cloud], "incomplete_deletions")
    validate_checks(plan.get("checks", []), cloud, expected)
    return len(request["resources"])


def check_backend(metadata, request):
    backend = metadata["backend"]
    require(backend["type"] == "azurerm", "local_state_not_independent")
    expected = {key: request["backend"][key] for key in ("resource_group_name", "storage_account_name", "container_name", "key")}
    expected.update(subscription_id=request["identity"]["azure_subscription_id"],
                    tenant_id=request["identity"]["azure_tenant_id"], use_azuread_auth=True, use_cli=True)
    config = backend["config"]
    require(all(type(config.get(key)) is type(value) and config.get(key) == value
                for key, value in expected.items()), "backend_binding")
    require(all(key in expected or (key == "environment" and value == "public")
                or value is None or value is False or value == "" or value == []
                for key, value in config.items()), "unsupported_backend_option")


def state_status(state, request):
    expected = request["backend"]
    require(state.get("version") == 4 and state.get("lineage") == expected["lineage"]
            and type(state.get("serial")) is int and state["serial"] >= expected["serial"]
            and isinstance(state.get("resources"), list), "state_binding")
    for resource in state["resources"]:
        require(resource.get("mode") in {"managed", "data"}, "state_shape")
        require(all(not instance.get("deposed") for instance in resource.get("instances", [])), "deposed_state")
    if not any(resource["mode"] == "managed" for resource in state["resources"]):
        return "empty"
    require(state["serial"] == expected["serial"] and digest(canonical(state)) == expected["state_sha256"], "state_changed")
    return "populated"


def identity(runner, request):
    expected = request["identity"]
    account = runner.az("account", "show")
    require(account.get("id") == expected["azure_subscription_id"] and account.get("tenantId") == expected["azure_tenant_id"]
            and account.get("user", {}).get("type") == "servicePrincipal"
            and account.get("user", {}).get("name", "").lower() == expected["azure_client_id"], "azure_identity")
    # Native Azure authentication validates tokens; decoding here only binds the selected principal.
    response = runner.az("account", "get-access-token", "--subscription", expected["azure_subscription_id"],
                         "--resource", "https://management.azure.com/")
    token = response.pop("accessToken")
    require(isinstance(token, str) and len(token) <= 32768 and token.count(".") == 2, "token_shape")
    part = token.split(".")[1]
    claims = core.load_json(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    token = None
    require(claims.get("oid") == expected["azure_principal_id"] and claims.get("tid") == expected["azure_tenant_id"]
            and claims.get("appid", claims.get("azp")) == expected["azure_client_id"]
            and claims.get("aud") == "https://management.azure.com/"
            and type(claims.get("exp")) is int and claims["exp"] > datetime.now(timezone.utc).timestamp() + 1300,
            "azure_token_binding")
    if request["cloud"] == "aws":
        caller = runner.aws("sts", "get-caller-identity")
        role = expected["aws_role_arn"].split(":role/")[1]
        require(caller.get("Account") == expected["aws_account_id"]
                and matches(r"arn:aws:sts::" + expected["aws_account_id"] + ":assumed-role/" + role
                            + r"/[A-Za-z0-9+=,.@_-]{2,64}", caller.get("Arn")), "aws_identity")


def source_bundle(bundle, request, runner, terraform):
    working = bundle / "root"
    source = WEEK / ("application-pipelines/target/terraform/aws" if request["cloud"] == "aws" else "self-hosted-agent/azure-vm")
    names = {"main.tf", "variables.tf", ".terraform.lock.hcl"}
    if request["cloud"] == "azure_agent":
        names |= {"versions.tf", "cloud-init.yaml"}
    for name in names:
        require(regular(working / name) == regular(source / name), "source_changed")
    if request["cloud"] == "aws":
        require(regular(bundle / "guard/main.tf") == regular(source.parent / "guard/main.tf"), "guard_changed")
        require({p.name for p in (bundle / "guard").iterdir()} == {"main.tf"}, "extra_module_source")
        modules = core.load_json(regular(working / ".terraform/modules/modules.json", private=True))
        require(modules == {"Modules": [{"Key": "", "Source": "", "Dir": "."},
                                        {"Key": "guard", "Source": "../guard", "Dir": "../guard"}]}, "module_cache_changed")
    require(regular(working / "backend_override.tf") == regular(ROOT / (request["cloud"] + ".backend.tf.example")),
            "backend_override_changed")
    allowed = names | {"backend_override.tf", ".terraform", "cleanup-inputs.json"}
    require({p.name for p in working.iterdir()} <= allowed, "unexpected_workspace_files")
    require(digest(regular(working / "cleanup-inputs.json", private=True)) == request["artifacts"]["inputs_sha256"], "inputs_changed")
    workspace = working / ".terraform/environment"
    if workspace.exists() or workspace.is_symlink():
        require(regular(workspace, private=True).strip() == b"default", "default_workspace_required")
    require(digest(regular(terraform, limit=256 * 1024 * 1024)) == request["terraform_sha256"], "tool_changed")
    commit = runner.call(["git", "-c", "core.fsmonitor=false", "-C", str(WEEK), "rev-parse", "HEAD"], structured=False)
    require(commit.decode().strip() == request["source_commit"], "source_revision")
    runner.call(["git", "-c", "core.fsmonitor=false", "-C", str(WEEK), "diff", "--quiet", "HEAD", "--", "."], structured=False)
    require(runner.call([str(terraform), "version", "-json"]).get("terraform_version") == "1.13.5", "tool_version")
    check_backend(core.load_json(regular(working / ".terraform/terraform.tfstate", private=True)), request)


def execute(runner, request, terraform, saved_plan, read=regular, clock=None, verify=inventory.verify):
    window(request, clock() if clock else None, reserve=1300)
    state = runner.call([str(terraform), "state", "pull"])
    if state_status(state, request) == "empty":
        verify(runner, request, absent=True)
        return {"status": "already_absent", "cloud_deletions": 0, "verified_absent": True, "workload_cleanup_ready": False}
    require(not saved_plan.exists() and not saved_plan.is_symlink(), "fresh_plan_path_required")
    verify(runner, request)
    runner.call([str(terraform), "plan", "-destroy", "-input=false", "-lock-timeout=30s",
                 "-var-file=cleanup-inputs.json", "-out=" + str(saved_plan)], timeout=300, structured=False)
    plan_hash = digest(read(saved_plan, private=True))
    plan = runner.call([str(terraform), "show", "-json", str(saved_plan)])
    count = validate_plan(plan, request)
    verify(runner, request)
    require(state_status(runner.call([str(terraform), "state", "pull"]), request) == "populated", "state_changed")
    require(digest(read(saved_plan, private=True)) == plan_hash, "plan_changed")
    window(request, clock() if clock else None, reserve=1300)
    runner.call([str(terraform), "apply", "-input=false", "-lock-timeout=30s", str(saved_plan)], timeout=1200, structured=False)
    require(state_status(runner.call([str(terraform), "state", "pull"]), request) == "empty", "state_not_empty")
    verify(runner, request, absent=True)
    return {"status": "deleted", "cloud_deletions": count, "verified_absent": True,
            "plan_sha256": plan_hash, "workload_cleanup_ready": False}


class DeadlineRunner(core.Runner):
    def __init__(self, environment, cwd, request):
        super().__init__(environment, cwd)
        self.request = request

    def call(self, arguments, *, timeout=180, structured=True):
        now = datetime.now(timezone.utc)
        window(self.request, now)
        remaining = int((core.utc(self.request["approval"]["execute_before"]) - now).total_seconds()) - 35
        require(remaining > 0, "cleanup_authority_expiring")
        return super().call(arguments, timeout=min(timeout, remaining), structured=structured)


def run(path, terraform):
    request = core.load_json(regular(path, limit=32768))
    if validate_request(request) == "unarmed":
        return {"status": "unarmed", "verified_absent": False, "workload_cleanup_ready": False}
    require(os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted",
            "independent_host_required")
    os.umask(0o077)
    runner_temporary = Path(os.environ["RUNNER_TEMP"])
    temporary = Path(os.environ["W10_RECOVERY_TEMP"])
    require(runner_temporary.is_absolute() and runner_temporary.resolve(strict=True) == runner_temporary
            and temporary != runner_temporary and temporary.is_relative_to(runner_temporary), "owned_temporary_root_required")
    bundle = path.parent
    for folder in (bundle, bundle / "root", bundle / "root/.terraform", bundle / "home", bundle / "azure"):
        private_directory(folder, temporary)
    if request["cloud"] == "aws":
        private_directory(bundle / "guard", temporary)
    regular(path, limit=32768, private=True)
    environment = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(bundle / "home"),
                   "AZURE_CONFIG_DIR": str(bundle / "azure"), "AZURE_CORE_COLLECT_TELEMETRY": "false",
                   "AZURE_CORE_NO_COLOR": "true", "AWS_EC2_METADATA_DISABLED": "true",
                   "AWS_SHARED_CREDENTIALS_FILE": "/dev/null", "AWS_CONFIG_FILE": "/dev/null",
                   "AWS_STS_REGIONAL_ENDPOINTS": "regional", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0",
                   "TF_CLI_CONFIG_FILE": "/dev/null", "TF_DATA_DIR": str(bundle / "root/.terraform"),
                   "CHECKPOINT_DISABLE": "1"}
    if request["cloud"] == "aws":
        for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            require(bool(os.environ.get(key)), "temporary_aws_session_required")
            environment[key] = os.environ[key]
    runner = DeadlineRunner(environment, bundle / "root", request)
    require(terraform is not None and terraform.is_absolute(), "explicit_tool_required")
    source_bundle(bundle, request, runner, terraform)
    identity(runner, request)
    return execute(runner, request, terraform, bundle / "destroy.tfplan")


def run_many(paths, terraform, operation=run):
    results = []
    for path in paths:
        try:
            result = operation(path, terraform)
        except (ValueError, OSError, KeyError, TypeError, AttributeError, UnicodeError):
            result = {"status": "failed", "verified_absent": False, "workload_cleanup_ready": False}
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, action="append", required=True)
    parser.add_argument("--terraform", type=Path)
    args = parser.parse_args()
    results = run_many(args.request, args.terraform)
    print(json.dumps({"results": results, "workload_cleanup_ready": False}, sort_keys=True))
    return int(any(result["status"] == "failed" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
