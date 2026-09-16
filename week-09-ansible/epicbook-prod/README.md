# Assignment 5 — EpicBook Azure preparation

**Status: code-ready preparation, not a deployed or production-certified application.**
All 15 numbered screenshots, passwordless SSH/ping, live MySQL/application checks,
public HTTP 200, second-run idempotency, LinkedIn and video evidence remain pending.
See [the original brief](../assignment-05-production-grade-epicbook-terraform-and-ansible-roles.md)
and [the evidence manifest](evidence/assignment-05-manifest.json).

No cloud resources were provisioned by this preparation. No credentials, state,
subscription/account IDs, real inventory or application JavaScript are committed.
Work here did not apply Terraform, SSH to a server, publish anything or perform
Assignment 6. GitHub Copilot assisted research, implementation and local
validation; this is not a learner's firsthand deployment reflection.

A separately authorized **real Azure plan** passed on 16 September 2026:
**11 creates, 0 updates, 0 deletes**, with a previously absent unique resource
group. The sanitized manifest records its source commit and plan SHA256; actual
plan/inputs/logs remain private and ignored. **No apply occurred.** A successful
plan does not prove SKU capacity, VM creation or application operation.

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
**Standard_B1ms** (1 vCPU/2 GiB), a **32 GiB Standard_LRS managed OS disk** and one
billed **Standard static public IPv4**. Azure encrypts managed disks at rest using
platform-managed keys; host encryption/customer-managed keys are not claimed.
Dedicated RG, VNet, subnet, NIC and NSG resources do not reuse other assignments.
SSH is IPv4 `/32` controller-only; HTTP 80 is public; an explicit deny rule blocks
other inbound traffic, including Azure's default VNet-wide allowance. There is no
3306/8080 ingress, external database, NAT gateway, load balancer, managed identity
or extra storage account. Default Azure outbound access remains available for
packages; egress restriction is a production follow-up.

The Ubuntu 22.04 Gen2 image uses Canonical's `0001-com-ubuntu-server-jammy` offer
and `22_04-lts-gen2` SKU. Secure Boot/vTPM are requested; actual SKU support and
capacity still require a live preflight. `latest` must be reviewed/resolved to the
actual image on the VM; an immutable image version is a production follow-up.
SSH password authentication is disabled. Managed boot diagnostics supports an
authenticated Azure boot-log fingerprint check before trusting SSH. No SSH keys
are generated by Terraform, no credentials are outputs, and no provisioners or
custom-data scripts execute configuration behind Ansible. Resource-provider
registration is disabled to avoid unsolicited subscription mutations.

The coordinator changed the selected cloud from AWS to **Azure only** after the
AWS non-root profile failed its EC2 authorization check. No AWS alternative or
AWS resource configuration remains in this project. This is a permission-based
scope decision, not permission to use AWS root or modify IAM.

Role order is exactly **common → nginx → epicbook**, preceded by a controller-only
approval/inventory guard. It aborts the entire playbook before SSH on missing
approval or empty inventory. The inventory renderer additionally rejects reserved,
private, loopback, multicast and documentation addresses and SSH argument injection.
Do not bypass it with a hand-edited inventory or extra-variable overrides.

- `common`: apt refresh/upgrade; baseline git, curl, unzip,
  software-properties-common plus CA certificates, ACL and xz support. Reboots are
  reported, never performed automatically; SSH hardening is not applied blindly.
- `nginx`: installs without auto-starting the default site, renders the vhost,
  enables its symlink, removes the default, tests config before start and tests
  again **before** its reload handler. Neither `root` nor `alias` points at source.
  Hidden paths, server-side files/config/SQL are denied in both modes.
- `epicbook`: immutable clone into `/opt/epicbook/source`, owned by
  `epicbook-deploy:epicbook` with restrictive umask; separate Git metadata directory
  is `0700`. The nonlogin runtime account `epicbook` can read but not own/write the
  source. Nginx's `www-data` user is not added to the application group.

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

Use an existing controller with Python, PyYAML, Jinja2, Ansible and ansible-lint.
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
lock, Terraform validation and **11 mocked tests**, Ansible syntax/production lint,
and **14 local tests**: two unapproved/unconfigured execution rejections with SSH
replaced by `/usr/bin/false`, plus positive source-only and runtime preflight
subtests using the documented inventory renderer and a non-networking SSH stub.
The positive cases must pass all controller guards and reach only that stub at
fact gathering; they intentionally stop before any role executes. Verification
disables cloud credential discovery for these commands.
A short unique `/tmp/w09-a5-verify.*` is cleaned on exit: long macOS paths otherwise
caused Ansible's Unix-socket RPC startup to fail. Init may download the provider if
no mirror is supplied; it does not query Azure. Shared provider reuse is read-only,
with its binary SHA256 checked against the coordinator's verified source and the
provider lock retained for registry checksums.

Observed compatibility test in a **disposable pinned upstream checkout**:
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
of security. Local MySQL, Nginx and Linux systemd were unavailable, so actual SQL
import, service sandboxing, `nginx -t` and end-to-end idempotency remain unverified.

## Future authorized lab runbook — NOT executed by this preparation

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
   Check regional B1ms compute, Standard IPv4 and Standard_LRS disk prices and
   ensure the two-hour maximum fits the remaining aggregate budget.
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
   back up anything required, then have the authorized operator review and run
   `terraform -chdir=terraform/azure plan -destroy`, followed by approved
   `terraform -chdir=terraform/azure destroy`. Verify deletion/no orphan resources
   and retain sanitized teardown proof. Teardown deletes the root-disk database.

## Production gaps and Assignment 6 handoff

HTTP is deliberately required by this assignment, but real production needs a
trusted domain/TLS, patch/dependency review, tested backup/restore, monitoring,
log retention, external durable DB/HA and a migration plan. One VM is one failure
domain. Do not store real customer data or call this production-ready merely
because the role names are reusable. Password rotation must be coordinated with
service restart; server source is immutable/pinned and never publicly served.

The A6 baseline is `ansible/site.yml`, `ansible/group_vars/web.yml`, the three role
directories and the actual approved inventory/recaps when later available. There
is **no A6 risk script, Claude transcript, auto-fix or evidence** in this change.
A6 must obtain its genuine **Claude Code plan before creating the risk script**,
then preserve human-only application of the proposed Ansible change. A5's Copilot
notes and local mocks cannot substitute for that sequence. Do not alter the live
baseline or extend the cloud budget while waiting for the human step.
