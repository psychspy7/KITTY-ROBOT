"""Real browser integration checks against the delivered standalone HTML."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

def check_zero_range_rays(page):
    saved=page.evaluate('kittyLab.snapshot().project')
    saved['obstacles']=[{'x':0,'z':140,'w':80,'d':80}]
    page.evaluate('(p)=>kittyLab.load(p)',saved)
    page.wait_for_function("kittyLab.snapshot().runtime.ranges?.front===79 && kittyLab.sensorRayPositions('front')[11]===180")
    previous=page.evaluate("kittyLab.sensorRayPositions('front')")
    saved['obstacles']=[{'x':0,'z':250,'w':100,'d':100}]
    page.evaluate('(p)=>kittyLab.load(p)',saved)
    page.wait_for_function('kittyLab.snapshot().runtime.ranges?.front===0')
    page.wait_for_function("previous=>JSON.stringify(kittyLab.sensorRayPositions('front'))!==JSON.stringify(previous)",arg=previous)
    positions=page.evaluate("kittyLab.sensorRayPositions('front')")
    assert len(positions)==18,positions
    for start in range(0,18,6):
        assert positions[start:start+3]==positions[start+3:start+6],positions

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--browser',default='/usr/bin/chromium');args=ap.parse_args()
    out=args.directory.resolve();file=out/'KITTY-ASSEMBLY-LAB.html';html=file.read_text();report={'html_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'checks':[],'errors':[],'external_requests':[],'transport':'exact final HTML via set_content, offline Chromium software WebGL; no user GPU claim'}
    def record(text):
        report['checks'].append(text)
        print(text,flush=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.browser,headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
        def page_for(**opts):
            context=browser.new_context(offline=True,accept_downloads=True,**opts);page=context.new_page();page.set_default_timeout(30000)
            page.on('pageerror',lambda e:report['errors'].append(str(e)))
            page.on('request',lambda r:report['external_requests'].append(r.url) if not r.url.startswith(('data:','blob:')) else None)
            return context,page
        ctx,p=page_for(viewport={'width':1440,'height':1000})
        p.set_content(html,wait_until='load');p.wait_for_function('window.kittyLab?.snapshot().ready',timeout=60000);p.locator('#quality').select_option('eco');p.wait_for_timeout(400)
        snap=lambda:p.evaluate('kittyLab.snapshot()')
        assert snap()['parts']==39,snap()['parts']
        assert not snap()['runtime']['armed']
        count=p.locator('#viewport').evaluate('''c=>{const g=c.getContext('webgl2')||c.getContext('webgl'),v=new Uint8Array(c.width*c.height*4);g.readPixels(0,0,c.width,c.height,g.RGBA,g.UNSIGNED_BYTE,v);let n=0;for(let i=0;i<v.length;i+=4)if(v[i]>120&&v[i+1]>110&&v[i+2]>90)n++;return n;}''')
        assert count>10000,count
        p.screenshot(path=str(out/'lab-assembly-desktop.png'))
        record('Real offline WebGL pixels, 39 selectable parts, initial disarm and desktop layout')
        p.locator('[data-part=v7_motor_left]').click();p.locator('#detach').click();assert not snap()['project']['placements']['v7_motor_left']['attached'];p.locator('#attach').click()
        p.locator('#offset-x').fill('12');p.locator('#offset-x').dispatch_event('change');assert snap()['project']['placements']['v7_motor_left']['offset'][0]==12;p.locator('#attach').click()
        p.locator('#rotate').click();assert snap()['project']['placements']['v7_motor_left']['rotation']==15;p.locator('#attach').click()
        p.locator('[data-part=motorL]').click();p.locator('#focus').click();p.locator('#drag-part').click();p.wait_for_timeout(300)
        point=p.evaluate("kittyLab.screenPoint('motorL')");p.mouse.move(point['x'],point['y']);p.mouse.down();p.mouse.move(point['x']+45,point['y']+12,steps=8);p.mouse.up()
        assert snap()['project']['placements']['motorL']['offset']!=[0,0,0],snap()['project']['placements']['motorL'];p.locator('#attach').click();p.locator('#drag-part').click()
        p.locator('#exercise').click();assert sum(v['attached'] for v in snap()['project']['placements'].values())==1;p.locator('#next-step').click();assert snap()['selected']=='v7_motor_left';p.locator('#assemble-all').click();p.locator('#view-iso').click()
        record('Detach/attach, typed offsets, rotate/reset, real pointer part drag, guided assembly exercise and full assembly')
        p.locator('[data-mode=wire]').click();p.locator('#wire-a').select_option('usb.V5');p.locator('#wire-b').select_option('esp.V5');p.locator('#connect').click();assert len(snap()['project']['wires'])==1
        p.locator('#clear-wires').click();p.locator('[data-part=esp]').click();p.locator('#pin-buttons').get_by_role('button',name='D25',exact=True).click();assert snap()['pending']=='esp.D25'
        p.locator('[data-part=driver]').click();p.locator('#pin-buttons').get_by_role('button',name='PWMA',exact=True).click();assert snap()['project']['wires']==[{'a':'esp.D25','b':'driver.PWMA'}]
        p.locator('#demo').click();assert len(snap()['project']['wires'])==31;assert p.locator('#check-badge').inner_text()=='MODEL READY'
        p.locator('details').filter(has=p.locator('#meter')).locator('summary').click();assert p.locator('#meter').inner_text()=='6.000 V DC'
        p.locator('#probe-red').select_option('divF.OUT');assert p.locator('#meter').inner_text()=='2.963 V DC'
        p.locator('#wire-a').select_option('front.ECHO');p.locator('#wire-b').select_option('esp.D33');p.locator('#connect').click();assert 'ISSUES' in p.locator('#check-badge').inner_text();p.locator('#demo').click()
        p.screenshot(path=str(out/'lab-wiring-desktop.png'))
        record('Dropdown wires, component pin buttons, nominal 31-wire demo, multimeter and unsafe raw ECHO rejection')
        p.locator('[data-mode=test]').click();p.locator('#chemistry').select_option('nimh');assert '4.80 V' in p.locator('#rail-reading').inner_text();p.locator('#arm').click();assert snap()['runtime']['armed']
        z=snap()['runtime']['pose']['z'];p.keyboard.down('w');p.wait_for_timeout(650);p.keyboard.up('w');p.wait_for_timeout(150);assert snap()['runtime']['pose']['z']<z;assert snap()['runtime']['left']==0
        p.locator('#link-ok').uncheck();assert not snap()['runtime']['armed'];p.locator('#link-ok').check();assert not snap()['runtime']['armed'];p.locator('#arm').click();p.locator('#sensor-ok').uncheck();assert not snap()['runtime']['armed'];p.locator('#sensor-ok').check()
        p.locator('#arm').click();p.locator('#estop').click();assert snap()['runtime']['estop'] and not snap()['runtime']['armed'];p.locator('#reset-stop').click();assert not snap()['runtime']['estop'] and not snap()['runtime']['armed']
        p.locator('#power-switch').uncheck();assert p.locator('#arm').is_disabled();p.locator('#power-switch').check()
        p.locator('#arm').click();p.keyboard.press('Space');assert snap()['runtime']['estop'];p.locator('#reset-stop').click()
        record('AA chemistry, actual keyboard drive/release, link/sensor loss, motor switch and stop latch inhibit and require rearm')
        saved=snap()['project'];saved['obstacles']=[{'x':0,'z':140,'w':80,'d':80}];p.evaluate('(p)=>kittyLab.load(p)',saved);p.locator('#arm').click();z=snap()['runtime']['pose']['z'];p.keyboard.down('w');p.wait_for_timeout(450);assert snap()['runtime']['pose']['z']==z;assert 'Obstacle' in snap()['runtime']['reason'];p.keyboard.up('w')
        saved['obstacles']=[{'x':50,'z':560,'w':80,'d':80}];p.evaluate('(p)=>kittyLab.load(p)',saved);p.locator('#arm').click();p.keyboard.down('s');p.wait_for_timeout(450);p.keyboard.up('s');assert snap()['runtime']['pose']['z']==350
        check_zero_range_rays(p)
        p.locator('#add-obstacle').click();assert len(snap()['project']['obstacles'])==2
        inp=p.locator('#obstacle-editor input').first;inp.fill('140');inp.dispatch_event('change');assert snap()['project']['obstacles'][0]['x']==140
        p.locator('#reset-arena').click();p.wait_for_timeout(250);p.screenshot(path=str(out/'lab-arena-desktop.png'))
        record('Front/rear obstacle range-to-motion guard through real controls, zero-range rendered rays collapse, obstacle creation/editing and arena reset')
        with p.expect_download() as dl:p.locator('#export').click()
        saved=json.loads(Path(dl.value.path()).read_text());assert saved==snap()['project'];assert 'armed' not in saved
        p.locator('#project-file').set_input_files({'name':'project.json','mimeType':'application/json','buffer':json.dumps(saved).encode()});assert snap()['project']==saved and not snap()['runtime']['armed']
        bad={**saved,'wires':[{'a':'esp.FAKE','b':'usb.V5'}]};p.locator('#project-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':json.dumps(bad).encode()});p.wait_for_timeout(200);assert snap()['project']==saved;assert 'Could not open' in p.locator('#toast').inner_text()
        p.locator('#arm').click();p.evaluate("window.dispatchEvent(new Event('blur'))");assert not snap()['runtime']['armed']
        record('Exact JSON download and input-file reopen, rejected corrupt import without mutation, runtime disarm on reopen and blur')
        p.locator('[data-mode=build]').click()
        with p.expect_download() as png:p.locator('#screenshot').click()
        assert Path(png.value.path()).read_bytes().startswith(b'\x89PNG')
        p.locator('#wireframe').click();p.locator('#ghost').uncheck();p.locator('#view-top').click();p.locator('#view-iso').click();p.locator('#wireframe').click();p.locator('#ghost').check()
        p.locator('[data-mode=test]').click();p.locator('#arm').click()
        p.evaluate("window.testContext=(document.getElementById('viewport').getContext('webgl2')||document.getElementById('viewport').getContext('webgl')).getExtension('WEBGL_lose_context');testContext.loseContext()")
        p.wait_for_function('!kittyLab.snapshot().ready');assert not snap()['runtime']['armed'];assert p.locator('#fallback').is_visible();assert p.locator('#drive-state').inner_text()=='DISARMED'
        p.evaluate('testContext.restoreContext()');p.wait_for_function('kittyLab.snapshot().ready',timeout=60000);assert not snap()['runtime']['armed'];assert len(snap()['project']['wires'])==31
        record('PNG download, rendering controls and actual WebGL loss/restore preserve project and disarm')
        ctx.close()
        ctx,p=page_for(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        p.set_content(html,wait_until='load');p.wait_for_function('window.kittyLab?.snapshot().ready',timeout=60000);p.locator('#quality').select_option('eco');p.wait_for_timeout(300)
        assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        p.locator('[data-mode=wire]').click();p.locator('#demo').click();assert p.locator('#check-badge').inner_text()=='MODEL READY'
        p.locator('[data-mode=test]').click();p.locator('#arm').click();assert p.evaluate('kittyLab.snapshot().runtime.armed');p.locator('#estop').click();assert not p.evaluate('kittyLab.snapshot().runtime.armed');p.screenshot(path=str(out/'lab-mobile.png'),full_page=True);ctx.close()
        record('390 px touch layout without horizontal overflow; wire demo, arm and stop controls usable')
        ctx,p=page_for(viewport={'width':1200,'height':900})
        p.evaluate("()=>{const old=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,...a){return /webgl/i.test(t)?null:old.call(this,t,...a)}}")
        p.set_content(html,wait_until='load');assert p.locator('#fallback img').is_visible();assert not p.evaluate('kittyLab.snapshot().ready')
        p.locator('[data-mode=wire]').click();p.locator('#demo').click();assert p.locator('#check-badge').inner_text()=='MODEL READY';p.locator('[data-mode=test]').click();assert p.locator('#arm').is_disabled();p.screenshot(path=str(out/'lab-no-webgl.png'));ctx.close()
        ctx,p=page_for(viewport={'width':1200,'height':900},java_script_enabled=False);p.set_content(html,wait_until='load');assert p.locator('#fallback img').is_visible();ctx.close()
        record('WebGL unavailable: image and wiring checks work, motion disabled; JavaScript disabled: saved CAD image visible')
        browser.close()
    assert not report['errors'],report['errors'];assert not report['external_requests'],report['external_requests']
    (out/'BROWSER-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(report['checks']),'errors':report['errors'],'external_requests':report['external_requests']}))
if __name__=='__main__':main()
