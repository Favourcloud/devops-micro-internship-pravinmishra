variable "lease_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{12}$", var.lease_id))
    error_message = "Use a unique lowercase 12-character hex canary lease."
  }
}
variable "account_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Supply the exact approved AWS account."
  }
}
variable "bootstrap_operator_arn" {
  type = string
  validation {
    condition     = can(regex("^arn:aws:(iam::[0-9]{12}:user/[A-Za-z0-9+=,.@_/-]+|sts::[0-9]{12}:assumed-role/[A-Za-z0-9+=,.@_/-]+)$", var.bootstrap_operator_arn))
    error_message = "A separately authorized non-root IAM user or assumed role must bootstrap IAM. No root or restricted federation broker."
  }
}
variable "live_execution_approved" {
  type    = bool
  default = false
}
variable "runtime_permissions_boundary_arn" {
  description = "Administrator-owned fixed canary boundary from operator/aws. The bootstrap user cannot edit or remove it."
  type        = string
  validation {
    condition     = var.runtime_permissions_boundary_arn == "arn:aws:iam::${var.account_id}:policy/dmi-w10-cleanup-boundary-${var.lease_id}"
    error_message = "The exact account/lease runtime permissions boundary is mandatory; arbitrary or absent boundaries are forbidden."
  }
}
variable "federation" {
  description = "Exact verified ARM connection claims; authorized_party is the azp claim, or null when absent. Never save the token."
  type = object({
    issuer            = string
    subject           = string
    authorized_party  = optional(string)
    metadata_verified = bool
  })
  validation {
    condition = (
      var.federation.metadata_verified &&
      can(regex("^https://login[.]microsoftonline[.]com/[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}/v2[.]0$", var.federation.issuer)) &&
      can(regex("^[A-Za-z0-9_:/.-]{10,400}$", var.federation.subject)) &&
      (var.federation.authorized_party == null ? true : can(regex("^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$", var.federation.authorized_party)))
    )
    error_message = "Verify the exact new Entra issuer, subject and azp presence/value; wildcard trust is forbidden."
  }
}
