# Synthetic schema/plan fixtures, never cloud authorization or live proof.
mock_provider "azurerm" {
  override_during = plan
  mock_data "azurerm_client_config" {
    defaults = {
      subscription_id = "00000000-0000-0000-0000-000000000001"
      tenant_id       = "00000000-0000-0000-0000-000000000002"
      object_id       = "00000000-0000-0000-0000-000000000004"
    }
  }
  mock_resource "azurerm_resource_group" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-cleanup-abcdef123456-control-rg" }
  }
  mock_resource "azurerm_storage_account" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-cleanup-abcdef123456-control-rg/providers/Microsoft.Storage/storageAccounts/w10clnabcdef123456" }
  }
  mock_resource "azurerm_user_assigned_identity" {
    defaults = {
      id           = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-cleanup-abcdef123456-control-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/dmi-w10-cleanup-abcdef123456-identity"
      principal_id = "00000000-0000-0000-0000-000000000005"
      client_id    = "00000000-0000-0000-0000-000000000006"
    }
  }
  mock_resource "azurerm_role_definition" {
    defaults = { role_definition_resource_id = "/subscriptions/00000000-0000-0000-0000-000000000001/providers/Microsoft.Authorization/roleDefinitions/00000000-0000-0000-0000-000000000007" }
  }
}
variables {
  lease_id                     = "abcdef123456"
  subscription_id              = "00000000-0000-0000-0000-000000000001"
  tenant_id                    = "00000000-0000-0000-0000-000000000002"
  bootstrap_operator_object_id = "00000000-0000-0000-0000-000000000004"
  live_execution_approved      = true
  approval = {
    approved_at            = timeadd(timestamp(), "-5m")
    expires_at             = timeadd(timestamp(), "4h")
    estimated_total_usd    = 1
    planning_allowance_usd = 10
  }
}
run "unbound_first_phase" {
  command = plan
  assert {
    condition     = length(azurerm_federated_identity_credential.cleanup) == 0 && length(azurerm_role_assignment.canary) == 0
    error_message = "The first phase must not invent connection claims or grant a nonexistent canary scope."
  }
}
run "private_entra_storage" {
  command = plan
  assert {
    condition     = !azurerm_storage_account.state.shared_access_key_enabled && !azurerm_storage_account.state.allow_nested_items_to_be_public && azurerm_storage_account.state.https_traffic_only_enabled && azurerm_storage_account.state.blob_properties[0].versioning_enabled && length(azurerm_storage_container.private) == 3
    error_message = "Use private, versioned, Entra-authenticated state and receipts without shared keys."
  }
}
run "exact_federation_and_canary_scope" {
  command = plan
  variables {
    canary_group_ready = true
    federation = {
      issuer            = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
      subject           = "fixture/exact-service-connection"
      metadata_verified = true
    }
  }
  assert {
    condition     = azurerm_federated_identity_credential.cleanup[0].subject == "fixture/exact-service-connection" && azurerm_role_assignment.canary[0].scope == "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/dmi-w10-cleanup-abcdef123456-canary-rg" && !contains(azurerm_role_definition.discovery.permissions[0].actions, "*")
    error_message = "Federation must be exact and deletion scoped to one canary RG."
  }
}
run "no_approval" {
  command = plan
  variables { live_execution_approved = false }
  expect_failures = [terraform_data.authorization]
}
run "wrong_operator" {
  command = plan
  variables { bootstrap_operator_object_id = "00000000-0000-0000-0000-000000000009" }
  expect_failures = [terraform_data.authorization]
}
run "no_wildcard_subject" {
  command = plan
  variables {
    federation = {
      issuer            = "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0"
      subject           = "fixture/*"
      metadata_verified = true
    }
  }
  expect_failures = [var.federation]
}
run "no_old_issuer" {
  command = plan
  variables {
    federation = {
      issuer            = "https://vstoken.dev.azure.com/00000000-0000-0000-0000-000000000002"
      subject           = "fixture/exact-service-connection"
      metadata_verified = true
    }
  }
  expect_failures = [var.federation]
}
run "no_long_window" {
  command = plan
  variables {
    approval = { approved_at = timestamp(), expires_at = timeadd(timestamp(), "25h"), estimated_total_usd = 1, planning_allowance_usd = 10 }
  }
  expect_failures = [var.approval]
}
