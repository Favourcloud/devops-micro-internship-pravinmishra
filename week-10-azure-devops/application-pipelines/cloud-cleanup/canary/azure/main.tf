terraform {
  required_version = "~> 1.13.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 4.47.0"
    }
  }
  backend "azurerm" {}
}
provider "azurerm" {
  subscription_id                 = var.subscription_id
  tenant_id                       = var.tenant_id
  resource_provider_registrations = "none"
  use_cli                         = true
  use_msi                         = false
  use_oidc                        = false
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}
data "azurerm_client_config" "current" {}
resource "terraform_data" "authorization" {
  input = var.lease_id
  lifecycle {
    precondition {
      condition = (
        var.live_execution_approved &&
        data.azurerm_client_config.current.subscription_id == var.subscription_id &&
        data.azurerm_client_config.current.tenant_id == var.tenant_id &&
        data.azurerm_client_config.current.object_id == var.operator_object_id &&
        timecmp(plantimestamp(), var.expires_at) < 0 &&
        timecmp(var.expires_at, timeadd(plantimestamp(), "24h")) <= 0
      )
      error_message = "Creating the empty canary RG requires fresh approval, exact identity and a maximum 24-hour expiry."
    }
    precondition {
      condition     = timecmp(timestamp(), var.expires_at) < 0
      error_message = "Canary creation approval must still be valid at apply time."
    }
  }
}
resource "azurerm_resource_group" "canary" {
  name     = "dmi-w10-cleanup-${var.lease_id}-canary-rg"
  location = "uksouth"
  tags = {
    assignment    = "week10-cleanup-canary"
    cleanup_lease = var.lease_id
    expires_at    = var.expires_at
    managed_by    = "terraform"
  }
  depends_on = [terraform_data.authorization]
}
