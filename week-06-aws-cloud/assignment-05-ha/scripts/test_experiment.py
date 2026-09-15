import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('experiment', Path(__file__).with_name('run-experiment.py'))
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


class TerminationGuardTests(unittest.TestCase):
    def setUp(self):
        self.group = {'AutoScalingGroupName': 'lab', 'DesiredCapacity': 2, 'MinSize': 2,
                      'Instances': [{'InstanceId': name, 'LifecycleState': 'InService', 'HealthStatus': 'Healthy'} for name in ['one', 'two']]}
        self.instance = {'InstanceId': 'one', 'VpcId': 'lab-vpc', 'Tags': [{'Key': 'Project', 'Value': 'lab'}], 'State': {'Name': 'running'}}
        self.targets = [{'Target': {'Id': name}, 'TargetHealth': {'State': 'healthy'}} for name in ['one', 'two']]

    def validate(self):
        experiment.validate_target(self.group, self.instance, self.targets, 'one', 'lab-vpc', 'lab')

    def test_accepts_only_stable_matching_lab_target(self):
        self.validate()

    def test_rejects_different_vpc(self):
        self.instance['VpcId'] = 'assignment-four'
        with self.assertRaises(RuntimeError):
            self.validate()

    def test_rejects_missing_project_tag(self):
        self.instance['Tags'] = []
        with self.assertRaises(RuntimeError):
            self.validate()

    def test_rejects_wrong_asg(self):
        self.group['AutoScalingGroupName'] = 'assignment-four'
        with self.assertRaises(RuntimeError):
            self.validate()

    def test_rejects_unhealthy_survivor(self):
        self.targets[1]['TargetHealth']['State'] = 'unhealthy'
        with self.assertRaises(RuntimeError):
            self.validate()

    def test_rejects_non_member(self):
        self.group['Instances'][0]['InstanceId'] = 'another'
        self.targets[0]['Target']['Id'] = 'another'
        with self.assertRaises(RuntimeError):
            self.validate()

    def test_rejects_capacity_change(self):
        self.group['DesiredCapacity'] = 1
        with self.assertRaises(RuntimeError):
            self.validate()

    def test_rejects_unstable_asg(self):
        self.group['Instances'][1]['LifecycleState'] = 'Pending'
        with self.assertRaises(RuntimeError):
            self.validate()


if __name__ == '__main__':
    unittest.main()
