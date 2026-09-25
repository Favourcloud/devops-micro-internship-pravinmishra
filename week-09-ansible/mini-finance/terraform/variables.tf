variable "name_prefix" {
  description = "Unique prefix for resources dedicated to this assignment; never reuse an existing project's name."
  type        = string
  default     = "dmi-mini-finance"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,29}$", var.name_prefix)) && !endswith(var.name_prefix, "-")
    error_message = "Use 3–30 lowercase letters, digits or hyphens, starting with a letter and not ending in a hyphen."
  }
}

variable "vm_size" {
  description = "B1s is the original lab size. F1als_v7 is the 1-vCPU alternative when legacy B-series capacity is unavailable."
  type        = string
  default     = "Standard_B1s"
  validation {
    condition     = contains(["Standard_B1s", "Standard_F1als_v7"], var.vm_size)
    error_message = "Choose the original B1s or reviewed 1-vCPU F1als_v7 alternative."
  }
}

variable "location" {
  description = "Azure region explicitly approved for this deployment and its costs. No region is preselected."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,39}$", var.location))
    error_message = "Supply an Azure region name, such as a lowercase Azure location slug, after approval."
  }
}

variable "admin_username" {
  description = "Non-root SSH administrator. Use the same value in the private local inventory."
  type        = string
  default     = "azureuser"

  validation {
    condition = can(regex("^[a-z][a-z0-9_]{2,31}$", var.admin_username)) && !contains([
      "root", "admin", "administrator", "guest", "user", "test", "ubuntu", "www", "www-data",
    ], var.admin_username)
    error_message = "Use a non-reserved 3–32 character Linux username, starting with a lowercase letter."
  }
}

variable "controller_cidr" {
  description = "Approved controller's current public IPv4 address as a single-host /32. Never use an open SSH range."
  type        = string
  sensitive   = true

  validation {
    condition = can(cidrnetmask(var.controller_cidr)) && can(regex("/32$", var.controller_cidr)) && !contains([
      "0.0.0.0/32", "127.0.0.1/32", "255.255.255.255/32",
    ], var.controller_cidr)
    error_message = "SSH must be restricted to one valid controller IPv4 /32, not an open range, loopback or unspecified address."
  }
}

variable "ssh_public_key" {
  description = "Existing user's OpenSSH PUBLIC key supplied explicitly in private local variables. Never supply or read a private key."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^(ssh-ed25519|ssh-rsa) [A-Za-z0-9+/]+={0,3}( [^\\r\\n]+)?$", trimspace(var.ssh_public_key)))
    error_message = "Supply a single-line existing OpenSSH RSA (2048+ bits) or Ed25519 public key, not a path or private key."
  }
}
