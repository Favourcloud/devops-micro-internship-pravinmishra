variable "aws_region" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^(af|ap|ca|eu|il|me|mx|sa|us)-(central|north|northeast|northwest|south|southeast|southwest|east|west)-[1-9][0-9]*$", var.aws_region))
    error_message = "Supply the explicitly approved commercial AWS region; availability and price need a fresh check."
  }
}

variable "account_id" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "Supply the approved account ID privately."
  }
}

variable "operator_arn" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^arn:aws:(iam::[0-9]{12}:user/[A-Za-z0-9+=,.@_/-]+|sts::[0-9]{12}:assumed-role/[A-Za-z0-9+=,.@_/-]+|sts::[0-9]{12}:federated-user/[A-Za-z0-9+=,.@_-]{2,32})$", var.operator_arn))
    error_message = "Supply the exact approved non-root IAM user, assumed-role or restricted federated-user session ARN; root cannot operate this target."
  }
}

variable "ami_id" {
  type     = string
  nullable = false
  validation {
    condition     = can(regex("^ami-[0-9a-f]{17}$", var.ami_id))
    error_message = "Pin an independently verified regional Canonical Ubuntu 24.04 x86_64 AMI, not a moving latest query."
  }
}

variable "operator_public_key" {
  type      = string
  nullable  = false
  sensitive = true
  validation {
    condition     = can(regex("^ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI[A-Za-z0-9+/]{43}$", var.operator_public_key))
    error_message = "Supply only the reviewed operator Ed25519 public key without options/comment; the deployment key is separate."
  }
}

variable "name_prefix" {
  type     = string
  nullable = false
}

variable "controller_ipv4_cidr" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "agent_ipv4_cidr" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "approval" {
  type = object({
    live_execution_approved = optional(bool, false)
    approved_at             = string
    expires_at              = string
    estimated_total_usd     = number
    planning_allowance_usd  = number
  })
  nullable = false
}
