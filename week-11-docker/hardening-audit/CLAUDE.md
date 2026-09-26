# Docker evidence audit

Inspect the named EpicBook training container and explain six hardening checks. This workspace is read-only with respect to Docker infrastructure and application source.

Use only `./inspect-container.sh` for the planning step and `./run-audit.sh` for the audit. The latter produces the local report as its documented output. Read that report and recommend a specific Dockerfile edit. Never edit the Dockerfile, Compose file, audit source, or wrappers. Never execute `docker build`, `docker run`, `docker stop`, `docker rm`, `docker rmi`, or any deployment command. Never invoke a general shell, SSH command, or alternate wrapper. An operator performs all remediation outside the Claude session and invokes the audit again. Do not claim the learner personally executed these delegated operations.
