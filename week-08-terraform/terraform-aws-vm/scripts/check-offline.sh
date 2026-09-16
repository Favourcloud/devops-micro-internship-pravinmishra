#!/bin/bash
set -Eeuo pipefail
umask 077

# The caller supplies installed tools; never install or download providers here.
: "${TERRAFORM_BIN:?Set TERRAFORM_BIN to an existing absolute Terraform 1.13.x executable}"
: "${AWS_PROVIDER_MIRROR:?Set AWS_PROVIDER_MIRROR to an existing filesystem mirror root}"
case "$TERRAFORM_BIN" in /*) ;; *) echo "TERRAFORM_BIN must be absolute" >&2; exit 2 ;; esac
case "$AWS_PROVIDER_MIRROR" in /*) ;; *) echo "AWS_PROVIDER_MIRROR must be absolute" >&2; exit 2 ;; esac
case "$AWS_PROVIDER_MIRROR" in *'"'*|*'\'*|*$'\n'*) echo "Unsupported mirror path" >&2; exit 2 ;; esac
[ -x "$TERRAFORM_BIN" ] || { echo "Terraform executable missing" >&2; exit 2; }
[ -d "$AWS_PROVIDER_MIRROR/registry.terraform.io/hashicorp/aws/6.64.0" ] || {
  echo "Locked AWS 6.64.0 provider is missing from the mirror" >&2
  exit 2
}

project=$(cd "$(dirname "$0")/.." && pwd)
# Short private socket paths avoid macOS plugin handshake path-length failures.
scratch=$(mktemp -d /tmp/dmi-a2.XXXXXX)
trap 'rm -rf -- "$scratch"' EXIT
mkdir -m 700 "$scratch/home" "$scratch/data" "$scratch/tmp"
cat > "$scratch/terraform.rc" <<EOF
provider_installation {
  filesystem_mirror {
    path    = "$AWS_PROVIDER_MIRROR"
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
terraform_offline test -test-directory=tests -no-color
bash -n "$project/scripts/cloud-init.sh" "$project/scripts/check-offline.sh"
printf '\nOffline checks passed. Mock resources are not a live plan, deployment or screenshot evidence.\n'
