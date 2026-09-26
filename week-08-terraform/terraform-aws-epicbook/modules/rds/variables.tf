variable "project_name" { type = string }
variable "private_subnet_ids" {
  type = list(string)
  validation {
    condition     = length(var.private_subnet_ids) == 2 && length(distinct(var.private_subnet_ids)) == 2
    error_message = "Provide two distinct private DB subnet IDs."
  }
}
variable "security_group_id" { type = string }
variable "instance_class" { type = string }
variable "engine_version" { type = string }
variable "db_username" {
  type      = string
  sensitive = true
  validation {
    condition     = lower(var.db_username) != "epicbookapp"
    error_message = "The RDS master username must not be epicbookapp (case-insensitive); it is reserved for the application."
  }
}
variable "db_password" {
  type      = string
  sensitive = true
  ephemeral = true
  validation {
    condition     = can(regex("^[A-Za-z0-9!#%^*+=_-]{24,41}$", var.db_password))
    error_message = "Use a unique 24-41 character password supported by the RDS MySQL master-password API."
  }
}
variable "credential_version" { type = number }
variable "accept_lab_data_loss" {
  type = bool
  validation {
    condition     = var.accept_lab_data_loss
    error_message = "Disposable lab deletion must be explicitly accepted."
  }
}
