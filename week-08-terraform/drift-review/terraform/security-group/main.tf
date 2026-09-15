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

variable "vpc_id" {
  description = "ID of only the new lab VPC, supplied locally after its reviewed creation."
  type        = string
  sensitive   = true
  validation {
    condition     = can(regex("^vpc-[0-9a-f]+$", var.vpc_id))
    error_message = "The dedicated lab VPC ID is required."
  }
}

variable "test_public_ssh" {
  description = "PLAN-ONLY configuration-change demonstration. Never apply when true."
  type        = bool
  default     = false
}

# This group is never attached to an instance, ENI or any workload.
resource "aws_security_group" "review" {
  name        = "dmi-week8-a6-review-20260915"
  description = "Isolated unattached ingress-policy review lab"
  vpc_id      = var.vpc_id
  egress      = []
  ingress = var.test_public_ssh ? [{
    description      = "UNAPPLIED policy detection exercise"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }] : []
  tags = {
    Name = "dmi-week8-a6-unattached-review"
  }
}
