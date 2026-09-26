import json,subprocess,sys,unittest,tempfile,shutil,os
from pathlib import Path
from classify import classify
ROOT=Path(__file__).resolve().parent
class Classification(unittest.TestCase):
 def test_both_completed_successful(self):
  self.assertEqual(classify({'pipelines':[{'status':'completed','result':'succeeded'}]*2}),('HEALTHY',0))
 def test_unmatched_failure_remains_incident(self):
  self.assertEqual(classify({'pipelines':[{'status':'completed','result':'succeeded'},{'status':'completed','result':'failed','signals':[]}]}),('INCIDENT',1))
 def test_missing_running_and_partial_fail_closed(self):
  for data in [{}, {'pipelines':[{'status':'inProgress','result':'succeeded'}]*2}]:self.assertEqual(classify(data),('ERROR',2))
  self.assertEqual(classify({'pipelines':[{'status':'completed','result':'partiallySucceeded'}]*2}),('INCIDENT',1))
class Guard(unittest.TestCase):
 def decision(self,name,args):
  e={'tool_name':name,'tool_input':args,'cwd':str(ROOT)}
  r=subprocess.run([sys.executable,str(ROOT/'guard.py')],input=json.dumps(e),text=True,capture_output=True,check=True)
  return json.loads(r.stdout)['hookSpecificOutput']['permissionDecision']
 def test_exact_wrapper_only(self):
  self.assertEqual(self.decision('Bash',{'command':'./run-triage.sh'}),'allow')
  for cmd in ['./run-triage.sh 2>&1','./run-triage.sh; env','cat ~/.aws/config','az pipelines run --id 5','./run-triage.sh && git push']:
   self.assertEqual(self.decision('Bash',{'command':cmd}),'deny')
 def test_private_and_edit_denied(self):
  self.assertEqual(self.decision('Read',{'file_path':str(ROOT/'.private/config.json')}),'deny')
  self.assertEqual(self.decision('Write',{'file_path':str(ROOT/'README.md')}),'deny')
class FreshnessGuard(unittest.TestCase):
 def test_stale_missing_and_pending_reports_are_denied(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);shutil.copy2(ROOT/'guard.py',root/'guard.py');(root/'reports').mkdir()
   report=root/'reports/pipeline-health-report.txt'
   for generated,started,status,want in [
    ('2026-09-25T10:00:00+00:00','2026-09-26T10:00:00+00:00','HEALTHY','deny'),
    ('2026-09-26T10:00:01+00:00',None,'HEALTHY','deny'),
    ('2026-09-26T10:00:01+00:00','2026-09-26T10:00:00+00:00','RUNNING','deny'),
    ('2026-09-26T10:00:01+00:00','2026-09-26T10:00:00+00:00','INCIDENT','allow')]:
    with self.subTest(generated=generated,started=started,status=status):
     report.write_text('Overall Status: '+status)
     (root/'reports/evidence.json').write_text(json.dumps({'generated_at':generated}))
     env=dict(os.environ);env.pop('DMI_TRIAGE_NOT_BEFORE',None)
     if started:env['DMI_TRIAGE_NOT_BEFORE']=started
     event={'tool_name':'Read','tool_input':{'file_path':str(report)},'cwd':str(root)}
     p=subprocess.run([sys.executable,str(root/'guard.py')],input=json.dumps(event),text=True,capture_output=True,env=env,check=True)
     self.assertEqual(json.loads(p.stdout)['hookSpecificOutput']['permissionDecision'],want)
class ShellIntegration(unittest.TestCase):
 def test_healthy_empty_categories_and_unknown_failure(self):
  for result,expected in [('succeeded',0),('failed',1)]:
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for name in ['pipeline-triage.sh','classify.py']:shutil.copy2(ROOT/name,root/name)
    run={'kind':'test','pipeline_id':1,'run_id':1,'branch':'refs/heads/main','status':'completed','result':result,'failed_steps':[],'signals':[],'url':'https://example.invalid'}
    report={'generated_at':'fixture','pipelines':[run,run]}
    (root/'fetch.py').write_text("from pathlib import Path\nPath('reports/evidence.json').write_text("+repr(json.dumps(report))+")\n")
    p=subprocess.run(['/bin/bash',str(root/'pipeline-triage.sh')],text=True,capture_output=True)
    self.assertEqual(p.returncode,expected,p.stderr)
    self.assertIn('HEALTHY' if expected==0 else 'INCIDENT',p.stdout)
if __name__=='__main__':unittest.main()
