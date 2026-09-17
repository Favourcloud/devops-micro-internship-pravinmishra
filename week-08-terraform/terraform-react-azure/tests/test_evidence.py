import datetime
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import subprocess
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence'
BRIEF = ROOT.parent / 'assignment-03-deploy-a-react-application-on-azure-virtual-machine-using-terraform.md'
SOURCE_HEAD = '3a0eea8f2dc9c62d28e511155065e6e145a3555b'
FROZEN_FILES = {
    '.terraform.lock.hcl', 'cloud-init.sh', 'main.tf', 'terraform.tfvars.example',
    'tests/app.tftest.hcl', 'tests/inputs.tftest.hcl', 'tests/run_offline.py', 'variables.tf',
}
MANIFEST = json.loads((EVIDENCE / 'manifest.json').read_text())
PROVENANCE = json.loads((EVIDENCE / 'provenance.json').read_text())


def png_chunks(data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Not a PNG')
    offset = 8
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        end = offset + 8 + length
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:end]
        if zlib.crc32(kind + payload) != struct.unpack('>I', data[end:end + 4])[0]:
            raise ValueError('Invalid PNG checksum')
        yield kind, payload
        offset = end + 4
    if offset != len(data):
        raise ValueError('Truncated PNG')


class EvidenceTests(unittest.TestCase):
    def test_original_capture_hashes_and_png_structure(self):
        for item in PROVENANCE['screenshots']:
            with self.subTest(slot=item['number']):
                path = EVIDENCE / item['file']
                self.assertFalse(path.is_symlink())
                data = path.read_bytes()
                self.assertEqual(len(data), item['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])
                chunks = list(png_chunks(data))
                self.assertEqual(chunks[0][0], b'IHDR')
                self.assertEqual(chunks[-1], (b'IEND', b''))
                self.assertIn(b'IDAT', [kind for kind, _ in chunks])
                width, height = struct.unpack('>II', chunks[0][1][:8])
                # Original Retina pixels are twice the receipt's logical window bounds.
                self.assertEqual(width, 3584)
                self.assertEqual(height, 2006 if item['number'] in (4, 6, 7) else 2010)

    def test_exact_capture_inventory_and_mapping(self):
        items = PROVENANCE['screenshots']
        self.assertEqual([s['number'] for s in items], list(range(1, 9)))
        self.assertEqual(len({s['sha256'] for s in items}), 8)
        expected = set()
        for item, slot in zip(items, MANIFEST['screenshots'][:8]):
            path = Path(item['file'])
            self.assertFalse(path.is_absolute())
            self.assertNotIn('..', path.parts)
            self.assertEqual(path.parent, Path('screenshots'))
            self.assertEqual(path.suffix, '.png')
            self.assertEqual(item['file'], slot['file'])
            expected.add(EVIDENCE / path)
        self.assertFalse((EVIDENCE / 'screenshots').is_symlink())
        self.assertEqual(set(EVIDENCE.rglob('*.png')), expected)
        self.assertEqual(MANIFEST['provenance'], 'provenance.json')

    def test_sanitized_provenance_schema(self):
        self.assertEqual(set(PROVENANCE), {
            'schema_version', 'learner', 'repository', 'source_head', 'source_hashes',
            'receipt_verified_at_utc', 'capture_method', 'operator', 'visible_identity',
            'privacy_review', 'screenshots', 'normal_init', 'cloud_actions_authorized',
            'cloud_execution_verified', 'assignment_complete', 'pending_slots', 'notes',
        })
        for item in PROVENANCE['screenshots']:
            self.assertEqual(set(item), {
                'number', 'file', 'sha256', 'bytes', 'captured_at_utc', 'image_modified',
                'privacy_checked', 'operator', 'evidence_kind', 'description',
            })
        self.assertEqual(set(PROVENANCE['normal_init']), {
            'command', 'backend_type', 'backend_target', 'managed_resource_state_exists',
            'filesystem_only_provider_mirror', 'startup_environment_guard_passed',
        })
        self.assertEqual(PROVENANCE['learner'], 'Eze Favour')
        self.assertEqual(PROVENANCE['repository'], 'Favourcloud/devops-micro-internship-pravinmishra')
        self.assertEqual(PROVENANCE['visible_identity'], 'Eze Favour — Week 08 Assignment 3')

    def test_capture_times_operator_and_original_attribution(self):
        verified = datetime.datetime.fromisoformat(PROVENANCE['receipt_verified_at_utc'])
        self.assertEqual(verified.utcoffset(), datetime.timedelta(0))
        operator = 'GitHub Copilot under user delegation; not manual learner execution'
        self.assertEqual(PROVENANCE['operator'], operator)
        for item in PROVENANCE['screenshots']:
            captured = datetime.datetime.fromisoformat(item['captured_at_utc'])
            self.assertEqual(captured.utcoffset(), datetime.timedelta(0))
            self.assertEqual(captured.date(), datetime.date(2026, 9, 17))
            self.assertLessEqual(captured, verified)
            self.assertEqual(item['operator'], operator)
            self.assertIs(item['image_modified'], False)
            self.assertIs(item['privacy_checked'], True)
        self.assertIn('not composites', PROVENANCE['capture_method'])

    def test_frozen_source_hashes_and_revision(self):
        self.assertEqual(PROVENANCE['source_head'], SOURCE_HEAD)
        self.assertEqual(set(PROVENANCE['source_hashes']), FROZEN_FILES)
        for name, digest in PROVENANCE['source_hashes'].items():
            with self.subTest(file=name):
                path = ROOT / name
                self.assertFalse(path.is_symlink())
                content = path.read_bytes()
                original = subprocess.check_output([
                    'git', 'show', f'{SOURCE_HEAD}:week-08-terraform/terraform-react-azure/{name}',
                ], cwd=ROOT)
                self.assertEqual(content, original)
                self.assertEqual(hashlib.sha256(content).hexdigest(), digest)

    def test_normal_initialization_is_local_only(self):
        init = PROVENANCE['normal_init']
        self.assertEqual(init['command'], 'terraform init -input=false -lockfile=readonly')
        self.assertEqual(init['backend_type'], 'local')
        self.assertEqual(init['backend_target'], '.private/terraform.tfstate')
        self.assertIs(init['managed_resource_state_exists'], False)
        self.assertIs(init['filesystem_only_provider_mirror'], True)
        self.assertIs(init['startup_environment_guard_passed'], True)
        kinds = [s['evidence_kind'] for s in PROVENANCE['screenshots']]
        self.assertEqual(kinds, [
            'local-tool-version', 'local-tool-version', 'local-editor-extension',
            'local-source', 'local-source', 'local-source', 'local-source', 'local-backend-init',
        ])
        self.assertFalse((ROOT / '.private/terraform.tfstate').exists())
        self.assertFalse((ROOT / '.private/terraform.tfstate.backup').exists())

    def test_scope_and_historical_results_remain_distinct(self):
        self.assertEqual(PROVENANCE['pending_slots'], list(range(9, 16)))
        for key in ('cloud_actions_authorized', 'cloud_execution_verified', 'assignment_complete'):
            self.assertIs(PROVENANCE[key], False)
        verification = MANIFEST['verification']
        self.assertEqual(verification['source_head'], SOURCE_HEAD)
        self.assertEqual(verification['terraform_mock_runs'], 35)
        self.assertEqual(verification['python_tests'], 46)
        self.assertIn('not rerun', verification['result_scope'])
        self.assertIs(verification['cloud_commands_executed'], False)
        build = verification['local_build']
        self.assertEqual(build['platform'], 'darwin_x64')
        self.assertEqual(build['status'], 'passed')
        self.assertEqual(build['node_version'], '22.23.2')
        self.assertIs(build['tracked_source_unchanged'], True)
        self.assertIs(build['cloud_evidence'], False)
        integration = MANIFEST['evidence_integration']
        self.assertEqual(integration['status'], 'passed')
        self.assertEqual(integration['focused_python_tests'], 25)
        self.assertEqual(integration['delivery_tests'] + integration['capture_tests'], 25)
        self.assertEqual(integration['original_pngs_verified'], 8)
        self.assertEqual(integration['frozen_source_files_verified'], 8)
        for key in ('frozen_source_changed', 'terraform_mocks_rerun', 'upstream_build_rerun', 'cloud_commands_executed'):
            self.assertIs(integration[key], False)

    def test_brief_slot_links_and_runtime_limits(self):
        brief = BRIEF.read_text()
        sections = re.split(r'^### Screenshot \d+ .+$', brief, flags=re.M)[1:]
        self.assertEqual(len(sections), 15)
        for slot, section in zip(MANIFEST['screenshots'], sections):
            images = re.findall(r'!\[([^\]]+)\]\(([^)]+)\)', section)
            if slot['number'] <= 8:
                self.assertEqual(len(images), 1)
                self.assertIn('Eze Favour', images[0][0])
                self.assertIn('Copilot-operated', images[0][0])
                self.assertEqual(images[0][1], 'terraform-react-azure/evidence/' + slot['file'])
                self.assertIn('**Evidence status:** Captured', section)
            else:
                self.assertEqual(images, [])
                self.assertIn('**Evidence status:** Pending', section)
        self.assertIn('whole file is not visible', sections[5])
        self.assertIn('not runtime', sections[5])
        self.assertIn('/tmp/dmi-react.XXXXXXXX', sections[5])
        self.assertIn('not a real public IP', sections[6])
        self.assertIn('normal **local backend**', sections[7])
        self.assertIn('- [ ] Signed in to Azure and confirmed the correct subscription', brief)
        self.assertIn('- [ ] Captured all 15 required screenshots', brief)

    def test_existing_private_capture_artifacts_remain_ignored(self):
        private = ROOT / '.private'
        self.assertFalse(private.is_symlink())
        if private.exists():
            self.assertTrue(private.is_dir())
            self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o700)
            for path in private.glob('evidence-*'):
                self.assertFalse(path.is_symlink())
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)
                result = subprocess.run([
                    'git', 'check-ignore', '--no-index', '--quiet', str(path.relative_to(ROOT)),
                ], cwd=ROOT, check=False)
                self.assertEqual(result.returncode, 0)
        tracked = subprocess.check_output(['git', 'ls-files', '--', '.private'], cwd=ROOT, text=True)
        self.assertEqual(tracked, '')

    def test_public_metadata_and_png_privacy_guards(self):
        patterns = [
            r'/' + r'Users/[^/\s]+/', r'/' + r'home/[^/\s]+/',
            r'(?i)window[_ -]?id\s*[:=]\s*\d+', r'AKIA[0-9A-Z]{16}',
            r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----',
            r'/subscriptions/(?!00000000-0000-0000-0000-000000000000)[0-9a-f-]{36}',
        ]
        texts = [BRIEF.read_text(), (ROOT / 'README.md').read_text()]
        texts.extend(p.read_text() for p in EVIDENCE.glob('*.json'))
        for item in PROVENANCE['screenshots']:
            for kind, payload in png_chunks((EVIDENCE / item['file']).read_bytes()):
                if kind == b'IDAT':
                    continue
                texts.append(payload.replace(b'\0', b'').decode('utf-8', errors='ignore'))
                if kind in (b'zTXt', b'iCCP'):
                    _, compressed = payload.split(b'\0', 1)
                    self.assertEqual(compressed[0], 0)
                    texts.append(zlib.decompress(compressed[1:]).decode('utf-8', errors='ignore'))
                elif kind == b'iTXt':
                    _, body = payload.split(b'\0', 1)
                    flag, method = body[:2]
                    self.assertIn(flag, (0, 1))
                    self.assertEqual(method, 0)
                    _, _, text = body[2:].split(b'\0', 2)
                    texts.append((zlib.decompress(text) if flag else text).decode('utf-8'))
        for text in texts:
            for pattern in patterns:
                self.assertNotRegex(text, pattern)
        self.assertFalse(any(p.suffix == '.log' for p in EVIDENCE.rglob('*')))


if __name__ == '__main__':
    unittest.main()
