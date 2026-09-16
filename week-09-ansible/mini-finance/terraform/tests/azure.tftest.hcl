# Mocked plans only: no Azure authentication, API calls, resources or spend.
mock_provider "azurerm" {}

variables {
  location        = "uksouth"
  controller_cidr = "198.51.100.20/32" # RFC 5737 documentation fixture, not a deployment address.
  # Public test vector from RFC 8032 section 7.1, not a generated or user key.
  ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea"
}

run "azure_assignment_contract" {
  command = plan

  assert {
    condition     = azurerm_linux_virtual_machine.site.size == "Standard_B1s"
    error_message = "The assignment requires Standard_B1s."
  }

  assert {
    condition = (
      azurerm_linux_virtual_machine.site.os_disk[0].storage_account_type == "Standard_LRS" &&
      azurerm_linux_virtual_machine.site.os_disk[0].disk_size_gb == 32
    )
    error_message = "Keep the dedicated OS disk within the estimated 32 GiB Standard HDD tier."
  }

  assert {
    condition = (
      azurerm_linux_virtual_machine.site.source_image_reference[0].publisher == "Canonical" &&
      azurerm_linux_virtual_machine.site.source_image_reference[0].offer == "0001-com-ubuntu-server-jammy" &&
      azurerm_linux_virtual_machine.site.source_image_reference[0].sku == "22_04-lts-gen2"
    )
    error_message = "The image must be Canonical Ubuntu 22.04."
  }

  assert {
    condition = (
      azurerm_linux_virtual_machine.site.disable_password_authentication &&
      length(azurerm_linux_virtual_machine.site.admin_ssh_key) == 1 &&
      one(azurerm_linux_virtual_machine.site.admin_ssh_key).public_key == var.ssh_public_key
    )
    error_message = "Use only the explicitly supplied existing public key and disable password login."
  }

  assert {
    condition = (
      azurerm_public_ip.site.sku == "Standard" &&
      azurerm_public_ip.site.allocation_method == "Static" &&
      azurerm_resource_group.site.name == "dmi-mini-finance-rg"
    )
    error_message = "Require a dedicated resource group and stable Standard public IP."
  }

  assert {
    condition = (
      length(azurerm_network_security_group.site.security_rule) == 3 &&
      length([for rule in azurerm_network_security_group.site.security_rule : rule if
        rule.name == "SSHFromController" && rule.source_address_prefix == var.controller_cidr &&
        rule.destination_port_range == "22" && rule.protocol == "Tcp" && rule.access == "Allow" && rule.direction == "Inbound"
      ]) == 1 &&
      length([for rule in azurerm_network_security_group.site.security_rule : rule if
        rule.name == "PublicHTTP" && rule.source_address_prefix == "Internet" &&
        rule.destination_port_range == "80" && rule.protocol == "Tcp" && rule.access == "Allow" && rule.direction == "Inbound"
      ]) == 1 &&
      length([for rule in azurerm_network_security_group.site.security_rule : rule if
        rule.name == "DenyOtherInbound" && rule.access == "Deny" && rule.direction == "Inbound" && rule.priority == 4096
      ]) == 1
    )
    error_message = "Permit only controller /32 SSH and public HTTP, then deny other inbound traffic."
  }
}

run "reject_open_ssh" {
  command = plan
  variables {
    controller_cidr = "0.0.0.0/0"
  }
  expect_failures = [var.controller_cidr]
}

run "reject_subnet_ssh" {
  command = plan
  variables {
    controller_cidr = "198.51.100.0/24"
  }
  expect_failures = [var.controller_cidr]
}

run "reject_ipv6_ssh" {
  command = plan
  variables {
    controller_cidr = "2001:db8::1/32"
  }
  expect_failures = [var.controller_cidr]
}

run "reject_malformed_ssh_address" {
  command = plan
  variables {
    controller_cidr = "999.51.100.20/32"
  }
  expect_failures = [var.controller_cidr]
}

run "reject_unspecified_ssh_address" {
  command = plan
  variables {
    controller_cidr = "0.0.0.0/32"
  }
  expect_failures = [var.controller_cidr]
}

run "reject_root_admin" {
  command = plan
  variables {
    admin_username = "root"
  }
  expect_failures = [var.admin_username]
}

run "reject_missing_public_key" {
  command = plan
  variables {
    ssh_public_key = "REPLACE_WITH_EXISTING_USER_PUBLIC_KEY_ONLY"
  }
  expect_failures = [var.ssh_public_key]
}

run "reject_unapproved_region_placeholder" {
  command = plan
  variables {
    location = "REPLACE_WITH_APPROVED_AZURE_REGION"
  }
  expect_failures = [var.location]
}

run "reject_unsafe_prefix" {
  command = plan
  variables {
    name_prefix = "../shared"
  }
  expect_failures = [var.name_prefix]
}
