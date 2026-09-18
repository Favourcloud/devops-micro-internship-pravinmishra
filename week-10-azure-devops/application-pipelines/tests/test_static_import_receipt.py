import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StaticImportReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "static-import-2026-09-18.json").read_text())

    def test_read_access_recovery_does_not_claim_unverified_permissions(self):
        reads = self.data["azure_devops_reads"]
        self.assertEqual(set(reads), {
            "observed_at", "authentication_verified", "private_project_verified",
            "repository_list_http_status", "repository_count_before_import",
            "ssh_connection_list_http_status", "ssh_connection_count", "online_agent_count",
            "pat_scopes_and_server_expiry_verified", "service_connection_write_permission_verified",
            "organization_permissions_changed_by_assistant",
        })
        for field in ("authentication_verified", "private_project_verified"):
            self.assertIs(reads[field], True)
        for field in ("repository_list_http_status", "ssh_connection_list_http_status"):
            self.assertEqual(reads[field], 200)
        for field in ("ssh_connection_count", "online_agent_count"):
            self.assertEqual(reads[field], 0)
        for field in ("pat_scopes_and_server_expiry_verified", "service_connection_write_permission_verified", "organization_permissions_changed_by_assistant"):
            self.assertIs(reads[field], False)

    def test_import_is_pinned_and_name_only_remote_edit_is_distinct(self):
        repo = self.data["static_repository"]
        source = json.loads((ROOT / "sources.json").read_text())["sources"]["static"]
        prepared = json.loads((ROOT / "readiness-2026-09-18.json").read_text())["static_personalization"]
        self.assertEqual(repo["source_commit"], source["commit"])
        self.assertEqual(repo["source_index_sha256"], source["index_html_sha256"])
        self.assertEqual(repo["remote_index_sha256"], prepared["candidate_sha256"])
        self.assertEqual(repo["personalized_commit"], "8bfa3682a7440f12791085c1d4d0aa0f7fbcb4fb")
        self.assertNotEqual(repo["personalized_commit"], repo["source_commit"])
        self.assertEqual(repo["import_status"], "completed")
        self.assertEqual(repo["visibility"], "private")
        self.assertEqual(repo["branch"], "refs/heads/main")
        self.assertEqual(repo["only_changed_path"], "/index.html")
        self.assertEqual(repo["url"], "https://dev.azure.com/aneneeze2021/DMI-Week10/_git/Azure-Static-Website")
        for field in ("imported_main_matched_source_commit", "remote_content_verified", "remote_parent_verified", "remote_git_changes_verified", "all_bytes_except_learner_paragraph_unchanged"):
            self.assertIs(repo[field], True)
        self.assertIs(repo["instructor_javascript_changed"], False)
        self.assertEqual(repo["application_pipeline_definition_count"], 0)

    def test_repository_progress_is_not_deployment_or_assignment_completion(self):
        self.assertEqual(self.data["status"], "repository-ready-deployment-blocked")
        self.assertIs(self.data["assignment_evidence"], False)
        outcome = self.data["outcome"]
        positives = {"repository_created", "repository_imported", "personalization_committed_and_read_back"}
        negatives = {"application_build_or_test_run", "application_pipeline_run", "ssh_service_connection_created", "authenticated_pipeline_transport_verified", "cloud_resources_created", "application_deployed", "javascript_executed", "browser_rendering_verified", "social_publication_performed", "assignment_complete"}
        self.assertEqual(set(outcome), positives | negatives | {"screenshots_captured"})
        for field in positives:
            self.assertIs(outcome[field], True)
        for field in negatives:
            self.assertIs(outcome[field], False)
        self.assertEqual(outcome["screenshots_captured"], 0)
        self.assertEqual(len(self.data["remaining_a2_gates"]), 8)

    def test_receipt_has_bounded_metadata_and_local_test_provenance(self):
        self.assertEqual(set(self.data), {"schema_version", "observed_at", "status", "operator", "assignment_evidence", "azure_devops_reads", "static_repository", "local_operation_tests", "outcome", "remaining_a2_gates"})
        self.assertEqual(self.data["operator"], "authorized assistant")
        self.assertEqual(set(self.data["static_repository"]), {
            "url", "visibility", "source_url", "source_commit", "source_index_sha256", "created_at",
            "import_request_id", "import_status", "import_completed_observed_at", "imported_main_matched_source_commit",
            "branch", "personalized_commit", "push_id", "personalized_at", "only_changed_path", "remote_index_sha256",
            "remote_content_verified_at", "remote_content_verified", "remote_parent_verified", "remote_git_changes_verified",
            "all_bytes_except_learner_paragraph_unchanged", "instructor_javascript_changed", "application_pipeline_definition_count",
        })
        tests = self.data["local_operation_tests"]
        self.assertEqual(set(tests), {"passed", "credentials_used", "network_denied", "filesystem_writes_denied", "scope"})
        self.assertEqual(tests["passed"], 9)
        self.assertIs(tests["credentials_used"], False)
        self.assertIs(tests["network_denied"], True)
        self.assertIs(tests["filesystem_writes_denied"], True)
        self.assertIn("not application tests or pipeline results", tests["scope"])

    def test_prior_failed_reads_and_local_only_preparation_are_preserved(self):
        earlier = json.loads((ROOT / "readiness-2026-09-18.json").read_text())
        self.assertEqual(earlier["azure_devops"]["repository_list_http_status"], 401)
        self.assertEqual(earlier["azure_devops"]["ssh_connection_list_http_status"], 401)
        self.assertIs(earlier["static_personalization"]["azure_repos_imported"], False)
        self.assertLess(earlier["azure_devops"]["observed_at"], self.data["azure_devops_reads"]["observed_at"])
        self.assertLess(self.data["azure_devops_reads"]["observed_at"], self.data["static_repository"]["created_at"])


if __name__ == "__main__":
    unittest.main()
