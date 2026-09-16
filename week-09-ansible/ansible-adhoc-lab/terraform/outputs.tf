output "public_ips" {
  description = "Role-name to public IPv4 mapping. Save locally after approved apply; never commit the real values."
  value       = { for name, ip in azurerm_public_ip.hosts : name => ip.ip_address }
}

output "web_urls" {
  description = "Controller-only HTTP URLs for the same web hosts reused by Assignment 3."
  value       = { for name, ip in azurerm_public_ip.hosts : name => "http://${ip.ip_address}" if local.hosts[name] == "web" }
}
