# Synthetic IDs and a public-only key fixture; no real subscription or credentials.
mock_provider "azurerm" {
  mock_resource "azurerm_subnet" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/mock/providers/Microsoft.Network/virtualNetworks/mock/subnets/web" }
  }
  mock_resource "azurerm_public_ip" {
    defaults = {
      id         = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/mock/providers/Microsoft.Network/publicIPAddresses/web"
      ip_address = "203.0.113.20"
    }
  }
  mock_resource "azurerm_network_security_group" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/mock/providers/Microsoft.Network/networkSecurityGroups/web" }
  }
  mock_resource "azurerm_network_interface" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/mock/providers/Microsoft.Network/networkInterfaces/web" }
  }
}

variables {
  subscription_id = "00000000-0000-0000-0000-000000000001"
  run_id          = "mock0001"
  controller_cidr = "203.0.113.10/32"
  ssh_public_key  = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f synthetic-public-fixture-no-private-key"
}

run "secure_single_vm" {
  command = apply

  assert {
    condition     = azurerm_linux_virtual_machine.web.size == "Standard_D2lds_v6" && azurerm_resource_group.epicbook.location == "uksouth" && azurerm_linux_virtual_machine.web.zone == null
    error_message = "Use the reviewed nonzonal D2lds_v6 VM in UK South; do not select restricted zones."
  }
  assert {
    condition     = azurerm_resource_group.epicbook.name == "week09-a5-epicbook-${var.run_id}-rg" && azurerm_linux_virtual_machine.web.name == "week09-a5-epicbook-${var.run_id}-vm"
    error_message = "Use the explicit unique A5 run identifier for isolated resource names."
  }
  assert {
    condition     = azurerm_linux_virtual_machine.web.os_disk[0].storage_account_type == "Standard_LRS" && azurerm_linux_virtual_machine.web.os_disk[0].disk_size_gb == 32
    error_message = "Use a platform-encrypted managed 32 GiB Standard_LRS disk."
  }
  assert {
    condition     = azurerm_linux_virtual_machine.web.disable_password_authentication && azurerm_linux_virtual_machine.web.secure_boot_enabled && azurerm_linux_virtual_machine.web.vtpm_enabled
    error_message = "Require key-only access and reviewed Gen2 boot protections."
  }
  assert {
    condition = (
      azurerm_linux_virtual_machine.web.source_image_reference[0].publisher == "Canonical" &&
      azurerm_linux_virtual_machine.web.source_image_reference[0].offer == "0001-com-ubuntu-server-jammy" &&
      azurerm_linux_virtual_machine.web.source_image_reference[0].sku == "22_04-lts-gen2" &&
      azurerm_linux_virtual_machine.web.source_image_reference[0].version == "22.04.202608060" &&
      azurerm_linux_virtual_machine.web.disk_controller_type == "NVMe"
    )
    error_message = "Pin the verified Ubuntu 22.04 Gen2 Trusted Launch/NVMe-capable image and controller."
  }
  assert {
    condition     = length(azurerm_linux_virtual_machine.web.os_disk[0].diff_disk_settings) == 0
    error_message = "Keep the managed OS disk; do not put application data on ephemeral local NVMe storage."
  }
  assert {
    condition     = azurerm_network_security_rule.ssh.source_address_prefix == var.controller_cidr && azurerm_network_security_rule.ssh.destination_port_range == "22"
    error_message = "SSH must be controller-only TCP22."
  }
  assert {
    condition     = azurerm_network_security_rule.http.source_address_prefix == "Internet" && azurerm_network_security_rule.http.destination_port_range == "80"
    error_message = "Only HTTP is publicly exposed."
  }
  assert {
    condition     = azurerm_network_security_rule.deny_other_inbound.access == "Deny" && azurerm_network_security_rule.deny_other_inbound.priority < 65000
    error_message = "Deny other inbound access before the Azure default VNet allow rule."
  }
  assert {
    condition     = azurerm_network_interface_security_group_association.web.network_security_group_id == azurerm_network_security_group.web.id && azurerm_network_interface.web.ip_configuration[0].subnet_id == azurerm_subnet.web.id
    error_message = "Associate the dedicated NIC, subnet and security group."
  }
  assert {
    condition     = azurerm_public_ip.web.sku == "Standard" && azurerm_public_ip.web.allocation_method == "Static" && length(azurerm_linux_virtual_machine.web.boot_diagnostics) == 1
    error_message = "Use a Standard static IP and managed boot diagnostics for trusted host-key verification."
  }
  assert {
    condition     = output.public_ip == "203.0.113.20" && output.admin_user == "ubuntu"
    error_message = "Keep the provider-independent inventory output contract."
  }
}

run "reject_world_ssh" {
  command = plan
  variables { controller_cidr = "0.0.0.0/0" }
  expect_failures = [var.controller_cidr]
}

run "reject_ipv6_ssh" {
  command = plan
  variables { controller_cidr = "::1/128" }
  expect_failures = [var.controller_cidr]
}

run "reject_invalid_ipv4" {
  command = plan
  variables { controller_cidr = "999.1.2.3/32" }
  expect_failures = [var.controller_cidr]
}

run "reject_loopback" {
  command = plan
  variables { controller_cidr = "127.0.0.1/32" }
  expect_failures = [var.controller_cidr]
}

run "reject_private_key" {
  command = plan
  variables { ssh_public_key = "-----BEGIN OPENSSH PRIVATE KEY-----" }
  expect_failures = [var.ssh_public_key]
}

run "reject_unreviewed_region" {
  command = plan
  variables { location = "eastus" }
  expect_failures = [var.location]
}

run "reject_expensive_size" {
  command = plan
  variables { vm_size = "Standard_D64s_v5" }
  expect_failures = [var.vm_size]
}

run "reject_superseded_b1ms" {
  command = plan
  variables { vm_size = "Standard_B1ms" }
  expect_failures = [var.vm_size]
}

run "reject_oversized_disk" {
  command = plan
  variables { os_disk_gib = 1000 }
  expect_failures = [var.os_disk_gib]
}

run "reject_invalid_run_id" {
  command = plan
  variables { run_id = "../reused lab" }
  expect_failures = [var.run_id]
}

run "reject_invalid_subscription" {
  command = plan
  variables { subscription_id = "not-an-id" }
  expect_failures = [var.subscription_id]
}
