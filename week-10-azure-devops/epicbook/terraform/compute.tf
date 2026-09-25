resource "azurerm_linux_virtual_machine" "vm" {
  for_each                        = toset(["frontend", "backend"])
  name                            = "${var.name_prefix}-${each.key}-vm"
  resource_group_name             = azurerm_resource_group.epicbook.name
  location                        = var.resource_location
  size                            = "Standard_D2lds_v6"
  disk_controller_type            = "NVMe"
  secure_boot_enabled             = true
  vtpm_enabled                    = true
  admin_username                  = "labadmin"
  disable_password_authentication = true
  network_interface_ids           = [azurerm_network_interface.vm[each.key].id]
  tags                            = local.tags
  boot_diagnostics {}
  admin_ssh_key {
    username   = "labadmin"
    public_key = var.operator_public_key
  }
  os_disk {
    name                 = "${var.name_prefix}-${each.key}-osdisk"
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
}
