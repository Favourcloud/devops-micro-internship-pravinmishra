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
  tags = {
    assignment = "week10-a4"
    learner    = "Eze Favour"
    managed_by = "Terraform"
    expires_at = var.approval.expires_at
  }
}

resource "terraform_data" "authorization" {
  input = {
    name_prefix = var.name_prefix
    approval    = var.approval
  }
  lifecycle {
    precondition {
      condition = (
        var.approval.live_execution_approved && var.approval.remote_state_ready &&
        var.approval.cleanup_safeguard_ready
      )
      error_message = "Fresh A4 authorization, independently verified protected state and a cleanup safeguard are required."
    }
    precondition {
      condition     = local.ssh_valid
      error_message = "Both SSH sources must be approved global unicast IPv4 /32s, not private, reserved, documentation or broad ranges."
    }
    precondition {
      condition = (
        timecmp(var.approval.approved_at, plantimestamp()) <= 0 &&
        timecmp(var.approval.expires_at, timeadd(plantimestamp(), "2h")) > 0 &&
        timecmp(var.approval.expires_at, timeadd(var.approval.approved_at, "24h")) <= 0
      )
      error_message = "Use an active window of at most 24 hours with more than two hours remaining for slow database cleanup."
    }
    precondition {
      condition     = timecmp(var.approval.expires_at, timeadd(timestamp(), "2h")) > 0
      error_message = "An old saved plan cannot create resources without the two-hour cleanup margin."
    }
    precondition {
      condition     = timecmp(var.approval.expires_at, "2027-02-01T00:00:00Z") < 0
      error_message = "This MySQL 8.0/provider baseline must be reviewed before Azure standard support ends; no automatic Extended Support charges are approved."
    }
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "epicbook" {
  name       = "${var.name_prefix}-rg"
  location   = "uksouth"
  tags       = local.tags
  depends_on = [terraform_data.authorization]
  lifecycle {
    precondition {
      condition = (
        data.azurerm_client_config.current.subscription_id == var.subscription_id &&
        data.azurerm_client_config.current.tenant_id == var.tenant_id &&
        data.azurerm_client_config.current.client_id == var.client_id &&
        data.azurerm_client_config.current.object_id == var.operator_object_id
      )
      error_message = "The active subscription, tenant, federated client and principal must match the approved private context."
    }
  }
}
