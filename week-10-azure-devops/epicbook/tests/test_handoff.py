import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "ci" / "validate_handoff.py"
SPEC = importlib.util.spec_from_file_location("handoff", HELPER)
HANDOFF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HANDOFF)

# Synthetic input only: these addresses are never contacted or claimed as owned.
VALID = {
    "app_public_ip": "8.8.4.4",
    "backend_ansible_host": "10.20.2.4",
    "backend_private_ip": "10.20.2.4",
    "mysql_fqdn": "fixture-db.mysql.database.azure.com",
}


def run_cli(raw, args=None):
    output, errors = io.StringIO(), io.StringIO()
    code = HANDOFF.main([] if args is None else args, io.BytesIO(raw), output, errors)
    return code, output.getvalue(), errors.getvalue()


class HandoffTests(unittest.TestCase):
    def test_valid_private_ssh(self):
        self.assertEqual(HANDOFF.validate_handoff(VALID), VALID)

    def test_valid_public_ssh(self):
        data = dict(VALID, backend_ansible_host="8.8.8.8")
        self.assertEqual(HANDOFF.validate_handoff(data), data)

    def test_rfc1918_ranges(self):
        for address in ("10.0.0.1", "172.16.0.1", "172.31.255.254", "192.168.0.1"):
            with self.subTest(address=address):
                data = dict(VALID, backend_private_ip=address, backend_ansible_host=address)
                self.assertEqual(HANDOFF.validate_handoff(data), data)

    def test_input_not_mutated(self):
        data = copy.deepcopy(VALID)
        HANDOFF.inventory(data)
        self.assertEqual(data, VALID)

    def test_exact_fields_required(self):
        for key in VALID:
            with self.subTest(key=key):
                data = dict(VALID)
                del data[key]
                with self.assertRaises(HANDOFF.HandoffError):
                    HANDOFF.validate_handoff(data)
        with self.assertRaises(HANDOFF.HandoffError):
            HANDOFF.validate_handoff(dict(VALID, password="not-a-real-secret"))

    def test_wrong_top_level_types(self):
        for value in ([], None, True, "data", 12):
            with self.subTest(value=value), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(value)

    def test_wrong_value_types(self):
        for value in (None, True, 7, [], {}, "", "a" * 254):
            for key in VALID:
                with self.subTest(value=value, key=key), self.assertRaises(HANDOFF.HandoffError):
                    HANDOFF.validate_handoff(dict(VALID, **{key: value}))

    def test_terraform_output_objects_rejected(self):
        outputs = {key: {"sensitive": False, "type": "string", "value": value}
                   for key, value in VALID.items()}
        with self.assertRaises(HANDOFF.HandoffError):
            HANDOFF.validate_handoff(outputs)

    def test_nonpublic_frontend_rejected(self):
        for address in ("10.0.0.1", "172.31.0.1", "192.168.1.1", "127.0.0.1", "0.0.0.0",
                        "169.254.169.254", "100.64.0.1", "192.0.2.1", "198.51.100.1",
                        "203.0.113.1", "224.0.0.1", "240.0.0.1", "255.255.255.255"):
            with self.subTest(address=address), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(dict(VALID, app_public_ip=address))

    def test_nonprivate_backend_rejected(self):
        for address in ("8.8.8.8", "172.15.255.255", "172.32.0.1", "192.169.0.1", "100.64.0.1",
                        "127.0.0.1", "169.254.1.1", "192.0.2.1", "0.0.0.0", "224.0.0.1"):
            with self.subTest(address=address), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(dict(VALID, backend_private_ip=address))

    def test_unsafe_ssh_addresses_rejected(self):
        for address in ("0.0.0.0", "127.0.0.1", "169.254.169.254", "100.64.0.1", "192.0.2.1",
                        "224.0.0.1", "255.255.255.255", "host.example", "user@10.20.2.4"):
            with self.subTest(address=address), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(dict(VALID, backend_ansible_host=address))

    def test_distinct_hosts_required(self):
        with self.assertRaises(HANDOFF.HandoffError):
            HANDOFF.validate_handoff(dict(VALID, backend_ansible_host=VALID["app_public_ip"]))

    def test_private_transport_must_match_backend(self):
        with self.assertRaises(HANDOFF.HandoffError):
            HANDOFF.validate_handoff(dict(VALID, backend_ansible_host="10.20.2.5"))

    def test_ipv4_canonical_form(self):
        for value in (" 8.8.4.4", "8.8.4.4\n", "008.8.4.4", "8.8.4", "8.8.4.999", "::1",
                      "::ffff:8.8.4.4", "8.8.4.4/32", "8.8.4.4:22", "８.８.４.４"):
            with self.subTest(value=value), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(dict(VALID, app_public_ip=value))

    def test_mysql_host_name_bounds(self):
        for name in ("abc", "a" * 63, "a-b"):
            host = name + ".mysql.database.azure.com"
            self.assertEqual(HANDOFF.validate_handoff(dict(VALID, mysql_fqdn=host))["mysql_fqdn"], host)
        for name in ("ab", "a" * 64, "-ab", "ab-", "Abc", "a_b"):
            with self.subTest(name=name), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(dict(VALID, mysql_fqdn=name + ".mysql.database.azure.com"))

    def test_mysql_suffix_and_urls(self):
        for host in ("db.example.com", "fixture-db.mysql.database.azure.com.evil.example",
                     "fixture-db.mysql.database.azure.com.", "fixture-db.mysql.database.azure.com:3306",
                     "mysql://user:dummy@fixture-db.mysql.database.azure.com/bookstore", "10.20.3.4",
                     "fixture-db.privatelink.mysql.database.azure.com", "fixture-db.mysql.database.azure.com\n"):
            with self.subTest(host=host), self.assertRaises(HANDOFF.HandoffError):
                HANDOFF.validate_handoff(dict(VALID, mysql_fqdn=host))

    def test_command_fragments_rejected_without_echo(self):
        for value in ("$(not-executed)", "8.8.4.4;not-executed", "x\n##vso[task.setvariable]fixture",
                      "@secret-file", "-oProxyCommand=not-executed", "dummy-credential-sentinel"):
            for key in VALID:
                with self.subTest(value=value, key=key):
                    code, output, errors = run_cli(json.dumps(dict(VALID, **{key: value})).encode())
                    self.assertEqual(code, 2)
                    self.assertEqual(output, "")
                    self.assertNotIn(value, errors)

    def test_duplicate_keys(self):
        raw = json.dumps(VALID)[:-1] + ',"app_public_ip":"8.8.8.8"}'
        code, output, errors = run_cli(raw.encode())
        self.assertEqual((code, output), (2, ""))
        self.assertIn("duplicate", errors)
        self.assertNotIn("8.8.8.8", errors)

    def test_nonstandard_constants(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            raw = json.dumps(VALID).replace('"8.8.4.4"', value)
            self.assertEqual(run_cli(raw.encode())[0], 2)

    def test_malformed_utf8_json(self):
        for raw in (b"", b"\xff", b"{", b"[]", b"null", b'{"dummy-sentinel":', b"{} {}",
                    b"\xef\xbb\xbf{}", b"[" * 1500 + b"0" + b"]" * 1500):
            with self.subTest(length=len(raw)):
                code, output, errors = run_cli(raw)
                self.assertEqual((code, output), (2, ""))
                self.assertNotIn("dummy-sentinel", errors)

    def test_bounded_input(self):
        raw = json.dumps(VALID).encode()
        self.assertEqual(run_cli(raw + b" " * (HANDOFF.MAX_BYTES - len(raw)))[0], 0)
        self.assertEqual(run_cli(raw + b" " * (HANDOFF.MAX_BYTES + 1 - len(raw)))[0], 2)
        source = io.BytesIO(b"x" * 100000)
        self.assertEqual(HANDOFF.main([], source, io.StringIO(), io.StringIO()), 2)
        self.assertEqual(source.tell(), HANDOFF.MAX_BYTES + 1)

    def test_unknown_keys_never_echoed(self):
        code, output, errors = run_cli(json.dumps(dict(VALID, **{"dummy-secret-key": "dummy-secret-value"})).encode())
        self.assertEqual((code, output), (2, ""))
        self.assertNotIn("dummy-secret", errors)

    def test_bad_arguments_do_not_read_or_echo(self):
        source = io.BytesIO(b"{}")
        output, errors = io.StringIO(), io.StringIO()
        self.assertEqual(HANDOFF.main(["dummy-secret-argument"], source, output, errors), 2)
        self.assertEqual(source.tell(), 0)
        self.assertNotIn("dummy-secret-argument", errors.getvalue())
        self.assertEqual(output.getvalue(), "")

    def test_io_errors_never_echoed(self):
        class BrokenSource:
            def read(self, _limit):
                raise OSError("dummy-secret-path")
        output, errors = io.StringIO(), io.StringIO()
        self.assertEqual(HANDOFF.main([], BrokenSource(), output, errors), 2)
        self.assertEqual(output.getvalue(), "")
        self.assertNotIn("dummy-secret-path", errors.getvalue())

    def test_success_is_only_allowlisted_json(self):
        code, output, errors = run_cli(json.dumps(VALID).encode())
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(json.loads(output), VALID)

    def test_real_cli_success(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(HELPER), "--inventory"],
                                input=json.dumps(VALID), text=True, capture_output=True, timeout=10,
                                env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"})
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(json.loads(result.stdout), HANDOFF.inventory(VALID))

    def test_real_cli_rejects_unset_example(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(HELPER)],
                                input=(ROOT / "handoff.example.json").read_bytes(), capture_output=True, timeout=10,
                                env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"})
        self.assertEqual((result.returncode, result.stdout), (2, b""))
        self.assertTrue(result.stderr.startswith(b"handoff rejected:"))

    def test_inventory_exact_structure(self):
        expected = {"all": {"children": {
            "frontend": {"hosts": {"epicbook_frontend": {"ansible_host": "8.8.4.4"}}},
            "backend": {"hosts": {"epicbook_backend": {"ansible_host": "10.20.2.4"}}},
        }, "vars": {"backend_private_ip": "10.20.2.4", "mysql_fqdn": VALID["mysql_fqdn"]}}}
        code, output, errors = run_cli(json.dumps(VALID).encode(), ["--inventory"])
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(json.loads(output), expected)

    def test_inventory_validates_before_rendering(self):
        with self.assertRaises(HANDOFF.HandoffError):
            HANDOFF.inventory(dict(VALID, backend_private_ip="unsafe-sentinel"))

    def test_output_deterministic(self):
        first = json.dumps(VALID).encode()
        second = json.dumps(dict(reversed(list(VALID.items())))).encode()
        self.assertEqual(run_cli(first), run_cli(second))
        self.assertEqual(run_cli(first, ["--inventory"]), run_cli(second, ["--inventory"]))


class SourceContractTests(unittest.TestCase):
    def test_example_remains_unset_and_rejected(self):
        raw = (ROOT / "handoff.example.json").read_bytes()
        self.assertEqual(set(json.loads(raw)), HANDOFF.FIELDS)
        self.assertTrue(all(value is None for value in json.loads(raw).values()))
        self.assertEqual(run_cli(raw)[0], 2)

    def test_helper_has_only_allowlisted_stdlib_imports(self):
        tree = ast.parse(HELPER.read_text())
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {"ipaddress", "json", "re", "sys"})
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree)))
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(calls & {"open", "exec", "eval", "compile", "__import__", "input"})
        attributes = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(attributes & {"write_bytes", "write_text", "open", "system", "popen", "run", "connect", "urlopen"})

    def test_public_source_coordinates_and_hash_shape(self):
        data = json.loads((ROOT / "sources.json").read_text())
        self.assertEqual(set(data), {"schema_version", "assignment", "learner", "source_reviewed_on",
                                     "upstream", "locked_dependencies", "manual_handoff_fields", "this_delivery"})
        self.assertEqual(set(data["upstream"]), {"repository", "commit", "file_sha256"})
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["assignment"], 4)
        self.assertEqual(data["learner"], "Eze Favour")
        self.assertEqual(data["upstream"]["repository"], "https://github.com/pravinmishraaws/theepicbook")
        self.assertEqual(data["upstream"]["commit"], "763becebb8d3f5663a76bb30facddc25be63cfd5")
        self.assertEqual(len(data["upstream"]["file_sha256"]), 13)
        for digest in data["upstream"]["file_sha256"].values():
            self.assertRegex(digest, r"\A[0-9a-f]{64}\Z")
        self.assertEqual(set(data["manual_handoff_fields"]), HANDOFF.FIELDS)
        self.assertEqual(data["locked_dependencies"], {"lockfile_version": 3, "mysql2": "2.1.0",
                                                      "sequelize": "6.3.0", "express": "4.17.1", "express-handlebars": "5.0.0"})

    def test_no_live_completion_or_evidence_claim(self):
        status = json.loads((ROOT / "sources.json").read_text())["this_delivery"]
        self.assertEqual(status, {"application_imported": False, "cloud_resources_created": False,
                                 "application_executed": False, "pipelines_run": False,
                                 "assignment_complete": False, "evidence": []})

    def test_original_briefs_bytes_and_requirements_preserved(self):
        cases = (
            ("assignment-04-automate-epicbook-deployment-with-dual-pipelines.md",
             "f9a2155ca0782a90e70998a007f618a0031f3c3bf6196aa5c4bfd64457bfdad4", 40, 6),
            ("assignment-05-ai-assisted-azure-devops-dual-pipeline-failure-triage.md",
             "16cae5c90b596b27249e2760c229a3c53d9c50d607bd95a78bdea951eabe35c9", 33, 12),
        )
        for filename, expected, checkboxes, screenshots in cases:
            with self.subTest(filename=filename):
                raw = (ROOT.parent / filename).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
                self.assertEqual(len(re.findall(rb"^[*-] \[ \] ", raw, re.M)), checkboxes)
                self.assertEqual([int(x) for x in re.findall(r"^### Screenshot (\d+) —".encode(), raw, re.M)],
                                 list(range(1, screenshots + 1)))

    def test_documented_limits_and_secret_policy(self):
        text = (ROOT / "README.md").read_text()
        for statement in ("Offline preparation, not a completed assignment", "does not establish",
                          "no_log: true", "diff: false", "Saved plans can contain secrets",
                          "actual supplied", "No npm or lint run is claimed", "JAWSDB_URL"):
            self.assertIn(statement, text)
        self.assertNotIn("StrictHostKeyChecking=no", text)
        ignored = (ROOT / ".gitignore").read_text().splitlines()
        for pattern in (".private/", "handoff.local.json", "inventory.local.json", "*.tfstate", "*.tfplan", "*.pem", "*.key", ".env"):
            self.assertIn(pattern, ignored)


if __name__ == "__main__":
    unittest.main()
