# Week 09 Assignment 2 — Azure four-host ad-hoc lab

**Learner:** Eze Favour. **Status:** code preparation and local validation, not a deployed lab.

Azure only: four Ubuntu 22.04 hosts named `web1`, `web2`, `app1`, `db1`. Assignment 3 reuses **these same two web hosts**; do not create another pair. The app/db names are inventory roles, not installed application/database services. Copilot assisted implementation, technical explanations and local checks. No learner SSH, provisioning, remote Ansible, screenshots or firsthand cloud experience is claimed here.

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
└── tests/test_lab.py
```

`for_each` defines all four roles. A dedicated resource group, VNet and subnet isolate this disposable lab in **UK South (`uksouth`)**. Four NICs each have a **Standard static public IPv4** and a dedicated NSG. SSH is allowed **only from the controller IPv4 /32**. Only `web1`/`web2` receive HTTP access, also restricted to that /32. An explicit priority-4096 deny blocks all other inbound traffic, including Azure's otherwise-default VNet allowance. App/db have no HTTP/database/application inbound ports. Default NSG outbound access remains available for packages/DNS; subnet implicit default outbound is disabled, with the explicit public IPs supplying outbound connectivity. No NAT Gateway, load balancer or additional service is created.

Each VM is **Standard_B1s** (four vCPUs total), with a **32 GiB Standard_LRS** OS disk, managed boot diagnostics, username `azureuser`, password authentication disabled, and the existing controller **public** key. The private key and agent are not changed. Canonical's `0001-com-ubuntu-server-jammy` / `22_04-lts-gen2` image uses `latest`; review the resolved image for each plan, as future images can differ. The OS hostname matches the role. Configuration expands to **23 managed resources**: resource group/VNet/subnet plus four each of VM, NIC, public IP, NSG and NIC/NSG association. AzureRM provider auto-registration is disabled. A real plan must confirm no unrelated state; mock success does not guarantee quota/capacity or access.

## Cost and lifetime planning

The public [Azure Retail Prices API](https://prices.azure.com/api/retail/prices) was read during preparation for `armRegionName eq 'uksouth'` and `priceType eq 'Consumption'`, in USD. Returned meters: Linux BS Series **B1s US$0.0118/hour**; Standard HDD Managed Disks **S4 LRS US$1.69/month** (32 GiB); IP Addresses **Standard IPv4 Static Public IP US$0.005/hour**. The IP meter has `isPrimaryMeterRegion=false` but explicitly matches `uksouth`; filtering it out would incorrectly omit IP costs. Recheck rates before plan approval; these are public retail estimates, not an account invoice or a free-tier promise.

For four of each resource, using 730 hours/month to prorate disks, estimated base cost is **US$0.0765/hour**, **US$0.153 for two hours**, or **US$55.82/month** if left running. A US$0.50 allowance for disk operations, boot diagnostics, data transfer, tax and rounding brings the two-hour planning estimate to **US$0.653**, below the US$2 allocation. Account-wide usage and billing delays remain uncertainties. No snapshots, premium disk tiers, NAT Gateway or extra A3 hosts are configured. Set a named cleanup owner and explicit two-hour deadline before apply. Deallocation still leaves billable disks and static IPs: remove them through reviewed Terraform teardown, not merely Stop. There is no automated budget resource or kill switch in this code.

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

`init` downloads provider packages if absent but does not provision. Reuse an approved existing provider mirror on a space-constrained controller; never mutate the shared cache. All Terraform test runs use `command = plan` with a mocked provider. Tests check four roles, group isolation, instance safeguards, outputs and rejected invalid/unapproved inputs. Python tests exercise rendering, mode 0600, bad/missing/duplicate IP rejection, overwrite/symlink rejection, approval gates and mocked command construction. The inventory graph lists deliberately unresolvable `.invalid` hosts. None of these results proves SSH, running instances, package installation or a successful live Terraform plan.

## Approved live runbook — plan checked; apply and remote work pending

With explicit coordinator permission, a real read-only Azure plan succeeded on **2026-09-16 at 18:20 UTC**: **23 creates, zero updates, zero deletes**. It used the existing approved public key, current controller /32 and privately pinned current Azure subscription. No apply or managed-host connection followed. [validation.json](validation.json) records sanitized results and source hashes; the saved plan, inputs and log are private/ignored. Exact-plan approval, actual capacity, deployment, screenshots, idempotency and cleanup remain pending. The commands below are the reusable workflow, not a transcript.

1. Obtain current permission for the existing Azure CLI identity, budget/rate approval, cleanup deadline and a plan reviewer. The coordinator owns this gate. Keep account/subscription identifiers and credentials out of evidence. Do not run `az login`, change subscription defaults/RBAC, register providers or escalate privileges. Existing Compute and Network registrations are prerequisites; availability/quota checks do not guarantee successful allocation.
2. From `ansible-adhoc-lab/`, copy `terraform/terraform.tfvars.example` to the ignored `terraform/terraform.tfvars`; fill the approved current controller public IPv4 `/32` and existing **public** key. The invalid example must not be usable. Do not create or copy a private key. Confirm the current agent already has the corresponding existing identity. Ansible/SSH use the existing key/agent configuration; where selection is necessary, pass `--private-key` to Ansible manually with the existing private path, never place it in Git or replace an agent. The fixed ad-hoc wrapper assumes the correct existing identity is already selected/loaded.
3. In the authorized shell only, privately pin the current subscription with `export ARM_SUBSCRIPTION_ID="$(az account show --query id --output tsv)"`; do not print it or modify global defaults. Disable shell tracing and Terraform debug logging. Set a unique `lab_name` and `live_execution_approved=true` in ignored tfvars **only after** this workflow is authorized. Protect state, plans and outputs with `umask 077`; these can contain the public key and private account metadata even when variables are sensitive. No credentials belong in tfvars.
4. Run and privately review the live plan. This **does read Azure APIs**; do not confuse it with mocked tests. Expect 23 creates, no changes/deletions/imports of existing resources, `uksouth`, the reviewed Ubuntu image/B1s/disk/IP choices and controller-only ingress. Stop on any surprise. The reviewer must approve the exact saved plan, source revision and lifetime before apply. Successful planning is not proof that B1s capacity is available.

```bash
# APPROVED LIVE WORK ONLY, from ansible-adhoc-lab/ with the environment above.
umask 077
terraform -chdir=terraform plan -input=false -out=../.local/lab.tfplan
terraform -chdir=terraform show ../.local/lab.tfplan
# STOP for exact-plan review. Only the approved operator continues:
terraform -chdir=terraform apply ../.local/lab.tfplan
terraform -chdir=terraform output public_ips
terraform -chdir=terraform output -json public_ips > .local/public-ips.json
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
# APPROVED TEARDOWN ONLY, from ansible-adhoc-lab/.
terraform -chdir=terraform plan -destroy -input=false -out=../.local/destroy.tfplan
terraform -chdir=terraform show ../.local/destroy.tfplan
# STOP: reviewer must confirm only the 23 lab resources are destroyed.
terraform -chdir=terraform apply ../.local/destroy.tfplan
terraform -chdir=terraform state list
```

An empty state list plus approved read-only Azure checks for the dedicated resource group and lab tags should confirm no surviving VMs/disks/public IPs/network resources. The resource-group deletion guard refuses deletion if unexpected resources remain; investigate rather than disabling it or deleting the group manually. Verify deletion even after a failed apply; capture cleanup before marking complete. Do not delete the controller's existing key or agent. Only then retire obsolete local inventory/output files; retain protected state/receipts per the learner's policy. Actual destroy is still pending.

## Real local issues and learning notes

Terraform was absent from the session PATH. A checksum-verified local copy was used initially, then removed in favor of the coordinator's preserved executable. Provider installation encountered shared disk pressure; only this task's duplicate binary/archive was removed, with a byte/hash-verified read-only shared provider symlink used thereafter. An early AWS mock needed plan-phase mock IDs; that draft was then fully replaced by Azure at the coordinator's direction because the allowed AWS user lacks EC2 permissions. Final Azure validation uses seven plan-only mock tests. No live apply or permission escalation was used to solve local preparation issues.

Technical takeaway: Terraform creates the hosts and routing; inventory selects hosts by role; Ansible executes the declared operation using SSH and Python. `ping` is not ICMP and does not prove a website is healthy. These are AI-assisted technical notes, not invented learner experiences. The learner must review the answers and add genuine SSH/inventory experience after authorized execution.
