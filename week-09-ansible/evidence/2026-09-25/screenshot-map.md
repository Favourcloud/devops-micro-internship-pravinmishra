# Numbered evidence map

This map preserves the full requested screenshot subjects. A linked image is supporting evidence, not an assertion that every element of the requested format is visible. `Recorded view` means a genuine browser capture of recorded output, not a live Terminal/VS Code window. `Historical` retains the original date, source and deployment phase. Page captures omit browser chrome. Missing exact captures remain explicit.

## Assignment 1

| Slot | Required subject | Evidence and scope |
|---|---|---|
| 1 | Terminal showing the `ansible-onboarding` path, `ls -la` output, and `git status` confirming the Git repository is on the `main` branch | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 2 | Terminal showing the active `(.venv)` environment, `which ansible`, `ansible --version`, `ansible-lint --version`, `yamllint --version`, and `pre-commit --version` | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 3 | VS Code Extensions panel showing the Ansible, YAML, and Python extensions installed | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 4 | VS Code showing `.vscode/settings.json` and `.editorconfig` open side by side, with the required settings clearly visible | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 5 | `ansible.cfg` open in VS Code or another editor, showing the complete configuration | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 6 | Terminal showing `ansible --version` with the `ansible.cfg` path and the output of `ansible-config dump --only-changed` | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 7 | Terminal showing `ssh-add -l` with the ED25519 key loaded and the SSH configuration verification output | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 8 | Terminal showing your Git full name, Git email, default branch, successful `pre-commit install` output, and `.git/hooks/pre-commit` | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 9 | Terminal showing `pre-commit run --all-files` completing successfully | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 10 | Terminal showing `ansible --version` with the project configuration path and `ssh-add -l` with the ED25519 key loaded | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 11 | Terminal showing the final `ansible-onboarding` project structure | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
| 12 | VS Code Markdown preview showing your full name, project summary, and part of the “New Machine? Do This” checklist | Exact screenshot unavailable. [Editable source and reports](../../ansible-onboarding/); [verified runtime evidence](README.md). |
## Assignment 2

| Slot | Required subject | Evidence and scope |
|---|---|---|
| 1 | Terminal showing the complete `ansible-adhoc-lab` project structure | [Historical capture; verify original scope](../../screenshots/assignment-02-01-project-structure.png) |
| 2 | Terminal showing `git status --short` with the new project files and updated `.gitignore` | Exact screenshot unavailable. [Editable source and reports](../../ansible-adhoc-lab/); [verified runtime evidence](README.md). |
| 3 | Terraform configuration showing the three or four server roles and the `for_each` or `count` implementation | [Historical capture; verify original scope](../../screenshots/assignment-02-03b-vm-for-each.png) |
| 4 | Terraform configuration showing SSH restricted to the controller IP and HTTP allowed only for web hosts | [Historical capture; verify original scope](../../screenshots/assignment-02-04a-inbound-rules.png) |
| 5 | Terraform output configuration showing how public IP addresses are associated with the server roles | [Historical capture; verify original scope](../../screenshots/assignment-02-05-role-outputs.png) |
| 6 | Final `terraform apply` output showing `Apply complete` | [Historical capture; verify original scope](../../screenshots/assignment-02-06-apply-complete.png) |
| 7 | `terraform output public_ips` showing the role-to-IP mapping for all three or four VMs | [Historical capture; verify original scope](../../screenshots/assignment-02-07-public-ips.png) |
| 8 | Azure Portal or AWS Management Console showing all three or four VMs in the `Running` state, with their role-based names visible | [Genuine browser page capture](a2-azure-four-running.png) |
| 9 | Terminal showing successful SSH hostname output from all VMs | [Historical capture; verify original scope](../../screenshots/assignment-02-09-ssh-hostnames-redacted.png) |
| 10 | `inventory.ini` showing the `web`, `app`, and `db` groups | [Historical capture; verify original scope](../../screenshots/assignment-02-10-generated-inventory.png) |
| 11 | Output of `ansible-inventory -i inventory.ini --graph` | [Historical capture; verify original scope](../../screenshots/assignment-02-11-inventory-graph.png) |
| 12 | Output of `ansible all -i inventory.ini -m ping` | [Recorded view; see linked full text/report](a2-ping.png) |
| 13 | Output of `ansible all -i inventory.ini -m command -a "uptime"` | [Recorded view; see linked full text/report](a2-uptime.png) |
| 14 | Output of `ansible web -i inventory.ini -m apt -a "name=nginx state=present update_cache=yes" --become` | [Recorded view; see linked full text/report](a2-nginx-install.png) |
| 15 | Output of `ansible web -i inventory.ini -m service -a "name=nginx state=started enabled=yes" --become` | [Recorded view; see linked full text/report](a2-nginx-service.png) |
| 16 | Output of `ansible all -i inventory.ini -m apt -a "name=htop state=present update_cache=yes" --become` | [Recorded view; see linked full text/report](a2-htop-install.png) |
| 17 | Output of `ansible web -i inventory.ini -m command -a "systemctl is-active nginx"` | [Recorded view; see linked full text/report](a2-nginx-active.png) |
| Post | Published LinkedIn post | [Genuine browser page capture](w09-linkedin-published.png) |
## Assignment 3

| Slot | Required subject | Evidence and scope |
|---|---|---|
| 1 | Terminal or VS Code showing the complete `static-web` project structure | [Historical capture; verify original scope](../../screenshots/assignment-03-01-project-structure.png) |
| 2 | Output of `ansible-inventory -i inventory.ini --graph` showing `web1` and `web2` | [Historical capture; verify original scope](../../screenshots/assignment-03-02-postcleanup-local-graph.png) |
| 3 | Ansible ping output showing `SUCCESS` and `pong` for both servers | [Recorded view; see linked full text/report](a2-ping.png) |
| 4 | Edited `files/index.html` showing the footer line with your full name | [Historical capture; verify original scope](../../screenshots/assignment-03-04-personalized-footer.png) |
| 5 | Successful syntax-check output showing `playbook: site.yml` | [Historical capture; verify original scope](../../screenshots/assignment-03-05-syntax-check.png) |
| 6 | Play 3 verification showing HTTP `200` for both servers | [Recorded view; see linked full text/report](a3-deploy.png) |
| 7 | Final play recap showing `unreachable=0` and `failed=0` for `web1`, `web2`, and `localhost` | [Recorded view; see linked full text/report](a3-deploy.png) |
| 8 | Second playbook run showing the play recap with `changed=0`, `unreachable=0`, and `failed=0` for both web servers | [Recorded view; see linked full text/report](a3-idempotence.png) |
| 9 | `curl -I` output showing HTTP `200 OK` from both servers | Exact screenshot unavailable. [Editable source and reports](../../static-web/); [verified runtime evidence](README.md). |
| 10 | Browser showing the website from Server 1 with the public IP and your full name visible | [Genuine browser page capture](a3-web1-home.png) |
| 11 | Browser showing the website from Server 2 with the public IP and your full name visible | [Genuine browser page capture](a3-web2-home.png) |
| Post | Published LinkedIn post | [Genuine browser page capture](w09-linkedin-published.png) |
## Assignment 4

| Slot | Required subject | Evidence and scope |
|---|---|---|
| 1 | Terminal or VS Code showing the complete `mini-finance` project structure | [Historical capture; verify original scope](../../screenshots/assignment-04/01-project-tree.png) |
| 2 | Terraform code showing the `Allow-SSH` rule for port `22` and the `Allow-HTTP` rule for port `80` | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 3 | Terraform code showing the association between `nsg-mini-finance` and `nic-mini-finance` | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 4 | End of the `terraform apply` output showing `Apply complete!` with no errors | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 5 | Output of `terraform output public_ip` showing the VM’s public IP address | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 6 | Passwordless SSH command and the returned `mini-finance` hostname | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 7 | Ansible ping output showing `SUCCESS` and `pong` from the Azure VM | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 8 | `site.yml` showing Play 1 and the beginning of Play 2 | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 9 | `site.yml` showing the deployment destination, handler, and Play 3 verification | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 10 | Successful playbook syntax check showing `playbook: site.yml` | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 11 | Play 3 output showing the successful HTTP verification and assertion | [Recorded view; see linked full text/report](a4-deploy-view.png) |
| 12 | Final `PLAY RECAP` showing `failed=0` and `unreachable=0` | [Recorded view; see linked full text/report](a4-deploy-view.png) |
| 13 | Mini Finance website successfully loading in the browser, with the Azure VM’s public IP address visible in the address bar | [Genuine browser page capture](a4-home.png) |
| 14 | Completed `README.md` displayed in the VS Code Markdown preview or terminal | Exact screenshot unavailable. [Editable source and reports](../../mini-finance/); [verified runtime evidence](README.md). |
| 15 | Published LinkedIn post showing the text and at least one deployment screenshot | [Genuine browser page capture](w09-linkedin-published.png) |
## Assignment 5

| Slot | Required subject | Evidence and scope |
|---|---|---|
| 1 | Terminal showing the completed `epicbook-prod` project structure | [Historical capture; verify original scope](../../epicbook-prod/evidence/images/screenshot-1a.png) |
| 2 | `terraform apply` completed successfully | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 3 | Output of `terraform output` | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 4 | Azure Portal or AWS Console showing the VM running | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 5 | Azure Portal or AWS Console showing the managed MySQL database created | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 6 | Successful SSH hostname check from the Ansible controller | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 7 | `inventory.ini` showing the VM under the `web` group | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 8 | Output of `ansible-inventory -i inventory.ini --graph` | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 9 | Output of `ansible web -i inventory.ini -m ping` | [Recorded view; see linked full text/report](a5-services.png) |
| 10 | `site.yml` showing the roles in the correct order | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 11 | Output of `ansible-playbook -i inventory.ini site.yml --syntax-check` | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 12 | `roles/common/tasks/main.yml` showing the common setup tasks | [Historical capture; verify original scope](../../epicbook-prod/evidence/images/screenshot-07.png) |
| 13 | `roles/nginx/tasks/main.yml` showing Nginx installation and site configuration tasks | [Historical capture; verify original scope](../../epicbook-prod/evidence/images/screenshot-8a.png) |
| 14 | `roles/nginx/templates/epicbook.conf.j2` showing the reverse proxy configuration | [Historical capture; verify original scope](../../epicbook-prod/evidence/images/screenshot-8c.png) |
| 15 | `roles/epicbook/tasks/main.yml` showing application deployment tasks | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 16 | Task or file showing how the database connection is configured, with secrets hidden | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 17 | Task or output showing the EpicBook application managed by PM2 | [Recorded view; see linked full text/report](a5-services.png) |
| 18 | `group_vars/web.yml` showing the application, PM2, and database variables, with passwords hidden or masked | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 19 | Ansible playbook output showing the roles running | [Recorded view; see linked full text/report](a5-deploy-managed-recap-view.png) |
| 20 | Final Ansible recap showing `failed=0` | [Recorded view; see linked full text/report](a5-deploy-managed-recap-view.png) |
| 21 | Output of `ansible web -i inventory.ini -m command -a "systemctl is-active nginx" --become` | [Recorded view; see linked full text/report](a5-services.png) |
| 22 | Output of `ansible web -i inventory.ini -m command -a "pm2 status"` | [Recorded view; see linked full text/report](a5-services.png) |
| 23 | Output of `ansible web -i inventory.ini -m command -a "curl -I http://localhost:8080"` | [Recorded view; see linked full text/report](a5-services.png) |
| 24 | Output of `curl -I http://<public_ip>` | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 25 | Output of the cart API test command | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 26 | Output of the `/cart` HTTP status check | Exact screenshot unavailable. [Editable source and reports](../../epicbook-prod/); [verified runtime evidence](README.md). |
| 27 | Browser showing the EpicBook application loaded from `http://<public_ip>` | [Genuine browser page capture](a5-managed-home.png) |
| Post | Published LinkedIn post | [Genuine browser page capture](w09-linkedin-published.png) |
## Assignment 6

| Slot | Required subject | Evidence and scope |
|---|---|---|
| 1 | Output of `ansible web -i inventory.ini -m ping` | [Recorded view; see linked full text/report](a5-services.png) |
| 2 | Output of `ansible-playbook -i inventory.ini site.yml --syntax-check` | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 3 | Output of `pwd` and `find . -maxdepth 4 -type d / sort` | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 4 | `CLAUDE.md` open in VS Code or terminal showing the safety rules | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 5 | Claude Code showing the four-category risk-classification plan | [Recorded view; see linked full text/report](a6-planning.png) |
| 6 | Top section of `ansible-check-review.sh` showing `full_name`, `playbook_path`, `inventory_path`, and the `checks` array | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 7 | Middle section showing `extract_changed_tasks` and `check_tasks_matching_pattern` | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 8 | Bottom section showing the loop, summary, and exit behavior | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 9 | Output of `bash -n ansible-check-review.sh` and `ls -l ansible-check-review.sh` | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 10 | Output of `./ansible-check-review.sh` | [Recorded view; see linked full text/report](a6-ansible-risk-report.png) |
| 11 | Output of `echo "Captured Exit Code: $script_exit_code"` and `cat reports/ansible-risk-report.txt` | [Recorded view; see linked full text/report](a6-ansible-risk-report.png) |
| 12 | `SKILL.md` showing the frontmatter, allowed tools, and safety rules | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 13 | Claude Code output after running `/ansible-risk-review` | [Recorded view; see linked full text/report](a6-ansible-risk-report.png) |
| 14 | The added risky task inside the role file | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 15 | Output of `./ansible-check-review.sh` | [Recorded view; see linked full text/report](a6-risky-change-report.png) |
| 16 | Claude Code `/ansible-risk-review` output showing the risky finding | [Recorded view; see linked full text/report](a6-risky-change-report.png) |
| 17 | Output of `cat reports/risky-change-report.txt` | [Recorded view; see linked full text/report](a6-risky-change-report.png) |
| 18 | Output of the real playbook run showing the final recap with `failed=0` | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 19 | Output of `ansible web -i inventory.ini -m ping` | [Recorded view; see linked full text/report](a5-services.png) |
| 20 | Second `/ansible-risk-review` output after applying the change | [Recorded view; see linked full text/report](a6-recovery-report.png) |
| 21 | Output of `ls -lah reports` | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| 22 | `change-summary.md` showing all required sections and your Full Name | Exact screenshot unavailable. [Editable source and reports](../../risk-review/); [verified runtime evidence](README.md). |
| Post | Published LinkedIn post | [Genuine browser page capture](w09-linkedin-published.png) |
