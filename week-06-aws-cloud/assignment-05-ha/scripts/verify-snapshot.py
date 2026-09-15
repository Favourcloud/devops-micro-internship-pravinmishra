"""Assert HA architecture invariants against a redacted AWS snapshot."""
import argparse
import json
from pathlib import Path


def verify(snapshot, web_az_count):
    vpc = snapshot['vpc']
    subnets = snapshot['subnets']
    assert len(subnets) == 4
    public = [subnet for subnet in subnets if subnet['PublicIP']]
    private = [subnet for subnet in subnets if not subnet['PublicIP']]
    assert len(public) == len(private) == 2
    assert len({subnet['AZ'] for subnet in public}) == len({subnet['AZ'] for subnet in private}) == 2
    for tier, gateway in [(public, 'GatewayId'), (private, 'NatGatewayId')]:
        for subnet in tier:
            tables = [table for table in snapshot['routes'] if any(association.get('SubnetId') == subnet['Id'] for association in table['Associations'])]
            assert len(tables) == 1
            assert any(route.get('DestinationCidrBlock') == '0.0.0.0/0' and route.get(gateway) and route['State'] == 'active' for route in tables[0]['Routes'])
    assert len(snapshot['nat']) == 1 and snapshot['nat'][0]['State'] == 'available'
    database, = snapshot['database']
    assert database['MultiAZ'] and not database['Public'] and database['Encrypted']
    assert database['Status'] == 'available' and database['ManagedSecretStatus'] == 'active'
    assert database['SubnetGroup']['VpcId'] == vpc
    assert {subnet['SubnetIdentifier'] for subnet in database['SubnetGroup']['Subnets']} == {subnet['Id'] for subnet in private}
    private_azs = {subnet['AZ'] for subnet in private}
    assert database['AZ'] in private_azs
    if database['SecondaryAZ'] is not None:
        assert database['SecondaryAZ'] in private_azs and database['AZ'] != database['SecondaryAZ']
    asg, = snapshot['asg']
    assert (asg['Min'], asg['Desired'], asg['Max']) == (2, 2, 4)
    assert len(asg['Instances']) == 2
    assert len({instance['AvailabilityZone'] for instance in asg['Instances']}) == web_az_count
    assert all(instance['LifecycleState'] == 'InService' and instance['HealthStatus'] == 'Healthy' for instance in asg['Instances'])
    healthy_ids = {target['Target']['Id'] for target in snapshot['targets'] if target['TargetHealth']['State'] == 'healthy'}
    assert healthy_ids == {instance['InstanceId'] for instance in asg['Instances']}
    lb, = snapshot['load_balancers']
    assert lb['State']['Code'] == 'active' and lb['Scheme'] == 'internet-facing' and lb['Vpc'] == vpc
    assert {zone['SubnetId'] for zone in lb['AZs']} == {subnet['Id'] for subnet in public}
    listener, = snapshot['listeners']
    assert listener['Port'] == 80 and listener['Protocol'] == 'HTTP'
    assert listener['Actions'][0]['TargetGroupArn'] in asg['TargetGroups']
    groups = {group['Id']: group for group in snapshot['security_groups']}
    alb_group, = lb['Groups']
    web_groups = {group['GroupId'] for instance in snapshot['instances'] for group in instance['Groups']}
    assert len(web_groups) == 1
    web_group, = web_groups
    db_group, = [group['VpcSecurityGroupId'] for group in database['Groups']]
    for destination, source, port in [(web_group, alb_group, 80), (db_group, web_group, 3306)]:
        group = groups[destination]
        assert group['Vpc'] == vpc
        rule, = group['Ingress']
        assert rule['IpProtocol'] == 'tcp' and rule['FromPort'] == rule['ToPort'] == port
        assert not rule['IpRanges'] and not rule['Ipv6Ranges']
        assert {pair['GroupId'] for pair in rule['UserIdGroupPairs']} == {source}
    assert all(instance['Vpc'] == vpc and instance['IMDS']['HttpTokens'] == 'required' for instance in snapshot['instances'])
    return {'architecture': 'passed', 'web_az_count': web_az_count, 'healthy_targets': len(healthy_ids), 'secondary_az_reported': database['SecondaryAZ'] is not None, 'observed_at': snapshot['observed_at']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--web-az-count', type=int, choices=[1, 2], default=2)
    args = parser.parse_args()
    print(json.dumps(verify(json.loads(args.snapshot.read_text()), args.web_az_count)))


if __name__ == '__main__':
    main()
