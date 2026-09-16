variable "project_name" {
  description = "Unique disposable assignment prefix; never reuse an existing deployment's name."
  type        = string
  default     = "dmi-w08-a3"
  nullable    = false

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,28}[a-z0-9]$", var.project_name))
    error_message = "Use 3–30 lowercase letters, digits or hyphens; start with a letter and end with a letter or digit."
  }
}

variable "location" {
  description = "Explicitly approved Azure region code; syntax does not establish permission, capacity or price."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{1,39}$", var.location))
    error_message = "Supply a region code, not its display name; independently verify approval and availability."
  }
}

variable "vm_size" {
  description = "Explicitly approved x86-64 Standard VM SKU with enough memory for the React build; no default or price promise."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^Standard_[A-Za-z0-9_]+$", var.vm_size))
    error_message = "Supply a Standard_ VM SKU after checking x86-64 support, memory, quota, capacity and cost."
  }
}

variable "controller_ipv4_cidr" {
  description = "Explicit controller public IPv4 /32; documentation ranges are allowed for mocks only, never live use."
  type        = string
  nullable    = false

  validation {
    condition = (
      can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/32$", var.controller_ipv4_cidr)) &&
      can(cidrhost(var.controller_ipv4_cidr, 0)) &&
      !can(regex("^(0\\.|10\\.|127\\.|169\\.254\\.|172\\.(1[6-9]|2[0-9]|3[01])\\.|192\\.168\\.|100\\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\\.|(22[4-9]|23[0-9]|24[0-9]|25[0-5])\\.)", var.controller_ipv4_cidr))
    )
    error_message = "Supply a valid public IPv4 /32; broad CIDRs, IPv6, wildcard, private, loopback, link-local, shared and multicast/reserved sources are forbidden."
  }
}

variable "admin_username" {
  description = "Non-reserved Linux administrator; SSH public-key authentication only."
  type        = string
  default     = "dmiuser"
  nullable    = false

  validation {
    condition = (
      can(regex("^[a-z][a-z0-9_-]{0,31}$", var.admin_username)) &&
      !contains([
        "a", "actuser", "adm", "admin", "admin1", "admin2", "administrator", "aspnet",
        "backup", "bin", "console", "daemon", "db1", "db2", "dmi-react-build", "guest", "guest1",
        "helpdesk", "lp", "mail", "man", "messagebus", "mysql", "news", "nobody", "operator",
        "oracle", "postfix", "postgres", "root", "sshd", "sync", "sys", "sysadmin", "test",
        "test1", "test2", "test3", "user", "user1", "user2", "user3", "user4", "user5",
        "uucp", "www", "www-data",
      ], var.admin_username)
    )
    error_message = "Use a non-reserved 1–32 character lowercase Linux username, starting with a letter."
  }
}

variable "admin_ssh_public_key" {
  description = "Existing single-line OpenSSH Ed25519 PUBLIC key only (optional comment); never supply or generate a private key here."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    # This checks the SSH wire type and 32-byte length, not merely a base64-looking string.
    condition     = can(regex("^ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI[A-P][A-Za-z0-9+/]{42}( [!-~]+)?$", var.admin_ssh_public_key))
    error_message = "Supply one valid OpenSSH Ed25519 PUBLIC key line without a trailing newline; key files, private keys, RSA and malformed blobs are not accepted."
  }
}
