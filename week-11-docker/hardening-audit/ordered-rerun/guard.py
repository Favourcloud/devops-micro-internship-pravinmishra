import json,sys,pathlib,os
x=json.load(sys.stdin);tool=x.get('tool_name');args=x.get('tool_input',{})
allowed=False
if tool=='Bash':allowed=args.get('command') in ['./run-audit.sh','./inspect-container.sh','./run-audit.sh 2>&1','./inspect-container.sh 2>&1']
elif tool=='Read':
 root=pathlib.Path(os.environ['DMI_AUDIT_ROOT']).resolve();p=pathlib.Path(args.get('file_path','')).resolve();allowed=p.is_relative_to(root) and not p.name.endswith('.private')
elif tool=='Skill':allowed=args.get('skill')=='docker-audit'
if not allowed:
 print('Docker audit guard: only the two fixed read-only wrappers, scoped Read, and docker-audit skill are allowed.',file=sys.stderr);sys.exit(2)
