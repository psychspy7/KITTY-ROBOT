"""Browser QA against explicit API fixtures; never connects to real electronics."""
from __future__ import annotations
import argparse, copy, json, time, hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

HERE=Path(__file__).resolve().parents[1]
BASE={"transport":"esp32-hardware-test","mode":"LOCKED","reason":"motor setup not verified",
      "left_pwm":0,"right_pwm":0,"remaining_ms":0,"front_mm":None,"rear_mm":None,
      "front_enabled":False,"rear_enabled":False,"led_enabled":False,"buzzer_enabled":False,
      "motors_ready":False,"sequence":0,"token":"a"*32,"stop_mm":200,"default_duty":48,
      "pulse_ms":150,"sample_id":0}

class Fixture:
    def __init__(self):self.state=copy.deepcopy(BASE);self.commands=[];self.failed=False;self.bad=False;self.old=False;self.pulse_at=None;self.owner=None;self.delay=None;self.pending=[]
    def handle(self,route):
        request=route.request
        if request.url=="http://192.168.4.1/":return route.fulfill(status=200,content_type="text/html",body=(HERE/'dashboard.html').read_text())
        if self.failed:return route.abort('failed')
        if request.url.endswith('/api/command'):
            from urllib.parse import parse_qs
            fields={k:v[0] for k,v in parse_qs(request.post_data or '').items()};action=fields['action']
            if self.delay==action:self.delay=None;self.pending.append(route);return
            self.commands.append(fields)
            assert request.headers.get('x-prometheus-token')==self.state['token']
            assert len(fields['client'])==24
            sequence=int(fields['seq']);active=self.state['mode'] in ['ARMED','PULSE']
            if action not in ['stop','estop'] and (sequence<=self.state['sequence'] or active and self.owner!=fields['client']):
                return route.fulfill(status=409,content_type='application/json',body='{"error":"stale sequence or owner"}')
            self.state['sequence']=max(self.state['sequence'],sequence)
            if action in ['stop','reset']:
                if action=='reset' or self.state['mode'] not in ['ESTOP','FAULT','OBSTACLE']:self.state['mode']='DISARMED' if self.state['motors_ready'] else 'LOCKED'
                self.state.update(left_pwm=0,right_pwm=0,remaining_ms=0);self.pulse_at=None;self.owner=None
            elif action=='estop':self.state.update(mode='ESTOP',left_pwm=0,right_pwm=0,remaining_ms=0);self.pulse_at=None;self.owner=None
            elif action=='arm':
                if self.state['mode'] not in ['DISARMED','COMPLETE'] or not self.state['motors_ready']:return route.fulfill(status=409,content_type='application/json',body='{"error":"arm rejected"}')
                self.state['mode']='ARMED';self.owner=fields['client']
            elif action=='heartbeat':
                if not active:return route.fulfill(status=409,content_type='application/json',body='{"error":"not active"}')
            elif action=='forward':self.state.update(mode='PULSE',left_pwm=int(fields['duty']),right_pwm=int(fields['duty']),remaining_ms=150);self.pulse_at=time.monotonic()
        if self.pulse_at and time.monotonic()-self.pulse_at>.15:self.state.update(mode='COMPLETE',left_pwm=0,right_pwm=0,remaining_ms=0);self.pulse_at=None
        self.state['sample_id']+=1;data=copy.deepcopy(self.state)
        if self.bad:data['left_pwm']='broken'
        if self.old:data.update(sample_id=1,mode='PULSE',left_pwm=48,right_pwm=48)
        return route.fulfill(status=200,content_type='application/json',body=json.dumps(data))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[];unexpected=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1100,'height':1000},accept_downloads=True)
        page=context.new_page();fixture=Fixture()
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            if r.request.url.startswith('http://192.168.4.1/'):fixture.handle(r)
            else:unexpected.append(r.request.url);r.abort()
        page.route('**/*',route);page.goto('http://192.168.4.1/')
        expect(page.locator('#mode')).to_have_text('LOCKED');expect(page.locator('#front')).to_have_text('N/A');expect(page.locator('#rear')).to_have_text('N/A');expect(page.locator('#arm')).to_be_disabled();expect(page.locator('[data-action="forward"]')).to_be_disabled();assert not fixture.commands
        checks.append('locked startup and absent telemetry do not become fake data or motor commands')
        fixture.state.update(motors_ready=True,mode='DISARMED',led_enabled=True,front_enabled=True,front_mm=500)
        expect(page.locator('#arm')).to_be_enabled();page.locator('#arm').click();expect(page.locator('[data-action="forward"]')).to_be_enabled();page.locator('[data-action="forward"]').click()
        expect(page.locator('#mode')).to_have_text('COMPLETE');expect(page.locator('[data-action="forward"]')).to_be_disabled()
        assert [c['action'] for c in fixture.commands if c['action']!='heartbeat']==['stop','arm','forward']
        assert next(c for c in fixture.commands if c['action']=='forward')['duty']=='48'
        expect(page.locator('#pulse-note')).to_contain_text('150 ms');checks.append('deliberate arm and exactly one bounded pulse command; completion requires rearm')
        page.locator('#estop').click();expect(page.locator('#mode')).to_have_text('ESTOP');expect(page.locator('#arm')).to_be_disabled();page.locator('#reset').click();expect(page.locator('#mode')).to_have_text('DISARMED');checks.append('latched-stop display and deliberate reset')
        page.locator('#arm').click();expect(page.locator('#mode')).to_have_text('ARMED');page.wait_for_timeout(250);assert any(c['action']=='heartbeat' for c in fixture.commands)
        fixture.failed=True;expect(page.locator('#mode')).to_have_text('UNAVAILABLE');n=sum(c['action']=='heartbeat' for c in fixture.commands);page.wait_for_timeout(300);assert sum(c['action']=='heartbeat' for c in fixture.commands)==n
        fixture.failed=False;fixture.state['mode']='DISARMED';expect(page.locator('#mode')).to_have_text('DISARMED');expect(page.locator('[data-action="forward"]')).to_be_disabled();page.wait_for_timeout(250);assert sum(c['action']=='heartbeat' for c in fixture.commands)==n;checks.append('link failure drops heartbeats; reconnect never rearms')
        fixture.old=True;page.wait_for_timeout(350);expect(page.locator('#mode')).to_have_text('DISARMED');expect(page.locator('#pwm')).to_have_text('0 / 0');fixture.old=False;checks.append('old sample cannot overwrite newer telemetry')
        fixture.bad=True;expect(page.locator('#mode')).to_have_text('UNAVAILABLE');fixture.bad=False;expect(page.locator('#mode')).to_have_text('DISARMED');checks.append('invalid numeric telemetry fails closed')
        start=len(fixture.commands);fixture.delay='stop';page.locator('#arm').click();page.wait_for_timeout(40);assert fixture.pending
        page.evaluate("window.dispatchEvent(new Event('blur'))");page.wait_for_timeout(50);fixture.handle(fixture.pending.pop());page.wait_for_timeout(150)
        assert not any(c['action']=='arm' for c in fixture.commands[start:]);expect(page.locator('[data-action="forward"]')).to_be_disabled();page.evaluate("window.dispatchEvent(new Event('focus'))");checks.append('blur cancels a delayed arm transaction before it can send arm or renew heartbeat')
        fixture.delay='arm';page.locator('#arm').click();page.wait_for_timeout(40);assert fixture.pending
        page.locator('#estop').click();expect(page.locator('#mode')).to_have_text('ESTOP');fixture.handle(fixture.pending.pop());page.wait_for_timeout(150);expect(page.locator('#mode')).to_have_text('ESTOP');expect(page.locator('[data-action="forward"]')).to_be_disabled();checks.append('priority ESTOP bypasses pending request and stale continuation cannot undo its latch')
        page.locator('#reset').click();expect(page.locator('#mode')).to_have_text('DISARMED');page.locator('#arm').click();expect(page.locator('#mode')).to_have_text('ARMED');page.wait_for_timeout(240)
        beats=[int(c['seq']) for c in fixture.commands if c['action']=='heartbeat'];assert all(a<b for a,b in zip(beats,beats[1:]));last=next(c for c in reversed(fixture.commands) if c['action']=='heartbeat')
        probe='''async data=>{const response=await fetch('/api/command',{method:'POST',headers:{'X-Prometheus-Token':data.token,'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(data.fields)});return response.status;}'''
        assert page.evaluate(probe,{'token':fixture.state['token'],'fields':last})==409
        wrong=dict(last,client='b'*24,seq=str(fixture.state['sequence']+100));assert page.evaluate(probe,{'token':fixture.state['token'],'fields':wrong})==409
        page.locator('#stop').click();expect(page.locator('#mode')).to_have_text('DISARMED');checks.append('strict fixture rejects replay/wrong owner and browser sends increasing heartbeat sequence')
        page.set_viewport_size({'width':360,'height':900});page.screenshot(path=str(args.out/'dashboard-mobile.png'),full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');checks.append('360px phone layout has no horizontal overflow')
        preview=context.new_page();preview.set_content((HERE/'dashboard.html').read_text());expect(preview.locator('#mode')).to_have_text('UNAVAILABLE');expect(preview.locator('#arm')).to_be_disabled();checks.append('disk-style preview does not connect or unlock controls')
        canvas=context.new_page();canvas.on('pageerror',lambda e:errors.append(str(e)))
        canvas.route('http://code.local/',lambda r:r.fulfill(status=200,content_type='text/html',body=(args.out/'PROMETHEUS-CODE-CANVAS.html').read_text()));canvas.goto('http://code.local/')
        assert canvas.locator('#file option').count()==len(list((HERE/'PrometheusTest').glob('*.h')))+1
        source=(HERE/'PrometheusTest/PrometheusTest.ino').read_text();expect(canvas.locator('#code')).to_have_value(source)
        canvas.locator('#code').fill(source+'\n// fixture edit\n');canvas.locator('#file').select_option('Settings.h')
        expect(canvas.locator('#code')).to_have_value((HERE/'PrometheusTest/Settings.h').read_text());canvas.locator('#file').select_option('PrometheusTest.ino');expect(canvas.locator('#code')).to_have_value(source+'\n// fixture edit\n')
        with canvas.expect_download() as download:canvas.locator('#save').click()
        saved=download.value;assert saved.suggested_filename=='PrometheusTest.ino';assert Path(saved.path()).read_text()==source+'\n// fixture edit\n'
        canvas.screenshot(path=str(args.out/'code-canvas.png'),full_page=True);checks.append('embedded source files match; edits survive switching and download intact')
        assert not errors,errors;assert not unexpected,unexpected
        browser.close()
    result={'evidence_kind':'browser tests with labelled API fixtures; no electronics connected','passed':len(checks),'input_sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'dashboard.html',HERE/'build_kit.py',HERE/'tests/browser_test.py',*list((HERE/'PrometheusTest').glob('*.h')),*list((HERE/'PrometheusTest').glob('*.ino'))]},'checks':checks,'page_errors':errors,'unexpected_requests':unexpected}
    (args.out/'BROWSER-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
