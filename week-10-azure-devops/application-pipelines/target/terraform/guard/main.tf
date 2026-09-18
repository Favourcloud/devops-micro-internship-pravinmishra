terraform {
  required_version = "~> 1.13.5"
}

variable "assignment" {
  type     = string
  nullable = false
  validation {
    condition     = contains(["week10-a2", "week10-a3"], var.assignment)
    error_message = "Only the two reviewed web-target assignments are supported."
  }
}

variable "name_prefix" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^dmi-w10-a[23]-[a-z0-9][a-z0-9-]{3,19}$", var.name_prefix))
    error_message = "Use a unique dmi-w10-a2- or dmi-w10-a3- label with a 4-20 character suffix."
  }
}

variable "controller_ipv4_cidr" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "agent_ipv4_cidr" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "approval" {
  type = object({
    live_execution_approved = optional(bool, false)
    approved_at             = string
    expires_at              = string
    estimated_total_usd     = number
    planning_allowance_usd  = number
  })
  nullable = false
  validation {
    condition = alltrue([
      for value in [var.approval.approved_at, var.approval.expires_at] :
      can(formatdate("YYYY-MM-DD", value)) && can(regex("Z$", value))
    ])
    error_message = "Approval and expiry must be valid UTC RFC3339 timestamps ending in Z."
  }
  validation {
    condition = try(
      var.approval.estimated_total_usd > 0 &&
      var.approval.estimated_total_usd <= var.approval.planning_allowance_usd &&
      var.approval.planning_allowance_usd > 0 && var.approval.planning_allowance_usd <= 10,
      false
    )
    error_message = "Supply a reviewed positive whole-window estimate within the approved allowance (at most US$10); this is not a billing cap."
  }
}

locals {
  ssh_cidrs = distinct([var.controller_ipv4_cidr, var.agent_ipv4_cidr])
  ssh_valid = alltrue([
    for cidr in local.ssh_cidrs : try(
      can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/32$", cidr)) &&
      cidrhost(cidr, 0) == trimsuffix(cidr, "/32") &&
      !contains(["0", "10", "127"], split(".", cidr)[0]) &&
      tonumber(split(".", cidr)[0]) < 224 &&
      !startswith(cidr, "169.254.") && !startswith(cidr, "192.168.") &&
      !startswith(cidr, "192.0.0.") && !startswith(cidr, "192.0.2.") && !startswith(cidr, "192.88.99.") &&
      !startswith(cidr, "198.51.100.") && !startswith(cidr, "203.0.113.") &&
      !(split(".", cidr)[0] == "172" && tonumber(split(".", cidr)[1]) >= 16 && tonumber(split(".", cidr)[1]) <= 31) &&
      !(split(".", cidr)[0] == "100" && tonumber(split(".", cidr)[1]) >= 64 && tonumber(split(".", cidr)[1]) <= 127) &&
      !(split(".", cidr)[0] == "198" && contains([18, 19], tonumber(split(".", cidr)[1]))),
      false
    )
  ])
}

resource "terraform_data" "authorization" {
  input = {
    assignment  = var.assignment
    name_prefix = var.name_prefix
    approval    = var.approval
  }
  lifecycle {
    precondition {
      condition     = var.approval.live_execution_approved
      error_message = "Fresh scoped authorization is required; default/example inputs never grant it."
    }
    precondition {
      condition     = startswith(var.name_prefix, "dmi-w10-${trimprefix(var.assignment, "week10-")}-")
      error_message = "The target prefix must match its assignment; do not reuse the other assignment's host."
    }
    precondition {
      condition     = local.ssh_valid
      error_message = "Both SSH sources must be approved global unicast IPv4 /32s, not ranges, private/reserved/documentation addresses or hostnames."
    }
    precondition {
      condition = (
        timecmp(var.approval.approved_at, plantimestamp()) <= 0 &&
        timecmp(var.approval.expires_at, plantimestamp()) > 0 &&
        timecmp(var.approval.expires_at, timeadd(var.approval.approved_at, "24h")) <= 0
      )
      error_message = "The approved window must already have begun, remain unexpired and be no longer than 24 hours."
    }
    precondition {
      condition     = timecmp(var.approval.expires_at, timestamp()) > 0
      error_message = "A saved plan cannot authorize creation after expiry; reviewed cleanup is still required."
    }
  }
}

output "ssh_cidrs" {
  value     = local.ssh_cidrs
  sensitive = true
}

output "tags" {
  value = {
    assignment = var.assignment
    learner    = "Eze Favour"
    managed_by = "Terraform"
    expires_at = var.approval.expires_at
  }
}
