# A4 — EpicBook Azure workload source

**Offline-tested source, not provisioned infrastructure or a successful pipeline.**
This is the workload configuration to review and eventually copy into the separate
`infra-epicbook` repository. Neither external A4 repository nor either pipeline is
created by these files. The original brief and its evidence/checklist remain unchanged.

## Defined topology

| Component | Source configuration |
| --- | --- |
| Network | UK South VNet `10.140.0.0/16`; distinct frontend, backend and delegated MySQL `/24` subnets |
| Frontend | Ubuntu 22.04 Gen2, private `10.140.1.4`, Standard public IPv4; public HTTP 80 |
| Backend | Ubuntu 22.04 Gen2, private `10.140.2.4`, separate Standard public IPv4 for restricted direct SSH; application 8080 only from frontend `10.140.1.4/32` |
| Both VMs | `Standard_D2lds_v6`, NVMe, Secure Boot/vTPM, 32-GiB Standard LRS OS disk, key-only `labadmin`; actual image version required, never `latest` |
| SSH | Only separately approved controller and agent global IPv4 `/32`s; other VM inbound traffic denied |
| MySQL | Burstable `B_Standard_B1ms`, fixed 20-GiB storage, seven-day backups, no HA/geo-backup/autogrow; private VNet integration, linked private DNS, public access disabled |
| Database isolation | Port 3306 only from backend `10.140.2.4/32` and within the delegated database subnet; other 3306 inbound denied; default platform/outbound rules retained |
| Database configuration | TLS required, TLS 1.2, empty `bookstore` database with `utf8mb4_unicode_ci`; **no tables, seeding or application execution** |

The backend's public management address deliberately satisfies the existing
[direct-SSH handoff contract](../README.md#validating-the-manual-handoff); its
application port is not public. A private-only backend would require a separately
reviewed agent route or transport extension, not an invented reachable address.
No bastion, NAT gateway, frontend HTTPS, VM extensions, cloud-init, provisioners,
package installation or runtime service configuration is included. `labadmin` is
a privileged provisioning account, **not** the future non-root application or
agent account; Ansible account/privilege boundaries remain to be implemented.

## Protected remote state is a prerequisite

The backend is explicitly `azurerm`, with Microsoft Entra data-plane authentication
and OIDC. The provider also selects OIDC, disables CLI/MSI fallback and automatic
provider registration, and checks the exact approved subscription, tenant, client
and principal. A future pipeline must use a clean credential allowlist: setting
`use_oidc` does not sanitize inherited client-secret/certificate environment values.
Do not place client secrets, SAS tokens or storage account keys in backend files.

**This root does not bootstrap the backend.** Before a live initialization, use a
separately reviewed Terraform state-bootstrap root or an approved, verified existing
backend. That bootstrap is still a delivery gap; do not create it manually with
Azure CLI/Portal. Privately record the exact storage resource group/account/container,
state key and approved identity; verify encryption, disabled anonymous/shared-key
access, narrowly scoped Blob Data permissions, network reachability, blob locking,
versioning/soft deletion and the retention/cost owner. Test denied access for unrelated
identities. `approval.remote_state_ready` is an acknowledgement, not an automated audit.
An ignored `backend.hcl` may hold reviewed non-secret coordinates; never commit it.

No backend is initialized during the offline checks below. `init -backend=false`
is a test-only choice, **not** a live workaround that stores workload state locally.
All real init/plan/apply operations still require fresh authorization. An unsuccessful
plan can perform provider reads; this configuration is not an offline preflight tool.

## Inputs, credentials and lifetime

`inputs.example.tfvars.json` intentionally contains unset values and false readiness
flags and cannot authorize a plan. Do not replace them with test fixtures for a live
run. A4 needs its **own** exact scope, identity, quota/capacity, current image, authentic
SSH host-key procedure, reviewed prices and whole-window allowance. A2's US$10/agent
approval is not an A4 authorization. Estimate both VMs/disks/public IPs, MySQL compute,
storage/backups, state retention and expected traffic; no estimate is supplied here.

- Use a unique `dmi-w10-a4-` prefix and fresh reviewed Ed25519 public key. Keep the
  private key in restricted Secure Files, never Terraform inputs or ordinary artifacts.
- Supply the database administrator password through protected, masked secret-variable
  injection, not YAML, command arguments or a committed tfvars file. The variable is
  **sensitive and ephemeral**, and uses the provider's write-only password argument.
  It must be supplied again for saved-plan application. Increment the explicit password
  version on authorized rotation. Never reuse the administrator account as the runtime
  application user; least-privilege users/TLS/bootstrap remain an Ansible review gate.
- State and saved plans still contain sensitive infrastructure metadata. Keep them in
  independently approved protected storage, never ordinary build artifacts or logs.
  Capture raw plan console output privately too: sensitive input declarations do not
  automatically redact the client-config data source's subscription/principal fields.
  The future infrastructure pipeline must approve and apply the **same immutable saved
  plan**, bind it to the source revision, and recheck expiry/identity before application.
- An A4 window must already be active, be at most 24 hours, and have more than two
  hours remaining at plan **and apply**. Start cleanup at least two hours before expiry:
  the provider documents a MySQL deletion timeout of one hour. Record the fixed UTC
  deadline from first provisioning; reruns/credential renewal must not extend it.
- Readiness flags and `expires_at` tags are **not** schedulers or billing caps. Verify an
  independent cleanup safeguard and end-to-end deletion permissions before creation.
  After any partial failure, preserve private state and reconcile exact resources before
  retrying. Do not erase state or disable deletion protections merely to get a green run.
  Teardown/state-retention handling and live cleanup are not tested by this delivery.

Only four outputs exist: `app_public_ip`, `backend_ansible_host`,
`backend_private_ip`, `mysql_fqdn`. After a genuinely successful apply, review and
manually transfer only those values through the existing handoff validator. Do not
feed it `terraform output -json` objects, raw state or plan JSON. No credentials,
subscription/tenant/principal identifiers or connection strings are outputs.

## Version decision, not a latest-version claim

The existing reviewed Terraform **1.13.5** and AzureRM **4.47.0** installation/lock
are reused; no provider was downloaded. [AzureRM 4.47.0's documented MySQL schema](https://github.com/hashicorp/terraform-provider-azurerm/blob/v4.47.0/website/docs/r/mysql_flexible_server.html.markdown)
supports the write-only password and the `8.0.21` API version selector. That selector
chooses Azure's managed **8.0** line, not a promise that deployed patches stay at 8.0.21.
[Microsoft's version policy](https://learn.microsoft.com/en-us/azure/mysql/concepts-version-policy),
checked on 18 September 2026, lists 8.0 and 8.4 as GA and ends Azure 8.0 standard
support on **31 January 2027**. This source rejects an expiry at/after 1 February;
review/upgrade the provider and application compatibility before then. It does not
silently opt into paid Extended Support or claim to deploy the latest MySQL line.

SKU/image availability, the instructor's older mysql2/Sequelize compatibility,
private DNS, TLS/CA verification, schema alignment and real application operations
remain live gates. No instructor JavaScript or SQL was changed or executed.

## Reproduce the offline checks

From the repository root, with the existing macOS system Python, Terraform and
provider mirror (the example reuses only the A1 **provider binary**, never its
retired credentials, inputs, state or wrappers):

```sh
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
  /usr/bin/python3 -I -B \
  week-10-azure-devops/epicbook/terraform/tests/run_offline.py \
  --terraform .tools/terraform \
  --plugin-dir week-10-azure-devops/self-hosted-agent/azure-vm/.private/tf-data/providers
```

If those tools are unavailable, provide another already-reviewed installation;
the runner does not install anything or retry without isolation. It copies only
source/lock/mock fixtures into a short, invocation-owned private temporary directory,
clears inherited credentials/HOME/configuration, disables downloads/backend/module
initialization, and runs format checking, native validation and **30 plan-only mock
cases**. macOS sandbox-exec denies external networking and writes outside that scratch
(with a `/dev/null` discard exception); local Unix sockets are allowed solely for
Terraform/provider RPC. Scratch is removed on exit. No real Azure plan is generated.

Run the independent read-only stdlib/preservation suite:

```sh
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
  /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)(deny file-write*)' \
  /usr/bin/python3 -I -B -m unittest discover \
  -s week-10-azure-devops/epicbook/tests -q
```

On 18 September 2026: **51 stdlib tests passed** (36 existing, 15 new); native
validation had zero errors/warnings and **30 mocked Terraform cases passed**.
These check source contracts and rejection paths, **not** Azure readiness, remote
state access, service availability, pipeline success, cost, deletion or evidence.
The two repositories, state bootstrap, saved-plan infrastructure pipeline, idempotent
Ansible/application pipeline, live handoff and all six screenshots remain pending.
