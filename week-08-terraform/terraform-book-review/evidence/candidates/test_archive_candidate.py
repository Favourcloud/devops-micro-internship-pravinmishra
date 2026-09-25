"""Operator regression checks for selected-source archive metadata; no network."""
import importlib.util
import os
from pathlib import Path
import tarfile
import unittest

BASE=Path(os.environ["A5_CANDIDATE_PROJECT"]).resolve()
spec=importlib.util.spec_from_file_location('candidate_upstream',BASE/'runtime/upstream.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
ROOT='book-review-app-'+u.COMMIT
LINKS={'backend/node_modules/.bin/bcrypt':'../bcryptjs/bin/bcrypt','backend/node_modules/.bin/mime':'../mime/cli.js','backend/node_modules/.bin/semver':'../semver/bin/semver.js','backend/node_modules/.bin/uuid':'../uuid/dist/bin/uuid'}
def member(path,kind=tarfile.SYMTYPE,target='',size=0):
 m=tarfile.TarInfo(path);m.type=kind;m.linkname=target;m.size=size;return m

class ArchiveCandidateTests(unittest.TestCase):
 def test_exact_links_skipped_only_in_pinned_source_mode(self):
  for p,t in LINKS.items():
   m=member(ROOT+'/'+p,target=t)
   self.assertEqual([],list(u.safe_members([m],strip_root=ROOT)))
   with self.assertRaises(u.VerificationError):list(u.safe_members([m]))
   with self.assertRaises(u.VerificationError):list(u.safe_members([member('other/'+p,target=t)],strip_root='other'))
 def test_rejects_mutated_link_metadata(self):
  p,t=next(iter(LINKS.items()))
  for m in [member(ROOT+'/'+p,target=t+'x'),member(ROOT+'/'+p+'x',target=t),member(ROOT+'/'+p,tarfile.LNKTYPE,t),member(ROOT+'/'+p,target=t,size=1),member(ROOT+'/'+p,target=t,size=-1),member(ROOT+'/'+p,tarfile.FIFOTYPE,t)]:
   with self.subTest(name=m.name,type=m.type,target=m.linkname,size=m.size),self.assertRaises(u.VerificationError):list(u.safe_members([m],strip_root=ROOT))
 def test_rejects_raw_normalization_traversal_and_absolute(self):
  p,t=next(iter(LINKS.items()))
  for raw in [ROOT+'//'+p,ROOT+'/./'+p,ROOT+'/../'+p,'/'+ROOT+'/'+p,ROOT+'/bad\\name',ROOT+'/bad\nname',ROOT+'/bad//file',ROOT+'/bad/./file']:
   with self.subTest(raw=raw),self.assertRaises(u.VerificationError):list(u.safe_members([member(raw,target=t)],strip_root=ROOT))
 def test_count_duplicate_size_and_sparse_guards_apply(self):
  p,t=next(iter(LINKS.items()));m=member(ROOT+'/'+p,target=t)
  for entries,opts in [([m,m],{}),([m],{'max_count':0}),([m,member(ROOT+'/'+p,tarfile.REGTYPE)],{}),([member(ROOT+'/x',tarfile.REGTYPE,size=3)],{'max_file':2}),([member(ROOT+'/x',tarfile.REGTYPE,size=3)],{'max_total':2})]:
   with self.subTest(opts=opts),self.assertRaises(u.VerificationError):list(u.safe_members(entries,strip_root=ROOT,**opts))
  m.sparse=[]
  with self.assertRaises(u.VerificationError):list(u.safe_members([m],strip_root=ROOT))
 def test_archive_root_directory_allowed_but_file_denied(self):
  self.assertEqual('.',list(u.safe_members([member(ROOT,tarfile.DIRTYPE)],strip_root=ROOT))[0][0])
  with self.assertRaises(u.VerificationError):list(u.safe_members([member(ROOT,tarfile.REGTYPE)],strip_root=ROOT))
 def test_real_archive_exact_selected_hashes_no_links_or_bundled_code(self):
  lock=u.load_lock(BASE/'source-lock.json')
  selected=u.verify_source(Path(os.environ['A5_SOURCE_ARCHIVE']).read_bytes(),lock)
  self.assertEqual(set(lock['files']),set(selected))
  for p,value in selected.items():
   self.assertEqual(lock['files'][p],u.digest(value))
   self.assertNotIn('node_modules',Path(p).parts)
   self.assertFalse(any(part.startswith('.env') for part in Path(p).parts))
 def test_hash_failure_precedes_tar_parse(self):
  from unittest.mock import patch
  with patch.object(u.tarfile,'open') as parse,self.assertRaises(u.VerificationError):u.verify_source(b'bad',u.load_lock(BASE/'source-lock.json'))
  parse.assert_not_called()
if __name__=='__main__':unittest.main()
