#!/usr/bin/env python3
"""Reduce Azure reads to a credential-free, fail-closed report."""
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import sys

def values(rule, single, plural):
    return rule.get(plural) or ([rule[single]] if rule.get(single) else [])

def port_matches(value, port):
    if value == '*': return True
    try:
        a, _, b = str(value).partition('-')
        return int(a) <= port <= int(b or a)
    except ValueError:
        return False

def internet_families(source):
    if source in ('*', 'Internet'): return {4, 6}
    try:
        network=ipaddress.ip_network(source, strict=False)
        return {network.version} if network.prefixlen == 0 else set()
    except ValueError:
        return set()

def audit(data):
    checks=[]
    def add(category, status, detail):
        checks.append(dict(check=category, status=status, evidence=detail))
    def valid(key):
        if not isinstance(data.get(key), list) or not data[key]:
            add(key, 'WARN', 'Required inventory absent or Azure read failed; not a PASS.')
            return False
        return True
    if valid('nsg'):
        findings=[]
        for nsg in data['nsg']:
            rules=sorted(nsg.get('securityRules',[])+nsg.get('defaultSecurityRules',[]),key=lambda r:r.get('priority',65536))
            for port in (22,3389):
                for protocol in ('Tcp','Udp'):
                    covered=set()
                    for rule in rules:
                        if rule.get('direction')!='Inbound' or rule.get('protocol','').lower() not in ('*',protocol.lower()): continue
                        if not any(port_matches(p,port) for p in values(rule,'destinationPortRange','destinationPortRanges')): continue
                        families=set().union(*(internet_families(s) for s in values(rule,'sourceAddressPrefix','sourceAddressPrefixes')))
                        remaining=families-covered
                        if rule.get('access')=='Allow' and remaining:
                            findings.append({'nsg':nsg['name'],'rule':rule['name'],'port':port,'protocol':protocol,'ip_families':sorted(remaining),'attached_nics':len(nsg.get('networkInterfaces',[])),'attached_subnets':len(nsg.get('subnets',[]))})
                        covered|=families
        add('nsg','FAIL' if findings else 'PASS',findings or 'No internet-wide SSH/RDP allow rule found in the required NSGs. This is a configuration check, not a complete effective-route audit.')
    if valid('storage'):
        rows=[{'name':x['name'],'allowBlobPublicAccess':x.get('allowBlobPublicAccess')} for x in data['storage']]
        status='FAIL' if any(x['allowBlobPublicAccess'] is True for x in rows) else ('WARN' if any(x['allowBlobPublicAccess'] is not False for x in rows) else 'PASS')
        add('storage',status,rows)
    if valid('disks'):
        rows=[{'name':x['name'],'encryption':x.get('encryption',{}).get('type'),'attached':bool(x.get('managedBy'))} for x in data['disks']]
        allowed={'EncryptionAtRestWithPlatformKey','EncryptionAtRestWithCustomerKey','EncryptionAtRestWithPlatformAndCustomerKeys'}
        status='WARN' if any(x['encryption'] is None for x in rows) else ('PASS' if all(x['encryption'] in allowed for x in rows) else 'FAIL')
        add('disks',status,rows)
    if valid('mysql'):
        rows=[{'name':x['name'],'publicNetworkAccess':(x.get('network') or {}).get('publicNetworkAccess'),'private_subnet_configured':bool((x.get('network') or {}).get('delegatedSubnetResourceId'))} for x in data['mysql']]
        status='FAIL' if any(x['publicNetworkAccess']=='Enabled' for x in rows) else ('PASS' if all(x['publicNetworkAccess']=='Disabled' and x['private_subnet_configured'] for x in rows) else 'WARN')
        add('mysql',status,rows)
    overall='FAIL' if any(x['status']=='FAIL' for x in checks) else ('WARN' if any(x['status']=='WARN' for x in checks) else 'PASS')
    return {'learner':'Eze Favour','operator':'Codex under learner delegation','captured_at':datetime.now(timezone.utc).isoformat(),'overall':overall,'checks':checks,'scope':'Week07 lab resource group + Mini Finance storage only','limitations':['No live remediation is executed by the audit.','Disk check verifies Azure managed-disk encryption, not guest ADE.','Storage static website remains intentionally public even when blob public access is disabled.','NSG check covers internet-wide administrative rules, not every partial public CIDR or effective flow.']}

def main():
    source,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
    report=audit({k:json.loads((source/(k+'.json')).read_text()) for k in ('nsg','storage','disks','mysql')})
    (out/'azure-audit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    text='Eze Favour — Week 07 Azure audit\n'+report['captured_at']+'\nOverall: '+report['overall']+'\n'
    for check in report['checks']:
        text+='\n['+check['status']+'] '+check['check']+'\n'+json.dumps(check['evidence'],indent=2)+'\n'
    (out/'azure-audit-report.txt').write_text(text)
    print(text)
    return {'PASS':0,'FAIL':1,'WARN':2}[report['overall']]

if __name__=='__main__': sys.exit(main())
