# Private Bedrock setup — 25 September 2026

Claude Code 2.1.220 used **Amazon Bedrock, `us.anthropic.claude-sonnet-4-6`, in us-east-1** to complete a public Terraform MCP lookup and invoke the fixed offline Terraform validation runner. The lookup returned AWS provider **6.66.0**; the workspace remains pinned to **6.64.0**. All six validation stages passed. The [sanitized workflow record](bedrock-workflow-20260925.json) includes actual tool results, usage estimates and private transcript hashes. The separate, isolated Claude configuration does not use the existing local Kimi bridge.

The operator was Codex under user delegation. This report records setup verification, not completed capstone implementation or manual learner execution. The paid starter kit, account identifiers, credentials, machine paths, and full private transcripts are not published.

## Verified

- Official AWS CLI 2.37.2 installed separately from the existing Homebrew CLI. Temporary console-login credentials passed the assignment account check.
- The Anthropic first-use warning disappeared after the user completed the form. The exact submitted fields were not independently re-read. The approved usage-based model agreement was activated; agreement, entitlement and regional availability were `AVAILABLE`, and authorization was `AUTHORIZED`.
- The private integration retained the restricted source tools, fixed offline validation runner and reviewed trust records. Seventeen guard tests and 27 offline-runner contract tests passed with network access denied. A separate operator preflight ran real Terraform with IP networking denied and passed all six stages.
- Claude then selected `mcp__terraform__get_latest_provider_version` with namespace `hashicorp` and name `aws`, and invoked the exact approved Bash command. Actual tool results confirm `version`, `fmt`, `init`, `validate`, `provider-schema` and `mock-plan-tests` passed. Terraform used isolated empty credential files, a locked local provider mirror and explicit mocked plan tests. The parent model session had network access for Bedrock and the public registry; no infrastructure was deployed.
- Claude's interactive `/mcp` screen showed **Terraform connected, seven tools**. This connection check used disabled AWS credential files and made no model request. The Docker image remains pinned to `hashicorp/terraform-mcp-server@sha256:423a6b8e2ee06affcf090892f40c86469caba45fd2448ffa8ca5d717a174f7d5`, without host mounts, published ports or forwarded AWS credentials.
- Actual Claude `Read` and `Bash` attempts outside the permitted workflow were denied by the pre-tool guard. The post-edit validation hook was not exercised.

## Problems found and corrected

The first paid test requested one public Terraform Registry lookup. Claude returned a response, but did **not** perform that lookup: the MCP server was pending, and the project notes still described inactive configuration. Private notes now distinguish the active integration from the frozen public source baseline. Tool preloading and startup timeouts are configured, and the isolated workspace trust step was completed.

A launcher defect allowed shell-heredoc source on inherited standard input to become model input. An interactive setup attempt also received that source and was stopped; the guard denied its attempted memory-file read and shell command. The print launcher now supplies `stdin=DEVNULL`, so only the explicit prompt is sent. A regression check with a real local child confirmed empty standard input while replacing AWS/model calls. Interactive configuration now runs from a file, with AWS credential files disabled.

The private guard also recognizes the current CLI's `manual` permission-mode name. The first additionally authorized workflow attempt connected to MCP but both requested tools were denied. Trusted-file hashes were intact. Inspection of the installed CLI's hook schema identified new `prompt_id` and `effort.level` metadata missing from the guard's strict allowlist, plus `duration_ms` on post-tool events. The guard now validates those specific fields; unknown fields, malformed metadata, credential reads, arbitrary commands and protected-file edits remain denied. Regression tests passed, and the subsequent Bedrock retry completed both approved tools without permission denials. Existing public hooks, source and screenshot anchors were not changed.

## Cost and remaining work

The initial setup used an estimated **$0.4364**, with a conservative interrupted-response estimate of **$0.4449**, against the original $0.50 approval. The user then explicitly approved **another $0.50** for the MCP lookup and guarded validation. The denied attempt used an estimated **$0.09641412** and the successful retry **$0.043767075**, totaling **$0.140181195** of that additional budget, leaving approximately **$0.36**. No further paid calls were made after the bounded test. These use the AWS offer's regional token rates before final billing/taxes; they are not a reconciled invoice or an account-level billing cap.

Still unverified: the two configured agent workflows, post-edit validation, and the required screenshots. Passing the pre-tool guard and running the validation command does not demonstrate the post-edit hook. No Terraform or application deployment occurred. A5 remains **9/28 screenshot slots** and Week 08 remains **98/118**; this report adds no screenshot credit or new DMI grade. Runtime/dependency remediation, deployment inputs and cost approval, learner reflections, publication and remaining evidence are still required.

The [starter-kit review](starter-kit-review-20260924.md) describes the earlier receipt-only stage. Original course files remain private.
