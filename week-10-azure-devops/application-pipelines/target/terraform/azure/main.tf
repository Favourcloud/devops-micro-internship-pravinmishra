terraform {
  required_version = "~> 1.13.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.47.0"
    }
  }
  backend "local" {
    path = ".private/terraform.tfstate"
  }
}

provider "azurerm" {
  subscription_id                 = var.subscription_id
  tenant_id                       = var.tenant_id
  resource_provider_registrations = "none"
  use_cli                         = true
  use_msi                         = false
  use_oidc                        = false
  features {
    virtual_machine {
      delete_os_disk_on_deletion = true
    }
  }
}

module "guard" {
  source               = "../guard"
  assignment           = "week10-a3"
  name_prefix          = var.name_prefix
  controller_ipv4_cidr = var.controller_ipv4_cidr
  agent_ipv4_cidr      = var.agent_ipv4_cidr
  approval             = var.approval
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "target" {
  name       = "${var.name_prefix}-rg"
  location   = "uksouth"
  tags       = module.guard.tags
  depends_on = [module.guard]
  lifecycle {
    precondition {
      condition = (
        data.azurerm_client_config.current.subscription_id == var.subscription_id &&
        data.azurerm_client_config.current.tenant_id == var.tenant_id &&
        data.azurerm_client_config.current.object_id == var.operator_object_id
      )
      error_message = "The active Azure subscription, tenant and operator must match the fresh approved context."
    }
  }
}

resource "azurerm_virtual_network" "target" {
  name                = "${var.name_prefix}-vnet"
  resource_group_name = azurerm_resource_group.target.name
  location            = azurerm_resource_group.target.location
  address_space       = ["10.130.0.0/16"]
  tags                = module.guard.tags
}

resource "azurerm_subnet" "target" {
  name                 = "${var.name_prefix}-subnet"
  resource_group_name  = azurerm_resource_group.target.name
  virtual_network_name = azurerm_virtual_network.target.name
  address_prefixes     = ["10.130.1.0/24"]
}

resource "azurerm_public_ip" "target" {
  name                = "${var.name_prefix}-ip"
  resource_group_name = azurerm_resource_group.target.name
  location            = azurerm_resource_group.target.location
  allocation_method   = "Static"
  sku                 = "Standard"
  ip_version          = "IPv4"
  tags                = module.guard.tags
}

resource "azurerm_network_security_group" "target" {
  name                = "${var.name_prefix}-nsg"
  resource_group_name = azurerm_resource_group.target.name
  location            = azurerm_resource_group.target.location
  tags                = module.guard.tags
  security_rule {
    name                       = "SSHFromControllerAndAgent"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefixes    = module.guard.ssh_cidrs
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "LabHTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "Internet"
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

resource "azurerm_network_interface" "target" {
  name                = "${var.name_prefix}-nic"
  resource_group_name = azurerm_resource_group.target.name
  location            = azurerm_resource_group.target.location
  tags                = module.guard.tags
  ip_configuration {
    name                          = "primary"
    subnet_id                     = azurerm_subnet.target.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.target.id
  }
}

resource "azurerm_network_interface_security_group_association" "target" {
  network_interface_id      = azurerm_network_interface.target.id
  network_security_group_id = azurerm_network_security_group.target.id
}

resource "azurerm_linux_virtual_machine" "target" {
  name                            = "${var.name_prefix}-vm"
  resource_group_name             = azurerm_resource_group.target.name
  location                        = azurerm_resource_group.target.location
  size                            = "Standard_D2lds_v6"
  disk_controller_type            = "NVMe"
  secure_boot_enabled             = true
  vtpm_enabled                    = true
  admin_username                  = "labadmin"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.target.id]
  tags                            = module.guard.tags
  boot_diagnostics {}
  admin_ssh_key {
    username   = "labadmin"
    public_key = var.operator_public_key
  }
  os_disk {
    name                 = "${var.name_prefix}-osdisk"
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 32
  }
  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = var.image_version
  }
  depends_on = [azurerm_network_interface_security_group_association.target]
}

output "target_public_ipv4" {
  value     = azurerm_public_ip.target.ip_address
  sensitive = true
}

output "target_resource_id" {
  value = azurerm_linux_virtual_machine.target.id
}

output "resource_group_name" {
  value = azurerm_resource_group.target.name
}

output "ssh_username" {
  value = "labadmin"
}

output "assignment" {
  value = "week10-a3"
}
