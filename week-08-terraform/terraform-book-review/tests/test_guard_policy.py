"""Guard and post-hook contracts; all command strings are inert test data."""
import contextlib
import io
import json
import os
import types
import unittest
from unittest.mock import patch

from test_offline_validation import Fixture, PROJECT, load

guard = load("a5_guard_test_subject", "hooks/pre_tool_guard.py")
post = load("a5_post_test_subject", "hooks/post_tool_validate.py")


class GuardTests(Fixture):
    def event(self, tool, args, **extra):
        return {"hook_event_name": "PreToolUse", "cwd": str(self.root), "tool_name": tool, "tool_input": args, **extra}

    def allowed(self, tool, args, **extra):
        return guard.decide(self.event(tool, args, **extra), self.root)

    def denied(self, tool, args, **extra):
        with self.assertRaises(guard.Denied):
            self.allowed(tool, args, **extra)

    def test_useful_source_reads_searches_and_edits(self):
        self.allowed("Read", {"file_path": "terraform/main.tf", "offset": 1, "limit": 10})
        self.allowed("Glob", {"path": "terraform", "pattern": "**/*.tf"})
        self.allowed("Grep", {"path": "terraform", "pattern": "aws_vpc", "glob": "*.tf", "-n": True, "output_mode": "content"})
        self.allowed("Edit", {"file_path": "terraform/main.tf", "old_string": "x", "new_string": "y"})
        self.allowed("Write", {"file_path": "runtime/new.conf", "content": "safe data"})
        self.allowed("Write", {"file_path": "terraform/modules/new/main.tf", "content": ""})
        self.allowed("Write", {"file_path": "terraform/modules/secrets/main.tf", "content": ""})
        self.allowed("Write", {"file_path": "README.md", "content": "offline runbook"})

    def test_only_exact_validation_command(self):
        self.allowed("Bash", {"command": guard.VALIDATION_COMMAND})
        commands = [
            "terraform " + command for command in ("test", "plan", "apply", "destroy", "state list", "init", "validate", "fmt", "console")
        ] + ["aws sts get-caller-identity", "az account show", "gcloud auth list", "ssh example.invalid", "curl example.invalid",
             "python3 -I scripts/validate_offline.py", "sudo " + guard.VALIDATION_COMMAND,
             "env " + guard.VALIDATION_COMMAND, "FOO=x " + guard.VALIDATION_COMMAND,
             " " + guard.VALIDATION_COMMAND, guard.VALIDATION_COMMAND + " ", guard.VALIDATION_COMMAND + "\n",
             guard.VALIDATION_COMMAND + "; true", guard.VALIDATION_COMMAND + " && true", guard.VALIDATION_COMMAND + " | cat",
             guard.VALIDATION_COMMAND + " > report", guard.VALIDATION_COMMAND + " --terraform-bin other",
             'sh -c "' + guard.VALIDATION_COMMAND + '"', "$(echo terraform) test", "`echo terraform` test",
             "/usr/bin/python3 -I ./scripts/validate_offline.py"]
        for command in commands:
            with self.subTest(command=command):
                self.denied("Bash", {"command": command})
        self.denied("Bash", {"command": guard.VALIDATION_COMMAND, "run_in_background": True})
        self.denied("Bash", {"command": guard.VALIDATION_COMMAND, "dangerouslyDisableSandbox": True})

    def test_policy_and_test_self_modification_denied(self):
        names = list(guard.PROTECTED) + [guard.MANIFEST, ".claude/settings.json", ".claude/new.md", ".mcp.json",
                 "tests/new.py", "terraform/tests/offline.tftest.hcl", "terraform/modules/x/hidden.tftest.hcl",
                 "hooks/other.py", "source-lock.json", "terraform/.terraform.lock.hcl", "scripts/other.py"]
        for name in names:
            with self.subTest(name=name):
                self.denied("Write", {"file_path": name, "content": "replacement"})
                self.denied("Edit", {"file_path": name, "old_string": "x", "new_string": "y"})

    def test_outside_private_symlink_and_special_inputs_denied(self):
        for name in ("../README.md", str(self.root.parent / "outside"), "~/.aws/config", ".env", "runtime/key.pem",
                     "terraform/private.tfvars", "terraform/override.tf", "runtime/main.js", "terraform/main.tf\x00"):
            with self.subTest(name=name):
                self.denied("Write", {"file_path": name, "content": "data"})
                self.denied("Read", {"file_path": name})
        link = self.root / "runtime/link.conf"
        link.symlink_to(self.root / "README.md")
        self.denied("Read", {"file_path": "runtime/link.conf"})
        self.denied("Glob", {"path": "runtime", "pattern": "**/*"})
        link.unlink()
        self.put("runtime/.env", "never read")
        self.denied("Grep", {"path": "runtime", "pattern": "."})

    def test_unknown_malformed_tools_and_fields_denied(self):
        for tool in ("Task", "WebFetch", "NotebookEdit", "TodoWrite", "BashOutput", "KillShell", "MultiEdit", "ReadFile", "mcp__aws__read"):
            self.denied(tool, {})
        self.denied("Read", {"file_path": "README.md", "extra": True})
        self.denied("Read", {"file_path": "README.md", "offset": True})
        self.denied("Grep", {"path": "terraform", "pattern": "x", "extra_args": "--follow"})
        self.denied("Glob", {"pattern": "../**/*"})
        self.denied("Read", {"file_path": "README.md"}, permission_mode="bypassPermissions")
        for event in ([], {}, self.event("Read", []), {**self.event("Read", {"file_path": "README.md"}), "hook_event_name": "PostToolUse"},
                      {**self.event("Read", {"file_path": "README.md"}), "unexpected": 1}):
            with self.subTest(event=event), self.assertRaises(guard.Denied):
                guard.decide(event, self.root)
        for text in ('{"tool_name":"Read","tool_name":"Bash"}', '{"value":NaN}', "{} trailing", "[]\n{}", ""):
            with self.subTest(text=text), self.assertRaises((ValueError, guard.Denied)):
                guard.strict_json(text)

    def test_exact_public_registry_mcp_only(self):
        inputs = {
            "search_providers": {"provider_name": "aws", "provider_namespace": "hashicorp", "service_slug": "vpc", "provider_document_type": "resources", "provider_version": "6.64.0"},
            "get_provider_details": {"provider_doc_id": "123456"},
            "get_latest_provider_version": {"namespace": "hashicorp", "name": "aws"},
            "get_provider_capabilities": {"namespace": "hashicorp", "name": "aws"},
            "search_modules": {"module_query": "vpc", "current_offset": 0},
            "get_module_details": {"module_id": "terraform-aws-modules/vpc/aws/6.0.0"},
            "get_latest_module_version": {"module_publisher": "terraform-aws-modules", "module_name": "vpc", "module_provider": "aws"},
        }
        for tool in guard.MCP_TOOLS:
            self.allowed(tool, inputs[tool.removeprefix("mcp__terraform__")])
            self.denied(tool, {})
            self.denied(tool, {**inputs[tool.removeprefix("mcp__terraform__")], "unknown": "value"})
        for tool in ("mcp__terraform__create_run", "mcp__terraform__get_workspace", "mcp__terraform__get_state_version",
                     "mcp__other__search_providers", "mcp__terraform_extra__search_providers", "mcp__terraform__search_providers_extra"):
            self.denied(tool, {})
        self.denied("mcp__terraform__search_providers", {"token": "synthetic"})
        self.denied("mcp__terraform__search_providers", {"query": "https://private.example"})

    def test_intended_subagents_only_and_readonly_reviewer(self):
        for name in guard.AGENTS:
            self.allowed("Agent", {"subagent_type": name, "description": "offline", "prompt": "Read source only."})
            self.allowed("Read", {"file_path": "README.md"}, agent_type=name, agent_id="synthetic")
        self.denied("Agent", {"subagent_type": "general-purpose", "description": "x", "prompt": "x"})
        self.denied("Agent", {"subagent_type": "terraform-engineer", "description": "x", "prompt": "x", "model": "paid-choice"})
        self.denied("Agent", {"subagent_type": "terraform-engineer", "description": "x", "prompt": "x"}, agent_type="terraform-engineer")
        self.denied("Write", {"file_path": "README.md", "content": "x"}, agent_type="architecture-security-reviewer")
        self.denied("Bash", {"command": guard.VALIDATION_COMMAND}, agent_type="architecture-security-reviewer")
        self.denied("Read", {"file_path": "README.md"}, agent_type="unknown")
        self.denied("Read", {"file_path": "README.md"}, agent_id="missing-type")

    def test_trust_change_and_unsealed_execution_denied(self):
        self.put("scripts/validate_offline.py", "unreviewed code")
        self.denied("Bash", {"command": guard.VALIDATION_COMMAND})
        self.denied("Read", {"file_path": "README.md"})
        self.seal()
        self.manifest["terraform_tests"] = {}
        self.put(".claude/trusted-files.json", json.dumps(self.manifest))
        self.allowed("Read", {"file_path": "README.md"})
        self.denied("Bash", {"command": guard.VALIDATION_COMMAND})

    def test_main_error_denies_without_reflecting_input(self):
        output, error = io.StringIO(), io.StringIO()
        with patch.object(guard.sys, "stdin", io.StringIO('{"secret":"DO_NOT_ECHO"')), contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            self.assertEqual(guard.main(), 2)
        self.assertEqual(json.loads(output.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn("DO_NOT_ECHO", output.getvalue() + error.getvalue())


class PostHookTests(Fixture):
    def invoke_post(self, returncode=0, malformed=False):
        event = {"hook_event_name": "PostToolUse", "cwd": str(self.root), "tool_name": "Write",
                 "tool_input": {"file_path": "README.md", "content": "edited source"}, "tool_response": {"success": True}}
        result = types.SimpleNamespace(returncode=returncode, stdout="not surfaced", stderr="not surfaced")
        output, error = io.StringIO(), io.StringIO()
        with patch.object(post, "ROOT", self.root), patch.object(post, "load_guard", return_value=guard), \
             patch.object(post.sys, "stdin", io.StringIO("{" if malformed else json.dumps(event))), \
             patch.dict(os.environ, {"A5_TERRAFORM_BIN": "/approved/terraform", "A5_PROVIDER_MIRROR": "/approved/mirror", "AWS_PROFILE": "DO_NOT_PASS"}), \
             patch.object(post.subprocess, "run", return_value=result) as process, \
             contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = post.main()
        return status, output.getvalue(), error.getvalue(), process

    def test_fixed_runner_post_edit_and_clean_environment(self):
        status, output, _, process = self.invoke_post()
        self.assertEqual(status, 0)
        self.assertEqual(process.call_args.args[0], ["/usr/bin/python3", "-I", str(self.root / "scripts/validate_offline.py")])
        self.assertNotIn("AWS_PROFILE", process.call_args.kwargs["env"])
        self.assertEqual(json.loads(output)["hookSpecificOutput"]["hookEventName"], "PostToolUse")

    def test_failed_runner_and_malformed_event_visible(self):
        status, output, error, _ = self.invoke_post(returncode=1)
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output)["decision"], "block")
        self.assertIn("FAILED", error)
        status, _, _, process = self.invoke_post(malformed=True)
        self.assertEqual(status, 2)
        process.assert_not_called()

    def test_untrusted_hook_never_imported(self):
        self.put("hooks/pre_tool_guard.py", "raise AssertionError('must not execute')")
        with patch.object(post, "ROOT", self.root), self.assertRaisesRegex(ValueError, "Untrusted hook"):
            post.load_guard()

    def test_inactive_templates_and_inherited_models(self):
        settings = json.loads((PROJECT / ".claude/settings.json.example").read_text())
        self.assertEqual(settings["hooks"]["PreToolUse"][0]["matcher"], ".*")
        guard.trust(PROJECT)
        self.assertFalse((PROJECT / ".claude/settings.json").exists())
        self.assertFalse((PROJECT / ".mcp.json").exists())
        mcp = json.loads((PROJECT / ".mcp.json.example").read_text())["mcpServers"]["terraform"]
        self.assertEqual({"mcp__terraform__" + tool for tool in mcp["args"][2].split(",")}, guard.MCP_TOOLS)
        for name in guard.AGENTS:
            self.assertIn("model: inherit", (PROJECT / f".claude/agents/{name}.md").read_text())


if __name__ == "__main__":
    unittest.main()
