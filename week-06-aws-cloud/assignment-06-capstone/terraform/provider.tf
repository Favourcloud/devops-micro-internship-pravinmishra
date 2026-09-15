terraform {
  required_version = ">= 1.13, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.64.0"
    }
  }
}

provider "aws" {
  region              = "eu-north-1"
  allowed_account_ids = [var.expected_account_id]
  default_tags {
    tags = {
      Project    = "dmi-a6-additions"
      Assignment = "week06-a6"
      ManagedBy  = "Terraform"
      Lifecycle  = "temporary-lab"
    }
  }
}
