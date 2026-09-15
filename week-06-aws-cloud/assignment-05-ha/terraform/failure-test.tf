# ASG instances are dynamically owned by the ASG rather than aws_instance resources.
# This opt-in, guarded fault action runs only from Terraform, never on destroy.
resource "terraform_data" "replacement_run" {
  count            = var.replacement_test ? 1 : 0
  triggers_replace = var.replacement_instance_id
  lifecycle {
    precondition {
      condition     = var.replacement_instance_id != null
      error_message = "Specify the exact lab ASG instance ID for the opt-in termination test."
    }
  }
  provisioner "local-exec" {
    command = "python3 ../scripts/run-experiment.py"
    environment = {
      AWS_REGION  = var.region
      INSTANCE_ID = var.replacement_instance_id
      LAB_VPC     = aws_vpc.ha.id
      LAB_NAME    = var.name
      LAB_ASG     = aws_autoscaling_group.web.name
    }
  }
  depends_on = [aws_autoscaling_group.web]
}
