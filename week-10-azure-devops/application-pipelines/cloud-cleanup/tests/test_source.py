"""Source scope, original brief preservation and native syntax checks; no cloud access."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEEK = ROOT.parents[1]
CONTRACT_SPEC = importlib.util.spec_from_file_location("brief_contract", WEEK / "submission/brief_contract.py")
CONTRACT = importlib.util.module_from_spec(CONTRACT_SPEC)
CONTRACT_SPEC.loader.exec_module(CONTRACT)
BRIEFS = {
    "assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md": "84cabf42cd42171267280ac5c32092c85134f1bd419072362ece9bfe9901e6cd",
    "assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md": "d64a31f43971a5ab8c911bf1110a9a4e0ae41a990550ed14fa0690fd75a6358a",
    "assignment-03-automate-react-app-deployment-using-azure-devops-cicd.md": "e4e45d2a65b75b1ba1af3286ecf490a27b820c1f34b9110299bc7daf47657624",
    "assignment-04-automate-epicbook-deployment-with-dual-pipelines.md": "f9a2155ca0782a90e70998a007f618a0031f3c3bf6196aa5c4bfd64457bfdad4",
    "assignment-05-ai-assisted-azure-devops-dual-pipeline-failure-triage.md": "16cae5c90b596b27249e2760c229a3c53d9c50d607bd95a78bdea951eabe35c9",
}


class SourceTests(unittest.TestCase):
    def test_all_five_original_requirement_hashes_preserved(self):
        for name, expected in BRIEFS.items():
            with self.subTest(brief=name):
                raw = (WEEK / name).read_bytes()
                raw = CONTRACT.restore_original_prompts(raw, name)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_canary_roots_cannot_create_workload_vms(self):
        for cloud, kind in (("azure", "azurerm_resource_group"), ("aws", "aws_vpc")):
            text = "\n".join(path.read_text() for path in (ROOT / "canary" / cloud).glob("*.tf"))
            self.assertEqual(set(re.findall(r'^resource "([^"]+)"', text, re.M)), {"terraform_data", kind})
            self.assertNotIn("provisioner", text)
            self.assertNotIn("user_data", text)
        self.assertNotIn("ec2:TerminateInstances", (ROOT / "bootstrap/aws/main.tf").read_text())

    def test_worker_no_shell_execution_or_automatic_creation(self):
        text = (ROOT / "worker.py").read_text()
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self.assertFalse(isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"})
                for keyword in node.keywords:
                    if keyword.arg == "shell":
                        self.assertIsInstance(keyword.value, ast.Constant)
                        self.assertFalse(keyword.value.value)
        for forbidden in ("-auto-approve", "controller.pat", "AWS_PROFILE", '"terminate-instances"', '"group", "delete"'):
            self.assertNotIn(forbidden, text)
        self.assertIn('token_file.unlink(missing_ok=True)', text)
        self.assertIn('"AWS_SHARED_CREDENTIALS_FILE": "/dev/null"', text)

    def test_yaml_scripts_parse_without_execution(self):
        for path in ROOT.glob("*.azure-pipelines.yml"):
            parsed = subprocess.run(["/usr/bin/ruby", "-e", 'require "yaml"; require "json"; puts JSON.generate(Psych.safe_load(File.read(ARGV[0])))', str(path)],
                                    capture_output=True, check=True)
            document = json.loads(parsed.stdout)
            self.assertEqual(document["trigger"], "none")
            self.assertEqual(document["pr"], "none")
            def check(value):
                if isinstance(value, dict):
                    for key, child in value.items():
                        if key in {"bash", "inlineScript"}:
                            result = subprocess.run(["/bin/bash", "-n"], input=child.encode(), capture_output=True)
                            self.assertEqual(result.returncode, 0, result.stderr)
                            for program in re.findall(r"python3 -I -B -c '([^']+)'", child):
                                compile(program, "inline-source-validation", "exec")
                        else:
                            check(child)
                elif isinstance(value, list):
                    for child in value:
                        check(child)
            check(document)

    def test_claim_probe_only_emits_allowlisted_metadata(self):
        import base64
        spec = importlib.util.spec_from_file_location("probe", ROOT / "probe_claims.py")
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        claims = {"iss": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0",
                  "sub": "fixture/exact-connection", "aud": "api://AzureADTokenExchange", "extra": "must-not-be-emitted"}
        token = "synthetic." + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=") + ".not-a-signature"
        result = probe.metadata(token)
        self.assertEqual(set(result), {"issuer", "subject", "authorized_party"})
        self.assertIsNone(result["authorized_party"])
        self.assertNotIn("must-not-be-emitted", json.dumps(result))
        self.assertNotIn(token, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
