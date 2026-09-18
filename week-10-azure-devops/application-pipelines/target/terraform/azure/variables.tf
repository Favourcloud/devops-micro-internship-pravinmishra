variable "subscription_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "Supply the approved subscription UUID privately."
  }
}

variable "tenant_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$", var.tenant_id))
    error_message = "Supply the approved tenant UUID privately."
  }
}

variable "operator_object_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$", var.operator_object_id))
    error_message = "Supply the independently verified operator object UUID privately."
  }
}

variable "operator_public_key" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^ssh-rsa [A-Za-z0-9+/]+={0,2}$", var.operator_public_key))
    error_message = "Supply the reviewed operator RSA public key without options/comment; verify its size/fingerprint separately."
  }
}

variable "image_version" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+$", var.image_version))
    error_message = "Pin an independently verified Canonical Ubuntu 22.04 Gen2 version, not latest."
  }
}

variable "name_prefix" {
  type     = string
  nullable = false
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
}
