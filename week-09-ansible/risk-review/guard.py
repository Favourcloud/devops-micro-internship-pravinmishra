#!/usr/bin/env python3
"""Claude PreToolUse guard: exact checker command and bounded source reads."""
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parent
event=json.load(sys.stdin)
name=event.get('tool_name'); args=event.get('tool_input',{})
allow=False
if name=='Bash':
    allow=(args.get('command')=='./run-review.sh' and not args.get('run_in_background') and
           Path(event.get('cwd','/')).resolve()==root)
elif name=='Read':
    p=Path(args.get('file_path','/'))
    if not p.is_absolute(): p=root/p
    p=p.resolve()
    allow=p.is_relative_to(root) and '.git' not in p.parts and not any(x in p.name for x in ('private','secret','vault','password'))
    if allow and p==root/'reports/latest.json' and p.exists():
        allow=json.loads(p.read_text()).get('status')!='RUNNING'
elif name=='Skill':
    allow=args.get('skill')=='ansible-risk-review'
decision={'hookEventName':'PreToolUse','permissionDecision':'allow' if allow else 'deny',
          'permissionDecisionReason':'Only bounded reads and the exact guarded dry-run wrapper are authorized; wait for a fresh completed report.'}
if allow and name=='Bash':
    decision['updatedInput']={**args,'timeout':600000}
print(json.dumps({'hookSpecificOutput':decision}))
