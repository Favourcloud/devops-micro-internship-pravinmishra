# Week 08 Assignment 1 — Azure VM (Eze Favour)

**Partial submission: 5/11 genuine screenshots verified; the assignment is not
complete.** Screenshots 1–5 document local installed tools and frozen source.
Screenshots 6–11 remain pending in the [evidence manifest](evidence/manifest.json).
No fresh cloud/spending authorization exists for this run. No Azure login, live
plan, apply, VM verification, public IP allocation or destroy was performed.
Local validation and mock resources are not deployment evidence or proof of a
grade.

- **Learner:** Eze Favour
- **Project:** [assignment branch](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/favourcloud-week-08-azure-vm/week-08-terraform/terraform-azure-vm)
- **Branch/review:** `favourcloud-week-08-azure-vm` · [Draft PR #9](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/9)
- **Evidence operator:** GitHub Copilot under user delegation, not manual learner execution.

The [submission](../assignment-01-create-an-azure-virtual-machine-using-terraform.md)
presents the five original, unmodified native VS Code PNGs in their correct
numbered slots. Every original requirement, heading, question and checklist item
text is retained; only responses, insertions and checkbox markers are updated.
The manifest's original byte-count/hash describe the reference rubric, not an
unchanged prefix of the current submission. This project owns only Assignment
1; it does not reuse another assignment's state, plans, credentials, approvals
or resources.

## Infrastructure

[main.tf](main.tf) contains the pinned Terraform/AzureRM requirements, AzureRM
provider, resource group, VNet, subnet, Standard static IPv4, NSG, NIC, NIC/NSG
association, Ubuntu Linux VM and outputs. There are **eight managed resources**;
NSG rules and the VM OS disk are nested blocks, not additional Terraform resources.

- AzureRM **4.47.0**; Terraform **1.13.5–1.13.x**. Commit the provider lock file.
- Provider registration is explicitly disabled (`resource_provider_registrations
  = "none"`). No registration, IAM, quota or subscription changes are performed.
- Password authentication is intentionally enabled to meet the rubric, not
  silently replaced with SSH keys. No key material is generated or stored.
- Exactly one inbound allow: TCP/22 from the explicitly supplied controller IPv4
  `/32`. A priority-200 deny overrides the default Azure VNet/load-balancer
  inbound allows. No HTTP/HTTPS/RDP allow rules. Azure's default outbound rules
  remain; no application, package deployment or SSH session is part of A1.
- The NIC must have its NSG associated before VM creation.
- The Ubuntu 22.04 Gen2 image uses `latest`; its resolved version may change
  between authorized runs. The OS disk uses `Standard_LRS` and is deleted with
  the VM. The public IP and disk can incur charges even when the VM is stopped.

Official references: [AzureRM provider](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs),
[Linux VM](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs/resources/linux_virtual_machine),
[Terraform mock providers](https://developer.hashicorp.com/terraform/language/tests/mocking),
[sensitive state](https://developer.hashicorp.com/terraform/language/manage-sensitive-data).

## Input interface

See [variables.tf](variables.tf) and the non-secret
[example inputs](terraform.tfvars.example). Do not turn the example into an
auto-loaded root `terraform.tfvars` or `*.auto.tfvars` file.

| Input | Default | Contract |
| --- | --- | --- |
| `project_name` | `dmi-w08-a1` | Unique disposable prefix, 3–30 lowercase letters/digits/hyphens; starts with a letter, ends alphanumeric. Do not collide with an existing deployment. |
| `location` | None; required | Freshly approved Azure region code. Syntax validation is not a capacity check. |
| `vm_size` | None; required | Freshly approved `Standard_...` SKU. Syntax validation is not a quota or price check. |
| `controller_ipv4_cidr` | None; required | The actual controller's public IPv4 `/32`; no `/0`, subnet, IPv6, wildcard or unspecified address. Determine it without an unapproved external lookup. |
| `admin_username` | `dmiuser` | Non-reserved Linux username, at most 32 characters. |
| `admin_password` | None; required; sensitive | External hidden input only; 16–72 printable ASCII characters, no spaces, all four character classes, and no case-insensitive username substring. |

The example `192.0.2.10/32` and mock `192.0.2.20` are documentation-only addresses,
not a real controller or deployment. `uksouth`/`Standard_D2lds_v6` in examples
are illustrative, not approved or guaranteed available. A historical B1s
allocation failure and a historical D2lds_v6 success establish neither current
capacity nor permission to deploy. Change region/SKU only after new approval.

Authentication is separate from these Terraform inputs. After authorization,
the controller supplies `ARM_SUBSCRIPTION_ID` privately and authenticates through
a private Azure CLI profile (or an independently approved external identity).
Never put real account/subscription/tenant IDs or credentials in this repository.

## Reproduce offline validation

Run from this project directory, with Python 3 and the existing Terraform binary:

```bash
python3 tests/run_offline.py
```

If Terraform is not on `PATH`, or an immutable installed provider mirror is
available, pass local paths privately (never commit them):

```bash
python3 tests/run_offline.py --terraform "$TERRAFORM_BIN" --plugin-dir "$PROVIDER_MIRROR"
```

The runner uses only the Python standard library. It creates a mode-0700 ignored
`.private` directory, sets `umask 077`, isolates the home/CLI config/data paths,
and does not inherit Azure credentials, Terraform argument overrides, logging
settings or `TF_VAR_*` inputs. A mode-0700, short temporary socket directory
avoids macOS Unix-socket path limits and is removed automatically. A disposable
mock password exists only in process memory/environment; it is not printed or
written to tfvars/state files. The provider mock uses in-memory test state,
separate from the live backend.

The runner performs these local checks, stopping on the first failure:

1. Fifteen Python delivery safeguards: reference-rubric fingerprint and ordered
   requirement parity, five exact PNG hashes/timestamps and six pending slots,
   absent authorization/runtime claims, ignore rules, sensitive external input
   contract, disabled registration/no live helpers, private backend/NSG ordering,
   safe outputs/eight resources, mock-only tests, publishable-file exclusions,
   local links, frozen-source bytes, numbered image mappings, truthful checklist
   markers and sanitized public provenance.
2. `terraform fmt -check -recursive -diff`.
3. `terraform init -backend=false -input=false -lockfile=readonly`.
4. `terraform validate`.
5. `terraform test -filter=tests/vm.tftest.hcl`: 31 mock-only runs, including eight
   topology assertions, valid password length boundaries and expected failures
   for weak passwords, unsafe SSH CIDRs, names, region codes and SKU syntax.

With `--plugin-dir`, initialization reuses the existing immutable provider package
read-only and checks it against the committed lock. Without a mirror, only
HashiCorp's official provider registry/package download may be needed; this is
not an Azure API call. No authentication, refresh, real `plan`/`apply`/`destroy`,
GUI action or screenshot is part of this runner. A test block named `apply`
executes **only the AzureRM mock**, not a cloud deployment.

The lock's public AzureRM checksums were reused from the existing repository's
compatible 4.47.0 lock and verified by backend-disabled, read-only initialization;
no other project's state or configuration is used. The current check result is
recorded in [the manifest](evidence/manifest.json), not as raw command logs.

## Private state, credentials and permissions

Terraform's `sensitive` flag redacts ordinary CLI displays; **it does not encrypt
state or saved plans**. `admin_password` will be present in live state and saved
plans. The local backend is deliberately `.private/terraform.tfstate`, with
backups beside it. Git ignore rules are not encryption or access control.

Before any authorized execution:

- Use an access-controlled, encrypted local disk. Exclude `.private`, shell
  recordings and credential profiles from public/shared backups or sync.
- Keep `.private` mode 0700, use `umask 077` before Terraform/CLI operations, and
  keep regular private files mode 0600. Do not follow or chmod provider symlinks.
- Use a new `.private/live-data` and `.private/azure` profile, never another
  assignment's Terraform data, workspace, state, saved plans or cloud credentials.
- Enter secrets with an unrecorded hidden prompt; disable shell tracing and
  Terraform debug logging. Never use `-var='admin_password=...'`, exported literal
  secrets in shell history, tfvars password entries, `terraform output -json`,
  `terraform show -json`, state dumps or screenshots of private files.
- Do not disable sensitivity or upload raw plans/state/logs. Capture only a
  necessary terminal summary; inspect screenshots for resource IDs, subscription
  IDs, usernames/private paths, credentials and history before publication.
- Retain state securely after any partial failure. Do **not** delete state to
  “reset” Terraform: that loses the resource inventory needed for cleanup.

## Prospective authorized runbook — NOT executed

**Stop here until the parent/controller obtains fresh, explicit authorization.**
It must cover the actual subscription, region/SKU, budget, time limit, credentials,
controller `/32`, provider/API access, GUI evidence and teardown. The earlier
unavailable approval response is not permission. Existing historical budgets,
keys, inventories and successful runs are not authorization.

The subscription must already allow the required Compute/Network providers,
permissions, quota and chosen SKU/Gen2 image. This project never auto-registers
providers. If prerequisites or allocation fail, stop and report; do not change
IAM, quotas, registration, region/SKU or budget to work around a failure. Arrange
Terraform cleanup of partial resources within the approved window, requesting
renewed authorization where necessary. No SSH is required for the rubric.

The following commands are **prospective**, intended for an authorized Bash
session opened in this project. Do not run them during offline validation.

### 1. Isolate the authorized session and supply private inputs

First open a clean Bash subshell, without old identity variables, Terraform
overrides or shell startup files. Exit this subshell after teardown:

```bash
env -i PATH="$PATH" HOME="$HOME" TERM="${TERM:-dumb}" bash --noprofile --norc
```

Then run the following inside that subshell:

```bash
set +x
umask 077
unset TF_LOG TF_LOG_PATH TF_CLI_ARGS TF_CLI_ARGS_init TF_CLI_ARGS_plan
unset TF_CLI_ARGS_apply TF_CLI_ARGS_destroy TF_WORKSPACE TF_CLI_CONFIG_FILE
mkdir -p .private/azure .private/live-data
chmod 700 .private .private/azure .private/live-data
export AZURE_CONFIG_DIR="$PWD/.private/azure"
export TF_DATA_DIR="$PWD/.private/live-data"
export CHECKPOINT_DISABLE=1

# Copy non-secret examples, then edit only this ignored file with approved values.
cp -n terraform.tfvars.example .private/approved.tfvars
chmod 600 .private/approved.tfvars

# Run only after editing the region, SKU, unique prefix and actual controller /32.
# Keep login/ID/password prompts OUTSIDE any recording or screenshot capture.
az login --output none
IFS= read -r -s -p 'Approved subscription ID: ' ARM_SUBSCRIPTION_ID
printf '\n'
export ARM_SUBSCRIPTION_ID
az account set --subscription "$ARM_SUBSCRIPTION_ID"
IFS= read -r -s -p 'VM administrator password: ' TF_VAR_admin_password
printf '\n'
export TF_VAR_admin_password
```

`cp -n` preserves an existing private file; do not reuse it without checking every
value and ownership. Neither the approved ID nor password belongs in that file.
The subscription selection must be privately verified by the controller before
planning; do not capture the account listing or authorization prompts.

### 2. Initialize, review, apply and capture only genuine results

```bash
terraform version
az version
terraform init -input=false -lockfile=readonly
terraform validate
terraform plan -input=false -var-file=.private/approved.tfvars -out=.private/create.tfplan

# Controller reviews the actual plan and confirms it stays within fresh approval.
terraform apply .private/create.tfplan
terraform output -raw public_ip_address
printf '\n'
az vm get-instance-view \
  --resource-group "$(terraform output -raw resource_group_name)" \
  --name "$(terraform output -raw vm_name)" \
  --query "{name:name,powerState:instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus | [0]}" \
  --output table
```

Do not infer success from source code or the plan. The real IP comes only from
successful runtime output. The VM must actually report `VM running` for slot 10.
Record the IP in the original assignment's answer only after this verification.
The parent owns the VS Code extension/source and terminal screenshots. Source
screenshots must show `var.admin_password`, not a supplied value or private file.
Do not run stale saved plans after changing inputs or approval scope.

### 3. Destroy and verify cleanup inside the approved window

```bash
terraform destroy -var-file=.private/approved.tfvars
# Confirm Terraform's interactive prompt only after reviewing the destruction.
terraform state list
unset TF_VAR_admin_password ARM_SUBSCRIPTION_ID
```

A successful destroy summary plus an empty A1 state list are required before
reporting cleanup. A failed apply can still leave billable resources: retain the
same private state and use Terraform, not manual Azure deletion, to clean up.
Do not delete or alter another assignment's resources. If the controller's
approved follow-up verification finds a retained resource, cleanup is not done.

After verified teardown, evidence review and parent approval, remove only this
run's private credential profile, plan files and state/backups from storage per
the local retention policy. Do not retain VM passwords. Do not delete shared
provider caches or old assignment artifacts. Until then keep all private files
restricted and ignored. Destroying the VM does not itself erase plaintext state
backups or saved plan files.

## Evidence handoff and status transitions

**5/11 verified.** The parent captured the five native images on 2026-09-16,
23:16–23:19 UTC, and verified privacy and visible requirements. This integration
copies those original PNG bytes without editing them. Exact timestamps and
SHA-256 values are in the [public manifest](evidence/manifest.json); private OCR,
window/PID metadata and local capture paths are intentionally excluded.

| Slot | Genuine evidence required | Current status |
| --- | --- | --- |
| 1 | Terminal: `terraform version` | [Verified: Terraform 1.13.5](evidence/screenshots/screenshot-01-terraform-version.png) |
| 2 | Terminal: `az version` | [Verified: Azure CLI 2.89.1](evidence/screenshots/screenshot-02-azure-cli-version.png) |
| 3 | VS Code HashiCorp Terraform extension installed/enabled | [Verified: extension 2.40.0, Disable/Uninstall controls](evidence/screenshots/screenshot-03-vscode-terraform-extension.png) |
| 4 | VS Code `main.tf`: AzureRM provider and resource group | [Verified: frozen source](evidence/screenshots/screenshot-04-provider-resource-group.png) |
| 5 | VS Code `main.tf`: VM and public-IP output; password hidden | [Verified: variable reference, no password value](evidence/screenshots/screenshot-05-vm-public-ip-source.png) |
| 6 | Terminal: successful actual `terraform init` | Pending authorized sequence/capture; backend-disabled checks are not this screenshot |
| 7 | Actual Terraform plan summary | Pending authorized run/capture |
| 8 | Actual successful Terraform apply | Pending authorized run/capture |
| 9 | Actual `terraform output` public IP | Pending authorized run/capture |
| 10 | Azure CLI VM name and `VM running` | Pending authorized run/capture |
| 11 | Actual successful Terraform destroy | Pending authorized run/capture |

Screenshots 4–5 bind `main.tf` to source commit
`dbdab95b21f517cfe0751d07e667001c0fb6a775`, SHA-256
`53a5a0f92c56d81437a66210af7cc4ed9f362604cca90b6ebf22b22f756405db`.
The Terraform source, variable/input contract, lock and mock-runner behavior are
unchanged by this evidence integration. Screenshot 5 shows
`admin_password = var.admin_password` and the complete public-IP output source,
not a secret or allocated IP. No manual learner execution is claimed.

For each remaining real capture, the parent must verify correspondence to this
A1 run and inspect privacy before publication. Record any necessary redaction
honestly rather than describing an edited image as original. Only after genuine
evidence exists should its slot become `verified`, with a relative artifact
path, timestamp and SHA-256, and an image/caption in the matching numbered slot.
Update evidence-test expectations alongside verified transitions while retaining
all rubric requirements. Never substitute mock outputs, generated images, another
assignment's logs or a local check for a required screenshot.

Deployment/authorization fields change only when supported by an actual newly
authorized run. The VM public IP remains null and the assignment remains
incomplete; completion requires every task and all eleven images, including
teardown evidence. No grade is asserted.
