"""Synthetic cloud inventories, including implicit disks and foreign namespace children."""
from copy import deepcopy
import unittest
from test_workloads import d, request


def aws_responses(value):
    r, a = value["resources"], value["auxiliary"]
    tag_values = [{"Key": key, "Value": val} for key, val in {
        "assignment": "week10-a2", "managed_by": "Terraform", "learner": "Eze Favour",
        "expires_at": value["original_expires_at"]}.items()]
    tagged = lambda **kw: dict(kw, Tags=deepcopy(tag_values))
    instance = tagged(InstanceId=r["aws_instance.target"], VpcId=r["aws_vpc.target"], SubnetId=r["aws_subnet.target"],
                      KeyName=r["aws_key_pair.operator"], State={"Name": "running"},
                      BlockDeviceMappings=[{"Ebs": {"VolumeId": a["root_volume"], "DeleteOnTermination": True}}])
    return {
        "describe-vpcs": {"Vpcs": [tagged(VpcId=r["aws_vpc.target"], OwnerId=value["identity"]["aws_account_id"], IsDefault=False)]},
        "describe-key-pairs": {"KeyPairs": [tagged(KeyName=r["aws_key_pair.operator"])]},
        "describe-volumes": {"Volumes": [{"VolumeId": a["root_volume"]}]},
        "describe-instances": {"Reservations": [{"Instances": [instance]}]},
        "describe-network-interfaces": {"NetworkInterfaces": [{"NetworkInterfaceId": a["primary_eni"],
            "Attachment": {"InstanceId": r["aws_instance.target"], "DeleteOnTermination": True}}]},
        "describe-addresses": {"Addresses": []},
        "describe-subnets": {"Subnets": [tagged(SubnetId=r["aws_subnet.target"])]},
        "describe-internet-gateways": {"InternetGateways": [tagged(InternetGatewayId=r["aws_internet_gateway.target"])]},
        "describe-security-groups": {"SecurityGroups": [tagged(GroupId=r["aws_security_group.target"]),
            {"GroupId": a["default_security_group"], "GroupName": "default"}]},
        "describe-route-tables": {"RouteTables": [tagged(RouteTableId=r["aws_route_table.target"], Associations=[{
            "RouteTableAssociationId": r["aws_route_table_association.target"], "SubnetId": r["aws_subnet.target"], "Main": False}]),
            {"RouteTableId": a["default_route_table"], "Associations": [{"Main": True}]}]},
        "describe-network-acls": {"NetworkAcls": [{"NetworkAclId": a["default_network_acl"], "IsDefault": True}]},
        "describe-nat-gateways": {"NatGateways": []}, "describe-vpc-endpoints": {"VpcEndpoints": []},
        "describe-vpn-gateways": {"VpnGateways": []}, "describe-vpc-peering-connections": {"VpcPeeringConnections": []},
        "describe-transit-gateway-attachments": {"TransitGatewayAttachments": []},
        "describe-egress-only-internet-gateways": {"EgressOnlyInternetGateways": []},
    }


class AWS:
    def __init__(self, value):
        self.responses = aws_responses(value)
        self.calls = []

    def aws(self, *args):
        self.calls.append(args)
        return deepcopy(self.responses[args[1]])


class Azure:
    def __init__(self, value):
        r, a = value["resources"], value["auxiliary"]
        tags = {"assignment": "week-10-assignment-01", "managed_by": "Terraform", "learner": "Eze Favour",
                "expires_at": value["original_expires_at"]}
        top = [identifier for address, identifier in r.items() if address not in {
            "azurerm_resource_group.agent", "azurerm_subnet.agent", "azurerm_network_interface_security_group_association.agent"}]
        self.exists = True
        self.inventory = [{"id": identifier, "tags": tags.copy()} for identifier in top] + [{"id": a["os_disk"]}]
        self.group = {"id": r["azurerm_resource_group.agent"], "tags": tags.copy()}
        self.vm = {"name": "fixture", "storageProfile": {"dataDisks": [], "osDisk": {"managedDisk": {"id": a["os_disk"]}}},
                   "networkProfile": {"networkInterfaces": [{"id": r["azurerm_network_interface.agent"]}]}}
        self.extensions = []
        self.network = {"virtualNetworkPeerings": [], "subnets": [{"id": r["azurerm_subnet.agent"], "delegations": [],
                        "ipConfigurations": [{"id": r["azurerm_network_interface.agent"] + "/ipConfigurations/fixture"}]}]}
        self.calls = []

    def az(self, *args):
        self.calls.append(args)
        if args[:2] == ("group", "exists"):
            return self.exists
        if args[:2] == ("group", "show"):
            return deepcopy(self.group)
        if args[:2] == ("resource", "list"):
            return deepcopy(self.inventory)
        if args[:2] == ("vm", "show"):
            return deepcopy(self.vm)
        if args[:3] == ("vm", "extension", "list"):
            return deepcopy(self.extensions)
        if args[:3] == ("network", "vnet", "show"):
            return deepcopy(self.network)
        raise AssertionError("Unrecognized fixture command")


class InventoryTests(unittest.TestCase):
    def test_complete_aws_inventory_read_only(self):
        value = request()
        runner = AWS(value)
        d.inventory.verify(runner, value)
        self.assertTrue(all(args[0] == "ec2" and args[1].startswith("describe-") for args in runner.calls))
        self.assertTrue(any("Name=attachment.instance-id,Values=" in repr(args) for args in runner.calls))
        self.assertEqual(sum(args[1] == "describe-vpc-peering-connections" for args in runner.calls), 2)

    def test_aws_foreign_children_and_partial_pages(self):
        for operation, key in (("describe-subnets", "Subnets"), ("describe-network-interfaces", "NetworkInterfaces"),
                               ("describe-nat-gateways", "NatGateways"), ("describe-vpc-endpoints", "VpcEndpoints"),
                               ("describe-transit-gateway-attachments", "TransitGatewayAttachments"),
                               ("describe-vpc-peering-connections", "VpcPeeringConnections"), ("describe-addresses", "Addresses")):
            value = request()
            runner = AWS(value)
            runner.responses[operation][key].append({"foreign": True})
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                d.inventory.verify(runner, value)
        value = request()
        runner = AWS(value)
        runner.responses["describe-vpcs"]["NextToken"] = "unfinished"
        with self.assertRaises(ValueError):
            d.inventory.verify(runner, value)

    def test_aws_os_disk_retention_and_extra_mount_rejected(self):
        for extra in (False, True):
            value = request()
            runner = AWS(value)
            mappings = runner.responses["describe-instances"]["Reservations"][0]["Instances"][0]["BlockDeviceMappings"]
            if extra:
                mappings.append({"Ebs": {"VolumeId": "foreign"}})
            else:
                mappings[0]["Ebs"]["DeleteOnTermination"] = False
            with self.assertRaises(ValueError):
                d.inventory.verify(runner, value)

    def test_aws_wrong_live_tags_or_nondefault_network(self):
        for change in ("tags", "vpc_default", "vpc_missing", "vpc_type", "acl", "group", "association", "egress", "egress_missing"):
            value = request()
            runner = AWS(value)
            if change == "tags":
                runner.responses["describe-vpcs"]["Vpcs"][0]["Tags"][0]["Value"] = "foreign"
            elif change.startswith("vpc_"):
                record = runner.responses["describe-vpcs"]["Vpcs"][0]
                if change == "vpc_missing":
                    del record["IsDefault"]
                else:
                    record["IsDefault"] = True if change == "vpc_default" else 0
            elif change == "acl":
                runner.responses["describe-network-acls"]["NetworkAcls"][0]["IsDefault"] = False
            elif change == "group":
                runner.responses["describe-security-groups"]["SecurityGroups"][1]["GroupName"] = "foreign"
            elif change == "association":
                runner.responses["describe-route-tables"]["RouteTables"][0]["Associations"][0]["SubnetId"] = "foreign"
            else:
                runner.responses["describe-egress-only-internet-gateways"]["EgressOnlyInternetGateways"] = [{
                    "Attachments": [{} if change == "egress_missing" else {"VpcId": value["resources"]["aws_vpc.target"]}]}]
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.inventory.verify(runner, value)

    def test_aws_absence_checks_disk_key_vpc_and_instance(self):
        value = request()
        runner = AWS(value)
        for key in ("describe-vpcs", "describe-key-pairs", "describe-volumes", "describe-instances"):
            for field in runner.responses[key]:
                runner.responses[key][field] = []
        d.inventory.verify(runner, value, absent=True)
        for operation, key, row in (("describe-volumes", "Volumes", {"VolumeId": value["auxiliary"]["root_volume"]}),
                                   ("describe-key-pairs", "KeyPairs", {"KeyName": value["resources"]["aws_key_pair.operator"]})):
            runner.responses[operation][key] = [row]
            with self.assertRaises(ValueError):
                d.inventory.verify(runner, value, absent=True)
            runner.responses[operation][key] = []

    def test_complete_azure_inventory_and_actual_absence(self):
        value = request("azure_agent")
        runner = Azure(value)
        d.inventory.verify(runner, value)
        with self.assertRaises(ValueError):
            d.inventory.verify(runner, value, absent=True)
        runner.exists = False
        d.inventory.verify(runner, value, absent=True)
        self.assertTrue(all(args[1] not in {"delete", "create", "update"} for args in runner.calls))

    def test_azure_unexpected_children_prevent_group_cascade(self):
        for change in ("resource", "disk", "extension", "subnet", "peering", "private_endpoint", "ip_configuration", "tags"):
            value = request("azure_agent")
            runner = Azure(value)
            if change == "resource":
                runner.inventory.append({"id": value["resources"]["azurerm_resource_group.agent"] + "/foreign"})
            elif change == "disk":
                runner.vm["storageProfile"]["dataDisks"].append({"id": "foreign"})
            elif change == "extension":
                runner.extensions.append({"id": "foreign"})
            elif change == "subnet":
                runner.network["subnets"].append({"id": "foreign"})
            elif change == "peering":
                runner.network["virtualNetworkPeerings"].append({"id": "foreign"})
            elif change == "private_endpoint":
                runner.network["subnets"][0]["privateEndpoints"] = [{"id": "foreign"}]
            elif change == "ip_configuration":
                runner.network["subnets"][0]["ipConfigurations"].append({"id": "foreign"})
            else:
                runner.group["tags"]["assignment"] = "foreign"
            with self.subTest(change=change), self.assertRaises(ValueError):
                d.inventory.verify(runner, value)

    def test_malformed_or_false_absence_is_not_success(self):
        for malformed in (None, {}, "false", 0):
            value = request("azure_agent")
            runner = Azure(value)
            runner.exists = malformed
            with self.assertRaises(ValueError):
                d.inventory.verify(runner, value, absent=True)
        value = request()
        runner = AWS(value)
        runner.responses["describe-vpcs"] = {}
        with self.assertRaises(ValueError):
            d.inventory.verify(runner, value, absent=True)


if __name__ == "__main__":
    unittest.main()
