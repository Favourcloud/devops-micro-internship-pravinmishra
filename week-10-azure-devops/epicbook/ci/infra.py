#!/usr/bin/env python3
"""Plan first; apply only the exact artifact digest reviewed by the operator."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

os.umask(0o077)
root=Path(__file__).resolve().parents[1]/'terraform'
private=root/'.private';private.mkdir(exist_ok=True)
inputs=json.loads(os.environ['DMI_TF_INPUTS'])
backend=json.loads(os.environ['DMI_TF_BACKEND'])
assert inputs['name_prefix'].startswith('dmi-w10-a4-') and inputs['use_managed_identity'] is True
assert backend['use_azuread_auth'] and backend['use_msi'] and not backend['use_oidc']
(root/'inputs.auto.tfvars.json').write_text(json.dumps(inputs))
config=private/'backend.json';config.write_text(json.dumps(backend))
env={k:v for k,v in os.environ.items() if k not in ('ARM_CLIENT_SECRET','ARM_CLIENT_ID','ARM_OIDC_TOKEN')}
env.update(ARM_SUBSCRIPTION_ID=inputs['subscription_id'],ARM_TENANT_ID=inputs['tenant_id'],TF_IN_AUTOMATION='1',CHECKPOINT_DISABLE='1')
terraform='/opt/dmi-tools/terraform'
def run(*args,capture=False):
    return subprocess.run([terraform,*args],cwd=root,env=env,text=True,check=True,capture_output=capture)
run('init','-input=false','-no-color','-backend-config='+str(config))
run('validate','-no-color')
mode=os.environ['DMI_MODE']
if mode=='plan':
    state=run('state','list',capture=True).stdout.splitlines()
    if 'azurerm_resource_group.epicbook' not in state:
        rg='/subscriptions/'+inputs['subscription_id']+'/resourceGroups/'+inputs['name_prefix']+'-rg'
        run('import','-input=false','-no-color','azurerm_resource_group.epicbook',rg,capture=True)
    plan=private/'reviewed.tfplan'
    run('plan','-input=false','-no-color','-out='+str(plan))
    data=json.loads(run('show','-json',str(plan),capture=True).stdout)
    changes=[{'address':r['address'],'actions':r['change']['actions']} for r in data.get('resource_changes',[]) if r['change']['actions']!=['no-op']]
    digest=hashlib.sha256(plan.read_bytes()).hexdigest()
    artifact=Path(os.environ['DMI_ARTIFACT_DIR']);artifact.mkdir(parents=True,exist_ok=True)
    shutil.copy2(plan,artifact/'reviewed.tfplan')
    (artifact/'reviewed-plan.private.json').write_text(json.dumps(data))
    (artifact/'summary.json').write_text(json.dumps({'learner':'Eze Favour','operator':'Codex (assisted)','plan_sha256':digest,'changes':changes},indent=2))
    print(json.dumps({'plan_sha256':digest,'changes':changes},indent=2))
    print('Plan saved. A separate apply run must identify this build and exact reviewed SHA-256.')
elif mode=='apply':
    expected=os.environ['DMI_PLAN_SHA256'];assert re.fullmatch('[a-f0-9]{64}',expected),'An explicit reviewed plan digest is required'
    plan=Path(os.environ['DMI_PLAN_DIR'])/'reviewed.tfplan'
    assert hashlib.sha256(plan.read_bytes()).hexdigest()==expected,'Downloaded plan differs from the reviewed plan'
    run('apply','-input=false','-no-color',str(plan))
    outputs=json.loads(run('output','-json',capture=True).stdout)
    handoff={k:outputs[k]['value'] for k in ('app_public_ip','backend_ansible_host','backend_private_ip','mysql_fqdn')}
    print('Eze Favour — Terraform-to-Ansible handoff (operator copies these four values):')
    print(json.dumps(handoff,indent=2))
else:
    raise ValueError('Unsupported pipeline operation')
