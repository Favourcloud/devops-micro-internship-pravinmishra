output "public_ip" {
  description = "Actual Azure public IPv4 address, available only after an authorized successful apply."
  value       = azurerm_public_ip.site.ip_address
}
