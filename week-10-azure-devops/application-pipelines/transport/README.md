# Host-pinned transport for A2/A3 native SSH tasks

**Offline-tested source, not an installed or live-verified transport.** No new
agent, target, service connection or pipeline was created by this increment.
The [native-task source finding](../README.md#ssh-transport-review--18-september-2026)
still applies: those Node clients do not consume OpenSSH `known_hosts`.
This design retains `SSH@0` and `CopyFilesOverSSH@0` without adding unsupported inputs.

## Trust boundary and two separate identities

On the dedicated agent, OpenSSH authenticates the target's independently verified
Ed25519 host key and opens one loopback listener. Native tasks use that listener:

```text
Azure task -> agent 127.0.0.1:22222 (A2) or :22223 (A3)
           -> host-pinned OpenSSH transport as week10tunnel
           -> target 127.0.0.1:22 -> inner SSH as week10deploy
```

- The outer key is generated on the agent. Its private half never leaves that
  host. The target accepts its public half only from the actual approved agent
  egress `/32`, with local TCP forwarding only to `127.0.0.1:22`. No remote/Unix
  forwarding, shell, SFTP, agent forwarding, PTY or sudo is allowed for this role.
- A **different** deployment key belongs to the approved SSH service connection.
  Its target authorized-key entry accepts only `127.0.0.1/32`, with forwarding and
  PTY disabled. The deployment account can update the dedicated site, not sudo.
- `/etc/dmi-week10/tunnels/<assignment>/profile.json` and `known_hosts` are root-owned
  `0644` under real root-owned `0755` directories. The agent's forwarding private
  key is `0400`, owned by `azdoagent`. The helper checks its metadata, never reads
  its contents; OpenSSH reads it internally. Public inputs reject comments,
  options, duplicate/extra fields, private addresses and private-key text.
- The root profile binds the exact **service-connection UUID** used by the YAML,
  target IP, host key and fixed UTC window. It cannot attest that Azure still has
  the correct endpoint settings. Independently verify its saved type `ssh`, host
  `127.0.0.1`, assignment port and user `week10deploy` before use. Never dump the
  endpoint's authorization parameters. Recheck after any endpoint change.
- This trusts the agent's root account, `azdoagent`, the reviewed pipeline and
  service-connection administrators. It does **not** isolate hostile local users
  or malicious jobs. Use one dedicated, single-job agent with no untrusted jobs,
  no containerized deployment job and exact pipeline/pool/connection permissions.
  Do not place the controller management PAT or VM administrator key on it.

## Ordered, human-authorized preparation

These steps are prospective. A timestamp or successful input check is not consent.
The old lab window and A1 resources/keys/state are retired.

1. Use fresh scoped lifetime/budget authorization. The [current A2 approval](../../README.md#current-resource-window-decision)
   already permits 24 hours from first provisioning within the unchanged US$10
   combined planning allowance; it has not started. Obtain verified non-root AWS
   apply/**cleanup** access and a working independent cloud cleanup safeguard.
   Review the exact Terraform plans, identities, images, prices and controller/
   agent egress IPs. Prepare a fresh A1 agent and distinct A2/A3 targets through
   reviewed Terraform; never edit cloud resources manually. A2 grading retention
   needs its own agreement. All live operations below also require this scope.
2. Verify agent and target host keys through trusted console/cloud channels.
   `ssh-keyscan` alone, TOFU, or accepting a changed key is insufficient. Review
   Ubuntu 22.04 agent/OpenSSH/systemd compatibility; these tests do not prove it.
3. Create the separate deployment key through an approved private workflow and
   a pipeline-restricted SSH connection using the loopback host/assignment port
   above. Keep private key/passphrase in its approved secret store, not command
   arguments, environment exports, chat, logs or screenshots. Record its UUID and
   independently verify saved endpoint metadata. Do not grant all-pipeline access.
4. In this directory, prepare protected ignored `inputs.local.json` and
   `inventory.local.json` from their examples. Supply exactly one `week10_agent`,
   its public IP, separate non-root administrator and a path to that administrator's
   protected key. Supply the six public profile fields, using canonical UTC
   `YYYY-MM-DDTHH:MM:SSZ`, the approved window (maximum 24 hours), authentic host
   public key without a comment and exact connection UUID. Null examples fail.
   Put the authentic **agent IP/key** in `known_hosts.local`. Do not use arbitrary
   extra variables, plugins, tags, `--limit` or `--start-at-task` to bypass preflight.
5. Validate raw JSON locally, before Ansible parses it:

   ```sh
   python3 -I -B ../ci/ssh_tunnel.py validate-agent-inputs < inputs.local.json
   ```

   This is read-only and never connects. It requires at least 21 minutes remaining.
   A credential-free `ansible-playbook --syntax-check -i inventory.example.json
   configure-agent.yml` checks syntax only. Do not mistake `--check` for offline:
   Ansible check mode can still contact a host.
6. Only with fresh live approval, review then run from this directory:

   ```sh
   ANSIBLE_CONFIG="$PWD/ansible.cfg" ansible-playbook \
     -i inventory.local.json -e @inputs.local.json configure-agent.yml --ask-become-pass
   ```

   Omit the interactive prompt only for a separately approved administrator with
   existing noninteractive sudo. Never grant `azdoagent` sudo. This playbook does
   change the approved agent: `dbus-user-session`, fresh key/profile, linger and
   its user manager. It verifies the existing locked, non-sudo account first. It
   does **not** create/register an agent or start a tunnel. It refuses any existing
   profile directory, including a partial installation; do not overwrite it to
   renew authorization. Inspect partial state and arrange separately reviewed
   recovery or fresh Terraform provisioning. The profile is written last.
7. Transfer only the displayed **public** forwarding key into `tunnel_public_key`
   in the [target inputs](../target/README.md), alongside the different deployment
   public key. Run that reviewed target playbook under the same approved scope.
   It validates the complete SSH config before reload, checks effective forwarding
   restrictions and applies them before authorizing the forwarding key. Its Match
   block is at EOF, not in a top-included drop-in that can change later parsing.
8. Copy the reviewed YAML and all three runtime helpers (`validate_site.py`,
   `verify_remote.sh`, `ssh_tunnel.py`) into the correct imported application's
   repository. Set its exact connection UUID. Authorize only the intended pipeline.
   Do not enable CI or queue a run until the live acceptance checks below pass.

## Job lifecycle and cleanup

`start <assignment> <System.JobId> <connection-UUID>` refuses another job service,
checks root-controlled public inputs and starts a uniquely named **user** systemd
unit. Its foreground OpenSSH master uses strict Ed25519 pinning, a private control
socket, one loopback forward, no shell and no authentication prompts. Both the
controller subprocess and unit child environments are cleared; no inherited
manager credentials are passed to OpenSSH.

`check` verifies the active transient unit, profile digest and matching systemd/
OpenSSH master PID. Its control-only check cannot fall back to a network connection.
This is transport readiness, **not successful target authentication by a native
task or deployment evidence**. The pipeline checks before copy and verification.

The deployment job has a 15-minute timeout, two-minute cancellation grace and a
final `condition: always()` stop. `stop <assignment> <System.JobId>` addresses only
that exact unit and still works after profile expiry/removal or an endpoint-input
error. Start failures attempt the same bounded cleanup; failures are not hidden.
A successful stop requires an absent unit or inactive/failed unit with no main PID.

The unit independently has `RuntimeMaxSec=1200`, ten-second stop grace, no restart
and control-group termination. Start requires **21 minutes remaining**, checked
again after connection, reserving headroom around the 20-minute lifetime. These
limits depend on a functioning host clock/systemd; they are not an infallible
absolute-time guarantee under suspension, clock changes or host failure. They do
not destroy a cloud VM, revoke keys or enforce billing. Keep the independent
Terraform/cloud cleanup safeguard and verify resource absence at the agreed
boundary. Review/remove linger, profiles and connection permissions if an approved
host is retained; do not remove other users' state or reuse a retired key/window.

## Required live acceptance — all pending

- Correct host pin succeeds; a deliberately wrong public pin on an approved
  disposable test profile fails before any native task. Never disable verification.
- A busy local port or stale job unit is refused, not adopted. Private key bytes
  never appear in output. Confirm effective target restrictions and actual source
  IP; shell/SFTP/remote/unapproved forwarding for `week10tunnel` must fail.
- The exact saved service connection is loopback/expected port/user and bound to
  this profile/pipeline. Confirm native-task sessions reach the intended target.
- Verify failed-start cleanup, cancellation and independent runtime expiry on the
  real supported image. Confirm no listener/master remains after stop.
- Target Ansible idempotence, manual **and automatic** deployments, real artifacts,
  external HTTP/browser behavior, grading retention and genuine evidence still
  need execution/approval. Local mocks and source contracts prove none of these.

Both updated playbooks passed native Ansible 2.21.4 syntax checks. Six synthetic,
controller-only rejection cases passed with zero changes; IP networking and
SSH/sudo execution were denied, a localhost-only limit excluded remote plays, and
all temporary writes were confined to cleaned invocation scratch. Initial tool-path
and inventory-harness launch failures are not counted as passed checks.

Run the [credential-free tests](../README.md#offline-checks) with network and writes
denied. They mock all transport/process/filesystem interactions; only JSON/YAML
parsing, Python fixture logic and existing shell syntax checks execute locally.
