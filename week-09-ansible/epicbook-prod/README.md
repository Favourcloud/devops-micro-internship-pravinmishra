# Assignment 5 — EpicBook Azure pilot and preparation

**Status: genuine VM pilot provisioned, application deployment failed, cleanup
verified; checkout corrected and tested offline only. This is not a completed or
production-certified application deployment.**

The parent coordinator executed the individually approved live stages on
16 September 2026 against frozen source
`49c70a333b0671f9e75c61363aaab4a580c712ee` and create-plan SHA256
`65d3b78f94b21b93c77eebe8da463f8c00957ef84ee14c44e2906e03d87e1520`:

| Actual stage (UTC) | Observed result |
| --- | --- |
| Apply 20:08:26–20:10:35 | 11 creates, 0 updates/deletes; Terraform exit 0 |
| Outputs 20:40:51 | Authenticated state, outputs, VM, managed OS disk and boot collection |
| Trust/SSH/inventory/ping 21:05–21:06 | Fresh authenticated host-key match, passwordless hostname check, displayed inventory and real pong |
| Deploy 21:07:29–21:14:28 | Ansible exit 2; web recap ok=20, changed=12, unreachable=0, failed=1 at Git checkout |
| Cleanup verified 21:37:27 | Reviewed saved plan: 11 deletes only; apply exit 0; empty state/outputs; authenticated RG, exact VM, OS disk and public IP absent |

Cleanup completed before the original **22:08:26 UTC** deadline. Resource absence
is not a zero-charge/final-billing claim. See the sanitized
[pilot outcome receipt](evidence/pilot-outcome.json) and
[approved live capture hashes](evidence/pilot-captures.json). These are derived
from preserved actual artifacts, not replayed output. No cleanup PNG is claimed.

Source slots **1, 3, 6, 7, 8 and 11** retain their reviewed scope; live slots
**2 and 4** now have genuine captures. Three new **10a–c corrected-source frames**
bind the post-cleanup working-tree snapshot; original pre-fix images remain
unchanged history. Slot 1 remains a historical 43-file tree at `a15fc8c`, not the
final file count. Slot 5 still lacks a valid numbered PNG despite genuine
inventory/ping; the proposed
220723 image belongs to A2 and is excluded. The deployment-failure PNG is
supporting evidence, **not successful slot 12**. Live application/database,
HTTP/browser, remote second-run idempotence, LinkedIn and video remain pending.

The original [Ansible capture receipts](evidence/source-captures.json) and
[tree/Terraform receipts](evidence/infrastructure-source-captures.json) are intact.
Unchanged Ansible views still match their recorded source; historical EpicBook
views are checked against their original Git revision, not relabeled current.
The [corrected-source receipt](evidence/corrected-source-captures.json) records
source SHA256 `f35f24479485f49a0f62e72d798f3a974d3ec1d68fac2cd38fad06d4608b71e3`,
verified before and after each new capture. HEAD `49c70a3` at capture did **not**
contain that fix; the later committed role must match this working-tree hash.
These source images are not evidence that the correction was re-deployed.
Screenshot 8d's editor-selected Python 3.9.6 is not controller evidence; actual
CLI validation uses Python 3.13.3. See
[the complete brief](../assignment-05-production-grade-epicbook-terraform-and-ansible-roles.md)
and [status manifest](evidence/assignment-05-manifest.json).

No credentials, state, subscription/account IDs, private logs or real inventory
are committed. Approved screenshots intentionally retain the temporary public lab
address/hostname. No application JavaScript was changed. GitHub Copilot assisted
implementation, diagnosis and local checks; these notes are not an invented
learner reflection or Assignment 6 evidence.

The never-applied B1ms and intermediate D2lds plans remain historical and must not
be executed. The final applied plan/approvals are also historical, not reusable
permission for another run. A reviewed private TMPDIR relocation was an explicit
exception, not exact full-environment equality. Original failed preflights,
failed trust, private artifacts and source seals remain unchanged. No current
cloud or runtime authorization exists; future allocation capacity is not promised.

## Source research: this is not a static website

The repository is linked in the [Week 08 Assignment 4 resources](../../week-08-terraform/assignment-04-deploy-epicbook-application-on-aws-using-terraform.md#resources).
Earlier [Week 06 Assignment 4](../../week-06-aws-cloud/assignment-04-deploy-epicbook-on-ubuntu-vm-and-mysql-rds.md)
also requires Node/npm/MySQL, but its generic port-3000/API description must not
replace inspection of the actual source:

- Repository: <https://github.com/pravinmishraaws/theepicbook>
- Reviewed immutable revision: [`763becebb8d3f5663a76bb30facddc25be63cfd5`](https://github.com/pravinmishraaws/theepicbook/tree/763becebb8d3f5663a76bb30facddc25be63cfd5).
- [`server.js`](https://github.com/pravinmishraaws/theepicbook/blob/763becebb8d3f5663a76bb30facddc25be63cfd5/server.js)
  runs Express/Handlebars on `PORT` (default **8080**) and listens only after
  `db.sequelize.sync()`. `/` queries MySQL. `public/` contains assets, not a complete
  static application; `views/` holds server-rendered templates.
- [`models/index.js`](https://github.com/pravinmishraaws/theepicbook/blob/763becebb8d3f5663a76bb30facddc25be63cfd5/models/index.js)
  selects `config/config.json` using `NODE_ENV`. Its existing **production** config
  reads **JAWSDB_URL**, so no JS or tracked configuration patch is necessary.
- SQL lives in `db/BuyTheBook_Schema.sql`, `db/author_seed.sql` and
  `db/books_seed.sql`; all target **bookstore**. These scripts are **not safe to
  replay** over existing tables/data.
- The instructor's [installation guide](https://github.com/pravinmishraaws/theepicbook/blob/763becebb8d3f5663a76bb30facddc25be63cfd5/Installation%20%26%20Configuration%20Guide.md)
  uses Amazon Linux `yum`, Node 17 and MySQL 5.7. Those old runtime versions must
  not be blindly installed on Ubuntu 22.04. This preparation instead pins Node
  **22.23.2 LTS** and uses Ubuntu's maintained `mysql-server-8.0` package. Full
  compatibility on Ubuntu/MySQL remains a live test gate.

## Layout and boundaries

```text
epicbook-prod/
├── terraform/azure/         # dedicated RG, VNet, subnet, NSG, NIC, IP, one VM
│   ├── .terraform.lock.hcl
│   ├── versions.tf / main.tf / variables.tf / outputs.tf
│   ├── terraform.tfvars.example
│   └── tests/secure_vm.tftest.hcl
├── ansible/
│   ├── ansible.cfg / inventory.ini / site.yml / requirements.yml
│   ├── group_vars/web.yml
│   └── roles/
│       ├── common/tasks/main.yml
│       ├── nginx/{tasks,handlers,templates}/
│       └── epicbook/{tasks,handlers,templates}/
├── scripts/                 # local verification, upstream probe, inventory renderer
├── tests/                   # local contracts and execution-rejection tests
└── evidence/                # honest preparation/source manifests, no secrets
```

Terraform uses AzureRM **4.47.0**, Terraform **>=1.9,<2**, region **uksouth**,
**nonzonal Standard_D2lds_v6** (2 vCPUs/4 GiB), a **32 GiB Standard_LRS managed OS disk** and one
billed **Standard static public IPv4**. Azure encrypts managed disks at rest using
platform-managed keys; host encryption/customer-managed keys are not claimed.
Dedicated RG, VNet, subnet, NIC and NSG resources do not reuse other assignments.
SSH is IPv4 `/32` controller-only; HTTP 80 is public; an explicit deny rule blocks
other inbound traffic, including Azure's default VNet-wide allowance. There is no
3306/8080 ingress, external database, NAT gateway, load balancer, managed identity
or extra storage account. Default Azure outbound access remains available for
packages; egress restriction is a production follow-up.

The Ubuntu 22.04 Gen2 image pins Canonical's `0001-com-ubuntu-server-jammy` offer,
`22_04-lts-gen2` SKU and **22.04.202608060** version. Its exact UK South metadata
reports V2/x64, `TrustedLaunchSupported`, `SCSI, NVMe`, an active image and a 30 GiB
OS disk. This v6 size is NVMe-only, so `disk_controller_type = "NVMe"` is explicit.
Secure Boot/vTPM remain enabled. Application files and MySQL stay on the managed
OS disk; the included 110 GiB temporary NVMe disk is not used for persistent data.
SSH password authentication is disabled. Managed boot diagnostics supports an
authenticated Azure boot-log fingerprint check before trusting SSH. No SSH keys
are generated by Terraform, no credentials are outputs, and no provisioners or
custom-data scripts execute configuration behind Ansible. Resource-provider
registration is disabled to avoid unsolicited subscription mutations.

The coordinator changed the selected cloud from AWS to **Azure only** after the
AWS non-root profile failed its EC2 authorization check. No AWS alternative or
AWS resource configuration remains in this project. This is a permission-based
scope decision, not permission to use AWS root or modify IAM.

### Reviewed replacement eligibility and cost — 16 September 2026

One cached UK South SKU/usage response reports no D2lds_v6 location restriction,
but zones 2/3 are restricted: **do not set a zone**. The Dldsv6 family and regional
quotas each had 0 used/10 allowed cores. A5's two cores plus the separately prepared
A2 fleet's eight exhaust both limits; this is not reserved quota or capacity.
That eligibility check did not allocate resources or change quota/billing/identity.
The separately approved genuine A5 allocation and subsequent cleanup are recorded above.

Official Microsoft documentation supports [Dldsv6 Gen2/x64 and Standard HDD](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dldsv6-series),
[D-family/Ubuntu 22.04 Trusted Launch](https://learn.microsoft.com/en-us/azure/virtual-machines/trusted-launch),
and [Ubuntu 22.04 Gen2/Trusted Launch NVMe images](https://learn.microsoft.com/en-us/azure/virtual-machines/enable-nvme-interface).
The pinned AzureRM provider schema supports the explicit NVMe controller.

Public USD consumption prices, excluding Spot/Windows: D2lds_v6 **$0.131/hour**
versus D2nls_v6 $0.134/hour; S4 32 GiB Standard HDD **$1.69/month**; Standard IPv4
**$0.005/hour**; the current primary disk transaction meter **$0.000625/10,000**.
A conservative 672-hour monthly disk divisor gives A5 approximately **$0.27703**
for two hours, or **$0.77703 including a $0.50 contingency**. This is an estimate,
not a hard billing guarantee; variable I/O, egress/diagnostics, prior lab charges
and the combined $5 limit still require the coordinator's oversight. The separate
A2 four-VM estimate is $1.60812 including its own $0.50 contingency. Each remains
below its $2 allocation; no free-tier/credit assumption is used. Pilot **only A5**
after exact new-plan approval, before considering A2's fleet.

Role order is exactly **common → nginx → epicbook**, preceded by controller-only
approval/inventory guards. The localhost play rejects missing approval or empty
inventory during normal invocation. The first web pre-task repeats approval and
single-target checks using the original host's variables, before fact gathering
or any SSH; `--limit web` cannot skip those checks. The inventory renderer also
rejects reserved, private, loopback, multicast and documentation addresses and SSH
argument injection. Do not bypass these safeguards with hand-edited inventories,
extra-variable overrides, `--start-at-task` or `--skip-tags always`.

- `common`: apt refresh/upgrade; baseline git, curl, unzip,
  software-properties-common plus CA certificates, ACL and xz support. Reboots are
  reported, never performed automatically; SSH hardening is not applied blindly.
- `nginx`: installs without auto-starting the default site, renders the vhost,
  enables its symlink, removes the default, tests config before start and tests
  again **before** its reload handler. Neither `root` nor `alias` points at source.
  Hidden paths, server-side files/config/SQL are denied in both modes.
- `epicbook`: immutable clone into `/opt/epicbook/source`, owned by
  `epicbook-deploy:epicbook` with restrictive umask. A deployment-user-owned
  **0700 metadata parent** `/opt/epicbook/git-metadata` allows Git to create the
  **previously uncreated** child `repository.git`; its ownership and 0700 mode
  are enforced after checkout. Precreating that child would reproduce the actual
  pilot failure. The root-owned application ancestor is not made group-writable,
  and cloning does not run as root. The nonlogin runtime account `epicbook` can
  read but not own/write source or traverse private Git metadata. Nginx's
  `www-data` user is not added to the application group.

### Two explicit modes

1. Default `app_runtime_enabled: false`: prepares the private source and returns
   **503**, not a fake static success page. This does not satisfy Tasks 9–10.
2. Opt-in runtime: installs MySQL 8 locally, binds MySQL and X protocol to loopback,
   creates `bookstore`, imports the ordered SQL scripts **only** into an empty DB,
   verifies nonzero authors/books and writes a root-only revision marker. Nonempty
   DB plus missing/wrong marker stops for human recovery instead of replaying SQL.
   Creates an application-scoped account, installs checksum-verified Node 22 and
   locked npm dependencies as the deployment user, and renders a root-only `0600`
   systemd environment file. `NODE_ENV=production`/`JAWSDB_URL` use upstream's
   existing interface. Passwords are vaulted, URL-safe, hidden from task logs and
   template diffs. No generated DB passwords go into Terraform state.

The service uses a separate identity, read-only system protection, no capabilities,
private temporary files and localhost-only systemd IP filtering. **Upstream itself
binds wildcard port 8080**, not specifically 127.0.0.1; the security group and
systemd filter protect it without modifying JS. Verify filter support on the VM.
Nginx proxies all application routes (not just `/api/`) to 127.0.0.1:8080. Runtime
completion requires a real Nginx HTTP 200 with EpicBook content, not merely service
startup. Database data checks run on every enabled playbook run.

The DB account needs CREATE/ALTER/INDEX/REFERENCES in this schema because upstream
calls `sequelize.sync()`. It has no global or GRANT privileges. Separate migrations
and a DML-only runtime account are a production follow-up, not silently claimed
here. No default `root` DB password is used; administration uses Ubuntu socket auth.

## Local validation (safe to run now)

Use an existing POSIX controller with Python, PyYAML, Jinja2, Ansible, ansible-lint,
OpenSSH at `/usr/bin/ssh`, `/usr/bin/false` for the non-networking proxy test,
and `/usr/bin/git`. Retain full repository history for historical source-capture
verification; the tests do not fetch missing commits.
Tested: Python 3.13.3, ansible-core 2.21.4 / Ansible 14.4, ansible-lint 26.8.0,
`ansible.mysql` **5.2.0**, Terraform **1.13.5**. The collection is pinned in
`ansible/requirements.yml`; install only if missing, into a task-local collection
path, not the shared controller. No dependency installation happens in verify.sh.

```bash
# From epicbook-prod; commands may also be supplied as absolute executable paths.
export TERRAFORM_BIN=terraform PYTHON_BIN=python3
export ANSIBLE_PLAYBOOK=ansible-playbook ANSIBLE_LINT=ansible-lint
# Optional: TF_PROVIDER_MIRROR=/absolute/read-only/provider-cache
bash scripts/verify.sh
```

This performs format checking, backend-disabled init using the checked-in provider
lock, Terraform validation and **12 mocked tests**, including rejection of the
superseded B1ms size and assertions for nonzonal NVMe/pinned-image/managed-disk
contracts, Ansible syntax/production lint, and **24 local tests**. These verify
approved PNG/source hashes and normal unapproved/unconfigured execution rejections, plus
`--limit web` missing/false-approval and invalid-target rejection subtests that
never invoke their recording SSH stub. Positive source-only/runtime preflights,
both normal and `--limit web`, use the documented inventory renderer and must
reach only that non-networking stub at fact gathering; they intentionally stop
before any role executes. The missing/false-approval regressions reproduced the
reviewed bypass before the web-play guard was added, then passed. An additional
real `/usr/bin/ssh` test evaluates configuration with `-G` and a deliberately long
inherited ControlPath, then uses `ProxyCommand=/usr/bin/false` to stop without any
network or credential access. Multiplexing is explicitly disabled with
`ControlMaster=no` and `ControlPath=none`: a short Ansible RPC temporary directory
alone does not prevent macOS's 104-byte SSH socket-path limit. Strict host-key
checking remains mandatory. Verification disables cloud credential discovery.
A short unique `/tmp/w09-a5-verify.*` is cleaned on exit: long macOS paths otherwise
caused Ansible's Unix-socket RPC startup to fail. Init may download the provider if
no mirror is supplied; it does not query Azure. Shared provider reuse is read-only,
with its binary SHA256 checked against the coordinator's verified source and the
provider lock retained for registry checksums.

The new Git regression first reproduces the existing-metadata failure with real
`/usr/bin/git` (exit 128). A separate local fixture runs the actual directory,
Git and post-clone permission tasks with only paths/principals adapted, local
connection, privilege escalation disabled and a harmless notification handler.
It checks a pinned commit different from upstream HEAD, source/private metadata
modes, current UID/GID ownership, `.git` indirection and a genuinely unchanged
second Ansible run. A non-writable fixture ancestor models the relevant write
restriction; it is **not** a Linux multi-user or complete remote-role test.
Git is file-protocol-only, global/system Git config and hooks are disabled, and
short owned temporary directories are removed. These tests neither run the
production site playbook locally nor contact a server.

Historical compatibility test in a **disposable pinned upstream checkout**:
Node 22.23.2/npm 10.9.8 `ci --omit=dev --ignore-scripts --no-audit --no-fund` installed
107 packages without changing either upstream manifest. Server syntax, six runtime
imports, Sequelize model construction and an actual Handlebars render containing
a fixture book title passed. The reproducible probe verifies all 19 recorded source
file SHA256s against `evidence/upstream-source.json`. It did **not** start HTTP or
connect to MySQL.

To repeat after obtaining the upstream revision in disposable local storage:

```bash
# Verify /usr/bin/git -C "$UPSTREAM" rev-parse HEAD matches the pinned SHA first.
# NODE and NPM_CLI must point to the checksum-verified Node22 distribution.
(cd "$UPSTREAM" && "$NODE" "$NPM_CLI" ci --omit=dev --ignore-scripts --no-audit --no-fund)
python3 scripts/verify_upstream.py --source "$UPSTREAM" --node "$NODE"
```

Node checksums were retrieved from
<https://nodejs.org/dist/v22.23.2/SHASUMS256.txt>:

- Linux x64 `.tar.xz`: `d60acfe00a2932254bb0ad20e01b0d74397a0875595de719654b214f4b03f307`
- macOS x64 `.tar.gz`: `58e99022c2ff89395576cc7fd4d98cea24bb68081475d5f88b801ee8729fb026`

Npm reported deprecated `debug@4.1.1`; no audit/remediation or lifecycle scripts were
run. Pinned old upstream dependencies are a production review gate, not an assurance
of security. Local MySQL, Nginx and Linux systemd were unavailable to that probe.
The later genuine pilot did pass the Nginx role's pre-start configuration check
and started Nginx before checkout failed. It did not complete the separate live
site/config capture, SQL/runtime installation, service sandbox verification or
end-to-end idempotence.

## Future authorized rerun — no current execution permission

**Stop until the coordinator verifies the current Azure identity/subscription,
plan, SSH key custody, SKU capacity, budget, expiry and teardown owner.** The later
aggregate cloud approval does not authorize this branch to apply on its own. A5's
cap is US$2 within the combined US$5 lab limit, with a maximum of **two hours after
apply**; this is a limit, not a price quote. Do not assume free-tier eligibility,
renew expired enrollment, change IAM/RBAC or reuse earlier-course state.
A1/A2/A3/A4/A6 remain separate.

1. Copy `terraform/azure/terraform.tfvars.example` to ignored `terraform.tfvars`
   and fill the approved subscription UUID, unique lowercase alphanumeric
   `run_id` (6-16 characters), controller `/32` and **public** key. Verify that
   `week09-a5-epicbook-<run_id>-rg` is absent before a fresh lab plan; never import
   or overwrite existing resources to bypass a collision.
   Keep the private key external. Use only the centrally approved Azure identity;
   no login/account switching or permission changes are automated here.
   Recheck the reviewed nonzonal D2lds_v6 eligibility, combined family/regional
   quota and compute/IP/disk budget without assuming capacity. Keep the explicit
   NVMe controller and exact reviewed image; never reuse the historical B1ms plan.
   Ensure the two-hour maximum fits the remaining aggregate budget.
2. Use the dedicated state directory. Review the saved plan for new A5 resources
   only, SSH restriction, Canonical image, disk size and absence of billable extras.
   Keep state, inputs, plans, JSON and logs private (files 0600, directories 0700).
   These future commands need explicit authorization before execution:

   ```bash
   umask 077
   mkdir -p .local
   terraform -chdir=terraform/azure init
   terraform -chdir=terraform/azure plan -out="$PWD/.local/a5.tfplan"
   # Only the authorized operator/coordinator, after reviewing the exact plan:
   terraform -chdir=terraform/azure apply "$PWD/.local/a5.tfplan"
   terraform -chdir=terraform/azure output -json > .local/outputs.json
   ```

3. Independently verify the SSH host fingerprint using authenticated Azure managed
   boot diagnostics (cloud-init's printed host-key fingerprints), matching it to
   the candidate public host key before writing `.local/known_hosts`. If that
   trusted fingerprint cannot be obtained, STOP; never disable host checking or
   blindly trust `ssh-keyscan`. Generate the inventory; the renderer
   does not read private keys, initiate SSH or overwrite an existing file:

   ```bash
   python3 scripts/render_inventory.py --outputs .local/outputs.json \
     --private-key /absolute/path/to/private-key \
     --known-hosts "$PWD/.local/known_hosts"
   ```

   The tracked `ansible/inventory.ini` is intentionally empty; use generated
   **inventory.local.ini** for real commands. Archive/remove only the old local
   generated inventory after re-verification when the ephemeral IP changes.
   First verify `ssh` with the same key/known-hosts options and `hostname`, then
   `ansible -i inventory.local.ini web -m ansible.builtin.ping` from `ansible/`.
   Neither check is authorized simply by successfully running the renderer.

4. Review the source probe and remaining compatibility risks. Before attempting
   the real MySQL/Node lab, explicitly accept that it is still an integration
   test. Create an encrypted local Vault file via `ansible-vault create` (no
   passwords in shell history, command arguments, plain tracked vars or logs):

   ```yaml
   deployment_approved: true
   app_runtime_enabled: true
   app_runtime_compatibility_acknowledged: true
   vault_epicbook_db_password: "<new random 32-128 character A-Z/a-z/0-9/_/- password>"
   ```

   Save as `.local/runtime.vault.yml`. `acknowledged` means the operator accepts
   the known test gate, not that integration has passed. Never use the displayed
   placeholder as a password. Then, from `ansible/`, after approval:

   ```bash
   ansible-playbook -i inventory.local.ini site.yml \
     -e @../.local/runtime.vault.yml --ask-vault-pass
   ```

   Do not treat fresh-host `--check` as a working deployment simulation: packages,
   checkout and database must exist for later tasks. Syntax/mock checks above are
   the non-mutating preflight. Source-only mode is not teardown of an existing DB.

5. On the approved VM inspect `nginx -t`, the vhost, `systemctl status epicbook`,
   and listener/firewall state without displaying the environment/password.
   Confirm real books/authors from MySQL, the homepage with books, gallery/cart
   flows and asset loading through the public IP. Check HTTP 404 for `/.git/config`,
   `/.env`, `/config/config.json`, `/db/books_seed.sql` and `/server.js`. A 200 status
   alone cannot prove DB correctness or cart behavior. Do not submit a 503 as success.
6. Run the **same approved playbook again** and save its actual recap. Expected
   stable dependencies/seeds are skipped, but apt updates or a required reboot can
   cause legitimate changes. Investigate every unexplained change; do not invent
   `changed=0`. Never delete seed markers or replay SQL to make a check pass.
   On partial import, stop, back up and inspect the schema. Recovery/migrations
   need their own reviewed decision; no automatic destructive reset is provided.
7. Capture each of the 15 numbered screenshots separately with sensitive data
   excluded, then update the manifest and original checklist only from real proof.
   LinkedIn publication, video and the learner's reflection remain human actions.
8. Retain the dedicated lab for Assignment 6 **only** within the approved budget
   and expiry. Otherwise stop and record the block. After approved evidence work,
   back up anything required, then have the authorized operator create a **saved
   delete-only plan** using the exact bound state, inputs, TF_DATA_DIR and account.
   Independently review every deletion before separately approving application
   of that saved plan, not an unreviewed fresh `destroy`:

   ```bash
   terraform -chdir=terraform/azure plan -destroy -out="$PWD/.local/a5-delete.tfplan"
   # Stop for exact-state/delete-only review and separate explicit authorization.
   terraform -chdir=terraform/azure apply "$PWD/.local/a5-delete.tfplan"
   ```

   Verify empty state/outputs, authenticated RG absence and the exact actual VM,
   OS managed disk and public IP absence. Retain sanitized proof without claiming
   zero cost. Teardown deletes the root-disk database. The completed pilot already
   followed the saved-plan workflow; its artifacts must not be reused for a new lab.

## Production gaps and Assignment 6 handoff

HTTP is deliberately required by this assignment, but real production needs a
trusted domain/TLS, patch/dependency review, tested backup/restore, monitoring,
log retention, external durable DB/HA and a migration plan. One VM is one failure
domain. Do not store real customer data or call this production-ready merely
because the role names are reusable. Password rotation must be coordinated with
service restart; server source is immutable/pinned and never publicly served.

The A6 baseline is `ansible/site.yml`, `ansible/group_vars/web.yml`, the three role
directories and fresh approved inventory/successful recaps when later available.
The pilot VM is deleted, its inventory is historical, and complete A5 runtime
success is still a prerequisite—not supplied by the offline checkout correction. There
is **no A6 risk script, Claude transcript, auto-fix or evidence** in this change.
A6 must obtain its genuine **Claude Code plan before creating the risk script**,
then preserve human-only application of the proposed Ansible change. A5's Copilot
notes and local mocks cannot substitute for that sequence. Do not alter the live
baseline or extend the cloud budget while waiting for the human step.
