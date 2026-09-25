"""Collect check-mode task identities without serializing module results/secrets."""
import json
import os
from pathlib import Path
from ansible.plugins.callback import CallbackBase

DOCUMENTATION = r'''
callback: dmi_risk
type: aggregate
short_description: Record changed task identities and host outcomes for risk review
version_added: "1.0.0"
requirements:
  - Enable with ANSIBLE_CALLBACKS_ENABLED=dmi_risk
'''

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'dmi_risk'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()
        self.tasks = {}
        self.errors = []

    def v2_runner_on_ok(self, result):
        if not result._result.get('changed'):
            return
        task = result._task
        args = task.args or {}
        module = task.action.split('.')[-1]
        state = str(args.get('state', ''))
        path = str(args.get('path', args.get('dest', '')))
        categories = []
        # Do not depend on attacker-controlled task names to identify risk.
        if task.__class__.__name__ == 'Handler' or module in ('service', 'systemd', 'systemd_service'):
            categories.append('service_restarts_handlers')
        if module in ('ufw', 'firewalld', 'iptables', 'iptables_state') or any(s in path for s in ('/ufw/', '/firewalld/', '/iptables/')):
            categories.append('firewall_changes')
        if module in ('user', 'group') or 'sudoers' in path:
            categories.append('user_sudo_changes')
        if (module in ('apt', 'yum', 'dnf', 'package', 'file') and state == 'absent'):
            categories.append('package_file_removal')
        # Unknown command/shell changes remain unmatched, never LOW by omission.
        key = str(task._uuid)
        entry = self.tasks.setdefault(key, {
            'task_id': key, 'task': task.get_name(), 'source': task.get_path(),
            'module': task.action, 'categories': categories, 'hosts': [],
            'no_log': bool(task.no_log),
        })
        host = result._host.get_name()
        if host not in entry['hosts']:
            entry['hosts'].append(host)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.errors.append({'host': result._host.get_name(), 'kind': 'failed', 'ignored': bool(ignore_errors)})

    def v2_runner_on_unreachable(self, result):
        self.errors.append({'host': result._host.get_name(), 'kind': 'unreachable'})

    def v2_playbook_on_stats(self, stats):
        payload = {'schema': 1, 'complete': True, 'changed_tasks': list(self.tasks.values()),
                   'errors': self.errors, 'recap': {h: stats.summarize(h) for h in sorted(stats.processed)}}
        path = Path(os.environ['DMI_RISK_EVENTS'])
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(payload, stream, indent=2)
            stream.write('\n')
