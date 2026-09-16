"""Local contract tests. These are NOT VM, MySQL or application deployment evidence."""

import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest

from jinja2 import Environment, StrictUndefined
import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
SPEC = importlib.util.spec_from_file_location("render_inventory", ROOT / "scripts/render_inventory.py")
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)


def load(path):
    return yaml.safe_load((ANSIBLE / path).read_text())


class InventoryTests(unittest.TestCase):
    def outputs(self, ip="8.8.8.8", user="ubuntu"):
        # Parser-only fixture: this address is never contacted.
        return {"public_ip": {"value": ip}, "admin_user": {"value": user}}

    def test_strict_inventory_without_reading_keys(self):
        result = RENDERER.render(self.outputs(), "/not-read/key", "/not-read/known_hosts")
        self.assertIn("ansible_connection=ssh", result)
        self.assertIn("StrictHostKeyChecking=yes", result)
        self.assertNotIn("ansible_password", result)

    def test_rejects_non_public_or_invalid_hosts(self):
        for value in ["127.0.0.1", "0.0.0.0", "169.254.169.254", "10.0.0.1", "203.0.113.20", "224.0.0.1", "::1", "1.2.3.999", "8.8.8.8 ansible_connection=local"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                RENDERER.render(self.outputs(value), "/key", "/hosts")

    def test_rejects_bad_output_shape_and_user(self):
        for outputs in [{}, {"public_ip": "8.8.8.8"}, self.outputs(user="root"), self.outputs(user="ubuntu\n[local]")]:
            with self.subTest(outputs=outputs), self.assertRaises(ValueError):
                RENDERER.render(outputs, "/key", "/hosts")

    def test_rejects_ssh_argument_injection(self):
        for path in ["relative", "/tmp/my key", "/key' ProxyCommand=evil", "/tmp/../key", "/key\nother"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                RENDERER.render(self.outputs(), path, "/known_hosts")

    def test_exclusive_private_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.ini"
            RENDERER.write_new(path, "fixture")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                RENDERER.write_new(path, "replacement")
            link = Path(directory) / "symlink.ini"
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                RENDERER.write_new(link, "replacement")
            self.assertEqual(path.read_text(), "fixture")


class RoleContractTests(unittest.TestCase):
    def test_role_order_and_controller_guard(self):
        plays = load("site.yml")
        self.assertEqual(plays[0]["hosts"], "localhost")
        self.assertTrue(plays[0]["any_errors_fatal"])
        self.assertEqual(plays[1]["roles"], ["common", "nginx", "epicbook"])
        self.assertFalse(plays[1]["gather_facts"])

    def test_required_baseline_packages(self):
        tasks = load("roles/common/tasks/main.yml")
        self.assertTrue(tasks[0]["ansible.builtin.apt"]["update_cache"])
        self.assertEqual(tasks[1]["ansible.builtin.apt"]["upgrade"], "dist")
        packages = tasks[2]["ansible.builtin.apt"]["name"]
        self.assertTrue({"git", "curl", "unzip", "software-properties-common"}.issubset(packages))

    def test_pinned_source_and_separate_identities(self):
        variables = load("group_vars/web.yml")
        self.assertRegex(variables["app_revision"], r"^[a-f0-9]{40}$")
        self.assertNotEqual(variables["app_user"], variables["app_runtime_user"])
        tasks = load("roles/epicbook/tasks/main.yml")
        clone = next(t for t in tasks if "ansible.builtin.git" in t)
        self.assertFalse(clone["ansible.builtin.git"]["force"])
        self.assertEqual(clone["ansible.builtin.git"]["umask"], "0027")
        self.assertEqual(clone["ansible.builtin.git"]["separate_git_dir"], "/opt/epicbook/git-metadata")
        self.assertEqual(clone["notify"], "Reload nginx")

    def test_fail_closed_and_reverse_proxy_templates(self):
        variables = load("group_vars/web.yml")
        self.assertFalse(variables["app_runtime_enabled"])
        text = (ANSIBLE / "roles/nginx/templates/epicbook.conf.j2").read_text()
        template = Environment(undefined=StrictUndefined).from_string(text)
        disabled = template.render(variables)
        enabled = template.render({**variables, "app_runtime_enabled": True})
        self.assertIn("return 503", disabled)
        self.assertNotIn("proxy_pass", disabled)
        self.assertIn("proxy_pass http://127.0.0.1:8080", enabled)
        for config in [disabled, enabled]:
            self.assertNotRegex(config, r"\b(root|alias)\s")
            patterns = re.findall(r"location ~\*? (\S+) \{ return 404; \}", config)
            for path in ["/.git/config", "/.env", "/config/config.json", "/db/books_seed.sql", "/models/index.js", "/package-lock.json", "/server.js", "/node_modules/a"]:
                self.assertTrue(any(re.search(pattern, path, re.I) for pattern in patterns), path)

    def test_validated_nginx_reload_order(self):
        handlers = load("roles/nginx/handlers/main.yml")
        self.assertEqual(handlers[0]["ansible.builtin.command"]["argv"], ["/usr/sbin/nginx", "-t"])
        self.assertEqual(handlers[1]["ansible.builtin.systemd_service"]["state"], "reloaded")
        self.assertEqual(handlers[0]["listen"], handlers[1]["listen"])

    def test_runtime_secret_and_seed_gates(self):
        tasks = load("roles/epicbook/tasks/runtime.yml")
        secret = next(t for t in tasks if t.get("ansible.builtin.template", {}).get("dest") == "/etc/epicbook/epicbook.env")
        self.assertTrue(secret["no_log"])
        self.assertFalse(secret["diff"])
        self.assertEqual(secret["ansible.builtin.template"]["mode"], "0600")
        importer = next(t for t in tasks if t.get("ansible.mysql.mysql_db", {}).get("state") == "import")
        self.assertEqual(importer["when"], "not epicbook_seed_marker.stat.exists")
        self.assertEqual(importer["loop"], ["BuyTheBook_Schema.sql", "author_seed.sql", "books_seed.sql"])
        self.assertTrue(any("partial or foreign" in t["name"] for t in tasks))
        npm = next(t for t in tasks if "locked runtime dependencies" in t["name"])
        self.assertIn("--ignore-scripts", npm["ansible.builtin.command"]["argv"])
        self.assertEqual(npm["become_user"], "{{ app_user }}")
        service = (ANSIBLE / "roles/epicbook/templates/epicbook.service.j2").read_text()
        for setting in ["ProtectSystem=strict", "NoNewPrivileges=true", "IPAddressDeny=any", "IPAddressAllow=localhost"]:
            self.assertIn(setting, service)


class ExecutionGuardTests(unittest.TestCase):
    def test_approved_rendered_inventory_reaches_only_offline_ssh_stub(self):
        executable = os.environ.get("ANSIBLE_PLAYBOOK", "ansible-playbook")
        for runtime in [False, True]:
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as directory:
                work = Path(directory)
                marker = work / "stub-called"
                stub = work / "ssh-stub"
                stub.write_text('#!/bin/sh\nprintf called > "$A5_STUB_MARKER"\nprintf A5_OFFLINE_SSH_STUB >&2\nexit 255\n')
                stub.chmod(0o700)
                inventory = work / "inventory.ini"
                outputs = {"public_ip": {"value": "8.8.8.8"}, "admin_user": {"value": "ubuntu"}}
                RENDERER.write_new(inventory, RENDERER.render(outputs, "/not-read/key", "/not-read/known_hosts"))
                extra = {
                    "deployment_approved": True,
                    "app_runtime_enabled": runtime,
                    "app_runtime_compatibility_acknowledged": runtime,
                    "vault_epicbook_db_password": "offline_fixture_" * 3,
                }
                env = dict(os.environ, ANSIBLE_CONFIG=str(ANSIBLE / "ansible.cfg"), ANSIBLE_LOCAL_TEMP=directory,
                           ANSIBLE_SSH_EXECUTABLE=str(stub), A5_STUB_MARKER=str(marker))
                result = subprocess.run([executable, "-i", str(inventory), "site.yml", "-e", json.dumps(extra)],
                                        cwd=ANSIBLE, env=env, text=True, capture_output=True, timeout=60)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(marker.exists(), result.stdout + result.stderr)
                self.assertEqual(marker.read_text(), "called")
                self.assertIn("Gather target facts", result.stdout)
                self.assertIn("UNREACHABLE", result.stdout)
                self.assertNotIn("common :", result.stdout)
                self.assertNotIn(extra["vault_epicbook_db_password"], result.stdout + result.stderr)

    def test_unconfigured_run_is_rejected_without_ssh(self):
        executable = os.environ.get("ANSIBLE_PLAYBOOK", "ansible-playbook")
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, ANSIBLE_CONFIG=str(ANSIBLE / "ansible.cfg"), ANSIBLE_LOCAL_TEMP=directory, ANSIBLE_SSH_EXECUTABLE="/usr/bin/false")
            result = subprocess.run([executable, "-i", "inventory.ini", "site.yml"], cwd=ANSIBLE, env=env, text=True, capture_output=True, timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("STOP: preparation only", result.stdout)
        self.assertNotIn("Gather target facts", result.stdout)
        self.assertNotIn("Prepare the dedicated Ubuntu", result.stdout)

    def test_unapproved_target_cannot_fall_through_to_next_play(self):
        executable = os.environ.get("ANSIBLE_PLAYBOOK", "ansible-playbook")
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / "inventory.ini"
            inventory.write_text("[web]\nfixture ansible_host=203.0.113.20 ansible_user=ubuntu ansible_connection=ssh\n")
            env = dict(os.environ, ANSIBLE_CONFIG=str(ANSIBLE / "ansible.cfg"), ANSIBLE_LOCAL_TEMP=directory, ANSIBLE_SSH_EXECUTABLE="/usr/bin/false")
            result = subprocess.run([executable, "-i", str(inventory), "site.yml"], cwd=ANSIBLE, env=env, text=True, capture_output=True, timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("STOP: preparation only", result.stdout)
        self.assertNotIn("Prepare the dedicated Ubuntu", result.stdout)


if __name__ == "__main__":
    unittest.main()
