terraform {
  required_version = "= 1.13.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.64.0"
    }
  }
}

variable "expected_account_id" {
  description = "Private account binding, supplied locally after non-root identity verification."
  type        = string
  sensitive   = true
  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "A verified account binding is required."
  }
}

provider "aws" {
  region              = "ap-south-1"
  profile             = "dmi-week8"
  allowed_account_ids = [var.expected_account_id]
  default_tags {
    tags = {
      DmiLab = "dmi-week8-a6-favour-20260915"
      Owner  = "Eze Favour"
    }
  }
}

# Isolated support network. No subnets, gateways, endpoints, instances or IPs.
resource "aws_vpc" "lab" {
  cidr_block           = "10.248.0.0/24"
  enable_dns_support   = false
  enable_dns_hostnames = false
  tags = {
    Name = "dmi-week8-a6-isolated-vpc"
  }
}

output "vpc_id" {
  value     = aws_vpc.lab.id
  sensitive = true
}
