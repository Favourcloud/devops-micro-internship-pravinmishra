"""Offline contracts for actual VM/SSH captures and the unsuccessful later registration."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import urlsplit
import zlib

WEEK = Path(__file__).resolve().parents[2]
EXPECTED = {
    2: ("assignment-01-screenshot-02-running-ubuntu-vm.png", "1a99f6ce0bfda368b96730b409ca71200d95e0745cf6d83d13976d1da07b97d8", [3584, 2064]),
    3: ("assignment-01-screenshot-03-ssh-ubuntu-details.png", "f1b0ff69561d13dd0881c04aef3a0c7bb56a1aef04f72530b63b3ff930a5283b", [2800, 1800]),
}


class VmSshEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((WEEK / "evidence/a1-vm-ssh-2026-09-19.json").read_text())
        cls.receipt = json.loads((WEEK / cls.bundle["runtime_receipt"]).read_text())
        cls.brief = (WEEK / "assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md").read_text()

    def test_allowlisted_provenance_and_nonhuman_claims(self):
        self.assertEqual(set(self.bundle), {"schema_version", "status", "runtime_receipt", "new_numbered_slots", "assistant_operated", "assignment_completion_claimed", "human_visual_review_verified", "captures"})
        self.assertEqual(self.bundle["schema_version"], 1)
        self.assertEqual(self.bundle["status"], "partial_captures_review_pending")
        self.assertEqual(self.bundle["new_numbered_slots"], 2)
        self.assertIs(self.bundle["assistant_operated"], True)
        self.assertIs(self.bundle["assignment_completion_claimed"], False)
        self.assertIs(self.bundle["human_visual_review_verified"], False)
        fields = {"assignment", "slot", "path", "sha256", "bytes", "dimensions", "captured_at", "source_kind", "source_url", "method", "pixels_edited_or_synthesized", "local_ocr_markers_checked", "ocr_sensitive_screen_marker_found", "human_visual_review_verified", "saved_output_replayed", "brief", "limitations"}
        self.assertEqual([i["slot"] for i in self.bundle["captures"]], [2, 3])
        for item in self.bundle["captures"]:
            self.assertEqual(set(item), fields)
            self.assertEqual(item["assignment"], 1)
            self.assertIs(item["local_ocr_markers_checked"], True)
            for flag in ("pixels_edited_or_synthesized", "ocr_sensitive_screen_marker_found", "human_visual_review_verified", "saved_output_replayed"):
                self.assertIs(item[flag], False)
            self.assertIn("host subsequently destroyed", item["limitations"])

    def test_runtime_receipt_allows_only_sanitized_metadata_fields(self):
        schema = {
            None: "schema_version assignment status assistant_operated source_commit authorization vm package registration pat new_service_started new_online_agent_verified new_pipeline_run cleanup local_checks submission",
            "authorization": "activated_at expires_at maximum_minutes planning_allowance_usd enforced_spending_cap actual_billed_cost_usd retired existing_full_access_pat_reuse_explicitly_approved",
            "vm": "cloud region name size os architecture secure_boot_verified vtpm_verified ssh_host_fingerprint_authenticated ssh_user agent_account agent_sudo_denied agent_password_locked",
            "package": "version published_sha256 release_url download_hash_matched listener_version_verified required_libraries_resolved dependency_installer_executed",
            "registration": "attempted succeeded blocked_prompt eula_response_sent pat_sent_to_agent timeout_seconds agent_configuration_and_credentials_absent_afterward agent_processes_absent_afterward retry_performed fresh_retry_approval_obtained secondary_zero_sized_pty_observed",
            "pat": "existing_protected_value_used_for_authorized_ado_reads value_exposed_or_copied server_scope_or_expiry_changed revoked native_metadata_scope_observed native_metadata_expiry_observed metadata_row_cryptographically_matched_to_protected_value least_privilege_token_claimed",
            "cleanup": "requested_at terraform_destroy_completed_at absence_verified_at terraform_state_empty resource_group_absent vm_absent os_disk_absent public_ip_absent owned_agent_absent pool_agent_count before_operating_expiry initial_verifier_rejected_disk_not_found_wording recheck_was_read_only destroy_retried",
            "local_checks": "controller_tests_passed absence_parser_tests_passed network_denied ordinary_file_writes_denied ci_run_claimed",
            "submission": "new_slots_captured human_visual_privacy_reviewed learner_reflection_supplied assignment_complete",
        }
        for key, fields in schema.items():
            with self.subTest(section=key):
                self.assertEqual(set(self.receipt if key is None else self.receipt[key]), set(fields.split()))
        self.assertEqual(self.receipt["schema_version"], 1)
        self.assertEqual(self.receipt["assignment"], "week-10-assignment-01")

    def test_original_png_bytes_dimensions_and_complete_crc_structure(self):
        for item in self.bundle["captures"]:
            name, digest, dimensions = EXPECTED[item["slot"]]
            self.assertEqual(item["path"], "screenshots/" + name)
            raw = (WEEK / item["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual(item["sha256"], digest)
            self.assertEqual(item["bytes"], len(raw))
            self.assertEqual(item["dimensions"], dimensions)
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
            offset, chunks = 8, []
            while offset < len(raw):
                length = struct.unpack_from(">I", raw, offset)[0]
                end = offset + length + 12
                self.assertLessEqual(end, len(raw))
                kind = raw[offset + 4:offset + 8]
                payload = raw[offset + 8:offset + 8 + length]
                crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
                self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, crc)
                if kind == b"IHDR":
                    self.assertEqual(list(struct.unpack_from(">II", payload)), dimensions)
                if kind == b"IEND":
                    self.assertEqual(length, 0)
                chunks.append(kind)
                offset = end
            self.assertEqual(chunks[0], b"IHDR")
            self.assertEqual(chunks[-1], b"IEND")
            self.assertEqual(chunks.count(b"IHDR"), 1)
            self.assertEqual(chunks.count(b"IEND"), 1)
            self.assertIn(b"IDAT", chunks)

    def test_only_corresponding_prompts_are_replaced(self):
        for item in self.bundle["captures"]:
            section = re.search(r"^#### Screenshot " + str(item["slot"]) + r" — [^\n]+\n(.*?)(?=\n---)", self.brief, re.M | re.S).group(1)
            self.assertNotIn("Add your screenshot here.", section)
            self.assertEqual(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", section), [item["path"]])
            self.assertIn("Human visual/privacy review is pending.", section)
            self.assertIn("subsequently destroyed", section)
        self.assertEqual(self.brief.count("- [ ]"), 8)

    def test_manifest_matches_original_capture_metadata(self):
        manifest = json.loads((WEEK / "self-hosted-agent/evidence/manifest.json").read_text())
        for item in self.bundle["captures"]:
            slot = manifest["screenshots"][item["slot"] - 1]
            self.assertIs(slot["captured"], True)
            for key in ("path", "sha256", "captured_at"):
                self.assertEqual(slot[key], item[key])
            self.assertEqual(slot["run_url"], item["source_url"])
        self.assertIs(manifest["live_verified"], False)

    def test_native_sources_have_no_embedded_credentials(self):
        browser, terminal = self.bundle["captures"]
        self.assertEqual(browser["source_kind"], "native_browser")
        self.assertEqual(terminal["source_kind"], "native_terminal")
        self.assertIsNone(terminal["source_url"])
        url = urlsplit(browser["source_url"])
        self.assertEqual((url.scheme, url.netloc), ("https", "portal.azure.com"))
        self.assertFalse(url.query)
        self.assertIsNone(url.username)
        self.assertIsNone(url.password)
        self.assertIn("/virtualMachines/" + self.receipt["vm"]["name"] + "/overview", url.fragment)

    def test_bounded_timeline_and_cleanup_are_not_current_host_health(self):
        auth, cleanup = self.receipt["authorization"], self.receipt["cleanup"]
        start, end = (datetime.fromisoformat(auth[k]) for k in ("activated_at", "expires_at"))
        self.assertEqual((end - start).total_seconds(), 3600)
        self.assertIs(auth["retired"], True)
        self.assertIs(auth["enforced_spending_cap"], False)
        self.assertIsNone(auth["actual_billed_cost_usd"])
        destroyed = datetime.fromisoformat(cleanup["terraform_destroy_completed_at"])
        verified = datetime.fromisoformat(cleanup["absence_verified_at"])
        self.assertLess(destroyed, verified)
        self.assertLess(verified, end)
        for item in self.bundle["captures"]:
            captured = datetime.fromisoformat(item["captured_at"])
            self.assertLess(start, captured)
            self.assertLess(captured, destroyed)
        for key in ("terraform_state_empty", "resource_group_absent", "vm_absent", "os_disk_absent", "public_ip_absent", "owned_agent_absent", "before_operating_expiry", "initial_verifier_rejected_disk_not_found_wording", "recheck_was_read_only"):
            self.assertIs(cleanup[key], True)
        self.assertEqual(cleanup["pool_agent_count"], 0)
        self.assertIs(cleanup["destroy_retried"], False)

    def test_actual_precredential_failure_is_not_rewritten_as_success(self):
        registration = self.receipt["registration"]
        self.assertIs(registration["attempted"], True)
        self.assertIn("TFVC", registration["blocked_prompt"])
        self.assertEqual(registration["timeout_seconds"], 300)
        for key in ("succeeded", "eula_response_sent", "pat_sent_to_agent", "retry_performed", "fresh_retry_approval_obtained"):
            self.assertIs(registration[key], False)
        self.assertIs(self.receipt["new_service_started"], False)
        self.assertIs(self.receipt["new_online_agent_verified"], False)
        self.assertIsNone(self.receipt["new_pipeline_run"])
        self.assertEqual(self.receipt["submission"]["new_slots_captured"], [2, 3])
        for key in ("human_visual_privacy_reviewed", "learner_reflection_supplied", "assignment_complete"):
            self.assertIs(self.receipt["submission"][key], False)

    def test_pat_observation_is_not_value_binding_or_least_privilege(self):
        pat = self.receipt["pat"]
        self.assertEqual(pat["native_metadata_scope_observed"], "Full access")
        self.assertEqual(pat["native_metadata_expiry_observed"], "2026-12-18")
        for key in ("value_exposed_or_copied", "server_scope_or_expiry_changed", "revoked", "metadata_row_cryptographically_matched_to_protected_value", "least_privilege_token_claimed"):
            self.assertIs(pat[key], False)
        self.assertIs(self.receipt["authorization"]["existing_full_access_pat_reuse_explicitly_approved"], True)

    def test_guest_package_and_local_checks_remain_scoped(self):
        self.assertEqual(self.receipt["status"], "vm_ssh_verified_registration_blocked_cleaned_up")
        self.assertEqual(self.receipt["source_commit"], "ecf5ad4b7d373a73bddeaca72efa2f7406b9ef7e")
        self.assertIs(self.receipt["assistant_operated"], True)
        self.assertEqual(self.receipt["vm"]["agent_account"], "azdoagent")
        self.assertIs(self.receipt["vm"]["agent_sudo_denied"], True)
        package = self.receipt["package"]
        self.assertEqual(package["version"], "5.279.0")
        self.assertEqual(package["published_sha256"], "6e3352e1dc44c924cd85840df279f21c200e6365596a7c38f3087015262555dc")
        self.assertIs(package["dependency_installer_executed"], False)
        self.assertEqual(self.receipt["local_checks"], {"controller_tests_passed": 81, "absence_parser_tests_passed": 8, "network_denied": True, "ordinary_file_writes_denied": True, "ci_run_claimed": False})

    def test_runbook_declines_optional_licence_and_protects_pat_entry(self):
        runbook = (WEEK / "self-hosted-agent/README.md").read_text()
        self.assertIn("answer **N** for this Git-only verification", runbook)
        self.assertIn("token only in its hidden prompt", runbook)
        self.assertIn("explicit fresh registration approval", runbook)
        self.assertNotIn("--acceptTeeEula", runbook)
        self.assertIn("before the hidden PAT prompt", self.brief)
        self.assertIn("successful resolution is not claimed", self.brief)


if __name__ == "__main__":
    unittest.main()
