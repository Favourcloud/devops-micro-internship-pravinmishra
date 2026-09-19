import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest


PROJECT = Path(__file__).resolve().parents[1]
WEEK = PROJECT.parent
REPO = WEEK.parent
BASELINE = json.loads((PROJECT / "tests/source-baseline.json").read_text())
NEW_ROOT_ROW = "| 10 | Azure DevOps (CI/CD) | 🔄 In Progress | [A1 manual run verified; A2–A4 preparation and submission evidence pending](./week-10-azure-devops/README.md) | — | — |"
A1 = WEEK / next(name for name in BASELINE["briefs"] if name.startswith("assignment-01-"))


class PreservationTests(unittest.TestCase):
    def test_every_original_brief_byte_preserved(self):
        for name, expected in BASELINE["briefs"].items():
            with self.subTest(brief=name):
                raw = (WEEK / name).read_bytes()
                raw = re.sub(rb"<!-- BEGIN WEEK10 CAPTURE (A1-S1|A1-S7|A2-S1|A2-S3) -->\n.*?<!-- END WEEK10 CAPTURE \1 -->\n\n", b"", raw, flags=re.S)
                if name.startswith("assignment-01-"):
                    raw, count = re.subn(
                        rb"<!-- BEGIN WEEK10 A1 OFFLINE PREPARATION -->\n.*?<!-- END WEEK10 A1 OFFLINE PREPARATION -->\n\n",
                        b"", raw, flags=re.S,
                    )
                    self.assertEqual(count, 1)
                self.assertEqual(len(raw), expected["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["sha256"])

    def test_seven_exact_screenshot_titles_and_eight_unchecked_items(self):
        text = A1.read_text()
        self.assertEqual(re.findall(r"^#### (Screenshot [0-9]+ .+)$", text, re.M), BASELINE["a1_screenshot_titles"])
        self.assertEqual(len(BASELINE["a1_screenshot_titles"]), 7)
        self.assertEqual(re.findall(r"^- \[ \] (.+)$", text, re.M), BASELINE["a1_unchecked_checklist"])
        self.assertEqual(len(BASELINE["a1_unchecked_checklist"]), 8)
        self.assertEqual(text.count("Add your screenshot here."), 7)
        self.assertEqual(text.count("Write your answer here."), 1)
        self.assertNotRegex(text, r"(?m)^- \[[xX]\]")

    def test_week_index_counts_match_all_five_briefs(self):
        counts = []
        checklists = []
        for name in BASELINE["briefs"]:
            text = (WEEK / name).read_text()
            counts.append(len(re.findall(r"^#{2,6} Screenshot [0-9]+ — ", text, re.M)))
            checklists.append(len(re.findall(r"^[*-] \[ \] ", text, re.M)))
        self.assertEqual(counts, [7, 5, 6, 6, 12])
        self.assertEqual(checklists, [8, 22, 21, 40, 33])
        self.assertEqual(sum(counts), 36)
        a2 = WEEK / next(name for name in BASELINE["briefs"] if name.startswith("assignment-02-"))
        self.assertEqual(a2.read_text().count("## LinkedIn Post Screenshot"), 1)

    def test_root_has_only_authorized_week10_row_change(self):
        raw = (REPO / "README.md").read_bytes()
        self.assertEqual(raw.count(NEW_ROOT_ROW.encode()), 1)
        original = raw.replace(NEW_ROOT_ROW.encode(), BASELINE["root_original_row"].encode())
        self.assertEqual(hashlib.sha256(original).hexdigest(), BASELINE["root_readme_sha256"])
        self.assertEqual(BASELINE["base_commit"], "d7c5fbf15c25edf2cc2d23c07d69796ed4b19212")

    def test_manifest_is_allowlisted_and_only_real_captures_are_attached(self):
        manifest = json.loads((PROJECT / "evidence/manifest.json").read_text())
        self.assertEqual(set(manifest), {"schema_version", "assignment", "status", "live_verified", "screenshots"})
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["assignment"], "week-10-assignment-01")
        self.assertEqual(manifest["status"], "partial_captures_review_pending")
        self.assertIs(manifest["live_verified"], False)
        self.assertEqual(len(manifest["screenshots"]), 7)
        captures = {item["slot"]: item for item in json.loads((WEEK / "evidence/captures-2026-09-19.json").read_text())["captures"] if item["assignment"] == 1}
        self.assertEqual(set(captures), {1, 7})
        for number, item in enumerate(manifest["screenshots"], 1):
            self.assertEqual(set(item), {"slot", "title", "status", "captured", "path", "sha256", "captured_at", "run_url"})
            self.assertEqual(item["slot"], number)
            self.assertEqual(item["title"], BASELINE["a1_screenshot_titles"][number - 1])
            if number in captures:
                self.assertEqual(item["status"], "captured_review_pending")
                self.assertIs(item["captured"], True)
                for key in ("path", "sha256", "captured_at"):
                    self.assertEqual(item[key], captures[number][key])
                self.assertEqual(item["run_url"], captures[number]["source_url"])
                self.assertEqual(hashlib.sha256((WEEK / item["path"]).read_bytes()).hexdigest(), item["sha256"])
            else:
                self.assertEqual(item["status"], "pending")
                self.assertIs(item["captured"], False)
                for key in ("path", "sha256", "captured_at", "run_url"):
                    self.assertIsNone(item[key])

    def test_no_new_images_or_javascript(self):
        prohibited = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".js", ".jsx", ".ts", ".tsx"}
        self.assertFalse([p for p in PROJECT.rglob("*") if p.suffix.lower() in prohibited])

    def test_local_delivery_links_resolve(self):
        for path in (WEEK / "README.md", PROJECT / "README.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if target.startswith(("https://", "http://", "#")):
                    continue
                with self.subTest(file=path.name, target=target):
                    self.assertTrue((path.parent / target.split("#")[0]).exists())


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parsed = subprocess.run(
            ["/usr/bin/ruby", "--disable-gems", "-rpsych", "-rjson", "-e",
             "puts JSON.generate(Psych.safe_load(STDIN.read, [], [], false))"],
            input=(PROJECT / "azure-pipelines.yml").read_text(), capture_output=True,
            text=True, check=True, timeout=10,
        )
        cls.pipeline = json.loads(parsed.stdout)

    def test_manual_only_no_resources_schedules_or_ci(self):
        self.assertEqual(set(self.pipeline), {"trigger", "pr", "parameters", "jobs"})
        self.assertEqual(self.pipeline["trigger"], "none")
        self.assertEqual(self.pipeline["pr"], "none")
        self.assertEqual(len(self.pipeline["jobs"]), 1)
        self.assertEqual(self.pipeline["jobs"][0]["condition"], "eq(variables['Build.Reason'], 'Manual')")

    def test_runtime_pool_and_linux_demand(self):
        self.assertEqual(self.pipeline["parameters"], [{
            "name": "poolName", "displayName": "Approved dedicated self-hosted pool (replace the placeholder)",
            "type": "string", "default": "__choose_approved_pool__",
        }])
        job = self.pipeline["jobs"][0]
        self.assertEqual(job["pool"], {"name": "${{ parameters.poolName }}", "demands": ["Agent.OS -equals Linux"]})
        self.assertEqual(job["timeoutInMinutes"], 5)

    def test_only_nonroot_check_and_required_commands_no_checkout(self):
        job = self.pipeline["jobs"][0]
        self.assertEqual(set(job), {"job", "displayName", "condition", "timeoutInMinutes", "pool", "steps"})
        self.assertEqual(len(job["steps"]), 2)
        self.assertEqual(job["steps"][0], {"checkout": "none"})
        self.assertEqual(set(job["steps"][1]), {"bash", "displayName"})
        self.assertEqual(job["steps"][1]["bash"].splitlines(), [
            "set -euo pipefail", 'test "$(id -u)" -ne 0', "uname -a", "whoami", "df -h",
        ])


class PolicyTests(unittest.TestCase):
    def test_helper_has_only_readonly_imports_and_no_execution_calls(self):
        tree = ast.parse((PROJECT / "validate_candidate.py").read_text())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, {"exec", "eval", "compile", "__import__", "system", "popen", "spawn", "write_text", "write_bytes", "unlink", "mkdir"})
                if name == "open":
                    self.assertEqual(len(node.args), 1)
                    self.assertEqual(ast.literal_eval(node.args[0]), "rb")
        self.assertEqual(imports, {"argparse", "hashlib", "json", "re", "sys", "pathlib"})

    def test_runbook_preserves_secret_and_authorization_guards(self):
        text = (PROJECT / "README.md").read_text()
        for phrase in (
            "STOP before any live action", "Merging source is not deployment consent",
            "Agent Pools (Read & Manage)", "Build (Read & Execute)", "shortest practical expiry",
            "command arguments, shell history, environment exports, YAML variables, commits, logs, screenshots",
            "hidden interactive prompt", "unattended token flag", "no general sudo permission",
            "Do not use `runAsRoot`", "untrusted/public fork PRs", "Do **not** grant access to all pipelines",
            "sudo ./svc.sh install azdoagent", "sudo ./svc.sh stop", "sudo ./svc.sh uninstall",
            "./config.sh remove", "Revoking the PAT alone does not decommission the agent",
            "All cloud resource changes must go through reviewed Terraform",
            "live compatibility gate", "source preparation only",
        ):
            self.assertIn(phrase.lower(), text.lower())
        for block in re.findall(r"```(?:sh|bash)\n(.*?)```", text, re.S):
            self.assertNotRegex(block, r"--token|AZP_TOKEN|VSO_AGENT_INPUT_TOKEN|set -x|curl|wget|runAsRoot|NOPASSWD")

    def test_example_contains_no_live_choices_or_credentials(self):
        candidate = json.loads((PROJECT / "candidate.example.json").read_text())
        for key in ("organization_url", "pool_name", "agent_name"):
            self.assertIsNone(candidate[key])
        self.assertIs(candidate["package"]["compatibility_reviewed"], False)
        for key in ("version", "architecture", "download_url", "sha256", "metadata_url"):
            self.assertIsNone(candidate["package"][key])


if __name__ == "__main__":
    unittest.main()
