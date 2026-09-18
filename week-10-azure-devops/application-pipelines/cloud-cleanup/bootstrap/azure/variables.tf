variable "lease_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{12}$", var.lease_id))
    error_message = "Use a new random 12-character lowercase hex lease; never reuse a canary namespace."
  }
}
variable "subscription_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$", var.subscription_id))
    error_message = "Supply the approved subscription UUID."
  }
}
variable "tenant_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$", var.tenant_id))
    error_message = "Supply the approved tenant UUID."
  }
}
variable "bootstrap_operator_object_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}$", var.bootstrap_operator_object_id))
    error_message = "Supply the exact approved bootstrap operator UUID."
  }
}
variable "live_execution_approved" {
  type    = bool
  default = false
}
variable "canary_group_ready" {
  description = "Second phase only: the separately state-owned, empty canary RG already exists."
  type        = bool
  default     = false
}
variable "federation" {
  description = "Copy exact verified values from the draft ARM service connection; null creates no trust. Do not derive the subject from names."
  type = object({
    issuer            = string
    subject           = string
    metadata_verified = bool
  })
  default = null
  validation {
    condition = var.federation == null ? true : (
      var.federation.metadata_verified &&
      can(regex("^https://login.microsoftonline.com/[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}/v2.0$", var.federation.issuer)) &&
      can(regex("^[A-Za-z0-9_:/.-]{10,400}$", var.federation.subject))
    )
    error_message = "Use the verified current Microsoft Entra issuer and exact subject, without wildcard trust."
  }
}
