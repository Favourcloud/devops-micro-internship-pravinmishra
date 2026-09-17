variable "name" { type = string }
variable "vpc_id" { type = string }
locals {
  links = {
    web         = { source = "public_lb", destination = "web", port = 80 }
    internal_lb = { source = "web", destination = "internal_lb", port = 80 }
    app         = { source = "internal_lb", destination = "app", port = 3001 }
    db          = { source = "app", destination = "db", port = 3306 }
  }
}
resource "aws_security_group" "tier" {
  for_each    = toset(["public_lb", "web", "internal_lb", "app", "db"])
  name_prefix = "${var.name}-${each.key}-"
  description = "Book Review ${each.key}; no default egress or SSH"
  vpc_id      = var.vpc_id
  tags        = { Name = "${var.name}-${each.key}" }
  lifecycle { create_before_destroy = true }
}
resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.tier["public_lb"].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS only; no HTTP credential endpoint"
}
resource "aws_vpc_security_group_ingress_rule" "chain" {
  for_each                     = local.links
  security_group_id            = aws_security_group.tier[each.value.destination].id
  referenced_security_group_id = aws_security_group.tier[each.value.source].id
  ip_protocol                  = "tcp"
  from_port                    = each.value.port
  to_port                      = each.value.port
}
resource "aws_vpc_security_group_egress_rule" "chain" {
  for_each                     = local.links
  security_group_id            = aws_security_group.tier[each.value.source].id
  referenced_security_group_id = aws_security_group.tier[each.value.destination].id
  ip_protocol                  = "tcp"
  from_port                    = each.value.port
  to_port                      = each.value.port
}
resource "aws_vpc_security_group_egress_rule" "https" {
  for_each          = toset(["web", "app"])
  security_group_id = aws_security_group.tier[each.key].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS package/artifact and SSM/Secrets endpoints; same-AZ NAT for App"
}
output "ids" { value = { for k, sg in aws_security_group.tier : k => sg.id } }
output "chain" { value = local.links }
