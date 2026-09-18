from datetime import datetime
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "runtime-2026-09-17.json").read_text())

    def test_metadata_is_allowlisted_and_redacted(self):
        self.assertEqual(set(self.record), {"schema_version", "assignment", "status", "date_utc", "budget", "attempts", "host_verification", "remaining_gates", "provenance"})
        self.assertEqual(set(self.record["budget"]), {"planning_allowance_usd", "enforced_cap", "billing_verified", "cleanup_deadline_utc", "d2lds_v6_linux_compute_quote_usd_per_hour", "quote_excludes"})
        for attempt in self.record["attempts"]:
            self.assertEqual(set(attempt), {"size", "region", "zonal", "apply_started_at", "apply_finished_at", "apply_exit_code", "result", "create_plan_sha256", "applied_source_sha256", "cleanup", "cleanup_verified_at", "destroy_plan_sha256"})
            self.assertEqual(set(attempt["applied_source_sha256"]), {".terraform.lock.hcl", "check_plan.py", "cloud-init.yaml", "main.tf", "variables.tf", "versions.tf"})
            for digest in list(attempt["applied_source_sha256"].values()) + [attempt["create_plan_sha256"], attempt["destroy_plan_sha256"]]:
                self.assertRegex(digest, r"^[0-9a-f]{64}$")
        text = json.dumps(self.record)
        for pattern in (r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", r"BEGIN .*PRIVATE KEY", r"ssh-rsa |ssh-ed25519 ", r"https://dev\.azure\.com/"):
            self.assertIsNone(re.search(pattern, text))

    def test_two_real_outcomes_and_cleanup_before_deadline(self):
        self.assertEqual(self.record["schema_version"], 1)
        self.assertEqual(self.record["status"], "vm_pilot_cleaned_agent_incomplete")
        attempts = self.record["attempts"]
        self.assertEqual([(a["size"], a["apply_exit_code"]) for a in attempts], [("Standard_B2s", 1), ("Standard_D2lds_v6", 0)])
        deadline = datetime.fromisoformat(self.record["budget"]["cleanup_deadline_utc"].replace("Z", "+00:00"))
        for attempt in attempts:
            self.assertEqual(attempt["region"], "uksouth")
            self.assertIs(attempt["zonal"], False)
            self.assertEqual(set(attempt["cleanup"]), {"resource_group_absent", "vm_absent", "disk_absent", "public_ip_absent", "terraform_state_empty"})
            self.assertTrue(all(value is True for value in attempt["cleanup"].values()))
            start, finish, cleaned = [datetime.fromisoformat(attempt[key]) for key in ("apply_started_at", "apply_finished_at", "cleanup_verified_at")]
            self.assertLess(start, finish)
            self.assertLess(finish, cleaned)
            self.assertLess(cleaned, deadline)
        self.assertIs(self.record["budget"]["enforced_cap"], False)
        self.assertIs(self.record["budget"]["billing_verified"], False)

    def test_unperformed_work_stays_pending(self):
        host = self.record["host_verification"]
        self.assertEqual(set(host), {"diagnostics_update_plan_sha256", "diagnostics_update_exit_code", "diagnostics_update_source_sha256", "finished_at", "stop_reason", "host_key_verified", "ssh_attempted", "guest_account_verified"})
        self.assertEqual(set(host["diagnostics_update_source_sha256"]), {"main.tf", "variables.tf", "versions.tf"})
        for digest in list(host["diagnostics_update_source_sha256"].values()) + [host["diagnostics_update_plan_sha256"]]:
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertEqual(host["stop_reason"], "trusted_ed25519_fingerprint_unavailable")
        self.assertEqual(host["diagnostics_update_exit_code"], 0)
        for key in ("host_key_verified", "ssh_attempted", "guest_account_verified"):
            self.assertIs(host[key], False)
        gates = self.record["remaining_gates"]
        self.assertEqual(set(gates), {"organization_confirmed", "pat_created", "pool_created", "agent_package_installed", "agent_registered", "agent_service_verified", "agent_online", "manual_pipeline_passed", "screenshots_captured", "assignment_complete"})
        for key, value in gates.items():
            if key == "screenshots_captured":
                self.assertIs(type(value), int)
                self.assertEqual(value, 0)
            else:
                self.assertIs(value, False)


if __name__ == "__main__":
    unittest.main()
