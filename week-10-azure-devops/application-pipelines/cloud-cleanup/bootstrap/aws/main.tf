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
  issuer_key = trimprefix(var.federation.issuer, "https://")
  # AWS maps :aud to azp when present, and :oaud to the original aud claim.
  audiences = distinct(compact(["api://AzureADTokenExchange", var.federation.authorized_party]))
  conditions = merge({
    "${local.issuer_key}:sub" = var.federation.subject
    "${local.issuer_key}:aud" = coalesce(var.federation.authorized_party, "api://AzureADTokenExchange")
    }, var.federation.authorized_party == null ? {} : {
    "${local.issuer_key}:oaud" = "api://AzureADTokenExchange"
  })
}

resource "terraform_data" "authorization" {
  input = var.lease_id
  lifecycle {
    precondition {
      condition = (
        var.live_execution_approved &&
        timecmp(plantimestamp(), var.approval.approved_at) >= 0 &&
        timecmp(plantimestamp(), var.approval.expires_at) < 0 &&
        data.aws_caller_identity.current.account_id == var.account_id &&
        data.aws_caller_identity.current.arn == var.bootstrap_operator_arn &&
        !endswith(data.aws_caller_identity.current.arn, ":root")
      )
      error_message = "Use an explicitly authorized non-root IAM bootstrap identity; the existing STS-only broker cannot administer IAM."
    }
    precondition {
      condition     = timecmp(timestamp(), var.approval.expires_at) < 0
      error_message = "The control-plane approval must still be valid at apply time."
    }
  }
}

resource "aws_iam_openid_connect_provider" "cleanup" {
  url            = var.federation.issuer
  client_id_list = local.audiences
  tags           = { assignment = "week10-cleanup-canary", cleanup_lease = var.lease_id }
  depends_on     = [terraform_data.authorization]
}

resource "aws_iam_role" "cleanup" {
  name                 = "dmi-w10-cleanup-${var.lease_id}"
  max_session_duration = 3600
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRoleWithWebIdentity"
      Principal = { Federated = aws_iam_openid_connect_provider.cleanup.arn }
      Condition = { StringEquals = local.conditions }
    }]
  })
  tags = { assignment = "week10-cleanup-canary", cleanup_lease = var.lease_id }
}

resource "aws_iam_role_policy" "canary" {
  name = "delete-only-canary-vpc"
  role = aws_iam_role.cleanup.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "NoOtherAPIs"
        Effect    = "Deny"
        NotAction = ["ec2:Describe*", "ec2:DeleteVpc", "sts:GetCallerIdentity"]
        Resource  = "*"
      },
      {
        Sid       = "RegionFence"
        Effect    = "Deny"
        Action    = "ec2:*"
        Resource  = "*"
        Condition = { StringNotEquals = { "aws:RequestedRegion" = "eu-west-2" } }
      },
      {
        Sid      = "RegionalMetadataReads"
        Effect   = "Allow"
        Action   = "ec2:Describe*"
        Resource = "*"
      },
      {
        Sid      = "OnlyThisCanary"
        Effect   = "Allow"
        Action   = "ec2:DeleteVpc"
        Resource = "arn:aws:ec2:eu-west-2:${var.account_id}:vpc/*"
        Condition = { StringEquals = {
          "ec2:ResourceTag/assignment"    = "week10-cleanup-canary"
          "ec2:ResourceTag/cleanup_lease" = var.lease_id
        } }
      },
      {
        Effect   = "Allow"
        Action   = "sts:GetCallerIdentity"
        Resource = "*"
      }
    ]
  })
}
output "cleanup_role_arn" {
  value = aws_iam_role.cleanup.arn
}
