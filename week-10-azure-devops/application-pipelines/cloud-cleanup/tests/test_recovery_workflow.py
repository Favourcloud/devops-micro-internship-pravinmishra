"""Offline contract for an inert fixture-review template, not hosted recovery proof."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "recovery/review-fixtures.github-actions.yml.example"
SOURCE_COMMIT = "e027755ef2d33e0145dd1476d48201da4aa4f4cb"
CHECKOUT_COMMIT = "d23441a48e516b6c34aea4fa41551a30e30af803"
PREFIX = "week-10-azure-devops/application-pipelines/cloud-cleanup/"
FILES = {
    "recovery/review.py": "6da4c270d9b092da56b235bf6fe593f36c8fc565367140c301b4679ae1f6baf1",
    "recovery/request.example.json": "d629cae03ae934e67913e9e2ece2b2fd33a30ec8d422f275a834b1e03b4d351e",
    "tests/test_recovery.py": "d377c43a1c5764e3f75503caef072f4a67b60192786a89b9d7916440852ebb6f",
    "bootstrap/aws/main.tf": "36bc902c756d753619ef90a70493bed344da33976a1440fae4133b764457e291",
    "bootstrap/azure/main.tf": "7ffe165689d1dfd3ce3ae978058737264e61c76292ec444d08b1e658000ed139",
}
GUARD = ("${{ false && github.event_name == 'workflow_dispatch' && "
         "github.ref == 'refs/heads/main' && github.event.repository.private == true && "
         "github.repository == 'REPLACE_WITH_APPROVED_OWNER/REPLACE_WITH_APPROVED_PRIVATE_RECOVERY_REPOSITORY' }}")
COMMAND = rf"""set -euo pipefail
printf '%s\n' 'SYNTHETIC FIXTURES ONLY: not state custody, cloud access, teardown or deployment evidence.'
test "$(git -c core.fsmonitor=false rev-parse HEAD)" = {SOURCE_COMMIT}
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent /usr/bin/python3 -I -B \
  -m unittest discover -q \
  -s {PREFIX}tests -p test_recovery.py
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent /usr/bin/python3 -I -B -O \
  -m unittest discover -q \
  -s {PREFIX}tests -p test_recovery.py
"""
EXPECTED = {
    "name": "Week10 recovery fixtures only - not live recovery",
    "on": {"workflow_dispatch": None},
    "permissions": {},
    "jobs": {"fixture_review": {
        "name": "Synthetic structural tests - not recovery acceptance",
        "if": GUARD,
        "runs-on": "ubuntu-24.04",
        "timeout-minutes": 5,
        "permissions": {"contents": "read"},
        "steps": [
            {"name": "Read only the frozen public fixture source",
             "uses": "actions/checkout@" + CHECKOUT_COMMIT,
             "with": {
                 "repository": "Favourcloud/devops-micro-internship-pravinmishra",
                 "ref": SOURCE_COMMIT, "path": "reviewed-source", "fetch-depth": 1,
                 "persist-credentials": False, "set-safe-directory": False,
                 "submodules": False, "lfs": False, "sparse-checkout-cone-mode": False,
                 "sparse-checkout": "".join(PREFIX + name + "\n" for name in FILES),
             }},
            {"name": "Run only synthetic fixtures with a cleared environment",
             "working-directory": "reviewed-source", "shell": "bash", "run": COMMAND},
        ],
    }},
}
PARSER = r'''
require "yaml"
require "json"
raw = STDIN.read
visit = lambda do |node|
  if node.is_a?(Psych::Nodes::Mapping)
    keys = node.children.each_slice(2).map do |key, _|
      raise "non_scalar_key" unless key.is_a?(Psych::Nodes::Scalar)
      key.value
    end
    raise "duplicate_key" unless keys.length == keys.uniq.length
  end
  Array(node.children).each { |child| visit.call(child) }
end
visit.call(Psych.parse_stream(raw))
puts JSON.generate(Psych.safe_load(raw))
'''


def parse_yaml(text):
    result = subprocess.run(["/usr/bin/ruby", "-e", PARSER], input=text,
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


class RecoveryWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = TEMPLATE.read_text()
        cls.document = parse_yaml(cls.raw)

    def assert_contract(self, document):
        self.assertEqual(json.dumps(document, sort_keys=True),
                         json.dumps(EXPECTED, sort_keys=True))

    def check_mutations(self, mutations):
        for path, key, value in mutations:
            with self.subTest(path=path, key=key, value=value):
                document = copy.deepcopy(self.document)
                target = document
                for part in path:
                    target = target[part]
                target[key] = value
                with self.assertRaises(AssertionError):
                    self.assert_contract(document)

    def test_exact_inert_private_manual_contract(self):
        self.assert_contract(self.document)
        self.assertNotIn(".github", TEMPLATE.parts)
        self.assertTrue(TEMPLATE.name.endswith(".yml.example"))

    def test_frozen_sparse_inputs_match_public_source(self):
        for name, expected in FILES.items():
            with self.subTest(path=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_command_is_syntax_checked_not_executed(self):
        script = self.document["jobs"]["fixture_review"]["steps"][1]["run"]
        self.assertEqual(script, COMMAND)
        result = subprocess.run(["/bin/bash", "-n"], input=script,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_activation_and_scope_expansion_fail_the_contract(self):
        job = ("jobs", "fixture_review")
        self.check_mutations([
            ((), "on", {"push": None}),
            ((), "on", {"schedule": [{"cron": "0 * * * *"}]}),
            ((), "permissions", {"id-token": "write"}),
            ((), "env", {"UNREVIEWED_INPUT": "fixture"}),
            (job, "if", GUARD.replace("false &&", "true &&", 1)),
            (job, "if", GUARD.replace("github.ref == 'refs/heads/main' && ", "")),
            (job, "if", "${{ false }}"),
            (job, "runs-on", "self-hosted"),
            (job, "timeout-minutes", 60),
            (job, "permissions", {"contents": "write"}),
            (job, "environment", "unapproved-cloud-environment"),
        ])

    def test_checkout_credentials_refs_and_extra_files_fail_the_contract(self):
        step = ("jobs", "fixture_review", "steps", 0)
        settings = step + ("with",)
        self.check_mutations([
            (step, "uses", "actions/checkout@v6"),
            (settings, "repository", "fixture/foreign-source"),
            (settings, "ref", "main"),
            (settings, "token", "${{ secrets.SHARED_PAT }}"),
            (settings, "persist-credentials", True),
            (settings, "persist-credentials", 0),
            (settings, "submodules", True),
            (settings, "sparse-checkout", ".private\n"),
            (settings, "path", ".."),
        ])

    def test_runtime_commands_and_additional_steps_fail_the_contract(self):
        job = ("jobs", "fixture_review")
        step = job + ("steps", 1)
        self.check_mutations([
            (step, "run", COMMAND + "terraform apply\n"),
            (step, "run", COMMAND.replace(" -I -B", "")),
            (step, "run", COMMAND.replace("-p test_recovery.py", "-p test_*.py")),
            (step, "working-directory", "/tmp"),
            (job, "steps", self.document["jobs"]["fixture_review"]["steps"] +
             [{"uses": "actions/upload-artifact@unreviewed"}]),
        ])

    def test_duplicate_keys_and_ambiguous_on_are_rejected(self):
        with self.assertRaises(subprocess.CalledProcessError):
            parse_yaml(self.raw + "\npermissions: {}\n")
        with self.assertRaises(AssertionError):
            self.assert_contract(parse_yaml(self.raw.replace('"on":', 'on:', 1)))

    def test_documentation_keeps_live_gates_separate(self):
        text = (ROOT / "recovery/README.md").read_text()
        for phrase in (TEMPLATE.name, SOURCE_COMMIT, CHECKOUT_COMMIT,
                       "not an installed recovery controller", "not a network sandbox",
                       "No hosted run is claimed", "19 September 2026, 18:18:03 UTC",
                       "No bootstrap teardown executor is delivered here"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
