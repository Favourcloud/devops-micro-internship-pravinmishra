"""Synthetic structural-review fixtures, not deployment or independent-recovery evidence."""
import ast
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import re
import stat
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("recovery_review", ROOT / "recovery/review.py")
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


def fixture(cloud="aws"):
    addresses = sorted(reviewer.AWS if cloud == "aws" else reviewer.AZURE)
    request = {
        "schema_version": 1, "execution_authorized": False, "cloud": cloud,
        "lease_id": "abcdef123456", "source_commit": "a" * 40,
        "approved_at": "2026-09-18T21:32:11Z", "expires_at": "2026-09-19T18:18:03Z",
        "saved_plan_sha256": "b" * 64, "plan_json_sha256": "c" * 64,
        "external_custody": {
            "storage_account_resource_id": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/fixture-external-recovery/providers/Microsoft.Storage/storageAccounts/fixturerecovery",
            "state_blob_version": "fixture-version-1", "state_sha256": "d" * 64,
            "restore_receipt_sha256": "e" * 64,
        },
        "resources": [{"address": address, "id": "synthetic-id-" + str(index)}
                      for index, address in enumerate(addresses)],
    }
    prior, changes = [], []
    for item in request["resources"] + [{"address": reviewer.GUARD, "id": "synthetic-guard"}]:
        before = {"id": item["id"]}
        if item["address"] == reviewer.GUARD:
            before["input"] = request["lease_id"]
        common = {"address": item["address"], "mode": "managed", "type": item["address"].split(".")[0]}
        prior.append(dict(common, values=copy.deepcopy(before)))
        changes.append(dict(common, change={"actions": ["delete"], "before": before, "after": None, "after_unknown": {}}))
    plan = {"format_version": "1.2", "terraform_version": "1.13.5", "complete": True,
            "errored": False, "applyable": True, "timestamp": "2026-09-19T00:30:00Z",
            "prior_state": {"values": {"root_module": {"resources": prior}}},
            "planned_values": {"root_module": {}}, "resource_changes": changes,
            "checks": [{"status": "pass"}]}
    return request, plan


def run(request, plan):
    return reviewer.review(request, plan, "b" * 64, "c" * 64)


class RecoveryTests(unittest.TestCase):
    def test_both_clouds_structural_only_and_partial_bootstrap(self):
        for cloud, count in (("aws", 3), ("azure", 15)):
            with self.subTest(cloud=cloud):
                request, plan = fixture(cloud)
                result = run(request, plan)
                self.assertEqual(result["cloud_deletions_in_supplied_plan"], count)
                self.assertTrue(result["structural_review_passed"])
                self.assertFalse(result["execution_authorized"])
                self.assertFalse(result["live_readiness_verified"])
                self.assertNotIn("synthetic-id", json.dumps(result))
                request["resources"] = request["resources"][:1]
                plan["prior_state"]["values"]["root_module"]["resources"] = plan["prior_state"]["values"]["root_module"]["resources"][:1] + plan["prior_state"]["values"]["root_module"]["resources"][-1:]
                plan["resource_changes"] = plan["resource_changes"][:1] + plan["resource_changes"][-1:]
                self.assertEqual(run(request, plan)["cloud_deletions_in_supplied_plan"], 1)

    def test_metadata_and_example_fail_closed(self):
        example = json.loads((ROOT / "recovery/request.example.json").read_text())
        self.assertFalse(example["execution_authorized"])
        with self.assertRaises(ValueError):
            reviewer.metadata(example)
        for key, value in (("execution_authorized", True), ("schema_version", True), ("cloud", "other"),
                           ("lease_id", "retired"), ("source_commit", "main"), ("expires_at", "2026-09-21T00:00:00Z"),
                           ("approved_at", "2026-09-19T18:18:03Z"), ("saved_plan_sha256", None),
                           ("resources", []), ("password", "must-not-appear")):
            with self.subTest(key=key):
                request, plan = fixture()
                request[key] = value
                with self.assertRaises(ValueError):
                    run(request, plan)

    def test_external_state_custody_and_protected_resources(self):
        for value in (None, {}, {"storage_account_resource_id": "bad"}):
            request, plan = fixture()
            request["external_custody"] = value
            with self.assertRaises(ValueError):
                run(request, plan)
        for suffix in ("control-rg", "canary-rg"):
            request, plan = fixture()
            request["external_custody"]["storage_account_resource_id"] = request["external_custody"]["storage_account_resource_id"].replace("fixture-external-recovery", "DMI-W10-CLEANUP-ABCDEF123456-" + suffix)
            with self.assertRaisesRegex(ValueError, "circular_custody"):
                run(request, plan)
        request, plan = fixture("azure")
        request["resources"][0]["id"] = request["external_custody"]["storage_account_resource_id"]
        with self.assertRaisesRegex(ValueError, "recovery_store_in_scope"):
            run(request, plan)
        for address in ("aws_iam_user.operator", "aws_iam_policy.operator", "aws_iam_policy.runtime_boundary", "aws_vpc.canary", "azurerm_resource_group.canary", "module.foreign.aws_iam_role.cleanup"):
            request, plan = fixture()
            request["resources"][0]["address"] = address
            with self.assertRaises(ValueError):
                run(request, plan)

    def test_artifacts_versions_and_window(self):
        request, plan = fixture()
        for saved_hash, json_hash in (("f" * 64, "c" * 64), ("b" * 64, "f" * 64)):
            with self.assertRaisesRegex(ValueError, "artifact_mismatch"):
                reviewer.review(request, plan, saved_hash, json_hash)
        cases = (("format_version", "2.0"), ("terraform_version", "1.14.0"), ("complete", False),
                 ("errored", True), ("applyable", False), ("deferred_changes", [{}]), ("resource_drift", [{}]),
                 ("checks", [{"status": "unknown"}]), ("checks", [{"status": "fail"}]),
                 ("timestamp", "2026-09-19T18:18:03Z"), ("timestamp", "2026-09-18T21:32:10Z"))
        for key, value in cases:
            with self.subTest(key=key, value=value):
                bad = copy.deepcopy(plan)
                bad[key] = value
                with self.assertRaises(ValueError):
                    run(request, bad)

    def test_no_create_update_noop_replace_import_move_deposed_or_unknown(self):
        for actions in (["create"], ["update"], ["no-op"], ["delete", "create"], ["create", "delete"]):
            request, plan = fixture()
            plan["resource_changes"][0]["change"]["actions"] = actions
            with self.assertRaises(ValueError):
                run(request, plan)
        for key, value in (("previous_address", "old.address"), ("deposed", "00000001"), ("module_address", "module.other")):
            request, plan = fixture()
            plan["resource_changes"][0][key] = value
            with self.assertRaises(ValueError):
                run(request, plan)
        for key, value in (("importing", {"id": "foreign"}), ("after", {}), ("after_unknown", {"id": True})):
            request, plan = fixture()
            plan["resource_changes"][0]["change"][key] = value
            with self.assertRaises(ValueError):
                run(request, plan)

    def test_identity_lease_inventory_completeness_and_duplicates(self):
        for change in ("prior-id", "change-id", "prior-lease", "change-lease", "missing-guard-id", "duplicate-guard-id", "missing-prior", "missing-change", "duplicate-prior", "duplicate-change", "duplicate-inventory"):
            request, plan = fixture()
            prior = plan["prior_state"]["values"]["root_module"]["resources"]
            changes = plan["resource_changes"]
            if change == "prior-id": prior[0]["values"]["id"] = "foreign"
            elif change == "change-id": changes[0]["change"]["before"]["id"] = "foreign"
            elif change == "prior-lease": prior[-1]["values"]["input"] = "0" * 12
            elif change == "change-lease": changes[-1]["change"]["before"]["input"] = "0" * 12
            elif change == "missing-guard-id":
                del prior[-1]["values"]["id"]
                del changes[-1]["change"]["before"]["id"]
            elif change == "duplicate-guard-id":
                prior[-1]["values"]["id"] = prior[0]["values"]["id"]
                changes[-1]["change"]["before"]["id"] = prior[0]["values"]["id"]
            elif change == "missing-prior": prior.pop(0)
            elif change == "missing-change": changes.pop(0)
            elif change == "duplicate-prior": prior.append(copy.deepcopy(prior[0]))
            elif change == "duplicate-change": changes.append(copy.deepcopy(changes[0]))
            elif change == "duplicate-inventory": request["resources"][1] = copy.deepcopy(request["resources"][0])
            with self.subTest(change=change), self.assertRaises(ValueError):
                run(request, plan)

    def test_modules_remaining_resources_and_data_scope(self):
        for section in ("prior", "planned"):
            request, plan = fixture()
            root = plan["prior_state"]["values"]["root_module"] if section == "prior" else plan["planned_values"]["root_module"]
            root["child_modules"] = [{}]
            with self.assertRaises(ValueError): run(request, plan)
        request, plan = fixture()
        plan["planned_values"]["root_module"]["resources"] = [{"address": "aws_iam_role.cleanup", "mode": "managed"}]
        with self.assertRaises(ValueError): run(request, plan)
        for cloud, address in (("aws", "data.aws_caller_identity.current"), ("azure", "data.azurerm_client_config.current")):
            request, plan = fixture(cloud)
            data = {"mode": "data", "address": address}
            plan["prior_state"]["values"]["root_module"]["resources"].append(data)
            plan["resource_changes"].append(dict(data, change={"actions": ["read"]}))
            run(request, plan)
            plan["resource_changes"][-1]["address"] = "data.other.secret"
            with self.assertRaises(ValueError): run(request, plan)

    def test_strict_json_bounded_regular_reads_and_no_writer_imports(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError): reviewer.strict_json(raw)
        path = ROOT / "recovery/request.example.json"
        self.assertEqual(reviewer.read_regular(path, 65536), path.read_bytes())
        with self.assertRaises(ValueError): reviewer.read_regular(path, 2)
        with self.assertRaises(ValueError): reviewer.read_regular(path.parent, 65536)
        with patch.object(reviewer.os, "open", return_value=42), patch.object(reviewer.os, "fstat") as info, patch.object(reviewer.os, "close") as close:
            info.return_value.st_mode = stat.S_IFIFO
            info.return_value.st_size = 0
            with self.assertRaises(ValueError): reviewer.read_regular(Path("synthetic-fifo"), 10)
            close.assert_called_once_with(42)
        tree = ast.parse((ROOT / "recovery/review.py").read_text())
        imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
        self.assertFalse(imports & {"subprocess", "socket", "urllib", "requests", "boto3"})
        self.assertIn("os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK", (ROOT / "recovery/review.py").read_text())

    def test_cli_redacts_failures_and_only_emits_structural_summary(self):
        request, plan = fixture()
        saved = b"synthetic fixture, not a native Terraform plan"
        plan_raw = json.dumps(plan).encode()
        request["saved_plan_sha256"] = reviewer.digest(saved)
        request["plan_json_sha256"] = reviewer.digest(plan_raw)
        argv = ["review", "--request", "private-request", "--plan-json", "private-json", "--saved-plan", "private-plan"]
        output = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(reviewer, "read_regular", side_effect=[json.dumps(request).encode(), plan_raw, saved]), contextlib.redirect_stdout(output):
            reviewer.main()
        self.assertFalse(json.loads(output.getvalue())["execution_authorized"])
        error = io.StringIO()
        with patch.object(sys, "argv", argv), patch.object(reviewer, "read_regular", side_effect=OSError("sensitive-value-must-not-appear")), contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as caught:
            reviewer.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertNotIn("sensitive-value", error.getvalue())
        self.assertNotIn("private-request", error.getvalue())

    def test_allowlists_match_only_bootstrap_source(self):
        for cloud, addresses in (("aws", reviewer.AWS), ("azure", reviewer.AZURE)):
            text = (ROOT / "bootstrap" / cloud / "main.tf").read_text()
            declared = {kind + "." + name for kind, name in re.findall(r'^resource "([^"]+)" "([^"]+)"', text, re.M)}
            self.assertEqual(declared, {address.split("[")[0] for address in addresses} | {reviewer.GUARD})


if __name__ == "__main__":
    unittest.main()
