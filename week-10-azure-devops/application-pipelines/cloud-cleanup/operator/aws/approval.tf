variable "approval" {
  description = "Fixed privileged-access window, not IAM-object retention. Zero is valid for identity-only setup; the existing combined allowance and lab deadlines are unchanged."
  type = object({
    approved_at            = string
    expires_at             = string
    estimated_total_usd    = number
    planning_allowance_usd = number
  })
  validation {
    condition = try(
      endswith(var.approval.approved_at, "Z") && endswith(var.approval.expires_at, "Z") &&
      timecmp(var.approval.expires_at, var.approval.approved_at) > 0 &&
      timecmp(var.approval.expires_at, timeadd(var.approval.approved_at, "24h")) <= 0 &&
      var.approval.estimated_total_usd >= 0 &&
      var.approval.estimated_total_usd <= var.approval.planning_allowance_usd &&
      var.approval.planning_allowance_usd > 0 &&
      var.approval.planning_allowance_usd <= 10, false
    )
    error_message = "Review a maximum 24-hour privileged-access window and nonnegative estimate within the existing positive allowance of at most US$10; no workload is authorized."
  }
}
