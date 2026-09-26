# Cloud deployment

Terraform created a dedicated VPC, public subnet, route table and association, internet gateway, security group, two t3.medium Ubuntu 24.04 VMs, and two Elastic IPs. A separate reviewed plan added the CloudFront distribution. Existing Week 07–10 demos were not modified. The VM images use encrypted 40 GB gp3 root disks, IMDSv2, standard CPU credits and no instance IAM role. The existing operator SSH key was reused. Host keys were obtained from authenticated EC2 console output before establishing SSH trust.

Cloud-init installs Docker from Docker's signed Ubuntu repository, enables its service and installs the Compose/Buildx plugins. Docker 29.8.1 and Compose 5.5.1 were observed. SSH is restricted to the operator /32. HTTP/HTTPS are allowed; port 3000 was restricted to the operator during the single-stage comparison and that container is now stopped. Database ports are not allowed by the AWS security group and have no Docker host bindings.

- React lab: http://3.225.177.203/
- EpicBook HTTPS: https://d209ibroel8p0b.cloudfront.net/
- Direct EpicBook teaching origin: http://98.86.65.226/
- Docker Hub: https://hub.docker.com/r/favourcloud/my-react-app

These are paid cloud resources. They remain online under the learner's explicit keep-online instruction. Teardown is deferred until requested. This is a single-host application architecture; the second VM is the lab machine, not a standby or load-balanced replica. Origin HTTP, local Compose file secrets and absence of automatic backups/alerting are explicit production limitations.

At 22:14 UTC the operator network had changed. Through the authenticated AWS console, only the SSH and comparison-port sources were replaced with the new operator /32; HTTP/HTTPS rules stayed unchanged. Private Terraform inputs were updated to match, and the next authenticated Terraform refresh should reconcile state. SSH then succeeded and all four Compose services were healthy in [the final state record](../../evidence/2026-09-26/a6-final-state.txt).
