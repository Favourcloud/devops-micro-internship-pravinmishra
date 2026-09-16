locals {
  tags = {
    project    = "dmi-mini-finance"
    assignment = "week-09-assignment-04"
    managed_by = "terraform"
  }
}

resource "azurerm_resource_group" "site" {
  name     = "${var.name_prefix}-rg"
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "site" {
  name                = "${var.name_prefix}-vnet"
  location            = azurerm_resource_group.site.location
  resource_group_name = azurerm_resource_group.site.name
  address_space       = ["10.42.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "site" {
  name                 = "${var.name_prefix}-subnet"
  resource_group_name  = azurerm_resource_group.site.name
  virtual_network_name = azurerm_virtual_network.site.name
  address_prefixes     = ["10.42.1.0/24"]
}

resource "azurerm_network_security_group" "site" {
  name                = "${var.name_prefix}-nsg"
  location            = azurerm_resource_group.site.location
  resource_group_name = azurerm_resource_group.site.name
  tags                = local.tags

  security_rule {
    name                       = "SSHFromController"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.controller_cidr
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "PublicHTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  # Override Azure's default VNet inbound allowance for this dedicated NIC.
  security_rule {
    name                       = "DenyOtherInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_public_ip" "site" {
  name                = "${var.name_prefix}-ip"
  location            = azurerm_resource_group.site.location
  resource_group_name = azurerm_resource_group.site.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = local.tags
}

resource "azurerm_network_interface" "site" {
  name                = "${var.name_prefix}-nic"
  location            = azurerm_resource_group.site.location
  resource_group_name = azurerm_resource_group.site.name
  tags                = local.tags

  ip_configuration {
    name                          = "public"
    subnet_id                     = azurerm_subnet.site.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.site.id
  }
}

resource "azurerm_network_interface_security_group_association" "site" {
  network_interface_id      = azurerm_network_interface.site.id
  network_security_group_id = azurerm_network_security_group.site.id
}

resource "azurerm_linux_virtual_machine" "site" {
  name                            = "${var.name_prefix}-vm"
  location                        = azurerm_resource_group.site.location
  resource_group_name             = azurerm_resource_group.site.name
  size                            = "Standard_B1s"
  admin_username                  = var.admin_username
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.site.id]
  tags                            = local.tags

  admin_ssh_key {
    username   = var.admin_username
    public_key = trimspace(var.ssh_public_key)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 32
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  depends_on = [azurerm_network_interface_security_group_association.site]
}
