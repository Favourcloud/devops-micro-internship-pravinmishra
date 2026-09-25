"""Offline content/guard tests and loopback-only execution of Play 3."""

from contextlib import contextmanager
import hashlib
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
COMMIT = "0983d638c1139d78bd9a4de18a719626bf89bc9c"
HASHES = {
    "index.html": "85f12fada8edce1730aa3aa43a4ed355acb48c5c7e333d9f05ffc23e0179ed94",
    "contact.html": "f843921259ba16c1e33dbf3788699c44ba2f95426b89af79651ca6ae7696d61a",
    "style.css": "96f92b381bfdbce824f5103aa1d1cc9b4182c489a02769dcc4dc2186765f5436",
}


class StaticHTML(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            raise AssertionError("JavaScript must not be included")
        for name, value in attrs:
            if name.startswith("on") or (value and value.lower().startswith("javascript:")):
                raise AssertionError("JavaScript must not be included")
            if name in ("href", "src"):
                if not value or ":" in value or value.startswith("/"):
                    raise AssertionError("Expect a bundled, relative static asset")
                if not (ROOT / "files" / value).is_file():
                    raise AssertionError(f"Missing asset: {value}")


@contextmanager
def server(status, body):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            if status == 302:
                self.send_header("Location", "/redirect-must-not-be-followed")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plays = yaml.safe_load((ROOT / "site.yml").read_text())

    def setUp(self):
        (ROOT / ".local").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / ".local")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.environment = os.environ.copy()
        self.environment.update({
            "ANSIBLE_CONFIG": str(ROOT / "ansible.cfg"),
            "ANSIBLE_LOCAL_TEMP": str(self.directory / "tmp"),
            "ANSIBLE_NOCOLOR": "1", "PYTHONDONTWRITEBYTECODE": "1",
        })

    def run_play(self, *args):
        return subprocess.run(["ansible-playbook", *args], cwd=ROOT, env=self.environment, capture_output=True, text=True, timeout=90)

    def test_provenance_and_all_links(self):
        for filename, digest in HASHES.items():
            original = subprocess.run(
                ["/usr/bin/git", "show", f"{COMMIT}:CodeTrack/{filename}"],
                cwd=REPO, capture_output=True, check=True,
            ).stdout
            self.assertEqual(hashlib.sha256(original).hexdigest(), digest)
            expected = original.decode().replace("Favour Eze", "Eze Favour").replace("Group 3", "Group 1")
            if filename.endswith(".html"):
                expected = expected.replace("      <p>© 2026 CodeTrack — DMI Cohort 3</p>", "      <p>© 2026 CodeTrack — DMI Cohort 3</p>\n      <p>Deployed by Eze Favour — Week 09 multi-host lab</p>")
                StaticHTML().feed((ROOT / "files" / filename).read_text())
            self.assertEqual((ROOT / "files" / filename).read_text(), expected)
        self.assertFalse(list((ROOT / "files").glob("*.js")))

    def test_three_plays_and_idempotent_modules(self):
        self.assertEqual([play["hosts"] for play in self.plays], ["web", "web", "localhost"])
        self.assertTrue(all(not play["gather_facts"] for play in self.plays))
        install, deploy, verify = self.plays
        self.assertEqual(install["tasks"][0]["ansible.builtin.apt"]["cache_valid_time"], 3600)
        self.assertEqual(install["tasks"][1]["ansible.builtin.service"]["state"], "started")
        self.assertEqual(deploy["tasks"][0]["loop"], ["index.html", "contact.html", "style.css"])
        self.assertEqual(deploy["tasks"][0]["notify"], deploy["handlers"][0]["name"])
        self.assertEqual(deploy["handlers"][0]["ansible.builtin.service"]["state"], "reloaded")
        self.assertEqual(verify["connection"], "local")
        self.assertFalse(verify["become"])
        self.assertFalse(verify["tasks"][1]["ansible.builtin.uri"]["use_proxy"])
        self.assertEqual(verify["tasks"][1]["ansible.builtin.uri"]["follow_redirects"], "none")

    def test_unapproved_or_template_execution_fails_before_ssh(self):
        sentinel = self.directory / "ssh-sentinel"
        sentinel.write_text("#!/bin/sh\necho UNEXPECTED_SSH_ATTEMPT >&2\nexit 97\n")
        sentinel.chmod(0o700)
        self.environment["ANSIBLE_SSH_EXECUTABLE"] = str(sentinel)
        for extra in ([], ["-e", "live_execution_approved=true"]):
            with self.subTest(extra=extra):
                result = self.run_play("-i", "inventory.ini", "site.yml", *extra)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Blocked.", result.stdout)
                self.assertNotIn("UNEXPECTED_SSH_ATTEMPT", result.stdout + result.stderr)
                self.assertNotIn("TASK [Install Nginx", result.stdout)
        configured = self.directory / "inventory.ini"
        configured.write_text((ROOT / "inventory.ini").read_text().replace("lab_inventory_configured=false", "lab_inventory_configured=true"))
        result = self.run_play("-i", str(configured), "site.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Blocked.", result.stdout)
        self.assertNotIn("UNEXPECTED_SSH_ATTEMPT", result.stdout + result.stderr)

    def test_configured_ssh_reaches_stub_but_local_connection_is_blocked(self):
        sentinel = self.directory / "ssh-sentinel"
        sentinel.write_text("#!/bin/sh\necho REACHED_SSH_BOUNDARY >&2\nexit 97\n")
        sentinel.chmod(0o700)
        self.environment["ANSIBLE_SSH_EXECUTABLE"] = str(sentinel)
        inventory = self.directory / "inventory.local.ini"
        template = (ROOT / "inventory.ini").read_text()
        configured = template.replace("lab_inventory_configured=false", "lab_inventory_configured=true")
        configured = configured.replace("web1.invalid", "54.0.0.10").replace("web2.invalid", "54.0.0.11")
        for connection in ("ssh", "local"):
            with self.subTest(connection=connection):
                inventory.write_text(configured.replace("ansible_connection=ssh", f"ansible_connection={connection}"))
                result = self.run_play("-i", str(inventory), "site.yml", "-e", "live_execution_approved=true")
                self.assertNotEqual(result.returncode, 0)
                output = result.stdout + result.stderr
                if connection == "ssh":
                    self.assertIn("TASK [Install Nginx", output)
                    self.assertIn("REACHED_SSH_BOUNDARY", output)
                    self.assertNotIn("Blocked.", output)
                else:
                    self.assertIn("Blocked.", output)
                    self.assertNotIn("REACHED_SSH_BOUNDARY", output)
                    self.assertNotIn("TASK [Install Nginx", output)

    def test_controller_verification_on_loopback_only(self):
        # Run only a copy of Play 3. Never execute install/deploy plays in this test.
        play = yaml.safe_load((ROOT / "site.yml").read_text())[2]
        play["tasks"][1].update({"retries": 0, "delay": 0})
        play["vars"]["ansible_remote_tmp"] = str(self.directory / "remote-tmp")
        playfile = self.directory / "verify.yml"
        playfile.write_text(yaml.safe_dump([play], sort_keys=False))
        cases = [
            (200, (ROOT / "files/index.html").read_text(), True),
            (200, "Default Nginx page", False),
            (200, "Eze Favour but no lab marker", False),
            (503, "Eze Favour — Week 09 multi-host lab", False),
            (302, "Eze Favour — Week 09 multi-host lab", False),
        ]
        for status, body, success in cases:
            with self.subTest(status=status, body=body[:30]), server(status, body) as port:
                inventory = self.directory / "loopback.ini"
                inventory.write_text(f"[web]\nweb1 ansible_host=127.0.0.1:{port}\nweb2 ansible_host=127.0.0.1:{port}\n[web:vars]\nlab_inventory_configured=true\n")
                result = self.run_play("-i", str(inventory), str(playfile), "-e", "live_execution_approved=true")
                self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
                if success:
                    self.assertIn("web1 returned HTTP 200", result.stdout)
                    self.assertIn("web2 returned HTTP 200", result.stdout)
                    self.assertRegex(result.stdout, r"localhost\s+: ok=\d+\s+changed=0\s+unreachable=0\s+failed=0")


if __name__ == "__main__":
    unittest.main()
