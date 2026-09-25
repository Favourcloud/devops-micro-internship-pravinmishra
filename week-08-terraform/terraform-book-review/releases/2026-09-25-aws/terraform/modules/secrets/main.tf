variable "name" { type = string }
variable "master_payload" {
  type      = string
  sensitive = true
  ephemeral = true
}
variable "app_payload" {
  type      = string
  sensitive = true
  ephemeral = true
}
variable "master_version" { type = number }
variable "app_version" { type = number }
resource "aws_secretsmanager_secret" "master" {
  name_prefix             = "${var.name}/master-"
  description             = "Initializer-only master credentials; never readable by Web/App roles"
  recovery_window_in_days = 7
}
resource "aws_secretsmanager_secret" "app" {
  name_prefix             = "${var.name}/app-"
  description             = "Shared schema-scoped DB credentials and JWT; coordinated rotation required"
  recovery_window_in_days = 7
}
resource "aws_secretsmanager_secret_version" "master" {
  secret_id                = aws_secretsmanager_secret.master.id
  secret_string_wo         = var.master_payload
  secret_string_wo_version = var.master_version
}
resource "aws_secretsmanager_secret_version" "app" {
  secret_id                = aws_secretsmanager_secret.app.id
  secret_string_wo         = var.app_payload
  secret_string_wo_version = var.app_version
}
output "master_arn" { value = aws_secretsmanager_secret.master.arn }
output "app_arn" { value = aws_secretsmanager_secret.app.arn }
output "master_version_id" { value = aws_secretsmanager_secret_version.master.version_id }
output "app_version_id" { value = aws_secretsmanager_secret_version.app.version_id }
