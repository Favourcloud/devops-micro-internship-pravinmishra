"""Offline subprocess tests only. All scratch files stay inside this project."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "AI Assignment/tf-drift-check.sh"
CLEAN = json.loads((ROOT / "fixtures/clean.json").read_text())
DETECTED = json.loads((ROOT / "fixtures/detected.json").read_text())


class ReviewTests(unittest.TestCase):
    def setUp(self):
        private = ROOT / ".review-data"
        private.mkdir(mode=0o700, exist_ok=True)
        self.work = private / ("test-" + uuid.uuid4().hex)
        self.work.mkdir(mode=0o700)
        self.addCleanup(shutil.rmtree, self.work)
        self.serial = 0

    def check(self, plan, code, status, *, env=None, name="fixture.json"):
        self.serial += 1
        source = self.work / (str(self.serial) + name)
        source.write_text(json.dumps(plan) if not isinstance(plan, str) else plan)
        report = self.work / f"report-{self.serial}.txt"
        process = subprocess.run(["/bin/bash", str(SCRIPT), "--fixture", str(source), "--report", str(report)],
                                 text=True, capture_output=True, env=env, cwd=ROOT)
        self.assertEqual(process.returncode, code, process.stdout + process.stderr)
        if report.exists():
            text = report.read_text()
            self.assertIn("Overall Status: " + status, text)
            self.assertTrue(text.startswith("SYNTHETIC FIXTURE DEMONSTRATION"))
            self.assertIn("Reviewer: Eze Favour", text)
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
            self.assertFalse(list(self.work.glob(".review-run-*")))
            return text
        self.assertNotEqual(code, 0)
        return process.stdout + process.stderr

    def changed(self, actions):
        plan = copy.deepcopy(DETECTED)
        resource = plan["resource_changes"][0]
        resource["change"]["actions"] = actions
        resource["change"]["after"]["ingress"] = []
        plan["planned_values"]["root_module"]["resources"][0]["values"]["ingress"] = []
        if actions == ["delete"]:
            resource["change"]["after"] = None
            plan["planned_values"] = {}
        elif actions == ["create"]:
            resource["change"]["before"] = None
        return plan

    def ingress(self, kind, *, cidr="0.0.0.0/0", ipv6=False, port=22, protocol="tcp"):
        plan = copy.deepcopy(CLEAN)
        resource = plan["planned_values"]["root_module"]["resources"][0]
        rule = copy.deepcopy(DETECTED["resource_changes"][0]["change"]["after"]["ingress"][0])
        rule.update(from_port=port, to_port=port, protocol=protocol,
                    cidr_blocks=[] if ipv6 else [cidr], ipv6_cidr_blocks=[cidr] if ipv6 else [])
        resource["type"] = kind
        if kind == "aws_security_group":
            resource["values"]["ingress"] = [rule]
        elif kind == "aws_security_group_rule":
            resource["values"] = rule | {"type": "ingress"}
        else:
            resource["values"] = {"ip_protocol": protocol, "from_port": port, "to_port": port,
                                  "cidr_ipv6" if ipv6 else "cidr_ipv4": cidr}
        return plan

    def test_clean_and_empty(self):
        for plan in (CLEAN, json.loads((ROOT / "fixtures/empty.json").read_text())):
            with self.subTest(plan=bool(plan["planned_values"])):
                self.check(plan, 0, "HEALTHY")

    def test_non_destructive_actions(self):
        for actions in (["update"], ["create"], ["read"]):
            with self.subTest(actions=actions):
                self.check(self.changed(actions), 1, "WARN")

    def test_delete_and_both_replacement_orders(self):
        for actions in (["delete"], ["delete", "create"], ["create", "delete"]):
            with self.subTest(actions=actions):
                self.check(self.changed(actions), 2, "FAIL")

    def test_all_three_ingress_representations(self):
        for kind in ("aws_security_group", "aws_security_group_rule", "aws_vpc_security_group_ingress_rule"):
            for cidr, ipv6 in (("0.0.0.0/0", False), ("::/0", True), ("0:0:0:0:0:0:0:0/0", True)):
                with self.subTest(kind=kind, cidr=cidr):
                    self.check(self.ingress(kind, cidr=cidr, ipv6=ipv6), 2, "FAIL")

    def test_sensitive_ports_and_all_protocols(self):
        for port, protocol in ((3389, "tcp"), (5432, "6"), (22, "udp"), (None, "-1"), (-1, "icmp")):
            with self.subTest(port=port, protocol=protocol):
                self.check(self.ingress("aws_vpc_security_group_ingress_rule", port=port, protocol=protocol), 2, "FAIL")

    def test_intentional_http_is_warn_not_blanket_approval(self):
        for kind in ("aws_security_group", "aws_security_group_rule", "aws_vpc_security_group_ingress_rule"):
            for port in (80, 443):
                with self.subTest(kind=kind, port=port):
                    self.check(self.ingress(kind, port=port), 1, "WARN")

    def test_public_subnets_and_noncanonical_cidrs(self):
        for cidr in ("8.8.8.0/24", "1.2.3.4/0", "128.0.0.0/1"):
            with self.subTest(cidr=cidr):
                self.check(self.ingress("aws_security_group", cidr=cidr), 2, "FAIL")

    def test_restricted_ipv4_and_ipv6(self):
        for cidr, ipv6 in (("10.0.0.0/24", False), ("fd00::/64", True)):
            with self.subTest(cidr=cidr):
                self.check(self.ingress("aws_security_group", cidr=cidr, ipv6=ipv6), 0, "HEALTHY")

    def test_invalid_cidrs_unknown_protocol_and_ports(self):
        for kwargs in ({"cidr": "garbage"}, {"cidr": "::/0"}, {"protocol": "future-protocol"}, {"port": "22"}, {"port": 70000}):
            with self.subTest(kwargs=kwargs):
                self.check(self.ingress("aws_security_group", **kwargs), 1, "WARN")

    def test_unknown_or_unsupported_rule_representation(self):
        for values in ({}, {"ingress": None}, {"ingress": {}}, {"ingress": [None]},
                       {"ingress": [{"protocol": "tcp", "from_port": 22, "to_port": 22, "prefix_list_ids": ["synthetic-prefix"]}]}):
            with self.subTest(values=values):
                plan = copy.deepcopy(CLEAN)
                plan["planned_values"]["root_module"]["resources"][0]["values"] = values
                self.check(plan, 1, "WARN")

    def test_unknown_values_and_deferred_evidence(self):
        for key, value in (("proposed_unknown", {"outputs": {"x": True}}), ("complete", False),
                           ("deferred_changes", [{"reason": "synthetic"}]), ("checks", [{"status": "unknown"}])):
            with self.subTest(key=key):
                plan = copy.deepcopy(CLEAN); plan[key] = value
                self.check(plan, 1, "WARN")
        plan = self.changed(["no-op"])
        plan["resource_changes"][0]["change"]["after_unknown"] = {"ingress": True}
        self.check(plan, 1, "WARN")

    def test_output_only_and_refresh_only_changes(self):
        plan = copy.deepcopy(CLEAN)
        plan["output_changes"] = {"demo": {"actions": ["update"], "before": "old", "after": "new", "after_unknown": False}}
        self.check(plan, 1, "WARN")
        plan = self.changed(["update"])
        plan["resource_drift"] = plan.pop("resource_changes")
        self.check(plan, 1, "WARN")

    def test_unknown_resource_and_provider(self):
        for key, value in (("type", "aws_network_acl_rule"), ("provider_name", "example.invalid/custom/aws")):
            with self.subTest(key=key):
                plan = copy.deepcopy(CLEAN)
                plan["planned_values"]["root_module"]["resources"][0][key] = value
                self.check(plan, 1, "WARN")

    def test_nested_modules_and_noop_rules(self):
        plan = self.ingress("aws_security_group", cidr="::/0", ipv6=True)
        module = plan["planned_values"]["root_module"]
        plan["planned_values"]["root_module"] = {"child_modules": [module]}
        self.check(plan, 2, "FAIL")

    def test_malformed_json_and_root(self):
        for plan in ("{", "{} {}", "[]", "null", "{}", '{"format_version":"1.2","format_version":"1.2"}', '{"x":NaN}'):
            with self.subTest(plan=plan):
                self.check(plan, 3, "ERROR")
        for key, value in (("format_version", "9.9"), ("resource_changes", None), ("planned_values", []),
                           ("output_changes", []), ("errored", True), ("complete", "true")):
            with self.subTest(key=key):
                plan = copy.deepcopy(CLEAN); plan[key] = value
                self.check(plan, 3, "ERROR")

    def test_malformed_resource_change(self):
        for key in ("address", "type", "provider_name", "mode", "change"):
            with self.subTest(key=key):
                plan = self.changed(["update"]); del plan["resource_changes"][0][key]
                self.check(plan, 3, "ERROR")
        for key, value in (("actions", []), ("actions", ["forget"]), ("actions", "delete"),
                           ("after", None), ("after", []), ("before", "invalid"), ("after_unknown", None)):
            with self.subTest(key=key, value=value):
                plan = self.changed(["update"]); plan["resource_changes"][0]["change"][key] = value
                self.check(plan, 3, "ERROR")

    def test_inconsistent_noop_and_multiple_modern_sources(self):
        plan = self.changed(["no-op"])
        plan["resource_changes"][0]["change"]["after"]["description"] = "changed despite no-op"
        self.check(plan, 3, "ERROR")
        plan = self.ingress("aws_vpc_security_group_ingress_rule", cidr="10.0.0.0/24")
        plan["planned_values"]["root_module"]["resources"][0]["values"]["cidr_ipv6"] = "fd00::/64"
        self.check(plan, 1, "WARN")

    def test_missing_input_and_output_parent(self):
        for report in (self.work / "report.txt", self.work / "missing/report.txt"):
            with self.subTest(report=report.name):
                proc = subprocess.run(["/bin/bash", str(SCRIPT), "--fixture", str(self.work / "absent.json"), "--report", str(report)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 3)
                self.assertNotIn("Overall Status: HEALTHY", proc.stdout)

    def test_no_overwrite_or_symlink_output(self):
        old = self.work / "old.txt"; old.write_text("historical evidence")
        link = self.work / "link.txt"; link.symlink_to(old)
        for report in (old, link):
            with self.subTest(report=report.name):
                proc = subprocess.run(["/bin/bash", str(SCRIPT), "--fixture", str(ROOT / "fixtures/clean.json"), "--report", str(report)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 3)
                self.assertEqual(old.read_text(), "historical evidence")

    def test_filename_spaces_and_shell_metacharacters(self):
        self.check(CLEAN, 0, "HEALTHY", name=' space;$(touch SHOULD_NOT_EXIST) [x].json')
        self.assertFalse((ROOT / "SHOULD_NOT_EXIST").exists())
        folder = self.work / 'output space;$(touch BAD)'; folder.mkdir()
        proc = subprocess.run(["/bin/bash", str(SCRIPT), "--fixture", str(ROOT / "fixtures/clean.json"), "--report", str(folder / "report [x].txt")], capture_output=True)
        self.assertEqual(proc.returncode, 0)
        self.assertFalse((ROOT / "BAD").exists())

    def test_sensitive_values_do_not_enter_report(self):
        plan = self.changed(["update"])
        secret = "SYNTHETIC_SECRET_MUST_NEVER_LEAK_12345"
        plan["resource_changes"][0]["change"]["after"]["password"] = secret
        plan["variables"] = {"token": {"value": secret}}
        plan["resource_changes"][0]["address"] = secret
        text = self.check(plan, 1, "WARN")
        self.assertNotIn(secret, text)
        self.assertNotIn(str(self.work), text)

    def test_missing_jq_and_python_fail_closed(self):
        tools = self.work / "tools"; tools.mkdir()
        (tools / "dirname").symlink_to(shutil.which("dirname"))
        (tools / "python3.13").symlink_to(sys.executable)
        env = dict(os.environ, PATH=str(tools))
        self.check(CLEAN, 3, "ERROR", env=env)
        (tools / "python3.13").unlink()
        self.check(CLEAN, 3, "ERROR", env=env)

    def simulate_live(self, exit_code, *, plan=None, omit_binary=False, show_exit=0, env_extra=None):
        self.serial += 1
        fake = self.work / f"fake-{self.serial}"; fake.mkdir()
        control = fake / "control.json"
        control.write_text(json.dumps({"exit": exit_code, "plan": CLEAN if plan is None else plan, "omit_binary": omit_binary, "show_exit": show_exit}))
        executable = fake / "terraform"
        executable.write_text(f'''#!{sys.executable}
import json,sys
from pathlib import Path
root=Path(__file__).parent
config=json.loads((root/'control.json').read_text())
with (root/'calls.jsonl').open('a') as log: log.write(json.dumps(sys.argv[1:])+'\\n')
if sys.argv[1] == 'plan':
    assert sys.argv[2:5] == ['-input=false','-no-color','-detailed-exitcode']
    assert len(sys.argv) == 6 and sys.argv[5].startswith('-out=')
    if not config['omit_binary']: Path(sys.argv[5][5:]).write_text('SYNTHETIC_BINARY')
    print('SYNTHETIC_PRIVATE_PROVIDER_LOG',file=sys.stderr)
    sys.exit(config['exit'])
if sys.argv[1:3] == ['show','-json']:
    assert len(sys.argv) == 4
    print(json.dumps(config['plan']))
    sys.exit(config['show_exit'])
raise AssertionError('Forbidden Terraform command')
''')
        executable.chmod(0o700)
        report = fake / "report.txt"
        env = dict(os.environ, PATH=str(fake) + os.pathsep + os.environ["PATH"])
        for key in ("TF_CLI_ARGS", "TF_CLI_ARGS_plan", "TF_CLI_ARGS_show"):
            env.pop(key, None)
        env.update(env_extra or {})
        process = subprocess.run(["/bin/bash", str(SCRIPT), "--live", "--terraform-dir", str(fake), "--authorize-live-read-only", "--report", str(report)], capture_output=True, text=True, env=env)
        calls = [json.loads(line) for line in (fake / "calls.jsonl").read_text().splitlines()] if (fake / "calls.jsonl").exists() else []
        self.assertNotIn("SYNTHETIC_PRIVATE_PROVIDER_LOG", process.stdout + process.stderr)
        self.assertFalse(list(fake.glob(".review-run-*")))
        return process, calls

    def test_fake_terraform_detailed_exit_codes(self):
        for plan_exit, plan, code, status in ((0, CLEAN, 0, "HEALTHY"), (1, CLEAN, 3, "ERROR"), (2, DETECTED, 2, "FAIL"), (9, CLEAN, 3, "ERROR")):
            with self.subTest(exit=plan_exit):
                process, calls = self.simulate_live(plan_exit, plan=plan)
                self.assertEqual(process.returncode, code, process.stdout + process.stderr)
                self.assertIn("Overall Status: " + status, process.stdout)
                self.assertEqual([call[0] for call in calls], ["plan", "show"] if plan_exit in (0, 2) else ["plan"])

    def test_fake_terraform_missing_binary_show_error_and_stale_mismatch(self):
        for kwargs in ({"omit_binary": True}, {"show_exit": 1}, {"plan": {}}, {"plan": DETECTED}):
            with self.subTest(kwargs=kwargs):
                process, _ = self.simulate_live(0, **kwargs)
                self.assertEqual(process.returncode, 3)
        process, _ = self.simulate_live(2)
        self.assertEqual(process.returncode, 3)

    def test_live_requires_explicit_authorization_and_rejects_injected_flags(self):
        proc = subprocess.run(["/bin/bash", str(SCRIPT), "--live", "--terraform-dir", str(self.work), "--report", str(self.work / "unauthorized.txt")], capture_output=True)
        self.assertEqual(proc.returncode, 3)
        for variable in ("TF_CLI_ARGS", "TF_CLI_ARGS_plan", "TF_CLI_ARGS_show"):
            with self.subTest(variable=variable):
                process, calls = self.simulate_live(0, env_extra={variable: "-destroy"})
                self.assertEqual(process.returncode, 3)
                self.assertEqual(calls, [])


class HookTests(unittest.TestCase):
    def setUp(self):
        private = ROOT / ".review-data"; private.mkdir(mode=0o700, exist_ok=True)
        self.work = private / ("hook-" + uuid.uuid4().hex); self.work.mkdir(mode=0o700)
        self.addCleanup(shutil.rmtree, self.work)
        hook_dir = self.work / ".claude/hooks"; hook_dir.mkdir(parents=True)
        self.hook = hook_dir / "review_gate.py"
        shutil.copyfile(ROOT / ".claude/hooks/review_gate.py", self.hook)
        (self.work / ".review-data").mkdir()

    def invoke(self, command=None, *, raw=None, tool="Bash", payload=None):
        event = {"hook_event_name": "PreToolUse", "cwd": str(self.work), "tool_name": tool,
                 "tool_input": payload if payload is not None else {"command": command}}
        env = dict(os.environ); env.pop("BASH_ENV", None); env.pop("ENV", None)
        return subprocess.run([sys.executable, str(self.hook)], input=json.dumps(event) if raw is None else raw,
                              text=True, capture_output=True, cwd=self.work, env=env)

    def test_allowed_review_commands(self):
        for command in ('cat reports/resolved-report.txt', 'ls -l reports', 'bash -n "AI Assignment/tf-drift-check.sh"',
                        'bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/clean.json --report .review-data/current-report.txt'):
            with self.subTest(command=command):
                self.assertEqual(self.invoke(command).returncode, 0)

    def test_mutation_always_denied_for_every_report_state(self):
        report = self.work / ".review-data/current-report.txt"
        now = datetime.now(timezone.utc)
        reports = (None, "malformed", f"Timestamp UTC: {now.isoformat()}\nOverall Status: FAIL\n",
                   f"Timestamp UTC: {now.isoformat()}\nOverall Status: HEALTHY\nMode: FIXTURE\n",
                   f"Timestamp UTC: {(now-timedelta(hours=1)).isoformat()}\nOverall Status: HEALTHY\n",
                   f"Timestamp UTC: {now.isoformat()}\nOverall Status: HEALTHY\nMode: LIVE\n")
        for text in reports:
            if text is not None: report.write_text(text)
            for command in ("terraform apply", "terraform destroy", "terraform apply -auto-approve"):
                with self.subTest(report=text, command=command):
                    self.assertEqual(self.invoke(command).returncode, 2)
        report.write_text(f"Timestamp UTC: {now.isoformat()}\nOverall Status: FAIL\n")
        self.assertIn("report=FAIL", self.invoke("terraform apply").stderr)

    def test_chaining_substitution_wrappers_and_environment_denied(self):
        for command in ("cat reports/resolved-report.txt; terraform apply", "ls -l reports && terraform destroy", "ls -l reports | sh",
                        "$(terraform apply)", "`terraform apply`", "env terraform apply", "bash -c 'terraform apply'", "command terraform apply",
                        "TF_CLI_ARGS=-auto-approve terraform apply", "python3.13 -c 'print(1)'", "ls -l reports\nterraform apply",
                        "cat reports/resolved-report.txt > evidence.txt", " cat reports/resolved-report.txt", "bash .claude/hooks/review_gate.py"):
            with self.subTest(command=command):
                self.assertEqual(self.invoke(command).returncode, 2)

    def test_bad_payload_and_outside_paths_denied(self):
        for raw in ("{", "[]", "{}", '{"tool_name":"Bash","tool_name":"Read"}', '{"hook_event_name":"PreToolUse","tool_input":null}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.invoke(raw=raw).returncode, 2)
        self.assertEqual(self.invoke(tool="Read", payload={"file_path": "../secret"}).returncode, 2)
        self.assertEqual(self.invoke(tool="Write", payload={"file_path": "README.md", "content": "x"}).returncode, 2)
        self.assertEqual(self.invoke(tool="Read", payload={"file_path": "README.md"}).returncode, 0)
        self.assertEqual(self.invoke(tool="Grep", payload={"path": "lib", "pattern": "delete"}).returncode, 0)
        self.assertEqual(self.invoke(payload={"command": "ls -l reports", "run_in_background": True}).returncode, 2)
        self.assertEqual(self.invoke(payload={"command": "ls -l reports", "env": {"PATH": "untrusted"}}).returncode, 2)

    def test_settings_and_skill_configuration(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text())
        hook = settings["hooks"]["PreToolUse"][0]
        self.assertEqual(hook["matcher"], "*")
        self.assertEqual(hook["hooks"][0]["command"], "python3.13")
        self.assertEqual(hook["hooks"][0]["args"], ["${CLAUDE_PROJECT_DIR}/.claude/hooks/review_gate.py"])
        skill = (ROOT / ".claude/skills/tf-drift-review/SKILL.md").read_text()
        self.assertTrue(skill.startswith("---\n"))
        self.assertIn("disable-model-invocation: true", skill)
        self.assertIn("allowed-tools: Bash Read Grep", skill)
        self.assertIn("**noWrite:**", skill)


class SubmissionTests(unittest.TestCase):
    def test_assignment_requirements_preserved(self):
        metadata = json.loads((ROOT / "tests/assignment-source.json").read_text())
        submission = (ROOT.parent / "assignment-06-ai-assisted-terraform-drift-and-policy-review.md").read_text()
        lines = submission.splitlines()
        for heading in metadata["required_headings"]:
            self.assertIn(heading, lines)
        for item in metadata["required_checklist"]:
            self.assertTrue(any(line in ("- [ ] " + item, "- [x] " + item) for line in lines), item)
        self.assertEqual(len(re.findall(r"^### Screenshot \d+ —", submission, re.M)), 19)
        self.assertEqual(submission.count("Add your screenshot here."), 19)
        self.assertIn("Add a screenshot of the published LinkedIn post here.", submission)

    def test_local_markdown_links(self):
        docs = list(ROOT.rglob("*.md")) + [ROOT.parent / "assignment-06-ai-assisted-terraform-drift-and-policy-review.md"]
        for doc in docs:
            if ".review-data" in doc.parts:
                continue
            for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
                if target.startswith(("https://", "http://", "#")):
                    continue
                target = target.split("#", 1)[0].replace("%20", " ")
                self.assertTrue((doc.parent / target).exists(), f"{doc.name}: {target}")


if __name__ == "__main__":
    unittest.main()
