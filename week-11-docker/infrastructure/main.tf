terraform {
  required_version = ">= 1.13, < 2.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = { Project = "DMI-Week11", Owner = "Eze Favour", ManagedBy = "Terraform" }
  }
}
variable "ami_id" { type = string }
variable "key_name" { type = string }
variable "operator_cidr" {
  type = string
  validation {
    condition     = can(cidrhost(var.operator_cidr, 0)) && endswith(var.operator_cidr, "/32")
    error_message = "SSH must be limited to the operator's IPv4 /32."
  }
}
resource "aws_vpc" "lab" {
  cidr_block           = "10.211.0.0/16"
  enable_dns_hostnames = true
  tags                 = { Name = "eze-week11" }
}
resource "aws_internet_gateway" "lab" { vpc_id = aws_vpc.lab.id }
resource "aws_subnet" "lab" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.211.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}
resource "aws_route_table" "lab" {
  vpc_id = aws_vpc.lab.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab.id
  }
}
resource "aws_route_table_association" "lab" {
  subnet_id      = aws_subnet.lab.id
  route_table_id = aws_route_table.lab.id
}
resource "aws_security_group" "lab" {
  name_prefix = "eze-week11-"
  vpc_id      = aws_vpc.lab.id
  ingress {
    description = "Operator SSH only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.operator_cidr]
  }
  dynamic "ingress" {
    for_each = [80, 443]
    content {
      description = "Public web"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
  ingress {
    description = "Operator-only single-stage React comparison"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.operator_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_instance" "docker" {
  for_each                    = toset(["labs", "epicbook"])
  ami                         = var.ami_id
  instance_type               = "t3.medium"
  subnet_id                   = aws_subnet.lab.id
  vpc_security_group_ids      = [aws_security_group.lab.id]
  key_name                    = var.key_name
  user_data                   = file("${path.module}/cloud-init.sh")
  user_data_replace_on_change = true
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
  root_block_device {
    volume_size           = 40
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  credit_specification { cpu_credits = "standard" }
  tags       = { Name = "eze-week11-${each.key}" }
  depends_on = [aws_route_table_association.lab]
}
resource "aws_eip" "docker" {
  for_each = aws_instance.docker
  domain   = "vpc"
  instance = each.value.id
  tags     = { Name = "eze-week11-${each.key}" }
}
output "public_ips" { value = { for name, ip in aws_eip.docker : name => ip.public_ip } }
output "instance_ids" { value = { for name, vm in aws_instance.docker : name => vm.id } }
