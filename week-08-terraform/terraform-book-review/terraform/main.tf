locals {
  tags = {
    Project     = "BookReview"
    Assignment  = "Week08-A5"
    Learner     = "Eze Favour"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CleanupId   = var.cleanup_id
  }
  public_origin   = "https://${var.public_hostname}"
  deploy_manifest = jsondecode(file("${path.module}/../runtime/deploy-manifest.json"))
  runtime_files = { for tier in ["web", "app", "initializer"] : tier => [
    for filename in concat(local.deploy_manifest.common, local.deploy_manifest.tiers[tier]) : {
      path        = "/opt/book-review/configuration/${filename}"
      content     = filename == "source-lock.json" ? file("${path.module}/../source-lock.json") : file("${path.module}/../runtime/${filename}")
      owner       = "root:root"
      permissions = endswith(filename, ".sh") || endswith(filename, ".py") ? "0755" : "0644"
    }
  ] }
  common_config = {
    region             = var.region
    public_origin      = local.public_origin
    internal_url       = module.load_balancing.internal_url
    db_host            = module.database.primary_address
    replica_host       = module.database.replica_address
    db_name            = var.db_name
    release_authorized = var.runtime_release_authorized
  }
  tier_config = {
    web = merge(local.common_config, {
      tier                    = "web"
      runtime_artifact_url    = var.runtime_artifact_url
      runtime_artifact_sha256 = var.runtime_artifact_sha256
    })
    app = merge(local.common_config, {
      tier                    = "app"
      runtime_artifact_url    = var.runtime_artifact_url
      runtime_artifact_sha256 = var.runtime_artifact_sha256
      rds_ca_path             = "/etc/book-review/rds-ca.pem"
      rds_ca_sha256           = var.rds_ca_sha256
      app_secret_arn          = module.secrets.app_arn
      app_secret_version      = module.secrets.app_version_id
      router_secret_arn       = var.router_secret_arn
    })
    initializer = merge(local.common_config, {
      tier                  = "initializer"
      rds_ca_path           = "/etc/book-review/rds-ca.pem"
      rds_ca_sha256         = var.rds_ca_sha256
      app_secret_arn        = module.secrets.app_arn
      app_secret_version    = module.secrets.app_version_id
      master_secret_arn     = module.secrets.master_arn
      master_secret_version = module.secrets.master_version_id
    })
  }
  user_data = { for tier, config in local.tier_config : tier => base64gzip(join("\n", ["#cloud-config", yamlencode({
    write_files = concat(local.runtime_files[tier], [{
      path        = "/etc/book-review/config.json"
      owner       = "root:root"
      permissions = "0600"
      content     = jsonencode(config)
    }])
    runcmd = [["/opt/book-review/configuration/bootstrap.sh", "/etc/book-review/config.json"]]
  })])) }
}
module "network" {
  source             = "./modules/network"
  name               = var.name
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}
module "security" {
  source = "./modules/security"
  name   = var.name
  vpc_id = module.network.vpc_id
}
module "load_balancing" {
  source              = "./modules/load_balancing"
  name                = var.name
  vpc_id              = module.network.vpc_id
  web_subnets         = values(module.network.web_subnets)
  app_subnets         = values(module.network.app_subnets)
  security_groups     = module.security.ids
  certificate_arn     = var.certificate_arn
  deletion_protection = var.deletion_protection
}
module "database" {
  source                = "./modules/database"
  name                  = var.name
  subnet_ids            = module.network.db_subnets
  security_group_id     = module.security.ids["db"]
  database_name         = var.db_name
  master_username       = var.db_master_username
  master_password       = var.db_master_password
  password_version      = var.master_secret_version
  engine_version        = var.db_engine_version
  instance_class        = var.db_instance_class
  deletion_protection   = var.deletion_protection
  final_snapshot_suffix = var.final_snapshot_suffix
}
module "secrets" {
  source         = "./modules/secrets"
  name           = var.name
  master_payload = jsonencode({ username = var.db_master_username, password = var.db_master_password })
  app_payload    = jsonencode({ username = var.app_username, password = var.app_password, jwt_secret = var.jwt_secret })
  master_version = var.master_secret_version
  app_version    = var.app_secret_version
  depends_on     = [module.database]
}
module "observability" {
  source                   = "./modules/observability"
  name                     = var.name
  enable_initializer       = var.enable_database_initializer
  load_balancer_dimensions = module.load_balancing.alarm_dimensions
  replica_identifier       = module.database.replica_identifier
}
module "web_identity" {
  source        = "./modules/identity"
  name          = var.name
  tier          = "web"
  secret_arns   = []
  log_group_arn = module.observability.log_group_arns["web"]
}
module "app_identity" {
  source        = "./modules/identity"
  name          = var.name
  tier          = "app"
  secret_arns   = [module.secrets.app_arn, var.router_secret_arn]
  log_group_arn = module.observability.log_group_arns["app"]
}
module "web" {
  source            = "./modules/compute"
  name              = var.name
  tier              = "web"
  ami_id            = var.ami_id
  instance_type     = var.instance_type
  subnets           = module.network.web_subnets
  security_group_id = module.security.ids["web"]
  instance_profile  = module.web_identity.profile_name
  target_group_arn  = module.load_balancing.web_target_group_arn
  user_data_base64  = local.user_data.web
  tags              = local.tags
  depends_on        = [module.load_balancing, module.network, module.web_identity]
}
module "app" {
  source            = "./modules/compute"
  name              = var.name
  tier              = "app"
  ami_id            = var.ami_id
  instance_type     = var.instance_type
  subnets           = module.network.app_subnets
  security_group_id = module.security.ids["app"]
  instance_profile  = module.app_identity.profile_name
  target_group_arn  = module.load_balancing.app_target_group_arn
  user_data_base64  = local.user_data.app
  tags              = local.tags
  depends_on        = [module.database, module.load_balancing, module.network, module.app_identity]
}
module "initializer_identity" {
  count         = var.enable_database_initializer ? 1 : 0
  source        = "./modules/identity"
  name          = var.name
  tier          = "initializer"
  secret_arns   = [module.secrets.master_arn, module.secrets.app_arn]
  log_group_arn = module.observability.log_group_arns["initializer"]
}
module "initializer" {
  count             = var.enable_database_initializer ? 1 : 0
  source            = "./modules/initializer"
  name              = var.name
  ami_id            = var.ami_id
  instance_type     = var.instance_type
  subnet_id         = module.network.app_subnets["0"]
  security_group_id = module.security.ids["app"]
  instance_profile  = module.initializer_identity[0].profile_name
  user_data_base64  = local.user_data.initializer
  depends_on        = [module.database, module.network, module.initializer_identity]
}
