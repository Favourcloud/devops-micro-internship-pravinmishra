terraform {
  required_version = "~> 1.13.0"

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

variable "aws_region" {
  description = "Explicit commercial AWS Region approved for this lab; no default or free-tier assumption."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^(af|ap|ca|eu|il|me|mx|sa|us)-(central|north|northeast|northwest|south|southeast|southwest|east|west)-[1-9][0-9]*$", var.aws_region))
    error_message = "Use a commercial AWS Region name, such as eu-west-2; confirm actual availability and approval separately."
  }
}

variable "ssh_cidr" {
  description = "Controller's current public IPv4 address as one /32. Documentation addresses are for mocks only."
  type        = string
  nullable    = false

  validation {
    condition = (
      can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/32$", var.ssh_cidr)) &&
      try(cidrhost(var.ssh_cidr, 0) == trimsuffix(var.ssh_cidr, "/32"), false) &&
      try(
        !contains(["0", "10", "127"], split(".", var.ssh_cidr)[0]) &&
        tonumber(split(".", var.ssh_cidr)[0]) < 224 &&
        !startswith(var.ssh_cidr, "169.254.") &&
        !startswith(var.ssh_cidr, "192.168.") &&
        !(split(".", var.ssh_cidr)[0] == "172" && tonumber(split(".", var.ssh_cidr)[1]) >= 16 && tonumber(split(".", var.ssh_cidr)[1]) <= 31) &&
        !(split(".", var.ssh_cidr)[0] == "100" && tonumber(split(".", var.ssh_cidr)[1]) >= 64 && tonumber(split(".", var.ssh_cidr)[1]) <= 127),
        false
      )
    )
    error_message = "SSH requires one valid public IPv4 /32; private, shared, loopback, link-local, multicast and world-open ranges are rejected."
  }
}

variable "ssh_public_key" {
  description = "Existing single-line OpenSSH Ed25519 PUBLIC key only; keep its matching private key outside this repository."
  type        = string
  sensitive   = true
  nullable    = false

  validation {
    condition     = can(regex("^ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI[A-Za-z0-9+/]{43}( [^\\r\\n]+)?$", var.ssh_public_key)) && !strcontains(var.ssh_public_key, "PRIVATE KEY")
    error_message = "Provide a single-line ssh-ed25519 public key, not a private key, a path, or another algorithm. Verify it with ssh-keygen -lf before a live run."
  }
}

variable "instance_type" {
  description = "Small x86_64 instance compatible with the Ubuntu AMI. Neither availability nor free-tier eligibility is guaranteed."
  type        = string
  default     = "t3.micro"
  nullable    = false

  validation {
    condition     = contains(["t3.micro", "t3.small"], var.instance_type)
    error_message = "Choose t3.micro or t3.small; ARM instance families are incompatible with this AMI."
  }
}

variable "name_prefix" {
  description = "Short lab label used in names and tags; no personal account identifiers."
  type        = string
  default     = "dmi-w08-a2"
  nullable    = false

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,31}$", var.name_prefix))
    error_message = "Use 3–32 lowercase letters, digits or hyphens, starting with a letter."
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.name_prefix
      ManagedBy = "Terraform"
      Learner   = "Eze Favour"
      Course    = "DMI-Week08-Assignment02"
    }
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  # Canonical's public image-publisher ID, not the learner's AWS account.
  owners = ["099720109477"]

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

resource "aws_vpc" "lab" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name_prefix}-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.name_prefix}-public" }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.name_prefix}-private" }
}

resource "aws_internet_gateway" "lab" {
  vpc_id = aws_vpc.lab.id
  tags   = { Name = "${var.name_prefix}-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lab.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab.id
  }
  tags = { Name = "${var.name_prefix}-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.lab.id
  # Explicitly manage an empty non-local route set; no IGW or NAT default route.
  route = []
  tags  = { Name = "${var.name_prefix}-private" }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "web" {
  name_prefix = "${var.name_prefix}-web-"
  description = "Nginx HTTP lab with controller-only SSH"
  vpc_id      = aws_vpc.lab.id

  ingress {
    description = "SSH from the approved controller IPv4 only"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [var.ssh_cidr]
  }
  ingress {
    description = "Public HTTP required by the assignment; no sensitive content"
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "HTTP Ubuntu package repositories"
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "HTTPS Ubuntu package repositories"
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.name_prefix}-web" }
}

resource "aws_key_pair" "lab" {
  key_name_prefix = "${var.name_prefix}-"
  public_key      = var.ssh_public_key
  tags            = { Name = "${var.name_prefix}-ssh" }
}

resource "aws_instance" "web" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  associate_public_ip_address = true
  key_name                    = aws_key_pair.lab.key_name
  user_data                   = file("${path.module}/scripts/cloud-init.sh")
  user_data_replace_on_change = true

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
  tags = { Name = "${var.name_prefix}-nginx" }

  # Bootstrap needs the public route in place, not merely a created subnet.
  depends_on = [aws_route_table_association.public]
}

output "public_ip" {
  description = "Ephemeral EC2 public IPv4; not evidence until a live authorized apply and verification."
  value       = aws_instance.web.public_ip
}

output "instance_id" {
  description = "Exact EC2 instance ID for targeted verification and cleanup."
  value       = aws_instance.web.id
}

output "website_url" {
  description = "Plain HTTP lab URL; do not submit credentials or personal data."
  value       = "http://${aws_instance.web.public_ip}"
}

output "ssh_username" {
  description = "Canonical Ubuntu SSH username; authenticate with the matching external private key."
  value       = "ubuntu"
}

output "ami_id" {
  description = "Resolved Canonical Ubuntu 24.04 x86_64 AMI; record it during plan review."
  value       = data.aws_ami.ubuntu.id
}
