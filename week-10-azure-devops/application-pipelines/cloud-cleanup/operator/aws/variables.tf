variable "lease_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{12}$", var.lease_id))
    error_message = "Use a fresh approved 12-character lowercase hex lease, unchanged throughout the lifecycle."
  }
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Use the exact approved AWS account ID."
  }
}
variable "administrator_arn" {
  type = string
  validation {
    condition     = can(regex("^arn:aws:(iam::[0-9]{12}:user/[A-Za-z0-9+=,.@_/-]+|sts::[0-9]{12}:assumed-role/[A-Za-z0-9+=,.@_/-]+)$", var.administrator_arn))
    error_message = "Use a separately authorized non-root IAM user or assumed role; root and federation-broker sessions are rejected."
  }
}
variable "oidc_issuer" {
  description = "The approved Entra tenant issuer to scope IAM permissions, not proof of actual connection/token claims."
  type        = string
  validation {
    condition     = can(regex("^https://login[.]microsoftonline[.]com/[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}/v2[.]0$", var.oidc_issuer))
    error_message = "Use one exact approved Entra tenant issuer, never a wildcard or legacy issuer."
  }
}
variable "live_execution_approved" {
  type    = bool
  default = false
}
variable "bootstrap_access_enabled" {
  type    = bool
  default = false
}
variable "mfa_enrolled_and_verified" {
  description = "Human attestation only; live MFA/session-context acceptance is still required."
  type        = bool
  default     = false
}
