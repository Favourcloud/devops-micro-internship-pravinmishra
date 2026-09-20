"""Restore reviewed answers to prompts when checking unchanged requirement hashes.

This checks worksheet structure, not grading eligibility, human review or live facts.
New completed slots or checklist answers require explicit allowlists and evidence tests.
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
    "03": ("A3-S2",),
}
CHECKLIST_COMPLETIONS = {
    "01": (
        "- [x] Task 2: Self-hosted agent pool created (Screenshot 1)",
        "- [x] Task 3: Ubuntu VM provisioned and SSH verified (Screenshots 2–3)",
        "- [x] Task 4: Agent installed, registered, and running as a service (Screenshots 4–5)",
        "- [x] Task 5: Agent verified Online (Screenshot 6)",
        "- [x] Task 6: Test pipeline run successfully (Screenshot 7)",
        "- [x] Platform/org/pool details and issue notes written (Notes)",
    ),
    "02": (
        "* [x] The correct Azure Static Website repository was imported into Azure Repos",
        "* [x] `index.html` is visible in Azure Repos",
        "* [x] Your Full Name was added to the website",
        "* [x] The YAML trigger includes all branches",
    ),
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
        "The original task instructions, evidence requirements and checklist wording remain intact; current captures, attributed technical notes and evidence-backed historical checklist answers appear below.",
    ),
)


def restore_original_prompts(raw, name):
    """Return original published brief bytes except for still-verifiable requirements.

    Normalize ten capture blocks, A1's technical notes, two checklist scope notes
    and exactly ten evidence/approval-backed checkbox answers. Unknown, duplicated or
    malformed substitutions fail closed; baseline hashes catch other changes.
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
    if assignment in CHECKLIST_COMPLETIONS:
        marker = ("A" + str(int(assignment)) + "-CHECKLIST").encode()
        pattern = (
            rb"(^# Completion Checklist\n\n)<!-- BEGIN WEEK10 ANSWER " + marker + rb" -->\n"
            rb"(?:(?!<!--).)*?<!-- END WEEK10 ANSWER " + marker + rb" -->\n\n"
        )
        raw, count = re.subn(pattern, rb"\1", raw, flags=re.S | re.M)
        if count != 1:
            raise ValueError("Missing, misplaced or duplicated checklist scope note")
    if b"WEEK10 ANSWER" in raw:
        raise ValueError("Unmatched or unapproved answer marker")
    completed = tuple(line.encode() for line in CHECKLIST_COMPLETIONS.get(assignment, ()))
    found = tuple(re.findall(rb"(?m)^[ \t]*[-*+] \[[xX]\] .+$", raw))
    if found != completed:
        raise ValueError("Unexpected completed checklist answers")
    for line in completed:
        raw = raw.replace(line + b"\n", line.replace(b"[x]", b"[ ]", 1) + b"\n", 1)
    return raw
