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
    condition = (
      can(regex("^arn:aws:(iam::[0-9]{12}:user/[A-Za-z0-9+=,.@_/-]+|sts::[0-9]{12}:assumed-role/[A-Za-z0-9+=,.@_/-]+)$", var.administrator_arn)) ||
      (var.root_bootstrap_approval != null && var.administrator_arn == "arn:aws:iam::${var.account_id}:root")
    )
    error_message = "Use an authorized non-root administrator, or the exact account root with explicit short-lived IAM-only bootstrap approval. Federation-broker sessions remain rejected."
  }
}
variable "root_bootstrap_approval" {
  description = "Optional, separately authorized root exception for this IAM identity root only; never credentials or permission to run workload roots."
  type = object({
    approved_at = string
    expires_at  = string
  })
  default = null
  validation {
    condition = var.root_bootstrap_approval == null ? true : try(
      endswith(var.root_bootstrap_approval.approved_at, "Z") &&
      endswith(var.root_bootstrap_approval.expires_at, "Z") &&
      timecmp(var.root_bootstrap_approval.expires_at, var.root_bootstrap_approval.approved_at) > 0 &&
      timecmp(var.root_bootstrap_approval.expires_at, timeadd(var.root_bootstrap_approval.approved_at, "1h")) <= 0,
      false
    )
    error_message = "The root IAM exception must have a fixed UTC window of at most one hour."
  }
}
variable "administration_approval" {
  description = "Optional fresh non-root administrator maintenance window; does not extend the operator's privilege expiry. Root must instead use root_bootstrap_approval."
  type = object({
    approved_at = string
    expires_at  = string
  })
  default = null
  validation {
    condition = var.administration_approval == null ? true : try(
      var.root_bootstrap_approval == null &&
      endswith(var.administration_approval.approved_at, "Z") &&
      endswith(var.administration_approval.expires_at, "Z") &&
      timecmp(var.administration_approval.expires_at, var.administration_approval.approved_at) > 0 &&
      timecmp(var.administration_approval.expires_at, timeadd(var.administration_approval.approved_at, "1h")) <= 0,
      false
    )
    error_message = "Non-root maintenance needs one fixed UTC window of at most one hour, never combined with a root exception."
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
variable "persistent_identity_approved" {
  description = "Explicit approval to retain the IAM user and protective policies, not to extend bootstrap permissions or any lab-resource lifetime."
  type        = bool
  default     = false
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
