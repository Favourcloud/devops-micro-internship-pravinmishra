# Mini Finance — Week 09 Assignment 4 (Azure, partial evidence)

**Status: VM allocation blocked; authorized cleanup verified, not a deployed assignment.** The coordinator visibly launched the reviewed first apply on 2026-09-16. Seven supporting Terraform instances were created, but Azure rejected **Standard_B1s in uksouth** with HTTP **409 `SkuNotAvailable`**. No VM or website was deployed. A reviewed cleanup plan removed only those seven instances; Azure resource absence and empty Terraform state/outputs were verified. Genuine coordinator-captured **Screenshots 1 and 4** are embedded unchanged in the [submission](../assignment-04-deploy-mini-finance-project-using-terraform-and-ansible.md), with hashes/source bindings in the [evidence manifest](../screenshots/assignment-04-manifest.json). Screenshots 2, 3, 5–8 and LinkedIn remain pending. No SSH, remote Ansible, browser/HTTP verification, remote idempotence or LinkedIn publication occurred.

The user approved a **US$5 combined AWS/Azure temporary-lab budget**; the coordinator allocated A4 **at most US$1 and two hours**, reviewed the exact fresh plan and separately authorized cleanup after failure. The first attempt started at **18:45:03 UTC**, cleanup finished at **18:55:43 UTC**, and absence was verified at **18:57:17 UTC** on 2026-09-16, before its 20:45:03 UTC deadline. Final Azure charges are not yet verified; absence is not a zero-cost claim. Quota/SKU listings and a successful plan do **not** guarantee allocation capacity. Required **Standard_B1s** remains unchanged; any retry needs a new reviewed plan and explicit authorization. No alternate-region queries were duplicated here. Historical AWS permission is not being renewed or treated as Azure authorization; no login, billing, IAM/RBAC, provider-registration or global configuration changes were made.

## Layout

```text
mini-finance/
├── .gitignore
├── README.md
├── requirements-dev.txt
├── terraform/
│   ├── .terraform.lock.hcl
│   ├── versions.tf
│   ├── variables.tf
│   ├── main.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   └── tests/azure.tftest.hcl
├── ansible/
│   ├── ansible.cfg
│   ├── inventory.ini              # deliberately empty [web] group
│   ├── group_vars/all.yml
│   ├── site.yml                   # exactly three plays
│   └── templates/nginx.conf.j2
└── tests/test_contract.py
```

## Design and provenance

- **Azure only:** a dedicated resource group, VNet (`10.42.0.0/16`), subnet (`10.42.1.0/24`), Standard static IPv4, NIC, NIC-scoped NSG, and Ubuntu **22.04 Standard_B1s** VM. SSH passwords are disabled. The only key input is an explicitly supplied existing **public** key. The image uses Canonical's current patched Jammy Gen2 image (`version = "latest"`); rebuilding can select a newer image. It is not an image-byte reproducibility claim.
- AzureRM **4.47.0** is exact-pinned with its generated checksum lock file. Terraform is constrained to `>= 1.9.8, < 2.0.0`. No credentials/subscription ID defaults, data-source account lookups, provisioners, remote-exec or role assignments. Provider auto-registration is disabled; an authorized owner must have the required `Microsoft.Compute` and `Microsoft.Network` providers already registered. Do not turn on subscription-wide registration to work around missing approval.
- Managed `boot_diagnostics {}` provides an Azure-authenticated channel for retrieving cloud-init SSH host fingerprints, without provisioning a separate storage account. All taggable resources carry the explicit `run_id`/name prefix so the run remains distinguishable from older labs.
- NSG permits TCP **22 only from the controller's IPv4 /32**, TCP **80 from Internet**, then explicitly denies other inbound traffic (including the default VNet allowance). The NSG is attached before VM creation. Outbound Azure defaults remain for DNS, Ubuntu packages and public GitHub; this is a lab, not a fully egress-restricted production design. Only approved Terraform changes may alter infrastructure.
- The authoritative course URL is [Week 06 Assignment 3](../../week-06-aws-cloud/assignment-03-deploy-mini-finance-website-on-aws-virtual-machine.md): `https://github.com/pravinmishraaws/mini_finance.git`. Read-only public GitHub API inspection on **2026-09-16** confirmed public visibility and [revision `296334fc27de87bdfcafdad041e41573d8815700`](https://github.com/pravinmishraaws/mini_finance/commit/296334fc27de87bdfcafdad041e41573d8815700) (commit timestamp 2025-10-24). No deployment clone or invented download/repository history is claimed.
- At that revision the root contains six HTML pages, `css/`, `fonts/`, `images/`, `js/`, documentation and `git_tracking_summary.txt`; `js/.DS_Store` is also tracked. The explicit export list in `group_vars/all.yml` includes only the web pages/assets, spelling upstream `transation-detail.html` exactly. JavaScript is **not authored or vendored into this coursework repo**; the future authorized deployment uses the upstream site's existing assets on the VM.
- Upstream does not declare a GitHub-detected SPDX license; its `ABOUT THIS TEMPLATE.txt` grants website usage/editing and restricts template-ZIP redistribution. See the [original Tooplate template](https://www.tooplate.com/view/2135-mini-finance). Upstream author/copyright notices remain in deployed assets; do not represent them as learner-authored work or redistribute a template archive here.
- Play 1 validates an explicit target locally before opening SSH, requires Ubuntu 22.04 and installs Nginx/Git. Play 2 clones outside the document root under `/opt/mini-finance/source`, archives the pinned allowlist, validates assets/markers and rejects hidden files/symlinks, then points `/var/www/html` at a root-owned release. An unrelated existing document directory is refused, not deleted. The initial stock Nginx welcome directory alone may be replaced. This dedicated VM's complete Nginx configuration is managed by the project.
- The configuration template is checked using `nginx -t -c` before replacement; notified handlers recheck the active configuration before reload. Handlers flush before Play 3. Changed content/configuration/publication triggers reload; read-only checks do not report changes. Later revisions use separate release directories and a symlink switch; this is not a transaction/automatic rollback guarantee, and initial installation may briefly show Nginx's welcome page.
- Play 3 uses `localhost`/the controller to require HTTP **200 plus both pinned Mini Finance content markers**, disallows redirects, ignores proxy/netrc credentials and expects **404** for `.git/config`, `js/.DS_Store`, `git_tracking_summary.txt` and `README.md`. Nginx also denies dot paths and directory listings. HTTP is deliberately unencrypted to satisfy the lab's port-80 brief; do not submit real financial/personal data to this static demonstration.

## Offline validation (safe without Azure login)

Run from `week-09-ansible/mini-finance`. Use existing approved Terraform and controller executables on `PATH`; the verified run reused preserved executables read-only and did not reinstall or alter the shared controller. If tools are genuinely missing on a future independent workstation, create a project-local Python 3.13 virtualenv and install `requirements-dev.txt` **there**, not globally. No additional Ansible collections are required.

```sh
umask 077
mkdir -p .local/tmp .local/cache
export CHECKPOINT_DISABLE=1
export TF_DATA_DIR="$PWD/.local/terraform-data"
export TF_CLI_CONFIG_FILE=/dev/null
export XDG_CACHE_HOME="$PWD/.local/cache"
export ANSIBLE_LOCAL_TEMP="$PWD/.local/tmp"
export PYTHONDONTWRITEBYTECODE=1
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend=false -input=false -lockfile=readonly
terraform -chdir=terraform validate
terraform -chdir=terraform test
python -m unittest discover -s tests -v
(cd ansible && ansible-playbook -i inventory.ini site.yml --syntax-check)
(cd ansible && ansible-lint --offline site.yml group_vars/all.yml)
```

`init` downloads the signed pinned provider from HashiCorp; it is not network-air-gapped, but does not authenticate to Azure or create resources. `terraform test` uses **only mocked plans**, no real apply, and no Azure environment variables are needed. Its RFC 5737 addresses and RFC 8032 public test vector are clearly marked fixtures, **not deployed addresses or the user's SSH key**. Do not reuse them for deployment.

The Ansible-related Python tests execute real inventory parsing and preflights with an SSH **refusal stub**, never a network SSH connection. Empty/malformed/multiple-host inventories, root login, explicit local targets and check mode fail before the stub, package operations or HTTP. Two positive cases use the documented inventory and an overridden localhost context: both pass the guard and reach only the refusing stub at fact gathering. The guard validates the original `hostvars[inventory_hostname]` for address, user and connection rather than delegated localhost variables. These are regression tests, **not connectivity evidence**. The committed empty inventory also fails a normal `ansible-playbook -i inventory.ini site.yml` invocation. `--syntax-check` is the supported offline check; `--check` is deliberately rejected instead of implying that uncreated release paths or HTTP were verified.

SSH multiplexing is explicitly disabled (`ControlMaster=no`, `ControlPath=none`, no `ControlPersist`) so long worktree/controller-cache paths cannot exceed macOS's 104-byte Unix socket limit. A separate real OpenSSH regression reproduced `ControlPath too long` before the fix, then reached only a refusing local `ProxyCommand` afterward. It uses no network, agent or private key; strict host-key checking and batch authentication remain required for deployment.

### Recorded local results — 2026-09-16

| Check | Actual local result |
| --- | --- |
| Terraform 1.13.5 `fmt -check -recursive` | Passed |
| `init -backend=false -input=false` | AzureRM 4.47.0 installed; signed provider checksums locked |
| `validate` | Valid configuration |
| `test` | 10 mocked-plan runs passed, 0 failed |
| Python 3.13.3 `unittest discover -s tests -v` | 21 tests passed; positive guards reach a refusal stub; real OpenSSH reaches only a refusing local proxy; no SSH network calls |
| Ansible core 2.21.4 `--syntax-check` | Passed |
| ansible-lint 26.8.0 `--offline site.yml group_vars/all.yml` | 0 failures, 0 warnings |

These offline checks do **not** establish live Azure capacity, VM creation, real key compatibility, remote Nginx syntax/runtime, availability, or second-run idempotence. The actual first attempt failed at VM allocation, as recorded below.

### Authorized plans, failed first apply and verified cleanup — 2026-09-16

Terraform 1.13.5 prepared a private saved plan against the current Azure CLI subscription from infrastructure commit `835b90b041315c76b10b6984448504b0c0d11fd4`: **8 creates, 0 updates, 0 deletes** (one each: resource group, VNet, subnet, NSG, public IP, NIC, NIC/NSG association and Linux VM). The unique run prefix is `dmi-w09-a4-20260916-835b90`; planned VM/image/disk/network settings match the assignment and include managed boot diagnostics.

The owner-approved existing public key was read from its `.pub` file only; controller `/32` was obtained via approved HTTPS lookup, and subscription selection came from the existing Azure CLI. Actual public-key content, controller address, subscription identifier, variables, full logs, plan binary and JSON remain in **0600 private session artifacts**, not this repository.

The original plan (`96d810732360f038241ceb2007f5845b16316da970dfcd9bbc99245328e32e97`) and raw logs are preserved. Its subscription selection was not separately persisted, so historical identity is **not inferred**. With renewed coordinator authorization, the current CLI subscription was sealed privately **before** generating a separate fresh real plan using unchanged Terraform source, inputs and provider. The unique resource group remained absent and the result remained **8 creates, 0 updates, 0 deletes**. The fresh plan SHA-256 is `65fe9cfe53dd2021cbe5f0688920443a7147e9600a5a93b8a734e5c3217d8cae`; the coordinator reviewed and authorized this exact plan before the first visible launch.

Before launch, **27 offline runner-helper tests passed** without invoking the entry point or external commands. The coordinator subsequently launched the private one-shot runner in an actual foreground VS Code terminal against source `b59867faedae39642653bb16ad1ded001403aaf8`. Its actual raw output records seven supporting instances followed by Azure's `SkuNotAvailable`/HTTP 409 error for the required VM; Terraform exited **1**. The private failure capture is provenance only, **not successful-apply Screenshot 2**.

After explicit cleanup authorization, the agent inspected state and the exact owned Azure group, confirmed there were no untracked resources or VM/disks, then reviewed a saved **0-create, 0-update, 7-delete** Terraform plan (`9f758cd4e709612ac830d22076eeb5f8e8fa5c0aea0cfd05c24907c3d26169fc`). Executing that exact plan exited **0**, removing the RG, VNet, subnet, NSG, public IP, NIC and NIC/NSG association. Read-only Azure checks verified **RG, VM, managed disk, public IP and all group resources absent**; Terraform state and outputs are empty. Sanitized timestamps, counts and raw-log hashes are in the existing evidence manifest. Original state/backup snapshots, both creation plans, attempt marker, raw failure/cleanup/verification logs and private receipts are retained; none are committed or reset. No retry or SSH occurred.

The two genuine PNGs were copied byte-for-byte from coordinator-approved captures, with no crop, resize, redaction or pixel edits. Screenshot 1 binds the 16 tracked filenames to `b59867f`; no new tracked files were added inside `mini-finance`. Screenshot 4 binds `terraform/main.tf` lines 31–64 to SHA-256 `409873591a4aa9b75edfa687eb201120a18d81e92a0057353927f0d6966f5fc8`, and proves code configuration only. Private receipt paths, account identifiers and operational inputs are not published.

## Future operator runbook — STOP until explicitly authorized

The following is a **manual procedure for any future attempt**, not retry authorization. The first failed apply and completed cleanup are recorded above; do not reset their one-shot marker, delete history or reuse an old plan to bypass review. Any new deployment/SSH/cleanup requires fresh approval for its exact Azure scope, required B1s size, region, spend/time limit and cleanup. Never renew expired AWS permission as a workaround.

### 1. Owner approves scope, identity and cost

Have the owner confirm their already-established Azure authentication out of band, intended tenant/subscription, least-privilege access for a new dedicated resource group and its compute/network resources, existing resource-provider registration, Standard_B1s availability/quota, budget and shutdown/deletion deadline. Stop if any item is unknown. Do not create credentials, change account context, alter billing or assign roles as part of this project. The owner may supply the necessary AzureRM subscription selection through private process environment (`ARM_SUBSCRIPTION_ID`), **not a tracked file, command transcript or screenshot**. No identifier is included here.

Charges may include VM compute, managed disk, Standard IPv4 and egress. Stopping/deallocating compute alone does not remove all charges. The disk is explicitly limited to 32 GiB Standard_LRS (S4).

Read-only [Azure Retail Prices API](https://prices.azure.com/api/retail/prices) queries on 2026-09-16 (`armRegionName=uksouth`, `priceType=Consumption`, USD) returned:

| Meter | Retail price |
| --- | --- |
| Virtual Machines BS Series, B1s (Linux, not Windows) | US$0.0118/hour |
| Standard HDD Managed Disks, S4 LRS Disk | US$1.69/month |
| S4 LRS Disk Operations | US$0.0005 per 10,000 operations |
| IP Addresses, Standard IPv4 Static Public IP | US$0.005/hour |

Using a 730-hour month for disk proration, compute + disk + IPv4 are **approximately US$0.04 for two hours**, excluding disk operations, diagnostic storage, egress, taxes, billing increments and any existing account charges. This is a planning estimate, not a billing guarantee or permission to exceed the **US$1/two-hour A4 allocation**. The owner/coordinator must still verify eligibility/quota, review the real plan, monitor elapsed time and retain enough budget for capture plus cleanup.

### 2. Private inputs and reviewed Terraform plan

Keep a restrictive umask and private local state. Copy the deliberately invalid `terraform/terraform.tfvars.example` to ignored `terraform/terraform.tfvars` with mode `0600`. In a local editor, replace placeholders with the approved region, unique resource prefix, chosen non-root admin, current controller public IPv4 `/32`, and the user's **existing `.pub` file content**. The agent must not read a private key, generate/rotate a key or use an example key. The owner must verify that the public key corresponds to their existing private key and meets Azure requirements (RSA 2048+ or Ed25519). Public keys/network details are operational data and remain in ignored local variables, not committed fixtures or screenshots.

```sh
# From mini-finance, ONLY after the explicit approval gate above:
terraform -chdir=terraform plan -out="$PWD/.local/deploy.tfplan"
# Review the complete plan privately: only this dedicated project's resources.
# Stop on unexpected changes, shared resources, missing registration or excess cost.
terraform -chdir=terraform apply "$PWD/.local/deploy.tfplan"
terraform -chdir=terraform output -raw public_ip
```

A saved plan can contain sensitive data. Keep it/state private and do not upload them; Terraform's `sensitive` flag hides display, not state contents. Secure retained state is necessary for cleanup. No remote backend is configured for this single-operator lab; do not share/concurrently apply local state. Capture Screenshots 2–3 only after a successful real VM deployment, reviewing identifiers first; Screenshot 4 already records the permitted code alternative. Record any future actual address privately. The first attempt's temporary public IP was deleted; no active VM/public endpoint exists now.

### 3. Trust the host and configure private inventory

After an approved deployment, use the existing authenticated Azure CLI to retrieve the new VM's **managed boot-diagnostics** log (`az vm boot-diagnostics get-boot-log --resource-group "$RESOURCE_GROUP" --name "$VM_NAME" > .local/boot.log`, with `umask 077`). This is a read of Azure-held output, not remote command execution. Confirm the exact newly deployed subscription/resource group/VM and locate cloud-init's SSH **host** key fingerprints (not the user's authorized-key fingerprints). Keep the full boot log private; only verified public host fingerprints are suitable for sanitized evidence.

A network `ssh-keyscan` can obtain candidate host public keys but is **not authenticated**. Compare each candidate's `ssh-keygen -lf <candidate-file> -E sha256` fingerprint and key type against that VM's Azure-authenticated boot-log host fingerprint. Only after an exact match may that candidate become an entry in project-local `ansible/.local/known_hosts` (mode `0600`). If the log is missing, ambiguous or mismatched, stop and obtain a trusted administrator channel; never silently trust the scan or fall back to `StrictHostKeyChecking=no`/`accept-new`. Do not write global known-hosts or modify old lab entries. No boot-log read or host-key bootstrap has been performed by this preparation.

Create ignored `ansible/.local/inventory.ini` with **actual Terraform output**, the same admin username, and the owner's existing private-key **path only**. The owner edits this file; no automation here opens the private key. Keep paths and network details out of Git and evidence. Preserve the committed `ansible/inventory.ini` as the unconfigured default.

```ini
# Structural template ONLY — placeholders must not be used as inventory values.
[web]
mini_finance ansible_host=ACTUAL_TERRAFORM_PUBLIC_IP ansible_user=ACTUAL_ADMIN_USER ansible_ssh_private_key_file="EXISTING_PRIVATE_KEY_ABSOLUTE_PATH"

[controller]
localhost ansible_connection=local
```

From `ansible/`, use the verified project-local known-hosts file for both the manual check and Ansible:

```sh
# Set VM_IP, VM_USER and EXISTING_PRIVATE_KEY_PATH privately to actual values first.
ssh -o StrictHostKeyChecking=yes -o BatchMode=yes -o IdentitiesOnly=yes \
  -o "UserKnownHostsFile=$PWD/.local/known_hosts" \
  -i "$EXISTING_PRIVATE_KEY_PATH" "$VM_USER@$VM_IP" hostname
export ANSIBLE_SSH_COMMON_ARGS="-o UserKnownHostsFile='$PWD/.local/known_hosts' -o IdentitiesOnly=yes"
ansible-playbook -i .local/inventory.ini site.yml
```

The example follows the required `inventory.ini` filename within ignored `.local/`; the `-i` override is deliberate so the checked-in baseline stays fail-closed. Always run from `ansible/` (or explicitly set `ANSIBLE_CONFIG` to its absolute config path). Confirm `ansible-config dump --only-changed` reports this project's configuration and host checking; do not publish private inventory/SSH arguments. Never add password/become-password values. Azure's key-only administrator normally has passwordless sudo; if policy differs, stop and resolve with the owner rather than storing passwords.

### 4. Verify behavior and collect honest evidence

- Capture Screenshot 5 only after the actual passwordless `hostname` succeeds with the verified host key.
- Inspect the three plays and sanitized inventory for Screenshot 6. Capture Screenshot 7 only after the controller gets HTTP 200, the content assertions pass, all metadata probes return 404, and the recap has no failures/unreachable hosts.
- Run the **same** playbook a second time without changing inputs. Expect `changed=0` for the remote host and localhost. Preserve the actual recaps; if changed counts remain, investigate (including the apt cache validity window), do not claim idempotence from syntax/tests. No second-run result has yet been observed.
- Load `http://<actual public_ip>` in a browser for Screenshot 8; the visible URL must match the real output. This is an operator action, not a desktop capture/control instruction executed by the agent. Never present a documentation IP or locally mocked page as Azure evidence.
- Diagnose unreachable SSH by checking approved IP `/32`, VM readiness, key path/user and independently verified host key; never broaden SSH to `0.0.0.0/0`. Diagnose deployment refusal by inspecting the owned document root/release and upstream pin; do not delete an unrelated website or bypass validation. Diagnose wrong HTTP content before taking screenshots; HTTP 200 alone is insufficient.
- Keep every evidence slot marked pending until authentic sanitized evidence exists. The learner must write their own deployment/reflection notes and manually publish a truthful LinkedIn post only after real work, with AI help acknowledged. No post, image or URL has been fabricated.

### 5. Approved cleanup only

After evidence is safely retained, obtain/confirm cleanup approval for this dedicated resource group. Use the **same Terraform state, workspace, private input file, subscription and credentials** as the deployment. Do not use portal deletes, `az ... delete`, broad resource-group cleanup scripts or `-target` shortcuts. Never delete state first or destroy shared coursework.

```sh
# From mini-finance, after scope and cleanup approval:
terraform -chdir=terraform plan -destroy -out="$PWD/.local/cleanup.tfplan"
# Review privately; all resources must belong solely to this Mini Finance state.
terraform -chdir=terraform apply "$PWD/.local/cleanup.tfplan"
```

If untracked/shared resources appear in the group, stop; do not disable the provider's resource-group nonempty deletion safeguard. The owner must verify that the VM, disk, public IP and other dedicated billable resources are removed and confirm billing after cleanup. Only then retire private plans/inventory/known-host entries and archive/delete local state according to retention policy. The first attempt's authorized Terraform cleanup and resource absence were verified as recorded above; final billing verification remains pending. Keep all retained private artifacts until the coordinator verifies evidence and retention requirements.

## Attribution and remaining work

GitHub Copilot authored the infrastructure/playbook preparation and tests, executed the explicitly authorized Terraform cleanup, verified absence and integrated the coordinator's unchanged evidence under user direction. The coordinator launched the actual first apply and captured the native-window images. Upstream Mini Finance belongs to its original authors. The observed capacity failure and scoped cleanup are a factual engineering record—not an invented learner reflection. Earlier AI-assisted inspection also found upstream hidden metadata, motivating the export allowlist. The learner must supply their own issue/fix/learning reflection. Successful VM/site deployment, Screenshots 2, 3, 5–8, remote idempotence and LinkedIn publication/screenshot remain pending.
