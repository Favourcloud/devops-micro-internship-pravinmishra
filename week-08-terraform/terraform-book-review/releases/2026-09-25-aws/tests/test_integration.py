"""Configuration-boundary checks only; no runtime service, network or database."""
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("a5_integrated_config", ROOT / "runtime/common.py")
common = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = common
sys.path.insert(0, str(ROOT / "runtime"))
try:
    spec.loader.exec_module(common)
finally:
    sys.path.pop(0)


class TerraformRuntimeIntegration(unittest.TestCase):
    def config(self, tier):
        source = (ROOT / "terraform/main.tf").read_text()
        body = source.split("  common_config = {", 1)[1].split("\n  }", 1)[0]
        keys = set(re.findall(r"(?m)^    ([a-z_][a-z_0-9]*)\s*=", body))
        values = {
            "region": "eu-west-1", "public_origin": "https://books.example.invalid",
            "internal_url": "http://internal.example.invalid", "db_host": "primary.example.invalid",
            "replica_host": "replica.example.invalid", "db_name": "book_review_db",
            "release_authorized": False,
        }
        self.assertEqual(keys, set(values), "Terraform common configuration drifted from this boundary fixture")
        body = source.split(tier + " = merge(local.common_config, {", 1)[1].split("\n    })", 1)[0]
        extra_keys = set(re.findall(r"(?m)^      ([a-z_][a-z_0-9]*)\s*=", body))
        extras = {"tier": tier}
        if tier != "initializer":
            extras.update(runtime_artifact_url="https://artifacts.example.invalid/build.tar.gz",
                          runtime_artifact_sha256="1" * 64)
        if tier != "web":
            extras.update(rds_ca_path="/etc/book-review/rds-ca.pem", rds_ca_sha256="0" * 64,
                          app_secret_arn="arn:aws:secretsmanager:eu-west-1:000000000000:secret:app-MOCK00",
                          app_secret_version="0" * 32)
        if tier == "app":
            extras["router_secret_arn"] = "arn:aws:secretsmanager:eu-west-1:000000000000:secret:router-MOCK00"
        if tier == "initializer":
            extras.update(master_secret_arn="arn:aws:secretsmanager:eu-west-1:000000000000:secret:master-MOCK00",
                          master_secret_version="1" * 32)
        self.assertEqual(extra_keys, set(extras), "Terraform tier fields drifted from this boundary fixture")
        return {**values, **extras}

    def test_all_terraform_tier_keys_are_accepted_by_runtime(self):
        for tier in ("web", "app", "initializer"):
            with self.subTest(tier=tier):
                config = self.config(tier)
                self.assertEqual(common.validate_config(config), config)

    def test_false_release_refuses_before_any_secret_command(self):
        calls = []
        def forbidden(*args, **kwargs):
            calls.append(args)
            raise AssertionError("No cloud command may run in this test")
        with self.assertRaises(common.RuntimeFailure):
            common.fetch_secret(self.config("app"), "app", runner=forbidden)
        self.assertEqual(calls, [])

    def test_deployment_uses_canonical_sealed_source_lock(self):
        source = (ROOT / "terraform/main.tf").read_text()
        self.assertIn('filename == "source-lock.json" ? file("${path.module}/../source-lock.json")', source)
        duplicate = ROOT / "runtime/source-lock.json"
        if duplicate.exists():
            self.assertEqual(json.loads(duplicate.read_text()), json.loads((ROOT / "source-lock.json").read_text()))

    def test_per_tier_payloads_exclude_repository_only_files(self):
        manifest = json.loads((ROOT / "runtime/deploy-manifest.json").read_text())
        excluded = set(manifest["repository_only"])
        for tier in ("web", "app", "initializer"):
            selected = manifest["common"] + manifest["tiers"][tier]
            self.assertEqual(len(selected), len(set(selected)))
            self.assertFalse(set(selected) & excluded)
            self.assertIn("bootstrap.sh", selected)
            self.assertIn("source-lock.json", selected)
            for name in selected:
                path = ROOT / (name if name == "source-lock.json" else "runtime/" + name)
                self.assertTrue(path.is_file() and not path.is_symlink())
                self.assertNotIn(path.suffix, {".js", ".jsx", ".ts", ".tsx"})


if __name__ == "__main__":
    unittest.main()
