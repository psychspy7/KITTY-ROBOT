"""Verify the delivered offline HTML over an internal HTTP transport."""
from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import http.server
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
VIEWS=('iso','front','rear','side','inside','joint')


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--browser-executable',required=True)
    args=parser.parse_args();out=args.directory.resolve()
    geometry=json.loads((ROOT/'checks/last-verified.json').read_text())
    volume_reduction=f"{geometry['optimization']['total_printed_solid_volume_mm3']['reduction_percent']:.2f}%"
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(out)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin=f'http://127.0.0.1:{server.server_port}/';url=origin+'KITTY-V3-REVIEW.html'
    report={'revision':geometry['revision'],'transport':'internal HTTP; managed cloud browser file navigation is restricted','checks':[],'external_requests':[],'page_errors':[]}

    def track(page):
        page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
        page.on('request',lambda r:report['external_requests'].append(r.url) if not r.url.startswith(('data:',origin)) else None)

    def saved(page,name):
        page.locator('label[for="view-'+name+'"]').click()
        assert page.locator('.stage figure:visible').count()==1,name
        assert page.locator('.stage .'+name).is_visible(),name
        assert page.locator('.stage .'+name+' img').evaluate('(i)=>i.complete&&i.naturalWidth===1200'),name

    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=args.browser_executable,headless=True)
            context=browser.new_context(java_script_enabled=False,viewport={'width':1440,'height':1000})
            page=context.new_page();track(page);page.goto(url);page.wait_for_load_state('load')
            for name in VIEWS:saved(page,name)
            saved(page,'iso');page.screenshot(path=str(out/'review-no-javascript.png'),full_page=True)
            report['checks'].append('JavaScript disabled: six native saved-view controls and embedded images passed')
            context.close()
            context=browser.new_context(viewport={'width':1440,'height':1000})
            page=context.new_page();track(page);page.goto(url);page.wait_for_load_state('load')
            assert page.locator('.stage .iso').is_visible() and page.locator('#canvas').is_hidden()
            assert page.locator('.metrics').is_visible() and volume_reduction in page.locator('.metrics').inner_text()
            assert page.locator('.metrics tbody tr').count()==3
            page.locator('#enable3d').click();page.wait_for_timeout(500)
            assert page.locator('#review').evaluate("e=>e.classList.contains('interactive')"),page.locator('#state').inner_text()
            assert page.locator('#canvas').evaluate('''c=>{const g=c.getContext('webgl');const p=new Uint8Array(c.width*c.height*4);g.readPixels(0,0,c.width,c.height,g.RGBA,g.UNSIGNED_BYTE,p);let n=0;for(let i=0;i<p.length;i+=4)if(p[i]>80&&p[i+1]>80)n++;return n>10000}''')
            before=page.locator('#canvas').screenshot()
            b=page.locator('#canvas').bounding_box();page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);page.mouse.down();page.mouse.move(b['x']+b['width']/2+120,b['y']+b['height']/2+45,steps=8);page.mouse.up();page.wait_for_timeout(200)
            after=page.locator('#canvas').screenshot();assert hashlib.sha256(before).digest()!=hashlib.sha256(after).digest()
            page.locator('#zoomIn').click();page.locator('#reset').click();page.locator('#canvas').press('ArrowRight');page.locator('#canvas').press('Home')
            page.screenshot(path=str(out/'review-interactive.png'),full_page=True)
            saved(page,'joint');assert page.locator('#canvas').is_hidden()
            mesh=base64.b64decode(page.locator('#mesh-data').text_content())
            assert mesh==(ROOT/'STL/v3_complete_draft.stl').read_bytes()
            report['checks'].append('Desktop: first-paint image, comparison table, real WebGL pixels, orbit, zoom/reset, keyboard controls, saved-view return and exact embedded mesh passed')
            context.close()
            context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            page=context.new_page();track(page);page.goto(url)
            for name in VIEWS:saved(page,name)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            saved(page,'iso');page.screenshot(path=str(out/'review-mobile.png'),full_page=True)
            page.locator('#enable3d').click();page.wait_for_timeout(300);assert page.locator('#review').evaluate("e=>e.classList.contains('interactive')")
            saved(page,'side');report['checks'].append('Mobile 390x844: six saved views, no horizontal overflow, opt-in 3D and saved-view return passed')
            context.close()
            for failure,script in [
                ('context initialization',"const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){if(kind==='webgl')throw Error('simulated context failure');return original.call(this,kind,...args)}"),
                ('asynchronous drawing',"WebGLRenderingContext.prototype.drawArrays=function(){throw Error('simulated drawing failure')}"),
            ]:
                context=browser.new_context();page=context.new_page();track(page);page.add_init_script(script);page.goto(url);page.locator('#enable3d').click();page.wait_for_timeout(250)
                assert page.locator('.stage .iso').is_visible() and page.locator('#canvas').is_hidden();saved(page,'joint')
                report['checks'].append('Throwing '+failure+': saved-image fallback and controls passed')
                context.close()
            browser.close()
            browser=p.chromium.launch(executable_path=args.browser_executable,headless=True,args=['--disable-webgl'])
            page=browser.new_page();track(page);page.goto(url);page.locator('#enable3d').click();assert page.locator('.stage .iso').is_visible();saved(page,'side')
            report['checks'].append('WebGL disabled: saved image stays visible and controls work')
            page.goto(origin+'KITTY-V3-SAVED-VIEWS.html');assert page.locator('#enable3d').is_hidden()
            for name in VIEWS:saved(page,name)
            assert not page.locator('#mesh-data').text_content().strip()
            report['checks'].append('Smaller image-only file: six views passed without WebGL or mesh data')
            browser.close()
        assert not report['external_requests'] and not report['page_errors'],report
        report['HTML_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.html')}
        (out/'REVIEW-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        server.shutdown();server.server_close()


if __name__=='__main__':main()
