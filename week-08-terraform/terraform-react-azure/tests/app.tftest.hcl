mock_provider "azurerm" {
  # Synthetic IDs and TEST-NET addresses are schema fixtures, never live inputs.
  mock_resource "azurerm_subnet" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a3-offline-rg/providers/Microsoft.Network/virtualNetworks/dmi-a3-offline-vnet/subnets/dmi-a3-offline-subnet"
    }
  }
  mock_resource "azurerm_public_ip" {
    defaults = {
      id         = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a3-offline-rg/providers/Microsoft.Network/publicIPAddresses/dmi-a3-offline-ip"
      ip_address = "192.0.2.30"
    }
  }
  mock_resource "azurerm_network_interface" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a3-offline-rg/providers/Microsoft.Network/networkInterfaces/dmi-a3-offline-nic"
    }
  }
  mock_resource "azurerm_network_security_group" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/dmi-a3-offline-rg/providers/Microsoft.Network/networkSecurityGroups/dmi-a3-offline-nsg"
    }
  }
}

variables {
  project_name         = "dmi-a3-offline"
  location             = "uksouth"
  vm_size              = "Standard_D2s_v5"
  controller_ipv4_cidr = "192.0.2.10/32"
  admin_username       = "dmiuser"
  # RFC 8032 section 7.1 test 1 public vector. Never use this known test key live.
  admin_ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea offline-test-only"
}

# Terraform's apply command here is in-memory with a mock, not an Azure apply.
run "mocked_topology" {
  command = apply

  assert {
    condition = (
      azurerm_resource_group.app.name == "dmi-a3-offline-rg" &&
      azurerm_resource_group.app.location == var.location &&
      azurerm_resource_group.app.tags.learner == "Eze Favour" &&
      azurerm_resource_group.app.tags.assignment == "week-08-assignment-03"
    )
    error_message = "Preserve assignment naming, explicit location and learner tags."
  }
  assert {
    condition = (
      azurerm_virtual_network.app.resource_group_name == azurerm_resource_group.app.name &&
      tolist(azurerm_virtual_network.app.address_space) == tolist(["10.83.0.0/16"]) &&
      azurerm_subnet.app.virtual_network_name == azurerm_virtual_network.app.name &&
      tolist(azurerm_subnet.app.address_prefixes) == tolist(["10.83.1.0/24"])
    )
    error_message = "The subnet must belong to the project VNet and resource group."
  }
  assert {
    condition = (
      azurerm_public_ip.app.sku == "Standard" &&
      azurerm_public_ip.app.allocation_method == "Static" &&
      azurerm_public_ip.app.ip_version == "IPv4" &&
      azurerm_public_ip.app.resource_group_name == azurerm_resource_group.app.name
    )
    error_message = "Require Standard static IPv4 in the project resource group."
  }
  assert {
    condition = (
      azurerm_network_interface.app.ip_configuration[0].subnet_id == azurerm_subnet.app.id &&
      azurerm_network_interface.app.ip_configuration[0].public_ip_address_id == azurerm_public_ip.app.id &&
      azurerm_network_interface.app.ip_configuration[0].private_ip_address_allocation == "Dynamic" &&
      azurerm_network_interface_security_group_association.app.network_interface_id == azurerm_network_interface.app.id &&
      azurerm_network_interface_security_group_association.app.network_security_group_id == azurerm_network_security_group.app.id
    )
    error_message = "NIC, subnet, public IP and NSG must be connected."
  }
  assert {
    condition = (
      length(azurerm_network_security_group.app.security_rule) == 3 &&
      length([for r in azurerm_network_security_group.app.security_rule : r if r.access == "Allow"]) == 2 &&
      alltrue([for r in azurerm_network_security_group.app.security_rule : (
        r.direction == "Inbound" && r.protocol == "Tcp" && r.source_port_range == "*" &&
        r.destination_address_prefix == "*" && (
          (r.priority == 100 && r.destination_port_range == "22" && r.source_address_prefix == var.controller_ipv4_cidr) ||
          (r.priority == 110 && r.destination_port_range == "80" && r.source_address_prefix == "*")
        )
      ) if r.access == "Allow"]) &&
      alltrue([for r in azurerm_network_security_group.app.security_rule : (
        r.direction == "Inbound" && r.priority == 200 && r.protocol == "*" &&
        r.source_port_range == "*" && r.destination_port_range == "*" &&
        r.source_address_prefix == "*" && r.destination_address_prefix == "*"
      ) if r.access == "Deny"])
    )
    error_message = "Only controller SSH and public HTTP may be allowed; deny all remaining inbound, overriding defaults."
  }
  assert {
    condition = (
      azurerm_linux_virtual_machine.app.resource_group_name == azurerm_resource_group.app.name &&
      azurerm_linux_virtual_machine.app.location == var.location &&
      azurerm_linux_virtual_machine.app.size == var.vm_size &&
      tolist(azurerm_linux_virtual_machine.app.network_interface_ids) == tolist([azurerm_network_interface.app.id]) &&
      azurerm_linux_virtual_machine.app.disable_password_authentication &&
      azurerm_linux_virtual_machine.app.admin_password == null &&
      one(azurerm_linux_virtual_machine.app.admin_ssh_key).username == var.admin_username &&
      one(azurerm_linux_virtual_machine.app.admin_ssh_key).public_key == var.admin_ssh_public_key
    )
    error_message = "VM must use the approved size, project NIC and only the supplied public SSH key."
  }
  assert {
    condition = (
      azurerm_linux_virtual_machine.app.os_disk[0].storage_account_type == "Standard_LRS" &&
      azurerm_linux_virtual_machine.app.os_disk[0].disk_size_gb == 32 &&
      azurerm_linux_virtual_machine.app.os_disk[0].disk_encryption_set_id == null &&
      azurerm_linux_virtual_machine.app.source_image_reference[0].publisher == "Canonical" &&
      azurerm_linux_virtual_machine.app.source_image_reference[0].offer == "ubuntu-24_04-lts" &&
      azurerm_linux_virtual_machine.app.source_image_reference[0].sku == "server"
    )
    error_message = "Use Ubuntu 24.04 LTS and an Azure platform-encrypted managed OS disk, no extra key service."
  }
  assert {
    condition     = base64decode(azurerm_linux_virtual_machine.app.custom_data) == file("${path.module}/cloud-init.sh")
    error_message = "custom_data must contain exactly the committed shell script, encoded once."
  }
  assert {
    condition = (
      output.public_ip_address == "192.0.2.30" &&
      output.public_ip_address == azurerm_public_ip.app.ip_address &&
      output.resource_group_name == azurerm_resource_group.app.name &&
      output.vm_name == azurerm_linux_virtual_machine.app.name
    )
    error_message = "Outputs must reference actual resources (synthetic in this mock), not fabricated deployment values."
  }
}

run "valid_input_boundaries" {
  command = plan
  variables {
    project_name         = "a-1"
    location             = "westeurope"
    vm_size              = "Standard_D2s_v5"
    admin_username       = "learner_1"
    controller_ipv4_cidr = "203.0.113.20/32"
    admin_ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea"
  }
}
