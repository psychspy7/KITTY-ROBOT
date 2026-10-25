import importlib.util,json,threading,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import tempfile
SPEC=importlib.util.spec_from_file_location('studio_server',Path(__file__).resolve().parents[1]/'server.py');M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
class ServerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();Path(self.tmp.name,'PROMETHEUS-MISSION-STUDIO.html').write_text('<h1>Studio fixture</h1>');self.server=M.create_server(self.tmp.name,'fixture-model');self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.url=f'http://127.0.0.1:{self.server.server_port}';self.info=self.get('/api/info')[1]
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def get(self,path,headers=None):
  try:
   with urlopen(Request(self.url+path,headers=headers or {})) as r:return r.status,json.loads(r.read()) if path=='/api/info' else r.read()
  except HTTPError as e:return e.code,e.read()
 def post(self,data,headers=None):
  h={'Origin':self.url,'Content-Type':'application/json','X-Studio-Token':self.info['token']};h.update(headers or {})
  raw=data if isinstance(data,bytes) else json.dumps(data).encode();request=Request(self.url+'/api/brain',data=raw,headers=h,method='POST')
  try:
   with urlopen(request) as r:return r.status,json.loads(r.read())
  except HTTPError as e:return e.code,json.loads(e.read())
 def payload(self):return {'text':'What do you see?','prompt':'Use simulator observations truthfully.','observation':{'mode':'IDLE','reason':'fixture','front_m':1.2,'rear_m':None,'prototype':True}}
 def test_root_and_identity(self):
  self.assertEqual(self.get('/')[0],200);self.assertFalse(self.info['physical_outputs']);self.assertEqual(self.info['service'],'prometheus-mission-studio');self.assertEqual(len(self.info['token']),48)
 def test_path_traversal_not_served(self):self.assertEqual(self.get('/../server.py')[0],404)
 def test_foreign_host_rejected(self):self.assertEqual(self.get('/api/info',{'Host':'outside.example'})[0],403)
 def test_foreign_origin_rejected_before_model(self):self.assertEqual(self.post(self.payload(),{'Origin':'https://outside.example'})[0],403)
 def test_wrong_token_rejected(self):self.assertEqual(self.post(self.payload(),{'X-Studio-Token':'bad'})[0],403)
 def test_oversize_body_rejected(self):self.assertEqual(self.post(b'x'*16001)[0],413)
 def test_invalid_json_and_nonfinite_range(self):
  self.assertEqual(self.post(b'not json')[0],400);d=self.payload();d['observation']['front_m']=float('nan');self.assertEqual(self.post(d)[0],400)
 def test_only_explicit_simulated_observations_accepted(self):d=self.payload();d['observation']['prototype']=False;self.assertEqual(self.post(d)[0],400)
 def test_configured_adapter_response_is_labelled_not_physical(self):
  response={'reply':'Fixture response from stub model.','intent':'explain','source':'TEST STUB / no inference'}
  with patch.object(M,'model_reply',return_value=response) as fn:
   code,data=self.post(self.payload());self.assertEqual(code,200);self.assertEqual(data,response);fn.assert_called_once();self.assertTrue(fn.call_args.args[3]['prototype'])
 def test_model_unavailability_does_not_execute_an_intent(self):
  with patch.object(M,'model_reply',side_effect=TimeoutError):self.assertEqual(self.post(self.payload())[0],502)
 def test_marker_snapshot_is_bounded_and_forwarded(self):
  data=self.payload();data['observation'].update(sim_time_s=4.5,marker={'valid':True,'age_s':.1,'box':{'x':20,'y':10,'w':12,'h':18}})
  with patch.object(M,'model_reply',return_value={'reply':'fixture','intent':'explain'}) as fn:
   self.assertEqual(self.post(data)[0],200);snapshot=fn.call_args.args[3];self.assertEqual(snapshot['sim_time_s'],4.5);self.assertEqual(snapshot['marker']['box']['x'],20)
   data['observation']['marker']['box']['x']=319;self.assertEqual(self.post(data)[0],400)
 def test_concurrent_inference_is_bounded(self):
  entered=threading.Event();release=threading.Event();results=[]
  def slow(*args):entered.set();release.wait(3);return {'reply':'fixture','intent':'explain'}
  with patch.object(M,'model_reply',side_effect=slow):
   worker=threading.Thread(target=lambda:results.append(self.post(self.payload())));worker.start()
   try:self.assertTrue(entered.wait(2));self.assertEqual(self.post(self.payload())[0],503)
   finally:release.set();worker.join()
   self.assertEqual(results[0][0],200)
 def test_model_contract_rejects_unbounded_action(self):
  class R:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):return json.dumps({'message':{'content':'{"reply":"bad", "intent":"run arbitrary motor script"}'}}).encode()
  with patch.object(M,'urlopen',return_value=R()):
   with self.assertRaises(ValueError):M.model_reply('fixture','text','prompt',{'prototype':True})
if __name__=='__main__':unittest.main(verbosity=2)
