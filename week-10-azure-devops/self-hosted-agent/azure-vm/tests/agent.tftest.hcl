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
  subscription_id         = "11111111-1111-1111-1111-111111111111"
  tenant_id               = "22222222-2222-2222-2222-222222222222"
  operator_object_id      = "33333333-3333-3333-3333-333333333333"
  project_name            = "dmi-w10-a1-mock"
  controller_ipv4_cidr    = "8.8.8.8/32"
  ssh_public_key          = file("tests/simulated-operator.pub")
  image_version           = "22.04.202608060"
  expires_at              = "2100-01-01T00:00:00Z"
  live_execution_approved = true
}

run "isolated_key_only_vm" {
  command = plan
  assert {
    condition = (
      azurerm_linux_virtual_machine.agent.disable_password_authentication &&
      azurerm_linux_virtual_machine.agent.admin_password == null &&
      azurerm_linux_virtual_machine.agent.admin_username == "labadmin" &&
      azurerm_linux_virtual_machine.agent.size == "Standard_D2lds_v6" &&
      azurerm_linux_virtual_machine.agent.disk_controller_type == "NVMe" &&
      azurerm_linux_virtual_machine.agent.secure_boot_enabled &&
      azurerm_linux_virtual_machine.agent.vtpm_enabled &&
      length(azurerm_linux_virtual_machine.agent.boot_diagnostics) == 1 &&
      length(azurerm_linux_virtual_machine.agent.identity) == 0 &&
      azurerm_linux_virtual_machine.agent.os_disk[0].disk_size_gb == 32 &&
      azurerm_linux_virtual_machine.agent.os_disk[0].storage_account_type == "Standard_LRS" &&
      azurerm_linux_virtual_machine.agent.source_image_reference[0].version == var.image_version
    )
    error_message = "The VM must remain key-only, identity-free and pinned to the reviewed image/disk."
  }
  assert {
    condition = (
      length(azurerm_network_security_group.agent.security_rule) == 2 &&
      length([for rule in azurerm_network_security_group.agent.security_rule : rule if rule.access == "Allow" && rule.destination_port_range == "22" && rule.source_address_prefix == var.controller_ipv4_cidr && rule.priority == 100]) == 1 &&
      length([for rule in azurerm_network_security_group.agent.security_rule : rule if rule.access == "Deny" && rule.direction == "Inbound" && rule.priority == 200]) == 1
    )
    error_message = "Only the controller /32 may enter over SSH; all other inbound traffic is denied."
  }
}

run "approval_required" {
  command = plan
  variables { live_execution_approved = false }
  expect_failures = [terraform_data.authorization]
}

run "identity_bound" {
  command = plan
  variables { operator_object_id = "44444444-4444-4444-4444-444444444444" }
  expect_failures = [terraform_data.authorization]
}

run "worldwide_ssh_rejected" {
  command = plan
  variables { controller_ipv4_cidr = "0.0.0.0/0" }
  expect_failures = [var.controller_ipv4_cidr]
}

run "large_ssh_range_rejected" {
  command = plan
  variables { controller_ipv4_cidr = "8.8.8.0/24" }
  expect_failures = [var.controller_ipv4_cidr]
}

run "region_change_rejected" {
  command = plan
  variables { location = "eastus" }
  expect_failures = [var.location]
}

run "size_change_rejected" {
  command = plan
  variables { vm_size = "Standard_D8s_v5" }
  expect_failures = [var.vm_size]
}

run "floating_image_rejected" {
  command = plan
  variables { image_version = "latest" }
  expect_failures = [var.image_version]
}

run "unrelated_prefix_rejected" {
  command = plan
  variables { project_name = "production" }
  expect_failures = [var.project_name]
}
