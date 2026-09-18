data "azurerm_client_config" "current" {}

resource "terraform_data" "authorization" {
  input = {
    assignment = "week-10-assignment-01"
    expires_at = var.expires_at
  }

  lifecycle {
    precondition {
      condition     = var.live_execution_approved
      error_message = "Fresh authorization is required before any live plan or apply."
    }
    precondition {
      condition = (
        data.azurerm_client_config.current.subscription_id == var.subscription_id &&
        data.azurerm_client_config.current.tenant_id == var.tenant_id &&
        data.azurerm_client_config.current.object_id == var.operator_object_id
      )
      error_message = "The active Azure identity does not match the approved context."
    }
    precondition {
      condition     = timecmp(var.expires_at, timestamp()) > 0
      error_message = "The approved lab lifetime has expired. Cleanup remains separately required."
    }
  }
}

locals {
  tags = {
    assignment = "week-10-assignment-01"
    learner    = "Eze Favour"
    managed_by = "Terraform"
    expires_at = var.expires_at
  }
}

resource "azurerm_resource_group" "agent" {
  name       = "${var.project_name}-rg"
  location   = var.location
  tags       = local.tags
  depends_on = [terraform_data.authorization]
}

resource "azurerm_virtual_network" "agent" {
  name                = "${var.project_name}-vnet"
  resource_group_name = azurerm_resource_group.agent.name
  location            = azurerm_resource_group.agent.location
  address_space       = ["10.110.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "agent" {
  name                 = "${var.project_name}-subnet"
  resource_group_name  = azurerm_resource_group.agent.name
  virtual_network_name = azurerm_virtual_network.agent.name
  address_prefixes     = ["10.110.1.0/24"]
}

resource "azurerm_public_ip" "agent" {
  name                = "${var.project_name}-ip"
  resource_group_name = azurerm_resource_group.agent.name
  location            = azurerm_resource_group.agent.location
  allocation_method   = "Static"
  sku                 = "Standard"
  ip_version          = "IPv4"
  tags                = local.tags
}

resource "azurerm_network_security_group" "agent" {
  name                = "${var.project_name}-nsg"
  resource_group_name = azurerm_resource_group.agent.name
  location            = azurerm_resource_group.agent.location
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

resource "azurerm_network_interface" "agent" {
  name                = "${var.project_name}-nic"
  resource_group_name = azurerm_resource_group.agent.name
  location            = azurerm_resource_group.agent.location
  tags                = local.tags

  ip_configuration {
    name                          = "primary"
    subnet_id                     = azurerm_subnet.agent.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.agent.id
  }
}

resource "azurerm_network_interface_security_group_association" "agent" {
  network_interface_id      = azurerm_network_interface.agent.id
  network_security_group_id = azurerm_network_security_group.agent.id
}

resource "azurerm_linux_virtual_machine" "agent" {
  name                            = "${var.project_name}-vm"
  resource_group_name             = azurerm_resource_group.agent.name
  location                        = azurerm_resource_group.agent.location
  size                            = var.vm_size
  disk_controller_type            = "NVMe"
  secure_boot_enabled             = true
  vtpm_enabled                    = true
  admin_username                  = "labadmin"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.agent.id]
  custom_data                     = filebase64("${path.module}/cloud-init.yaml")
  tags                            = local.tags

  boot_diagnostics {}

  admin_ssh_key {
    username   = "labadmin"
    public_key = trimspace(var.ssh_public_key)
  }

  os_disk {
    name                 = "${var.project_name}-osdisk"
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

  depends_on = [azurerm_network_interface_security_group_association.agent]
}

output "resource_group_name" {
  value = azurerm_resource_group.agent.name
}

output "vm_name" {
  value = azurerm_linux_virtual_machine.agent.name
}

output "public_ip_address" {
  sensitive = true
  value     = azurerm_public_ip.agent.ip_address
}
