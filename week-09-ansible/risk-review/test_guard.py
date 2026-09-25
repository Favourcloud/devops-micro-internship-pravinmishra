import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        shutil.copy2(Path(__file__).with_name('guard.py'),self.root/'guard.py')
        (self.root/'reports').mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def decide(self,name,inputs):
        result=subprocess.run([sys.executable,str(self.root/'guard.py')],input=json.dumps({'tool_name':name,'tool_input':inputs,'cwd':str(self.root)}),capture_output=True,text=True,check=True)
        return json.loads(result.stdout)['hookSpecificOutput']

    def test_only_fixed_foreground_command_allowed(self):
        self.assertEqual(self.decide('Bash',{'command':'ansible-playbook site.yml'})['permissionDecision'],'deny')
        self.assertEqual(self.decide('Bash',{'command':'./run-review.sh; id'})['permissionDecision'],'deny')
        self.assertEqual(self.decide('Bash',{'command':'./run-review.sh','run_in_background':True})['permissionDecision'],'deny')
        result=self.decide('Bash',{'command':'./run-review.sh','timeout':1000})
        self.assertEqual(result['permissionDecision'],'allow')
        self.assertEqual(result['updatedInput']['timeout'],600000)

    def test_pending_report_cannot_be_treated_as_final(self):
        p=self.root/'reports/latest.json'
        p.write_text('{"status":"RUNNING"}')
        self.assertEqual(self.decide('Read',{'file_path':str(p)})['permissionDecision'],'deny')
        p.write_text('{"status":"LOW"}')
        self.assertEqual(self.decide('Read',{'file_path':str(p)})['permissionDecision'],'allow')

    def test_private_and_external_reads_denied(self):
        for p in [self.root/'input.private.json',self.root/'vault-password',Path('/etc/passwd')]:
            self.assertEqual(self.decide('Read',{'file_path':str(p)})['permissionDecision'],'deny')


if __name__=='__main__': unittest.main()
