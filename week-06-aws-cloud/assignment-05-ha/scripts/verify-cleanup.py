"""Read-only verification for the recorded dmi-a5-ha run and preserved Assignment 4."""
import datetime
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
NAME = 'dmi-a5-ha'
REGION = 'us-east-1'


def aws(service, operation, *arguments, query):
    result = subprocess.run(['aws', service, operation, *arguments, '--region', REGION, '--query', query, '--output', 'json'],
                            check=True, capture_output=True, text=True, env={**os.environ, 'AWS_PAGER': ''})
    return json.loads(result.stdout)


def main():
    state = subprocess.run([os.environ.get('TF_BIN', 'terraform'), f'-chdir={ROOT / "terraform"}', 'state', 'list'],
                           check=True, capture_output=True, text=True)
    assert not state.stdout.strip(), 'Terraform state still has resources'
    report = {'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'terraform_state_empty': True}
    remaining = {
        'vpcs': aws('ec2', 'describe-vpcs', '--filters', f'Name=tag:Project,Values={NAME}', query='Vpcs[].VpcId'),
        'subnets': aws('ec2', 'describe-subnets', '--filters', f'Name=tag:Project,Values={NAME}', query='Subnets[].SubnetId'),
        'security_groups': aws('ec2', 'describe-security-groups', '--filters', f'Name=tag:Project,Values={NAME}', query='SecurityGroups[].GroupId'),
        'elastic_ips': aws('ec2', 'describe-addresses', '--filters', f'Name=tag:Project,Values={NAME}', query='Addresses[].AllocationId'),
        'active_instances': aws('ec2', 'describe-instances', '--filters', f'Name=tag:Project,Values={NAME}', 'Name=instance-state-name,Values=pending,running,stopping,stopped', query='Reservations[].Instances[].InstanceId'),
        'asgs': aws('autoscaling', 'describe-auto-scaling-groups', '--auto-scaling-group-names', NAME, query='AutoScalingGroups[].AutoScalingGroupName'),
        'databases': aws('rds', 'describe-db-instances', query=f'DBInstances[?DBInstanceIdentifier==`{NAME}`].DBInstanceIdentifier'),
        'load_balancers': aws('elbv2', 'describe-load-balancers', query=f'LoadBalancers[?LoadBalancerName==`{NAME}`].LoadBalancerName'),
        'log_groups': aws('logs', 'describe-log-groups', '--log-group-name-prefix', f'/aws/rds/instance/{NAME}/error', query='logGroups[].logGroupName'),
        'iam_roles': aws('iam', 'list-roles', query=f'Roles[?starts_with(RoleName, `{NAME}-`)].RoleName'),
        'instance_profiles': aws('iam', 'list-instance-profiles', query=f'InstanceProfiles[?starts_with(InstanceProfileName, `{NAME}-`)].InstanceProfileName'),
        'launch_templates': aws('ec2', 'describe-launch-templates', '--filters', f'Name=tag:Project,Values={NAME}', query='LaunchTemplates[].LaunchTemplateId'),
        'active_nat_gateways': aws('ec2', 'describe-nat-gateways', '--filter', f'Name=tag:Project,Values={NAME}', query='NatGateways[?State!=`deleted`].NatGatewayId'),
        'internet_gateways': aws('ec2', 'describe-internet-gateways', '--filters', f'Name=tag:Project,Values={NAME}', query='InternetGateways[].InternetGatewayId'),
        'route_tables': aws('ec2', 'describe-route-tables', '--filters', f'Name=tag:Project,Values={NAME}', query='RouteTables[].RouteTableId'),
        'target_groups': aws('elbv2', 'describe-target-groups', query=f'TargetGroups[?TargetGroupName==`{NAME}`].TargetGroupName'),
        'db_subnet_groups': aws('rds', 'describe-db-subnet-groups', query=f'DBSubnetGroups[?DBSubnetGroupName==`{NAME}-private`].DBSubnetGroupName'),
        'db_parameter_groups': aws('rds', 'describe-db-parameter-groups', query=f'DBParameterGroups[?starts_with(DBParameterGroupName, `{NAME}-`)].DBParameterGroupName'),
    }
    assert all(not items for items in remaining.values()), remaining
    report['remaining_lab_resources'] = remaining
    original_ec2 = aws('ec2', 'describe-instances', '--instance-ids', 'i-056d7d7f615dc4bfd', query='Reservations[].Instances[].{Id:InstanceId,State:State.Name,Vpc:VpcId}')
    original_db = aws('rds', 'describe-db-instances', '--db-instance-identifier', 'epicbook-db', query='DBInstances[].{Name:DBInstanceIdentifier,Status:DBInstanceStatus,Public:PubliclyAccessible,MultiAZ:MultiAZ}')
    assert original_ec2[0]['State'] == 'running' and original_ec2[0]['Vpc'] == 'vpc-092b56242a6f75ccf'
    assert original_db[0]['Status'] == 'available' and not original_db[0]['Public'] and not original_db[0]['MultiAZ']
    report['assignment_four_preserved'] = {'ec2': original_ec2, 'database': original_db}
    report['note'] = 'Temporary lab removed; Assignment 4 remains running and can incur charges. Billing can lag deletion.'
    (ROOT / 'evidence' / 'cleanup.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
