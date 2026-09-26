# Assignment 4 — Deploy EpicBook Web App on AWS Using Terraform Modules and Amazon RDS for MySQL

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Learner:** Eze Favour

**Repository:** [Favourcloud/devops-micro-internship-pravinmishra](https://github.com/Favourcloud/devops-micro-internship-pravinmishra)
**Current status —26 September 2026:** a fresh AWS deployment now proves browser checkout and persisted RDS orders. All 22 live HTTP/SQL checks passed; browser order2 matches RDS cart3 and subtotal32.50. The temporary stack’s 28 resources were then removed. [New proof and scope](terraform-aws-epicbook/evidence/2026-09-26/README.md). Earlier screenshots and source-only limitations below describe the historical unpatched deployment. Delegated work and exact capture limitations remain disclosed.

## Historical preparation record — superseded by the live update

The following preparation notes and original screenshot captions describe their capture-time state; they do not override the current results above.

**Historical status:** OFFLINE PREPARATION ONLY — not deployed, not a completed live submission.

The [modular source and runbook](terraform-aws-epicbook/README.md) and
[sanitized local validation record](terraform-aws-epicbook/evidence/local-validation.md)
distinguish historical source/mock checks from **19 original local captures (slots 1–19)**.
The [exact 35-slot manifest](terraform-aws-epicbook/evidence/screenshot-manifest.json) retains
**slots 20–35 pending**. [Sanitized provenance and original SHA-256 hashes](terraform-aws-epicbook/evidence/provenance.json)
pin every unmodified PNG and 22 source files to commit `7c0005592f167730edb0ec3f56bf29324af6a031`.
All captures were Copilot-operated under delegation, not manual learner execution or live deployment proof.
Checked items below refer only to six source deliverables and successful local init/validate, not AWS resources.
The modular-project check covers source structure only: slot 4 shows `terraform.tfvars.example`,
not the required private `terraform.tfvars`; that file has not been created and remains gated.
Output views show source expressions, not live values. Slot 10 shows native split-editor excerpts,
not the entire script or an executed bootstrap. The parent confirmed targeted independent review
of credential fixes at the frozen source head; independent evidence-integration verification remains pending.
All live URLs, cloud provisioning, software/runtime validation, cart/database evidence, destruction,
learner reflection and mandatory LinkedIn publication remain pending behind fresh consent.
The pinned instructor app supports a cart path, but its checkout click deletes carts rather than
creating an order; see the runbook's source-derived limitation. The checkout/order checklist is not waived.

## Historical evidence-backed technical notes —19 September2026

These are factual Copilot-operated source/local-check notes, not firsthand learner reflection or new execution. Generic empty-image prompts are replaced only where the original local captures already follow; screenshot requirements, partial-view limitations and unmet live slots remain.

- The [network source](terraform-aws-epicbook/modules/network/main.tf) separates the public application subnet from two database subnets. Its security-group references limit MySQL ingress to the EC2 group; this explains the design, not a live firewall test.
- The [root source](terraform-aws-epicbook/main.tf) passes network outputs into the EC2 and RDS modules. Endpoint output expressions are configuration, not deployed addresses. The missing private input file and excerpt-only script view remain explicit in slots 4 and 10.
- The [recorded local checks](terraform-aws-epicbook/evidence/local-validation.md) and unchanged slots 18–19 establish local initialization and validation only. No real plan, application/database transaction, order workflow, destroy run, learner reflection or publication is added by this reconciliation.

---

## Purpose

In this assignment, you will use reusable Terraform modules to provision the AWS infrastructure required by EpicBook. You will create a custom VPC, one public subnet, two private database subnets across different Availability Zones, an Internet Gateway, a public route table, Security Groups, an EC2 Linux instance, and a private Amazon RDS for MySQL database.

You will use EC2 `user_data` to install the required software, initialize the EpicBook database, connect the application to Amazon RDS, configure Nginx, validate the complete browser-to-database workflow, destroy the resources after testing, and publish the required LinkedIn post.

---

# Task 0 — Set Up and Verify the Terraform and AWS CLI Environment

## Goal

Prepare your local environment by installing Terraform, AWS CLI, and the HashiCorp Terraform extension in VS Code, configuring AWS CLI, and confirming that all required tools are working correctly.

## Evidence

### Screenshot 1 — Terraform Version

Add a screenshot of the terminal showing successful `terraform version` output.

![Screenshot 1 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-01-terraform-version.png)

**Captured local evidence only:** Existing Terraform 1.13.5 on darwin_amd64, checked locally by Copilot; not a learner installation record.

---

### Screenshot 2 — AWS CLI Version

Add a screenshot of the terminal showing successful `aws --version` output.

![Screenshot 2 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-02-aws-cli-version.png)

**Captured local evidence only:** Existing AWS CLI 2.26.1 version output only; no AWS configuration, authentication, account or Region verification.

---

### Screenshot 3 — HashiCorp Terraform Extension

Add a screenshot of VS Code showing the HashiCorp Terraform extension installed and enabled.

![Screenshot 3 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-03-terraform-extension.png)

**Captured local evidence only:** Local VS Code view of the installed/enabled HashiCorp Terraform extension; Copilot-operated, not manual learner execution.

---

# Task 1 — Create the Modular Terraform Project

## Goal

Create the Terraform project and organize the AWS infrastructure into separate Network, EC2, and RDS modules.

The completed project structure must include the root Terraform files, all three module directories, and `user_data.sh`:

```text
terraform-aws-epicbook/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars
└── modules/
    ├── network/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── ec2/
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── user_data.sh
    └── rds/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Evidence

### Screenshot 4 — Modular Project Structure

Add a screenshot of the VS Code Explorer showing the complete root project and the `network`, `ec2`, and `rds` module directory structure.

Partial source evidence is supplied below; the required private input file remains pending.

![Screenshot 4 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-04-modular-project-explorer.png)

**Captured local evidence only:** Partial requirement evidence: Explorer shows the complete module directories and terraform.tfvars.example only. The required private terraform.tfvars has not been created and remains gated.

---

# Task 2 — Build the Network Module

## Goal

Create a reusable Terraform network module containing the VPC, subnets, Internet Gateway, routing, and Security Groups required by EpicBook.

The network module must include:

- VPC: `10.0.0.0/16`
- Public subnet: `10.0.1.0/24`
- Private database subnet A: `10.0.2.0/24`
- Private database subnet B: `10.0.3.0/24`
- Private database subnets in different Availability Zones
- Internet Gateway
- Public route table and public-subnet association
- EC2 Security Group allowing SSH and HTTP
- RDS Security Group allowing MySQL port `3306` only from the EC2 Security Group
- Network module variables and outputs

## Evidence

### Screenshot 5 — VPC and Subnets

Add a screenshot of VS Code showing the VPC, public subnet, and two private database subnet configurations.

![Screenshot 5 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-05-vpc-subnets-source.png)

**Captured local evidence only:** VPC and public/private subnet source configuration only; no deployed VPC or subnets.

---

### Screenshot 6 — Internet Gateway and Public Routing

Add a screenshot of VS Code showing the Internet Gateway, public route table, and route table association.

![Screenshot 6 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-06-internet-gateway-routing-source.png)

**Captured local evidence only:** Internet Gateway, public routing and association source configuration only; no created AWS resources.

---

### Screenshot 7 — EC2 and RDS Security Groups

Add a screenshot of VS Code showing the EC2 and RDS Security Groups, including MySQL access from the EC2 Security Group only.

![Screenshot 7 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-07-security-groups-source.png)

**Captured local evidence only:** EC2/RDS security-group source, including EC2-referenced MySQL ingress; no live security-group verification.

---

### Screenshot 8 — Network Module Outputs

Add a screenshot of VS Code showing the network module outputs.

![Screenshot 8 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-08-network-outputs-source.png)

**Captured local evidence only:** Network output source expressions, not actual resource IDs or runtime values.

---

# Task 3 — Build the EC2 Module and User Data Installation Script

## Goal

Create an EC2 module that launches the EpicBook application server inside the public subnet and automatically installs the required server software using EC2 user data.

The EC2 module must:

- Deploy the instance inside the public subnet
- Use the EC2 Security Group from the Network module
- Use a supported Ubuntu LTS AMI
- Assign a public IPv4 address
- Use an EC2 key pair for SSH authentication
- Connect `user_data.sh` through the EC2 `user_data` argument
- Expose the EC2 instance ID and public IP

The `user_data.sh` script must install the required software without storing database credentials or other secrets.

## Evidence

### Screenshot 9 — EC2 Resource and `user_data`

Add a screenshot of VS Code showing the EC2 resource and `user_data` configuration.

![Screenshot 9 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-09-ec2-user-data-source.png)

**Captured local evidence only:** EC2 resource and user_data template connection source only; no instance launch or executed bootstrap.

---

### Screenshot 10 — `user_data.sh`

**24 September source update:** The current bootstrap uses Node 22.23.3 with its official archive checksum. The original image below retains the earlier script; it does not prove the updated bootstrap ran. See the [current preflight](terraform-aws-epicbook/evidence/preflight-20260924.md).

Add a screenshot of VS Code showing `user_data.sh`.

Ensure that no credentials, passwords, private keys, access tokens, or application secrets are visible.

Source excerpts are supplied below; they do not show the entire script or a bootstrap run.

![Screenshot 10 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-10-user-data-script-source.png)

**Captured local evidence only:** Native split-editor source excerpts at lines 21–47 and 83–117, with editor word-wrap. Not the whole script visible, an executed script, or a synthetic composite.

---

### Screenshot 11 — EC2 Module Variables and Outputs

Add a screenshot of VS Code showing the EC2 module variables and outputs.

![Screenshot 11 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-11-ec2-variables-outputs-source.png)

**Captured local evidence only:** Native split-editor variables and output source expressions, not actual instance IDs/public IPs or a synthetic composite.

---

# Task 4 — Build the Amazon RDS Module

## Goal

Create an RDS module that provisions Amazon RDS for MySQL inside private database subnets.

The RDS module must include:

- A DB subnet group using both private database subnets
- Amazon RDS for MySQL
- RDS Security Group reference
- `publicly_accessible = false`
- Sensitive variables for database credentials
- RDS endpoint output
- No password output

## Evidence

### Screenshot 12 — DB Subnet Group and RDS MySQL

Add a screenshot of VS Code showing the DB subnet group and RDS MySQL configuration.

![Screenshot 12 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-12-rds-subnet-group-source.png)

**Captured local evidence only:** DB subnet group and MySQL resource source only; no provisioned RDS instance.

---

### Screenshot 13 — Private RDS and Sensitive Variables

Add a screenshot of VS Code showing `publicly_accessible = false`, the RDS Security Group configuration or reference, and the sensitive database variable configuration.

Ensure that the database password and other sensitive values are hidden.

![Screenshot 13 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-13-private-rds-sensitive-inputs-source.png)

**Captured local evidence only:** Native split-editor private-RDS/SG and sensitive-variable declarations, not secret values, a running database or a synthetic composite.

---

### Screenshot 14 — RDS Endpoint Output

Add a screenshot of VS Code showing the RDS endpoint output.

![Screenshot 14 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-14-rds-endpoint-output-source.png)

**Captured local evidence only:** RDS endpoint output source expressions, not an actual endpoint or runtime value.

---

# Task 5 — Connect the Terraform Modules from the Root Module

## Goal

Use the root Terraform configuration to call the Network, EC2, and RDS modules and pass values between them.

## Evidence

### Screenshot 15 — Root Module Blocks

Add a screenshot of VS Code showing the root `main.tf` with the Network, EC2, and RDS module blocks.

![Screenshot 15 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-15-root-module-blocks-source.png)

**Captured local evidence only:** Native split-editor root Network/EC2/RDS module blocks, not applied modules or a synthetic composite.

---

### Screenshot 16 — Values Passed Between Modules

Add a screenshot of VS Code showing values passed from the Network module to the EC2 and RDS modules.

![Screenshot 16 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-16-module-value-wiring-source.png)

**Captured local evidence only:** Cross-module subnet/SG input source wiring, not values returned by deployed resources.

---

### Screenshot 17 — Root Outputs

Add a screenshot of VS Code showing the root EC2 public IP and RDS endpoint outputs.

![Screenshot 17 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-17-root-outputs-source.png)

**Captured local evidence only:** Root public-IP and RDS-endpoint output source expressions, not actual public IPs, endpoints or runtime values.

---

# Task 6 — Initialize, Validate, Plan, and Apply the Terraform Configuration

## Goal

Initialize the modular Terraform project, validate the configuration, review the execution plan, and provision the AWS infrastructure.

## Evidence

### Screenshot 18 — Terraform Initialization

Add a screenshot of the terminal showing successful `terraform init` output.

![Screenshot 18 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-18-terraform-init.png)

**Captured local evidence only:** Successful local terraform init -input=false -lockfile=readonly, credential-free with the existing filesystem-only provider mirror. Implicit default local backend; no backend metadata .tfstate or managed state at the root/default or .private path was created. TF_DATA_DIR is metadata-only, not a state-path override. This was not backend-disabled init or a cloud operation.

---

### Screenshot 19 — Terraform Validation

Add a screenshot of the terminal showing successful `terraform validate` output.

![Screenshot 19 — Eze Favour — original local capture](terraform-aws-epicbook/evidence/screenshots/screenshot-19-terraform-validate.png)

**Captured local evidence only:** Successful local terraform validate, separately executed by Copilot; not a live plan, apply or deployment.

---

### Screenshot 20 — Terraform Plan

Add a screenshot showing the Terraform plan summary and proposed resources.

![Screenshot 20 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-20-terraform-plan.png)

**Recorded live-run evidence:** Selected genuine local Terraform plan output replayed with explicit delegation label; full private logs retained

---

### Screenshot 21 — Terraform Apply

Add a screenshot showing successful `terraform apply` completion.

![Screenshot 21 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-21-terraform-apply.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

### Screenshot 22 — Terraform Outputs

Add a screenshot showing the EC2 public IP and RDS endpoint returned by `terraform output`.

![Screenshot 22 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-22-terraform-outputs.png)

**Recorded live-run evidence:** Actual Terraform public IP output; private RDS hostname explicitly redacted. Full-endpoint display is a documented partial requirement.

---

# Task 7 — Verify EC2, User Data, and Amazon RDS

## Goal

Verify that the EC2 and RDS resources were successfully provisioned and confirm that the EC2 user data script installed the required software.

## Evidence

### Screenshot 23 — EC2 Running

Add a screenshot of AWS CLI showing the EC2 instance running.

![Screenshot 23 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-23-ec2-running.png)

**Recorded live-run evidence:** Live AWS CLI query executed in CloudShell, showing the EC2 running state

---

### Screenshot 24 — Private RDS Available

Add a screenshot of AWS CLI showing that RDS is available and not publicly accessible.

![Screenshot 24 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-24-private-rds-available.png)

**Recorded live-run evidence:** Live AWS CLI query executed in CloudShell; RDS available, private, encrypted and single-AZ

---

### Screenshot 25 — Installed Software and Nginx

Add a screenshot of the EC2 terminal showing the required software version checks and the active Nginx service.

![Screenshot 25 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-25-installed-software.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

# Task 8 — Prepare the EpicBook Database

## Goal

Connect from EC2 to Amazon RDS, create the EpicBook database, import the schema and seed data, and verify the database contents.

## Evidence

### Screenshot 26 — EC2-to-RDS Connection

Add a screenshot of the terminal showing a successful connection from EC2 to Amazon RDS.

Ensure that the database password is not visible.

![Screenshot 26 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-26-ec2-rds-tls.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

### Screenshot 27 — EpicBook Tables and Imported Data

Add a screenshot of the terminal showing the EpicBook tables and imported data.

![Screenshot 27 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-27-tables-and-seed-data.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

# Task 9 — Deploy and Configure the EpicBook Application

## Goal

Install EpicBook dependencies, configure the application to use Amazon RDS, configure Nginx as a reverse proxy, and start the application.

## Evidence

### Screenshot 28 — Dependencies and `node_modules`

Add a screenshot of the terminal showing successful dependency installation and the `node_modules` directory.

![Screenshot 28 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-28-installed-dependencies.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

### Screenshot 29 — Nginx Configuration and Service

Add a screenshot of the terminal showing a successful Nginx configuration test and active service status.

![Screenshot 29 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-29-nginx-configuration.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

### Screenshot 30 — EpicBook on Port `8080`

Add a screenshot of the terminal showing EpicBook running or listening on port `8080`.

![Screenshot 30 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-30-epicbook-port-8080.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

# Task 10 — Test End-to-End Functionality

## Goal

Verify that EpicBook, EC2, Nginx, and Amazon RDS work together successfully.

## EC2 Public IP URL

**EC2 Public IP URL:** `http://3.234.183.199/` — retired after verified cleanup.

**Status:** Verified during the approved run; the instance is now terminated. See the live summary and screenshots 31–34.

## Evidence

### Screenshot 31 — EpicBook Through the EC2 Public IP

Add a screenshot of the browser showing EpicBook using the EC2 public IP.

![Screenshot 31 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-31-epicbook-browser.png)

**Recorded live-run evidence:** Real EpicBook page at live EC2 IP; banner contains learner/operator and current location.href, not application functionality. Browser chrome is not captured. Original unannotated capture retained privately.

---

### Screenshot 32 — Cart or Checkout Action

Add a screenshot of the browser showing a successful cart or checkout action.

![Screenshot 32 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-32-browser-cart.png)

**Recorded live-run evidence:** Actual cart after one browser Add to Cart action: 28 Summers, quantity1, total$28. Annotation supplies learner/operator and current location.href; not instructor-app functionality. No checkout/order claimed.

---

**26 September continuation:** [Actual saved browser order2](terraform-aws-epicbook/evidence/2026-09-26/aws-order2.png) and [matching RDS order](terraform-aws-epicbook/evidence/2026-09-26/browser-order-rds.json) establish the repaired checkout path.

### Screenshot 33 — Corresponding RDS Record

Add a screenshot of the terminal showing the corresponding RDS database record created by the application action.

Ensure that database credentials and other sensitive values are not visible.

![Screenshot 33 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-33-matching-cart-rds-record.png)

**Recorded live-run evidence:** Genuine recorded command results replayed with explicit source/delegation attribution

---

# Task 11 — Destroy the Terraform Infrastructure

## Goal

Remove all AWS resources created by the modular Terraform configuration.

## Evidence

### Screenshot 34 — Terraform Destroy

Add a screenshot of the terminal showing successful `terraform destroy` completion.

![Screenshot 34 — Eze Favour — verified live run](terraform-aws-epicbook/evidence/screenshots/screenshot-34-terraform-destroy.png)

**Recorded live-run evidence:** Real saved Terraform destruction plans applied:28 application and1 key resource destroyed; both states empty and independent exact-ID checks passed. Command form is plan -destroy then apply saved plan, not literal terraform destroy.

---

# Task 12 — LinkedIn Post (Mandatory)

## Goal

Share what you built and learned from the modular AWS Terraform deployment.

Write the post in your own words and include at least one deployment screenshot or other proof. Ensure that the post can be viewed by the submission reviewer.

## Evidence

### Screenshot 35 — Published LinkedIn Post

Add a screenshot of the published LinkedIn post showing the post and at least one deployment image or other proof.

![Screenshot 35 — Published LinkedIn post with EpicBook proof](publication/linkedin-published-epicbook-cart.png)

Actual published post gallery showing EZE FAVOUR, post text and the original EpicBook cart proof. [Database image and provenance](publication/README.md) accompany this capture. The original app endpoint is retired; publication does not imply completed checkout.

## LinkedIn Post URL

**LinkedIn Post URL:** https://www.linkedin.com/posts/eze-favour-52732752_dmibypravinmishra-devops-terraform-ugcPost-7509164778045595649-LVlQ/

**Status:** Published under explicit completion authorization, with five proof images and disclosed AI-assisted wording. This does not establish manual learner execution or completed checkout.

---

# Submission Instructions

- Complete Tasks 0–12 in sequence.
- Include all Screenshots 1–35 exactly as specified.
- Ensure that your full name is visible in the required screenshots.
- Include the working EpicBook EC2 public IP URL.
- Include the published LinkedIn post URL.
- Include proof of frontend, backend, and database integration.
- Ensure that the required Terraform root files, module files, and `user_data.sh` are included in the GitHub submission.
- Do not upload Terraform state files, `.pem` files, or a `terraform.tfvars` file containing passwords or other sensitive values.
- Do not expose AWS credentials, account IDs, private SSH keys, RDS passwords, access tokens, Terraform sensitive values, or other confidential information.
- Review all screenshots and files carefully before submitting through GitHub.

---

# Completion Checklist

- [ ] Installed and verified Terraform
- [ ] Installed and verified AWS CLI
- [x] Configured AWS CLI
- [x] Confirmed the AWS Region
- [ ] Installed the HashiCorp Terraform extension
- [x] Created the modular Terraform project
- [x] Created the root `main.tf`, `variables.tf`, and `outputs.tf`
- [x] Created the Network module
- [x] Created the EC2 module
- [x] Created the RDS module
- [x] Created the EC2 `user_data.sh`
- [x] Created VPC `10.0.0.0/16`
- [x] Created public subnet `10.0.1.0/24`
- [x] Created private DB subnet A `10.0.2.0/24`
- [x] Created private DB subnet B `10.0.3.0/24`
- [x] Used different Availability Zones for the database subnets
- [x] Created and attached the Internet Gateway
- [x] Created the public route table
- [x] Associated the public subnet with the public route table
- [x] Created the EC2 Security Group
- [x] Allowed HTTP port `80`
- [x] Restricted SSH port `22`
- [x] Created the RDS Security Group
- [x] Allowed MySQL port `3306` from the EC2 Security Group only
- [x] Exposed the required Network module outputs
- [x] Defined the EC2 instance
- [x] Connected `user_data.sh` using the EC2 `user_data` argument
- [x] Configured EC2 with a public IP
- [x] Installed the required software using user data
- [x] Created the RDS DB subnet group
- [x] Created Amazon RDS for MySQL
- [x] Confirmed RDS is not publicly accessible
- [x] Configured sensitive database variables
- [x] Exposed the RDS endpoint
- [x] Connected all modules through the root module
- [x] Passed Network module outputs to EC2 and RDS
- [x] Added root EC2 public IP and RDS endpoint outputs
- [x] Completed `terraform init`
- [x] Completed `terraform validate`
- [x] Reviewed `terraform plan`
- [x] Completed `terraform apply`
- [x] Verified EC2 is running
- [x] Verified RDS is available
- [x] Verified user data installation
- [x] Connected to EC2 using SSH
- [x] Cloned EpicBook
- [x] Created the `bookstore` database
- [x] Imported the database schema
- [x] Imported author seed data
- [x] Imported book seed data
- [x] Verified database records
- [x] Installed EpicBook dependencies
- [x] Configured EpicBook to use RDS
- [x] Configured Nginx
- [x] Started EpicBook
- [x] Verified port `8080`
- [x] Loaded EpicBook through the EC2 public IP
- [x] Verified product viewing
- [x] Verified Add to Cart
- [x] Verified the checkout or order workflow (26 September AWS browser/API/RDS proof)
- [x] Confirmed application actions in Amazon RDS
- [x] Completed `terraform destroy`
- [x] Published the required LinkedIn post
- [x] Added the LinkedIn post URL
- [x] Captured all 35 required screenshots
- [ ] Confirmed that my full name is visible in the required screenshots
- [x] Checked that no sensitive information is exposed

---

## About DMI & CloudAdvisory

DevOps Micro Internship (DMI) is a project-based DevOps program run by Pravin Mishra (The CloudAdvisory), focused on real-world execution, systems thinking, and career readiness.

It helps learners build strong DevOps foundations through hands-on experience.

---

## Resources

- EpicBook Repository: [https://github.com/pravinmishraaws/theepicbook](https://github.com/pravinmishraaws/theepicbook)
- EpicBook Installation, Configuration & Troubleshooting Guide: [Installation & Configuration Guide](https://github.com/pravinmishraaws/theepicbook/blob/main/Installation%20%26%20Configuration%20Guide.md)
- DMI Official Website: [https://dmi.pravinmishra.com](https://dmi.pravinmishra.com)
- University: [https://university.pravinmishra.com](https://university.pravinmishra.com)
- Discord Community: [https://discord.pravinmishra.com](https://discord.pravinmishra.com)
- Blog: [https://dmi.pravinmishra.com/blog](https://dmi.pravinmishra.com/blog)
- YouTube Playlist: [https://www.youtube.com/playlist?list=PLFeSNDtI4Cho](https://www.youtube.com/playlist?list=PLFeSNDtI4Cho)
- Pravin Mishra on LinkedIn: [https://www.linkedin.com/in/pravin-mishra-aws-trainer/](https://www.linkedin.com/in/pravin-mishra-aws-trainer/)
- CloudAdvisory on LinkedIn: [https://www.linkedin.com/company/thecloudadvisory/](https://www.linkedin.com/company/thecloudadvisory/)

---

*This submission is part of the DevOps Micro Internship (DMI) Cohort 3 — Agentic AI Track.*
