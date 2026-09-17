from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_offline as runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / 'tests').mkdir()
        for name in (*runner.TF_FILES, *runner.TEST_FILES, '.terraform.lock.hcl', 'cloud-init.sh'):
            shutil.copyfile(runner.ROOT / name, self.root / name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_clean_source_passes(self):
        runner.guard_project(self.root)

    def test_rejects_every_autoload_and_override(self):
        for name in ('terraform.tfvars', 'terraform.tfvars.json', 'prod.auto.tfvars', 'x.auto.tfvars.json',
                     'override.tf', 'override.tf.json', 'x_override.tf', 'extra.tf', 'extra.tf.json',
                     'terraform.tfstate', 'terraform.tfstate.backup', 'run.tfplan'):
            with self.subTest(name=name):
                path = self.root / name
                path.touch()
                with self.assertRaises(ValueError):
                    runner.guard_project(self.root)
                path.unlink()

    def test_refuses_symlinked_private_directory(self):
        (self.root / '.private').symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaises(ValueError):
            runner.guard_project(self.root)

    def test_refuses_symlinked_source(self):
        (self.root / 'main.tf').unlink()
        (self.root / 'main.tf').symlink_to(runner.ROOT / 'main.tf')
        with self.assertRaises(ValueError):
            runner.guard_project(self.root)

    def test_refuses_unknown_test(self):
        (self.root / 'tests/live.tftest.hcl').write_text('provider "azurerm" {}')
        with self.assertRaises(ValueError):
            runner.guard_project(self.root)

    def test_refuses_live_provider_and_module(self):
        target = self.root / runner.TEST_FILES[0]
        original = target.read_text()
        for addition in ('provider "azurerm" {}', 'module { source = "elsewhere" }', 'providers = { azurerm = azurerm.live }', 'alias = "live"'):
            target.write_text(original + '\n' + addition)
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                runner.guard_project(self.root)
        target.write_text(original)

    def test_environment_drops_ambient_credentials_and_cli_overrides(self):
        with patch.dict(os.environ, {'ARM_CLIENT_SECRET': 'fake', 'AWS_ACCESS_KEY_ID': 'fake', 'TF_CLI_ARGS': '-var-file=live', 'TF_VAR_location': 'live', 'NODE_OPTIONS': 'bad'}):
            env = runner.isolated_environment(self.root, '/tmp/dmi-a3-test')
        for name in ('ARM_CLIENT_SECRET', 'AWS_ACCESS_KEY_ID', 'TF_CLI_ARGS', 'TF_VAR_location', 'NODE_OPTIONS'):
            self.assertNotIn(name, env)
        self.assertEqual(env['HOME'], str(self.root))
        self.assertEqual(env['TF_DATA_DIR'], str(self.root / 'terraform-data'))
        self.assertLess(len(env['TMPDIR']) + 30, 103)

    def test_failure_stops_later_steps_and_preserves_exit_status(self):
        for fail_index in range(7):
            calls = []
            def fake(command, **kwargs):
                index = len(calls)
                calls.append(command)
                text = 'Ran 99 tests in 0.1s\n' if index == 0 else ''
                if index == 2:
                    text = json.dumps({'terraform_version': '1.13.5'})
                return subprocess.CompletedProcess(command, 43 if index == fail_index else 0, text, '')
            with self.subTest(step=fail_index), patch.object(runner.subprocess, 'run', side_effect=fake), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    runner.run_steps(self.root, '/trusted/terraform', self.root, runner.isolated_environment(self.root, '/tmp/dmi-a3-test'))
            self.assertEqual(caught.exception.code, 43)
            self.assertEqual(len(calls), fail_index + 1)

    def test_missing_mock_summary_fails_closed(self):
        calls = []
        def fake(command, **kwargs):
            calls.append(command)
            text = 'Ran 1 test in 0.1s' if len(calls) == 1 else ''
            if len(calls) == 3:
                text = json.dumps({'terraform_version': '1.13.5'})
            return subprocess.CompletedProcess(command, 0, text, '')
        with patch.object(runner.subprocess, 'run', side_effect=fake), redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            runner.run_steps(self.root, '/trusted/terraform', self.root, runner.isolated_environment(self.root, '/tmp/dmi-a3-test'))

    def test_guard_failure_prevents_any_subprocess(self):
        (self.root / 'terraform.tfvars').touch()
        with patch.object(runner, 'ROOT', self.root), patch.object(runner.subprocess, 'run') as process, patch('sys.argv', ['runner', '--terraform', '/trusted/terraform', '--plugin-dir', str(self.root)]), redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 1)
        process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
