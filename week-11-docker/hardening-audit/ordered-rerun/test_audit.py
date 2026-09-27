import json,os,pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parent
class AuditTests(unittest.TestCase):
 def run_case(self,user='node',health=True,image='app:1.0',priv=False,ports=1,missing=False,running=True,image_inspect=True,bindings=None,name='fixture'):
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td);d={'State':{'Running':running},'Config':{'User':user,'Image':image,'Healthcheck':({'Test':['NONE']} if health=='NONE' else {'Test':['CMD','true']}) if health else None,'ExposedPorts':{str(80+i)+'/tcp':{} for i in range(ports)}},'HostConfig':{'Privileged':priv,'PortBindings':bindings or {}},'Image':'sha256:fixture'}
   (p/'container.json').write_text(json.dumps([d])); (p/'image.json').write_text(json.dumps([d]))
   (p/'docker').write_text('#!/bin/sh\ncase "$1 $2" in "inspect --type") '+('exit 1' if missing else 'cat "'+str(p/'container.json')+'"')+';; "image inspect") '+('cat "'+str(p/'image.json')+'"' if image_inspect else 'exit 1')+';; *) echo "Forbidden Docker operation" >&2; exit 99;; esac\n');(p/'docker').chmod(0o755)
   r=subprocess.run(['bash',str(ROOT/'docker-audit.sh'),name],cwd=p,env={**os.environ,'PATH':td+':'+os.environ['PATH']},capture_output=True,text=True);self.assertEqual(r.returncode,2 if name.startswith('-') else 0,r.stderr);return r.stdout
 def test_hardened(self):self.assertIn('SUMMARY: PASS=6 WARN=0 FAIL=0',self.run_case())
 def test_root_without_probe_latest(self):self.assertIn('SUMMARY: PASS=3 WARN=0 FAIL=3',self.run_case(user='',health=False,image='app:latest'))
 def test_uid_zero_group(self):self.assertIn('FAIL | user',self.run_case(user='0:1000'))
 def test_privileged(self):self.assertIn('FAIL | privileged',self.run_case(priv=True))
 def test_extra_ports(self):self.assertIn('WARN | ports',self.run_case(ports=3))
 def test_missing(self):self.assertIn('SUMMARY: PASS=0 WARN=5 FAIL=1',self.run_case(missing=True))
 def test_digest(self):self.assertIn('immutable digest',self.run_case(image='app@sha256:'+'a'*64))
 def test_healthcheck_none(self):self.assertIn('FAIL | healthcheck',self.run_case(health='NONE'))
 def test_stopped(self):self.assertIn('WARN | exists',self.run_case(running=False))
 def test_registry_port_is_not_tag(self):self.assertIn('FAIL | image',self.run_case(image='localhost:5000/app'))
 def test_image_inspection_failure(self):self.assertIn('WARN | ports',self.run_case(image_inspect=False))
 def test_null_bindings_not_published(self):self.assertIn('0 published port(s)',self.run_case(bindings={'80/tcp':None}))
 def test_extra_published_ports(self):self.assertIn('WARN | ports',self.run_case(bindings={'80/tcp':[{'HostPort':'80'}],'81/tcp':[{'HostPort':'81'}]}))
 def test_invalid_name(self):self.run_case(name='--help')
 def test_guard(self):
  for command,allowed in [('./run-audit.sh',True),('./inspect-container.sh 2>&1',True),('./run-audit.sh; docker stop app',False),('docker build .',False),('./run-audit.sh > Dockerfile',False),('bash ./run-audit.sh',False)]:
   r=subprocess.run(['python3',str(ROOT/'guard.py')],input=json.dumps({'tool_name':'Bash','tool_input':{'command':command}}),text=True,capture_output=True,env={**os.environ,'DMI_AUDIT_ROOT':str(ROOT)})
   self.assertEqual(r.returncode==0,allowed,command)
if __name__=='__main__':unittest.main()
