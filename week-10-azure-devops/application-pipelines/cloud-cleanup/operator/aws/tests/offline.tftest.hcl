# Synthetic plans only; not IAM authorization or MFA/browser-login evidence.
mock_provider "aws" {
  override_during = plan
  mock_data "aws_caller_identity" {
    defaults = { account_id = "000000000001", arn = "arn:aws:sts::000000000001:assumed-role/fixture-administrator/test" }
  }
  mock_resource "aws_iam_policy" {
    defaults = { arn = "arn:aws:iam::000000000001:policy/fixture" }
  }
}
variables {
  lease_id                = "abcdef123456"
  account_id              = "000000000001"
  administrator_arn       = "arn:aws:sts::000000000001:assumed-role/fixture-administrator/test"
  oidc_issuer             = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
  live_execution_approved = true
  approval                = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "4h"), estimated_total_usd = 1, planning_allowance_usd = 10 }
}
run "inert_until_mfa_verification" {
  command = plan
  assert {
    condition     = length(aws_iam_user_policy_attachment.operator) == 0 && !aws_iam_user.operator.force_destroy && aws_iam_user.operator.permissions_boundary == aws_iam_policy.operator.arn
    error_message = "The user must have a boundary, no attached permissions by default, and no force-destroy credential cleanup."
  }
}
run "enable_after_mfa_attestation" {
  command = plan
  variables {
    bootstrap_access_enabled  = true
    mfa_enrolled_and_verified = true
  }
  assert {
    condition     = length(aws_iam_user_policy_attachment.operator) == 1 && aws_iam_user_policy_attachment.operator[0].policy_arn == aws_iam_policy.operator.arn
    error_message = "Only the same bounded policy may be attached after MFA verification."
  }
}
run "no_unverified_mfa" {
  command = plan
  variables { bootstrap_access_enabled = true }
  expect_failures = [aws_iam_user_policy_attachment.operator[0]]
}
run "fixed_boundary_and_deadline" {
  command = plan
  assert {
    condition = (
      jsondecode(local.operator_policy).Statement[8].Condition.StringEquals["iam:PermissionsBoundary"] == "arn:aws:iam::000000000001:policy/dmi-w10-cleanup-boundary-abcdef123456" &&
      jsondecode(local.operator_policy).Statement[1].Condition.DateGreaterThanEquals["aws:CurrentTime"] == var.approval.expires_at &&
      jsondecode(local.operator_policy).Statement[2].Condition.BoolIfExists["aws:MultiFactorAuthPresent"] == "false"
    )
    error_message = "Require the exact immutable boundary, original expiry and MFA request context."
  }
}
run "runtime_remains_canary_only" {
  command = plan
  assert {
    condition = (
      toset(jsondecode(aws_iam_policy.runtime_boundary.policy).Statement[0].NotAction) == toset(["ec2:Describe*", "ec2:DeleteVpc", "sts:GetCallerIdentity"]) &&
      jsondecode(aws_iam_policy.runtime_boundary.policy).Statement[3].Condition.StringEquals["ec2:ResourceTag/cleanup_lease"] == var.lease_id
    )
    error_message = "The boundary must not allow IAM escalation, VMs or another lease."
  }
}
run "no_execution_approval" {
  command = plan
  variables { live_execution_approved = false }
  expect_failures = [terraform_data.authorization]
}
run "no_root_administrator" {
  command = plan
  variables { administrator_arn = "arn:aws:iam::000000000001:root" }
  expect_failures = [var.administrator_arn]
}
run "explicit_root_identity_only" {
  command = plan
  variables {
    administrator_arn = "arn:aws:iam::000000000001:root"
    root_bootstrap_approval = {
      approved_at = timeadd(timestamp(), "-1m")
      expires_at  = timeadd(timestamp(), "30m")
    }
    approval = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "4h"), estimated_total_usd = 0, planning_allowance_usd = 10 }
  }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "000000000001", arn = "arn:aws:iam::000000000001:root" }
  }
  assert {
    condition     = length(aws_iam_user_policy_attachment.operator) == 0 && aws_iam_user.operator.permissions_boundary == aws_iam_policy.operator.arn
    error_message = "Explicit root bootstrap still creates only a bounded, inactive identity."
  }
}
run "root_cannot_skip_mfa" {
  command = plan
  variables {
    administrator_arn        = "arn:aws:iam::000000000001:root"
    bootstrap_access_enabled = true
    root_bootstrap_approval  = { approved_at = timeadd(timestamp(), "-1m"), expires_at = timeadd(timestamp(), "30m") }
  }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "000000000001", arn = "arn:aws:iam::000000000001:root" }
  }
  expect_failures = [aws_iam_user_policy_attachment.operator[0]]
}
run "no_root_exception_for_nonroot_caller" {
  command = plan
  variables {
    root_bootstrap_approval = { approved_at = timeadd(timestamp(), "-1m"), expires_at = timeadd(timestamp(), "30m") }
  }
  expect_failures = [terraform_data.authorization]
}
run "no_long_root_exception" {
  command = plan
  variables {
    root_bootstrap_approval = { approved_at = timeadd(timestamp(), "-1m"), expires_at = timeadd(timestamp(), "1h") }
  }
  expect_failures = [var.root_bootstrap_approval]
}
run "no_expired_root_exception" {
  command = plan
  variables {
    administrator_arn       = "arn:aws:iam::000000000001:root"
    root_bootstrap_approval = { approved_at = "2000-01-01T00:00:00Z", expires_at = "2000-01-01T01:00:00Z" }
  }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "000000000001", arn = "arn:aws:iam::000000000001:root" }
  }
  expect_failures = [terraform_data.authorization]
}
run "no_future_root_exception" {
  command = plan
  variables {
    administrator_arn       = "arn:aws:iam::000000000001:root"
    root_bootstrap_approval = { approved_at = timeadd(timestamp(), "1m"), expires_at = timeadd(timestamp(), "30m") }
  }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "000000000001", arn = "arn:aws:iam::000000000001:root" }
  }
  expect_failures = [terraform_data.authorization]
}
run "root_exception_cannot_extend_identity_window" {
  command = plan
  variables {
    administrator_arn       = "arn:aws:iam::000000000001:root"
    root_bootstrap_approval = { approved_at = timeadd(timestamp(), "-1m"), expires_at = timeadd(timestamp(), "30m") }
    approval                = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "10m"), estimated_total_usd = 0, planning_allowance_usd = 10 }
  }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "000000000001", arn = "arn:aws:iam::000000000001:root" }
  }
  expect_failures = [terraform_data.authorization]
}
run "no_negative_estimate" {
  command = plan
  variables {
    approval = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "4h"), estimated_total_usd = -1, planning_allowance_usd = 10 }
  }
  expect_failures = [var.approval]
}
run "no_zero_allowance" {
  command = plan
  variables {
    approval = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "4h"), estimated_total_usd = 0, planning_allowance_usd = 0 }
  }
  expect_failures = [var.approval]
}
run "no_federation_broker" {
  command = plan
  variables { administrator_arn = "arn:aws:sts::000000000001:federated-user/fixture" }
  expect_failures = [var.administrator_arn]
}
run "no_wrong_account" {
  command = plan
  variables { account_id = "000000000009" }
  expect_failures = [terraform_data.authorization]
}
run "no_self_administration" {
  command = plan
  variables { administrator_arn = "arn:aws:iam::000000000001:user/dmi-w10-bootstrap-abcdef123456" }
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "000000000001", arn = "arn:aws:iam::000000000001:user/dmi-w10-bootstrap-abcdef123456" }
  }
  expect_failures = [terraform_data.authorization]
}
run "no_expired_approval" {
  command = plan
  variables {
    approval = { approved_at = "2000-01-01T00:00:00Z", expires_at = "2000-01-01T04:00:00Z", estimated_total_usd = 1, planning_allowance_usd = 10 }
  }
  expect_failures = [terraform_data.authorization]
}
run "no_long_window" {
  command = plan
  variables {
    approval = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "25h"), estimated_total_usd = 1, planning_allowance_usd = 10 }
  }
  expect_failures = [var.approval]
}
run "no_wildcard_issuer" {
  command = plan
  variables { oidc_issuer = "https://login.microsoftonline.com/*/v2.0" }
  expect_failures = [var.oidc_issuer]
}
run "no_lookalike_issuer_host" {
  command = plan
  variables { oidc_issuer = "https://login-microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0" }
  expect_failures = [var.oidc_issuer]
}
run "no_lookalike_issuer_version" {
  command = plan
  variables { oidc_issuer = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2x0" }
  expect_failures = [var.oidc_issuer]
}
