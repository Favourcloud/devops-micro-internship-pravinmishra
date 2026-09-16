locals {
  hosts = {
    web1 = "web"
    web2 = "web"
    app1 = "app"
    db1  = "db"
  }
  tags = {
    Project   = var.lab_name
    Course    = "Week09-Ansible"
    ManagedBy = "Terraform"
  }
}

resource "azurerm_resource_group" "lab" {
  name     = "${var.lab_name}-rg"
  location = var.azure_location
  tags     = local.tags
}

resource "azurerm_virtual_network" "lab" {
  name                = "${var.lab_name}-vnet"
  address_space       = ["10.90.0.0/16"]
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = local.tags
}

resource "azurerm_subnet" "lab" {
  name                            = "${var.lab_name}-subnet"
  resource_group_name             = azurerm_resource_group.lab.name
  virtual_network_name            = azurerm_virtual_network.lab.name
  address_prefixes                = ["10.90.1.0/24"]
  default_outbound_access_enabled = false
}

resource "azurerm_public_ip" "hosts" {
  for_each            = local.hosts
  name                = "${var.lab_name}-${each.key}-ip"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = merge(local.tags, { Role = each.value })
}

resource "azurerm_network_interface" "hosts" {
  for_each            = local.hosts
  name                = "${var.lab_name}-${each.key}-nic"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = merge(local.tags, { Role = each.value })

  ip_configuration {
    name                          = "primary"
    subnet_id                     = azurerm_subnet.lab.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.hosts[each.key].id
  }
}

resource "azurerm_network_security_group" "hosts" {
  for_each            = local.hosts
  name                = "${var.lab_name}-${each.key}-nsg"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = merge(local.tags, { Role = each.value })

  security_rule {
    name                       = "SSHFromController"
    description                = "SSH from the approved controller only"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.controller_ipv4_cidr
    destination_address_prefix = "*"
  }

  dynamic "security_rule" {
    for_each = each.value == "web" ? [1] : []
    content {
      name                       = "HTTPFromController"
      description                = "Website verification on web hosts only"
      priority                   = 110
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "80"
      source_address_prefix      = var.controller_ipv4_cidr
      destination_address_prefix = "*"
    }
  }

  # Override Azure's default AllowVNetInBound rule as well as public ingress.
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

resource "azurerm_network_interface_security_group_association" "hosts" {
  for_each                  = local.hosts
  network_interface_id      = azurerm_network_interface.hosts[each.key].id
  network_security_group_id = azurerm_network_security_group.hosts[each.key].id
}

resource "azurerm_linux_virtual_machine" "hosts" {
  for_each                        = local.hosts
  name                            = "${var.lab_name}-${each.key}"
  computer_name                   = each.key
  location                        = azurerm_resource_group.lab.location
  resource_group_name             = azurerm_resource_group.lab.name
  size                            = "Standard_B1s"
  admin_username                  = "azureuser"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.hosts[each.key].id]
  tags                            = merge(local.tags, { Role = each.value })

  admin_ssh_key {
    username   = "azureuser"
    public_key = trimspace(var.ssh_public_key)
  }

  os_disk {
    name                 = "${var.lab_name}-${each.key}-os"
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

  boot_diagnostics {}

  depends_on = [azurerm_network_interface_security_group_association.hosts]
}
