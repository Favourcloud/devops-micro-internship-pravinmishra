# High Availability Is Not a Promise: What Four Failed Requests Taught Me

**Week 06 — AWS Cloud | Eze Favour**


## From a working application to a measurable system

A working page is a useful beginning, but it is not the same as a dependable system. My Week 06 AWS work made that distinction concrete: I had deployment verification, recovery evidence, and remaining submission requirements that needed to be described separately.

The two-tier EpicBook deployment connected a public-facing application through Nginx to a private MySQL RDS database. The later verification record reported a successful frontend response, backend health response, books returned through the API, and database access from EC2. Those checks supported the deployment result. They did not replace the missing screenshots showing both subnets, the explicit RDS public-access setting, and the browser view. I now keep those screenshot-backed requirements open rather than treating a working endpoint as proof of every deliverable.

The next question was more demanding: what would happen when part of the application infrastructure stopped working?

## The architecture helped, but the measurements mattered more

The high-availability lab used an Application Load Balancer, web instances distributed across two Availability Zones, an Auto Scaling Group, and a private encrypted Multi-AZ MySQL database. The group's minimum and desired capacity were two instances, with a maximum of four. The application used ordinary HTML forms, and the evidence included actual database writes and reads through different web instances.

That architecture provided redundancy. It did not, by itself, establish uninterrupted availability. To investigate behavior rather than rely on a diagram, the experiment collected readiness probes that also performed a database query. It retained failed requests instead of retrying them out of the results.

That distinction changed the conclusion I could honestly draw.

## Four failures were part of the result, not a detail to remove

During the abrupt instance-termination test, automatic replacement succeeded. Of 287 readiness probes, 283 succeeded and four failed. The failures included two HTTP 502 responses and two timeouts.

The useful result was not “zero downtime.” It was evidence that replacement and recovery worked while a short interruption remained visible. The assignment's strict uninterrupted-availability requirement was not met by that run.

This matters because a surviving instance and an Auto Scaling Group do not make every request succeed immediately after a target disappears. Detection, routing, and replacement take time. A successful recovery is valuable, but it answers a different question from whether every first-attempt request succeeded.

Keeping the failures in the report makes the next engineering decision clearer. Before another experiment, I would want an agreed acceptance criterion and a spending limit. Orderly connection draining, retry behavior, and abrupt instance loss should not be silently treated as the same test.

## A second test answered a narrower question

The controlled web-tier Availability Zone evacuation produced 260 successful probes out of 260. The web instances served from the remaining selected zone, database writes and reads continued, and the original two-zone distribution was restored. Previously written records remained readable afterward.

That was useful evidence of the specific operation tested. It was not a complete AWS Availability Zone outage, network partition, or RDS failover experiment. The procedure could create replacement capacity before removing old capacity, and the load balancer and database were not subjected to an equivalent zone-wide failure.

The lesson is to describe both the observation and its boundary. “No failed samples during this controlled evacuation” is supported by the evidence. A promise that all possible outages would be interruption-free is not.

## Evidence, cleanup, and cost belong in the same workflow

The lab produced raw probe records, state snapshots, application captures, and readable summaries. Some architecture and availability images were rendered from recorded CLI evidence. They are labeled that way rather than presented as original AWS Console screenshots.

A later review also identified a practical evidence-management problem: a future retest could overwrite the historical termination record. The runner now requires a fresh destination, refuses an existing record before termination, and records the action through the file reserved for that invocation. Local regression tests check this behavior without terminating another instance. The historical experiment files were preserved unchanged.

Cleanup was another deliverable, not an optional final step. Terraform destroyed all 37 temporary lab resources, and the cleanup record documented the checks performed. The earlier Assignment 4 deployment was excluded from that teardown. Removing the temporary lab does not mean the account has no remaining costs, and the old load-balancer URL must not be advertised as a live service after deletion.

## What AI assistance did—and what it did not prove

I used AI assistance to prepare implementation work, examine results, and identify inconsistencies between evidence and completion claims. That assistance is useful when it makes the reasoning and checks reproducible. It is not a substitute for recorded outcomes or instructor acceptance.

The three-tier capstone illustrates the boundary. Its current work includes read-only preflight evidence, guarded Terraform preparation, and local tests. It is not a completed deployment. Approved access, spending boundaries, the missing infrastructure additions, and real end-to-end verification still remain.

Local tests can check that a guard rejects an unsafe input. They cannot establish that an uncreated application is reachable, that a replica is working, or that a screenshot exists.

## The habit I want to keep

My practical takeaway from Week 06 is to keep a short evidence ledger for each task: what was built, what was actually tested, what the result showed, and what remains unverified.

For this work, that means preserving the four failed probes, naming the limited scope of the evacuation test, retaining missing screenshot requirements, and treating cleanup and cost controls as part of delivery. It also means improving the implementation without rewriting older results to make them look better.

Reliable engineering communication is precise enough to be checked. That is the standard I want my next assignment to meet—not just a green checklist or a convincing architecture diagram.

## Recorded work behind this reflection

- [Assignment 4 deployment verification and outstanding screenshot evidence](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/4b74f674e608d183e0f5a5e250686d6330ce242c/week-06-aws-cloud/assignment-04-deploy-epicbook-on-ubuntu-vm-and-mysql-rds.md#deployment-verification-and-evidence-status)
- [Assignment 5 actual experiment, limitations, publication, and cleanup results](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/4b74f674e608d183e0f5a5e250686d6330ce242c/week-06-aws-cloud/assignment-05-ha/RESULTS.md)
- [Assignment 5 reproducible implementation and retest boundaries](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/4b74f674e608d183e0f5a5e250686d6330ce242c/week-06-aws-cloud/assignment-05-ha/README.md)
- [Assignment 6 preflight, local preparation, and remaining deployment requirements](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/4b74f674e608d183e0f5a5e250686d6330ce242c/week-06-aws-cloud/assignment-06-capstone-deploy-book-review-app-three-tier-architecture-on-aws.md)

This work is part of the [DevOps Micro Internship](https://dmi.pravinmishra.com/) led by [Pravin Mishra](https://www.linkedin.com/in/pravin-mishra-aws-trainer/).

[Follow my graded progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
