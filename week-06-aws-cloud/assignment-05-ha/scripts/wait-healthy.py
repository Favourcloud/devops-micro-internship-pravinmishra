"""Wait for exactly two healthy ASG instances and the requested AZ count."""
import argparse
import datetime
import json
import os
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='dmi-a5-ha')
    parser.add_argument('--region', default='us-east-1')
    parser.add_argument('--az-count', type=int, choices=[1, 2], default=2)
    parser.add_argument('--exclude-instance', action='append', default=[])
    parser.add_argument('--timeout', type=int, default=1200)
    args = parser.parse_args()

    def aws(service, operation, *parameters):
        response = subprocess.run(['aws', service, operation, *parameters, '--region', args.region, '--output', 'json'],
                                  capture_output=True, text=True, check=True, env={**os.environ, 'AWS_PAGER': ''})
        return json.loads(response.stdout)

    deadline = time.monotonic() + args.timeout
    stable = 0
    while time.monotonic() < deadline:
        groups = aws('autoscaling', 'describe-auto-scaling-groups', '--auto-scaling-group-names', args.name)['AutoScalingGroups']
        if not groups:
            raise RuntimeError('Lab ASG not found')
        group = groups[0]
        instances = group['Instances']
        healthy = []
        if group['TargetGroupARNs']:
            targets = aws('elbv2', 'describe-target-health', '--target-group-arn', group['TargetGroupARNs'][0])['TargetHealthDescriptions']
            healthy = [target['Target']['Id'] for target in targets if target['TargetHealth']['State'] == 'healthy']
        ready = (len(instances) == 2 and len(healthy) == 2
                 and len({instance['AvailabilityZone'] for instance in instances}) == args.az_count
                 and all(instance['LifecycleState'] == 'InService' and instance['HealthStatus'] == 'Healthy'
                         and instance['InstanceId'] in healthy and instance['InstanceId'] not in args.exclude_instance
                         for instance in instances))
        stable = stable + 1 if ready else 0
        if stable >= 3:
            print(json.dumps({'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                              'healthy_instance_ids': healthy, 'availability_zones': sorted({instance['AvailabilityZone'] for instance in instances})}))
            return
        time.sleep(15)
    raise TimeoutError('Two healthy ASG instances with the requested AZ layout were not observed')


if __name__ == '__main__':
    main()
