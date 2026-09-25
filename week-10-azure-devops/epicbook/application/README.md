# EpicBook application pipeline

The Azure Repos `theepicbook` repository contains the pinned instructor application, disclosed checkout patch and the application pipeline. Build verifies the complete source lock and creates an immutable release artifact. Deploy runs only for `refs/heads/main`, downloads the dedicated SSH Secure File, validates the four-value handoff and pinned host keys, configures frontend/backend with Ansible, verifies the application and demands changed=0 on a second unchanged run.

The infrastructure pipeline uses the separate `infra-epicbook` repository and a reviewed saved plan. The operator transfers only `app_public_ip`, `backend_ansible_host`, `backend_private_ip` and `mysql_fqdn` into `handoff.json`. Database secrets and the signed-cart secret are pipeline secret variables; never place them in this file, source, screenshots or artifacts. Azure service connection/secure-file access is individually scoped to the pipeline.

Application run14 passed both hosts and the public workflow. The temporary triage branch runs18/19 intentionally skipped Deploy. See [verified evidence](../../evidence/2026-09-25/README.md) and [triage report](../../pipeline-triage/change-summary.md).
