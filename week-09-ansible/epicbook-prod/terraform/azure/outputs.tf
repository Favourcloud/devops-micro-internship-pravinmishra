output "public_ip" {
  description = "Web VM IPv4 address for the guarded local inventory renderer."
  value       = azurerm_public_ip.web.ip_address
}

output "admin_user" {
  description = "Explicit Ubuntu VM SSH administrator."
  value       = azurerm_linux_virtual_machine.web.admin_username
}
