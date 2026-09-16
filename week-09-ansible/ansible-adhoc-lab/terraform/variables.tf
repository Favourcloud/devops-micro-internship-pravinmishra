variable "live_execution_approved" {
  description = "Explicit operator acknowledgment AFTER renewed, scoped cloud/budget approval. Not authorization itself."
  type        = bool
  default     = false
  nullable    = false

  validation {
    condition     = var.live_execution_approved
    error_message = "Live planning/provisioning is blocked. Obtain current cloud, budget and cleanup approval before acknowledging it."
  }
}

variable "azure_location" {
  description = "Approved Azure location. Subscription/credentials must remain in the authorized environment."
  type        = string
  default     = "uksouth"

  validation {
    condition     = var.azure_location == "uksouth"
    error_message = "This scoped lab is restricted to the reviewed UK South region."
  }
}

variable "lab_name" {
  description = "Unique, non-sensitive prefix for this disposable lab."
  type        = string
  default     = "week09-ansible"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,31}$", var.lab_name))
    error_message = "Use 3-32 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "controller_ipv4_cidr" {
  description = "Current, approved controller public IPv4 address with /32; SSH and web HTTP are restricted to it."
  type        = string
  nullable    = false

  validation {
    condition = try(
      cidrnetmask(var.controller_ipv4_cidr) == "255.255.255.255" &&
      cidrhost(var.controller_ipv4_cidr, 0) != "0.0.0.0",
      false
    )
    error_message = "Provide one controller IPv4 address with /32, never 0.0.0.0/0 or IPv6."
  }
}

variable "ssh_public_key" {
  description = "Existing controller PUBLIC key only. Keep the private key/passphrase in its existing location and agent."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition     = can(regex("^ssh-(ed25519|rsa) [A-Za-z0-9+/]+={0,3}( [^\n\r]+)?[\n\r]*$", var.ssh_public_key))
    error_message = "Supply an existing OpenSSH ed25519 or RSA PUBLIC key, not a private key or a path."
  }
}
