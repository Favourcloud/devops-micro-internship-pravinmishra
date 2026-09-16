"""Render actual redacted CLI evidence as static HTML, not imitation AWS Console screenshots."""
import html
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1] / 'evidence'
STYLE = '''body{font:16px/1.5 system-ui,sans-serif;background:#f3f6fa;color:#17283a;margin:0;padding:32px}main{max-width:1160px;margin:auto;background:white;padding:28px;border-radius:12px}h1,h2{color:#163f62}table{border-collapse:collapse;width:100%;margin:18px 0}td,th{border:1px solid #bbc9d6;text-align:left;padding:9px;overflow-wrap:anywhere}th{background:#e6eef5}code{overflow-wrap:anywhere}.note{padding:16px;background:#fff1d4;border-left:5px solid #b77500}small{color:#42586d}pre{white-space:pre-wrap;overflow-wrap:anywhere}'''


def esc(value):
    return html.escape(str(value))


def load(name):
    return json.loads((EVIDENCE / name).read_text())


def table(headers, rows):
    return '<table><thead><tr>' + ''.join('<th>' + esc(cell) + '</th>' for cell in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(cell) + '</td>' for cell in row) + '</tr>' for row in rows) + '</tbody></table>'


def page(title, content):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + esc(title) + '</title><style>' + STYLE + '</style><main><h1>' + esc(title) + '</h1><p class="note">Real AWS CLI evidence rendered for readability. This is not the AWS Console. Account IDs are redacted. Captures describe the recorded test time, not a currently live deployment.</p>' + content + '</main></html>'


def architecture():
    snapshot = load('baseline.json')
    db, = snapshot['database']
    secondary_az = db['SecondaryAZ'] or 'Not yet reported; confirmed in test-a-after.json'
    alb, = snapshot['load_balancers']
    group, = snapshot['asg']
    content = '<p>Source: <code>baseline.json</code> · UTC capture: ' + esc(snapshot['observed_at']) + '</p>'
    content += '<h2>Network</h2><p>VPC: ' + esc(snapshot['vpc']) + ' · Region: ' + esc(snapshot['region']) + '</p>'
    content += table(['Subnet', 'CIDR', 'AZ', 'Tier'], [[subnet['Id'], subnet['Cidr'], subnet['AZ'], 'Public' if subnet['PublicIP'] else 'Private'] for subnet in snapshot['subnets']])
    content += table(['Route table', 'Associated subnet', 'Default route'], [[route_table['Id'], ', '.join(association.get('SubnetId', 'Main') for association in route_table['Associations']), ', '.join(route.get('NatGatewayId', route.get('GatewayId', '')) for route in route_table['Routes'] if route.get('DestinationCidrBlock') == '0.0.0.0/0')] for route_table in snapshot['routes']])
    content += '<p>NAT: ' + esc(snapshot['nat'][0]['State']) + ' (one zonal gateway; not redundant egress).</p>'
    content += '<h2>Security groups</h2>'
    rows = []
    for security_group in snapshot['security_groups']:
        if security_group['Name'] == 'default':
            continue
        for rule in security_group['Ingress']:
            sources = [source['CidrIp'] for source in rule['IpRanges']] + [source['GroupId'] for source in rule['UserIdGroupPairs']]
            rows.append([security_group['Name'], rule.get('FromPort'), ', '.join(sources)])
    content += table(['Group', 'Inbound TCP port', 'Only allowed source'], rows)
    content += '<p>SSH closed; SSM administration. IMDSv2 required. Database TLS enforced.</p>'
    content += '<h2>Database and web tier</h2>'
    content += table(['Setting', 'Observed value'], [['Database', db['Name']], ['Engine', db['Engine'] + ' ' + db['Version']], ['Multi-AZ / public / encrypted', f"{db['MultiAZ']} / {db['Public']} / {db['Encrypted']}"], ['Primary / secondary AZ', db['AZ'] + ' / ' + secondary_az], ['Database status', db['Status']], ['ALB state / scheme', alb['State']['Code'] + ' / ' + alb['Scheme']], ['ALB DNS', alb['DNS']], ['ASG min / desired / max', f"{group['Min']} / {group['Desired']} / {group['Max']}"]])
    content += table(['Instance', 'AZ', 'ASG state', 'Health'], [[instance['InstanceId'], instance['AvailabilityZone'], instance['LifecycleState'], instance['HealthStatus']] for instance in group['Instances']])
    content += '<p>Architecture invariants verified by <code>verify-snapshot.py</code>. Passwords and user data are excluded.</p>'
    (EVIDENCE / 'architecture-evidence.html').write_text(page('Assignment 5 — verified HA architecture', content))


def availability():
    action = load('experiment.json')
    summary_a = load('test-a-probes.summary.json')
    summary_b = load('test-b-probes.summary.json')
    content = table(['Test', 'Successful probes', 'Failed probes', 'Interpretation'], [['A: abrupt instance termination', summary_a['successes'], summary_a['failures'], 'Automatic recovery; zero downtime NOT demonstrated'], ['B: controlled web-tier AZ evacuation and restoration', summary_b['successes'], summary_b['failures'], 'Sampled availability only; not a real AZ outage or DB failover']])
    content += '<p>Probe: <code>GET /ready</code> (database query), one-second spacing, five-second timeout, no retries. Sampling does not prove continuous availability.</p>'
    content += '<h2>Test A action</h2>' + table(['Field', 'Observed value'], [[key, action[key]] for key in ['started_at', 'accepted_at', 'instance_id', 'availability_zone', 'asg']])
    failures = [json.loads(line) for line in (EVIDENCE / 'test-a-probes.jsonl').read_text().splitlines() if not json.loads(line)['ok']]
    content += table(['Failed sample (UTC)', 'HTTP status', 'Duration ms'], [[row['timestamp'], row['status'], row['duration_ms']] for row in failures])
    content += '<h2>Verified recovery and evacuation</h2>'
    rows = []
    for name in ['baseline.json', 'test-a-after.json', 'test-b-evacuated.json', 'recovered.json']:
        snapshot = load(name)
        for instance in snapshot['asg'][0]['Instances']:
            rows.append([name, snapshot['observed_at'], instance['InstanceId'], instance['AvailabilityZone'], instance['HealthStatus']])
    content += table(['Evidence source', 'UTC capture', 'Instance', 'AZ', 'Health'], rows)
    content += '<p>FIS subscription was unavailable; the actual termination ran through a guarded Terraform provisioner. Assignment 4 resources were excluded.</p>'
    (EVIDENCE / 'availability-evidence.html').write_text(page('Assignment 5 — measured failure-test results', content))


if __name__ == '__main__':
    architecture()
    if (EVIDENCE / 'recovered.json').exists() and (EVIDENCE / 'test-b-probes.summary.json').exists():
        availability()
