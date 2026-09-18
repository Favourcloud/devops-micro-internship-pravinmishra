"""Credential-free fixtures; no cloud commands or canary execution."""
import base64
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("canary_worker", ROOT / "worker.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
NOW = datetime(2026, 1, 1, 3, tzinfo=timezone.utc)


def fixture():
    return {"schema_version": 1, "kind": "canary", "armed": True, "lease_id": "abcdef123456",
            "source_commit": "a" * 40, "approved_at": "2026-01-01T00:00:00Z",
            "cleanup_at": "2026-01-01T02:00:00Z", "expires_at": "2026-01-01T04:00:00Z",
            "budget": {"estimated_total_usd": 1, "planning_allowance_usd": 10},
            "readiness": {key: True for key in w.GATES},
            "azure": {key: "00000000-0000-0000-0000-00000000000" + str(n)
                      for n, key in enumerate(("subscription_id", "tenant_id", "client_id", "principal_id"), 1)},
            "aws": {"account_id": "000000000001"},
            "federation": {"issuer": "https://login.microsoftonline.com/00000000-0000-0000-0000-000000000002/v2.0",
                           "subject": "fixture/exact-service-connection", "authorized_party": None}}


def plan(cloud="azure"):
    config = fixture()
    tags = {"assignment": w.ASSIGNMENT, "cleanup_lease": config["lease_id"],
            "expires_at": config["expires_at"], "managed_by": "terraform"}
    if cloud == "azure":
        address = "azurerm_resource_group.canary"
        before = {"id": w.group_id(config), "name": w.group_id(config).split("/")[-1],
                  "location": "uksouth", "tags": tags}
    else:
        address = "aws_vpc.canary"
        tags["Name"] = "dmi-w10-cleanup-abcdef123456-canary"
        before = {"id": "vpc-" + "a" * 17, "owner_id": "000000000001", "cidr_block": "10.199.0.0/24", "tags": tags}
    return {"format_version": "1.2", "complete": True, "errored": False, "resource_changes": [
        {"address": address, "mode": "managed", "type": address.split(".")[0],
         "change": {"actions": ["delete"], "before": before, "after": None}},
        {"address": "terraform_data.authorization", "mode": "managed", "type": "terraform_data",
         "change": {"actions": ["delete"], "before": {"input": config["lease_id"]}, "after": None}}]}


def token(claims):
    return "synthetic." + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=") + ".not-a-signature"


class ConfigTests(unittest.TestCase):
    def test_example_unarmed_and_no_commands(self):
        with patch.object(w.subprocess, "Popen", side_effect=AssertionError("No process expected")):
            self.assertEqual(w.validate_config(w.load_json((ROOT / "config.example.json").read_text()), NOW), "unarmed")

    def test_due_not_due_and_expired_retry(self):
        config = fixture()
        self.assertEqual(w.validate_config(config, NOW), "due")
        self.assertEqual(w.validate_config(config, NOW.replace(hour=1)), "not_due")
        self.assertEqual(w.validate_config(config, NOW.replace(day=2)), "due")

    def test_no_workload_or_unknown_fields(self):
        for key, value in (("kind", "a2-live"), ("armed", "true"), ("schema_version", True),
                           ("controller_pat", "fixture"), ("lease_id", "../../state"), ("source_commit", "0" * 40)):
            with self.subTest(key=key), self.assertRaises(w.Rejected):
                config = fixture()
                config[key] = value
                w.validate_config(config, NOW)

    def test_each_gate_is_required(self):
        for gate in w.GATES:
            with self.subTest(gate=gate), self.assertRaises(w.Rejected):
                config = fixture()
                config["readiness"][gate] = False
                w.validate_config(config, NOW)

    def test_window_and_timezone(self):
        for key, value in (("expires_at", "2026-01-02T00:00:01Z"), ("cleanup_at", "2026-01-01T03:00:00Z"),
                           ("approved_at", "2026-01-01T04:00:00Z"), ("expires_at", "2026-01-01T04:00:00+00:00"),
                           ("expires_at", "2026-02-31T04:00:00Z")):
            with self.subTest(value=value), self.assertRaises(w.Rejected):
                config = fixture()
                config[key] = value
                w.validate_config(config, NOW)

    def test_budget_not_a_boolean_or_nan_or_new_allowance(self):
        for value in (True, float("nan"), 0, -1, 11, "1"):
            with self.subTest(value=value), self.assertRaises(w.Rejected):
                config = fixture()
                config["budget"]["estimated_total_usd"] = value
                w.validate_config(config, NOW)

    def test_exact_federation_and_identity(self):
        for field, value in (("issuer", "https://vstoken.dev.azure.com/fixture"), ("subject", "*"),
                             ("authorized_party", "*")):
            with self.subTest(field=field), self.assertRaises(w.Rejected):
                config = fixture()
                config["federation"][field] = value
                w.validate_config(config, NOW)
        config = fixture()
        config["azure"]["client_id"] = "not-an-id"
        with self.assertRaises(w.Rejected):
            w.validate_config(config, NOW)

    def test_json_duplicate_nonfinite_and_malformed(self):
        for text in ('{"armed":false,"armed":true}', '{"n":NaN}', '{"n":Infinity}', 'no json'):
            with self.subTest(text=text), self.assertRaises(w.Rejected):
                w.load_json(text)

    def test_claim_binding_and_freshness(self):
        config = fixture()
        claims = {"iss": config["federation"]["issuer"], "sub": config["federation"]["subject"],
                  "aud": "api://AzureADTokenExchange", "nbf": int(NOW.timestamp()) - 10,
                  "exp": int(NOW.timestamp()) + 300}
        w.validate_claims(token(claims), config, NOW)
        for key, value in (("iss", "https://example.invalid"), ("sub", "different"), ("aud", ["unexpected"]),
                           ("azp", "00000000-0000-0000-0000-000000000005"), ("exp", 0),
                           ("exp", True), ("nbf", int(NOW.timestamp()) + 100)):
            with self.subTest(key=key), self.assertRaises(w.Rejected):
                changed = dict(claims, **{key: value})
                w.validate_claims(token(changed), config, NOW)
        config["federation"]["authorized_party"] = "00000000-0000-0000-0000-000000000005"
        claims["azp"] = config["federation"]["authorized_party"]
        w.validate_claims(token(claims), config, NOW)


class PlanTests(unittest.TestCase):
    def test_both_exact_canaries(self):
        for cloud in ("azure", "aws"):
            self.assertEqual(w.validate_plan(plan(cloud), fixture(), cloud), 1)

    def test_no_creation_update_replacement_or_noop(self):
        for actions in (["create"], ["update"], ["delete", "create"], ["no-op"]):
            with self.subTest(actions=actions), self.assertRaises(w.Rejected):
                candidate = plan()
                candidate["resource_changes"][0]["change"]["actions"] = actions
                w.validate_plan(candidate, fixture(), "azure")

    def test_no_move_import_deposed_unknown_duplicate(self):
        for field, value in (("previous_address", "old"), ("deposed", "old"),
                             ("address", "azurerm_linux_virtual_machine.canary"), ("mode", "other")):
            with self.subTest(field=field), self.assertRaises(w.Rejected):
                candidate = plan()
                candidate["resource_changes"][0][field] = value
                w.validate_plan(candidate, fixture(), "azure")
        candidate = plan()
        candidate["resource_changes"][0]["change"]["importing"] = {"id": "unrelated"}
        with self.assertRaises(w.Rejected):
            w.validate_plan(candidate, fixture(), "azure")
        candidate = plan()
        candidate["resource_changes"].append(copy.deepcopy(candidate["resource_changes"][0]))
        with self.assertRaises(w.Rejected):
            w.validate_plan(candidate, fixture(), "azure")

    def test_partial_empty_failed_deferred_plans(self):
        candidate = plan()
        candidate["resource_changes"] = candidate["resource_changes"][:1]
        self.assertEqual(w.validate_plan(candidate, fixture(), "azure"), 1)
        candidate["resource_changes"] = []
        self.assertEqual(w.validate_plan(candidate, fixture(), "azure"), 0)
        for key, value in (("errored", True), ("complete", False), ("deferred_changes", [{}])):
            with self.subTest(key=key), self.assertRaises(w.Rejected):
                changed = dict(candidate, **{key: value})
                w.validate_plan(changed, fixture(), "azure")

    def test_wrong_subscription_name_account_and_tags(self):
        for cloud, key, value in (("azure", "id", "/subscriptions/other/resourceGroups/other"),
                                  ("azure", "location", "eastus"), ("aws", "owner_id", "000000000002"),
                                  ("aws", "cidr_block", "10.0.0.0/16")):
            with self.subTest(cloud=cloud, key=key), self.assertRaises(w.Rejected):
                candidate = plan(cloud)
                candidate["resource_changes"][0]["change"]["before"][key] = value
                w.validate_plan(candidate, fixture(), cloud)
        for tag in ("assignment", "cleanup_lease", "expires_at", "managed_by"):
            with self.subTest(tag=tag), self.assertRaises(w.Rejected):
                candidate = plan()
                candidate["resource_changes"][0]["change"]["before"]["tags"][tag] = "wrong"
                w.validate_plan(candidate, fixture(), "azure")

    def test_state_recursive_and_data_only(self):
        self.assertTrue(w.managed_state_empty({"format_version": "1.0"}))
        self.assertTrue(w.managed_state_empty({"format_version": "1.0", "values": {"root_module": {
            "resources": [{"mode": "data"}]}}}))
        self.assertFalse(w.managed_state_empty({"format_version": "1.0", "values": {"root_module": {
            "child_modules": [{"resources": [{"mode": "managed"}]}]}}}))
        with self.assertRaises(w.Rejected):
            w.managed_state_empty({})


class ProcessAndInventoryTests(unittest.TestCase):
    def test_capture_failures_and_timeouts_do_not_expose_output(self):
        runner = w.Runner({"HOME": "/nonexistent"}, ROOT)
        for timeout in (False, True):
            process = Mock(returncode=1, pid=12345)
            process.communicate.side_effect = ([subprocess.TimeoutExpired([], 1), (b"private", b"private")]
                                               if timeout else [(b"private", b"private")])
            with self.subTest(timeout=timeout), patch.object(w.subprocess, "Popen", return_value=process) as call:
                with self.assertRaises(w.Rejected) as error:
                    runner.call(["not-executed"])
                self.assertNotIn("private", str(error.exception))
                self.assertTrue(call.call_args.kwargs["start_new_session"])
                self.assertEqual(call.call_args.kwargs["stdout"], subprocess.PIPE)
                self.assertEqual(call.call_args.kwargs["stderr"], subprocess.PIPE)
                self.assertEqual(call.call_args.kwargs["env"], {"HOME": "/nonexistent"})
                if timeout:
                    process.send_signal.assert_called_once_with(w.signal.SIGINT)
                    self.assertEqual(process.communicate.call_args.kwargs["timeout"], 30)

    def test_stuck_command_kills_only_its_owned_process_group(self):
        process = Mock(returncode=-9, pid=12345)
        process.communicate.side_effect = [subprocess.TimeoutExpired([], 1), subprocess.TimeoutExpired([], 30),
                                          (b"private", b"private")]
        with patch.object(w.subprocess, "Popen", return_value=process), patch.object(w.os, "killpg") as kill:
            with self.assertRaises(w.Rejected):
                w.Runner({}, ROOT).call(["not-executed"])
        kill.assert_called_once_with(12345, w.signal.SIGKILL)
        self.assertEqual(process.communicate.call_count, 3)

    def test_success_decodes_only_captured_stdout(self):
        process = Mock(returncode=0)
        process.communicate.return_value = (b'{"ok":true}', b"not printed")
        with patch.object(w.subprocess, "Popen", return_value=process):
            self.assertEqual(w.Runner({}, ROOT).call(["not-executed"]), {"ok": True})

    def test_azure_children_block_group_deletion(self):
        runner = Mock()
        runner.az.side_effect = [True, [{"id": "unexpected-child"}]]
        with self.assertRaises(w.Rejected):
            w.verify_empty_canary(runner, fixture(), "azure")
        runner.az.side_effect = [False]
        w.verify_empty_canary(runner, fixture(), "azure")

    def test_aws_children_and_ambiguous_inventory_fail_closed(self):
        for results in ([{"Vpcs": [{}, {}]}], [{"Vpcs": [{"VpcId": "vpc-" + "a" * 17}]},
                                               {"Subnets": [{"SubnetId": "unexpected"}]}]):
            runner = Mock()
            runner.aws.side_effect = results
            with self.assertRaises(w.Rejected):
                w.verify_empty_canary(runner, fixture(), "aws")

    def test_only_empty_vpc_with_default_network_objects_is_accepted(self):
        identifier = "vpc-" + "a" * 17
        responses = [{"Vpcs": [{"VpcId": identifier}]}] + [{key: []} for key in (
            "Subnets", "NetworkInterfaces", "InternetGateways", "EgressOnlyInternetGateways", "VpcEndpoints",
            "VpnGateways", "VpcPeeringConnections", "VpcPeeringConnections", "TransitGatewayAttachments")]
        responses += [
            {"SecurityGroups": [{"VpcId": identifier, "GroupName": "default"}]},
            {"NetworkAcls": [{"VpcId": identifier, "IsDefault": True}]},
            {"RouteTables": [{"VpcId": identifier, "Associations": [{"Main": True}]}]},
        ]
        runner = Mock()
        runner.aws.side_effect = copy.deepcopy(responses)
        w.verify_empty_canary(runner, fixture(), "aws")
        self.assertEqual(runner.aws.call_count, len(responses))
        self.assertEqual(runner.aws.call_args_list[4].args, ("ec2", "describe-egress-only-internet-gateways"))
        for attached_to, accepted in (("vpc-" + "b" * 17, True), (identifier, False)):
            altered = copy.deepcopy(responses)
            altered[4] = {"EgressOnlyInternetGateways": [{"Attachments": [{"VpcId": attached_to}]}]}
            runner.aws.side_effect = altered
            if accepted:
                w.verify_empty_canary(runner, fixture(), "aws")
            else:
                with self.assertRaises(w.Rejected):
                    w.verify_empty_canary(runner, fixture(), "aws")
        for index in range(1, len(responses)):
            with self.subTest(inventory=index), self.assertRaises(w.Rejected):
                altered = copy.deepcopy(responses)
                rows = next(iter(altered[index].values()))
                rows.append({"unexpected": True})
                runner.aws.side_effect = altered
                w.verify_empty_canary(runner, fixture(), "aws")

    def test_malformed_network_inventory_cannot_count_as_empty(self):
        identifier = "vpc-" + "a" * 17
        for response in ({}, {"Subnets": None}, {"Subnets": ""}):
            runner = Mock()
            runner.aws.side_effect = [{"Vpcs": [{"VpcId": identifier}]}, response]
            with self.subTest(response=response), self.assertRaises(w.Rejected):
                w.verify_empty_canary(runner, fixture(), "aws")

    def test_absence_requires_successful_typed_responses(self):
        runner = Mock()
        runner.az.return_value = "false"
        with self.assertRaises(w.Rejected):
            w.absent(runner, fixture(), "azure")
        runner.aws.return_value = {}
        with self.assertRaises(w.Rejected):
            w.absent(runner, fixture(), "aws")
        runner.aws.return_value = {"Vpcs": []}
        self.assertTrue(w.absent(runner, fixture(), "aws"))

    def test_backend_login_not_shared_keys_and_separate_states(self):
        for cloud in ("azure", "aws"):
            config = w.backend(fixture(), cloud)
            self.assertTrue(config["use_azuread_auth"])
            self.assertTrue(config["use_cli"])
            self.assertEqual(config["container_name"], "canary-" + cloud)
            self.assertNotIn("access_key", config)
            self.assertNotIn("sas_token", config)

    def test_missing_state_never_initializes_empty_replacement(self):
        runner = Mock()
        runner.az.return_value = {"exists": False}
        with patch.object(w, "Runner", side_effect=AssertionError("Do not initialize Terraform")):
            with self.assertRaises(w.Rejected):
                w.clean_cloud(runner, fixture(), "azure", Path("/not-executed"), Path("/not-written"))

    def test_saved_delete_plan_and_absence_are_both_required(self):
        outer = Mock()
        outer.environment = {}
        outer.az.return_value = {"exists": True}
        inner = Mock()
        inner.call.side_effect = [b"", b"", plan(), b"", {"format_version": "1.0"}]
        with patch.object(w, "Runner", return_value=inner), patch.object(w, "verify_empty_canary"), \
             patch.object(w, "absent", return_value=True), patch.object(Path, "mkdir"), \
             patch.object(Path, "is_file", return_value=True), patch.object(Path, "is_symlink", return_value=False), \
             patch.object(w.shutil, "copyfile"), patch.object(Path, "write_text") as writes, \
             patch.object(Path, "read_bytes", return_value=b"synthetic saved plan"):
            result = w.clean_cloud(outer, fixture(), "azure", Path("/not-executed"), Path("/not-written"))
        self.assertTrue(result["verified_absent"])
        commands = [call.args[0] for call in inner.call.call_args_list]
        self.assertIn("-destroy", commands[1])
        self.assertEqual(commands[3][-1], "destroy.tfplan")
        self.assertNotIn("-auto-approve", commands[3])
        self.assertFalse(json.loads(writes.call_args_list[-1].args[0])["live_execution_approved"])

    def test_aws_auth_failure_does_not_skip_azure_cleanup(self):
        with patch.object(w, "assume_aws", side_effect=w.Rejected("fixture")), \
             patch.object(w, "clean_cloud", return_value={"verified_absent": True}) as clean:
            result = w.clean_both(Mock(), fixture(), "synthetic", Path("/not-executed"), Path("/not-written"))
        self.assertFalse(result["aws"]["verified_absent"])
        self.assertTrue(result["azure"]["verified_absent"])
        self.assertEqual(clean.call_args.args[2], "azure")

    def test_invalid_plan_never_applied(self):
        outer = Mock()
        outer.environment = {}
        outer.az.return_value = {"exists": True}
        inner = Mock()
        invalid = plan()
        invalid["resource_changes"][0]["change"]["actions"] = ["create"]
        inner.call.side_effect = [b"", b"", invalid]
        with patch.object(w, "Runner", return_value=inner), patch.object(w, "verify_empty_canary"), \
             patch.object(Path, "mkdir"), patch.object(Path, "is_file", return_value=True), \
             patch.object(Path, "is_symlink", return_value=False), patch.object(w.shutil, "copyfile"), \
             patch.object(Path, "write_text"):
            with self.assertRaises(w.Rejected):
                w.clean_cloud(outer, fixture(), "azure", Path("/not-executed"), Path("/not-written"))
        self.assertEqual(inner.call.call_count, 3)

    def test_real_yaml_parser_and_hosted_schedule(self):
        result = subprocess.run(["/usr/bin/ruby", "-e", 'require "yaml"; require "json"; puts JSON.generate(Psych.safe_load(File.read(ARGV[0])))',
                                 str(ROOT / "canary.azure-pipelines.yml")], capture_output=True, check=True)
        document = json.loads(result.stdout)
        self.assertEqual(document["trigger"], "none")
        self.assertEqual(document["pr"], "none")
        self.assertEqual(document["schedules"][0]["cron"], "*/15 * * * *")
        job = document["stages"][0]["jobs"][0]
        self.assertEqual(job["pool"], {"vmImage": "ubuntu-24.04"})
        steps = job["strategy"]["runOnce"]["deploy"]["steps"]
        task = [s for s in steps if s.get("task") == "AzureCLI@2"][0]
        self.assertFalse(task["inputs"]["useGlobalConfig"])
        self.assertFalse(task["inputs"]["visibleAzLogin"])
        self.assertIn("canaryDue", task["condition"])
        self.assertNotIn("PublishPipelineArtifact", json.dumps(document))


if __name__ == "__main__":
    unittest.main()
