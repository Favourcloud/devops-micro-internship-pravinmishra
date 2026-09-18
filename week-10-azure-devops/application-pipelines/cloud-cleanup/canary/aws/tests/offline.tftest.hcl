# All apply/teardown operations use mocked AWS and isolated synthetic state.
mock_provider "aws" {
  override_during = plan
  mock_data "aws_caller_identity" {
    defaults = { account_id = "000000000001", arn = "arn:aws:sts::000000000001:assumed-role/fixture/test" }
  }
}
variables {
  lease_id                = "abcdef123456"
  account_id              = "000000000001"
  operator_arn            = "arn:aws:sts::000000000001:assumed-role/fixture/test"
  expires_at              = timeadd(timestamp(), "4h")
  live_execution_approved = true
}
run "empty_vpc_only" {
  command = plan
  assert {
    condition     = aws_vpc.canary.cidr_block == "10.199.0.0/24" && aws_vpc.canary.tags.assignment == "week10-cleanup-canary" && aws_vpc.canary.tags.cleanup_lease == "abcdef123456"
    error_message = "The AWS canary must be one empty VPC, not an instance or network stack."
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
