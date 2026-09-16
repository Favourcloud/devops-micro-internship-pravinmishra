"""Small offline regression checks for the rubric, evidence and private input contract."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT.parent / "assignment-01-create-an-azure-virtual-machine-using-terraform.md"


class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "main.tf").read_text()
        cls.variables = (ROOT / "variables.tf").read_text()
        cls.manifest = json.loads((ROOT / "evidence/manifest.json").read_text())

    def test_original_rubric_preserved_byte_for_byte(self):
        original = BRIEF.read_bytes()[:5672]
        self.assertEqual(hashlib.sha256(original).hexdigest(), "23ec7be7267e6cc02c29afadb4b3bdefc730843b7a583ca0eea5c82381bcb787")
        self.assertEqual(len(re.findall(rb"^#### Screenshot \d+", original, re.M)), 11)

    def test_all_eleven_evidence_slots_are_explicitly_pending(self):
        slots = self.manifest["screenshots"]
        self.assertEqual([slot["number"] for slot in slots], list(range(1, 12)))
        for slot in slots:
            self.assertEqual(slot["status"], "pending")
            self.assertIsNone(slot["artifact"])
            self.assertIsNone(slot["captured_at"])

    def test_no_runtime_or_approval_claim(self):
        self.assertEqual(self.manifest["phase"], "offline-ready-runtime-pending")
        self.assertEqual(self.manifest["cloud_authorization"], "not-granted-for-this-run")
        self.assertFalse(self.manifest["live_deployment_performed"])
        self.assertIsNone(self.manifest["vm_public_ip"])
        self.assertFalse(self.manifest["assignment_complete"])

    def test_state_and_secret_paths_are_ignored(self):
        paths = [".private/terraform.tfstate", ".private/approved.tfvars", ".private/azure/token", ".terraform/plugins/cache", "terraform.tfstate.backup", "review.tfplan", "local.auto.tfvars", ".env", "private.key", "crash.log"]
        result = subprocess.run(["git", "check-ignore", "--stdin"], cwd=ROOT, input="\n".join(paths) + "\n", text=True, capture_output=True, check=True)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_sensitive_external_password_contract(self):
        block = self.variables.split('variable "admin_password" {', 1)[1]
        self.assertIn("sensitive   = true", block)
        self.assertNotRegex(block, r"\bdefault\s*=")
        self.assertIn("admin_password                  = var.admin_password", self.main)
        self.assertNotRegex((ROOT / "terraform.tfvars.example").read_text(), r"(?m)^\s*admin_password\s*=")
        for name in ("location", "vm_size", "controller_ipv4_cidr"):
            block = self.variables.split(f'variable "{name}" {{', 1)[1].split('\nvariable "', 1)[0]
            self.assertNotRegex(block, r"\bdefault\s*=")

    def test_provider_registration_disabled_and_no_live_helpers(self):
        self.assertIn('resource_provider_registrations = "none"', self.main)
        self.assertNotRegex(self.main, r'\b(data|provisioner)\s+"')
        self.assertNotRegex(self.main, r"\b(subscription_id|tenant_id|client_id|client_secret)\s*=")
        self.assertIn('version = "= 4.47.0"', self.main)
        self.assertIn('required_version = "~> 1.13.5"', self.main)

    def test_private_backend_and_nsg_before_vm(self):
        self.assertIn('path = ".private/terraform.tfstate"', self.main)
        self.assertIn("depends_on = [azurerm_network_interface_security_group_association.vm]", self.main)
        self.assertIn("delete_os_disk_on_deletion = true", self.main)

    def test_only_safe_outputs(self):
        self.assertEqual(re.findall(r'output "([^"]+)"', self.main), ["public_ip_address", "resource_group_name", "vm_name"])
        self.assertEqual(len(re.findall(r'^resource "', self.main, re.M)), 8)

    def test_mock_is_required_and_no_literal_password_fixture(self):
        source = (ROOT / "tests/vm.tftest.hcl").read_text()
        self.assertIn('mock_provider "azurerm"', source)
        self.assertNotRegex(source, r'(?m)^\s*provider "')
        self.assertNotRegex(source, r'admin_password\s*=\s*"[^$\"]+"')

    def test_no_private_artifacts_in_publishable_file_list(self):
        result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", "."], cwd=ROOT, text=True, capture_output=True, check=True)
        for name in result.stdout.splitlines():
            self.assertNotRegex(name, r"(^|/)(\.private|\.terraform)/|\.tfstate|\.tfplan|\.tfvars$|\.log$|\.(pem|key)$")

    def test_relative_markdown_links_resolve(self):
        for file in (ROOT / "README.md", BRIEF):
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", file.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((file.parent / target.split("#", 1)[0]).exists(), f"Broken link in {file.name}: {target}")


if __name__ == "__main__":
    unittest.main()
