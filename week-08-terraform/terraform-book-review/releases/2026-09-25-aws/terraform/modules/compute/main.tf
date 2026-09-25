variable "name" { type = string }
variable "tier" { type = string }
variable "ami_id" { type = string }
variable "instance_type" { type = string }
variable "subnets" { type = map(string) }
variable "security_group_id" { type = string }
variable "instance_profile" { type = string }
variable "target_group_arn" { type = string }
variable "user_data_base64" {
  type = string
  validation {
    condition     = floor(length(replace(var.user_data_base64, "=", "")) * 3 / 4) <= 16384
    error_message = "Compressed EC2 user data must be at most 16 KiB; split reviewed files per tier rather than loading unverified remote code."
  }
}
variable "tags" { type = map(string) }
resource "aws_launch_template" "this" {
  name_prefix            = "${var.name}-${var.tier}-"
  image_id               = var.ami_id
  instance_type          = var.instance_type
  user_data              = var.user_data_base64
  update_default_version = true
  iam_instance_profile { name = var.instance_profile }
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }
  network_interfaces {
    device_index                = 0
    associate_public_ip_address = var.tier == "web"
    security_groups             = [var.security_group_id]
    delete_on_termination       = true
  }
  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size           = 30
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }
  tag_specifications {
    resource_type = "instance"
    tags          = merge(var.tags, { Name = "${var.name}-${var.tier}", Tier = var.tier })
  }
  tag_specifications {
    resource_type = "volume"
    tags          = merge(var.tags, { Name = "${var.name}-${var.tier}", Tier = var.tier })
  }
  lifecycle { create_before_destroy = true }
}
resource "aws_autoscaling_group" "az" {
  for_each                  = var.subnets
  name                      = "${var.name}-${var.tier}-${each.key}"
  min_size                  = 1
  desired_capacity          = 1
  max_size                  = 2
  vpc_zone_identifier       = [each.value]
  target_group_arns         = [var.target_group_arn]
  health_check_type         = "ELB"
  health_check_grace_period = 1200
  default_instance_warmup   = 120
  wait_for_capacity_timeout = "0"
  launch_template {
    id      = aws_launch_template.this.id
    version = tostring(aws_launch_template.this.latest_version)
  }
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 100
      max_healthy_percentage = 200
      instance_warmup        = 120
    }
  }
  dynamic "tag" {
    for_each = merge(var.tags, { Name = "${var.name}-${var.tier}-${each.key}", Tier = var.tier })
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}
output "az_groups" { value = { for k, asg in aws_autoscaling_group.az : k => { min = asg.min_size, desired = asg.desired_capacity, max = asg.max_size, subnets = asg.vpc_zone_identifier } } }
output "metadata" { value = aws_launch_template.this.metadata_options }
output "controls" {
  value = {
    root_encrypted = one(one(aws_launch_template.this.block_device_mappings).ebs).encrypted
    root_type      = one(one(aws_launch_template.this.block_device_mappings).ebs).volume_type
    public_ip      = one(aws_launch_template.this.network_interfaces).associate_public_ip_address
    ssh_key        = aws_launch_template.this.key_name
    health_types   = [for group in aws_autoscaling_group.az : group.health_check_type]
  }
}
