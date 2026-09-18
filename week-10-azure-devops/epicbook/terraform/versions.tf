terraform {
  required_version = "~> 1.13.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.47.0"
    }
  }
  backend "azurerm" {
    use_azuread_auth = true
    use_oidc         = true
  }
}

provider "azurerm" {
  subscription_id                 = var.subscription_id
  tenant_id                       = var.tenant_id
  client_id                       = var.client_id
  resource_provider_registrations = "none"
  use_oidc                        = true
  use_cli                         = false
  use_msi                         = false
  features {
    virtual_machine {
      delete_os_disk_on_deletion = true
    }
  }
}
