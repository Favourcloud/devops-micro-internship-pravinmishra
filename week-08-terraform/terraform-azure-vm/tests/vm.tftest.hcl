variable "admin_password" {
  type      = string
  sensitive = true
}

mock_provider "azurerm" {
  # Synthetic all-zero subscription IDs satisfy schema parsing, not authentication.
  mock_resource "azurerm_subnet" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a1-offline-rg/providers/Microsoft.Network/virtualNetworks/dmi-a1-offline-vnet/subnets/dmi-a1-offline-subnet"
    }
  }

  mock_resource "azurerm_public_ip" {
    defaults = {
      id         = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a1-offline-rg/providers/Microsoft.Network/publicIPAddresses/dmi-a1-offline-ip"
      ip_address = "192.0.2.20"
    }
  }

  mock_resource "azurerm_network_interface" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a1-offline-rg/providers/Microsoft.Network/networkInterfaces/dmi-a1-offline-nic"
    }
  }

  mock_resource "azurerm_network_security_group" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a1-offline-rg/providers/Microsoft.Network/networkSecurityGroups/dmi-a1-offline-nsg"
    }
  }
}

variables {
  project_name         = "dmi-a1-offline"
  location             = "uksouth"
  vm_size              = "Standard_D2lds_v6"
  admin_username       = "dmiuser"
  controller_ipv4_cidr = "192.0.2.10/32"
}

# This apply uses ONLY the mock provider and never creates Azure resources.
run "mocked_topology" {
  command = apply

  assert {
    condition = (
      azurerm_resource_group.vm.name == "dmi-a1-offline-rg" &&
      azurerm_resource_group.vm.location == var.location &&
      azurerm_resource_group.vm.tags.learner == "Eze Favour"
    )
    error_message = "Resource group naming, selected location and learner tag must be preserved."
  }

  assert {
    condition = (
      azurerm_virtual_network.vm.resource_group_name == azurerm_resource_group.vm.name &&
      tolist(azurerm_virtual_network.vm.address_space) == tolist(["10.80.0.0/16"]) &&
      azurerm_subnet.vm.virtual_network_name == azurerm_virtual_network.vm.name &&
      tolist(azurerm_subnet.vm.address_prefixes) == tolist(["10.80.1.0/24"])
    )
    error_message = "The VM subnet must belong to this project's private virtual network."
  }

  assert {
    condition = (
      azurerm_public_ip.vm.sku == "Standard" &&
      azurerm_public_ip.vm.allocation_method == "Static" &&
      azurerm_public_ip.vm.ip_version == "IPv4"
    )
    error_message = "Use a Standard, static IPv4 public IP."
  }

  assert {
    condition = (
      azurerm_network_interface.vm.ip_configuration[0].subnet_id == azurerm_subnet.vm.id &&
      azurerm_network_interface.vm.ip_configuration[0].public_ip_address_id == azurerm_public_ip.vm.id &&
      azurerm_network_interface.vm.ip_configuration[0].private_ip_address_allocation == "Dynamic" &&
      azurerm_network_interface_security_group_association.vm.network_interface_id == azurerm_network_interface.vm.id &&
      azurerm_network_interface_security_group_association.vm.network_security_group_id == azurerm_network_security_group.vm.id
    )
    error_message = "The NIC must connect the subnet, public IP and restrictive NSG."
  }

  assert {
    condition = (
      length(azurerm_network_security_group.vm.security_rule) == 2 &&
      length([for rule in azurerm_network_security_group.vm.security_rule : rule if rule.access == "Allow"]) == 1 &&
      alltrue([for rule in azurerm_network_security_group.vm.security_rule : (
        rule.direction == "Inbound" && rule.priority == 100 && rule.protocol == "Tcp" &&
        rule.source_address_prefix == var.controller_ipv4_cidr && rule.source_port_range == "*" &&
        rule.destination_address_prefix == "*" && rule.destination_port_range == "22"
      ) if rule.access == "Allow"]) &&
      alltrue([for rule in azurerm_network_security_group.vm.security_rule : (
        rule.direction == "Inbound" && rule.priority == 200 && rule.protocol == "*" &&
        rule.source_address_prefix == "*" && rule.destination_address_prefix == "*" &&
        rule.source_port_range == "*" && rule.destination_port_range == "*"
      ) if rule.access == "Deny"])
    )
    error_message = "Only controller /32 SSH may be allowed; deny all other inbound traffic, including Azure defaults."
  }

  assert {
    condition = (
      azurerm_linux_virtual_machine.vm.size == var.vm_size &&
      azurerm_linux_virtual_machine.vm.location == var.location &&
      azurerm_linux_virtual_machine.vm.resource_group_name == azurerm_resource_group.vm.name &&
      tolist(azurerm_linux_virtual_machine.vm.network_interface_ids) == tolist([azurerm_network_interface.vm.id]) &&
      azurerm_linux_virtual_machine.vm.admin_username == var.admin_username &&
      azurerm_linux_virtual_machine.vm.admin_password == var.admin_password &&
      azurerm_linux_virtual_machine.vm.disable_password_authentication == false &&
      length(azurerm_linux_virtual_machine.vm.admin_ssh_key) == 0
    )
    error_message = "VM must preserve the selected SKU, wiring and required username/password authentication."
  }

  assert {
    condition = (
      issensitive(var.admin_password) &&
      issensitive(azurerm_linux_virtual_machine.vm.admin_password) &&
      azurerm_linux_virtual_machine.vm.os_disk[0].storage_account_type == "Standard_LRS" &&
      azurerm_linux_virtual_machine.vm.source_image_reference[0].publisher == "Canonical" &&
      azurerm_linux_virtual_machine.vm.source_image_reference[0].sku == "22_04-lts-gen2"
    )
    error_message = "Password must stay sensitive and the VM must use the intended Ubuntu image and disk."
  }

  assert {
    condition = (
      output.public_ip_address == "192.0.2.20" &&
      output.public_ip_address == azurerm_public_ip.vm.ip_address &&
      output.resource_group_name == azurerm_resource_group.vm.name &&
      output.vm_name == azurerm_linux_virtual_machine.vm.name
    )
    error_message = "Outputs must follow their resources; this IP is a mock documentation address, not a deployment."
  }
}

run "accepts_password_minimum" {
  command = plan
  variables {
    admin_password = substr(var.admin_password, 0, 16)
  }
}

run "accepts_password_maximum" {
  command = plan
  variables {
    admin_password = "${var.admin_password}${var.admin_password}${substr(var.admin_password, 0, 8)}"
  }
}

run "rejects_short_password" {
  command = plan
  variables {
    admin_password = substr(var.admin_password, 0, 15)
  }
  expect_failures = [var.admin_password]
}

run "rejects_long_password" {
  command = plan
  variables {
    admin_password = "${var.admin_password}${var.admin_password}${var.admin_password}"
  }
  expect_failures = [var.admin_password]
}

run "rejects_missing_lowercase" {
  command = plan
  variables {
    admin_password = upper(var.admin_password)
  }
  expect_failures = [var.admin_password]
}

run "rejects_missing_uppercase" {
  command = plan
  variables {
    admin_password = lower(var.admin_password)
  }
  expect_failures = [var.admin_password]
}

run "rejects_missing_digit" {
  command = plan
  variables {
    admin_password = replace(var.admin_password, "/[0-9]/", "x")
  }
  expect_failures = [var.admin_password]
}

run "rejects_missing_symbol" {
  command = plan
  variables {
    admin_password = replace(var.admin_password, "/[^a-zA-Z0-9]/", "x")
  }
  expect_failures = [var.admin_password]
}

run "rejects_password_containing_username" {
  command = plan
  variables {
    admin_password = "${var.admin_password}${upper(var.admin_username)}"
  }
  expect_failures = [var.admin_password]
}

run "rejects_password_space" {
  command = plan
  variables {
    admin_password = "${var.admin_password} "
  }
  expect_failures = [var.admin_password]
}

run "rejects_password_non_ascii" {
  command = plan
  variables {
    admin_password = "${var.admin_password}é"
  }
  expect_failures = [var.admin_password]
}

run "rejects_password_empty" {
  command = plan
  variables {
    admin_password = ""
  }
  expect_failures = [var.admin_password]
}

run "rejects_world_open_ssh" {
  command = plan
  variables {
    controller_ipv4_cidr = "0.0.0.0/0"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_controller_subnet" {
  command = plan
  variables {
    controller_ipv4_cidr = "192.0.2.0/24"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_controller_pair" {
  command = plan
  variables {
    controller_ipv4_cidr = "192.0.2.10/31"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_ipv6_controller" {
  command = plan
  variables {
    controller_ipv4_cidr = "2001:db8::1/128"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_invalid_ipv4_controller" {
  command = plan
  variables {
    controller_ipv4_cidr = "256.0.2.10/32"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_unspecified_controller" {
  command = plan
  variables {
    controller_ipv4_cidr = "0.0.0.0/32"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_controller_without_mask" {
  command = plan
  variables {
    controller_ipv4_cidr = "192.0.2.10"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_controller_wildcard" {
  command = plan
  variables {
    controller_ipv4_cidr = "*"
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_controller_empty" {
  command = plan
  variables {
    controller_ipv4_cidr = ""
  }
  expect_failures = [var.controller_ipv4_cidr]
}

run "rejects_reserved_username" {
  command = plan
  variables {
    admin_username = "root"
  }
  expect_failures = [var.admin_username]
}

run "rejects_long_username" {
  command = plan
  variables {
    admin_username = join("", [for i in range(33) : "z"])
  }
  expect_failures = [var.admin_username]
}

run "rejects_invalid_username" {
  command = plan
  variables {
    admin_username = "invalid user"
  }
  expect_failures = [var.admin_username]
}

run "rejects_invalid_project_name" {
  command = plan
  variables {
    project_name = "not-valid-"
  }
  expect_failures = [var.project_name]
}

run "rejects_long_project_name" {
  command = plan
  variables {
    project_name = join("", [for i in range(31) : "z"])
  }
  expect_failures = [var.project_name]
}

run "rejects_region_display_name" {
  command = plan
  variables {
    location = "UK South"
  }
  expect_failures = [var.location]
}

run "rejects_empty_region" {
  command = plan
  variables {
    location = ""
  }
  expect_failures = [var.location]
}

run "rejects_invalid_vm_size" {
  command = plan
  variables {
    vm_size = "B1s"
  }
  expect_failures = [var.vm_size]
}

run "rejects_empty_vm_size" {
  command = plan
  variables {
    vm_size = ""
  }
  expect_failures = [var.vm_size]
}
