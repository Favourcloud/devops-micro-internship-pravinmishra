#!/usr/bin/env python3
"""Refuse local inputs/overrides before Terraform can implicitly load them."""
from pathlib import Path
import sys


def check(project):
    for path in project.rglob('*'):
        name = path.name
        if path.is_symlink():
            raise ValueError('Symlinks are forbidden in the offline source tree')
        if (name.endswith(('.tfvars', '.tfvars.json', '.tfstate', '.tfplan', '.pem', '.key'))
                or name.startswith('terraform.tfstate') or name == 'override.tf'
                or name == 'override.tf.json' or name.endswith(('_override.tf', '_override.tf.json'))
                or name in ('.terraform', '.private')):
            raise ValueError('Private inputs, state, overrides or initialized trees are forbidden offline')


if __name__ == '__main__':
    try:
        check(Path(sys.argv[1]))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
