"""Read-only checks for the bounded 19 September submission reconciliation."""
import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
AWS = ROOT / 'week-06-aws-cloud/assignment-03-deploy-mini-finance-website-on-aws-virtual-machine.md'
ANSIBLE = ROOT / 'week-09-ansible/assignment-03-deploy-static-website-to-multiple-servers-using-multi-play-ansible-playbook.md'
REPLACEMENTS = {
    'Copy and paste the complete contents of your `inventory.ini` file below:':
        'Submitted [`inventory.ini`](static-web/inventory.ini) source is reproduced below. It is intentionally unconfigured; this supplies the editable template, not a live inventory or connectivity result:',
    'Copy and paste the complete contents of your `site.yml` file below:':
        'Submitted [`site.yml`](static-web/site.yml) source is reproduced below. The three plays are prepared with execution disabled by default; this is not a successful deployment record:',
    'Copy and paste the complete contents of your `README.md` file below:':
        'Submitted [`README.md`](static-web/README.md) content is reproduced below, including factual Copilot-assisted preparation notes. Firsthand learner reflection and live results remain pending:',
}


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


class ChronologicalEvidenceTests(unittest.TestCase):
    def test_week06_only_the_filled_url_prompt_changed(self):
        current = AWS.read_text()
        new = 'Recorded EC2 URL from the original submission (historical, not a current availability claim):'
        old = 'Paste the public IP address of your EC2 instance here (e.g. `http://3.91.105.10`):'
        self.assertEqual(current.count(new), 1)
        self.assertNotIn(old, current)
        self.assertEqual(git_blob(current.replace(new, old).encode()), '74a5dcf2636010301e0cb4c3fe9701853318d36b')
        self.assertIn('the EC2 public IP did not respond', current)
        self.assertEqual(git_blob((AWS.parent / 'image.png').read_bytes()), 'eb58042739f2204166ed0e2c329af0e56b66bda3')

    def test_week09_only_supplied_text_prompts_changed(self):
        current = ANSIBLE.read_text()
        for old, new in REPLACEMENTS.items():
            self.assertEqual(current.count(new), 1)
            self.assertNotIn(old, current)
            current = current.replace(new, old)
        self.assertEqual(git_blob(current.encode()), '971d999c83e96d4e7213f9df3d3a73136a2081dc')

    def test_week09_embedded_files_match_submitted_source(self):
        text = ANSIBLE.read_text()
        for filename, fence, language in (('inventory.ini', '```', 'ini'), ('site.yml', '```', 'yaml'), ('README.md', '````', 'markdown')):
            with self.subTest(filename=filename):
                content = re.search(r'^' + fence + language + r'\n(.*?)^' + fence + r'$', text, re.M | re.S).group(1)
                self.assertEqual(content.rstrip(), (ANSIBLE.parent / 'static-web' / filename).read_text().rstrip())

    def test_root_changes_are_confined_to_the_dated_reconciliation(self):
        text = (ROOT / 'README.md').read_text()
        heading = '### Chronological evidence reconciliation — 19 September 2026\n'
        following = '### Publication and rubric review — 16 September 2026\n'
        self.assertEqual(text.count(heading), 1)
        before, after = text.split(heading)
        section, remainder = after.split(following, 1)
        self.assertEqual(git_blob((before + following + remainder).encode()), '9674073deaab4a229542df992126925c06e155d6')
        self.assertIn('15 personal reflections remain unanswered', section)
        self.assertIn('No form submission, instructor request, grading run or improved score', section)
        self.assertIn('no qualifying weekly publication URLs', section)
        self.assertEqual(len(re.findall(r'^\| Week 0[6-9] \|', section, re.M)), 4)
        for target in re.findall(r'\]\(([^)]+)\)', section):
            if '://' not in target:
                self.assertTrue((ROOT / unquote(target.split('#')[0])).is_file(), target)

    def test_week07_historical_inventory_is_preserved(self):
        # This suite concerns the earlier reconciliation; later recoveries may
        # replace live files without altering the archived evidence audit.
        audit = json.loads((ROOT / 'publication-review/evidence/2026-09-26-earlier-weeks/week07-image-audit.json').read_text())
        self.assertEqual(audit['image_count'], 22)
        self.assertEqual(audit['non_evidence_placeholder_images'], 22)
        self.assertTrue(all((row['width'], row['height'], row['bytes']) == (1, 1, 68)
                            for row in audit['images']))



if __name__ == '__main__':
    unittest.main()
