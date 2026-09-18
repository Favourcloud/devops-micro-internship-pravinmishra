"""Offline policy structure and metadata tests, not an AWS IAM simulator."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("operator_review", ROOT / "operator/review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
FIXTURE = json.loads((ROOT / "operator/review.example.json").read_text())


def actions(value):
    return {value} if isinstance(value, str) else set(value)


class OperatorTests(unittest.TestCase):
    def test_renderer_matches_templates_and_is_not_evidence(self):
        result = review.render(FIXTURE)
        self.assertTrue(result["source_only"])
        self.assertFalse(result["live_verified"])
        self.assertFalse(result["bootstrap_access_enabled"])
        for policy in result["policies"].values():
            self.assertLessEqual(len(json.dumps(policy, separators=(",", ":"))), 6144)
            self.assertNotIn("${", json.dumps(policy))
        self.assertEqual(FIXTURE["expires_at"], "2000-01-01T04:00:00Z")

    def test_only_exact_metadata_is_accepted(self):
        cases = [{}, [], {**FIXTURE, "token": "never-echo-this"}, {**FIXTURE, "account_id": 1},
                 {**FIXTURE, "lease_id": "../../secret"}, {**FIXTURE, "oidc_issuer": "https://example.invalid/*"},
                 {**FIXTURE, "expires_at": "2000-02-31T00:00:00Z"},
                 {**FIXTURE, "approved_at": "2000-01-01T00:00:00+00:00"}]
        for value in cases:
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError) as error:
                review.render(value)
            self.assertNotIn("never-echo-this", str(error.exception))

    def test_fixed_window_limits(self):
        for end in ("2000-01-01T00:00:00Z", "1999-12-31T23:59:59Z", "2000-01-02T00:00:01Z"):
            with self.subTest(end=end), self.assertRaises(ValueError):
                review.render({**FIXTURE, "expires_at": end})
        review.render({**FIXTURE, "expires_at": "2000-01-02T00:00:00Z"})
        for issuer in (FIXTURE["oidc_issuer"].replace("login.microsoftonline", "login-microsoftonline"),
                       FIXTURE["oidc_issuer"].replace("v2.0", "v2x0")):
            with self.subTest(issuer=issuer), self.assertRaises(ValueError):
                review.render({**FIXTURE, "oidc_issuer": issuer})

    def test_mfa_expiry_and_no_escalation_actions(self):
        policy = review.render(FIXTURE)["policies"]["operator-policy"]
        statements = {s["Sid"]: s for s in policy["Statement"]}
        self.assertEqual(statements["RequireMFA"]["Condition"], {"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}})
        self.assertEqual(statements["ExpireWithoutRenewal"]["Condition"]["DateGreaterThanEquals"]["aws:CurrentTime"], FIXTURE["expires_at"])
        allowed = set().union(*(actions(s["Action"]) for s in policy["Statement"] if s["Effect"] == "Allow"))
        self.assertEqual(allowed, actions(statements["NoOtherAPIs"]["NotAction"]))
        self.assertFalse(allowed & {"iam:PassRole", "sts:AssumeRole", "sts:GetFederationToken", "iam:CreateUser",
                                    "iam:CreateAccessKey", "iam:CreatePolicyVersion", "iam:DeletePolicy",
                                    "iam:DeleteRolePermissionsBoundary", "iam:AttachRolePolicy", "iam:UpdateLoginProfile"})
        self.assertFalse(any("*" in action or action.startswith("ec2:") for action in allowed))
        for statement in policy["Statement"]:
            if statement["Effect"] == "Allow" and statement["Resource"] == "*":
                self.assertEqual(statement["Sid"], "IdentityAndIssuerInventory")

    def test_role_writes_require_exact_boundary(self):
        result = review.render(FIXTURE)
        statement = next(s for s in result["policies"]["operator-policy"]["Statement"] if s["Sid"] == "ManageOnlyBoundedRole")
        self.assertEqual(statement["Resource"], result["cleanup_role_arn"])
        self.assertEqual(statement["Condition"], {"StringEquals": {"iam:PermissionsBoundary": result["runtime_permissions_boundary_arn"]}})
        self.assertIn("iam:PutRolePolicy", statement["Action"])
        self.assertIn("iam:CreateRole", statement["Action"])
        source = (ROOT / "bootstrap/aws/main.tf").read_text()
        self.assertIn("permissions_boundary = var.runtime_permissions_boundary_arn", source)

    def test_runtime_boundary_cannot_administer_iam_and_survives_expiry(self):
        statements = review.render(FIXTURE)["policies"]["runtime-boundary"]["Statement"]
        self.assertEqual(statements[0]["Effect"], "Deny")
        self.assertEqual(actions(statements[0]["NotAction"]), {"ec2:Describe*", "ec2:DeleteVpc", "sts:GetCallerIdentity"})
        self.assertEqual(statements[1]["Condition"], {"StringNotEquals": {"aws:RequestedRegion": "eu-west-2"}})
        self.assertEqual(statements[3]["Condition"]["StringEquals"]["ec2:ResourceTag/cleanup_lease"], FIXTURE["lease_id"])
        self.assertNotIn("aws:CurrentTime", json.dumps(statements))

    def test_login_only_approved_account_region_remote_client(self):
        statements = review.render(FIXTURE)["policies"]["operator-policy"]["Statement"]
        statement = next(s for s in statements if s["Sid"] == "RemoteBrowserLogin")
        self.assertEqual(statement["Resource"], "arn:aws:signin:eu-west-2:000000000001:oauth2/public-client/remote")
        self.assertEqual(actions(statement["Action"]), {"signin:AuthorizeOAuth2Access", "signin:CreateOAuth2Token"})

    def test_cli_version_gate(self):
        for version in ("aws-cli/2.26.1 Python/3.13.3", "aws-cli/2.31.99", "aws-cli/1.99.0", "aws-cli/3.0.0", "garbage"):
            self.assertFalse(review.supports_browser_login(version), version)
        for version in ("aws-cli/2.32.0", "aws-cli/2.40.1 Python/3.13.3"):
            self.assertTrue(review.supports_browser_login(version), version)

    def test_exact_identity_check_never_claims_permissions_or_mfa(self):
        document = {"Account": FIXTURE["account_id"], "Arn": review.render(FIXTURE)["operator_arn"], "UserId": "AIDA" + "A" * 17}
        result = review.verify_identity(document, FIXTURE["account_id"], FIXTURE["lease_id"])
        self.assertTrue(result["identity_matches"])
        self.assertFalse(result["mfa_verified"])
        self.assertFalse(result["bootstrap_permissions_verified"])
        self.assertNotIn("UserId", result)
        for arn in ("arn:aws:iam::000000000001:root", "arn:aws:sts::000000000001:federated-user/fixture",
                    "arn:aws:sts::000000000001:assumed-role/other/test", "arn:aws:iam::000000000009:user/dmi-w10-bootstrap-abcdef123456"):
            with self.subTest(arn=arn), self.assertRaises(ValueError):
                review.verify_identity({**document, "Arn": arn}, FIXTURE["account_id"], FIXTURE["lease_id"])
        with self.assertRaises(ValueError):
            review.verify_identity({**document, "Credentials": {}}, FIXTURE["account_id"], FIXTURE["lease_id"])

    def test_handoff_shell_examples_parse_without_execution(self):
        text = (ROOT / "operator/README.md").read_text()
        blocks = re.findall(r"^[ \t]*```(?:sh|bash)\n(.*?)^[ \t]*```", text, re.S | re.M)
        self.assertEqual(len(blocks), 2)
        for block in blocks:
            result = subprocess.run(["/bin/bash", "-n"], input=block, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AWS_SHARED_CREDENTIALS_FILE=/dev/null", text)
        self.assertIn("AWS_LOGIN_CACHE_DIRECTORY=", text)
        self.assertIn("never run it standalone", text.replace("**", ""))

    def test_root_exception_does_not_broaden_resource_or_policy_scope(self):
        text = "\n".join(p.read_text() for p in (ROOT / "operator/aws").glob("*.tf"))
        resources = set(re.findall(r'^resource "([^"]+)" "([^"]+)"', text, re.M))
        self.assertEqual(resources, {("terraform_data", "authorization"),
                                     ("aws_iam_policy", "runtime_boundary"),
                                     ("aws_iam_policy", "operator"),
                                     ("aws_iam_user", "operator"),
                                     ("aws_iam_user_policy_attachment", "operator")})
        self.assertRegex(text, r'variable "root_bootstrap_approval" \{[\s\S]*?default\s*=\s*null')
        self.assertIn('timeadd(var.root_bootstrap_approval.approved_at, "1h")', text)
        self.assertIn('timecmp(timestamp(), var.root_bootstrap_approval.expires_at) < 0', text)
        self.assertIn('var.administrator_arn == "arn:aws:iam::${var.account_id}:root"', text)
        self.assertIn('var.mfa_enrolled_and_verified', text)
        for phase in ("bootstrap", "canary"):
            variables = (ROOT / phase / "aws/variables.tf").read_text()
            self.assertNotIn("root_bootstrap_approval", variables)
        readme = (ROOT / "operator/README.md").read_text()
        self.assertIn("not an IAM restriction or revocation of root credentials", readme)
        self.assertIn("local state alone is not independent custody", readme)
        self.assertIn("Creation-time Terraform preconditions are not a destroy authorization mechanism", readme)

    def test_no_credentials_provisioners_or_network_in_source(self):
        files = list((ROOT / "operator/aws").glob("*.tf"))
        text = "\n".join(p.read_text() for p in files)
        for forbidden in ('resource "aws_iam_access_key"', 'resource "aws_iam_user_login_profile"',
                          'resource "aws_iam_virtual_mfa_device"', "provisioner", 'resource "aws_instance"'):
            self.assertNotIn(forbidden, text)
        tree = ast.parse((ROOT / "operator/review.py").read_text())
        imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
        self.assertFalse(imports & {"subprocess", "socket", "requests", "urllib", "boto3"})


if __name__ == "__main__":
    unittest.main()
