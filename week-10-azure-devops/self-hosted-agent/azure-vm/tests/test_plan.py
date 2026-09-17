import base64
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_plan", ROOT / "check_plan.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 17, tzinfo=timezone.utc)
        self.inputs = {"project_name": "dmi-w10-a1-test", "live_execution_approved": True,
                       "subscription_id": "11111111-1111-1111-1111-111111111111",
                       "expires_at": (self.now + timedelta(hours=1)).isoformat(),
                       "controller_ipv4_cidr": "8.8.8.8/32", "ssh_public_key": "test-public-key",
                       "image_version": "22.04.202608060"}
        self.plan = {"applyable": True, "resource_changes": []}
        for address in sorted(CHECK.ADDRESSES):
            kind = address.split(".")[0]
            values = {"name": "dmi-w10-a1-test-resource", "resource_group_name": "dmi-w10-a1-test-rg", "location": "uksouth",
                      "id": "/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/dmi-w10-a1-test-rg/providers/test/resource"}
            self.plan["resource_changes"].append({"mode": "managed", "address": address, "type": kind, "change": {"actions": ["create"], "after": values}})
        self.vm = self.values("azurerm_linux_virtual_machine.agent")
        self.vm.update(size="Standard_D2lds_v6", admin_username="labadmin", disable_password_authentication=True,
                       disk_controller_type="NVMe", secure_boot_enabled=True, vtpm_enabled=True,
                       boot_diagnostics=[{"storage_account_uri": None}],
                       admin_ssh_key=[{"username": "labadmin", "public_key": "test-public-key"}],
                       custom_data=base64.b64encode((ROOT / "cloud-init.yaml").read_bytes()).decode(),
                       os_disk=[{"disk_size_gb": 32, "storage_account_type": "Standard_LRS"}],
                       source_image_reference=[{"publisher": "Canonical", "offer": "0001-com-ubuntu-server-jammy", "sku": "22_04-lts-gen2", "version": self.inputs["image_version"]}])
        self.nsg = self.values("azurerm_network_security_group.agent")
        self.nsg["security_rule"] = [
            {"name": "SSHFromControllerOnly", "priority": 100, "direction": "Inbound", "access": "Allow", "protocol": "Tcp", "destination_port_range": "22", "source_address_prefix": "8.8.8.8/32"},
            {"name": "DenyOtherInbound", "priority": 200, "direction": "Inbound", "access": "Deny", "protocol": "*", "source_address_prefix": "*", "destination_port_range": "*"}]

    def values(self, address):
        return next(r["change"]["after"] for r in self.plan["resource_changes"] if r["address"] == address)

    def check(self, destroy=False):
        return CHECK.validate(self.plan, self.inputs, destroy=destroy, now=self.now)

    def test_exact_create_allowed(self):
        self.assertEqual(self.check(), [])

    def test_missing_or_extra_resources_rejected(self):
        self.plan["resource_changes"].pop()
        self.assertIn("resource_set", self.check())
        self.plan["resource_changes"].append({"address": "azurerm_role_assignment.extra", "change": {"actions": ["create"]}})
        self.assertIn("unexpected_resource", self.check())

    def test_replacement_or_import_rejected(self):
        self.plan["resource_changes"][0]["change"]["actions"] = ["delete", "create"]
        self.assertIn("unexpected_action", self.check())
        self.plan["resource_changes"][0]["change"] = {"actions": ["create"], "importing": {"id": "existing"}}
        self.assertIn("unexpected_action", self.check())

    def test_shared_resource_rejected(self):
        self.vm["resource_group_name"] = "production-rg"
        self.assertIn("resource_group", self.check())

    def test_root_password_and_identity_rejected(self):
        for key, value in [("admin_username", "root"), ("admin_password", "fixture-not-secret"), ("identity", [{"type": "SystemAssigned"}]), ("disable_password_authentication", False)]:
            original = self.vm.get(key)
            self.vm[key] = value
            self.assertIn("vm_identity_or_size", self.check())
            self.vm[key] = original

    def test_nvme_secure_boot_and_vtpm_required(self):
        for key, value in [("disk_controller_type", "SCSI"), ("secure_boot_enabled", False), ("vtpm_enabled", False)]:
            original = self.vm[key]
            self.vm[key] = value
            self.assertIn("vm_disk_security", self.check())
            self.vm[key] = original

    def test_managed_boot_diagnostics_required(self):
        for value in ([], [{"storage_account_uri": "https://unexpected.invalid/"}]):
            self.vm["boot_diagnostics"] = value
            self.assertIn("managed_boot_diagnostics", self.check())

    def test_key_image_disk_and_bootstrap_bound(self):
        for key, value, error in [("admin_ssh_key", [], "ssh_key"), ("source_image_reference", [], "image"), ("os_disk", [], "disk"), ("custom_data", "", "bootstrap")]:
            original = self.vm[key]
            self.vm[key] = value
            self.assertIn(error, self.check())
            self.vm[key] = original

    def test_wide_or_private_ssh_rejected(self):
        for cidr in ("0.0.0.0/0", "8.8.8.0/24", "127.0.0.1/32", "10.0.0.1/32"):
            self.inputs["controller_ipv4_cidr"] = cidr
            self.nsg["security_rule"][0]["source_address_prefix"] = cidr
            self.assertIn("ssh_boundary", self.check())

    def test_extra_inbound_rule_rejected(self):
        self.nsg["security_rule"].append({"name": "HTTP"})
        self.assertIn("inbound_rules", self.check())

    def test_expired_or_overlong_lifetime_rejected(self):
        for hours in (-1, 3):
            self.inputs["expires_at"] = (self.now + timedelta(hours=hours)).isoformat()
            self.assertIn("lifetime", self.check())

    def test_missing_approval_rejected(self):
        self.inputs["live_execution_approved"] = False
        self.assertIn("approval", self.check())

    def test_partial_cleanup_allowed_after_expiry(self):
        resource = copy.deepcopy(self.plan["resource_changes"][0])
        resource["change"] = {"actions": ["delete"], "before": resource["change"]["after"]}
        self.plan["resource_changes"] = [resource]
        self.inputs["expires_at"] = "2020-01-01T00:00:00Z"
        self.assertEqual(self.check(destroy=True), [])

    def test_cleanup_wrong_subscription_rejected(self):
        resource = copy.deepcopy(self.plan["resource_changes"][0])
        before = resource["change"]["after"]
        before["id"] = before["id"].replace(self.inputs["subscription_id"], "44444444-4444-4444-4444-444444444444")
        resource["change"] = {"actions": ["delete"], "before": before}
        self.plan["resource_changes"] = [resource]
        self.assertIn("subscription_ownership", self.check(destroy=True))

    def test_cleanup_shared_association_rejected(self):
        self.plan["resource_changes"] = [{"mode": "managed", "address": "azurerm_network_interface_security_group_association.agent", "type": "azurerm_network_interface_security_group_association", "change": {"actions": ["delete"], "before": {"network_interface_id": "/resourceGroups/production-rg/nic", "network_security_group_id": "/resourceGroups/production-rg/nsg"}}}]
        self.assertIn("association_ownership", self.check(destroy=True))

    def test_cleanup_association_requires_same_subscription(self):
        scope = "/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/dmi-w10-a1-test-rg/providers/Microsoft.Network/"
        nic = scope + "networkInterfaces/dmi-w10-a1-test-nic"
        foreign_nsg = (scope + "networkSecurityGroups/dmi-w10-a1-test-nsg").replace("11111111-1111-1111-1111-111111111111", "44444444-4444-4444-4444-444444444444")
        self.plan["resource_changes"] = [{"mode": "managed", "address": "azurerm_network_interface_security_group_association.agent", "type": "azurerm_network_interface_security_group_association", "change": {"actions": ["delete"], "before": {"id": nic + "|" + foreign_nsg, "network_interface_id": nic, "network_security_group_id": foreign_nsg}}}]
        self.assertIn("association_ownership", self.check(destroy=True))

    def test_cloud_init_is_nonprivileged_and_has_no_install_or_registration(self):
        result = subprocess.run(["/usr/bin/ruby", "--disable-gems", "-rpsych", "-rjson", "-e", "puts JSON.generate(Psych.safe_load(STDIN.read, [], [], false))"], input=(ROOT / "cloud-init.yaml").read_text(), text=True, capture_output=True, check=True)
        config = json.loads(result.stdout)
        self.assertFalse(config["package_update"])
        self.assertFalse(config["package_upgrade"])
        self.assertFalse(config["ssh_pwauth"])
        account = config["users"][1]
        self.assertEqual(account["name"], "azdoagent")
        self.assertIs(account["sudo"], False)
        self.assertIs(account["lock_passwd"], True)
        self.assertEqual(account["groups"], [])
        self.assertEqual(config["runcmd"], [["install", "-d", "-m", "0700", "-o", "azdoagent", "-g", "azdoagent", "/home/azdoagent/azdo-agent"], ["chmod", "0700", "/home/azdoagent"]])


if __name__ == "__main__":
    unittest.main()
