"""Synthetic A2 cleanup cases. No SDK, credentials, subprocess, cloud or filesystem writes."""
import base64
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / "workloads"
spec = importlib.util.spec_from_file_location("workload_destroy", ROOT / "destroy.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
NOW = datetime(2026, 9, 20, 8, 0, tzinfo=timezone.utc)
UUIDS = ["00000000-0000-0000-0000-00000000000" + str(n) for n in range(1, 6)]


def request(cloud="aws"):
    value = json.loads((ROOT / "request.example.json").read_text())
    value.update(armed=True, cloud=cloud, source_commit="1" * 40, terraform_sha256="2" * 64,
                 prefix="dmi-w10-a2-fixture" if cloud == "aws" else "dmi-w10-a1-fixture",
                 original_expires_at="2026-09-19T12:00:00Z")
    value["approval"] = {"approved_at": "2026-09-20T07:30:00Z", "execute_before": "2026-09-20T09:00:00Z",
                         "receipt_sha256": "3" * 64}
    value["gates"] = dict.fromkeys(d.GATES, True)
    value["artifacts"] = {"inputs_sha256": "4" * 64}
    identity = dict(zip(("azure_subscription_id", "azure_tenant_id", "azure_client_id", "azure_principal_id"), UUIDS))
    identity.update(aws_account_id="000000000001" if cloud == "aws" else None,
                    aws_role_arn="arn:aws:iam::000000000001:role/dmi-w10-a2-cleanup-fixture" if cloud == "aws" else None)
    value["identity"] = identity
    value["backend"] = {"resource_group_name": "independent-state", "storage_account_name": "independentfixture",
                        "container_name": "private-state", "key": value["prefix"] + "/" + cloud + ".tfstate",
                        "lineage": UUIDS[4], "serial": 1, "state_sha256": "5" * 64, "restore_receipt_sha256": "6" * 64}
    if cloud == "aws":
        value["resources"] = {address: prefix + "-" + format(n, "017x") if prefix else value["prefix"] + "-key"
                              for n, (address, prefix) in enumerate(d.AWS.items(), 1)}
        value["auxiliary"] = {key: prefix + "-" + format(n, "017x") for n, (key, prefix) in enumerate({
            "root_volume": "vol", "primary_eni": "eni", "default_route_table": "rtb",
            "default_security_group": "sg", "default_network_acl": "acl"}.items(), 20)}
    else:
        group = "/subscriptions/" + UUIDS[0] + "/resourceGroups/" + value["prefix"] + "-rg"
        value["resources"] = {address: group + suffix + ("fixture" if suffix else "") for address, suffix in d.AZURE.items()}
        value["resources"]["azurerm_subnet.agent"] += "/subnets/fixture"
        value["auxiliary"] = {"os_disk": group + "/providers/Microsoft.Compute/disks/fixture-osdisk"}
    return value


def plan_for(value):
    cloud = value["cloud"]
    ownership = {"assignment": "week10-a2" if cloud == "aws" else "week-10-assignment-01",
                 "managed_by": "Terraform", "learner": "Eze Favour", "expires_at": value["original_expires_at"]}
    changes, root, guard = [], [], []
    for address in [*value["resources"], d.GUARD[cloud]]:
        before = {"id": value["resources"].get(address, UUIDS[4])}
        if address == d.GUARD[cloud]:
            before["input"] = {"assignment": ownership["assignment"], "expires_at": value["original_expires_at"]}
            if cloud == "aws":
                before["input"] = {"assignment": "week10-a2", "name_prefix": value["prefix"],
                                   "approval": {"expires_at": value["original_expires_at"]}}
        else:
            before["tags_all" if cloud == "aws" else "tags"] = ownership.copy()
        if address == "aws_instance.target":
            before.update(root_block_device=[{"volume_id": value["auxiliary"]["root_volume"], "delete_on_termination": True}],
                          primary_network_interface_id=value["auxiliary"]["primary_eni"], ebs_block_device=[])
        if address == "azurerm_linux_virtual_machine.agent":
            before["os_disk"] = [{"name": "fixture-osdisk"}]
        resource = {"address": address, "mode": "managed", "type": address.split(".")[-2]}
        changes.append(dict(resource, change={"actions": ["delete"], "before": before, "after": None}))
        (guard if address.startswith("module.") else root).append(dict(resource, values=deepcopy(before)))
    module = {"resources": root}
    if guard:
        module["child_modules"] = [{"address": "module.guard", "resources": guard}]
    return {"format_version": "1.2", "terraform_version": "1.13.5", "complete": True, "errored": False,
            "applyable": True, "timestamp": "2026-09-20T08:00:00Z", "resource_changes": changes,
            "prior_state": {"values": {"root_module": module}}, "planned_values": {}, "checks": []}


def state_for(value):
    state = {"version": 4, "lineage": value["backend"]["lineage"], "serial": 1,
             "resources": [{"mode": "managed", "instances": [{}]}]}
    value["backend"]["state_sha256"] = d.digest(d.canonical(state))
    return state


def backend_for(value):
    config = {key: value["backend"][key] for key in ("resource_group_name", "storage_account_name", "container_name", "key")}
    config.update(subscription_id=UUIDS[0], tenant_id=UUIDS[1], use_azuread_auth=True, use_cli=True,
                  access_key=None, sas_token=None, use_msi=False, use_oidc=False, environment="public")
    return {"backend": {"type": "azurerm", "config": config}}


class FakeRunner:
    def __init__(self, value):
        self.calls = []
        self.state = state_for(value)
        self.plan = plan_for(value)

    def call(self, arguments, **options):
        self.calls.append((arguments, options))
        operation = arguments[1]
        if operation == "state":
            return deepcopy(self.state)
        if operation == "show":
            return deepcopy(self.plan)
        if operation == "apply":
            self.state.update(serial=2, resources=[])
        return b""


class RequestTests(unittest.TestCase):
    def test_unarmed_without_any_process(self):
        with mock.patch.object(d.core, "Runner", side_effect=AssertionError("process forbidden")), mock.patch.dict(d.os.environ, {}, clear=True):
            self.assertEqual(d.run(ROOT / "request.example.json", None)["status"], "unarmed")

    def test_both_scopes_and_late_cleanup(self):
        for cloud in d.GUARD:
            value = request(cloud)
            self.assertEqual(d.validate_request(value, NOW), "armed")
            self.assertLess(d.core.utc(value["original_expires_at"]), NOW)

    def test_wrong_schema_flags_and_scope(self):
        for field, wrong in (("schema_version", True), ("armed", "true"), ("kind", "canary"), ("cloud", "azure"),
                             ("cloud", "a3"), ("prefix", "dmi-w10-a3-fixture"), ("source_commit", "0" * 40)):
            with self.subTest(field=field, wrong=wrong):
                value = request()
                value[field] = wrong
                with self.assertRaises(ValueError):
                    d.validate_request(value, NOW)

    def test_unknown_fields_and_missing_gates(self):
        for field in ("gates", "approval", "backend", "identity", "artifacts", "resources", "auxiliary"):
            value = request()
            value[field]["unexpected"] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                d.validate_request(value, NOW)
        for gate in d.GATES:
            value = request()
            value["gates"][gate] = False
            with self.subTest(gate=gate), self.assertRaises(ValueError):
                d.validate_request(value, NOW)

    def test_authority_expiry_not_resource_expiry(self):
        for end in ("2026-09-20T08:00:00Z", "2026-09-22T09:00:00Z"):
            value = request()
            value["approval"]["execute_before"] = end
            with self.assertRaises(ValueError):
                d.validate_request(value, NOW)
        value = request()
        value["approval"]["approved_at"] = "2026-09-20T08:01:00Z"
        with self.assertRaises(ValueError):
            d.validate_request(value, NOW)

    def test_no_root_or_user_cleanup_role(self):
        for role in ("arn:aws:iam::000000000001:root", "arn:aws:iam::000000000001:user/dmi-week10-operator",
                     "arn:aws:iam::000000000002:role/dmi-w10-a2-cleanup-fixture"):
            value = request()
            value["identity"]["aws_role_arn"] = role
            with self.assertRaises(ValueError):
                d.validate_request(value, NOW)

    def test_circular_state_and_wrong_key(self):
        for field, wrong in (("resource_group_name", "dmi-w10-cleanup-fixture"), ("storage_account_name", "w10clnabcdef123456"),
                             ("key", "other.tfstate"), ("serial", True), ("restore_receipt_sha256", None)):
            value = request()
            value["backend"][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                d.validate_request(value, NOW)

    def test_foreign_azure_group_disk_or_association(self):
        for section, key in (("resources", "azurerm_resource_group.agent"), ("resources", "azurerm_subnet.agent"),
                             ("resources", "azurerm_network_interface_security_group_association.agent"), ("auxiliary", "os_disk")):
            value = request("azure_agent")
            value[section][key] = value[section][key].replace("fixture", "foreign")
            with self.subTest(key=key), self.assertRaises(ValueError):
                d.validate_request(value, NOW)

    def test_backend_no_key_sas_oidc_local_or_wrong_identity(self):
        value = request()
        d.check_backend(backend_for(value), value)
        for field, wrong in (("access_key", "not-a-secret-fixture"), ("sas_token", "fixture"), ("use_oidc", True),
                             ("endpoint", "https://invalid.example"), ("key", "different.tfstate"), ("subscription_id", UUIDS[4])):
            metadata = backend_for(value)
            metadata["backend"]["config"][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                d.check_backend(metadata, value)
        metadata = backend_for(value)
        metadata["backend"]["type"] = "local"
        with self.assertRaises(ValueError):
            d.check_backend(metadata, value)

    def test_strict_json_and_regular_file_flags(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}'):
            with self.assertRaises(ValueError):
                d.core.load_json(text)
        with mock.patch.object(d.os, "open", wraps=d.os.open) as opened:
            self.assertTrue(d.regular(ROOT / "request.example.json"))
        self.assertTrue(opened.call_args.args[1] & d.os.O_NOFOLLOW)
        self.assertTrue(opened.call_args.args[1] & d.os.O_NONBLOCK)


class BundleTests(unittest.TestCase):
    def bundle(self, cloud="aws", mutation=None):
        value = request(cloud)
        bundle = ROOT / "never-created-bundle"
        working = bundle / "root"
        source = d.WEEK / ("application-pipelines/target/terraform/aws" if cloud == "aws" else "self-hosted-agent/azure-vm")
        names = {"main.tf", "variables.tf", ".terraform.lock.hcl"}
        if cloud == "azure_agent":
            names |= {"versions.tf", "cloud-init.yaml"}
        files = {working / name: (source / name).read_bytes() for name in names}
        files[working / "backend_override.tf"] = (ROOT / (cloud + ".backend.tf.example")).read_bytes()
        files[working / "cleanup-inputs.json"] = b"{}"
        files[working / ".terraform/terraform.tfstate"] = json.dumps(backend_for(value)).encode()
        modules = {"Modules": [{"Key": "", "Source": "", "Dir": "."},
                                {"Key": "guard", "Source": "../guard", "Dir": "../guard"}]}
        files[working / ".terraform/modules/modules.json"] = json.dumps(modules).encode()
        files[working / ".terraform/environment"] = b"default"
        if cloud == "aws":
            files[bundle / "guard/main.tf"] = (source.parent / "guard/main.tf").read_bytes()
        tool = bundle / "terraform"
        files[tool] = b"synthetic-tool"
        value["terraform_sha256"] = d.digest(files[tool])
        value["artifacts"]["inputs_sha256"] = d.digest(files[working / "cleanup-inputs.json"])
        listing = [working / name for name in names | {"backend_override.tf", "cleanup-inputs.json", ".terraform"}]
        if mutation:
            mutation(files, value, working, listing)
        original = d.regular
        def read(path, **kwargs):
            return files[path] if path in files else original(path, **kwargs)
        def children(path):
            return iter([bundle / "guard/main.tf"] if path == bundle / "guard" else listing)
        runner = mock.Mock()
        runner.call.side_effect = [value["source_commit"].encode(), b"", {"terraform_version": "1.13.5"}]
        with mock.patch.object(d, "regular", side_effect=read), mock.patch.object(Path, "iterdir", children), mock.patch.object(Path, "exists", return_value=True):
            d.source_bundle(bundle, value, runner, tool)
        return runner

    def test_frozen_source_copies_and_module_cache(self):
        for cloud in d.GUARD:
            runner = self.bundle(cloud)
            self.assertEqual(runner.call.call_count, 3)
            self.assertIn("--quiet", runner.call.call_args_list[1].args[0])

    def test_changed_source_override_tool_or_inputs_refused(self):
        for filename in ("main.tf", "backend_override.tf", "cleanup-inputs.json", ".terraform.lock.hcl"):
            def mutation(files, value, working, listing):
                files[working / filename] += b"changed"
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.bundle(mutation=mutation)
        def tool_change(files, value, working, listing):
            value["terraform_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            self.bundle(mutation=tool_change)

    def test_extra_tf_file_and_cached_foreign_module_refused(self):
        def extra(files, value, working, listing):
            listing.append(working / "foreign.tf")
        with self.assertRaises(ValueError):
            self.bundle(mutation=extra)
        def foreign(files, value, working, listing):
            files[working / ".terraform/modules/modules.json"] = b'{"Modules":[{"Key":"guard","Source":"../guard","Dir":"/foreign"}]}'
        with self.assertRaises(ValueError):
            self.bundle(mutation=foreign)

    def test_nondefault_workspace_and_local_backend_refused(self):
        def workspace(files, value, working, listing):
            files[working / ".terraform/environment"] = b"production"
        with self.assertRaises(ValueError):
            self.bundle(mutation=workspace)
        def local(files, value, working, listing):
            files[working / ".terraform/terraform.tfstate"] = b'{"backend":{"type":"local"}}'
        with self.assertRaises(ValueError):
            self.bundle(mutation=local)

    def test_private_file_size_and_permissions(self):
        with self.assertRaises(ValueError):
            d.regular(ROOT / "request.example.json", limit=1)
        fake = mock.Mock(st_mode=d.stat.S_IFREG | 0o644, st_uid=d.os.getuid(), st_size=10)
        with mock.patch.object(d.os, "fstat", return_value=fake), self.assertRaises(ValueError):
            d.regular(ROOT / "request.example.json", private=True)


class PlanTests(unittest.TestCase):
    def test_exact_both_cloud_deletions(self):
        for cloud in d.GUARD:
            value = request(cloud)
            self.assertEqual(d.validate_plan(plan_for(value), value), 8)

    def test_bad_actions_and_resource_types(self):
        for actions in (["create"], ["update"], ["delete", "create"], ["no-op"], ["forget"]):
            value = request()
            plan = plan_for(value)
            plan["resource_changes"][0]["change"]["actions"] = actions
            with self.subTest(actions=actions), self.assertRaises(ValueError):
                d.validate_plan(plan, value)
        value = request()
        plan = plan_for(value)
        plan["resource_changes"][0]["type"] = "aws_iam_role"
        with self.assertRaises(ValueError):
            d.validate_plan(plan, value)

    def test_incomplete_drift_or_checks(self):
        for field, wrong in (("complete", False), ("errored", True), ("applyable", False), ("format_version", "1.0"),
                             ("terraform_version", "1.14.0"), ("resource_drift", [{}]), ("deferred_changes", [{}]),
                             ("checks", [{"status": "unknown"}]), ("timestamp", "2026-09-20T07:00:00Z")):
            value = request()
            plan = plan_for(value)
            plan[field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                d.validate_plan(plan, value)

    def test_import_move_deposed_duplicate_and_omission(self):
        for operation in ("import", "move", "deposed", "duplicate", "omit"):
            value = request()
            plan = plan_for(value)
            item = plan["resource_changes"][0]
            if operation == "import":
                item["change"]["importing"] = {"id": "foreign"}
            elif operation == "move":
                item["previous_address"] = "foreign.address"
            elif operation == "deposed":
                item["deposed"] = "deadbeef"
            elif operation == "duplicate":
                plan["resource_changes"].append(deepcopy(item))
            else:
                plan["resource_changes"].pop()
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                d.validate_plan(plan, value)

    def test_wrong_tags_guard_and_ids(self):
        for cloud in d.GUARD:
            value = request(cloud)
            for field in ("id", "tags", "guard"):
                plan = plan_for(value)
                item = plan["resource_changes"][-1 if field == "guard" else 0]
                before = item["change"]["before"]
                if field == "id":
                    before["id"] += "foreign"
                elif field == "tags":
                    before["tags_all" if cloud == "aws" else "tags"]["assignment"] = "foreign"
                else:
                    before["input"]["assignment"] = "foreign"
                prior = d.flatten(plan["prior_state"]["values"]["root_module"], ("module.guard",))
                prior[item["address"]]["values"] = deepcopy(before)
                with self.subTest(cloud=cloud, field=field), self.assertRaises(ValueError):
                    d.validate_plan(plan, value)

    def test_implicit_disk_mismatch_and_retained_volume(self):
        for key, wrong in (("volume_id", "vol-" + "f" * 17), ("delete_on_termination", False)):
            value = request()
            plan = plan_for(value)
            item = next(r for r in plan["resource_changes"] if r["address"] == "aws_instance.target")
            item["change"]["before"]["root_block_device"][0][key] = wrong
            prior = d.flatten(plan["prior_state"]["values"]["root_module"], ("module.guard",))
            prior[item["address"]]["values"] = deepcopy(item["change"]["before"])
            with self.assertRaises(ValueError):
                d.validate_plan(plan, value)

    def test_foreign_modules_or_remaining_managed_state(self):
        value = request()
        for where in ("prior", "remaining"):
            plan = plan_for(value)
            if where == "prior":
                plan["prior_state"]["values"]["root_module"]["child_modules"][0]["address"] = "module.foreign"
            else:
                plan["planned_values"] = {"root_module": {"resources": [{"address": "aws_vpc.target", "mode": "managed"}]}}
            with self.assertRaises(ValueError):
                d.validate_plan(plan, value)

    def test_state_hash_lineage_serial_and_deposed(self):
        value = request()
        state = state_for(value)
        self.assertEqual(d.state_status(state, value), "populated")
        for field, wrong in (("lineage", UUIDS[0]), ("serial", 2), ("version", 3), ("resources", [{"mode": "managed", "instances": [{"deposed": "x"}]}])):
            changed = deepcopy(state)
            changed[field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                d.state_status(changed, value)
        state.update(serial=2, resources=[])
        self.assertEqual(d.state_status(state, value), "empty")


class ExecutionTests(unittest.TestCase):
    def execute(self, value=None, read=None, verify=None, runner=None, clock=None):
        value = value or request()
        runner = runner or FakeRunner(value)
        result = d.execute(runner, value, Path("/reviewed/terraform"), ROOT / "never-created.tfplan",
                           read=read or (lambda *a, **kw: b"synthetic-plan"), clock=clock or (lambda: NOW),
                           verify=verify or mock.Mock())
        return result, runner

    def test_saved_plan_order_no_auto_approve_or_direct_delete(self):
        value = request()
        verifier = mock.Mock()
        result, runner = self.execute(value, verify=verifier)
        self.assertEqual([args[1] for args, _ in runner.calls], ["state", "plan", "show", "state", "apply", "state"])
        self.assertIn("-destroy", runner.calls[1][0])
        self.assertIn("-lock-timeout=30s", runner.calls[4][0])
        self.assertEqual(runner.calls[4][0][-1], str(ROOT / "never-created.tfplan"))
        self.assertEqual(runner.calls[4][1]["timeout"], 1200)
        self.assertNotIn("-auto-approve", repr(runner.calls))
        self.assertEqual(verifier.call_count, 3)
        self.assertTrue(verifier.call_args.kwargs["absent"])
        self.assertEqual(result["cloud_deletions"], 8)
        self.assertFalse(result["workload_cleanup_ready"])

    def test_plan_tampering_never_applies(self):
        value = request()
        runner = FakeRunner(value)
        with self.assertRaises(ValueError):
            self.execute(value, runner=runner, read=mock.Mock(side_effect=[b"original", b"changed"]))
        self.assertNotIn("apply", [args[1] for args, _ in runner.calls])

    def test_external_existing_plan_refused(self):
        value = request()
        runner = FakeRunner(value)
        with mock.patch.object(Path, "exists", return_value=True), self.assertRaises(ValueError):
            self.execute(value, runner=runner)
        self.assertEqual([args[1] for args, _ in runner.calls], ["state"])

    def test_inventory_failures_before_and_after_are_not_success(self):
        for responses in ([ValueError("fixture")], [None, ValueError("fixture")], [None, None, ValueError("fixture")]):
            with self.subTest(stage=len(responses)), self.assertRaises(ValueError):
                self.execute(verify=mock.Mock(side_effect=responses))

    def test_authority_rechecked_before_apply(self):
        value = request()
        runner = FakeRunner(value)
        clock = mock.Mock(side_effect=[NOW, datetime(2026, 9, 20, 8, 55, tzinfo=timezone.utc)])
        with self.assertRaises(ValueError):
            self.execute(value, runner=runner, clock=clock)
        self.assertNotIn("apply", [args[1] for args, _ in runner.calls])

    def test_empty_retry_needs_actual_absence_without_new_plan(self):
        value = request()
        runner = FakeRunner(value)
        runner.state.update(serial=2, resources=[])
        verifier = mock.Mock()
        result, runner = self.execute(value, runner=runner, verify=verifier)
        self.assertEqual(result["status"], "already_absent")
        self.assertEqual(result["cloud_deletions"], 0)
        self.assertEqual([args[1] for args, _ in runner.calls], ["state"])
        self.assertTrue(verifier.call_args.kwargs["absent"])

    def test_failed_cloud_does_not_skip_other_request(self):
        operation = mock.Mock(side_effect=[ValueError("SENSITIVE FIXTURE MUST NOT ESCAPE"), {"status": "unarmed"}])
        results = d.run_many([Path("aws.json"), Path("azure.json")], None, operation)
        self.assertEqual(operation.call_count, 2)
        self.assertEqual([result["status"] for result in results], ["failed", "unarmed"])
        self.assertNotIn("SENSITIVE", json.dumps(results))

    def test_identity_wrong_principal_and_root(self):
        value = request()
        runner = mock.Mock()
        runner.az.return_value = {"id": UUIDS[0], "tenantId": UUIDS[1], "user": {"type": "user", "name": "fixture"}}
        with self.assertRaises(ValueError):
            d.identity(runner, value)
        self.assertFalse(runner.aws.called)
        claims = {"oid": UUIDS[3], "tid": UUIDS[1], "appid": UUIDS[2], "aud": "https://management.azure.com/", "exp": 9999999999}
        token = "header." + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=") + ".signature"
        runner.az.side_effect = [{"id": UUIDS[0], "tenantId": UUIDS[1], "user": {"type": "servicePrincipal", "name": UUIDS[2]}},
                                 {"accessToken": token}]
        runner.aws.return_value = {"Account": "000000000001", "Arn": "arn:aws:iam::000000000001:root"}
        with self.assertRaises(ValueError):
            d.identity(runner, value)

    def test_no_deployment_or_secret_handoff_in_entrypoint(self):
        source = (ROOT / "destroy.py").read_text()
        for forbidden in ("-auto-approve", "force-unlock", "config.sh", "controller.pat", "assume-role-with-web-identity",
                          '"init"', '"import"', '"destroy"', '"login"', "shell=True"):
            self.assertNotIn(forbidden, source)
        self.assertIn('"AWS_SHARED_CREDENTIALS_FILE": "/dev/null"', source)
        self.assertIn('"TF_CLI_CONFIG_FILE": "/dev/null"', source)
        self.assertIn("DeadlineRunner(environment", source)

    def test_command_deadline_keeps_grace_period(self):
        value = request()
        value["approval"]["execute_before"] = "2026-09-20T08:02:00Z"
        with mock.patch.object(d, "datetime") as clock, mock.patch.object(d.core.Runner, "call", return_value={}) as call:
            clock.now.return_value = NOW
            d.DeadlineRunner({}, ROOT, value).call(["fixture"], timeout=180)
            self.assertEqual(call.call_args.kwargs["timeout"], 85)
            clock.now.return_value = datetime(2026, 9, 20, 8, 2, tzinfo=timezone.utc)
            with self.assertRaises(ValueError):
                d.DeadlineRunner({}, ROOT, value).call(["fixture"])
            self.assertEqual(call.call_count, 1)

    def test_only_known_skipped_creation_checks_accepted(self):
        check = {"address": {"kind": "resource", "to_display": d.GUARD["aws"]}, "status": "unknown"}
        d.validate_checks([check], "aws", {d.GUARD["aws"]})
        for field, wrong in (("status", "fail"), ("status", "error")):
            changed = deepcopy(check)
            changed[field] = wrong
            with self.assertRaises(ValueError):
                d.validate_checks([changed], "aws", {d.GUARD["aws"]})
        check["address"]["to_display"] = "module.foreign.terraform_data.authorization"
        with self.assertRaises(ValueError):
            d.validate_checks([check], "aws", {d.GUARD["aws"]})


if __name__ == "__main__":
    unittest.main()
