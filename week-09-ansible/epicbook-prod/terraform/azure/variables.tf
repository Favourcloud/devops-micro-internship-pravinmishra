variable "subscription_id" {
  description = "Explicitly approved Azure subscription, supplied locally and never committed."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$", var.subscription_id))
    error_message = "Provide a UUID subscription ID using ignored local input."
  }
}

variable "run_id" {
  description = "Unique approved lab identifier; reuse only with its own existing state, never import another lab."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[a-z0-9]{6,16}$", var.run_id))
    error_message = "Use a unique 6-16 character lowercase alphanumeric run ID."
  }
}

variable "location" {
  description = "Reviewed Azure region; SKU capacity and authorization still require a live preflight."
  type        = string
  default     = "uksouth"

  validation {
    condition     = var.location == "uksouth"
    error_message = "Only the reviewed uksouth location is allowed."
  }
}

variable "controller_cidr" {
  description = "Controller's approved public IPv4 address with /32; no default or world-open SSH."
  type        = string
  nullable    = false

  validation {
    condition = (
      can(cidrnetmask(var.controller_cidr)) &&
      can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+/32$", var.controller_cidr)) &&
      !can(regex("^(0|127)\\.", var.controller_cidr))
    )
    error_message = "Use one non-loopback IPv4 controller address with /32."
  }
}

variable "ssh_public_key" {
  description = "Public SSH key only, supplied locally; never supply private key material."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition     = can(regex("^(ssh-ed25519|ssh-rsa) [A-Za-z0-9+/]+={0,3}( [^\\r\\n]*)?$", var.ssh_public_key))
    error_message = "Supply a single-line OpenSSH Ed25519 or RSA public key."
  }
}

variable "vm_size" {
  description = "Reviewed nonzonal 2-vCPU/4-GiB NVMe single-VM lab size; allocation capacity is not assumed."
  type        = string
  default     = "Standard_D2lds_v6"

  validation {
    condition     = var.vm_size == "Standard_D2lds_v6"
    error_message = "Only the reviewed nonzonal Standard_D2lds_v6 is approved by this preparation."
  }
}

variable "os_disk_gib" {
  description = "Platform-encrypted Standard_LRS OS disk, fixed to the approved 32 GiB."
  type        = number
  default     = 32

  validation {
    condition     = var.os_disk_gib == 32
    error_message = "Only the reviewed 32 GiB OS disk is allowed."
  }
}
