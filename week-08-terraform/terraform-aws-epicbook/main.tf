terraform {
  required_version = "~> 1.13.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.64.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project    = var.project_name
      Assignment = "week08-a4"
      ManagedBy  = "Terraform"
    }
  }
}

module "network" {
  source          = "./modules/network"
  project_name    = var.project_name
  azs             = var.availability_zones
  controller_cidr = var.controller_cidr
}

module "rds" {
  source               = "./modules/rds"
  project_name         = var.project_name
  private_subnet_ids   = module.network.private_subnet_ids
  security_group_id    = module.network.rds_security_group_id
  db_username          = var.db_username
  db_password          = var.db_password
  credential_version   = var.credential_version
  instance_class       = var.db_instance_class
  engine_version       = var.mysql_version
  accept_lab_data_loss = var.accept_lab_data_loss
}

resource "aws_secretsmanager_secret" "database" {
  name_prefix             = "${var.project_name}-database-"
  description             = "Short-lived EpicBook lab runtime database credentials"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id                = aws_secretsmanager_secret.database.id
  secret_string_wo         = jsonencode({ username = var.db_username, password = var.db_password })
  secret_string_wo_version = var.credential_version
  depends_on               = [module.rds]
}

module "ec2" {
  source             = "./modules/ec2"
  project_name       = var.project_name
  aws_region         = var.aws_region
  subnet_id          = module.network.public_subnet_id
  security_group_id  = module.network.ec2_security_group_id
  instance_type      = var.ec2_instance_type
  key_name           = var.key_name
  db_host            = module.rds.address
  runtime_secret_arn = aws_secretsmanager_secret.database.arn
  credential_version = var.credential_version
  depends_on         = [module.network, aws_secretsmanager_secret_version.database]
}
