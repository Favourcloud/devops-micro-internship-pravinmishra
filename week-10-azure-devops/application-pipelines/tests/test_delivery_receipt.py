from datetime import datetime, timedelta
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PipelineSourceReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "static-pipeline-source-2026-09-18.json").read_text())

    def test_exact_parent_four_files_and_directory_are_distinct(self):
        repo = self.data["repository"]
        imported = json.loads((ROOT / "static-import-2026-09-18.json").read_text())
        self.assertEqual(repo["parent_commit"], imported["static_repository"]["personalized_commit"])
        self.assertEqual(repo["prepared_commit"], "6b38993a18f75c2588803a42b6e7790c95e95b81")
        self.assertEqual(repo["source_revision"], "a9930bcd39168906681de4b7c30ebc0cba09eebf")
        self.assertEqual(repo["url"], imported["static_repository"]["url"])
        self.assertEqual(set(repo["only_added_files"]), {
            "/azure-pipelines.yml", "/ci/validate_site.py", "/ci/verify_remote.sh", "/ci/ssh_tunnel.py",
        })
        self.assertEqual(repo["added_directory"], "/ci")
        self.assertEqual(set(repo["original_blobs"]), {"/README.md", "/index.html"})
        for sha in repo["original_blobs"].values():
            self.assertRegex(sha, r"^[a-f0-9]{40}$")
        for path, asset in repo["only_added_files"].items():
            self.assertEqual(set(asset), {"source_path", "sha256"})
            self.assertEqual(asset["source_path"], "static.azure-pipelines.yml" if path == "/azure-pipelines.yml" else path.lstrip("/"))
            self.assertRegex(asset["sha256"], r"^[a-f0-9]{64}$")
        for field in ("exact_parent_verified", "exact_file_and_directory_changes_verified", "stored_source_hashes_verified", "original_application_blobs_unchanged"):
            self.assertIs(repo[field], True)

    def test_source_trigger_is_not_an_enabled_pipeline(self):
        self.assertEqual(self.data["status"], "pipeline-source-uploaded-execution-not-enabled")
        self.assertEqual(self.data["execution_gate"], {
            "application_pipeline_definition_count": 0, "application_build_count": 0,
            "existing_a1_definition_revision": 4,
            "a1_uses_separate_repository_and_unchanged_manual_yaml": True,
            "source_contains_all_branch_ci_trigger": True,
            "ssh_connection_id_is_unset_placeholder": True,
            "pipeline_created": False, "pipeline_enabled_or_queued": False,
        })
        self.assertIs(self.data["assignment_evidence"], False)
        self.assertEqual(self.data["outcome"], {
            "pipeline_source_uploaded_and_read_back": True,
            "instructor_javascript_changed_or_executed": False,
            "application_pipeline_run": False, "ssh_service_connection_created": False,
            "cloud_resources_created": False, "application_deployed": False,
            "screenshots_captured": 0, "assignment_complete": False,
        })

    def test_local_tests_are_not_application_results(self):
        self.assertEqual(self.data["local_operation_tests"], {
            "passed": 16, "credentials_used": False, "network_denied": True,
            "filesystem_writes_denied": True, "discard_only_exception": "/dev/null",
            "scope": "Exact-parent/add-only handoff, source hashes, CI drift, original blob preservation and no write retry; not application tests or pipeline results",
        })

    def test_metadata_has_no_unreviewed_fields(self):
        self.assertEqual(set(self.data), {"schema_version", "observed_at", "status", "operator", "assignment_evidence", "repository", "execution_gate", "local_operation_tests", "outcome"})
        self.assertEqual(set(self.data["repository"]), {
            "url", "visibility", "branch", "parent_commit", "prepared_commit", "push_id", "pushed_at",
            "source_revision", "only_added_files", "added_directory", "original_blobs", "exact_parent_verified",
            "exact_file_and_directory_changes_verified", "stored_source_hashes_verified", "original_application_blobs_unchanged",
        })
        self.assertEqual(self.data["operator"], "authorized assistant")
        self.assertLess(self.data["repository"]["pushed_at"], self.data["observed_at"])


class AwsSessionReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "aws-session-readiness-2026-09-18.json").read_text())

    def test_root_issuance_is_not_root_deployment_or_permanent_iam(self):
        issued = self.data["credential_issuance"]
        for field in ("root_use_explicitly_authorized", "root_used_only_for_sts_identity_and_issuance", "expected_issuer_account_verified", "expected_non_root_identity_independently_verified"):
            self.assertIs(issued[field], True)
        for field in ("permanent_iam_identity_or_key_created", "root_used_by_terraform_or_pipeline", "credential_values_published_or_forwarded_to_agent"):
            self.assertIs(issued[field], False)
        self.assertEqual(issued["requested_duration_seconds"], 3600)
        delta = datetime.fromisoformat(issued["credential_expiration"]) - datetime.fromisoformat(issued["identity_verified_at"])
        self.assertGreater(delta, timedelta(minutes=45))
        self.assertLessEqual(delta, timedelta(hours=1))
        self.assertEqual(issued["policy_characters"], 1856)
        self.assertRegex(issued["policy_sha256"], r"^[a-f0-9]{64}$")
        self.assertIn("not unique-prefix isolation", issued["policy_scope"])

    def test_dry_run_and_read_probes_are_not_complete_write_or_cleanup_proof(self):
        self.assertEqual(self.data["aws_checks"], {
            "region": "eu-west-2", "tagged_create_vpc_dry_run": "DryRunOperation",
            "untagged_create_vpc_dry_run": "UnauthorizedOperation",
            "other_region_describe_vpcs": "UnauthorizedOperation", "existing_a2_vpc_count": 0,
            "ami_id": "ami-03cf5768bcc686a8c",
            "ami_name": "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20260904",
            "canonical_ami_available_x86_64_hvm_ebs_verified": True, "standard_vcpu_quota": 5,
            "quota_usage_or_launch_capacity_verified": False, "all_apply_destroy_permissions_verified": False,
            "live_cleanup_tested": False,
        })
        self.assertEqual(self.data["outcome"], {
            "temporary_non_root_aws_session_created": True, "cloud_resources_created": False,
            "real_target_plan_generated": False, "agent_registered": False, "application_pipeline_run": False,
            "application_deployed": False, "screenshots_captured": 0, "assignment_complete": False,
        })
        self.assertIs(self.data["assignment_evidence"], False)
        self.assertEqual(self.data["status"], "temporary-session-verified-deployment-not-started")

    def test_one_hour_credentials_do_not_start_or_extend_resource_window(self):
        self.assertEqual(self.data["resource_window"], {
            "approved_hours": 24, "combined_planning_allowance_usd": 10,
            "provider_enforced_spending_cap": False, "activated": False,
            "activated_at": None, "expires_at": None, "cleanup_lead_minutes": 45,
            "credential_renewal_extends_resource_deadline": False,
        })
        tests = self.data["local_operation_tests"]
        self.assertEqual(set(tests), {"passed", "credentials_used", "network_denied", "filesystem_writes_denied", "scope"})
        self.assertEqual(tests["passed"], 16)
        self.assertIs(tests["credentials_used"], False)
        self.assertIs(tests["network_denied"], True)
        self.assertIs(tests["filesystem_writes_denied"], True)
        self.assertIn("not a full IAM simulator", tests["scope"])

    def test_allowlisted_metadata_excludes_credentials_and_controller_paths(self):
        self.assertEqual(set(self.data), {"schema_version", "observed_at", "status", "operator", "assignment_evidence", "credential_issuance", "aws_checks", "local_operation_tests", "resource_window", "outcome"})
        self.assertEqual(set(self.data["credential_issuance"]), {
            "root_use_explicitly_authorized", "root_used_only_for_sts_identity_and_issuance",
            "expected_issuer_account_verified", "expected_non_root_identity_independently_verified", "identity_verified_at",
            "requested_duration_seconds", "credential_expiration", "permanent_iam_identity_or_key_created",
            "root_used_by_terraform_or_pipeline", "credential_values_published_or_forwarded_to_agent",
            "policy_sha256", "policy_characters", "policy_scope",
        })
        self.assertEqual(self.data["operator"], "authorized assistant")
        for path in ("aws-session-readiness-2026-09-18.json", "static-pipeline-source-2026-09-18.json"):
            text = (ROOT / path).read_text()
            self.assertNotRegex(text, r"(?:AKIA|ASIA)[A-Z0-9]{16}")
            for forbidden in ("SecretAccessKey", "SessionToken", "AccessKeyId", "/Users/", "/home/", "PRIVATE KEY"):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
