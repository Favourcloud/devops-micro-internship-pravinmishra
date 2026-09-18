terraform {
  required_version = "~> 1.13.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.64.0"
    }
  }
  backend "azurerm" {}
}
provider "aws" {
  region              = "eu-west-2"
  allowed_account_ids = [var.account_id]
}
data "aws_caller_identity" "current" {}
resource "terraform_data" "authorization" {
  input = var.lease_id
  lifecycle {
    precondition {
      condition = (
        var.live_execution_approved &&
        data.aws_caller_identity.current.account_id == var.account_id &&
        data.aws_caller_identity.current.arn == var.operator_arn &&
        !endswith(data.aws_caller_identity.current.arn, ":root") &&
        timecmp(plantimestamp(), var.expires_at) < 0 &&
        timecmp(var.expires_at, timeadd(plantimestamp(), "24h")) <= 0
      )
      error_message = "Creating the empty canary VPC requires fresh approval, exact non-root identity and maximum 24-hour expiry."
    }
    precondition {
      condition     = timecmp(timestamp(), var.expires_at) < 0
      error_message = "Canary creation approval must still be valid at apply time."
    }
  }
}
resource "aws_vpc" "canary" {
  cidr_block = "10.199.0.0/24"
  tags = {
    Name          = "dmi-w10-cleanup-${var.lease_id}-canary"
    assignment    = "week10-cleanup-canary"
    cleanup_lease = var.lease_id
    expires_at    = var.expires_at
    managed_by    = "terraform"
  }
  depends_on = [terraform_data.authorization]
}
