import tempfile
from pathlib import Path
import unittest
from review import inspect_source, summarize

class ReviewTests(unittest.TestCase):
    def test_clean_complete_report(self):
        result=summarize({'schema':1,'complete':True,'recap':{'web':{'changed':0,'failures':0,'unreachable':0}},'changed_tasks':[]},0)
        self.assertEqual(result['status'],'LOW')

    def test_partial_and_failed_outputs_never_healthy(self):
        for event,rc in [({},0),({'schema':1,'complete':True,'recap':{'web':{'changed':0,'failures':1}}},0),({'schema':1,'complete':True,'recap':{'web':{'changed':0}}},2)]:
            self.assertEqual(summarize(event,rc)['status'],'ERROR')

    def test_multi_host_task_counts_once_and_lists_both_hosts(self):
        task={'task':'Remove lab marker','categories':['package_file_removal'],'hosts':['web1','web2']}
        result=summarize({'schema':1,'complete':True,'recap':{h:{'changed':1} for h in task['hosts']},'changed_tasks':[task]},0)
        self.assertEqual(result['status'],'HOLD')
        self.assertEqual(result['changed_task_count'],1)
        self.assertEqual(result['categories']['package_file_removal'][0]['hosts'],['web1','web2'])

    def test_unmatched_change_is_held(self):
        result=summarize({'schema':1,'complete':True,'recap':{'web':{'changed':1}},'changed_tasks':[{'categories':[],'hosts':['web']}]},0)
        self.assertEqual(result['status'],'HOLD')
        self.assertEqual(len(result['unmatched_changes']),1)

    def test_missing_callback_change_is_an_error(self):
        result=summarize({'schema':1,'complete':True,'recap':{'web':{'changed':1}},'changed_tasks':[]},0)
        self.assertEqual(result['status'],'ERROR')

    def test_explicit_check_mode_bypass_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'site.yml'
            p.write_text('- hosts: all\n  tasks:\n    - command: true\n      check_mode: false\n')
            with self.assertRaises(ValueError): inspect_source(Path(directory))

if __name__=='__main__': unittest.main()
