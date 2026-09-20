"""Read-only checks for current A2 guidance, not approval or live readiness."""

import json
from pathlib import Path
import re
import unittest


APPLICATION = Path(__file__).resolve().parents[1]
WEEK = APPLICATION.parent
GATE = "runtime-authorization-remains-separate"
GUIDES = {
    "README.md": "../README.md#" + GATE,
    "target/terraform/README.md": "../../../README.md#" + GATE,
    "transport/README.md": "../../README.md#" + GATE,
}


class ReadinessHandoffTests(unittest.TestCase):
    def test_all_three_guides_link_to_the_existing_runtime_gate(self):
        for path, target in GUIDES.items():
            with self.subTest(path=path):
                guide = APPLICATION / path
                links = re.findall(r"\]\(([^\s)]+)\)", guide.read_text())
                self.assertIn(target, links)
                relative, fragment = target.split("#")
                destination = (guide.parent / relative).resolve()
                self.assertEqual(destination, WEEK / "README.md")
                headings = re.findall(r"^## (.+)$", destination.read_text(), re.M)
                anchors = [heading.lower().replace(" ", "-") for heading in headings]
                self.assertIn(fragment, anchors)

    def test_proposed_window_is_explicitly_historical_not_permission(self):
        for path in GUIDES:
            with self.subTest(path=path):
                text = re.sub(r"\s+", " ", (APPLICATION / path).read_text()).lower()
                self.assertIn("historical proposal", text)
                self.assertIn("does not authorize provisioning", text)
                self.assertIn("fresh", text)

    def test_removed_anchor_and_stale_activation_instructions_do_not_return(self):
        for path in GUIDES:
            with self.subTest(path=path):
                text = re.sub(r"\s+", " ", (APPLICATION / path).read_text()).lower()
                for stale in (
                    "current-resource-window-decision",
                    "use that fresh scope",
                    "already permits 24 hours from first provisioning",
                ):
                    self.assertNotIn(stale, text)

    def test_guidance_does_not_change_unapproved_inputs_or_human_gates(self):
        inputs = json.loads((APPLICATION / "target/terraform/aws/inputs.example.json").read_text())
        self.assertEqual(inputs["approval"], {
            "live_execution_approved": False,
            "approved_at": None,
            "expires_at": None,
            "estimated_total_usd": None,
            "planning_allowance_usd": None,
        })
        text = (APPLICATION / "README.md").read_text()
        self.assertIn("All four still need human review", text)
        self.assertIn("The shared PAT is to remain unchanged", text)
        self.assertIn("the root authorization is retired", text)
        self.assertIn("No live gate is satisfied by a source test or a readiness boolean", text)
        evidence = json.loads((WEEK / "evidence/current.json").read_text())
        self.assertIs(evidence["human_visual_review_verified"], False)


if __name__ == "__main__":
    unittest.main()
