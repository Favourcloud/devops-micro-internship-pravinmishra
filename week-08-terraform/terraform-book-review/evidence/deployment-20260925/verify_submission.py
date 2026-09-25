"""Read-only current submission/evidence checks; not live cloud or grading proof."""
from pathlib import Path
import hashlib,json,re,unittest
D=Path(__file__).resolve().parent
P=D.parents[1]
W=D.parents[2]
R=D.parents[3]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class SubmissionEvidence(unittest.TestCase):
 def test_original_a5_requirements_and_questions_remain(self):
  old=(D/'historical-predeployment-brief.md').read_text();new=(W/'assignment-05-deploy-book-review-app-in-your-favorite-cloud-agentic-terraform-project.md').read_text()
  self.assertEqual(digest(D/'historical-predeployment-brief.md'),'9d1dd03a3ab3412d1f45c4806d7a3c585952f0053fea41febce0738734797dd2')
  for pattern,count in [(r'^### Screenshot \d+ — .+$',28),(r'^### \d+\. .+$',15),(r'^# Task \d+ — .+$',11)]:
   self.assertEqual(re.findall(pattern,old,re.M),re.findall(pattern,new,re.M));self.assertEqual(len(re.findall(pattern,new,re.M)),count)
  checks=lambda s:re.findall(r'^- \[[ x]\] (.+)$',s,re.M)
  self.assertEqual(checks(old),checks(new));self.assertEqual(len(checks(new)),55)
  for phrase in ['Add your screenshot here.','Write your answer here.','Add your LinkedIn post URL here']:self.assertNotIn(phrase,new)
  self.assertIn('AI-assisted reflection disclosure',new)
 def test_original_captured_source_is_preserved(self):
  r=json.loads((P/'evidence/reviewed-source.json').read_text())
  protected={k:v for k,v in r['source_sha256'].items() if k not in r['permitted_evidence_exceptions']}
  self.assertEqual(len(protected),59)
  for n,h in protected.items():self.assertEqual(digest(P/n),h,n)
 def test_new_original_captures_and_records_match_hashes(self):
  rows=json.loads((D/'capture-provenance.json').read_text());self.assertEqual({r['slot'] for r in rows},{9,10,11,12,13,18,19,20,21,22,23,24,25});self.assertEqual(len(rows),13)
  for r in rows:
   self.assertEqual(digest(D/r['path']),r['sha256']);self.assertFalse(r['image_pixels_modified'])
   if r.get('snapshot'):self.assertEqual(digest(D/r['snapshot']),r['source_sha256'])
 def test_deployed_release_matches_export_provenance(self):
  release=P/'releases/2026-09-25-aws';r=json.loads((release/'source-provenance.json').read_text())
  self.assertEqual(len(r['file_sha256']),47)
  for n,h in r['file_sha256'].items():self.assertEqual(digest(release/n),h,n)
  for f in release.rglob('*'):
   if f.is_file():self.assertNotRegex(f.name,r'tfstate|tfplan|private|^terraform\.tfvars(?:\.json)?$')
 def test_actual_results_keep_their_limits(self):
  for name in ['api-e2e-result.json','browser-e2e-result.json','database-evidence.json','recovery-evidence.json','final-python-tests.json']:self.assertEqual(json.loads((D/name).read_text())['status'],'passed')
  recovery=json.loads((D/'recovery-evidence.json').read_text());self.assertFalse(recovery['az_change_observed']);self.assertIn('not a full AZ outage',recovery['limitation'])
  review=json.loads((D/'bedrock-final-architecture-review.result.json').read_text());self.assertEqual(review['tool_calls'],0);self.assertEqual(review['subtype'],'success');self.assertTrue((D/'final-review-followup.md').is_file())
 def test_publications_and_original_published_views(self):
  pub=W/'publication';r=json.loads((pub/'publication.json').read_text());self.assertTrue(r['linkedin'].startswith('https://www.linkedin.com/posts/'));self.assertTrue(r['blog'].startswith('https://medium.com/@rosenaefavour/'));self.assertTrue(r['blog_exact_dmi_backlink_verified']);self.assertEqual(r['linkedin_uploaded_proof_images'],5)
  row=next(x for x in (R/'README.md').read_text().splitlines() if x.startswith('| 08 |'));self.assertIn(r['linkedin'],row);self.assertIn(r['blog'],row)
  for name in ['assignment-04-deploy-epicbook-application-on-aws-using-terraform.md','assignment-05-deploy-book-review-app-in-your-favorite-cloud-agentic-terraform-project.md','assignment-06-ai-assisted-terraform-drift-and-policy-review.md']:
   text=(W/name).read_text();self.assertIn(r['linkedin'],text);self.assertNotIn('Add your LinkedIn post URL here',text)
  for item in json.loads((pub/'capture-provenance.json').read_text()):self.assertEqual(digest(pub/item['file']),item['sha256']);self.assertFalse(item['image_pixels_modified'])
  a6=(W/'assignment-06-ai-assisted-terraform-drift-and-policy-review.md').read_text();self.assertIn('- [ ] Performed any infrastructure-changing action manually',a6)
if __name__=='__main__':unittest.main()
