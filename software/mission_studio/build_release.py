"""Build the self-contained studio and portable source archive, without network."""
from __future__ import annotations
import argparse,base64,gzip,hashlib,html,json,re,shutil,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--archive',action='store_true');a=ap.parse_args();out=a.out.resolve()
 if out==HERE or HERE in out.parents:ap.error('Output must be outside the source directory')
 out.mkdir(parents=True,exist_ok=True);vendor=HERE/'vendor'
 if not vendor.exists():vendor=HERE.parents[1]/'design/v7/advanced-viewer/vendor'
 provenance=json.loads((HERE/'assets/provenance.json').read_text(encoding='utf-8'))
 for n,h in provenance['assets_sha256'].items():assert sha(HERE/'assets'/n)==h,n
 model=json.loads(gzip.decompress((HERE/'assets/model.json.gz').read_bytes()));assert len(model['parts'])==28 and not model['physicalFitVerified']
 three=(vendor/'three.min.js').read_text(encoding='utf-8');orbit=(vendor/'OrbitControls.js').read_text(encoding='utf-8');orbit=re.sub(r'import\s*\{([\s\S]*?)\}\s*from\s*[\'"]three[\'"];',r'const {\1} = THREE;',orbit,count=1);orbit=re.sub(r'export\s*\{\s*OrbitControls\s*\};?','window.OrbitControls = OrbitControls;',orbit)
 prompt=(HERE/'prompt.txt').read_text(encoding='utf-8');page=(HERE/'index.html.in').read_text(encoding='utf-8');values={'__STYLE__':(HERE/'style.css').read_text(encoding='utf-8'),'__MODEL__':json.dumps(model,separators=(',',':')),'__THREE__':three,'__ORBIT__':orbit,'__CORE__':(HERE/'core.js').read_text(encoding='utf-8'),'__APP__':(HERE/'app.js').read_text(encoding='utf-8'),'__PROMPT__':html.escape(prompt),'__FALLBACK__':'data:image/png;base64,'+base64.b64encode((HERE/'assets/chassis.png').read_bytes()).decode()}
 for key,value in values.items():
  if key not in ['__STYLE__','__PROMPT__','__FALLBACK__']:value=value.replace('</script','<\\/script')
  page=page.replace(key,value)
 assert not re.search(r'__(?:STYLE|MODEL|ORBIT|CORE|APP|PROMPT|FALLBACK)__',page)
 target=out/'PROMETHEUS-MISSION-STUDIO.html';target.write_text(page, encoding='utf-8',newline='\n')
 for record in out.glob('*VERIFICATION.json'):
  value=json.loads(record.read_text(encoding='utf-8'));current=bool(value.get('html_sha256') or value.get('input_sha256'))
  if value.get('html_sha256') and value['html_sha256']!=sha(target):current=False
  for name,digest in value.get('input_sha256',{}).items():
   f=(HERE/name).resolve();current=current and HERE in f.parents and f.is_file() and sha(f)==digest
  for name,digest in value.get('artifact_sha256',{}).items():
   f=(out/name).resolve();current=current and out in f.parents and f.is_file() and sha(f)==digest
  if not current:record.replace(record.with_suffix('.json.stale'))
 for name in ['README.md','prompt.txt','server.py','launch_ai.py','PRESENTATION-SCRIPT.md','ENGLISH-CAPTIONS.srt']:
  if (HERE/name).exists():shutil.copyfile(HERE/name,out/('START-HERE.md' if name=='README.md' else name))
 # The server reads this generated HTML beside itself. Windows launcher is local.
 (out/'START-STUDIO-WINDOWS.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\npy -3 server.py\r\npause\r\n', encoding='utf-8',newline='\n')
 (out/'START-WITH-LOCAL-AI.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\npy -3 launch_ai.py\r\npause\r\n', encoding='utf-8',newline='\n')
 files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 evidence={'html_sha256':sha(target),'html_bytes':target.stat().st_size,'source_sha256':{str(p.relative_to(HERE)):sha(p) for p in files},'cad_geometry_changed':False,'physical_outputs':False,'trained_detector_bundled':False,'flight_model':'scripted concept animation; no aerodynamics','runtime':'browser CPU/GPU; no CDN or mandatory AI service'}
 (out/'BUILD-PROVENANCE.json').write_text(json.dumps(evidence,indent=2)+'\n', encoding='utf-8',newline='\n')
 if a.archive:
  with zipfile.ZipFile(out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip','w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
   for n in ['PROMETHEUS-MISSION-STUDIO.html','START-HERE.md','prompt.txt','server.py','START-STUDIO-WINDOWS.cmd','START-WITH-LOCAL-AI.cmd','launch_ai.py','PRESENTATION-SCRIPT.md','ENGLISH-CAPTIONS.srt','BUILD-PROVENANCE.json']:
    if (out/n).exists():z.write(out/n,n)
   for p in files:z.write(p,'source/'+str(p.relative_to(HERE)))
   if vendor.parent!=HERE:
    for p in vendor.iterdir():
     if p.is_file():z.write(p,'source/vendor/'+p.name)
   for p in out.glob('*VERIFICATION.json'):
    z.write(p,p.name)
    for name in json.loads(p.read_text(encoding='utf-8')).get('artifact_sha256',{}):
     artifact=(out/name).resolve()
     if out in artifact.parents and artifact.is_file() and name not in z.namelist():z.write(artifact,name)
  with zipfile.ZipFile(out/'PROMETHEUS-MISSION-STUDIO-COMPLETE.zip') as z:assert z.testzip() is None
 print(json.dumps({'html':str(target),'bytes':target.stat().st_size,'sha256':sha(target)}))
if __name__=='__main__':main()
