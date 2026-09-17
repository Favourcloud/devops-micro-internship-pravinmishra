#!/usr/bin/env python3
"""Check installed provider write-only support; no provider/cloud methods are called."""
import json
import sys


def check(schema):
    resources = schema['provider_schemas']['registry.terraform.io/hashicorp/aws']['resource_schemas']
    for resource, attribute, version in (
        ('aws_db_instance', 'password_wo', 'password_wo_version'),
        ('aws_secretsmanager_secret_version', 'secret_string_wo', 'secret_string_wo_version'),
    ):
        fields = resources[resource]['block']['attributes']
        assert fields[attribute]['write_only'] is True
        assert fields[attribute]['sensitive'] is True
        assert fields[version]['type'] == 'number'


if __name__ == '__main__':
    with open(sys.argv[1]) as source:
        check(json.load(source))
    print('Installed AWS schema: both credential fields sensitive and write-only; numeric version fields present.')
