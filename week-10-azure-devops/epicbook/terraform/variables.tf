variable "subscription_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "Supply the approved subscription UUID privately."
  }
}

variable "tenant_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.tenant_id))
    error_message = "Supply the approved tenant UUID privately."
  }
}

variable "client_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.client_id))
    error_message = "Supply the approved federated application's client UUID privately."
  }
}

variable "operator_object_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.operator_object_id))
    error_message = "Supply the approved service principal's object UUID privately."
  }
}

variable "name_prefix" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^dmi-w10-a4-[a-z0-9]{4,12}$", var.name_prefix))
    error_message = "Use a unique dmi-w10-a4- prefix followed by 4-12 lowercase alphanumeric characters."
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

variable "operator_public_key" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^ssh-ed25519 [A-Za-z0-9+/]{68}( [A-Za-z0-9_.@-]+)?$", var.operator_public_key))
    error_message = "Supply a reviewed Ed25519 public key, not a private key or multiline value."
  }
}

variable "image_version" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+$", var.image_version))
    error_message = "Pin a freshly verified Canonical Ubuntu 22.04 Gen2 image version; latest is not accepted."
  }
}

variable "mysql_admin_password" {
  type      = string
  nullable  = false
  sensitive = true
  ephemeral = true
  validation {
    condition = (
      length(var.mysql_admin_password) >= 20 && length(var.mysql_admin_password) <= 128 &&
      can(regex("[a-z]", var.mysql_admin_password)) && can(regex("[A-Z]", var.mysql_admin_password)) &&
      can(regex("[0-9]", var.mysql_admin_password)) && can(regex("[^A-Za-z0-9]", var.mysql_admin_password)) &&
      !can(regex("[\\r\\n]", var.mysql_admin_password))
    )
    error_message = "Provide a fresh 20-128 character secret with upper/lowercase, digits and punctuation, without newlines."
  }
}

variable "mysql_password_version" {
  type     = number
  nullable = false
  validation {
    condition     = var.mysql_password_version >= 1 && floor(var.mysql_password_version) == var.mysql_password_version
    error_message = "Use a positive integer rotation version for the write-only password."
  }
}

variable "approval" {
  type = object({
    scope                   = string
    live_execution_approved = optional(bool, false)
    remote_state_ready      = optional(bool, false)
    cleanup_safeguard_ready = optional(bool, false)
    approved_at             = string
    expires_at              = string
    estimated_total_usd     = number
    planning_allowance_usd  = number
  })
  nullable = false
  validation {
    condition     = var.approval.scope == "week10-a4-two-vms-private-mysql"
    error_message = "A2/A3 authorization cannot authorize A4's two VMs, database and state costs."
  }
  validation {
    condition = alltrue([
      for value in [var.approval.approved_at, var.approval.expires_at] :
      can(formatdate("YYYY-MM-DD", value)) && can(regex("Z$", value))
    ])
    error_message = "Approval and expiry must be valid UTC RFC3339 timestamps ending in Z."
  }
  validation {
    condition = try(
      var.approval.estimated_total_usd > 0 && var.approval.planning_allowance_usd > 0 &&
      var.approval.estimated_total_usd <= var.approval.planning_allowance_usd,
      false
    )
    error_message = "Supply a current whole-window estimate within a separately approved positive A4 allowance; neither is a billing cap."
  }
}
