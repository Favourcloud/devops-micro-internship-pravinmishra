variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name" {
  type    = string
  default = "dmi-a5-ha"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.name))
    error_message = "Use 3–20 lowercase alphanumeric/hyphen characters, starting with a letter."
  }
}

variable "ssh_cidr" {
  description = "Optional operator IPv4 /32; SSM provides administration without SSH keys."
  type        = string
  default     = null
  validation {
    condition     = var.ssh_cidr == null ? true : can(cidrnetmask(var.ssh_cidr)) && endswith(var.ssh_cidr, "/32")
    error_message = "SSH must be limited to one IPv4 /32 address."
  }
}

variable "web_az_indexes" {
  description = "Normally [0,1]; [1] temporarily models loss of the web tier in AZ A, not a full AWS AZ outage."
  type        = set(number)
  default     = [0, 1]
  validation {
    condition     = length(var.web_az_indexes) > 0 && alltrue([for index in var.web_az_indexes : contains([0, 1], index)])
    error_message = "Choose one or both of AZ indexes 0 and 1."
  }
}

variable "replacement_instance_id" {
  description = "Exact existing lab ASG instance to terminate; required only for replacement_test."
  type        = string
  default     = null
  validation {
    condition     = var.replacement_instance_id == null ? true : can(regex("^i-[0-9a-f]{17}$", var.replacement_instance_id))
    error_message = "Supply an exact EC2 instance ID."
  }
}

variable "replacement_test" {
  description = "Temporarily enable a guarded one-instance termination test through Terraform."
  type        = bool
  default     = false
}
