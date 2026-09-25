#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RECOMMENDATIONS={
 'auth':'Review the failing identity and its scoped service connection. Do not print or rotate credentials automatically.',
 'terraform':'Review the exact failed resource and a fresh Terraform plan before any operator-approved apply.',
 'ansible':'Inspect inventory, host trust and the named task; review the smallest configuration correction before rerunning.',
 'application':'Review the failed build or test input. For the documented controlled-failure signal, remove that pre-deployment failure only on the temporary branch and rerun it; do not merge the deliberate failure into main.',
 'unclassified':'Inspect the failed step with the operator. Unmatched failed or canceled runs remain INCIDENT.',
}
def classify(data):
 runs=data.get('pipelines',[])
 if len(runs)!=2 or any(r.get('status')!='completed' or r.get('result') not in ['succeeded','partiallySucceeded','failed','canceled'] for r in runs):return 'ERROR',2
 return ('HEALTHY',0) if all(r['result']=='succeeded' for r in runs) else ('INCIDENT',1)
def main(args):
 data=json.loads((ROOT/'reports/evidence.json').read_text())
 if len(args)==2 and args[0]=='has':return 0 if any(args[1] in p['signals'] and p['result']!='succeeded' for p in data['pipelines']) else 1
 assert args and args[0]=='report'
 status,code=classify(data);categories=args[1:]
 if status=='INCIDENT' and not categories:categories=['unclassified']
 lines=['Eze Favour — Azure DevOps dual-pipeline triage','Operator: Codex-assisted; read-only evidence gathering','Generated: '+data['generated_at'],'Overall Status: '+status,'Exit code: '+str(code)]
 for p in data['pipelines']:
  lines.extend([f"{p['kind']}: pipeline {p['pipeline_id']}, run {p['run_id']}, {p['result']}",'Branch: '+p['branch'],'Run: '+p['url']])
  lines.extend('Failed step: '+s for s in p['failed_steps'])
  if 'APPLICATION' in p['signals']:lines.append('Sanitized signal: controlled application failure or application build error matched.')
 for category in categories:lines.extend(['Category: '+category.upper(),'Recommendation: '+RECOMMENDATIONS[category]])
 if status=='HEALTHY':lines.append('No fix required. Both selected completed runs succeeded.')
 lines.append('No edit, push, approval, deployment, cloud change, or pipeline rerun was performed by this triage tool.')
 (ROOT/'reports/pipeline-health-report.txt').write_text('\n'.join(lines)+'\n')
 return code
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
