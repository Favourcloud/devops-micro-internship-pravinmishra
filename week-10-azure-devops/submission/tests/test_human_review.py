"""Offline contracts for scoped user attestation, not observation of human review."""

import copy
import hashlib
import json
from pathlib import Path
import re
import unittest


WEEK = Path(__file__).resolve().parents[2]
RECEIPT = "a1-human-review-2026-09-19.json"
A1 = "assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md"
QUESTION = "Have you personally inspected all seven published A1 screenshots at full size and confirmed that their visible content is accurate and suitable to share?"
IMAGES = (
    ("agent-pool", "f2a7640a96c5d3a2136ed1ee3882c762863ea189e1063253345552ebada9a128"),
    ("running-ubuntu-vm", "1a99f6ce0bfda368b96730b409ca71200d95e0745cf6d83d13976d1da07b97d8"),
    ("ssh-ubuntu-details", "f1b0ff69561d13dd0881c04aef3a0c7bb56a1aef04f72530b63b3ff930a5283b"),
    ("registered-agent-configuration", "35f89125ca6ad904f5ddba714fef23fcf2894e06f504d51cb68bf63c84749830"),
    ("running-agent-service", "a73869bbce92a2d7df251a57bf26d653915f958d7417ae39da6914ed6bcc33fe"),
    ("online-agent", "f7a9da72b5f0e67f2f3004c2b0f005117b6b0b795b42e3d8436c721f11546d14"),
    ("linux-pipeline-output", "956e610d09f104a667dd5e7dad3d41ea09db8d7334d725339df6f63fd8480496"),
)
HISTORICAL = {
    "self-hosted-agent/runtime-2026-09-18.json": "202313ad1c78db9eb164688b78f8a10677625861d8e54d088649143e0772cb2f",
    "self-hosted-agent/runtime-2026-09-19.json": "0f71b0a09ad10068cc362cae56600b185cf63df20000dafba623e0e0164fbb3f",
    "self-hosted-agent/runtime-2026-09-19-interactive.json": "c196e5b7bb6011fe466933a439c732d889f0967c304fbffa45a489940832e565",
    "evidence/captures-2026-09-19.json": "fc4f851e320fe4b086cc49e81008bf9989d09b993f6f9352615e845424b0061b",
    "evidence/a1-vm-ssh-2026-09-19.json": "3fd88fc744c85096e2f75b5d73264e43860d36b41a2ef17747ea0f5ca8907620",
    "evidence/a1-interactive-2026-09-19.json": "3dfb45a15f614b978b45d8b3948b7f078774e5489e5af8bc60c66fe871f841bb",
    "evidence/static-yaml-2026-09-19.json": "853f34025f081f555f3cebd662df9c25cf48b700deabf2ea8a1efdb855eb42c4",
}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate metadata key")
        result[key] = value
    return result


class HumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((WEEK / "evidence" / RECEIPT).read_text(), object_pairs_hook=unique_keys)
        self.manifest = json.loads((WEEK / "self-hosted-agent/evidence/manifest.json").read_text())

    def assert_receipt(self, value):
        self.assertEqual(set(value), set("schema_version assignment status recorded_on reviewed_source_commit source question response full_size_inspection_attested visible_content_accuracy_and_suitability_attested review_performed_at review_independently_observed reviewer_identity_independently_verified images boundaries".split()))
        for key in ("schema_version", "assignment"):
            self.assertIs(type(value[key]), int)
        for key, expected in {
            "schema_version": 1, "assignment": 1, "status": "user_attested",
            "recorded_on": "2026-09-19",
            "reviewed_source_commit": "f5d5d2ebcb66ded3d12a5e1ce80b9dfd420bb2a9",
            "source": "direct_user_confirmation_in_session", "question": QUESTION, "response": "yes",
        }.items():
            self.assertEqual(value[key], expected)
        for key in ("full_size_inspection_attested", "visible_content_accuracy_and_suitability_attested"):
            self.assertIs(value[key], True)
        self.assertIsNone(value["review_performed_at"])
        self.assertIs(value["review_independently_observed"], False)
        self.assertIs(value["reviewer_identity_independently_verified"], False)
        self.assertEqual(set(value["boundaries"]), set("other_assignments_reviewed independent_secret_absence_certification learner_reflection_supplied pat_compliance_attested assignment_completion_claimed new_runtime_authorization social_publication_authorized".split()))
        for flag in value["boundaries"].values():
            self.assertIs(flag, False)
        self.assertEqual(value["images"], [
            {"slot": slot, "path": "screenshots/assignment-01-screenshot-%02d-%s.png" % (slot, name), "sha256": digest}
            for slot, (name, digest) in enumerate(IMAGES, 1)
        ])

    def test_allowlisted_direct_confirmation_not_independent_observation(self):
        self.assert_receipt(self.receipt)

    def test_scope_expansion_unknown_metadata_and_hash_changes_are_rejected(self):
        mutations = []
        for key in self.receipt["boundaries"]:
            candidate = copy.deepcopy(self.receipt)
            candidate["boundaries"][key] = True
            mutations.append(candidate)
        for key, value in (("assignment", 2), ("response", "proceed"), ("review_independently_observed", True), ("review_performed_at", "2026-09-19T00:00:00Z"), ("extra", "unapproved metadata")):
            candidate = copy.deepcopy(self.receipt)
            candidate[key] = value
            mutations.append(candidate)
        candidate = copy.deepcopy(self.receipt)
        candidate["images"][0]["sha256"] = "0" * 64
        mutations.append(candidate)
        candidate = copy.deepcopy(self.receipt)
        candidate["images"][0]["path"] = "../unapproved.png"
        mutations.append(candidate)
        candidate = copy.deepcopy(self.receipt)
        candidate["images"].pop()
        mutations.append(candidate)
        for candidate in mutations:
            with self.assertRaises(AssertionError):
                self.assert_receipt(candidate)
        with self.assertRaises(ValueError):
            json.loads('{"response":"yes","response":"yes"}', object_pairs_hook=unique_keys)

    def test_seven_exact_pngs_and_manifest_status_are_bound_to_confirmation(self):
        self.assertEqual(self.manifest["status"], "captures_user_review_attested")
        self.assertEqual(self.manifest["human_review_receipt"], "evidence/" + RECEIPT)
        self.assertIs(self.manifest["live_verified"], False)
        self.assertEqual(len(self.manifest["screenshots"]), 7)
        for image, slot in zip(self.receipt["images"], self.manifest["screenshots"]):
            for key in ("slot", "path", "sha256"):
                self.assertEqual(slot[key], image[key])
            self.assertEqual(slot["status"], "captured_user_review_attested")
            self.assertIs(slot["captured"], True)
            self.assertEqual(hashlib.sha256((WEEK / image["path"]).read_bytes()).hexdigest(), image["sha256"])

    def test_aggregate_and_a2_review_stay_pending(self):
        current = json.loads((WEEK / "evidence/current.json").read_text())
        self.assertEqual(current["human_review_receipts"], [RECEIPT])
        self.assertEqual(current["status"], "partial_captures_review_pending")
        self.assertEqual([current[key] for key in ("numbered_required", "numbered_captured", "numbered_missing", "raw_images")], [36, 9, 27, 11])
        for key in ("human_visual_review_verified", "assignment_completion_claimed", "separate_linkedin_image_captured"):
            self.assertIs(current[key], False)
        original = json.loads((WEEK / "evidence/captures-2026-09-19.json").read_text())
        a2 = [item for item in original["captures"] if item["assignment"] == 2]
        self.assertEqual(len(a2), 1)
        self.assertIs(a2[0]["human_visual_review_verified"], False)
        yaml = json.loads((WEEK / "evidence/static-yaml-2026-09-19.json").read_text())
        self.assertEqual(len(yaml["images"]), 3)
        self.assertIs(yaml["human_visual_review_verified"], False)

    def test_historical_capture_and_runtime_receipts_are_not_rewritten(self):
        for path, expected in HISTORICAL.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((WEEK / path).read_bytes()).hexdigest(), expected)

    def test_brief_placement_leaves_human_claims_and_reflection_pending(self):
        text = (WEEK / A1).read_text()
        blocks = re.findall(r"<!-- BEGIN WEEK10 CAPTURE A1-S([1-7]) -->\n(.*?)<!-- END WEEK10 CAPTURE A1-S\1 -->", text, re.S)
        self.assertEqual([number for number, _ in blocks], list("1234567"))
        for _, block in blocks:
            self.assertIn("Full-size content/privacy review is user-attested", block)
            self.assertIn("(evidence/" + RECEIPT + ")", block)
        self.assertIn("the learner reflection and PAT requirements remain pending", text)
        self.assertIn("has not been supplied", text)
        self.assertIn("not a PAT-entry or `config.sh` transcript", text)
        self.assertIn("screenshot 7 remains historical run 1", text)
        self.assertEqual(re.findall(r"^- \[ \] (.+)$", text, re.M), [
            "Task 1: PAT created with required scopes and stored securely",
            "Platform/org/pool details and issue notes written (Notes)",
            "No secrets exposed",
        ])
        self.assertEqual(re.findall(r"^- \[x\] Task ([2-6]):", text, re.M), list("23456"))

    def test_current_documentation_distinguishes_attestation_and_remaining_scope(self):
        for path in ("README.md", "self-hosted-agent/README.md", "evidence/README.md", A1):
            text = (WEEK / path).read_text()
            with self.subTest(path=path):
                self.assertIn(RECEIPT, text)
                self.assertIn("user-attested", text)
                self.assertNotIn("slots 4–6 remain `captured: false`", text)
        for path in ("README.md", "evidence/README.md"):
            self.assertIn("four A2 images", (WEEK / path).read_text())


if __name__ == "__main__":
    unittest.main()
