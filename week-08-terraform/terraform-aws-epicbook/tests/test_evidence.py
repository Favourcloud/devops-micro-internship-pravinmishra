"""Preservation, publication-boundary and local-link checks; no external requests."""
import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT.parent / 'assignment-04-deploy-epicbook-application-on-aws-using-terraform.md'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads((ROOT / 'tests/assignment-source.json').read_text())
        self.manifest = json.loads((ROOT / 'evidence/screenshot-manifest.json').read_text())

    def test_original_brief_every_line_preserved_in_order(self):
        original = '\n'.join(self.baseline['lines']) + '\n'
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), self.baseline['sha256'])
        current = iter(BRIEF.read_text().replace('- [x]', '- [ ]').splitlines())
        for required in self.baseline['lines']:
            self.assertTrue(any(line == required for line in current), 'Lost or reordered original line: ' + required)

    def test_manifest_exact_original_titles(self):
        titles = re.findall(r'^### Screenshot (\d+) — (.+)$', '\n'.join(self.baseline['lines']), re.M)
        self.assertEqual([(slot['number'], slot['title']) for slot in self.manifest['slots']], [(int(n), title) for n, title in titles])

    def test_all_35_slots_are_pending_without_files(self):
        slots = self.manifest['slots']
        self.assertEqual([slot['number'] for slot in slots], list(range(1, 36)))
        self.assertTrue(all(slot['status'] == 'pending' and slot['file'] is None for slot in slots))

    def test_only_six_local_source_checkmarks(self):
        checked = re.findall(r'^- \[x\] (.+)$', BRIEF.read_text(), re.M)
        self.assertEqual(checked, ['Created the modular Terraform project', 'Created the root `main.tf`, `variables.tf`, and `outputs.tf`', 'Created the Network module', 'Created the EC2 module', 'Created the RDS module', 'Created the EC2 `user_data.sh`'])

    def test_local_markdown_links_exist(self):
        for path in [BRIEF, ROOT / 'README.md', ROOT / 'evidence/local-validation.md']:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in target and not target.startswith('#'):
                    self.assertTrue((path.parent / unquote(target.split('#')[0])).exists(), str(path) + ': ' + target)

    def test_proposed_source_resource_counts(self):
        sources = list(ROOT.rglob('*.tf'))
        self.assertEqual(len(sources), 12)
        text = '\n'.join(path.read_text() for path in sources)
        self.assertEqual(len(re.findall(r'^resource "', text, re.M)), 25)
        self.assertEqual(len(re.findall(r'^data "', text, re.M)), 1)
        # Two count=2 blocks and one 2-element for_each add three instances.
        self.assertEqual(len(re.findall(r'^\s*count\s*=\s*2$', text, re.M)), 2)
        self.assertIn('toset(["80", "443"])', text)

    def test_no_public_raw_evidence_or_private_paths(self):
        for path in (ROOT / 'evidence').iterdir():
            self.assertIn(path.suffix, ['.md', '.json'])
            text = path.read_text()
            self.assertNotIn('/Users/', text)
            self.assertNotIn('arn:aws:', text)
            self.assertNotIn('BEGIN PRIVATE KEY', text)

    def test_runbook_explicit_gates_and_upstream_limitation(self):
        text = (ROOT / 'README.md').read_text()
        for required in ['OFFLINE PREPARATION ONLY', '28 managed resource instances', 'no free-tier promise', 'No automatic dependency upgrades', 'no checkout/order creation endpoint', 'Mandatory LinkedIn', 'AccessDenied', 'Fresh IAM review/permission']:
            self.assertIn(required, text)

    def test_record_identifies_mock_only_results(self):
        record = (ROOT / 'evidence/local-validation.md').read_text()
        for required in ['OFFLINE ONLY', '18', '46', 'not runtime evidence', '35 screenshots remain pending']:
            self.assertIn(required, record)


if __name__ == '__main__':
    unittest.main()
