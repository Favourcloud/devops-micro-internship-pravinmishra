#!/bin/bash
set -Eeuo pipefail
umask 077
: "${TERRAFORM_BIN:?Set an existing absolute Terraform 1.13.5 executable}"
: "${AWS_PROVIDER_MIRROR:?Set an existing AWS 6.64.0 filesystem mirror root}"
case "$TERRAFORM_BIN" in /*) ;; *) echo 'Terraform path must be absolute' >&2; exit 2 ;; esac
case "$AWS_PROVIDER_MIRROR" in /*) ;; *) echo 'Mirror path must be absolute' >&2; exit 2 ;; esac
case "$AWS_PROVIDER_MIRROR" in *'"'*|*'\'*|*$'\n'*) echo 'Unsupported mirror path' >&2; exit 2 ;; esac
[ -x "$TERRAFORM_BIN" ] || { echo 'Missing Terraform' >&2; exit 2; }
[ -d "$AWS_PROVIDER_MIRROR/registry.terraform.io/hashicorp/aws/6.64.0" ] || { echo 'Missing locked provider' >&2; exit 2; }
project=$(cd "$(dirname "$0")/.." && pwd)
python3 "$project/scripts/offline-preflight.py" "$project"
scratch=$(mktemp -d /tmp/dmi-a4-XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
mkdir -m 700 "$scratch/home" "$scratch/data" "$scratch/tmp"
cat > "$scratch/terraform.rc" <<EOF
provider_installation {
  filesystem_mirror {
    path = "$AWS_PROVIDER_MIRROR"
    include = ["registry.terraform.io/hashicorp/aws"]
  }
}
EOF
terraform_offline() {
  env -i PATH=/usr/bin:/bin HOME="$scratch/home" TMPDIR="$scratch/tmp" \
    TF_DATA_DIR="$scratch/data" TF_CLI_CONFIG_FILE="$scratch/terraform.rc" \
    TF_IN_AUTOMATION=1 TF_INPUT=0 CHECKPOINT_DISABLE=1 \
    AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null \
    AWS_SHARED_CREDENTIALS_FILE=/dev/null BOTO_CONFIG=/dev/null \
    "$TERRAFORM_BIN" -chdir="$project" "$@"
}
terraform_offline version
terraform_offline fmt -check -recursive
terraform_offline init -backend=false -lockfile=readonly -input=false -no-color
terraform_offline validate -no-color
terraform_offline providers schema -json > "$scratch/schema.json"
python3 "$project/scripts/check-schema.py" "$scratch/schema.json"
terraform_offline test -test-directory=tests -no-color
bash -n "$project/modules/ec2/user_data.sh" "$project/scripts/check-offline.sh"
env -i PATH="$PATH" HOME="$scratch/home" TMPDIR="$scratch/tmp" PYTHONDONTWRITEBYTECODE=1 \
  AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null \
  python3 -m unittest discover -s "$project/tests" -p 'test_*.py' -v
printf '\nOFFLINE ONLY: validation passed; no real cloud plan/apply, runtime or screenshot proof.\n'
