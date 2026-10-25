import hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verification import temporary_video,verified_response_sha
class VerificationTests(unittest.TestCase):
 def test_served_document_must_match_output_bytes(self):
  class Response:
   status=200
   def body(self):return b'actual served build'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'page.html';p.write_bytes(b'other build')
   with self.assertRaisesRegex(ValueError,'different HTML'):verified_response_sha(Response(),p)
   p.write_bytes(Response().body());self.assertEqual(verified_response_sha(Response(),p),hashlib.sha256(p.read_bytes()).hexdigest())
 def test_interrupted_render_preserves_old_artifact(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'demo.mp4';p.write_bytes(b'old verified video')
   with self.assertRaises(RuntimeError):
    with temporary_video(p) as pending:
     pending.write_bytes(b'incomplete new render');raise RuntimeError('render failed')
   self.assertEqual(p.read_bytes(),b'old verified video');self.assertEqual(list(Path(d).iterdir()),[p])
