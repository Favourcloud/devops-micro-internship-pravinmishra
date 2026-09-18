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
