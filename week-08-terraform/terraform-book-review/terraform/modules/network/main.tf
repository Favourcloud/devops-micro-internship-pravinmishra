variable "name" { type = string }
variable "vpc_cidr" { type = string }
variable "availability_zones" { type = list(string) }

locals {
  subnets = merge([
    for tier_index, tier in ["web", "app", "db"] : {
      for az_index, az in var.availability_zones : "${tier}-${az_index}" => {
        tier = tier
        az   = az
        slot = az_index
        cidr = cidrsubnet(var.vpc_cidr, 8, tier_index * 2 + az_index)
      }
    }
  ]...)
}
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = var.name }
}
resource "aws_default_security_group" "closed" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-default-closed" }
}
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = var.name }
}
resource "aws_subnet" "tier" {
  for_each                = local.subnets
  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.name}-${each.key}", Tier = each.value.tier }
}
resource "aws_eip" "nat" {
  for_each = { for i, az in var.availability_zones : tostring(i) => az }
  domain   = "vpc"
  tags     = { Name = "${var.name}-nat-${each.key}" }
}
resource "aws_nat_gateway" "az" {
  for_each      = aws_eip.nat
  allocation_id = each.value.id
  subnet_id     = aws_subnet.tier["web-${each.key}"].id
  depends_on    = [aws_internet_gateway.this]
  tags          = { Name = "${var.name}-nat-${each.key}" }
}
resource "aws_route_table" "tier" {
  for_each = local.subnets
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-${each.key}" }
}
resource "aws_route_table_association" "tier" {
  for_each       = local.subnets
  subnet_id      = aws_subnet.tier[each.key].id
  route_table_id = aws_route_table.tier[each.key].id
}
resource "aws_route" "web_internet" {
  for_each               = { for k, v in local.subnets : k => v if v.tier == "web" }
  route_table_id         = aws_route_table.tier[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}
resource "aws_route" "app_outbound" {
  for_each               = { for k, v in local.subnets : k => v if v.tier == "app" }
  route_table_id         = aws_route_table.tier[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.az[tostring(each.value.slot)].id
}
output "vpc_id" { value = aws_vpc.this.id }
output "web_subnets" { value = { for i, az in var.availability_zones : tostring(i) => aws_subnet.tier["web-${i}"].id } }
output "app_subnets" { value = { for i, az in var.availability_zones : tostring(i) => aws_subnet.tier["app-${i}"].id } }
output "db_subnets" { value = [for i, az in var.availability_zones : aws_subnet.tier["db-${i}"].id] }
output "design" {
  value = {
    subnet_count      = length(aws_subnet.tier)
    nat_count         = length(aws_nat_gateway.az)
    db_default_routes = 0
    routes            = { for k, v in local.subnets : k => v.tier == "web" ? "igw" : v.tier == "app" ? "nat-${v.slot}" : "local-only" }
    cidrs             = [for s in aws_subnet.tier : s.cidr_block]
  }
}
