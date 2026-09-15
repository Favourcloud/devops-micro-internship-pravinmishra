# Every run must stay plan-only: mocked AWS does not disable terraform_data local-exec.
mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }
  mock_data "aws_ssm_parameter" {
    defaults = {
      value = "ami-0123456789abcdef0"
    }
  }
}

override_resource {
  target          = aws_subnet.public[0]
  override_during = plan
  values = {
    id = "subnet-0123456789abcdef0"
  }
}

override_resource {
  target          = aws_subnet.public[1]
  override_during = plan
  values = {
    id = "subnet-0123456789abcdef1"
  }
}

run "baseline_architecture" {
  command = plan

  assert {
    condition     = length(aws_subnet.public) == 2 && length(aws_subnet.private) == 2
    error_message = "The lab must have exactly two public and two private subnets."
  }
  assert {
    condition     = aws_subnet.private[0].availability_zone != aws_subnet.private[1].availability_zone && aws_subnet.public[0].availability_zone != aws_subnet.public[1].availability_zone
    error_message = "Each tier must span two AZs."
  }
  assert {
    condition     = aws_db_instance.ha.multi_az && !aws_db_instance.ha.publicly_accessible && aws_db_instance.ha.storage_encrypted && aws_db_instance.ha.manage_master_user_password
    error_message = "RDS must be Multi-AZ, private, encrypted and use an AWS-managed password."
  }
  assert {
    condition     = aws_autoscaling_group.web.min_size == 2 && aws_autoscaling_group.web.desired_capacity == 2 && aws_autoscaling_group.web.max_size == 4
    error_message = "ASG capacity must remain 2/2/4."
  }
  assert {
    condition     = aws_launch_template.web.metadata_options[0].http_tokens == "required"
    error_message = "Instances must require IMDSv2."
  }
  assert {
    condition     = length(aws_vpc_security_group_ingress_rule.ssh) == 0 && length(terraform_data.replacement_run) == 0
    error_message = "SSH and destructive fault injection must be disabled by default."
  }
}

run "reject_public_ssh" {
  command = plan
  variables {
    ssh_cidr = "0.0.0.0/0"
  }
  expect_failures = [var.ssh_cidr]
}

run "reject_empty_web_tier" {
  command = plan
  variables {
    web_az_indexes = []
  }
  expect_failures = [var.web_az_indexes]
}

run "reject_unspecified_termination_target" {
  command = plan
  variables {
    replacement_test          = true
    replacement_evidence_path = "../evidence/new-run/experiment.json"
  }
  expect_failures = [terraform_data.replacement_run[0]]
}

run "reject_missing_action_evidence" {
  command = plan
  variables {
    replacement_test        = true
    replacement_instance_id = "i-0123456789abcdef0"
  }
  expect_failures = [terraform_data.replacement_run[0]]
}

run "reject_empty_action_evidence" {
  command = plan
  variables {
    replacement_test          = true
    replacement_instance_id   = "i-0123456789abcdef0"
    replacement_evidence_path = ""
  }
  expect_failures = [terraform_data.replacement_run[0]]
}

run "reject_blank_action_evidence" {
  command = plan
  variables {
    replacement_test          = true
    replacement_instance_id   = "i-0123456789abcdef0"
    replacement_evidence_path = " \t\n"
  }
  expect_failures = [terraform_data.replacement_run[0]]
}

run "reject_directory_action_evidence" {
  command = plan
  variables {
    replacement_test          = true
    replacement_instance_id   = "i-0123456789abcdef0"
    replacement_evidence_path = "../evidence/"
  }
  expect_failures = [terraform_data.replacement_run[0]]
}

run "reject_dot_action_evidence" {
  command = plan
  variables {
    replacement_test          = true
    replacement_instance_id   = "i-0123456789abcdef0"
    replacement_evidence_path = "."
  }
  expect_failures = [terraform_data.replacement_run[0]]
}

run "explicit_action_evidence_destination" {
  command = plan
  variables {
    replacement_test          = true
    replacement_instance_id   = "i-0123456789abcdef0"
    replacement_evidence_path = "../evidence/run with spaces and $literal;quote'/experiment.json"
  }
  assert {
    condition     = length(terraform_data.replacement_run) == 1 && terraform_data.replacement_run[0].triggers_replace == var.replacement_instance_id
    error_message = "An explicit evidence destination must permit planning the guarded exact-instance action."
  }
}

run "single_az_evacuation" {
  command = plan
  variables {
    web_az_indexes = [1]
  }
  assert {
    condition     = length(aws_autoscaling_group.web.vpc_zone_identifier) == 1 && length(aws_lb.ha.subnets) == 2 && aws_db_instance.ha.multi_az
    error_message = "Evacuation must restrict the ASG only, leaving ALB and RDS multi-AZ."
  }
}
