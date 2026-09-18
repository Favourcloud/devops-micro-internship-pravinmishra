"""Read-only Terraform source contracts, not provider schema or deployment evidence."""

import json
from pathlib import Path
import re
import subprocess
import unittest


APPLICATION = Path(__file__).resolve().parents[1]
REPO = APPLICATION.parents[1]
TERRAFORM = APPLICATION / "target" / "terraform"
ROOTS = ("aws", "azure")


def source(root):
    return "\n".join(path.read_text() for path in sorted((TERRAFORM / root).glob("*.tf")))


class TerraformTargetTests(unittest.TestCase):
    def test_hcl_is_parsed_and_formatted_by_existing_terraform(self):
        result = subprocess.run(
            [str(REPO / ".tools" / "terraform"), "fmt", "-check", "-recursive", str(TERRAFORM)],
            capture_output=True, timeout=30,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "CHECKPOINT_DISABLE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode() + result.stdout.decode())

    def test_examples_are_inert_and_exactly_match_declared_inputs(self):
        for root in ROOTS:
            with self.subTest(root=root):
                inputs = json.loads((TERRAFORM / root / "inputs.example.json").read_text())
                variables = set(re.findall(r'^variable "([^"]+)"', source(root), re.M))
                self.assertEqual(set(inputs), variables)
                self.assertEqual(inputs.pop("approval"), {
                    "live_execution_approved": False,
                    "approved_at": None,
                    "expires_at": None,
                    "estimated_total_usd": None,
                    "planning_allowance_usd": None,
                })
                self.assertTrue(all(value is None for value in inputs.values()))
                self.assertFalse(list((TERRAFORM / root).glob("*.auto.tfvars*")))

    def test_resource_scope_is_exactly_eight_per_cloud_and_one_shared_guard(self):
        expected = {
            "aws": {"aws_vpc", "aws_subnet", "aws_internet_gateway", "aws_route_table", "aws_route_table_association", "aws_security_group", "aws_key_pair", "aws_instance"},
            "azure": {"azurerm_resource_group", "azurerm_virtual_network", "azurerm_subnet", "azurerm_public_ip", "azurerm_network_security_group", "azurerm_network_interface", "azurerm_network_interface_security_group_association", "azurerm_linux_virtual_machine"},
            "guard": {"terraform_data"},
        }
        for root, types in expected.items():
            actual = re.findall(r'^resource "([^"]+)" "[^"]+"', source(root), re.M)
            self.assertEqual(set(actual), types)
            self.assertEqual(len(actual), len(types))

    def test_no_bootstrap_application_execution_or_extra_providers(self):
        for root in (*ROOTS, "guard"):
            text = source(root)
            self.assertNotRegex(text, r'(?m)^\s*(user_data|user_data_base64|custom_data|provisioner|connection)\b')
            self.assertNotRegex(text, r'(?m)^data "(external|http|local_file)"')
            self.assertNotRegex(text, r'(?m)^variable "[^\"]*(password|token|private_key)[^\"]*"')
            for forbidden in ("local-exec", "remote-exec", "config.sh", "npm ", "cloud-init", "tls_private_key", "null_resource"):
                self.assertNotIn(forbidden, text)

    def test_previous_reviewed_lockfiles_are_reused_without_changes(self):
        references = {
            "aws": REPO / "week-08-terraform/terraform-aws-vm/.terraform.lock.hcl",
            "azure": APPLICATION.parent / "self-hosted-agent/azure-vm/.terraform.lock.hcl",
        }
        for root, reference in references.items():
            lock = TERRAFORM / root / ".terraform.lock.hcl"
            self.assertEqual(lock.read_bytes(), reference.read_bytes())

    def test_state_plans_and_private_live_inputs_are_not_source(self):
        ignored = (TERRAFORM / ".gitignore").read_text().splitlines()
        for pattern in ("**/.terraform/", "**/.private/", "**/*.tfstate*", "**/*.tfplan", "**/*.tfvars", "**/*.tfvars.json"):
            self.assertIn(pattern, ignored)
        for root in ROOTS:
            self.assertIn('path = ".private/terraform.tfstate"', source(root))
            self.assertNotIn('backend "remote"', source(root))

    def test_guard_binds_approval_identity_scope_and_both_ssh_sources(self):
        for root, assignment, resource in (("aws", "week10-a2", "aws_vpc"), ("azure", "week10-a3", "azurerm_resource_group")):
            text = source(root)
            self.assertRegex(text, r'assignment\s*=\s*"' + assignment + '"')
            self.assertRegex(text, r'controller_ipv4_cidr\s*=\s*var.controller_ipv4_cidr')
            self.assertRegex(text, r'agent_ipv4_cidr\s*=\s*var.agent_ipv4_cidr')
            self.assertRegex(text, r'approval\s*=\s*var.approval')
            scope = text.split('resource "' + resource + '" "target" {')[1].split('\nresource ')[0]
            self.assertRegex(scope, r'depends_on\s*=\s*\[module.guard\]')
            self.assertIn("precondition {", scope)

    def test_expiry_is_checked_at_plan_and_apply_without_cleanup_timestamp_validation(self):
        text = source("guard")
        resource = text.split('resource "terraform_data" "authorization" {')[1]
        self.assertIn("var.approval.live_execution_approved", resource)
        self.assertIn("plantimestamp()", resource)
        self.assertIn("timestamp()", resource)
        self.assertIn('timeadd(var.approval.approved_at, "4h")', resource)
        self.assertIn("var.approval.planning_allowance_usd <= 10", text)
        self.assertNotIn("timestamp()", text.split('resource "terraform_data"')[0])

    def test_aws_is_non_root_bound_and_uses_exact_canonical_ami(self):
        text = source("aws")
        for required in ('allowed_account_ids = [var.account_id]', 'data.aws_caller_identity.current.arn == var.operator_arn', '!endswith(data.aws_caller_identity.current.arn, ":root")', 'owners = ["099720109477"]', 'values = [var.ami_id]', 'values = ["x86_64"]', 'ubuntu-noble-24.04-amd64-server-*'):
            self.assertIn(required, text)
        self.assertNotIn("most_recent", text)
        self.assertNotIn("iam_instance_profile", text)

    def test_aws_has_encrypted_small_disk_and_scoped_metadata(self):
        text = source("aws")
        for key, value in (("instance_type", '"t3.micro"'), ("encrypted", "true"), ("delete_on_termination", "true"), ("volume_size", "8"), ("http_tokens", '"required"'), ("http_put_response_hop_limit", "1"), ("instance_metadata_tags", '"disabled"'), ("cpu_credits", '"standard"')):
            self.assertRegex(text, r'(?m)^\s*' + key + r'\s*=\s*' + value + r'\s*$')

    def test_azure_context_is_exact_and_images_do_not_float(self):
        text = source("azure")
        for field in ("subscription_id", "tenant_id"):
            self.assertIn("data.azurerm_client_config.current." + field + " == var." + field, text)
        self.assertIn("data.azurerm_client_config.current.object_id == var.operator_object_id", text)
        self.assertRegex(text, r'resource_provider_registrations\s*=\s*"none"')
        self.assertRegex(text, r'use_msi\s*=\s*false')
        self.assertRegex(text, r'use_oidc\s*=\s*false')
        self.assertRegex(text, r'version\s*=\s*var.image_version')
        self.assertNotRegex(text, r'version\s*=\s*"latest"')

    def test_cloud_native_tests_are_mock_only_plans_not_evidence(self):
        for root, provider in (("aws", "aws"), ("azure", "azurerm")):
            text = (TERRAFORM / root / "tests/target.tftest.hcl").read_text()
            self.assertIn('mock_provider "' + provider + '"', text)
            commands = re.findall(r'(?m)^\s*command\s*=\s*(\w+)', text)
            self.assertGreater(len(commands), 0)
            self.assertEqual(set(commands), {"plan"})
        self.assertIn("Synthetic plan fixtures", (TERRAFORM / "azure/tests/target.tftest.hcl").read_text())
