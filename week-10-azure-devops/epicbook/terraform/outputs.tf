output "app_public_ip" {
  description = "Frontend public IPv4; release only this approved handoff value, not state or plan JSON."
  value       = azurerm_public_ip.vm["frontend"].ip_address
}

output "backend_ansible_host" {
  description = "Backend public IPv4 for direct SSH from the two allowlisted /32 sources only."
  value       = azurerm_public_ip.vm["backend"].ip_address
}

output "backend_private_ip" {
  description = "Backend private IPv4 for Nginx's upstream, not a public application endpoint."
  value       = azurerm_network_interface.vm["backend"].private_ip_address
}

output "mysql_fqdn" {
  description = "Canonical private-access MySQL hostname; verify private DNS/TLS before application use."
  value       = azurerm_mysql_flexible_server.mysql.fqdn
}
