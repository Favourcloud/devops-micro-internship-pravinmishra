"""Local-only tests: no Terraform, cloud, SSH or Ansible execution."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lab", ROOT / "scripts/lab.py")
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)
# Synthetic public-address fixtures, never contact these addresses.
IPS = dict(zip(("web1", "web2", "app1", "db1"), ("54.0.0.10", "54.0.0.11", "54.0.0.12", "54.0.0.13")))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".local").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / ".local")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.outputs = self.root / "public-ips.json"
        self.outputs.write_text(json.dumps(IPS))
        self.inventory = self.root / "inventory.local.ini"

    def test_all_and_web_rendering(self):
        lab.render(self.outputs, self.inventory)
        self.assertEqual(lab.read_local_inventory(self.inventory), IPS)
        self.assertEqual(self.inventory.stat().st_mode & 0o777, 0o600)
        web = self.root / "web"
        web.mkdir()
        destination = web / "inventory.local.ini"
        lab.render(self.outputs, destination, True)
        self.assertIn("[web]", destination.read_text())
        self.assertNotIn("[app]", destination.read_text())
        self.assertNotIn("db1", destination.read_text())
        self.assertIn("StrictHostKeyChecking=yes", destination.read_text())
        self.assertNotIn("private_key", destination.read_text())

    def test_reject_bad_outputs(self):
        cases = [None, [], {}, {**IPS, "extra": "54.0.0.14"}, {key: value for key, value in IPS.items() if key != "db1"}]
        for value in (None, 1, "", "web1.invalid", "192.0.2.10", "10.0.0.10", "127.0.0.1", "0.0.0.0", "224.0.0.1", "::1", "54.0.0.10\nansible_connection=local", IPS["web2"]):
            cases.append({**IPS, "web1": value})
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                lab.validate_ips(data)

    def test_refuse_template_overwrite_existing_and_symlink(self):
        with self.assertRaises(ValueError):
            lab.render(self.outputs, self.root / "inventory.ini")
        lab.render(self.outputs, self.inventory)
        original = self.inventory.read_bytes()
        with self.assertRaises(FileExistsError):
            lab.render(self.outputs, self.inventory)
        self.assertEqual(original, self.inventory.read_bytes())
        self.inventory.unlink()
        self.inventory.symlink_to(self.outputs)
        with self.assertRaises(FileExistsError):
            lab.render(self.outputs, self.inventory)
        with self.assertRaises(ValueError):
            lab.read_local_inventory(self.inventory)

    def test_refuse_tampering_and_template(self):
        with self.assertRaises(ValueError):
            lab.read_local_inventory(ROOT / "ansible/inventory.ini")
        lab.render(self.outputs, self.inventory)
        self.inventory.write_text(self.inventory.read_text() + "ansible_connection=local\n")
        with self.assertRaises(ValueError):
            lab.read_local_inventory(self.inventory)

    @patch.object(lab.subprocess, "run")
    def test_missing_approval_never_executes(self, run):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            lab.main(["adhoc", "ping", "--inventory", str(self.inventory)])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            lab.main(["render", "--outputs", str(self.outputs), "--output", str(self.inventory)])
        self.assertFalse(self.inventory.exists())
        run.assert_not_called()

    @patch.object(lab.subprocess, "run")
    def test_explicit_adhoc_commands_and_ssh_options(self, run):
        lab.render(self.outputs, self.inventory)
        for action, arguments in lab.ACTIONS.items():
            self.assertEqual(lab.main(["adhoc", action, "--inventory", str(self.inventory), "--approved"]), 0)
            self.assertEqual(run.call_args.args[0], ["ansible", "-i", str(self.inventory), *arguments])
            self.assertEqual(run.call_args.kwargs["env"]["ANSIBLE_HOST_KEY_CHECKING"], "True")
        run.reset_mock()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lab.main(["adhoc", "ssh-hostnames", "--inventory", str(self.inventory), "--approved"]), 0)
        self.assertEqual(run.call_count, 4)
        for call in run.call_args_list:
            self.assertIn("StrictHostKeyChecking=yes", call.args[0])
            self.assertIn("ForwardAgent=no", call.args[0])
            self.assertIn("BatchMode=yes", call.args[0])
            self.assertIn(f"UserKnownHostsFile={ROOT / '.local/known_hosts'}", call.args[0])
            self.assertIn("GlobalKnownHostsFile=/dev/null", call.args[0])
            self.assertTrue(call.args[0][-2].startswith("azureuser@"))

    @patch.object(lab.subprocess, "run")
    def test_tampered_inventory_never_executes(self, run):
        self.inventory.write_text("[all]\nlocalhost ansible_connection=local\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(lab.main(["adhoc", "install-nginx", "--inventory", str(self.inventory), "--approved"]), 1)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
