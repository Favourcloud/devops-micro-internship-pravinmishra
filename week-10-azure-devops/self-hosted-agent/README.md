# Assignment 1 — Self-hosted Ubuntu agent: offline foundation

Learner: **Eze Favour**. **Source preparation only — assignment not complete.**

This project does not provision, register, install, start, or contact anything. No VM, PAT, agent pool, Online agent, successful Azure run, or screenshot has been verified. All seven [evidence slots](evidence/manifest.json) remain pending and all eight original checklist items remain unchecked. Local test success is not live evidence.

## Deliverables

- [`azure-pipelines.yml`](azure-pipelines.yml): a manual-only, five-minute verification job with a runtime pool parameter, Linux demand, non-root check, and the three required commands. No checkout, dependencies, deployments, or credentials.
- [`validate_candidate.py`](validate_candidate.py): read-only validation of an explicitly supplied, allowlisted JSON candidate; optional SHA-256 comparison of an already acquired archive. It never executes the archive, `config.sh`, shell commands, network requests, package installation, or service operations.
- [`candidate.example.json`](candidate.example.json): deliberately incomplete input, which must fail validation. It is not a host inventory or package pin.
- [`tests/`](tests/): stdlib unit/fixture and contract tests, including original-brief preservation and a real YAML parse using existing Ruby/Psych.

## Offline validation

From the repository root on this macOS workstation, using the already installed system tools:

```sh
env -i PATH=/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network*) (deny file-write*)' \
  /usr/bin/python3 -I -B -m unittest discover \
  -s week-10-azure-devops/self-hosted-agent/tests -v
```

The process sandbox denies networking and file writes, including child processes. Tests use memory fixtures and repository reads; no temporary HOME, caches, package downloads, or global changes are needed. The sandbox is **not** a credential-read isolation boundary; the test code reads only its own source/fixtures, the five Week 10 briefs, and the root README preservation baseline. Do not supply credentials in the environment. Ruby/Psych is used only to parse YAML into JSON; no YAML-provided commands execute. Parser success is not Azure server-side validation. If these exact tools are missing, stop and choose a reviewed local runner; do not silently install dependencies or drop sandbox protections.

A future human can provide a sanitized candidate file explicitly:

```sh
python3 -I -B week-10-azure-devops/self-hosted-agent/validate_candidate.py \
  week-10-azure-devops/self-hosted-agent/candidate.example.json
```

The committed example intentionally exits **1**. Exit **0** means only that supplied fields pass local policy; exit **2** means invalid arguments/unreadable input. Output contains fixed check codes, never input values. Optional `--archive /approved/local/package.tar.gz` computes a streaming SHA-256 and compares it to the supplied publisher digest without extraction. No archive has been downloaded or hashed in this delivery. A matching hash does not prove the supplied digest is authentic, the host facts are true, or the package is safe. The helper never reads ambient credentials, host configuration, `.agent`, `.credentials`, logs, or HOME. Unknown/duplicate JSON keys, URLs with credentials, and unreviewed compatibility are rejected. Never put a PAT, password, private key, log dump, or command in a candidate file. Real candidates belong in an approved private location, not Git.

`tests/fixtures/simulated-candidate.json` supplies simulated host/account facts and public release coordinates to exercise validation. Its successful checks are **not** evidence of an actual VM, package download, or compatibility review. The 2,048 MiB free-space floor is a conservative local A1 policy, **not** a Microsoft minimum or sufficient capacity for later application builds. Review memory, disk, workspace growth, updates, and budget separately.

## 1. Fresh authorization and VM choice

**STOP before any live action.** Merging source is not deployment consent. Obtain fresh, scoped human approval for the cloud, account/subscription identity, region, SKU/image/architecture, budget and lifetime, current controller SSH `/32`, key handling, ownership, cleanup plan, Azure DevOps organization/project, dedicated pool, and trusted repository/ref. Obtain explicit approval for PAT creation, package acquisition, account setup, registration, service changes and the manual pipeline run. Screenshot capture and social publication are separate decisions. No GUI capture is authorized by this preparation.

Reuse reviewed Week 08 source as a reference, not proof that old resources remain live:

| Reference | Existing behavior | A1 gap that must be resolved before live use |
| --- | --- | --- |
| [Azure VM (Week 08 A1)](../../week-08-terraform/terraform-azure-vm/README.md) / [source](../../week-08-terraform/terraform-azure-vm/main.tf) | Ubuntu 22.04, controller-only SSH, explicit region/SKU, private local state | Password SSH is deliberately enabled for that earlier assignment; it is not the desired key-only agent baseline. A separate reviewed Terraform adaptation is needed for key-only SSH and chosen capacity/architecture. No agent account or agent package is installed. |
| [AWS VM (Week 08 A2)](../../week-08-terraform/terraform-aws-vm/README.md) / [source](../../week-08-terraform/terraform-aws-vm/main.tf) | Ubuntu 24.04 x86_64, key-based controller-only SSH, encrypted 8 GiB root disk, Nginx bootstrap and public HTTP | It is a web lab, not a dedicated agent: remove public port 80 and Nginx through a separately reviewed Terraform adaptation, size the disk, and review outbound dependencies. No agent account or package is installed. |

Neither template is an A1-ready provisioner unchanged. This delivery copies no provider project and changes neither reference. All cloud resource changes must go through reviewed Terraform with approved inputs/state ownership; do not modify AWS/Azure resources manually or run Terraform here. Never inspect or publish earlier private state/tfvars. No cost/free-tier assumption is made. Do not attach a cloud instance role or managed identity to this verification-only agent unless separately justified and approved; builds can otherwise inherit that access.

The host needs outbound TLS/DNS access to the organization's documented Azure DevOps endpoints and approved package/update sources. The agent initiates communication: no inbound agent port is required. Restrict inbound SSH to the approved operator and verify the host key out of band; never bypass host-key checking. Do not open SSH to the world to troubleshoot. Confirm Ubuntu and architecture after authorized SSH with `cat /etc/os-release` and `uname -m`; these commands are instructions, not recorded execution.

## 2. Dedicated pool and short-lived PAT (human only)

1. In the approved organization, create a **dedicated self-hosted pool**, for example `DMI-Week10-A1`. Grant the registering human pool Administrator only where needed; grant the approved project/pipeline use of this pool only. Do **not** grant access to all pipelines. Restrict who can edit the YAML or queue builds. Do not attach this agent to unrelated projects or untrusted/public fork PRs.
2. Create a PAT for **this organization only**, with the shortest practical expiry (for example one day if organizational policy allows). The original brief requires **Agent Pools (Read & Manage)** and **Build (Read & Execute)**; select only those two scopes, not Full access. Microsoft documents that registration alone needs only Agent Pools (read, manage). Build permission is an additional assignment requirement, not an agent runtime requirement; narrow/revoke it as soon as its approved purpose is finished.
3. Use an approved secret manager, not a repository file. Never put the PAT in command arguments, shell history, environment exports, YAML variables, commits, logs, screenshots, transcripts, tickets, or chat. Do not use an unattended token flag. Use only the verified tool's hidden interactive prompt; stop if input is echoed. Disable shell tracing and terminal/session recording before entry. Do not screenshot the token creation result or rely solely on automatic masking.
4. Plan revocation/expiry before use. The registration PAT is not used for ongoing agent communication, but the agent creates its **own persistent credentials**. Revoking the PAT alone does not decommission the agent. Never upload the agent directory or raw diagnostics.

## 3. Dedicated non-root Ubuntu account and package review (human only)

A separately approved administrator prepares one dedicated account named `azdoagent`, with a private home and agent directory (owner-only access), no password login, and no `sudo`, `docker`, `lxd`, disk-access, or other privileged group membership. Keep the SSH/operator administrator separate. Give the service account **no passwordless sudo** and no general sudo permission. Do not use `runAsRoot`, root-run registration, or a blanket sudo bypass. Do not place personal credentials, SSH keys, cloud CLI configuration, or unrelated repositories in its home. One agent per isolated VM; no co-tenants or production workloads.

The administrator may switch to this account for interactive configuration with `sudo -iu azdoagent`; this does **not** grant sudo rights to `azdoagent`. Start from a clean environment, not one containing cloud credentials or a PAT. Under that account, use `umask 077` and create a private, empty directory such as `/home/azdoagent/azdo-agent`. Verify account UID is nonzero, ownership/permissions are restricted, and privileged groups/sudo grants are absent. Check Git (2.9.0 or newer), Bash, `tar`, `sha256sum`, `uname`, `whoami`, `df`, and systemd tooling. The helper validates only a manually supplied summary of these facts; it does not discover or certify them.

Package selection is **pending**:

1. In the dedicated pool's **New agent → Linux** dialog, choose a release supported by the actual Azure DevOps service/server and Ubuntu version. Use **Linux x64** for `x86_64`, **Linux ARM64** for `aarch64`/`arm64`; never select macOS, Windows, 32-bit ARM, or Alpine/musl for this Ubuntu runbook. The helper intentionally accepts only Ubuntu 22.04/24.04 and those two architectures. A newer Ubuntu release needs an explicit support review and helper/test update, not an assumption that “latest” works.
2. Consult the exact Microsoft release's download table and compatibility requirements. Copy the exact version, architecture, HTTPS download URL, release-page URL and **published SHA-256** into a private candidate. Cross-check the host and reviewed release; set `compatibility_reviewed` only after that real review. No selected version or digest is pinned in the live candidate example.
3. Acquire the package only after approval, over HTTPS from the documented Microsoft agent download host. Independently compare its SHA-256 with the publisher table **before extracting or executing it**. Stop on missing metadata or a mismatch; do not generate a digest locally and call it publisher verification. The optional helper archive comparison only checks equality against your supplied digest.
4. Review the archive member paths before extraction (no absolute paths, traversal or unexpected links); extract as `azdoagent` into the private empty directory, not as root. Review the supplied `config.sh` and dependency/service scripts without executing them. The agent bundles its runtime; dependency requirements vary by release. Do not blindly run `bin/installdependencies.sh`: it can contact third-party sources and install packages. An administrator must separately review and approve any missing OS dependencies. Do not install unrelated application tools for A1.

Documentation read on 2026-09-17: the Linux guide describes the 4.x/.NET 8 matrix including Ubuntu 22.04/24.04 x64/ARM64, while the public latest release endpoint returned **v5.279.0**. This difference is a **live compatibility gate**, not a reason to install the latest package blindly. The test fixture uses publicly published v5.279.0 x64 coordinates solely for structural tests; it is not the selected or recommended runtime package.

## 4. Interactive registration and service setup (human only)

Only after the preceding gates and explicit fresh registration approval:

1. As `azdoagent`, in the reviewed agent directory, run **`./config.sh` without token arguments**. Enter the approved `https://dev.azure.com/<organization>` URL, choose PAT authentication, and enter the token only in its hidden prompt. Specify the **dedicated pool explicitly** (do not accept Default), a unique agent name, and a private work directory under the agent directory. Do not replace an existing agent without checking ownership and obtaining approval. Do not enable automatic logon or untrusted job access.
2. Confirm the configuration targets the right pool and agent, without reading or publishing credential files. Capture configuration success only if capture has been separately authorized and the visible output is secret-free. Discard any proposed evidence containing secrets; revoke/rotate exposed credentials immediately.
3. The package generates `svc.sh` after configuration. An administrator reviews it and the exact target path, then performs the following commands **from that reviewed directory**, with an explicit non-root service user:

   ```sh
   sudo ./svc.sh install azdoagent
   sudo ./svc.sh start
   sudo ./svc.sh status
   ```

   These are future human actions, not commands executed by this project. `azdoagent` itself does not gain sudo. Never run the service as root. Verify the actual systemd unit's `User=azdoagent`, active state, expected executable/working directory, and startup behavior. Do not guess a unit name or upload full service environment/log output. Do not run an interactive `run.sh` process alongside the service.
4. In Azure DevOps, verify that this exact agent appears **Online** in the dedicated pool. A local active service alone does not prove registration or connectivity. If Offline, check approved TLS/DNS/proxy reachability, UTC clock, service identity and restricted local diagnostics. Do not disable TLS validation, broaden PAT scopes or open inbound ports as a shortcut. Record actual failures and fixes only after they occur.

## 5. Manually verify the agent

After a human has approved creating/queuing the pipeline:

1. Point a new YAML pipeline at the reviewed source/ref and `week-10-azure-devops/self-hosted-agent/azure-pipelines.yml`. Do not authorize arbitrary repositories or all pipelines to the pool.
2. Use **Save**, not **Save and run**, until ready. Ensure UI trigger overrides, schedules, pipeline-completion triggers and Azure Repos build-validation policies do not auto-queue it. `trigger: none` and `pr: none` disable YAML CI/PR triggers; Azure Repos PR build policies are configured outside YAML. The job additionally requires `Build.Reason == Manual`. That condition is a guard, not a permissions boundary.
3. Use **Run pipeline** on the approved ref and replace `__choose_approved_pool__` with the exact dedicated pool name. The placeholder names no intended pool and must never be created. The Linux demand rejects non-Linux agents; pool membership must ensure all eligible agents are this approved isolated host. If more than one exists, stop and resolve targeting before queuing.
4. The job checks a nonzero UID, then runs `uname -a`, `whoami`, and `df -h`. Confirm it used the intended agent, printed Ubuntu host kernel information, showed `azdoagent`, reported disk usage, and completed successfully. `uname -a` alone does not prove Ubuntu's release: retain the separate Task 3 OS check. Review output for host/user/mount identifiers before sharing. No checkout or PAT is needed in this job.
5. Only an actual successful run with the required output satisfies Screenshot 7. A skipped job, YAML parse, test fixture, local service status, or this runbook cannot substitute for it.

## 6. Evidence and cleanup

The manifest permits only seven exact slot titles and explicit pending state: `captured: false`, `status: pending`, and null path/hash/time/run URL. It contains no tokens, org identifiers, arbitrary notes, images, or fake output. Tests deliberately freeze these pending values for this **offline** delivery. A later authorized evidence change must review/update that contract, record genuine provenance, and validate readable, secret-free captures. Do not fill slots with PNG placeholders, mock UI, or prior unreadable capture failures. Keep the learner's original Notes unanswered until they provide actual platform/org/pool details, issues and resolutions.

Cleanup is also a separately authorized human operation:

1. Disable queueing/use of the dedicated agent; let the approved job finish or explicitly cancel it. Confirm no other workload owns this agent/pool/VM.
2. From the reviewed agent directory, an administrator runs `sudo ./svc.sh stop`, confirms it stopped, then `sudo ./svc.sh uninstall`. As `azdoagent`, run `./config.sh remove` interactively; if authentication is requested, use a fresh narrowly scoped, short-lived PAT via the hidden prompt, then revoke it. Verify server-side removal and revoke the original PAT if still present. Do not treat PAT revocation as agent removal.
3. Retain only approved, sanitized evidence. The agent's credentials, workspaces, diagnostic logs and cached artifacts must remain private and be removed by the approved owner after de-registration. No broad recursive cleanup commands are supplied here.
4. Use the correct reviewed Terraform configuration/state and a separately authorized destroy plan to remove only resources created for this run. Verify disks/public IPs and other billable resources are gone. Do not destroy shared/earlier resources or assume VM shutdown stops all charges. Record cleanup only after verification.

## Sources (public read-only references)

- [Microsoft Linux agent prerequisites, permissions, configuration and service commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/linux-agent?view=azure-devops)
- [Microsoft PAT registration scope and registration-only token lifetime](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/personal-access-token-agent-registration?view=azure-devops)
- [Microsoft agent v5.279.0 published download/checksum table](https://github.com/microsoft/azure-pipelines-agent/releases/tag/v5.279.0)
- [YAML CI trigger](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/trigger?view=azure-pipelines) and [PR trigger / Azure Repos policy distinction](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines)

For actual checks executed on this source, see [offline validation results](evidence/offline-validation.md); no live completion claim is made there.
