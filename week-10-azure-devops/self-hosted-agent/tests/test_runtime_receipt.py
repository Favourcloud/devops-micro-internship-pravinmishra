"""Offline publication contracts, not a replay or independent live verification."""

from datetime import datetime
import json
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[1]
RECEIPT = json.loads((PROJECT / "runtime-2026-09-18.json").read_text())


class RuntimeReceiptTests(unittest.TestCase):
    def test_only_allowlisted_metadata_is_published(self):
        self.assertEqual(set(RECEIPT), {
            "schema_version", "assignment", "status", "date_utc", "execution",
            "authorization", "agent_trial", "manual_run", "cleanup", "submission", "provenance",
        })
        expected = {
            "authorization": "operating_expires_at retired authorizes_future_runtime",
            "agent_trial": (
                "os architecture agent_version published_package_digest_verified "
                "bundled_runtime_verified_on_host registered_agent_id pool_id service_user "
                "service_running_nonroot_verified online_verified_during_trial"
            ),
            "manual_run": (
                "definition_id run_id run_url branch source_commit pool_name queue_id "
                "queued_at started_at finished_at status result worker_matches_registered_agent "
                "commands_verified whoami task_log_sha256"
            ),
            "cleanup": (
                "service_stopped_disabled_uninstalled terraform_delete_apply_exit_code "
                "terraform_cleanup_verified_at terraform_state_empty resource_group_absent "
                "vm_absent os_disk_absent public_ip_absent agent_removal_verified_at agent_absent "
                "pool_registered_agent_count successful_run_retained_after_cleanup "
                "session_cleanup_backstop_cleared"
            ),
            "submission": (
                "screenshots_captured required_screenshot_slots original_checklist_items_checked "
                "required_checklist_items learner_notes pat_scope_verified pat_expiry_verified "
                "pat_revocation_verified assignment_complete"
            ),
        }
        for key, fields in expected.items():
            with self.subTest(section=key):
                self.assertEqual(set(RECEIPT[key]), set(fields.split()))
        text = json.dumps(RECEIPT)
        self.assertNotRegex(text, r"\.private/|BEGIN .*PRIVATE KEY|Bearer |gh[pousr]_[A-Za-z0-9]+")
        self.assertNotRegex(text, r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    def test_identifies_historical_trial_not_assignment_completion(self):
        self.assertEqual(RECEIPT["schema_version"], 1)
        self.assertEqual(RECEIPT["assignment"], "week-10-assignment-01")
        self.assertEqual(RECEIPT["date_utc"], "2026-09-18")
        self.assertEqual(RECEIPT["status"], "technical_trial_succeeded_and_cleaned_submission_pending")
        self.assertIn("Assistant-operated", RECEIPT["execution"])
        self.assertIn("not screenshot evidence", RECEIPT["provenance"])
        self.assertIn("not the live facts", RECEIPT["provenance"])
        self.assertIs(RECEIPT["authorization"]["retired"], True)
        self.assertIs(RECEIPT["authorization"]["authorizes_future_runtime"], False)

    def test_run_identity_and_actual_required_commands(self):
        run = RECEIPT["manual_run"]
        self.assertEqual((run["definition_id"], run["run_id"], run["queue_id"]), (1, 1, 11))
        self.assertEqual(run["branch"], "refs/heads/main")
        self.assertEqual(run["source_commit"], "aef39187af3b62f0508f831b3282ac052ddb3dae")
        self.assertEqual(run["pool_name"], "DMI-Week10-A1")
        self.assertEqual(run["run_url"], "https://dev.azure.com/aneneeze2021/DMI-Week10/_build/results?buildId=1&view=results")
        self.assertEqual((run["status"], run["result"]), ("completed", "succeeded"))
        self.assertIs(run["worker_matches_registered_agent"], True)
        self.assertEqual(run["commands_verified"], ["uname -a", "whoami", "df -h"])
        self.assertEqual(run["whoami"], "azdoagent")
        self.assertEqual(run["task_log_sha256"], "d387b7b6bdb4f77c9b81bcf77ec2c8e47c056bd8ccc9f3356d19eefa35043659")

    def test_nonroot_historical_online_state_is_separate_from_cleanup(self):
        agent = RECEIPT["agent_trial"]
        self.assertEqual((agent["os"], agent["architecture"], agent["agent_version"]), ("Ubuntu 22.04", "x86_64", "5.279.0"))
        self.assertEqual((agent["registered_agent_id"], agent["pool_id"]), (17, 11))
        self.assertEqual(agent["service_user"], RECEIPT["manual_run"]["whoami"])
        for key in ("published_package_digest_verified", "bundled_runtime_verified_on_host",
                    "service_running_nonroot_verified", "online_verified_during_trial"):
            self.assertIs(agent[key], True)
        cleanup = RECEIPT["cleanup"]
        self.assertEqual(cleanup["terraform_delete_apply_exit_code"], 0)
        self.assertEqual(cleanup["pool_registered_agent_count"], 0)
        for key in ("service_stopped_disabled_uninstalled", "terraform_state_empty", "resource_group_absent",
                    "vm_absent", "os_disk_absent", "public_ip_absent", "agent_absent",
                    "successful_run_retained_after_cleanup", "session_cleanup_backstop_cleared"):
            self.assertIs(cleanup[key], True)

    def test_ordered_run_and_cleanup_before_fixed_expiry(self):
        run, cleanup = RECEIPT["manual_run"], RECEIPT["cleanup"]
        times = [run["queued_at"], run["started_at"], run["finished_at"],
                 cleanup["terraform_cleanup_verified_at"], cleanup["agent_removal_verified_at"],
                 RECEIPT["authorization"]["operating_expires_at"]]
        parsed = []
        for value in times:
            self.assertRegex(value, r"^2026-09-18T\d{2}:\d{2}:\d{2}\.\d{1,7}Z$")
            seconds, fraction = value[:-1].split(".")
            # Azure DevOps emits 100 ns precision; Python 3.9 accepts microseconds.
            parsed.append(datetime.fromisoformat(f"{seconds}.{fraction[:6].ljust(6, '0')}+00:00"))
        self.assertTrue(all(earlier < later for earlier, later in zip(parsed, parsed[1:])))

    def test_evidence_and_pat_claims_remain_pending(self):
        self.assertEqual(RECEIPT["submission"], {
            "screenshots_captured": 0, "required_screenshot_slots": 7,
            "original_checklist_items_checked": 0, "required_checklist_items": 8,
            "learner_notes": "pending", "pat_scope_verified": None,
            "pat_expiry_verified": None, "pat_revocation_verified": None, "assignment_complete": False,
        })
        manifest = json.loads((PROJECT / "evidence/manifest.json").read_text())
        self.assertEqual(manifest["status"], "pending")
        self.assertFalse(any(slot["captured"] for slot in manifest["screenshots"]))


if __name__ == "__main__":
    unittest.main()
