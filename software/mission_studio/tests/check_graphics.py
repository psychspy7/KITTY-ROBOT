"""Graphics-loss cancellation cases on the exact released HTML bytes."""
import argparse,hashlib,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from verification import verified_response_sha,atomic_json

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();errors=[];checks=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for case in ['held drive','pending scrub','pending reply']:
   page=browser.new_page(viewport={'width':1100,'height':800});page.on('pageerror',lambda e:errors.append(str(e)+'\n'+str(e.stack)));document=page.context.request.get(a.url);digest=verified_response_sha(document,a.out/'PROMETHEUS-MISSION-STUDIO.html');page.route(a.url,lambda route:route.fulfill(response=document))
   page.route('**/api/info',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'service':'prometheus-mission-studio','model':'TEST STUB','token':'a'*48})))
   page.goto(a.url);page.wait_for_function('()=>PrometheusStudio.state.ready');page.locator('#quality').select_option('1');page.locator('[data-mode="mission"]').click()
   if case=='held drive':
    page.keyboard.down('w');page.wait_for_timeout(100);page.evaluate('()=>{PrometheusStudio.renderer.forceContextLoss();PrometheusStudio.renderNow();}');page.wait_for_timeout(300);assert page.evaluate('PrometheusStudio.sim.speed')==0;assert page.evaluate('PrometheusStudio.sim.mode')=='PAUSED'
   elif case=='pending scrub':
    page.evaluate('async()=>{const work=PrometheusStudio.seek(115);setTimeout(()=>PrometheusStudio.renderer.forceContextLoss(),0);await work;}');page.wait_for_timeout(100);assert page.evaluate('PrometheusStudio.state.demoTime')<115;assert page.evaluate('PrometheusStudio.sim.speed')==0
   else:
    page.wait_for_function('()=>document.getElementById("brain-mode").textContent.includes("CONFIGURED")');page.evaluate('()=>{window.fetch=()=>new Promise(resolve=>{window.__reply=resolve;});}');page.locator('#chat-input').fill('go to marker');page.locator('#send-chat').click();page.wait_for_function('()=>!!window.__reply');page.evaluate('()=>{PrometheusStudio.renderer.forceContextLoss();PrometheusStudio.renderNow();}');page.wait_for_timeout(100);page.evaluate('()=>window.__reply(new Response(JSON.stringify({reply:"late fixture",intent:"goal_alpha"})))');page.wait_for_timeout(100);assert page.evaluate('PrometheusStudio.sim.goal') is None;assert page.evaluate('PrometheusStudio.sim.speed')==0
   assert not page.evaluate('PrometheusStudio.state.ready');checks.append(case+' cancelled by actual graphics loss');page.close()
  browser.close()
 assert not errors,errors
 record={'evidence_kind':'real Chromium forced WebGL loss; inference explicitly stubbed; no physical devices','passed':len(checks),'checks':checks,'html_sha256':digest,'served_html_sha256':digest,'input_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['tests/check_graphics.py','verification.py']},'page_errors':errors};atomic_json(a.out/'GRAPHICS-VERIFICATION.json',record);print(json.dumps(record,indent=2))
if __name__=='__main__':main()
