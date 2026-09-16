locals {
  name = "week09-a5-epicbook-${var.run_id}"
  tags = {
    Project   = "week09-assignment05-epicbook"
    ManagedBy = "Terraform"
  }
}

resource "azurerm_resource_group" "epicbook" {
  name     = "${local.name}-rg"
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "epicbook" {
  name                = "${local.name}-vnet"
  location            = azurerm_resource_group.epicbook.location
  resource_group_name = azurerm_resource_group.epicbook.name
  address_space       = ["10.95.0.0/24"]
  tags                = local.tags
}

resource "azurerm_subnet" "web" {
  name                 = "web"
  resource_group_name  = azurerm_resource_group.epicbook.name
  virtual_network_name = azurerm_virtual_network.epicbook.name
  address_prefixes     = ["10.95.0.0/26"]
}

resource "azurerm_network_security_group" "web" {
  name                = "${local.name}-nsg"
  location            = azurerm_resource_group.epicbook.location
  resource_group_name = azurerm_resource_group.epicbook.name
  tags                = local.tags
}

resource "azurerm_network_security_rule" "ssh" {
  name                        = "ControllerSSH"
  priority                    = 100
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "22"
  source_address_prefix       = var.controller_cidr
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.epicbook.name
  network_security_group_name = azurerm_network_security_group.web.name
}

resource "azurerm_network_security_rule" "http" {
  name                        = "PublicHTTP"
  priority                    = 110
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_port_range           = "*"
  destination_port_range      = "80"
  source_address_prefix       = "Internet"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.epicbook.name
  network_security_group_name = azurerm_network_security_group.web.name
}

resource "azurerm_network_security_rule" "deny_other_inbound" {
  name                        = "DenyOtherInbound"
  priority                    = 200
  direction                   = "Inbound"
  access                      = "Deny"
  protocol                    = "*"
  source_port_range           = "*"
  destination_port_range      = "*"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = azurerm_resource_group.epicbook.name
  network_security_group_name = azurerm_network_security_group.web.name
}

resource "azurerm_public_ip" "web" {
  name                = "${local.name}-ip"
  location            = azurerm_resource_group.epicbook.location
  resource_group_name = azurerm_resource_group.epicbook.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = local.tags
}

resource "azurerm_network_interface" "web" {
  name                = "${local.name}-nic"
  location            = azurerm_resource_group.epicbook.location
  resource_group_name = azurerm_resource_group.epicbook.name
  tags                = local.tags

  ip_configuration {
    name                          = "web"
    subnet_id                     = azurerm_subnet.web.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.web.id
  }
}

resource "azurerm_network_interface_security_group_association" "web" {
  network_interface_id      = azurerm_network_interface.web.id
  network_security_group_id = azurerm_network_security_group.web.id
}

resource "azurerm_linux_virtual_machine" "web" {
  name                            = "${local.name}-vm"
  location                        = azurerm_resource_group.epicbook.location
  resource_group_name             = azurerm_resource_group.epicbook.name
  size                            = var.vm_size
  admin_username                  = "ubuntu"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.web.id]
  secure_boot_enabled             = true
  vtpm_enabled                    = true
  tags                            = local.tags

  boot_diagnostics {}

  admin_ssh_key {
    username   = "ubuntu"
    public_key = var.ssh_public_key
  }

  # Azure managed disks use platform-managed encryption at rest by default.
  os_disk {
    name                 = "${local.name}-os"
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = var.os_disk_gib
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  depends_on = [
    azurerm_network_interface_security_group_association.web,
    azurerm_network_security_rule.ssh,
    azurerm_network_security_rule.http,
    azurerm_network_security_rule.deny_other_inbound,
  ]
}
