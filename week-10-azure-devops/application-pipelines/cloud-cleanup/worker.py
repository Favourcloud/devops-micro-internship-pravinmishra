"""Canary-only hosted cleanup. Never provisions, registers an agent or deletes workload VMs."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
UUID = r"[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}"
ASSIGNMENT = "week10-cleanup-canary"
GATES = {"nonroot_bootstrap_verified", "scoped_connection_verified", "hosted_capacity_verified",
         "exclusive_lock_verified", "control_plane_teardown_verified"}


class Rejected(ValueError):
    """Only fixed, non-sensitive error codes cross the CLI boundary."""


def require(condition, code):
    if not condition:
        raise Rejected(code)


def exact_keys(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys), "unexpected_fields")


def matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def utc(value):
    require(matches(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "invalid_time")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise Rejected("invalid_time") from None


def load_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_field")
            result[key] = value
        return result
    try:
        return json.loads(text, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(Rejected("nonfinite_number")))
    except (ValueError, TypeError):
        raise Rejected("invalid_json") from None


def read_config(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "r") as stream:
        metadata = os.fstat(stream.fileno())
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid()
                and metadata.st_size <= 32768, "unsafe_config_file")
        return load_json(stream.read(32769))


def validate_config(config, now=None):
    now = now or datetime.now(timezone.utc)
    exact_keys(config, {"schema_version", "kind", "armed", "lease_id", "source_commit", "approved_at",
                        "cleanup_at", "expires_at", "budget", "readiness", "azure", "aws", "federation"})
    require(type(config["schema_version"]) is int and config["schema_version"] == 1, "schema_version")
    require(config["kind"] == "canary", "canary_only")
    require(type(config["armed"]) is bool, "invalid_armed_flag")
    if not config["armed"]:
        return "unarmed"
    require(matches(r"[a-f0-9]{12}", config["lease_id"]), "lease_id")
    require(matches(r"[a-f0-9]{40}", config["source_commit"])
            and config["source_commit"] != "0" * 40, "source_commit")
    start, due, end = (utc(config[key]) for key in ("approved_at", "cleanup_at", "expires_at"))
    require(start <= now and 0 < (end - start).total_seconds() <= 86400
            and start <= due and (end - due).total_seconds() >= 7200, "resource_window")
    exact_keys(config["budget"], {"estimated_total_usd", "planning_allowance_usd"})
    estimate, allowance = (config["budget"][key] for key in ("estimated_total_usd", "planning_allowance_usd"))
    require(all(type(n) in (int, float) and math.isfinite(n) for n in (estimate, allowance))
            and 0 < estimate <= allowance <= 10, "budget")
    exact_keys(config["readiness"], GATES)
    require(all(config["readiness"][gate] is True for gate in GATES), "readiness_pending")
    exact_keys(config["azure"], {"subscription_id", "tenant_id", "client_id", "principal_id"})
    require(all(matches(UUID, value) for value in config["azure"].values()), "azure_identity")
    exact_keys(config["aws"], {"account_id"})
    require(matches(r"[0-9]{12}", config["aws"]["account_id"]), "aws_identity")
    exact_keys(config["federation"], {"issuer", "subject", "authorized_party"})
    federation = config["federation"]
    require(matches(r"https://login\.microsoftonline\.com/" + UUID + r"/v2\.0", federation["issuer"])
            and matches(r"[A-Za-z0-9_:/.-]{10,400}", federation["subject"])
            and (federation["authorized_party"] is None or matches(UUID, federation["authorized_party"])),
            "federation_metadata")
    # Expiry never disables a late cleanup retry.
    return "due" if now >= due else "not_due"


def validate_claims(token, config, now=None):
    now = now or datetime.now(timezone.utc)
    require(isinstance(token, str) and len(token) <= 16384 and token.count(".") == 2, "oidc_shape")
    try:
        encoded = token.split(".")[1]
        claims = load_json(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    except (ValueError, TypeError):
        raise Rejected("oidc_shape") from None
    expected = config["federation"]
    require(isinstance(claims, dict) and claims.get("iss") == expected["issuer"]
            and claims.get("sub") == expected["subject"]
            and claims.get("aud") == "api://AzureADTokenExchange"
            and claims.get("azp") == expected["authorized_party"], "oidc_claims")
    require(type(claims.get("exp")) is int and claims["exp"] > now.timestamp() + 120
            and type(claims.get("nbf")) is int and claims["nbf"] <= now.timestamp() + 30, "oidc_lifetime")
    # This is a binding check, not signature validation. STS validates the signed token.


def group_id(config):
    return ("/subscriptions/" + config["azure"]["subscription_id"]
            + "/resourceGroups/dmi-w10-cleanup-" + config["lease_id"] + "-canary-rg")


def validate_plan(plan, config, cloud):
    require(cloud in {"azure", "aws"}, "cloud")
    require(isinstance(plan, dict) and str(plan.get("format_version", "")).startswith("1.")
            and plan.get("errored") is not True and plan.get("complete") is not False
            and not plan.get("deferred_changes"), "invalid_plan")
    target = "azurerm_resource_group.canary" if cloud == "azure" else "aws_vpc.canary"
    data_address = "data.azurerm_client_config.current" if cloud == "azure" else "data.aws_caller_identity.current"
    seen, cloud_deletes = set(), 0
    for resource in plan.get("resource_changes", []):
        require(isinstance(resource, dict), "invalid_resource")
        address, change = resource.get("address"), resource.get("change", {})
        require(address not in seen, "duplicate_resource")
        seen.add(address)
        require(not resource.get("previous_address") and not resource.get("deposed")
                and not change.get("importing"), "import_move_or_deposed")
        if resource.get("mode") == "data":
            require(address == data_address and change.get("actions") in (["read"], ["no-op"], ["delete"]),
                    "unexpected_data")
            continue
        require(resource.get("mode") == "managed" and address in {target, "terraform_data.authorization"}
                and resource.get("type") == address.split(".")[0]
                and change.get("actions") == ["delete"], "not_canary_delete_only")
        before = change.get("before")
        require(isinstance(before, dict), "missing_before")
        if address == "terraform_data.authorization":
            require(before.get("input") == config["lease_id"], "guard_ownership")
            continue
        cloud_deletes += 1
        tags = before.get("tags", {})
        require(all(tags.get(key) == value for key, value in {
            "assignment": ASSIGNMENT, "cleanup_lease": config["lease_id"],
            "expires_at": config["expires_at"], "managed_by": "terraform"}.items()), "ownership_tags")
        if cloud == "azure":
            require(str(before.get("id", "")).lower() == group_id(config).lower()
                    and before.get("name") == group_id(config).split("/")[-1]
                    and before.get("location") == "uksouth", "azure_ownership")
        else:
            require(matches(r"vpc-[a-f0-9]{17}", before.get("id"))
                    and before.get("owner_id") == config["aws"]["account_id"]
                    and before.get("cidr_block") == "10.199.0.0/24"
                    and tags.get("Name") == "dmi-w10-cleanup-" + config["lease_id"] + "-canary",
                    "aws_ownership")
    return cloud_deletes


def managed_state_empty(state):
    def walk(module):
        require(isinstance(module, dict), "invalid_state")
        return (not any(r.get("mode") == "managed" for r in module.get("resources", []))
                and all(walk(child) for child in module.get("child_modules", [])))
    require(isinstance(state, dict) and str(state.get("format_version", "")).startswith("1."), "invalid_state")
    return walk(state.get("values", {}).get("root_module", {}))


class Runner:
    def __init__(self, environment, cwd):
        self.environment, self.cwd = environment, cwd

    def call(self, arguments, *, timeout=180, structured=True):
        try:
            process = subprocess.Popen(arguments, cwd=self.cwd, env=self.environment,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
        except OSError:
            raise Rejected("command_unavailable") from None
        try:
            output, _ = process.communicate(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Give Terraform time to persist state and release its lock before stopping this process tree.
            try:
                process.send_signal(signal.SIGINT)
                process.communicate(timeout=30)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.communicate()
            raise Rejected("command_interrupted_or_timeout") from None
        require(process.returncode == 0 and len(output) <= 4 * 1024 * 1024, "command_failed")
        return load_json(output) if structured else output

    def az(self, *arguments):
        return self.call(["az", *arguments, "--only-show-errors", "--output", "json"])

    def aws(self, *arguments):
        return self.call(["aws", "--region", "eu-west-2", "--no-cli-pager", *arguments, "--output", "json"])


def backend(config, cloud):
    return {"storage_account_name": "w10cln" + config["lease_id"], "container_name": "canary-" + cloud,
            "key": "canary.tfstate", "tenant_id": config["azure"]["tenant_id"],
            "subscription_id": config["azure"]["subscription_id"],
            "use_azuread_auth": True, "use_cli": True, "use_oidc": False, "use_msi": False}


def vpcs(runner, config):
    result = runner.aws("ec2", "describe-vpcs", "--filters",
                        "Name=tag:cleanup_lease,Values=" + config["lease_id"])
    require(isinstance(result.get("Vpcs"), list), "invalid_inventory")
    return result["Vpcs"]


def verify_empty_canary(runner, config, cloud):
    if cloud == "azure":
        exists = runner.az("group", "exists", "--name", group_id(config).split("/")[-1])
        require(type(exists) is bool, "invalid_inventory")
        if exists:
            children = runner.az("resource", "list", "--resource-group", group_id(config).split("/")[-1])
            require(children == [], "canary_group_has_children")
    else:
        found = vpcs(runner, config)
        require(len(found) <= 1, "ambiguous_canary")
        for vpc in found:
            identifier = vpc.get("VpcId")
            require(matches(r"vpc-[a-f0-9]{17}", identifier), "invalid_inventory")
            inventories = (
                ("describe-subnets", "Subnets", "vpc-id"),
                ("describe-network-interfaces", "NetworkInterfaces", "vpc-id"),
                ("describe-internet-gateways", "InternetGateways", "attachment.vpc-id"),
                ("describe-egress-only-internet-gateways", "EgressOnlyInternetGateways", None),
                ("describe-vpc-endpoints", "VpcEndpoints", "vpc-id"),
                ("describe-vpn-gateways", "VpnGateways", "attachment.vpc-id"),
                ("describe-vpc-peering-connections", "VpcPeeringConnections", "requester-vpc-info.vpc-id"),
                ("describe-vpc-peering-connections", "VpcPeeringConnections", "accepter-vpc-info.vpc-id"),
                ("describe-transit-gateway-attachments", "TransitGatewayAttachments", "resource-id"),
            )
            for operation, key, filter_name in inventories:
                if filter_name is None:
                    # This API documents tag filters only; inspect its paginated regional attachments locally.
                    rows = runner.aws("ec2", operation).get(key)
                    require(isinstance(rows, list), "invalid_inventory")
                    for row in rows:
                        require(isinstance(row, dict) and isinstance(row.get("Attachments"), list), "invalid_inventory")
                        for attachment in row["Attachments"]:
                            require(isinstance(attachment, dict) and isinstance(attachment.get("VpcId"), str),
                                    "invalid_inventory")
                            require(attachment["VpcId"] != identifier, "canary_vpc_has_children")
                else:
                    result = runner.aws("ec2", operation, "--filters", "Name=" + filter_name + ",Values=" + identifier)
                    require(result.get(key) == [], "canary_vpc_has_children")
            for operation, key, default_field in (
                ("describe-security-groups", "SecurityGroups", "GroupName"),
                ("describe-network-acls", "NetworkAcls", "IsDefault"),
                ("describe-route-tables", "RouteTables", None),
            ):
                rows = runner.aws("ec2", operation, "--filters", "Name=vpc-id,Values=" + identifier).get(key)
                require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict)
                        and rows[0].get("VpcId") == identifier, "nondefault_canary_network")
                if default_field == "GroupName":
                    require(rows[0].get(default_field) == "default", "nondefault_canary_network")
                elif default_field == "IsDefault":
                    require(rows[0].get(default_field) is True, "nondefault_canary_network")
                else:
                    associations = rows[0].get("Associations")
                    require(isinstance(associations, list) and len(associations) == 1
                            and isinstance(associations[0], dict) and associations[0].get("Main") is True
                            and not associations[0].get("SubnetId")
                            and not associations[0].get("GatewayId"), "nondefault_canary_network")


def absent(runner, config, cloud):
    if cloud == "azure":
        value = runner.az("group", "exists", "--name", group_id(config).split("/")[-1])
        require(type(value) is bool, "invalid_inventory")
        return not value
    return vpcs(runner, config) == []


def clean_cloud(runner, config, cloud, terraform, scratch):
    connection = backend(config, cloud)
    exists = runner.az("storage", "blob", "exists", "--auth-mode", "login", "--account-name",
                       connection["storage_account_name"], "--container-name", connection["container_name"],
                       "--name", connection["key"])
    require(exists.get("exists") is True, "state_blob_missing")
    root = scratch / cloud
    root.mkdir(mode=0o700)
    for name in ("main.tf", "variables.tf", ".terraform.lock.hcl"):
        source = ROOT / "canary" / cloud / name
        require(source.is_file() and not source.is_symlink(), "unsafe_source")
        shutil.copyfile(source, root / name)
    (root / "backend.json").write_text(json.dumps(connection))
    inputs = {"lease_id": config["lease_id"], "expires_at": config["expires_at"], "live_execution_approved": False}
    if cloud == "azure":
        inputs.update(subscription_id=config["azure"]["subscription_id"], tenant_id=config["azure"]["tenant_id"],
                      operator_object_id=config["azure"]["principal_id"])
    else:
        inputs.update(account_id=config["aws"]["account_id"], operator_arn=runner.environment["W10_OPERATOR_ARN"])
    (root / "cleanup.auto.tfvars.json").write_text(json.dumps(inputs))
    tf = Runner(dict(runner.environment, TF_DATA_DIR=str(root / "data")), root)
    tf.call([str(terraform), "init", "-input=false", "-lockfile=readonly", "-backend-config=backend.json"],
            timeout=300, structured=False)
    verify_empty_canary(runner, config, cloud)
    tf.call([str(terraform), "plan", "-destroy", "-input=false", "-lock-timeout=30s", "-out=destroy.tfplan"],
            timeout=300, structured=False)
    plan = tf.call([str(terraform), "show", "-json", "destroy.tfplan"])
    deletions = validate_plan(plan, config, cloud)
    # A real deletion must be observed before this lease can prove canary acceptance.
    plan_hash = hashlib.sha256((root / "destroy.tfplan").read_bytes()).hexdigest()
    verify_empty_canary(runner, config, cloud)
    tf.call([str(terraform), "apply", "-input=false", "-lock-timeout=30s", "destroy.tfplan"],
            timeout=600, structured=False)
    require(managed_state_empty(tf.call([str(terraform), "show", "-json"])), "state_not_empty")
    for attempt in range(7):
        if absent(runner, config, cloud):
            return {"verified_absent": True, "cloud_deletions": deletions, "plan_sha256": plan_hash}
        if attempt < 6:
            time.sleep(10)
    raise Rejected("absence_unverified")


def assume_aws(runner, config, token, scratch):
    token_file = scratch / "assertion.jwt"
    token_file.write_text(token)
    role = "arn:aws:iam::" + config["aws"]["account_id"] + ":role/dmi-w10-cleanup-" + config["lease_id"]
    try:
        response = runner.aws("sts", "assume-role-with-web-identity", "--no-sign-request", "--role-arn", role,
                              "--role-session-name", "w10-cleanup-" + config["lease_id"],
                              "--duration-seconds", "3600", "--web-identity-token", "file://" + str(token_file))
    finally:
        token_file.unlink(missing_ok=True)
    credentials = response["Credentials"]
    runner.environment.update(AWS_ACCESS_KEY_ID=credentials["AccessKeyId"],
                              AWS_SECRET_ACCESS_KEY=credentials["SecretAccessKey"],
                              AWS_SESSION_TOKEN=credentials["SessionToken"])
    identity = runner.aws("sts", "get-caller-identity")
    expected = ("arn:aws:sts::" + config["aws"]["account_id"] + ":assumed-role/dmi-w10-cleanup-"
                + config["lease_id"] + "/w10-cleanup-" + config["lease_id"])
    require(identity.get("Account") == config["aws"]["account_id"] and identity.get("Arn") == expected,
            "aws_account_or_role")
    runner.environment["W10_OPERATOR_ARN"] = expected


def clean_both(runner, config, token, terraform, scratch):
    results = {}
    for cloud in ("aws", "azure"):
        try:
            if cloud == "aws":
                assume_aws(runner, config, token, scratch)
            results[cloud] = clean_cloud(runner, config, cloud, terraform, scratch)
        except (Rejected, OSError, ValueError, KeyError, TypeError):
            results[cloud] = {"verified_absent": False, "cloud_deletions": None, "plan_sha256": None}
        finally:
            token = None
    return results


def run(config, terraform):
    require(validate_config(config) == "due", "not_due")
    require(os.environ.get("AGENT_ID") and os.environ.get("TF_BUILD") == "True", "pipeline_job_required")
    require(os.environ.get("servicePrincipalId", "").lower() == config["azure"]["client_id"]
            and os.environ.get("tenantId", "").lower() == config["azure"]["tenant_id"], "connection_identity")
    token = os.environ.pop("idToken", None)
    validate_claims(token, config)
    temporary = Path(os.environ["AGENT_TEMPDIRECTORY"]).resolve(strict=True)
    azure_config = Path(os.environ["AZURE_CONFIG_DIR"]).resolve(strict=True)
    require(azure_config.is_relative_to(temporary), "nonisolated_azure_cache")
    require(terraform.is_file() and terraform.resolve().is_relative_to(temporary), "unsafe_tool_path")
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix="w10-cleanup-", dir=temporary) as directory:
        scratch = Path(directory)
        environment = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(scratch),
                       "AZURE_CONFIG_DIR": str(azure_config), "AZURE_CORE_COLLECT_TELEMETRY": "false",
                       "AZURE_CORE_NO_COLOR": "true", "AWS_EC2_METADATA_DISABLED": "true",
                       "AWS_SHARED_CREDENTIALS_FILE": "/dev/null", "AWS_CONFIG_FILE": "/dev/null",
                       "AWS_STS_REGIONAL_ENDPOINTS": "regional", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0",
                       "TF_CLI_CONFIG_FILE": "/dev/null", "CHECKPOINT_DISABLE": "1"}
        runner = Runner(environment, scratch)
        actual_commit = runner.call(["git", "-C", str(ROOT), "rev-parse", "HEAD"], structured=False).decode().strip()
        require(actual_commit == config["source_commit"], "source_commit_mismatch")
        runner.call(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", "."], structured=False)
        require(runner.call([str(terraform), "version", "-json"]).get("terraform_version") == "1.13.5", "tool_version")
        account = runner.az("account", "show")
        require(account.get("id") == config["azure"]["subscription_id"]
                and account.get("tenantId") == config["azure"]["tenant_id"], "azure_account")
        results = clean_both(runner, config, token, terraform, scratch)
        token = None
        receipt = {"schema_version": 1, "kind": "canary", "lease_id": config["lease_id"],
                   "source_commit": config["source_commit"], "checked_at": datetime.now(timezone.utc).isoformat(),
                   "results": results, "workload_cleanup_ready": False}
        receipt_file = scratch / "receipt.json"
        receipt_file.write_text(json.dumps(receipt, sort_keys=True))
        runner.az("storage", "blob", "upload", "--auth-mode", "login", "--account-name", "w10cln" + config["lease_id"],
                  "--container-name", "receipts", "--name", config["lease_id"] + "/" + scratch.name + ".json",
                  "--file", str(receipt_file), "--overwrite", "false")
        print(json.dumps(receipt, sort_keys=True))
        require(all(result["verified_absent"] for result in results.values()), "cleanup_incomplete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("ready", "run"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--terraform", type=Path)
    args = parser.parse_args()
    try:
        config = read_config(args.config)
        status = validate_config(config)
        if args.mode == "ready":
            print("##vso[task.setvariable variable=canaryDue]" + str(status == "due").lower())
            print(json.dumps({"status": status, "workload_cleanup_ready": False}))
        elif status != "due":
            print(json.dumps({"status": status, "workload_cleanup_ready": False}))
        else:
            require(args.terraform is not None, "terraform_required")
            run(config, args.terraform)
        return 0
    except (Rejected, OSError, ValueError, KeyError, TypeError, AttributeError):
        print('{"status":"failed","verified_absent":false,"workload_cleanup_ready":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
