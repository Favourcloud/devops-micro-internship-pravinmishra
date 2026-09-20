"""Bind the approved draft to one notes answer without broadening human/live claims."""

import hashlib
import json
from pathlib import Path
import re
import unittest


WEEK = Path(__file__).resolve().parents[2]
A1 = "assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md"
RECEIPT = "a1-reflection-approval-2026-09-20.json"
TEXT = (
    "During the lab, agent registration stalled at the optional TFVC licence prompt before PAT entry. "
    "The runbook was clarified for Git-only use, and a separate authorized interactive attempt subsequently succeeded. "
    "The agent ran as the non-root `azdoagent` account, and a manual pipeline verified `uname -a`, `whoami`, and `df -h`. "
    "The temporary agent and VM were removed afterward. This highlights the importance of checking interactive prompts, "
    "using non-root service accounts, and verifying cleanup."
)
DIGEST = "4ae3aebf648094f77034e48b4d659b43710f7ec0ab49bfa22766efcc780bfb2a"


def load(path):
    return json.loads((WEEK / path).read_text())


class ReflectionApprovalTests(unittest.TestCase):
    def test_receipt_is_exact_allowlisted_metadata_with_no_duplicate_keys(self):
        raw = (WEEK / "evidence" / RECEIPT).read_text()
        actual = json.loads(raw)
        expected = {
            "schema_version": 1,
            "assignment": "week-10-assignment-01",
            "status": "assistant_draft_user_approved",
            "learner_name": "Eze Favour",
            "authorship": "assistant_drafted_user_approved",
            "approval": {
                "date_utc": "2026-09-20",
                "response": "approved",
                "context": "Explicit reply to the immediately preceding reflection draft for review, after the user requested: write for me",
                "scope": "Adopt this exact reflection in A1 Notes and complete the notes checklist item; not independent verification of learner-performed actions",
            },
            "reflection": {"text": TEXT, "sha256": DIGEST},
            "source_receipts": [
                "self-hosted-agent/runtime-2026-09-19.json",
                "self-hosted-agent/runtime-2026-09-19-interactive.json",
            ],
            "boundaries": {key: False for key in (
                "learner_performed_all_steps_claimed", "independent_learning_verification_claimed",
                "pat_compliance_attested", "pat_change_or_use_authorized", "secret_absence_certified",
                "a2_image_review_attested", "new_runtime_authorization", "assignment_completion_claimed",
                "social_publication_authorized",
            )},
        }
        self.assertEqual(raw, json.dumps(actual, indent=2) + "\n")
        self.assertEqual(json.dumps(actual, sort_keys=True), json.dumps(expected, sort_keys=True))
        for path in actual["source_receipts"]:
            self.assertTrue((WEEK / path).is_file())

    def test_approved_text_is_verbatim_once_inside_attributed_notes(self):
        brief = (WEEK / A1).read_text()
        notes = re.search(r"<!-- BEGIN WEEK10 ANSWER A1-NOTES -->\n(.*?)<!-- END WEEK10 ANSWER A1-NOTES -->", brief, re.S).group(1)
        self.assertEqual(hashlib.sha256(TEXT.encode()).hexdigest(), DIGEST)
        self.assertEqual(brief.count(TEXT), 1)
        self.assertIn("**User-approved reflection — assistant-drafted, approved 20 September 2026:**\n\n" + TEXT + "\n\n", notes)
        self.assertIn("The user requested this draft and explicitly approved it", notes)
        self.assertIn("not a claim that the learner personally performed every step", notes)
        self.assertIn("(evidence/" + RECEIPT + ")", notes)
        self.assertNotIn("Learner input still required", notes)

    def test_only_notes_adds_credit_and_pat_privacy_items_stay_open(self):
        brief = (WEEK / A1).read_text()
        self.assertEqual(re.findall(r"^- \[ \] (.+)$", brief, re.M), [
            "Task 1: PAT created with required scopes and stored securely", "No secrets exposed",
        ])
        self.assertEqual(len(re.findall(r"^- \[x\] ", brief, re.M)), 6)
        self.assertIn("- [x] Platform/org/pool details and issue notes written (Notes)", brief)
        self.assertIn("The shared PAT is left unchanged as requested", brief)
        self.assertIn("Neither image review nor reflection approval establishes those claims", brief)
        self.assertIn("not current health or assignment completion", brief)

    def test_historical_then_pending_reflection_flags_are_not_rewritten(self):
        first = load("self-hosted-agent/runtime-2026-09-18.json")
        self.assertEqual(first["submission"]["learner_notes"], "pending")
        self.assertEqual(first["submission"]["original_checklist_items_checked"], 0)
        for path in ("self-hosted-agent/runtime-2026-09-19.json", "self-hosted-agent/runtime-2026-09-19-interactive.json"):
            historical = load(path)
            self.assertIs(historical["submission"]["learner_reflection_supplied"], False)
            self.assertIs(historical["submission"]["assignment_complete"], False)
            self.assertIs(historical["authorization"]["retired"], True)
        review = load("evidence/a1-human-review-2026-09-19.json")
        self.assertIs(review["boundaries"]["learner_reflection_supplied"], False)
        self.assertIs(review["boundaries"]["pat_compliance_attested"], False)

    def test_approval_does_not_complete_image_review_or_authorize_runtime(self):
        current = load("evidence/current.json")
        self.assertEqual([current[k] for k in ("numbered_required", "numbered_captured", "numbered_missing", "raw_images")], [36, 10, 26, 13])
        self.assertEqual(current["human_review_receipts"], ["a1-human-review-2026-09-19.json"])
        for key in ("human_visual_review_verified", "assignment_completion_claimed", "separate_linkedin_image_captured"):
            self.assertIs(current[key], False)
        self.assertIs(load("self-hosted-agent/evidence/manifest.json")["live_verified"], False)
        self.assertIs(load("evidence/static-yaml-2026-09-19.json")["human_visual_review_verified"], False)
        trial = load("self-hosted-agent/runtime-2026-09-19-interactive.json")
        self.assertIs(trial["authorization"]["authorizes_future_runtime"], False)
        self.assertIs(trial["registration"]["pat_entry_observed"], False)

    def test_current_docs_reference_the_separate_approval_and_updated_counts(self):
        for path in (A1, "README.md", "evidence/README.md", "self-hosted-agent/README.md", "application-pipelines/README.md"):
            text = (WEEK / path).read_text()
            with self.subTest(path=path):
                self.assertIn(RECEIPT, text)
                self.assertIn("assistant-drafted", text)
                self.assertNotIn("the learner's personal issue/resolution reflection remains pending", text)
                self.assertNotIn("personal reflection and the universal secrecy assertion remain", text)
        self.assertIn("ten evidence/approval-backed answers are checked and 114 remain pending", (WEEK / "README.md").read_text())
        self.assertIn("A1 6/8, A2 4/22; 10 checked and 114 pending", (WEEK / "evidence/README.md").read_text())


if __name__ == "__main__":
    unittest.main()
