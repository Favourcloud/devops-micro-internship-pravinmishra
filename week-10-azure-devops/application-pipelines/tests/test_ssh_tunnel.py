"""Synthetic offline contracts only: no SSH, systemd, accounts, keys or hosts created."""

import base64
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import stat
import struct
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, mock_open, patch

from test_pipelines import parse_yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ssh_tunnel', ROOT / 'ci/ssh_tunnel.py')
tunnel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tunnel)
NOW = datetime.now(timezone.utc).replace(microsecond=0)
JOB = '11111111-2222-4333-8444-555555555555'
ENDPOINT = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'
BLOB = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32) + bytes(range(32))
KEY = 'ssh-ed25519 ' + base64.b64encode(BLOB).decode('ascii')


def timestamp(value):
    return value.strftime('%Y-%m-%dT%H:%M:%SZ')


def fixture(**changes):
    return dict(assignment='week10-a2', target_ipv4='1.1.1.1', host_public_key=KEY,
                ssh_endpoint_id=ENDPOINT, authorized_at=timestamp(NOW - timedelta(minutes=1)),
                expires_at=timestamp(NOW + timedelta(minutes=90)), **changes)


def context():
    return dict(tunnel.names('week10-a2', JOB, 1001), uid=1001,
                env={'PATH': '/usr/bin:/bin', 'HOME': '/home/azdoagent', 'LANG': 'C', 'LC_ALL': 'C',
                     'XDG_RUNTIME_DIR': '/run/user/1001', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/1001/bus'})


def result(code=0, stdout='', stderr=''):
    return subprocess.CompletedProcess([], code, stdout, stderr)


def metadata(**changes):
    value = dict(LoadState='loaded', ActiveState='active', SubState='running', MainPID='1234', Transient='yes',
                 Environment='SSH_ASKPASS_REQUIRE=never DMI_W10_PROFILE_SHA256=' + tunnel.profile_digest(fixture()))
    value.update(changes)
    return value


class ProfileTests(unittest.TestCase):
    def reject(self, **changes):
        data = fixture()
        data.update(changes)
        with self.assertRaises(tunnel.InvalidTransport):
            tunnel.validate_profile(data, now=NOW)

    def test_valid_shape_is_not_host_trust_or_authorization(self):
        self.assertEqual(tunnel.validate_profile(fixture(), now=NOW), fixture())
        for assignment in tunnel.PORTS:
            data = fixture()
            data['assignment'] = assignment
            tunnel.validate_profile(data, now=NOW)

    def test_exact_schema_rejects_secrets_duplicates_and_missing_fields(self):
        for extra in ('pat', 'private_key', 'password', 'approved', 'command'):
            self.reject(**{extra: 'synthetic-do-not-echo'})
        for key in fixture():
            data = fixture()
            del data[key]
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.validate_profile(data, now=NOW)
        with self.assertRaises(tunnel.InvalidTransport):
            tunnel.unique_object([('a', 1), ('a', 2)])

    def test_invalid_assignments_and_nonobjects_fail(self):
        for value in (None, [], {}, 'a2', 'week10-a2\n', '../a2'):
            self.reject(assignment=value)
        for value in (None, [], 1, 'profile'):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.validate_profile(value, now=NOW)

    def test_nonpublic_noncanonical_addresses_fail(self):
        for value in (None, [], '127.0.0.1', '10.0.0.1', '192.0.2.1', '169.254.169.254', '100.64.0.1',
                      '224.0.0.1', '240.0.0.1', '::1', '1.1.1.1/32', '01.1.1.1', '1.1.1.1\n'):
            self.reject(target_ipv4=value)

    def test_public_key_shape_options_and_encoding(self):
        for key in (None, [], 'private-fixture', KEY + '\n', KEY + ' comment', 'restrict ' + KEY,
                    'ssh-ed25519 ' + '!' * 68,
                    'ssh-ed25519 ' + base64.b64encode(BLOB[:-32] + bytes(32)).decode(),
                    'ssh-ed25519 ' + base64.b64encode(b'x' + BLOB[1:]).decode()):
            self.reject(host_public_key=key)

    def test_endpoint_and_job_require_canonical_nonzero_uuids(self):
        for value in (None, [], '', ENDPOINT.upper(), '{' + ENDPOINT + '}', '0' * 32,
                      '00000000-0000-0000-0000-000000000000', JOB + '; command'):
            self.reject(ssh_endpoint_id=value)
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.names('week10-a2', value, 1001)

    def test_bounded_started_window_and_strict_utc(self):
        self.reject(authorized_at=timestamp(NOW + timedelta(seconds=1)))
        self.reject(expires_at=timestamp(NOW))
        self.reject(expires_at=timestamp(NOW + timedelta(hours=24)))
        full_day = fixture()
        full_day['authorized_at'] = timestamp(NOW)
        full_day['expires_at'] = timestamp(NOW + timedelta(hours=24))
        tunnel.validate_profile(full_day, now=NOW)
        for value in (None, [], '2026-02-30T10:00:00Z', timestamp(NOW) + '\n', NOW.isoformat()):
            self.reject(expires_at=value)

    def test_start_requires_twenty_one_minutes_not_just_twenty(self):
        data = fixture()
        for seconds in (1200, 1259):
            data['expires_at'] = timestamp(NOW + timedelta(seconds=seconds))
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.validate_profile(data, now=NOW, minimum_remaining=tunnel.START_HEADROOM)
        data['expires_at'] = timestamp(NOW + timedelta(seconds=1260))
        tunnel.validate_profile(data, now=NOW, minimum_remaining=tunnel.START_HEADROOM)

    def test_agent_wrapper_and_distinct_public_address(self):
        data = {'agent_ipv4': '8.8.8.8', 'profile': fixture()}
        self.assertEqual(tunnel.validate_agent_inputs({'week10_agent_transport': data}, NOW), data)
        for bad in ({'agent_ipv4': '1.1.1.1', 'profile': fixture()}, dict(data, pat='fixture'),
                    {'week10_agent_transport': data, 'ansible_connection': 'local'}):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.validate_agent_inputs(bad, NOW)

    def test_cli_validation_never_activates_services_or_echoes_bad_input(self):
        values = [json.dumps(fixture()).encode(), b'private-fixture', b'\xff', b'[]', b'x' * 4097,
                  (json.dumps(fixture())[:-1] + ', "assignment": "week10-a3"}').encode(),
                  b'[' * 1500 + b']' * 1500]
        for index, raw in enumerate(values):
            completed = subprocess.run(['/usr/bin/python3', '-I', '-B', str(ROOT / 'ci/ssh_tunnel.py'), 'validate-profile'],
                                       input=raw, capture_output=True, timeout=10,
                                       env={'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent'})
            self.assertEqual(completed.returncode, 0 if index == 0 else 1)
            if index == 0:
                self.assertIn(b'not_authorization_or_host_trust', completed.stdout)
            else:
                self.assertEqual(completed.stdout, b'')
                self.assertEqual(completed.stderr, b'transport_failed_closed; no native SSH task is authorized by this result\n')


class FilesystemTests(unittest.TestCase):
    def info(self, **changes):
        data = dict(st_uid=0, st_mode=stat.S_IFREG | 0o644, st_nlink=1, st_size=128, st_dev=1, st_ino=2)
        data.update(changes)
        return SimpleNamespace(**data)

    def test_unsafe_file_metadata_is_rejected(self):
        for changes in ({'st_uid': 1001}, {'st_mode': stat.S_IFREG | 0o666}, {'st_mode': stat.S_IFLNK | 0o644},
                        {'st_mode': stat.S_IFIFO | 0o644}, {'st_nlink': 2}, {'st_size': 0}, {'st_size': 4097}):
            path = Mock()
            path.lstat.return_value = self.info(**changes)
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.inspect_path(path, 0, {0o644}, 'file', 4096)

    def test_public_reads_are_bounded_nofollow_and_inode_checked(self):
        opened = mock_open(read_data=b'public')
        opened.return_value.fileno.return_value = 7
        with patch.object(tunnel, 'inspect_path', return_value=self.info()), patch.object(tunnel.os, 'open', return_value=7) as opening, \
                patch.object(tunnel.os, 'fdopen', opened), patch.object(tunnel.os, 'fstat', return_value=self.info()):
            self.assertEqual(tunnel.read_public(Path('/fixture'), 256), b'public')
            opening.assert_called_once_with(Path('/fixture'), tunnel.os.O_RDONLY | tunnel.os.O_NOFOLLOW)
            opened.return_value.read.assert_called_once_with(257)
        with patch.object(tunnel, 'inspect_path', return_value=self.info()), patch.object(tunnel.os, 'open', return_value=7), \
                patch.object(tunnel.os, 'fdopen', opened), patch.object(tunnel.os, 'fstat', return_value=self.info(st_ino=3)):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.read_public(Path('/fixture'), 256)

    def test_private_key_contents_are_never_read(self):
        known = ('week10-a2 ' + KEY + '\n').encode()
        with patch.object(tunnel, 'inspect_path') as inspect, patch.object(tunnel, 'read_public', side_effect=[json.dumps(fixture()).encode(), known]) as read:
            tunnel.load_profile('week10-a2', 1001)
        self.assertEqual([call.args[0].name for call in read.call_args_list], ['profile.json', 'known_hosts'])
        inspect.assert_any_call(tunnel.ROOT / 'week10-a2/id_ed25519', 1001, {0o400}, 'file', 4096)
        self.assertEqual(inspect.call_count, 5)

    def test_wrong_pin_rejected_before_key_inspection(self):
        with patch.object(tunnel, 'inspect_path') as inspect, patch.object(tunnel, 'read_public', side_effect=[json.dumps(fixture()).encode(), b'wrong-host fixture']):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.load_profile('week10-a2', 1001)
        self.assertEqual(inspect.call_count, 4)

    def test_context_rejects_root_other_accounts_and_clears_environment(self):
        with patch.object(tunnel.sys, 'platform', 'linux'), patch.object(tunnel.os, 'getuid', return_value=0):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.context('week10-a2', JOB)
        account = SimpleNamespace(pw_name='azdoagent', pw_dir='/home/azdoagent')
        with patch.object(tunnel.sys, 'platform', 'linux'), patch.object(tunnel.os, 'getuid', return_value=1001), \
                patch.object(tunnel.os, 'geteuid', return_value=1001), patch.object(tunnel.pwd, 'getpwuid', return_value=account), \
                patch.object(tunnel, 'inspect_path'), patch.dict(tunnel.os.environ, {'AWS_SECRET_ACCESS_KEY': 'synthetic', 'PAT': 'synthetic'}):
            self.assertEqual(tunnel.context('week10-a2', JOB)['env'], context()['env'])
            account.pw_name = 'ubuntu'
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.context('week10-a2', JOB)


class LifecycleTests(unittest.TestCase):
    def test_fixed_loopback_secure_client_and_bounded_unit(self):
        ctx = context()
        args = tunnel.start_arguments(fixture(), ctx)
        self.assertEqual(args[:4], ['/usr/bin/systemd-run', '--user', '--quiet', '--collect'])
        for value in ('RuntimeMaxSec=1200', 'TimeoutStopSec=10', 'KillMode=control-group', 'Restart=no', 'NoNewPrivileges=yes', 'RuntimeDirectoryMode=0700'):
            self.assertIn('--property=' + value, args)
        for value in ('StrictHostKeyChecking=yes', 'IdentityAgent=none', 'GlobalKnownHostsFile=/dev/null',
                      'HostKeyAlias=week10-a2', 'HostKeyAlgorithms=ssh-ed25519', 'ExitOnForwardFailure=yes',
                      'PermitLocalCommand=no', 'ForwardAgent=no', 'PasswordAuthentication=no', 'GatewayPorts=no', 'ControlPersist=no'):
            self.assertIn(value, args)
        self.assertIn('127.0.0.1:22222:127.0.0.1:22', args)
        self.assertEqual(args[-1], 'week10tunnel@1.1.1.1')
        offset = args.index('/usr/bin/env')
        self.assertEqual(args[offset:offset + 2], ['/usr/bin/env', '-i'])
        self.assertNotIn('-f', args)
        self.assertNotIn('sudo', ' '.join(args))
        self.assertIn(JOB.replace('-', ''), ctx['unit'])
        other = fixture()
        other['assignment'] = 'week10-a3'
        self.assertIn('127.0.0.1:22223:127.0.0.1:22', tunnel.ssh_arguments(other, ctx))

    def test_subprocess_has_no_shell_inherited_environment_or_input(self):
        with patch.object(tunnel.subprocess, 'run', return_value=result()) as run:
            tunnel.run(['/fixed-command'], context())
        kwargs = run.call_args.kwargs
        self.assertNotIn('shell', kwargs)
        self.assertEqual(kwargs['env'], context()['env'])
        self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
        self.assertEqual(kwargs['timeout'], 15)

    def test_timeout_bad_encoding_and_oversized_output_are_sanitized(self):
        for error in (OSError('private-fixture'), subprocess.TimeoutExpired('private-fixture', 1), UnicodeError('private-fixture')):
            with patch.object(tunnel.subprocess, 'run', side_effect=error):
                with self.assertRaises(tunnel.InvalidTransport) as raised:
                    tunnel.run(['/fixed-command'], context())
                self.assertNotIn('private-fixture', str(raised.exception))
        with patch.object(tunnel.subprocess, 'run', return_value=result(stdout='x' * 4097)):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.run(['/fixed-command'], context())

    def test_exact_service_metadata_required(self):
        for output in ('LoadState=loaded\n', 'LoadState=loaded\nLoadState=loaded\n', 'Secret=fixture\n',
                       '\n'.join(k + '=' + v for k, v in metadata(Transient='no').items())):
            with patch.object(tunnel, 'run', return_value=result(stdout=output)):
                with self.assertRaises(tunnel.InvalidTransport):
                    tunnel.properties(context())
        with patch.object(tunnel, 'run', return_value=result(code=1, stdout='LoadState=not-found\n')):
            self.assertEqual(tunnel.properties(context()), {'LoadState': 'not-found'})

    def test_readiness_binds_profile_master_pid_and_local_control_socket(self):
        with patch.object(tunnel, 'properties', return_value=metadata()), patch.object(tunnel, 'run', return_value=result(stderr='Master running (pid=1234)\r\n')) as run:
            self.assertTrue(tunnel.ready(fixture(), context()))
            self.assertIn('ProxyCommand=/usr/bin/false', run.call_args.args[0])
            self.assertIn(str(context()['control']), run.call_args.args[0])
        for value in (metadata(MainPID='0'), metadata(Environment='unrelated=fixture'), metadata(Environment='"unterminated')):
            with patch.object(tunnel, 'properties', return_value=value):
                with self.assertRaises(tunnel.InvalidTransport):
                    tunnel.ready(fixture(), context())
        with patch.object(tunnel, 'properties', return_value=metadata()), patch.object(tunnel, 'run', return_value=result(stderr='Master running (pid=9999)\n')):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.ready(fixture(), context())

    def test_inactive_or_unready_tunnel_is_not_success(self):
        with patch.object(tunnel, 'properties', return_value=metadata(ActiveState='activating')):
            self.assertFalse(tunnel.ready(fixture(), context()))
        with patch.object(tunnel, 'properties', return_value=metadata()), patch.object(tunnel, 'run', return_value=result(code=255)):
            self.assertFalse(tunnel.ready(fixture(), context()))

    def test_existing_job_is_never_adopted_or_stopped_by_start(self):
        with patch.object(tunnel, 'properties', return_value=metadata()), patch.object(tunnel, 'run') as run, patch.object(tunnel, 'stop') as stop:
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.start(fixture(), context())
            run.assert_not_called()
            stop.assert_not_called()

    def test_failed_start_and_failed_readiness_stop_only_exact_job(self):
        for failure in ('start', 'ready'):
            with patch.object(tunnel, 'properties', return_value={'LoadState': 'not-found'}), \
                    patch.object(tunnel, 'run', return_value=result(code=1 if failure == 'start' else 0)), \
                    patch.object(tunnel, 'ready', side_effect=tunnel.InvalidTransport('fixture')), patch.object(tunnel, 'stop') as stop:
                with self.assertRaises(tunnel.InvalidTransport):
                    tunnel.start(fixture(), context())
                stop.assert_called_once_with(context())

    def test_readiness_timeout_cleans_up(self):
        with patch.object(tunnel, 'properties', return_value={'LoadState': 'not-found'}), patch.object(tunnel, 'run', return_value=result()), \
                patch.object(tunnel.time, 'monotonic', side_effect=[0, 21]), patch.object(tunnel, 'stop') as stop:
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.start(fixture(), context())
            stop.assert_called_once_with(context())

    def test_start_rechecks_headroom_after_connection_and_cleans_up_if_lost(self):
        with patch.object(tunnel, 'properties', return_value={'LoadState': 'not-found'}), patch.object(tunnel, 'run', return_value=result()), \
                patch.object(tunnel, 'ready', return_value=True), patch.object(tunnel, 'validate_profile', side_effect=[fixture(), tunnel.InvalidTransport('expired')]) as validate, \
                patch.object(tunnel, 'stop') as stop:
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.start(fixture(), context())
            self.assertEqual(validate.call_count, 2)
            stop.assert_called_once_with(context())

    def test_failed_cleanup_is_not_reported_as_success(self):
        with patch.object(tunnel, 'properties', return_value={'LoadState': 'not-found'}), patch.object(tunnel, 'run', return_value=result(code=1)), \
                patch.object(tunnel, 'stop', side_effect=tunnel.InvalidTransport('fixture')):
            with self.assertRaisesRegex(tunnel.InvalidTransport, 'cleanup is not confirmed'):
                tunnel.start(fixture(), context())

    def test_stop_issues_exact_command_before_status_and_handles_absent_unit(self):
        with patch.object(tunnel, 'run', return_value=result(code=5)) as run, patch.object(tunnel, 'properties', return_value={'LoadState': 'not-found'}):
            tunnel.stop(context())
            self.assertEqual(run.call_args.args[0], ['/usr/bin/systemctl', '--user', 'stop', context()['unit']])
        with patch.object(tunnel, 'run', return_value=result()), patch.object(tunnel, 'properties', return_value=metadata()):
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.stop(context())

    def test_cleanup_does_not_depend_on_profile_existence_expiry_or_endpoint(self):
        with patch.object(tunnel, 'context', return_value=context()), patch.object(tunnel, 'load_profile') as load, \
                patch.object(tunnel, 'stop') as stop, patch('sys.stdout', new_callable=io.StringIO):
            tunnel.main(['stop', 'week10-a2', JOB])
            load.assert_not_called()
            stop.assert_called_once_with(context())

    def test_wrong_endpoint_rejected_before_start(self):
        with patch.object(tunnel, 'context', return_value=context()), patch.object(tunnel, 'load_profile', return_value=fixture()), patch.object(tunnel, 'start') as start:
            with self.assertRaises(tunnel.InvalidTransport):
                tunnel.main(['start', 'week10-a2', JOB, JOB])
            start.assert_not_called()


class TransportSourceTests(unittest.TestCase):
    def test_lifecycle_surrounds_all_native_tasks_and_always_stops(self):
        for name, assignment in (('static.azure-pipelines.yml', 'week10-a2'), ('react.azure-pipelines.yml', 'week10-a3')):
            pipeline = parse_yaml(name)
            job = pipeline['jobs'][0] if 'jobs' in pipeline else pipeline['stages'][-1]['jobs'][0]
            self.assertEqual(job['cancelTimeoutInMinutes'], 2)
            self.assertEqual(job['timeoutInMinutes'], 15)
            steps = job['steps']
            native = [i for i, step in enumerate(steps) if step.get('task') in ('SSH@0', 'CopyFilesOverSSH@0')]
            for index, position in enumerate(native):
                previous = steps[position - 1]
                self.assertIn('ssh_tunnel.py ' + ('start' if index == 0 else 'check') + ' ' + assignment, previous['bash'])
                self.assertEqual(previous['env'], {'JOB_ID': '$(System.JobId)', 'SSH_CONNECTION_ID': '$(sshServiceConnection)'})
                self.assertEqual(steps[position]['inputs']['sshEndpoint'], '$(sshServiceConnection)')
            self.assertEqual(steps[-1]['condition'], 'always()')
            self.assertIn('ssh_tunnel.py stop ' + assignment + ' "$JOB_ID"', steps[-1]['bash'])
            self.assertNotIn('SSH_CONNECTION_ID', steps[-1]['env'])

    def test_agent_preparation_is_fresh_only_and_never_starts_a_tunnel(self):
        controller, agent = parse_yaml('transport/configure-agent.yml')
        self.assertEqual(controller['hosts'], 'localhost')
        self.assertFalse(agent['gather_facts'])
        self.assertEqual(agent['pre_tasks'][0]['delegate_to'], 'localhost')
        pre = json.dumps(agent['pre_tasks'])
        for check in ('not week10_existing_profile.stat.exists', "week10_agent_sudo.rc == 1", "['azdoagent', 'L']", "mode == '0755'"):
            self.assertIn(check, pre)
        text = (ROOT / 'transport/configure-agent.yml').read_text()
        for forbidden in ('ansible.builtin.user:', 'ansible.builtin.shell:', 'config.sh', 'ssh_tunnel.py start', 'NOPASSWD', 'ansible.builtin.fetch:'):
            self.assertNotIn(forbidden, text)
        tasks = agent['tasks']
        generator = next(task for task in tasks if task.get('ansible.builtin.command', {}).get('argv', [''])[0] == '/usr/bin/ssh-keygen')
        self.assertTrue(generator['no_log'])
        slurp = [task['ansible.builtin.slurp']['src'] for task in tasks if 'ansible.builtin.slurp' in task]
        self.assertEqual(slurp, ['{{ week10_profile_dir }}/id_ed25519.pub'])
        self.assertEqual(tasks[-2]['ansible.builtin.copy']['dest'], '{{ week10_profile_dir }}/profile.json')
        self.assertIn('StrictHostKeyChecking=yes', agent['vars']['ansible_ssh_common_args'])

    def test_forwarding_account_restricted_before_key_authorization(self):
        tasks = parse_yaml('target/configure-tunnel.yml')
        user = next(task['ansible.builtin.user'] for task in tasks if 'ansible.builtin.user' in task)
        self.assertTrue(user['password_lock'])
        self.assertEqual(user['groups'], '')
        self.assertEqual(user['shell'], '/usr/sbin/nologin')
        config = next(task['ansible.builtin.blockinfile'] for task in tasks if 'ansible.builtin.blockinfile' in task)
        self.assertEqual(config['path'], '/etc/ssh/sshd_config')
        self.assertEqual(config['insertafter'], 'EOF')
        self.assertEqual(config['validate'], '/usr/sbin/sshd -t -f %s')
        for control in ('Match User week10tunnel', 'AllowTcpForwarding local', 'PermitListen none', 'PermitOpen 127.0.0.1:22', 'MaxSessions 0', 'AllowStreamLocalForwarding no'):
            self.assertIn(control, config['block'])
        key_index = next(i for i, task in enumerate(tasks) if task.get('ansible.builtin.copy', {}).get('dest', '').endswith('authorized_keys'))
        self.assertEqual(tasks[key_index - 1]['ansible.builtin.meta'], 'flush_handlers')
        key = tasks[key_index]['ansible.builtin.copy']
        self.assertIn('restrict,port-forwarding,from="{{ week10_target.agent_ipv4 }}/32",permitopen="127.0.0.1:22"', key['content'])
        self.assertIn('week10_target.tunnel_public_key', key['content'])
        self.assertEqual(tasks[-1]['ansible.builtin.copy']['dest'], '/etc/ssh/.dmi-week10-tunnel')

    def test_examples_remain_null_and_secrets_are_ignored(self):
        data = json.loads((ROOT / 'transport/inputs.example.json').read_text())['week10_agent_transport']
        self.assertIsNone(data['agent_ipv4'])
        self.assertTrue(all(value is None for value in data['profile'].values()))
        self.assertEqual(set(data['profile']), tunnel.FIELDS)
        self.assertIn('*.local.json', (ROOT / 'transport/.gitignore').read_text())
        with self.assertRaises(tunnel.InvalidTransport):
            tunnel.validate_agent_inputs(data)
