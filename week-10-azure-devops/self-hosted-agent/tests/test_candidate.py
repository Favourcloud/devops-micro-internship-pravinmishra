import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_candidate", PROJECT / "validate_candidate.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
FIXTURE = PROJECT / "tests/fixtures/simulated-candidate.json"


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = json.loads(FIXTURE.read_text())

    def test_simulated_input_only_passes_offline_checks(self):
        self.assertEqual(CHECKER.validate(self.candidate), [])

    def test_null_example_fails_closed(self):
        self.assertTrue(CHECKER.validate(json.loads((PROJECT / "candidate.example.json").read_text())))

    def test_unknown_or_missing_keys_rejected_at_every_level(self):
        for section in (None, "host", "package"):
            for operation in ("add", "remove"):
                with self.subTest(section=section, operation=operation):
                    candidate = copy.deepcopy(self.candidate)
                    target = candidate if section is None else candidate[section]
                    if operation == "add":
                        target["token"] = "SYNTHETIC-DO-NOT-LOG"
                    else:
                        target.pop(next(iter(target)))
                    self.assertTrue(CHECKER.validate(candidate))

    def test_malformed_section_types_do_not_crash(self):
        for value in (None, [], "wrong", 123, True):
            self.assertTrue(CHECKER.validate(value))
            for section in ("host", "package"):
                candidate = copy.deepcopy(self.candidate)
                candidate[section] = value
                self.assertTrue(CHECKER.validate(candidate))

    def test_schema_requires_integer_one(self):
        for value in (True, 1.0, "1", 2, None):
            self.candidate["schema_version"] = value
            self.assertIn("candidate.schema_version", CHECKER.validate(self.candidate))

    def test_organization_url_rejects_credentials_and_non_https(self):
        for value in ("http://dev.azure.com/example", "https://secret@dev.azure.com/example",
                      "https://dev.azure.com/example?token=secret", "https://dev.azure.com.evil/example",
                      "https://dev.azure.com/example/#fragment", "$(command)", {}):
            self.candidate["organization_url"] = value
            self.assertIn("candidate.organization_url", CHECKER.validate(self.candidate))

    def test_dedicated_names_reject_default_placeholder_and_shell_text(self):
        for key in ("pool_name", "agent_name"):
            for value in ("Default", "default", "__choose_approved_pool__", "$(command)", "x\ny", {}, None):
                candidate = copy.deepcopy(self.candidate)
                candidate[key] = value
                self.assertIn("candidate." + key, CHECKER.validate(candidate))

    def test_supported_ubuntu_versions_and_architectures(self):
        for version in ("22.04", "24.04"):
            self.candidate["host"]["version_id"] = version
            self.assertEqual(CHECKER.validate(self.candidate), [])
        for machine in ("aarch64", "arm64"):
            candidate = copy.deepcopy(self.candidate)
            candidate["host"]["machine"] = machine
            candidate["package"]["architecture"] = "arm64"
            candidate["package"]["download_url"] = "https://download.agent.dev.azure.com/agent/5.279.0/vsts-agent-linux-arm64-5.279.0.tar.gz"
            candidate["package"]["sha256"] = "d97cb1286de41c97347a5da4f663daed70f65f9cdd4322f50f8cc7b4e2df9dd4"
            self.assertEqual(CHECKER.validate(candidate), [])

    def test_unsupported_hosts_rejected(self):
        for key, values in {"system": ["Darwin", "Windows"], "distribution": ["debian", "alpine"],
                            "version_id": ["20.04", "26.04", "latest"], "machine": ["i386", "armv7l"]}.items():
            for value in values:
                candidate = copy.deepcopy(self.candidate)
                candidate["host"][key] = value
                self.assertTrue(CHECKER.validate(candidate))

    def test_root_wrong_account_and_invalid_uid_rejected(self):
        for value in (0, -1, True, 1.5, "1001", None):
            self.candidate["host"]["uid"] = value
            self.assertIn("host.uid", CHECKER.validate(self.candidate))
        self.candidate["host"]["account"] = "root"
        self.assertIn("host.account", CHECKER.validate(self.candidate))

    def test_privileged_account_rejected(self):
        for groups in (["sudo"], ["docker"], ["lxd"], None, ""):
            candidate = copy.deepcopy(self.candidate)
            candidate["host"]["privileged_groups"] = groups
            self.assertIn("host.privilege", CHECKER.validate(candidate))
        for value in (True, None, 0, "false"):
            candidate = copy.deepcopy(self.candidate)
            candidate["host"]["sudo_allowed"] = value
            self.assertIn("host.privilege", CHECKER.validate(candidate))

    def test_disk_floor_and_git_minimum(self):
        for value in (2047, -1, True, 4096.0, None):
            self.candidate["host"]["free_disk_mib"] = value
            self.assertIn("host.free_disk_mib", CHECKER.validate(self.candidate))
        self.candidate["host"]["free_disk_mib"] = 2048
        self.candidate["host"]["git_version"] = "2.9.0"
        self.assertEqual(CHECKER.validate(self.candidate), [])
        for value in ("2.8.9", "not a version", "2.43.0; command", 2):
            self.candidate["host"]["git_version"] = value
            self.assertIn("host.git_version", CHECKER.validate(self.candidate))

    def test_required_commands_exact_allowlist(self):
        for value in ([], ["bash"], [None], [{}], "bash", None,
                      list(CHECKER.COMMANDS) + ["printenv"], ["bash"] * len(CHECKER.COMMANDS)):
            self.candidate["host"]["commands"] = value
            self.assertIn("host.commands", CHECKER.validate(self.candidate))

    def test_package_url_metadata_digest_and_review_are_required(self):
        invalid = {
            "version": ["latest", "3.1.0", "5.279.0/../", None],
            "architecture": ["osx-x64", "musl-x64", None],
            "download_url": ["http://download.agent.dev.azure.com/agent/file", "https://evil.example/file", None],
            "metadata_url": ["https://github.com/other/azure-pipelines-agent/releases/tag/v5.279.0", None],
            "sha256": ["abc", "0" * 63, "G" * 64, None],
            "compatibility_reviewed": [False, None, "true", 1],
        }
        for key, values in invalid.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    candidate = copy.deepcopy(self.candidate)
                    candidate["package"][key] = value
                    self.assertIn("package." + key, CHECKER.validate(candidate))

    def test_architecture_mismatch_rejected(self):
        self.candidate["host"]["machine"] = "aarch64"
        self.assertIn("package.host_architecture", CHECKER.validate(self.candidate))

    def test_hash_comparison_uses_only_supplied_bytes(self):
        data = b"synthetic bytes for hash unit test; not a package\n" * 100000
        self.assertTrue(CHECKER.archive_matches(io.BytesIO(data), hashlib.sha256(data).hexdigest()))
        self.assertFalse(CHECKER.archive_matches(io.BytesIO(data + b"changed"), hashlib.sha256(data).hexdigest()))
        self.assertFalse(CHECKER.archive_matches(io.BytesIO(data), "bad digest"))

    def test_duplicate_keys_rejected(self):
        for raw in ('{"token": 1, "token": 2}', '{"host": {"uid": 0, "uid": 1}}'):
            with self.assertRaises(ValueError):
                json.loads(raw, object_pairs_hook=CHECKER.unique_object)

    def test_bounded_file_input_and_malformed_json(self):
        for raw in (b"x" * (CHECKER.MAX_CANDIDATE_BYTES + 1), b"{", b"\xff", b'{"x":1,"x":2}'):
            path = Mock()
            path.is_symlink.return_value = False
            path.is_file.return_value = True
            path.open.return_value = io.BytesIO(raw)
            with self.assertRaises(ValueError):
                CHECKER.read_candidate(path)

    def test_symlinks_and_nonfiles_rejected_before_read(self):
        for symlink, regular in ((True, True), (False, False)):
            path = Mock()
            path.is_symlink.return_value = symlink
            path.is_file.return_value = regular
            with self.assertRaises(ValueError):
                CHECKER.read_candidate(path)
            path.open.assert_not_called()

    def test_archive_cli_branches_without_filesystem_writes(self):
        for data, code, matched in ((b"unit bytes", 0, True), (b"different", 1, False)):
            candidate = copy.deepcopy(self.candidate)
            candidate["package"]["sha256"] = hashlib.sha256(b"unit bytes").hexdigest()
            output = io.StringIO()
            with patch.object(CHECKER, "read_candidate", return_value=candidate), \
                    patch.object(Path, "is_symlink", return_value=False), \
                    patch.object(Path, "is_file", return_value=True), \
                    patch.object(Path, "open", return_value=io.BytesIO(data)), \
                    patch("sys.stdout", output):
                self.assertEqual(CHECKER.main(["synthetic.json", "--archive", "synthetic.tar.gz"]), code)
            result = json.loads(output.getvalue())
            self.assertEqual(result["archive_checksum_matched"], matched)
            self.assertIs(result["live_verified"], False)

    def test_invalid_candidate_does_not_open_archive(self):
        output = io.StringIO()
        with patch.object(CHECKER, "read_candidate", return_value={}), \
                patch.object(Path, "open") as opened, patch("sys.stdout", output):
            self.assertEqual(CHECKER.main(["synthetic.json", "--archive", "synthetic.tar.gz"]), 1)
            opened.assert_not_called()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-B", str(PROJECT / "validate_candidate.py"), *map(str, args)],
                              capture_output=True, text=True, check=False, timeout=10)

    def test_cli_reports_no_live_verification(self):
        result = self.run_cli(FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "offline_checks_passed")
        self.assertIs(report["live_verified"], False)
        self.assertIs(report["archive_checksum_matched"], False)
        self.assertNotIn("example-organization", result.stdout)

    def test_cli_example_fails_and_unknown_arguments_are_private(self):
        self.assertEqual(self.run_cli(PROJECT / "candidate.example.json").returncode, 1)
        result = self.run_cli(FIXTURE, "--token", "SYNTHETIC-DO-NOT-LOG")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("SYNTHETIC-DO-NOT-LOG", result.stdout + result.stderr)

    def test_cli_read_errors_do_not_echo_path_or_input(self):
        for path in (PROJECT / "tests/fixtures/SYNTHETIC-DO-NOT-LOG.json", PROJECT / "README.md"):
            result = self.run_cli(path)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout), {"status": "invalid_input", "live_verified": False})
            self.assertNotIn("SYNTHETIC-DO-NOT-LOG", result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
