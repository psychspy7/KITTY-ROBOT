"""Connect a real rendered marker detection to the virtual FOLLOW controller."""
import argparse,hashlib,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from verification import verified_response_sha,atomic_json

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1100,'height':800});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  document=page.context.request.get(a.url);digest=verified_response_sha(document,a.out/'PROMETHEUS-MISSION-STUDIO.html');page.route(a.url,lambda route:route.fulfill(response=document));page.goto(a.url);page.wait_for_function('PrometheusStudio.state.ready');page.locator('#quality').select_option('1')
  page.evaluate('()=>{PrometheusStudio.setMode("mission");const s=PrometheusStudio.sim;s.pose={x:0,z:.6,yaw:Math.atan2(1.8,1.7)};PrometheusStudio.renderNow();}');page.wait_for_function('PrometheusStudio.sim.vision.valid');before=page.evaluate('({...PrometheusStudio.sim.pose})');page.locator('#follow-marker').click()
  result=page.evaluate('()=>{const s=PrometheusStudio.sim;for(let i=0;i<6;i++){s.step(.05);PrometheusStudio.renderNow();}return {mode:s.mode,pose:s.pose,vision:s.vision};}')
  assert result['mode']=='FOLLOW',result;assert abs(result['pose']['x']-before['x'])+abs(result['pose']['z']-before['z'])>.005
  page.locator('[data-fault="camera"]').check();page.wait_for_function('()=>PrometheusStudio.sim.mode==="FAULT"');assert page.evaluate('PrometheusStudio.sim.speed')==0;assert page.evaluate('PrometheusStudio.sim.latched');b.close()
 assert not errors,errors
 record={'evidence_kind':'actual synthetic RGB detection consumed by virtual camera-follow; no real camera or trained detector','passed':2,'checks':['Rendered-pixel marker permits FOLLOW and measured virtual displacement','Camera-fault UI latches FAULT and zeros virtual speed'],'html_sha256':digest,'served_html_sha256':digest,'input_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['tests/check_follow.py','verification.py']},'page_errors':errors}
 atomic_json(a.out/'FOLLOW-VERIFICATION.json',record);print(json.dumps(record,indent=2))
if __name__=='__main__':main()
