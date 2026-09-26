#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path
import sys
root=Path(__file__).resolve().parent
e=json.load(sys.stdin);name=e.get('tool_name');args=e.get('tool_input',{});allow=False
if name=='Bash':allow=args.get('command')=='./run-triage.sh' and not args.get('run_in_background') and Path(e.get('cwd','/')).resolve()==root
elif name=='Skill':allow=args.get('skill')=='pipeline-triage'
elif name=='Read':
 p=Path(args.get('file_path','/'));p=(root/p if not p.is_absolute() else p).resolve()
 allowed=[root/'CLAUDE.md',root/'README.md',root/'.claude/skills/pipeline-triage/SKILL.md',root/'pipeline-triage.sh',root/'fetch.py',root/'classify.py']
 allow=p in allowed or p in [root/'reports'/n for n in ['pipeline-health-report.txt','baseline-report.txt','incident-failure-report.txt','recovery-report.txt']]
 if allow and p==root/'reports/pipeline-health-report.txt':
  try:
   evidence=json.loads((root/'reports/evidence.json').read_text())
   generated=datetime.fromisoformat(evidence['generated_at'])
   started=datetime.fromisoformat(os.environ['DMI_TRIAGE_NOT_BEFORE'])
   allow=p.exists() and 'Overall Status: RUNNING' not in p.read_text() and generated>=started
  except (KeyError,ValueError,OSError,TypeError):allow=False
x={'hookEventName':'PreToolUse','permissionDecision':'allow' if allow else 'deny','permissionDecisionReason':'Only exact read-only triage and sanitized completed reports are authorized. No edits, raw credentials, arbitrary shell or pipeline mutations.'}
if allow and name=='Bash':x['updatedInput']={**args,'timeout':600000}
print(json.dumps({'hookSpecificOutput':x}))
