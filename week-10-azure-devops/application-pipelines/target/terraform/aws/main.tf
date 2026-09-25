terraform {
  required_version = "~> 1.13.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "local" {
    path = ".private/terraform.tfstate"
  }
}

provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.account_id]
  default_tags {
    tags = module.guard.tags
  }
}

module "guard" {
  source               = "../guard"
  assignment           = "week10-a2"
  name_prefix          = var.name_prefix
  controller_ipv4_cidr = var.controller_ipv4_cidr
  agent_ipv4_cidr      = var.agent_ipv4_cidr
  approval             = var.approval
}

data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  owners = ["099720109477"]
  filter {
    name   = "image-id"
    values = [var.ami_id]
  }
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_vpc" "target" {
  cidr_block           = "10.120.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name_prefix}-vpc" }
  depends_on           = [module.guard]
  lifecycle {
    precondition {
      condition = (
        data.aws_caller_identity.current.account_id == var.account_id &&
        data.aws_caller_identity.current.arn == var.operator_arn &&
        (!endswith(data.aws_caller_identity.current.arn, ":root") || var.allow_root_operator)
      )
      error_message = "The active principal must exactly match the approved identity; root requires an explicit opt-in for local provisioning."
    }
  }
}

resource "aws_subnet" "target" {
  availability_zone       = var.availability_zone
  vpc_id                  = aws_vpc.target.id
  cidr_block              = "10.120.1.0/24"
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.name_prefix}-subnet" }
}

resource "aws_internet_gateway" "target" {
  vpc_id = aws_vpc.target.id
  tags   = { Name = "${var.name_prefix}-igw" }
}

resource "aws_route_table" "target" {
  vpc_id = aws_vpc.target.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.target.id
  }
  tags = { Name = "${var.name_prefix}-routes" }
}

resource "aws_route_table_association" "target" {
  subnet_id      = aws_subnet.target.id
  route_table_id = aws_route_table.target.id
}

resource "aws_security_group" "target" {
  name_prefix = "${var.name_prefix}-web-"
  description = "Dedicated A2 HTTP target with operator and agent SSH only"
  vpc_id      = aws_vpc.target.id
  ingress {
    description = "SSH from reviewed controller and agent"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = module.guard.ssh_cidrs
  }
  ingress {
    description = "Non-sensitive lab HTTP"
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Ubuntu HTTP package repositories"
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Ubuntu HTTPS package repositories"
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.name_prefix}-web" }
}

resource "aws_key_pair" "operator" {
  key_name_prefix = "${var.name_prefix}-"
  public_key      = var.operator_public_key
  depends_on      = [aws_vpc.target]
}

resource "aws_instance" "target" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.target.id
  vpc_security_group_ids      = [aws_security_group.target.id]
  associate_public_ip_address = true
  key_name                    = aws_key_pair.operator.key_name
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }
  root_block_device {
    encrypted             = true
    volume_type           = "gp3"
    volume_size           = 8
    delete_on_termination = true
  }
  credit_specification {
    cpu_credits = "standard"
  }
  tags       = { Name = "${var.name_prefix}-vm" }
  depends_on = [aws_route_table_association.target]
}

output "target_public_ipv4" {
  value     = aws_instance.target.public_ip
  sensitive = true
}

output "target_resource_id" {
  value = aws_instance.target.id
}

output "vpc_id" {
  value = aws_vpc.target.id
}

output "ssh_username" {
  value = "ubuntu"
}

output "assignment" {
  value = "week10-a2"
}
