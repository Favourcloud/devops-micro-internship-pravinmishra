"""Small source contracts complementary to Terraform's actual mocked plans."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TF = ROOT / "terraform"


def variable_body(text, name):
    start = re.search(r'variable\s+"' + re.escape(name) + r'"\s*\{', text)
    if not start:
        raise AssertionError(f"Missing variable {name}")
    # Required declarations precede any nested validation blocks.
    return text[start.end():].split("validation", 1)[0].split("\n}", 1)[0]


class InfrastructureSourceContract(unittest.TestCase):
    def test_all_secret_input_boundaries_are_ephemeral_and_sensitive(self):
        for filename, names in {
            "variables.tf": ["db_master_password", "app_password", "jwt_secret"],
            "modules/database/main.tf": ["master_password"],
            "modules/secrets/main.tf": ["master_payload", "app_payload"],
        }.items():
            text = (TF / filename).read_text()
            for name in names:
                with self.subTest(file=filename, variable=name):
                    body = variable_body(text, name)
                    self.assertRegex(body, r"ephemeral\s*=\s*true")
                    self.assertRegex(body, r"sensitive\s*=\s*true")

    def test_secret_values_only_enter_write_only_resource_fields(self):
        text = "\n".join(path.read_text() for path in (TF / "modules").rglob("*.tf"))
        self.assertNotRegex(text, r"(?m)^\s*(password|secret_string)\s*=")
        self.assertRegex(text, r"password_wo\s*=\s*var\.master_password")
        self.assertRegex(text, r"secret_string_wo\s*=\s*var\.master_payload")
        self.assertRegex(text, r"secret_string_wo\s*=\s*var\.app_payload")
        self.assertNotRegex(text, r'resource\s+"(?:random_password|tls_private_key|aws_iam_access_key)"')

    def test_write_only_password_omits_conflicting_management_flag(self):
        database = (TF / "modules/database/main.tf").read_text()
        self.assertNotRegex(database, r"(?m)^\s*manage_master_user_password\s*=")
        self.assertIn("password_wo", database)

    def test_no_secret_values_in_user_data(self):
        text = (TF / "main.tf").read_text()
        config = text.split('module "network"', 1)[0]
        self.assertNotRegex(config, r"var\.(?:db_master_password|app_password|jwt_secret)\b")
        self.assertIn("base64gzip", config)
        self.assertIn('permissions = "0600"', re.sub(r" +", " ", config))

    def test_no_secret_values_in_outputs(self):
        outputs = (TF / "outputs.tf").read_text()
        self.assertNotRegex(outputs, r"(?:db_master_password|app_password|jwt_secret|secret_string_wo|password_wo)")

    def test_only_local_modules_and_no_provisioners_or_data_lookups(self):
        text = "\n".join(path.read_text() for path in TF.rglob("*.tf"))
        sources = re.findall(r'(?m)^\s*source\s*=\s*"([^\"]+)"', text)
        self.assertEqual(14, len(sources))
        self.assertEqual(1, sources.count("hashicorp/aws"))
        self.assertTrue(all(source.startswith("./modules/") or source == "hashicorp/aws" for source in sources))
        self.assertNotRegex(text, r'(?m)^\s*(?:provisioner|data|backend|cloud)\s*(?:"|\{)')
        self.assertNotRegex(text, r'resource\s+"aws_(?:key_pair|iam_user|iam_access_key)"')

    def test_db_routes_are_derived_from_tier_filters(self):
        text = (TF / "modules/network/main.tf").read_text()
        self.assertEqual(2, len(re.findall(r'resource\s+"aws_route"', text)))
        self.assertIn('if v.tier == "web"', text)
        self.assertIn('if v.tier == "app"', text)
        self.assertNotIn('if v.tier == "db"', text)

    def test_no_ssh_or_egress_all_rule(self):
        text = (TF / "modules/security/main.tf").read_text()
        self.assertNotRegex(text, r"(?:from_port|to_port)\s*=\s*22\b")
        self.assertNotRegex(text, r'ip_protocol\s*=\s*"-1"')
        self.assertIn('for_each = toset(["web", "app"])', re.sub(r" +", " ", text))

    def test_every_authored_tf_run_is_mock_plan_only(self):
        for file in (TF / "tests").glob("*.tftest.hcl"):
            text = file.read_text()
            self.assertIn('mock_provider "aws"', text)
            self.assertNotRegex(text, r'(?m)^provider\s+"')
            runs = len(re.findall(r'(?m)^run\s+"', text))
            plans = len(re.findall(r"(?m)^\s*command\s*=\s*plan\s*$", text))
            self.assertGreater(runs, 0)
            self.assertEqual(runs, plans)
            self.assertNotRegex(text, r"command\s*=\s*apply")

    def test_runtime_release_and_initializer_default_closed(self):
        text = (TF / "variables.tf").read_text()
        for name in ["runtime_release_authorized", "enable_database_initializer"]:
            self.assertRegex(variable_body(text, name), r"default\s*=\s*false")

    def test_no_application_javascript_vendored(self):
        files = [path for path in ROOT.rglob("*") if ".private" not in path.parts and path.is_file()]
        self.assertFalse([str(path.relative_to(ROOT)) for path in files if path.suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}])


if __name__ == "__main__":
    unittest.main()
