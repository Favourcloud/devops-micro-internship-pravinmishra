mock_provider "aws" {
  mock_data "aws_ami" {
    defaults = { id = "ami-00000000000000000" }
  }
  mock_resource "aws_instance" {
    defaults = {
      id        = "i-00000000000000000"
      public_ip = "198.51.100.20"
    }
  }
}

variables {
  aws_region = "eu-west-2"
  ssh_cidr   = "198.51.100.10/32"
  # Synthetic zero-byte public payload; no private key exists and it is not a login key.
  ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
}

run "topology_and_hardening" {
  command = apply

  assert {
    condition     = aws_vpc.lab.cidr_block == "10.0.0.0/16" && aws_vpc.lab.enable_dns_support && aws_vpc.lab.enable_dns_hostnames
    error_message = "The custom VPC must have the rubric CIDR and DNS enabled."
  }
  assert {
    condition     = aws_subnet.public.cidr_block == "10.0.1.0/24" && aws_subnet.private.cidr_block == "10.0.2.0/24"
    error_message = "Both rubric subnets must exist."
  }
  assert {
    condition     = aws_subnet.public.vpc_id == aws_vpc.lab.id && aws_subnet.private.vpc_id == aws_vpc.lab.id
    error_message = "Both subnets must belong to the lab VPC."
  }
  assert {
    condition     = !aws_subnet.public.map_public_ip_on_launch && !aws_subnet.private.map_public_ip_on_launch
    error_message = "Public IP allocation must be explicit on the EC2 instance, not automatic for all subnet occupants."
  }
  assert {
    condition     = aws_internet_gateway.lab.vpc_id == aws_vpc.lab.id
    error_message = "The IGW must attach to the lab VPC."
  }
  assert {
    condition     = aws_route_table.public.vpc_id == aws_vpc.lab.id && aws_route_table.private.vpc_id == aws_vpc.lab.id
    error_message = "Both route tables must belong to the lab VPC."
  }
  assert {
    condition     = length(aws_route_table.public.route) == 1 && one(aws_route_table.public.route).cidr_block == "0.0.0.0/0" && one(aws_route_table.public.route).gateway_id == aws_internet_gateway.lab.id
    error_message = "The public default route must target the IGW."
  }
  assert {
    condition     = length(aws_route_table.private.route) == 0
    error_message = "The private table must have no non-local routes, including no Internet default."
  }
  assert {
    condition     = aws_route_table_association.public.subnet_id == aws_subnet.public.id && aws_route_table_association.public.route_table_id == aws_route_table.public.id
    error_message = "The public subnet must use its public route table."
  }
  assert {
    condition     = aws_route_table_association.private.subnet_id == aws_subnet.private.id && aws_route_table_association.private.route_table_id == aws_route_table.private.id
    error_message = "The private subnet must use its explicit isolated table."
  }
  assert {
    condition     = aws_security_group.web.vpc_id == aws_vpc.lab.id && length(aws_security_group.web.ingress) == 2
    error_message = "Exactly two ingress rules belong to the lab VPC security group."
  }
  assert {
    condition = length([for rule in aws_security_group.web.ingress : rule if(
      rule.from_port == 22 && rule.to_port == 22 && rule.protocol == "tcp" &&
      toset(rule.cidr_blocks) == toset([var.ssh_cidr]) && length(coalesce(rule.ipv6_cidr_blocks, [])) == 0 &&
      length(coalesce(rule.security_groups, [])) == 0 && length(coalesce(rule.prefix_list_ids, [])) == 0 && !coalesce(rule.self, false)
    )]) == 1
    error_message = "SSH must allow only the controller /32, with no alternate ingress sources."
  }
  assert {
    condition = length([for rule in aws_security_group.web.ingress : rule if(
      rule.from_port == 80 && rule.to_port == 80 && rule.protocol == "tcp" &&
      toset(rule.cidr_blocks) == toset(["0.0.0.0/0"]) && length(coalesce(rule.ipv6_cidr_blocks, [])) == 0 &&
      length(coalesce(rule.security_groups, [])) == 0 && length(coalesce(rule.prefix_list_ids, [])) == 0 && !coalesce(rule.self, false)
    )]) == 1
    error_message = "The assignment requires public IPv4 HTTP only."
  }
  assert {
    condition = length(aws_security_group.web.egress) == 2 && alltrue([
      for rule in aws_security_group.web.egress : rule.protocol == "tcp" &&
      contains([80, 443], rule.from_port) && rule.from_port == rule.to_port &&
      toset(rule.cidr_blocks) == toset(["0.0.0.0/0"]) && length(coalesce(rule.ipv6_cidr_blocks, [])) == 0 &&
      length(coalesce(rule.security_groups, [])) == 0 && length(coalesce(rule.prefix_list_ids, [])) == 0 && !coalesce(rule.self, false)
    ])
    error_message = "Package bootstrap egress must be limited to HTTP and HTTPS."
  }
  assert {
    condition     = aws_instance.web.subnet_id == aws_subnet.public.id && aws_instance.web.associate_public_ip_address
    error_message = "The instance needs the public subnet and an explicit public IP."
  }
  assert {
    condition     = aws_instance.web.vpc_security_group_ids == toset([aws_security_group.web.id])
    error_message = "Only the lab security group should be attached."
  }
  assert {
    condition     = aws_instance.web.ami == data.aws_ami.ubuntu.id && aws_instance.web.instance_type == "t3.micro"
    error_message = "The instance must use the resolved Ubuntu AMI and default small x86_64 instance."
  }
  assert {
    condition     = data.aws_ami.ubuntu.owners == tolist(["099720109477"]) && data.aws_ami.ubuntu.most_recent
    error_message = "AMI discovery must restrict ownership to Canonical."
  }
  assert {
    condition = tomap({ for f in data.aws_ami.ubuntu.filter : f.name => one(f.values) }) == tomap({
      name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
      architecture        = "x86_64"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
      state               = "available"
    })
    error_message = "AMI discovery must select supported Ubuntu 24.04, not arbitrary or ARM images."
  }
  assert {
    condition     = aws_key_pair.lab.public_key == var.ssh_public_key && aws_instance.web.key_name == aws_key_pair.lab.key_name
    error_message = "The managed key pair must import the supplied external public key and authenticate this instance."
  }
  assert {
    condition     = aws_instance.web.user_data == file("${path.module}/scripts/cloud-init.sh") && aws_instance.web.user_data_replace_on_change
    error_message = "The real Nginx bootstrap must be wired into the instance and replace on change."
  }
  assert {
    condition     = one(aws_instance.web.metadata_options).http_tokens == "required" && one(aws_instance.web.metadata_options).http_endpoint == "enabled" && one(aws_instance.web.metadata_options).http_put_response_hop_limit == 1 && one(aws_instance.web.metadata_options).instance_metadata_tags == "disabled"
    error_message = "IMDSv2 must be required, with hop limit 1 and metadata tags disabled."
  }
  assert {
    condition     = one(aws_instance.web.root_block_device).encrypted && one(aws_instance.web.root_block_device).volume_type == "gp3" && one(aws_instance.web.root_block_device).volume_size == 8 && one(aws_instance.web.root_block_device).delete_on_termination
    error_message = "The small encrypted gp3 root volume must be deleted with the instance."
  }
  assert {
    condition     = one(aws_instance.web.credit_specification).cpu_credits == "standard"
    error_message = "Do not opt into unlimited CPU-credit charges."
  }
  assert {
    condition     = output.public_ip == "198.51.100.20" && output.instance_id == "i-00000000000000000" && output.website_url == "http://198.51.100.20"
    error_message = "The IP, instance ID and HTTP URL outputs must match the mocked instance (not runtime evidence)."
  }
  assert {
    condition     = output.ssh_username == "ubuntu" && output.ami_id == data.aws_ami.ubuntu.id
    error_message = "The username and selected AMI outputs must be coherent."
  }
}

run "supported_overrides" {
  command = plan
  variables {
    aws_region     = "us-east-1"
    instance_type  = "t3.small"
    name_prefix    = "test-a2"
    ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA synthetic-test"
  }
  assert {
    condition     = aws_instance.web.instance_type == "t3.small" && aws_vpc.lab.tags.Name == "test-a2-vpc"
    error_message = "Supported overrides and public-key comments should work."
  }
}

run "reject_world_ssh" {
  command = plan
  variables { ssh_cidr = "0.0.0.0/0" }
  expect_failures = [var.ssh_cidr]
}
run "reject_wide_ssh" {
  command = plan
  variables { ssh_cidr = "198.51.100.0/24" }
  expect_failures = [var.ssh_cidr]
}
run "reject_ipv6_ssh" {
  command = plan
  variables { ssh_cidr = "2001:db8::1/128" }
  expect_failures = [var.ssh_cidr]
}
run "reject_invalid_ip" {
  command = plan
  variables { ssh_cidr = "999.51.100.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_private_ssh" {
  command = plan
  variables { ssh_cidr = "10.0.0.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_private_172_ssh" {
  command = plan
  variables { ssh_cidr = "172.31.1.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_private_192_ssh" {
  command = plan
  variables { ssh_cidr = "192.168.1.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_loopback_ssh" {
  command = plan
  variables { ssh_cidr = "127.0.0.1/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_link_local_ssh" {
  command = plan
  variables { ssh_cidr = "169.254.1.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_shared_ssh" {
  command = plan
  variables { ssh_cidr = "100.64.1.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_multicast_ssh" {
  command = plan
  variables { ssh_cidr = "224.0.0.1/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_key_path" {
  command = plan
  variables { ssh_public_key = "/path/to/id_ed25519.pub" }
  expect_failures = [var.ssh_public_key]
}
run "reject_private_key" {
  command = plan
  variables { ssh_public_key = "-----BEGIN OPENSSH PRIVATE KEY-----\nTEST-ONLY-NOT-KEY-MATERIAL\n-----END OPENSSH PRIVATE KEY-----" }
  expect_failures = [var.ssh_public_key]
}
run "reject_key_shape" {
  command = plan
  variables { ssh_public_key = "ssh-ed25519 not-base64" }
  expect_failures = [var.ssh_public_key]
}
run "reject_multiline_public_key" {
  command = plan
  variables { ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nsecond-line" }
  expect_failures = [var.ssh_public_key]
}
run "reject_unsupported_key" {
  command = plan
  variables { ssh_public_key = "ecdsa-sha2-nistp256 TEST-ONLY" }
  expect_failures = [var.ssh_public_key]
}
run "reject_empty_region" {
  command = plan
  variables { aws_region = "" }
  expect_failures = [var.aws_region]
}
run "reject_region_format" {
  command = plan
  variables { aws_region = "London" }
  expect_failures = [var.aws_region]
}
run "reject_arm_instance" {
  command = plan
  variables { instance_type = "t4g.micro" }
  expect_failures = [var.instance_type]
}
run "reject_name" {
  command = plan
  variables { name_prefix = "INVALID NAME" }
  expect_failures = [var.name_prefix]
}
run "reject_noncanonical_ssh" {
  command = plan
  variables { ssh_cidr = "010.0.0.10/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_zero_host_ssh" {
  command = plan
  variables { ssh_cidr = "0.0.0.0/32" }
  expect_failures = [var.ssh_cidr]
}
run "reject_private_key_in_comment" {
  command = plan
  variables { ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA -----BEGIN PRIVATE KEY-----" }
  expect_failures = [var.ssh_public_key]
}
