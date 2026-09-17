data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's public image publisher, not the learner account.
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}
resource "aws_iam_role" "runtime" {
  name_prefix = "${var.project_name}-runtime-"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "secret" {
  name = "read-only-this-lab-secret"
  role = aws_iam_role.runtime.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = var.runtime_secret_arn }]
  })
}
resource "aws_iam_instance_profile" "runtime" {
  name_prefix = "${var.project_name}-"
  role        = aws_iam_role.runtime.name
}
resource "aws_instance" "this" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = true
  key_name                    = var.key_name
  iam_instance_profile        = aws_iam_instance_profile.runtime.name
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/user_data.sh", {
    runtime_config = jsonencode({ region = var.aws_region, host = var.db_host, secret_arn = var.runtime_secret_arn, credential_version = var.credential_version })
    runtime_py     = file("${path.module}/runtime.py")
  })
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }
  root_block_device {
    volume_size           = 12
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  credit_specification { cpu_credits = "standard" }
  tags       = { Name = "${var.project_name}-web" }
  depends_on = [aws_iam_role_policy.secret]
}
