resource "terraform_data" "deployment_gate" {
  input = {
    account_id = data.aws_caller_identity.current.account_id
    vpc_id     = data.aws_vpc.existing.id
  }

  lifecycle {
    precondition {
      condition     = var.deployment_approved && var.runtime_verified
      error_message = "STOP: explicit scope/spending/cleanup approval and verified runtime readiness are required."
    }
    precondition {
      condition = (
        data.aws_caller_identity.current.account_id == var.expected_account_id &&
        can(regex("^arn:aws:(iam|sts)::[0-9]{12}:(user/|assumed-role/).+", data.aws_caller_identity.current.arn))
      )
      error_message = "STOP: use an approved non-root IAM user or assumed role in the expected account."
    }
    precondition {
      condition = (
        data.aws_vpc.existing.id == local.vpc_id && data.aws_vpc.existing.cidr_block == "10.0.0.0/16" &&
        data.aws_vpc.existing.enable_dns_support && data.aws_vpc.existing.enable_dns_hostnames &&
        alltrue([for subnet in merge(data.aws_subnet.public, { for key, subnet in data.aws_subnet.db : "db_${key}" => subnet }) : subnet.vpc_id == local.vpc_id]) &&
        alltrue([for group in data.aws_security_group.existing : group.vpc_id == local.vpc_id]) &&
        data.aws_db_subnet_group.existing.vpc_id == local.vpc_id
      )
      error_message = "STOP: the selected VPC, subnets, DB subnet group or security groups no longer match the verified capstone."
    }
    precondition {
      condition = (
        length(toset([for subnet in data.aws_subnet.public : subnet.availability_zone])) == 2 &&
        length(toset([for subnet in data.aws_subnet.db : subnet.availability_zone])) == 2 &&
        alltrue([for subnet in data.aws_subnet.public : subnet.available_ip_address_count >= 8]) &&
        toset(data.aws_db_subnet_group.existing.subnet_ids) == toset(values(local.db_subnets))
      )
      error_message = "STOP: require two AZs, at least eight free addresses per ALB subnet, and the two verified DB subnets."
    }
    precondition {
      condition = alltrue([
        for table in data.aws_route_table.public : table.vpc_id == local.vpc_id && anytrue([
          for route in table.routes : route.cidr_block == "0.0.0.0/0" && startswith(coalesce(route.gateway_id, "none"), "igw-")
        ])
      ])
      error_message = "STOP: both ALB subnets must retain an Internet Gateway default route in this VPC."
    }
    precondition {
      condition = alltrue([
        for table in data.aws_route_table.db : table.vpc_id == local.vpc_id && length(table.routes) > 0 && alltrue([
          for route in table.routes : route.gateway_id == "local" && route.cidr_block == data.aws_vpc.existing.cidr_block
        ])
      ])
      error_message = "STOP: DB subnets must retain only the verified VPC-local route."
    }
    precondition {
      condition = (
        data.aws_instance.web.instance_id == local.web_instance_id && data.aws_instance.web.instance_state == "running" &&
        contains(values(local.public_subnets), data.aws_instance.web.subnet_id) &&
        toset(data.aws_instance.web.vpc_security_group_ids) == toset([local.security_groups.web])
      )
      error_message = "STOP: the Web target must be the verified running instance in a Web subnet with only SG-Web attached."
    }
    precondition {
      condition = (
        data.aws_db_instance.primary.db_instance_identifier == "bookreview-db" &&
        can(regex(":db:bookreview-db$", data.aws_db_instance.primary.db_instance_arn)) &&
        data.aws_db_instance.primary.engine == "mysql" && data.aws_db_instance.primary.db_instance_port == 3306 &&
        data.aws_db_instance.primary.multi_az && !data.aws_db_instance.primary.publicly_accessible &&
        data.aws_db_instance.primary.storage_encrypted && data.aws_db_instance.primary.backup_retention_period >= 1 &&
        data.aws_db_instance.primary.allocated_storage == 20 && data.aws_db_instance.primary.storage_type == "gp2" &&
        toset(data.aws_db_instance.primary.vpc_security_groups) == toset([local.security_groups.db])
      )
      error_message = "STOP: require the private, encrypted, backed-up Multi-AZ Book Review primary and quoted 20 GiB gp2 storage; never substitute ha-mysql-db."
    }
    precondition {
      condition = anytrue([
        for rule in local.ingress_rules : rule.security_group_id == local.security_groups.public_alb &&
        rule.ip_protocol == "tcp" && rule.from_port == 80 && rule.to_port == 80 && rule.cidr_ipv4 == "0.0.0.0/0"
        ]) && anytrue([
        for rule in local.alb_egress_rules :
        (rule.ip_protocol == "-1" || (rule.ip_protocol == "tcp" && try(rule.from_port <= 80 && rule.to_port >= 80, false))) &&
        (rule.referenced_security_group_id == local.security_groups.web || rule.cidr_ipv4 == "0.0.0.0/0")
        ]) && anytrue([
        for rule in local.ingress_rules : rule.security_group_id == local.security_groups.web &&
        rule.ip_protocol == "tcp" && rule.from_port == 80 && rule.to_port == 80 &&
        rule.referenced_security_group_id == local.security_groups.public_alb
      ])
      error_message = "STOP: existing groups must allow Internet HTTP to the public ALB and ALB-to-Web HTTP; no existing rules will be changed."
    }
    precondition {
      condition = length(local.db_ingress_rules) > 0 && alltrue([
        for rule in local.db_ingress_rules : rule.ip_protocol == "tcp" && rule.from_port == 3306 && rule.to_port == 3306 &&
        rule.referenced_security_group_id == local.app_security_group_id &&
        coalesce(rule.cidr_ipv4, "none") == "none" && coalesce(rule.cidr_ipv6, "none") == "none"
      ])
      error_message = "STOP: DB ingress must remain MySQL from SG-App only."
    }
  }
}
