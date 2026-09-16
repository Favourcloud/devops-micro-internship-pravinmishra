"""Small offline regression checks for the rubric, evidence and private input contract."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT.parent / "assignment-01-create-an-azure-virtual-machine-using-terraform.md"
REFERENCE_COMMIT = "faa96981d6edb4cb3fd67c56a98864f222d59da7"
SOURCE_COMMIT = "dbdab95b21f517cfe0751d07e667001c0fb6a775"
MAIN_SHA256 = "53a5a0f92c56d81437a66210af7cc4ed9f362604cca90b6ebf22b22f756405db"
EVIDENCE = {
    1: ("screenshot-01-terraform-version.png", "74b9d503afc2358ed99bf744e6ad85bdc96e7b201402e350e62f8599a8828302", "2026-09-16T23:16:55.898946+00:00"),
    2: ("screenshot-02-azure-cli-version.png", "eab34f1d807225ad3d708ae879c22dc2854e5de7b696affbf8cb717fdec057e4", "2026-09-16T23:17:27.854821+00:00"),
    3: ("screenshot-03-vscode-terraform-extension.png", "e28bef4bb2c24b3c848f8eb8d18709c275707444efb0a6933987a495b90fa316", "2026-09-16T23:17:43.782880+00:00"),
    4: ("screenshot-04-provider-resource-group.png", "c55e65fdb6d57bc019a35c75f76194e64446636cf9aec033dd8a67f412f864da", "2026-09-16T23:18:40.961449+00:00"),
    5: ("screenshot-05-vm-public-ip-source.png", "a868ba9d1d7c44dd6381d1d1381281da39c47994cc6e21cb0e24130682a52262", "2026-09-16T23:19:01.779340+00:00"),
    6: ("screenshot-06-terraform-init.png", "25c14486cf7e12c6280a37007d5b8bba309ee3ed810d7f51fa6e2dac3468233b", "2026-09-16T23:29:53.340580+00:00"),
}


class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "main.tf").read_text()
        cls.variables = (ROOT / "variables.tf").read_text()
        cls.manifest = json.loads((ROOT / "evidence/manifest.json").read_text())
        cls.original = subprocess.check_output([
            "git", "show", f"{REFERENCE_COMMIT}:week-08-terraform/{BRIEF.name}"
        ], cwd=ROOT)

    def test_original_rubric_requirements_preserved_with_completed_responses(self):
        reference = self.manifest["original_rubric"]
        self.assertEqual(reference["base_commit"], REFERENCE_COMMIT)
        self.assertEqual(len(self.original), reference["original_bytes"])
        self.assertEqual(reference["original_bytes"], 5672)
        self.assertEqual(hashlib.sha256(self.original).hexdigest(), reference["original_sha256"])
        self.assertEqual(reference["original_sha256"], "23ec7be7267e6cc02c29afadb4b3bdefc730843b7a583ca0eea5c82381bcb787")
        self.assertNotIn("preserved_prefix_bytes", reference)

        def requirement(line):
            line = re.sub(r"^- \[[ xX]\] ", "- ", line.strip())
            if line.startswith("VM Public IP Address:"):
                return "VM Public IP Address:"
            return line

        original = self.original.decode()
        current = BRIEF.read_text()
        remaining = iter(requirement(line) for line in current.splitlines())
        for line in original.splitlines():
            if not line.strip() or line == "Add your screenshot here.":
                continue
            expected = requirement(line)
            self.assertTrue(any(candidate == expected for candidate in remaining), f"Missing or reordered rubric requirement: {expected}")
        self.assertEqual(re.findall(r"^#### Screenshot .+$", current, re.M), re.findall(r"^#### Screenshot .+$", original, re.M))
        self.assertNotIn("Add your screenshot here.", current)
        self.assertNotIn("[Enter the public IP", current)

    def test_six_original_images_verified_and_five_slots_pending(self):
        slots = self.manifest["screenshots"]
        self.assertEqual([slot["number"] for slot in slots], list(range(1, 12)))
        self.assertEqual(self.manifest["evidence_summary"], {"verified": 6, "pending": 5, "required": 11})
        for slot in slots:
            number = slot["number"]
            if number in EVIDENCE:
                name, digest, captured_at = EVIDENCE[number]
                self.assertEqual(slot["status"], "verified")
                self.assertEqual(slot["artifact"], f"screenshots/{name}")
                self.assertEqual(slot["captured_at"], captured_at)
                self.assertEqual(slot["sha256"], digest)
                self.assertFalse(slot["image_modified"])
                data = (ROOT / "evidence" / slot["artifact"]).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            else:
                self.assertEqual(slot["status"], "pending")
                self.assertIsNone(slot["artifact"])
                self.assertIsNone(slot["captured_at"])
                self.assertIsNone(slot.get("sha256"))

    def test_no_runtime_or_approval_claim(self):
        self.assertEqual(self.manifest["phase"], "offline-ready-partial-evidence-runtime-pending")
        self.assertEqual(self.manifest["cloud_authorization"], "not-granted-for-this-run")
        self.assertFalse(self.manifest["live_deployment_performed"])
        self.assertIsNone(self.manifest["vm_public_ip"])
        self.assertFalse(self.manifest["assignment_complete"])
        self.assertIn("VM Public IP Address: Pending", BRIEF.read_text())

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

    def test_frozen_source_and_capture_binding(self):
        for name in ("main.tf", "variables.tf", ".terraform.lock.hcl", "terraform.tfvars.example", "tests/run_offline.py", "tests/vm.tftest.hcl"):
            original = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:week-08-terraform/terraform-azure-vm/{name}"], cwd=ROOT)
            self.assertEqual((ROOT / name).read_bytes(), original, f"Frozen source changed: {name}")
        self.assertEqual(hashlib.sha256((ROOT / "main.tf").read_bytes()).hexdigest(), MAIN_SHA256)
        self.assertEqual(self.manifest["source_provenance"], {
            "path": "../main.tf", "commit": SOURCE_COMMIT, "sha256": MAIN_SHA256, "bound_screenshot_numbers": [4, 5, 6]
        })
        for slot in self.manifest["screenshots"][3:6]:
            self.assertEqual(slot["source_commit"], SOURCE_COMMIT)
            self.assertEqual(slot["source_sha256"], MAIN_SHA256)

    def test_numbered_images_and_submission_identity(self):
        current = BRIEF.read_text()
        sections = re.findall(r"^#### Screenshot (\d+)[^\n]*\n(.*?)(?=^#### Screenshot |\Z)", current, re.M | re.S)
        self.assertEqual([int(number) for number, _ in sections], list(range(1, 12)))
        for number, section in sections:
            number = int(number)
            images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", section)
            if number in EVIDENCE:
                self.assertEqual(images, [f"terraform-azure-vm/evidence/screenshots/{EVIDENCE[number][0]}"])
                self.assertIn("**Verified", section)
            else:
                self.assertEqual(images, [])
                self.assertIn("**Pending:", section)
        for file in (BRIEF, ROOT / "README.md"):
            text = file.read_text()
            self.assertIn("**Learner:** Eze Favour", text)
            self.assertIn("6/11", text)
            self.assertIn("https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/favourcloud-week-08-azure-vm/week-08-terraform/terraform-azure-vm", text)
            self.assertIn("https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/9", text)
            self.assertIn("not manual learner execution", text)

    def test_only_verified_local_checklist_items_checked(self):
        def checklist(text):
            return text.split("# Completion Checklist\n", 1)[1].split("\n---", 1)[0]

        original_items = re.findall(r"^- (.+)$", checklist(self.original.decode()), re.M)
        current_items = re.findall(r"^- \[([ x])\] (.+)$", checklist(BRIEF.read_text()), re.M)
        self.assertEqual([text for _, text in current_items], original_items)
        checked = [index for index, (marker, _) in enumerate(current_items, 1) if marker == "x"]
        self.assertEqual(checked, [1, 2, 5, 6, 7, 8, 9, 10, 11])

    def test_public_provenance_excludes_private_capture_material(self):
        self.assertEqual(self.manifest["schema_version"], 2)
        capture = self.manifest["capture_provenance"]
        self.assertEqual(capture["operator"], "GitHub Copilot under user delegation; not manual learner execution")
        self.assertTrue(capture["privacy_checked"])
        slots = self.manifest["screenshots"]
        self.assertEqual(slots[0]["tools"], {"terraform": "1.13.5", "platform": "darwin_amd64"})
        self.assertEqual(slots[1]["tools"], {"azure_cli": "2.89.1"})
        self.assertEqual(slots[2]["tools"], {"extension_id": "hashicorp.terraform", "extension_version": "2.40.0"})
        self.assertTrue(slots[2]["extension_installed_and_enabled"])
        init = slots[5]
        self.assertEqual(init["tools"], {"terraform": "1.13.5", "azurerm": "4.47.0"})
        self.assertEqual(init["timestamp_basis"], "Original macOS PNG filesystem creation time")
        self.assertEqual(init["operator"], capture["operator"])
        self.assertTrue(init["privacy_checked"])
        self.assertEqual(init["command"], 'terraform init -input=false -lockfile=readonly -plugin-dir="$PROVIDER_MIRROR"')
        self.assertIn("normal initialization of the configured local backend", init["boundary"])
        self.assertIn("no Azure provider configuration", init["boundary"])
        validation = self.manifest["evidence_validation"]
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(validation["delivery_tests_passed"], 15)
        self.assertEqual(validation["original_png_hashes_verified"], 6)
        self.assertFalse(validation["terraform_rerun"])
        serialized = json.dumps(self.manifest)
        self.assertNotRegex(serialized, r"/(Users|home)/|\.ocr\.txt|integration-input\.json")
        self.assertNotRegex(serialized, r'"(window|pid|window_id|bounds|raw_ocr|private_path|capture_path)"\s*:')
        expected = {"manifest.json"} | {f"screenshots/{record[0]}" for record in EVIDENCE.values()}
        actual = {path.relative_to(ROOT / "evidence").as_posix() for path in (ROOT / "evidence").rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)

    def test_relative_markdown_links_resolve(self):
        for file in (ROOT / "README.md", BRIEF):
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", file.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((file.parent / target.split("#", 1)[0]).exists(), f"Broken link in {file.name}: {target}")


if __name__ == "__main__":
    unittest.main()
