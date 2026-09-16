"""Offline integrity checks for dated observations; never replay cloud/model calls."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "reports/live"


def record(name):
    return json.loads((LIVE / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentCycleTests(unittest.TestCase):
    def test_three_native_reviews_match_actual_reports(self):
        for kind, report in (("clean", "baseline-report.txt"), ("risk", "drift-detected-report.txt"),
                             ("final", "resolved-report.txt")):
            with self.subTest(review=kind):
                data = record(f"claude-{kind}-review-20260916.json")
                self.assertEqual(data["status"], "GENUINE_NATIVE_SKILL_REVIEW_VERIFIED")
                self.assertEqual(data["review_kind"], kind)
                self.assertEqual(data["registered_manual_skill"], "tf-drift-review")
                self.assertEqual(data["successful_reads"], ["CLAUDE.md", "README.md", f"reports/live/{report}"])
                self.assertEqual(data["native_pretooluse_read_events"], 3)
                self.assertEqual(data["hook_exit_codes"], [0, 0, 0])
                self.assertTrue(data["matching_hook_and_tool_events"])
                self.assertTrue(data["full_read_contents_verified"])
                self.assertEqual(data["api_retries"], 0)
                self.assertFalse(data["bash_or_cloud_tools_used"])
                self.assertFalse(data["human_resolution_attested_by_this_review"])
                self.assertFalse(data["model_mutation_authorization"])
                self.assertEqual(data["report_sha256"], digest(LIVE / report))
                self.assertEqual(data["source_sha256_at_review"]["CLAUDE.md"], digest(ROOT / "CLAUDE.md"))
                self.assertEqual(data["source_sha256_at_review"][f"reports/live/{report}"], digest(LIVE / report))
                self.assertRegex(data["source_sha256_at_review"]["README.md"], r"^[a-f0-9]{64}$")
                self.assertLess(datetime.fromisoformat(data["report_timestamp_utc"]),
                                datetime.fromisoformat(data["started_at_utc"]))
                self.assertLess(datetime.fromisoformat(data["started_at_utc"]),
                                datetime.fromisoformat(data["verified_at_utc"]))
                for text in ((LIVE / report).read_text(), data["sanitized_actual_response"]):
                    self.assertIn(data["report_timestamp_utc"], text)
                    self.assertIn(data["report_plan_json_sha256"], text)
                    self.assertIn(data["report_status"], text)
                self.assertIn("SANITIZED RECORDED OUTPUT", (LIVE / f"claude-{kind}-review-20260916.txt").read_text())
        response = record("claude-risk-review-20260916.json")["sanitized_actual_response"]
        self.assertIn("Do not apply this configuration", response)

    def test_native_fail_control_is_not_missing_report_control(self):
        data = record("native-hook-fail-20260916.json")
        self.assertEqual(data["status"], "GENUINE_NATIVE_FAIL_REPORT_DENIAL_VERIFIED")
        self.assertEqual(data["requested_command"], "terraform apply -input=false")
        for key in ("request_count", "native_hook_start_count", "native_hook_response_count"):
            self.assertEqual(data[key], 1)
        self.assertEqual(data["native_hook_exit_code"], 2)
        self.assertTrue(data["matching_hook_session_and_tool_ids"])
        self.assertTrue(data["matching_tool_result_is_error"])
        self.assertTrue(data["report_byte_identical_to_actual_checker"])
        self.assertEqual(data["report_sha256"], digest(LIVE / "drift-detected-report.txt"))
        self.assertTrue(data["actual_stderr"].endswith("report=FAIL"))
        self.assertEqual(data["api_retries"], 0)
        self.assertFalse(data["terraform_executed"])
        self.assertFalse(data["public_ssh_applied"])
        self.assertFalse(data["human_resolution_attested"])
        self.assertIn(data["actual_stderr"], (LIVE / "native-hook-fail-20260916.txt").read_text())
        earlier = record("native-hook-denial-20260916.json")
        self.assertTrue(earlier["exact_gate_stderr"].endswith("report=missing or invalid"))
        self.assertNotEqual(data["raw_transcript_sha256"], earlier["raw_transcript_sha256"])

    def test_human_decision_then_final_then_exact_cleanup(self):
        human = record("human-resolution-20260916.json")
        self.assertEqual(human["exact_user_response"], "approved")
        self.assertTrue(human["human_resolution_obtained"])
        for key in ("human_manually_executed_terraform", "public_ssh_apply_authorized", "enrollment_expiry_extended",
                    "model_allowance_increased", "exact_message_sent_timestamp_asserted"):
            self.assertFalse(human[key])
        for key, filename in (("risk_report_sha256", "drift-detected-report.txt"),
                              ("claude_risk_review_sha256", "claude-risk-review-20260916.json"),
                              ("native_fail_denial_sha256", "native-hook-fail-20260916.json")):
            self.assertEqual(human[key], digest(LIVE / filename))
        cycle = record("cycle-20260916.json")
        self.assertTrue(cycle["human_resolution"]["obtained"])
        self.assertTrue(cycle["final_review_performed"])
        self.assertTrue(cycle["cleanup_completed"])
        self.assertFalse(cycle["full_assignment_complete"])
        self.assertFalse(cycle["proposal"]["applied"])
        self.assertFalse(cycle["proposal"]["persistent_override_file_created"])
        self.assertFalse(cycle["proposal"]["out_of_band_drift"])
        stages = {o["summary"]["stage"]: o for o in cycle["verified_stage_observations"]}
        final = record("claude-final-review-20260916.json")
        times = [human["recorded_at_utc"], stages["final"]["started_at_utc"], stages["final"]["completed_at_utc"],
                 cycle["checker_evidence"]["final"]["completed_at_utc"], final["started_at_utc"], final["verified_at_utc"],
                 stages["apply-cleanup-security-group"]["started_at_utc"], stages["apply-cleanup-security-group"]["completed_at_utc"],
                 stages["apply-cleanup-network"]["started_at_utc"], stages["apply-cleanup-network"]["completed_at_utc"],
                 stages["verify-cleanup"]["completed_at_utc"]]
        self.assertEqual([datetime.fromisoformat(t) for t in times], sorted(datetime.fromisoformat(t) for t in times))
        for stage in stages.values():
            self.assertEqual(stage["process_exit"], 0)
            self.assertTrue(stage["operator_unchanged_during_execution"])
            self.assertFalse(stage["summary"]["human_resolution_obtained"])
            self.assertFalse(stage["summary"]["final_review_significance"])
        for kind, report in (("baseline", "baseline-report.txt"), ("proposal", "drift-detected-report.txt"),
                             ("final", "resolved-report.txt")):
            check = cycle["checker_evidence"][kind]
            self.assertEqual(check["report_sha256"], digest(LIVE / report))
            self.assertTrue(check["local_state_unchanged"])
            self.assertTrue(check["stdout_matches_report"])
            self.assertEqual(check["checker_exit"], 2 if kind == "proposal" else 0)
        cleanup = cycle["cleanup_verification"]
        self.assertTrue(cleanup["both_current_cycle_states_empty"])
        self.assertTrue(cleanup["security_group_deleted_before_vpc"])
        self.assertEqual([cleanup["tagged_vpc_count"], cleanup["tagged_security_group_count"]], [0, 0])
        self.assertEqual(cleanup["exact_security_group_lookup"], "InvalidGroup.NotFound")
        self.assertEqual(cleanup["exact_vpc_lookup"], "InvalidVpcID.NotFound")
        self.assertTrue(any(o.get("summary", {}).get("code") == "PLAN_CHECK_FAILED"
                            for o in cycle["refused_stage_observations"]))
        fix = cycle["cleanup_check_compatibility"]
        self.assertEqual([fix["normal_tests_passed"], fix["optimized_tests_passed"]], [71, 71])
        self.assertTrue(fix["no_apply_attempt_preceded_recovery"])
        screenshots = cycle["screenshot_evidence"]
        self.assertEqual(screenshots["manifest_sha256"], digest(ROOT / "screenshots/manifest.json"))
        self.assertEqual(screenshots["captured_slots"], list(range(1, 20)))
        self.assertEqual(screenshots["pending_slots"], [])
        self.assertFalse(screenshots["manual_human_execution_proven"])
        self.assertFalse(screenshots["publication_proven"])

    def test_budget_and_public_privacy_boundaries(self):
        cycle = record("cycle-20260916.json")
        usage = (record("native-hook-denial-20260916.json")["reported_cost_usd"]
                 + cycle["first_clean_attempt"]["reported_cost_usd"]
                 + record("native-hook-fail-20260916.json")["reported_model_cost_usd"]
                 + sum(record(f"claude-{k}-review-20260916.json")["reported_model_cost_usd"] for k in ("clean", "risk", "final")))
        budget = cycle["budget"]
        self.assertAlmostEqual(usage, budget["reported_additional_cost_usd"])
        self.assertAlmostEqual(usage + budget["unreconciled_usage_reserved_usd"], budget["accounted_usd"])
        self.assertAlmostEqual(budget["accounted_usd"] + budget["remaining_after_reservation_usd"], budget["approved_additional_usd"])
        self.assertEqual(budget["unreconciled_usage_reserved_usd"], 0.18)
        self.assertFalse(budget["additional_model_calls_required"])
        self.assertFalse(cycle["account_billing_audited"])
        self.assertFalse(cycle["enrollment_permissions_renewed"])
        self.assertEqual(cycle["enrollment_permission_expiry_utc"], "2026-09-16T13:30:00Z")
        for path in LIVE.glob("*-20260916.*"):
            with self.subTest(public=path.name):
                self.assertNotRegex(path.read_text(), r"(?:AKIA|ASIA)[A-Z0-9]{16}|arn:aws:|/Users/|\b[0-9]{12}\b|\b(?:vpc|sg)-[0-9a-f]{8,17}\b")


if __name__ == "__main__":
    unittest.main()
