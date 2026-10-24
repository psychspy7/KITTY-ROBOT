"""Exercise the delivered self-contained HTML with real Chromium graphics."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright


def settled(page):
    page.wait_for_function('''()=>{const n=kittyViewer.info().drawn;
      if(window.lastDrawCount!==n){window.lastDrawCount=n;window.lastDrawAt=performance.now();return false;}
      return performance.now()-window.lastDrawAt>1000;}''',timeout=30000)


def pixel_difference(before, after):
    difference=ImageChops.difference(Image.open(io.BytesIO(before)).convert('RGB'),
                                    Image.open(io.BytesIO(after)).convert('RGB'))
    return sum(ImageStat.Stat(difference).mean)/3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--browser', default='/usr/bin/chromium')
    parser.add_argument('--dual-ultrasonic', action='store_true')
    args = parser.parse_args(); out = args.directory.resolve()
    filename = 'KITTY-V7.1-DUAL-ULTRASONIC-3D-STUDIO.html' if args.dual_ultrasonic else 'KITTY-V7-3D-STUDIO.html'
    total_parts = 28 if args.dual_ultrasonic else 24
    visible_parts = total_parts - 2
    production_parts = 13 if args.dual_ultrasonic else 12
    html = (out / filename).read_text()
    report = {'checks': [], 'requests': [], 'errors': [], 'transport': 'exact HTML via set_content; browser offline'}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser, headless=True,
                                    args=['--enable-unsafe-swiftshader'])
        def open_page(**kwargs):
            context = browser.new_context(offline=True, accept_downloads=True, **kwargs)
            page = context.new_page()
            page.on('request', lambda r: report['requests'].append(r.url) if not r.url.startswith(('data:','blob:')) else None)
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            return context, page
        context, page = open_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        page.set_content(html, wait_until='load')
        page.wait_for_function('window.kittyViewer && kittyViewer.info().ready', timeout=60000)
        page.wait_for_timeout(500)
        info = page.evaluate('kittyViewer.info()'); assert len(info['visible']) == visible_parts, info
        assert info['drawn'] > 0 and info['triangles'] > 100000
        assert page.locator('#viewport').is_visible() and page.locator('#saved').is_hidden()
        page.screenshot(path=str(out / 'studio-desktop.png'))
        # Pixels must contain a substantial non-background robot region.
        pixels = page.locator('#viewport').evaluate('''c=>{const g=c.getContext('webgl2')||c.getContext('webgl');
          const p=new Uint8Array(c.width*c.height*4);g.readPixels(0,0,c.width,c.height,g.RGBA,g.UNSIGNED_BYTE,p);
          let n=0;for(let i=0;i<p.length;i+=4)if(p[i]>125&&p[i+1]>120&&p[i+2]>100)n++;return n}''')
        assert pixels > 12000, pixels
        report['checks'].append(f'Offline desktop: real WebGL pixels, {total_parts} actual part meshes / {visible_parts} default visible, first-frame render')
        if args.dual_ultrasonic:
            assert 'v7_sensor_bracket' in info['visible'] and 'v7_rear_sensor_bracket' in info['visible']
            page.locator('[data-view=rear]').click();page.wait_for_timeout(150)
            page.screenshot(path=str(out/'studio-dual-rear.png'))
            page.locator('[data-id=v7_rear_sensor_bracket] button').click()
            with page.expect_download() as rear_download:page.locator('#download-part').click()
            rear_path=Path('/workspace/outputs/kitty-robot/v7-dual-ultrasonic/STL_PARTS/v7_rear_sensor_bracket.stl')
            assert Path(rear_download.value.path()).read_bytes()==rear_path.read_bytes()
            page.locator('#reset').click()
            report['checks'].append('Front and rear sensor mounts present; rear view and exact rear-bracket STL download passed')
        # A hidden group filter must never turn isolation into an empty model.
        for selected, setup in [
            ('v7_battery_tray','optional'),
            ('REFERENCE_ONLY_phone_case_envelope','hardware'),
            ('REFERENCE_ONLY_phone_case_envelope','print'),
        ]:
            page.locator('#reset').click()
            if setup=='hardware':page.locator('#hardware').uncheck()
            if setup=='print':page.locator('[data-layout=print]').click()
            page.locator('[data-id="'+selected+'"] button').click()
            page.locator('#isolate').click()
            isolated=page.evaluate('kittyViewer.info()')
            assert isolated['selected']==selected and isolated['visible']==[selected], isolated
        page.locator('#reset').click()
        report['checks'].append('Hidden optional part, disabled reference hardware, and reference selected from print layout all isolate to exactly the selected visible part')
        before = page.evaluate('kittyViewer.info().camera')
        rect = page.locator('#viewport').bounding_box()
        page.mouse.move(rect['x']+rect['width']*.55, rect['y']+rect['height']*.55)
        page.mouse.down(); page.mouse.move(rect['x']+rect['width']*.55+130,rect['y']+rect['height']*.55+45,steps=8);page.mouse.up()
        page.wait_for_timeout(250);assert before != page.evaluate('kittyViewer.info().camera')
        for view in ['front','rear','side','top','bottom','iso']:
            page.locator('[data-view="'+view+'"]').click(); page.wait_for_timeout(70)
        page.locator('#zoom-in').click();page.locator('#zoom-out').click();page.locator('#fit').click()
        page.locator('#viewport').press('ArrowLeft');page.locator('#viewport').press('f')
        report['checks'].append('Real pointer orbit, camera presets, zoom, fit and keyboard controls')
        for mode in ['wire','xray','technical','studio']:
            page.locator('#render-mode').select_option(mode);page.wait_for_timeout(120)
            page.screenshot(path=str(out / ('studio-'+mode+'.png')))
        page.locator('#ghost').check();page.wait_for_timeout(120)
        page.screenshot(path=str(out/'studio-interior.png'))
        page.locator('#ghost').uncheck()
        settled(page);full_model=page.locator('#viewport').screenshot()
        for axis in ['x','y','z']:
            page.locator('#cut-axis').select_option(axis)
            page.locator('#cut').fill('55');page.locator('#cut').dispatch_event('input')
            assert '≤' in page.locator('#cut-value').inner_text()
            settled(page)
            assert pixel_difference(full_model,page.locator('#viewport').screenshot())>.05,axis
            page.locator('#cut').fill('100');page.locator('#cut').dispatch_event('input')
            settled(page)
            assert pixel_difference(full_model,page.locator('#viewport').screenshot())<.15,axis+' restoration'
        page.locator('#cut').fill('55');page.locator('#cut').dispatch_event('input')
        page.screenshot(path=str(out/'studio-section.png'))
        page.locator('#cut').fill('100');page.locator('#cut').dispatch_event('input')
        page.locator('[data-layout=exploded]').click();page.wait_for_timeout(150)
        assert page.evaluate('kittyViewer.info().layout')=='exploded'
        page.locator('#dimensions').check();page.locator('#labels').check()
        page.screenshot(path=str(out/'studio-exploded.png'))
        page.locator('#labels').uncheck();page.locator('#dimensions').uncheck()
        page.locator('[data-layout=print]').click();page.wait_for_timeout(120)
        assert len(page.evaluate('kittyViewer.info().visible'))==production_parts
        page.screenshot(path=str(out/'studio-parts.png'))
        page.locator('[data-layout=assembly]').click();page.locator('#optional').check()
        assert len(page.evaluate('kittyViewer.info().visible'))==total_parts
        page.locator('#optional').uncheck();page.locator('#hardware').uncheck()
        assert len(page.evaluate('kittyViewer.info().visible'))==production_parts
        page.locator('#hardware').check()
        report['checks'].append('Surface modes, ghost shell, XYZ cuts, exploded/print layouts, optional and purchased-hardware filters, dimensions and labels')
        page.locator('[data-id=v7_tail] button').click()
        assert page.evaluate('kittyViewer.info().selected')=='v7_tail'
        page.locator('#focus').click()
        with page.expect_download() as download_info: page.locator('#download-part').click()
        downloaded = Path(download_info.value.path()).read_bytes()
        source = Path('/workspace/outputs/kitty-robot/v7-print-service/STL_PARTS/v7_tail.stl').read_bytes()
        assert downloaded == source
        page.locator('#isolate').click();assert page.evaluate('kittyViewer.info().visible')==['v7_tail']
        page.locator('#show-all').click();assert len(page.evaluate('kittyViewer.info().visible'))==visible_parts
        page.locator('[data-id=REFERENCE_ONLY_phone_case_envelope] button').click()
        assert page.locator('#download-part').is_hidden()
        page.locator('#reset').click()
        with page.expect_download() as png_info:page.locator('#snapshot').click()
        assert Path(png_info.value.path()).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        for q in ['ultra','eco','auto']:page.locator('#quality').select_option(q)
        page.locator('#rotate').check();camera=page.evaluate('kittyViewer.info().camera')
        page.wait_for_timeout(350);assert camera != page.evaluate('kittyViewer.info().camera')
        page.locator('#rotate').uncheck();page.locator('#reset').click()
        # Damping settles in frames; software WebGL takes longer than a desktop GPU.
        settled(page)
        drawn=page.evaluate('kittyViewer.info().drawn');page.wait_for_timeout(350)
        assert page.evaluate('kittyViewer.info().drawn')==drawn, 'Idle renderer did not settle'
        report['checks'].append('Part selection/focus/isolate/reset, exact original STL download, reference download exclusion, PNG export, quality, turntable and idle rendering suspension')
        page.locator('[data-id=v7_tail] button').click()
        page.evaluate('''()=>{const c=document.getElementById('viewport');const g=c.getContext('webgl2')||c.getContext('webgl');window.loseTest=g.getExtension('WEBGL_lose_context');window.loseTest.loseContext();}''')
        page.wait_for_function('!kittyViewer.info().ready')
        assert page.locator('#saved').is_visible()
        page.wait_for_timeout(150)
        page.evaluate('window.loseTest.restoreContext()')
        page.wait_for_function('kittyViewer.info().ready',timeout=60000)
        assert page.locator('#viewport').is_visible()
        assert page.evaluate('kittyViewer.info().selected')=='v7_tail'
        assert page.locator('#selection').is_visible() and page.locator('#download-part').is_visible()
        assert page.locator('#selection-title').inner_text()=='Detachable keyed tail'
        report['checks'].append('Real graphics context loss: native saved-view fallback, restored-context recovery and retained selected-part inspection/STL controls')
        context.close()
        context,page = open_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        page.set_content(html,wait_until='load');page.wait_for_function('kittyViewer.info().ready',timeout=60000)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(out/'studio-mobile.png'),full_page=True)
        page.locator('[data-layout=exploded]').click();page.locator('#render-mode').select_option('wire')
        page.locator('#reset').click();context.close()
        report['checks'].append('Mobile 390×844: GPU view, responsive no-overflow layout and controls')
        context,page = open_page(viewport={'width':1200,'height':850},java_script_enabled=False)
        page.set_content(html,wait_until='load')
        for name in ['front','rear','inside','iso']:
            page.locator('label[for=saved-'+name+']').click()
            assert page.locator('.saved-'+name).is_visible()
        assert page.locator('#saved').is_visible()
        page.screenshot(path=str(out/'studio-no-javascript.png'));context.close()
        report['checks'].append('JavaScript disabled: four saved native CAD views and CSS-only selection')
        context,page = open_page(viewport={'width':1200,'height':850})
        # set_content does not run add_init_script: prepend the failure fixture directly.
        failure = "<script>const old=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(k,...a){if(k==='webgl2'||k==='webgl'||k==='experimental-webgl')return null;return old.call(this,k,...a)};<"+"/script>"
        page.set_content(html.replace('<script id="model-data"', failure+'<script id="model-data"'),wait_until='load')
        page.wait_for_timeout(250);assert page.locator('#saved').is_visible()
        assert 'could not start' in page.locator('#fallback-message').inner_text()
        page.locator('label[for=saved-rear]').click();assert page.locator('.saved-rear').is_visible()
        page.screenshot(path=str(out/'studio-no-webgl.png'));context.close()
        report['checks'].append('No WebGL: actionable fallback, no blank canvas, saved rear-view control')
        browser.close()
    assert not report['requests'] and not report['errors'], report
    report['html_sha256']=hashlib.sha256(html.encode()).hexdigest()
    (out/'BROWSER-VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
