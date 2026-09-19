"""Offline contracts for limited historical credit, not live or grading verification."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest


WEEK = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("brief_contract", WEEK / "submission/brief_contract.py")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


def receipt(path):
    return json.loads((WEEK / path).read_text())


class ChecklistReconciliationTests(unittest.TestCase):
    def test_exact_nine_answers_and_all_124_requirements(self):
        self.assertEqual(CONTRACT.CHECKLIST_COMPLETIONS, {
            "01": (
                "- [x] Task 2: Self-hosted agent pool created (Screenshot 1)",
                "- [x] Task 3: Ubuntu VM provisioned and SSH verified (Screenshots 2–3)",
                "- [x] Task 4: Agent installed, registered, and running as a service (Screenshots 4–5)",
                "- [x] Task 5: Agent verified Online (Screenshot 6)",
                "- [x] Task 6: Test pipeline run successfully (Screenshot 7)",
            ),
            "02": (
                "* [x] The correct Azure Static Website repository was imported into Azure Repos",
                "* [x] `index.html` is visible in Azure Repos",
                "* [x] Your Full Name was added to the website",
                "* [x] The YAML trigger includes all branches",
            ),
        })
        totals, completed, pending = [], [], []
        for name, assignment in CONTRACT.ASSIGNMENTS.items():
            text = (WEEK / name).read_text()
            checked = tuple(re.findall(r"^[*-] \[x\] .+$", text, re.M))
            self.assertEqual(checked, CONTRACT.CHECKLIST_COMPLETIONS.get(assignment, ()))
            totals.append(len(re.findall(r"^[*-] \[[ x]\] ", text, re.M)))
            completed.append(len(checked))
            pending.append(len(re.findall(r"^[*-] \[ \] ", text, re.M)))
        self.assertEqual(totals, [8, 22, 21, 40, 33])
        self.assertEqual(completed, [5, 4, 0, 0, 0])
        self.assertEqual(pending, [3, 18, 21, 40, 33])
        self.assertEqual((sum(totals), sum(completed), sum(pending)), (124, 9, 115))

    def test_a1_credit_is_bound_to_separate_trials_and_retired_resources(self):
        first = receipt("self-hosted-agent/runtime-2026-09-18.json")
        vm_ssh = receipt("self-hosted-agent/runtime-2026-09-19.json")
        interactive = receipt("self-hosted-agent/runtime-2026-09-19-interactive.json")
        self.assertEqual(first["agent_trial"]["pool_id"], 11)
        self.assertEqual(first["manual_run"]["pool_name"], "DMI-Week10-A1")
        self.assertEqual(first["manual_run"]["run_id"], 1)
        self.assertEqual(first["manual_run"]["result"], "succeeded")
        self.assertEqual(first["manual_run"]["commands_verified"], ["uname -a", "whoami", "df -h"])
        self.assertEqual(vm_ssh["submission"]["new_slots_captured"], [2, 3])
        self.assertEqual(vm_ssh["vm"]["os"], "Ubuntu 22.04.5 LTS")
        self.assertIs(vm_ssh["vm"]["ssh_host_fingerprint_authenticated"], True)
        self.assertIs(vm_ssh["registration"]["succeeded"], False)
        self.assertEqual(interactive["registration"]["agent_id"], 18)
        self.assertEqual(interactive["registration"]["vendor_exit"], 0)
        self.assertIs(interactive["package"]["download_hash_matched"], True)
        self.assertEqual(interactive["service"]["user"], "azdoagent")
        self.assertEqual(interactive["service"]["sub_state"], "running")
        self.assertIs(interactive["service"]["online_verified_during_trial"], True)
        self.assertIs(interactive["service"]["current_online_agent_claimed"], False)
        self.assertEqual(interactive["manual_run"]["id"], 2)
        self.assertEqual(interactive["manual_run"]["result"], "succeeded")
        self.assertEqual(interactive["submission"]["new_slots_captured"], [4, 5, 6])
        self.assertIs(interactive["submission"]["screenshot_7_remains_historical_run_1"], True)
        self.assertEqual(first["submission"]["original_checklist_items_checked"], 0)
        for historical in (first, vm_ssh, interactive):
            self.assertIs(historical["authorization"]["retired"], True)
            self.assertIs(historical["cleanup"]["vm_absent"], True)
            self.assertIs(historical["submission"]["assignment_complete"], False)

    def test_a2_import_and_name_credit_bind_to_unchanged_source_receipt(self):
        path = "application-pipelines/static-import-2026-09-18.json"
        self.assertEqual(hashlib.sha256((WEEK / path).read_bytes()).hexdigest(), "3ba4bf72f3b77836c58dc4dca3097fc4ced44fe1892cdf13a26db78b5442d779")
        historical = receipt(path)
        source = historical["static_repository"]
        self.assertEqual(source["source_url"], "https://github.com/pravinmishraaws/Azure-Static-Website")
        self.assertEqual(source["import_status"], "completed")
        self.assertIs(source["imported_main_matched_source_commit"], True)
        self.assertEqual(source["personalized_commit"], "8bfa3682a7440f12791085c1d4d0aa0f7fbcb4fb")
        self.assertEqual(source["only_changed_path"], "/index.html")
        for key in ("remote_content_verified", "remote_parent_verified", "remote_git_changes_verified", "all_bytes_except_learner_paragraph_unchanged"):
            self.assertIs(source[key], True)
        self.assertIs(historical["outcome"]["personalization_committed_and_read_back"], True)
        self.assertIs(historical["outcome"]["application_deployed"], False)
        self.assertIs(historical["outcome"]["assignment_complete"], False)

    def test_a2_trigger_credit_is_source_only_not_a_pipeline_run(self):
        path = "application-pipelines/static-pipeline-source-2026-09-18.json"
        self.assertEqual(hashlib.sha256((WEEK / path).read_bytes()).hexdigest(), "83ef79488a1a4e7afe3f40e20afa5474f2ec45873c60afc2ca59fe45cdf1886d")
        historical = receipt(path)
        source = historical["repository"]
        self.assertEqual(source["prepared_commit"], "6b38993a18f75c2588803a42b6e7790c95e95b81")
        self.assertIs(source["stored_source_hashes_verified"], True)
        expected = source["only_added_files"]["/azure-pipelines.yml"]
        actual = WEEK / "application-pipelines" / expected["source_path"]
        self.assertEqual(hashlib.sha256(actual.read_bytes()).hexdigest(), expected["sha256"])
        self.assertIs(historical["execution_gate"]["source_contains_all_branch_ci_trigger"], True)
        self.assertIs(historical["execution_gate"]["ssh_connection_id_is_unset_placeholder"], True)
        for key in ("application_pipeline_definition_count", "application_build_count"):
            self.assertEqual(historical["execution_gate"][key], 0)
        for key in ("pipeline_created", "pipeline_enabled_or_queued"):
            self.assertIs(historical["execution_gate"][key], False)
        for key in ("application_pipeline_run", "ssh_service_connection_created", "application_deployed", "assignment_complete"):
            self.assertIs(historical["outcome"][key], False)

    def test_scope_notes_are_adjacent_attributed_and_link_to_existing_receipts(self):
        for name, assignment in CONTRACT.ASSIGNMENTS.items():
            if assignment not in CONTRACT.CHECKLIST_COMPLETIONS:
                continue
            text = (WEEK / name).read_text()
            marker = "A" + str(int(assignment)) + "-CHECKLIST"
            pattern = r"^# Completion Checklist\n\n<!-- BEGIN WEEK10 ANSWER " + marker + r" -->\n(.*?)<!-- END WEEK10 ANSWER " + marker + r" -->\n\n[*-] \["
            match = re.search(pattern, text, re.M | re.S)
            self.assertIsNotNone(match)
            note = match.group(1)
            self.assertIn("assistant reconciliation", note)
            self.assertIn("PAT", note)
            for target in re.findall(r"\]\(([^)]+)\)", note):
                self.assertFalse(target.startswith(("/", "http")))
                self.assertTrue((WEEK / target).is_file())
            if assignment == "01":
                self.assertIn("temporary agents and VMs were removed", note)
                self.assertIn("shared PAT is left unchanged", note)
                self.assertIn("three unchecked items remain unresolved", note)
            else:
                self.assertIn("Eze Favour", note)
                self.assertIn("remaining 18 checks stay open", note)
                self.assertIn("All four A2 images still need full-size human review", note)
                self.assertIn("[Write your summary here.]", text)
                self.assertIn("[Paste your final website URL here]", text)

    def test_no_remaining_checkbox_can_be_credited_by_normalization(self):
        for name in CONTRACT.ASSIGNMENTS:
            raw = (WEEK / name).read_bytes()
            pending = re.findall(rb"(?m)^[*-] \[ \] .+$", raw)
            for line in pending:
                with self.subTest(brief=name, item=line), self.assertRaises(ValueError):
                    CONTRACT.restore_original_prompts(raw.replace(line, line.replace(b"[ ]", b"[x]", 1), 1), name)

    def test_missing_duplicate_modified_reordered_and_uppercase_checks_rejected(self):
        for name, assignment in CONTRACT.ASSIGNMENTS.items():
            if assignment not in CONTRACT.CHECKLIST_COMPLETIONS:
                continue
            raw = (WEEK / name).read_bytes()
            first, second = (line.encode() for line in CONTRACT.CHECKLIST_COMPLETIONS[assignment][:2])
            mutations = (
                raw.replace(first, first.replace(b"[x]", b"[ ]", 1), 1),
                raw + first + b"\n",
                raw.replace(first, first + b" altered", 1),
                raw.replace(first, first.replace(b"[x]", b"[X]", 1), 1),
                raw.replace(first + b"\n" + second, second + b"\n" + first, 1),
            )
            for index, mutated in enumerate(mutations):
                with self.subTest(brief=name, mutation=index), self.assertRaises(ValueError):
                    CONTRACT.restore_original_prompts(mutated, name)

    def test_checklist_scope_markers_are_required_and_cannot_move_or_nest(self):
        for name, assignment in CONTRACT.ASSIGNMENTS.items():
            if assignment not in CONTRACT.CHECKLIST_COMPLETIONS:
                continue
            raw = (WEEK / name).read_bytes()
            marker = ("A" + str(int(assignment)) + "-CHECKLIST").encode()
            block = re.search(rb"<!-- BEGIN WEEK10 ANSWER " + marker + rb" -->\n.*?<!-- END WEEK10 ANSWER " + marker + rb" -->\n\n", raw, re.S).group()
            mutations = (
                raw.replace(block, b"", 1),
                raw + block,
                block + raw.replace(block, b"", 1),
                raw.replace(block, block.replace(b"**", b"<!-- nested -->\n**", 1), 1),
                raw.replace(b"END WEEK10 ANSWER " + marker, b"END WEEK10 ANSWER UNKNOWN", 1),
                raw.replace(block, block.replace(marker, b"A3-CHECKLIST"), 1),
            )
            for index, mutated in enumerate(mutations):
                with self.subTest(brief=name, mutation=index), self.assertRaises(ValueError):
                    CONTRACT.restore_original_prompts(mutated, name)

    def test_checklist_credit_does_not_expand_capture_or_human_review_claims(self):
        current = receipt("evidence/current.json")
        self.assertEqual([current[key] for key in ("numbered_captured", "numbered_missing", "raw_images")], [9, 27, 11])
        for key in ("assignment_completion_claimed", "human_visual_review_verified", "separate_linkedin_image_captured"):
            self.assertIs(current[key], False)
        self.assertIs(receipt("self-hosted-agent/evidence/manifest.json")["live_verified"], False)
        self.assertIs(receipt("evidence/static-yaml-2026-09-19.json")["human_visual_review_verified"], False)


if __name__ == "__main__":
    unittest.main()
