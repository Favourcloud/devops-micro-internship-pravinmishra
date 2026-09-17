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
}
variable "db_password" {
  type      = string
  sensitive = true
  ephemeral = true
}
variable "credential_version" { type = number }
variable "accept_lab_data_loss" {
  type = bool
  validation {
    condition     = var.accept_lab_data_loss
    error_message = "Disposable lab deletion must be explicitly accepted."
  }
}
