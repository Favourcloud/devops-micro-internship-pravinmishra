#!/usr/bin/env python3
"""Consume the explicit four-value handoff and scoped pipeline secrets."""
import hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
from validate_handoff import parse_handoff,inventory
root=Path(__file__).resolve().parent
os.umask(0o077)
handoff=parse_handoff((root/'handoff.json').read_bytes())
release_dir=Path(os.environ['DMI_RELEASE_DIR']);release=json.loads((release_dir/'release.json').read_text())
archive=release_dir/'epicbook.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==release['archive_sha256']
key=Path(os.environ['DMI_SSH_KEY']);assert key.is_file();key.chmod(0o600)
for name in ['DMI_DATABASE_PASSWORD','DMI_SESSION_SECRET']:
 assert re.fullmatch('[A-Za-z0-9_-]{32,128}',os.environ[name])
with tempfile.TemporaryDirectory(prefix='dmi-epic10-') as d:
 private=Path(d)
 known=private/'known_hosts';known.write_text(os.environ['DMI_KNOWN_HOSTS'].strip()+'\n')
 for ip in [handoff['app_public_ip'],handoff['backend_ansible_host']]:
  assert any(line.split()[0]==ip and line.split()[1]=='ssh-ed25519' for line in known.read_text().splitlines())
 inv=inventory(handoff)
 inv['all']['vars'].update(ansible_user='labadmin',ansible_connection='ssh',ansible_python_interpreter='/usr/bin/python3',ansible_ssh_private_key_file=str(key),ansible_ssh_common_args=f'-o StrictHostKeyChecking=yes -o UserKnownHostsFile={known} -o GlobalKnownHostsFile=/dev/null -o IdentitiesOnly=yes -o ForwardAgent=no')
 (private/'inventory.json').write_text(json.dumps(inv))
 variables={'deployment_approved':True,'app_runtime_compatibility_acknowledged':True,'app_release_id':release['release_id'],'app_runtime_dest':'/opt/epicbook/releases/'+release['release_id'],'app_release_archive':str(archive),'vault_epicbook_db_password':os.environ['DMI_DATABASE_PASSWORD'],'vault_epicbook_session_secret':os.environ['DMI_SESSION_SECRET'],'vault_epicbook_mysql_admin_password':os.environ['DMI_MYSQL_ADMIN_PASSWORD']}
 (private/'vars.json').write_text(json.dumps(variables))
 env={k:v for k,v in os.environ.items() if not k.startswith(('DMI_','AWS_','ARM_'))}
 env.update(ANSIBLE_HOST_KEY_CHECKING='True',ANSIBLE_NOCOLOR='1',ANSIBLE_LOCAL_TEMP=str(private/'tmp'),ANSIBLE_COLLECTIONS_PATH=str(root/'.venv/collections'))
 command=[str(root/'.venv/bin/ansible-playbook'),'-i',str(private/'inventory.json'),str(root/'ansible/site.yml'),'-e','@'+str(private/'vars.json')]
 for step in ['deploy','idempotence']:
  result=subprocess.run(command,env=env,text=True,capture_output=True)
  print(result.stdout);print(result.stderr)
  assert result.returncode==0,'Ansible failed'
  recap=result.stdout.split('PLAY RECAP')[-1]
  for host in ['epicbook_frontend','epicbook_backend']:
   assert re.search(host+r'\s+:.*unreachable=0\s+failed=0',recap)
   if step=='idempotence':assert re.search(host+r'\s+:.*changed=0',recap),'Idempotence regression'
 print('Eze Favour — both hosts verified; unchanged second run changed=0.')
