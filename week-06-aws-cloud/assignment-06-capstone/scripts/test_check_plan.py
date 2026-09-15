import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_plan import AWS_PROVIDER, CONSTRAINTS, GATE, VPC, validate_plan

ACCOUNT = "000000000000"
ELB = f"arn:aws:elasticloadbalancing:eu-north-1:{ACCOUNT}:"
DB = f"arn:aws:rds:eu-north-1:{ACCOUNT}:db:"


def plan_fixture(mode="create"):
    changes = []
    for address, fields in CONSTRAINTS.items():
        values = copy.deepcopy(fields)
        if address == GATE:
            values["input"] = {"account_id": ACCOUNT, "vpc_id": VPC}
        if address == "aws_db_instance.replica":
            values.update(arn=DB + "dmi-a6-read-replica", replicate_source_db=DB + "bookreview-db")
        if address == "aws_lb.public":
            values["arn"] = ELB + "loadbalancer/app/dmi-a6-public-alb/synthetic"
        if address == "aws_lb_listener.http":
            values.update(arn=ELB + "listener/app/dmi-a6-public-alb/synthetic/listener",
                          load_balancer_arn=ELB + "loadbalancer/app/dmi-a6-public-alb/synthetic")
        if address == "aws_lb_target_group.web":
            values["arn"] = ELB + "targetgroup/dmi-a6-web/synthetic"
        if address == "aws_lb_target_group_attachment.web":
            values["target_group_arn"] = ELB + "targetgroup/dmi-a6-web/synthetic"
        changes.append({"address": address, "mode": "managed",
                        "provider_name": "terraform.io/builtin/terraform" if address == GATE else AWS_PROVIDER,
                        "change": {"actions": ["create" if mode == "create" else "delete"],
                                   "before": values if mode == "cleanup" else None,
                                   "after": values if mode == "create" else None}})
    return {"format_version": "1.2", "complete": True, "errored": False,
            "variables": {"expected_account_id": {"value": ACCOUNT},
                          "deployment_approved": {"value": True}, "runtime_verified": {"value": True}},
            "checks": [{"status": "pass", "address": {"to_display": GATE}}],
            "resource_changes": changes}


class PlanBoundaryTests(unittest.TestCase):
    def test_expected_creation(self):
        self.assertEqual(validate_plan(plan_fixture(), "create"), 5)

    def test_full_cleanup(self):
        self.assertEqual(validate_plan(plan_fixture("cleanup"), "cleanup"), 5)

    def test_partial_and_empty_cleanup(self):
        for size in (0, 1, 3):
            with self.subTest(size=size):
                plan = plan_fixture("cleanup")
                plan["resource_changes"] = plan["resource_changes"][:size]
                self.assertEqual(validate_plan(plan, "cleanup"), size)

    def test_idempotent_creation(self):
        plan = plan_fixture()
        for resource in plan["resource_changes"]:
            resource["change"]["actions"] = ["no-op"]
        self.assertEqual(validate_plan(plan, "create"), 0)

    def test_reject_shared_resources_even_noop(self):
        for address in ("aws_db_instance.primary", "aws_db_instance.ha_mysql", "aws_vpc.existing"):
            with self.subTest(address=address):
                plan = plan_fixture()
                resource = copy.deepcopy(plan["resource_changes"][0])
                resource.update(address=address)
                resource["change"]["actions"] = ["no-op"]
                plan["resource_changes"].append(resource)
                with self.assertRaises(ValueError):
                    validate_plan(plan, "create")

    def test_reject_updates_replacements_deletions_and_imports(self):
        for mode, actions in (("create", ["update"]), ("create", ["delete", "create"]),
                              ("create", ["delete"]), ("cleanup", ["create"])):
            with self.subTest(mode=mode, actions=actions):
                plan = plan_fixture(mode)
                plan["resource_changes"][0]["change"]["actions"] = actions
                with self.assertRaises(ValueError):
                    validate_plan(plan, mode)
        for location, key, value in (("change", "importing", {"id": "existing"}),
                                     ("resource", "previous_address", "aws_lb.old")):
            plan = plan_fixture()
            resource = plan["resource_changes"][0]
            (resource["change"] if location == "change" else resource)[key] = value
            with self.assertRaises(ValueError):
                validate_plan(plan, "create")

    def test_reject_unknown_or_mutated_critical_values(self):
        for address, fields in CONSTRAINTS.items():
            for field in fields:
                with self.subTest(address=address, field=field):
                    plan = plan_fixture()
                    resource = next(item for item in plan["resource_changes"] if item["address"] == address)
                    resource["change"]["after"][field] = None
                    with self.assertRaises(ValueError):
                        validate_plan(plan, "create")

    def test_reject_wrong_replica_source_and_cleanup_arns(self):
        for mode in ("create", "cleanup"):
            plan = plan_fixture(mode)
            replica = next(item for item in plan["resource_changes"] if item["address"] == "aws_db_instance.replica")
            replica["change"]["after" if mode == "create" else "before"]["replicate_source_db"] = DB + "ha-mysql-db"
            with self.assertRaises(ValueError):
                validate_plan(plan, mode)
        for index in range(5):
            plan = plan_fixture("cleanup")
            values = plan["resource_changes"][index]["change"]["before"]
            for field in ("arn", "load_balancer_arn", "target_group_arn"):
                if field in values:
                    values[field] = "arn:aws:unrelated"
            with self.assertRaises(ValueError):
                validate_plan(plan, "cleanup")

    def test_reject_missing_resources_duplicates_and_wrong_provider(self):
        for mutation in ("missing", "duplicate", "provider"):
            plan = plan_fixture()
            if mutation == "missing":
                plan["resource_changes"].pop()
            elif mutation == "duplicate":
                plan["resource_changes"].append(copy.deepcopy(plan["resource_changes"][0]))
            else:
                plan["resource_changes"][0]["provider_name"] = "unexpected/provider"
            with self.assertRaises(ValueError):
                validate_plan(plan, "create")

    def test_reject_failed_incomplete_deferred_or_unsupported_plans(self):
        for field, value in (("complete", False), ("errored", True), ("deferred_changes", [{}]),
                              ("format_version", "2.0"), ("checks", [])):
            plan = plan_fixture()
            plan[field] = value
            with self.assertRaises(ValueError):
                validate_plan(plan, "create")
        for status in ("fail", "unknown"):
            plan = plan_fixture()
            plan["checks"][0]["status"] = status
            with self.assertRaises(ValueError):
                validate_plan(plan, "create")

    def test_reject_missing_approval_and_account(self):
        for name in ("deployment_approved", "runtime_verified", "expected_account_id"):
            plan = plan_fixture()
            plan["variables"].pop(name)
            with self.assertRaises(ValueError):
                validate_plan(plan, "create")

    def test_data_sources_read_only(self):
        plan = plan_fixture()
        plan["resource_changes"].append({"address": "data.aws_vpc.existing", "mode": "data",
                                         "change": {"actions": ["read"]}})
        self.assertEqual(validate_plan(plan, "create"), 5)
        plan["resource_changes"][-1]["change"]["actions"] = ["delete"]
        with self.assertRaises(ValueError):
            validate_plan(plan, "create")

    def test_cli_succeeds_and_fails_without_printing_private_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.tfplan.json"
            path.write_text(json.dumps(plan_fixture()))
            command = [sys.executable, str(Path(__file__).with_name("check_plan.py")), str(path), "--mode", "create"]
            accepted = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            for content in ('{"secret": "DO_NOT_ECHO"}', 'DO_NOT_ECHO', '{"complete": true, "variables": []}'):
                path.write_text(content)
                rejected = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertNotIn("DO_NOT_ECHO", rejected.stdout + rejected.stderr)


if __name__ == "__main__":
    unittest.main()
