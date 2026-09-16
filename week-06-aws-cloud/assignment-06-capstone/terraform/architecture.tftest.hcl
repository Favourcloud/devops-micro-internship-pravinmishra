# All identities, rule IDs and ARNs below are synthetic. No AWS credentials are used.
# Overrides replace mock defaults, so each override repeats all guarded fields.
mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "000000000000"
      arn        = "arn:aws:sts::000000000000:assumed-role/approved-lab/operator"
    }
  }
  mock_data "aws_vpc" {
    defaults = {
      cidr_block           = "10.0.0.0/16"
      enable_dns_support   = true
      enable_dns_hostnames = true
    }
  }
  mock_data "aws_instance" {
    defaults = {
      instance_state         = "running"
      subnet_id              = "subnet-085c9fb75f5d16407"
      vpc_security_group_ids = ["sg-0a9531b6f952ed1b5"]
    }
  }
  mock_data "aws_subnet" {
    defaults = {
      vpc_id                     = "vpc-0f7b4a0baa38141ca"
      availability_zone          = "eu-north-1a"
      available_ip_address_count = 200
    }
  }
  mock_data "aws_security_group" {
    defaults = {
      vpc_id = "vpc-0f7b4a0baa38141ca"
    }
  }
  mock_data "aws_route_table" {
    defaults = {
      vpc_id = "vpc-0f7b4a0baa38141ca"
      routes = [{ cidr_block = "10.0.0.0/16", gateway_id = "local" }]
    }
  }
  mock_data "aws_db_subnet_group" {
    defaults = {
      vpc_id     = "vpc-0f7b4a0baa38141ca"
      subnet_ids = ["subnet-00af54f1fe19dbc07", "subnet-0b89716b6b5981b85"]
    }
  }
  mock_data "aws_db_instance" {
    defaults = {
      db_instance_arn         = "arn:aws:rds:eu-north-1:000000000000:db:bookreview-db"
      db_subnet_group         = "bookreview-db-subnets"
      engine                  = "mysql"
      db_instance_port        = 3306
      multi_az                = true
      publicly_accessible     = false
      storage_encrypted       = true
      backup_retention_period = 1
      allocated_storage       = 20
      storage_type            = "gp2"
      vpc_security_groups     = ["sg-07c71b323797c692f"]
    }
  }
  mock_data "aws_vpc_security_group_rule" {
    defaults = {
      is_egress                    = false
      ip_protocol                  = "tcp"
      from_port                    = 80
      to_port                      = 80
      cidr_ipv4                    = ""
      cidr_ipv6                    = ""
      referenced_security_group_id = ""
    }
  }
}

variables {
  expected_account_id = "000000000000"
  deployment_approved = true
  runtime_verified    = true
}

override_data {
  target = data.aws_subnet.public["b"]
  values = { availability_zone = "eu-north-1b"
    vpc_id                     = "vpc-0f7b4a0baa38141ca"
    available_ip_address_count = 200
  }
}
override_data {
  target = data.aws_subnet.db["b"]
  values = { availability_zone = "eu-north-1b"
    vpc_id                     = "vpc-0f7b4a0baa38141ca"
    available_ip_address_count = 200
  }
}
override_data {
  target = data.aws_route_table.public["a"]
  values = { routes = [{ cidr_block = "0.0.0.0/0", gateway_id = "igw-synthetic" }]
    vpc_id = "vpc-0f7b4a0baa38141ca"
  }
}
override_data {
  target = data.aws_route_table.public["b"]
  values = { routes = [{ cidr_block = "0.0.0.0/0", gateway_id = "igw-synthetic" }]
    vpc_id = "vpc-0f7b4a0baa38141ca"
  }
}
override_data {
  target = data.aws_vpc_security_group_rules.existing["public_alb"]
  values = { ids = ["sgr-00000000000000001", "sgr-00000000000000002"] }
}
override_data {
  target = data.aws_vpc_security_group_rules.existing["web"]
  values = { ids = ["sgr-00000000000000003"] }
}
override_data {
  target = data.aws_vpc_security_group_rules.existing["db"]
  values = { ids = ["sgr-00000000000000004"] }
}
override_data {
  target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000001"]
  values = { security_group_id = "sg-04ec165a8f60d0229", cidr_ipv4 = "0.0.0.0/0"
    is_egress                    = false
    ip_protocol                  = "tcp"
    from_port                    = 80
    to_port                      = 80
    cidr_ipv6                    = ""
    referenced_security_group_id = ""
  }
}
override_data {
  target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000002"]
  values = { security_group_id = "sg-04ec165a8f60d0229", is_egress = true, ip_protocol = "-1", cidr_ipv4 = "0.0.0.0/0"
    from_port                    = 80
    to_port                      = 80
    cidr_ipv6                    = ""
    referenced_security_group_id = ""
  }
}
override_data {
  target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000003"]
  values = { security_group_id = "sg-0a9531b6f952ed1b5", referenced_security_group_id = "sg-04ec165a8f60d0229"
    is_egress   = false
    ip_protocol = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_ipv4   = ""
    cidr_ipv6   = ""
  }
}
override_data {
  target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000004"]
  values = {
    security_group_id            = "sg-07c71b323797c692f"
    referenced_security_group_id = "sg-0a9a60173ae231c71"
    from_port                    = 3306
    to_port                      = 3306

    is_egress   = false
    ip_protocol = "tcp"
    cidr_ipv4   = ""
    cidr_ipv6   = ""
  }
}

run "approved_additions_only" {
  command = plan
  assert {
    condition = (
      !aws_lb.public.internal && aws_lb.public.ip_address_type == "ipv4" &&
      toset(aws_lb.public.subnets) == toset(values(local.public_subnets)) &&
      toset(aws_lb.public.security_groups) == toset([local.security_groups.public_alb]) &&
      aws_lb_listener.http.port == 80 && aws_lb_listener.http.protocol == "HTTP" &&
      aws_lb_target_group.web.port == 80 && aws_lb_target_group.web.health_check[0].path == "/" &&
      aws_lb_target_group_attachment.web.target_id == local.web_instance_id
    )
    error_message = "The public ALB must reuse verified Web subnets, SG and HTTP target without changing existing infrastructure."
  }
  assert {
    condition = (
      aws_db_instance.replica.identifier == "dmi-a6-read-replica" &&
      aws_db_instance.replica.replicate_source_db == data.aws_db_instance.primary.db_instance_arn &&
      !aws_db_instance.replica.publicly_accessible && aws_db_instance.replica.storage_encrypted &&
      !aws_db_instance.replica.multi_az && aws_db_instance.replica.instance_class == "db.t4g.micro" &&
      aws_db_instance.replica.storage_type == "gp2" && aws_db_instance.replica.password == null &&
      aws_db_instance.replica.db_subnet_group_name == data.aws_db_subnet_group.existing.name &&
      toset(aws_db_instance.replica.vpc_security_group_ids) == toset([local.security_groups.db])
    )
    error_message = "The only DB addition must be a private encrypted Single-AZ replica of the Book Review primary, with no supplied password."
  }
}

run "reject_unapproved_defaults" {
  command = plan
  variables {
    deployment_approved = false
    runtime_verified    = false
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_missing_approval" {
  command = plan
  variables { deployment_approved = false }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_unverified_runtime" {
  command = plan
  variables { runtime_verified = false }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_unset_account" {
  command = plan
  variables { expected_account_id = "" }
  expect_failures = [var.expected_account_id]
}
run "reject_root" {
  command = plan
  override_data {
    target = data.aws_caller_identity.current
    values = { arn = "arn:aws:iam::000000000000:root"
      account_id = "000000000000"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_wrong_account" {
  command = plan
  override_data {
    target = data.aws_caller_identity.current
    values = { account_id = "111111111111"
      arn = "arn:aws:sts::000000000000:assumed-role/approved-lab/operator"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_wrong_vpc" {
  command = plan
  override_data {
    target = data.aws_subnet.public["a"]
    values = { vpc_id = "vpc-00000000000000000"
      availability_zone          = "eu-north-1a"
      available_ip_address_count = 200
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_wrong_db_group_vpc" {
  command = plan
  override_data {
    target = data.aws_db_subnet_group.existing
    values = { vpc_id = "vpc-00000000000000000"
      subnet_ids = ["subnet-00af54f1fe19dbc07", "subnet-0b89716b6b5981b85"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_single_az_alb" {
  command = plan
  override_data {
    target = data.aws_subnet.public["b"]
    values = { availability_zone = "eu-north-1a"
      vpc_id                     = "vpc-0f7b4a0baa38141ca"
      available_ip_address_count = 200
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_single_az_db_subnets" {
  command = plan
  override_data {
    target = data.aws_subnet.db["b"]
    values = { availability_zone = "eu-north-1a"
      vpc_id                     = "vpc-0f7b4a0baa38141ca"
      available_ip_address_count = 200
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_exhausted_alb_subnet" {
  command = plan
  override_data {
    target = data.aws_subnet.public["a"]
    values = { available_ip_address_count = 7
      vpc_id            = "vpc-0f7b4a0baa38141ca"
      availability_zone = "eu-north-1a"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_nonpublic_alb_route" {
  command = plan
  override_data {
    target = data.aws_route_table.public["a"]
    values = { routes = [{ cidr_block = "0.0.0.0/0", nat_gateway_id = "nat-synthetic", gateway_id = "" }]
      vpc_id = "vpc-0f7b4a0baa38141ca"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_db_internet_route" {
  command = plan
  override_data {
    target = data.aws_route_table.db["a"]
    values = { routes = [{ cidr_block = "0.0.0.0/0", gateway_id = "igw-synthetic" }]
      vpc_id = "vpc-0f7b4a0baa38141ca"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_stopped_web" {
  command = plan
  override_data {
    target = data.aws_instance.web
    values = { instance_state = "stopped"
      subnet_id              = "subnet-085c9fb75f5d16407"
      vpc_security_group_ids = ["sg-0a9531b6f952ed1b5"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_extra_web_group" {
  command = plan
  override_data {
    target = data.aws_instance.web
    values = { vpc_security_group_ids = ["sg-0a9531b6f952ed1b5", "sg-00000000000000000"]
      instance_state = "running"
      subnet_id      = "subnet-085c9fb75f5d16407"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_unrelated_primary" {
  command = plan
  override_data {
    target = data.aws_db_instance.primary
    values = { db_instance_arn = "arn:aws:rds:eu-north-1:000000000000:db:ha-mysql-db"
      db_subnet_group         = "bookreview-db-subnets"
      engine                  = "mysql"
      db_instance_port        = 3306
      multi_az                = true
      publicly_accessible     = false
      storage_encrypted       = true
      backup_retention_period = 1
      allocated_storage       = 20
      storage_type            = "gp2"
      vpc_security_groups     = ["sg-07c71b323797c692f"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_public_primary" {
  command = plan
  override_data {
    target = data.aws_db_instance.primary
    values = { publicly_accessible = true
      db_instance_arn         = "arn:aws:rds:eu-north-1:000000000000:db:bookreview-db"
      db_subnet_group         = "bookreview-db-subnets"
      engine                  = "mysql"
      db_instance_port        = 3306
      multi_az                = true
      storage_encrypted       = true
      backup_retention_period = 1
      allocated_storage       = 20
      storage_type            = "gp2"
      vpc_security_groups     = ["sg-07c71b323797c692f"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_unencrypted_primary" {
  command = plan
  override_data {
    target = data.aws_db_instance.primary
    values = { storage_encrypted = false
      db_instance_arn         = "arn:aws:rds:eu-north-1:000000000000:db:bookreview-db"
      db_subnet_group         = "bookreview-db-subnets"
      engine                  = "mysql"
      db_instance_port        = 3306
      multi_az                = true
      publicly_accessible     = false
      backup_retention_period = 1
      allocated_storage       = 20
      storage_type            = "gp2"
      vpc_security_groups     = ["sg-07c71b323797c692f"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_missing_multi_az" {
  command = plan
  override_data {
    target = data.aws_db_instance.primary
    values = { multi_az = false
      db_instance_arn         = "arn:aws:rds:eu-north-1:000000000000:db:bookreview-db"
      db_subnet_group         = "bookreview-db-subnets"
      engine                  = "mysql"
      db_instance_port        = 3306
      publicly_accessible     = false
      storage_encrypted       = true
      backup_retention_period = 1
      allocated_storage       = 20
      storage_type            = "gp2"
      vpc_security_groups     = ["sg-07c71b323797c692f"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_missing_backups" {
  command = plan
  override_data {
    target = data.aws_db_instance.primary
    values = { backup_retention_period = 0
      db_instance_arn     = "arn:aws:rds:eu-north-1:000000000000:db:bookreview-db"
      db_subnet_group     = "bookreview-db-subnets"
      engine              = "mysql"
      db_instance_port    = 3306
      multi_az            = true
      publicly_accessible = false
      storage_encrypted   = true
      allocated_storage   = 20
      storage_type        = "gp2"
      vpc_security_groups = ["sg-07c71b323797c692f"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_changed_cost_basis" {
  command = plan
  override_data {
    target = data.aws_db_instance.primary
    values = { allocated_storage = 100
      db_instance_arn         = "arn:aws:rds:eu-north-1:000000000000:db:bookreview-db"
      db_subnet_group         = "bookreview-db-subnets"
      engine                  = "mysql"
      db_instance_port        = 3306
      multi_az                = true
      publicly_accessible     = false
      storage_encrypted       = true
      backup_retention_period = 1
      storage_type            = "gp2"
      vpc_security_groups     = ["sg-07c71b323797c692f"]
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_unexpected_db_subnet" {
  command = plan
  override_data {
    target = data.aws_db_subnet_group.existing
    values = { subnet_ids = ["subnet-00af54f1fe19dbc07", "subnet-00000000000000000"]
      vpc_id = "vpc-0f7b4a0baa38141ca"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_missing_public_http" {
  command = plan
  override_data {
    target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000001"]
    values = { security_group_id = "sg-04ec165a8f60d0229", from_port = 443, to_port = 443, cidr_ipv4 = "0.0.0.0/0"
      is_egress                    = false
      ip_protocol                  = "tcp"
      cidr_ipv6                    = ""
      referenced_security_group_id = ""
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_wrong_web_source" {
  command = plan
  override_data {
    target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000003"]
    values = { security_group_id = "sg-0a9531b6f952ed1b5", referenced_security_group_id = "sg-00000000000000000"
      is_egress   = false
      ip_protocol = "tcp"
      from_port   = 80
      to_port     = 80
      cidr_ipv4   = ""
      cidr_ipv6   = ""
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
run "reject_open_db_ingress" {
  command = plan
  override_data {
    target = data.aws_vpc_security_group_rule.existing["sgr-00000000000000004"]
    values = { security_group_id = "sg-07c71b323797c692f", from_port = 3306, to_port = 3306, cidr_ipv4 = "0.0.0.0/0"
      is_egress                    = false
      ip_protocol                  = "tcp"
      cidr_ipv6                    = ""
      referenced_security_group_id = "sg-0a9a60173ae231c71"
    }
  }
  expect_failures = [terraform_data.deployment_gate]
}
