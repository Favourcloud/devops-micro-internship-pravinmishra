resource "azurerm_private_dns_zone" "mysql" {
  name                = "${var.name_prefix}.mysql.database.azure.com"
  resource_group_name = azurerm_resource_group.epicbook.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "mysql" {
  name                  = "${var.name_prefix}-mysql-dns"
  resource_group_name   = azurerm_resource_group.epicbook.name
  private_dns_zone_name = azurerm_private_dns_zone.mysql.name
  virtual_network_id    = azurerm_virtual_network.epicbook.id
  registration_enabled  = false
  tags                  = local.tags
}

resource "azurerm_mysql_flexible_server" "mysql" {
  name                              = "${var.name_prefix}-mysql"
  resource_group_name               = azurerm_resource_group.epicbook.name
  location                          = azurerm_resource_group.epicbook.location
  administrator_login               = "epicadmin"
  administrator_password_wo         = var.mysql_admin_password
  administrator_password_wo_version = var.mysql_password_version
  create_mode                       = "Default"
  version                           = "8.0.21"
  sku_name                          = "B_Standard_B1ms"
  delegated_subnet_id               = azurerm_subnet.database.id
  private_dns_zone_id               = azurerm_private_dns_zone.mysql.id
  public_network_access             = "Disabled"
  backup_retention_days             = 7
  geo_redundant_backup_enabled      = false
  tags                              = local.tags
  storage {
    size_gb            = 20
    auto_grow_enabled  = false
    io_scaling_enabled = false
  }
  depends_on = [
    azurerm_private_dns_zone_virtual_network_link.mysql,
    azurerm_subnet_network_security_group_association.database,
  ]
}

resource "azurerm_mysql_flexible_server_configuration" "tls" {
  for_each = {
    require_secure_transport = "ON"
    tls_version              = "TLSv1.2"
  }
  name                = each.key
  resource_group_name = azurerm_resource_group.epicbook.name
  server_name         = azurerm_mysql_flexible_server.mysql.name
  value               = each.value
}

resource "azurerm_mysql_flexible_database" "bookstore" {
  name                = "bookstore"
  resource_group_name = azurerm_resource_group.epicbook.name
  server_name         = azurerm_mysql_flexible_server.mysql.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
  depends_on          = [azurerm_mysql_flexible_server_configuration.tls]
}
