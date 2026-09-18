# A2/A3 Terraform web targets — offline preparation

These are **separate, human-operated target definitions**, not deployed VMs or
assignment evidence. Neither application pipeline invokes Terraform or Ansible.
The existing A1 agent was removed after its historical successful run; a new agent
needs its own approval and state. Do not reuse an agent as either web target.

| Root | Prepared shape | Current validation / live gate |
| --- | --- | --- |
| `guard/` | Shared explicit approval, assignment, SSH sources, time and estimate contract | Provider-free validation and 19 native **plan** tests passed |
| `aws/` — A2 | One Ubuntu 24.04 x86_64 `t3.micro`, dedicated VPC/subnet/Internet route, scoped SSH, public lab HTTP | AWS schema validation and five native **mock plan** tests passed after explicitly approved provider restoration; a scoped non-root deployment identity and fresh live review remain required |
| `azure/` — A3 | One Ubuntu 22.04 Gen2 `Standard_D2lds_v6` in UK South, separate network, scoped SSH, public lab HTTP | AzureRM schema validation and six native **mock plan** tests passed; fresh identity, quota, image, pricing and live execution remain pending |

Each cloud root declares **eight cloud resources plus one local `terraform_data`
approval resource**. The Azure VM includes its billable managed OS disk; AWS includes
its EBS root disk and provider-created VPC defaults. Resource counts are Terraform
addresses, not a complete list of billable objects. No NAT gateway, database,
managed identity/instance profile, agent registration, provisioner, `user_data`,
`custom_data`, application build or web-server bootstrap is configured.

The [Week08 AWS reference](../../../../week-08-terraform/terraform-aws-vm/README.md)
was not changed: this adaptation removes its Nginx cloud-init and adds the selected
agent SSH source and fresh identity/image/approval gates. A3 follows the reviewed
[A1 Azure VM shape](../../../self-hosted-agent/azure-vm/README.md), but **not its
state, keys, runtime or retired authorization**. It avoids the Week08 React
cloud-init build: all application builds belong on the pipeline agent. Only the
reviewed provider lockfile text is reused, unchanged.

## Fresh decisions required before any cloud command

1. Obtain explicit authorization for the exact source commit, assignment, cloud
   identity, account/subscription, region, target, SSH sources, keys, costs,
   lifetime and cleanup. Do not turn repeated “proceed” messages into a renewed
   time window. These definitions authorize nothing by themselves.
2. **Never use AWS root**, including for access bootstrapping or cleanup. Obtain
   an existing approved IAM/SSO identity through the account administrator. Bind
   `account_id` and the exact non-root IAM-user/assumed-role-session `operator_arn`.
   A changed session requires identity re-review. Azure binds subscription, tenant
   and operator object ID; required resource providers must already be registered.
   Do not enable automatic subscription-wide registration to bypass a failure.
3. Verify the exact regional image and compatibility before filling the null
   input. A2 requires a public Canonical (`099720109477`) available Ubuntu 24.04
   amd64 HVM/EBS AMI with the reviewed Noble gp3 image name. The owner ID is the
   public publisher, not the learner's account. A3 requires an exact Canonical
   `0001-com-ubuntu-server-jammy` / `22_04-lts-gen2` version, NVMe support and the
   selected size's current quota/capacity. `latest` is not accepted. A historical
   image/VM result is not current capacity or compatibility proof.
4. Use a unique assignment-matching prefix and separate hosts: A2 and A3 both
   serve `/var/www/html`. Choose the controller's and fresh agent's **actual egress
   IPv4 `/32`s**, not private addresses, an assumed laptop IP or world-open SSH.
   Shared egress is deduplicated. Verify routing/host trust again after an IP change.
5. Supply a fresh, reviewed **operator public key only**: Ed25519 for AWS, RSA for
   the reviewed Azure path. Check real key encoding, size, ownership and fingerprint
   independently; Terraform's string checks are not cryptographic verification.
   Remove comments/options. Never place private keys, PATs, passwords or cloud
   credentials in inputs, source, Terraform variables, CLI values, logs or screenshots.
   The separate `week10deploy` key belongs to the later Ansible/service-connection step.
6. Review current VM, disk, public-IPv4, transfer and applicable diagnostic/storage
   charges for the entire approved window, including the agent and other hosts.
   No free-tier eligibility is assumed. `estimated_total_usd` is the **combined
   whole-window estimate**, not a per-root quote; repeating `planning_allowance_usd`
   in two inputs does not grant two budgets. Maintain one external resource/cost
   ledger. These roots do not aggregate spending or impose a provider billing cap.
7. Approval must already have started, remain unexpired and last at most four
   hours, with a positive estimate within an allowance of at most US$10. These
   conservative source limits do not replace a fresh grant. Arrange and verify an
   independent, narrowly scoped cleanup safeguard **before apply**, with enough
   margin for failures. No safeguard or paid resource is started by these files.
   Grading retention beyond that window needs separately reviewed permission.

Public HTTP is for non-sensitive internship content only, not credentials or
production use. AWS explicitly permits TCP 80/443 egress for package repositories;
AWS-provided DNS has its own platform behavior. Azure retains standard NSG outbound
rules. Neither is an application-aware egress filter. The key-only administrators
(`ubuntu` / `labadmin`) are for reviewed Ansible setup, **not pipeline deployment**.

## Protected input, plan and state workflow

Inside the selected cloud root, use a fresh owner-only `.private/` directory and
`umask 077`. Prepare `inputs.example.json` as `.private/inputs.tfvars.json`; all null
fields deliberately fail. There is no auto-loaded live variables file. Verify
permissions and keep private keys outside the repository. Terraform state/plans
can contain sensitive metadata in plaintext even when outputs are `sensitive`;
Git ignores and output redaction are not encryption or access control.

Only after the live gates and the root's outstanding offline checks are satisfied,
a human may initialize the locked provider, review an actual saved plan and approve
its exact scope. The following are **prospective commands, not an execution record**:

```sh
terraform init -lockfile=readonly
terraform validate
terraform plan -input=false -var-file=.private/inputs.tfvars.json -out=.private/reviewed.tfplan
terraform show -no-color .private/reviewed.tfplan
```

Sensitive values can hide an entire network-rule block in the text plan. Review
those fields against the protected inputs; if full plan JSON is needed, redirect
`terraform show -json .private/reviewed.tfplan` to an owner-only file under
`.private/`. That JSON is unredacted: do not print, upload or screenshot it.

Check the account/operator again immediately before applying the reviewed saved
plan. Do not change the source, inputs, identity, state or provider between review
and execution; re-plan/review if any changed. Require only the intended eight cloud
creates and local approval object, with no import, replacement or unrelated change.
A plan can authenticate/read APIs **before** lifecycle checks: never run a real
plan as an identity that lacks approval. The identity data is a plan-time snapshot,
not proof that the apply-time session is unchanged.

The guard also checks expiry at apply time before its dependants proceed. It does
**not** cancel a long-running apply, enforce a maximum resource lifetime, prevent
manual bypasses or perform cleanup. It is not an IAM security boundary. Do not use
`-target`, `-refresh=false`, edited saved plans or removed guards for live creation.
After separate review/approval, a human may apply the exact saved plan. Supplying a
saved plan executes **without a further Terraform approval prompt**, even without
`-auto-approve`: obtain explicit confirmation first. These sources never invoke it
automatically.

Keep state and the reviewed provider available until verified cleanup. Do not
reuse another root's backend, migrate old A1/Week08 state or delete state to hide a
partial failure. Stop and inspect a failed apply; identify resources it actually
created and clean up only those owned by this invocation.

## Manual handoff to Ansible and the application pipeline

1. Privately inspect `target_public_ipv4`, `target_resource_id`, `ssh_username`,
   `assignment` and the VPC/resource-group output. AWS uses an ephemeral public IP;
   stop/start or replacement can change it. Azure's Standard static IP is billable
   and exists until destroyed. Neither output proves a listening web server.
2. Authenticate the host key through an approved independent cloud/console channel.
   Then follow the [Ansible target runbook](../README.md) with the exact target IP,
   correct assignment, dedicated deployment public key and fresh agent egress IP.
   Do not use TOFU or transfer the administrator's private key to a pipeline.
3. Perform approved real configuration and unchanged-input idempotence checks.
   Terraform deliberately leaves Nginx/account/marker creation to Ansible. Review
   Azure SSH task host-authentication separately; controller pinning does not prove
   `CopyFilesOverSSH@0` / `SSH@0` enforce it.
4. Only after target and agent acceptance, import/personalize the separately approved
   application and run its real build/test/deploy and automatic-trigger checks.
   Application JavaScript changes, screenshots, learner notes and social posts
   remain distinct authorization/evidence gates, not outputs of this project.

## Cleanup without inventing a new creation window

Within the approved lifetime, use the same root, protected state and original
scoped inputs to prepare a **saved destroy plan** (`terraform plan -destroy` with
`-var-file` and `-out`), review it, then separately approve its execution. Re-verify
non-root/approved identity and exact ownership for cleanup too. Current-time expiry
checks are resource lifecycle preconditions rather than variable validation, so
expired creation approval must not be “renewed” merely to remove owned resources.
Cloud-provider cleanup has **not** been exercised for these new targets.

Verify empty state **and independent cloud absence** of the exact VM, attached
OS/root disk, public IP, network resources and AWS key-pair record as applicable.
Remove/revoke the dedicated service connection/key access after the final authorized
run. Only then clear the invocation's cleanup safeguard. Preserve sanitized receipts
and private records appropriately; an empty local state alone is not cleanup proof.

## Reproducing the offline checks

The [parent stdlib suite](../../README.md#offline-checks) includes 12 read-only
Terraform source contracts using the existing `.tools/terraform` formatter/parser.
Those source checks are distinct from the separately executed provider schema and
mock-plan tests. All original briefs/evidence remain unchanged. The native checks additionally used Terraform **1.13.5**:

- `guard`: `init -backend=false`, `validate` and `test` — 19 plan cases passed.
- `azure`: `init -backend=false -lockfile=readonly`, `validate` and `test` — six mock
  plan cases passed with the existing **AzureRM 4.47.0** executable linked from an
  existing reviewed provider mirror, not copied/downloaded. Terraform checked the
  committed lock; offline mirror initialization reports no registry signature
  authentication, not a fresh online signature verification.
- `aws`: the initial offline-only initialization could not find **AWS 6.64.0**.
  After explicit permission to restore the approximately 195 MB compressed package,
  backend-disabled initialization installed the locked provider in an ignored,
  owner-only cache. Terraform verified the committed checksums and reported it
  signed by HashiCorp. With credentials cleared and IP networking denied again,
  schema validation and **five mock plan cases passed**. One initial assertion
  depended on computed `user_data_base64`, which is unknown before apply; the native
  test now checks known plan values, while the source-contract suite independently
  rejects any `user_data_base64` configuration. No mock apply was substituted for
  the failed plan assertion, and no live AWS operation was performed by the tests.

For native tests use a cleared environment, `HOME=/nonexistent`, checkpointing
disabled, separate fresh `TF_DATA_DIR`s and a filesystem-only provider mirror
configuration (no registry fallback). Confine all writes and `TMPDIR` to owner-only,
short-path invocation scratch. On macOS the sandbox policy denies external networking
and allows only the local Unix sockets Terraform's provider RPC requires:

```text
(version 1)
(allow default)
(deny network*)
(allow network* (local unix-socket) (remote unix-socket))
(deny file-write* (require-not (subpath "/absolute/owned/scratch")))
```

Replace that scratch path with your actual owned directory; keep the policy and
`TF_DATA_DIR` consistent. Run only `terraform test` with the committed mock providers,
not a normal cloud plan. Fixtures are synthetic; they are not live approval,
published image verification, current prices, application results or screenshots.
No tests register agents, create cloud accounts/resources, install target packages,
run applications or contact AWS/Azure. Real target provisioning, saved-plan expiry
rejection, runtime compatibility, idempotence, deployment and cleanup remain live
acceptance gates.
