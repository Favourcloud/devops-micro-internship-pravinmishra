#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d /tmp/w09-a5-verify.XXXXXX)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/home" "$work/cache" "$work/ansible" "$root/.local"

export HOME="$work/home" TMPDIR="$work" XDG_CACHE_HOME="$work/cache"
export ANSIBLE_LOCAL_TEMP="$work/ansible" PYTHONDONTWRITEBYTECODE=1
export ANSIBLE_CONFIG="$root/ansible/ansible.cfg"
export TF_DATA_DIR="${TF_DATA_DIR:-$root/.local/terraform}"
export TF_CLI_CONFIG_FILE=/dev/null CHECKPOINT_DISABLE=1
export AZURE_CONFIG_DIR="$work/azure"
export ARM_USE_CLI=false ARM_USE_MSI=false ARM_USE_OIDC=false
unset ARM_CLIENT_ID ARM_CLIENT_SECRET ARM_TENANT_ID ARM_SUBSCRIPTION_ID ARM_OIDC_TOKEN ARM_CLIENT_CERTIFICATE_PATH

terraform_bin=${TERRAFORM_BIN:-terraform}
python_bin=${PYTHON_BIN:-python3}
export ANSIBLE_PLAYBOOK=${ANSIBLE_PLAYBOOK:-ansible-playbook}
ansible_lint=${ANSIBLE_LINT:-ansible-lint}

init_args=(-backend=false -input=false -lockfile=readonly -no-color)
if [[ -n "${TF_PROVIDER_MIRROR:-}" ]]; then
  init_args+=("-plugin-dir=$TF_PROVIDER_MIRROR")
fi

"$terraform_bin" -chdir="$root/terraform/azure" fmt -check -recursive
"$terraform_bin" -chdir="$root/terraform/azure" init "${init_args[@]}"
"$terraform_bin" -chdir="$root/terraform/azure" validate -no-color
# The test file uses only mock_provider; its apply/teardown never contacts Azure.
"$terraform_bin" -chdir="$root/terraform/azure" test -no-color
(
  cd "$root/ansible"
  "$ANSIBLE_PLAYBOOK" -i inventory.ini site.yml --syntax-check
  "$ansible_lint" --offline site.yml roles
)
"$python_bin" -m unittest discover -s "$root/tests" -v
printf '\nLocal preparation checks passed. No cloud, SSH, MySQL, Nginx or server idempotency verification performed.\n'
