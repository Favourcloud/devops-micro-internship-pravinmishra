"""Focused local evidence checks; no network, GUI, cloud or runtime execution."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import unquote
import zlib

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT.parent / 'assignment-04-deploy-epicbook-application-on-aws-using-terraform.md'
EVIDENCE = ROOT / 'evidence'
SOURCE_HEAD = '7c0005592f167730edb0ec3f56bf29324af6a031'
SOURCE_HASHES_DIGEST = 'e7711fdb2bd13c7283060c1de3860785f451ea4257c6f59d2181173f25c977a2'
CAPTURE_HASHES_DIGEST = '4313be26eca24d954a48146148fb244d62438cebc0f7cf3dea4dba2a4a838a39'
PRIVATE_MARKERS = rb'/Users/|/private/var/|/var/folders/|/tmp/|arn:aws:|BEGIN PRIVATE KEY|\b(?:window|process)[ _-]?id\b'


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def png_chunks(raw):
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG signature')
    chunks, offset = [], 8
    while offset < len(raw):
        if len(raw) - offset < 12:
            raise ValueError('Truncated PNG chunk')
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        end = offset + 12 + size
        if end > len(raw):
            raise ValueError('Truncated PNG payload')
        kind, payload = raw[offset + 4:offset + 8], raw[offset + 8:end - 4]
        checksum = struct.unpack('>I', raw[end - 4:end])[0]
        if zlib.crc32(kind + payload) != checksum:
            raise ValueError('PNG CRC mismatch')
        chunks.append((kind, payload))
        offset = end
        if kind == b'IEND':
            if payload or offset != len(raw):
                raise ValueError('Data after PNG end')
            return chunks
    raise ValueError('Missing PNG end')


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads((ROOT / 'tests/assignment-source.json').read_text())
        self.manifest = json.loads((EVIDENCE / 'screenshot-manifest.json').read_text())
        self.provenance = json.loads((EVIDENCE / 'provenance.json').read_text())
        self.captures = self.provenance['screenshots']

    def assert_original_requirements(self, text):
        notices = {
            4: 'Partial source evidence is supplied below; the required private input file remains pending.',
            10: 'Source excerpts are supplied below; they do not show the entire script or a bootstrap run.',
        }
        for capture in self.captures:
            number = capture['number']
            heading = f"### Screenshot {number} — {self.manifest['slots'][number - 1]['title']}\n"
            self.assertEqual(text.count(heading), 1)
            section = text.split(heading, 1)[1].split('\n### Screenshot ', 1)[0]
            self.assertNotIn('Add your screenshot here.', section)
            image = f"![Screenshot {number} — Eze Favour — original local capture](terraform-aws-epicbook/evidence/{capture['file']})"
            self.assertEqual(section.count(image), 1)
            if number in notices:
                self.assertEqual(section.count(notices[number]), 1)
                restored = section.replace(notices[number], 'Add your screenshot here.')
            else:
                restored = section.replace(image, 'Add your screenshot here.\n\n' + image)
            text = text.replace(heading + section, heading + restored, 1)
        current = iter(text.replace('- [x]', '- [ ]').splitlines())
        for required in self.baseline['lines']:
            self.assertTrue(any(line == required for line in current), 'Lost or reordered original line: ' + required)

    def test_original_requirements_preserved_with_evidenced_prompt_replacements(self):
        original = '\n'.join(self.baseline['lines']) + '\n'
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), self.baseline['sha256'])
        self.assert_original_requirements(BRIEF.read_text())

    def test_missing_or_duplicate_accepted_image_is_rejected(self):
        text = BRIEF.read_text()
        image = re.search(r'^!\[Screenshot 1 — .+$', text, re.M).group()
        for replacement in ('', image + '\n' + image):
            with self.subTest(replacement=replacement), self.assertRaises(AssertionError):
                self.assert_original_requirements(text.replace(image, replacement))

    def test_unmet_prompt_and_requirement_removal_is_rejected(self):
        text = BRIEF.read_text()
        for changed in (text.replace('Add your screenshot here.\n', '', 1),
                        text.replace('### Screenshot 20 — Terraform Plan\n', '', 1),
                        text.replace('- [ ] Created VPC `10.0.0.0/16`\n', '', 1)):
            with self.subTest(changed=changed[:30]), self.assertRaises(AssertionError):
                self.assert_original_requirements(changed)

    def test_partial_notices_cannot_be_removed(self):
        text = BRIEF.read_text()
        for notice in ('Partial source evidence is supplied below; the required private input file remains pending.',
                       'Source excerpts are supplied below; they do not show the entire script or a bootstrap run.'):
            with self.subTest(notice=notice), self.assertRaises(AssertionError):
                self.assert_original_requirements(text.replace(notice, 'Complete live proof.'))

    def test_source_notes_are_attributed_and_do_not_complete_live_work(self):
        text = BRIEF.read_text()
        self.assertIn('factual Copilot-operated source/local-check notes, not firsthand learner reflection', text)
        self.assertIn('No real plan, application/database transaction, order workflow, destroy run', text)
        self.assertEqual(text.count('Add your screenshot here.'), 16)

    def test_manifest_exact_original_titles(self):
        titles = re.findall(r'^### Screenshot (\d+) — (.+)$', '\n'.join(self.baseline['lines']), re.M)
        self.assertEqual([(slot['number'], slot['title']) for slot in self.manifest['slots']], [(int(n), title) for n, title in titles])
        self.assertEqual(re.findall(r'^### Screenshot (\d+) — (.+)$', BRIEF.read_text(), re.M), titles)

    def test_nineteen_local_captures_and_sixteen_pending_slots(self):
        slots = self.manifest['slots']
        self.assertEqual([slot['number'] for slot in slots], list(range(1, 36)))
        self.assertEqual([capture['number'] for capture in self.captures], list(range(1, 20)))
        for slot, capture in zip(slots[:19], self.captures):
            self.assertEqual(slot['status'], 'captured_local')
            self.assertEqual(slot['file'], capture['file'])
            self.assertEqual(slot['sha256'], capture['sha256'])
            self.assertEqual(slot['reason'], capture['scope'])
        self.assertTrue(all(slot['status'] == 'pending' and slot['file'] is None for slot in slots[19:]))
        self.assertEqual(self.provenance['pending_slots'], list(range(20, 36)))

    def test_only_source_and_local_init_validate_checkmarks(self):
        checked = re.findall(r'^- \[x\] (.+)$', BRIEF.read_text(), re.M)
        self.assertEqual(checked, ['Created the modular Terraform project', 'Created the root `main.tf`, `variables.tf`, and `outputs.tf`', 'Created the Network module', 'Created the EC2 module', 'Created the RDS module', 'Created the EC2 `user_data.sh`', 'Completed `terraform init`', 'Completed `terraform validate`'])
        self.assertIn('six source deliverables and successful local init/validate, not AWS resources', BRIEF.read_text())

    def test_local_markdown_links_exist(self):
        for path in [BRIEF, ROOT / 'README.md', EVIDENCE / 'local-validation.md', EVIDENCE / 'preflight-20260924.md']:
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in target and not target.startswith('#'):
                    self.assertTrue((path.parent / unquote(target.split('#')[0])).exists(), str(path) + ': ' + target)

    def test_brief_images_match_slots_and_qualified_captions(self):
        sections = re.split(r'^### Screenshot \d+ — .+$', BRIEF.read_text(), flags=re.M)[1:]
        for number, section in enumerate(sections, 1):
            images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', section)
            if number <= 19:
                capture = self.captures[number - 1]
                self.assertEqual(images, ['terraform-aws-epicbook/evidence/' + capture['file']])
                self.assertIn('**Captured local evidence only:** ' + capture['scope'], section)
            else:
                self.assertEqual(images, [])

    def test_original_capture_hashes_and_byte_counts(self):
        originals = [{'number': c['number'], 'file': Path(c['file']).name, 'sha256': c['sha256']} for c in self.captures]
        self.assertEqual(canonical_digest(originals), CAPTURE_HASHES_DIGEST)
        self.assertEqual(sum(c['bytes'] for c in self.captures), 10553523)
        for capture in self.captures:
            with self.subTest(slot=capture['number']):
                self.assertRegex(capture['file'], r'^screenshots/screenshot-\d{2}-[a-z0-9-]+\.png$')
                raw = (EVIDENCE / capture['file']).read_bytes()
                self.assertEqual(len(raw), capture['bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), capture['sha256'])

    def test_png_signatures_crcs_dimensions_and_scanlines(self):
        for capture in self.captures:
            with self.subTest(slot=capture['number']):
                chunks = png_chunks((EVIDENCE / capture['file']).read_bytes())
                self.assertEqual(chunks[0][0], b'IHDR')
                self.assertEqual(sum(kind == b'IHDR' for kind, _ in chunks), 1)
                self.assertEqual(struct.unpack('>IIBBBBB', chunks[0][1]), (3584, 2000, 8, 6, 0, 0, 0))
                self.assertEqual((capture['width'], capture['height']), (3584, 2000))
                decoder = zlib.decompressobj()
                decoded = decoder.decompress(b''.join(data for kind, data in chunks if kind == b'IDAT'))
                self.assertTrue(decoder.eof)
                self.assertEqual(decoder.unused_data, b'')
                self.assertEqual(len(decoded), 2000 * (3584 * 4 + 1))
                self.assertTrue(all(value <= 4 for value in decoded[::3584 * 4 + 1]))

    def test_png_checks_reject_corruption_and_extra_bytes(self):
        raw = (EVIDENCE / self.captures[0]['file']).read_bytes()
        bad_crc = raw[:29] + bytes([raw[29] ^ 1]) + raw[30:]
        for bad in (b'not PNG', bad_crc, raw[:-1], raw + b'extra'):
            with self.assertRaises(ValueError):
                png_chunks(bad)

    def test_historical_source_hashes_and_exact_node_update(self):
        self.assertEqual(self.provenance['source_head'], SOURCE_HEAD)
        sources = self.provenance['source_hashes']
        self.assertEqual(len(sources), 22)
        self.assertEqual(canonical_digest(sources), SOURCE_HASHES_DIGEST)
        update = json.loads((EVIDENCE / 'runtime-update-20260924.json').read_text())
        self.assertEqual(update['changed_file'], 'modules/ec2/user_data.sh')
        self.assertEqual(update['historical_source_commit'], SOURCE_HEAD)
        self.assertEqual(update['previous_node_version'], '22.22.0')
        self.assertEqual(update['node_version'], '22.23.3')
        self.assertEqual(update['linux_x64_archive_sha256'], 'df450af89261115ef9f9e3830c3eeb2cc9213b63c720b1af623cb5dcbe2e02de')
        for name, expected in sources.items():
            raw = (ROOT / name).read_bytes()
            if name == update['changed_file']:
                self.assertEqual(hashlib.sha256(raw).hexdigest(), update['after_sha256'])
                self.assertEqual(update['before_sha256'], expected)
                self.assertEqual(raw.count(update['node_version'].encode()), 2)
                self.assertEqual(raw.count(update['linux_x64_archive_sha256'].encode()), 1)
                raw = raw.replace(update['node_version'].encode(), update['previous_node_version'].encode())
                raw = raw.replace(update['linux_x64_archive_sha256'].encode(), update['previous_linux_x64_archive_sha256'].encode())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected, name)
        self.assertNotIn('tests/test_evidence.py', sources)
        self.assertEqual(self.provenance['evidence_test_base_sha256'], '7698b6a38fe2800aa2683cbdfeebb927dc9e84e73275548a5a862c53ca86427a')

    def test_proposed_source_resource_counts(self):
        sources = list(ROOT.glob('*.tf')) + list((ROOT / 'modules').glob('*/*.tf'))
        self.assertEqual(len(sources), 12)
        text = '\n'.join(path.read_text() for path in sources)
        self.assertEqual(len(re.findall(r'^resource "', text, re.M)), 25)
        self.assertEqual(len(re.findall(r'^data "', text, re.M)), 1)
        # Two count=2 blocks and one 2-element for_each add three instances.
        self.assertEqual(len(re.findall(r'^\s*count\s*=\s*2$', text, re.M)), 2)
        self.assertIn('toset(["80", "443"])', text)

    def test_only_allowlisted_public_artifacts_and_provenance_fields(self):
        expected = {'local-validation.md', 'screenshot-manifest.json', 'provenance.json', 'runtime-update-20260924.json', 'preflight-20260924.md'} | {c['file'] for c in self.captures}
        actual = set()
        for path in EVIDENCE.rglob('*'):
            self.assertFalse(path.is_symlink())
            if path.is_file():
                actual.add(path.relative_to(EVIDENCE).as_posix())
            else:
                self.assertEqual(path, EVIDENCE / 'screenshots')
        self.assertEqual(actual, expected)
        self.assertEqual(set(self.provenance), {'learner', 'assignment', 'source_head', 'verified_at_utc', 'operator', 'capture_method', 'image_modified', 'privacy_review', 'source_hashes', 'evidence_test_base_sha256', 'evidence_only_edit_exception', 'local_init', 'local_validate', 'pending_slots', 'completion', 'limitations', 'screenshots', 'source_review'})
        for capture in self.captures:
            self.assertEqual(set(capture), {'number', 'file', 'captured_at_utc', 'sha256', 'bytes', 'width', 'height', 'scope'})

    def test_no_private_paths_or_identifiers_in_public_text_and_png_metadata(self):
        for path in EVIDENCE.iterdir():
            if path.is_file():
                self.assertIsNone(re.search(PRIVATE_MARKERS, path.read_bytes(), re.I), path.name)
        for capture in self.captures:
            for kind, data in png_chunks((EVIDENCE / capture['file']).read_bytes()):
                if kind == b'iTXt':
                    _, rest = data.split(b'\0', 1)
                    compressed, method = rest[:2]
                    _, _, data = rest[2:].split(b'\0', 2)
                    self.assertIn(compressed, (0, 1))
                    self.assertEqual(method, 0)
                    if compressed:
                        data = zlib.decompress(data)
                elif kind == b'iCCP':
                    _, rest = data.split(b'\0', 1)
                    self.assertEqual(rest[0], 0)
                    data = zlib.decompress(rest[1:])
                elif kind != b'eXIf':
                    continue
                self.assertIsNone(re.search(PRIVATE_MARKERS, data, re.I), capture['file'])

    def test_copilot_capture_and_review_scope_are_explicit(self):
        self.assertIn('not manual learner execution', self.provenance['operator'])
        self.assertIs(self.provenance['image_modified'], False)
        verified = datetime.fromisoformat(self.provenance['verified_at_utc'])
        for capture in self.captures:
            captured = datetime.fromisoformat(capture['captured_at_utc'])
            self.assertIsNotNone(captured.tzinfo)
            self.assertLessEqual(captured, verified)
        review = self.provenance['source_review']
        self.assertEqual(review['reviewed_head'], SOURCE_HEAD)
        self.assertEqual(review['base_head'], '86210c7b1436b6bbe7d0b2bb61f45b5b4c2618fe')
        self.assertIn('Parent reports', review['result'])
        self.assertIn('fixes/regressions', review['scope'])
        self.assertEqual(review['evidence_integration_independent_verification'], 'pending')

    def test_local_init_is_normal_default_local_backend_without_state(self):
        init = self.provenance['local_init']
        self.assertEqual(init['command'], 'terraform init -input=false -lockfile=readonly')
        for key in ('successful', 'startup_guard_passed', 'credential_free', 'command_was_not_backend_disabled'):
            self.assertIs(init[key], True)
        for key in ('managed_resource_state_created', 'backend_metadata_state_created', 'root_managed_state_created', 'private_managed_state_created', 'remote_backend_or_aws_calls'):
            self.assertIs(init[key], False)
        self.assertIn('implicit default local backend', init['backend'])
        self.assertIn('terraform.tfstate unless deliberately overridden', init['default_future_state_path'])
        self.assertIn('does not override the managed-state path', init['tf_data_dir_scope'])
        self.assertEqual(self.provenance['local_validate'], {'command': 'terraform validate', 'successful': True, 'not_live_plan_or_apply': True})
        for path in (ROOT / 'README.md', EVIDENCE / 'local-validation.md'):
            text = path.read_text()
            for required in ('TF_DATA_DIR', 'implicit default local backend', 'metadata only', '.private/terraform.tfstate'):
                self.assertIn(required, text)

    def test_partial_views_and_pending_human_live_requirements(self):
        self.assertIn('terraform.tfvars has not been created', self.captures[3]['scope'])
        for required in ('21–47', '83–117', 'word-wrap', 'Not the whole script'):
            self.assertIn(required, self.captures[9]['scope'])
        for number in (11, 13, 15):
            self.assertIn('Native split-editor', self.captures[number - 1]['scope'])
        for number in (8, 11, 14, 17):
            self.assertIn('source expressions', self.captures[number - 1]['scope'])
        pending = self.provenance['completion']
        self.assertEqual(set(pending), {'live_deployment', 'application_runtime', 'cleanup', 'order_workflow', 'linkedin_publication', 'learner_reflection', 'manual_learner_execution', 'private_tfvars_created', 'evidence_integration_independently_verified'})
        self.assertTrue(all(value is False for value in pending.values()))

    def test_runbook_explicit_gates_and_upstream_limitation(self):
        text = (ROOT / 'README.md').read_text()
        for required in ['OFFLINE PREPARATION ONLY', '28 managed resource instances', 'no free-tier promise', 'No automatic dependency upgrades', 'no checkout/order creation endpoint', 'Mandatory LinkedIn', 'AccessDenied', 'Fresh IAM review/permission']:
            self.assertIn(required, text)

    def test_record_separates_historical_mocks_from_current_evidence(self):
        record = (EVIDENCE / 'local-validation.md').read_text()
        for required in ['OFFLINE ONLY', 'Historical results — not rerun for evidence integration', '22 native mock runs and 52 standard-library tests', 'not runtime evidence', '19 original local PNGs', 'slots 20–35 remain pending', 'Focused evidence-only verification']:
            self.assertIn(required, record)


if __name__ == '__main__':
    unittest.main()
