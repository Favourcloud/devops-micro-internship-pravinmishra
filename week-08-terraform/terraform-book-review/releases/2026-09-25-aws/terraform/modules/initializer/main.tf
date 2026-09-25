variable "name" { type = string }
variable "ami_id" { type = string }
variable "instance_type" { type = string }
variable "subnet_id" { type = string }
variable "security_group_id" { type = string }
variable "instance_profile" { type = string }
variable "user_data_base64" {
  type = string
  validation {
    condition     = floor(length(replace(var.user_data_base64, "=", "")) * 3 / 4) <= 16384
    error_message = "Compressed initializer user data must be at most 16 KiB."
  }
}
resource "aws_instance" "this" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = false
  iam_instance_profile        = var.instance_profile
  user_data_base64            = var.user_data_base64
  user_data_replace_on_change = true
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    encrypted             = true
    delete_on_termination = true
  }
  tags = { Name = "${var.name}-initializer", Tier = "app", Role = "initializer" }
}
output "id" { value = aws_instance.this.id }
