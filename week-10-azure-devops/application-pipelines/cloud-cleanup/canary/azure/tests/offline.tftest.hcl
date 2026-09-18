# All apply/teardown operations use mocked Azure and isolated synthetic state.
mock_provider "azurerm" {
  override_during = plan
  mock_data "azurerm_client_config" {
    defaults = {
      subscription_id = "00000000-0000-0000-0000-000000000001"
      tenant_id       = "00000000-0000-0000-0000-000000000002"
      object_id       = "00000000-0000-0000-0000-000000000004"
    }
  }
}
variables {
  lease_id                = "abcdef123456"
  subscription_id         = "00000000-0000-0000-0000-000000000001"
  tenant_id               = "00000000-0000-0000-0000-000000000002"
  operator_object_id      = "00000000-0000-0000-0000-000000000004"
  expires_at              = timeadd(timestamp(), "4h")
  live_execution_approved = true
}
run "empty_group_only" {
  command = plan
  assert {
    condition     = azurerm_resource_group.canary.name == "dmi-w10-cleanup-abcdef123456-canary-rg" && azurerm_resource_group.canary.tags.cleanup_lease == "abcdef123456" && azurerm_resource_group.canary.location == "uksouth"
    error_message = "The Azure canary must be one correctly scoped empty resource group."
  }
}
run "approval_required" {
  command = plan
  variables { live_execution_approved = false }
  expect_failures = [terraform_data.authorization]
}
run "mock_creation_and_automatic_teardown" {
  command = apply
}
