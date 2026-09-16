#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export ANSIBLE_CONFIG="$project_dir/ansible.cfg"
export ANSIBLE_HOME="$project_dir/.ansible"
export PATH="$project_dir/.venv/bin:$PATH"

case "${1:-}" in
  yamllint)
    exec "$project_dir/.venv/bin/yamllint" --strict .
    ;;
  ansible-lint)
    exec "$project_dir/.venv/bin/ansible-lint" --offline playbooks/
    ;;
  *)
    printf 'Usage: bash scripts/lint.sh {yamllint|ansible-lint}\n' >&2
    exit 2
    ;;
esac
