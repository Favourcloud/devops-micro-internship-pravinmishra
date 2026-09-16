resource "aws_lb" "public" {
  name                       = "dmi-a6-public-alb"
  internal                   = false
  load_balancer_type         = "application"
  ip_address_type            = "ipv4"
  security_groups            = [data.aws_security_group.existing["public_alb"].id]
  subnets                    = [for subnet in data.aws_subnet.public : subnet.id]
  drop_invalid_header_fields = true
  enable_deletion_protection = false
  depends_on                 = [terraform_data.deployment_gate]
}

resource "aws_lb_target_group" "web" {
  name                 = "dmi-a6-web"
  port                 = 80
  protocol             = "HTTP"
  target_type          = "instance"
  vpc_id               = data.aws_vpc.existing.id
  deregistration_delay = 30
  health_check {
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  depends_on = [terraform_data.deployment_gate]
}

resource "aws_lb_target_group_attachment" "web" {
  target_group_arn = aws_lb_target_group.web.arn
  target_id        = data.aws_instance.web.instance_id
  port             = 80
  depends_on       = [terraform_data.deployment_gate]
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.public.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
  depends_on = [terraform_data.deployment_gate]
}

resource "aws_db_instance" "replica" {
  identifier                 = "dmi-a6-read-replica"
  replicate_source_db        = data.aws_db_instance.primary.db_instance_arn
  instance_class             = "db.t4g.micro"
  db_subnet_group_name       = data.aws_db_subnet_group.existing.name
  vpc_security_group_ids     = [data.aws_security_group.existing["db"].id]
  publicly_accessible        = false
  storage_encrypted          = true
  storage_type               = "gp2"
  multi_az                   = false
  backup_retention_period    = 0
  deletion_protection        = false
  skip_final_snapshot        = true
  delete_automated_backups   = true
  copy_tags_to_snapshot      = true
  auto_minor_version_upgrade = true
  depends_on                 = [terraform_data.deployment_gate]
}
