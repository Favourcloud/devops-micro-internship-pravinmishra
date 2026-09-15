locals {
  vpc_id          = "vpc-0f7b4a0baa38141ca"
  web_instance_id = "i-09a4ad0db643b5f0a"
  public_subnets = {
    a = "subnet-085c9fb75f5d16407"
    b = "subnet-094b1c5c548c54e68"
  }
  db_subnets = {
    a = "subnet-00af54f1fe19dbc07"
    b = "subnet-0b89716b6b5981b85"
  }
  security_groups = {
    public_alb = "sg-04ec165a8f60d0229"
    web        = "sg-0a9531b6f952ed1b5"
    db         = "sg-07c71b323797c692f"
  }
  app_security_group_id = "sg-0a9a60173ae231c71"
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "existing" {
  id = local.vpc_id
}

data "aws_instance" "web" {
  instance_id   = local.web_instance_id
  get_user_data = false
}

data "aws_db_instance" "primary" {
  db_instance_identifier = "bookreview-db"
}

data "aws_db_subnet_group" "existing" {
  name = data.aws_db_instance.primary.db_subnet_group
}

data "aws_subnet" "public" {
  for_each = local.public_subnets
  id       = each.value
}

data "aws_subnet" "db" {
  for_each = local.db_subnets
  id       = each.value
}

data "aws_route_table" "public" {
  for_each  = local.public_subnets
  subnet_id = each.value
}

data "aws_route_table" "db" {
  for_each  = local.db_subnets
  subnet_id = each.value
}

data "aws_security_group" "existing" {
  for_each = local.security_groups
  id       = each.value
}

data "aws_vpc_security_group_rules" "existing" {
  for_each = local.security_groups
  filter {
    name   = "group-id"
    values = [each.value]
  }
}

data "aws_vpc_security_group_rule" "existing" {
  for_each               = toset(flatten([for group in data.aws_vpc_security_group_rules.existing : group.ids]))
  security_group_rule_id = each.value
}

locals {
  ingress_rules = [for rule in data.aws_vpc_security_group_rule.existing : rule if !rule.is_egress]
  alb_egress_rules = [
    for rule in data.aws_vpc_security_group_rule.existing : rule
    if rule.is_egress && rule.security_group_id == local.security_groups.public_alb
  ]
  db_ingress_rules = [for rule in local.ingress_rules : rule if rule.security_group_id == local.security_groups.db]
}
