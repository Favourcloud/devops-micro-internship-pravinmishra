# Assignment 7 — AI-Assisted AWS Security and Cost Audit

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

---

## Purpose

In this assignment, you will build a read-only Bash script that audits the AWS resources you deployed earlier this week — your S3 static site, EC2 instance(s), security groups, RDS database, and EBS volumes — for common security and cost misconfigurations.

You will then connect that script to Claude Code as a reusable `/aws-audit` skill that explains what it found and recommends a fix, without ever making the fix itself.

Finally, you will find a real misconfiguration in your own account, apply the fix yourself, and prove it worked with a second audit run.

## Evidence audit — 13 September 2026

**Status: historical Bash audit and manual SSH remediation are evidenced; the complete source submission and successful Claude skill workflow are not.** No AWS changes were made during this documentation audit.

- The inventory capture uses `eu-north-1` and lists `epicbook-db` and `ha-mysql-db`. The later script/report uses `ap-south-1` and `week7-audit-db`. That scope change must be explained and verified before claiming this audited the same EC2/RDS resources as the earlier assignments.
- The baseline reports **3 PASS, 1 WARN, 1 FAIL; overall FAIL; reported exit code 2**. S3 public-ACL protection fails and one EBS volume is unencrypted.
- A later pre-remediation capture reports SSH open to `0.0.0.0/0`. Successful manual revoke/authorize responses and a subsequent **SSH PASS** are shown. S3 remains FAIL and EBS remains WARN; the overall result is still FAIL.
- The Claude planning capture ends with **Credit balance too low**, and the claimed skill-output capture shows only the Claude startup banner. Neither proves a completed plan or successful `/aws-audit` run.
- The linked check-function image is a **1×1 placeholder**. All 14 generic `assignment-07-...-screencap-*.png` files have those placeholder dimensions; use the substantive named screenshots below instead.

### Required source artifacts still missing from this repository

The screenshots refer to `C:\Users\FAVOUR\week-06-aws-audit`, but its audit-specific `CLAUDE.md`, `scripts/aws-audit.sh`, `.claude/skills/aws-audit/SKILL.md`, and original baseline/reverified text reports are absent from this checkout. The top-level repository `CLAUDE.md` describes a different portfolio/Terraform project. Screenshots are not substitutes for the required executable source and report files. No reconstructed script or report is presented as the original.

---

# Task 1 — Confirm Your AWS Resources and Set Up Your Workspace

## Goal

Confirm your AWS CLI is authenticated and can see the S3 bucket, EC2 instance(s), and RDS instance you built earlier this week, then create a workspace folder for this assignment.

### Evidence

#### Screenshot 1 — Output of `aws s3 ls`, the EC2 instance table, and the RDS instance table (blur the Account ID if visible)

![Screenshot 1](<Screenshot week6 assign7 scrn 1.png>)

---

#### Screenshot 2 — Output of `pwd` and `find . -maxdepth 4 -type d | sort`

![Screenshot 2](<Screenshot week6 assign7 scrn 2.png>)

---

### Notes You Must Write (Very Important)

**1. Which resources from this week's earlier assignments did you see in the listings?**

The capture lists S3 bucket `pravin-portfolio-favour-af-south-1`, three stopped EC2 instances in `eu-north-1`, and available RDS instances `epicbook-db` and `ha-mysql-db` in `eu-north-1`. It does not show a security-group inventory. The later report instead identifies `ap-south-1` and RDS `week7-audit-db`; its EC2/RDS/EBS results must not be attributed to the earlier region without matching evidence. The bucket's name is not proof of its actual region.

**2. Why must you confirm your resources exist before writing an audit script against them?**

The audit script depends on real AWS identifiers such as instance IDs, bucket names, security group IDs, and database identifiers. If the resources do not exist, the script would either fail, return empty results, or produce misleading findings. Confirming the inventory first ensures that the reporting logic is grounded in the actual AWS environment.

---

# Task 2 — Define Safety Rules in CLAUDE.md

## Goal

Create a `CLAUDE.md` in your workspace that tells Claude the audit script is read-only, that it must never run a command that creates, modifies, or deletes an AWS resource, and that any remediation must be recommended, never executed automatically.

### Evidence

#### Screenshot 3 — `CLAUDE.md` open in VS Code showing all four sections

![Screenshot 3](<Screenshot week6 assign7 scrn3.png>)

The editor shows Project Overview, Audit Workflow, Safety Rules, and Output Rules for the audit workspace. The corresponding source file is still required in the submission.

---

### Notes You Must Write (Very Important)

**1. Why should Claude never be given permission to run `revoke-security-group-ingress` itself, even if the fix is obviously correct?**

Even when a remediation is clearly correct, the automation should not be trusted to perform network changes without human validation. Security group modifications can remove access unexpectedly, affect application connectivity, or create a production outage. The safe pattern is to recommend the remediation and let the human approve and execute it after reviewing the evidence.

**2. Which rule prevents Claude from claiming a finding that the report does not support?**

The captured rule says: **“Do not claim a finding unless the report contains supporting evidence.”** Report the resource, region, check, and observed status, and distinguish a failed control from proof of an actual exposure or a successful remediation.

---

# Task 3 — Plan the Audit with Claude Code

## Goal

Ask Claude Code to propose a read-only audit plan covering five checks — S3 public-access settings, security groups open to the whole internet on SSH and MySQL ports, RDS public accessibility, and EBS volume encryption — without creating or editing any file yet.

### Evidence

#### Screenshot 4 — Five-check planning request blocked by insufficient credit

![Screenshot 4](<Screenshot week6 assign7 task3 scrn4.png>)

The prompt requests exactly five checks, but Claude returns **Credit balance too low**. No generated plan is visible, so this task remains incomplete.

---

### Notes You Must Write (Very Important)

**1. Which part of this task represents the Gather phase?**

Gather means collecting inventory and AWS configuration evidence with read-only calls. The prompt requests a plan for that collection; it does not show Claude actually inspecting AWS, and billing prevented a visible plan response.

**2. Did every proposed command start with `describe-`, `get-`, or `list-`? Why does that matter?**

This cannot be verified because no completed plan is shown. The intended checks should use read-only APIs, such as `s3api get-public-access-block`, `ec2 describe-security-groups`, `rds describe-db-instances`, and `ec2 describe-volumes`. Reviewing the actual calls and IAM permissions matters more than relying on command-name prefixes alone.

---

# Task 4 — Build the AWS Audit Script

## Goal

Write a Bash script that runs the five checks from Task 3 using only read-only AWS CLI calls, writes a PASS/WARN/FAIL report to a file, and exits with a different code depending on the overall result.

Make it executable and confirm it has no syntax errors.

### Evidence

#### Screenshot 5 — Top section of `aws-audit.sh` showing the variables and the checks array

![Screenshot 5](<Screenshot week6 assign7 task4 scrn5.png>)

This capture shows an early script draft with `YOUR FULL NAME`, `ap-south-1`, `week7-audit-db`, and five check-function names. Later output shows the name corrected to `FAVOUR EZE`. Supply the final complete source so function behavior, scope, error handling, and exit codes can be reviewed.

---

#### Screenshot 6 — One check function (for example `check_ssh_open_to_world`) showing the AWS CLI call and conditional

**Missing.** The previous link pointed to a 1×1 placeholder, not a check function. Supply a real function capture showing its AWS CLI call, condition, and PASS/WARN/FAIL handling.

---

#### Screenshot 7 — Output of `bash -n scripts/aws-audit.sh` and `ls -l scripts/aws-audit.sh`

![Git Bash syntax check reports PASS and ls shows executable aws-audit.sh permissions](<Screenshot Week6 assign7 task5 scrn8.png>)

The upper portion shows `bash -n: PASS` and executable permissions for a 5,413-byte script; the lower portion is the baseline run used in Task 5. The previously linked `task4 scrn5b.png` shows editing an incomplete script rather than syntax/executable verification. The full final script is not available to rerun `bash -n` in this checkout.

---

### Notes You Must Write (Very Important)

**1. What is stored in the checks array, and how does the loop use it?**

The draft lists `check_s3_public_access`, `check_ssh_open_to_world`, `check_mysql_open_to_world`, `check_rds_public_access`, and `check_ebs_encryption`. The displayed loop calls each named function through `"${checks[@]}"`. The final source is needed to verify the actual implementations and counters.

**2. Why does every AWS CLI call in this script use `--query` and `--output text` instead of parsing raw JSON?**

`--query` selects fields and `--output text` makes simple values easier to evaluate in Bash. The screenshots do not show every final AWS call, so universal use of these options cannot be asserted. The source must also distinguish API/permission failures and empty results from a true PASS.

**3. Why does the script use different exit codes for HEALTHY, WARN, and FAIL?**

Distinct exit codes let automation distinguish HEALTHY, WARN, and FAIL. The captured report prints **Script Exit Code: 2** for overall FAIL. The complete script and reliable shell-level capture are still needed to verify all exit-code paths; a value printed by the script alone does not prove the process's exit status.

---

# Task 5 — Run the Baseline Audit

## Goal

Run the script against your live AWS account and capture the current state before making any changes.

### Evidence

#### Screenshot 8 — Output of `./scripts/aws-audit.sh` showing your Full Name and all five checks

![Screenshot 8](<Screenshot Week6 assign7 task5 scrn8.png>)

---

#### Screenshot 9 — Final summary and attempts to capture the process exit code

![Screenshot 9](<Screenshot week6 assign7 task5 scrn9.png>)

The report prints exit code `2`. One wrapper command has a quoting error; the later output ends with `captured` without a visible numeric value. Capture `$?` directly in Bash after the script and retain it before running another command. Save the original baseline and after-fix reports under distinct filenames so a rerun does not overwrite the baseline.

---

### Notes You Must Write (Very Important)

**1. What is the overall status of your baseline audit?**

The historical baseline at `2026-08-31T21:54:57Z` reports **FAIL**, with **PASS: 3, WARN: 1, FAIL: 1** and a printed exit code of **2**. It identifies `FAVOUR EZE`, region `ap-south-1`, the portfolio S3 bucket, and RDS `week7-audit-db`. The later baseline attempt at `22:01:31Z` shows the same counts. This is evidence of the captured run, not today's AWS state or an independent verification of the missing script.

**2. Did any check return FAIL or WARN? If so, which one, and what evidence did it show?**

| Check | Captured baseline result | Evidence and limits |
| --- | --- | --- |
| S3 public-ACL protection | FAIL | `BlockPublicAcls=False`, `IgnorePublicAcls=False` for the portfolio bucket. This fails the script's stated control; it does not alone prove objects are public. Review Object Ownership, account-level controls, bucket policy, and the intentional static-website configuration before selecting a fix. |
| SSH open to IPv4 internet | PASS | Report says no security group permits port 22 from `0.0.0.0/0` in the audited scope. A later pre-fix run does show one such rule. |
| MySQL open to IPv4 internet | PASS | Report says no security group permits port 3306 from `0.0.0.0/0`; IPv6 coverage is not established. |
| RDS public accessibility | PASS | Report says `week7-audit-db` is not publicly accessible; this is a different DB from the Task 1 inventory. |
| EBS encryption | WARN | Report says one volume is unencrypted, but does not identify the volume, size, attachment state, or monthly cost. |

No numeric monthly cost or savings estimate is justified by these captures. In particular, lack of EBS encryption is a security finding, not evidence that a volume is unused or can be deleted.

**3. If every check passed, what does that tell you about the security posture of your account so far?**

Every check did not pass here. Even a clean run would establish only the checked controls, resources, region, and timestamp, assuming reliable API/error handling. It would not prove complete AWS security or cost optimization.

---

# Task 6 — Build and Run the /aws-audit Skill

## Goal

Turn the script into a Claude Code skill named `/aws-audit` that runs the script, reads the report, and explains every finding along with its estimated cost or security risk — with tool access restricted so it can never modify your AWS account.

### Evidence

#### Screenshot 10 — `SKILL.md` showing the frontmatter, tool restrictions, and safety rules

![Screenshot 10](<Screenshot week6 assign7 task6 scrn10.png>)

The editor capture shows an intended `aws-audit` definition and a `Bash, Read, Grep` tool list. The source is missing, so valid frontmatter, exact installed path, and effective permissions cannot be fully checked. Unrestricted Bash can write files or call mutating AWS APIs even when the separate Write tool is absent; this tool list alone does not enforce read-only behavior.

---

#### Screenshot 11 — Claude startup banner; successful skill output missing

![Screenshot 11](<Screenshot week6 assign7 task6 scrn11.png>)

No `/aws-audit` invocation, findings, cost/risk analysis, or recommendation appears. Supply the actual skill source and a complete successful invocation before marking this task done.

---

### Notes You Must Write (Very Important)

**1. Why does this skill have Bash, Read, and Grep, but not Write?**

Read and Grep support inspection; Bash runs the audit. Omitting Write reduces direct editor capabilities but does **not** make broad Bash access read-only. The actual command restrictions, reviewed script, and read-only AWS IAM permissions must enforce the boundary. The current screenshot is evidence of intended rules, not proof that AWS mutations are technically impossible.

**2. What part is performed by Bash, and what part is performed by Claude?**

The captured Bash run performs checks and writes a local report. Claude is intended to read that report and explain findings and recommended remediation; that successful analysis step is not visible in Screenshot 11. Local report writing is compatible with an audit that is read-only with respect to AWS resources.

**3. Why is estimating cost/risk impact something the AI adds on top of a plain PASS/FAIL script?**

A PASS/FAIL signal does not describe impact or urgency. AI can explain the observed control failure and prioritize review, but monetary estimates require supporting resource size, usage, pricing, and billing-period assumptions. Unsupported savings estimates should not be invented.

---

# Task 7 — Fix a Real Finding and Re-Verify

## Goal

Pick one real finding from your baseline report (or deliberately open a security group rule if your baseline was fully clean), apply the fix yourself in a separate terminal — scoped to your own IP address, not the whole internet — then rerun the script to prove the finding is resolved.

### Evidence

#### Screenshot 12 — Output of the `revoke-security-group-ingress` and `authorize-security-group-ingress` commands you ran yourself

![Screenshot 12](<Screenshot week6 assign7 task7 scrn12.png>)

---

#### Screenshot 13 — Rerun of `./scripts/aws-audit.sh` showing the finding is now PASS

![Screenshot 13](<Screenshot week6 assign7 task7 scrn13.png>)

---

### Notes You Must Write (Very Important)

**1. Which exact finding did you fix, and what command did you run?**

The later pre-fix report in Screenshot 12 shows **one security group allowing SSH (port 22) from `0.0.0.0/0`**, with 2 PASS, 1 WARN, and 2 FAIL. The initial baseline had SSH PASS; the capture does not show how or when the open rule was introduced.

The PowerShell terminal then shows these historical commands returning `Return: true` for `sg-001ddd6b6281ab83b`:

```bash
aws ec2 revoke-security-group-ingress --group-id sg-001ddd6b6281ab83b --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-001ddd6b6281ab83b --protocol tcp --port 22 --cidr 102.91.92.67/32
```

These are records of the commands in the capture, not instructions to rerun them against the current account. The returned rule ARN identifies `ap-south-1`; the displayed commands rely on the configured region rather than passing `--region`.

The rerun at `2026-08-31T22:24:06Z` reports **SSH PASS**, with 3 PASS, 1 WARN, and 1 FAIL. S3 still fails the ACL-protection check and EBS is still WARN, so this proves a captured SSH finding changed to PASS, not that the whole audit became healthy.

**2. Why did you scope the new rule to your own IP address instead of leaving it open to `0.0.0.0/0`?**

The replacement is scoped to the single address `102.91.92.67/32`, reducing access from all IPv4 addresses to one permitted address. This is narrower than `0.0.0.0/0`; the capture does not independently prove address ownership or that this remains the operator's current IP.

**3. Did Claude execute the remediation command, or did you? Why does that matter?**

The evidence shows the remediation commands entered in a separate PowerShell terminal with successful AWS responses, followed by a Bash audit rerun. It supports the manual workflow described by the assignment. No successful Claude skill invocation is shown, and this limited capture is not a complete execution log proving the skill could never run a mutation.

**4. Which phase of the Agentic Loop does the Bash script represent? Which phase does Claude's explanation represent? Which phase is you running the fix?**

The Bash script represents the Gather and Analyze phases because it inspects the environment and classifies findings based on the real AWS state. Claude's explanation represents the Interpret and Recommend phases, where the findings are explained and prioritized. The human running the fix represents the Act phase, where the approved change is executed and then reverified.

---

# LinkedIn Post (Required)

## Goal

Create a LinkedIn post including:

- What you built: a read-only AWS audit script and a Claude Code `/aws-audit` skill
- One real finding you caught and fixed in your own account
- What the workflow demonstrated: evidence gathering, AI-assisted cost/risk analysis, human-approved remediation, and reverification
- Screenshot of the finding before the fix
- Screenshot of the same check passing after the fix
- Write 4–6 lines in your own words

Suggested tags:

`#DMIByPravinMishra #AWS #AgenticAI #ClaudeCode #DevOps`

### Evidence

#### LinkedIn Post URL

[Submitted LinkedIn audit post](https://www.linkedin.com/posts/eze-favour-52732752_aws-devops-devsecops-activity-7500322844539551744-hmmz)

The public LinkedIn page was verified on 13 September 2026 and matches the published-post screenshot below. It describes the S3 and EBS findings and the intended human-remediation workflow. Publication and the submitted URL are confirmed. The post text does not identify the specific SSH rule that was fixed, and its required attached before/after evidence was not verified. Those content requirements remain open; distinguish the SSH fix from the still-open S3/EBS findings.

---

#### Screenshot of Published LinkedIn Post

![Screenshot 14](image-2.png)

---

# Submission Instructions

Complete all tasks in sequence.

Your submission must include:

- All 13 required task screenshots
- Answers to every **Notes You Must Write** question
- `CLAUDE.md`
- `scripts/aws-audit.sh`
- `.claude/skills/aws-audit/SKILL.md`
- `reports/aws-audit-report.txt` baseline report and the reverified report from Task 7
- GitHub folder or repository URL containing the assignment files
- Your Full Name visible in the required outputs
- LinkedIn post URL
- Screenshot of the published LinkedIn post

Submit only a Google Doc link.

Add the GitHub URL inside the Google Doc.

Follow the Assignment Submission Guidelines.

---

# Completion Checklist

Checked items below reflect specific historical evidence only. Missing source artifacts, scope reconciliation, and successful skill output still prevent a complete submission.

- [x] Task 1: Inventory and workspace captured (Screenshots 1–2); later regional scope differs
- [x] Task 2: Audit `CLAUDE.md` creation shown (Screenshot 3); source file still required
- [ ] Task 3: Claude produced a read-only five-check audit plan before any script existed (Screenshot 4)
- [ ] Task 4: `aws-audit.sh` built, executable, and passes `bash -n` (Screenshots 5–7)
- [ ] Task 5: Baseline audit captured and saved with Full Name visible (Screenshots 8–9)
- [ ] Task 6: `/aws-audit` skill loads and runs successfully with no Write permission (Screenshots 10–11)
- [x] Task 7: Manual SSH restriction and subsequent SSH PASS shown (Screenshots 12–13); overall audit remains FAIL
- [ ] Skill never executed a remediation command
- [x] New security group rule is scoped to one `/32` address rather than `0.0.0.0/0`; ownership/current IP not independently verified
- [ ] All 13 required task screenshots are included
- [ ] All "Notes You Must Write" questions are answered in your own words
- [ ] No AWS credentials or unblurred account IDs exposed
- [x] LinkedIn post published and URL submitted; public page and matching text verified
- [ ] LinkedIn post identifies the SSH finding fixed and includes verified before/after proof
- [ ] GitHub URL included in the Google Doc
- [ ] Google Doc is accessible
- [ ] Link tested in incognito mode

The existing remediation captures contain account IDs/ARNs. Source screenshots were not changed in this audit; prepare redacted copies before checking the credentials/account-ID item. No Google Doc URL or access verification was provided.

---

# Final Submission

Submit only your Google Doc link.

### Question

Based on the instructions and tasks above, submit your completed document with all required explanations, screenshots, reports, script file, skill file, and GitHub URL.

`Add your Google Doc link here`

---

## 📌 About DMI & CloudAdvisory

DevOps Micro Internship (DMI) is a project-based DevOps program run by Pravin Mishra (The CloudAdvisory) focused on real-world execution, systems thinking, and career readiness.

It helps learners build strong DevOps foundations with hands-on experience.

---

## 📌 Resources

- 🌐 DMI Official Website: https://dmi.pravinmishra.com?utm_source=github&utm_medium=readme  
- 🎓 University: https://university.pravinmishra.com?utm_source=github&utm_medium=readme  
- 💬 Discord Community: https://discord.pravinmishra.com?utm_source=github&utm_medium=readme  
- 📝 Blog: https://dmi.pravinmishra.com/blog?utm_source=github&utm_medium=readme  
- ▶️ YouTube Playlist: https://www.youtube.com/playlist?list=PLFeSNDtI4Cho  
- 🔗 Pravin Mishra (LinkedIn): https://www.linkedin.com/in/pravin-mishra-aws-trainer/  
- 🏢 CloudAdvisory (LinkedIn): https://www.linkedin.com/company/thecloudadvisory/

---

*This submission is part of DevOps Micro Internship (DMI) Cohort 3 — Agentic AI Track.*
