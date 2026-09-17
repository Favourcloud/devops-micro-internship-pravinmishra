# Synthetic values only. Every run uses a mocked provider and command = plan.
mock_provider "aws" {
  override_during = plan
  mock_resource "aws_vpc" { defaults = { id = "vpc-0123456789abcdef0" } }
  mock_resource "aws_subnet" { defaults = { id = "subnet-0123456789abcdef0" } }
  mock_resource "aws_security_group" { defaults = { id = "sg-0123456789abcdef0" } }
  mock_resource "aws_eip" { defaults = { id = "eipalloc-0123456789abcdef0" } }
  mock_resource "aws_nat_gateway" { defaults = { id = "nat-0123456789abcdef0" } }
  mock_resource "aws_lb" { defaults = {
    arn        = "arn:aws:elasticloadbalancing:eu-west-1:000000000000:loadbalancer/app/mock/0123456789abcdef"
    arn_suffix = "app/mock/0123456789abcdef"
    dns_name   = "internal-mock.eu-west-1.elb.amazonaws.com"
  } }
  mock_resource "aws_lb_target_group" { defaults = {
    arn        = "arn:aws:elasticloadbalancing:eu-west-1:000000000000:targetgroup/mock/0123456789abcdef"
    arn_suffix = "targetgroup/mock/0123456789abcdef"
  } }
  mock_resource "aws_db_instance" { defaults = { address = "mock-db.example.invalid", arn = "arn:aws:rds:eu-west-1:000000000000:db:mock-primary" } }
  mock_resource "aws_secretsmanager_secret" { defaults = { arn = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:mock-AbCdEf" } }
  mock_resource "aws_secretsmanager_secret_version" { defaults = { version_id = "00000000-0000-0000-0000-000000000000" } }
  mock_resource "aws_iam_role" { defaults = { arn = "arn:aws:iam::000000000000:role/mock", name = "mock-role", id = "mock-role" } }
  mock_resource "aws_iam_instance_profile" { defaults = { name = "mock-profile" } }
  mock_resource "aws_cloudwatch_log_group" { defaults = { arn = "arn:aws:logs:eu-west-1:000000000000:log-group:mock" } }
  mock_resource "aws_launch_template" { defaults = { id = "lt-0123456789abcdef0", latest_version = 1 } }
}
override_resource {
  target          = module.database.aws_db_instance.primary
  override_during = plan
  values          = { address = "primary.example.invalid", arn = "arn:aws:rds:eu-west-1:000000000000:db:mock-primary" }
}
override_resource {
  target          = module.database.aws_db_instance.replica
  override_during = plan
  values          = { address = "replica.example.invalid", arn = "arn:aws:rds:eu-west-1:000000000000:db:mock-replica" }
}
override_resource {
  target          = module.secrets.aws_secretsmanager_secret.master
  override_during = plan
  values          = { id = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:master-MOCK00", arn = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:master-MOCK00" }
}
override_resource {
  target          = module.secrets.aws_secretsmanager_secret.app
  override_during = plan
  values          = { id = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:app-MOCK00", arn = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:app-MOCK00" }
}
variables {
  region                  = "eu-west-1"
  availability_zones      = ["eu-west-1a", "eu-west-1b"]
  cleanup_id              = "synthetic-offline-only"
  ami_id                  = "ami-0123456789abcdef0"
  public_hostname         = "books.example.invalid"
  certificate_arn         = "arn:aws:acm:eu-west-1:000000000000:certificate/00000000-0000-0000-0000-000000000000"
  router_secret_arn       = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:router-MOCK00"
  rds_ca_sha256           = "0000000000000000000000000000000000000000000000000000000000000000"
  runtime_artifact_url    = "https://artifacts.example.invalid/mock-only.tar.gz"
  runtime_artifact_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
  final_snapshot_suffix   = "mockonly"
  db_master_password      = "MockOnlyPasswordNotARealSecret123!"
  app_password            = "MockOnlyAppPasswordNotASecret123!"
  jwt_secret              = "MockOnlyJwtSigningValueNotASecret123!"
}
run "six_subnets_two_nat" {
  command = plan
  assert {
    condition     = output.architecture.network.subnet_count == 6 && output.architecture.network.nat_count == 2 && length(distinct(output.architecture.network.cidrs)) == 6
    error_message = "Six distinct subnets and two NATs are required."
  }
}
run "db_has_no_default_internet_route" {
  command = plan
  assert {
    condition     = output.architecture.network.routes["db-0"] == "local-only" && output.architecture.network.routes["db-1"] == "local-only" && output.architecture.network.db_default_routes == 0
    error_message = "Database routing must be isolated."
  }
}
run "az_local_app_routes" {
  command = plan
  assert {
    condition     = output.architecture.network.routes["app-0"] == "nat-0" && output.architecture.network.routes["app-1"] == "nat-1" && output.architecture.network.routes["web-0"] == "igw" && output.architecture.network.routes["web-1"] == "igw"
    error_message = "Outbound routing must match each AZ and tier."
  }
}
run "exclusive_tier_security_chain" {
  command = plan
  assert {
    condition     = length(output.architecture.security_chain) == 4 && output.architecture.security_chain.web.source == "public_lb" && output.architecture.security_chain.internal_lb.source == "web" && output.architecture.security_chain.app.source == "internal_lb" && output.architecture.security_chain.app.port == 3001 && output.architecture.security_chain.db.source == "app" && output.architecture.security_chain.db.port == 3306
    error_message = "The ALB/Web/internal ALB/App/DB chain must remain restricted."
  }
}
run "ha_is_not_read_replication" {
  command = plan
  assert {
    condition     = output.architecture.database.multi_az && !output.architecture.database.replica_multi_az && output.architecture.database.backup_days == 7
    error_message = "Multi-AZ primary and independent replica serve distinct functions."
  }
}
run "both_databases_private_encrypted" {
  command = plan
  assert {
    condition     = !output.architecture.database.primary_public && !output.architecture.database.replica_public && output.architecture.database.primary_encrypted && output.architecture.database.replica_encrypted && !output.architecture.database.secret_managed
    error_message = "Both databases must be private/encrypted; source-managed master credentials conflict with MySQL replicas."
  }
}
run "per_az_web_app_capacity" {
  command = plan
  assert {
    condition     = length(output.architecture.web_az_groups) == 2 && length(output.architecture.app_az_groups) == 2 && alltrue([for group in concat(values(output.architecture.web_az_groups), values(output.architecture.app_az_groups)) : group.min == 1 && group.desired == 1 && group.max == 2 && length(group.subnets) == 1])
    error_message = "Each tier must retain an instance in each AZ with bounded rollout capacity."
  }
}
run "safe_source_only_defaults" {
  command = plan
  assert {
    condition     = !output.architecture.initializer_enabled && !output.architecture.runtime_authorized && !output.source_status.assignment_complete && !output.source_status.cloud_verified && output.source_status.evidence_slots == 28 && output.source_status.reflections_pending == 15
    error_message = "Never infer runtime approval or completed evidence from source preparation."
  }
}
run "initializer_is_explicit" {
  command = plan
  variables { enable_database_initializer = true }
  assert {
    condition     = output.architecture.initializer_enabled && !output.architecture.runtime_authorized
    error_message = "Opt-in DB initialization must not implicitly authorize public release."
  }
}
run "https_and_dependency_backed_health" {
  command = plan
  assert {
    condition     = module.load_balancing.controls.public_port == 443 && module.load_balancing.controls.public_protocol == "HTTPS" && module.load_balancing.controls.certificate == var.certificate_arn && module.load_balancing.controls.internal_private && module.load_balancing.controls.public_health == "/healthz" && module.load_balancing.controls.app_health == "/api/books" && module.load_balancing.controls.app_port == 3001
    error_message = "Public credential transport and DB-backed health must not regress."
  }
}
run "hardened_compute_metadata_and_disks" {
  command = plan
  assert {
    condition     = one(module.web.metadata).http_tokens == "required" && one(module.app.metadata).http_tokens == "required" && one(module.web.metadata).http_put_response_hop_limit == 1 && one(module.app.metadata).http_put_response_hop_limit == 1 && module.web.controls.root_encrypted && module.app.controls.root_encrypted && module.web.controls.root_type == "gp3" && module.app.controls.root_type == "gp3" && module.web.controls.public_ip && !module.app.controls.public_ip && alltrue([for kind in concat(module.web.controls.health_types, module.app.controls.health_types) : kind == "ELB"])
    error_message = "IMDSv2, encrypted volumes, private App networking and ELB health are mandatory."
  }
}
run "replica_stays_in_dedicated_db_subnets" {
  command = plan
  assert {
    condition     = module.database.design.primary_subnet_group == var.name && module.database.design.replica_subnet_group == var.name
    error_message = "The replica must explicitly use the dedicated private DB subnet group, not an account default."
  }
}
run "bounded_non_secret_user_data" {
  command = plan
  assert {
    condition     = alltrue([for data in values(local.user_data) : floor(length(replace(data, "=", "")) * 3 / 4) <= 16384])
    error_message = "All compressed tier payloads must fit the EC2 16 KiB limit."
  }
}
run "scoped_runtime_secret_reads" {
  command = plan
  assert {
    condition     = length([for statement in jsondecode(module.web_identity.policy).Statement : statement if statement.Sid == "ExactRuntimeSecretsOnly"]) == 0 && one([for statement in jsondecode(module.app_identity.policy).Statement : statement if statement.Sid == "ExactRuntimeSecretsOnly"]).Action == ["secretsmanager:GetSecretValue"] && toset(one([for statement in jsondecode(module.app_identity.policy).Statement : statement if statement.Sid == "ExactRuntimeSecretsOnly"]).Resource) == toset([module.secrets.app_arn, var.router_secret_arn])
    error_message = "Web reads no secrets and App reads only its exact App/Router secrets."
  }
}
run "bounded_ssm_permission_actions" {
  command = plan
  assert {
    condition     = toset(one([for statement in jsondecode(module.app_identity.policy).Statement : statement if statement.Sid == "SessionManagerChannels"]).Action) == toset(["ssm:UpdateInstanceInformation", "ssmmessages:CreateControlChannel", "ssmmessages:CreateDataChannel", "ssmmessages:OpenControlChannel", "ssmmessages:OpenDataChannel"])
    error_message = "Session Manager channels must not become admin or service-wildcard permissions."
  }
}
run "protected_cleanup_and_replica_snapshot_rule" {
  command = plan
  assert {
    condition     = module.database.design.primary_final_snapshot && module.database.design.replica_skip_final_snapshot && module.database.design.primary_deletion_protected && module.database.design.replica_deletion_protected && module.load_balancing.controls.public_deletion_protected && module.load_balancing.controls.internal_deletion_protected
    error_message = "Preserve the primary snapshot; RDS forbids a final snapshot for an unpromoted replica."
  }
}
run "reject_repeated_az" {
  command = plan
  variables { availability_zones = ["eu-west-1a", "eu-west-1a"] }
  expect_failures = [var.availability_zones]
}
run "reject_foreign_az" {
  command = plan
  variables { availability_zones = ["eu-west-1a", "eu-west-2a"] }
  expect_failures = [var.availability_zones]
}
run "reject_local_zone" {
  command = plan
  variables { availability_zones = ["eu-west-1a", "eu-west-1-wl1-a"] }
  expect_failures = [var.availability_zones]
}
run "reject_vpc_size" {
  command = plan
  variables { vpc_cidr = "10.84.0.0/24" }
  expect_failures = [var.vpc_cidr]
}
run "reject_url_as_hostname" {
  command = plan
  variables { public_hostname = "http://books.example.invalid" }
  expect_failures = [var.public_hostname]
}
run "reject_foreign_certificate" {
  command = plan
  variables { certificate_arn = "arn:aws:acm:eu-west-2:000000000000:certificate/00000000-0000-0000-0000-000000000000" }
  expect_failures = [var.certificate_arn]
}
run "reject_foreign_router_secret" {
  command = plan
  variables { router_secret_arn = "arn:aws:secretsmanager:eu-west-2:000000000000:secret:router-MOCK00" }
  expect_failures = [var.router_secret_arn]
}
run "reject_dynamic_ami_input" {
  command = plan
  variables { ami_id = "latest" }
  expect_failures = [var.ami_id]
}
run "reject_master_as_app" {
  command = plan
  variables { app_username = "bookreview_admin" }
  expect_failures = [var.app_username]
}
run "reject_weak_master" {
  command = plan
  variables { db_master_password = "not-real" }
  expect_failures = [var.db_master_password]
}
run "reject_weak_app" {
  command = plan
  variables { app_password = "not-real" }
  expect_failures = [var.app_password]
}
run "reject_weak_jwt" {
  command = plan
  variables { jwt_secret = "not-real" }
  expect_failures = [var.jwt_secret]
}
run "reject_secret_newline" {
  command = plan
  variables { app_password = "MockOnlyLongPasswordNotReal\n12345" }
  expect_failures = [var.app_password]
}
run "reject_missing_ca_digest" {
  command = plan
  variables { rds_ca_sha256 = "unverified" }
  expect_failures = [var.rds_ca_sha256]
}
run "reject_nonintegral_secret_version" {
  command = plan
  variables { app_secret_version = 1.5 }
  expect_failures = [var.app_secret_version]
}
run "reject_zero_master_version" {
  command = plan
  variables { master_secret_version = 0 }
  expect_failures = [var.master_secret_version]
}
run "reject_mysql_family_mismatch" {
  command = plan
  variables { db_engine_version = "8.0" }
  expect_failures = [var.db_engine_version]
}
run "reject_unreviewed_compute_class" {
  command = plan
  variables { instance_type = "t3.2xlarge" }
  expect_failures = [var.instance_type]
}
run "reject_unreviewed_db_class" {
  command = plan
  variables { db_instance_class = "db.r7g.16xlarge" }
  expect_failures = [var.db_instance_class]
}
run "reject_unsafe_cleanup_name" {
  command = plan
  variables { cleanup_id = "../../outside" }
  expect_failures = [var.cleanup_id]
}
run "reject_invalid_snapshot_suffix" {
  command = plan
  variables { final_snapshot_suffix = "ends-in-hyphen-" }
  expect_failures = [var.final_snapshot_suffix]
}

run "reject_http_runtime_artifact" {
  command = plan
  variables { runtime_artifact_url = "http://artifacts.example.invalid/build.tar.gz" }
  expect_failures = [var.runtime_artifact_url]
}
run "reject_credential_bearing_artifact_url" {
  command = plan
  variables { runtime_artifact_url = "https://artifacts.example.invalid/build.tar.gz?token=synthetic" }
  expect_failures = [var.runtime_artifact_url]
}
run "reject_unreviewed_artifact_digest" {
  command = plan
  variables { runtime_artifact_sha256 = "missing" }
  expect_failures = [var.runtime_artifact_sha256]
}
run "least_data_tier_configuration" {
  command = plan
  assert {
    condition     = !contains(keys(local.tier_config.web), "rds_ca_path") && !contains(keys(local.tier_config.web), "app_secret_arn") && !contains(keys(local.tier_config.initializer), "runtime_artifact_url") && local.tier_config.app.rds_ca_path == "/etc/book-review/rds-ca.pem" && local.tier_config.initializer.rds_ca_sha256 == var.rds_ca_sha256
    error_message = "Only database clients need the pinned preinstalled CA, and initializer must not download application artifacts."
  }
}
run "synthetic_markers_absent_from_ordinary_payloads" {
  command = plan
  assert {
    condition     = alltrue([for marker in ["MockOnlyPasswordNotARealSecret123!", "MockOnlyAppPasswordNotASecret123!", "MockOnlyJwtSigningValueNotASecret123!"] : !strcontains(jsonencode({ config = local.tier_config, architecture = output.architecture, source_status = output.source_status }), marker)])
    error_message = "Synthetic credential markers must not enter ordinary configuration or outputs; real state remains unobserved."
  }
}
run "immutable_artifact_and_exact_master_version" {
  command = plan
  assert {
    condition     = local.tier_config.web.runtime_artifact_url == var.runtime_artifact_url && local.tier_config.app.runtime_artifact_sha256 == var.runtime_artifact_sha256 && local.tier_config.app.rds_ca_sha256 == var.rds_ca_sha256 && !local.common_config.release_authorized && local.tier_config.initializer.master_secret_version == module.secrets.master_version_id && local.tier_config.app.app_secret_version == module.secrets.app_version_id
    error_message = "Artifact/CA digests, closed bootstrap and exact secret VersionIds must remain explicit."
  }
}
