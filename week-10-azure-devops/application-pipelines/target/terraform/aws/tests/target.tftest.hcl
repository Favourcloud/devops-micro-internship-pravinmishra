# Synthetic plan fixtures only. These tests require the separately installed AWS provider.
mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "000000000000"
      arn        = "arn:aws:iam::000000000000:user/synthetic-operator"
    }
  }
  mock_data "aws_ami" {
    defaults = {
      id = "ami-00000000000000000"
    }
  }
}

variables {
  aws_region           = "eu-west-2"
  account_id           = "000000000000"
  operator_arn         = "arn:aws:iam::000000000000:user/synthetic-operator"
  ami_id               = "ami-00000000000000000"
  name_prefix          = "dmi-w10-a2-fixture"
  controller_ipv4_cidr = "8.8.8.8/32"
  agent_ipv4_cidr      = "1.1.1.1/32"
  operator_public_key  = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f"
  approval = {
    live_execution_approved = true
    approved_at             = timestamp()
    expires_at              = timeadd(timestamp(), "2h")
    estimated_total_usd     = 2
    planning_allowance_usd  = 10
  }
}

run "isolated_no_bootstrap_target" {
  command = plan
  assert {
    condition = (
      aws_instance.target.ami == var.ami_id &&
      aws_instance.target.instance_type == "t3.micro" &&
      aws_instance.target.associate_public_ip_address &&
      aws_instance.target.user_data == null &&
      # user_data_base64 is unknown until apply; source contracts check its omission.
      aws_instance.target.metadata_options[0].http_tokens == "required" &&
      aws_instance.target.metadata_options[0].http_put_response_hop_limit == 1 &&
      aws_instance.target.metadata_options[0].instance_metadata_tags == "disabled" &&
      aws_instance.target.root_block_device[0].encrypted &&
      aws_instance.target.root_block_device[0].delete_on_termination &&
      aws_instance.target.root_block_device[0].volume_size == 8 &&
      aws_instance.target.credit_specification[0].cpu_credits == "standard"
    )
    error_message = "Keep a small encrypted IMDSv2-only target with no app bootstrap or unlimited CPU credits."
  }
  assert {
    condition = (
      length(aws_security_group.target.ingress) == 2 &&
      length([for rule in aws_security_group.target.ingress : rule if rule.from_port == 22 && rule.to_port == 22 && toset(rule.cidr_blocks) == toset([var.controller_ipv4_cidr, var.agent_ipv4_cidr])]) == 1 &&
      length([for rule in aws_security_group.target.ingress : rule if rule.from_port == 80 && rule.to_port == 80 && toset(rule.cidr_blocks) == toset(["0.0.0.0/0"])]) == 1 &&
      length(aws_security_group.target.egress) == 2 &&
      output.ssh_username == "ubuntu" && output.assignment == "week10-a2"
    )
    error_message = "Permit only scoped SSH and lab HTTP; keep the Ansible handoff explicit."
  }
}

run "operator_mismatch" {
  command = plan
  variables {
    operator_arn = "arn:aws:iam::000000000000:user/different-operator"
  }
  expect_failures = [aws_vpc.target]
}

run "root_runtime_rejected" {
  command = plan
  override_data {
    target = data.aws_caller_identity.current
    values = {
      account_id = "000000000000"
      arn        = "arn:aws:iam::000000000000:root"
    }
  }
  expect_failures = [aws_vpc.target]
}

run "root_input_rejected" {
  command = plan
  variables {
    operator_arn = "arn:aws:iam::000000000000:root"
  }
  expect_failures = [var.operator_arn]
}

run "restricted_federated_session" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::000000000000:federated-user/synthetic-session"
  }
  override_data {
    target = data.aws_caller_identity.current
    values = {
      account_id = "000000000000"
      arn        = "arn:aws:sts::000000000000:federated-user/synthetic-session"
    }
  }
  assert {
    condition     = data.aws_caller_identity.current.arn == var.operator_arn
    error_message = "A federated caller must match the exact approved non-root session."
  }
}

run "federated_session_mismatch" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::000000000000:federated-user/different-session"
  }
  override_data {
    target = data.aws_caller_identity.current
    values = {
      account_id = "000000000000"
      arn        = "arn:aws:sts::000000000000:federated-user/synthetic-session"
    }
  }
  expect_failures = [aws_vpc.target]
}

run "federated_account_mismatch" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::111111111111:federated-user/synthetic-session"
  }
  override_data {
    target = data.aws_caller_identity.current
    values = {
      account_id = "111111111111"
      arn        = "arn:aws:sts::111111111111:federated-user/synthetic-session"
    }
  }
  expect_failures = [aws_vpc.target]
}

run "federated_wrong_service_rejected" {
  command = plan
  variables {
    operator_arn = "arn:aws:iam::000000000000:federated-user/synthetic-session"
  }
  expect_failures = [var.operator_arn]
}

run "federated_path_rejected" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::000000000000:federated-user/path/session"
  }
  expect_failures = [var.operator_arn]
}

run "federated_short_name_rejected" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::000000000000:federated-user/a"
  }
  expect_failures = [var.operator_arn]
}

run "federated_long_name_rejected" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::000000000000:federated-user/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  expect_failures = [var.operator_arn]
}

run "iam_user_wrong_service_rejected" {
  command = plan
  variables {
    operator_arn = "arn:aws:sts::000000000000:user/synthetic-operator"
  }
  expect_failures = [var.operator_arn]
}

run "floating_ami_rejected" {
  command = plan
  variables {
    ami_id = "latest"
  }
  expect_failures = [var.ami_id]
}
