#!/usr/bin/env python3
"""Build only checksum-verified application source already committed to this repo."""
import gzip,hashlib,io,json,os,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
source=Path(os.environ.get('BUILD_SOURCESDIRECTORY',root))
lock=json.loads((root/'app-patches/source-lock.json').read_text())
assert hashlib.sha256((root/'app-patches/demo-checkout.patch').read_bytes()).hexdigest()==lock['release_id']
payload={}
for name,expected in lock['files'].items():
 p=source/name
 assert p.is_file() and not p.is_symlink(),name
 data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==expected,'Source mismatch: '+name
 payload[name]=data
payload['RELEASE.json']=(json.dumps({'upstream':lock['upstream'],'release_id':lock['release_id']})+'\n').encode()
out=Path(os.environ['BUILD_ARTIFACTSTAGINGDIRECTORY']);out.mkdir(exist_ok=True,parents=True)
with (out/'epicbook.tar.gz').open('wb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tar:
 for name,data in sorted(payload.items()):
  info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data))
(out/'release.json').write_text(json.dumps({'release_id':lock['release_id'],'archive_sha256':hashlib.sha256((out/'epicbook.tar.gz').read_bytes()).hexdigest()},indent=2)+'\n')
print('Verified immutable source and built release '+lock['release_id'])
