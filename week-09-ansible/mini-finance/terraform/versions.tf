terraform {
  required_version = ">= 1.9.8, < 2.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.47.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }

  # Provider registration is subscription-wide; an authorized owner must handle it.
  resource_provider_registrations = "none"
}
