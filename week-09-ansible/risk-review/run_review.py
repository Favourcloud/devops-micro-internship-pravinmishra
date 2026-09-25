"""Fixed command adapter: private raw output, public sanitized report only."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
(root/'reports').mkdir(exist_ok=True)
(root/'reports/latest.json').write_text(json.dumps({'status':'RUNNING','started_at':datetime.now(timezone.utc).isoformat(),'message':'No final report yet. Do not reuse a previous finding.'}))
output=Path(os.environ['DMI_REVIEW_OUTPUT']).resolve()/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
env=dict(os.environ, DMI_REVIEW_PYTHON=sys.executable)
result=subprocess.run(['bash',str(root/'ansible-check-review.sh'),'--config',os.environ['DMI_REVIEW_CONFIG'],'--output',str(output)],cwd=root,env=env)
report=output/'report.json'
if report.is_file():
    (root/'reports').mkdir(exist_ok=True)
    (root/'reports/latest.json').write_bytes(report.read_bytes())
sys.exit(result.returncode)
