# Optional CI/CD choice

The capstone marks CI/CD optional. This delivery uses a reviewed operator workflow: lock source and dependencies, build images, run the local/remote checks, review Terraform plans, deploy through Compose, then verify the browser, HTTP API and independent database results. GitHub holds the reviewed source and evidence. Docker Hub hosts the React release by immutable digest.

No unattended deployment pipeline or additional cloud credentials were created for this optional task. Adding a pipeline should use scoped short-lived credentials, a protected deployment environment, immutable image promotion and an explicit rollback. It should run the meaningful HTTP/security tests before updating a retained demo. This document records the choice honestly; it is not evidence of a completed CI/CD run.
