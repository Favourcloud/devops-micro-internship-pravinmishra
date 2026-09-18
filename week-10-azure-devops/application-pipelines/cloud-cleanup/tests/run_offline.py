"""Reuse the reviewed sandbox runner and installed providers; never download or authenticate."""
import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT.parents[1] / "epicbook/terraform/tests/run_offline.py"
spec = importlib.util.spec_from_file_location("native_sandbox", REFERENCE)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def source_files(root):
    provider = "azurerm" if root.name == "azure" else "aws"
    files = sorted([*root.glob("*.tf"), *root.glob("*.json.tftpl"), root / ".terraform.lock.hcl", *root.glob("tests/*.tftest.hcl")])
    if not all(path.is_file() and not path.is_symlink() for path in files):
        raise ValueError("Only regular reviewed source and lockfiles are allowed.")
    for path in root.glob("tests/*.tftest.hcl"):
        text = path.read_text()
        runs = re.findall(r'^run "[a-z0-9_]+"', text, re.M)
        commands = re.findall(r'\bcommand\s*=\s*(\w+)', text)
        allowed = {"plan", "apply"} if root.parent.name == "canary" else {"plan"}
        if not runs or len(runs) != len(commands) or not set(commands) <= allowed or 'mock_provider "' + provider + '"' not in text:
            raise ValueError("Every run must explicitly use the correct mocked provider; bootstrap is plan-only.")
    return files


def builtin_destroy(terraform, cloud):
    """Native Terraform semantics using the exact guard, with identity data replaced by fixture locals."""
    root = ROOT / "canary" / cloud
    guard = re.search(r'(?ms)^resource "terraform_data" "authorization" \{.*?^\}', (root / "main.tf").read_text())
    if guard is None:
        raise ValueError("Canary authorization guard missing.")
    now = datetime.now(timezone.utc)
    inputs = {"lease_id": "abcdef123456", "expires_at": (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "live_execution_approved": True}
    if cloud == "azure":
        inputs.update(subscription_id="00000000-0000-0000-0000-000000000001",
                      tenant_id="00000000-0000-0000-0000-000000000002",
                      operator_object_id="00000000-0000-0000-0000-000000000004")
        identity = {"subscription_id": inputs["subscription_id"], "tenant_id": inputs["tenant_id"],
                    "object_id": inputs["operator_object_id"]}
        original = "data.azurerm_client_config.current"
    else:
        inputs.update(account_id="000000000001", operator_arn="arn:aws:sts::000000000001:assumed-role/fixture/test")
        identity = {"account_id": inputs["account_id"], "arn": inputs["operator_arn"]}
        original = "data.aws_caller_identity.current"
    with tempfile.TemporaryDirectory(prefix="w10-g-", dir="/private/tmp") as directory:
        scratch = Path(directory)
        (scratch / "main.tf").write_text(guard.group().replace(original, "local.identity"))
        (scratch / "fixtures.tf.json").write_text(json.dumps({"locals": {"identity": identity}}))
        shutil.copyfile(root / "variables.tf", scratch / "variables.tf")
        variables = scratch / "case.auto.tfvars.json"
        variables.write_text(json.dumps(inputs))

        def run(arguments):
            result = subprocess.run(["/usr/bin/sandbox-exec", "-p", native.profile_for(scratch), str(terraform), *arguments],
                                    cwd=scratch, env=native.environment_for(scratch), capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise ValueError("Builtin-only fixture failed: " + result.stderr[:2000])
            return result.stdout

        run(["init", "-backend=false", "-input=false"])
        # Only Terraform's built-in terraform_data resource exists in this scratch root.
        run(["apply", "-input=false", "-auto-approve"])
        inputs.update(expires_at="2000-01-01T00:00:00Z", live_execution_approved=False)
        if cloud == "azure":
            inputs["operator_object_id"] = "00000000-0000-0000-0000-000000000009"
        else:
            inputs["operator_arn"] = "arn:aws:sts::000000000001:assumed-role/cleanup/test"
        variables.write_text(json.dumps(inputs))
        run(["plan", "-destroy", "-out=destroy.tfplan", "-input=false"])
        plan = json.loads(run(["show", "-json", "destroy.tfplan"]))
        changes = plan.get("resource_changes", [])
        if len(changes) != 1 or changes[0]["address"] != "terraform_data.authorization" or changes[0]["change"]["actions"] != ["delete"]:
            raise ValueError("Expected exactly one built-in guard deletion.")
        run(["apply", "-input=false", "destroy.tfplan"])
    return {"cloud_contract": cloud, "expired_approval_and_changed_identity_allow_guard_deletion": True,
            "real_cloud_provider_used": False}


def builtin_root_expiry(terraform):
    """A saved plan must fail after root approval expires, without any cloud provider."""
    root = ROOT / "operator/aws"
    guard = re.search(r'(?ms)^resource "terraform_data" "authorization" \{.*?^\}', (root / "main.tf").read_text())
    if guard is None:
        raise ValueError("Operator authorization guard missing.")
    identity = {"account_id": "000000000001", "arn": "arn:aws:iam::000000000001:root"}
    with tempfile.TemporaryDirectory(prefix="w10-r-", dir="/private/tmp") as directory:
        scratch = Path(directory)
        (scratch / "main.tf").write_text(guard.group().replace("data.aws_caller_identity.current", "local.identity"))
        (scratch / "fixtures.tf.json").write_text(json.dumps({"locals": {
            "identity": identity, "user_arn": "arn:aws:iam::000000000001:user/dmi-w10-bootstrap-abcdef123456"}}))
        for name in ("variables.tf", "approval.tf"):
            shutil.copyfile(root / name, scratch / name)

        def run(arguments, expected_failure=False):
            result = subprocess.run(["/usr/bin/sandbox-exec", "-p", native.profile_for(scratch), str(terraform), *arguments],
                                    cwd=scratch, env=native.environment_for(scratch), capture_output=True, text=True, timeout=120)
            if expected_failure:
                if not result.returncode or "The separate root exception must still be valid" not in result.stdout + result.stderr:
                    raise ValueError("Expired root saved-plan application did not fail at the expected guard.")
            elif result.returncode:
                raise ValueError("Builtin root-expiry fixture failed: " + result.stderr[:2000])
            return result.stdout

        run(["init", "-backend=false", "-input=false"])
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(seconds=10)
        stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
        inputs = {
            "lease_id": "abcdef123456", "account_id": identity["account_id"], "administrator_arn": identity["arn"],
            "oidc_issuer": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0",
            "live_execution_approved": True,
            "approval": {"approved_at": stamp(now - timedelta(minutes=2)), "expires_at": stamp(now + timedelta(hours=1)),
                         "estimated_total_usd": 0, "planning_allowance_usd": 10},
            "root_bootstrap_approval": {"approved_at": stamp(now - timedelta(minutes=1)), "expires_at": stamp(expiry)},
        }
        (scratch / "case.auto.tfvars.json").write_text(json.dumps(inputs))
        run(["plan", "-input=false", "-out=fixture.tfplan"])
        time.sleep(max(0, (expiry - datetime.now(timezone.utc)).total_seconds()) + 0.1)
        run(["apply", "-input=false", "-no-color", "fixture.tfplan"], expected_failure=True)
        state = json.loads(run(["show", "-json"]))
        if state.get("values", {}).get("root_module", {}).get("resources"):
            raise ValueError("Expired root fixture unexpectedly created a built-in resource.")
    return {"expired_saved_plan_rejected": True, "real_cloud_provider_used": False,
            "root_credentials_used": False, "resources_created": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform", required=True, type=Path)
    parser.add_argument("--azure-plugin-dir", required=True, type=Path)
    parser.add_argument("--aws-plugin-dir", required=True, type=Path)
    args = parser.parse_args()
    terraform = args.terraform.resolve()
    native.source_files = source_files
    checks = {}
    roots = [("operator", "aws"), ("bootstrap", "azure"), ("bootstrap", "aws"),
             ("canary", "azure"), ("canary", "aws")]
    for phase, cloud in roots:
        native.SOURCE = ROOT / phase / cloud
        plugins = args.azure_plugin_dir if cloud == "azure" else args.aws_plugin_dir
        checks[phase + "/" + cloud] = native.check(terraform, plugins.resolve())
    guards = [builtin_destroy(terraform, cloud) for cloud in ("azure", "aws")]
    print(json.dumps({"roots": checks, "builtin_guard_destroy_checks": guards,
                      "builtin_root_expiry_check": builtin_root_expiry(terraform),
                      "external_network_denied": True, "cloud_resources_created": False}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
