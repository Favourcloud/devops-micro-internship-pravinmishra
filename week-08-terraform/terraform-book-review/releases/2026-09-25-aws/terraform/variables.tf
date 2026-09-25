variable "region" {
  type        = string
  description = "Human-approved AWS region; no account access is implied."
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.region))
    error_message = "Provide an AWS region name."
  }
}
variable "availability_zones" {
  type = list(string)
  validation {
    condition     = length(var.availability_zones) == 2 && length(distinct(var.availability_zones)) == 2 && alltrue([for az in var.availability_zones : can(regex("^${var.region}[a-z]$", az))])
    error_message = "Exactly two distinct AZs in the selected region are required."
  }
}
variable "name" {
  type    = string
  default = "dmi-book-review"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.name)) && !endswith(var.name, "-") && !strcontains(var.name, "--") && !startswith(var.name, "internal-")
    error_message = "Use 3-20 lowercase letters, digits and internal hyphens."
  }
}
variable "environment" {
  type    = string
  default = "capstone"
}
variable "cleanup_id" {
  type        = string
  description = "Non-secret identifier linking resources to a human-approved cleanup record."
  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{3,50}$", var.cleanup_id))
    error_message = "Provide a safe non-secret cleanup identifier."
  }
}
variable "vpc_cidr" {
  type    = string
  default = "10.84.0.0/16"
  validation {
    condition     = can(cidrnetmask(var.vpc_cidr)) && can(cidrsubnet(var.vpc_cidr, 8, 5)) && endswith(var.vpc_cidr, "/16")
    error_message = "Use an IPv4 /16; the six /24 subnets are derived, not independently overlapping inputs."
  }
}
variable "ami_id" {
  type        = string
  description = "Approved amd64 Ubuntu AMI with the exact runtime prerequisites; no dynamic AMI lookup."
  validation {
    condition     = can(regex("^ami-[0-9a-f]{17}$", var.ami_id))
    error_message = "Supply the reviewed AMI ID."
  }
}
variable "instance_type" {
  type        = string
  default     = "t3.large"
  description = "8 GiB default accommodates conservative artifact verification; smaller allowed classes need measured artifact/runtime memory review. Not free-tier."
  validation {
    condition     = contains(["t3.small", "t3.medium", "t3.large"], var.instance_type)
    error_message = "Choose an allowed amd64 instance class and review its cost."
  }
}
variable "public_hostname" {
  type        = string
  description = "Existing authorized DNS hostname matching the external ACM certificate."
  validation {
    condition     = length(var.public_hostname) <= 253 && can(regex("^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z]{2,63}$", var.public_hostname))
    error_message = "Provide a valid DNS hostname (max 253 characters, each label max 63 characters); not a URL, wildcard, IP, path or shell input."
  }
}
variable "public_endpoint_mode" {
  type    = string
  default = "acm_alb"
  validation {
    condition     = contains(["acm_alb", "api_gateway"], var.public_endpoint_mode)
    error_message = "Use direct ACM ALB HTTPS or AWS-provided API Gateway HTTPS."
  }
}
variable "gateway_api_id" {
  type    = string
  default = ""
  validation {
    condition     = var.public_endpoint_mode != "api_gateway" || (can(regex("^[a-z0-9]{10}$", var.gateway_api_id)) && var.public_hostname == "${var.gateway_api_id}.execute-api.${var.region}.amazonaws.com")
    error_message = "Provide the owned HTTP API ID for API Gateway mode."
  }
}
variable "certificate_arn" {
  type        = string
  default     = null
  description = "Same-region ACM certificate for direct ALB mode; absent for private VPC-link HTTP."
  validation {
    condition     = var.public_endpoint_mode == "api_gateway" ? var.certificate_arn == null : can(regex("^arn:aws:acm:[a-z0-9-]+:[0-9]{12}:certificate/[0-9a-f-]{36}$", var.certificate_arn)) && try(split(":", var.certificate_arn)[3] == var.region, false)
    error_message = "Direct ALB HTTPS needs same-region ACM; API Gateway mode uses its AWS-managed certificate."
  }
}
variable "router_secret_arn" {
  type        = string
  description = "Existing secret containing the Router's local TLS certificate/private_key; never a secret value."
  validation {
    condition     = can(regex("^arn:aws:secretsmanager:[a-z0-9-]+:[0-9]{12}:secret:[A-Za-z0-9/_+=.@-]+$", var.router_secret_arn)) && try(split(":", var.router_secret_arn)[3] == var.region, false)
    error_message = "Provide an existing same-region Secrets Manager ARN."
  }
}
variable "runtime_artifact_url" {
  type        = string
  description = "Existing reviewed immutable Linux build artifact URL; publishing/storage are outside this project."
  validation {
    condition     = can(regex("^https://[a-z0-9.-]+/[A-Za-z0-9_./-]+$", var.runtime_artifact_url)) && !strcontains(var.runtime_artifact_url, "/../")
    error_message = "Supply an approved plain HTTPS artifact URL without auth, query, redirect, traversal or shell syntax."
  }
}
variable "runtime_artifact_sha256" {
  type        = string
  description = "Exact reviewed Linux artifact digest; a source archive or macOS build is not a runtime artifact."
  validation {
    condition     = can(regex("^[0-9a-f]{64}$", var.runtime_artifact_sha256))
    error_message = "Supply the reviewed Linux artifact SHA-256."
  }
}
variable "rds_ca_sha256" {
  type        = string
  description = "Verified SHA-256 of the official RDS CA bundle preinstalled at /etc/book-review/rds-ca.pem in the approved AMI; no runtime CA download."
  validation {
    condition     = can(regex("^[0-9a-f]{64}$", var.rds_ca_sha256))
    error_message = "Provide the verified CA bundle SHA-256, not certificate/private-key contents."
  }
}
variable "db_name" {
  type    = string
  default = "book_review_db"
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{2,31}$", var.db_name))
    error_message = "Use a safe 3-32 character database identifier."
  }
}
variable "db_master_username" {
  type    = string
  default = "bookreview_admin"
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{2,15}$", var.db_master_username))
    error_message = "Use a safe 3-16 character master username."
  }
}
variable "app_username" {
  type    = string
  default = "bookreview_app"
  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{2,15}$", var.app_username)) && var.app_username != var.db_master_username
    error_message = "Use a distinct safe schema-scoped application username."
  }
}
variable "db_master_password" {
  type      = string
  sensitive = true
  ephemeral = true
  validation {
    condition     = length(var.db_master_password) >= 24 && length(var.db_master_password) <= 41 && can(regex("^[A-Za-z0-9!#$%&*+,:;<=>?^_{|}~-]+$", var.db_master_password))
    error_message = "Supply 24-41 approved printable characters, excluding RDS-disallowed quotes, slash, at-sign and whitespace."
  }
}
variable "app_password" {
  type      = string
  sensitive = true
  ephemeral = true
  validation {
    condition     = length(var.app_password) >= 24 && length(var.app_password) <= 128 && can(regex("^[[:graph:]]+$", var.app_password))
    error_message = "Supply a strong 24-128 character printable application password without whitespace/control characters."
  }
}
variable "jwt_secret" {
  type      = string
  sensitive = true
  ephemeral = true
  validation {
    condition     = length(var.jwt_secret) >= 32 && length(var.jwt_secret) <= 256 && can(regex("^[[:graph:]]+$", var.jwt_secret))
    error_message = "Supply a shared strong 32-256 character printable signing secret without whitespace/control characters."
  }
}
variable "master_secret_version" {
  type    = number
  default = 1
  validation {
    condition     = var.master_secret_version >= 1 && floor(var.master_secret_version) == var.master_secret_version
    error_message = "Use a positive integer version; increment only during coordinated master rotation."
  }
}
variable "app_secret_version" {
  type    = number
  default = 1
  validation {
    condition     = var.app_secret_version >= 1 && floor(var.app_secret_version) == var.app_secret_version
    error_message = "Use a positive integer version; coordinate DB/JWT rotation before incrementing."
  }
}
variable "db_engine_version" {
  type    = string
  default = "8.4"
  validation {
    condition     = can(regex("^8\\.4(\\.[0-9]+)?$", var.db_engine_version))
    error_message = "Use an available reviewed MySQL 8.4 LTS version; availability is a human live gate."
  }
}
variable "db_instance_class" {
  type    = string
  default = "db.t4g.small"
  validation {
    condition     = contains(["db.t4g.small", "db.t4g.medium", "db.m7g.large"], var.db_instance_class)
    error_message = "Choose a supported reviewed class; no free-tier claim is made."
  }
}
variable "enable_database_initializer" {
  type    = bool
  default = false
}
variable "runtime_release_authorized" {
  type        = bool
  default     = false
  description = "Closed by default. A true value cannot remedy vulnerable upstream: requires separately reviewed fixed-source/security/runtime release approval."
}
variable "deletion_protection" {
  type        = bool
  default     = true
  description = "Disable only in a separately human-reviewed cleanup plan."
}
variable "final_snapshot_suffix" {
  type        = string
  description = "Unique approved cleanup snapshot suffix; reused names can block a later destroy."
  validation {
    condition     = can(regex("^[a-z0-9]{4,24}$", var.final_snapshot_suffix))
    error_message = "Use a unique 4-24 character lowercase alphanumeric snapshot suffix."
  }
}
