# Week 09 Assignment 3 — Multi-play static website

**Learner:** Eze Favour. **Platform:** Azure, targeting Assignment 2's same `web1` and `web2` Ubuntu 22.04 hosts. **Status:** code preparation with genuine local captures for slots **1/2/4/5**; **no A3 deployment, HTTP result, remote idempotency, browser evidence or published post**. A2 was genuinely provisioned, trusted, inventoried and SSH-checked, then stopped after a controller callback error before Ansible managed tasks. All infrastructure was deleted and cleanup verified at **2026-09-16 21:53:43 UTC**. Former IPs are historical, not live website URLs; do not contact them.

Copilot assisted the code, source download, technical explanations and local checks. These notes are not a record of learner-operated cloud work. The learner must review them and supply firsthand reflection after genuine execution.

## Files and website source

```text
static-web/
├── .gitignore, .ansible-lint, ansible.cfg
├── inventory.ini                 # safe UNCONFIGURED template
├── site.yml                      # exactly three plays
├── README.md, SOURCE.md
├── files/{index.html,contact.html,style.css}
└── tests/test_site.py
```

The existing course `CodeTrack` website was genuinely downloaded from the learner's GitHub repository at a pinned commit. [SOURCE.md](SOURCE.md) records the exact immutable URLs, original SHA-256 values, verification and reproduction command. `index.html` and the linked contact page use `Eze Favour` and add `Deployed by Eze Favour — Week 09 multi-host lab` to the preserved DMI footer. The stylesheet is unchanged and bundled. No JavaScript, build step or external asset dependency is introduced. The footer is desired artifact content, not a claim of deployment.

## Prerequisites and approval

Use the existing Assignment 1 Ansible controller (validated with Python 3.13.3, Ansible 14.4.0/core 2.21.4 and ansible-lint 26.8.0). Do not recreate its environment, keys or agent. Reuse the four-host [A2 Terraform lab](../ansible-adhoc-lab/README.md); A3 creates **no extra infrastructure**. Standard Ubuntu Nginx's default site serves `/var/www/html`. This playbook is for the dedicated fresh lab, not arbitrary production servers with custom Nginx configuration.

The completed temporary run had a coordinator-approved A2+A3 allocation of at most US$2 and two hours after apply. Azure replaced the initial AWS choice because the non-root AWS identity lacked EC2 permissions. The historical B1s plans were never applied; the later D2lds_v6 plan was separately identity-sealed, reviewed and applied after A5's pilot. Cleanup finished before the original deadline; this is not a claim of zero charges or a finalized invoice. All old approvals are retired. A future attempt requires new identity, budget, plan, capacity and runtime review; **do not reuse historical IPs, state inputs or approval files**. Expired AWS enrollment is not reused. No provisioning, SSH, package/service tasks or managed HTTP requests are currently authorized. Verify both hosts' fingerprints against authenticated Azure boot diagnostics and store matching keys only in A2's `.local/known_hosts`; the configuration preserves strict checking with no global known-hosts fallback. Current `.invalid` inventory names are intentionally not real endpoints.

A2's renderer creates ignored, mode-0600 `inventory.local.ini` explicitly from real Terraform output after approval. Its `--web-only` option selects the same `web1` and `web2`; never invent IPs or replace tracked `inventory.ini`. No private-key path or credentials are committed. The existing SSH key/agent must already be selected. Approval assertions run before remote modules because fact gathering is off. Each play defaults `live_execution_approved` to false; only an authorized operator may explicitly override it. These are workflow safeguards, not a substitute for authorization.

## The three plays

1. **Install:** target `web`, require approval/configured inventory, install Nginx with `apt state=present` and a 3600-second cache validity, then start and enable the service with privilege escalation.
2. **Deploy:** target only `web`, recheck approval and copy the three static files to `/var/www/html` with root ownership and mode `0644`. A change notifies `Reload Nginx`, which runs once per host at the end of that play. Copying unchanged content does not notify it. Reload is included as the assignment's handler example; changing static content normally does not itself require an Nginx reload.
3. **Verify:** run on `localhost` without escalation using the controller Python. For each web host, `uri` requests its HTTP root directly (no proxy/redirect), requires HTTP 200 and returns content. Assertions require both `Eze Favour` and the unique lab marker, so Nginx's default welcome page cannot pass. Retry handles a short startup delay, not a replacement for troubleshooting. Check mode deliberately skips HTTP validation and is not deployment evidence.

Splitting these concerns makes a failure easier to locate. `copy` stages the reviewed, personalized controller artifact without requiring Git or outbound repository access on managed hosts. Terraform is responsible for infrastructure; Ansible handles packages/content/service state.

## Safe local validation

From `static-web/`, with the existing controller environment on `PATH`:

```bash
export PYTHONDONTWRITEBYTECODE=1
export ANSIBLE_HOME="$PWD/.ansible" ANSIBLE_LOCAL_TEMP="$PWD/.ansible/tmp"
export XDG_CACHE_HOME="$PWD/.cache"
ansible-inventory -i inventory.ini --graph
ansible-playbook -i inventory.ini site.yml --list-hosts
ansible-playbook -i inventory.ini site.yml --syntax-check
ansible-lint --offline --nocolor site.yml
python -m unittest discover -s tests -v
```

SSH multiplexing is disabled with `ControlMaster=no` and `ControlPath=none`, avoiding Unix control-socket path limits in deep worktrees while retaining strict task-local host-key verification. A2's `tests/test_ssh_configuration.py` covers both configurations with real, no-network OpenSSH configuration/socket checks.

The graph shows two unconfigured names; syntax/lint do not SSH. The tests verify source hashes and all relative links, module/handler structure and approval refusal before an SSH sentinel could run. A positive preflight test confirms that an approved, configured SSH inventory reaches a deliberately failing SSH stub, while a local-connection inventory is refused before package tasks; the stub never contacts a host. They execute **only a temporary copy of Play 3** against a loopback HTTP fixture, checking success plus wrong content, missing marker, HTTP 503 and redirect rejection. Temporary inventory values and reduced retry delays are test-only. This proves controller-side logic, **not** reachability or deployment of two cloud servers. No install/deploy module is executed by these tests. Keep the pinned source Git commit available (a shallow clone may need that commit fetched explicitly).

## Future authorized live execution — not a transcript

A future run requires a new approved A2 Terraform apply, fingerprint review, SSH checks and explicit rendering of `static-web/inventory.local.ini`; never reuse the retired historical inventory. Keep A2's full local role/IP mapping in `ansible-adhoc-lab/.local/public-ips.json`. From `static-web/`:

```bash
# LIVE WORK ONLY AFTER the coordinator's access/plan/time-window approval.
ansible-inventory -i inventory.local.ini --graph
ansible web -i inventory.local.ini -m ansible.builtin.ping
ansible-playbook -i inventory.local.ini site.yml --syntax-check
mkdir -p .local
set -o pipefail
ansible-playbook -i inventory.local.ini site.yml \
  -e '{"live_execution_approved": true}' | tee .local/first-run.log
# Inspect real Play 3 results and recap before continuing.
ansible-playbook -i inventory.local.ini site.yml \
  -e '{"live_execution_approved": true}' | tee .local/second-run.log
```

Run the second pass immediately with no edits and within the apt cache window. Expected first recap: `unreachable=0` and `failed=0` for web1, web2 and localhost; both controller HTTP/content assertions pass. Expected second recap: also `changed=0` for both web hosts, with no handler executed. These are **expected acceptance criteria**, not recorded outputs. Later package-index refreshes or deliberate content edits may legitimately change state. A2 may already have installed Nginx, so A3's first installation play can legitimately report no changes. Do not edit output to manufacture idempotency.

After the playbook succeeds, validate manually from the approved controller:

```bash
# Read the actual URLs from A2's private local outputs; do not paste them into Git.
python -c 'import json; d=json.load(open("../ansible-adhoc-lab/.local/public-ips.json")); print("Server 1: http://"+d["web1"]); print("Server 2: http://"+d["web2"])'
# Set these shell variables to the real reviewed output values, not placeholders.
# WEB1_IP and WEB2_IP must already be set in this authorized shell.
curl --fail --silent --show-error --noproxy '*' --head "http://${WEB1_IP:?set actual web1 IP}/"
curl --fail --silent --show-error --noproxy '*' --head "http://${WEB2_IP:?set actual web2 IP}/"
```

Open each actual URL in the controller's browser; verify the footer, CSS and contact/back links. HTTP access is restricted to the controller /32, so another viewer will not reach the site. Capture the public IP/full name in genuine browser windows only after privacy review. Do not broaden the Terraform-managed NSGs for a screenshot. If the controller IP changes, update it through Terraform after a fresh authorized plan.

The [A3 manifest](../screenshots/assignment-03-manifest.json) preserves all 11 numbered slots plus LinkedIn. Approved genuine native captures cover **1** (tracked filenames), **2** (post-cleanup local retained-inventory graph), **4** (personalized source) and **5** (local syntax). Slot 2 was genuinely executed once locally after cleanup, with SSH/SFTP/SCP disabled, and visibly shows `web1` and `web2`; it is **not connectivity evidence**. An earlier incomplete graph frame was not accepted. Original PNG and source/run hashes are recorded. Slots **3, 6–11** and LinkedIn remain pending. Neither template checks, the retained graph nor localhost tests fulfill ping/deployment evidence. Website URLs and published-post links remain pending. Never publish account IDs, credentials, keys, state or private paths; no LinkedIn publication is authorized.

## Troubleshooting, learning and cleanup

A2's actual SSH hostname and cloud-init checks succeeded, but the private runtime environment set `ANSIBLE_CALLBACKS_ENABLED=''`. Ansible core 2.21.4 parsed that as `['']` and raised `ValueError: A non-empty plugin name is required` before its ping tasks (exit 250). The coordinator stopped execution; A3 deployment was never attempted. After verified cleanup, a new private copy omitted that variable, without changing frozen execution history or copying approvals. Five local regressions passed, including reproducing the original callback failure and a genuine **localhost-only** pong. This is not a successful managed-host retry. [The sanitized runtime receipt](../ansible-adhoc-lab/runtime-validation.json) records hashes and limits. During preparation, tests intentionally confirmed that a default Nginx page with HTTP 200 is insufficient: the personalized content assertion rejects it. A shared-disk shortage was resolved by removing only this task's redundant tool/provider copies and reusing verified existing executables; no learner action is invented. These are local engineering notes, not firsthand deployment reflections.

For future authorized runs: SSH denial means review the existing identity, verified fingerprint, controller /32 and instance readiness; do not disable verification. Apt locks can mean Ubuntu initialization is unfinished; wait rather than killing package managers. HTTP failure requires inspecting the Nginx service/default-site configuration, copied files and Terraform-managed web-only rule. If a second run changes files, compare source bytes and destination ownership/mode before claiming idempotency.

Cleanup takes priority over completing screenshots. For the historical run, the coordinator stopped both runtimes and disabled approvals, separately reviewed/applied the exact **23-delete** teardown, and passed **16 absence/empty-state checks** at **21:53:43 UTC**, before the original **22:22:02 UTC** deadline. Persistent empty state advanced to serial **48** with the same lineage. A3 had no separate infrastructure. All historical plans, state backups and inventories remain private evidence, not runnable inputs. No zero-charge claim or cloud retry is authorized. For any future approved run, follow A2's exact-state reviewed cleanup workflow even when evidence is incomplete.
