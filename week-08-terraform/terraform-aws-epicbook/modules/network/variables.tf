variable "project_name" { type = string }
variable "azs" {
  type = list(string)
  validation {
    condition     = length(var.azs) == 2 && length(distinct(var.azs)) == 2
    error_message = "Network requires exactly two distinct AZs."
  }
}
variable "controller_cidr" {
  type = string
  validation {
    condition     = can(cidrnetmask(var.controller_cidr)) && endswith(var.controller_cidr, "/32")
    error_message = "SSH must use a single IPv4 /32. Root validation additionally requires a public address."
  }
}
