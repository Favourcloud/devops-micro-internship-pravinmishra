"""Real OpenSSH configuration/control-socket checks; never open a network connection."""

import configparser
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("lab_ssh", ROOT / "scripts/lab.py")
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


class SSHConfigurationTests(unittest.TestCase):
    def configurations(self):
        for directory in (ROOT / "ansible", ROOT.parent / "static-web"):
            config = configparser.ConfigParser(interpolation=None)
            config.read(directory / "ansible.cfg")
            self.assertNotIn("control_path_dir", config["ssh_connection"])
            args = shlex.split(config["ssh_connection"]["ssh_args"])
            self.assertFalse(any("ControlPersist" in arg for arg in args))
            yield directory, args
        yield ROOT, lab.SSH_OPTIONS

    def ssh(self, cwd, mode, args):
        return subprocess.run(
            ["ssh", "-F", "/dev/null", *mode, *args, "never-contact.invalid"],
            cwd=cwd, env={**os.environ, "LC_ALL": "C"},
            capture_output=True, text=True, timeout=10,
        )

    def test_effective_config_disables_multiplexing_and_preserves_trust(self):
        # -G prints configuration and exits without connecting or resolving the host.
        for directory, args in self.configurations():
            with self.subTest(directory=directory.name):
                result = self.ssh(directory, ["-G"], args)
                self.assertEqual(result.returncode, 0, result.stderr)
                config = dict(line.split(" ", 1) for line in result.stdout.splitlines())
                self.assertEqual(config["controlmaster"], "false")
                self.assertEqual(config["controlpersist"], "no")
                self.assertNotIn("controlpath", config)
                self.assertEqual(config["stricthostkeychecking"], "true")
                self.assertEqual(config["forwardagent"], "no")
                self.assertEqual(config["globalknownhostsfile"], "/dev/null")
                self.assertEqual(
                    (directory / config["userknownhostsfile"]).resolve(),
                    ROOT / ".local/known_hosts",
                )

    def test_overlong_control_socket_is_never_used(self):
        # -O check only checks a local multiplexing socket; it cannot open SSH/TCP.
        for directory, args in self.configurations():
            with self.subTest(directory=directory.name):
                path = str(directory / ".ansible/cp" / ("x" * 128))
                legacy = self.ssh(directory, ["-O", "check"], [
                    "-o", "ControlMaster=auto", "-o", f"ControlPath={path}",
                ])
                self.assertEqual(legacy.returncode, 255)
                self.assertIn("ControlPath too long", legacy.stderr)
                result = self.ssh(directory, ["-O", "check"], [
                    *args, "-o", f"ControlPath={path}",
                ])
                self.assertEqual(result.returncode, 255)
                self.assertIn("No ControlPath specified", result.stderr)
                self.assertNotIn("ControlPath too long", result.stderr)


if __name__ == "__main__":
    unittest.main()
