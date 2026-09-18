# Assignment 4 — EpicBook handoff preparation

**Eze Favour · Offline preparation, not a completed assignment.**

This folder provides a read-only validator for the four-value manual
Terraform-to-Ansible handoff, a deterministic JSON inventory formatter, and
findings from the actual pinned instructor source. It does **not** provision
infrastructure, create repositories, run Ansible, install Node packages, execute
instructor JavaScript or SQL, register an agent, or produce submission evidence.
The [original assignment](../assignment-04-automate-epicbook-deployment-with-dual-pipelines.md)
remains unchanged, with all 40 checklist items and six screenshot slots pending.

## Two-repository delivery boundary

| Repository | Required responsibility | Current gate |
| --- | --- | --- |
| `infra-epicbook` | Terraform, private Azure Storage remote state, reviewed saved-plan approval/apply pipeline, four non-sensitive outputs | Repository, infrastructure source, Azure identity/scope, prices, retention budget and live run pending |
| `theepicbook` | Reviewed application source, idempotent Ansible and a separate application pipeline | Repository import, runtime compatibility, database/TLS bootstrap, protected SSH access and live run pending |

These are separate future deliverables, not folders pretending to be two existing
repositories. A1's imported **assessment** repository does not satisfy either
EpicBook repository requirement. No A4 infrastructure is inferred from the
retired A1 VM or an earlier assignment.

## Validating the manual handoff

After a genuinely successful, approved infrastructure run, manually copy only:

- `app_public_ip`: frontend public, globally routable unicast IPv4 address;
- `backend_ansible_host`: backend direct SSH IPv4 address, public or RFC1918;
- `backend_private_ip`: backend's RFC1918 IPv4 address for the frontend proxy;
- `mysql_fqdn`: canonical lowercase `<server>.mysql.database.azure.com` name.

Start with `handoff.example.json`; its deliberately unset `null` values **fail**
validation. Populate an ignored `handoff.local.json` only from reviewed real
outputs. Record the infrastructure revision/run and approval separately; the
four-value handoff is not provenance or authorization.

From this directory:

```sh
python3 -I -B ci/validate_handoff.py < handoff.local.json
```

For JSON inventory on standard output, without creating files or connecting:

```sh
python3 -I -B ci/validate_handoff.py --inventory < handoff.local.json
```

The inventory has `frontend` and `backend` groups, distinct logical host names,
`ansible_host` values and only `backend_private_ip`/`mysql_fqdn` as shared
variables. The formatter does not set SSH users, private keys, privilege
escalation, host-key bypasses or SSH command arguments. If a reviewed deployment
needs an inventory file, save it privately as ignored `inventory.local.json` and
validate it with the deployment's actual `ansible-inventory` version first.
Ansible is not required by, or invoked during, this folder's tests.

The direct-SSH contract rejects a shared frontend/backend address. A private
SSH target must equal the backend private address. DNS SSH names, bastions,
ProxyJump and nonstandard SSH ports need a separately reviewed transport
extension; do not work around a rejection by disabling host authentication.

The helper rejects unknown/missing fields, duplicates, nested Terraform output
objects, null values, nonstandard JSON, oversized input, malformed hosts,
connection strings, reserved addresses and shell/pipeline-command fragments.
Errors do not echo input keys, values or command-line arguments. Successful
output contains the allowlisted values you supplied: verify they really are
non-sensitive and approved before sharing them. Never pipe Terraform state,
plan JSON, an unfiltered output dump, credentials or a complete database URL
into this helper. Git ignore rules are only a convenience, not secret storage.

**A passing result proves syntax and this narrow address contract only.** It
performs no DNS, SSH, HTTP or Azure query and cannot establish resource ownership,
agent reachability, host trust, NSG rules, private DNS routing, MySQL private
access, TLS, current resource existence or a working application. A matching
MySQL hostname is not proof that public database access is disabled.

## Actual upstream constraints

Source: [pravinmishraaws/theepicbook at `763bece`](https://github.com/pravinmishraaws/theepicbook/tree/763becebb8d3f5663a76bb30facddc25be63cfd5).
`sources.json` records the exact public revision and SHA-256 values read on
18 September 2026. No application checkout, dependency installation or execution
was needed. Digests identify reviewed bytes; they are not evidence of runtime
compatibility or a comprehensive dependency audit.

1. **Application topology:** `server.js` serves static files and Handlebars pages
   with Express, defaulting to port **8080**. Nginx on the frontend must proxy to
   the backend **private** address, including application/API routes. This is not
   the React static-build deployment from A3. Keep the backend application port
   non-public and MySQL on private access in a separate database subnet.
2. **Configuration:** `models/index.js` selects `config/config.json` using
   `NODE_ENV`, defaulting to `development`. Upstream `production` uses
   `JAWSDB_URL`; that branch constructs Sequelize from the URL alone and does
   **not** pass the remaining JSON options. Simply adding TLS options alongside
   `use_env_variable` is therefore insufficient. A reviewed runtime-only
   `production` configuration must use the direct configuration branch, with
   explicit Azure host/database/user/password and verified TLS options. Do not
   copy the upstream development password or deploy it as a default.
3. **Secrets and TLS:** render runtime configuration only on the backend through
   secret-aware Ansible tasks (`no_log: true`, `diff: false`, restrictive owner
   and mode). Keep the database password in an authorized secret pipeline
   variable and the SSH private key in Secure Files. Do not print configuration,
   use password-bearing command arguments, embed connection strings in YAML, or
   disable certificate validation. Review Microsoft's current Azure MySQL CA/TLS
   guidance and prove TLS/private DNS with the chosen Node/mysql2 versions.
4. **Runtime compatibility:** the lockfile is version 3 and pins mysql2 2.1.0,
   Sequelize 6.3.0, Express 4.17.1 and express-handlebars 5.0.0. `package.json`
   does not declare Node engines. The instructor installation guide targets
   Amazon Linux 2, MySQL 5.7 and Node 17; do not run its installer or treat those
   obsolete instructions as an Azure/Ubuntu compatibility test. Select and test
   a supported runtime before live deployment. No npm or lint run is claimed.
5. **Database bootstrap:** the reviewed schema uses `bookstore` and unconditional
   `CREATE TABLE` statements. `server.js` also calls `sequelize.sync()` before
   listening. Review schema/model alignment, seeding and narrowly scoped runtime
   privileges before execution. Do not blindly rerun schema/seed SQL or assume
   `mysql_db` imports are idempotent. Require a versioned bootstrap guard, reject
   partially initialized/conflicting schemas, and verify a second Ansible run
   changes nothing unexpectedly. Never resolve a mismatch by dropping live data.
6. **Persistence evidence:** models include `Cart`, `Checkout` and a `Cartbook`
   association; the cart POST route creates a cart and associates a book. These
   source observations are not proof of a successful checkout or persisted rows.
   Verify a real database-backed product and an approved test cart/order action,
   correlating the result with MySQL without exposing customer or credential data.
7. **Personalization without JavaScript edits:** `views/layouts/main.handlebars`
   has the shared body layout. A separately reviewed HTML/Handlebars change can
   display Eze Favour and the actual deployment date. Do not invent the date or
   mark the name/date requirement satisfied before the real page is visible.

## Remaining execution gates

- Fresh, bounded Azure scope and retention budget for two VMs, networking,
  private MySQL and remote state; no retired A1 approval is reusable.
- Dedicated infrastructure/application identities and an approved connection
  model. Retain isolation from untrusted repository changes.
- Real Terraform definitions and an exact reviewed saved plan; approval before
  apply; protected state and plan handling. Saved plans can contain secrets too:
  do not publish raw plan/state files or JSON in ordinary artifacts or logs.
- An explicitly reviewed route from the self-hosted agent to both SSH targets,
  authentic host keys, least-privilege non-root accounts and no blanket sudo
  bypass. Inventory formatting does not establish any of these.
- Actual idempotent Ansible, persistent service, TLS-enabled database connection,
  Nginx, live workflow verification and a documented teardown/retention decision.
- Six genuine readable screenshots, both repository URLs, application URL,
  human reflections where required, and separately authorized LinkedIn evidence.
- A5 additionally needs healthy A4 pipelines and the **actual supplied** triage
  kit. A public filename search did not locate the instructor's script; that is
  not proof it does not exist privately. Do not author a substitute kit or invent
  failures/recovery evidence. Claude execution remains a separate gate.

## Credential-free local tests

From the repository root, using the system Python already available on macOS:

```sh
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
  /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)(deny file-write*)' \
  /usr/bin/python3 -I -B -m unittest discover \
  -s week-10-azure-devops/epicbook/tests -v
```

The suite uses in-memory fixtures, including explicitly synthetic addresses that
are never contacted. It checks input rejection, deterministic inventory shape,
non-echoing failures, no network/process/file-write API use in the helper, source
metadata and unchanged A4/A5 briefs. It does not run an application, Ansible,
Terraform, SQL, Azure Pipelines or a cloud API. No screenshots or reports are
presented as live assignment evidence.
