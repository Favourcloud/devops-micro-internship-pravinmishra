# Operating the 25 September 2026 A5 release

This is the deployed AWS release, operated by Codex under Eze Favour's authorization. The original preparation source and evidence remain preserved separately. The deployment report records actual API, browser, database and recovery results; local tests alone are not runtime proof.

## Runtime contract

Use the verified Ubuntu 24.04 amd64 image and origin-bound Linux artifact. The build uses Node 22.23.3, npm 10.9.9, Nginx 1.24.0, MySQL Router 8.4.10, AWS CLI 2.37.2, Python 3.12.3 and PyMySQL 1.1.1. Four selected package/lock files are updated through `deployment-lock.json`; the other 31 selected upstream files are unchanged. `source-lock.json` retains the original upstream identity. The artifact manifest binds source hashes, member hashes, release identity, origin, platform and runtime versions. Bootstrap verifies the downloaded artifact before installing it.

Instances use encrypted 30 GiB roots and t3.large memory capacity. Bootstrap requires at least 2.5 GiB free disk; archive limits are 512 MiB compressed and 1.5 GiB expanded. It does not install dependencies or build application code. Existing application directories cause a fail-closed error: use reviewed launch-template updates and rolling ASG replacement rather than rerunning installation over an existing node.

## Request path and isolation

The browser reaches an AWS HTTP API over certificate-validated HTTPS. A private VPC link reaches an internal Network Load Balancer, whose ALB target is the assignment's internet-facing Application Load Balancer. That ALB accepts TCP 80 only from the entry NLB security group. No Internet CIDR ingress was added. The internal NLB was required after direct VPC-link/ALB integration returned `INTEGRATION_NETWORK_FAILURE`.

The public ALB forwards to Nginx on the two Web nodes. Nginx forwards application requests through the internal ALB to port 3001 on the two private App nodes. Next listens only on loopback port 3000. The inspected upstream server actions are not used; Nginx blocks non-API writes and returns 404 for the unused Next image-optimization route. The App and database subnets have no public instance addresses; database routes have no Internet default route. Each App AZ has its own NAT gateway for approved outbound access.

API Gateway overwrites viewer identity headers; Nginx verifies the expected public host and HTTPS marker. These headers supplement the security-group boundaries. API-mode public ALB uses AWS's `defensive` desync handling because API Gateway emits `Content-Length: 0` on GET. The internal ALB and direct ACM mode retain `strictest`. Nginx strips request bodies and Content-Length on permitted read-only book/review routes before forwarding. Unknown API routes and book writes return 405/404; only review POST forwards Authorization. Cookies and unrelated authorization headers are stripped. API stage limits are 50 requests/second with burst 100.

HTTP between gateway and application tiers is confined to the VPC; this is not TLS on every internal HTTP hop. The database path has verified TLS. The original upstream frontend has poor dark-mode card contrast; recorded light-mode screenshots use temporary browser emulation, with no pixel or application-source edits.

## Database and service startup

The primary is private, encrypted Multi-AZ RDS MySQL 8.4.11. Its managed standby differs from the separate asynchronous read replica. The unchanged application uses the primary only. `report_replica.py` is an explicit read-only reporting check, not application read splitting.

Node's unchanged database TLS behavior is confined to loopback Router port 6446. Router verifies the RDS CA and hostname; direct Python connections do likewise with the pinned PyMySQL adapter. Before authentication, that adapter rejects a non-TLS server greeting. Runtime verification includes successful TLS 1.3 connections and rejection of an untrusted CA and incorrect hostname. The Router AppArmor profile stays enforced, with narrowly scoped access to `/run/book-router/**` and `/etc/book-review/rds-ca.pem`.

A primary-database named lock serializes each fresh backend's startup. The supervisor verifies that its newly spawned child owns port 3001, the required tables/columns exist and API probes succeed before releasing the lock. Named locks are advisory and connection-scoped, not a distributed transaction. Database-backed readiness intentionally fails when useful database operations fail. systemd allows three starts per 900 seconds with a 15-second restart delay. If recovery exhausts that limit, inspect the sanitized stages, restore the dependency, then perform a task-scoped `systemctl reset-failed book-app` and restart. Do not weaken readiness or run a second backend outside its supervisor.

Services run as distinct non-root users with root-owned source, read-only filesystem protections, no privilege escalation and disabled core dumps. Non-secret config uses systemd LoadCredential. Ubuntu's root-owned 0440 delivered credentials are accepted only in the exact protected `/run/credentials/<unit>/config` location; ordinary config remains 0600. Nginx uses `error_log stderr` for journald compatibility and a sufficient hostname map bucket size.

The initializer created and verified the dedicated application database identity. It was removed after successful initialization, along with its instance, profile, role, policy and log group. It is disabled in final deployment inputs. No master credential is delivered to ordinary App/Web nodes. Password and JWT inputs use ephemeral/write-only Terraform handling and are not published.

## Change and verification procedure

Work in a separate private directory. Supply task-scoped inputs and an approved existing API, image/artifact, Router certificate secret and strong ephemeral secrets. Run the pinned Terraform 1.13.5/AWS provider 6.64.0 toolchain. Validate the source, create a new real saved plan, inspect exact actions and privacy/network/cost effects, then apply that reviewed plan. A plan predating an apply or state change is stale. Initial deployment used 51-resource and 35-resource phases followed by reviewed runtime/network corrections; final reconciliation must be non-targeted.

After an ASG change, wait for all four refreshes and healthy targets. Independently verify homepage, login, books, browser review submission/reload, API authorization failures, primary/replica persistence and database TLS. Preserve original screenshot bytes and sanitized results with timestamps/hashes. Do not publish Terraform state/plans, credentials, full account IDs, raw access logs or private test-user files.

## Cost and cleanup

Eze Favour requested on 25 September that the demo remain online until an explicit cleanup request. No automatic teardown is scheduled. Baseline core resources are approximately $0.5873/hour ($14.10/day), excluding storage, public IPv4, traffic, API requests, LCU usage and taxes. This is an estimate, not the actual bill. The temporary builder and initializer are already removed.

When cleanup is requested, preserve evidence first. Disable deletion protection in a reviewed update, then review/apply a separate main destroy plan with the final primary snapshot. Destroy prerequisites afterward. Remove only this task's image/snapshots, Router TLS secret, retained database snapshots/backups and scheduled runtime secrets after checking exact identities. Verify no task ASGs, instances, load balancers, NATs, EIPs, RDS instances, VPC or artifact distribution/bucket remain. Update the historical URL to say retired. Never clean up unrelated account resources.
