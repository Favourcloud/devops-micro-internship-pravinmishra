variable "subscription_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-f-]{36}$", var.subscription_id))
    error_message = "Use the approved Azure subscription UUID."
  }
}

variable "tenant_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-f-]{36}$", var.tenant_id))
    error_message = "Use the approved Azure tenant UUID."
  }
}

variable "operator_object_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-f-]{36}$", var.operator_object_id))
    error_message = "Use the verified signed-in operator object UUID."
  }
}

variable "project_name" {
  type = string
  validation {
    condition     = can(regex("^dmi-w10-a1-[a-z0-9-]{4,20}$", var.project_name))
    error_message = "Use a unique Week 10 A1 project prefix."
  }
}

variable "location" {
  type    = string
  default = "uksouth"
  validation {
    condition     = var.location == "uksouth"
    error_message = "A different region requires a new scope and pricing review."
  }
}

variable "vm_size" {
  type    = string
  default = "Standard_D2lds_v6"
  validation {
    condition     = var.vm_size == "Standard_D2lds_v6"
    error_message = "A different size requires a new capacity and cost review."
  }
}

variable "controller_ipv4_cidr" {
  type      = string
  sensitive = true
  validation {
    condition     = can(cidrnetmask(var.controller_ipv4_cidr)) && can(regex("/32$", var.controller_ipv4_cidr)) && !can(regex("^0\\.", var.controller_ipv4_cidr))
    error_message = "SSH requires the approved controller's IPv4 /32, never a public range."
  }
}

variable "ssh_public_key" {
  type = string
  validation {
    condition     = can(regex("^ssh-rsa [A-Za-z0-9+/]+={0,3}( [^\\r\\n]+)?$", trimspace(var.ssh_public_key)))
    error_message = "Supply the dedicated operator's RSA public key, never a private key."
  }
}

variable "image_version" {
  type = string
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+$", var.image_version))
    error_message = "Pin a verified Canonical Ubuntu 22.04 Gen2 image version, not latest."
  }
}

variable "expires_at" {
  type = string
  validation {
    condition     = can(formatdate("YYYY-MM-DD", var.expires_at))
    error_message = "Use the approved UTC cleanup deadline in RFC3339 format."
  }
}

variable "live_execution_approved" {
  type    = bool
  default = false
}
variable "enable_managed_identity" {
  type        = bool
  default     = false
  description = "Enable a dedicated system identity only when scoped pipeline Azure access is needed."
}
