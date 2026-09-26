# Entire file uses a native mock provider. None of these runs create cloud resources.
mock_provider "aws" {
  mock_data "aws_ami" {
    defaults = { id = "ami-00000000000000001" }
  }
  mock_resource "aws_db_instance" {
    defaults = { address = "mock.example.invalid", endpoint = "mock.example.invalid:3306" }
  }
  mock_resource "aws_instance" {
    defaults = { public_ip = "203.0.113.20" }
  }
}
variables {
  aws_region           = "eu-west-1"
  availability_zones   = ["eu-west-1a", "eu-west-1b"]
  controller_cidr      = "203.0.113.10/32"
  key_name             = "mock-only-key"
  db_username          = "mockadmin"
  db_password          = "mock-only-not-a-real-secret-1234"
  accept_lab_data_loss = true
}

run "network_topology" {
  command = apply
  module { source = "./modules/network" }
  variables {
    project_name = "mock-epicbook"
    azs          = ["eu-west-1a", "eu-west-1b"]
  }
  assert {
    condition     = aws_vpc.this.cidr_block == "10.0.0.0/16" && aws_vpc.this.enable_dns_support && aws_vpc.this.enable_dns_hostnames
    error_message = "Required VPC and private DNS must exist."
  }
  assert {
    condition     = aws_subnet.public.cidr_block == "10.0.1.0/24" && aws_subnet.private[0].cidr_block == "10.0.2.0/24" && aws_subnet.private[1].cidr_block == "10.0.3.0/24" && aws_subnet.private[0].availability_zone != aws_subnet.private[1].availability_zone
    error_message = "Exact three subnets and two AZs are required."
  }
  assert {
    condition     = aws_route.internet.gateway_id == aws_internet_gateway.this.id && aws_route.internet.destination_cidr_block == "0.0.0.0/0" && aws_route_table_association.public.subnet_id == aws_subnet.public.id && aws_route_table_association.public.route_table_id == aws_route_table.public.id
    error_message = "Public subnet must explicitly route through the IGW."
  }
  assert {
    condition     = length(aws_route_table.private.route) == 0 && alltrue([for association in aws_route_table_association.private : association.route_table_id == aws_route_table.private.id]) && alltrue([for subnet in aws_subnet.private : !subnet.map_public_ip_on_launch])
    error_message = "Both DB subnets must have explicit private local-only routing."
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.ssh.cidr_ipv4 == var.controller_cidr && aws_vpc_security_group_ingress_rule.ssh.from_port == 22 && aws_vpc_security_group_ingress_rule.http.from_port == 80 && aws_vpc_security_group_ingress_rule.http.cidr_ipv4 == "0.0.0.0/0"
    error_message = "Only explicit controller SSH and public HTTP are intended."
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.mysql.referenced_security_group_id == aws_security_group.ec2.id && aws_vpc_security_group_ingress_rule.mysql.security_group_id == aws_security_group.rds.id && aws_vpc_security_group_ingress_rule.mysql.from_port == 3306 && aws_vpc_security_group_ingress_rule.mysql.to_port == 3306
    error_message = "MySQL ingress must reference only the application SG."
  }
  assert {
    condition     = output.public_subnet_id == aws_subnet.public.id && output.private_subnet_ids == aws_subnet.private[*].id && output.ec2_security_group_id == aws_security_group.ec2.id && output.rds_security_group_id == aws_security_group.rds.id
    error_message = "All network outputs must expose the actual module resources."
  }
}

run "private_rds" {
  command = apply
  module { source = "./modules/rds" }
  variables {
    project_name       = "mock-epicbook"
    private_subnet_ids = ["subnet-00000000000000002", "subnet-00000000000000003"]
    security_group_id  = "sg-00000000000000002"
    instance_class     = "db.t3.micro"
    engine_version     = "8.4"
    credential_version = 1
  }
  assert {
    condition     = !aws_db_instance.this.publicly_accessible && aws_db_instance.this.storage_encrypted && !aws_db_instance.this.multi_az && aws_db_instance.this.db_name == "bookstore" && aws_db_instance.this.engine == "mysql"
    error_message = "Encrypted private single-AZ MySQL bookstore is required."
  }
  assert {
    condition     = aws_db_instance.this.db_subnet_group_name == aws_db_subnet_group.this.name && aws_db_instance.this.vpc_security_group_ids == toset([var.security_group_id]) && aws_db_subnet_group.this.subnet_ids == toset(var.private_subnet_ids)
    error_message = "RDS must use both supplied private subnets and only its SG."
  }
  assert {
    condition     = aws_db_instance.this.password_wo == null && aws_db_instance.this.password_wo_version == 1 && output.endpoint == aws_db_instance.this.endpoint
    error_message = "Write-only password must not be readable in state; endpoint must be wired."
  }
  assert {
    condition     = aws_db_instance.this.parameter_group_name == aws_db_parameter_group.this.name && one(aws_db_parameter_group.this.parameter).value == "1" && aws_db_instance.this.allocated_storage == 20 && aws_db_instance.this.skip_final_snapshot
    error_message = "TLS, bounded storage and explicit lab disposal settings are required."
  }
}

run "ec2_bootstrap" {
  command = apply
  module { source = "./modules/ec2" }
  variables {
    project_name       = "mock-epicbook"
    subnet_id          = "subnet-00000000000000001"
    security_group_id  = "sg-00000000000000001"
    instance_type      = "t3.micro"
    db_host            = "mock.example.invalid"
    runtime_secret_arn = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:mock-only"
    credential_version = 1
  }
  assert {
    condition     = aws_instance.this.associate_public_ip_address && aws_instance.this.subnet_id == var.subnet_id && aws_instance.this.vpc_security_group_ids == toset([var.security_group_id]) && aws_instance.this.key_name == var.key_name && aws_instance.this.ami == data.aws_ami.ubuntu.id
    error_message = "Public Ubuntu instance must use network module inputs and existing key."
  }
  assert {
    condition     = aws_instance.this.metadata_options[0].http_tokens == "required" && aws_instance.this.root_block_device[0].encrypted && aws_instance.this.root_block_device[0].delete_on_termination && aws_instance.this.credit_specification[0].cpu_credits == "standard"
    error_message = "IMDSv2, encrypted disposable disk and standard burst credits are required."
  }
  assert {
    condition     = length(aws_instance.this.user_data_base64) <= 21848 && aws_instance.this.user_data == null
    error_message = "Compressed user data must fit the encoded 16 KiB EC2 limit."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.secret.policy).Statement[0].Resource == var.runtime_secret_arn && jsondecode(aws_iam_role_policy.secret.policy).Statement[0].Action == ["secretsmanager:GetSecretValue"] && aws_instance.this.iam_instance_profile == aws_iam_instance_profile.runtime.name
    error_message = "Runtime IAM must grant only retrieval of this lab secret."
  }
}

run "root_wiring" {
  command = apply
  override_resource {
    target = module.network.aws_subnet.private[0]
    values = { id = "subnet-00000000000000002" }
  }
  override_resource {
    target = module.network.aws_subnet.private[1]
    values = { id = "subnet-00000000000000003" }
  }
  assert {
    condition     = output.ec2_public_ip == module.ec2.public_ip && output.rds_endpoint == module.rds.endpoint && output.application_url == "http://${module.ec2.public_ip}"
    error_message = "Root outputs must expose the module results, not fabricated live addresses."
  }
  assert {
    condition     = aws_secretsmanager_secret_version.database.secret_string_wo == null && aws_secretsmanager_secret_version.database.secret_string_wo_version == var.credential_version && aws_secretsmanager_secret.database.recovery_window_in_days == 0
    error_message = "Secret value must be write-only and use shared rotation counter and disclosed disposal policy."
  }
}

run "reject_open_ssh" {
  command = plan
  variables { controller_cidr = "0.0.0.0/0" }
  expect_failures = [var.controller_cidr]
}
run "reject_private_ssh" {
  command = plan
  variables { controller_cidr = "10.1.2.3/32" }
  expect_failures = [var.controller_cidr]
}
run "reject_ipv6_ssh" {
  command = plan
  variables { controller_cidr = "::1/128" }
  expect_failures = [var.controller_cidr]
}
run "reject_duplicate_az" {
  command = plan
  variables { availability_zones = ["eu-west-1a", "eu-west-1a"] }
  expect_failures = [var.availability_zones]
}
run "reject_wrong_region_az" {
  command = plan
  variables { availability_zones = ["us-east-1a", "us-east-1b"] }
  expect_failures = [var.availability_zones]
}
run "reject_old_mysql" {
  command = plan
  variables { mysql_version = "5.7" }
  expect_failures = [var.mysql_version]
}
run "reject_expensive_instance" {
  command = plan
  variables { ec2_instance_type = "m7i.24xlarge" }
  expect_failures = [var.ec2_instance_type]
}
run "reject_expensive_db" {
  command = plan
  variables { db_instance_class = "db.r7g.16xlarge" }
  expect_failures = [var.db_instance_class]
}
run "reject_weak_password" {
  command = plan
  variables { db_password = "mock-short" }
  expect_failures = [var.db_password]
}
run "reject_reserved_username" {
  command = plan
  variables { db_username = "rdsadmin" }
  expect_failures = [var.db_username]
}
run "reject_application_master_username" {
  command = plan
  variables { db_username = "epicbookapp" }
  expect_failures = [var.db_username]
}
run "reject_application_master_username_case_insensitive" {
  command = plan
  variables { db_username = "EpicBookApp" }
  expect_failures = [var.db_username]
}
run "rds_reject_application_master_username" {
  command = plan
  module { source = "./modules/rds" }
  variables {
    project_name       = "mock-epicbook"
    private_subnet_ids = ["subnet-00000000000000002", "subnet-00000000000000003"]
    security_group_id  = "sg-00000000000000002"
    instance_class     = "db.t3.micro"
    engine_version     = "8.4"
    credential_version = 1
    db_username        = "epicbookapp"
  }
  expect_failures = [var.db_username]
}
run "accept_distinct_master_and_hash_password" {
  command = plan
  variables {
    db_username = "mockadmin"
    db_password = "MockPasswordOnly#0123456789"
  }
}
run "reject_fractional_rotation" {
  command = plan
  variables { credential_version = 1.5 }
  expect_failures = [var.credential_version]
}
run "reject_implicit_disposal" {
  command = plan
  variables { accept_lab_data_loss = false }
  expect_failures = [var.accept_lab_data_loss]
}
run "reject_key_path" {
  command = plan
  variables { key_name = "/tmp/private.pem" }
  expect_failures = [var.key_name]
}
run "reject_bad_name" {
  command = plan
  variables { project_name = "Name With Spaces" }
  expect_failures = [var.project_name]
}

run "reject_mysql_master_password_over_41" {
  command = plan
  variables { db_password = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" }
  expect_failures = [var.db_password]
}
run "accept_mysql_master_password_41" {
  command = plan
  variables { db_password = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" }
}
