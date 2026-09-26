import json,os,pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parent
class AuditTests(unittest.TestCase):
 def run_case(self,user='node',health=True,image='app:1.0',priv=False,ports=1,missing=False):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td);d={'Config':{'User':user,'Image':image,'Healthcheck':{'Test':['CMD','true']} if health else None,'ExposedPorts':{str(80+i)+'/tcp':{} for i in range(ports)}},'HostConfig':{'Privileged':priv,'PortBindings':{}},'Image':'sha256:fixture'}
   (p/'container.json').write_text(json.dumps([d])); (p/'image.json').write_text(json.dumps([d]))
   (p/'docker').write_text('#!/bin/sh\ncase "$1 $2" in "inspect --type") '+('exit 1' if missing else 'cat "'+str(p/'container.json')+'"')+';; "image inspect") cat "'+str(p/'image.json')+'";; *) echo "Forbidden Docker operation" >&2; exit 99;; esac\n');(p/'docker').chmod(0o755)
   r=subprocess.run(['bash',str(ROOT/'docker-audit.sh'),'fixture'],cwd=p,env={**os.environ,'PATH':td+':'+os.environ['PATH']},capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);return r.stdout
 def test_hardened(self):self.assertIn('SUMMARY: PASS=6 WARN=0 FAIL=0',self.run_case())
 def test_root_without_probe_latest(self):self.assertIn('SUMMARY: PASS=3 WARN=0 FAIL=3',self.run_case(user='',health=False,image='app:latest'))
 def test_uid_zero_group(self):self.assertIn('FAIL | user',self.run_case(user='0:1000'))
 def test_privileged(self):self.assertIn('FAIL | privileged',self.run_case(priv=True))
 def test_extra_ports(self):self.assertIn('WARN | ports',self.run_case(ports=3))
 def test_missing(self):self.assertIn('SUMMARY: PASS=0 WARN=5 FAIL=1',self.run_case(missing=True))
 def test_digest(self):self.assertIn('Digest-pinned image',self.run_case(image='app@sha256:abc'))
 def test_guard(self):
  for command,allowed in [('./run-audit.sh',True),('./inspect-container.sh 2>&1',True),('./run-audit.sh; docker stop app',False),('docker build .',False),('./run-audit.sh > Dockerfile',False),('bash ./run-audit.sh',False)]:
   r=subprocess.run(['python3',str(ROOT/'guard.py')],input=json.dumps({'tool_name':'Bash','tool_input':{'command':command}}),text=True,capture_output=True,env={**os.environ,'DMI_AUDIT_ROOT':str(ROOT)})
   self.assertEqual(r.returncode==0,allowed,command)
if __name__=='__main__':unittest.main()
