from concurrent.futures import ThreadPoolExecutor
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

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


class ActionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(
            dir=Path(__file__).parent, prefix='.test-experiment-',
        )))
        self.path = self.directory / 'run-one' / 'experiment.json'
        self.group = {
            'AutoScalingGroupName': 'lab', 'DesiredCapacity': 2, 'MinSize': 2,
            'TargetGroupARNs': ['lab-target-group'],
            'Instances': [{'InstanceId': name, 'LifecycleState': 'InService', 'HealthStatus': 'Healthy'}
                          for name in ['one', 'two']],
        }
        self.instances = {
            name: {'InstanceId': name, 'VpcId': 'lab-vpc', 'Tags': [{'Key': 'Project', 'Value': 'lab'}],
                   'State': {'Name': 'running'}, 'Placement': {'AvailabilityZone': zone}}
            for name, zone in [('one', 'az-a'), ('two', 'az-b')]
        }
        self.describe_barrier = None
        self.termination_hook = None
        self.enterContext(patch.dict(experiment.os.environ, {
            'INSTANCE_ID': 'one', 'LAB_VPC': 'lab-vpc', 'LAB_ASG': 'lab', 'LAB_NAME': 'lab',
            'AWS_REGION': 'us-east-1', 'ACTION_EVIDENCE_PATH': str(self.path),
        }, clear=True))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.enterContext(patch.object(experiment.subprocess, 'run', side_effect=AssertionError('No real AWS calls')))
        self.aws = self.enterContext(patch.object(experiment, 'aws', side_effect=self.aws_response))

    @staticmethod
    def termination_response(instance_id):
        return {'TerminatingInstances': [{'InstanceId': instance_id, 'CurrentState': {'Name': 'shutting-down'}}]}

    def aws_response(self, service, operation, *arguments):
        if (service, operation) == ('autoscaling', 'describe-auto-scaling-groups'):
            return {'AutoScalingGroups': [self.group]}
        if (service, operation) == ('elbv2', 'describe-target-health'):
            return {'TargetHealthDescriptions': [
                {'Target': {'Id': name}, 'TargetHealth': {'State': 'healthy'}} for name in self.instances
            ]}
        if (service, operation) == ('ec2', 'describe-instances'):
            if self.describe_barrier:
                self.describe_barrier.wait(timeout=5)
            return {'Reservations': [{'Instances': [self.instances[arguments[1]]]}]}
        if (service, operation) == ('ec2', 'terminate-instances'):
            if self.termination_hook:
                return self.termination_hook(arguments[1])
            return self.termination_response(arguments[1])
        self.fail(f'Unexpected AWS call: {service} {operation}')

    def invoke(self, instance_id, path):
        with patch.dict(experiment.os.environ, {'INSTANCE_ID': instance_id, 'ACTION_EVIDENCE_PATH': str(path)}):
            experiment.main()

    def termination_calls(self):
        return [call for call in self.aws.call_args_list if call.args[:2] == ('ec2', 'terminate-instances')]

    def test_requires_meaningful_destination_before_aws(self):
        for destination in [None, '', ' \t\n', '.', '..', '/', 'run/']:
            with self.subTest(destination=destination), patch.dict(experiment.os.environ):
                experiment.os.environ.pop('ACTION_EVIDENCE_PATH', None)
                if destination is not None:
                    experiment.os.environ['ACTION_EVIDENCE_PATH'] = destination
                with self.assertRaisesRegex(RuntimeError, 'fresh action evidence file'):
                    experiment.main()
                self.aws.assert_not_called()

    def test_different_instance_cannot_overwrite_reserved_action(self):
        self.invoke('one', self.path)
        original = self.path.read_bytes()
        self.aws.reset_mock()
        with self.assertRaises(FileExistsError):
            self.invoke('two', self.path)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(json.loads(original)['instance_id'], 'one')
        self.assertEqual(self.termination_calls(), [])

    def test_existing_historical_record_is_untouched(self):
        historical = self.directory / 'experiment.json'
        original = b'{"instance_id": "historical-instance", "accepted_at": "historical-timestamp"}\n'
        historical.write_bytes(original)
        with self.assertRaises(FileExistsError):
            self.invoke('two', historical)
        self.assertEqual(historical.read_bytes(), original)
        self.assertEqual(self.termination_calls(), [])

    def test_fresh_run_paths_work_independently(self):
        other = self.directory / 'run-two' / 'experiment.json'
        for instance_id, path in [('one', self.path), ('two', other)]:
            self.invoke(instance_id, path)
            report = json.loads(path.read_text())
            self.assertEqual(report['instance_id'], instance_id)
            self.assertEqual(report['termination_status'], 'accepted')
            self.assertEqual(report['termination_response'], self.termination_response(instance_id)['TerminatingInstances'])
            self.assertIn('accepted_at', report)
        self.assertEqual(len(self.termination_calls()), 2)
        self.assertEqual(json.loads(self.path.read_text())['instance_id'], 'one')

    def test_record_is_synced_before_termination(self):
        with patch.object(experiment.os, 'fsync', wraps=experiment.os.fsync) as sync:
            def terminate(instance_id):
                report = json.loads(self.path.read_text())
                self.assertEqual(report['termination_status'], 'prepared')
                self.assertEqual(report['instance_id'], instance_id)
                self.assertIn('started_at', report)
                self.assertNotIn('accepted_at', report)
                self.assertEqual(sync.call_count, 1)
                return self.termination_response(instance_id)

            self.termination_hook = terminate
            experiment.main()
        self.assertEqual(sync.call_count, 2)

    def test_concurrent_duplicates_allow_only_one_termination(self):
        self.describe_barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(experiment.main) for _ in range(2)]
            errors = [future.exception(timeout=10) for future in futures]
        self.assertEqual(errors.count(None), 1)
        self.assertEqual(sum(isinstance(error, FileExistsError) for error in errors), 1)
        self.assertEqual(len(self.termination_calls()), 1)
        self.assertEqual(json.loads(self.path.read_text())['termination_status'], 'accepted')

    def test_updates_only_the_reserved_file_descriptor(self):
        moved = self.directory / 'reserved-record.json'
        replacement = b'An unrelated record now occupies this pathname.\n'

        def terminate(instance_id):
            self.path.rename(moved)
            self.path.write_bytes(replacement)
            return self.termination_response(instance_id)

        self.termination_hook = terminate
        experiment.main()
        self.assertEqual(self.path.read_bytes(), replacement)
        self.assertEqual(json.loads(moved.read_text())['termination_status'], 'accepted')
        self.assertEqual(len(self.termination_calls()), 1)

    def test_existing_and_dangling_symlinks_are_refused(self):
        for exists in [True, False]:
            with self.subTest(existing_target=exists):
                target = self.directory / f'target-{exists}.json'
                link = self.directory / f'link-{exists}.json'
                if exists:
                    target.write_bytes(b'Historical evidence\n')
                link.symlink_to(target)
                with self.assertRaises(FileExistsError):
                    self.invoke('one', link)
                self.assertTrue(link.is_symlink())
                if exists:
                    self.assertEqual(target.read_bytes(), b'Historical evidence\n')
                else:
                    self.assertFalse(target.exists())
        self.assertEqual(self.termination_calls(), [])

    def test_aws_error_retains_unconfirmed_record_and_blocks_reuse(self):
        error = subprocess.CalledProcessError(255, ['aws'], stderr='private diagnostic')

        def terminate(_):
            raise error

        self.termination_hook = terminate
        with self.assertRaises(subprocess.CalledProcessError) as raised:
            experiment.main()
        self.assertIs(raised.exception, error)
        original = self.path.read_bytes()
        report = json.loads(original)
        self.assertEqual(report['termination_status'], 'unconfirmed')
        self.assertEqual(report['error'], 'CalledProcessError')
        self.assertIn('failed_at', report)
        self.assertNotIn('accepted_at', report)
        self.assertNotIn('private diagnostic', original.decode())
        with self.assertRaises(FileExistsError):
            self.invoke('two', self.path)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(len(self.termination_calls()), 1)

    def test_initial_sync_failure_prevents_termination_and_keeps_reservation(self):
        with patch.object(experiment.os, 'fsync', side_effect=OSError('Cannot persist record')):
            with self.assertRaises(OSError):
                experiment.main()
        self.assertTrue(self.path.exists())
        self.assertEqual(self.termination_calls(), [])
        with self.assertRaises(FileExistsError):
            experiment.main()
        self.assertEqual(self.termination_calls(), [])

    def test_directory_destination_prevents_termination(self):
        self.path.mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            experiment.main()
        self.assertTrue(self.path.is_dir())
        self.assertEqual(self.termination_calls(), [])

    def test_final_write_failure_does_not_retry_termination_or_release_record(self):
        write_report = experiment.write_report

        def fail_update(record, report):
            if report['termination_status'] == 'accepted':
                raise OSError('Cannot update record')
            write_report(record, report)

        with patch.object(experiment, 'write_report', side_effect=fail_update):
            with self.assertRaises(OSError):
                experiment.main()
        self.assertEqual(json.loads(self.path.read_text())['termination_status'], 'prepared')
        with self.assertRaises(FileExistsError):
            experiment.main()
        self.assertEqual(len(self.termination_calls()), 1)

    def test_invalid_target_never_reserves_or_terminates(self):
        self.instances['one']['VpcId'] = 'another-vpc'
        with self.assertRaisesRegex(RuntimeError, 'mismatch'):
            experiment.main()
        self.assertFalse(self.path.exists())
        self.assertEqual(self.termination_calls(), [])

    def test_shell_metacharacters_in_path_are_literal(self):
        path = self.directory / 'run $(not-a-command); "$literal"' / 'experiment.json'
        self.invoke('one', path)
        self.assertEqual(json.loads(path.read_text())['termination_status'], 'accepted')
        self.assertEqual(len(self.termination_calls()), 1)


if __name__ == '__main__':
    unittest.main()
