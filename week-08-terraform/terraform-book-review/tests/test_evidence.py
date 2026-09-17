"""Offline checks for source and original local-editor evidence, never cloud proof."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT.parent / "assignment-05-deploy-book-review-app-in-your-favorite-cloud-agentic-terraform-project.md"
SOURCE_COMMIT = "23748110108196f26c1394830a48af5317f7ca22"
ORIGINALS = {
    1: ("e52b793ea08e9cbede1948028e4528fb0589b741e5be8e9b4734898b290e88f9", 1001847, "2026-09-17T03:02:07.231982+00:00"),
    2: ("9812b3ec6a95e43ab65819269b1b9da536758a7c75d0614f326214b6e13b62fc", 689323, "2026-09-17T03:05:19.736326+00:00"),
    3: ("0f9638042f33e67f06a91606b8553c150504a37cff07add4cbc67d98ec8ee646", 696174, "2026-09-17T03:09:58.865036+00:00"),
    6: ("eb9928185dbb1923ecb88f54b2687e4993abfcdf62c12cb9b5e88a108711f026", 789571, "2026-09-17T03:10:54.828839+00:00"),
}
CAPTURE_BLOCK = re.compile(r"\n<!-- A5 source capture (1|2|3|6) -->\n.*?\n<!-- /A5 source capture -->\n", re.S)


class EvidenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = ASSIGNMENT.read_text()
        cls.manifest = json.loads((ROOT / "evidence/manifest.json").read_text())
        cls.captures = [item for item in cls.manifest["screenshots"] if item["status"] == "captured_source_only"]

    def test_all_28_exact_titles_and_order(self):
        expected = [(int(number), title) for number, title in re.findall(r"^### Screenshot (\d+) — (.+)$", self.brief, re.M)]
        actual = [(item["slot"], item["title"]) for item in self.manifest["screenshots"]]
        self.assertEqual(list(range(1, 29)), [slot for slot, _ in actual])
        self.assertEqual(expected, actual)

    def test_only_four_accepted_original_captures(self):
        self.assertEqual([1, 2, 3, 6], [item["slot"] for item in self.captures])
        self.assertEqual({"accepted_source_only": 4, "missing": 24, "total": 28}, self.manifest["screenshot_progress"])
        self.assertEqual(4, len({item["path"] for item in self.captures}))
        self.assertEqual(4, len({item["sha256"] for item in self.captures}))
        for item in self.manifest["screenshots"]:
            if item["slot"] not in ORIGINALS:
                self.assertEqual("pending", item["status"])
                self.assertIsNone(item["path"])

    def test_original_png_integrity_dimensions_and_timestamps(self):
        expected_paths = set()
        for item in self.captures:
            with self.subTest(slot=item["slot"]):
                relative = Path(item["path"])
                self.assertEqual("screenshots", relative.parent.as_posix())
                self.assertEqual(".png", relative.suffix)
                path = ROOT / "evidence" / relative
                self.assertFalse(path.is_symlink())
                data = path.read_bytes()
                expected_hash, expected_bytes, expected_timestamp = ORIGINALS[item["slot"]]
                self.assertEqual(expected_timestamp, item["captured_at_utc"])
                self.assertEqual(expected_hash, hashlib.sha256(data).hexdigest())
                self.assertEqual(expected_hash, item["sha256"])
                self.assertEqual(expected_bytes, len(data))
                self.assertEqual(expected_bytes, item["bytes"])
                self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
                self.assertEqual(b"IHDR", data[12:16])
                self.assertEqual((3584, 2000), struct.unpack(">II", data[16:24]))
                self.assertEqual([3584, 2000], item["dimensions"])
                offset, last_kind = 8, None
                while offset < len(data):
                    length = int.from_bytes(data[offset:offset + 4], "big")
                    kind = data[offset + 4:offset + 8]
                    self.assertLessEqual(offset + length + 12, len(data))
                    payload = data[offset + 8:offset + 8 + length]
                    self.assertEqual(zlib.crc32(kind + payload), int.from_bytes(data[offset + 8 + length:offset + 12 + length], "big"))
                    offset, last_kind = offset + length + 12, kind
                self.assertEqual((len(data), b"IEND"), (offset, last_kind))
                captured = datetime.fromisoformat(item["captured_at_utc"])
                self.assertEqual(timezone.utc.utcoffset(captured), captured.utcoffset())
                self.assertEqual("2026-09-17", captured.date().isoformat())
                expected_paths.add(path)
        self.assertEqual(expected_paths, set((ROOT / "evidence/screenshots").iterdir()))
        self.assertEqual(3176915, sum(item["bytes"] for item in self.captures))

    def test_reviewed_source_anchor_and_only_four_source_exceptions(self):
        self.assertEqual(SOURCE_COMMIT, self.manifest["captured_source_commit"])
        self.assertEqual("reviewed-source.json", self.manifest["reviewed_source_record"])
        source = json.loads((ROOT / "evidence/reviewed-source.json").read_text())
        self.assertEqual(SOURCE_COMMIT, source["source_commit"])
        hashes = source["source_sha256"]
        digest = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual("3dbb41138a2f776e054e2ba74f8f47f135bd5138fa4fa2234265b51cae933e39", digest)
        self.assertEqual(digest, source["canonical_source_hash_map_sha256"])
        self.assertEqual(63, len(hashes))
        exceptions = {"README.md", "evidence/manifest.json", "evidence/offline-validation.json", "tests/test_evidence.py"}
        self.assertEqual(exceptions, set(source["permitted_evidence_exceptions"]))
        actual_exceptions = set()
        for name, expected in hashes.items():
            path = ROOT / name
            self.assertFalse(path.is_symlink())
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                actual_exceptions.add(name)
        self.assertEqual(exceptions, actual_exceptions)
        trust = json.loads((ROOT / ".claude/trusted-files.json").read_text())
        self.assertFalse(exceptions & set(trust["files"]))
        for item in self.captures:
            self.assertEqual(SOURCE_COMMIT, item["source_commit"])

    def test_pending_local_capture_and_separate_gates_are_disjoint(self):
        local = self.manifest["local_capture_blocked_slots"]
        gated = self.manifest["separately_gated_slots"]
        self.assertEqual([7, 8, 14, 15, 16, 17], local)
        self.assertEqual([4, 5, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28], gated)
        self.assertEqual(list(range(1, 29)), sorted(list(ORIGINALS) + local + gated))
        self.assertIn("unreadable", self.manifest["capture_blocker"])
        self.assertIn("not inherently cloud", self.manifest["capture_blocker"])

    def test_capture_provenance_and_slot_six_are_not_runtime_or_agent_proof(self):
        provenance = self.manifest["capture_provenance"]
        for field in ("image_pixels_modified", "manual_learner_execution", "provided_kit_demonstrated",
                      "claude_execution_demonstrated", "human_cloud_change_approved", "gui_terminal_validation_screenshot_produced"):
            self.assertIs(provenance[field], False)
        self.assertIn("Copilot under user delegation", provenance["operator"])
        self.assertIn("not OS-network-sandboxed", provenance["environment"])
        modules = {path.name for path in (ROOT / "terraform/modules").iterdir() if path.is_dir()}
        self.assertEqual({"compute", "database", "identity", "initializer", "load_balancing", "network", "observability", "secrets", "security"}, modules)
        self.assertEqual(12, len(re.findall(r'^module "', (ROOT / "terraform/main.tf").read_text(), re.M)))
        structure = next(item for item in self.captures if item["slot"] == 6)
        self.assertIn("nine actual module directories", structure["caption"])
        self.assertIn("Twelve is the root module-call count", structure["caption"])
        self.assertIn("NOT counted as slot 7", structure["acceptance_note"])
        self.assertIn("initially captured while framing network source", structure["acceptance_note"])

    def test_four_brief_embeds_preserve_snapshot_and_captions(self):
        self.assertEqual(["1", "2", "3", "6"], CAPTURE_BLOCK.findall(self.brief))
        for item in self.captures:
            block = next(match.group(0) for match in CAPTURE_BLOCK.finditer(self.brief) if int(match.group(1)) == item["slot"])
            section = self.brief.split(f'### Screenshot {item["slot"]} — ', 1)[1].split("\n---", 1)[0]
            self.assertIn(block.strip(), section)
            self.assertIn(f'(terraform-book-review/evidence/{item["path"]})', block)
            self.assertIn(item["caption"], block)
            self.assertIn(SOURCE_COMMIT, block)
            if "acceptance_note" in item:
                self.assertIn(item["acceptance_note"], block)

    def test_validation_record_separates_original_captures_from_cli(self):
        record = json.loads((ROOT / "evidence/offline-validation.json").read_text())
        self.assertEqual(SOURCE_COMMIT, record["source_validation_commit"])
        self.assertEqual(149, record["python"]["normal_tests_passed"])
        self.assertEqual(149, record["python"]["optimized_tests_passed"])
        self.assertEqual(43, record["terraform"]["mock_tests_passed"])
        self.assertEqual([1, 2, 3, 6], record["evidence_integration"]["accepted_original_slots"])
        self.assertFalse(record["evidence_integration"]["gui_terminal_validation_screenshot_produced"])
        self.assertFalse(record["evidence_integration"]["new_dependency_installation"])
        validation = record["evidence_integration"]["validation"]
        self.assertEqual(21, validation["focused_evidence_and_integration_tests_passed"])
        self.assertEqual(155, validation["normal_tests_passed"])
        self.assertEqual(155, validation["optimized_tests_passed"])
        self.assertEqual((0, 0), (validation["tests_failed"], validation["tests_skipped"]))
        self.assertTrue(validation["dependency_directory_writes_denied"])
        self.assertEqual("all_network_denied", validation["process_network_isolation"])
        self.assertEqual(43, validation["protected_terraform_runner"]["mock_tests_passed"])
        self.assertTrue(validation["protected_terraform_runner"]["source_and_trust_manifest_unchanged"])
        self.assertEqual((63, 59), (validation["source_preservation"]["reviewed_project_files"],
                                  validation["source_preservation"]["byte_identical_project_files"]))
        self.assertEqual(4, record["preserved_requirements"]["captures"])
        self.assertEqual(24, record["preserved_requirements"]["pending_screenshot_slots"])
        self.assertEqual(15, record["preserved_requirements"]["unanswered_reflections"])
        self.assertEqual(55, record["preserved_requirements"]["unchecked_final_requirements"])

    def test_no_completion_or_cloud_claim(self):
        self.assertIs(self.manifest["assignment_complete"], False)
        self.assertIs(self.manifest["cloud_verified"], False)
        self.assertIsNone(self.manifest["public_url"])

    def test_all_reflections_remain_learner_work(self):
        section = self.brief.split("# Task 9 — Answer the Reflection Questions", 1)[1].split("# Task 10", 1)[0]
        self.assertEqual(15, len(re.findall(r"^### \d+\.", section, re.M)))
        self.assertEqual({"required": 15, "answered": 0, "status": "pending_learner"}, self.manifest["own_words_reflections"])

    def test_all_55_checklist_entries_retained_unchecked(self):
        self.assertEqual(55, len(re.findall(r"^- \[ \] ", self.brief, re.M)))
        self.assertNotRegex(self.brief, r"(?m)^- \[[xX]\]")

    def test_publication_is_required_and_pending(self):
        self.assertEqual({"required": True, "status": "pending", "url": None}, self.manifest["linkedin_publication"])

    def test_missing_kit_and_unexecuted_workflow_are_honest(self):
        self.assertFalse(self.manifest["instructor_starter_kit"]["found_in_pinned_upstream"])
        self.assertEqual("pending_not_executed", self.manifest["claude_mcp_workflow"])

    def test_policy_contains_concrete_screenshot_one_architecture_context(self):
        policy = (ROOT / "CLAUDE.md").read_text()
        context = policy.split("## Architecture context", 1)[1].split("## Scope and authority", 1)[0]
        for requirement in ("six subnets in two AZs", "Four baseline", "public ALB443", "Web80",
                            "loopback3000", "private ALB80", "App3001", "Router6446", "MySQL3306",
                            "Multi-AZ primary", "distinct asynchronous read replica", "no internet default route",
                            "No SSH", "separate least-privilege identity", "disabled by default", "1.13.5/AWS6.64.0",
                            "write-only", "Not free-tier", "release remains blocked", "human-reviewed real plan",
                            "Copilot-authored inactive draft pending the provided kit"):
            self.assertIn(requirement, context)

    def test_manifest_contains_no_local_account_or_secret_artifacts(self):
        for name in ("manifest.json", "reviewed-source.json", "offline-validation.json", "README.md"):
            text = (ROOT / "evidence" / name).read_text()
            self.assertNotRegex(text, r"/Users/|/tmp/|\.review-data/|arn:aws:|AKIA[A-Z0-9]{16}|BEGIN .*PRIVATE KEY")
        self.assertEqual("manifest_directory", self.manifest["image_path_base"])
        for path in (ROOT / "evidence").rglob("*"):
            self.assertFalse(path.is_symlink())
            self.assertNotIn(path.suffix, {".log", ".txt"})
            self.assertFalse(path.name.endswith(".png.json"))

    def test_entire_original_brief_preserved_except_explicit_additions(self):
        restored = self.brief.replace("**Full Name:** Eze Favour  ", "**Full Name:** Add your full name here  ")
        restored = restored.replace("**Cloud Platform:** AWS — coordinator-selected offline architecture assumption; learner confirmation and cloud-change approval remain pending  ", "**Cloud Platform:** AWS or Azure  ")
        restored = restored.replace("**GitHub Repository URL:** https://github.com/Favourcloud/devops-micro-internship-pravinmishra  ", "**GitHub Repository URL:** Add your repository URL here  ")
        restored = re.sub(r"\n> \*\*Preparation status — not a completed submission:\*\*[^\n]*\n", "", restored)
        restored = CAPTURE_BLOCK.sub("", restored)
        restored = restored.replace("The [completed source architecture diagram](terraform-book-review/README.md#architecture-created-before-infrastructure-source) was written before infrastructure source. It shows the two-AZ/six-subnet VPC, IGW and per-AZ NAT, public and internal load balancers, Web/App tiers, Multi-AZ MySQL and a separate read replica. It is a design artifact, **not evidence of deployed resources**.", "Add the completed architecture diagram here.")
        self.assertEqual("086e7fbc6c5dceaa07312b02b19e7ef1c1849d4d04dcc0c41ed9634faacb285b", hashlib.sha256(restored.encode()).hexdigest())

    def test_dependency_matches_are_not_release_clearance(self):
        advisories = json.loads((ROOT / "evidence/dependency-advisories.json").read_text())
        self.assertTrue(advisories["release_status"].startswith("blocked_"))
        self.assertFalse(advisories["application_javascript_modified"])
        windows = next(item for item in advisories["findings"] if item["id"] == "GHSA-p293-qw3h-jr36")
        self.assertIn("does not match", windows["applicability"])


if __name__ == "__main__":
    unittest.main()
