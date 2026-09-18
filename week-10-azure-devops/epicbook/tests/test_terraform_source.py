import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "terraform"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load("offline_terraform", TF / "tests" / "run_offline.py")
HANDOFF = load("infra_handoff", ROOT / "ci" / "validate_handoff.py")


class TerraformSourceTests(unittest.TestCase):
    def test_explicit_source_selection_excludes_inputs_state_and_scripts(self):
        selected = {str(path.relative_to(TF)) for path in RUNNER.source_files(TF)}
        self.assertEqual(selected, {"versions.tf", "variables.tf", "guard.tf", "network.tf", "compute.tf",
                                    "database.tf", "outputs.tf", ".terraform.lock.hcl", "tests/offline.tftest.hcl"})

    def test_remote_backend_and_workload_identity(self):
        source = (TF / "versions.tf").read_text()
        self.assertIn('backend "azurerm"', source)
        self.assertIn("use_azuread_auth = true", source)
        self.assertRegex(source, r"use_oidc\s*=\s*true")
        self.assertRegex(source, r"use_cli\s*=\s*false")
        self.assertRegex(source, r"use_msi\s*=\s*false")
        self.assertNotIn('backend "local"', source)
        self.assertNotRegex(source, r"\b(access_key|sas_token|client_secret)\s*=")
        self.assertIn('version = "= 4.47.0"', source)

    def test_password_ephemeral_and_write_only(self):
        variables = (TF / "variables.tf").read_text()
        password = variables.split('variable "mysql_admin_password"', 1)[1].split('variable "mysql_password_version"', 1)[0]
        self.assertRegex(password, r"sensitive\s*=\s*true")
        self.assertRegex(password, r"ephemeral\s*=\s*true")
        database = (TF / "database.tf").read_text()
        self.assertRegex(database, r"administrator_password_wo\s*=\s*var.mysql_admin_password")
        self.assertNotRegex(database, r"\badministrator_password\s*=")
        self.assertNotIn("mysql_admin_password", (TF / "guard.tf").read_text())

    def test_no_runtime_bootstrap_or_external_data(self):
        source = "\n".join(path.read_text() for path in TF.glob("*.tf"))
        for forbidden in ('provisioner "', 'data "external"', 'data "http"', 'local-exec', 'remote-exec',
                          'custom_data', 'user_data', 'templatefile(', 'file(', 'filebase64('):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_exact_allowlisted_outputs(self):
        source = (TF / "outputs.tf").read_text()
        names = re.findall(r'^output "([a-z_]+)"', source, re.M)
        self.assertEqual(set(names), HANDOFF.FIELDS)
        self.assertEqual(len(names), 4)
        self.assertNotRegex(source, r"password|subscription_id|tenant_id|object_id|connection_string")

    def test_mock_output_contract_matches_existing_handoff(self):
        # These are fixtures, never contacted or claimed as owned resources.
        data = {"app_public_ip": "8.8.4.4", "backend_ansible_host": "8.8.8.8",
                "backend_private_ip": "10.140.2.4", "mysql_fqdn": "fixture-mysql.mysql.database.azure.com"}
        self.assertEqual(HANDOFF.validate_handoff(data), data)
        inventory = HANDOFF.inventory(data)
        self.assertEqual(inventory["all"]["vars"]["backend_private_ip"], "10.140.2.4")

    def test_example_is_unapproved_and_unusable(self):
        example = json.loads((TF / "inputs.example.tfvars.json").read_text())
        self.assertTrue(all(value is None for key, value in example.items() if key != "approval"))
        approval = example["approval"]
        self.assertEqual(approval["scope"], "week10-a4-two-vms-private-mysql")
        for key in ("live_execution_approved", "remote_state_ready", "cleanup_safeguard_ready"):
            self.assertIs(approval[key], False)
        for key in ("approved_at", "expires_at", "estimated_total_usd", "planning_allowance_usd"):
            self.assertIsNone(approval[key])
        self.assertNotIn("mysql_admin_password", example)

    def test_approval_and_cleanup_are_not_inherited(self):
        variables = (TF / "variables.tf").read_text()
        self.assertIn('var.approval.scope == "week10-a4-two-vms-private-mysql"', variables)
        self.assertEqual(variables.count("optional(bool, false)"), 3)
        guard = (TF / "guard.tf").read_text()
        self.assertIn('timeadd(var.approval.approved_at, "24h")', guard)
        self.assertIn('timeadd(timestamp(), "2h")', guard)
        self.assertIn('"2027-02-01T00:00:00Z"', guard)

    def test_mock_fixtures_never_apply(self):
        source = (TF / "tests" / "offline.tftest.hcl").read_text()
        self.assertEqual(len(re.findall(r'^run "', source, re.M)), 30)
        self.assertEqual(re.findall(r"\bcommand\s*=\s*(\w+)", source), ["plan"] * 30)
        self.assertIn('mock_provider "azurerm"', source)
        self.assertIn("TEST-ONLY-not-a-live-secret", source)

    def test_environment_does_not_inherit_credentials_or_home(self):
        environment = RUNNER.environment_for(Path("/private/tmp/synthetic"))
        self.assertEqual(set(environment), {"PATH", "HOME", "TMPDIR", "TF_CLI_CONFIG_FILE", "TF_DATA_DIR",
                                            "CHECKPOINT_DISABLE", "TF_IN_AUTOMATION", "TF_INPUT"})
        self.assertEqual(environment["HOME"], "/nonexistent")
        self.assertEqual(environment["TF_CLI_CONFIG_FILE"], "/dev/null")
        self.assertFalse(any(key.startswith(("ARM_", "AWS_", "AZURE_", "TF_VAR_")) for key in environment))

    def test_sandbox_denies_external_network_and_outside_writes(self):
        profile = RUNNER.profile_for(Path("/private/tmp/synthetic"))
        self.assertIn("(deny network*)", profile)
        self.assertIn("(allow network* (local unix-socket))", profile)
        self.assertIn("(deny file-write*)", profile)
        self.assertIn('(subpath "/private/tmp/synthetic")', profile)
        self.assertNotIn("ip", profile)

    def test_runner_does_not_initialize_remote_backend_or_install(self):
        source = (TF / "tests" / "run_offline.py").read_text()
        for flag in ('"-backend=false"', '"-get=false"', '"-lockfile=readonly"', '"-plugin-dir="'):
            self.assertIn(flag, source)
        for tool in ("pip install", "npm install", "terraform apply", "terraform destroy", "shell=True"):
            self.assertNotIn(tool, source)

    def test_unsupported_platform_fails_closed(self):
        with patch.object(RUNNER.sys, "platform", "linux"), patch.object(RUNNER.subprocess, "run") as execute:
            with self.assertRaises(ValueError):
                RUNNER.check(Path("/not-used"), Path("/not-used"))
            execute.assert_not_called()

    def test_apply_fixture_rejected_before_execution(self):
        fixture = 'mock_provider "azurerm" {}\nrun "unsafe" {\ncommand = apply\n}\n'
        with patch.object(Path, "read_text", return_value=fixture), patch.object(RUNNER.subprocess, "run") as execute:
            with self.assertRaises(ValueError):
                RUNNER.source_files(TF)
            execute.assert_not_called()

    def test_private_files_ignored(self):
        ignored = (TF / ".gitignore").read_text().splitlines()
        for pattern in (".terraform/", ".private/", "*.tfvars", "*.tfvars.json", "backend.hcl"):
            self.assertIn(pattern, ignored)
        self.assertIn("!*.example.tfvars.json", ignored)


if __name__ == "__main__":
    unittest.main()
