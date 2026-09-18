variable "lease_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{12}$", var.lease_id))
    error_message = "Use a new lowercase hex canary lease."
  }
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Supply the approved AWS account ID."
  }
}
variable "operator_arn" {
  type = string
  validation {
    condition     = can(regex("^arn:aws:(iam::[0-9]{12}:user/[A-Za-z0-9+=,.@_/-]+|sts::[0-9]{12}:(assumed-role/[A-Za-z0-9+=,.@_/-]+|federated-user/[A-Za-z0-9+=,.@_-]+))$", var.operator_arn))
    error_message = "The exact operator must not be root."
  }
}
variable "expires_at" {
  type = string
  validation {
    condition     = can(formatdate("YYYY-MM-DD", var.expires_at)) && endswith(var.expires_at, "Z")
    error_message = "Use the fixed approved UTC expiry."
  }
}
variable "live_execution_approved" {
  type    = bool
  default = false
}
