"""Called only by Terraform's opt-in, exact-instance termination resource."""
import datetime
import json
import os
from pathlib import Path
import subprocess


def aws(service, *arguments):
    result = subprocess.run(
        ['aws', service, *arguments, '--region', os.environ['AWS_REGION'], '--output', 'json'],
        check=True, capture_output=True, text=True,
        env={**os.environ, 'AWS_PAGER': ''},
    )
    return json.loads(result.stdout)


def validate_target(group, instance, targets, instance_id, vpc, name):
    if group['AutoScalingGroupName'] != name or group['DesiredCapacity'] != 2 or group['MinSize'] != 2:
        raise RuntimeError('Unexpected ASG identity/capacity; refusing fault injection')
    members = group['Instances']
    healthy = {target['Target']['Id'] for target in targets if target['TargetHealth']['State'] == 'healthy'}
    if len(members) != 2 or healthy != {member['InstanceId'] for member in members}:
        raise RuntimeError('Exactly two healthy ASG targets required before termination')
    if not any(member['InstanceId'] == instance_id for member in members):
        raise RuntimeError('Target is not a member of the lab ASG')
    if any(member['LifecycleState'] != 'InService' or member['HealthStatus'] != 'Healthy' for member in members):
        raise RuntimeError('ASG not stable; refusing fault injection')
    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
    if instance['InstanceId'] != instance_id or instance['VpcId'] != vpc or tags.get('Project') != name or instance['State']['Name'] != 'running':
        raise RuntimeError('Target identity/VPC/tag/state mismatch; refusing fault injection')


def main():
    instance_id = os.environ['INSTANCE_ID']
    group, = aws('autoscaling', 'describe-auto-scaling-groups', '--auto-scaling-group-names', os.environ['LAB_ASG'])['AutoScalingGroups']
    target_group, = group['TargetGroupARNs']
    targets = aws('elbv2', 'describe-target-health', '--target-group-arn', target_group)['TargetHealthDescriptions']
    reservations = aws('ec2', 'describe-instances', '--instance-ids', instance_id)['Reservations']
    instance, = [item for reservation in reservations for item in reservation['Instances']]
    validate_target(group, instance, targets, instance_id, os.environ['LAB_VPC'], os.environ['LAB_NAME'])
    report = {
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'action': 'Terraform-triggered EC2 termination of one exact ASG member after identity and health checks',
        'instance_id': instance_id, 'availability_zone': instance['Placement']['AvailabilityZone'],
        'vpc': os.environ['LAB_VPC'], 'asg': os.environ['LAB_ASG'],
        'desired_capacity_decremented': False,
        'fis_note': 'FIS template creation was denied with SubscriptionRequiredException; no FIS experiment ran.',
    }
    evidence = Path(__file__).resolve().parents[1] / 'evidence' / 'experiment.json'
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(report, indent=2) + '\n')
    response = aws('ec2', 'terminate-instances', '--instance-ids', instance_id)
    report['termination_response'] = response['TerminatingInstances']
    report['accepted_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    evidence.write_text(json.dumps(report, indent=2) + '\n')
    print('Termination accepted for exact verified lab instance:', instance_id)


if __name__ == '__main__':
    main()
