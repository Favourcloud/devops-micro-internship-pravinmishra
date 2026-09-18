# Synthetic plan fixtures, not a live subscription, price review or authorization.
mock_provider "azurerm" {
  mock_data "azurerm_client_config" {
    defaults = {
      subscription_id = "11111111-1111-1111-1111-111111111111"
      tenant_id       = "22222222-2222-2222-2222-222222222222"
      object_id       = "33333333-3333-3333-3333-333333333333"
    }
  }
}

variables {
  subscription_id      = "11111111-1111-1111-1111-111111111111"
  tenant_id            = "22222222-2222-2222-2222-222222222222"
  operator_object_id   = "33333333-3333-3333-3333-333333333333"
  name_prefix          = "dmi-w10-a3-fixture"
  controller_ipv4_cidr = "8.8.8.8/32"
  agent_ipv4_cidr      = "1.1.1.1/32"
  operator_public_key = join(" ", slice(split(" ", trimspace(file(
    "../../../../self-hosted-agent/azure-vm/tests/simulated-operator.pub"
  ))), 0, 2))
  image_version = "22.04.202608060"
  approval = {
    live_execution_approved = true
    approved_at             = timestamp()
    expires_at              = timeadd(timestamp(), "2h")
    estimated_total_usd     = 2
    planning_allowance_usd  = 10
  }
}

run "isolated_artifact_only_target" {
  command = plan
  assert {
    condition = (
      azurerm_linux_virtual_machine.target.admin_username == "labadmin" &&
      azurerm_linux_virtual_machine.target.disable_password_authentication &&
      azurerm_linux_virtual_machine.target.admin_password == null &&
      azurerm_linux_virtual_machine.target.custom_data == null &&
      azurerm_linux_virtual_machine.target.user_data == null &&
      azurerm_linux_virtual_machine.target.size == "Standard_D2lds_v6" &&
      azurerm_linux_virtual_machine.target.disk_controller_type == "NVMe" &&
      azurerm_linux_virtual_machine.target.secure_boot_enabled &&
      azurerm_linux_virtual_machine.target.vtpm_enabled &&
      length(azurerm_linux_virtual_machine.target.identity) == 0 &&
      length(azurerm_linux_virtual_machine.target.boot_diagnostics) == 1 &&
      azurerm_linux_virtual_machine.target.os_disk[0].disk_size_gb == 32 &&
      azurerm_linux_virtual_machine.target.source_image_reference[0].version == var.image_version
    )
    error_message = "Keep the key-only, identity-free target separate from app builds, packages and agent registration."
  }
  assert {
    condition = (
      azurerm_public_ip.target.sku == "Standard" &&
      azurerm_public_ip.target.allocation_method == "Static" &&
      azurerm_public_ip.target.ip_version == "IPv4" &&
      azurerm_resource_group.target.location == "uksouth" &&
      output.assignment == "week10-a3" && output.ssh_username == "labadmin"
    )
    error_message = "Keep the approved target shape and manual Ansible handoff."
  }
  assert {
    condition = (
      length(azurerm_network_security_group.target.security_rule) == 3 &&
      length([for rule in azurerm_network_security_group.target.security_rule : rule if rule.access == "Allow" && rule.destination_port_range == "22" && toset(rule.source_address_prefixes) == toset([var.controller_ipv4_cidr, var.agent_ipv4_cidr]) && rule.priority == 100]) == 1 &&
      length([for rule in azurerm_network_security_group.target.security_rule : rule if rule.access == "Allow" && rule.destination_port_range == "80" && rule.source_address_prefix == "Internet" && rule.priority == 110]) == 1 &&
      length([for rule in azurerm_network_security_group.target.security_rule : rule if rule.access == "Deny" && rule.direction == "Inbound" && rule.source_address_prefix == "*" && rule.priority == 200]) == 1
    )
    error_message = "Permit only scoped SSH and lab HTTP; deny the remaining inbound traffic."
  }
}

run "operator_mismatch" {
  command = plan
  variables {
    operator_object_id = "44444444-4444-4444-4444-444444444444"
  }
  expect_failures = [azurerm_resource_group.target]
}

run "subscription_mismatch" {
  command = plan
  variables {
    subscription_id = "44444444-4444-4444-4444-444444444444"
  }
  expect_failures = [azurerm_resource_group.target]
}

run "tenant_mismatch" {
  command = plan
  variables {
    tenant_id = "44444444-4444-4444-4444-444444444444"
  }
  expect_failures = [azurerm_resource_group.target]
}

run "floating_image_rejected" {
  command = plan
  variables {
    image_version = "latest"
  }
  expect_failures = [var.image_version]
}

run "private_key_text_rejected" {
  command = plan
  variables {
    operator_public_key = "-----BEGIN OPENSSH PRIVATE KEY-----"
  }
  expect_failures = [var.operator_public_key]
}
