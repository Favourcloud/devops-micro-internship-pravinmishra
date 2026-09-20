# A2 workload teardown — disabled source, not an installed service

[destroy.py](destroy.py) is a separate executable path for **only** the A2 AWS web target and the reused A1 Azure-agent root. It does not extend the canary worker or its permissions. No independent runner, state facility, cleanup identity, schedule, workload canary or deployment has been created or accepted by this delivery. The [example](request.example.json) is unarmed; every acceptance gate is false. **Workload cleanup readiness remains false**, including in successful executor receipts.

This closes a source-execution gap, not the live-acceptance gate. The existing Azure Repos application source, shared PAT, original briefs and historical evidence are unchanged. There are no new screenshots or application-run claims. See [runtime authorization](../../../README.md#runtime-authorization-remains-separate) and the [independent recovery design](../recovery/README.md). Earlier windows and allowances do not authorize this executable.

## What the executable does

For each independently approved request, it:

1. Validates a fresh **destruction-only** authorization window, exact source/tool hashes, immutable original resource expiry, resource IDs, external backend coordinates, state lineage/serial/hash, and supporting acceptance-receipt hashes. The authorization must explicitly cover automated destroy planning and application within this exact inventory. Booleans and hashes are operator bindings, **not proof that approvals, custody, independence or permissions exist**.
2. Requires a separately prepared, private GitHub-hosted recovery job and isolated temporary credentials. It checks the Azure service-principal account/token metadata and, for AWS, a live STS identity for the exact `dmi-w10-a2-cleanup-*` assumed role. No IAM user/root fallback, PAT, SSH key handoff, login or credential creation is implemented. JWT decoding binds metadata; it is not independent signature verification. Native Azure authentication and successful server requests remain necessary.
3. Verifies the copied Terraform source/lockfiles, approved input hash, default workspace, local-module cache and a pre-initialized **external Entra-authenticated Azure Blob backend**. A local backend, canary storage, unexpected nonempty backend options, SAS/shared keys, extra source files and dirty source checkout fail closed.
4. Pulls and binds the populated remote state, reads the complete supported cloud inventory, creates a **fresh destroy-only saved plan**, reads that actual binary through `terraform show -json`, and validates every planned deletion. It rejects an incoming/reused plan file: otherwise an opaque saved plan could carry a different backend/configuration than the inspected workspace. No external binary plan is trusted.
5. Rechecks the live inventory, state and freshly computed binary-plan hash, then applies **that exact saved file**, with input disabled and state locking enabled. There is no unsaved/auto-approved apply, direct cloud delete, import, state removal, backend initialization/migration or force-unlock operation.
6. Requires empty managed remote state **and actual cloud absence**. An already-empty matching state still needs cloud absence and reports zero deletions, not a successful canary exercise. Failures are sanitized. With two `--request` arguments, one cloud's failure does not skip the other request; the process returns nonzero if either fails.

The process reuses the canary worker's owned-process timeout handling: SIGINT first, a 30-second persistence/unlock grace period, then only its own process group if necessary. Every command is bounded by the separate cleanup-authority deadline. There must be more than 1,300 seconds remaining before the initial state read (including an empty-state retry) and again before application. This is a conservative execution guard, not a cloud completion-time or billing guarantee.

**Creation expiry is not a reason to retain resources.** An overdue workload can be destroyed under a separately valid cleanup grant without changing its original expiry. Native Terraform 1.13.5 tests confirm both exact builtin creation guards can be destroyed with expired/disabled creation inputs. Terraform reports skipped creation/variable checks as `unknown` in destroy plans; the validator accepts this only for the pinned roots' declared variables and resources being deleted. Failed/error checks and foreign check addresses remain rejected. Unknown creation checks are not reported as passed.

## Supported inventory and limitations

| Scope | Explicit Terraform addresses | Implicit resources and safeguards |
| --- | --- | --- |
| AWS A2, `eu-west-2` | Eight addresses from [`target/terraform/aws`](../../target/terraform/aws/main.tf): VPC, subnet, internet gateway, route table/association, security group, operator key pair and EC2 instance; plus `module.guard.terraform_data.authorization` | Exact root volume and primary ENI, with deletion-on-termination verified; only the approved default route table, security group and ACL. Refuses other instances, interfaces, subnets, EIPs, gateways, endpoints, peerings, transit attachments, extra disks or ownership-tag mismatches. Final reads separately check VPC, instance, key pair and root-volume absence. |
| Reused Azure agent | Eight addresses from [`self-hosted-agent/azure-vm`](../../../self-hosted-agent/azure-vm/main.tf): group, VNet/subnet, public IP, NSG, NIC/association and VM; plus `terraform_data.authorization` | Exact implicit OS disk in the dedicated group. Refuses foreign group resources, additional VM disks/NICs/extensions, VNet peerings, extra subnets, private endpoints and foreign IP configurations. The provider override refuses nonempty-group deletion and enables OS-disk deletion. Final verification requires the exact group to be absent. |

The Azure agent deliberately retains the reused root's `dmi-w10-a1-*` namespace and `week-10-assignment-01` tags. **Select a freshly authorized A2 agent, not a retired historical A1 ID/state/key.** The A3 `.target` Azure root, EpicBook, bootstrap/recovery resources, persistent operator IAM, shared issuers and other assignments are outside scope.

There is no atomic cloud-inventory lock against other administrators. A protected workflow lock serializes cooperating jobs only; exclusive namespace ownership and no external writers must be accepted independently. Inventory responses and permission behavior are fixture-tested, not live-accepted. This first version accepts a complete supported populated state or a verified empty retry. **Partial teardown/state-write failures deliberately require independent operator recovery**, preserving the state, lock, private failure artifacts and exact IDs. Do not force-unlock, manufacture an empty state, delete `errored.tfstate`, relax inventory guards or automatically import orphaned disks. An independently tested partial-failure recovery procedure is still a live gate.

VM deletion does not remove Azure DevOps pool registrations, SSH connections or pipeline definitions. Authorized service/agent unregistration should precede normal teardown; independent cloud cleanup must not depend on a controller PAT. A stale registration or connection requires separately approved Azure DevOps follow-up. This executable is not bootstrap teardown and cannot delete the state facility or its own identity.

## External-state integration — prepare only after fresh approval

The original roots still use local `.private/terraform.tfstate`; **they have not been edited or migrated**. The two `*.backend.tf.example` files are inert override templates. Terraform override-file merging replaces the original backend block; the native offline probe validates this without initializing a remote backend. Azure's template additionally sets the group/OS-disk safeguards. It is not a new provider project.

Before any workload canary creation, the independent owner must review the exact private source copy plus override, provision no facility from this script, and establish:

- An existing/independently approved private state store outside disposable workload/control groups, with durable versioned state, tested retrieval/restore and real lock behavior. Backend discovery/data permissions must survive deletion. A different name alone does not prove independence. No bootstrap state or only recovery copy may depend on resources/identity being deleted.
- Separate scoped workload cleanup identities and effective permission tests. Existing canary permissions **cannot terminate EC2 or delete these VMs** and are unchanged. AWS metadata reads are regional; deletes must be restricted to the approved resource IDs/namespace. Azure inventory/discovery reads must remain possible after group deletion, without broad write permissions.
- A private trusted recovery repository/job independent of Azure DevOps, the Mac and disposable identities. Restrict workflow refs, protected approvals, state access and credentials; no untrusted code, fork PRs or public plan/state artifacts. `GITHUB_ACTIONS`/`RUNNER_ENVIRONMENT` are context checks, not cryptographic hosting proof. No workflow or repository is installed here.
- Tested notifications, cancellation, separate-cloud failure handling, successful workload-canary deletion/absence, empty-state retry and partial-failure recovery. Bootstrap/control-plane teardown and its independent state custody remain separately pending.

For future authorized jobs, make an **invocation-owned** `0700` directory below `RUNNER_TEMP` and expose it as `W10_RECOVERY_TEMP`; do not change the shared temporary directory. Each request uses this layout:

```text
<owned-root>/<cloud>/
  request.json             # owner-only, approved metadata; no credentials
  home/                    # isolated 0700 home
  azure/                   # isolated 0700 native Azure CLI WIF cache
  guard/main.tf            # AWS only: exact sibling guard source
  root/
    main.tf, variables.tf, .terraform.lock.hcl
    versions.tf, cloud-init.yaml    # Azure agent only
    backend_override.tf    # exact corresponding .example bytes
    cleanup-inputs.json    # owner-only approved original inputs
    .terraform/            # already initialized with approved, verified providers/backend
```

Use `umask 077` during private preparation. Do not copy README/test files into `root/`, add automatic tfvars, reuse a plan, use another Terraform workspace or allow another process to alter this bundle. Backend initialization must be independently approved and use the committed lockfile read-only; the executor never downloads providers. Before initial workload creation, use this same reviewed external-state arrangement, rather than creating disposable local-only state first. Any migration of existing state is a separate reviewed operation, not permission to inspect or reuse old private records.

The request contract is enforced by `validate_request`:

- `cloud` is `aws` or `azure_agent`; all eight address-to-ID bindings are mandatory. `auxiliary` contains `root_volume`, `primary_eni`, `default_route_table`, `default_security_group`, `default_network_acl` for AWS, or `os_disk` for Azure. IDs must come from actual approved state/inventory, not guessed names.
- Both scopes need the independently verified Azure subscription, tenant, cleanup client and principal IDs for external state. Azure-only requests set AWS identity fields to null. AWS requests bind the exact account/cleanup-role ARN and use only an already-issued temporary environment session, including its session token.
- Backend fields identify the external group/account/container and exact `<prefix>/<cloud>.tfstate` key. `lineage`/`serial` and `state_sha256` bind **canonical raw `terraform state pull` JSON**: sorted keys, compact separators, UTF-8, no newline, finite values. State remains private. A new authorization may be needed after state changes; no automatic state-hash rebinding occurs.
- `source_commit` is the reviewed 40-character commit containing this executor; `terraform_sha256` is the independently verified Terraform 1.13.5 executable hash. `inputs_sha256` hashes the exact private input-file bytes. Approval and restore hashes identify genuine protected records, not fixtures. The example intentionally provides no identities, resources, hashes, dates or accepted gates.

Only after those gates and a fresh destruction grant, a prospective invocation is:

```sh
python3 -I -B week-10-azure-devops/application-pipelines/cloud-cleanup/workloads/destroy.py \
  --request "$W10_RECOVERY_TEMP/aws/request.json" \
  --request "$W10_RECOVERY_TEMP/azure_agent/request.json" \
  --terraform /approved/verified/terraform
```

Keep plans, state, inputs, credentials and raw provider diagnostics private. Never put tokens in command arguments, shell history, commits, screenshots, tracing or logs. The executor captures native output and emits only bounded status/count/hash metadata. Native WIF login and temporary credential issuance are **outside** this executable and must be reviewed separately. Preserve necessary private recovery records under an explicit retention decision; no automatic scratch/state deletion is performed during execution.

## Actual offline validation

The final local checkpoint passed **108 cleanup tests** (including 42 workload tests) and **4 readiness-handoff tests**, each in normal and optimized mode, plus all 65 local file/heading links in the three changed guides. The unarmed CLI returned `unarmed` with readiness false and no credentials or cloud calls.

These commands use existing tools, cleared environments and no credentials. The first denies all network/filesystem writes except discard-only `/dev/null`; its synthetic runner never launches cloud commands. Repeat with `-O` before `-I` to verify guards do not rely on assertions. The focused selector below runs the 42 workload tests; use `test_*.py` for the full cleanup suite.

```sh
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
  /usr/bin/sandbox-exec -p \
  '(version 1)(allow default)(deny network*)(deny file-write*)(allow file-write-data (literal "/dev/null"))' \
  /usr/bin/python3 -I -B -m unittest discover \
  -s week-10-azure-devops/application-pipelines/cloud-cleanup/tests -p 'test_workload*.py' -q

/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
  /usr/bin/python3 -I -B \
  week-10-azure-devops/application-pipelines/cloud-cleanup/tests/run_workload_guards_offline.py \
  --terraform .tools/terraform
```

The native harness uses only Terraform's **builtin local** `terraform_data`, the exact AWS guard module and exact Azure guard with identity replaced by fixture locals. Both guards were first created locally with valid fixture inputs, then destroyed with expired/disabled creation inputs; the Azure cleanup fixture also changes the operator. No cloud provider is loaded, no provider package is installed, no remote backend is initialized and no cloud resource is created or removed. Each Terraform subprocess has network denial and write access only to its own temporary fixture, which the harness removes. It also checks both override templates' formatting and native backend-type replacement. These are source tests, not assignment evidence or hosted cleanup acceptance.
