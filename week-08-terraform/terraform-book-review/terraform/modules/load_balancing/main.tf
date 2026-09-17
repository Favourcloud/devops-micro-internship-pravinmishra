variable "name" { type = string }
variable "vpc_id" { type = string }
variable "web_subnets" { type = list(string) }
variable "app_subnets" { type = list(string) }
variable "security_groups" { type = map(string) }
variable "certificate_arn" { type = string }
variable "deletion_protection" { type = bool }
resource "aws_lb" "public" {
  name                       = "${var.name}-public"
  internal                   = false
  load_balancer_type         = "application"
  subnets                    = var.web_subnets
  security_groups            = [var.security_groups["public_lb"]]
  enable_deletion_protection = var.deletion_protection
  drop_invalid_header_fields = true
  desync_mitigation_mode     = "strictest"
  enable_http2               = true
}
resource "aws_lb" "internal" {
  name                       = "${var.name}-internal"
  internal                   = true
  load_balancer_type         = "application"
  subnets                    = var.app_subnets
  security_groups            = [var.security_groups["internal_lb"]]
  enable_deletion_protection = var.deletion_protection
  drop_invalid_header_fields = true
  desync_mitigation_mode     = "strictest"
}
resource "aws_lb_target_group" "web" {
  name_prefix          = "brweb-"
  port                 = 80
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  target_type          = "instance"
  deregistration_delay = 30
  health_check {
    path                = "/healthz"
    matcher             = "200"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  lifecycle { create_before_destroy = true }
}
resource "aws_lb_target_group" "app" {
  name_prefix          = "brapp-"
  port                 = 3001
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  target_type          = "instance"
  deregistration_delay = 30
  health_check {
    path                = "/api/books"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  lifecycle { create_before_destroy = true }
}
resource "aws_lb_listener" "public" {
  load_balancer_arn = aws_lb.public.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}
resource "aws_lb_listener" "internal" {
  load_balancer_arn = aws_lb.internal.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
output "web_target_group_arn" { value = aws_lb_target_group.web.arn }
output "app_target_group_arn" { value = aws_lb_target_group.app.arn }
output "internal_url" { value = "http://${aws_lb.internal.dns_name}" }
output "public_dns" { value = aws_lb.public.dns_name }
output "controls" {
  value = {
    public_port                 = aws_lb_listener.public.port
    public_protocol             = aws_lb_listener.public.protocol
    tls_policy                  = aws_lb_listener.public.ssl_policy
    certificate                 = aws_lb_listener.public.certificate_arn
    internal_private            = aws_lb.internal.internal
    public_health               = aws_lb_target_group.web.health_check[0].path
    app_health                  = aws_lb_target_group.app.health_check[0].path
    app_port                    = aws_lb_target_group.app.port
    public_deletion_protected   = aws_lb.public.enable_deletion_protection
    internal_deletion_protected = aws_lb.internal.enable_deletion_protection
  }
}
output "alarm_dimensions" {
  value = {
    web = { LoadBalancer = aws_lb.public.arn_suffix, TargetGroup = aws_lb_target_group.web.arn_suffix }
    app = { LoadBalancer = aws_lb.internal.arn_suffix, TargetGroup = aws_lb_target_group.app.arn_suffix }
  }
}
