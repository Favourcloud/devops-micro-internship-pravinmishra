variable "lease_id" {
  type = string
  validation {
    condition     = can(regex("^[a-f0-9]{12}$", var.lease_id))
    error_message = "Use a new lowercase hex canary lease."
  }
}
variable "subscription_id" { type = string }
variable "tenant_id" { type = string }
variable "operator_object_id" { type = string }
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
