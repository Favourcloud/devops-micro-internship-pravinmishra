"""Bounded cloud reads for the separately approved A2 namespaces; no cloud writes."""


def require(value):
    if not value:
        raise ValueError("workload_inventory_rejected")


def rows(response, key):
    require(isinstance(response, dict) and not response.get("NextToken")
            and not response.get("nextLink") and isinstance(response.get(key), list))
    require(all(isinstance(row, dict) for row in response[key]))
    return response[key]


def ids(records, field, expected):
    actual = [row.get(field) for row in records]
    require(all(isinstance(value, str) for value in actual)
            and len(actual) == len(set(actual)) and set(actual) == set(expected))


def tags(records, request):
    expected = {"assignment": "week10-a2", "managed_by": "Terraform",
                "learner": "Eze Favour", "expires_at": request["original_expires_at"]}
    for record in records:
        pairs = record.get("Tags")
        require(isinstance(pairs, list) and all(isinstance(pair, dict) for pair in pairs))
        values = {pair.get("Key"): pair.get("Value") for pair in pairs}
        require(len(values) == len(pairs) and all(values.get(key) == value for key, value in expected.items()))


def aws_inventory(runner, request, absent=False):
    owned, extra = request["resources"], request["auxiliary"]
    vpc = owned["aws_vpc.target"]

    def get(operation, key, name="vpc-id", value=vpc):
        return rows(runner.aws("ec2", operation, "--filters", "Name=" + name + ",Values=" + value), key)

    vpcs = get("describe-vpcs", "Vpcs")
    keys = get("describe-key-pairs", "KeyPairs", "key-name", owned["aws_key_pair.operator"])
    volumes = get("describe-volumes", "Volumes", "volume-id", extra["root_volume"])
    reservations = get("describe-instances", "Reservations", "instance-id", owned["aws_instance.target"])
    instances = [instance for reservation in reservations for instance in rows(reservation, "Instances")]
    if absent:
        require(not vpcs and not keys and not volumes)
        require(all(instance.get("InstanceId") == owned["aws_instance.target"]
                    and instance.get("State", {}).get("Name") == "terminated" for instance in instances))
        return
    ids(vpcs, "VpcId", [vpc])
    require(vpcs[0].get("OwnerId") == request["identity"]["aws_account_id"] and vpcs[0].get("IsDefault") is False)
    ids(keys, "KeyName", [owned["aws_key_pair.operator"]])
    ids(volumes, "VolumeId", [extra["root_volume"]])
    ids(instances, "InstanceId", [owned["aws_instance.target"]])
    instance = instances[0]
    require(instance.get("VpcId") == vpc and instance.get("SubnetId") == owned["aws_subnet.target"]
            and instance.get("KeyName") == owned["aws_key_pair.operator"])
    mappings = instance.get("BlockDeviceMappings")
    require(isinstance(mappings, list) and len(mappings) == 1
            and mappings[0].get("Ebs", {}).get("VolumeId") == extra["root_volume"]
            and mappings[0].get("Ebs", {}).get("DeleteOnTermination") is True)
    attached = get("describe-volumes", "Volumes", "attachment.instance-id", owned["aws_instance.target"])
    ids(attached, "VolumeId", [extra["root_volume"]])
    all_instances = [i for r in get("describe-instances", "Reservations") for i in rows(r, "Instances")
                     if i.get("State", {}).get("Name") != "terminated"]
    ids(all_instances, "InstanceId", [owned["aws_instance.target"]])
    interfaces = get("describe-network-interfaces", "NetworkInterfaces")
    ids(interfaces, "NetworkInterfaceId", [extra["primary_eni"]])
    require(interfaces[0].get("Attachment", {}).get("InstanceId") == owned["aws_instance.target"]
            and interfaces[0].get("Attachment", {}).get("DeleteOnTermination") is True)
    require(not get("describe-addresses", "Addresses", "network-interface-id", extra["primary_eni"]))
    subnets = get("describe-subnets", "Subnets")
    gateways = get("describe-internet-gateways", "InternetGateways", "attachment.vpc-id")
    groups = get("describe-security-groups", "SecurityGroups")
    routes = get("describe-route-tables", "RouteTables")
    acls = get("describe-network-acls", "NetworkAcls")
    ids(subnets, "SubnetId", [owned["aws_subnet.target"]])
    ids(gateways, "InternetGatewayId", [owned["aws_internet_gateway.target"]])
    ids(groups, "GroupId", [owned["aws_security_group.target"], extra["default_security_group"]])
    ids(routes, "RouteTableId", [owned["aws_route_table.target"], extra["default_route_table"]])
    ids(acls, "NetworkAclId", [extra["default_network_acl"]])
    require(acls[0].get("IsDefault") is True)
    require(next(g for g in groups if g["GroupId"] == extra["default_security_group"]).get("GroupName") == "default")
    table = next(r for r in routes if r["RouteTableId"] == owned["aws_route_table.target"])
    associations = table.get("Associations")
    require(isinstance(associations, list) and len(associations) == 1
            and associations[0].get("RouteTableAssociationId") == owned["aws_route_table_association.target"]
            and associations[0].get("SubnetId") == owned["aws_subnet.target"]
            and associations[0].get("Main") is False)
    main = next(r for r in routes if r["RouteTableId"] == extra["default_route_table"]).get("Associations")
    require(isinstance(main, list) and len(main) == 1 and main[0].get("Main") is True
            and not main[0].get("SubnetId") and not main[0].get("GatewayId"))
    for operation, key, name in (
        ("describe-nat-gateways", "NatGateways", "vpc-id"),
        ("describe-vpc-endpoints", "VpcEndpoints", "vpc-id"),
        ("describe-vpn-gateways", "VpnGateways", "attachment.vpc-id"),
        ("describe-vpc-peering-connections", "VpcPeeringConnections", "requester-vpc-info.vpc-id"),
        ("describe-vpc-peering-connections", "VpcPeeringConnections", "accepter-vpc-info.vpc-id"),
        ("describe-transit-gateway-attachments", "TransitGatewayAttachments", "resource-id"),
    ):
        require(not get(operation, key, name))
    for gateway in rows(runner.aws("ec2", "describe-egress-only-internet-gateways"), "EgressOnlyInternetGateways"):
        require(all(isinstance(attachment.get("VpcId"), str) and attachment["VpcId"] != vpc
                    for attachment in rows(gateway, "Attachments")))
    tags(vpcs + keys + instances + subnets + gateways + [table]
         + [g for g in groups if g["GroupId"] == owned["aws_security_group.target"]], request)


def azure_inventory(runner, request, absent=False):
    owned, extra = request["resources"], request["auxiliary"]
    group = owned["azurerm_resource_group.agent"]
    subscription = request["identity"]["azure_subscription_id"]
    name = group.split("/")[-1]
    exists = runner.az("group", "exists", "--subscription", subscription, "--name", name)
    require(type(exists) is bool)
    if absent:
        require(not exists)
        return
    require(exists)
    inventory = runner.az("resource", "list", "--subscription", subscription, "--resource-group", name)
    require(isinstance(inventory, list) and all(isinstance(row, dict) for row in inventory))
    top_level = [value.lower() for address, value in owned.items() if address not in {
        "azurerm_resource_group.agent", "azurerm_subnet.agent",
        "azurerm_network_interface_security_group_association.agent"}]
    ids([{"id": row.get("id", "").lower()} for row in inventory], "id",
        top_level + [extra["os_disk"].lower()])
    group_record = runner.az("group", "show", "--subscription", subscription, "--name", name)
    expected = {"assignment": "week-10-assignment-01", "managed_by": "Terraform",
                "learner": "Eze Favour", "expires_at": request["original_expires_at"]}
    for record in inventory + [group_record]:
        if record.get("id", "").lower() != extra["os_disk"].lower():
            require(all(record.get("tags", {}).get(key) == value for key, value in expected.items()))
    vm = runner.az("vm", "show", "--ids", owned["azurerm_linux_virtual_machine.agent"])
    storage = vm.get("storageProfile", {})
    require(storage.get("dataDisks") == []
            and storage.get("osDisk", {}).get("managedDisk", {}).get("id", "").lower() == extra["os_disk"].lower())
    ids([{"id": row.get("id", "").lower()} for row in vm.get("networkProfile", {}).get("networkInterfaces", [])],
        "id", [owned["azurerm_network_interface.agent"].lower()])
    require(runner.az("vm", "extension", "list", "--subscription", subscription,
                      "--resource-group", name, "--vm-name", vm["name"]) == [])
    network = runner.az("network", "vnet", "show", "--ids", owned["azurerm_virtual_network.agent"])
    require(network.get("virtualNetworkPeerings") == [])
    subnets = network.get("subnets")
    require(isinstance(subnets, list) and len(subnets) == 1
            and subnets[0].get("id", "").lower() == owned["azurerm_subnet.agent"].lower()
            and not subnets[0].get("delegations") and not subnets[0].get("serviceAssociationLinks")
            and not subnets[0].get("privateEndpoints"))
    ip_configs = subnets[0].get("ipConfigurations")
    require(isinstance(ip_configs, list) and len(ip_configs) == 1
            and ip_configs[0].get("id", "").lower().startswith(
                owned["azurerm_network_interface.agent"].lower() + "/ipconfigurations/"))


def verify(runner, request, absent=False):
    if request["cloud"] == "aws":
        aws_inventory(runner, request, absent)
    elif request["cloud"] == "azure_agent":
        azure_inventory(runner, request, absent)
    else:
        require(False)
