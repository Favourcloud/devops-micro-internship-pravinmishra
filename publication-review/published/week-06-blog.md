# High Availability Needs Measurements: My Week 06 AWS Reflection

Eze Favour · DMI Week 06 · 26 September 2026

My Week 06 AWS reflection is about the difference between deploying redundant infrastructure and proving how it behaves during a failure. This article was prepared with Codex assistance from the repository's recorded deployment, probe and cleanup results. The operations described were performed under delegation; the evidence does not establish personal manual execution of every assignment step.

## Start with the actual system

The recorded two-tier lab used an Application Load Balancer, web instances in two Availability Zones, an Auto Scaling Group and a private encrypted Multi-AZ MySQL database. The scaling group had a minimum and desired capacity of two instances and a maximum of four. Requests reached the application through the load balancer, while the database accepted connections from the application tier using verified TLS.

The baseline included a meaningful application check: insert a row through an HTML form, then read that row through two different web instances. This connected the network and compute configuration to observable database behavior. A green infrastructure operation alone would not have proved that the application's read and write paths worked.

## Keep failed requests in the result

The abrupt instance-termination experiment recorded 287 readiness probes. Of those, 283 succeeded and four failed: two HTTP 502 responses and two timeouts. The scaling group replaced the terminated instance and healthy capacity returned across both zones.

The supported conclusion is recovery with a short observed interruption. That run did not meet the assignment's strict uninterrupted-availability criterion. Keeping the failed samples makes the result useful: it exposes the interval in which a disappeared target, load-balancer routing and replacement capacity affect real requests.

Retrying the failures out of the report would answer a different question. A sound experiment needs a stated acceptance criterion, the original probe records and a clear account of the operation performed. Planned connection draining and abrupt instance loss deserve separate tests.

## Name the scope of a successful test

A second experiment temporarily moved the web tier into one selected Availability Zone and then restored the two-zone distribution. All 260 recorded probes succeeded, and database rows written before and during the operation remained readable afterward.

This was a controlled web-tier evacuation. It did not simulate a complete AWS zone failure, a network partition or an RDS failover. Replacement capacity could be created before older capacity was removed. Those boundaries matter when turning an observation into an engineering claim.

The two tests together are more informative than a single availability label: one showed successful automatic replacement with transient errors; the other showed successful requests throughout a narrower planned operation.

## Preserve evidence and close the cost loop

The repository keeps probe records, state snapshots, application captures and clearly labeled graphics rendered from command output. Such graphics help explain the result, but their labels must distinguish them from native AWS Console screenshots.

After the experiments, Terraform destroyed all 37 temporary lab resources, and the cleanup checks confirmed an empty state and no remaining resources in the categories inspected. The older lab address is historical evidence, not a current demo URL. Separate assignments and their costs were outside that teardown.

The original run recorded 47 passing automated tests. A later local follow-up recorded 55 after adding graceful-shutdown and monitoring checks. Those later local tests do not establish that a new live failure experiment occurred or that the four earlier failed requests disappeared.

## The lesson I am documenting

A useful DevOps report connects architecture, experiment, observation and limitation. For this assignment, that means naming the failing requests, describing the successful recovery, limiting the evacuation claim to what was actually tested, and preserving cleanup evidence.

The repository still discloses exact screenshot and manual-execution requirements. Later AWS Book Review work is documented separately under Week 08; it is not silently relabeled as the original Week 06 capstone result. This reflection records the AWS resilience work whose results can be inspected today.

[Read the recorded Week 06 experiments, scope and cleanup](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/main/week-06-aws-cloud/assignment-05-ha/RESULTS.md).

This work is part of Pravin Mishra's [DevOps Micro Internship with Agentic AI](https://dmi.pravinmishra.com/), Cohort 3. [Follow my graded DMI progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
