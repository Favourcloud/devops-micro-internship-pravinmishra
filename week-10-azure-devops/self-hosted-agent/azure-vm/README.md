# A1 — isolated Azure VM adaptation and actual pilot

**Assignment incomplete. No lab resources remain from this run.** This module prepares a host, not an installed or registered Azure DevOps agent. The [parent runbook](../README.md) still governs PAT handling, package review, registration, service setup and the manual pipeline.

## Actual outcome — 2026-09-17

The user explicitly approved one temporary Azure lab, local missing-tool installation, dedicated SSH access, a **US$1 planning allowance** and cleanup within the original two-hour window. The allowance was **not an enforced billing cap**. That authorization window has ended; do not reuse it for another deployment.

| Operation | Actual result |
| --- | --- |
| UK South `Standard_B2s` | Apply failed with `SkuNotAvailable`; no VM was created. Partial networking was destroyed and absence verified at 10:15:17 UTC. |
| Subscription SKU review | B2s had a location-level `NotAvailableForSubscription` restriction. D2lds v6 had zone restrictions for zones 2/3, but no nonzonal/location restriction; regional and Dldsv6 family quota were each 0/10 cores used. Eligibility did not guarantee capacity. |
| Nonzonal `Standard_D2lds_v6` | Apply succeeded at 10:23:16 UTC. A control-plane read confirmed `Succeeded`, NVMe and Trusted Launch with Secure Boot/vTPM. |
| Host verification | Managed boot diagnostics was initially absent. A separately reviewed Terraform update enabled only that VM setting. Its boot log lacked a verifiable ED25519 host fingerprint, so **SSH was not attempted**. No guest account, OS release or prerequisite check is claimed. |
| Cleanup | Reviewed destroy plan applied. Empty state and exact resource-group/VM/OS-disk/public-IP absence verified at **11:55:19 UTC**, before **11:58:58 UTC**. Initial CLI verification errors were resolved using exact read-only ARM resource URLs. The cleanup reminder was then cleared. |
| Azure DevOps | Organization not confirmed; no PAT/pool, package installation, registration, service, Online agent or pipeline run. No screenshots or learner reflections. |

The [machine-readable runtime receipt](runtime-2026-09-17.json) is derived from private invocation records, **not screenshot evidence**. It retains hashes of the actual saved plans and applied sources. Final source differs deliberately: managed diagnostics is now enabled at creation, and the cleanup checker additionally rejects association IDs from another subscription. These final changes have offline tests; first-boot host-fingerprint retrieval has **not** been live-verified. No reboot, Run Command extension or host-key bypass was used.

The reviewed public Linux VM compute quote was **US$0.131/hour** (US$0.262 for two hours), excluding disk, public IP, egress and tax. This is an estimate, not an invoice; actual billing has not been verified. VM shutdown alone would not have removed all billable resources.

## Scope and design

This is a narrow adaptation of the [Week 08 Azure VM reference](../../../week-08-terraform/terraform-azure-vm/README.md), resolving its password-SSH gap. The [existing Week 09 Azure source](../../../week-09-ansible/epicbook-prod/terraform/azure/main.tf) supplied the previously used nonzonal SKU/NVMe/image precedent; fresh subscription eligibility and pricing were checked independently. Neither earlier project nor its state was modified or assumed live.

- Terraform `~> 1.13.5`; signed, locked `hashicorp/azurerm = 4.47.0`. No automatic Azure resource-provider registration.
- Eight `azurerm` managed entries (RG, VNet, subnet, public IPv4, NSG, NIC, NIC–NSG association, VM), plus one local `terraform_data` approval gate. No role assignments, managed identity, database, web listener or agent extension.
- UK South, nonzonal D2lds v6: 2 vCPUs, 4 GiB, x64, Gen2/NVMe. 32 GiB Standard LRS OS disk. Secure Boot and vTPM enabled.
- Pin an independently verified `Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2` version. The pilot used `22.04.202608060`; do not assume future availability or use `latest`.
- SSH key-only `labadmin` operator, controller's current global IPv4 `/32` only. A higher-priority deny rule blocks all other inbound traffic, including default VNet/LB access. Outbound DNS/TLS is not restricted by this module; review destinations before any package or agent work.
- Cloud-init declares locked-password `azdoagent`, no sudo/privileged groups, owner-only `/home/azdoagent` and `/home/azdoagent/azdo-agent`. It creates directories, not an agent: no package update/install, registration, service or application execution. Guest execution was not independently verified in this pilot.
- Managed boot diagnostics uses Azure-managed storage, not a new user-owned storage account. Keep console output private. Enable it at creation so the initial host-key fingerprint can be retrieved through authenticated Azure access.
- Local state and all live inputs/plans/logs/keys belong under ignored, mode-0700 `.private/`; files should be mode 0600. `tests/simulated-operator.pub` is a separate public-only test fixture whose private key was destroyed, not an operator key.

The source/plan checks prevent selected mistakes; they are **not an IAM boundary, automatic TTL controller or spending cap**. An expiry tag does not delete resources. The Terraform gate verifies the explicit subscription/tenant/operator, approval flag and nonexpired deadline at apply. The separate checker requires at most two hours remaining for creation. Cleanup remains possible after expiry.

## Offline validation

Use the existing system Python 3.9/Ruby/Psych and locally installed Terraform/provider. The original helper/pipeline/preservation tests remain [documented separately](../README.md#offline-validation). From the repository root:

```sh
env -i PATH=/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network*) (deny file-write*)' \
  /usr/bin/python3 -I -B -m unittest discover \
  -s week-10-azure-devops/self-hosted-agent/azure-vm/tests -v

TF="$PWD/.tools/terraform"
cd week-10-azure-devops/self-hosted-agent/azure-vm
"$TF" fmt -check -recursive
```

For each of `validate -no-color` and `test -filter=tests/agent.tftest.hcl -no-color`, invoke the installed Terraform using:

```sh
env -i PATH=/usr/bin:/bin HOME=/nonexistent CHECKPOINT_DISABLE=1 \
  TF_IN_AUTOMATION=1 TF_DATA_DIR="$PWD/.private/tf-data" \
  /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network*) (allow network* (local unix-socket) (remote unix-socket))' \
  "$TF" test -filter=tests/agent.tftest.hcl -no-color
```

All nine Terraform tests use a **mock provider and `command = plan`**, not cloud operations. Provider-local Unix RPC is allowed; external networking is denied. Unlike Python tests, native Terraform tests permit local writes needed by the runner. The mock's year-2100 deadline exercises plan structure only: the apply-time timestamp condition is unknown during a mock plan. Python tests separately reject expired and overlong lifetimes. No tests create accounts, install packages, run cloud-init, contact Azure or execute registration/service scripts.

If the chosen validation command fails because Terraform/provider is missing, stop for a reviewed, disk-budgeted restoration; do not download another large provider copy unnecessarily. The pilot installed Terraform 1.13.5 only after it was missing, verified the published archive SHA-256 `92f76865230cbe6bb747e49cb3dc5b44a054324bbdd1a080bb127b326b94c404`, and initialized the signed provider. The executable/provider and private records are intentionally not committed. A fresh checkout must verify its own platform's official checksum and initialize the pinned provider; the recorded archive digest is not a universal platform digest.

### Recorded local results

Final source validation on 2026-09-17 passed: **37 original Python tests, 20 adaptation/receipt Python tests, Terraform formatting/schema validation, and 9 mocked Terraform plan runs; zero skipped or failed**. Python tests ran with a cleared environment/HOME and network/file writes denied; native Terraform used the network-denied/local-Unix-RPC exception described above. The five original briefs, seven A1 screenshot requirements, eight unchecked checklist entries and unanswered Notes are preserved. These results are not agent or pipeline evidence.

## Future human-operated run — gated, not automatic

1. **Resolve missing information before paying for another VM:** confirm the Azure DevOps organization/project, dedicated pool administrator, approved repository/ref and safe hidden-interactive PAT handoff. Obtain a new scoped identity/region/SKU/image, budget, controller `/32`, key and cleanup-window approval. PATs never belong in Terraform, environment variables, arguments, state, chat, logs or screenshots. Follow the parent runbook's least-privilege scopes and expiry.
2. Recheck native Azure CLI identity, explicit subscription/tenant/operator object ID, detailed SKU restrictions, required family/regional quota, exact image and current Linux **Virtual Machines** consumption pricing. A size catalogue or quota alone is insufficient. Never raise quota, change IAM or broaden SSH as a workaround. Keep at least 15 minutes in reserve for cleanup.
3. Review `main.tf`, `cloud-init.yaml`, provider lock and `check_plan.py`. Generate a new dedicated RSA-3072 operator key in the approved private directory without displaying its private contents. Do not reuse the test fixture or inspect earlier private keys/state. Prepare a private `approved-inputs.tfvars.json` with every variable in `variables.tf`: verified IDs, unique `dmi-w10-a1-…` prefix, UK South, reviewed SKU/image, controller `/32`, public key, UTC deadline and an explicitly approved `live_execution_approved: true`. No committed live inputs are supplied.
4. Initialize only this local backend at `.private/terraform.tfstate`, with `TF_DATA_DIR` under `.private/`. Use a minimal invocation environment: approved native CLI HOME/cache, explicit PATH, disabled telemetry/log-file collection and checkpoint checks, with no inherited AWS/ARM/service-principal credentials or `TF_VAR_*` overrides. Native Azure CLI may update its normal cache/lock files; this live invocation is not the all-write-denied test sandbox. Use a private Terraform CLI configuration and a private temporary directory.
5. Save a **new** plan with `terraform plan -var-file=.private/approved-inputs.tfvars.json -out=.private/create.tfplan -input=false`. Review its complete source and plan privately. Feed its JSON directly to the read-only checker (do not publish the JSON):

   ```sh
   set -o pipefail
   "$TF" show -json .private/create.tfplan | \
     /usr/bin/python3 -I -B check_plan.py --inputs .private/approved-inputs.tfvars.json
   ```

   Preserve the same approved environment for all Terraform commands. The checker expects exactly nine creates and rejects unrelated resources, imports, replacements, wrong VM/SSH/image/bootstrap settings and invalid approval/lifetime. It is deliberately not a general update checker and does not prove provider configuration, every reference/attribute, identity freshness or capacity. Exit 0 means only that these selected local checks passed; 1 means a rejected plan; 2 means malformed input. Review the remaining Terraform JSON/configuration, reject surprises and bind the plan plus source SHA-256 values.
6. Establish a real cleanup reminder/operator **before apply**; a reminder alone is not guaranteed deletion. Recheck identity, plan/source hashes, deadline and free disk. Only then apply the exact saved plan: `terraform apply -input=false .private/create.tfplan`. Keep raw output private. Do not automatically retry or overwrite failed-attempt provenance.
7. Retrieve boot console output through authenticated `az vm boot-diagnostics get-boot-log` for the exact owned VM into a private file. Compare its ED25519 fingerprint with `ssh-keyscan`/`ssh-keygen` output before placing the key in a dedicated known-hosts file. A public IP match or keyscan alone is not authentication. If the trusted fingerprint is unavailable, stop SSH; never use `StrictHostKeyChecking=no`, TOFU acceptance or a guessed key. Managed-diagnostics-from-first-boot behavior remains a live gate.
8. After that comparison, use strict SSH host checking, the dedicated key, no agent forwarding, no inherited SSH configuration and only the owned public IP. Wait for cloud-init; check Ubuntu 22.04, x86_64, a nonzero `azdoagent` UID, no privileged groups/sudo, and owner-only `/home/azdoagent` and `/home/azdoagent/azdo-agent`. Verify disk, Git/Bash/archive/hash/systemd prerequisites. The operator may switch users; the agent must not gain sudo. Run `uname -a`, `whoami`, `df -h` as `azdoagent` for host checks, but do not call this an Azure pipeline success. Only then follow the separate human package/registration/service runbook.

## Cleanup — on failure, missing information or completion

Use only this invocation's state and approved resource ownership. Never delete the private state to pretend cleanup succeeded, manually delete cloud resources, shut down the VM and call it cleanup, or touch earlier/shared projects.

1. If registration ever happened, perform the parent runbook's scoped service stop/uninstall, agent removal and PAT revocation first. None was required in this pilot because registration never happened.
2. Save a fresh destroy plan with the same approved private inputs and `terraform plan -destroy -var-file=.private/approved-inputs.tfvars.json -out=.private/destroy.tfplan -input=false`. Review its complete scope and pipe `terraform show -json .private/destroy.tfplan` into `check_plan.py --inputs .private/approved-inputs.tfvars.json --destroy`.
3. The checker permits a delete-only subset after a partial apply and after expiry, but rejects foreign resource IDs/subscriptions and unrelated changes. Recheck the reviewed plan hash, then apply **that saved plan**. Preserve its output and exit status privately; investigate any failure immediately.
4. Verify `terraform state list` is empty and authenticated exact RG/VM/OS-disk/public-IP reads prove absence. If a convenience CLI command fails, use exact read-only ARM URLs and require a genuine `ResourceGroupNotFound`/`ResourceNotFound`, not any error. Retain sanitized receipts and private originals; clear the reminder only after verified cleanup. Recheck billing separately without claiming zero cost.

## References

- [Azure boot diagnostics and managed storage](https://learn.microsoft.com/en-us/azure/virtual-machines/boot-diagnostics)
- [Pinned AzureRM Linux VM resource](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs/resources/linux_virtual_machine)
- [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
- [Original seven-slot evidence manifest](../evidence/manifest.json): unchanged and entirely pending.
