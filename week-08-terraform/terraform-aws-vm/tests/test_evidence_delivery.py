"""Historical and live evidence integrity; no Terraform, AWS, GUI or bootstrap execution."""

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import unittest
import zlib

import test_contract


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
BRIEF = test_contract.BRIEF
SOURCE_HEAD = "ded8bf1b44fe0e76fb0d9a36b40d795aab46e4b4"
FROZEN_FILES = {
    "main.tf", ".terraform.lock.hcl", "terraform.tfvars.example", "scripts/cloud-init.sh",
    "scripts/check-offline.sh", "scripts/check-cleanup.py", "tests/offline.tftest.hcl",
}
ORIGINAL_HASHES = {
    1: "9266633c48e844ad579fb3cae0ac057a4deb41dece2e990e966b145094fe0c99",
    2: "944ddc9006baaab8547718d05210f5cab5ac3520d78f3f3cd2b9e2b1034ec4ab",
    3: "8d408535a6a787afa1cfc6e4749ee1726753e109b5cac6c33603b338d6f92481",
    4: "ce60e6dee0a4065c8737dfaace3dc9e2d9fa7c31f5789dfd5ee74386973ac22a",
}
LINUX_PROVIDER_HASH = "h1:2fTLxzUDmp/KVIHbIeLTB4bIzWHx8E6Dw+1ALLUi+Yw="
LIVE_SOURCE_HEAD = "40771b24f19ea79a0fe5061790f2c0836e71d770"


def source_bytes(path):
    return subprocess.check_output(["git", "show", f"{SOURCE_HEAD}:{path.relative_to(REPO)}"], cwd=REPO)


class EvidenceDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.provenance = json.loads((PROJECT / "evidence/capture-provenance.json").read_text())
        self.live = json.loads((PROJECT / "evidence/live-capture-provenance.json").read_text())
        self.manifest = json.loads((PROJECT / "evidence/manifest.json").read_text())
        self.validation = json.loads((PROJECT / "evidence/local-validation.json").read_text())
        self.brief = BRIEF.read_text()

    def test_receipt_source_head_and_all_seven_frozen_paths(self):
        self.assertEqual(self.provenance["source_head"], SOURCE_HEAD)
        self.assertEqual(set(self.provenance["source_hashes"]), FROZEN_FILES)
        self.assertEqual(self.validation["evidence_integration"]["source_head"], SOURCE_HEAD)
        self.assertEqual(self.validation["evidence_integration"]["frozen_source_files"], 7)

    def test_source_history_preserved_with_only_verified_linux_lock_addition(self):
        for name, expected in self.provenance["source_hashes"].items():
            with self.subTest(file=name):
                path = PROJECT / name
                original = source_bytes(path)
                self.assertEqual(hashlib.sha256(original).hexdigest(), expected)
                current = path.read_bytes()
                if name == ".terraform.lock.hcl":
                    added_line = f'    "{LINUX_PROVIDER_HASH}",\n'.encode()
                    self.assertEqual(current.count(added_line), 1)
                    self.assertEqual(current.replace(added_line, b""), original)
                else:
                    self.assertEqual(current, original)
                self.assertEqual(hashlib.sha256(current).hexdigest(), self.live["source_hashes"][name])
        self.assertEqual(self.live["source_commit"], LIVE_SOURCE_HEAD)
        self.assertEqual(self.live["linux_provider_hash_added"], LINUX_PROVIDER_HASH)
        self.assertEqual(self.live["aws_provider_version"], "6.64.0")

    def test_original_png_byte_hashes_match_independent_receipt_constants(self):
        for shot in self.provenance["screenshots"]:
            with self.subTest(number=shot["number"]):
                expected = ORIGINAL_HASHES[shot["number"]]
                self.assertEqual(shot["sha256"], expected)
                self.assertEqual(hashlib.sha256((PROJECT / shot["file"]).read_bytes()).hexdigest(), expected)
                self.assertFalse(shot["image_modified"])

    def test_png_structure_dimensions_and_chunk_checksums(self):
        for shot in self.provenance["screenshots"] + self.live["screenshots"]:
            with self.subTest(number=shot["number"]):
                data = (PROJECT / shot["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), shot["sha256"])
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                offset, chunks = 8, []
                while offset < len(data):
                    length = struct.unpack(">I", data[offset:offset + 4])[0]
                    kind = data[offset + 4:offset + 8]
                    payload = data[offset + 8:offset + 8 + length]
                    crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
                    self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, crc)
                    chunks.append(kind)
                    if kind == b"IHDR":
                        width, height = struct.unpack(">II", payload[:8])
                        expected = (3584, 2006) if shot["number"] <= 4 else (1280, 720 if shot["number"] == 9 else 630)
                        self.assertEqual((width, height), expected)
                        self.assertEqual((width, height), (shot["width_px"], shot["height_px"]))
                    offset += 12 + length
                self.assertEqual(offset, len(data))
                self.assertEqual(chunks[0], b"IHDR")
                self.assertEqual(chunks[-1], b"IEND")
                self.assertIn(b"IDAT", chunks)

    def test_capture_times_operator_and_local_only_scope(self):
        verified = datetime.fromisoformat(self.provenance["receipt_verified_at_utc"])
        self.assertEqual(verified.utcoffset(), timedelta(0))
        self.assertEqual(self.provenance["operator"], "GitHub Copilot under user delegation; not manual learner execution")
        self.assertEqual(self.provenance["window_title"], "Eze Favour — Week 08 Assignment 2")
        for shot in self.provenance["screenshots"]:
            captured = datetime.fromisoformat(shot["captured_at_utc"])
            self.assertEqual(captured.utcoffset(), timedelta(0))
            self.assertLessEqual(captured, verified)
            self.assertIn("not AWS runtime evidence", shot["scope"])
            self.assertTrue(shot["privacy_checked_by_capture_session"])

    def test_manifest_counts_paths_hashes_and_labels_match_provenance(self):
        captured = [shot for shot in self.manifest["screenshots"] if shot["status"] == "captured"]
        self.assertEqual([shot["number"] for shot in captured], list(range(1, 11)))
        self.assertEqual(self.manifest["captured_count"], len(captured))
        self.assertEqual(self.manifest["required_count"], 10)
        self.assertEqual(self.manifest["pending_slots"], [])
        self.assertEqual(len(self.manifest["screenshots"]), 10)
        self.assertEqual([shot["number"] for shot in self.provenance["screenshots"]], [1, 2, 3, 4])
        self.assertEqual(self.provenance["pending_slots"], [5, 6, 7, 8, 9, 10])
        self.assertEqual((PROJECT / self.manifest["provenance"]).name, "capture-provenance.json")
        self.assertEqual([shot["number"] for shot in self.live["screenshots"]], list(range(5, 11)))
        self.assertEqual((PROJECT / self.manifest["live_provenance"]).name, "live-capture-provenance.json")
        for shot, original in zip(captured, self.provenance["screenshots"] + self.live["screenshots"]):
            for key in ("number", "file", "sha256", "captured_at_utc"):
                self.assertEqual(shot[key], original[key])
            section = self.brief.split("#### " + shot["requirement"], 1)[1].split("\n---", 1)[0]
            self.assertIn(f'![{original["label"]}](terraform-aws-vm/{original["file"]})', section)
            self.assertNotIn("Add your screenshot here.", section)

    def test_exactly_ten_images_from_historical_and_live_provenance(self):
        expected = {shot["file"] for shot in self.provenance["screenshots"] + self.live["screenshots"]}
        actual = {str(path.relative_to(PROJECT)) for path in (PROJECT / "evidence").rglob("*")
                  if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp")}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 10)

    def test_all_ordered_rubric_requirements_and_ten_titles_survive(self):
        self.assertTrue(test_contract.protected_requirements_present(self.brief))
        self.assertEqual(re.findall(r"^#### Screenshot .+$", self.brief, re.M), test_contract.SOURCE["screenshot_headings"])
        test_contract.AssignmentContractTests().test_source_metadata_matches_baseline()

    def test_rubric_protection_allows_actual_answers_images_and_checkmarks(self):
        future = self.brief.replace("Add your screenshot here.", "![Later genuine capture](evidence/future.png)")
        future = future.replace("`Pending — no authorized live deployment`", "`198.51.100.20`")
        future = future.replace("* [ ]", "* [x]")
        self.assertTrue(test_contract.protected_requirements_present(future))

    def test_rubric_protection_rejects_removed_requirement(self):
        removed = self.brief.replace("* Public subnet route table association\n", "")
        self.assertFalse(test_contract.protected_requirements_present(removed))

    def test_live_lifecycle_records_verification_cleanup_and_retired_ip(self):
        self.assertIn("**EC2 Public IP Address:** `3.80.169.89`", self.brief)
        self.assertIn("retired after verified teardown", self.brief)
        self.assertNotIn("Add your screenshot here.", self.brief)
        for requirement in (
            "Configured AWS CLI and verified account access", "Confirmed the correct AWS Region",
            "Reviewed the Terraform execution plan using `terraform plan`", "Completed `terraform apply` successfully",
            "Captured and recorded the EC2 public IP using `terraform output`", "Verified Nginx access through the EC2 public IP",
            "Completed `terraform destroy` successfully", "Captured all 10 required screenshots",
        ):
            self.assertIn(f"* [x] {requirement}", self.brief)
        # The old receipt is deliberately not rewritten to claim a later run.
        for key in ("cloud_actions_authorized", "cloud_execution_verified", "assignment_complete"):
            self.assertFalse(self.provenance[key])
        self.assertTrue(self.manifest["cloud_execution_verified"])
        self.assertTrue(self.live["cloud_execution_verified"])
        self.assertTrue(self.live["authorization"]["user_approved"])
        self.assertEqual(self.live["plan"], {"add": 11, "change": 0, "destroy": 0})
        self.assertEqual(self.live["apply"]["added"], 11)
        self.assertEqual(self.live["apply"]["changed"], 0)
        self.assertEqual(self.live["apply"]["destroyed"], 0)
        cleanup = self.live["cleanup"]
        self.assertEqual(cleanup["destroyed_resources"], 11)
        self.assertEqual(cleanup["exact_id_checks_passed"], 13)
        self.assertEqual(cleanup["exact_id_checks_exit_code"], 0)
        self.assertEqual(cleanup["remaining_state_resources"], 0)
        expected_addresses = {
            "aws_instance.web", "aws_internet_gateway.lab", "aws_key_pair.lab", "aws_route_table.private",
            "aws_route_table.public", "aws_route_table_association.private", "aws_route_table_association.public",
            "aws_security_group.web", "aws_subnet.private", "aws_subnet.public", "aws_vpc.lab", "primary_eni", "root_volume",
        }
        self.assertEqual(set(cleanup["checked_addresses"]), expected_addresses)
        self.assertEqual(len(cleanup["checked_addresses"]), 13)
        start = datetime.fromisoformat(self.live["apply"]["started_at_utc"])
        finish = datetime.fromisoformat(cleanup["completed_at_utc"])
        self.assertGreater(finish, start)
        self.assertLess(finish - start, timedelta(minutes=self.live["authorization"]["maximum_minutes"]))
        for shot in self.live["screenshots"]:
            captured = datetime.fromisoformat(shot["captured_at_utc"])
            self.assertEqual(captured.utcoffset(), timedelta(0))
            if shot["number"] == 5:
                self.assertLess(captured, start)
            elif shot["number"] == 10:
                self.assertGreater(captured, finish)
            else:
                self.assertLess(start, captured)
                self.assertLess(captured, finish)
            self.assertEqual(shot["crop_box_xywh"], None if shot["number"] == 9 else [0, 55, 1280, 630])
            self.assertEqual(shot["original_format"], "JPEG")
            self.assertEqual(shot["published_format"], "PNG")
            self.assertTrue(shot["privacy_checked"])
        self.assertTrue(self.live["outputs"]["address_retired_after_teardown"])
        self.assertFalse(self.live["cost"]["actual_bill_verified"])
        self.assertTrue(self.live["verification"]["ssh_strict_host_checking"])
        self.assertTrue(self.live["verification"]["aws_matches_terraform_instance_and_ip"])
        self.assertEqual(self.live["verification"]["browser_tab_url"], self.live["outputs"]["website_url"])

    def test_normal_init_is_distinct_local_backend_evidence(self):
        init = self.provenance["normal_init"]
        self.assertEqual(init["command"], "terraform init -input=false -lockfile=readonly")
        self.assertEqual(init["backend_type"], "local")
        self.assertEqual(init["backend_target"], ".private/terraform.tfstate")
        self.assertEqual(init["aws_provider_version"], "6.64.0")
        self.assertFalse(init["managed_resource_state_exists"])
        self.assertTrue(init["filesystem_only_provider_mirror"])
        for guard in ("env -i", "empty authentication", "metadata disabled", "startup environment guard"):
            self.assertIn(guard, init["environment"])
        self.assertIn("* [x] Completed `terraform init` successfully", self.brief)
        self.assertIn("* [x] Installed AWS CLI and verified it using `aws --version`", self.brief)

    def test_documentation_states_ten_captures_and_delegated_execution(self):
        for text in (self.brief, (PROJECT / "README.md").read_text()):
            self.assertIn("10 of 10", text)
            self.assertIn("5–10", text)
            self.assertIn("not manual learner execution", text)
            self.assertIn("capture-provenance.json", text)
            self.assertIn("live-capture-provenance.json", text)
            self.assertIn("Eze Favour", text)
            self.assertNotIn("All ten screenshot slots below remain", text)
            self.assertNotIn("All ten screenshots remain pending", text)
            self.assertNotIn("runtime tasks remain unverified", text)
        self.assertIn("SOURCE", self.manifest["screenshots"][2]["note"])
        self.assertIn("no HCL or image modification", self.manifest["screenshots"][1]["note"])

    def test_historical_validation_is_preserved_separately_from_delivery(self):
        original = json.loads(source_bytes(PROJECT / "evidence/local-validation.json"))
        self.assertEqual(self.validation["checks"], original["checks"])
        self.assertEqual(self.validation["validated_at_utc"], original["validated_at_utc"])
        self.assertEqual(self.validation["validated_source_head"], SOURCE_HEAD)
        self.assertEqual(self.validation["checks"][0]["mock_runs_passed"], 25)
        self.assertEqual(self.validation["checks"][1]["tests_passed"], 28)
        integration = self.validation["evidence_integration"]
        focused = integration["checks"][0]
        self.assertEqual(focused["command"], "python3 -B -m unittest discover -s tests -p 'test_evidence_delivery.py' -v")
        self.assertEqual(focused["tests_passed"], 18)  # Historical September 17 run.
        self.assertEqual(focused["tests_failed"], 0)
        self.assertGreater(datetime.fromisoformat(integration["validated_at_utc"]), datetime.fromisoformat(self.provenance["receipt_verified_at_utc"]))
        self.assertEqual(integration["local_originals_integrated"], 4)
        self.assertEqual(integration["pending_screenshot_slots"], [5, 6, 7, 8, 9, 10])
        self.assertFalse(integration["native_mock_tests_reexecuted"])
        self.assertFalse(integration["terraform_commands_executed_by_integration_session"])
        self.assertEqual(integration["aws_api_calls_by_integration_session"], 0)
        self.assertEqual(integration["new_screenshots_captured_by_integration_session"], 0)
        self.assertFalse(integration["png_bytes_modified"])

    def test_public_provenance_has_only_sanitized_fields(self):
        self.assertEqual(set(self.provenance), {
            "schema_version", "assignment", "learner", "source_head", "receipt_verified_at_utc", "operator",
            "capture_method", "window_title", "source_hashes", "screenshots", "normal_init", "cloud_actions_authorized",
            "cloud_execution_verified", "assignment_complete", "pending_slots", "notes",
        })
        for shot in self.provenance["screenshots"]:
            self.assertEqual(set(shot), {"number", "file", "label", "captured_at_utc", "sha256", "width_px", "height_px",
                                         "image_modified", "privacy_checked_by_capture_session", "scope"})
        self.assertEqual(set(self.provenance["normal_init"]), {
            "screenshot_number", "command", "backend_type", "backend_target", "managed_resource_state_exists",
            "filesystem_only_provider_mirror", "aws_provider_version", "environment", "verification_source",
        })
        self.assertEqual(self.live["operator"], "Codex under user delegation; not manual learner execution")
        serialized = json.dumps([self.provenance, self.live])
        for private_fragment in ("/Users/", ".review-data/", "integration-input.json", "expected_visible_text", '"pid"', '"bounds"'):
            self.assertNotIn(private_fragment, serialized)

    def test_evidence_only_diff_excludes_runtime_and_private_artifacts(self):
        prefix = str(PROJECT.relative_to(REPO)) + "/"
        allowed = {str(BRIEF.relative_to(REPO))} | {prefix + path for path in (
            "README.md", "evidence/manifest.json", "evidence/local-validation.json", "evidence/capture-provenance.json",
            "tests/test_evidence_delivery.py", ".terraform.lock.hcl", "evidence/live-capture-provenance.json",
            "evidence/live-run-summary.md", "evidence/live-validation.json",
            *(shot["file"] for shot in self.provenance["screenshots"] + self.live["screenshots"]),
        )}
        scope = [str(BRIEF.relative_to(REPO)), str(PROJECT.relative_to(REPO))]
        changed = set(subprocess.check_output(["git", "diff", "--name-only", SOURCE_HEAD, "--", *scope], cwd=REPO, text=True).splitlines())
        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--", *scope], cwd=REPO, text=True).splitlines())
        self.assertTrue(changed | untracked <= allowed, sorted((changed | untracked) - allowed))
        tracked = subprocess.check_output(["git", "ls-files", "--cached", "--", *scope], cwd=REPO, text=True).splitlines()
        for name in tracked:
            self.assertFalse({".private", ".terraform", ".offline"} & set(Path(name).parts))
        if (PROJECT / ".private").exists():
            self.assertEqual((PROJECT / ".private").stat().st_mode & 0o077, 0)

    def test_existing_markdown_link_and_manifest_contracts_accept_images(self):
        contracts = test_contract.AssignmentContractTests()
        contracts.test_markdown_links_local_files_and_external_syntax()
        contracts.test_ten_original_screenshot_headings_and_manifest()

    def test_publishable_text_privacy_and_private_artifact_ignores(self):
        contracts = test_contract.AssignmentContractTests()
        contracts.test_owned_publishable_files_have_no_secret_material()
        contracts.test_private_artifact_ignores()


if __name__ == "__main__":
    unittest.main()
