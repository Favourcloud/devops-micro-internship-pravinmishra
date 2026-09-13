---
name: sprint-health
description: Produce a read-only Jira sprint health report covering velocity, at-risk work, and missing estimates. Use only when the user explicitly invokes sprint-health or requests a Jira sprint health report.
allowed-tools:
  - Read
  - jira_search
  - jira_get_issue
  - jira_get_agile_boards
  - jira_get_board_issues
  - jira_get_sprints_from_board
  - jira_get_sprint_issues
disable-model-invocation: true
---

# Sprint Health

Generate a concise report from live Jira data. This skill is strictly read-only: never create, edit, transition, assign, delete, comment on, move, or otherwise mutate Jira work.

## Allowed tools

Use only `Read` plus these read-only Jira MCP tools:

- `jira_search`
- `jira_get_issue`
- `jira_get_agile_boards`
- `jira_get_board_issues`
- `jira_get_sprints_from_board`
- `jira_get_sprint_issues`

Do not use mutating tools such as `jira_create_issue`, `jira_update_issue`, `jira_transition_issue`, `jira_assign_issue`, `jira_delete_issue`, `jira_add_comment`, `jira_edit_comment`, or sprint-management write tools.

## Workflow

1. Identify the requested Jira project or board. If none is supplied, use the configured project filter and ask only when it is ambiguous.
2. Read the active sprint and its issues using the agile read tools. Use `jira_search` or `jira_get_issue` only to fill missing details.
3. Calculate:
   - committed points: total estimated points in the sprint;
   - completed points: points on completed issues;
   - completion ratio and remaining points;
   - at-risk stories: unresolved work in progress or to-do work with a due date/priority signal, or work consuming most of the sprint with no progress;
   - missing estimates: sprint issues with no story-point value.
4. Report the source sprint, issue keys, status, estimates, assumptions, and a short triage summary. Clearly distinguish observed Jira fields from inference.
5. Never recommend that the skill itself perform a board change. Any change must be made by a human in Jira and then re-read.

## Output

Use these sections: `Sprint`, `Velocity`, `At risk`, `Missing estimates`, and `Read-only boundary`. Include a compact issue table when there are issues to report.
