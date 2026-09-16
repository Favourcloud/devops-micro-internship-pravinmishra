# Week 09 Assignment 2 — Azure four-host ad-hoc lab

**Learner:** Eze Favour. **Status:** code preparation and local validation, not a deployed lab.

Azure only: four Ubuntu 22.04 hosts named `web1`, `web2`, `app1`, `db1`. Assignment 3 reuses **these same two web hosts**; do not create another pair. The app/db names are inventory roles, not installed application/database services. Copilot assisted implementation, technical explanations and local checks. No learner SSH, provisioning, remote Ansible or firsthand cloud experience is claimed here. Coordinator-supplied genuine source captures are included for A2 slots 1/3/4/5; they do not prove deployed infrastructure.

## Approval and safety boundary

The historical AWS enrollment expired at `2026-09-16T13:30Z`; it is not silently renewed. The coordinator relayed user approval of **US$5 total across temporary Week 09 labs**, allocating **at most US$2 and two hours after apply to A2+A3**, with teardown after evidence. The authorized non-root AWS identity lacks EC2 permissions, so the coordinator selected **Azure only**. Current Azure identity, exact plan, capacity and execution window still require review. An allowance is not a hard billing cap or approval of an unreviewed apply. Never fall back to AWS root/default credentials, change Azure RBAC/provider registrations, IAM/billing, credentials, global SSH/Git settings or other coursework.

`live_execution_approved=false` is the Terraform default. `scripts/lab.py` requires explicit `--approved` for rendering and managed-host operations. A3 has assertions before any remote module. These are accidental-execution interlocks, **not** authorization or a hard spending cap. Do not bypass them for screenshots. No key generation, agent restart, new environment installation or LinkedIn publication is part of this lab.

## Layout and architecture

```text
ansible-adhoc-lab/
├── .gitignore
├── README.md
├── terraform/
│   ├── providers.tf, main.tf, variables.tf, outputs.tf
│   ├── .terraform.lock.hcl
│   ├── terraform.tfvars.example
│   └── tests/lab.tftest.hcl
├── ansible/
│   ├── ansible.cfg
│   └── inventory.ini                 # tracked UNCONFIGURED template
├── scripts/lab.py
└── tests/{test_lab.py,test_ssh_configuration.py}
```

`for_each` defines all four roles. A dedicated resource group, VNet and subnet isolate this disposable lab in **UK South (`uksouth`)**. Four NICs each have a **Standard static public IPv4** and a dedicated NSG. SSH is allowed **only from the controller IPv4 /32**. Only `web1`/`web2` receive HTTP access, also restricted to that /32. An explicit priority-4096 deny blocks all other inbound traffic, including Azure's otherwise-default VNet allowance. App/db have no HTTP/database/application inbound ports. Default NSG outbound access remains available for packages/DNS; subnet implicit default outbound is disabled, with the explicit public IPs supplying outbound connectivity. No NAT Gateway, load balancer or additional service is created.

Each VM is **nonzonal Standard_D2lds_v6** (2 vCPUs/4 GiB each, **eight vCPUs total**), with an explicit **NVMe disk controller**, a **32 GiB Standard_LRS managed OS disk**, managed boot diagnostics, username `azureuser`, password authentication disabled, and the existing controller **public** key. The private key and agent are not changed. The Canonical image is pinned to **`0001-com-ubuntu-server-jammy:22_04-lts-gen2:22.04.202608060`**: the coordinator-reviewed metadata confirms x64, Gen2, NVMe support and a 30 GiB source OS disk that fits the 32 GiB target. [Dldsv6 specifications](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dldsv6-series) and [NVMe compatibility](https://learn.microsoft.com/en-us/azure/virtual-machines/enable-nvme-interface) support this combination. Local NVMe temporary storage is ephemeral: do not use it for application data. A3 deploys to `/var/www/html` on the managed OS disk; no ephemeral OS disk is configured.

The coordinator approved this replacement after B1s allocation failed in the separate A4 lab; A2 itself has **not** applied. Cached UK South Dldsv6-family and regional quotas were both 0/10 used at review. A2's eight cores plus A5's two consume all ten, leaving **no headroom**. D2lds_v6 has zone 2/3 restrictions but no location restriction; this configuration explicitly leaves `zone = null`. Quota/SKU metadata is not a capacity reservation. The A5 single-VM pilot must succeed first, followed by coordinator review of A2's fresh identity-sealed plan and execution window. A4's B1s-only requirement is unchanged.

The OS hostname matches the role. Configuration still expands to **23 managed resources**: resource group/VNet/subnet plus four each of VM, NIC, public IP, NSG and NIC/NSG association. AzureRM provider auto-registration is disabled. A real plan must confirm no unrelated state; mock success does not guarantee allocation or access.

## Cost and lifetime planning

The coordinator-reviewed A5 evidence from **16 September 2026, 19:06 UTC** reuses the public [Azure Retail Prices API](https://prices.azure.com/api/retail/prices) for UK South USD on-demand Linux rates; no duplicate price requests were made for A2. **D2lds_v6 costs US$0.131/VM-hour**, Standard HDD **S4 LRS costs US$1.69/month** (32 GiB), and **Standard static IPv4 costs US$0.005/hour**. The reviewed disk transaction meter is US$0.000625 per 10,000 operations. [validation.json](validation.json) records the decision/evidence hashes. These are public retail estimates, not an account invoice, discount or free-tier promise.

For four VMs, four OS disks and four IPs over two hours: VM compute is **US$1.048**, IPv4 is **US$0.04**, and disks are approximately **US$0.02012**, conservatively prorated over a 672-hour month. Base cost is **US$1.10812**; adding **US$0.50 contingency** gives **US$1.60812**, below the **US$2 A2+A3 allocation**. Account-wide usage and billing delays remain uncertainties; A5 and earlier A4 costs are separate and remain under the coordinator's shared US$5 authority. No snapshots, premium disk tiers, NAT Gateway or extra A3 hosts are configured. Set a named cleanup owner and explicit two-hour deadline before apply. Deallocation still leaves billable disks and static IPs: remove them through reviewed Terraform teardown, not merely Stop. There is no automated budget resource or kill switch in this code.

## Local checks — no cloud or managed hosts

Reuse the Assignment 1 controller environment and Terraform **1.13.5** / AzureRM provider **4.47.0**. Keep the lock file. From this directory, with those executables on `PATH`:

```bash
export PYTHONDONTWRITEBYTECODE=1
export TF_DATA_DIR="$PWD/.local/terraform-data"
export TF_IN_AUTOMATION=1 CHECKPOINT_DISABLE=1
export ANSIBLE_HOME="$PWD/.ansible" ANSIBLE_LOCAL_TEMP="$PWD/.ansible/tmp"
export XDG_CACHE_HOME="$PWD/.cache"
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend=false -input=false -lockfile=readonly
terraform -chdir=terraform validate
terraform -chdir=terraform test
python -m unittest discover -s tests -v
(cd ansible && ansible-inventory -i inventory.ini --graph)
(cd ansible && ansible-config dump --only-changed)
```

SSH multiplexing is explicitly disabled (`ControlMaster=no`, `ControlPath=none`) in both Ansible configurations and the direct hostname wrapper. Deep worktree paths can exceed macOS/Unix control-socket limits; removing persistent control sockets avoids this without weakening host-key verification. The real OpenSSH regressions use only `ssh -G` and local `ssh -O check` (no network), reproduce an overlong legacy socket path, and verify that both labs and the wrapper never use it.

`init` downloads provider packages if absent but does not provision. Reuse an approved existing provider mirror on a space-constrained controller; never mutate the shared cache. All Terraform test runs use `command = plan` with a mocked provider. Tests check four roles, group isolation, instance safeguards, outputs and rejected invalid/unapproved inputs. Python tests exercise rendering, mode 0600, bad/missing/duplicate IP rejection, overwrite/symlink rejection, approval gates and mocked command construction. The inventory graph lists deliberately unresolvable `.invalid` hosts. None of these results proves SSH, running instances, package installation or a successful live Terraform plan.

## Approved live runbook — revised plan review and runtime work gated

Historical B1s read-only plans on **2026-09-16 at 18:20 and 18:28 UTC** each proposed **23 creates, zero updates, zero deletes**, without apply or managed-host connections. The latter has a private subscription identity seal created before planning; the first did not preserve that pre-plan identity binding. Both are preserved as historical evidence and **must not be executed**. They do not describe the D2lds_v6 revision. [validation.json](validation.json) preserves the old plan hashes separately from current offline validation and the approved replacement evidence. The revised source requires a **new unique run, private inputs, state path, pre-plan identity seal and saved plan bound to the committed source**. The coordinator receives the private plan/invocation receipt; it must remain held until A5's successful pilot and A2's exact-plan approval. Actual allocation, deployment, idempotency and cleanup remain unverified. The commands below are a reusable workflow, not a transcript.

1. Obtain current permission for the existing Azure CLI identity, budget/rate approval, cleanup deadline and a plan reviewer. The coordinator owns this gate. Keep account/subscription identifiers and credentials out of evidence. Do not run `az login`, change subscription defaults/RBAC, register providers or escalate privileges. Existing Compute and Network registrations are prerequisites; availability/quota checks do not guarantee successful allocation.
2. From `ansible-adhoc-lab/`, create a new mode-0700 ignored run directory under `.local/`, never reusing an old run. Set absolute `RUN_DIR`, `INPUTS` and `STATE` paths for that run; the operational receipt binds these paths. Copy `terraform/terraform.tfvars.example` to the private inputs file, or generate equivalent `.tfvars.json`. Fill the approved current controller IPv4 `/32` and existing **public** key. Do not create/copy a private key or replace an agent. Confirm the current agent already has the corresponding existing identity. Ansible/SSH retain existing key/agent selection; the fixed ad-hoc wrapper assumes the correct identity is loaded. Set a unique `lab_name` and `live_execution_approved=true` only after approval. Verify neither the selected state nor an unrelated default state exists before a first plan; investigate instead of deleting unexpected state.
3. Use `umask 077`, disable tracing/debug logging, and use an explicit environment without inherited `ARM_*`, `TF_VAR_*` or `TF_CLI_ARGS*` settings. Read the existing Azure CLI account **before planning**, save the subscription ID and account metadata privately with mode 0600, and pin `ARM_SUBSCRIPTION_ID`/`ARM_TENANT_ID` to those saved values. Enable CLI-only auth and disable MSI/OIDC/workload identity. Persist a before-plan seal hashing identity files, inputs, Terraform source/lock files and the committed Git head. Never infer a historical plan's identity from a later account selection. Do not alter global Azure defaults or credentials. Plans/state can contain private account metadata and must not enter Git or screenshots.
4. Run and privately review the live plan. This **does read Azure APIs**, unlike mocked tests. Expect **23 creates**, no updates/deletions/imports, four nonzonal UK South **D2lds_v6** VMs with **NVMe**, image version **22.04.202608060**, the existing managed disks/IP/key boundaries and controller-only ingress. Save plan SHA256 and verify source/identity seals are unchanged. Stop on any surprise. The reviewer must approve the exact saved plan, source revision, A5 pilot result, current quota context and lifetime before apply; a successful plan does not guarantee allocation. Use the private `apply-command.json` exact argv/cwd/replacement environment and matching state/cleanup paths for the coordinated run, rather than reconstructing them from memory.

```bash
# APPROVED LIVE WORK ONLY; absolute paths come from the reviewed run receipt.
: "${RUN_DIR:?Set the new approved run directory}"
: "${INPUTS:?Set the approved private inputs file}"
: "${STATE:?Set this run's dedicated absolute state path}"
umask 077
terraform -chdir=terraform plan -input=false -state="$STATE" \
  -var-file="$INPUTS" -out="$RUN_DIR/lab.tfplan"
terraform -chdir=terraform show "$RUN_DIR/lab.tfplan"
# STOP for A5 pilot and exact-plan review. Only the approved operator continues:
terraform -chdir=terraform apply -state="$STATE" "$RUN_DIR/lab.tfplan"
terraform -chdir=terraform output -state="$STATE" public_ips
terraform -chdir=terraform output -state="$STATE" -json public_ips > .local/public-ips.json
python scripts/lab.py render --approved --outputs .local/public-ips.json \
  --output ansible/inventory.local.ini
python scripts/lab.py render --approved --outputs .local/public-ips.json \
  --web-only --output ../static-web/inventory.local.ini
```

The renderer accepts exactly four distinct globally routable IPv4 strings, refuses missing/extra/null/private/documentation addresses, writes mode 0600 and refuses to overwrite any existing file. A3 selects web1/web2 from the **same** mapping. Files named `inventory.ini` remain safe templates; `inventory.local.ini`, outputs, plans, tfvars and state are ignored. After an instance replacement, retain needed private evidence, remove only the obsolete local generated inventory and explicitly re-render. Never publish actual inventory IPs in source; redacted screenshots can document the mapping.

5. Confirm all four VMs are running and finished booting. Using the approved Azure identity, retrieve each VM's boot-diagnostics log privately (`az vm boot-diagnostics get-boot-log --resource-group <reviewed-lab-rg> --name <reviewed-vm-name>`). Compare its cloud-init SSH host-key fingerprints against `ssh-keygen -lf` on that host's `ssh-keyscan` result. If authenticated fingerprints are absent, stop; a key scan alone is not authentication. Save only matching entries in **`ansible-adhoc-lab/.local/known_hosts`** with mode 0600. Both labs use this task-local file and disable global known-hosts fallback. Do not change the user's global known_hosts, disable strict checking or accept changed fingerprints blindly. Run A2 commands from the documented directory (the wrapper sets its Ansible working directory) and A3 commands from `static-web/`, so relative known-hosts paths resolve correctly. Run the wrapper only after that review:

```bash
python scripts/lab.py adhoc ssh-hostnames --approved --inventory ansible/inventory.local.ini
(cd ansible && ansible-inventory -i inventory.local.ini --graph)
python scripts/lab.py adhoc ping --approved --inventory ansible/inventory.local.ini
python scripts/lab.py adhoc uptime --approved --inventory ansible/inventory.local.ini
python scripts/lab.py adhoc install-nginx --approved --inventory ansible/inventory.local.ini
python scripts/lab.py adhoc start-nginx --approved --inventory ansible/inventory.local.ini
python scripts/lab.py adhoc install-htop --approved --inventory ansible/inventory.local.ini
python scripts/lab.py adhoc nginx-status --approved --inventory ansible/inventory.local.ini
```

The wrapper invokes the assignment's exact module arguments using fully qualified names: `ping`, `command uptime`, `apt name=nginx state=present update_cache=yes --become`, `service name=nginx state=started enabled=yes --become`, `apt name=htop state=present update_cache=yes --become`, and `command systemctl is-active nginx`. It validates the generated inventory before invoking any executable and does not accept arbitrary modules or extra arguments. The SSH step runs `hostname` as `azureuser` on each VM; Terraform sets the VM's computer name to its role. Expected evidence is real `pong`/SUCCESS, uptime, package/service outcomes and `active`, not canned output. Ubuntu's apt/cloud-init may still be busy; wait for initialization rather than killing apt or forcing locks.

6. Continue [Assignment 3](../static-web/README.md) against the same web hosts. Capture A2's 17 numbered slots and LinkedIn slot according to the [pending manifest](../screenshots/assignment-02-manifest.json). Put `Eze Favour` visibly in each genuine terminal/editor/browser capture; redact private identifiers before capture and disclose redactions. CLI logs are not screenshots. No screenshots or posts have been fabricated or published.

## Cleanup — only this lab, after evidence

The coordinator must retain approval for teardown and verify the same dedicated state/Azure subscription/region/code. First preserve sanitized evidence, then review the destroy plan; never use a different coursework directory or delete state to hide resources.

```bash
# APPROVED TEARDOWN ONLY; reuse the exact run's environment, inputs and state.
: "${RUN_DIR:?Set the same approved run directory}"
: "${INPUTS:?Set the same private inputs file}"
: "${STATE:?Set the same dedicated absolute state path}"
terraform -chdir=terraform plan -destroy -input=false -state="$STATE" \
  -var-file="$INPUTS" -out="$RUN_DIR/destroy.tfplan"
terraform -chdir=terraform show "$RUN_DIR/destroy.tfplan"
# STOP: review only this lab's resources, including any partial-apply resources.
terraform -chdir=terraform apply -state="$STATE" "$RUN_DIR/destroy.tfplan"
terraform -chdir=terraform state list -state="$STATE"
```

An empty state list plus approved read-only Azure checks for the dedicated resource group and lab tags should confirm no surviving VMs/disks/public IPs/network resources. The resource-group deletion guard refuses deletion if unexpected resources remain; investigate rather than disabling it or deleting the group manually. Verify deletion even after a failed apply; capture cleanup before marking complete. Do not delete the controller's existing key or agent. Only then retire obsolete local inventory/output files; retain protected state/receipts per the learner's policy. Actual destroy is still pending.

## Real local issues and learning notes

Terraform was absent from the session PATH. A checksum-verified local copy was used initially, then removed in favor of the coordinator's preserved executable. Provider installation encountered shared disk pressure; only this task's duplicate binary/archive was removed, with a byte/hash-verified read-only shared provider symlink used thereafter. An early AWS mock needed plan-phase mock IDs; that draft was then fully replaced by Azure at the coordinator's direction because the allowed AWS user lacks EC2 permissions. Final Azure validation uses seven plan-only mock tests. No live apply or permission escalation was used to solve local preparation issues.

Technical takeaway: Terraform creates the hosts and routing; inventory selects hosts by role; Ansible executes the declared operation using SSH and Python. `ping` is not ICMP and does not prove a website is healthy. These are AI-assisted technical notes, not invented learner experiences. The learner must review the answers and add genuine SSH/inventory experience after authorized execution.
