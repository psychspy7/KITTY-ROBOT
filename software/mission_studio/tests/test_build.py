import hashlib,json,re,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
class BuildTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.out=self.root/'out'
 def tearDown(self):self.temp.cleanup()
 def build(self,source=HERE,archive=True):
  cmd=[sys.executable,str(source/'build_release.py'),'--out',str(self.out)]
  if archive:cmd.append('--archive')
  return subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 def test_standalone_has_embedded_assets_and_no_external_scripts(self):
  self.build();page=(self.out/'PROMETHEUS-MISSION-STUDIO.html').read_text();self.assertNotRegex(page,r'<script[^>]+src=');self.assertIn('data:image/png;base64,',page);self.assertIn('SOFTWARE PROTOTYPE',page);self.assertIn('CONCEPT ANIMATION',page);self.assertNotRegex(page,r'__(?:STYLE|MODEL|ORBIT|CORE|APP|PROMPT|FALLBACK)__')
 def test_portable_source_rebuild_is_exact(self):
  self.build();original=(self.out/'PROMETHEUS-MISSION-STUDIO.html').read_bytes()
  with zipfile.ZipFile(self.out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip') as z:z.extractall(self.root/'extracted')
  self.build(self.root/'extracted/source');self.assertEqual(original,(self.out/'PROMETHEUS-MISSION-STUDIO.html').read_bytes())
 def test_zip_crc_licenses_launchers_and_captions(self):
  self.build()
  with zipfile.ZipFile(self.out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip') as z:
   self.assertIsNone(z.testzip());names=z.namelist();self.assertIn('source/vendor/THREE-LICENSE.txt',names);self.assertIn('ENGLISH-CAPTIONS.srt',names);self.assertIn('START-WITH-LOCAL-AI.cmd',names);self.assertIn('source/core.js',names);self.assertFalse(any('__pycache__' in n or n.endswith('.stale') for n in names))
 def test_nested_output_rejected(self):
  result=subprocess.run([sys.executable,str(HERE/'build_release.py'),'--out',str(HERE/'test-nested-output')],capture_output=True)
  self.assertNotEqual(result.returncode,0);self.assertFalse((HERE/'test-nested-output').exists())
 def test_stale_browser_claim_is_excluded(self):
  self.build();p=self.out/'BROWSER-VERIFICATION.json';p.write_text(json.dumps({'html_sha256':'0'*64,'passed':999}));self.build();self.assertFalse(p.exists())
  with zipfile.ZipFile(self.out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip') as z:self.assertNotIn('BROWSER-VERIFICATION.json',z.namelist())
 def test_valid_verification_artifact_is_preserved_in_zip(self):
  self.build();p=self.out/'fixture.webm';p.write_bytes(b'verified media fixture');record={'html_sha256':hashlib.sha256((self.out/'PROMETHEUS-MISSION-STUDIO.html').read_bytes()).hexdigest(),'artifact_sha256':{'fixture.webm':hashlib.sha256(p.read_bytes()).hexdigest()}};(self.out/'BROWSER-VERIFICATION.json').write_text(json.dumps(record));self.build()
  with zipfile.ZipFile(self.out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip') as z:self.assertEqual(z.read('fixture.webm'),p.read_bytes())
 def test_changed_video_cannot_reuse_old_verification(self):
  self.build();p=self.out/'demo.mp4';p.write_bytes(b'old');record=self.out/'VIDEO-VERIFICATION.json';record.write_text(json.dumps({'html_sha256':hashlib.sha256((self.out/'PROMETHEUS-MISSION-STUDIO.html').read_bytes()).hexdigest(),'artifact_sha256':{'demo.mp4':hashlib.sha256(p.read_bytes()).hexdigest()}}));p.write_bytes(b'changed');self.build();self.assertFalse(record.exists())
 def test_prompt_is_escaped_and_source_manifest_matches(self):
  self.build();data=json.loads((self.out/'BUILD-PROVENANCE.json').read_text());self.assertFalse(data['physical_outputs']);self.assertFalse(data['cad_geometry_changed']);self.assertEqual(hashlib.sha256((HERE/'core.js').read_bytes()).hexdigest(),data['source_sha256']['core.js']);self.assertIn('source_sha256',data)
  with zipfile.ZipFile(self.out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip') as z:z.extractall(self.root/'escaped')
  source=self.root/'escaped/source';(source/'prompt.txt').write_text('</textarea><script>UNTRUSTED_PROMPT_SENTINEL</script>');self.build(source);page=(self.out/'PROMETHEUS-MISSION-STUDIO.html').read_text();self.assertIn('&lt;/textarea&gt;&lt;script&gt;UNTRUSTED_PROMPT_SENTINEL',page);self.assertNotIn('<script>UNTRUSTED_PROMPT_SENTINEL',page)
if __name__=='__main__':unittest.main(verbosity=2)
