terraform {
  required_version = ">= 1.13, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project    = var.name
      Assignment = "week06-a5"
      ManagedBy  = "Terraform"
      Lifecycle  = "temporary-lab"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ssm_parameter" "ubuntu" {
  name = "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "ha" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = var.name }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.ha.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.name}-public-${count.index + 1}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.ha.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = local.azs[count.index]
  tags              = { Name = "${var.name}-private-${count.index + 1}" }
}

resource "aws_internet_gateway" "ha" {
  vpc_id = aws_vpc.ha.id
}

resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "ha" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
  depends_on    = [aws_internet_gateway.ha]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.ha.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ha.id
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.ha.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.ha.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.name}-alb-"
  vpc_id      = aws_vpc.ha.id
}
resource "aws_security_group" "web" {
  name_prefix = "${var.name}-web-"
  vpc_id      = aws_vpc.ha.id
}
resource "aws_security_group" "db" {
  name_prefix = "${var.name}-db-"
  vpc_id      = aws_vpc.ha.id
}
resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.alb.id
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}
resource "aws_vpc_security_group_egress_rule" "alb_web" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.web.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}
resource "aws_vpc_security_group_ingress_rule" "web" {
  security_group_id            = aws_security_group.web.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}
resource "aws_vpc_security_group_ingress_rule" "ssh" {
  count             = var.ssh_cidr == null ? 0 : 1
  security_group_id = aws_security_group.web.id
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = var.ssh_cidr
}
resource "aws_vpc_security_group_ingress_rule" "db" {
  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = aws_security_group.web.id
  ip_protocol                  = "tcp"
  from_port                    = 3306
  to_port                      = 3306
}
resource "aws_vpc_security_group_egress_rule" "web_https" {
  security_group_id = aws_security_group.web.id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}
resource "aws_vpc_security_group_egress_rule" "web_http" {
  security_group_id = aws_security_group.web.id
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}
resource "aws_vpc_security_group_egress_rule" "web_db" {
  security_group_id            = aws_security_group.web.id
  referenced_security_group_id = aws_security_group.db.id
  ip_protocol                  = "tcp"
  from_port                    = 3306
  to_port                      = 3306
}

resource "aws_db_subnet_group" "ha" {
  name       = "${var.name}-private"
  subnet_ids = aws_subnet.private[*].id
}
resource "aws_db_parameter_group" "ha" {
  name_prefix = "${var.name}-"
  family      = "mysql8.4"
  parameter {
    name  = "require_secure_transport"
    value = "1"
  }
}
resource "aws_cloudwatch_log_group" "database" {
  name              = "/aws/rds/instance/${var.name}/error"
  retention_in_days = 1
}

resource "aws_db_instance" "ha" {
  identifier                      = var.name
  engine                          = "mysql"
  engine_version                  = "8.4"
  instance_class                  = "db.t3.micro"
  allocated_storage               = 20
  storage_type                    = "gp3"
  storage_encrypted               = true
  db_name                         = "epicbook"
  username                        = "dbadmin"
  manage_master_user_password     = true
  multi_az                        = true
  publicly_accessible             = false
  db_subnet_group_name            = aws_db_subnet_group.ha.name
  vpc_security_group_ids          = [aws_security_group.db.id]
  parameter_group_name            = aws_db_parameter_group.ha.name
  backup_retention_period         = 1
  auto_minor_version_upgrade      = true
  enabled_cloudwatch_logs_exports = ["error"]
  skip_final_snapshot             = true
  delete_automated_backups        = true
  deletion_protection             = false
  apply_immediately               = true
  depends_on                      = [aws_cloudwatch_log_group.database]
}

resource "aws_iam_role" "web" {
  name_prefix = "${var.name}-web-"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.web.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
resource "aws_iam_role_policy" "secret" {
  role = aws_iam_role.web.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow", Action = ["secretsmanager:GetSecretValue"],
      Resource = aws_db_instance.ha.master_user_secret[0].secret_arn
    }]
  })
}
resource "aws_iam_instance_profile" "web" {
  name_prefix = "${var.name}-"
  role        = aws_iam_role.web.name
}

resource "aws_lb" "ha" {
  name               = var.name
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}
resource "aws_lb_target_group" "web" {
  name                 = var.name
  port                 = 80
  protocol             = "HTTP"
  vpc_id               = aws_vpc.ha.id
  deregistration_delay = 15
  health_check {
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.ha.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}
resource "aws_launch_template" "web" {
  name_prefix   = "${var.name}-"
  image_id      = nonsensitive(data.aws_ssm_parameter.ubuntu.value)
  instance_type = "t3.micro"
  iam_instance_profile {
    name = aws_iam_instance_profile.web.name
  }
  vpc_security_group_ids = [aws_security_group.web.id]
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size           = 10
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }
  user_data = base64gzip(templatefile("${path.module}/bootstrap.sh.tftpl", {
    server_b64 = filebase64("${path.module}/../app/server.py")
    region     = var.region
    secret_arn = aws_db_instance.ha.master_user_secret[0].secret_arn
    db_host    = aws_db_instance.ha.address
  }))
  tag_specifications {
    resource_type = "instance"
    tags          = { Name = "${var.name}-web", Project = var.name, Assignment = "week06-a5" }
  }
}
resource "aws_autoscaling_group" "web" {
  name                      = var.name
  min_size                  = 2
  desired_capacity          = 2
  max_size                  = 4
  vpc_zone_identifier       = [for index in sort([for index in var.web_az_indexes : tostring(index)]) : aws_subnet.public[tonumber(index)].id]
  target_group_arns         = [aws_lb_target_group.web.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 600
  default_instance_warmup   = 120
  wait_for_capacity_timeout = "20m"
  min_elb_capacity          = 2
  launch_template {
    id      = aws_launch_template.web.id
    version = aws_launch_template.web.latest_version
  }
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 100
      max_healthy_percentage = 200
      instance_warmup        = 120
    }
  }
  tag {
    key                 = "Project"
    value               = var.name
    propagate_at_launch = true
  }
  depends_on = [aws_lb_listener.http, aws_route_table_association.public, aws_iam_role_policy.secret, aws_iam_role_policy_attachment.ssm]
}
