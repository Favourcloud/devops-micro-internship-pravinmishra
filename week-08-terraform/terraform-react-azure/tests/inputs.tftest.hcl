mock_provider "azurerm" {}

variables {
  location             = "uksouth"
  vm_size              = "Standard_D2s_v5"
  controller_ipv4_cidr = "192.0.2.10/32"
  admin_ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea offline-test-only"
}

run "reject_short_name" {
  command = plan
  variables { project_name = "ab" }
  expect_failures = [var.project_name]
}
run "reject_long_name" {
  command = plan
  variables { project_name = "abcdefghijklmnopqrstuvwxyz12345" }
  expect_failures = [var.project_name]
}
run "reject_uppercase_name" {
  command = plan
  variables { project_name = "DMI-app" }
  expect_failures = [var.project_name]
}
run "reject_trailing_hyphen" {
  command = plan
  variables { project_name = "dmi-app-" }
  expect_failures = [var.project_name]
}
run "reject_empty_region" {
  command = plan
  variables { location = "" }
  expect_failures = [var.location]
}
run "reject_region_display_name" {
  command = plan
  variables { location = "UK South" }
  expect_failures = [var.location]
}
run "reject_empty_sku" {
  command = plan
  variables { vm_size = "" }
  expect_failures = [var.vm_size]
}
run "reject_basic_sku" {
  command = plan
  variables { vm_size = "Basic_A1" }
  expect_failures = [var.vm_size]
}
run "reject_internet_ssh" {
  command = plan
  variables { controller_ipv4_cidr = "0.0.0.0/0" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_broad_ssh" {
  command = plan
  variables { controller_ipv4_cidr = "192.0.2.0/24" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_wildcard_ssh" {
  command = plan
  variables { controller_ipv4_cidr = "*" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_ipv6_ssh" {
  command = plan
  variables { controller_ipv4_cidr = "2001:db8::1/128" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_invalid_ipv4" {
  command = plan
  variables { controller_ipv4_cidr = "999.0.0.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_unspecified_ipv4" {
  command = plan
  variables { controller_ipv4_cidr = "0.0.0.0/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_private_ipv4" {
  command = plan
  variables { controller_ipv4_cidr = "10.0.0.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_private_172" {
  command = plan
  variables { controller_ipv4_cidr = "172.31.0.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_private_192" {
  command = plan
  variables { controller_ipv4_cidr = "192.168.1.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_loopback" {
  command = plan
  variables { controller_ipv4_cidr = "127.0.0.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_link_local" {
  command = plan
  variables { controller_ipv4_cidr = "169.254.1.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_shared_ipv4" {
  command = plan
  variables { controller_ipv4_cidr = "100.64.0.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_multicast_ipv4" {
  command = plan
  variables { controller_ipv4_cidr = "224.0.0.1/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_broadcast_ipv4" {
  command = plan
  variables { controller_ipv4_cidr = "255.255.255.255/32" }
  expect_failures = [var.controller_ipv4_cidr]
}
run "reject_root_user" {
  command = plan
  variables { admin_username = "root" }
  expect_failures = [var.admin_username]
}
run "reject_builder_user" {
  command = plan
  variables { admin_username = "dmi-react-build" }
  expect_failures = [var.admin_username]
}
run "reject_username_case" {
  command = plan
  variables { admin_username = "Learner" }
  expect_failures = [var.admin_username]
}
run "reject_empty_username" {
  command = plan
  variables { admin_username = "" }
  expect_failures = [var.admin_username]
}
run "reject_empty_key" {
  command = plan
  variables { admin_ssh_public_key = "" }
  expect_failures = [var.admin_ssh_public_key]
}
run "reject_key_path" {
  command = plan
  variables { admin_ssh_public_key = "~/.ssh/id_ed25519.pub" }
  expect_failures = [var.admin_ssh_public_key]
}
run "reject_private_key_marker" {
  command = plan
  variables { admin_ssh_public_key = "PRIVATE KEY INPUT IS FORBIDDEN" }
  expect_failures = [var.admin_ssh_public_key]
}
run "reject_malformed_key_blob" {
  command = plan
  variables { admin_ssh_public_key = "ssh-ed25519 aGVsbG8=" }
  expect_failures = [var.admin_ssh_public_key]
}
run "reject_wrong_key_type" {
  command = plan
  variables { admin_ssh_public_key = "ssh-rsa AAAAC3NzaC1lZDI1NTE5AAAAINdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea" }
  expect_failures = [var.admin_ssh_public_key]
}
run "reject_wrong_key_wire_length" {
  command = plan
  variables { admin_ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIZdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea" }
  expect_failures = [var.admin_ssh_public_key]
}
run "reject_key_newline" {
  command = plan
  variables { admin_ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINdamAGCsQq31Uv+08lkBzoO4XLz2qYjJa8CGmj3B1Ea\n" }
  expect_failures = [var.admin_ssh_public_key]
}
