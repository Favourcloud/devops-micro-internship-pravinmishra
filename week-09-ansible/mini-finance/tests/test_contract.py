"""Offline Ansible contract/SSH-stub tests. No cloud access or SSH network calls."""

import configparser
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
REVISION = "296334fc27de87bdfcafdad041e41573d8815700"


class DeploymentContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plays = yaml.safe_load((ANSIBLE / "site.yml").read_text())
        cls.variables = yaml.safe_load((ANSIBLE / "group_vars/all.yml").read_text())
        cls.deploy = cls.plays[1]["tasks"]

    def test_exactly_three_plays_and_failure_stops_later_plays(self):
        self.assertEqual([p["hosts"] for p in self.plays], ["web", "web", "localhost"])
        self.assertTrue(all(p["any_errors_fatal"] for p in self.plays))
        self.assertFalse(any(p.get("force_handlers", False) for p in self.plays))
        self.assertFalse(self.plays[0]["gather_facts"])
        self.assertEqual(self.plays[0]["pre_tasks"][0]["delegate_to"], "localhost")

    def test_ssh_host_checking_and_noninteractive_auth_are_required(self):
        config = configparser.ConfigParser()
        config.read(ANSIBLE / "ansible.cfg")
        self.assertTrue(config.getboolean("defaults", "host_key_checking"))
        args = config.get("ssh_connection", "ssh_args")
        self.assertIn("StrictHostKeyChecking=yes", args)
        self.assertIn("BatchMode=yes", args)
        self.assertIn("ControlMaster=no", args)
        self.assertIn("ControlPath=none", args)
        self.assertNotIn("ControlPersist", args)
        self.assertFalse(config.has_option("ssh_connection", "control_path_dir"))
        self.assertNotIn("accept-new", args)

    def test_public_source_is_immutable_and_not_inside_docroot(self):
        self.assertEqual(self.variables["mini_finance_repo"], "https://github.com/pravinmishraaws/mini_finance.git")
        self.assertEqual(self.variables["mini_finance_revision"], REVISION)
        self.assertEqual(self.variables["mini_finance_docroot"], "/var/www/html")
        self.assertTrue(self.variables["mini_finance_checkout"].startswith("/opt/"))
        git_task = next(t["ansible.builtin.git"] for t in self.deploy if "ansible.builtin.git" in t)
        self.assertFalse(git_task["force"])
        self.assertEqual(git_task["version"], "{{ mini_finance_revision }}")

    def test_export_does_not_include_hidden_metadata_or_upstream_histories(self):
        paths = self.variables["mini_finance_public_paths"]
        self.assertIn("index.html", paths)
        self.assertNotIn("js", paths)  # Upstream js/.DS_Store must never be exported.
        for path in paths:
            self.assertFalse(any(part.startswith(".") for part in Path(path).parts))
            self.assertNotIn("README", path)
            self.assertNotIn("tracking", path)
        command = next(t["ansible.builtin.command"] for t in self.deploy if "ansible.builtin.command" in t)
        self.assertIn("archive", command["argv"])
        self.assertIn("mini_finance_public_paths", command["argv"])
        self.assertIn("creates", command)

    def test_validation_precedes_publish_and_handlers_precede_http(self):
        names = [t["name"] for t in self.deploy]
        publish = names.index("Publish the validated release at the required document root")
        for guard in (
            "Reject hidden files or symlinks before publishing",
            "Require Mini Finance content before switching the document root",
            "Refuse to replace any directory except the stock Nginx welcome directory",
            "Install the dedicated VM Nginx configuration after syntax validation",
        ):
            self.assertLess(names.index(guard), publish)
        self.assertEqual(self.deploy[-1]["ansible.builtin.meta"], "flush_handlers")
        template = next(t["ansible.builtin.template"] for t in self.deploy if "ansible.builtin.template" in t)
        self.assertEqual(template["validate"], "/usr/sbin/nginx -t -c %s")
        handlers = self.plays[1]["handlers"]
        self.assertEqual(handlers[0]["ansible.builtin.command"], "/usr/sbin/nginx -t")
        self.assertFalse(handlers[0]["changed_when"])
        self.assertEqual(handlers[1]["ansible.builtin.service"]["state"], "reloaded")

    def test_site_changes_notify_reload_without_always_changed_shell(self):
        for task in self.deploy:
            self.assertNotIn("ansible.builtin.shell", task)
            if "ansible.builtin.unarchive" in task:
                self.assertEqual(task["notify"], "Reload Mini Finance")
        self.assertEqual(self.deploy[-2]["ansible.builtin.file"]["state"], "link")
        self.assertEqual(self.deploy[-2]["notify"], "Reload Mini Finance")

    def test_http_verification_checks_content_and_nonpublic_files(self):
        verify = self.plays[2]
        self.assertEqual(verify["connection"], "local")
        self.assertFalse(verify["become"])
        uris = [t for t in verify["tasks"] if "ansible.builtin.uri" in t]
        self.assertEqual(uris[0]["ansible.builtin.uri"]["status_code"], 200)
        self.assertTrue(uris[0]["ansible.builtin.uri"]["return_content"])
        for task in uris:
            self.assertFalse(task["ansible.builtin.uri"]["use_proxy"])
            self.assertFalse(task["ansible.builtin.uri"]["use_netrc"])
            self.assertEqual(task["ansible.builtin.uri"]["follow_redirects"], "none")
        self.assertEqual(uris[1]["ansible.builtin.uri"]["status_code"], 404)
        self.assertIn(".git/config", uris[1]["loop"])
        self.assertIn("js/.DS_Store", uris[1]["loop"])
        assertion = verify["tasks"][2]["ansible.builtin.assert"]["that"]
        self.assertIn("item in mini_finance_http.content", assertion)

    def test_nginx_is_static_with_dotfile_denial(self):
        config = (ANSIBLE / "templates/nginx.conf.j2").read_text()
        self.assertIn("root {{ mini_finance_docroot }};", config)
        self.assertIn("autoindex off;", config)
        self.assertIn(r"location ~ (^|/)\.", config)
        self.assertNotIn("proxy_pass", config)
        self.assertNotIn("sites-enabled", config)

    def test_terraform_has_no_cloud_execution_or_identity_side_effects(self):
        files = list((ROOT / "terraform").glob("*.tf"))
        config = "\n".join(p.read_text() for p in files)
        for prohibited in ('provider "aws"', 'provisioner "', 'resource "azurerm_role_assignment"', 'data "', 'admin_password', 'subscription_id'):
            self.assertNotIn(prohibited, config)
        self.assertIn('resource_provider_registrations = "none"', config)
        self.assertIn('version = "= 4.47.0"', config)
        self.assertIn('depends_on = [azurerm_network_interface_security_group_association.site]', config)
        self.assertIn('value       = azurerm_public_ip.site.ip_address', config)
        self.assertEqual(len(re.findall(r'^resource "', config, re.MULTILINE)), 8)

    def test_private_local_artifacts_ignored_but_lock_and_example_kept(self):
        private = [
            "terraform/terraform.tfvars", "terraform/local.auto.tfvars",
            "terraform/local.auto.tfvars.json", "terraform/terraform.tfstate.backup",
            "terraform/deploy.tfplan", "ansible/inventory.local.ini",
            "ansible/.local/inventory.ini", "ansible/.local/known_hosts", "ansible/id_ed25519",
        ]
        result = subprocess.run(
            ["/usr/bin/git", "check-ignore", "--no-index", "--stdin"],
            input="\n".join(str(ROOT / p) for p in private) + "\n",
            text=True, capture_output=True, check=True,
        )
        self.assertEqual(len(result.stdout.splitlines()), len(private))
        result = subprocess.run(
            ["/usr/bin/git", "check-ignore", "--no-index", str(ROOT / "terraform/.terraform.lock.hcl"),
             str(ROOT / "terraform/terraform.tfvars.example")], capture_output=True,
        )
        self.assertEqual(result.returncode, 1)

    def test_no_vendored_javascript_or_private_keys(self):
        self.assertEqual(list(ROOT.rglob("*.js")), [])
        self.assertEqual(list(ROOT.rglob("*.pem")), [])
        for file in (ANSIBLE / "inventory.ini", ROOT / "terraform/terraform.tfvars.example"):
            self.assertNotRegex(file.read_text(), r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class RealOpenSSHConfiguration(unittest.TestCase):
    def test_long_control_path_reaches_refusing_proxy_without_network_or_keys(self):
        ssh = shutil.which("ssh")
        self.assertIsNotNone(ssh, "OpenSSH is required for the local configuration regression")
        config = configparser.ConfigParser()
        config.read(ANSIBLE / "ansible.cfg")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            marker = directory / "proxy-called"
            proxy = directory / "refuse-network"
            proxy.write_text(f"#!/bin/sh\n: > {shlex.quote(str(marker))}\nexit 99\n")
            proxy.chmod(0o700)
            long_path = str(directory / ("x" * 160) / "unit-test-socket")
            result = subprocess.run(
                [ssh, "-F", "/dev/null", *shlex.split(config.get("ssh_connection", "ssh_args")),
                 "-o", f"ControlPath={long_path}", "-o", f"ProxyCommand={shlex.quote(str(proxy))}",
                 "-o", "IdentityFile=none", "-o", "IdentityAgent=none", "-o", "IdentitiesOnly=yes",
                 "-o", "UserKnownHostsFile=/dev/null", "-o", "GlobalKnownHostsFile=/dev/null",
                 "-o", "ConnectTimeout=1", "azureuser@192.0.2.10", "true"],
                text=True, capture_output=True, timeout=10,
            )
            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, "The proxy must refuse all connections")
            self.assertTrue(marker.exists(), output)
            self.assertNotIn("too long", output.lower())
            self.assertFalse(Path(long_path).exists())


class RealAnsiblePreflight(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("ansible-playbook"), "Use the documented controller environment")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.ssh_called = self.directory / "ssh-called"
        ssh_stub = self.directory / "forbid-ssh"
        ssh_stub.write_text(f"#!/bin/sh\n: > '{self.ssh_called}'\nexit 99\n")
        ssh_stub.chmod(0o700)
        self.env = os.environ | {
            "ANSIBLE_CONFIG": str(ANSIBLE / "ansible.cfg"),
            "ANSIBLE_LOCAL_TEMP": str(self.directory / "tmp"),
            "ANSIBLE_HOME": str(self.directory / "ansible-home"),
            "XDG_CACHE_HOME": str(self.directory / "cache"),
            "ANSIBLE_SSH_EXECUTABLE": str(ssh_stub),
            "ANSIBLE_NOCOLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    def run_guard(self, inventory, *extra):
        result = subprocess.run(
            ["ansible-playbook", "-i", str(inventory), "site.yml", *extra],
            cwd=ANSIBLE, env=self.env, text=True, capture_output=True, timeout=60,
        )
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertFalse(self.ssh_called.exists(), output)
        self.assertNotIn("TASK [Install web server", output)
        self.assertNotIn("TASK [Fetch the public site", output)
        return output

    def test_committed_inventory_has_no_web_hosts(self):
        result = subprocess.run(
            ["ansible-inventory", "-i", "inventory.ini", "--list"], cwd=ANSIBLE,
            env=self.env, text=True, capture_output=True, check=True,
        )
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory.get("web", {}).get("hosts", []), [])

    def test_empty_inventory_fails_without_ssh_or_http(self):
        output = self.run_guard(ANSIBLE / "inventory.ini")
        self.assertIn("No configured Azure VM", output)

    def test_malformed_address_fails_before_ssh(self):
        inventory = self.directory / "inventory.ini"
        inventory.write_text("[web]\nmini ansible_host=999.999.999.999 ansible_user=azureuser\n")
        self.assertIn("Configure one real Azure host", self.run_guard(inventory))

    def test_multiple_hosts_fail_before_ssh(self):
        inventory = self.directory / "inventory.ini"
        inventory.write_text("[web]\none\ntwo\n")
        self.assertIn("Configure one real Azure host", self.run_guard(inventory))

    def test_root_admin_fails_before_ssh(self):
        inventory = self.directory / "inventory.ini"
        inventory.write_text("[web]\nmini ansible_host=192.0.2.10 ansible_user=root\n")
        self.assertIn("Configure one real Azure host", self.run_guard(inventory))

    def test_check_mode_is_not_misrepresented_as_deployment(self):
        inventory = self.directory / "inventory.ini"
        inventory.write_text("[web]\nmini ansible_host=192.0.2.10 ansible_user=azureuser\n")
        self.assertIn("Check mode is not a substitute", self.run_guard(inventory, "--check"))

    def assert_ssh_boundary(self, controller_variables):
        inventory = self.directory / "inventory.ini"
        inventory.write_text(
            '[web]\nmini_finance ansible_host=192.0.2.10 ansible_user=azureuser '
            'ansible_ssh_private_key_file="/not-read-by-refusing-stub"\n'
            '[controller]\nlocalhost ' + controller_variables + '\n'
        )
        result = subprocess.run(
            ["ansible-playbook", "-i", str(inventory), "site.yml"],
            cwd=ANSIBLE, env=self.env, text=True, capture_output=True, timeout=60,
        )
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, "The SSH refusal stub must stop the run")
        self.assertTrue(self.ssh_called.exists(), output)
        self.assertIn("All assertions passed", output)
        self.assertIn("TASK [Gather facts only after the controller preflight succeeds]", output)
        self.assertNotIn("TASK [Install web server", output)
        self.assertNotIn("TASK [Fetch the public site", output)

    def test_documented_inventory_reaches_ssh_boundary(self):
        self.assert_ssh_boundary("ansible_connection=local")

    def test_delegated_host_connection_variables_do_not_replace_target_values(self):
        self.assert_ssh_boundary("ansible_connection=local ansible_host=localhost ansible_user=root")

    def test_explicit_local_target_fails_before_ssh(self):
        inventory = self.directory / "inventory.ini"
        inventory.write_text(
            "[web]\nmini ansible_host=192.0.2.10 ansible_user=azureuser ansible_connection=local\n"
            "[controller]\nlocalhost ansible_connection=local\n"
        )
        self.assertIn("Configure one real Azure host", self.run_guard(inventory))


if __name__ == "__main__":
    unittest.main(verbosity=2)
