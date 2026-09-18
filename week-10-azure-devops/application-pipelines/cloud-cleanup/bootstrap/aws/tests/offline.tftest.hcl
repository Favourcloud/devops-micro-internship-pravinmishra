# Synthetic schema/plan fixtures, not IAM evaluation or a token exchange.
mock_provider "aws" {
  override_during = plan
  mock_data "aws_caller_identity" {
    defaults = { account_id = "000000000001", arn = "arn:aws:sts::000000000001:assumed-role/fixture-bootstrap/test" }
  }
  mock_resource "aws_iam_openid_connect_provider" {
    defaults = { arn = "arn:aws:iam::000000000001:oidc-provider/login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0" }
  }
}
variables {
  lease_id                         = "abcdef123456"
  account_id                       = "000000000001"
  bootstrap_operator_arn           = "arn:aws:sts::000000000001:assumed-role/fixture-bootstrap/test"
  live_execution_approved          = true
  runtime_permissions_boundary_arn = "arn:aws:iam::000000000001:policy/dmi-w10-cleanup-boundary-abcdef123456"
  federation = {
    issuer            = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
    subject           = "fixture/exact-service-connection"
    metadata_verified = true
  }
  approval = { approved_at = timeadd(timestamp(), "-5m"), expires_at = timeadd(timestamp(), "4h"), estimated_total_usd = 1, planning_allowance_usd = 10 }
}
run "exact_trust" {
  command = plan
  assert {
    condition     = jsondecode(aws_iam_role.cleanup.assume_role_policy).Statement[0].Condition.StringEquals["login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0:sub"] == "fixture/exact-service-connection" && aws_iam_role.cleanup.max_session_duration == 3600
    error_message = "Trust only the exact issuer/subject and use short-lived sessions."
  }
}
run "authorized_party_mapping" {
  command = plan
  variables {
    federation = {
      issuer            = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
      subject           = "fixture/exact-service-connection"
      authorized_party  = "00000000-0000-0000-0000-000000000003"
      metadata_verified = true
    }
  }
  assert {
    condition     = local.conditions["${local.issuer_key}:aud"] == "00000000-0000-0000-0000-000000000003" && local.conditions["${local.issuer_key}:oaud"] == "api://AzureADTokenExchange" && length(local.audiences) == 2
    error_message = "When azp exists, bind both AWS's mapped audience and original audience."
  }
}
run "canary_delete_not_workload_permissions" {
  command = plan
  assert {
    condition     = jsondecode(aws_iam_role_policy.canary.policy).Statement[3].Action == "ec2:DeleteVpc" && jsondecode(aws_iam_role_policy.canary.policy).Statement[3].Condition.StringEquals["ec2:ResourceTag/cleanup_lease"] == "abcdef123456" && jsondecode(aws_iam_role_policy.canary.policy).Statement[1].Condition.StringNotEquals["aws:RequestedRegion"] == "eu-west-2"
    error_message = "Do not grant create, instance, IAM, cross-region or other-lease deletion rights."
  }
}
run "mandatory_runtime_boundary" {
  command = plan
  assert {
    condition     = aws_iam_role.cleanup.permissions_boundary == var.runtime_permissions_boundary_arn
    error_message = "A delegated bootstrap must not create an unbounded runtime role."
  }
}
run "no_arbitrary_boundary" {
  command = plan
  variables { runtime_permissions_boundary_arn = "arn:aws:iam::000000000001:policy/AdministratorAccess" }
  expect_failures = [var.runtime_permissions_boundary_arn]
}
run "no_approval" {
  command = plan
  variables { live_execution_approved = false }
  expect_failures = [terraform_data.authorization]
}
run "wrong_identity" {
  command = plan
  variables { bootstrap_operator_arn = "arn:aws:sts::000000000001:assumed-role/other/test" }
  expect_failures = [terraform_data.authorization]
}
run "no_root_bootstrap" {
  command = plan
  variables { bootstrap_operator_arn = "arn:aws:iam::000000000001:root" }
  expect_failures = [var.bootstrap_operator_arn]
}
run "no_sts_broker_bootstrap" {
  command = plan
  variables { bootstrap_operator_arn = "arn:aws:sts::000000000001:federated-user/fixture" }
  expect_failures = [var.bootstrap_operator_arn]
}
run "no_lookalike_issuer_host" {
  command = plan
  variables {
    federation = {
      issuer            = "https://login-microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
      subject           = "fixture/exact-service-connection"
      metadata_verified = true
    }
  }
  expect_failures = [var.federation]
}
run "no_lookalike_issuer_version" {
  command = plan
  variables {
    federation = {
      issuer            = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2x0"
      subject           = "fixture/exact-service-connection"
      metadata_verified = true
    }
  }
  expect_failures = [var.federation]
}
run "no_unverified_claims" {
  command = plan
  variables {
    federation = {
      issuer            = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
      subject           = "fixture/exact-service-connection"
      metadata_verified = false
    }
  }
  expect_failures = [var.federation]
}
