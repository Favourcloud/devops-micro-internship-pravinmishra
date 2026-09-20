"""Credential-free checks for the explicitly unpublished social draft."""

import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit


WEEK = Path(__file__).resolve().parents[2]


class LinkedInProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status = json.loads((WEEK / "evidence/linkedin-progress.json").read_text())
        cls.raw = (WEEK / cls.status["draft_path"]).read_bytes()
        cls.text = cls.raw.decode("utf-8")

    def test_metadata_is_allowlisted_and_explicitly_unpublished(self):
        self.assertEqual(set(self.status), {
            "schema_version", "learner", "request_date_utc", "publication_status",
            "publication_authorized", "draft_path", "draft_sha256", "draft_basis",
            "account_verified", "post_submitted", "publication_verified",
            "public_post_url", "screenshot_path", "counts_as_assignment_evidence",
            "assignment_specific_linkedin_requirements_met", "blocker",
        })
        self.assertEqual(self.status["schema_version"], 1)
        self.assertEqual(self.status["learner"], "Eze Favour")
        self.assertEqual(self.status["request_date_utc"], "2026-09-19")
        self.assertEqual(self.status["publication_status"], "blocked_private_sign_in")
        self.assertIs(self.status["publication_authorized"], True)
        for flag in ("account_verified", "post_submitted", "publication_verified",
                     "counts_as_assignment_evidence", "assignment_specific_linkedin_requirements_met"):
            self.assertIs(self.status[flag], False, flag)
        self.assertIsNone(self.status["public_post_url"])
        self.assertIsNone(self.status["screenshot_path"])
        self.assertIn("No post was submitted", self.status["blocker"])

    def test_draft_bytes_are_bound_and_ready_for_manual_review(self):
        self.assertEqual(self.status["draft_path"], "submission/linkedin-progress-draft.txt")
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), self.status["draft_sha256"])
        self.assertTrue(self.text.endswith("\n"))
        self.assertLessEqual(len(self.text), 3000)
        self.assertNotRegex(self.text, r"\[(?:TODO|Paste|Enter)|<placeholder>")
        self.assertIn("Pravin Mishra", self.text)
        self.assertIn("CloudAdvisory", self.text)

    def test_draft_claims_match_existing_operational_receipts(self):
        basis = self.status["draft_basis"]
        self.assertEqual(set(basis), {
            "source_commit", "a1_receipt", "static_source_receipt",
            "local_validation_checkpoint_tests", "local_validation_checkpoint_date_utc",
        })
        self.assertEqual(basis["source_commit"], "459cc1a8d2f79038ca64f5fb6c2ed4745268e17a")
        trial = json.loads((WEEK / basis["a1_receipt"]).read_text())
        uploaded = json.loads((WEEK / basis["static_source_receipt"]).read_text())
        self.assertEqual(trial["manual_run"]["result"], "succeeded")
        for command in trial["manual_run"]["commands_verified"]:
            self.assertIn(command, self.text)
        for flag in ("vm_absent", "agent_absent", "terraform_state_empty"):
            self.assertIs(trial["cleanup"][flag], True)
        self.assertIs(uploaded["outcome"]["pipeline_source_uploaded_and_read_back"], True)
        self.assertIs(uploaded["outcome"]["application_deployed"], False)
        self.assertEqual(basis["local_validation_checkpoint_tests"], 338)
        self.assertEqual(basis["local_validation_checkpoint_date_utc"], "2026-09-19")
        self.assertRegex((WEEK / "evidence/README.md").read_text(), r"\b338\b")

    def test_draft_does_not_invent_live_completion_or_learner_reflections(self):
        for phrase in (
            "historical evidence, not a currently running lab",
            "not live deployment acceptance tests", "workflow is planned",
            "are still pending", "Week 10 is not complete",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)\bI (?:deployed|configured|learned|completed|ran|fixed)\b")
        self.assertNotIn("@Pravin", self.text)

    def test_draft_adds_no_screenshot_or_completed_assignment(self):
        current = json.loads((WEEK / "evidence/current.json").read_text())
        self.assertEqual(current["numbered_captured"], 10)
        self.assertEqual(current["numbered_missing"], 26)
        self.assertEqual(current["raw_images"], 13)
        self.assertIs(current["separate_linkedin_image_captured"], False)
        self.assertIs(current["assignment_completion_claimed"], False)
        self.assertIs(current["human_visual_review_verified"], False)
        self.assertEqual(len(list((WEEK / "screenshots").glob("*.png"))), 13)

    def test_only_the_public_repository_url_is_in_the_draft(self):
        urls = re.findall(r"https?://\S+", self.text)
        self.assertEqual(urls, [
            "https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/main/week-10-azure-devops"
        ])
        for url in urls:
            parsed = urlsplit(url)
            self.assertEqual(parsed.scheme, "https")
            self.assertFalse(parsed.query)
            self.assertIsNone(parsed.username)
        for marker in ("/Users/", "dev.azure.com", "management.azure.com", "ssh-rsa", "PRIVATE KEY", "Bearer ", "Basic "):
            self.assertNotIn(marker, self.text)
        self.assertNotRegex(self.text, r"[\w.+-]+@[\w.-]+\.\w+")

    def test_checker_links_and_preserved_capture_count_are_clear(self):
        for path in ("README.md", "SUBMISSION.md"):
            document = (WEEK / path).read_text()
            self.assertIn("submission/linkedin-progress-draft.txt", document)
            self.assertIn("evidence/linkedin-progress.json", document)
            self.assertIn("**not published**", document)
            self.assertIn("does not satisfy A2", document)
        readme = (WEEK / "README.md").read_text()
        self.assertIn("## Assignment status", readme)
        self.assertIn("nine explicitly allowlisted image substitutions", readme)
        blocks = sum(len(re.findall(rb"<!-- BEGIN WEEK10 CAPTURE ", path.read_bytes()))
                     for path in WEEK.glob("assignment-*.md"))
        self.assertEqual(blocks, 10)


if __name__ == "__main__":
    unittest.main()
