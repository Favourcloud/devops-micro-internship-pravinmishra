mock_provider "azurerm" {}

# Offline fixtures, not an authorized controller or a usable private identity.
variables {
  live_execution_approved = true
  controller_ipv4_cidr    = "192.0.2.10/32"
  ssh_public_key          = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
}

run "four_role_hosts" {
  command = plan

  assert {
    condition     = toset(keys(azurerm_linux_virtual_machine.hosts)) == toset(["web1", "web2", "app1", "db1"])
    error_message = "Exactly four named hosts must be planned."
  }
  assert {
    condition     = toset(keys(output.public_ips)) == toset(["web1", "web2", "app1", "db1"]) && toset(keys(output.web_urls)) == toset(["web1", "web2"])
    error_message = "Outputs must preserve role names and expose only web URLs."
  }
  assert {
    condition     = alltrue([for name, host in azurerm_linux_virtual_machine.hosts : host.tags.Role == local.hosts[name] && host.name == "week09-ansible-${name}" && host.computer_name == name])
    error_message = "Each VM needs the correct role, resource name and hostname."
  }
  assert {
    condition     = alltrue([for name, nsg in azurerm_network_security_group.hosts : length([for rule in nsg.security_rule : rule if rule.access == "Allow" && rule.destination_port_range == "80"]) == (startswith(name, "web") ? 1 : 0)])
    error_message = "Only web hosts can have an HTTP allow rule."
  }
  assert {
    condition = alltrue(flatten([for nsg in azurerm_network_security_group.hosts : [for rule in nsg.security_rule :
      rule.source_address_prefix == var.controller_ipv4_cidr && rule.direction == "Inbound" && rule.protocol == "Tcp" && contains(["22", "80"], rule.destination_port_range) if rule.access == "Allow"
    ]]))
    error_message = "All allowed inbound traffic must come from controller /32 on SSH/HTTP only."
  }
  assert {
    condition     = alltrue([for nsg in azurerm_network_security_group.hosts : length([for rule in nsg.security_rule : rule if rule.name == "SSHFromController" && rule.destination_port_range == "22" && rule.priority == 100]) == 1])
    error_message = "Every host must allow controller SSH."
  }
  assert {
    condition     = alltrue([for nsg in azurerm_network_security_group.hosts : length([for rule in nsg.security_rule : rule if rule.access == "Deny" && rule.priority == 4096 && rule.direction == "Inbound" && rule.source_address_prefix == "*" && rule.destination_port_range == "*"]) == 1])
    error_message = "Explicit deny must override Azure default VNet inbound access."
  }
  assert {
    condition     = alltrue([for host in azurerm_linux_virtual_machine.hosts : host.size == "Standard_B1s" && host.admin_username == "azureuser" && host.disable_password_authentication && host.os_disk[0].disk_size_gb == 32 && host.os_disk[0].storage_account_type == "Standard_LRS"])
    error_message = "Small B1s VMs, SSH-only authentication and 32GiB Standard HDDs are required."
  }
  assert {
    condition     = alltrue([for host in azurerm_linux_virtual_machine.hosts : host.source_image_reference[0].publisher == "Canonical" && host.source_image_reference[0].offer == "0001-com-ubuntu-server-jammy" && host.source_image_reference[0].sku == "22_04-lts-gen2"])
    error_message = "Use the Canonical Ubuntu 22.04 Gen2 image."
  }
  assert {
    condition     = alltrue([for ip in azurerm_public_ip.hosts : ip.sku == "Standard" && ip.allocation_method == "Static"])
    error_message = "Each host requires a Standard static public IP."
  }
  assert {
    condition     = length(azurerm_network_interface_security_group_association.hosts) == 4 && !azurerm_subnet.lab.default_outbound_access_enabled && azurerm_resource_group.lab.location == "uksouth"
    error_message = "All four NICs require an NSG; use explicit outbound public IPs in UK South."
  }
}

run "reject_unapproved_execution" {
  command = plan
  variables { live_execution_approved = false }
  expect_failures = [var.live_execution_approved]
}

run "reject_world_ssh" {
  command = plan
  variables { controller_ipv4_cidr = "0.0.0.0/0" }
  expect_failures = [var.controller_ipv4_cidr]
}

run "reject_controller_subnet" {
  command = plan
  variables { controller_ipv4_cidr = "192.0.2.0/24" }
  expect_failures = [var.controller_ipv4_cidr]
}

run "reject_ipv6_controller" {
  command = plan
  variables { controller_ipv4_cidr = "::1/128" }
  expect_failures = [var.controller_ipv4_cidr]
}

run "reject_unconfigured_controller" {
  command = plan
  variables { controller_ipv4_cidr = "REPLACE_ME/32" }
  expect_failures = [var.controller_ipv4_cidr]
}

run "reject_private_key_material" {
  command = plan
  variables { ssh_public_key = "-----BEGIN OPENSSH PRIVATE KEY-----" }
  expect_failures = [var.ssh_public_key]
}
