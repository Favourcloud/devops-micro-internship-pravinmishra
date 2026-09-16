"""Offline subprocess tests only. All scratch files stay inside this project."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
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

    def test_only_named_sanitized_live_reports_are_readable(self):
        for filename in ("baseline-report.txt", "drift-detected-report.txt", "resolved-report.txt"):
            with self.subTest(report=filename):
                process = self.invoke(tool="Read", payload={"file_path": "reports/live/" + filename})
                self.assertEqual(process.returncode, 0)
                context = json.loads(process.stdout)["hookSpecificOutput"]
                self.assertEqual(context["hookEventName"], "PreToolUse")
                self.assertNotIn("permissionDecision", context)
                self.assertIn("not mutation authorization", context["additionalContext"])
        for path in ("reports/live/unknown.txt", "reports/live", "terraform/network/terraform.tfstate",
                     ".review-data/live-session-20260915/created-bindings.json", "~/.aws/credentials"):
            with self.subTest(denied=path):
                self.assertEqual(self.invoke(tool="Read", payload={"file_path": path}).returncode, 2)
        self.assertEqual(self.invoke(tool="Grep", payload={"path": "reports/live", "pattern": "."}).returncode, 2)
        live = self.work / "reports/live"
        live.mkdir(parents=True)
        (live / "baseline-report.txt").symlink_to(self.work / "private.txt")
        self.assertEqual(self.invoke(tool="Read", payload={"file_path": "reports/live/baseline-report.txt"}).returncode, 2)

    def test_configured_exec_form_command(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text())
        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]
        spaced = self.work / "project with spaces"
        script = spaced / ".claude/hooks/review_gate.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(self.hook, script)
        (spaced / ".review-data").mkdir()
        for workspace in (self.work, spaced):
            command = [hook["command"], *(arg.replace("${CLAUDE_PROJECT_DIR}", str(workspace))
                                         for arg in hook["args"])]
            for tool, payload, expected_exit in (
                ("Read", {"file_path": "README.md"}, 0),
                ("Bash", {"command": "ls -l reports"}, 0),
                ("Bash", {"command": "terraform apply -input=false"}, 2),
            ):
                with self.subTest(workspace=workspace.name, tool=tool, payload=payload):
                    event = {"hook_event_name": "PreToolUse", "cwd": str(workspace),
                             "tool_name": tool, "tool_input": payload}
                    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(workspace))
                    env.pop("BASH_ENV", None); env.pop("ENV", None)
                    process = subprocess.run(command, input=json.dumps(event), text=True,
                                             capture_output=True, cwd=workspace, env=env,
                                             timeout=hook["timeout"])
                    self.assertEqual(process.returncode, expected_exit, process.stderr)
                    if expected_exit == 2:
                        self.assertIn("DENY:", process.stderr)
                    else:
                        context = json.loads(process.stdout)["hookSpecificOutput"]
                        self.assertEqual(context["hookEventName"], "PreToolUse")
                        self.assertIn("not mutation authorization", context["additionalContext"])

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
    captures = {
        1: ("screenshot-01-clean-plan.png", {"reports/live/baseline-execution.txt"}),
        2: ("screenshot-02-workspace.png", {"terraform/network/main.tf"}),
        3: ("screenshot-03-context.png", {"CLAUDE.md"}),
        4: ("screenshot-04-variables-checks.png", {"AI Assignment/tf-drift-check.sh"}),
        5: ("screenshot-05-policy-checks.png", {"AI Assignment/tf-drift-check.sh", "lib/ingress.jq"}),
        6: ("screenshot-06-validation-permissions.png", {"AI Assignment/tf-drift-check.sh"}),
        7: ("screenshot-07-healthy-baseline.png", {"reports/live/baseline-report.txt"}),
        8: ("screenshot-08-baseline-exit.png", {"reports/live/baseline-execution.txt"}),
        9: ("screenshot-09-skill-configuration.png", {".claude/skills/tf-drift-review/SKILL.md"}),
        11: ("screenshot-11-unapplied-proposal.png", {"terraform/public-ssh-proposal.tfvars.example"}),
        13: ("screenshot-13-live-detected-report.png", {"reports/live/drift-detected-report.txt"}),
        14: ("screenshot-14-hook-configuration.png", {".claude/settings.json"}),
        18: ("screenshot-18-saved-reports.png", {"reports/drift-detected-report.txt", "reports/resolved-report.txt",
                                               "reports/live/drift-detected-report.txt", "reports/live/resolved-report.txt"}),
        19: ("screenshot-19-summary.png", {"drift-review-summary.md"}),
    }

    def test_assignment_requirements_preserved(self):
        metadata = json.loads((ROOT / "tests/assignment-source.json").read_text())
        submission = (ROOT.parent / "assignment-06-ai-assisted-terraform-drift-and-policy-review.md").read_text()
        lines = submission.splitlines()
        for heading in metadata["required_headings"]:
            self.assertIn(heading, lines)
        for item in metadata["required_checklist"]:
            self.assertTrue(any(line in ("- [ ] " + item, "- [x] " + item) for line in lines), item)
        self.assertEqual(len(re.findall(r"^### Screenshot \d+ —", submission, re.M)), 19)
        self.assertEqual(submission.count("Add your screenshot here."), 19 - len(self.captures))
        sections = {int(number): body for number, body in re.findall(
            r"^### Screenshot (\d+) — [^\n]+\n(.*?)(?=^### Screenshot \d+ —|\Z)", submission, re.M | re.S)}
        self.assertEqual(set(sections), set(range(1, 20)))
        for number, body in sections.items():
            with self.subTest(screenshot=number):
                images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
                if number in self.captures:
                    self.assertEqual(images, ["drift-review/screenshots/" + self.captures[number][0]])
                    self.assertNotIn("Add your screenshot here.", body)
                else:
                    self.assertEqual(images, [])
                    self.assertEqual(body.count("Add your screenshot here."), 1)
        self.assertIn("Add a screenshot of the published LinkedIn post here.", submission)
        self.assertIn("- [ ] Included all 19 numbered screenshots", submission)
        self.assertIn("- [ ] Published the required LinkedIn post", submission)

    def test_enrollment_continuation_boundaries(self):
        self.assertIn("!reports/continuation-20260916.json", (ROOT / ".gitignore").read_text().splitlines())
        record = json.loads((ROOT / "reports/continuation-20260916.json").read_text())
        self.assertIn("NOT CLAUDE REVIEW OR DEPLOYMENT EVIDENCE", record["evidence_class"])
        self.assertEqual(record["model"], "anthropic.claude-haiku-4-5-20251001-v1:0")
        self.assertEqual(record["origin_region"], "ap-south-1")
        acceptance = record["offer_acceptance"]
        ready = record["independent_read_only_availability"]
        self.assertEqual(acceptance["status"], "ACCEPTANCE_RESPONSE_CONFIRMED")
        self.assertEqual(acceptance["immediate_agreement_status"], "PENDING")
        self.assertEqual([ready[key] for key in ("agreement", "authorization", "entitlement", "region")],
                         ["AVAILABLE", "AUTHORIZED", "AVAILABLE", "AVAILABLE"])
        self.assertIs(ready["acceptance_repeated"], False)
        self.assertIs(ready["model_invoked"], False)
        self.assertLess(datetime.fromisoformat(acceptance["timestamp_utc"]),
                        datetime.fromisoformat(ready["timestamp_utc"]))
        self.assertLess(datetime.fromisoformat(ready["timestamp_utc"]),
                        datetime.fromisoformat(record["mfa_session"]["expires_at_utc"]))
        self.assertEqual(record["mfa_session"]["permission_expires_at_utc"], "2026-09-16T13:30:00+00:00")
        self.assertIs(record["mfa_session"]["expiry_extended"], False)
        approval = record["review_budget_approval"]
        self.assertAlmostEqual(approval["maximum_new_usage_usd"] + approval["unchanged_unknown_usage_reservation_usd"],
                               approval["original_additional_allowance_usd"])
        for flag in ("provisioning_approved", "terraform_human_resolution_approved", "aws_account_spending_cap"):
            self.assertIs(approval[flag], False)
        plan = record["fresh_lab_preflight"]
        self.assertEqual(plan["terraform_plan_exit"], 2)
        self.assertEqual(plan["network_plan_resource_type"], "aws_vpc")
        self.assertEqual([plan[key] for key in ("network_plan_create_count", "network_plan_update_count", "network_plan_delete_count")], [1, 0, 0])
        for flag in ("network_plan_applied", "security_group_create_plan_prepared", "deleted_vpc_binding_reused"):
            self.assertIs(plan[flag], False)
        for digest in (acceptance["approved_offer_source_sha256"], acceptance["approved_legal_pdf_sha256"],
                       acceptance["private_result_sha256"], ready["private_result_sha256"], plan["network_plan_sha256"]):
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_screenshot_provenance_matches_files(self):
        manifest = json.loads((ROOT / "screenshots/manifest.json").read_text())
        self.assertEqual(manifest["student"], "Eze Favour")
        self.assertIn("SANITIZED HISTORICAL LIVE-EVIDENCE", manifest["evidence_class"])
        self.assertIn("NOT CLAUDE RUNTIME EVIDENCE", manifest["evidence_class"])
        self.assertEqual(manifest["pending_numbers"], [10, 12, 15, 16, 17])
        self.assertEqual(len(manifest["screenshots"]), len(self.captures))
        self.assertEqual({item["number"] for item in manifest["screenshots"]}, set(self.captures))
        self.assertEqual({path.name for path in (ROOT / "screenshots").glob("*.png")},
                         {filename for filename, _ in self.captures.values()})
        for item in manifest["screenshots"]:
            with self.subTest(screenshot=item["number"]):
                filename, sources = self.captures[item["number"]]
                self.assertEqual(item["file"], filename)
                image = (ROOT / "screenshots" / filename).read_bytes()
                self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", image[16:24]), (item["width_pixels"], item["height_pixels"]))
                self.assertEqual(hashlib.sha256(image).hexdigest(), item["sha256"])
                self.assertIs(item["image_modified"], False)
                self.assertEqual(datetime.fromisoformat(item["captured_at_utc"]).utcoffset(), timedelta(0))
                self.assertEqual(set(item["source_sha256"]), sources)
                for path, expected_hash in item["source_sha256"].items():
                    self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected_hash, path)

    def test_live_capture_scope_and_pending_runtime(self):
        text = (ROOT / "screenshots/manifest.json").read_text()
        manifest = json.loads(text)
        self.assertNotRegex(text, r"(?:AKIA|ASIA)[A-Z0-9]{16}|arn:aws:|/Users/|\b[0-9]{12}\b")
        items = {item["number"]: item for item in manifest["screenshots"]}
        for number in (1, 3, 7, 8, 9, 11, 13, 18, 19):
            with self.subTest(capture=number):
                item = items[number]
                proof = item["window_verification"]
                self.assertEqual(proof["bundle_id"], "com.microsoft.VSCode")
                self.assertIs(proof["native_owner_verified"], True)
                self.assertIs(proof["isolated_profile_verified"], True)
                self.assertIn("Eze Favour", proof["title"])
                self.assertIs(item["ocr_name_verified"], True)
                self.assertTrue(all(item["ocr_source_coverage"].values()))
                self.assertIs(item["privacy_preflight_passed"], True)
                expected = ("terminal" if number == 18 else "sanitized-historical-export"
                            if number in (1, 7, 8, 13) else "source-view")
                self.assertEqual(item["evidence_kind"], expected)
        self.assertEqual(items[18]["terminal_commands"], ["ls -lah -g -o reports", "ls -lah -g -o reports/live"])
        for number in (3, 9):
            self.assertNotEqual(items[number]["sha256"], items[number]["replaced_previous_sha256"])
        self.assertTrue(any("no image pixels were edited" in note for note in manifest["limitations"]))
        self.assertTrue(any("Human resolution approval is not established" in note for note in manifest["limitations"]))

    def test_prepared_terraform_and_preflight_boundaries(self):
        text = (ROOT / "reports/live-preflight.json").read_text()
        record = json.loads(text)
        self.assertEqual(record["status"], "BLOCKED")
        self.assertIs(record["identity"]["root"], False)
        self.assertIs(record["aws_mutations_performed"], False)
        self.assertIs(record["real_terraform_plan_performed"], False)
        self.assertIs(record["claude_skill_or_hook_exercised"], False)
        self.assertEqual(record["aws_checks"]["create-vpc-tagged"], "DryRunOperation")
        self.assertIn("UNVERIFIED", record["cleanup_permissions"])
        self.assertNotRegex(text, r"(?:AKIA|ASIA)[A-Z0-9]{16}|arn:aws:|/Users/|\b[0-9]{12}\b")
        self.assertEqual(len(record["source_sha256"]), 4)
        for source, expected in record["source_sha256"].items():
            with self.subTest(source=source):
                self.assertEqual(hashlib.sha256((ROOT / source).read_bytes()).hexdigest(), expected)
        resources = []
        for project in ("network", "security-group"):
            source = (ROOT / "terraform" / project / "main.tf").read_text()
            resources.extend(re.findall(r'resource "([^"]+)"', source))
            self.assertIn('profile             = "dmi-week8"', source)
            self.assertIn('allowed_account_ids = [var.expected_account_id]', source)
            self.assertIn('DmiLab = "dmi-week8-a6-favour-20260915"', source)
            self.assertTrue(record["terraform_validation"][project]["valid"])
        self.assertEqual(resources, ["aws_vpc", "aws_security_group"])
        self.assertIn('default     = false', (ROOT / "terraform/security-group/main.tf").read_text())

    def test_private_terraform_artifacts_are_not_hashed(self):
        from run_validation import is_private_artifact
        for path in ("terraform/network/.terraform/providers/provider", "terraform/network/terraform.tfstate",
                     "terraform/network/terraform.tfstate.backup", "terraform/network/private.tfvars",
                     "terraform/security-group/private.tfvars.json", "terraform/network/create.tfplan.json",
                     "terraform/network/tfplan.json", "terraform/network/plan.binary", ".review-data/private.json"):
            with self.subTest(private=path):
                self.assertTrue(is_private_artifact(Path(path)))
        for path in ("terraform/network/main.tf", "terraform/network/.terraform.lock.hcl", "reports/live-preflight.json"):
            with self.subTest(source=path):
                self.assertFalse(is_private_artifact(Path(path)))

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
