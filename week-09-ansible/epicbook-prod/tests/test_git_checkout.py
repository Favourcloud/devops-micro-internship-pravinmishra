"""Real offline Git/Ansible regression; no SSH, sudo, packages or remote application."""
import copy
import grp
import hashlib
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml


PROJECT = Path(__file__).resolve().parents[1]
TASKS = PROJECT / "ansible/roles/epicbook/tasks/main.yml"
GIT = "/usr/bin/git"


class GitCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="w09-a5-git-", dir="/tmp")
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir(mode=0o700)
        self.parent = self.root / "epicbook"
        self.parent.mkdir(mode=0o750)
        os.chown(self.parent, -1, os.getgid())
        self.source = self.parent / "source"
        self.metadata_parent = self.parent / "git-metadata"
        self.metadata = self.metadata_parent / "repository.git"
        self.upstream = self.root / "upstream"
        self.upstream.mkdir()
        inherited = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env = dict(inherited, HOME=str(self.home), TMPDIR=str(self.root),
            ANSIBLE_CONFIG=str(PROJECT / "ansible/ansible.cfg"),
            XDG_CONFIG_HOME=str(self.home), XDG_CACHE_HOME=str(self.root / "cache"),
            GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM="/dev/null", GIT_CONFIG_GLOBAL="/dev/null",
            GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="core.hooksPath", GIT_CONFIG_VALUE_0="/dev/null",
            ANSIBLE_LOCAL_TEMP=str(self.root / "ansible-local"), ANSIBLE_NOCOLOR="1",
            PYTHONDONTWRITEBYTECODE="1")
        self.git("init", "--quiet", "--object-format=sha1", str(self.upstream))
        (self.upstream / "README.txt").write_text("Offline pinned source fixture.\n")
        self.commit("First local fixture")
        self.revision = self.git("-C", str(self.upstream), "rev-parse", "HEAD").stdout.strip()
        (self.upstream / "README.txt").write_text("Different upstream HEAD; must not replace the pinned revision.\n")
        self.commit("Second local fixture")

    def tearDown(self):
        self.parent.chmod(0o700)
        self.temporary.cleanup()

    def git(self, *args, check=True):
        return subprocess.run([GIT, *args], env=self.env, cwd=self.root, capture_output=True,
                              text=True, timeout=30, check=check)

    def commit(self, title):
        self.git("-C", str(self.upstream), "add", "README.txt")
        message = title + "\n\nCo-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
        self.git("-C", str(self.upstream), "-c", "user.name=Offline fixture",
                 "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
                 "commit", "--quiet", "-m", message)

    def test_existing_metadata_destination_reproduces_real_git_failure(self):
        self.source.mkdir(mode=0o750)
        self.metadata_parent.mkdir(mode=0o700)
        self.parent.chmod(0o550)
        result = self.git("clone", "--origin", "origin", "--separate-git-dir=" + str(self.metadata_parent),
                          self.upstream.as_uri(), str(self.source), check=False)
        self.assertEqual(result.returncode, 128)
        self.assertIn("already exists", result.stderr)
        self.assertFalse((self.source / "README.txt").exists())

    def local_tasks(self):
        tasks = yaml.safe_load(TASKS.read_text())
        directories = next(t for t in tasks if "loop" in t and "ansible.builtin.file" in t)
        clone = next(t for t in tasks if "ansible.builtin.git" in t)
        protection = next(t for t in tasks if t.get("ansible.builtin.file", {}).get("path") ==
                          clone["ansible.builtin.git"]["separate_git_dir"])

        def relocate(value):
            if isinstance(value, str):
                return value.replace("/opt/epicbook", str(self.parent))
            if isinstance(value, list):
                return [relocate(item) for item in value]
            if isinstance(value, dict):
                return {key: relocate(item) for key, item in value.items()}
            return value

        directories, clone, protection = relocate(copy.deepcopy([directories, clone, protection]))
        clone["become"] = False
        clone.pop("become_user")
        clone["ansible.builtin.git"]["executable"] = GIT
        return [directories,
            {"name": "Deny writes to the application ancestor in this local fixture",
             "ansible.builtin.file": {"path": str(self.parent), "state": "directory", "mode": "0550"}},
            clone, protection,
            {"name": "Assert the actual local Git module result and pinned revision",
             "ansible.builtin.assert": {"that": ["epicbook_checkout.changed == expected_changed",
                                                  "epicbook_checkout.after == app_revision"]}}]

    def test_real_git_module_private_parent_uncreated_leaf_and_second_run(self):
        playbook = self.root / "checkout.yml"
        variables = {"app_repo": self.upstream.as_uri(), "app_revision": self.revision,
                     "app_dest": str(self.source), "app_user": pwd.getpwuid(os.getuid()).pw_name,
                     "app_group": grp.getgrgid(os.getgid()).gr_name,
                     "ansible_python_interpreter": sys.executable}
        playbook.write_text(yaml.safe_dump([{"name": "Offline checkout fixture only", "hosts": "all",
            "connection": "local", "become": False, "gather_facts": False, "vars": variables,
            "tasks": self.local_tasks(), "handlers": [{"name": "Reload nginx",
                "ansible.builtin.debug": {"msg": "Local notification fixture only; no service command."}}]}], sort_keys=False))
        executable = os.environ.get("ANSIBLE_PLAYBOOK", "ansible-playbook")
        before = None
        for changed in (True, False):
            result = subprocess.run([executable, "-i", "localhost,", str(playbook), "-e",
                "{\"expected_changed\": " + str(changed).lower() + "}"], cwd=self.root, env=self.env,
                capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertRegex(result.stdout, r"unreachable=0\s+failed=0")
            if not changed:
                self.assertRegex(result.stdout, r"localhost\s+:\s+ok=\d+\s+changed=0\s+unreachable=0\s+failed=0")
            self.assertEqual(self.git("-C", str(self.source), "rev-parse", "HEAD").stdout.strip(), self.revision)
            self.assertEqual(Path(self.git("-C", str(self.source), "rev-parse", "--absolute-git-dir").stdout.strip()).resolve(), self.metadata.resolve())
            self.assertTrue((self.source / ".git").is_file())
            for path, mode in ((self.parent, 0o550), (self.source, 0o750),
                               (self.metadata_parent, 0o700), (self.metadata, 0o700)):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)
                self.assertEqual(path.stat().st_uid, os.getuid())
                self.assertEqual(path.stat().st_gid, os.getgid())
            if os.geteuid() != 0:
                self.assertFalse(os.access(self.parent, os.W_OK))
                self.assertTrue(os.access(self.metadata_parent, os.W_OK))
            snapshot = {}
            for path in self.source.rglob("*"):
                mode = stat.S_IMODE(path.stat().st_mode)
                self.assertEqual(mode & 0o027, 0)
                self.assertEqual(path.stat().st_uid, os.getuid())
                self.assertEqual(path.stat().st_gid, os.getgid())
                snapshot[str(path.relative_to(self.source))] = (mode, hashlib.sha256(path.read_bytes()).hexdigest())
            if before is not None:
                self.assertEqual(snapshot, before)
            before = snapshot
        self.assertEqual((self.source / "README.txt").read_text(), "Offline pinned source fixture.\n")
