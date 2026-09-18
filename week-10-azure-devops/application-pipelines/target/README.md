# A2/A3 Ubuntu target configuration

**Tested offline preparation, not a configured VM or completed assignment.** This
human-operated Ansible playbook fills the target-configuration gap in the
[application pipeline contract](../README.md). It is never invoked by either
pipeline. Running it against a host **does change that host**: packages, a locked
account, its authorized public key, directories, the dedicated Nginx configuration
and service, and the assignment marker. The input helper is read-only.

## Required decisions before any connection

- Obtain current authorization for the exact cloud identity, target, controller,
  agent, reviewed source commit, package changes, cost, lifetime and cleanup.
  Previous A1 permissions/resources are retired. A planning allowance is not a
  provider-enforced spending cap. Never deploy or create IAM users using AWS root.
- Provision a **dedicated, fresh Ubuntu 22.04 or 24.04 target** through reviewed
  Terraform. A2 requires AWS; A3 needs a separate target. Do not reuse either A1's
  agent host or A2's grading host for A3. Terraform adaptations are **still pending**:
  use the linked Week08 references only after removing their web/app cloud-init
  bootstrap and restricting SSH to the controller and agent's approved `/32`s.
  Do not copy old state/keys or assume an older resource is still running.
- Verify the target image, administrator, fixed public IPv4s and independently
  authenticated SSH host key. This playbook requires an inventory with exactly
  one `week10_web` host and a separate, non-root administrator with reviewed sudo
  access. Do not give the pipeline the administrator's identity or private key.
- Use a dedicated deployment key. Inputs contain only its **single Ed25519 public
  key**, with no comment/options. Keep its private key/passphrase in the approved
  SSH service-connection secret store, never source, CLI values, environment
  exports, logs or screenshots. This playbook does not create or handle PATs.
- Review the Azure `CopyFilesOverSSH@0`/`SSH@0` tasks' actual host-authentication
  support separately. Controller OpenSSH pinning below does **not** prove those
  tasks authenticate the deployment host. Stop live pipeline setup if the required
  assurance is unavailable; the marker does not replace host authentication.
- Agree a grading/retention window before promising a publicly reachable A2 site.
  Public HTTP is only for non-sensitive lab content, not credentials or production
  use. No screenshots, learner reflections or social posts are generated here.

## Review inputs locally

Use an existing reviewed controller with Python 3, OpenSSH and Ansible Core.
Offline syntax validation used Ansible Core **2.21.4** on Python **3.13.3**; Ubuntu
22.04/24.04's system Python meets that release's managed-host requirement. This
is not a live image/package/runtime compatibility result. Recheck compatibility
before selecting a different controller/target version.

In this directory, prepare protected, ignored copies of
`inputs.example.json` → `inputs.local.json` and
`inventory.example.json` → `inventory.local.json`. Null defaults deliberately
fail. Supply only the four `week10_target` fields; set inventory host/IP, approved
administrator and the path to its protected key. Paths are not key contents.
Do not add arbitrary Ansible overrides, dynamic inventory plugins, SSH options,
`--limit`, `--start-at-task`, tags or extra variables that bypass the preflight.
Review the entire static inventory as executable configuration, not untrusted data.

Create `known_hosts.local` containing the **approved target IP and authentic host
public key** verified through a trusted console/cloud channel. A keyscan alone,
TOFU, disabling host checking, or accepting a changed key is not verification.
Local configuration files and public metadata are ignored, but this is not a
license to store private keys/tokens in the repository.

The validator reads only JSON on stdin and never echoes its contents:

```sh
python3 -I -B validate_inputs.py < inputs.local.json
```

A success means **input shape only**, not approval, correct key ownership, identity,
reachability, SSH trust, quota, price or a working target. Reserved/private addresses,
extra fields, duplicate fields (including nested fields), multiline keys, SSH
options and private-key text fail closed. Validate the raw input file before
Ansible parses it; do not normalize away ambiguous configuration. Review the
inventory independently as described above.

## Offline validation versus actual execution

Credential-free syntax check (no target connection):

```sh
ANSIBLE_CONFIG="$PWD/ansible.cfg" ansible-playbook \
  --syntax-check -i inventory.example.json configure.yml
```

Run the [parent's offline test command](../README.md#offline-checks) from the
repository root. Its **74 tests** include 24 target input/source-contract tests,
real YAML parsing and negative cases, in addition to the existing pipeline/payload
checks. These tests deny network and filesystem writes. Separate real Ansible
syntax and in-memory expression checks, plus both Jinja render branches, passed
with network denied and writes confined to owned Ansible scratch. An attempted
controller-only playbook execution was blocked by the sandbox at Ansible's local
RPC startup; it is **not** a successful negative-preflight execution. The guard was
not relaxed. Actual task execution and idempotence remain pending. Use a cleared
environment and never an existing authenticated inventory for offline tests.
These checks are not deployment evidence.

Only after the live gates above are satisfied, a human may review and execute:

```sh
ANSIBLE_CONFIG="$PWD/ansible.cfg" ansible-playbook \
  -i inventory.local.json -e @inputs.local.json configure.yml --ask-become-pass
```

The prompt is interactive and not logged. If the administrator already has
separately approved noninteractive sudo, omit the prompt flag; do not change
sudoers or grant the deployment account sudo to make this command work. Never
add `--diff` or verbose secret-bearing diagnostics. `--check` is not the offline
test: it can still connect and read the actual host, so it also needs permission.

## Behavior and live acceptance gates

- Controller assertions reject missing/ambiguous inventory and mismatched inputs
  before the remote play gathers facts. Remote configuration requires successful
  controller preflight. SSH uses strict checking and only `known_hosts.local`.
- Symlinks/special files, hard-linked managed files and unsafe parent paths are
  rejected. An unmarked existing web root/home/account is not silently adopted.
  Existing markers must be root-owned, mode `0644`, exactly ten bytes and match
  this assignment. Do not create a marker manually to bypass these checks.
- `week10deploy` has a locked password, its own group, no supplementary groups and
  no sudo. Actual UID, groups and sudo denial are checked **before** its key is
  installed. The key is restricted to the agent `/32`, with no forwarding or PTY.
- `/var/www` remains `root:root 0755`; only `/var/www/html` is made writable by the
  deployment account. There is no recursive chown/delete or application upload.
  Review the actual contents before pipeline deployment; installing Ubuntu Nginx
  may add its default page, which is not personalized assignment evidence.
- A **complete, dedicated** Nginx configuration is tested using `nginx -t -c` on
  the candidate before installation/reload; existing unrelated virtual hosts
  are not supported. Static uses real 404s; React routes fall back to `index.html`
  while missing `/static/` assets remain 404s. No application index is generated.
- The marker is written only after service start/reload succeeds. A partial first
  run can therefore leave an account/packages but no marker. Stop and inspect:
  a blind rerun must not adopt that state. Prefer reviewed Terraform cleanup and
  fresh provisioning, or a separately reviewed recovery; never loosen checks.
- After a successful approved run, rerun unchanged inputs and inspect the recap
  for idempotence. Verify service state, account isolation, parent/marker metadata
  and authentic agent-to-target SSH. These runtime checks are **not yet performed**.
  Then run the existing unprivileged pipeline preflight, deploy the actual artifact,
  and verify checksum/HTTP/fallback/external-browser behavior and CI triggers.
- At the approved deadline, use reviewed Terraform cleanup, verify exact resource
  absence, remove/revoke the dedicated SSH service connection/key access as
  appropriate, and retain only sanitized receipts. Do not delete a target still
  required for an explicitly approved grading window without coordinating it.

No target was provisioned, package installed on a target, account/service changed,
application built, pipeline run, screenshot captured or assignment checked off by
these offline tests. All original requirements and evidence slots remain pending.
