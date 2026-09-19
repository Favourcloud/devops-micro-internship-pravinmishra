"""Offline consistency checks, not a replay of live operations or human review."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import parse_qs, urlsplit
import zlib

WEEK = Path(__file__).resolve().parents[2]
EXPECTED = {
    4: ("registered-agent-configuration", "35f89125ca6ad904f5ddba714fef23fcf2894e06f504d51cb68bf63c84749830", 822929, [2800, 1800]),
    5: ("running-agent-service", "a73869bbce92a2d7df251a57bf26d653915f958d7417ae39da6914ed6bcc33fe", 1023446, [2800, 1800]),
    6: ("online-agent", "f7a9da72b5f0e67f2f3004c2b0f005117b6b0b795b42e3d8436c721f11546d14", 365083, [3584, 2064]),
}


def timestamp(value):
    return datetime.fromisoformat(re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00"))


class InteractiveAgentEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads((WEEK / "evidence/a1-interactive-2026-09-19.json").read_text())
        cls.receipt = json.loads((WEEK / cls.bundle["runtime_receipt"]).read_text())
        cls.brief = (WEEK / "assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md").read_text()

    def test_capture_schema_is_allowlisted_and_nonhuman(self):
        self.assertEqual(set(self.bundle), set("schema_version status runtime_receipt new_numbered_slots assistant_operated assignment_completion_claimed human_visual_review_verified captures".split()))
        self.assertEqual(self.bundle["schema_version"], 1)
        self.assertEqual(self.bundle["status"], "partial_captures_review_pending")
        self.assertEqual(self.bundle["new_numbered_slots"], 3)
        self.assertIs(self.bundle["assistant_operated"], True)
        for flag in ("assignment_completion_claimed", "human_visual_review_verified"):
            self.assertIs(self.bundle[flag], False)
        self.assertEqual([c["slot"] for c in self.bundle["captures"]], [4, 5, 6])
        for capture in self.bundle["captures"]:
            self.assertEqual(set(capture), set("assignment slot path sha256 bytes dimensions captured_at source_kind source_url method pixels_edited_or_synthesized local_ocr_markers_checked ocr_sensitive_screen_marker_found human_visual_review_verified saved_output_replayed brief limitations".split()))
            self.assertEqual(capture["assignment"], 1)
            self.assertIs(capture["local_ocr_markers_checked"], True)
            for flag in ("pixels_edited_or_synthesized", "ocr_sensitive_screen_marker_found", "human_visual_review_verified", "saved_output_replayed"):
                self.assertIs(capture[flag], False)
            self.assertIn("host subsequently destroyed and agent removed", capture["limitations"])

    def test_runtime_metadata_schema_excludes_arbitrary_private_records(self):
        schema = {
            None: "schema_version assignment status assistant_operated source_commit authorization vm package registration service manual_run pat_and_isolation_limits cleanup local_checks submission",
            "authorization": "fresh_approval_received activated_at expires_at maximum_minutes planning_allowance_usd enforced_spending_cap actual_billed_cost_usd retired authorizes_future_runtime",
            "vm": "cloud region name size os architecture ssh_host_fingerprint_authenticated agent_account agent_sudo_denied agent_password_locked",
            "package": "version published_sha256 release_url download_hash_matched listener_version_verified required_libraries_resolved dependency_installer_executed",
            "registration": "entry_mode vendor_exit vendor_completed_at user_reported_completion user_reported_at pat_entry_observed pat_sent_to_hidden_prompt stored_pat_forwarded_to_registration raw_terminal_output_retained independent_agent_verification_at agent_id agent_name pool_id pool_name organization project credential_file_owner_and_mode_verified credential_file_contents_read",
            "service": "verified_at user active_state sub_state main_pid publisher_scripts_unchanged online_verified_during_trial current_online_agent_claimed",
            "manual_run": "id definition_id definition_revision reason status result queued_at started_at finished_at run_url source_commit source_branch yaml_sha256 yaml_bytes task_log_sha256 commands_verified whoami runs_queued_in_this_trial",
            "pat_and_isolation_limits": "existing_full_access_pat_reuse_explicitly_approved credential_value_recorded_by_controller server_scope_or_expiry_changed revoked metadata_row_cryptographically_matched_to_protected_value least_privilege_compliance_claimed only_definition_1_authorized_in_visible_yaml_pool_permissions inaccessible_projects_audited classic_access_globally_disabled",
            "cleanup": "early_cleanup_requested service_uninstalled_at service_uninstalled agent_removed_at removed_agent_ids owned_agent_absent other_agents_untouched terraform_destroy_completed_at destroy_exit destroy_interrupted destroy_retried absence_verified_at terraform_state_empty resource_group_absent vm_absent os_disk_absent public_ip_absent before_operating_expiry",
            "local_checks": "controller_tests_normal_passed controller_tests_optimized_passed network_denied ordinary_file_writes_denied ci_run_claimed capture_ocr earlier_ocr_tool_failures_preserved human_visual_privacy_reviewed",
            "submission": "new_slots_captured configuration_image_is_post_registration_readback registration_terminal_captured screenshot_7_remains_historical_run_1 human_visual_privacy_reviewed learner_reflection_supplied assignment_complete",
        }
        for key, fields in schema.items():
            self.assertEqual(set(self.receipt if key is None else self.receipt[key]), set(fields.split()), key)
        self.assertEqual(self.receipt["schema_version"], 1)
        self.assertEqual(self.receipt["assignment"], "week-10-assignment-01")
        self.assertEqual(self.receipt["status"], "registration_service_manual_run_verified_cleaned_up")
        self.assertIs(self.receipt["assistant_operated"], True)
        encoded = json.dumps(self.receipt)
        self.assertNotRegex(encoded, r"(?:/Users/|\.private/|controller\.pat|BEGIN [A-Z ]*PRIVATE KEY|Bearer |Basic )")

    def test_original_png_hashes_sizes_dimensions_and_all_chunk_crcs(self):
        for capture in self.bundle["captures"]:
            suffix, digest, size, dimensions = EXPECTED[capture["slot"]]
            self.assertEqual(capture["path"], f"screenshots/assignment-01-screenshot-{capture['slot']:02d}-{suffix}.png")
            raw = (WEEK / capture["path"]).read_bytes()
            self.assertEqual((capture["sha256"], capture["bytes"], capture["dimensions"]), (digest, size, dimensions))
            self.assertEqual((hashlib.sha256(raw).hexdigest(), len(raw)), (digest, size))
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
            offset, kinds = 8, []
            while offset < len(raw):
                self.assertGreaterEqual(len(raw) - offset, 12)
                length = struct.unpack_from(">I", raw, offset)[0]
                end = offset + length + 12
                self.assertLessEqual(end, len(raw))
                kind, payload = raw[offset + 4:offset + 8], raw[offset + 8:end - 4]
                self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, struct.unpack_from(">I", raw, end - 4)[0])
                if kind == b"IHDR":
                    self.assertEqual(length, 13)
                    self.assertEqual(list(struct.unpack_from(">II", payload)), dimensions)
                if kind == b"IEND":
                    self.assertEqual(length, 0)
                kinds.append(kind)
                offset = end
            self.assertEqual((kinds[0], kinds[-1]), (b"IHDR", b"IEND"))
            self.assertEqual((kinds.count(b"IHDR"), kinds.count(b"IEND")), (1, 1))
            self.assertIn(b"IDAT", kinds)

    def test_exact_placement_and_manifest_do_not_claim_current_health(self):
        manifest = json.loads((WEEK / "self-hosted-agent/evidence/manifest.json").read_text())
        self.assertIs(manifest["live_verified"], False)
        self.assertEqual(self.brief.count("- [ ]"), 8)
        self.assertNotIn("Add your screenshot here.", self.brief)
        for capture in self.bundle["captures"]:
            slot = capture["slot"]
            section = re.search(r"^#### Screenshot " + str(slot) + r" — [^\n]+\n(.*?)(?=\n---)", self.brief, re.M | re.S).group(1)
            self.assertEqual(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", section), [capture["path"]])
            self.assertIn(f"<!-- BEGIN WEEK10 CAPTURE A1-S{slot} -->", section)
            self.assertIn("Full-size content/privacy review is user-attested", section)
            self.assertIn("(evidence/a1-human-review-2026-09-19.json)", section)
            self.assertIn("subsequently", section)
            entry = manifest["screenshots"][slot - 1]
            self.assertIs(entry["captured"], True)
            self.assertEqual(entry["status"], "captured_user_review_attested")
            for key in ("path", "sha256", "captured_at"):
                self.assertEqual(entry[key], capture[key])
            self.assertEqual(entry["run_url"], capture["source_url"])

    def test_source_urls_and_human_entry_are_not_token_observations(self):
        for capture in self.bundle["captures"]:
            if capture["slot"] < 6:
                self.assertEqual(capture["source_kind"], "native_terminal")
                self.assertIsNone(capture["source_url"])
            else:
                self.assertEqual(capture["source_kind"], "native_browser")
                self.assertEqual(capture["source_url"], "https://dev.azure.com/aneneeze2021/_settings/agentpools?poolId=11&view=agents")
        registration = self.receipt["registration"]
        self.assertEqual(registration["entry_mode"], "human_direct_to_vendor")
        self.assertEqual((registration["vendor_exit"], registration["agent_id"], registration["pool_id"]), (0, 18, 11))
        self.assertEqual(registration["agent_name"] + "-vm", self.receipt["vm"]["name"])
        self.assertIs(registration["user_reported_completion"], True)
        self.assertIsNone(registration["pat_sent_to_hidden_prompt"])
        for key in ("pat_entry_observed", "stored_pat_forwarded_to_registration", "raw_terminal_output_retained", "credential_file_contents_read"):
            self.assertIs(registration[key], False)
        self.assertIs(registration["credential_file_owner_and_mode_verified"], True)

    def test_one_real_run_binds_source_and_log_not_screenshot_7(self):
        run = self.receipt["manual_run"]
        self.assertEqual((run["id"], run["definition_id"], run["definition_revision"], run["runs_queued_in_this_trial"]), (2, 1, 4, 1))
        self.assertEqual((run["reason"], run["status"], run["result"]), ("manual", "completed", "succeeded"))
        self.assertEqual(run["commands_verified"], ["uname -a", "whoami", "df -h"])
        self.assertEqual(run["whoami"], "azdoagent")
        self.assertEqual(run["source_commit"], "aef39187af3b62f0508f831b3282ac052ddb3dae")
        self.assertEqual(run["source_branch"], "refs/heads/main")
        source = (WEEK / "self-hosted-agent/azure-pipelines.yml").read_bytes()
        self.assertEqual((hashlib.sha256(source).hexdigest(), len(source)), (run["yaml_sha256"], run["yaml_bytes"]))
        self.assertEqual(run["task_log_sha256"], "d672641ec196bd9318a6ae26b27be905f3fa21cdac70229e6a7d0e5ff390c8c6")
        url = urlsplit(run["run_url"])
        self.assertEqual((url.scheme, url.netloc, url.path), ("https", "dev.azure.com", "/aneneeze2021/DMI-Week10/_build/results"))
        self.assertEqual(parse_qs(url.query), {"buildId": ["2"], "view": ["results"]})
        self.assertIsNone(url.username)
        self.assertIsNone(url.password)
        seventh = json.loads((WEEK / "self-hosted-agent/evidence/manifest.json").read_text())["screenshots"][6]
        self.assertEqual(parse_qs(urlsplit(seventh["run_url"]).query)["buildId"], ["1"])
        self.assertIn("screenshot 7 remains historical run 1", self.brief)

    def test_bounded_timeline_places_captures_before_independent_cleanup(self):
        auth, reg, service, run, cleanup = (self.receipt[k] for k in ("authorization", "registration", "service", "manual_run", "cleanup"))
        timeline = [auth["activated_at"], reg["vendor_completed_at"], reg["independent_agent_verification_at"], reg["user_reported_at"], service["verified_at"], run["queued_at"], run["started_at"], run["finished_at"]]
        timeline += [c["captured_at"] for c in self.bundle["captures"]]
        timeline += [cleanup["service_uninstalled_at"], cleanup["agent_removed_at"], cleanup["terraform_destroy_completed_at"], cleanup["absence_verified_at"], auth["expires_at"]]
        parsed = list(map(timestamp, timeline))
        self.assertTrue(all(a < b for a, b in zip(parsed, parsed[1:])))
        self.assertEqual((timestamp(auth["expires_at"]) - timestamp(auth["activated_at"])).total_seconds(), 3600)
        self.assertEqual(auth["maximum_minutes"], 60)
        self.assertIs(auth["fresh_approval_received"], True)
        self.assertIs(auth["retired"], True)
        self.assertIs(auth["authorizes_future_runtime"], False)
        self.assertIs(auth["enforced_spending_cap"], False)
        self.assertIsNone(auth["actual_billed_cost_usd"])
        for key in ("service_uninstalled", "owned_agent_absent", "other_agents_untouched", "terraform_state_empty", "resource_group_absent", "vm_absent", "os_disk_absent", "public_ip_absent", "before_operating_expiry"):
            self.assertIs(cleanup[key], True)
        self.assertEqual(cleanup["removed_agent_ids"], [18])
        self.assertEqual(cleanup["destroy_exit"], 0)
        self.assertIs(cleanup["destroy_interrupted"], False)
        self.assertIs(cleanup["destroy_retried"], False)

    def test_nonroot_service_package_and_limited_pat_claims(self):
        vm, service, package = (self.receipt[k] for k in ("vm", "service", "package"))
        self.assertEqual((vm["cloud"], vm["region"], vm["os"], vm["architecture"]), ("Azure", "uksouth", "Ubuntu 22.04", "x86_64"))
        self.assertEqual((vm["agent_account"], service["user"]), ("azdoagent", "azdoagent"))
        for key in ("ssh_host_fingerprint_authenticated", "agent_sudo_denied", "agent_password_locked"):
            self.assertIs(vm[key], True)
        self.assertEqual((service["active_state"], service["sub_state"], service["main_pid"]), ("active", "running", 2221))
        self.assertIs(service["online_verified_during_trial"], True)
        self.assertIs(service["current_online_agent_claimed"], False)
        self.assertEqual(package["version"], "5.279.0")
        self.assertEqual(package["published_sha256"], "6e3352e1dc44c924cd85840df279f21c200e6365596a7c38f3087015262555dc")
        for key in ("download_hash_matched", "listener_version_verified", "required_libraries_resolved"):
            self.assertIs(package[key], True)
        self.assertIs(package["dependency_installer_executed"], False)
        limits = self.receipt["pat_and_isolation_limits"]
        for key, value in limits.items():
            self.assertIs(value, key in {"existing_full_access_pat_reuse_explicitly_approved", "only_definition_1_authorized_in_visible_yaml_pool_permissions"})

    def test_local_checks_do_not_complete_human_requirements(self):
        checks, submission = self.receipt["local_checks"], self.receipt["submission"]
        self.assertEqual((checks["controller_tests_normal_passed"], checks["controller_tests_optimized_passed"]), (106, 106))
        for key in ("network_denied", "ordinary_file_writes_denied", "earlier_ocr_tool_failures_preserved"):
            self.assertIs(checks[key], True)
        self.assertIn("CPU-only", checks["capture_ocr"])
        self.assertIs(checks["ci_run_claimed"], False)
        self.assertIs(checks["human_visual_privacy_reviewed"], False)
        self.assertEqual(submission["new_slots_captured"], [4, 5, 6])
        for key in ("configuration_image_is_post_registration_readback", "screenshot_7_remains_historical_run_1"):
            self.assertIs(submission[key], True)
        for key in ("registration_terminal_captured", "human_visual_privacy_reviewed", "learner_reflection_supplied", "assignment_complete"):
            self.assertIs(submission[key], False)
        self.assertIn("Learner input still required", self.brief)
        self.assertIn("Least-privilege PAT compliance is not claimed", self.brief)

    def test_prior_attempt_receipts_are_byte_immutable(self):
        expected = {
            "self-hosted-agent/runtime-2026-09-18.json": "202313ad1c78db9eb164688b78f8a10677625861d8e54d088649143e0772cb2f",
            "self-hosted-agent/runtime-2026-09-19.json": "0f71b0a09ad10068cc362cae56600b185cf63df20000dafba623e0e0164fbb3f",
            "evidence/a1-vm-ssh-2026-09-19.json": "3fd88fc744c85096e2f75b5d73264e43860d36b41a2ef17747ea0f5ca8907620",
        }
        for path, digest in expected.items():
            self.assertEqual(hashlib.sha256((WEEK / path).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
