"""Capture selected AWS evidence without credentials, user data or account IDs."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def command(arguments):
    result = subprocess.run(arguments, capture_output=True, text=True, check=True,
                            env={**os.environ, 'AWS_PAGER': ''})
    return json.loads(result.stdout)


def outputs():
    data = command([os.environ.get('TF_BIN', 'terraform'), f'-chdir={ROOT / "terraform"}', 'output', '-json'])
    return {key: value['value'] for key, value in data.items()}


def capture(region):
    out = outputs()

    def aws(service, operation, *arguments, query):
        return command(['aws', service, operation, '--region', region, *arguments,
                        '--query', query, '--output', 'json'])

    asg = aws('autoscaling', 'describe-auto-scaling-groups', '--auto-scaling-group-names', out['asg_name'],
              query='AutoScalingGroups[].{Name:AutoScalingGroupName,Min:MinSize,Desired:DesiredCapacity,Max:MaxSize,Subnets:VPCZoneIdentifier,TargetGroups:TargetGroupARNs,Instances:Instances,HealthCheckType:HealthCheckType,Template:LaunchTemplate}')
    instance_ids = [item['InstanceId'] for group in asg for item in group['Instances']]
    result = {
        'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'region': region, 'url': out['url'], 'vpc': out['vpc_id'], 'asg': asg,
        'instances': aws('ec2', 'describe-instances', '--instance-ids', *instance_ids,
                         query='Reservations[].Instances[].{Id:InstanceId,State:State.Name,AZ:Placement.AvailabilityZone,Subnet:SubnetId,Vpc:VpcId,Groups:SecurityGroups,Template:LaunchTemplate,Image:ImageId,IMDS:MetadataOptions}') if instance_ids else [],
        'targets': aws('elbv2', 'describe-target-health', '--target-group-arn', out['target_group_arn'], query='TargetHealthDescriptions'),
        'database': aws('rds', 'describe-db-instances', '--db-instance-identifier', out['database_identifier'],
                        query='DBInstances[].{Name:DBInstanceIdentifier,Status:DBInstanceStatus,Engine:Engine,Version:EngineVersion,MultiAZ:MultiAZ,Public:PubliclyAccessible,Encrypted:StorageEncrypted,AZ:AvailabilityZone,SecondaryAZ:SecondaryAvailabilityZone,SubnetGroup:DBSubnetGroup,Groups:VpcSecurityGroups,Parameters:DBParameterGroups,Backups:BackupRetentionPeriod,ManagedSecretStatus:MasterUserSecret.SecretStatus}'),
        'subnets': aws('ec2', 'describe-subnets', '--filters', f'Name=vpc-id,Values={out["vpc_id"]}',
                       query='Subnets[].{Id:SubnetId,Cidr:CidrBlock,AZ:AvailabilityZone,PublicIP:MapPublicIpOnLaunch,Name:Tags[?Key==`Name`].Value|[0]}'),
        'routes': aws('ec2', 'describe-route-tables', '--filters', f'Name=vpc-id,Values={out["vpc_id"]}',
                      query='RouteTables[].{Id:RouteTableId,Routes:Routes,Associations:Associations}'),
        'security_groups': aws('ec2', 'describe-security-groups', '--filters', f'Name=vpc-id,Values={out["vpc_id"]}',
                               query='SecurityGroups[].{Id:GroupId,Name:GroupName,Vpc:VpcId,Ingress:IpPermissions,Egress:IpPermissionsEgress}'),
        'nat': aws('ec2', 'describe-nat-gateways', '--filter', f'Name=vpc-id,Values={out["vpc_id"]}',
                   query='NatGateways[].{Id:NatGatewayId,State:State,Subnet:SubnetId,Connectivity:ConnectivityType}'),
        'activities': aws('autoscaling', 'describe-scaling-activities', '--auto-scaling-group-name', out['asg_name'], '--max-items', '30',
                          query='Activities[].{Description:Description,Start:StartTime,End:EndTime,Status:StatusCode,Cause:Cause}'),
    }
    lbs = aws('elbv2', 'describe-load-balancers', '--names', out['asg_name'],
              query='LoadBalancers[].{Arn:LoadBalancerArn,DNS:DNSName,Scheme:Scheme,State:State,Vpc:VpcId,AZs:AvailabilityZones,Groups:SecurityGroups}')
    result['load_balancers'] = lbs
    result['listeners'] = aws('elbv2', 'describe-listeners', '--load-balancer-arn', lbs[0]['Arn'],
                               query='Listeners[].{Port:Port,Protocol:Protocol,Actions:DefaultActions}')
    return json.loads(re.sub(r'(?<!\d)\d{12}(?!\d)', '[REDACTED]', json.dumps(result)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--region', default='us-east-1')
    args = parser.parse_args()
    result = capture(args.region)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Saved redacted snapshot:', args.output)


if __name__ == '__main__':
    main()
