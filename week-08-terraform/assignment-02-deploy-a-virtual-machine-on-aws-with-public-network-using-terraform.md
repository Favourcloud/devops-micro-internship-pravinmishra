# Assignment 2 — Create an AWS EC2 Virtual Machine Using Terraform

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Learner:** Eze Favour

**Repository:** [Favourcloud/devops-micro-internship-pravinmishra](https://github.com/Favourcloud/devops-micro-internship-pravinmishra)

**Status: live AWS lab completed and cleaned up — 10 of 10 genuine captures included.**

On 23 September 2026, the approved [Terraform project](terraform-aws-vm/README.md) created a custom VPC, public and private subnets, Internet Gateway, route tables, security group, SSH key import and Ubuntu EC2 instance in `us-east-1`. The actual apply added 11 resources. AWS CLI confirmed the running instance and matching public IP; SSH verified cloud-init completion and active Nginx, and the browser loaded the named page. Terraform subsequently destroyed all 11 resources. Exact-ID AWS checks confirmed cleanup of the managed objects, root disk and network interface, and the state was empty.

Screenshots 1–4 are the unchanged earlier local captures, operated by GitHub Copilot. Screenshots 5–10 are the new live captures, operated by Codex under user delegation, not manual learner execution. The original rubric remains intact, and checkmarks below record verified delegated work. The local HashiCorp Terraform extension is installed in Visual Studio Code as version 2.40.0. See the [manifest](terraform-aws-vm/evidence/manifest.json), [historical capture provenance](terraform-aws-vm/evidence/capture-provenance.json), [live provenance](terraform-aws-vm/evidence/live-capture-provenance.json) and [run summary](terraform-aws-vm/evidence/live-run-summary.md). No personal reflection or new grade is claimed.

---

## Purpose

In this assignment, you will use Terraform to provision a complete AWS environment consisting of a custom VPC, public and private subnets, an Internet Gateway, a public route table, a security group, and an EC2 instance deployed inside the public subnet.

You will configure SSH and HTTP access, install Nginx, capture the EC2 instance’s public IP address, verify the deployment using AWS CLI and a web browser, and destroy all Terraform-managed resources after testing.

---

# Task 0 — Set Up and Verify the Terraform and AWS CLI Environment

## Goal

Prepare your local environment for Terraform deployment by installing Terraform, AWS CLI, and the HashiCorp Terraform extension in VS Code, configuring AWS CLI with your AWS account, and confirming that all required tools are working correctly.

### Evidence

#### Screenshot 1 — Terminal showing successful `aws --version` output

Ensure that your full name is visible and that no AWS credentials, account IDs, or other sensitive information are exposed.

![Eze Favour — Screenshot 1: local AWS CLI version](terraform-aws-vm/evidence/screenshot-01-aws-cli-version.png)

Genuine, unmodified local capture showing the installed AWS CLI version. Copilot-operated under user delegation; this does not verify AWS account access.

---

# Task 1 — Create a New Terraform Project and Define the Infrastructure

## Goal

Create a new Terraform project and define the complete AWS EC2 environment in `main.tf` by using the official Terraform Registry documentation.

The configuration must include:

* Terraform and AWS provider configuration
* Custom VPC using the CIDR block `10.0.0.0/16`
* Public subnet using the CIDR block `10.0.1.0/24`
* Private subnet using the CIDR block `10.0.2.0/24`
* Internet Gateway
* Public route table with a route to `0.0.0.0/0`
* Public subnet route table association
* Security group allowing SSH on port `22`
* Security group allowing HTTP on port `80`
* EC2 instance deployed inside the public subnet
* SSH authentication configuration
* Public IP address association
* Public IP output block

### Evidence

#### Screenshot 2 — VS Code showing the AWS provider configuration and VPC configuration in `main.tf`

![Eze Favour — Screenshot 2: AWS provider and VPC source in main.tf](terraform-aws-vm/evidence/screenshot-02-aws-provider-vpc-source.png)

Genuine VS Code source capture. The AMI data block is folded in the editor so the provider and VPC are visible together; neither HCL nor PNG pixels were modified.

---

#### Screenshot 3 — VS Code showing the EC2 instance configuration and public IP `output` block in `main.tf`

Ensure that no AWS credentials, private keys, account IDs, or other sensitive information are visible.

![Eze Favour — Screenshot 3: EC2 and public-IP output source in main.tf](terraform-aws-vm/evidence/screenshot-03-ec2-public-ip-source.png)

Genuine VS Code capture of the EC2 resource and public-IP **output source**. This is not an actual EC2 instance, Terraform output result, or deployed public IP.

---

# Task 2 — Initialize Terraform

## Goal

Initialize the Terraform working directory and download the required provider components.

### Evidence

#### Screenshot 4 — Terminal showing the successful `terraform init` output

![Eze Favour — Screenshot 4: successful normal local-backend Terraform init](terraform-aws-vm/evidence/screenshot-04-terraform-init.png)

Actual `terraform init -input=false -lockfile=readonly` completed with the **local** backend targeting `.private/terraform.tfstate`, using the AWS 6.64.0 filesystem-only provider mirror. The capture session verified an `env -i` startup guard, empty authentication configuration, disabled metadata discovery, and no managed resource state. This differs from the earlier mock runner's `-backend=false` initialization; neither result establishes an AWS deployment.

---

# Task 3 — Plan and Apply the Configuration

## Goal

Review the Terraform execution plan, provision the AWS resources, and record the EC2 instance’s public IP address from the Terraform output.

### Evidence

#### Screenshot 5 — Terraform plan summary showing the proposed resources

![Eze Favour — Screenshot 5: real Terraform plan](terraform-aws-vm/evidence/screenshot-05-terraform-plan.png)

The saved real plan proposed 11 additions, no changes and no deletions. This exact reviewed plan was subsequently applied under the user’s approval.

---

#### Screenshot 6 — Terraform apply output showing successful completion

![Eze Favour — Screenshot 6: successful Terraform apply](terraform-aws-vm/evidence/screenshot-06-terraform-apply.png)

Actual Terraform apply completed: 11 resources added, 0 changed, 0 destroyed. This output was followed by independent application and AWS checks.

---

#### Screenshot 7 — Terraform output showing the public IP address of the EC2 instance

![Eze Favour — Screenshot 7: actual EC2 public IP output](terraform-aws-vm/evidence/screenshot-07-public-ip-output.png)

Terraform returned the actual public IP 3.80.169.89 for instance i-05972a6598e2eb990. This address was retired after the lab was destroyed; it is historical evidence, not a current endpoint.

---

### EC2 Public IP Address

Record the public IP address displayed by `terraform output`.

**EC2 Public IP Address:** `3.80.169.89` — retired after verified teardown on 23 September 2026; not a current endpoint.

---

# Task 4 — Verify the Deployment

## Goal

Confirm through AWS CLI that the EC2 instance was created successfully and is running, and verify HTTP access through the instance public IP.

Confirm that:

* The EC2 instance appears in the AWS CLI output.
* The EC2 instance state shows `running`.
* The public IP shown by AWS matches the public IP recorded from Terraform.
* Nginx is installed and running.
* The Nginx page is accessible through the EC2 instance’s public IP.

### Evidence

#### Screenshot 8 — AWS CLI output showing the EC2 instance ID, `running` state, and public IP address

![Eze Favour — Screenshot 8: running EC2 instance and matching public IP](terraform-aws-vm/evidence/screenshot-08-ec2-running.png)

AWS CLI showed instance i-05972a6598e2eb990 running at 3.80.169.89. Both identifiers matched Terraform outputs; EC2 system and instance health were ok.

---

#### Screenshot 9 — Browser showing the Nginx page successfully loaded using the EC2 instance public IP

![Eze Favour — Screenshot 9: live Nginx page in the browser](terraform-aws-vm/evidence/screenshot-09-nginx-browser.png)

The browser loaded the Nginx page from `http://3.80.169.89/` during the live run. The content capture excludes the address bar; the selected tab URL and independent HTTP/SSH checks are recorded in the live provenance. The address was retired after teardown.

---

# Task 5 — Destroy the Resources

## Goal

Remove all AWS resources created by Terraform after completing the deployment and verification.

### Evidence

#### Screenshot 10 — Terminal showing successful `terraform destroy` completion

![Eze Favour — Screenshot 10: Terraform destroy and exact cleanup checks](terraform-aws-vm/evidence/screenshot-10-terraform-destroy.png)

Terraform destroyed all 11 managed resources. The exact-ID cleanup helper passed all 13 checks, including the root EBS volume and primary network interface; Terraform state was empty.

---

# Submission Instructions

* Complete all tasks in sequence.
* Include all required screenshots specified in Tasks 0–5.
* Ensure that your full name is visible in the required screenshots.
* Record the EC2 public IP address in Task 3.
* Follow the screenshot requirements exactly as specified.
* Ensure that the submitted evidence clearly matches the required task outputs.
* Do not expose AWS access keys, secret keys, private keys, passwords, account IDs, or other sensitive information.
* Do not upload your private key file (`.pem`) to your GitHub repository.
* Review your submission carefully before submitting it through GitHub.

---

# Completion Checklist

Checked items below record the earlier local preparation and the approved September 23 live run. Codex verified account access and Region through the existing CloudShell session, completed the real plan/apply, checked EC2 and Nginx through AWS CLI/SSH/HTTP/browser, and verified Terraform teardown. These are verified delegated operations, not manual learner execution.

* [x] Installed Terraform and verified it using `terraform version`
* [x] Installed AWS CLI and verified it using `aws --version`
* [x] Configured AWS CLI and verified account access
* [x] Confirmed the correct AWS Region
* [x] Installed and enabled the HashiCorp Terraform extension in VS Code
* [x] Created the `terraform-aws-vm` project directory and `main.tf`
* [x] Added the Terraform and AWS provider configuration
* [x] Defined the custom VPC, public subnet, and private subnet
* [x] Configured the Internet Gateway and public route table
* [x] Associated the public route table with the public subnet
* [x] Defined the security group for SSH and HTTP access
* [x] Restricted SSH access to my public IP whenever possible
* [x] Defined the EC2 instance inside the public subnet
* [x] Configured SSH authentication without exposing the private key
* [x] Added the Terraform output for the EC2 public IP address
* [x] Completed `terraform init` successfully
* [x] Reviewed the Terraform execution plan using `terraform plan`
* [x] Completed `terraform apply` successfully
* [x] Captured and recorded the EC2 public IP using `terraform output`
* [x] Verified that the EC2 instance is running using AWS CLI
* [x] Verified that the AWS public IP matches the Terraform output
* [x] Verified Nginx access through the EC2 public IP
* [x] Completed `terraform destroy` successfully
* [x] Captured all 10 required screenshots
* [x] Confirmed that my full name is visible in the required screenshots
* [x] Checked that no AWS credentials, private keys, passwords, account IDs, or other sensitive information are visible
* [x] Confirmed that no `.pem` private key file has been uploaded to the GitHub repository

---

## 📌 About DMI & CloudAdvisory

DevOps Micro Internship (DMI) is a project-based DevOps program run by Pravin Mishra (The CloudAdvisory), focused on real-world execution, systems thinking, and career readiness.

It helps learners build strong DevOps foundations through hands-on experience.

---

## 📌 Resources

* 🌐 DMI Official Website: https://dmi.pravinmishra.com?utm_source=github&utm_medium=readme
* 🎓 University: https://university.pravinmishra.com?utm_source=github&utm_medium=readme
* 💬 Discord Community: https://discord.pravinmishra.com?utm_source=github&utm_medium=readme
* 📝 Blog: https://dmi.pravinmishra.com/blog?utm_source=github&utm_medium=readme
* ▶️ YouTube Playlist: https://www.youtube.com/playlist?list=PLFeSNDtI4Cho
* 🔗 Pravin Mishra (LinkedIn): https://www.linkedin.com/in/pravin-mishra-aws-trainer/
* 🏢 CloudAdvisory (LinkedIn): https://www.linkedin.com/company/thecloudadvisory/

---

*This submission is part of the DevOps Micro Internship (DMI) Cohort 3 — Agentic AI Track.*
