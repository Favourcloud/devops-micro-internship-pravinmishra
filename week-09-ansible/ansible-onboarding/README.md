# Week 09 — Ansible workstation onboarding

**Learner:** Eze Favour

**Scope:** Local workstation setup for [Assignment 1](../assignment-01-set-up-a-team-ready-ansible-development-workstation.md). No cloud infrastructure, remote SSH, service installation or system configuration is managed by this project.

**Current brief:** aligned on 15 September 2026 with the official assignment's eight tasks, twelve screenshots and four written questions. `inventories/` and `roles/` are prepared as empty tracked directories for future labs; the smoke test still uses the existing root `inventory.ini`. Submission source remains in the shared feature-branch worktree. On 16 September 2026, a persistent sparse controller clone was created inside the ignored Week 09 working directory. It has its own `.git` directory and actual `main` branch, so its workstation hooks and identity can be configured without changing the shared worktree. The controller is for continued local use, not a disposable validation fixture. Its local `main` is not the published grading branch; submission and any reviewed merge are separate steps.

## Machine and evidence

Prepared on **macOS (Darwin), x86_64, Python 3.13.3**. The isolated `.venv` is under this directory; system Python and other assignments' environments are unchanged. [`requirements.txt`](requirements.txt) pins the resolved dependencies; [`requirements.in`](requirements.in) lists the four requested tools for deliberate future upgrades.

The [15 September validation record](evidence/local-validation.json) is preserved as historical evidence for its recorded source hashes. It contains actual sanitized local command results, the localhost smoke result and an isolated Git-hook installation test. It is **not a screenshot**, remote connectivity test or proof that editor extensions, signing or SSH keys are configured. Assignment-required screenshots and human access steps remain open until genuinely verified.

## New Machine? Do This

- [ ] Clone the repository and use your own worktree. Confirm macOS/Linux and Python **3.13** with `python3.13 --version`; record differences instead of claiming this environment was tested everywhere.
- [ ] Enter `week-09-ansible/ansible-onboarding`, confirm the `inventories/` and `roles/` directories are present, and create `.venv` with `python3.13 -m venv .venv`.
- [ ] Activate it with `source .venv/bin/activate`; install the lock using `python -m pip install -r requirements.txt`, then run `python -m pip check`. Never use `sudo pip` or disable TLS certificate verification.
- [ ] Confirm `ansible --version`, `ansible-lint --version`, `yamllint --version` and `pre-commit --version`; capture genuine terminal screenshots with your learner name visible and private paths/identifiers redacted.
- [ ] Open **this folder**, not the repository root, in genuine Visual Studio Code. On this Mac use `/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code`; the generic `code` command may open Cursor. Install/enable the recommended `redhat.ansible`, `redhat.vscode-yaml` and `ms-python.python` extensions; confirm the `.venv` interpreter and capture the Extensions panel. Recommendations alone do not install extensions.
- [ ] Read `.vscode/settings.json`, `.editorconfig`, `ansible.cfg` and `inventory.ini`. Run `ansible-config dump --only-changed` and verify this project's configuration, localhost-only inventory, host-key checking, no default escalation and no agent forwarding.
- [ ] Review an existing Ed25519 SSH identity before generating a new one. If one is needed, create a **passphrase-protected** key interactively outside the repository; add it to your existing agent and check `ssh-add -l`. Never overwrite a key or publish its contents. On this workstation, the learner created and loaded the separately named Week 09 key privately. The [sanitized SSH check](evidence/ssh-readiness-20260916.json) passed in that same Terminal. Another Terminal may see a different agent.
- [ ] Review the optional [SSH readiness alias](ssh_config.example). It targets public `github.com`, uses only the Week 09 identity, and preserves strict host checking. `python scripts/verify_ssh.py` checks your real config and current agent without contacting the host. For future remote labs, review each real host and fingerprint before connecting. Keep `StrictHostKeyChecking yes`, `ForwardAgent no` and `IdentitiesOnly yes`; do not use `Host *` exceptions or invent a reachable host for this local task.
- [ ] Verify your Git identity privately using `git var GIT_AUTHOR_IDENT`. Configure missing identity, `init.defaultBranch main` and signing only with the intended personal/team policy; do not replace shared/global settings automatically. The isolated controller uses Eze Favour and the verified GitHub noreply address, with repository-local `init.defaultBranch=main`. No global signing policy is changed.
- [ ] Run both lint checks and the smoke playbook below. Inspect the target list first. The smoke test must report `changed=0`, `unreachable=0` and `failed=0`; it tests local Python execution, not remote SSH readiness.
- [ ] From the **repository root**, run the explicit pre-commit command below. On your own clone, review existing hooks and `core.hooksPath` before installing this config. In a shared worktree, do not overwrite common hooks; the validation uses a disposable nested Git fixture instead.
- [ ] Capture the required file-tree/config/README/terminal screenshots, finish the SSH/editor checks and update the parent checklist truthfully. Keep `.venv`, keys, local inventory, caches and sensitive evidence out of Git; review the staged diff before committing.

## Local validation

Run the complete check suite from this directory with `.venv` activated:

```bash
python scripts/verify.py
```

This also tests both passing hooks and deliberately invalid YAML/module names in a disposable Git fixture, removes the fixture, and refreshes the sanitized evidence JSON. It does not install hooks in this shared repository. For individual checks:

```bash
bash scripts/lint.sh yamllint
bash scripts/lint.sh ansible-lint
ansible-playbook playbooks/smoke.yml --syntax-check
ansible-playbook playbooks/smoke.yml --list-hosts
ansible-playbook playbooks/smoke.yml --check
ansible-playbook playbooks/smoke.yml
```

The playbook uses the virtual environment's Python, targets only `localhost`, disables fact gathering and privilege escalation, and runs assertions plus `ansible.builtin.ping`. Ansible creates temporary files only under this project’s ignored `.ansible/` directory. The localhost playbook pins `ansible_remote_tmp` there as well: a local connection otherwise inherits Ansible’s home-directory target-temp default. Lint/verification wrappers also set project-local Ansible and pip caches, so restricted execution does not require writes to home-directory caches. No package/service/cloud mutation is part of the playbook. Check mode and normal mode should both be clean. A production lint profile is a coding standard, not a claim that this workstation or an undeployed service is production-ready.

From the **repository root**, after files are tracked:

```bash
week-09-ansible/ansible-onboarding/.venv/bin/pre-commit run \
  --config week-09-ansible/ansible-onboarding/.pre-commit-config.yaml --all-files
```

Hooks are monorepo-aware and limited to this onboarding project. They run the exact tools in `.venv` through `scripts/lint.sh`; no hidden hook-time package installation occurs. On a private clone where hook installation is appropriate, use the same config path with `pre-commit install`. Do not run that installation blindly in this shared worktree: Git hooks can live in its common repository directory.

## Files and safe defaults

```text
ansible-onboarding/
├── .ansible-lint
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── .vscode/{extensions,settings}.json
├── .yamllint.yaml
├── ansible.cfg
├── inventory.ini
├── inventories/.gitkeep
├── roles/.gitkeep
├── playbooks/smoke.yml
├── requirements.in
├── requirements.txt
├── ssh_config.example
├── scripts/{lint.sh,verify.py,verify_ssh.py}
├── evidence/local-validation.json
└── README.md
```

- **Team-friendly choice:** a pinned, project-local toolchain plus matching editor/lint/hook settings lets another learner reproduce the same checks without changing global Python packages.
- **Pitfall avoided:** installing pre-commit into a shared worktree can overwrite another project's common Git hook. The test suite still uses an isolated fixture for negative checks. Actual workstation hooks are installed only in the persistent controller clone, which owns its Git metadata.
- **SSH safety:** host-key checking remains enabled. No private key, agent fingerprint, real host inventory or machine-wide SSH configuration is committed. Remote access is not claimed by the local `pong` result.
- **Proxy/CA:** no custom corporate proxy/CA configuration was added. On managed networks, obtain the approved CA/proxy configuration from the administrator; do not use `--trusted-host`, `curl -k`, or disable certificate verification as a workaround.
- **Upgrade policy:** change `requirements.in` deliberately, resolve into a clean Python 3.13 environment, regenerate `requirements.txt` using `pip freeze`, then rerun validation before committing. A version lock does not guarantee package safety or indefinite support.

To discard this local environment, deactivate it and remove only this project's `.venv`/`.ansible` caches after checking the paths. No cloud teardown is needed.

## Intel macOS dependency note

The 16 September controller installation retains all 38 pinned versions. PyPI does not provide an Intel macOS wheel for `cryptography==50.0.1`. The first clean install attempted a Rust build and failed; it was not counted as successful. A cached local wheel was then checked against its official PyPI source archive hash and against the native binary in the previously validated environment. The retry uses that wheel and official binary packages. On another Intel Mac, prepare a supported Rust/OpenSSL build toolchain or deliberately review a new lock; do not assume a binary-only install will work everywhere.

## SSH evidence boundaries

`verify_ssh.py` reads only the public key, private-file metadata, effective client settings and agent listings. Agent fingerprints and comments are removed before display. It does not read private-key contents, change a passphrase, connect to GitHub, validate a remote fingerprint or prove GitHub account authorization. The existing `known_hosts` file is checked only for existence. The optional alias does not add a key to GitHub.
