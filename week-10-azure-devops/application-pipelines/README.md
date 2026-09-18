# Week 10 — static and React pipeline preparation

Learner: **Eze Favour**. **Offline source preparation only. Neither assignment is complete.**

These are separately scoped follow-on files; see the [Week 10 status and remaining gates](../README.md) for the combined delivery. No application-repository import, application dependency installation/build/test, SSH service connection, pipeline run, deployment, screenshot or social publication is claimed here. [Source coordinates](sources.json) record public reads, not successful execution.

| Brief | Prepared source | Still required |
| --- | --- | --- |
| [A2 — static site](../assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md) | All-branch CI, runtime-selected Linux pool, variables/checkout/information, payload-only `CopyFilesOverSSH@0`, `SSH@0` verification, guarded Ansible target source | Azure Repos import/personalization, approved AWS Terraform target, actual Ansible execution, restricted SSH connection, successful manual **and automatic** deployments, live grading window, five numbered images and separate LinkedIn image/URL |
| [A3 — React](../assignment-03-automate-react-app-deployment-using-azure-devops-cicd.md) | Main CI, Build → Test → Publish → Deploy, same-run artifact promotion, checksums, SPA/HTTP verification, guarded Ansible target source | Authorized application personalization/test correction, separate approved Terraform target and actual Ansible execution, real four-stage success and automatic trigger, browser verification, six images including LinkedIn |

## Before configuring either pipeline

1. Complete [A1's actual agent gates](../self-hosted-agent/README.md). A pool's existence does not mean an agent is Online. Use only a dedicated, unprivileged agent and reviewed code in the private project. Do not run untrusted fork PRs. `pr: none` is not an Azure Repos branch-policy or Classic-pipeline security control: review those separately. Authorize only each exact pipeline to its pool and SSH connection; never grant all pipelines access.
2. Obtain fresh identity, cloud scope, price/budget, lifetime, cleanup and evidence permissions. A1's temporary Azure-agent allowance does **not** authorize A2's AWS host or A3's host. A2 specifically requires AWS and that its EC2 instance remain running during grading; a grading/retention window has not been agreed. Never use AWS root credentials.
3. Import the correct instructor repository into **Azure Repos** using the approved private project. Review the import and commit/ref before enabling CI. No repository was imported by this preparation. Recheck the [pinned public source facts](sources.json) if upstream changed.
4. Copy the selected `static.azure-pipelines.yml` or `react.azure-pipelines.yml` to the **imported application's** root as `azure-pipelines.yml`. Copy [ci/validate_site.py](ci/validate_site.py) and [ci/verify_remote.sh](ci/verify_remote.sh) unchanged into its `ci/` directory. Do not point these application pipelines at this assessment repository. No instructor JavaScript is vendored, edited or executed here.
5. Replace the SSH service-connection placeholder with the reviewed connection's **name**, not a secret. Select the approved pool at queue time; its default name does not prove readiness. For React, set `deploymentDate` to the actual intended date, `YYYY-MM-DD`, matching the personalized app. Keep `learnerName: Eze Favour` and `targetFolder: /var/www/html`.

## Actual starter constraints — do not conceal them

- A2's source contains `README.md` and `index.html`. The HTML includes an upstream inline script. Add the name in the HTML body without modifying that instructor script. Only the reviewed HTML and generated checksum manifest are staged, never the repository, `.git`, pipeline definitions or credentials. External script/stylesheet dependencies need a separately reviewed payload contract.
- A3 uses React 19 / `react-scripts` 5.0.1. Its documented name/date fields are in **`src/App.js`**. Changing them is outside this preparation's no-JavaScript-edit boundary and remains a separately authorized application-repository task. A terminal caption or an added screenshot label is not application personalization.
- The starter's `npm test` is `react-scripts test tests`: it filters tests to `src/tests/App.test.js`. Another file, `src/App.test.js`, expects “learn react”, which is absent from the reviewed component. This is a **source-review finding**, not a reported test execution. The pipeline deliberately invokes the local test runner without that filter. It is expected to expose the stale assertion; a real run is still required. Review/fix the test to match intended behavior under appropriate authorization. Do not delete tests, hide the failure, use `--passWithNoTests`, or claim all tests passed after selecting only the convenient tests.
- Node **22.23.2** is an actual published version; its official [checksum listing](https://nodejs.org/dist/v22.23.2/SHASUMS256.txt) was read without downloading a package. `NodeTool@0` uses that exact version in both Build and Test. This does not claim independent archive verification by NodeTool. Review the release/support status before live use; do not silently upgrade the application lockfile.

## Target contract — implement through reviewed Terraform and Ansible

The pipeline/helper files do **not** provision or configure a VM. A separate [human-operated Ansible target playbook, input validator and runbook](target/README.md) now implement the configuration source below. They have been tested **offline only**; running the playbook against an approved host would install packages and change its account/Nginx/service configuration. Neither pipeline invokes it. Terraform target/network adaptations and live target validation remain pending.

Use **different A2 and A3 targets**: both serve `/var/www/html`, so using the same host would overwrite A2's grading site.

The [Week 08 AWS reference](../../week-08-terraform/terraform-aws-vm/README.md) is a useful starting point, **not a drop-in A2 target**. It bootstraps Nginx through cloud-init rather than the required Ansible, permits SSH from one controller `/32` rather than also the selected agent's approved egress `/32`, and does not create the dedicated deployment account/marker below. The [Week 08 Azure React reference](../../week-08-terraform/terraform-react-azure/README.md) builds on the VM through cloud-init, whereas A3 must build/test/publish on the pipeline agent and deploy only the artifact. It likewise needs a separately reviewed target/network/account adaptation. Neither older stack nor its state was modified or presumed live. Do not blindly apply either reference, copy its state, or broaden SSH to the Internet.

Required Ansible-managed target state: verify the provisioning configuration and run the narrower runtime preflight before copying. The script checks the account name and nonzero UID, not its full privilege set. Review group memberships, sudoers and SSH authentication separately; passing the script is not proof of those controls.

- Dedicated Ubuntu target with Bash, GNU coreutils/find, curl, systemd and active Nginx. Public HTTP is a temporary non-sensitive lab endpoint, not a production security recommendation.
- SSH key authentication as **`week10deploy`**, a dedicated non-root account with **no sudo/privileged groups**. Do not give a pipeline the VM administrator's key. The service connection's private key/passphrase stays in its approved secret store, never YAML, arguments, environment exports, logs or screenshots.
- `/var/www` is `root:root`, mode `0755`; neither it nor `/var` is a symlink. `/var/www/html` is a real directory, writable by `week10deploy`, readable by Nginx, and contains no other application, symlinks, special files, raw `src/`, or `node_modules/`. Review existing contents before the first run; the preflight is not a comprehensive remote secret scanner.
- `/var/www/.dmi-week10-target` is a **regular, non-symlink file, owner/group `root:root`, mode `0644`**. Its sole line is `week10-a2` for static or `week10-a3` for React. Create it through the reviewed Ansible configuration, not by these pipeline tasks. It reduces accidental cross-target deployment; it is not SSH host authentication.
- Verify the host fingerprint through a trusted cloud/console channel before configuring SSH. Do not use TOFU, `StrictHostKeyChecking=no`, a private-key printout, or a keyscan alone as proof. These templates do not claim the Azure tasks enforce an OpenSSH known-hosts file; review the actual task/service-connection host-authentication behavior before live use. If the required assurance is unavailable, stop rather than describe it as pinned.
- HTTP routes to the exact web root. Static should return genuine 404s for missing content. React must serve the index for application routes but not missing static assets. The relevant Nginx locations for the latter are:

  ```nginx
  location ^~ /static/ {
      try_files $uri =404;
  }
  location / {
      try_files $uri $uri/ /index.html;
  }
  ```

No account creation, sudo change, package installation, Nginx configuration or cloud mutation is performed by the supplied helper or verification script.

## Artifact and deployment behavior

- The Python helper is read-only. It rejects symlinks, special files, unexpected directories/files, source maps and oversized payloads. It checks static body text or React build shape/name/date **presence**, not visual rendering or factual date correctness. Human review and a real browser check remain necessary.
- Build emits a deterministic SHA-256 manifest via stdout, which the pipeline writes outside the payload before moving it into place. Each later artifact boundary rechecks it. Unknown assets require a reviewed allowlist change, not disabling validation.
- React Build publishes **`candidate-site`**. Test independently checks out the same run's commit and installs its lockfile; it does not assume the same agent/workspace survives between stages. Publish downloads that candidate from the **current run**, verifies it after Test succeeds, and promotes **`site-build`**. Deploy downloads only that artifact, verifies it again and requires `refs/heads/main`. No raw React source, dependencies or source maps are uploaded.
- `npm ci --ignore-scripts` avoids dependency lifecycle hooks; the intended build/test runners are invoked explicitly. App/npm commands are prospective pipeline behavior only: none ran on this workstation during preparation. Dependencies still require review; these flags are not a sandbox.
- Copy uses the exact artifact root, fails on empty input and does **not** recursively clean the target. Old content-hashed assets can remain. Deployment is **not atomic** and automatic rollback is not implemented; use a controlled lab window and review retention/cleanup through Ansible. Do not share the target with another application.
- Remote verification is unprivileged: checksum validation, active Nginx, byte-for-byte local HTTP index comparison, React fallback and genuine static 404 checks, and a top-level web-root listing. It does not prove external firewall reachability or client-side rendering. `enableRemoteVsoCommands: false` prevents remote output from issuing Azure logging commands on the documented current SSH task.
- None of these scripts invokes Terraform, cloud APIs, agent registration, PAT handling or service mutation. A failed check stops the job/stage; there is no success-on-error shortcut.

## Offline checks

From this assessment repository's root, using the existing system Python, Bash and Ruby/Psych:

```sh
env -i PATH=/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
  /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network*) (deny file-write*)' \
  /usr/bin/python3 -I -B -m unittest discover \
  -s week-10-azure-devops/application-pipelines/tests -v
```

The suite parses both YAML files with real Psych, checks pipeline dependencies/permissions/artifact wiring, validates Bash syntax, tests payload/manifest rejection paths and runs the remote verifier **only with in-process shell stubs**. Fixtures are in-memory and explicitly synthetic; they are not React builds, deployments, pipeline logs or evidence. No test creates a file/account/service, contacts a host, installs a package, or executes instructor JavaScript. Azure's service-side schema validation, real npm tests, task execution and all live proof remain pending.

## Remaining Week 10 gates

A1's [historical manual run 1 and cleanup](../self-hosted-agent/runtime-2026-09-18.json) were verified on 18 September 2026; that temporary agent/VM were removed. A fresh approved Online agent is needed for subsequent runs, and A1's screenshots, checklist and notes remain pending. A2/A3 need the Terraform adaptations, actual Ansible target execution and all live and human requirements above. A4 additionally requires its actual application/configuration review, two repositories, a separately approved two-VM/private-MySQL Azure design, protected remote state/connections, approved infrastructure pipeline and manual output handoff. A5 requires healthy A4 pipelines and the **actual supplied kit**; the previously inspected nontruncated instructor main tree contained no supplied `CLAUDE.md`, `pipeline-triage.sh` or `.claude/skills/pipeline-triage/SKILL.md`. Do not manufacture the kit, incidents, reports, learner explanations, screenshots or LinkedIn posts. Original briefs and their unchecked completion lists are unchanged.
