# In-memory plan fixtures only: these values are not deployment approval or live inputs.
variables {
  assignment           = "week10-a2"
  name_prefix          = "dmi-w10-a2-fixture"
  controller_ipv4_cidr = "8.8.8.8/32"
  agent_ipv4_cidr      = "1.1.1.1/32"
  approval = {
    live_execution_approved = true
    approved_at             = timestamp()
    expires_at              = timeadd(timestamp(), "2h")
    estimated_total_usd     = 2
    planning_allowance_usd  = 10
  }
}

run "valid_contract" {
  command = plan
  assert {
    condition     = toset(output.ssh_cidrs) == toset(["8.8.8.8/32", "1.1.1.1/32"])
    error_message = "Only the two reviewed SSH sources may be exposed."
  }
  assert {
    condition     = output.tags.assignment == "week10-a2" && output.tags.managed_by == "Terraform"
    error_message = "Ownership tags must remain explicit."
  }
}

run "approval_required" {
  command = plan
  variables {
    approval = {
      live_execution_approved = false
      approved_at             = timestamp()
      expires_at              = timeadd(timestamp(), "2h")
      estimated_total_usd     = 2
      planning_allowance_usd  = 10
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "wrong_assignment_prefix" {
  command = plan
  variables {
    name_prefix = "dmi-w10-a3-fixture"
  }
  expect_failures = [terraform_data.authorization]
}

run "world_open_ssh" {
  command = plan
  variables {
    controller_ipv4_cidr = "0.0.0.0/0"
  }
  expect_failures = [terraform_data.authorization]
}

run "private_agent_address" {
  command = plan
  variables {
    agent_ipv4_cidr = "10.0.0.1/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "noncanonical_address" {
  command = plan
  variables {
    agent_ipv4_cidr = "001.1.1.1/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "expired_window" {
  command = plan
  variables {
    approval = {
      live_execution_approved = true
      approved_at             = timeadd(timestamp(), "-2h")
      expires_at              = timeadd(timestamp(), "-1h")
      estimated_total_usd     = 2
      planning_allowance_usd  = 10
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "future_approval" {
  command = plan
  variables {
    approval = {
      live_execution_approved = true
      approved_at             = timeadd(timestamp(), "1h")
      expires_at              = timeadd(timestamp(), "2h")
      estimated_total_usd     = 2
      planning_allowance_usd  = 10
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "overlong_window" {
  command = plan
  variables {
    approval = {
      live_execution_approved = true
      approved_at             = timestamp()
      expires_at              = timeadd(timestamp(), "5h")
      estimated_total_usd     = 2
      planning_allowance_usd  = 10
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "estimate_exceeds_allowance" {
  command = plan
  variables {
    approval = {
      live_execution_approved = true
      approved_at             = timestamp()
      expires_at              = timeadd(timestamp(), "2h")
      estimated_total_usd     = 11
      planning_allowance_usd  = 10
    }
  }
  expect_failures = [var.approval]
}

run "allowance_exceeds_scope" {
  command = plan
  variables {
    approval = {
      live_execution_approved = true
      approved_at             = timestamp()
      expires_at              = timeadd(timestamp(), "2h")
      estimated_total_usd     = 2
      planning_allowance_usd  = 11
    }
  }
  expect_failures = [var.approval]
}

run "duplicate_sources_are_deduplicated" {
  command = plan
  variables {
    agent_ipv4_cidr = "8.8.8.8/32"
  }
  assert {
    condition     = length(output.ssh_cidrs) == 1
    error_message = "An explicitly shared egress IP must not produce duplicate firewall entries."
  }
}

run "ipv6_not_in_scope" {
  command = plan
  variables {
    agent_ipv4_cidr = "2606:4700:4700::1111/128"
  }
  expect_failures = [terraform_data.authorization]
}

run "documentation_address_rejected" {
  command = plan
  variables {
    agent_ipv4_cidr = "192.0.2.1/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "shared_address_rejected" {
  command = plan
  variables {
    agent_ipv4_cidr = "100.64.0.1/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "multicast_address_rejected" {
  command = plan
  variables {
    agent_ipv4_cidr = "224.0.0.1/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "invalid_octet_rejected" {
  command = plan
  variables {
    agent_ipv4_cidr = "8.8.8.256/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "retired_relay_address_rejected" {
  command = plan
  variables {
    agent_ipv4_cidr = "192.88.99.1/32"
  }
  expect_failures = [terraform_data.authorization]
}

run "zero_estimate_rejected" {
  command = plan
  variables {
    approval = {
      live_execution_approved = true
      approved_at             = timestamp()
      expires_at              = timeadd(timestamp(), "2h")
      estimated_total_usd     = 0
      planning_allowance_usd  = 10
    }
  }
  expect_failures = [var.approval]
}
