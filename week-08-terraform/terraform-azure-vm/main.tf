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
  features {
    virtual_machine {
      delete_os_disk_on_deletion = true
    }
  }

  resource_provider_registrations = "none"
}

locals {
  tags = {
    assignment = "week-08-assignment-01"
    learner    = "Eze Favour"
    managed_by = "Terraform"
  }
}

resource "azurerm_resource_group" "vm" {
  name     = "${var.project_name}-rg"
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "vm" {
  name                = "${var.project_name}-vnet"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  address_space       = ["10.80.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "vm" {
  name                 = "${var.project_name}-subnet"
  resource_group_name  = azurerm_resource_group.vm.name
  virtual_network_name = azurerm_virtual_network.vm.name
  address_prefixes     = ["10.80.1.0/24"]
}

resource "azurerm_public_ip" "vm" {
  name                = "${var.project_name}-ip"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  allocation_method   = "Static"
  sku                 = "Standard"
  ip_version          = "IPv4"
  tags                = local.tags
}

resource "azurerm_network_security_group" "vm" {
  name                = "${var.project_name}-nsg"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  tags                = local.tags

  security_rule {
    name                       = "SSHFromControllerOnly"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.controller_ipv4_cidr
    destination_address_prefix = "*"
  }

  # Override Azure's default VNet/LB inbound allows; this VM needs only SSH.
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

resource "azurerm_network_interface" "vm" {
  name                = "${var.project_name}-nic"
  location            = azurerm_resource_group.vm.location
  resource_group_name = azurerm_resource_group.vm.name
  tags                = local.tags

  ip_configuration {
    name                          = "primary"
    subnet_id                     = azurerm_subnet.vm.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm.id
  }
}

resource "azurerm_network_interface_security_group_association" "vm" {
  network_interface_id      = azurerm_network_interface.vm.id
  network_security_group_id = azurerm_network_security_group.vm.id
}

resource "azurerm_linux_virtual_machine" "vm" {
  name                            = "${var.project_name}-vm"
  location                        = azurerm_resource_group.vm.location
  resource_group_name             = azurerm_resource_group.vm.name
  size                            = var.vm_size
  admin_username                  = var.admin_username
  admin_password                  = var.admin_password
  disable_password_authentication = false
  network_interface_ids           = [azurerm_network_interface.vm.id]
  tags                            = local.tags

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  depends_on = [azurerm_network_interface_security_group_association.vm]
}

output "public_ip_address" {
  description = "Public IPv4 of the VM, allocated only after an authorized apply."
  value       = azurerm_public_ip.vm.ip_address
}

output "resource_group_name" {
  description = "Resource group name for the authorized Azure CLI verification."
  value       = azurerm_resource_group.vm.name
}

output "vm_name" {
  description = "VM name for the authorized Azure CLI verification."
  value       = azurerm_linux_virtual_machine.vm.name
}
