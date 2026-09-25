#!/usr/bin/env python3
"""Read-only Azure DevOps evidence gathering; raw responses never leave memory."""
import base64,json,os,re,urllib.request,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PAT=os.environ['AZDO_READ_PAT']
CONFIG=json.loads((ROOT/'.private/config.json').read_text())
assert set(CONFIG)=={'infrastructure_id','application_id','application_branch'}
assert all(type(CONFIG[k]) is int and CONFIG[k]>0 for k in ['infrastructure_id','application_id'])
assert CONFIG['application_branch'] in ['refs/heads/main','refs/heads/triage-safe-drill']
ORG='https://dev.azure.com/aneneeze2021/DMI-Week10/_apis/'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):raise RuntimeError('Unexpected API redirect')
opener=urllib.request.build_opener(NoRedirect())
def get(path,text=False):
 assert path.startswith('build/builds')
 url=ORG+path+('&' if '?' in path else '?')+'api-version=7.1'
 req=urllib.request.Request(url,method='GET',headers={'Authorization':'Basic '+base64.b64encode((':'+PAT).encode()).decode()})
 with opener.open(req,timeout=40) as r:
  data=r.read(4_000_001);assert len(data)<=4_000_000,'Evidence exceeds bound'
 value=data.decode()
 return value if text else json.loads(value)
SIGNALS={
 'AUTH':r'AuthorizationFailed|AuthenticationFailed|AADSTS\d+|TF400813|InvalidAuthenticationToken|ExpiredToken',
 'TERRAFORM':r'Error: (?:creating|acquiring|Unsupported|Invalid|a resource)|terraform.*(?:failed|exit code [1-9])|ProvisionNotSupportedForRegion|SkuNotAvailable',
 'ANSIBLE':r'UNREACHABLE!|FAILED!|failed=[1-9]\d*|unreachable=[1-9]\d*',
 'APPLICATION':r'DMI_CONTROLLED_FAILURE: missing demo build input|npm ERR!|npm error|Source mismatch:|test suite failed|FAIL src/',
}
def pipeline(kind,definition,branch):
 values=get('build/builds?definitions='+str(definition)+'&statusFilter=completed&queryOrder=finishTimeDescending&$top=1&branchName='+urllib.parse.quote(branch,safe=''))['value']
 assert len(values)==1,'No completed run for '+kind
 run=values[0];assert run['definition']['id']==definition
 result={'kind':kind,'pipeline_id':definition,'run_id':run['id'],'branch':run['sourceBranch'],'status':run['status'],'result':run['result'],'finish_time':run['finishTime'],'signals':[],'failed_steps':[],'url':'https://dev.azure.com/aneneeze2021/DMI-Week10/_build/results?buildId='+str(run['id'])}
 timeline=get('build/builds/'+str(run['id'])+'/timeline')['records']
 tasks=[t for t in timeline if t.get('type')=='Task' and t.get('result') in ['failed','canceled']]
 for t in tasks[:20]:
  # Step names are untrusted source: retain only bounded readable characters.
  result['failed_steps'].append(re.sub(r'[^A-Za-z0-9 .:_/-]','?',t.get('name','unknown'))[:120])
  log=t.get('log')
  if not log:continue
  assert type(log['id']) is int
  raw=get('build/builds/'+str(run['id'])+'/logs/'+str(log['id']),text=True)
  for category,pattern in SIGNALS.items():
   if re.search(pattern,raw,re.I):result['signals'].append(category)
 result['signals']=sorted(set(result['signals']))
 return result
report={'learner':'Eze Favour','operator':'Codex-assisted','generated_at':datetime.now(timezone.utc).isoformat(),'read_only':True,'pipelines':[pipeline('infrastructure',CONFIG['infrastructure_id'],'refs/heads/main'),pipeline('application',CONFIG['application_id'],CONFIG['application_branch'])]}
(ROOT/'reports/evidence.json').write_text(json.dumps(report,indent=2)+'\n')
