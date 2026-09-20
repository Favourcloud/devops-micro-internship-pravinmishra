"""Credential-free checks for narrowly reviewed evidence and answer substitutions."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit


WEEK = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("brief_contract", WEEK / "submission/brief_contract.py")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


class BriefContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((WEEK / "submission/status.json").read_text())
        cls.assignments = cls.snapshot["assignments"]
        cls.a1 = cls.assignments[0]["brief"]
        cls.raw = (WEEK / cls.a1).read_bytes()

    def assert_not_preserved(self, raw, name=None):
        name = name or self.a1
        try:
            restored = CONTRACT.restore_original_prompts(raw, name)
        except ValueError:
            return
        expected = next(a["brief_sha256"] for a in self.assignments if a["brief"] == name)
        self.assertNotEqual(hashlib.sha256(restored).hexdigest(), expected)

    def test_all_five_unchanged_baseline_hashes_still_match(self):
        for assignment in self.assignments:
            name = assignment["brief"]
            with self.subTest(brief=name):
                original = CONTRACT.restore_original_prompts((WEEK / name).read_bytes(), name)
                self.assertEqual(hashlib.sha256(original).hexdigest(), assignment["brief_sha256"])

    def test_only_exact_published_brief_filenames_are_accepted(self):
        self.assertEqual(set(CONTRACT.ASSIGNMENTS), {a["brief"] for a in self.assignments})
        for name in ("assignment-01-unapproved.md", "assignment-06-unapproved.md", "../" + self.a1):
            with self.subTest(name=name), self.assertRaises(ValueError):
                CONTRACT.restore_original_prompts(self.raw, name)

    def test_only_supported_screenshot_prompts_are_replaced(self):
        current = json.loads((WEEK / "evidence/current.json").read_text())
        supported = [(int(a), int(s.split("-S")[1])) for a, slots in CONTRACT.CAPTURE_SLOTS.items() for s in slots]
        self.assertEqual(supported, [tuple(pair) for pair in current["captured_slots"]])
        for assignment in self.assignments:
            name = assignment["brief"]
            raw = (WEEK / name).read_bytes()
            restored = CONTRACT.restore_original_prompts(raw, name)
            approved_count = len(CONTRACT.CAPTURE_SLOTS.get(name.split("-")[1], ()))
            self.assertEqual(raw.count(b"Add your screenshot here."), restored.count(b"Add your screenshot here.") - approved_count)
        self.assertEqual(current["numbered_missing"], 26)
        self.assertFalse(current["assignment_completion_claimed"])
        self.assertFalse(current["human_visual_review_verified"])

    def test_duplicate_capture_is_rejected(self):
        block = re.search(rb"<!-- BEGIN WEEK10 CAPTURE A1-S1 -->.*?<!-- END WEEK10 CAPTURE A1-S1 -->\n\n", self.raw, re.S).group()
        with self.assertRaises(ValueError):
            CONTRACT.restore_original_prompts(self.raw + block, self.a1)

    def test_unapproved_capture_and_wrong_assignment_are_rejected(self):
        with self.assertRaises(ValueError):
            CONTRACT.restore_original_prompts(self.raw.replace(b"A1-S1", b"A1-S8"), self.a1)
        with self.assertRaises(ValueError):
            CONTRACT.restore_original_prompts(self.raw, self.assignments[1]["brief"])
        with self.assertRaises(ValueError):
            CONTRACT.restore_original_prompts(self.raw, "../" + self.a1)

    def test_missing_mismatched_and_nested_markers_are_rejected(self):
        mutations = (
            self.raw.replace(b"<!-- BEGIN WEEK10 CAPTURE A1-S1 -->\n", b"", 1),
            self.raw.replace(b"<!-- END WEEK10 CAPTURE A1-S1 -->", b"<!-- END WEEK10 CAPTURE A1-S2 -->", 1),
            self.raw.replace(b"<!-- BEGIN WEEK10 CAPTURE A1-S1 -->\n", b"<!-- BEGIN WEEK10 CAPTURE A1-S1 -->\n<!-- unexpected -->\n", 1),
        )
        for raw in mutations:
            with self.subTest(raw_length=len(raw)), self.assertRaises(ValueError):
                CONTRACT.restore_original_prompts(raw, self.a1)

    def test_unknown_duplicate_or_missing_answer_is_rejected(self):
        block = re.search(rb"<!-- BEGIN WEEK10 ANSWER A1-NOTES -->.*?<!-- END WEEK10 ANSWER A1-NOTES -->\n\n", self.raw, re.S).group()
        for raw in (self.raw + block, self.raw.replace(block, b""), self.raw.replace(b"ANSWER A1-NOTES", b"ANSWER A1-UNAPPROVED")):
            with self.subTest(raw_length=len(raw)), self.assertRaises(ValueError):
                CONTRACT.restore_original_prompts(raw, self.a1)

    def test_requirement_edits_and_unfulfilled_prompt_removal_are_detected(self):
        self.assert_not_preserved(b"Changed task instructions.\n" + self.raw)
        a2 = self.assignments[1]["brief"]
        raw_a2 = (WEEK / a2).read_bytes()
        self.assert_not_preserved(raw_a2.replace(b"Add your screenshot here.\n\n", b"", 1), a2)
        self.assert_not_preserved(self.raw.replace(b"- [ ]", b"- [x]", 1))
        self.assert_not_preserved(self.raw.replace(b"#### Screenshot 2", b"#### Screenshot 22", 1))

    def test_misplaced_capture_or_redundant_prompt_is_detected(self):
        block = re.search(rb"<!-- BEGIN WEEK10 CAPTURE A1-S1 -->.*?<!-- END WEEK10 CAPTURE A1-S1 -->\n\n", self.raw, re.S).group()
        self.assert_not_preserved(block + self.raw.replace(block, b"", 1))
        self.assert_not_preserved(self.raw.replace(block, b"Add your screenshot here.\n\n" + block, 1))

    def test_unapproved_a2_answer_cannot_be_silently_normalized(self):
        name = self.assignments[1]["brief"]
        raw = (WEEK / name).read_bytes()
        self.assert_not_preserved(raw + b"<!-- BEGIN WEEK10 ANSWER A2-SUMMARY -->\nDone.\n<!-- END WEEK10 ANSWER A2-SUMMARY -->\n\n", name)
        self.assert_not_preserved(raw.replace(b"Add your screenshot here.\n\n", b"Unsupported claim.\n\n", 1), name)

    def test_preparation_notice_edits_are_exact_and_still_partial(self):
        for original, current in CONTRACT.PREPARATION_EDITS:
            self.assertEqual(self.raw.count(current.encode()), 1)
            with self.assertRaises(ValueError):
                CONTRACT.restore_original_prompts(self.raw.replace(current.encode(), b"Assignment complete."), self.a1)
        self.assertIn(b"seven genuine captures from separate trials", self.raw)
        self.assertIn(b"the user has attested full-size content/privacy review of all seven A1 screenshots", self.raw)
        self.assertIn(b"Other assignment requirements remain pending", self.raw)

    def test_notes_reference_actual_historical_receipt_without_impersonation(self):
        receipt = json.loads((WEEK / "self-hosted-agent/runtime-2026-09-18.json").read_text())
        notes = re.search(rb"<!-- BEGIN WEEK10 ANSWER A1-NOTES -->\n(.*?)<!-- END WEEK10 ANSWER A1-NOTES -->", self.raw, re.S).group(1).decode()
        run, agent, cleanup = receipt["manual_run"], receipt["agent_trial"], receipt["cleanup"]
        parsed = urlsplit(run["run_url"])
        for fact in (agent["os"], agent["architecture"], agent["agent_version"], agent["service_user"], run["run_url"], run["pool_name"], *parsed.path.split("/")[1:3], *run["commands_verified"]):
            self.assertIn(fact, notes)
        for timestamp in (run["finished_at"], cleanup["terraform_cleanup_verified_at"], cleanup["agent_removal_verified_at"]):
            self.assertIn(timestamp.split("T")[1].split(".")[0] + " UTC", notes)
        self.assertIn("assistant-operated", notes)
        self.assertIn("not learner-performed actions", notes)
        self.assertIn("User-approved reflection — assistant-drafted", notes)
        self.assertIn("not a claim that the learner personally performed every step", notes)
        self.assertIn("a1-reflection-approval-2026-09-20.json", notes)
        self.assertIn("Screenshots **4–6** were captured", notes)
        self.assertIn("input itself was not observed or recorded", notes)
        self.assertIn("PAT scope, server expiry and revocation were not independently verified", notes)
        self.assertIn("metadata row showed **Full access**", notes)
        self.assertIn("No token was sent during the first 19 September registration attempt", notes)
        self.assertNotRegex(notes, r"(?i)\b(I|my|we|our)\b")
        self.assertEqual(receipt["submission"]["learner_notes"], "pending")
        self.assertFalse(receipt["submission"]["assignment_complete"])
        self.assertTrue(receipt["authorization"]["retired"])

    def test_notes_local_links_resolve_without_network_or_credentials(self):
        notes = re.search(rb"<!-- BEGIN WEEK10 ANSWER A1-NOTES -->\n(.*?)<!-- END WEEK10 ANSWER A1-NOTES -->", self.raw, re.S).group(1).decode()
        for target in re.findall(r"\]\(([^)]+)\)", notes):
            if target.startswith("https://"):
                self.assertIsNone(urlsplit(target).username)
                self.assertIsNone(urlsplit(target).password)
            else:
                path, separator, anchor = target.partition("#")
                self.assertTrue((WEEK / path).is_file())
                if separator:
                    headings = re.findall(r"^#{1,6} (.+)$", (WEEK / path).read_text(), re.M)
                    slugs = [re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-") for heading in headings]
                    self.assertIn(anchor, slugs)
        self.assertNotRegex(notes, r"(?i)(AZDO_PAT=|BEGIN [A-Z ]*PRIVATE KEY|access_token=)")


if __name__ == "__main__":
    unittest.main()
