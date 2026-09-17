"""Source-only acceptance checks; never browser/cloud evidence."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT.parent / "assignment-05-deploy-book-review-app-in-your-favorite-cloud-agentic-terraform-project.md"


class EvidenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = ASSIGNMENT.read_text()
        cls.manifest = json.loads((ROOT / "evidence/manifest.json").read_text())

    def test_all_28_exact_titles_and_order(self):
        expected = [(int(number), title) for number, title in re.findall(r"^### Screenshot (\d+) — (.+)$", self.brief, re.M)]
        actual = [(item["slot"], item["title"]) for item in self.manifest["screenshots"]]
        self.assertEqual(list(range(1, 29)), [slot for slot, _ in actual])
        self.assertEqual(expected, actual)

    def test_no_fabricated_capture(self):
        self.assertTrue(all(item["status"] == "pending" and item["path"] is None for item in self.manifest["screenshots"]))

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

    def test_manifest_contains_no_local_account_or_secret_artifacts(self):
        text = json.dumps(self.manifest)
        self.assertNotRegex(text, r"/Users/|/tmp/|arn:aws:|AKIA[A-Z0-9]{16}|BEGIN .*PRIVATE KEY")

    def test_entire_original_brief_preserved_except_explicit_additions(self):
        restored = self.brief.replace("**Full Name:** Eze Favour  ", "**Full Name:** Add your full name here  ")
        restored = restored.replace("**Cloud Platform:** AWS — coordinator-selected offline architecture assumption; learner confirmation and cloud-change approval remain pending  ", "**Cloud Platform:** AWS or Azure  ")
        restored = restored.replace("**GitHub Repository URL:** https://github.com/Favourcloud/devops-micro-internship-pravinmishra  ", "**GitHub Repository URL:** Add your repository URL here  ")
        restored = re.sub(r"\n> \*\*Preparation status — not a completed submission:\*\*[^\n]*\n", "", restored)
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
