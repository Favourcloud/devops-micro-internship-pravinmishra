"""Developer-run fakes only: no Terraform process, provider, network or runtime."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]


def load(name, relative):
    path = PROJECT / relative
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


runner = load("a5_offline_test_subject", "scripts/validate_offline.py")
CONFIG = '''terraform {
  required_version = "= 1.13.5"
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "= 6.64.0"
    }
  }
}
provider "aws" {
  region = "eu-west-1"
}
resource "aws_vpc" "main" {
  cidr_block = "10.50.0.0/16"
}
'''
MOCK_TEST = '''mock_provider "aws" {}
run "offline" {
  command = plan
  assert {
    condition = true
    error_message = "synthetic contract"
  }
}
'''
LOCK = '''provider "registry.terraform.io/hashicorp/aws" {
  version = "6.64.0"
  constraints = "6.64.0"
  hashes = ["h1:synthetic-not-a-real-provider-checksum"]
}
'''


class Fixture(unittest.TestCase):
    def setUp(self):
        self.scratch = PROJECT / "hooks" / ".unit-work"
        self.scratch.mkdir(mode=0o700, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="case-", dir=self.scratch))
        self.addCleanup(self.cleanup_fixture)
        for name in runner.TRUSTED:
            self.put(name, "fixture-policy\n")
        self.put("terraform/main.tf", CONFIG)
        self.put("terraform/.terraform.lock.hcl", LOCK)
        self.put("terraform/tests/offline.tftest.hcl", MOCK_TEST)
        self.put("runtime/app.conf", "example static configuration\n")
        self.put("runtime/deploy-manifest.json", json.dumps({"common": ["app.conf"], "tiers": {"web": [], "app": [], "initializer": []}}))
        self.put("scripts/verify_upstream.py", "raise AssertionError('extractor data must never execute')\n")
        self.put("source-lock.json", '{"source":"synthetic"}\n')
        self.put("README.md", "Fixture only\n")
        self.seal()

    def cleanup_fixture(self):
        shutil.rmtree(self.root)
        try:
            self.scratch.rmdir()
        except OSError:
            pass

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def seal(self):
        self.manifest = {"version": 1, "files": {}, "terraform_tests": {}}
        for name in runner.TRUSTED | {runner.DEPLOY_MANIFEST}:
            self.manifest["files"][name] = runner.digest(self.root / name)
        for path in sorted((self.root / "terraform/tests").glob("*.tftest.hcl")):
            self.manifest["terraform_tests"][path.relative_to(self.root).as_posix()] = runner.digest(path)
        self.put(".claude/trusted-files.json", json.dumps(self.manifest))

    def inventory(self):
        return runner.source_inventory(self.root, runner.trusted_manifest(self.root))


class OfflineSourceTests(Fixture):
    def test_only_source_allowlist_staged(self):
        self.put("scripts/evil.py", 'raise RuntimeError("must never execute")')
        names = self.inventory()
        self.assertIn("runtime/app.conf", names)
        self.assertIn("source-lock.json", names)
        self.assertIn("scripts/verify_upstream.py", names)
        self.assertNotIn("scripts/evil.py", names)
        self.assertNotIn("scripts/validate_offline.py", names)

    def test_live_or_unsupported_inputs_fail_closed(self):
        for name in ("terraform/local.tfvars", "terraform/modules/x/nested.tfvars.json", "runtime/secret.tfstate",
                     "saved.tfplan", "terraform/override.tf", "terraform/modules/x/foo_override.tf",
                     "terraform/main.tf.json", ".aws/config", "runtime/key.pem", "terraform/.terraform/providers/entry"):
            with self.subTest(name=name):
                path = self.put(name, "not read")
                with self.assertRaises(runner.Refused):
                    self.inventory()
                path.unlink()
                parent = path.parent
                while parent != self.root and parent not in {self.root / "terraform", self.root / "runtime"}:
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent

    def test_links_rejected_without_following(self):
        path = self.root / "runtime/link.conf"
        path.symlink_to(self.root / "README.md")
        with self.assertRaises(runner.Refused):
            self.inventory()
        path.unlink()
        os.link(self.root / "README.md", path)
        with self.assertRaises(runner.Refused):
            self.inventory()

    def test_backend_exec_extra_provider_and_remote_modules_denied(self):
        snippets = (
            'terraform { backend "s3" {} }',
            'resource "aws_vpc" "x" { provisioner "local-exec" { command = "no" } }',
            'data "external" "x" { program = ["no"] }',
            'provider "aws" { alias = "live" }',
            'provider "aws" { profile = "live" }',
            'provider "external" {}',
            'module "x" { source = "hashicorp/vpc/aws" }',
            'module "x" { source = "../outside" }',
            'ephemeral "aws_secretsmanager_secret_version" "x" {}',
            'terraform { cloud {} }',
            'resource "aws_vpc" "x" { provider = aws.live }',
            'locals { x = provider::aws::arn_parse("x") }',
        )
        for snippet in snippets:
            with self.subTest(snippet=snippet):
                self.put("terraform/main.tf", CONFIG + snippet)
                with self.assertRaises(runner.Refused):
                    self.inventory()

    def test_unpinned_providers_and_hcl_ambiguity_denied(self):
        for content in (CONFIG.replace("= 6.64.0", "~> 6.64"), CONFIG.replace("hashicorp/aws", "evil/aws"),
                        CONFIG + 'locals { x = "unterminated }', CONFIG + 'resource "aws_vpc" "x" {',
                        CONFIG + 'locals { x = 1\nx = 2\n}', CONFIG.replace("= 1.13.5", ">= 1.0")):
            with self.subTest(content=content[-80:]):
                self.put("terraform/main.tf", content)
                with self.assertRaises((runner.Refused, ValueError)):
                    self.inventory()

    def test_local_module_allowed(self):
        self.put("terraform/modules/network/main.tf", 'resource "aws_vpc" "x" {}\n')
        self.put("terraform/main.tf", CONFIG + 'module "network" { source = "./modules/network" }\n')
        self.assertIn("terraform/modules/network/main.tf", self.inventory())

    def test_secrets_module_and_dot_template_data_are_allowed(self):
        self.put("terraform/modules/secrets/main.tf", 'resource "aws_secretsmanager_secret" "example" {}\n')
        self.put("runtime/nginx.conf.template", "synthetic Nginx template data\n")
        self.put("runtime/mysqlrouter.conf.template", "synthetic Router template data\n")
        self.put("terraform/main.tf", CONFIG + '''module "secrets" {
  source = "./modules/secrets"
}
locals {
  nginx = file("../runtime/nginx.conf.template")
  router = file("../runtime/mysqlrouter.conf.template")
}
''')
        names = self.inventory()
        self.assertIn("terraform/modules/secrets/main.tf", names)
        self.assertIn("runtime/nginx.conf.template", names)
        self.assertIn("runtime/mysqlrouter.conf.template", names)
        self.put("runtime/secrets/values.json", "{}")
        with self.assertRaises(runner.Refused):
            self.inventory()

    def test_runtime_file_template_and_fileset_allowed(self):
        self.put("runtime/config.tftpl", 'name = ${name}\n')
        self.put("terraform/main.tf", CONFIG + '''locals {
  one = file("${path.module}/../runtime/app.conf")
  two = templatefile("${path.root}/../runtime/config.tftpl", {name = "offline"})
  names = fileset("../runtime", "**/*.conf")
  provenance = file("../source-lock.json")
  extractor = file("${path.module}/../scripts/verify_upstream.py")
}
''')
        self.inventory()

    def test_ternaries_with_provider_named_field_and_bounded_files(self):
        self.put("terraform/main.tf", CONFIG + '''locals {
  labels = { provider = "offline" }
  selected = true ? local.labels.provider : "unset"
  runtime_data = true ? file("${path.module}/../runtime/app.conf") : "unset"
  provenance = true ? file("../source-lock.json") : file("../scripts/verify_upstream.py")
  nested = "${true ? local.labels.provider : file("../runtime/app.conf")}"
}
''')
        self.inventory()
        for path in ("/etc/passwd", "../README.md", "../scripts/evil.py", "../runtime/${var.filename}"):
            with self.subTest(path=path):
                self.put("terraform/main.tf", CONFIG + 'locals { value = true ? "safe" : file("' + path + '") }\n')
                with self.assertRaises(runner.Refused):
                    self.inventory()

    def test_parent_plan_mock_contract_and_bare_override_timing(self):
        source = (PROJECT / "terraform/tests/architecture.tftest.hcl").read_text()
        runs = [block for block in runner.parse(runner.lex(source))[1] if block.kind == "run"]
        self.assertGreaterEqual(len(runs), 35)
        self.assertTrue(all(runner.compact(block.attrs["command"]) == [runner.Token("id", "plan")] for block in runs))
        self.put("terraform/tests/offline.tftest.hcl", source)
        self.seal()
        self.inventory()

    def test_override_timing_cannot_apply_or_be_dynamic(self):
        for timing in ("apply", '"apply"', "var.timing", "true ? plan : apply"):
            for header in (f'mock_provider "aws" {{ override_during = {timing} }}',
                           'mock_provider "aws" {}\noverride_resource {\n target = aws_vpc.main\n override_during = ' + timing + '\n values = { id = "mock" }\n}'):
                with self.subTest(timing=timing, header=header):
                    self.put("terraform/tests/offline.tftest.hcl", MOCK_TEST.replace('mock_provider "aws" {}', header))
                    self.seal()
                    with self.assertRaises(runner.Refused):
                        self.inventory()

    def test_closed_runtime_fileset_and_parent_main_contract(self):
        self.put("terraform/main.tf", CONFIG + "locals {\n runtime_files = " + runner.RUNTIME_FILESET_EXPRESSION + "\n}\n")
        self.inventory()
        parent_main = (PROJECT / "terraform/main.tf").read_text()
        for block in runner.parse(runner.lex(parent_main))[1]:
            if block.kind == "module":
                source = runner.literal(block.attrs["source"])
                (self.root / "terraform" / source).mkdir(parents=True, exist_ok=True)
        self.put("terraform/main.tf", CONFIG + parent_main)
        names = self.inventory()
        self.assertIn("scripts/verify_upstream.py", names)
        for path in (PROJECT / "terraform").rglob("*.tf"):
            self.put(path.relative_to(PROJECT).as_posix(), path.read_text())
        self.inventory()

    def test_literal_manifest_declaration_preserves_bounded_dynamic_paths(self):
        prefix = CONFIG + "locals {\n deploy_manifest = "
        suffix = "\n runtime_files = " + runner.RUNTIME_MANIFEST_WITH_SOURCE_LOCK + "\n}\n"
        self.put("terraform/main.tf", prefix + runner.DEPLOY_MANIFEST_RELATIVE_EXPRESSION + suffix)
        self.inventory()
        for declaration in ('jsondecode(file("../source-lock.json"))', 'var.manifest', 'jsondecode(file("../runtime/${var.manifest}"))'):
            with self.subTest(declaration=declaration):
                self.put("terraform/main.tf", prefix + declaration + suffix)
                with self.assertRaises(runner.Refused):
                    self.inventory()

    def test_manifest_source_lock_ternary_is_closed_and_staged(self):
        self.put(runner.DEPLOY_MANIFEST, json.dumps({"common": ["app.conf", "source-lock.json"], "tiers": {"web": [], "app": [], "initializer": []}}))
        self.seal()
        prefix = CONFIG + "locals {\n deploy_manifest = " + runner.DEPLOY_MANIFEST_EXPRESSION + "\n runtime_files = "
        expression = runner.RUNTIME_MANIFEST_WITH_SOURCE_LOCK
        self.put("terraform/main.tf", prefix + expression + "\n}\n")
        self.assertIn("source-lock.json", self.inventory())
        self.assertFalse((self.root / "runtime/source-lock.json").exists())
        for variant in (
            expression.replace('filename == "source-lock.json"', 'var.use_source_lock'),
            expression.replace('file("${path.module}/../source-lock.json")', 'file("${path.module}/../README.md")'),
            expression.replace('local.deploy_manifest.common', 'var.runtime_files'),
            expression.replace('file("${path.module}/../runtime/${filename}")', 'file("${path.module}/../runtime/${var.filename}")'),
            runner.RUNTIME_MANIFEST_EXPRESSION,
        ):
            with self.subTest(expression=variant[:80]):
                self.put("terraform/main.tf", prefix + variant + "\n}\n")
                with self.assertRaises(runner.Refused):
                    self.inventory()

    def test_deployment_manifest_paths_and_trust_are_checked(self):
        self.manifest["files"].pop(runner.DEPLOY_MANIFEST)
        self.put(".claude/trusted-files.json", json.dumps(self.manifest))
        with self.assertRaisesRegex(runner.Refused, "seal runtime/deploy-manifest"):
            self.inventory()
        for name in ("../README.md", "/etc/passwd", "../scripts/verify_upstream.py", "missing.py", "app.conf/../../README.md"):
            with self.subTest(name=name):
                self.put(runner.DEPLOY_MANIFEST, json.dumps({"common": [name], "tiers": {"web": [], "app": [], "initializer": []}}))
                self.seal()
                with self.assertRaises(runner.Refused):
                    self.inventory()

    def test_runtime_filename_scope_and_collection_mutations_denied(self):
        original = runner.RUNTIME_FILESET_EXPRESSION
        variants = (
            original.replace('sort(fileset("${path.module}/../runtime", "**"))', '["../source-lock.json"]'),
            original.replace('file("${path.module}/../runtime/${filename}")', 'file("${path.module}/../runtime/${var.filename}")'),
            original.replace('file("${path.module}/../runtime/${filename}")', 'file("${path.module}/../runtime/../${filename}")'),
            original.replace('sort(fileset("${path.module}/../runtime", "**"))', 'var.runtime_files'),
        )
        for value in variants:
            with self.subTest(value=value[-80:]):
                self.put("terraform/main.tf", CONFIG + "locals {\n runtime_files = " + value + "\n}\n")
                with self.assertRaises(runner.Refused):
                    self.inventory()
        self.put("terraform/main.tf", CONFIG + "locals {\n runtime_files = " + original + '\n outside = file("${path.module}/../runtime/${filename}")\n}\n')
        with self.assertRaises(runner.Refused):
            self.inventory()

    def test_root_tfvars_examples_are_never_staged(self):
        for name in (".tfvars.example", "terraform/.tfvars.example", "terraform/terraform.tfvars.example", "terraform/offline.tfvars.example"):
            self.put(name, "not valid HCL and must never be loaded")
        names = self.inventory()
        self.assertFalse(any(".tfvars" in name for name in names))

    def test_provider_default_tags_is_data_only(self):
        content = CONFIG.replace('  region = "eu-west-1"', '  region = "eu-west-1"\n  default_tags {\n    tags = { Project = "offline" }\n  }')
        self.put("terraform/main.tf", content)
        self.inventory()
        self.put("terraform/main.tf", content.replace("default_tags", "assume_role"))
        with self.assertRaises(runner.Refused):
            self.inventory()

    def test_private_dynamic_or_hidden_filesystem_reads_denied(self):
        expressions = ('file("/etc/passwd")', 'file("../README.md")',
                       'file("../runtime/${var.name}")', 'filebase64("../runtime/app.conf")',
                       '"${file(\"/etc/passwd\")}"', 'pathexpand("~/.aws/config")',
                       'fileset("../runtime", "../*")')
        for expression in expressions:
            with self.subTest(expression=expression):
                self.put("terraform/main.tf", CONFIG + 'locals { x = ' + expression + ' }\n')
                with self.assertRaises(runner.Refused):
                    self.inventory()
        self.put("runtime/unsafe.tftpl", '${file /* comment */ ("/etc/passwd")}\n')
        self.put("terraform/main.tf", CONFIG + 'locals { x = templatefile("../runtime/unsafe.tftpl", {}) }\n')
        with self.assertRaises(runner.Refused):
            self.inventory()

    def test_test_apply_default_alias_and_module_override_denied(self):
        for content in (MOCK_TEST.replace("  command = plan\n", ""), MOCK_TEST.replace("command = plan", "command = apply"),
                        MOCK_TEST.replace('mock_provider "aws" {}', 'mock_provider "aws" { alias = "live" }'),
                        MOCK_TEST.replace('mock_provider "aws" {}', 'provider "aws" {}'),
                        MOCK_TEST + 'override_module { target = module.x }',
                        MOCK_TEST.replace('command = plan', 'command = plan\nproviders = { aws = aws.live }'),
                        MOCK_TEST.replace('command = plan', 'command = plan\nmodule { source = "./evil" }')):
            with self.subTest(content=content):
                self.put("terraform/tests/offline.tftest.hcl", content)
                self.seal()
                with self.assertRaises(runner.Refused):
                    self.inventory()

    def test_trusted_manifest_and_fixed_tests_required(self):
        self.put("terraform/tests/unreviewed.tftest.hcl", MOCK_TEST)
        with self.assertRaises(runner.Refused):
            self.inventory()
        (self.root / "terraform/tests/unreviewed.tftest.hcl").unlink()
        self.put("terraform/tests/offline.tftest.hcl", MOCK_TEST + "\n# changed\n")
        with self.assertRaises(runner.Refused):
            self.inventory()
        self.seal()
        self.manifest["terraform_tests"] = {}
        self.put(".claude/trusted-files.json", json.dumps(self.manifest))
        with self.assertRaises(runner.Refused):
            self.inventory()

    def test_schema_and_synthetic_marker_helpers(self):
        schema = fake_schema()
        runner.verify_schema(schema)
        attrs = schema["provider_schemas"][runner.AWS_PROVIDER]["resource_schemas"]["aws_db_instance"]["block"]["attributes"]
        attrs["password_wo"]["write_only"] = False
        with self.assertRaises(runner.Refused):
            runner.verify_schema(schema)
        attrs["password_wo"] = {"write_only": True, "sensitive": False}
        with self.assertRaises(runner.Refused):
            runner.verify_schema(schema)
        marker = "A5_SYNTHETIC_NOT_A_SECRET_0123456789"
        runner.assert_no_markers({"ordinary": "safe"}, [marker])
        with self.assertRaises(runner.Refused):
            runner.assert_no_markers({"ordinary": marker}, [marker])


def fake_schema():
    return {"provider_schemas": {runner.AWS_PROVIDER: {"resource_schemas": {
        resource: {"block": {"attributes": {attribute: {"write_only": True, "sensitive": True}}}}
        for resource, attribute in (("aws_db_instance", "password_wo"), ("aws_secretsmanager_secret_version", "secret_string_wo"))
    }}}}


class OfflineExecutionTests(Fixture):
    def setUp(self):
        super().setUp()
        self.binary = self.put("tools/terraform", "NONEXECUTABLE FAKE DATA\n")
        self.binary.chmod(0o700)
        self.mirror = self.root / "mirror"
        (self.mirror / runner.AWS_PROVIDER / runner.AWS_VERSION / "darwin_arm64").mkdir(parents=True)
        self.calls = []

    def fake_process(self, args, **kwargs):
        self.calls.append((args, kwargs))
        self.assertEqual(args[0], str(self.binary))
        self.assertFalse(kwargs.get("shell", False))
        self.assertNotIn(args[1], {"plan", "apply", "destroy", "state"})
        cwd = kwargs["cwd"]
        self.assertEqual(stat.S_IMODE(cwd.parents[1].stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((cwd / "main.tf").stat().st_mode), 0o600)
        self.assertEqual([path.name for path in (cwd.parent / "scripts").iterdir()], ["verify_upstream.py"])
        self.assertIn("must never execute", (cwd.parent / "scripts/verify_upstream.py").read_text())
        self.assertTrue((cwd.parent / "source-lock.json").is_file())
        self.assertTrue((cwd.parent / "runtime/app.conf").is_file())
        env = kwargs["env"]
        for forbidden in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE", "TF_CLI_ARGS", "TF_VAR_password", "TFE_TOKEN", "HTTPS_PROXY", "PYTHONPATH"):
            self.assertNotIn(forbidden, env)
        socket_directory = (cwd / env["TMPDIR"]).resolve()
        self.assertTrue(socket_directory.is_relative_to(cwd.parents[1]))
        self.assertTrue(socket_directory.is_dir())
        self.assertEqual(stat.S_IMODE(socket_directory.stat().st_mode), 0o700)
        self.assertLess(len(env["TMPDIR"] + "/plugin123456789"), 100)
        self.assertEqual(list(Path(env["HOME"]).iterdir()), [])
        rc = Path(env["TF_CLI_CONFIG_FILE"]).read_text()
        self.assertIn("filesystem_mirror", rc)
        self.assertNotIn("direct", rc)
        value = json.dumps({"terraform_version": "1.13.5", "platform": "darwin_arm64"}) if args[1] == "version" else ""
        if args[1:3] == ["providers", "schema"]:
            value = json.dumps(fake_schema())
        return types.SimpleNamespace(returncode=0, stdout=value, stderr="")

    def invoke(self, process=None):
        hostile = {"AWS_ACCESS_KEY_ID": "FAKE_AMBIENT", "AWS_PROFILE": "FAKE", "TF_CLI_ARGS": "-not-a-real-flag",
                   "TF_VAR_password": "FAKE_AMBIENT", "HTTPS_PROXY": "https://invalid.example", "TFE_TOKEN": "FAKE_AMBIENT"}
        with patch.dict(os.environ, hostile), patch.object(runner, "TERRAFORM_SHA256", runner.digest(self.binary)), \
             patch.object(runner.subprocess, "run", side_effect=process or self.fake_process), \
             patch.object(socket, "socket", side_effect=AssertionError("network prohibited in fake tests")), \
             contextlib.redirect_stdout(io.StringIO()):
            runner.validate(self.root, str(self.binary), str(self.mirror))

    def test_exact_fixed_argv_and_no_network_fakes(self):
        self.invoke()
        self.assertEqual([args[1:] for args, _ in self.calls], [
            ["version", "-json"], ["fmt", "-check", "-recursive", "-no-color"],
            ["init", "-backend=false", "-lockfile=readonly", "-input=false", "-no-color"],
            ["validate", "-no-color"], ["providers", "schema", "-json"],
            ["test", "-no-color", "-test-directory=tests", "-filter=tests/offline.tftest.hcl"],
        ])
        self.assertFalse((self.root / "hooks/.offline-work").exists())

    def test_failure_visible_and_own_scratch_cleaned(self):
        def failing(args, **kwargs):
            if args[1] == "validate":
                return types.SimpleNamespace(returncode=1, stdout="secret-like output withheld", stderr="withheld")
            return self.fake_process(args, **kwargs)
        with self.assertRaisesRegex(runner.Refused, "stage failed: validate"):
            self.invoke(failing)
        self.assertFalse((self.root / "hooks/.offline-work").exists())
        self.assertTrue(self.binary.is_file())

    def test_missing_mirror_package_never_downloads(self):
        shutil.rmtree(self.mirror)
        self.mirror.mkdir()
        with self.assertRaisesRegex(runner.Refused, "no downloads"):
            self.invoke()
        self.assertEqual([args[1] for args, _ in self.calls], ["version"])

    def test_binary_digest_mismatch_launches_nothing(self):
        with patch.object(runner.subprocess, "run") as process:
            with self.assertRaisesRegex(runner.Refused, "binary missing/mismatched"):
                runner.validate(self.root, str(self.binary), str(self.mirror))
            process.assert_not_called()

    def test_no_arbitrary_cli_passthrough(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            runner.main(["--command", "terraform apply"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
