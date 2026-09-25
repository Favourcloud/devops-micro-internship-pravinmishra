import json,subprocess,sys,unittest,tempfile,shutil
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
  for cmd in ['./run-triage.sh; env','cat ~/.aws/config','az pipelines run --id 5','./run-triage.sh && git push']:
   self.assertEqual(self.decision('Bash',{'command':cmd}),'deny')
 def test_private_and_edit_denied(self):
  self.assertEqual(self.decision('Read',{'file_path':str(ROOT/'.private/config.json')}),'deny')
  self.assertEqual(self.decision('Write',{'file_path':str(ROOT/'README.md')}),'deny')
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
