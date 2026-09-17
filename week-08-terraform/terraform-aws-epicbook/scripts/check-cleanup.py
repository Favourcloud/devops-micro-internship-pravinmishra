#!/usr/bin/env python3
"""Validate a PRIVATE exact-ID cleanup ledger; this does not query AWS or prove deletion."""
import json
import sys


def check(inventory, observations):
    if not inventory.get('account') or not inventory.get('region'):
        raise ValueError('Private inventory needs the authorized account and Region')
    if any(observations.get(key) != inventory[key] for key in ('account', 'region')):
        raise ValueError('Reconfirmed account/Region does not match the provisioned inventory')
    expected = inventory.get('resources', [])
    found = observations.get('resources', [])
    if len(expected) != 28 or len(found) != len(expected):
        raise ValueError('This unchanged source requires 28 exact managed-resource observations')
    expected_pairs = {(row['address'], row['id']) for row in expected}
    found_pairs = {(row['address'], row['id']) for row in found}
    if len(expected_pairs) != 28 or expected_pairs != found_pairs or any(not row['id'] for row in expected):
        raise ValueError('Missing, duplicate or substituted resource identity')
    for row in found:
        if row.get('status') not in ('absent', 'terminated'):
            raise ValueError('Presence, timeout, AccessDenied and unrecognized errors are not deletion proof')
        if row['status'] == 'terminated' and not row['address'].endswith('aws_instance.this'):
            raise ValueError('Only EC2 has a terminated terminal state')
        if not row.get('checked_at') or not row.get('check'):
            raise ValueError('Every row needs a timestamp and exact read-only verification command')
    if observations.get('remaining_state_addresses') != []:
        raise ValueError('Terraform state is not confirmed empty')
    if observations.get('attached_ebs_absent') is not True or observations.get('db_snapshots_absent') is not True:
        raise ValueError('Also verify the recorded root EBS ID and DB snapshots/backups')


if __name__ == '__main__':
    try:
        with open(sys.argv[1]) as stream:
            inventory = json.load(stream)
        with open(sys.argv[2]) as stream:
            observations = json.load(stream)
        check(inventory, observations)
    except (ValueError, KeyError, IndexError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    print('Private ledger is internally consistent. Live CLI provenance and billing review remain human checks.')
