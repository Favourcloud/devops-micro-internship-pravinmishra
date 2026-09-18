terraform {
  required_version = "~> 1.13.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.64.0"
    }
  }
  backend "local" {
    path = ".private/terraform.tfstate"
  }
}
provider "aws" {
  region              = "eu-west-2"
  allowed_account_ids = [var.account_id]
}
data "aws_caller_identity" "current" {}

locals {
  administration_window = var.root_bootstrap_approval != null ? var.root_bootstrap_approval : (
    var.administration_approval != null ? var.administration_approval : {
      approved_at = var.approval.approved_at
      expires_at  = var.approval.expires_at
    }
  )
  user_name    = "dmi-week10-operator"
  user_arn     = "arn:aws:iam::${var.account_id}:user/${local.user_name}"
  role_arn     = "arn:aws:iam::${var.account_id}:role/dmi-w10-cleanup-${var.lease_id}"
  boundary_arn = "arn:aws:iam::${var.account_id}:policy/dmi-w10-cleanup-boundary-${var.lease_id}"
  issuer_arn   = "arn:aws:iam::${var.account_id}:oidc-provider/${trimprefix(var.oidc_issuer, "https://")}"
  tags         = { assignment = "week10-cleanup-canary", cleanup_lease = var.lease_id, identity_lifecycle = "persistent" }
  operator_policy = templatefile("${path.module}/operator-policy.json.tftpl", {
    account_id   = var.account_id
    lease_id     = var.lease_id
    user_arn     = local.user_arn
    role_arn     = local.role_arn
    boundary_arn = local.boundary_arn
    issuer_arn   = local.issuer_arn
    approved_at  = var.approval.approved_at
    expires_at   = var.approval.expires_at
  })
}
resource "terraform_data" "authorization" {
  input = var.lease_id
  lifecycle {
    precondition {
      condition = (
        var.live_execution_approved && var.persistent_identity_approved &&
        data.aws_caller_identity.current.account_id == var.account_id &&
        data.aws_caller_identity.current.arn == var.administrator_arn &&
        var.administrator_arn != local.user_arn &&
        timecmp(plantimestamp(), local.administration_window.approved_at) >= 0 &&
        timecmp(plantimestamp(), local.administration_window.expires_at) < 0
      )
      error_message = "The exact administrator needs persistent-identity approval and a current administration window; the operator cannot administer itself."
    }
    precondition {
      condition     = var.root_bootstrap_approval == null ? true : var.administrator_arn == "arn:aws:iam::${var.account_id}:root"
      error_message = "The root IAM-only exception is usable only by the exact account root, never another administrator."
    }
    precondition {
      condition     = timecmp(timestamp(), local.administration_window.expires_at) < 0
      error_message = "The administration approval must still be valid when applying the saved plan."
    }
    precondition {
      condition     = var.root_bootstrap_approval == null ? true : try(timecmp(timestamp(), var.root_bootstrap_approval.expires_at) < 0, false)
      error_message = "The separate root exception must still be valid when applying the saved plan."
    }
  }
}
resource "aws_iam_policy" "runtime_boundary" {
  name = "dmi-w10-cleanup-boundary-${var.lease_id}"
  policy = templatefile("${path.module}/runtime-boundary.json.tftpl", {
    account_id = var.account_id
    lease_id   = var.lease_id
  })
  tags       = local.tags
  depends_on = [terraform_data.authorization]
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_iam_policy" "operator" {
  name       = local.user_name
  policy     = local.operator_policy
  tags       = local.tags
  depends_on = [terraform_data.authorization]
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_iam_user" "operator" {
  name                 = local.user_name
  permissions_boundary = aws_iam_policy.operator.arn
  force_destroy        = false
  tags                 = local.tags
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_iam_user_policy_attachment" "operator" {
  count      = var.bootstrap_access_enabled ? 1 : 0
  user       = aws_iam_user.operator.name
  policy_arn = aws_iam_policy.operator.arn
  lifecycle {
    precondition {
      condition     = var.mfa_enrolled_and_verified
      error_message = "Enroll and independently verify the user's MFA before enabling any bootstrap or browser-login permissions."
    }
    precondition {
      condition     = timecmp(plantimestamp(), var.approval.approved_at) >= 0 && timecmp(plantimestamp(), var.approval.expires_at) < 0
      error_message = "Persistent identity or fresh administrator approval must not enable an expired or future privilege window."
    }
    precondition {
      condition     = timecmp(timestamp(), var.approval.expires_at) < 0
      error_message = "The original privilege window must still be valid when applying the policy attachment."
    }
  }
}
output "operator_arn" {
  value = aws_iam_user.operator.arn
}
output "runtime_permissions_boundary_arn" {
  value = aws_iam_policy.runtime_boundary.arn
}
output "bootstrap_access_enabled" {
  value = var.bootstrap_access_enabled
}
