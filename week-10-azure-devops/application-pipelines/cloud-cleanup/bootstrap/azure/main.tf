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
  storage_use_azuread             = true
  features {}
}

data "azurerm_client_config" "current" {}

locals {
  prefix = "dmi-w10-cleanup-${var.lease_id}"
  tags = {
    assignment    = "week10-cleanup-canary"
    cleanup_lease = var.lease_id
    managed_by    = "terraform"
  }
}

resource "terraform_data" "authorization" {
  input = var.lease_id
  lifecycle {
    precondition {
      condition = (
        var.live_execution_approved &&
        timecmp(plantimestamp(), var.approval.approved_at) >= 0 &&
        timecmp(plantimestamp(), var.approval.expires_at) < 0 &&
        data.azurerm_client_config.current.subscription_id == var.subscription_id &&
        data.azurerm_client_config.current.tenant_id == var.tenant_id &&
        data.azurerm_client_config.current.object_id == var.bootstrap_operator_object_id
      )
      error_message = "Explicit cleanup bootstrap approval and the exact non-root operator are required. This is not workload authorization."
    }
    precondition {
      condition     = timecmp(timestamp(), var.approval.expires_at) < 0
      error_message = "The control-plane approval must still be valid at apply time."
    }
  }
}

resource "azurerm_resource_group" "control" {
  name       = "${local.prefix}-control-rg"
  location   = "uksouth"
  tags       = local.tags
  depends_on = [terraform_data.authorization]
}

resource "azurerm_user_assigned_identity" "cleanup" {
  name                = "${local.prefix}-identity"
  location            = azurerm_resource_group.control.location
  resource_group_name = azurerm_resource_group.control.name
  tags                = local.tags
}

resource "azurerm_federated_identity_credential" "cleanup" {
  count               = var.federation != null ? 1 : 0
  name                = "azure-pipelines-cleanup"
  resource_group_name = azurerm_resource_group.control.name
  parent_id           = azurerm_user_assigned_identity.cleanup.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = var.federation.issuer
  subject             = var.federation.subject
}

resource "azurerm_storage_account" "state" {
  name                             = "w10cln${var.lease_id}"
  resource_group_name              = azurerm_resource_group.control.name
  location                         = azurerm_resource_group.control.location
  account_tier                     = "Standard"
  account_replication_type         = "LRS"
  account_kind                     = "StorageV2"
  min_tls_version                  = "TLS1_2"
  shared_access_key_enabled        = false
  default_to_oauth_authentication  = true
  allow_nested_items_to_be_public  = false
  https_traffic_only_enabled       = true
  public_network_access_enabled    = true
  cross_tenant_replication_enabled = false
  local_user_enabled               = false
  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }
  tags = local.tags
}

resource "azurerm_role_assignment" "operator_state" {
  scope                = azurerm_storage_account.state.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.bootstrap_operator_object_id
}

resource "azurerm_storage_container" "private" {
  for_each              = toset(["canary-azure", "canary-aws", "receipts"])
  name                  = each.value
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
  depends_on            = [azurerm_role_assignment.operator_state]
}

resource "azurerm_role_assignment" "state" {
  for_each             = azurerm_storage_container.private
  scope                = "${azurerm_storage_account.state.id}/blobServices/default/containers/${each.key}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.cleanup.principal_id
}

resource "azurerm_role_definition" "discovery" {
  name  = "${local.prefix}-discovery"
  scope = "/subscriptions/${var.subscription_id}"
  permissions {
    actions = [
      "Microsoft.Resources/subscriptions/read",
      "Microsoft.Resources/subscriptions/providers/read",
      "Microsoft.Resources/subscriptions/resourceGroups/read",
    ]
  }
  assignable_scopes = ["/subscriptions/${var.subscription_id}"]
  depends_on        = [terraform_data.authorization]
}

resource "azurerm_role_assignment" "discovery" {
  scope              = "/subscriptions/${var.subscription_id}"
  role_definition_id = azurerm_role_definition.discovery.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.cleanup.principal_id
}

resource "azurerm_role_definition" "canary" {
  name  = "${local.prefix}-canary-delete"
  scope = "/subscriptions/${var.subscription_id}"
  permissions {
    actions = [
      "Microsoft.Resources/subscriptions/resourceGroups/read",
      "Microsoft.Resources/subscriptions/resourceGroups/delete",
      "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
    ]
  }
  assignable_scopes = ["/subscriptions/${var.subscription_id}"]
  depends_on        = [terraform_data.authorization]
}

resource "azurerm_role_assignment" "canary" {
  count              = var.canary_group_ready ? 1 : 0
  scope              = "/subscriptions/${var.subscription_id}/resourceGroups/${local.prefix}-canary-rg"
  role_definition_id = azurerm_role_definition.canary.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.cleanup.principal_id
}

output "cleanup_client_id" {
  value = azurerm_user_assigned_identity.cleanup.client_id
}
output "cleanup_principal_id" {
  value = azurerm_user_assigned_identity.cleanup.principal_id
}
output "storage_account_name" {
  value = azurerm_storage_account.state.name
}
