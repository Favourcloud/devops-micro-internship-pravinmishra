import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cleanup", PROJECT / "scripts/check-cleanup.py")
cleanup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup)


def fixture_inventory():
    return {address: spec[4] + "-00000000000000000" for address, spec in cleanup.SPECS.items()}


def fixture_state():
    inventory = fixture_inventory()
    resources = [
        {"address": address, "mode": "managed", "values": {"id": value, "unused_sensitive_value": "OMIT-ME"}}
        for address, value in inventory.items() if address not in ("root_volume", "primary_eni")
    ]
    for resource in resources:
        if resource["address"] == "aws_key_pair.lab":
            resource["values"].update(id="lab-key-name", key_pair_id=inventory[resource["address"]])
        if resource["address"] == "aws_instance.web":
            resource["values"].update(primary_network_interface_id=inventory["primary_eni"],
                                      root_block_device=[{"volume_id": inventory["root_volume"]}])
    return {"values": {"root_module": {"resources": resources}}}


class CleanupTests(unittest.TestCase):
    def test_capture_keeps_only_exact_ids_and_no_sensitive_state(self):
        with patch.object(cleanup.subprocess, "run") as run:
            inventory = cleanup.capture(fixture_state())
            self.assertEqual(inventory, fixture_inventory())
            self.assertNotIn("OMIT-ME", json.dumps(inventory))
            run.assert_not_called()

    def test_capture_rejects_partial_apply(self):
        state = fixture_state()
        state["values"]["root_module"]["resources"].pop()
        with self.assertRaises(ValueError):
            cleanup.capture(state)

    def test_capture_rejects_other_modules(self):
        state = fixture_state()
        state["values"]["root_module"]["child_modules"] = [{"address": "module.unrelated"}]
        with self.assertRaises(ValueError):
            cleanup.capture(state)

    def test_inventory_rejects_missing_volume_or_invalid_id(self):
        for address, invalid in (("root_volume", None), ("aws_vpc.lab", "vpc-not-an-id")):
            with self.subTest(address=address):
                inventory = fixture_inventory()
                inventory[address] = invalid
                with self.assertRaises(ValueError):
                    cleanup.validate_inventory(inventory)

    def test_matching_not_found_is_absence(self):
        for address, spec in cleanup.SPECS.items():
            if not spec[3]:
                continue
            response = subprocess.CompletedProcess([], 255, "", f"An error occurred ({spec[3]}) when calling an operation")
            with self.subTest(address=address), patch.object(cleanup.subprocess, "run", return_value=response):
                self.assertTrue(cleanup.check_one(address, fixture_inventory()[address], "eu-west-2"))

    def test_denied_expired_or_generic_errors_are_not_absence(self):
        for error in ("UnauthorizedOperation", "AccessDenied", "ExpiredToken", "RequestTimeout", "Other.NotFound"):
            with self.subTest(error=error), patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 255, "", f"An error occurred ({error})")):
                self.assertFalse(cleanup.check_one("aws_vpc.lab", fixture_inventory()["aws_vpc.lab"], "eu-west-2"))

    def test_remaining_resource_is_not_absent(self):
        response = subprocess.CompletedProcess([], 0, json.dumps({"Volumes": [{"VolumeId": "vol-00000000000000000"}]}), "")
        with patch.object(cleanup.subprocess, "run", return_value=response):
            self.assertFalse(cleanup.check_one("root_volume", fixture_inventory()["root_volume"], "eu-west-2"))

    def test_terminated_instance_is_accepted_but_running_is_not(self):
        resource_id = fixture_inventory()["aws_instance.web"]
        for state in ("terminated", "running", "stopped", "shutting-down"):
            data = {"Reservations": [{"Instances": [{"InstanceId": resource_id, "State": {"Name": state}}]}]}
            with self.subTest(state=state), patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(data), "")):
                self.assertEqual(cleanup.check_one("aws_instance.web", resource_id, "eu-west-2"), state == "terminated")

    def test_wrong_instance_and_empty_reservations_do_not_prove_termination(self):
        for data in ({"Reservations": []}, {"Reservations": [{"Instances": [{"InstanceId": "i-11111111111111111", "State": {"Name": "terminated"}}]}]}):
            with patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(data), "")):
                self.assertFalse(cleanup.check_one("aws_instance.web", fixture_inventory()["aws_instance.web"], "eu-west-2"))

    def test_association_uses_exact_filter_and_read_only_operation(self):
        with patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"RouteTables": []}', "")) as run:
            address = "aws_route_table_association.public"
            self.assertTrue(cleanup.check_one(address, fixture_inventory()[address], "eu-west-2"))
            argv = run.call_args.args[0]
            self.assertEqual(argv[:3], ["aws", "ec2", "describe-route-tables"])
            self.assertIn("Name=association.route-table-association-id,Values=rtbassoc-00000000000000000", argv)
            self.assertEqual(run.call_args.kwargs["env"]["AWS_EC2_METADATA_DISABLED"], "true")
        self.assertTrue(all(spec[0].startswith("describe-") for spec in cleanup.SPECS.values()))

    def test_unexpected_response_shape_fails(self):
        for stdout in ('{"Vpcs": null}', '{"wrong": []}', 'not-json'):
            with patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout, "")):
                with self.assertRaises((ValueError, KeyError)):
                    cleanup.check_one("aws_vpc.lab", fixture_inventory()["aws_vpc.lab"], "eu-west-2")

    def test_verify_without_approval_cannot_call_aws(self):
        with patch.object(cleanup.subprocess, "run") as run, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                cleanup.main(["verify", "--inventory", "unused.json", "--region", "eu-west-2"])
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()

    def test_verify_region_mismatch_cannot_call_aws(self):
        with tempfile.TemporaryDirectory(prefix="a2-test-", dir="/tmp") as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps({"region": "eu-west-2", "resources": fixture_inventory()}))
            with patch.object(cleanup.subprocess, "run") as run, contextlib.redirect_stderr(io.StringIO()):
                result = cleanup.main(["verify", "--inventory", str(path), "--region", "us-east-1", "--authorized-live-check"])
                self.assertEqual(result, 1)
                run.assert_not_called()

    def test_capture_cli_is_local_and_records_region(self):
        output = io.StringIO()
        with patch.object(cleanup.sys, "stdin", io.StringIO(json.dumps(fixture_state()))), contextlib.redirect_stdout(output), patch.object(cleanup.subprocess, "run") as run:
            self.assertEqual(cleanup.main(["capture", "--region", "eu-west-2"]), 0)
            self.assertEqual(json.loads(output.getvalue()), {"region": "eu-west-2", "resources": fixture_inventory()})
            run.assert_not_called()

    def test_verification_failure_returns_nonzero(self):
        with tempfile.TemporaryDirectory(prefix="a2-test-", dir="/tmp") as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps({"region": "eu-west-2", "resources": fixture_inventory()}))
            with patch.object(cleanup, "check_one", side_effect=[False] + [True] * 12) as check, contextlib.redirect_stdout(io.StringIO()):
                result = cleanup.main(["verify", "--inventory", str(path), "--region", "eu-west-2", "--authorized-live-check"])
                self.assertEqual(result, 1)
                self.assertEqual(check.call_count, 13)


if __name__ == "__main__":
    unittest.main()
