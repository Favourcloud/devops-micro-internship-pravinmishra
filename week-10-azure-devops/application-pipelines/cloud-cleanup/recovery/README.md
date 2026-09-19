# Bootstrap recovery and canary-creator review — source only

**Design, offline structural-review tooling and an inert fixture-review workflow template, not an installed recovery controller.** No backend has migrated, recovery identity/role has been created, permission has changed, teardown has run, or hosted capacity has been verified by this delivery. The existing worker remains canary-only and `config.example.json` remains unarmed. This closes a source-preparation gap, not a live readiness gate.

## Selected preparation route — separate private GitHub Actions project

The user delegated the technical choice. Prepare a separate private GitHub Actions recovery project so eventual recovery does not depend on the Azure DevOps organization, self-hosted application agent or disposable cleanup identities. This selects a source-preparation route, **not repository creation, hosting expenditure, credential use or cloud authority**. The exact private repository, protected state store, identities, billing/quota and retention still require owner approval. Reuse an existing independently managed facility if the owner identifies one rather than creating a duplicate.

The [fixture-review workflow template](review-fixtures.github-actions.yml.example) is a deliberately small first component, **not a recovery executor**:

- It remains outside this repository's `.github/workflows/` and has an `.example` suffix. Even if copied unchanged, its literal `false` job guard prevents execution. Only manual dispatch from `main` is permitted; there is no push, PR or scheduled trigger. Private visibility and an unresolved exact-repository guard are additional conditions, not proof of an approved facility.
- It sparse-checks out only five public files from [frozen source `e027755ef2d33e0145dd1476d48201da4aa4f4cb`](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/e027755ef2d33e0145dd1476d48201da4aa4f4cb/week-10-azure-devops/application-pipelines/cloud-cleanup): the reviewer, its non-authorizing example, synthetic tests and two bootstrap source files read by those tests. It never accepts real plans, state, resource inventories, credentials or arbitrary source-ref inputs. Updated source needs a separately reviewed pin and hash-binding update; this template cannot certify subsequent changes automatically.
- The only action is [checkout v6 pinned to `d23441a48e516b6c34aea4fa41551a30e30af803`](https://github.com/actions/checkout/commit/d23441a48e516b6c34aea4fa41551a30e30af803), resolved from public GitHub metadata on 19 September 2026 UTC. Its public metadata specifies Node 24. No action package was downloaded or run locally. A future run would use only GitHub's ordinary ephemeral checkout credential with `contents: read`, not a PAT; credential persistence, global safe-directory configuration, submodules and LFS are disabled.
- The sole run step checks the source SHA and runs **only `test_recovery.py` synthetic fixtures**, in normal and optimized Python modes, with an empty environment, `HOME=/nonexistent`, `-I` and `-B`. It performs no cloud login, Terraform operation, state download, artifact upload, package installation or cleanup. The five-minute job timeout is not a lab lease, cleanup guarantee or spending cap.
- An empty environment is **not a network sandbox**. The proposed hosted test process is not claimed to have OS-level network/write denial; the current local validation uses the existing macOS sandbox. Before any hosted activation, separately review the exact private repository/branch, runner/runtime availability, permissions, GitHub Actions quota/costs and the changes removing the disabled/placeholder guards. Do not install or enable this template merely because its source is published.

**No hosted run is claimed.** Even a future green fixture-review job would prove only those synthetic checks on that pinned source—not independent state custody/restore, effective cloud permissions, scheduled operation, failure escalation, canary cleanup, bootstrap teardown or assignment evidence. The external state and executor acceptance requirements below remain open. The shared PAT and original expired privilege deadline remain unchanged.

The [template contract tests](../tests/test_recovery_workflow.py) use the existing real Psych parser, reject duplicate YAML keys, check Bash syntax without executing the workflow body, bind the five public files by hash and reject activation/permission/source/command-expansion mutations. Run them through the existing [credential-free source checks](../README.md); they do not require GitHub Actions, cloud access or a new dependency.

## Fixed scope and authority

For the current verified IAM grant, retain lease `1ccbfc4640bd` and the original **19 September 2026, 18:18:03 UTC** privilege deadline. The latest theoretical cleanup target is **16:18:03 UTC**, allowing the required two-hour margin; it is not an approved schedule. Do not reset that clock by choosing another lease, refreshing login, approving this source, or retrying. Temporary sign-in may expire sooner. The old root window is expired. A future window or different principal requires explicit, separately reviewed authorization.

The persistent IAM user and its two managed policies are **excluded from teardown**. Preserve their existing protected state, active attachment override and recovery record. Never apply the earlier inactive creation inputs alone. None of the example metadata below contains a current credential, deployment authorization or actual recovery receipt.

## Independent recovery architecture

Use an **owner-approved private recovery repository/runner and protected remote state outside the disposable control resource group**. Prefer an existing independently managed recovery facility; this delivery does not authorize another persistent cloud installation. If none exists, stop and approve its Terraform scope, retention, costs and lifecycle first.

A suitable proposed hosting arrangement is a separate private GitHub Actions recovery repository, with restricted environments and independently scoped Azure/AWS GitHub OIDC identities. Its actual repository, subjects, identities, quota and billing are all pending. No workflow or service connection is installed here, and this repository's `.github/` is unchanged. Do not substitute a self-hosted Mac job for independent execution.

The dependency constraints matter more than the hosting label:

- Recovery must not rely on the cleanup user-assigned identity, cleanup role, `w10cln<lease>` storage account, canary runner, disposable group or the Mac session.
- **Do not authenticate AWS teardown through the Entra OIDC provider it is deleting.** An independently owned GitHub issuer/trust is one possible separation. An existing issuer is account-wide: never import, replace or delete a shared provider to satisfy this design. Exact ownership and trust review are still required.
- Scope recovery identities to independently verified resource IDs. They need separately reviewed teardown permissions, not administrator access, workload creation, permissions to edit themselves, or unbounded role-assignment deletion. Their own issuer/role/state resources must remain outside the target inventory.
- Prove both ordinary scheduled execution and failure escalation while the Mac/controller is unavailable. A cron expression, copied receipt, configuration boolean or successful metadata read does not prove this.

### State custody before bootstrap

1. Select an existing owner-approved private Blob account/container outside both disposable groups. Use Entra authorization, restricted data-plane access, encryption, versioning and a separately approved retention period. Never use public Git, public workflow artifacts, SAS/shared keys, a console transcript or the disposable account as the only copy.
2. Separately review conversion of the two bootstrap roots from their current **local** backends to that external backend. Use distinct keys per cloud/lease and an exclusive lock. These source roots have **not** been changed or migrated by this delivery.
3. Preserve the original local state and any backup before migration. Verify lineage, serial, resource IDs and bytes/hash privately. Do not replace populated state with an empty backend, use `state rm`, import guessed resources, force-unlock, or run old saved plans. Do not migrate the persistent IAM state incidentally.
4. From the independent recovery runner, prove authorized retrieval of the exact version and a private restore into an isolated review directory without refreshing/applying resources. Verify that its identity cannot read unrelated state or delete its own recovery store. Record allowlisted version/hash/result metadata, not state contents.
5. Ensure the independent recovery actor retains access after all disposable identities/assignments are removed. Storage versions and soft deletion are not proof of off-account durability or continued authorization. State often contains provider secrets even when output values appear harmless.

### Teardown sequence to implement and accept later

| Phase | Required operation and gate |
| --- | --- |
| Quiesce | Disable the canary schedule; confirm no running/queued writers, acquire the real exclusive lock, preserve private state/receipt versions externally. Never automatically force-unlock. |
| Canaries | Exercise the existing separately authorized canary deletion; require actual state and inventory absence. Failed AWS cleanup must not skip Azure recovery, or vice versa. |
| AWS bootstrap | From the independent identity, review the saved Terraform destroy plan for only the owned inline policy, cleanup role and exclusively owned Entra OIDC provider. Confirm no foreign role/policy attachments, issuer consumers or out-of-state dependencies before deletion. Persistent operator policies/user remain excluded. |
| Azure bootstrap | Independently inventory the group and subscription-scoped custom roles/assignments. Require every child and assignment to be owned and accounted for; otherwise stop. Review removal of assignments/federation before identities/storage/group, respecting Terraform dependencies. Role definitions and assignments outside the group are not cleaned merely by deleting the group. |
| Verification | Apply only the separately approved, hash-bound saved plans under still-valid authority; then verify empty respective managed states **and independent cloud absence**. Preserve recovery records externally. A zero-change retry is not first-deletion evidence. |
| Recovery facility | Retain or tear down its separate state/identities/runner only under its own owner-approved retention and lifecycle decision; never destroy the only recovery record to report a clean lab. |

Azure group/storage deletion can cascade into unexpected children and Blob versions that are absent from Terraform's resource list. The structural reviewer below cannot prove cloud emptiness, provider behavior, identity permissions, ordering across jobs, notifications, state-lock safety or receipt authenticity. These remain independent live gates. No bootstrap teardown executor is delivered here.

## Read-only saved-plan structural reviewer

[`review.py`](review.py) accepts a private copy of [`request.example.json`](request.example.json), a supplied Terraform 1.13.5 JSON plan and its saved binary artifact. It invokes **no Terraform, SDK, subprocess, authentication or network operation**, creates no files and never applies a plan. Keep plan/state files private; only hashes, a count and explicitly source-only review booleans are printed. The null example intentionally fails closed.

Populate the inventory from an **independently reviewed ownership record**, not by automatically trusting every resource in the candidate plan. Allowed targets are only addresses from the two bootstrap roots, including optional federation/canary assignment and the built-in lease guard. Partial bootstrap inventories are supported; empty/no-change inventories, canaries, workloads, persistent IAM resources and the named recovery account are rejected.

The reviewer checks strict JSON/metadata, exact artifact hashes, pinned plan format/version, an original window of at most 24 hours, the plan timestamp, reported check results, no drift/deferred changes, root-only prior-state identities, the lease guard, complete delete-only changes and no remaining managed resources. It rejects imports, moves, replacements, deposed instances and duplicate/missing identities/changes. File reads are size-bounded and reject final-path symlinks, directories and special files.

**Limits:** hashes bind the supplied files, but do not prove the JSON came from that binary, that either came from the recorded source commit, or that receipt/hash references represent successful recovery. A trusted separately authorized operator must establish that provenance using the pinned Terraform tool and verify provider/source semantics. The helper does not validate the opaque binary format, inspect credentials, fetch receipts, determine current IAM authority or authorize execution. It can review a historical plan; never treat acceptance as fresh permission to apply it now.

After separately obtaining the genuine private artifacts, structural review is local only:

```sh
/usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
  /usr/bin/sandbox-exec -p \
  '(version 1)(allow default)(deny network*)(deny file-write*)(allow file-write-data (literal "/dev/null"))' \
  /usr/bin/python3 -I -B \
  week-10-azure-devops/application-pipelines/cloud-cleanup/recovery/review.py \
  --request /absolute/private/review-request.json \
  --plan-json /absolute/private/destroy-plan.json \
  --saved-plan /absolute/private/destroy.tfplan
```

Do not paste tokens, passwords or assertions into any argument or metadata field. A successful result always says `execution_authorized: false` and `live_readiness_verified: false`. No review output is assignment screenshot evidence.

## Narrow canary-creator permission proposal — not an IAM policy change

The currently verified operator's `NoOtherAPIs` deny excludes EC2 creation. Attaching another allow policy cannot bypass its boundary/explicit deny. **Use a separately authorized creator principal**, with its identity, MFA/federation behavior, boundary and fixed expiry reviewed independently. Assuming a new role also needs permission; the existing operator is not assumed to have it. No new role, policy, trust or assumption grant is created by this proposal.

The [pinned AWS provider VPC source](https://github.com/hashicorp/terraform-provider-aws/blob/v6.64.0/internal/service/ec2/vpc_.go) was read publicly on 19 September 2026. The unchanged canary source requests only CIDR `10.199.0.0/24`, default tenancy and its five existing tags; no IPv6, IPAM, subnets, endpoints, public IPv4 or compute.

| Candidate capability | Constraint to review before a future Terraform-managed grant |
| --- | --- |
| `ec2:CreateVpc` | `eu-west-2`, exact account VPC ARN namespace; require all five exact request tags and their allowlisted keys. Bind the original lease/expiry, assignment, managed-by and Name values. No general `ec2:*`. |
| `ec2:CreateTags` during creation only | Same namespace and exact request tags, with `ec2:CreateAction = CreateVpc`; no standalone retagging or tag deletion. AWS documents [tag-on-create authorization](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/supported-iam-actions-tagging.html). |
| Read/refresh metadata | Start with `ec2:DescribeVpcs`, `ec2:DescribeVpcAttribute`, `ec2:DescribeNetworkAcls`, `ec2:DescribeRouteTables`, `ec2:DescribeSecurityGroups`, plus `sts:GetCallerIdentity`. Fence EC2 to the region; metadata reads may require resource `*`. Trace helper/waiter calls and prove provider acceptance before claiming this list sufficient. |
| Emergency empty-canary rollback | Separately reviewed `ec2:DeleteVpc` on the exact created VPC, with lease/assignment tags and independent empty-inventory/state checks; do not turn rollback into general network deletion. The existing hosted runtime boundary must stay delete-only. |
| Deliberately withheld | `ModifyVpcAttribute`, tenancy/CIDR changes, standalone tags, instance/subnet/endpoint creation, IAM administration and GuardDuty changes. With the unchanged defaults, the provider's on-create attribute helper skips unchanged values. Drift or changed configuration must stop rather than silently expanding this list. |

The provider's deletion path can inspect and attempt removal of GuardDuty-managed dependencies after `DependencyViolation`. **Do not grant those extra deletion/dissociation actions.** An unexpected dependency fails the empty-canary design and requires investigation; broader provider capabilities are not authorization.

Tag restrictions alone do not enforce the VPC CIDR, exactly one creation, cost, or absence of future writers. Validate the exact saved creation plan and actual inventory, serialize approved writers, and require independent teardown acceptance. Complete action/resource/condition review and real non-root write acceptance are still pending; no valid/effective IAM policy document is claimed by this matrix.

## Costs and local validation

AWS documents [no additional IAM/STS charge](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) and [no additional charge for a plain VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html#pricing). On that narrow no-traffic/no-paid-feature basis, the IAM/empty-VPC incremental estimate is **US$0**, not a total solution estimate or account bill. Azure Blob storage/versions/transactions/egress, Azure Pipelines and independent recovery runner/storage/identity costs remain unquantified. The **US$10 combined planning allowance is not a billing cap**. Current prices, usage assumptions, hosted grants and retention must be reviewed before provisioning.

Run the existing [credential-free stdlib/source suite](../README.md#credential-free-offline-validation), which now includes `tests/test_recovery.py`. Its generated fixtures are synthetic structural cases, not native Terraform plans, real state backups, live permission tests or hosted recovery evidence. No new dependency or provider installation is needed.
