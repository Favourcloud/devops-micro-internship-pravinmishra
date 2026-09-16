"""Offline integrity checks for separately captured live evidence; no cloud calls."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "reports/live"


class LiveEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.operations = json.loads((LIVE / "operations.json").read_text())

    def test_current_reports_match_recorded_live_outcomes(self):
        cycle = json.loads((LIVE / "cycle-20260916.json").read_text())
        expected = (("baseline", "baseline-report.txt", "HEALTHY", 0, 0, 0),
                    ("proposal", "drift-detected-report.txt", "FAIL", 2, 1, 1),
                    ("final", "resolved-report.txt", "HEALTHY", 0, 0, 0))
        times = []
        for kind, filename, status, exit_code, ingress, changes in expected:
            with self.subTest(report=filename):
                content = (LIVE / filename).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(),
                                 cycle["checker_evidence"][kind]["report_sha256"])
                self.assertNotEqual(hashlib.sha256(content).hexdigest(),
                                    self.operations["public_report_sha256"][filename])
                fields = dict(line.split(": ", 1) for line in content.decode().splitlines() if ": " in line)
                self.assertEqual(fields["Mode"], "LIVE")
                self.assertEqual(fields["Reviewer"], "Eze Favour")
                self.assertEqual(fields["Overall Status"], status)
                self.assertEqual(fields["Terraform detailed exit code"], str(exit_code))
                self.assertEqual(fields["Unsafe public ingress findings"], str(ingress))
                self.assertEqual(fields["Non-no-op resource changes"], str(changes))
                self.assertEqual(fields["Refresh drift entries"], "0")
                self.assertEqual(fields["Destructive resource actions"], "0")
                self.assertRegex(fields["Plan SHA256"], r"^[a-f0-9]{64}$")
                timestamp = datetime.fromisoformat(fields["Timestamp UTC"])
                self.assertEqual(timestamp.date().isoformat(), "2026-09-16")
                self.assertEqual(timestamp, datetime.fromisoformat(
                    cycle["checker_evidence"][kind]["completed_at_utc"]).replace(microsecond=0))
                times.append(timestamp)
        self.assertEqual(times, sorted(times))
        self.assertEqual(len(set(times)), 3)

    def test_historical_records_remain_byte_identical(self):
        expected = {
            "operations.json": "d84676cd32c26ff04b0545614739225c6588de4dfd110e6b4e7bcb39b770327f",
            "claude-runtime.json": "a48e6b7bc3de0cc43ecb9214a8ce8621f3db616794915d6d888bdbf4851ddda4",
            "human-resolution.json": "fc32c28f6d118b9f40b7fb7e571cb6cbc6327e40c4b2ccaad68ad86f8d22976f",
        }
        for filename, digest in expected.items():
            with self.subTest(historical=filename):
                self.assertEqual(hashlib.sha256((LIVE / filename).read_bytes()).hexdigest(), digest)

    def test_historical_proposal_never_applied_and_cleanup_verified(self):
        proposal = self.operations["proposal"]
        example = ROOT / "terraform/public-ssh-proposal.tfvars.example"
        self.assertIn("NEVER APPLY", example.read_text())
        self.assertIn("test_public_ssh = true", example.read_text())
        self.assertEqual(hashlib.sha256(example.read_bytes()).hexdigest(), proposal["public_proposal_sha256"])
        self.assertIs(proposal["private_loaded_override_matches_public_example"], True)
        self.assertIs(proposal["risky_rule_applied"], False)
        self.assertEqual(proposal["deployed_ingress_rule_count_after_planning"], 0)
        self.assertEqual(proposal["checker_exit"], 2)
        for creation in self.operations["creation"]:
            self.assertEqual(creation["terraform_exit"], 0)
        for baseline in self.operations["baseline"]:
            self.assertEqual(baseline["terraform_exit"], 0)
            self.assertEqual(baseline["resources"][0]["actions"], ["no-op"])
        self.assertEqual([x["deleted_resource_type"] for x in self.operations["cleanup_actions"]],
                         ["aws_security_group", "aws_vpc"])
        for deletion in self.operations["cleanup_actions"]:
            self.assertEqual(deletion["terraform_exit"], 0)
            self.assertIs(deletion["only_created_resource_binding_matched"], True)
        cleanup = self.operations["cleanup_verification"]
        self.assertEqual(cleanup["cleanup"], "VERIFIED")
        for key in ("terraform_managed_resource_count", "lab_tagged_vpc_count", "lab_tagged_security_group_count"):
            self.assertEqual(cleanup[key], 0)
        self.assertEqual(cleanup["exact_created_vpc_lookup"], "InvalidVpcID.NotFound")
        self.assertEqual(cleanup["exact_created_group_lookup"], "InvalidGroup.NotFound")
        for key in ("earlier_coursework_resources_targeted", "bedrock_role_targeted", "risky_rule_applied"):
            self.assertIs(cleanup[key], False)
        for result in self.operations["final_local_terraform_validation"].values():
            self.assertEqual(result["fmt_exit"], 0)
            self.assertEqual(result["validate_exit"], 0)
            self.assertIs(result["valid"], True)

    def test_historical_pending_approval_is_not_rewritten(self):
        approval = json.loads((LIVE / "human-resolution.json").read_text())
        self.assertEqual(approval["status"], "PENDING")
        self.assertIn("Human resolution approval and successful Claude review remain pending.",
                      approval["verbatim_user_clarification"])
        self.assertIs(approval["human_resolution_approved"], False)
        self.assertIs(approval["general_continuation_approval_is_not_resolution_approval"], True)
        self.assertEqual(approval["screenshot_16"], "PENDING")
        self.assertIs(approval["human_operated_terraform"], False)
        self.assertIs(approval["claude_review_success"], False)
        self.assertIs(self.operations["technical_reset"]["human_resolution_approved"], False)

    def test_historical_runtime_failure_and_budget_remain_explicit(self):
        runtime = json.loads((LIVE / "claude-runtime.json").read_text())
        for key in ("successful_skill_reviews", "actual_read_calls", "actual_pretooluse_hook_events"):
            self.assertEqual(runtime[key], 0)
        self.assertIs(runtime["actual_blocked_apply_demonstrated"], False)
        self.assertIs(runtime["iam_permissions_expanded"], False)
        self.assertIs(runtime["account_spending_cap"], False)
        self.assertEqual(runtime["additional_budget_usd"], 0.50)
        self.assertEqual(runtime["additional_reported_cost_usd"], 0)
        self.assertEqual(runtime["unknown_usage_reservation_usd"], 0.18)
        self.assertAlmostEqual(runtime["additional_reported_cost_usd"] + runtime["unknown_usage_reservation_usd"]
                               + runtime["remaining_unreserved_budget_usd"], runtime["additional_budget_usd"])
        self.assertEqual(runtime["attempts"][1]["http_status"], 403)
        self.assertIn("not a confirmed charge", runtime["billing_note"])
        self.assertIs(runtime["historical_tool_free_connection"]["proves_skill_or_hook_execution"], False)

    def test_public_exports_exclude_private_bindings(self):
        expected = {"baseline-report.txt", "drift-detected-report.txt", "resolved-report.txt", "operations.json",
                    "claude-runtime.json", "human-resolution.json", "baseline-execution.txt", "cycle-20260916.json"}
        expected.update(f"{kind}-20260916.{suffix}"
                        for kind in ("native-hook-denial", "native-hook-fail", "claude-clean-review",
                                     "claude-risk-review", "claude-final-review", "human-resolution")
                        for suffix in ("json", "txt"))
        self.assertEqual({p.name for p in LIVE.iterdir()}, expected)
        for path in LIVE.iterdir():
            with self.subTest(file=path.name):
                self.assertNotRegex(path.read_text(),
                                    r"(?:AKIA|ASIA)[A-Z0-9]{16}|arn:aws:|/Users/|\b[0-9]{12}\b|(?:vpc|sg)-[0-9a-f]{8,}")
        execution = (LIVE / "baseline-execution.txt").read_text()
        self.assertIn("SANITIZED RECORDED OUTPUT EXPORT", execution)
        self.assertIn("not a reconstructed terminal", execution)
        self.assertEqual(execution.count("No changes. Your infrastructure matches the configuration."), 2)
        self.assertIn("Actual captured subprocess exit: 0", execution)
        self.assertIn("[PRIVATE PLAN PATH]", execution)

    def test_git_excludes_raw_data_but_includes_named_exports(self):
        def assert_ignored(path, expected):
            # Older Git versions return 0 even for a matching !include rule.
            # Inspect the NUL-delimited final rule, not that ambiguous status.
            process = subprocess.run(
                ["git", "check-ignore", "--no-index", "--verbose", "-z", "--stdin"],
                input=str(path).encode() + b"\0", capture_output=True, cwd=ROOT)
            self.assertEqual(process.returncode, 0)
            fields = process.stdout.split(b"\0")
            self.assertEqual(len(fields), 5)
            self.assertEqual(fields[-1], b"")
            self.assertEqual(fields[3], str(path).encode())
            self.assertTrue(fields[2], "Every evidence path needs an explicit rule")
            self.assertEqual(not fields[2].startswith(b"!"), expected)

        for path in (ROOT / ".review-data/private.json", ROOT / "reports/live/raw.log",
                     ROOT / "reports/live/unreviewed.json", ROOT.parents[1] / ".review-data/private.json"):
            with self.subTest(private=str(path.relative_to(ROOT.parents[1]))):
                assert_ignored(path, True)
        for path in LIVE.iterdir():
            with self.subTest(public=path.name):
                assert_ignored(path, False)


if __name__ == "__main__":
    unittest.main()
