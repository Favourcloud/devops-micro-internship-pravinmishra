"""Restore reviewed answers to prompts when checking unchanged requirement hashes.

This checks worksheet structure, not grading eligibility, human review or live facts.
New completed slots require an explicit allowlist update and evidence tests.
"""

import re


ASSIGNMENTS = {
    "assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md": "01",
    "assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md": "02",
    "assignment-03-automate-react-app-deployment-using-azure-devops-cicd.md": "03",
    "assignment-04-automate-epicbook-deployment-with-dual-pipelines.md": "04",
    "assignment-05-ai-assisted-azure-devops-dual-pipeline-failure-triage.md": "05",
}
CAPTURE_SLOTS = {
    "01": ("A1-S1", "A1-S2", "A1-S3", "A1-S4", "A1-S5", "A1-S6", "A1-S7"),
    "02": ("A2-S1", "A2-S3"),
}
PREPARATION_EDITS = (
    (
        "## Source preparation — not a completed assignment",
        "## Historical source preparation — not a completed assignment",
    ),
    (
        "The [seven-slot manifest](self-hosted-agent/evidence/manifest.json) is entirely pending; no live resource, agent, pipeline success, or screenshot is claimed.",
        "At the source-preparation checkpoint, the [seven-slot manifest](self-hosted-agent/evidence/manifest.json) was entirely pending; no live resource, agent, pipeline success, or screenshot was claimed. The current manifest and attachments below now record seven genuine captures from separate trials; the user has attested full-size content/privacy review of all seven A1 screenshots. Other assignment requirements remain pending.",
    ),
    (
        "The original tasks, evidence slots, checklist, and unanswered notes below are unchanged.",
        "The original task instructions, evidence requirements and unchecked checklist remain intact; current captures and attributed technical notes appear below.",
    ),
)


def restore_original_prompts(raw, name):
    """Return original published brief bytes except for still-verifiable requirements.

    Only the nine evidenced image placeholders and A1's attributed technical notes
    may be replaced. Unknown, duplicated or malformed answer markers fail closed.
    Existing baseline hashes then catch any other change to a brief.
    """
    if name not in ASSIGNMENTS:
        raise ValueError("Unknown assignment filename")
    assignment = ASSIGNMENTS[name]
    expected = tuple(marker.encode() for marker in CAPTURE_SLOTS.get(assignment, ()))
    found = tuple(re.findall(rb"<!-- BEGIN WEEK10 CAPTURE ([^\n]+) -->", raw))
    if found != expected:
        raise ValueError("Unexpected capture substitutions")
    for marker in expected:
        pattern = (
            rb"<!-- BEGIN WEEK10 CAPTURE " + marker + rb" -->\n"
            rb"(?:(?!<!--).)*?<!-- END WEEK10 CAPTURE " + marker + rb" -->\n\n"
        )
        raw, count = re.subn(pattern, b"Add your screenshot here.\n\n", raw, flags=re.S)
        if count != 1:
            raise ValueError("Malformed capture substitution")
    if b"WEEK10 CAPTURE" in raw:
        raise ValueError("Unmatched capture marker")
    if assignment == "01":
        pattern = (
            rb"<!-- BEGIN WEEK10 ANSWER A1-NOTES -->\n"
            rb"(?:(?!<!--).)*?<!-- END WEEK10 ANSWER A1-NOTES -->\n\n"
        )
        raw, count = re.subn(pattern, b"Write your answer here.\n\n", raw, flags=re.S)
        if count != 1:
            raise ValueError("Missing or duplicated technical notes")
        for original, current in PREPARATION_EDITS:
            if raw.count(current.encode()) != 1:
                raise ValueError("Unexpected preparation notice")
            raw = raw.replace(current.encode(), original.encode(), 1)
    if b"WEEK10 ANSWER" in raw:
        raise ValueError("Unmatched or unapproved answer marker")
    return raw
