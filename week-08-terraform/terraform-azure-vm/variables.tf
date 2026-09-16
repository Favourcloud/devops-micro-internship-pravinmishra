variable "project_name" {
  description = "Unique disposable assignment prefix; do not reuse an existing deployment name."
  type        = string
  default     = "dmi-w08-a1"
  nullable    = false

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,28}[a-z0-9]$", var.project_name))
    error_message = "Use 3–30 lowercase letters, digits or hyphens, starting with a letter and ending with a letter or digit."
  }
}

variable "location" {
  description = "Explicitly approved Azure region. No default or availability guarantee."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{1,39}$", var.location))
    error_message = "Supply an Azure region code, not its display name; approval and availability must be checked separately."
  }
}

variable "vm_size" {
  description = "Explicitly approved VM SKU. Syntax validation does not establish quota, capacity or price."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^Standard_[A-Za-z0-9_]+$", var.vm_size))
    error_message = "Supply a Standard_ VM SKU approved for this run; do not assume availability."
  }
}

variable "controller_ipv4_cidr" {
  description = "Current controller public IPv4 with /32, supplied explicitly; only this source can reach SSH."
  type        = string
  nullable    = false

  validation {
    condition = (
      can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/32$", var.controller_ipv4_cidr)) &&
      can(cidrhost(var.controller_ipv4_cidr, 0)) &&
      var.controller_ipv4_cidr != "0.0.0.0/32"
    )
    error_message = "Supply an explicit, valid controller IPv4 /32; IPv6, 0.0.0.0, wildcards and broader CIDRs are forbidden."
  }
}

variable "admin_username" {
  description = "Non-reserved Linux administrator name; password authentication is required by the assignment."
  type        = string
  default     = "dmiuser"
  nullable    = false

  validation {
    condition = (
      can(regex("^[a-z][a-z0-9_-]{0,31}$", var.admin_username)) &&
      !contains([
        "1", "123", "a", "actuser", "adm", "admin", "admin1", "admin2", "administrator",
        "aspnet", "backup", "bin", "console", "daemon", "db1", "db2", "guest", "guest1",
        "helpdesk", "lp", "mail", "man", "messagebus", "mysql", "news", "nobody", "operator",
        "oracle", "postfix", "postgres", "root", "sshd", "sync", "sys", "sysadmin", "test",
        "test1", "test2", "test3", "user", "user1", "user2", "user3", "user4", "user5",
        "uucp", "www", "www-data",
      ], var.admin_username)
    )
    error_message = "Use a non-reserved 1–32 character Linux username, starting with a lowercase letter; remaining characters may be lowercase letters, digits, underscores or hyphens."
  }
}

variable "admin_password" {
  description = "Supply only through a hidden prompt or TF_VAR_admin_password; sensitive but still stored in private Terraform state."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition = (
      length(var.admin_password) >= 16 && length(var.admin_password) <= 72 &&
      can(regex("^[!-~]+$", var.admin_password)) &&
      can(regex("[a-z]", var.admin_password)) &&
      can(regex("[A-Z]", var.admin_password)) &&
      can(regex("[0-9]", var.admin_password)) &&
      can(regex("[^a-zA-Z0-9]", var.admin_password)) &&
      !strcontains(lower(var.admin_password), lower(var.admin_username))
    )
    error_message = "Password must be 16–72 printable ASCII characters without spaces, with uppercase, lowercase, digit and symbol, and must not contain the username. Never save it in tfvars or evidence."
  }
}
