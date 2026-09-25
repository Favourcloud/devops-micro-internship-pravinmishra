"""Offline fixtures and source contracts; never connects to or configures a host."""

import ast
import base64
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import unittest

from test_pipelines import parse_yaml


TARGET = Path(__file__).resolve().parents[1] / "target"
spec = importlib.util.spec_from_file_location("target_inputs", TARGET / "validate_inputs.py")
inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs)
# Synthetic public-key bytes with no associated private key or deployment authorization.
KEY_BLOB = struct.pack(">I", 11) + b"ssh-ed25519" + struct.pack(">I", 32) + bytes(range(32))
PUBLIC_KEY = "ssh-ed25519 " + base64.b64encode(KEY_BLOB).decode("ascii")
FIXTURE = {
    "assignment": "week10-a2",
    "agent_ipv4": "8.8.8.8",
    "target_ipv4": "1.1.1.1",
    "deployment_public_key": PUBLIC_KEY,
    "tunnel_public_key": "ssh-ed25519 " + base64.b64encode(KEY_BLOB[:-32] + bytes(range(1, 33))).decode("ascii"),
}


class InputTests(unittest.TestCase):
    def reject(self, **changes):
        with self.assertRaises((ValueError, TypeError)):
            inputs.validate(dict(FIXTURE, **changes))

    def run_cli(self, raw, *args):
        return subprocess.run(
            ["/usr/bin/python3", "-I", "-B", str(TARGET / "validate_inputs.py"), *args],
            input=raw, capture_output=True, timeout=10,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"},
        )

    def test_both_assignments_accept_only_public_input_shape(self):
        for assignment in ("week10-a2", "week10-a3"):
            inputs.validate(dict(FIXTURE, assignment=assignment))

    def test_unfilled_example_is_not_authorization(self):
        example = json.loads((TARGET / "inputs.example.json").read_text())["week10_target"]
        self.assertTrue(all(value is None for value in example.values()))
        with self.assertRaises(ValueError):
            inputs.validate(example)

    def test_exact_fields_reject_credentials_and_unknown_settings(self):
        for extra in ("pat", "password", "private_key", "ansible_connection", "approved"):
            self.reject(**{extra: "synthetic-do-not-echo"})
        for missing in FIXTURE:
            value = dict(FIXTURE)
            del value[missing]
            with self.assertRaises(ValueError):
                inputs.validate(value)

    def test_non_objects_and_wrong_assignments_fail(self):
        for value in (None, [], "week10-a2", 1):
            with self.assertRaises(ValueError):
                inputs.validate(value)
        for value in (None, "a2", "week10-a4", "week10-a2\n", []):
            self.reject(assignment=value)

    def test_non_public_or_noncanonical_addresses_fail(self):
        for value in (None, 123, [], "localhost", "127.0.0.1", "10.0.0.1", "169.254.169.254", "192.0.2.1", "100.64.0.1", "224.0.0.1", "240.0.0.1", "0.0.0.0", "255.255.255.255", "::1", "2606:4700:4700::1111", "8.8.8.8/32", "08.8.8.8", "8.8.8.8\n"):
            for field in ("agent_ipv4", "target_ipv4"):
                with self.subTest(field=field, value=value):
                    self.reject(**{field: value})

    def test_agent_and_target_must_differ(self):
        self.reject(target_ipv4=FIXTURE["agent_ipv4"])

    def test_key_options_comments_private_keys_and_multiple_keys_fail(self):
        for key in (None, [], "", "-----BEGIN OPENSSH PRIVATE KEY-----", "command=whoami " + PUBLIC_KEY, PUBLIC_KEY + " comment", PUBLIC_KEY + "\n", PUBLIC_KEY + "\n" + PUBLIC_KEY, PUBLIC_KEY.replace("ssh-ed25519", "ssh-rsa")):
            with self.subTest(key=key):
                self.reject(deployment_public_key=key)

    def test_forwarding_key_must_be_valid_and_separate(self):
        for value in (PUBLIC_KEY, None, [], 'private-fixture', PUBLIC_KEY + ' comment'):
            self.reject(tunnel_public_key=value)

    def test_key_wire_structure_and_encoding_are_checked(self):
        for blob in (KEY_BLOB[:-1], KEY_BLOB + b"x", b"x" + KEY_BLOB[1:], KEY_BLOB[:15] + struct.pack(">I", 31) + KEY_BLOB[19:], KEY_BLOB[:-32] + bytes(32)):
            self.reject(deployment_public_key="ssh-ed25519 " + base64.b64encode(blob).decode("ascii"))
        self.reject(deployment_public_key="ssh-ed25519 " + "!" * 68)

    def test_cli_success_cannot_be_misread_as_live_verification(self):
        result = self.run_cli(json.dumps(FIXTURE).encode())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"target_input_shape_valid_not_live_verified\n")
        self.assertEqual(result.stderr, b"")

    def test_cli_failure_never_echoes_input(self):
        for raw in (b"synthetic-sensitive-value", b"\xff", b"[]", b"null", b"{" + b"x" * 4096, b"[" * 1500 + b"]" * 1500, json.dumps(dict(FIXTURE, pat="synthetic-do-not-echo")).encode()):
            result = self.run_cli(raw)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr, b"target_inputs_invalid\n")

    def test_duplicate_json_fields_fail_closed(self):
        raw = json.dumps(FIXTURE)[:-1] + ', "assignment": "week10-a3"}'
        self.assertEqual(self.run_cli(raw.encode()).returncode, 1)

    def test_cli_accepts_exact_example_wrapper_without_normalizing_duplicates(self):
        wrapped = json.dumps({"week10_target": FIXTURE})
        self.assertEqual(self.run_cli(wrapped.encode()).returncode, 0)
        duplicate = wrapped[:-1] + ', "week10_target": ' + json.dumps(FIXTURE) + '}'
        self.assertEqual(self.run_cli(duplicate.encode()).returncode, 1)
        nested = '{"week10_target": ' + json.dumps(FIXTURE)[:-1] + ', "assignment": "week10-a3"}}'
        self.assertEqual(self.run_cli(nested.encode()).returncode, 1)
        extra = json.dumps({"week10_target": FIXTURE, "ansible_connection": "local"})
        self.assertEqual(self.run_cli(extra.encode()).returncode, 1)

    def test_arguments_are_not_an_input_channel(self):
        result = self.run_cli(json.dumps(FIXTURE).encode(), "synthetic-do-not-echo")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, b"target_inputs_invalid\n")

    def test_helper_has_only_read_only_standard_library_imports(self):
        tree = ast.parse((TARGET / "validate_inputs.py").read_text())
        imports = {node.name for statement in ast.walk(tree) if isinstance(statement, ast.Import) for node in statement.names}
        self.assertEqual(imports, {"base64", "binascii", "ipaddress", "json", "struct", "sys"})
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree)))
        for forbidden in ("open(", "subprocess", "socket", "os.system", "eval(", "exec("):
            self.assertNotIn(forbidden, (TARGET / "validate_inputs.py").read_text())


class TargetSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plays = parse_yaml("target/configure.yml")
        cls.controller, cls.target = cls.plays
        cls.tasks = cls.target["tasks"]

    def module_tasks(self, module):
        return [task[module] for task in self.tasks if module in task]

    def test_controller_runs_first_and_remote_facts_wait_for_preflight(self):
        self.assertEqual(self.controller["hosts"], "localhost")
        self.assertEqual(self.controller["connection"], "local")
        self.assertFalse(self.controller["become"])
        self.assertTrue(self.controller["any_errors_fatal"])
        self.assertEqual(self.controller["vars"]["ansible_python_interpreter"], "{{ ansible_playbook_python }}")
        assertions = self.controller["tasks"][0]["ansible.builtin.assert"]["that"]
        self.assertIn("groups.get('week10_web', []) | length == 1", assertions)
        self.assertFalse(self.target["gather_facts"])
        gate = self.target["pre_tasks"][0]
        self.assertEqual(gate["delegate_to"], "localhost")
        self.assertFalse(gate["become"])
        self.assertIn("week10_preflight_passed", gate["ansible.builtin.assert"]["that"][0])

    def test_public_inputs_are_validated_before_inventory_binding(self):
        command = self.controller["tasks"][1]
        self.assertTrue(command["no_log"])
        self.assertFalse(command["changed_when"])
        self.assertEqual(command["ansible.builtin.command"]["argv"][:3], ["/usr/bin/python3", "-I", "-B"])
        binding = self.controller["tasks"][2]["ansible.builtin.assert"]["that"]
        self.assertTrue(any("ansible_host == week10_target.target_ipv4" in test for test in binding))
        self.assertTrue(any("not in ['root', 'week10deploy', 'week10tunnel']" in test for test in binding))
        self.assertTrue(any("ansible_connection" in test and "== 'ssh'" in test for test in binding))

    def test_strict_host_authentication_is_not_tofu(self):
        config = (TARGET / "ansible.cfg").read_text()
        self.assertIn("host_key_checking = True", config)
        args = self.target["vars"]["ansible_ssh_common_args"]
        for required in ("StrictHostKeyChecking=yes", "UserKnownHostsFile=", "known_hosts.local", "GlobalKnownHostsFile=/dev/null", "IdentitiesOnly=yes"):
            self.assertIn(required, args)
        self.assertNotIn("StrictHostKeyChecking=no", (TARGET / "configure.yml").read_text())

    def test_ownership_and_symlink_checks_precede_all_mutations(self):
        pre = self.target["pre_tasks"]
        self.assertFalse(any("ansible.builtin.apt" in task or "ansible.builtin.user" in task for task in pre))
        stat = next(task for task in pre if "ansible.builtin.stat" in task)
        self.assertFalse(stat["ansible.builtin.stat"]["follow"])
        paths = {item["path"] for item in stat["loop"]}
        self.assertTrue({"/var", "/home", "/var/www", "/var/www/html", "/var/www/.dmi-week10-target", "/home/week10deploy/.ssh/authorized_keys"}.issubset(paths))
        text = json.dumps(pre)
        for required in ("nlink == 1", "getent_passwd", "mode == '0644'", "size == 10", "b64decode"):
            self.assertIn(required, text)

    def test_account_is_locked_and_privileges_checked_before_key_installation(self):
        user = self.module_tasks("ansible.builtin.user")[0]
        self.assertEqual(user["name"], "week10deploy")
        self.assertEqual(user["groups"], "")
        self.assertFalse(user["append"])
        self.assertTrue(user["password_lock"])
        command_args = [task["ansible.builtin.command"]["argv"] for task in self.tasks if "ansible.builtin.command" in task]
        self.assertIn(["/usr/bin/id", "-u", "week10deploy"], command_args)
        self.assertIn(["/usr/bin/id", "-Gn", "week10deploy"], command_args)
        self.assertIn(["/usr/bin/sudo", "-n", "-l", "-U", "week10deploy"], command_args)
        assert_index = next(i for i, task in enumerate(self.tasks) if "ansible.builtin.assert" in task)
        key_index = next(i for i, task in enumerate(self.tasks) if task.get("ansible.builtin.copy", {}).get("dest", "").endswith("authorized_keys"))
        self.assertLess(assert_index, key_index)
        key = self.tasks[key_index]["ansible.builtin.copy"]
        self.assertEqual(key["mode"], "0600")
        self.assertTrue(key["content"].startswith('restrict,from="127.0.0.1/32"'))
        self.assertNotIn("sudoers", json.dumps(self.module_tasks("ansible.builtin.copy")))

    def test_parent_and_webroot_match_pipeline_contract_without_recursive_chown(self):
        files = {task["path"]: task for task in self.module_tasks("ansible.builtin.file")}
        self.assertEqual(files["/var/www"]["owner"], "root")
        self.assertEqual(files["/var/www"]["group"], "root")
        self.assertEqual(files["/var/www"]["mode"], "0755")
        self.assertEqual(files["/var/www/html"]["owner"], "week10deploy")
        self.assertFalse(files["/var/www/html"]["recurse"])
        self.assertFalse(any(task.get("recurse") for task in self.module_tasks("ansible.builtin.file")))

    def test_full_nginx_config_is_validated_before_reload_and_marker_is_last(self):
        template = self.module_tasks("ansible.builtin.template")[0]
        self.assertEqual(template["dest"], "/etc/nginx/nginx.conf")
        self.assertEqual(template["validate"], "/usr/sbin/nginx -t -c %s")
        self.assertEqual(self.tasks[-2]["ansible.builtin.meta"], "flush_handlers")
        marker = self.tasks[-1]["ansible.builtin.copy"]
        self.assertEqual(marker["dest"], "/var/www/.dmi-week10-target")
        self.assertEqual(marker["owner"], "root")
        self.assertEqual(marker["group"], "root")
        self.assertEqual(marker["mode"], "0644")
        self.assertEqual(marker["content"], '{{ week10_target.assignment }}\n')

    def test_template_separates_spa_fallback_from_static_404(self):
        template = (TARGET / "templates/nginx.conf.j2").read_text()
        for text in ("root /var/www/html;", "location ^~ /static/", "try_files $uri =404;", "week10_target.assignment == 'week10-a3'", "try_files $uri $uri/ /index.html;", "try_files $uri $uri/ =404;"):
            self.assertIn(text, template)
        self.assertNotIn("sites-enabled", template)

    def test_no_application_execution_cloud_registration_or_automatic_pipeline_setup(self):
        playbook = (TARGET / "configure.yml").read_text()
        for forbidden in ("ansible.builtin.shell", "npm ", "config.sh", "terraform ", "aws ", "az ", "runAsRoot", "NOPASSWD", "apt_key"):
            self.assertNotIn(forbidden, playbook)
        for name in ("static.azure-pipelines.yml", "react.azure-pipelines.yml"):
            self.assertNotIn("configure.yml", (TARGET.parent / name).read_text())

    def test_inventory_is_explicitly_unusable_until_reviewed(self):
        inventory = json.loads((TARGET / "inventory.example.json").read_text())
        hosts = inventory["all"]["children"]["week10_web"]["hosts"]
        self.assertEqual(len(hosts), 1)
        host = hosts["reviewed_target"]
        self.assertIsNone(host["ansible_host"])
        self.assertIsNone(host["ansible_user"])
        self.assertIsNone(host["ansible_ssh_private_key_file"])
        self.assertEqual(host["ansible_connection"], "ssh")
        ignored = (TARGET / ".gitignore").read_text().splitlines()
        self.assertIn("*.local", ignored)
        self.assertIn("*.local.json", ignored)
