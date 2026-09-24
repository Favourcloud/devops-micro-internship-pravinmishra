# Private Bedrock setup — 25 September 2026

Claude Code 2.1.220 produced a real response using **Amazon Bedrock, `us.anthropic.claude-sonnet-4-6`, in us-east-1**. Its response metadata identified the provider as `bedrock`. The separate, isolated Claude configuration does not use the existing local Kimi bridge.

The operator was Codex under user delegation. This report records setup verification, not completed capstone implementation or manual learner execution. The paid starter kit, account identifiers, credentials, machine paths, and full private transcripts are not published.

## Verified

- Official AWS CLI 2.37.2 installed separately from the existing Homebrew CLI. Temporary console-login credentials passed the assignment account check.
- The Anthropic first-use warning disappeared after the user completed the form. The exact submitted fields were not independently re-read. The approved usage-based model agreement was activated; agreement, entitlement and regional availability were `AVAILABLE`, and authorization was `AUTHORIZED`.
- The private integration retained the restricted source tools, fixed offline validation runner and reviewed trust records. Fourteen guard tests and 27 offline-runner tests passed with network access denied. No real Terraform validation was rerun in this setup session.
- Claude's interactive `/mcp` screen showed **Terraform connected, seven tools**. This connection check used disabled AWS credential files and made no model request. The Docker image remains pinned to `hashicorp/terraform-mcp-server@sha256:423a6b8e2ee06affcf090892f40c86469caba45fd2448ffa8ca5d717a174f7d5`, without host mounts, published ports or forwarded AWS credentials.
- Actual Claude `Read` and `Bash` attempts outside the permitted workflow were denied by the pre-tool guard. The post-edit validation hook was not exercised.

## Problems found and corrected

The first paid test requested one public Terraform Registry lookup. Claude returned a response, but did **not** perform that lookup: the MCP server was pending, and the project notes still described inactive configuration. Private notes now distinguish the active integration from the frozen public source baseline. Tool preloading and startup timeouts are configured, and the isolated workspace trust step was completed.

A launcher defect allowed shell-heredoc source on inherited standard input to become model input. An interactive setup attempt also received that source and was stopped; the guard denied its attempted memory-file read and shell command. The print launcher now supplies `stdin=DEVNULL`, so only the explicit prompt is sent. A regression check with a real local child confirmed empty standard input while replacing AWS/model calls. Interactive configuration now runs from a file, with AWS credential files disabled.

The private guard also recognizes the current CLI's `manual` permission-mode name. A regression check retains credential-read and arbitrary-command denials in that mode. Existing public hooks, source and screenshot anchors were not changed.

## Cost and remaining work

Observed model usage estimates **$0.4364** using the AWS offer's regional rates. A conservative calculation using the configured 512-token output cap for the interrupted response is **$0.4449**, before final billing/taxes. The user approved a $0.50 test limit; further paid calls were stopped. These are usage estimates, not a reconciled AWS invoice or an account-level billing cap.

Still unverified: the intended model-selected MCP lookup, the two configured agent workflows, post-edit validation, and the required screenshots. No Terraform or application deployment occurred. A5 remains **9/28 screenshot slots** and Week 08 remains **98/118**; this report adds no screenshot credit or new DMI grade. Runtime/dependency remediation, deployment inputs and cost approval, learner reflections, publication and remaining evidence are still required.

The [starter-kit review](starter-kit-review-20260924.md) describes the earlier receipt-only stage. Original course files remain private.
