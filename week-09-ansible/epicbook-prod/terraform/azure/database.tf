variable "mysql_location" {
  description = "Region with verified managed MySQL subscription availability. A peered private VNet preserves the existing application VM."
  type = string
  default = "swedencentral"
  validation {
    condition = contains(["swedencentral", "northeurope", "westeurope", "eastus"], var.mysql_location)
    error_message = "Use a region checked for MySQL availability."
  }
}

resource "azurerm_virtual_network" "database" {
  count = var.managed_mysql_enabled ? 1 : 0
  name = "${local.name}-database-vnet"
  resource_group_name = azurerm_resource_group.epicbook.name
  location = var.mysql_location
  address_space = ["10.96.0.0/24"]
  tags = local.tags
}

resource "azurerm_virtual_network_peering" "app_to_database" {
  count = var.managed_mysql_enabled ? 1 : 0
  name = "app-to-database"
  resource_group_name = azurerm_resource_group.epicbook.name
  virtual_network_name = azurerm_virtual_network.epicbook.name
  remote_virtual_network_id = azurerm_virtual_network.database[0].id
  allow_virtual_network_access = true
}

resource "azurerm_virtual_network_peering" "database_to_app" {
  count = var.managed_mysql_enabled ? 1 : 0
  name = "database-to-app"
  resource_group_name = azurerm_resource_group.epicbook.name
  virtual_network_name = azurerm_virtual_network.database[0].name
  remote_virtual_network_id = azurerm_virtual_network.epicbook.id
  allow_virtual_network_access = true
}

resource "azurerm_private_dns_zone_virtual_network_link" "database" {
  count = var.managed_mysql_enabled ? 1 : 0
  name = "database-mysql"
  resource_group_name = azurerm_resource_group.epicbook.name
  private_dns_zone_name = azurerm_private_dns_zone.mysql[0].name
  virtual_network_id = azurerm_virtual_network.database[0].id
  registration_enabled = false
}

resource "azurerm_network_security_group" "database" {
  count = var.managed_mysql_enabled ? 1 : 0
  name = "${local.name}-database-nsg"
  resource_group_name = azurerm_resource_group.epicbook.name
  location = var.mysql_location
  tags = local.tags
  security_rule {
    name = "MySQLFromAppAndDatabaseSubnet"
    priority = 100
    direction = "Inbound"
    access = "Allow"
    protocol = "Tcp"
    source_port_range = "*"
    destination_port_range = "3306"
    source_address_prefixes = ["10.95.0.0/26", "10.96.0.0/26"]
    destination_address_prefix = "*"
  }
  security_rule {
    name = "DenyOtherMySQL"
    priority = 200
    direction = "Inbound"
    access = "Deny"
    protocol = "Tcp"
    source_port_range = "*"
    destination_port_range = "3306"
    source_address_prefix = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "database" {
  count = var.managed_mysql_enabled ? 1 : 0
  subnet_id = azurerm_subnet.database[0].id
  network_security_group_id = azurerm_network_security_group.database[0].id
}

variable "managed_mysql_enabled" {
  type    = bool
  default = false
}

variable "mysql_admin_password" {
  type      = string
  sensitive = true
  ephemeral = true
  default   = null
}

resource "azurerm_subnet" "database" {
  count                = var.managed_mysql_enabled ? 1 : 0
  name                 = "database"
  resource_group_name  = azurerm_resource_group.epicbook.name
  virtual_network_name = azurerm_virtual_network.database[0].name
  address_prefixes     = ["10.96.0.0/26"]
  service_endpoints    = ["Microsoft.Storage"]
  delegation {
    name = "mysql"
    service_delegation {
      name    = "Microsoft.DBforMySQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_private_dns_zone" "mysql" {
  count               = var.managed_mysql_enabled ? 1 : 0
  name                = "${local.name}.mysql.database.azure.com"
  resource_group_name = azurerm_resource_group.epicbook.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "mysql" {
  count                 = var.managed_mysql_enabled ? 1 : 0
  name                  = "epicbook-mysql"
  resource_group_name   = azurerm_resource_group.epicbook.name
  private_dns_zone_name = azurerm_private_dns_zone.mysql[0].name
  virtual_network_id    = azurerm_virtual_network.epicbook.id
  registration_enabled  = false
}

resource "azurerm_mysql_flexible_server" "mysql" {
  count                             = var.managed_mysql_enabled ? 1 : 0
  name                              = "${local.name}-mysql-se"
  resource_group_name               = azurerm_resource_group.epicbook.name
  location                          = var.mysql_location
  administrator_login               = "epicadmin"
  administrator_password_wo         = var.mysql_admin_password
  administrator_password_wo_version = 1
  create_mode                       = "Default"
  version                           = "8.0.21"
  sku_name                          = "B_Standard_B1ms"
  delegated_subnet_id                = azurerm_subnet.database[0].id
  private_dns_zone_id                = azurerm_private_dns_zone.mysql[0].id
  public_network_access             = "Disabled"
  backup_retention_days             = 7
  geo_redundant_backup_enabled       = false
  storage {
    size_gb            = 20
    auto_grow_enabled  = false
    io_scaling_enabled = false
  }
  tags       = local.tags
  depends_on = [azurerm_private_dns_zone_virtual_network_link.mysql, azurerm_private_dns_zone_virtual_network_link.database, azurerm_subnet_network_security_group_association.database]
}

resource "azurerm_mysql_flexible_server_configuration" "tls" {
  for_each = var.managed_mysql_enabled ? {
    require_secure_transport = "ON"
    tls_version              = "TLSv1.2"
  } : {}
  name                = each.key
  resource_group_name = azurerm_resource_group.epicbook.name
  server_name         = azurerm_mysql_flexible_server.mysql[0].name
  value               = each.value
}

resource "azurerm_mysql_flexible_database" "bookstore" {
  count               = var.managed_mysql_enabled ? 1 : 0
  name                = "bookstore"
  resource_group_name = azurerm_resource_group.epicbook.name
  server_name         = azurerm_mysql_flexible_server.mysql[0].name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

output "mysql_fqdn" {
  value = var.managed_mysql_enabled ? azurerm_mysql_flexible_server.mysql[0].fqdn : null
}
