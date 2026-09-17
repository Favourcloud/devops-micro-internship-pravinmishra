"""Standard-library tests only: no AWS, app server, package install or browser is exercised."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load('runtime', ROOT / 'modules/ec2/runtime.py')
preflight = load('preflight', ROOT / 'scripts/offline-preflight.py')
cleanup = load('cleanup', ROOT / 'scripts/check-cleanup.py')
schema = load('schema', ROOT / 'scripts/check-schema.py')


def parse_mysql_option_value(raw):
    """Small independent model of MySQL 8.4 option syntax, not a MySQL client."""
    quote, escaped, content = None, False, []
    for char in raw:
        if char == '#' and quote is None:
            break
        if char in ('"', "'") and not escaped:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        content.append(char)
        escaped = bool(quote and char == '\\' and not escaped)
    value = ''.join(content).strip()
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        value = value[1:-1]
    escapes = {'b': '\b', 'n': '\n', 'r': '\r', 't': '\t', 's': ' ', '\\': '\\', '"': '"', "'": "'"}
    return re.sub(r'''\\([bnrts\\"'])''', lambda match: escapes[match[1]], value)


class RuntimeTests(unittest.TestCase):
    def test_retry_succeeds_after_transient_failure(self):
        with patch.object(runtime.time, 'sleep') as sleep:
            call = unittest.mock.Mock(side_effect=[ValueError('private'), 7])
            self.assertEqual(runtime.retry(call, attempts=2), 7)
            sleep.assert_called_once()

    def test_retry_exhaustion_redacts_exception(self):
        with patch.object(runtime.time, 'sleep'):
            call = unittest.mock.Mock(side_effect=ValueError('do-not-print-this'))
            with self.assertRaisesRegex(RuntimeError, 'Bounded operation failed') as result:
                runtime.retry(call, attempts=3)
            self.assertNotIn('do-not-print-this', str(result.exception))
            self.assertEqual(call.call_count, 3)

    def test_mysql_tls_options(self):
        options = runtime.mysql_options({'host': 'mock.invalid'}, {'username': 'mockadmin', 'password': 'mock-only'})
        self.assertIn('ssl-mode=VERIFY_IDENTITY', options)
        self.assertIn('connect-timeout=10', options)

    def test_mysql_password_hash_round_trip(self):
        for password in ['MockPasswordOnly#0123456789', '#MockPasswordOnly0123456789',
                         'MockPasswordOnly0123456789#', 'Mock!#%^*+=_-Password0123456789']:
            with self.subTest(password=password):
                options = runtime.mysql_options({'host': 'mock.invalid'}, {'username': 'mockadmin', 'password': password})
                value = next(line.split('=', 1)[1] for line in options.splitlines() if line.startswith('password='))
                self.assertEqual(value[0], '"')
                self.assertEqual(parse_mysql_option_value(value), password)

    def test_mysql_option_quote_escape_round_trip(self):
        # Serializer-only inputs; quotes/backslashes/control characters remain forbidden in real passwords.
        for value in ['mock"#quoted', "mock'#quoted", r'mock\n#literal', 'mock\\',
                      ' mock with spaces ', 'mock\t\n\r\b#control']:
            with self.subTest(value=value):
                options = runtime.mysql_options({'host': 'mock.invalid'}, {'username': 'mockadmin', 'password': value})
                encoded = next(line.split('=', 1)[1] for line in options.splitlines() if line.startswith('password='))
                self.assertEqual(parse_mysql_option_value(encoded), value)
                self.assertEqual(len(options.splitlines()), 8)

    def test_mysql_option_parser_reference_cases(self):
        self.assertEqual(parse_mysql_option_value('MockPasswordOnly#0123456789'), 'MockPasswordOnly')
        self.assertEqual(parse_mysql_option_value('"MockPasswordOnly#0123456789" # comment'), 'MockPasswordOnly#0123456789')
        self.assertEqual(parse_mysql_option_value(r'''"mock\"#quoted"'''), 'mock"#quoted')
        self.assertEqual(parse_mysql_option_value(r'''"mock\\n\s\S"'''), 'mock\\n \\S')

    def test_runtime_username_collision_rejected_before_sql(self):
        for username in ['epicbookapp', 'EpicBookApp', 'EPICBOOKAPP']:
            for operation in [runtime.prepare, runtime.verify]:
                with self.subTest(username=username, operation=operation.__name__):
                    client = unittest.mock.Mock()
                    client.get_secret_value.return_value = {'SecretString': json.dumps({
                        'username': username, 'password': 'MockPasswordOnly#0123456789'})}
                    boto = types.SimpleNamespace(client=unittest.mock.Mock(return_value=client))
                    conf = types.SimpleNamespace(Config=lambda **kwargs: kwargs)
                    with patch.dict('sys.modules', {'boto3': boto, 'botocore.config': conf}), \
                         patch.object(runtime, 'run_sql') as sql, patch.object(runtime, 'initialize_database') as initialize, \
                         patch.object(runtime, 'RUNTIME') as directory, \
                         patch.object(runtime.tempfile, 'TemporaryDirectory', side_effect=AssertionError('No files before validation')) as temporary:
                        directory.mkdir.side_effect = AssertionError('No files before validation')
                        with self.assertRaisesRegex(ValueError, 'reserved'):
                            operation({'region': 'eu-west-1', 'secret_arn': 'mock-only', 'host': 'mock.invalid'})
                        sql.assert_not_called()
                        initialize.assert_not_called()
                        directory.mkdir.assert_not_called()
                        temporary.assert_not_called()

    def test_noncolliding_username_and_hash_password_accepted(self):
        credentials = {'username': 'mockadmin', 'password': 'MockPasswordOnly#0123456789'}
        client = unittest.mock.Mock()
        client.get_secret_value.return_value = {'SecretString': json.dumps(credentials)}
        boto = types.SimpleNamespace(client=unittest.mock.Mock(return_value=client))
        conf = types.SimpleNamespace(Config=lambda **kwargs: kwargs)
        with patch.dict('sys.modules', {'boto3': boto, 'botocore.config': conf}):
            self.assertEqual(runtime.fetch_credentials({'region': 'eu-west-1', 'secret_arn': 'mock-only', 'host': 'mock.invalid'}), credentials)

    def test_verify_preserves_hash_password_in_private_options(self):
        original = tempfile.TemporaryDirectory
        credentials = {'username': 'mockadmin', 'password': 'MockPasswordOnly#0123456789'}
        with original() as directory:
            base = Path(directory)
            def sql(options, statement):
                self.assertEqual(options.stat().st_mode & 0o777, 0o600)
                value = next(line.split('=', 1)[1] for line in options.read_text().splitlines() if line.startswith('password='))
                self.assertEqual(parse_mysql_option_value(value), credentials['password'])
                return 'mock-only verification'
            with patch.object(runtime, 'fetch_credentials', return_value=credentials), \
                 patch.object(runtime, 'run_sql', side_effect=sql) as execute, patch('builtins.print'), \
                 patch.object(runtime.tempfile, 'TemporaryDirectory', side_effect=lambda **kwargs: original(dir=base)):
                runtime.verify({'host': 'mock.invalid'})
            execute.assert_called_once()
            self.assertEqual(list(base.iterdir()), [])

    def test_sql_password_not_on_command_line(self):
        response = types.SimpleNamespace(returncode=0, stdout='1\n')
        with patch.object(runtime.subprocess, 'run', return_value=response) as run:
            self.assertEqual(runtime.run_sql('/mock-private.cnf', 'SELECT 1;'), '1')
            args, options = run.call_args
            self.assertEqual(args[0][1], '--defaults-extra-file=/mock-private.cnf')
            self.assertNotIn('password', ' '.join(args[0]))
            self.assertEqual(options['timeout'], 120)
            self.assertTrue(options['capture_output'])

    def test_sql_failure_redacts_stderr(self):
        response = types.SimpleNamespace(returncode=1, stdout='', stderr='private-credential')
        with patch.object(runtime.subprocess, 'run', return_value=response):
            with self.assertRaises(RuntimeError) as result:
                runtime.run_sql('/mock.cnf', 'SELECT 1;')
            self.assertNotIn('private-credential', str(result.exception))

    def test_new_database_import_order(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            (app / 'db').mkdir()
            for filename in runtime.FILES:
                (app / 'db' / filename).write_text(filename)
            execute = unittest.mock.Mock(side_effect=['0', '', '', '', '30\t100'])
            runtime.initialize_database(execute, app)
            self.assertEqual([c.args[0] for c in execute.call_args_list][1:4], list(runtime.FILES))

    def test_existing_database_does_not_reseed(self):
        execute = unittest.mock.Mock(side_effect=['6', '30\t100'])
        runtime.initialize_database(execute)
        self.assertEqual(execute.call_count, 2)

    def test_partial_seed_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'partial'):
            runtime.initialize_database(unittest.mock.Mock(side_effect=['3', '30\t0']))

    def test_invalid_schema_inventory_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'inventory'):
            runtime.initialize_database(unittest.mock.Mock(return_value='AccessDenied'))

    def test_import_failure_stops_before_later_seeds(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            (app / 'db').mkdir()
            (app / 'db' / runtime.FILES[0]).write_text('schema')
            execute = unittest.mock.Mock(side_effect=['0', RuntimeError('mock failure')])
            with self.assertRaises(RuntimeError):
                runtime.initialize_database(execute, app)
            self.assertEqual(execute.call_count, 2)

    def test_app_config_requires_tls_and_limited_user(self):
        config = runtime.app_config('mock.invalid', 'mock-only', 'mock-ca')['production']
        self.assertEqual(config['username'], 'epicbookapp')
        self.assertEqual(config['database'], 'bookstore')
        self.assertFalse(config['logging'])
        self.assertTrue(config['dialectOptions']['ssl']['rejectUnauthorized'])
        self.assertNotIn('use_env_variable', config)

    def test_secret_fetch_and_input_validation(self):
        for credentials, valid in [({'username': 'mockadmin', 'password': 'mock-only-not-real-secret-123'}, True),
                                   ({'username': 'bad\nuser', 'password': 'mock-only-not-real-secret-123'}, False),
                                   ({'username': 'mockadmin', 'password': 'bad\npassword'}, False)]:
            with self.subTest(valid=valid, username=credentials['username']):
                client = unittest.mock.Mock()
                client.get_secret_value.return_value = {'SecretString': json.dumps(credentials)}
                boto = types.SimpleNamespace(client=unittest.mock.Mock(return_value=client))
                conf = types.SimpleNamespace(Config=lambda **kwargs: kwargs)
                with patch.dict('sys.modules', {'boto3': boto, 'botocore.config': conf}):
                    if valid:
                        self.assertEqual(runtime.fetch_credentials({'region': 'eu-west-1', 'secret_arn': 'mock-only', 'host': 'mock.invalid'}), credentials)
                    else:
                        with self.assertRaises(ValueError):
                            runtime.fetch_credentials({'region': 'eu-west-1', 'secret_arn': 'mock-only', 'host': 'mock.invalid'})

    def test_prepare_private_files_and_scoped_grant(self):
        original = tempfile.TemporaryDirectory
        with original() as directory:
            base = Path(directory)
            ca = base / 'ca.pem'
            ca.write_text('mock-ca')
            credentials = {'username': 'mockadmin', 'password': 'MockPasswordOnly#0123456789'}
            seen = []
            def sql(options, statement):
                self.assertEqual(options.stat().st_mode & 0o777, 0o600)
                value = next(line.split('=', 1)[1] for line in options.read_text().splitlines() if line.startswith('password='))
                self.assertEqual(parse_mysql_option_value(value), credentials['password'])
                seen.append(statement)
                return '1'
            with patch.object(runtime, 'RUNTIME', base / 'run'), patch.object(runtime, 'CA', ca), \
                 patch.object(runtime, 'fetch_credentials', return_value=credentials), \
                 patch.object(runtime, 'initialize_database'), patch.object(runtime, 'run_sql', side_effect=sql), \
                 patch.object(runtime.os, 'chown'), patch.object(runtime.grp, 'getgrnam', return_value=types.SimpleNamespace(gr_gid=1)), \
                 patch.object(runtime.tempfile, 'TemporaryDirectory', side_effect=lambda **kwargs: original(dir=base)):
                runtime.prepare({'host': 'mock.invalid'})
            config_file = base / 'run/config.json'
            self.assertEqual(config_file.stat().st_mode & 0o777, 0o640)
            config = json.loads(config_file.read_text())['production']
            self.assertNotEqual(config['password'], credentials['password'])
            self.assertIn('ON bookstore.*', seen[-1])
            self.assertNotIn('ON *.*', seen[-1])
            self.assertEqual(sorted(p.name for p in base.iterdir()), ['ca.pem', 'run'])

    def test_prepare_failure_removes_temporary_credentials(self):
        original = tempfile.TemporaryDirectory
        with original() as directory:
            base = Path(directory)
            with patch.object(runtime, 'RUNTIME', base / 'run'), \
                 patch.object(runtime, 'fetch_credentials', return_value={'username': 'mockadmin', 'password': 'mock-only'}), \
                 patch.object(runtime.os, 'chown'), patch.object(runtime.grp, 'getgrnam', return_value=types.SimpleNamespace(gr_gid=1)), \
                 patch.object(runtime.time, 'sleep'), patch.object(runtime, 'run_sql', side_effect=RuntimeError('mock error')), \
                 patch.object(runtime.tempfile, 'TemporaryDirectory', side_effect=lambda **kwargs: original(dir=base)):
                with self.assertRaises(RuntimeError):
                    runtime.prepare({'host': 'mock.invalid'})
            self.assertEqual([p.name for p in base.iterdir()], ['run'])
            self.assertFalse((base / 'run/config.json').exists())


class ShellTests(unittest.TestCase):
    source = (ROOT / 'modules/ec2/user_data.sh').read_text()

    def function(self, name):
        return re.search(r'^' + name + r'\(\) \{.*?^\}', self.source, re.M | re.S).group()

    def shell(self, text):
        return subprocess.run(['/bin/bash', '-c', text], capture_output=True, text=True, timeout=10)

    def test_retry_success_branch(self):
        text = self.function('retry') + '\nsleep() { :; }; n=0; operation() { n=$((n+1)); test "$n" = 2; }; retry operation; test "$n" = 2'
        self.assertEqual(self.shell(text).returncode, 0)

    def test_retry_exhaustion_branch(self):
        text = self.function('retry') + '\nsleep() { :; }; n=0; operation() { n=$((n+1)); return 1; }; retry operation; result=$?; test "$result" = 1 && test "$n" = 5'
        self.assertEqual(self.shell(text).returncode, 0)

    def test_catalogue_readiness_not_default_nginx(self):
        with tempfile.TemporaryDirectory() as directory:
            for body, status in [('Add to Cart', 0), ('Welcome to nginx!', 1), ('no books available', 1)]:
                with self.subTest(body=body):
                    text = self.function('catalogue_ready') + '\nwork=' + directory + '\nsystemctl() { return 0; }; curl() { printf "%s" "' + body + '"; }; catalogue_ready'
                    self.assertEqual(self.shell(text).returncode, status)

    def test_catalogue_rejects_failed_service(self):
        text = self.function('catalogue_ready') + '\nsystemctl() { return 1; }; curl() { echo "Add to Cart"; }; catalogue_ready'
        self.assertEqual(self.shell(text).returncode, 1)

    def test_catalogue_rejects_http_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            text = self.function('catalogue_ready') + '\nwork=' + directory + '\nsystemctl() { return 0; }; curl() { return 22; }; catalogue_ready'
            self.assertEqual(self.shell(text).returncode, 22)

    def test_bootstrap_contract(self):
        for part in ['npm ci --omit=dev --ignore-scripts', 'NODE_ENV=production PORT=8080', 'sha256sum -c', 'http://127.0.0.1:8080', 'rm -f /etc/nginx/sites-enabled/default', 'IPAddressDeny=169.254.169.254/32', 'chmod -R a+rX,go-w']:
            self.assertIn(part, self.source)
        self.assertNotIn('set -x', self.source)
        self.assertNotIn('TF_VAR_db_password', self.source)


class PrivacyTests(unittest.TestCase):
    def test_preflight_accepts_clean_project(self):
        preflight.check(ROOT)

    def test_preflight_rejects_implicit_inputs(self):
        for filename in ['terraform.tfvars', 'oops.auto.tfvars.json', 'override.tf', 'local_override.tf.json', 'terraform.tfstate.backup', 'private.pem', '.private']:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                (Path(directory) / filename).touch()
                with self.assertRaises(ValueError):
                    preflight.check(Path(directory))

    def test_preflight_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / '.private').symlink_to('/nonexistent')
            with self.assertRaises(ValueError):
                preflight.check(Path(directory))

    def test_no_javascript_or_secret_outputs(self):
        self.assertFalse(list(ROOT.rglob('*.js')))
        for path in ROOT.rglob('outputs.tf'):
            self.assertNotRegex(path.read_text(), r'(?i)password|secret_arn|secret_string|account_id')

    def test_sensitive_ephemeral_root_and_module(self):
        for file in ['variables.tf', 'modules/rds/variables.tf']:
            text = (ROOT / file).read_text()
            block = re.search(r'variable "db_password" \{.*?\n\}', text, re.S).group()
            self.assertRegex(block, r'sensitive\s*=\s*true')
            self.assertRegex(block, r'ephemeral\s*=\s*true')

    def test_root_cross_module_inputs(self):
        text = (ROOT / 'main.tf').read_text()
        for expression in ['module.network.private_subnet_ids', 'module.network.rds_security_group_id', 'module.network.public_subnet_id', 'module.network.ec2_security_group_id', 'module.rds.address']:
            self.assertIn(expression, text)
        self.assertNotRegex(text, r'(?m)^\s*(password|secret_string)\s*=')

    def test_runner_only_offline_commands(self):
        text = (ROOT / 'scripts/check-offline.sh').read_text()
        self.assertIn('env -i', text)
        self.assertIn('-lockfile=readonly', text)
        self.assertIn('filesystem_mirror', text)
        self.assertNotIn('direct {', text)
        self.assertNotRegex(text, r'terraform_offline (plan|apply|destroy)')

    def test_required_files(self):
        for directory in ['.', 'modules/network', 'modules/ec2', 'modules/rds']:
            for filename in ['main.tf', 'variables.tf', 'outputs.tf']:
                self.assertTrue((ROOT / directory / filename).is_file())
        self.assertTrue((ROOT / 'modules/ec2/user_data.sh').is_file())

    def test_schema_contract_rejects_non_write_only(self):
        resources = {}
        for name, field, version in [('aws_db_instance', 'password_wo', 'password_wo_version'), ('aws_secretsmanager_secret_version', 'secret_string_wo', 'secret_string_wo_version')]:
            resources[name] = {'block': {'attributes': {field: {'write_only': True, 'sensitive': True}, version: {'type': 'number'}}}}
        document = {'provider_schemas': {'registry.terraform.io/hashicorp/aws': {'resource_schemas': resources}}}
        schema.check(document)
        resources['aws_db_instance']['block']['attributes']['password_wo']['write_only'] = False
        with self.assertRaises(AssertionError):
            schema.check(document)


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {'account': 'mock-only', 'region': 'mock-region', 'resources': [
            {'address': 'mock.resource' + str(i), 'id': 'mock-id-' + str(i)} for i in range(28)]}
        self.observed = copy.deepcopy(self.inventory)
        self.observed.update(remaining_state_addresses=[], attached_ebs_absent=True, db_snapshots_absent=True)
        for row in self.observed['resources']:
            row.update(status='absent', checked_at='mock-time', check='mock exact-ID read')

    def test_consistent_mock_ledger(self):
        cleanup.check(self.inventory, self.observed)

    def test_wrong_identity_rejected(self):
        self.observed['account'] = 'different'
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)

    def test_access_denied_is_not_absence(self):
        self.observed['resources'][0]['status'] = 'AccessDenied'
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)

    def test_missing_id_rejected(self):
        self.observed['resources'].pop()
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)

    def test_duplicate_id_rejected(self):
        self.observed['resources'][0] = self.observed['resources'][1]
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)

    def test_retained_ebs_rejected(self):
        self.observed['attached_ebs_absent'] = False
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)

    def test_nonempty_state_rejected(self):
        self.observed['remaining_state_addresses'] = ['mock.resource0']
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)

    def test_wrong_terminal_state_rejected(self):
        self.observed['resources'][0]['status'] = 'terminated'
        with self.assertRaises(ValueError):
            cleanup.check(self.inventory, self.observed)


if __name__ == '__main__':
    unittest.main()
