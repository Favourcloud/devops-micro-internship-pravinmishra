"""Native destroy semantics using only Terraform's builtin resource, never a cloud provider."""
import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1] / "workloads"
spec = importlib.util.spec_from_file_location("workload_destroy", ROOT / "destroy.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def command(tool, root, args, stdin=None):
    profile = ('(version 1)(allow default)(deny network*)(deny file-write*)'
               '(allow file-write* (subpath ' + json.dumps(str(root)) + '))'
               '(allow file-write-data (literal "/dev/null"))')
    environment = {"PATH": "/usr/bin:/bin", "HOME": str(root), "TF_CLI_CONFIG_FILE": "/dev/null",
                   "TF_IN_AUTOMATION": "1", "TF_INPUT": "0", "CHECKPOINT_DISABLE": "1"}
    result = subprocess.run(["/usr/bin/sandbox-exec", "-p", profile, str(tool), *args], cwd=root,
                            env=environment, input=stdin, capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError("Builtin fixture failed: " + result.stderr.decode()[:2000])
    return result.stdout


def check(tool, cloud):
    now = datetime.now(timezone.utc)
    stamp = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory(prefix="w10-builtin-", dir="/private/tmp") as directory:
        root = Path(directory)
        if cloud == "aws":
            (root / "guard").mkdir(mode=0o700)
            (root / "guard/main.tf").write_bytes((d.WEEK / "application-pipelines/target/terraform/guard/main.tf").read_bytes())
            root = root / "root"
            root.mkdir(mode=0o700)
            (root / "main.tf").write_text('variable "approval" {}\nmodule "guard" {\n'
                ' source = "../guard"\n assignment = "week10-a2"\n name_prefix = "dmi-w10-a2-fixture"\n'
                ' controller_ipv4_cidr = "8.8.8.8/32"\n agent_ipv4_cidr = "1.1.1.1/32"\n approval = var.approval\n}\n')
            inputs = {"approval": {"live_execution_approved": True, "approved_at": stamp(now - timedelta(minutes=1)),
                                   "expires_at": stamp(now + timedelta(hours=1)), "estimated_total_usd": 1,
                                   "planning_allowance_usd": 10}}
        else:
            text = (d.WEEK / "self-hosted-agent/azure-vm/main.tf").read_text()
            guard = re.search(r'(?ms)^resource "terraform_data" "authorization" \{.*?^\}', text)
            if guard is None:
                raise ValueError("Missing exact builtin guard")
            text = guard.group().replace("data.azurerm_client_config.current", "local.identity")
            (root / "main.tf").write_text(text)
            inputs = {"subscription_id": "00000000-0000-0000-0000-000000000001",
                      "tenant_id": "00000000-0000-0000-0000-000000000002",
                      "operator_object_id": "00000000-0000-0000-0000-000000000003",
                      "live_execution_approved": True, "expires_at": stamp(now + timedelta(hours=1))}
            variables = set(re.findall(r"var\.([a-z0-9_]+)", text))
            if variables != set(inputs):
                raise ValueError("Guard input contract changed")
            (root / "fixture.tf.json").write_text(json.dumps({
                "variable": {name: {} for name in variables},
                "locals": {"identity": {"subscription_id": inputs["subscription_id"], "tenant_id": inputs["tenant_id"],
                                        "object_id": inputs["operator_object_id"]}}}))
        path = root / "case.auto.tfvars.json"
        path.write_text(json.dumps(inputs))
        command(tool, root, ["init", "-backend=false", "-input=false"])
        if cloud == "aws":
            modules = json.loads((root / ".terraform/modules/modules.json").read_text())
            expected = {"Modules": [{"Key": "", "Source": "", "Dir": "."},
                                    {"Key": "guard", "Source": "../guard", "Dir": "../guard"}]}
            if modules != expected:
                raise ValueError("Native module cache differs from executor contract")
        command(tool, root, ["apply", "-input=false", "-auto-approve"])
        if cloud == "aws":
            inputs["approval"].update(live_execution_approved=False, approved_at="2000-01-01T00:00:00Z",
                                      expires_at="2000-01-01T01:00:00Z")
        else:
            inputs.update(live_execution_approved=False, expires_at="2000-01-01T01:00:00Z",
                          operator_object_id="00000000-0000-0000-0000-000000000004")
        path.write_text(json.dumps(inputs))
        command(tool, root, ["plan", "-destroy", "-input=false", "-out=fixture.tfplan"])
        plan = json.loads(command(tool, root, ["show", "-json", "fixture.tfplan"]))
        changes = plan["resource_changes"]
        if len(changes) != 1 or changes[0]["address"] != d.GUARD[cloud] or changes[0]["change"]["actions"] != ["delete"]:
            raise ValueError("Unexpected builtin changes")
        d.validate_checks(plan.get("checks", []), cloud, {d.GUARD[cloud]})
        command(tool, root, ["apply", "-input=false", "fixture.tfplan"])
        state = json.loads(command(tool, root, ["state", "pull"]))
        if any(resource["mode"] == "managed" for resource in state.get("resources", [])):
            raise ValueError("Builtin state not empty")
        return {"cloud_guard": cloud, "expired_creation_approval_allows_destroy": True,
                "builtin_resources_deleted": 1, "cloud_providers_used": False}


def override_check(tool):
    with tempfile.TemporaryDirectory(prefix="w10-override-", dir="/private/tmp") as directory:
        root = Path(directory)
        for cloud in d.GUARD:
            command(tool, root, ["fmt", "-check", "-"], (ROOT / (cloud + ".backend.tf.example")).read_bytes())
        (root / "main.tf").write_text('terraform {\n backend "local" {}\n}\n')
        (root / "backend_override.tf").write_bytes((ROOT / "aws.backend.tf.example").read_bytes())
        command(tool, root, ["init", "-backend=false", "-input=false"])
        result = json.loads(command(tool, root, ["validate", "-json"]))
        if not result["valid"] or result["error_count"] or result["warning_count"]:
            raise ValueError("Backend override fixture invalid")
        return {"backend_type_override_parsed": True, "backend_initialized": False, "templates_format_checked": 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform", required=True, type=Path)
    args = parser.parse_args()
    tool = args.terraform.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="w10-version-", dir="/private/tmp") as directory:
        if json.loads(command(tool, Path(directory), ["version", "-json"]))["terraform_version"] != "1.13.5":
            raise ValueError("Terraform 1.13.5 required; no download fallback")
    print(json.dumps({"guards": [check(tool, cloud) for cloud in d.GUARD], "override": override_check(tool),
                      "external_network_denied": True, "workload_cleanup_ready": False}, sort_keys=True))


if __name__ == "__main__":
    main()
