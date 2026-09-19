"""Read-only consistency checks for the dated, explicitly partial submission."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import unittest


WEEK = Path(__file__).resolve().parents[2]
SNAPSHOT = WEEK / "submission" / "status.json"


class SubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        cls.assignments = cls.snapshot["assignments"]

    def test_snapshot_is_partial_and_source_validation_is_consistent(self):
        self.assertEqual(self.snapshot["schema_version"], 1)
        self.assertEqual(self.snapshot["learner"], "Eze Favour")
        self.assertEqual(self.snapshot["date_utc"], "2026-09-19")
        self.assertEqual(self.snapshot["status"], "partial_submission")
        self.assertIs(self.snapshot["week_complete"], False)
        self.assertIs(self.snapshot["cloud_operations_during_packaging"], False)
        self.assertRegex(self.snapshot["baseline_commit"], r"^[0-9a-f]{40}$")
        checks = self.snapshot["local_validation"]
        self.assertIs(checks["credentials_used"], False)
        self.assertIs(checks["network_denied"], True)
        self.assertIs(checks["ordinary_file_writes_denied"], True)
        self.assertEqual(checks["discard_only_write_exception"], "/dev/null")
        self.assertIs(checks["native_terraform_suites_rerun"], False)
        self.assertEqual(checks["total_passed"], sum(s["passed"] for s in checks["suites"]))
        self.assertEqual(len({s["path"] for s in checks["suites"]}), len(checks["suites"]))
        for suite in checks["suites"]:
            self.assertGreater(suite["passed"], 0)
            self.assertTrue((WEEK / suite["path"]).is_dir())

    def test_all_five_published_briefs_are_byte_preserved(self):
        self.assertEqual([a["number"] for a in self.assignments], [1, 2, 3, 4, 5])
        self.assertEqual(
            {a["brief"] for a in self.assignments},
            {path.name for path in WEEK.glob("assignment-*.md")},
        )
        for assignment in self.assignments:
            with self.subTest(assignment=assignment["number"]):
                raw = (WEEK / assignment["brief"]).read_bytes()
                raw = re.sub(rb"<!-- BEGIN WEEK10 CAPTURE (A1-S1|A1-S7|A2-S1) -->\n.*?<!-- END WEEK10 CAPTURE \1 -->\n\n", b"", raw, flags=re.S)
                actual = hashlib.sha256(raw).hexdigest()
                self.assertEqual(actual, assignment["brief_sha256"])
                self.assertIs(assignment["assignment_complete"], False)
                self.assertEqual(assignment["learner_notes"], "pending")
                self.assertTrue(assignment["remaining"])

    def test_a1_status_matches_historical_trial_not_screenshot_completion(self):
        assignment = self.assignments[0]
        receipt = json.loads((WEEK / assignment["receipts"][0]).read_text(encoding="utf-8"))
        self.assertEqual(assignment["status"], receipt["status"])
        self.assertEqual(receipt["manual_run"]["result"], "succeeded")
        self.assertEqual(receipt["manual_run"]["commands_verified"], ["uname -a", "whoami", "df -h"])
        self.assertEqual(receipt["manual_run"]["whoami"], "azdoagent")
        self.assertIs(receipt["agent_trial"]["online_verified_during_trial"], True)
        for flag in ("terraform_state_empty", "vm_absent", "agent_absent"):
            self.assertIs(receipt["cleanup"][flag], True)
        self.assertIs(receipt["authorization"]["retired"], True)
        self.assertIs(receipt["authorization"]["authorizes_future_runtime"], False)
        self.assertEqual(receipt["submission"]["original_checklist_items_checked"], 0)
        self.assertEqual(receipt["submission"]["required_checklist_items"], 8)
        self.assertIs(receipt["submission"]["assignment_complete"], False)
        report = (WEEK / "SUBMISSION.md").read_text(encoding="utf-8")
        for key in ("run_url", "source_commit", "task_log_sha256"):
            self.assertIn(receipt["manual_run"][key], report)

    def test_a2_receipts_do_not_claim_deployment(self):
        imported, uploaded = [
            json.loads((WEEK / path).read_text(encoding="utf-8"))
            for path in self.assignments[1]["receipts"]
        ]
        self.assertIs(imported["outcome"]["repository_imported"], True)
        self.assertIs(imported["outcome"]["personalization_committed_and_read_back"], True)
        self.assertIs(uploaded["outcome"]["pipeline_source_uploaded_and_read_back"], True)
        self.assertEqual(uploaded["repository"]["parent_commit"], imported["static_repository"]["personalized_commit"])
        for receipt in (imported, uploaded):
            for flag in ("assignment_complete", "application_deployed", "application_pipeline_run"):
                self.assertIs(receipt["outcome"][flag], False)
            self.assertIs(receipt["assignment_evidence"], False)
        self.assertEqual(uploaded["execution_gate"]["application_pipeline_definition_count"], 0)
        self.assertEqual(uploaded["execution_gate"]["application_build_count"], 0)
        self.assertIs(uploaded["execution_gate"]["ssh_connection_id_is_unset_placeholder"], True)
        report = (WEEK / "SUBMISSION.md").read_text(encoding="utf-8")
        self.assertIn(imported["static_repository"]["personalized_commit"], report)
        self.assertIn(uploaded["repository"]["prepared_commit"], report)

    def test_zero_image_snapshot_precedes_later_genuine_captures(self):
        self.assertEqual([a["numbered_screenshots_required"] for a in self.assignments], [7, 5, 6, 6, 12])
        summary = self.snapshot["screenshots"]
        self.assertEqual(summary["numbered_required"], sum(a["numbered_screenshots_required"] for a in self.assignments))
        self.assertEqual(summary["numbered_captured"], 0)
        self.assertEqual(summary["separate_linkedin_image_required"], 1)
        self.assertEqual(summary["separate_linkedin_image_captured"], 0)
        self.assertEqual(summary["status"], "pending")
        for assignment in self.assignments:
            self.assertEqual(assignment["numbered_screenshots_captured"], 0)
        evidence = json.loads((WEEK / "self-hosted-agent/evidence/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(evidence["screenshots"]), 7)
        self.assertIs(evidence["live_verified"], False)
        captured = [slot for slot in evidence["screenshots"] if slot["captured"]]
        self.assertEqual([slot["slot"] for slot in captured], [1, 7])
        for slot in captured:
            self.assertEqual(slot["status"], "captured_review_pending")
            self.assertGreater(datetime.fromisoformat(slot["captured_at"]), datetime.fromisoformat("2026-09-19T08:15:30+00:00"))

    def test_deliverable_paths_and_report_links_are_local_and_exist(self):
        for assignment in self.assignments:
            for relative in [assignment["brief"], assignment["source"], *assignment["receipts"]]:
                self.assertNotIn("..", Path(relative).parts)
                self.assertFalse(Path(relative).is_absolute())
                self.assertTrue((WEEK / relative).is_file())
        report = (WEEK / "SUBMISSION.md").read_text(encoding="utf-8")
        self.assertIn("Partial submission", report)
        self.assertIn("not a new live inventory", report)
        self.assertIn("0/36 numbered screenshots", report)
        for destination in re.findall(r"\]\(([^)]+)\)", report):
            if destination.startswith("https://"):
                continue
            self.assertNotIn("..", Path(destination).parts)
            self.assertFalse(Path(destination).is_absolute())
            self.assertTrue((WEEK / destination.split("#", 1)[0]).is_file(), destination)
        self.assertIn("SUBMISSION.md", (WEEK / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
