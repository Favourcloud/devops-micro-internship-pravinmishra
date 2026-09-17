resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-db"
  subnet_ids = var.private_subnet_ids
}
resource "aws_db_parameter_group" "this" {
  name_prefix = "${var.project_name}-"
  family      = "mysql8.4"
  parameter {
    name  = "require_secure_transport"
    value = "ON"
  }
}
resource "aws_db_instance" "this" {
  identifier                  = "${var.project_name}-db"
  engine                      = "mysql"
  engine_version              = var.engine_version
  instance_class              = var.instance_class
  allocated_storage           = 20
  storage_type                = "gp3"
  storage_encrypted           = true
  db_name                     = "bookstore"
  username                    = var.db_username
  password_wo                 = var.db_password
  password_wo_version         = var.credential_version
  port                        = 3306
  db_subnet_group_name        = aws_db_subnet_group.this.name
  parameter_group_name        = aws_db_parameter_group.this.name
  vpc_security_group_ids      = [var.security_group_id]
  publicly_accessible         = false
  multi_az                    = false
  backup_retention_period     = 0
  skip_final_snapshot         = var.accept_lab_data_loss
  delete_automated_backups    = true
  deletion_protection         = false
  auto_minor_version_upgrade  = true
  allow_major_version_upgrade = false
  apply_immediately           = true
  copy_tags_to_snapshot       = true
}
