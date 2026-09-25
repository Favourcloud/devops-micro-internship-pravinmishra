#!/usr/bin/env python3
"""Execute a fresh guarded check-mode run and summarize a sanitized event stream."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml

CATEGORIES = ('service_restarts_handlers', 'firewall_changes', 'user_sudo_changes', 'package_file_removal')

def inspect_source(root):
    files = sorted(set(root.rglob('*.yml')) | set(root.rglob('*.yaml')))
    hashes = {}
    def walk(value):
        if isinstance(value, dict):
            if 'check_mode' in value and value['check_mode'] not in (True, 'yes', 'true'):
                raise ValueError('Source can bypass check mode; review refused.')
            for k, v in value.items():
                if k.split('.')[-1] == 'uri' and isinstance(v, dict) and v.get('method', 'GET') not in ('GET','HEAD','OPTIONS'):
                    raise ValueError('Non-read-only URI task is not allowed in this review.')
                walk(v)
        elif isinstance(value, list):
            for item in value: walk(item)
    for p in files:
        if p.is_symlink(): raise ValueError('Symlinked YAML is not accepted.')
        raw=p.read_bytes()
        hashes[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
        walk(yaml.safe_load(raw))
    return hashes

def summarize(events, exit_code):
    recap=events.get('recap', {})
    valid=(events.get('schema')==1 and events.get('complete') is True and bool(recap))
    failed=(not valid or exit_code!=0 or bool(events.get('errors')) or
            any(v.get('failures',0) or v.get('unreachable',0) for v in recap.values()))
    tasks=events.get('changed_tasks', [])
    if sum(v.get('changed',0) for v in recap.values()) != sum(len(t['hosts']) for t in tasks):
        failed=True
    categorized={c:[t for t in tasks if c in t['categories']] for c in CATEGORIES}
    unmatched=[t for t in tasks if not t['categories']]
    return {'status':'ERROR' if failed else ('HOLD' if tasks else 'LOW'),
            'changed_task_count':len(tasks),'categories':categorized,
            'unmatched_changes':unmatched,'recap':recap,'errors':events.get('errors',[]),
            'exit_code':3 if failed else (2 if tasks else 0)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text())
    required={'inventory','playbook','ansible_bin','extra_vars','source_root','environment'}
    if set(cfg)!=required: raise ValueError('Unexpected or missing configuration field.')
    source=Path(cfg['source_root']).resolve()
    playbook=Path(cfg['playbook']).resolve()
    if not playbook.is_relative_to(source): raise ValueError('Playbook outside reviewed source.')
    hashes=inspect_source(source)
    out=Path(args.output).resolve()
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith('ANSIBLE_')}
    allowed={'ANSIBLE_CONFIG','ANSIBLE_COLLECTIONS_PATH','ANSIBLE_PRIVATE_KEY_FILE','ANSIBLE_LOCAL_TEMP','ANSIBLE_HOST_KEY_CHECKING','ANSIBLE_VAULT_PASSWORD_FILE','ANSIBLE_SSH_ARGS'}
    if set(cfg['environment'])-allowed: raise ValueError('Unsupported Ansible environment override.')
    env.update(cfg['environment'])
    env.update(ANSIBLE_CALLBACK_PLUGINS=str(Path(__file__).parent/'callback_plugins'),
               ANSIBLE_CALLBACKS_ENABLED='dmi_risk',DMI_RISK_EVENTS=str(out/'events.json'),
               ANSIBLE_NOCOLOR='1',ANSIBLE_DISPLAY_ARGS_TO_STDOUT='false')
    command=[cfg['ansible_bin'],'-i',cfg['inventory'],str(playbook),'--check','--diff','-e','@'+cfg['extra_vars']]
    with (out/'raw.stdout').open('x') as stdout,(out/'raw.stderr').open('x') as stderr:
        result=subprocess.run(command,cwd=source,env=env,stdout=stdout,stderr=stderr,stdin=subprocess.DEVNULL,timeout=1800)
    events=json.loads((out/'events.json').read_text()) if (out/'events.json').exists() else {}
    report=summarize(events,result.returncode)
    # Public reports include logical task source paths, not workstation paths.
    for group in list(report['categories'].values())+[report['unmatched_changes']]:
        for task in group: task['source']=task['source'].replace(str(source)+'/','')
    report.update(learner='Eze Favour',operator='Codex (assisted)',generated_at=datetime.now(timezone.utc).isoformat(),
                  source_sha256=hashes,raw_sha256={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['raw.stdout','raw.stderr']},
                  ansible_exit_code=result.returncode,mode='ansible-playbook --check --diff',
                  limitation='Check mode predicts supported module changes; it is not a security sandbox or manual learner execution.')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report['exit_code']

if __name__=='__main__':
    os.umask(0o077)
    try: sys.exit(main())
    except (ValueError,OSError,subprocess.TimeoutExpired) as e:
        print('Review failed closed: '+type(e).__name__,file=sys.stderr)
        sys.exit(3)
