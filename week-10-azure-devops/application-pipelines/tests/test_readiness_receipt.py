import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReadinessReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "readiness-2026-09-18.json").read_text())

    def test_read_access_is_not_claimed_as_management_or_write_access(self):
        ado = self.data["azure_devops"]
        self.assertIs(ado["authentication_verified"], True)
        self.assertIs(ado["private_project_verified"], True)
        self.assertEqual(ado["online_agent_count"], 0)
        self.assertEqual(ado["repository_list_http_status"], 401)
        self.assertEqual(ado["ssh_connection_list_http_status"], 401)
        for name in ("management_access_verified", "write_permissions_verified", "pat_scopes_and_server_expiry_verified", "scope_or_account_permission_cause_confirmed", "organization_permissions_changed_by_this_check"):
            self.assertIs(ado[name], False)
        self.assertEqual(set(ado), {
            "observed_at", "authentication_verified", "private_project_verified", "pool_id", "pipeline_id",
            "online_agent_count", "repository_list_http_status", "ssh_connection_list_http_status",
            "management_access_verified", "write_permissions_verified", "pat_scopes_and_server_expiry_verified",
            "organization_permissions_changed_by_this_check", "scope_or_account_permission_cause_confirmed",
        })

    def test_personalization_is_not_an_import_build_render_or_deployment(self):
        prepared = self.data["static_personalization"]
        source = json.loads((ROOT / "sources.json").read_text())["sources"]["static"]
        self.assertEqual(prepared["source_commit"], source["commit"])
        self.assertEqual(prepared["source_sha256"], source["index_html_sha256"])
        self.assertRegex(prepared["candidate_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotEqual(prepared["candidate_sha256"], prepared["source_sha256"])
        for field in ("all_other_source_bytes_unchanged", "upstream_script_blocks_unchanged", "static_payload_contract_passed"):
            self.assertIs(prepared[field], True)
        for field in ("javascript_executed", "browser_rendering_verified", "azure_repos_imported", "deployed"):
            self.assertIs(prepared[field], False)
        self.assertEqual(self.data["status"], "pre-deployment-blocked")
        self.assertIs(self.data["assignment_evidence"], False)
        self.assertEqual(self.data["outcome"], {
            "application_repository_created": False, "application_pipeline_run": False,
            "cloud_resources_created": False, "screenshots_captured": 0, "assignment_complete": False,
        })

    def test_transport_source_review_is_not_runtime_host_authentication(self):
        review = self.data["ssh_transport_review"]
        self.assertIs(review["source_review_only"], True)
        for field in ("tasks_commit", "ssh2_reference_commit", "sftp_client_reference_commit"):
            self.assertRegex(review[field], r"^[a-f0-9]{40}$")
        for field in ("host_verifier_configured_in_reviewed_tasks", "known_hosts_input_exposed_by_reviewed_tasks", "service_installed_task_packages_examined", "authenticated_transport_verified", "live_use_approved"):
            self.assertIs(review[field], False)


if __name__ == "__main__":
    unittest.main()
