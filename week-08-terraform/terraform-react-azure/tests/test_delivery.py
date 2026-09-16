import base64
import json
from pathlib import Path
import re
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT.parent / "assignment-03-deploy-a-react-application-on-azure-virtual-machine-using-terraform.md"
MAIN = (ROOT / "main.tf").read_text()
BOOTSTRAP = (ROOT / "cloud-init.sh").read_text()


def public_files():
    return [p for p in ROOT.rglob("*") if p.is_file() and not any(
        part in {".private", ".terraform", "__pycache__"} for part in p.relative_to(ROOT).parts
    )]


class DeliveryTests(unittest.TestCase):
    def test_eight_required_resources_only(self):
        resources = re.findall(r'^resource "([^"]+)" "([^"]+)"', MAIN, re.M)
        self.assertEqual({kind for kind, name in resources}, {
            "azurerm_resource_group", "azurerm_virtual_network", "azurerm_subnet",
            "azurerm_network_security_group", "azurerm_public_ip", "azurerm_network_interface",
            "azurerm_network_interface_security_group_association", "azurerm_linux_virtual_machine",
        })
        self.assertEqual(len(resources), 8)
        self.assertTrue(all(name == "app" for _, name in resources))
        self.assertNotRegex(MAIN, r'\b(data|module|provisioner)\s+"')

    def test_provider_registration_and_disk_deletion(self):
        self.assertIn('resource_provider_registrations = "none"', MAIN)
        self.assertIn('delete_os_disk_on_deletion = true', MAIN)
        self.assertIn('required_version = "~> 1.13.5"', MAIN)
        self.assertIn('version = "= 4.47.0"', MAIN)

    def test_local_backend(self):
        self.assertIn('backend "local"', MAIN)
        self.assertIn('path = ".private/terraform.tfstate"', MAIN)
        self.assertNotIn('backend "azurerm"', MAIN)

    def test_nsg_association_precedes_vm(self):
        self.assertIn('depends_on = [azurerm_network_interface_security_group_association.app]', MAIN)

    def test_exact_custom_data_and_no_provisioners(self):
        self.assertIn('base64encode(file("${path.module}/cloud-init.sh"))', MAIN)
        self.assertLess(len(BOOTSTRAP.encode()), 65535)
        self.assertNotIn('local-exec', MAIN)
        self.assertNotIn('remote-exec', MAIN)

    def test_no_implicit_live_inputs(self):
        text = (ROOT / "variables.tf").read_text()
        for name in ("location", "vm_size", "controller_ipv4_cidr", "admin_ssh_public_key"):
            block = text.split(f'variable "{name}" {{', 1)[1].split('validation {', 1)[0]
            self.assertNotRegex(block, r'\bdefault\s*=')
            self.assertIn('nullable    = false', block)
        example = (ROOT / "terraform.tfvars.example").read_text()
        self.assertEqual(example.count('= "REPLACE_'), 4)

    def test_public_only_rfc_fixture(self):
        tests = (ROOT / "tests/app.tftest.hcl").read_text()
        blob = base64.b64decode(re.search(r'ssh-ed25519 ([A-Za-z0-9+/]+)', tests).group(1), validate=True)
        self.assertEqual(blob[:19], struct.pack('>I', 11) + b'ssh-ed25519' + struct.pack('>I', 32))
        self.assertEqual(blob[19:].hex(), 'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a')

    def test_rubric_lines_preserved_in_order(self):
        expected = json.loads((ROOT / 'tests/rubric.json').read_text())['ordered_required_lines']
        actual = BRIEF.read_text().replace('- [x]', '- [ ]').replace('- [X]', '- [ ]').splitlines()
        index = 0
        for line in expected:
            while index < len(actual) and actual[index] != line:
                index += 1
            self.assertLess(index, len(actual), f'Missing/reordered rubric line: {line}')
            index += 1

    def test_all_fifteen_slots_pending(self):
        data = json.loads((ROOT / 'evidence/manifest.json').read_text())
        self.assertFalse(data['assignment_complete'])
        self.assertFalse(data['cloud_authorized'])
        self.assertFalse(data['cloud_deployment_verified'])
        self.assertIsNone(data['public_ip_address'])
        self.assertEqual([s['number'] for s in data['screenshots']], list(range(1, 16)))
        headings = re.findall(r'^### Screenshot .+$', BRIEF.read_text(), re.M)
        self.assertEqual([s['rubric_heading'] for s in data['screenshots']], headings)
        self.assertEqual([s['task'] for s in data['screenshots']], [0]*3 + [1]*4 + [2] + [3]*3 + [4]*2 + [5, 6])
        for slot in data['screenshots']:
            self.assertEqual(slot['status'], 'pending')
            self.assertIsNone(slot['file'])
        self.assertEqual(BRIEF.read_text().count('Add your screenshot here.'), 15)
        self.assertNotRegex(BRIEF.read_text(), r'!\[[^\]]*\]\(')

    def test_known_identity_and_pending_ip(self):
        brief = BRIEF.read_text()
        self.assertIn('Eze Favour', brief)
        self.assertIn('Favourcloud/devops-micro-internship-pravinmishra', brief)
        self.assertIn('**VM Public IP Address:** Pending', brief)

    def test_public_files_do_not_include_private_material(self):
        patterns = [r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----', r'AKIA[0-9A-Z]{16}',
                    '/' + r'Users/[^/\s]+/', r'(?i)window[_ -]?id\s*[:=]\s*\d+']
        for path in public_files():
            self.assertFalse(path.is_symlink())
            self.assertNotIn(path.suffix, {'.js', '.jsx', '.pem', '.key', '.tfstate', '.tfplan'})
            text = path.read_text()
            for pattern in patterns:
                self.assertNotRegex(text, pattern, str(path.relative_to(ROOT)))
            for account in re.findall(r'/subscriptions/([0-9a-f-]{36})', text):
                self.assertEqual(account, '00000000-0000-0000-0000-000000000000')

    def test_private_outputs_ignored(self):
        paths = ['.private/state', 'terraform.tfstate', 'backup.tfstate.backup', 'run.tfplan',
                 'real.tfvars', 'real.tfvars.json', 'override.tf', 'test_override.tf.json',
                 'secret.pem', 'key.key', 'id_ed25519', 'id_ed25519.pub', '.terraform/data',
                 'evidence/raw/screenshot.png', 'node_modules/a', 'build/index.html', 'debug.log']
        result = subprocess.run(['git', 'check-ignore', '--no-index', *paths], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_relative_links_resolve(self):
        for file in [BRIEF, ROOT / 'README.md']:
            for link in re.findall(r'\]\(([^)]+)\)', file.read_text()):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((file.parent / link.split('#')[0]).exists(), link)

    def test_pinned_dependency_provenance(self):
        data = json.loads((ROOT / 'evidence/manifest.json').read_text())
        self.assertIn(data['upstream']['commit'], BOOTSTRAP)
        self.assertIn(data['upstream']['lock_sha256'], BOOTSTRAP)
        self.assertFalse(data['upstream']['source_modified'])
        self.assertIn('readonly NODE_VERSION=22.23.2', BOOTSTRAP)
        self.assertIn('sha256sum --check --status', BOOTSTRAP)
        self.assertNotRegex(BOOTSTRAP, r'curl[^\n]*\|\s*(?:sudo\s+)?bash')
        self.assertNotIn('npm install', BOOTSTRAP)
        self.assertNotIn('ssh-keygen', BOOTSTRAP)

    def test_truthful_runbook_and_no_cloud_commands_in_runner(self):
        readme = (ROOT / 'README.md').read_text()
        for gate in ('fresh', 'budget', 'permission', 'pending', 'cloud-init status --wait', 'terraform destroy', '8 managed resources'):
            self.assertIn(gate, readme)
        runner = (ROOT / 'tests/run_offline.py').read_text()
        self.assertNotRegex(runner, r'\[terraform, "(?:plan|apply|destroy)"')
        self.assertNotRegex(runner, r'\["(?:az|aws|ssh)"')


if __name__ == '__main__':
    unittest.main()
