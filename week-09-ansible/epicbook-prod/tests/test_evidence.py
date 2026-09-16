from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import unittest


PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]


class SourceCaptureTests(unittest.TestCase):
    def test_original_capture_bytes_and_historical_or_current_sources(self):
        evidence = json.loads((PROJECT / "evidence/assignment-05-manifest.json").read_text())
        review = evidence["source_capture_review"]
        historical = set(review["historical_epicbook_slots"])
        self.assertEqual(historical, {"10a", "10b", "10c"})
        corrected = REPOSITORY / review["corrected_source_file"]
        self.assertEqual(hashlib.sha256(corrected.read_bytes()).hexdigest(), review["corrected_source_sha256"])
        historical_sources = {}
        manifest_text = (PROJECT / "evidence/source-captures.json").read_text()
        manifest = json.loads(manifest_text)
        self.assertNotIn("/Users/", manifest_text)
        self.assertEqual(
            {item["slot"] for item in manifest["items"]},
            {"6", "7", "8a", "8b", "8c", "8d", "10a", "10b", "10c", "11"},
        )
        self.assertEqual(len(manifest["items"]), 10)
        for item in manifest["items"]:
            with self.subTest(slot=item["slot"]):
                image = (PROJECT / "evidence" / item["image"]).resolve()
                source = (REPOSITORY / item["source_file"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence/images"))
                self.assertTrue(source.is_relative_to(PROJECT / "ansible"))
                raw = image.read_bytes()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(len(raw), item["image_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["image_sha256"])
                if item["slot"] in historical:
                    self.assertEqual(source, corrected)
                    self.assertNotEqual(hashlib.sha256(source.read_bytes()).hexdigest(), item["source_sha256"])
                    revision_path = item["source_commit"] + ":" + item["source_file"]
                    if revision_path not in historical_sources:
                        historical_sources[revision_path] = subprocess.run(
                            ["/usr/bin/git", "show", revision_path], cwd=REPOSITORY,
                            capture_output=True, check=True, timeout=10).stdout
                    recorded_source = historical_sources[revision_path]
                else:
                    recorded_source = source.read_bytes()
                self.assertEqual(hashlib.sha256(recorded_source).hexdigest(), item["source_sha256"])
                self.assertEqual(item["source_commit"], manifest["source_commit"])
                self.assertTrue(item["source_only"])
        evidence = json.loads((PROJECT / "evidence/assignment-05-manifest.json").read_text())
        self.assertEqual(
            {item["number"] for item in evidence["numbered_screenshots"]
             if item["status"] == "captured-source-only"},
            {1, 3, 6, 7, 8, 10, 11},
        )

    def test_corrected_source_captures_bind_working_tree_not_old_head(self):
        evidence = json.loads((PROJECT / "evidence/assignment-05-manifest.json").read_text())
        text = (PROJECT / "evidence" / evidence["corrected_source_capture_manifest"]).read_text()
        self.assertNotIn("/Users/", text)
        self.assertNotRegex(text, r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b")
        manifest = json.loads(text)
        source = (REPOSITORY / manifest["source_file"]).resolve()
        self.assertEqual(source, PROJECT / "ansible/roles/epicbook/tasks/main.yml")
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), manifest["source_sha256"])
        self.assertEqual(manifest["source_sha256"], evidence["source_capture_review"]["corrected_source_sha256"])
        self.assertEqual(manifest["snapshot_kind"], "working-tree")
        self.assertFalse(manifest["head_blob_matches_captured_source"])
        self.assertFalse(manifest["human_review_claimed"])
        self.assertTrue(manifest["historical_images_preserved"])
        old_source = subprocess.run(
            ["/usr/bin/git", "show", manifest["workspace_head_at_capture"] + ":" + manifest["source_file"]],
            cwd=REPOSITORY, capture_output=True, check=True, timeout=10).stdout
        self.assertNotEqual(hashlib.sha256(old_source).hexdigest(), manifest["source_sha256"])
        pilot = json.loads((PROJECT / "evidence/pilot-outcome.json").read_text())
        cleaned_at = datetime.fromisoformat(pilot["cleanup"]["additional_absence"]["verified_utc"])
        expected = {"10a": [1, 28], "10b": [30, 61], "10c": [63, 89]}
        self.assertEqual({item["slot"] for item in manifest["items"]}, set(expected))
        self.assertEqual(len(manifest["items"]), 3)
        for item in manifest["items"]:
            with self.subTest(slot=item["slot"]):
                image = (PROJECT / "evidence" / item["image"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence/images"))
                self.assertEqual(image.name, "screenshot-" + item["slot"] + "-corrected.png")
                raw = image.read_bytes()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(len(raw), item["image_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["image_sha256"])
                self.assertEqual(item["source_lines"], expected[item["slot"]])
                self.assertLessEqual(item["source_lines"][1], len(source.read_text().splitlines()))
                self.assertGreater(datetime.fromisoformat(item["captured_at_utc"]), cleaned_at)
                self.assertTrue(item["source_verified_before_and_after_capture"])
                self.assertTrue(item["source_only"])
                self.assertEqual(item["pixel_edits"], "none")
                self.assertRegex(item["private_capture_provenance_sha256"], r"^[0-9a-f]{64}$")
        slot = next(row for row in evidence["numbered_screenshots"] if row["number"] == 10)
        self.assertEqual(slot["images"], [item["image"] for item in manifest["items"]])
        self.assertTrue(set(slot["images"]).isdisjoint(slot["historical_images"]))

    def test_infrastructure_captures_and_historical_tree_scope(self):
        text = (PROJECT / "evidence/infrastructure-source-captures.json").read_text()
        self.assertNotIn("/Users/", text)
        manifest = json.loads(text)
        self.assertEqual({item["slot"] for item in manifest["items"]},
                         {"1a", "1b", "1c", "3a", "3b"})
        self.assertEqual(len(manifest["items"]), 5)
        tree = manifest["tree_at_capture"]
        self.assertEqual(tree["tracked_file_count"], 43)
        self.assertEqual(len(tree["source_hashes"]), 43)
        self.assertEqual(tree["source_commit"], "a15fc8c7c728d699fe1a0ae43177b8809f19eba7")
        for relative in tree["source_hashes"]:
            self.assertTrue((REPOSITORY / relative).is_relative_to(PROJECT))
        for item in manifest["items"]:
            with self.subTest(slot=item["slot"]):
                image = (PROJECT / "evidence" / item["image"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence/images"))
                raw = image.read_bytes()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(len(raw), item["image_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["image_sha256"])
                self.assertTrue(item["source_only"])
                if item["source_kind"] == "terraform-source":
                    source = (REPOSITORY / item["source_file"]).resolve()
                    self.assertTrue(source.is_relative_to(PROJECT / "terraform/azure"))
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     item["source_sha256"])
                else:
                    self.assertEqual(item["source_commit"], tree["source_commit"])

    def test_approved_live_capture_bytes_and_failure_scope(self):
        manifest = json.loads((PROJECT / "evidence/pilot-captures.json").read_text())
        pilot = json.loads((PROJECT / "evidence/pilot-outcome.json").read_text())
        expected = {"images/screenshot-2a.png": (2, pilot["terraform_apply"]),
                    "images/screenshot-2b.png": (2, pilot["outputs"]),
                    "images/screenshot-04.png": (4, pilot["readiness"]["ssh"]),
                    "images/deployment-failure.png": (None, pilot["deployment"])}
        self.assertEqual({item["image"] for item in manifest["items"]}, set(expected))
        for item in manifest["items"]:
            with self.subTest(image=item["image"]):
                image = (PROJECT / "evidence" / item["image"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence/images"))
                raw = image.read_bytes()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(len(raw), item["image_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["image_sha256"])
                slot, outcome = expected[item["image"]]
                self.assertEqual(item["slot"], slot)
                self.assertEqual(item["outcome_sha256"], outcome["outcome_sha256"])
                self.assertEqual(item["pilot_source_commit"], pilot["frozen_pilot_source_commit"])
                self.assertEqual(item["pixel_edits"], "none")

    def test_pilot_chronology_cleanup_and_unproven_runtime_stay_explicit(self):
        evidence = json.loads((PROJECT / "evidence/assignment-05-manifest.json").read_text())
        text = (PROJECT / "evidence/pilot-outcome.json").read_text()
        pilot = json.loads(text)
        for forbidden in ('/Users/', '/subscriptions/', '"argv"', '"environment"', '"state_path"', '"resource_id"'):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b")
        apply, deploy, cleanup = pilot["terraform_apply"], pilot["deployment"], pilot["cleanup"]
        self.assertEqual((apply["creates"], apply["updates"], apply["deletes"], apply["terraform_exit_code"]), (11, 0, 0, 0))
        self.assertEqual(deploy["ansible_exit_code"], 2)
        self.assertEqual(deploy["recap"]["web"]["failed"], 1)
        self.assertFalse(deploy["successful_runtime"])
        self.assertFalse(deploy["remote_second_run_performed"])
        self.assertFalse(pilot["post_cleanup_fix"]["redeployed"])
        self.assertEqual(pilot["post_cleanup_fix"]["source_sha256"], evidence["source_capture_review"]["corrected_source_sha256"])
        self.assertEqual((cleanup["plan"]["deletes"], cleanup["plan"]["creates"], cleanup["plan"]["updates"]), (11, 0, 0))
        self.assertEqual(cleanup["apply"]["terraform_exit_code"], 0)
        self.assertEqual(cleanup["apply"]["plan_sha256"], cleanup["plan"]["plan_sha256"])
        self.assertEqual(cleanup["apply"]["state_sha256"], cleanup["verify"]["state_sha256"])
        for field in ("empty_state", "empty_outputs", "authenticated_resource_group_absent"):
            self.assertTrue(cleanup["verify"][field])
        absence = cleanup["additional_absence"]
        self.assertEqual(absence["actual_get_count"], 3)
        self.assertEqual({row["resource_kind"] for row in absence["results"]}, {"vm", "os-disk", "public-ip"})
        for row in absence["results"]:
            self.assertEqual(row["status"], "absent")
            self.assertEqual(row["exit_code"], 3)
            self.assertIn(row["arm_error_code"], {"ResourceNotFound", "ResourceGroupNotFound"})
        timestamps = [apply["finished_utc"], pilot["outputs"]["finished_utc"]]
        timestamps += [pilot["readiness"][step]["finished_utc"] for step in ("trust", "ssh", "inventory", "ping")]
        timestamps += [deploy["finished_utc"], cleanup["plan"]["finished_utc"], cleanup["apply"]["finished_utc"],
                       cleanup["verify"]["finished_utc"], absence["verified_utc"], apply["cleanup_deadline_utc"]]
        parsed = [datetime.fromisoformat(value) for value in timestamps]
        self.assertTrue(all(left < right for left, right in zip(parsed, parsed[1:])))
        numbered = {item["number"]: item for item in evidence["numbered_screenshots"]}
        self.assertEqual(set(numbered), set(range(1, 16)))
        self.assertEqual({number for number, row in numbered.items() if row["status"] == "captured-live-pilot"}, {2, 4})
        for number in (5, 9, 12, 13, 14, 15):
            self.assertEqual(numbered[number]["status"], "pending")
        self.assertEqual(numbered[10]["status"], "captured-source-only")
        self.assertTrue(numbered[5]["execution_verified"])
        self.assertFalse(evidence["assignment_06_handoff"]["implemented_here"])


if __name__ == "__main__":
    unittest.main()
