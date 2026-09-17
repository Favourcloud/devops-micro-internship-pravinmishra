import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from urllib.parse import unquote, urlparse


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
BRIEF = PROJECT.parent / "assignment-02-deploy-a-virtual-machine-on-aws-with-public-network-using-terraform.md"
SOURCE = json.loads((PROJECT / "tests/assignment-source.json").read_text())


def protected_requirements_present(text):
    lines = [re.sub(r"^(\* )\[[xX]\]", r"\1[ ]", line) for line in text.splitlines()]
    position = 0
    for expected in SOURCE["protected_lines"]:
        try:
            position = lines.index(expected, position) + 1
        except ValueError:
            return False
    return True


class AssignmentContractTests(unittest.TestCase):
    def test_source_metadata_matches_baseline(self):
        baseline = subprocess.check_output(
            ["git", "show", f"{SOURCE['baseline_commit']}:{SOURCE['source_path']}"], cwd=REPO
        )
        self.assertEqual(hashlib.sha256(baseline).hexdigest(), SOURCE["baseline_sha256"])
        self.assertEqual(SOURCE["source_path"], str(BRIEF.relative_to(REPO)))
        self.assertIn("pravinmishraaws/", SOURCE["source_repository"])

    def test_every_original_requirement_preserved_in_order(self):
        self.assertTrue(protected_requirements_present(BRIEF.read_text()))

    def test_protection_allows_answers_and_future_images(self):
        text = BRIEF.read_text()
        text = text.replace("Add your screenshot here.", "![Genuine later capture](evidence/later.png)")
        text = re.sub(r"\* \[ \]", "* [x]", text)
        text = text.replace("**EC2 Public IP Address:**", "A verified field answer may be supplied later.\n\n**EC2 Public IP Address:**")
        self.assertTrue(protected_requirements_present(text))

    def test_protection_rejects_removed_rubric_item(self):
        text = BRIEF.read_text().replace("* Security group allowing HTTP on port `80`\n", "")
        self.assertFalse(protected_requirements_present(text))

    def test_ten_original_screenshot_headings_and_manifest(self):
        text = BRIEF.read_text()
        headings = re.findall(r"^#### Screenshot .+$", text, re.M)
        self.assertEqual(headings, SOURCE["screenshot_headings"])
        manifest = json.loads((PROJECT / "evidence/manifest.json").read_text())
        shots = manifest["screenshots"]
        self.assertEqual([s["number"] for s in shots], list(range(1, 11)))
        self.assertEqual(["#### " + s["requirement"] for s in shots], headings)
        self.assertEqual(manifest["learner"], "Eze Favour")
        for shot in shots:
            section = text.split("#### " + shot["requirement"], 1)[1].split("\n---", 1)[0]
            self.assertIn(shot["status"], ("pending", "captured"))
            if shot["status"] == "pending":
                self.assertIsNone(shot["file"])
                self.assertIn("Pending", section)
            else:
                image = (PROJECT / shot["file"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence"))
                self.assertTrue(image.is_file())
                self.assertIn(shot["file"], section)
                self.assertTrue(image.read_bytes().startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")))

    def test_markdown_links_local_files_and_external_syntax(self):
        for path in [BRIEF, PROJECT / "README.md"]:
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text()):
                parsed = urlparse(target)
                if parsed.scheme:
                    self.assertEqual(parsed.scheme, "https")
                    self.assertTrue(parsed.netloc)
                elif parsed.path:
                    destination = (path.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(destination.is_relative_to(REPO))
                    self.assertTrue(destination.is_file(), f"Missing link from {path.name}: {target}")

    def test_exact_resource_scope_and_outputs(self):
        main = (PROJECT / "main.tf").read_text()
        resources = re.findall(r'^resource "([^"]+)" "([^"]+)"', main, re.M)
        self.assertEqual(set(resources), {
            ("aws_vpc", "lab"), ("aws_subnet", "public"), ("aws_subnet", "private"),
            ("aws_internet_gateway", "lab"), ("aws_route_table", "public"), ("aws_route_table", "private"),
            ("aws_route_table_association", "public"), ("aws_route_table_association", "private"),
            ("aws_security_group", "web"), ("aws_key_pair", "lab"), ("aws_instance", "web"),
        })
        self.assertEqual(len(resources), 11)
        self.assertEqual(re.findall(r'^data "([^"]+)" "([^"]+)"', main, re.M), [("aws_ami", "ubuntu")])
        self.assertEqual(set(re.findall(r'^output "([^"]+)"', main, re.M)), {"public_ip", "instance_id", "website_url", "ssh_username", "ami_id"})
        self.assertRegex(main, r'provider "aws"\s*\{\s*region\s*=\s*var\.aws_region')
        self.assertRegex(main, r'depends_on\s*=\s*\[aws_route_table_association.public\]')
        self.assertIn('path = ".private/terraform.tfstate"', main)
        self.assertNotIn('"tls_private_key"', main)

    def test_all_terraform_tests_use_aws_mocks(self):
        tests = list((PROJECT / "tests").glob("*.tftest.hcl"))
        self.assertTrue(tests)
        for path in tests:
            self.assertEqual(re.findall(r'^mock_provider "([^"]+)"', path.read_text(), re.M), ["aws"])
            self.assertNotRegex(path.read_text(), r'^provider\s+"', path.name)

    def test_bootstrap_and_documented_bash_syntax(self):
        scripts = sorted((PROJECT / "scripts").glob("*.sh"))
        subprocess.run(["bash", "-n", *map(str, scripts)], check=True)
        for snippet in re.findall(r"```bash\n(.*?)\n```", (PROJECT / "README.md").read_text(), re.S):
            subprocess.run(["bash", "-n"], input=snippet, text=True, check=True)
        bootstrap = (PROJECT / "scripts/cloud-init.sh").read_text()
        for expected in (
            "set -Eeuo pipefail", "trap ", "for attempt in 1 2 3 4 5", "return 1", "DEBIAN_FRONTEND=noninteractive",
            "Acquire::Retries=3", "DPkg::Lock::Timeout=120", "install -y --no-install-recommends nginx curl ca-certificates",
            "nginx -t", "systemctl enable --now nginx", "systemctl is-active --quiet nginx", "curl --fail",
            "Eze Favour", "Nginx — Week 08 Assignment 2", "http://127.0.0.1/",
        ):
            self.assertIn(expected, bootstrap)
        self.assertNotIn("<script", bootstrap)

    def test_private_artifact_ignores(self):
        prefix = str(PROJECT.relative_to(REPO))
        names = [".private/state.json", ".terraform/plugin", ".offline/log", "secrets.tfvars", "inputs.tfvars.json",
                 "key.pem", "key.key", "id_ed25519", "lab.tfstate", "lab.tfstate.backup", "lab.tfplan", "debug.log"]
        for name in names:
            result = subprocess.run(["git", "check-ignore", "--quiet", "--", f"{prefix}/{name}"], cwd=REPO)
            self.assertEqual(result.returncode, 0, name)
        for name in [".terraform.lock.hcl", "terraform.tfvars.example"]:
            result = subprocess.run(["git", "check-ignore", "--quiet", "--", f"{prefix}/{name}"], cwd=REPO)
            self.assertEqual(result.returncode, 1, name)

    def test_owned_publishable_files_have_no_secret_material(self):
        files = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", str(BRIEF.relative_to(REPO)), str(PROJECT.relative_to(REPO))],
            cwd=REPO, text=True,
        ).splitlines()
        for name in set(files):
            path = REPO / name
            self.assertNotIn(path.suffix, (".pem", ".key", ".tfstate", ".tfplan", ".log", ".js"))
            if path.suffix in (".png", ".jpg", ".jpeg"):
                continue
            text = path.read_text()
            self.assertNotRegex(text, r"(?:AKIA|ASIA)[A-Z0-9]{16}")
            self.assertNotRegex(text, r"(?m)^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----$")
            self.assertNotRegex(text, r"arn:aws:[^\s]*:\d{12}:")
            self.assertTrue(set(re.findall(r"\b\d{12}\b", text)) <= {"099720109477"}, name)

    def test_offline_runner_clears_environment_and_cleans_temp_on_success(self):
        self.exercise_runner(fail=False)

    def test_offline_runner_cleans_temp_on_failure(self):
        self.exercise_runner(fail=True)

    def exercise_runner(self, fail):
        with tempfile.TemporaryDirectory(prefix="a2-contract-", dir="/tmp") as directory:
            temp = Path(directory)
            mirror = temp / "mirror/registry.terraform.io/hashicorp/aws/6.64.0"
            mirror.mkdir(parents=True)
            marker = temp / "observed-home"
            executable = temp / "terraform-stub"
            # Stub validates the runner boundary only; real Terraform is tested separately.
            executable.write_text(
                '#!/bin/bash\nset -eu\n'
                '[ -z "${AWS_ACCESS_KEY_ID+x}" ] && [ -z "${ARM_CLIENT_SECRET+x}" ] && [ -z "${TF_VAR_ssh_cidr+x}" ]\n'
                '[ "$AWS_EC2_METADATA_DISABLED" = true ] && [ "$AWS_CONFIG_FILE" = /dev/null ]\n'
                '[ "$AWS_SHARED_CREDENTIALS_FILE" = /dev/null ] && [ "$TF_INPUT" = 0 ]\n'
                '[ -d "$TF_DATA_DIR" ] && [ -d "$TMPDIR" ]\n'
                f'printf "%s" "$HOME" > "{marker}"\n'
                + ('exit 9\n' if fail else 'exit 0\n')
            )
            executable.chmod(0o700)
            environment = dict(os.environ, TERRAFORM_BIN=str(executable), AWS_PROVIDER_MIRROR=str(temp / "mirror"),
                               AWS_ACCESS_KEY_ID="TEST-NOT-A-CREDENTIAL", ARM_CLIENT_SECRET="TEST-NOT-A-SECRET", TF_VAR_ssh_cidr="INVALID")
            result = subprocess.run(["bash", str(PROJECT / "scripts/check-offline.sh")], env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 9 if fail else 0, result.stderr)
            home = Path(marker.read_text())
            self.assertTrue(str(home).startswith("/tmp/dmi-a2."))
            self.assertFalse(home.parent.exists(), "Temporary HOME/data/sockets must be cleaned")


if __name__ == "__main__":
    unittest.main()
