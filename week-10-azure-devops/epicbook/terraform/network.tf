resource "azurerm_virtual_network" "epicbook" {
  name                = "${var.name_prefix}-vnet"
  resource_group_name = azurerm_resource_group.epicbook.name
  location            = var.resource_location
  address_space       = ["10.140.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "vm" {
  for_each = {
    frontend = "10.140.1.0/24"
    backend  = "10.140.2.0/24"
  }
  name                 = each.key
  resource_group_name  = azurerm_resource_group.epicbook.name
  virtual_network_name = azurerm_virtual_network.epicbook.name
  address_prefixes     = [each.value]
}

resource "azurerm_subnet" "database" {
  name                 = "database"
  resource_group_name  = azurerm_resource_group.epicbook.name
  virtual_network_name = azurerm_virtual_network.epicbook.name
  address_prefixes     = ["10.140.3.0/24"]
  service_endpoints    = ["Microsoft.Storage"]
  delegation {
    name = "mysql"
    service_delegation {
      name    = "Microsoft.DBforMySQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_network_security_group" "vm" {
  for_each            = toset(["frontend", "backend"])
  name                = "${var.name_prefix}-${each.key}-nsg"
  resource_group_name = azurerm_resource_group.epicbook.name
  location            = var.resource_location
  tags                = local.tags
  security_rule {
    name                       = "SSHFromControllerAndAgent"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefixes    = local.ssh_cidrs
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = each.key == "frontend" ? "PublicHTTP" : "PrivateApplication"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = each.key == "frontend" ? "80" : "8080"
    source_address_prefix      = each.key == "frontend" ? "Internet" : "10.140.1.4/32"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "DenyOtherInbound"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_security_group" "database" {
  name                = "${var.name_prefix}-database-nsg"
  resource_group_name = azurerm_resource_group.epicbook.name
  location            = var.resource_location
  tags                = local.tags
  security_rule {
    name                       = "MySQLFromBackendAndDatabaseSubnet"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3306"
    source_address_prefixes    = ["10.140.2.4/32", "10.140.3.0/24"]
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "DenyOtherMySQL"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3306"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "vm" {
  for_each                  = toset(["frontend", "backend"])
  subnet_id                 = azurerm_subnet.vm[each.key].id
  network_security_group_id = azurerm_network_security_group.vm[each.key].id
}

resource "azurerm_subnet_network_security_group_association" "database" {
  subnet_id                 = azurerm_subnet.database.id
  network_security_group_id = azurerm_network_security_group.database.id
}

resource "azurerm_public_ip" "vm" {
  for_each            = toset(["frontend", "backend"])
  name                = "${var.name_prefix}-${each.key}-ip"
  resource_group_name = azurerm_resource_group.epicbook.name
  location            = var.resource_location
  allocation_method   = "Static"
  sku                 = "Standard"
  ip_version          = "IPv4"
  tags                = local.tags
}

resource "azurerm_network_interface" "vm" {
  for_each = {
    frontend = "10.140.1.4"
    backend  = "10.140.2.4"
  }
  name                = "${var.name_prefix}-${each.key}-nic"
  resource_group_name = azurerm_resource_group.epicbook.name
  location            = var.resource_location
  tags                = local.tags
  ip_configuration {
    name                          = "primary"
    subnet_id                     = azurerm_subnet.vm[each.key].id
    private_ip_address_allocation = "Static"
    private_ip_address            = each.value
    public_ip_address_id          = azurerm_public_ip.vm[each.key].id
  }
  depends_on = [azurerm_subnet_network_security_group_association.vm]
}
