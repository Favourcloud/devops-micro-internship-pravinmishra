"""Bounded, host-pinned transport for required native SSH tasks on one trusted agent."""

import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import stat
import struct
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone


ROOT = Path('/etc/dmi-week10/tunnels')
ACCOUNT = 'azdoagent'
PORTS = {'week10-a2': 22222, 'week10-a3': 22223}
LIFETIME = 1200
START_HEADROOM = LIFETIME + 60
FIELDS = {'assignment', 'target_ipv4', 'host_public_key', 'ssh_endpoint_id', 'authorized_at', 'expires_at'}
PROPERTIES = {'LoadState', 'ActiveState', 'SubState', 'MainPID', 'Transient', 'Environment'}


class InvalidTransport(Exception):
    pass


def require(condition, message):
    if not condition:
        raise InvalidTransport(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate field')
        result[key] = value
    return result


def public_key(value):
    require(isinstance(value, str) and len(value) == 80 and value.startswith('ssh-ed25519 '), 'Public Ed25519 key required')
    try:
        blob = base64.b64decode(value[12:], validate=True)
    except ValueError:
        raise InvalidTransport('Invalid public key') from None
    prefix = struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32)
    require(len(blob) == 51 and blob.startswith(prefix) and blob[-32:] != bytes(32), 'Invalid public key')
    require(base64.b64encode(blob).decode('ascii') == value[12:], 'Noncanonical public key')


def public_ipv4(value):
    require(isinstance(value, str), 'Public IPv4 required')
    try:
        address = ipaddress.IPv4Address(value)
    except ValueError:
        raise InvalidTransport('Invalid IPv4') from None
    require(str(address) == value and address.is_global and not address.is_multicast and not address.is_reserved, 'Public unicast IPv4 required')


def identifier(value):
    try:
        parsed = uuid.UUID(value)
        require(str(parsed) == value and parsed.int != 0, 'Canonical nonzero UUID required')
    except (ValueError, TypeError, AttributeError):
        raise InvalidTransport('Invalid UUID') from None
    return parsed


def instant(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value), 'UTC timestamp required')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        raise InvalidTransport('Invalid timestamp') from None


def validate_profile(data, now=None, minimum_remaining=0):
    require(isinstance(data, dict) and set(data) == FIELDS, 'Unexpected profile fields')
    require(isinstance(data['assignment'], str) and data['assignment'] in PORTS, 'Unsupported assignment')
    public_ipv4(data['target_ipv4'])
    public_key(data['host_public_key'])
    identifier(data['ssh_endpoint_id'])
    start, end = instant(data['authorized_at']), instant(data['expires_at'])
    now = now or datetime.now(timezone.utc)
    require(0 < (end - start).total_seconds() <= 86400, 'Window must be at most 24 hours')
    require(start <= now < end and (end - now).total_seconds() >= minimum_remaining, 'Authorization window unavailable or too short')
    return data


def validate_agent_inputs(data, now=None):
    if isinstance(data, dict) and set(data) == {'week10_agent_transport'}:
        data = data['week10_agent_transport']
    require(isinstance(data, dict) and set(data) == {'agent_ipv4', 'profile'}, 'Unexpected agent input fields')
    public_ipv4(data['agent_ipv4'])
    validate_profile(data['profile'], now=now, minimum_remaining=START_HEADROOM)
    require(data['agent_ipv4'] != data['profile']['target_ipv4'], 'Separate agent and target required')
    return data


def profile_digest(profile):
    return hashlib.sha256(json.dumps(profile, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def inspect_path(path, owner, modes, kind, maximum=None):
    info = path.lstat()
    require(info.st_uid == owner and stat.S_IMODE(info.st_mode) in modes, 'Unsafe path ownership or permissions')
    require(not stat.S_ISLNK(info.st_mode), 'Symlink refused')
    require({'file': stat.S_ISREG, 'directory': stat.S_ISDIR, 'socket': stat.S_ISSOCK}[kind](info.st_mode), 'Unexpected path type')
    if kind == 'file':
        require(info.st_nlink == 1 and 0 < info.st_size <= maximum, 'Unsafe file shape')
    return info


def read_public(path, maximum):
    before = inspect_path(path, 0, {0o644}, 'file', maximum)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        after = os.fstat(stream.fileno())
        require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino), 'File changed during open')
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, 'Public file exceeds bound')
    return data


def load_profile(assignment, uid, minimum_remaining=0):
    directory = ROOT / assignment
    for path in (Path('/etc'), ROOT.parent, ROOT, directory):
        inspect_path(path, 0, {0o755}, 'directory')
    profile = json.loads(read_public(directory / 'profile.json', 4096), object_pairs_hook=unique_object)
    validate_profile(profile, minimum_remaining=minimum_remaining)
    require(profile['assignment'] == assignment, 'Profile assignment mismatch')
    expected = (assignment + ' ' + profile['host_public_key'] + '\n').encode('ascii')
    require(read_public(directory / 'known_hosts', 256) == expected, 'Host pin mismatch')
    # The helper checks metadata only. OpenSSH alone reads the private identity.
    inspect_path(directory / 'id_ed25519', uid, {0o400}, 'file', 4096)
    return profile


def names(assignment, job_id, uid):
    require(isinstance(assignment, str) and assignment in PORTS, 'Unsupported assignment')
    job = identifier(job_id)
    stem = 'dmi-' + assignment + '-' + job.hex
    runtime = Path('/run/user') / str(uid)
    control = runtime / stem / 'control'
    require(len(os.fsencode(control)) < 100, 'Control path exceeds bound')
    return {'unit': stem + '.service', 'directory': stem, 'runtime': runtime, 'control': control}


def context(assignment, job_id):
    uid = os.getuid()
    require(sys.platform == 'linux' and uid != 0 and uid == os.geteuid(), 'Non-root Linux agent required')
    account = pwd.getpwuid(uid)
    require(account.pw_name == ACCOUNT, 'Dedicated agent account required')
    ctx = names(assignment, job_id, uid)
    inspect_path(Path('/run'), 0, {0o755}, 'directory')
    inspect_path(Path('/run/user'), 0, {0o755}, 'directory')
    inspect_path(ctx['runtime'], uid, {0o700}, 'directory')
    inspect_path(ctx['runtime'] / 'bus', uid, {0o600, 0o660, 0o666}, 'socket')
    ctx['uid'] = uid
    ctx['env'] = {'PATH': '/usr/bin:/bin', 'HOME': account.pw_dir, 'LANG': 'C', 'LC_ALL': 'C',
                  'XDG_RUNTIME_DIR': str(ctx['runtime']), 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=' + str(ctx['runtime'] / 'bus')}
    return ctx


def ssh_arguments(profile, ctx):
    assignment = profile['assignment']
    directory = ROOT / assignment
    options = ['BatchMode=yes', 'IdentitiesOnly=yes', 'IdentityAgent=none',
               'StrictHostKeyChecking=yes', 'UserKnownHostsFile=' + str(directory / 'known_hosts'),
               'GlobalKnownHostsFile=/dev/null', 'HostKeyAlias=' + assignment,
               'HostKeyAlgorithms=ssh-ed25519', 'UpdateHostKeys=no', 'VerifyHostKeyDNS=no',
               'PreferredAuthentications=publickey', 'PasswordAuthentication=no', 'KbdInteractiveAuthentication=no',
               'ForwardAgent=no', 'ForwardX11=no', 'GatewayPorts=no', 'PermitLocalCommand=no',
               'ExitOnForwardFailure=yes', 'ControlPersist=no', 'ConnectionAttempts=1', 'ConnectTimeout=10',
               'ServerAliveInterval=10', 'ServerAliveCountMax=2']
    argv = ['/usr/bin/ssh', '-F', '/dev/null', '-N', '-T', '-M', '-S', str(ctx['control'])]
    for option in options:
        argv.extend(['-o', option])
    argv.extend(['-i', str(directory / 'id_ed25519'), '-L', '127.0.0.1:' + str(PORTS[assignment]) + ':127.0.0.1:22',
                 'week10tunnel@' + profile['target_ipv4']])
    return argv


def start_arguments(profile, ctx):
    validate_profile(profile, minimum_remaining=START_HEADROOM)
    properties = ['Type=exec', 'RuntimeMaxSec=' + str(LIFETIME), 'TimeoutStopSec=10', 'KillMode=control-group',
                  'Restart=no', 'NoNewPrivileges=yes', 'UMask=0077', 'RuntimeDirectory=' + ctx['directory'],
                  'RuntimeDirectoryMode=0700']
    argv = ['/usr/bin/systemd-run', '--user', '--quiet', '--collect', '--unit=' + ctx['unit']]
    argv.extend('--property=' + value for value in properties)
    argv.extend(['--setenv=SSH_ASKPASS_REQUIRE=never', '--setenv=DMI_W10_PROFILE_SHA256=' + profile_digest(profile), '--'])
    # A user manager can retain login environment; clear it again inside the unit.
    return argv + ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME=' + ctx['env']['HOME'],
                   'LANG=C', 'LC_ALL=C', 'SSH_ASKPASS_REQUIRE=never'] + ssh_arguments(profile, ctx)


def run(argv, ctx, timeout=15):
    try:
        result = subprocess.run(argv, env=ctx['env'], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired, UnicodeError, ValueError):
        raise InvalidTransport('Transport command failed or timed out') from None
    require(len(result.stdout) <= 4096 and len(result.stderr) <= 4096, 'Transport response exceeds bound')
    return result


def properties(ctx):
    result = run(['/usr/bin/systemctl', '--user', '--no-pager', 'show', '--property=' + ','.join(sorted(PROPERTIES)), ctx['unit']], ctx)
    values = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition('=')
        require(sep and key in PROPERTIES and key not in values, 'Unexpected service metadata')
        values[key] = value
    if values.get('LoadState') == 'not-found' and result.returncode in (0, 1):
        return values
    require(result.returncode == 0 and set(values) == PROPERTIES and values['Transient'] == 'yes', 'Unverified job service')
    return values


def stop(ctx):
    # Attempt the exact job-scoped stop even when earlier status output was malformed.
    result = run(['/usr/bin/systemctl', '--user', 'stop', ctx['unit']], ctx)
    value = properties(ctx)
    require(value.get('LoadState') == 'not-found' or (result.returncode == 0 and value.get('ActiveState') in ('inactive', 'failed') and value.get('MainPID') == '0'), 'Tunnel cleanup not confirmed')


def ready(profile, ctx):
    value = properties(ctx)
    if value.get('ActiveState') != 'active' or value.get('SubState') != 'running':
        return False
    require(re.fullmatch(r'[1-9][0-9]*', value['MainPID']), 'Invalid tunnel process')
    expected = {'SSH_ASKPASS_REQUIRE=never', 'DMI_W10_PROFILE_SHA256=' + profile_digest(profile)}
    try:
        environment = set(shlex.split(value['Environment']))
    except ValueError:
        raise InvalidTransport('Malformed service metadata') from None
    require(environment == expected, 'Active service profile mismatch')
    result = run(['/usr/bin/ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'ProxyCommand=/usr/bin/false',
                  '-S', str(ctx['control']), '-O', 'check', '127.0.0.1'], ctx, timeout=5)
    if result.returncode != 0:
        return False
    match = re.fullmatch(r'Master running \(pid=([1-9][0-9]*)\)\s*', result.stderr)
    require(match and match.group(1) == value['MainPID'], 'Control master identity mismatch')
    return True


def start(profile, ctx):
    require(properties(ctx).get('LoadState') == 'not-found', 'Existing job service refused')
    try:
        result = run(start_arguments(profile, ctx), ctx)
        require(result.returncode == 0, 'Job tunnel start failed')
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if ready(profile, ctx):
                validate_profile(profile, minimum_remaining=START_HEADROOM)
                return
            time.sleep(0.2)
        raise InvalidTransport('Host-pinned connection not ready')
    except (InvalidTransport, KeyboardInterrupt):
        try:
            stop(ctx)
        except InvalidTransport:
            raise InvalidTransport('Start failed and cleanup is not confirmed') from None
        raise


def main(argv):
    if argv in (['validate-profile'], ['validate-agent-inputs']):
        raw = sys.stdin.buffer.read(4097)
        require(len(raw) <= 4096, 'Input exceeds bound')
        data = json.loads(raw, object_pairs_hook=unique_object)
        if argv == ['validate-profile']:
            validate_profile(data, minimum_remaining=START_HEADROOM)
        else:
            validate_agent_inputs(data)
        print('profile_shape_valid_not_authorization_or_host_trust')
        return
    require((len(argv) == 3 and argv[0] == 'stop') or (len(argv) == 4 and argv[0] in ('start', 'check')), 'Expected bounded action and resource identifiers')
    action, assignment, job_id = argv[:3]
    ctx = context(assignment, job_id)
    if action == 'stop':
        stop(ctx)
        print('job_tunnel_stopped_or_absent')
        return
    endpoint = argv[3]
    identifier(endpoint)
    profile = load_profile(assignment, ctx['uid'], START_HEADROOM if action == 'start' else 0)
    require(profile['ssh_endpoint_id'] == endpoint, 'Unapproved service connection')
    if action == 'start':
        start(profile, ctx)
    else:
        require(ready(profile, ctx), 'Host-pinned job tunnel unavailable')
    print('host_pinned_tunnel_ready_not_deployment_evidence')


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (InvalidTransport, OSError, ValueError, TypeError, UnicodeError, RecursionError, KeyboardInterrupt):
        print('transport_failed_closed; no native SSH task is authorized by this result', file=sys.stderr)
        raise SystemExit(1)
