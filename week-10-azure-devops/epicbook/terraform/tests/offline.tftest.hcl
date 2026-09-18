# Synthetic fixtures only. Run with the isolated, network-denied procedure in README.md.
mock_provider "azurerm" {
  override_during = plan
  mock_data "azurerm_client_config" {
    defaults = {
      subscription_id = "00000000-0000-0000-0000-000000000001"
      tenant_id       = "00000000-0000-0000-0000-000000000002"
      client_id       = "00000000-0000-0000-0000-000000000003"
      object_id       = "00000000-0000-0000-0000-000000000004"
    }
  }
  mock_resource "azurerm_mysql_flexible_server" {
    defaults = { fqdn = "fixture-mysql.mysql.database.azure.com" }
  }
}

override_resource {
  target          = azurerm_public_ip.vm["frontend"]
  override_during = plan
  values = {
    ip_address = "8.8.4.4"
    id         = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-a4-fixture-rg/providers/Microsoft.Network/publicIPAddresses/fixture-frontend-ip"
  }
}
override_resource {
  target          = azurerm_public_ip.vm["backend"]
  override_during = plan
  values = {
    ip_address = "8.8.8.8"
    id         = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-a4-fixture-rg/providers/Microsoft.Network/publicIPAddresses/fixture-backend-ip"
  }
}
override_resource {
  target          = azurerm_network_interface.vm["backend"]
  override_during = plan
  values = {
    private_ip_address = "10.140.2.4"
    id                 = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-a4-fixture-rg/providers/Microsoft.Network/networkInterfaces/fixture-backend-nic"
  }
}

variables {
  subscription_id        = "00000000-0000-0000-0000-000000000001"
  tenant_id              = "00000000-0000-0000-0000-000000000002"
  client_id              = "00000000-0000-0000-0000-000000000003"
  operator_object_id     = "00000000-0000-0000-0000-000000000004"
  name_prefix            = "dmi-w10-a4-fixture"
  controller_ipv4_cidr   = "8.8.4.4/32"
  agent_ipv4_cidr        = "8.8.8.8/32"
  operator_public_key    = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  image_version          = "0.0.0"
  mysql_admin_password   = "TEST-ONLY-not-a-live-secret-123!"
  mysql_password_version = 1
  approval = {
    scope                   = "week10-a4-two-vms-private-mysql"
    live_execution_approved = true
    remote_state_ready      = true
    cleanup_safeguard_ready = true
    approved_at             = timestamp()
    expires_at              = timeadd(timestamp(), "4h")
    estimated_total_usd     = 1
    planning_allowance_usd  = 2
  }
}

run "two_vms_three_subnets" {
  command = plan
  assert {
    condition = (
      length(azurerm_linux_virtual_machine.vm) == 2 && length(azurerm_public_ip.vm) == 2 &&
      toset(azurerm_virtual_network.epicbook.address_space) == toset(["10.140.0.0/16"]) &&
      toset(azurerm_subnet.vm["frontend"].address_prefixes) == toset(["10.140.1.0/24"]) &&
      toset(azurerm_subnet.vm["backend"].address_prefixes) == toset(["10.140.2.0/24"]) &&
      toset(azurerm_subnet.database.address_prefixes) == toset(["10.140.3.0/24"])
    )
    error_message = "Keep exactly two VMs and separate frontend, backend and delegated database subnets."
  }
  assert {
    condition = alltrue([for vm in azurerm_linux_virtual_machine.vm :
      vm.disable_password_authentication && vm.secure_boot_enabled && vm.vtpm_enabled &&
      vm.size == "Standard_D2lds_v6" && vm.disk_controller_type == "NVMe" &&
      vm.source_image_reference[0].version == "0.0.0" && vm.os_disk[0].disk_size_gb == 32 &&
      vm.tags.assignment == "week10-a4" && vm.tags.learner == "Eze Favour"
    ])
    error_message = "VM identity, key-only access, pinned image and bounded lab shape must remain explicit."
  }
}

run "restricted_network_paths" {
  command = plan
  assert {
    condition = alltrue([for nsg in azurerm_network_security_group.vm :
      [for r in nsg.security_rule : r if r.name == "SSHFromControllerAndAgent"][0].destination_port_range == "22" &&
      toset([for r in nsg.security_rule : r if r.name == "SSHFromControllerAndAgent"][0].source_address_prefixes) == toset(["8.8.4.4/32", "8.8.8.8/32"]) &&
      [for r in nsg.security_rule : r if r.name == "DenyOtherInbound"][0].access == "Deny"
    ])
    error_message = "SSH must be limited to both approved /32 sources, with other inbound traffic denied."
  }
  assert {
    condition = (
      [for r in azurerm_network_security_group.vm["frontend"].security_rule : r if r.name == "PublicHTTP"][0].source_address_prefix == "Internet" &&
      [for r in azurerm_network_security_group.vm["frontend"].security_rule : r if r.name == "PublicHTTP"][0].destination_port_range == "80" &&
      [for r in azurerm_network_security_group.vm["backend"].security_rule : r if r.name == "PrivateApplication"][0].source_address_prefix == "10.140.1.4/32" &&
      [for r in azurerm_network_security_group.vm["backend"].security_rule : r if r.name == "PrivateApplication"][0].destination_port_range == "8080" &&
      azurerm_network_interface.vm["frontend"].ip_configuration[0].private_ip_address == "10.140.1.4" &&
      azurerm_network_interface.vm["backend"].ip_configuration[0].private_ip_address == "10.140.2.4"
    )
    error_message = "Only HTTP is public; the frontend private address alone reaches the backend application."
  }
}

run "private_database_and_tls" {
  command = plan
  assert {
    condition = (
      azurerm_mysql_flexible_server.mysql.public_network_access == "Disabled" &&
      azurerm_mysql_flexible_server.mysql.version == "8.0.21" &&
      azurerm_mysql_flexible_server.mysql.storage[0].size_gb == 20 &&
      !azurerm_mysql_flexible_server.mysql.storage[0].auto_grow_enabled &&
      azurerm_mysql_flexible_server.mysql.administrator_password == null &&
      azurerm_mysql_flexible_server.mysql.administrator_password_wo_version == 1 &&
      azurerm_mysql_flexible_server_configuration.tls["require_secure_transport"].value == "ON" &&
      azurerm_mysql_flexible_server_configuration.tls["tls_version"].value == "TLSv1.2" &&
      azurerm_mysql_flexible_database.bookstore.name == "bookstore"
    )
    error_message = "Keep private MySQL, write-only credentials, TLS and bounded storage; no schema/seed execution is implied."
  }
  assert {
    condition = (
      toset([for r in azurerm_network_security_group.database.security_rule : r if r.name == "MySQLFromBackendAndDatabaseSubnet"][0].source_address_prefixes) == toset(["10.140.2.4/32", "10.140.3.0/24"]) &&
      [for r in azurerm_network_security_group.database.security_rule : r if r.name == "DenyOtherMySQL"][0].access == "Deny" &&
      azurerm_subnet.database.delegation[0].service_delegation[0].name == "Microsoft.DBforMySQL/flexibleServers" &&
      !azurerm_private_dns_zone_virtual_network_link.mysql.registration_enabled
    )
    error_message = "Keep database delegation, linked private DNS and database-port isolation."
  }
}

run "four_handoff_outputs" {
  command = plan
  assert {
    condition = (
      output.app_public_ip == "8.8.4.4" && output.backend_ansible_host == "8.8.8.8" &&
      output.backend_private_ip == "10.140.2.4" && output.mysql_fqdn == "fixture-mysql.mysql.database.azure.com"
    )
    error_message = "Preserve the four-value direct-SSH handoff contract."
  }
}

run "identity_mismatch" {
  command = plan
  variables { operator_object_id = "00000000-0000-0000-0000-000000000099" }
  expect_failures = [azurerm_resource_group.epicbook]
}

run "subscription_mismatch" {
  command = plan
  variables { subscription_id = "00000000-0000-0000-0000-000000000099" }
  expect_failures = [azurerm_resource_group.epicbook]
}

run "tenant_mismatch" {
  command = plan
  variables { tenant_id = "00000000-0000-0000-0000-000000000099" }
  expect_failures = [azurerm_resource_group.epicbook]
}

run "client_mismatch" {
  command = plan
  variables { client_id = "00000000-0000-0000-0000-000000000099" }
  expect_failures = [azurerm_resource_group.epicbook]
}

run "wrong_assignment_prefix" {
  command = plan
  variables { name_prefix = "dmi-w10-a2-fixture" }
  expect_failures = [var.name_prefix]
}

run "latest_image_rejected" {
  command = plan
  variables { image_version = "latest" }
  expect_failures = [var.image_version]
}

run "private_key_rejected" {
  command = plan
  variables { operator_public_key = "TEST-ONLY-NOT-A-PUBLIC-KEY" }
  expect_failures = [var.operator_public_key]
}

run "weak_database_secret_rejected" {
  command = plan
  variables { mysql_admin_password = "TEST-ONLY" }
  expect_failures = [var.mysql_admin_password]
}

run "password_rotation_version_rejected" {
  command = plan
  variables { mysql_password_version = 0 }
  expect_failures = [var.mysql_password_version]
}

run "world_open_ssh_rejected" {
  command = plan
  variables { controller_ipv4_cidr = "0.0.0.0/0" }
  expect_failures = [terraform_data.authorization]
}

run "private_agent_rejected" {
  command = plan
  variables { agent_ipv4_cidr = "10.140.1.4/32" }
  expect_failures = [terraform_data.authorization]
}

run "documentation_address_rejected" {
  command = plan
  variables { agent_ipv4_cidr = "203.0.113.4/32" }
  expect_failures = [terraform_data.authorization]
}

run "invalid_octet_rejected" {
  command = plan
  variables { agent_ipv4_cidr = "8.8.8.999/32" }
  expect_failures = [terraform_data.authorization]
}

run "multicast_rejected" {
  command = plan
  variables { agent_ipv4_cidr = "224.0.0.1/32" }
  expect_failures = [terraform_data.authorization]
}

run "carrier_nat_rejected" {
  command = plan
  variables { agent_ipv4_cidr = "100.64.0.1/32" }
  expect_failures = [terraform_data.authorization]
}

run "approval_required" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = false,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "state_readiness_required" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = false, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "cleanup_readiness_required" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = false,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "wrong_approval_scope" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a2", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [var.approval]
}

run "expired_window" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timeadd(timestamp(), "-4h"), expires_at = timeadd(timestamp(), "-1h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "future_window" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timeadd(timestamp(), "1h"), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "overlong_window" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "25h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "cleanup_margin_missing" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "1h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [terraform_data.authorization]
}

run "budget_exceeded" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 3, planning_allowance_usd = 2
    }
  }
  expect_failures = [var.approval]
}

run "zero_estimate" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = timestamp(), expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 0, planning_allowance_usd = 2
    }
  }
  expect_failures = [var.approval]
}

run "malformed_timestamp" {
  command = plan
  variables {
    approval = {
      scope               = "week10-a4-two-vms-private-mysql", live_execution_approved = true,
      remote_state_ready  = true, cleanup_safeguard_ready = true,
      approved_at         = "not-a-timestamp", expires_at = timeadd(timestamp(), "4h"),
      estimated_total_usd = 1, planning_allowance_usd = 2
    }
  }
  expect_failures = [var.approval]
}
