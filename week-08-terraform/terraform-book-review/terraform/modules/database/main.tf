variable "name" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_group_id" { type = string }
variable "database_name" { type = string }
variable "master_username" { type = string }
variable "master_password" {
  type      = string
  sensitive = true
  ephemeral = true
}
variable "password_version" { type = number }
variable "engine_version" { type = string }
variable "instance_class" { type = string }
variable "deletion_protection" { type = bool }
variable "final_snapshot_suffix" { type = string }
resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = var.subnet_ids
}
resource "aws_db_parameter_group" "this" {
  name_prefix = "${var.name}-"
  family      = "mysql8.4"
  parameter {
    name         = "require_secure_transport"
    value        = "ON"
    apply_method = "immediate"
  }
  lifecycle { create_before_destroy = true }
}
resource "aws_db_instance" "primary" {
  identifier     = "${var.name}-primary"
  engine         = "mysql"
  engine_version = var.engine_version
  instance_class = var.instance_class
  db_name        = var.database_name
  username       = var.master_username
  # Even explicit false conflicts with password_wo in the pinned provider schema.
  password_wo                = var.master_password
  password_wo_version        = var.password_version
  multi_az                   = true
  db_subnet_group_name       = aws_db_subnet_group.this.name
  parameter_group_name       = aws_db_parameter_group.this.name
  vpc_security_group_ids     = [var.security_group_id]
  publicly_accessible        = false
  port                       = 3306
  storage_encrypted          = true
  storage_type               = "gp3"
  allocated_storage          = 20
  max_allocated_storage      = 50
  backup_retention_period    = 7
  backup_window              = "02:00-03:00"
  maintenance_window         = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true
  deletion_protection        = var.deletion_protection
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${var.name}-primary-${var.final_snapshot_suffix}"
  copy_tags_to_snapshot      = true
  delete_automated_backups   = false
  apply_immediately          = false
}
resource "aws_db_instance" "replica" {
  identifier = "${var.name}-replica"
  # An explicit same-region subnet group requires the source ARN in AWS provider 6.64.0.
  replicate_source_db        = aws_db_instance.primary.arn
  db_subnet_group_name       = aws_db_subnet_group.this.name
  instance_class             = var.instance_class
  multi_az                   = false
  parameter_group_name       = aws_db_parameter_group.this.name
  vpc_security_group_ids     = [var.security_group_id]
  publicly_accessible        = false
  port                       = 3306
  storage_encrypted          = true
  storage_type               = "gp3"
  max_allocated_storage      = 50
  backup_retention_period    = 1
  maintenance_window         = "sun:05:00-sun:06:00"
  auto_minor_version_upgrade = true
  deletion_protection        = var.deletion_protection
  # RDS forbids a final snapshot when deleting an unpromoted read replica.
  skip_final_snapshot      = true
  copy_tags_to_snapshot    = true
  delete_automated_backups = false
  apply_immediately        = false
}
output "primary_address" { value = aws_db_instance.primary.address }
output "replica_address" { value = aws_db_instance.replica.address }
output "replica_identifier" { value = aws_db_instance.replica.identifier }
output "design" {
  value = {
    multi_az                    = aws_db_instance.primary.multi_az
    replica_multi_az            = aws_db_instance.replica.multi_az
    primary_public              = aws_db_instance.primary.publicly_accessible
    replica_public              = aws_db_instance.replica.publicly_accessible
    primary_encrypted           = aws_db_instance.primary.storage_encrypted
    replica_encrypted           = aws_db_instance.replica.storage_encrypted
    backup_days                 = aws_db_instance.primary.backup_retention_period
    secret_managed              = coalesce(aws_db_instance.primary.manage_master_user_password, false)
    primary_final_snapshot      = !aws_db_instance.primary.skip_final_snapshot
    replica_skip_final_snapshot = aws_db_instance.replica.skip_final_snapshot
    primary_deletion_protected  = aws_db_instance.primary.deletion_protection
    replica_deletion_protected  = aws_db_instance.replica.deletion_protection
    primary_subnet_group        = aws_db_instance.primary.db_subnet_group_name
    replica_subnet_group        = aws_db_instance.replica.db_subnet_group_name
  }
}
