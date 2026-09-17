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
    assignment = "week-08-assignment-03"
    learner    = "Eze Favour"
    managed_by = "Terraform"
  }
}

resource "azurerm_resource_group" "app" {
  name     = "${var.project_name}-rg"
  location = var.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "app" {
  name                = "${var.project_name}-vnet"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
  address_space       = ["10.83.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "app" {
  name                 = "${var.project_name}-subnet"
  resource_group_name  = azurerm_resource_group.app.name
  virtual_network_name = azurerm_virtual_network.app.name
  address_prefixes     = ["10.83.1.0/24"]
}

resource "azurerm_network_security_group" "app" {
  name                = "${var.project_name}-nsg"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
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

  security_rule {
    name                       = "PublicHTTP"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Override Azure's default VNet/LB inbound allows, not just Internet traffic.
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

resource "azurerm_public_ip" "app" {
  name                = "${var.project_name}-ip"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
  allocation_method   = "Static"
  sku                 = "Standard"
  ip_version          = "IPv4"
  tags                = local.tags
}

resource "azurerm_network_interface" "app" {
  name                = "${var.project_name}-nic"
  location            = azurerm_resource_group.app.location
  resource_group_name = azurerm_resource_group.app.name
  tags                = local.tags

  ip_configuration {
    name                          = "primary"
    subnet_id                     = azurerm_subnet.app.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.app.id
  }
}

resource "azurerm_network_interface_security_group_association" "app" {
  network_interface_id      = azurerm_network_interface.app.id
  network_security_group_id = azurerm_network_security_group.app.id
}

resource "azurerm_linux_virtual_machine" "app" {
  name                            = "${var.project_name}-vm"
  location                        = azurerm_resource_group.app.location
  resource_group_name             = azurerm_resource_group.app.name
  size                            = var.vm_size
  admin_username                  = var.admin_username
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.app.id]
  custom_data                     = base64encode(file("${path.module}/cloud-init.sh"))
  tags                            = local.tags

  admin_ssh_key {
    username   = var.admin_username
    public_key = var.admin_ssh_public_key
  }

  # Managed OS disks use Azure platform-managed encryption at rest by default.
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 32
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }

  depends_on = [azurerm_network_interface_security_group_association.app]
}

output "public_ip_address" {
  description = "Public IPv4 allocated only by a future authorized deployment, not a readiness signal."
  value       = azurerm_public_ip.app.ip_address
}

output "resource_group_name" {
  description = "Name for later authorized cleanup verification."
  value       = azurerm_resource_group.app.name
}

output "vm_name" {
  description = "Name for later authorized VM verification."
  value       = azurerm_linux_virtual_machine.app.name
}
