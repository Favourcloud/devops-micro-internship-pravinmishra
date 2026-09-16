variable "expected_account_id" {
  description = "Approved AWS account ID; set locally through TF_VAR_expected_account_id. Never commit the real value."
  type        = string
  sensitive   = true
  default     = ""
  nullable    = false
  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "Set the approved 12-digit account ID locally before a real plan."
  }
}

variable "deployment_approved" {
  description = "Explicit human approval for these five AWS additions, incremental spending and their cleanup. This is an acknowledgement, not an enforced budget."
  type        = bool
  default     = false
  nullable    = false
}

variable "runtime_verified" {
  description = "An authorized operator has checked the actual Web/App runtime, source, dependencies, API routing and schema risks before public exposure. Mock tests do not satisfy this gate."
  type        = bool
  default     = false
  nullable    = false
}
