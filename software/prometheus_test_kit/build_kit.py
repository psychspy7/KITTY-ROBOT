"""Generate matched Arduino headers, an editable text code page and test PDF."""
from __future__ import annotations
import argparse,base64,hashlib,json,re,shutil,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def invalidate_stale(out,artifacts=False):
    for p in out.glob('*VERIFICATION.json'):
        record=json.loads(p.read_text());inputs=record.get('input_sha256',{})
        current=bool(inputs)
        for name,expected in inputs.items():
            f=(HERE/name).resolve()
            current=current and HERE in f.parents and f.is_file() and sha(f)==expected
        if artifacts:
            for name,expected in record.get('artifact_sha256',{}).items():
                f=(out/name).resolve()
                current=current and out in f.parents and f.is_file() and sha(f)==expected
        if not current:
            p.replace(p.with_suffix('.json.stale'))
            print('Excluded stale verification:',p.name)
def headers():
    plan=json.loads((HERE/'pins.json').read_text());pins=plan['pins'];values=list(pins.values())
    assert len(set(values))==len(values)
    assert not set(values)&{0,1,2,3,5,6,7,8,9,10,11,12,15,34,35,36,37,38,39}
    content='#pragma once\n// GENERATED from pins.json. Candidate labels, not a physical release.\nnamespace pins {\n'
    content+=''.join(f'constexpr int {key}={value};\n' for key,value in pins.items())+'}\n'
    (HERE/'PrometheusTest/RobotPins.h').write_text(content)
    dashboard=(HERE/'dashboard.html').read_text();assert ')PROM_DASH"' not in dashboard
    (HERE/'PrometheusTest/Dashboard.h').write_text('#pragma once\n#include <Arduino.h>\nconst char PROMETHEUS_DASHBOARD[] PROGMEM=R"PROM_DASH('+dashboard+')PROM_DASH";\n')
    return plan

def code_page(files):
    data=json.dumps(files).replace('</','<\\/')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PROMETHEUS · editable code</title><style>body{margin:0;background:#0e1c26;color:#e1edf2;font:14px Segoe UI,Arial}header{padding:20px;display:flex;align-items:center;gap:15px;flex-wrap:wrap}h1{font-size:21px;margin:0}select,button{background:#294656;color:#e6f5fc;border:1px solid #708c9b;padding:9px;border-radius:6px}p{margin:0 20px 16px;color:#afc8d6;font-size:12px;line-height:1.7}textarea{box-sizing:border-box;width:calc(100% - 40px);height:73vh;margin:0 20px 20px;padding:16px;background:#102430;color:#d5f5e9;border:1px solid #476371;border-radius:8px;font:12px/1.65 Consolas,monospace;tab-size:2}#status{color:#92ebd2;font-size:12px}</style><header><h1>PROMETHEUS / Code text canvas</h1><select id="file" aria-label="Code file"></select><button id="save">Save selected file</button><button id="copy">Copy text</button><span id="status"></span></header><p>This is an editable local text page, not a firmware uploader. Edits stay in this page until saved. Keep every header beside PrometheusTest.ino inside the PrometheusTest folder. Original settings lock physical outputs. Complete the PDF's hardware checks before changing stage flags.</p><textarea id="code" spellcheck="false" aria-label="Editable Arduino source"></textarea><script id="sources" type="application/json">'''+data+'''</script><script>(()=>{const files=JSON.parse(document.getElementById('sources').textContent),pick=document.getElementById('file'),editor=document.getElementById('code'),status=document.getElementById('status');let selected=Object.keys(files)[0];for(const name of Object.keys(files)){const o=document.createElement('option');o.value=name;o.textContent=name;pick.append(o);}editor.value=files[selected];pick.onchange=()=>{files[selected]=editor.value;selected=pick.value;editor.value=files[selected];status.textContent='';};editor.oninput=()=>status.textContent='Edited · save to keep this file';document.getElementById('save').onclick=()=>{files[selected]=editor.value;const a=document.createElement('a'),url=URL.createObjectURL(new Blob([editor.value],{type:'text/plain;charset=utf-8'}));a.href=url;a.download=selected;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);status.textContent='Downloaded '+selected;};document.getElementById('copy').onclick=async()=>{try{await navigator.clipboard.writeText(editor.value);status.textContent='Copied';}catch{editor.focus();editor.select();status.textContent='Selected all · press Ctrl+C';}};})();</script></html>'''

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--code-only',action='store_true');ap.add_argument('--archive',action='store_true');args=ap.parse_args();plan=headers()
    if args.code_only:print('Matched RobotPins.h and Dashboard.h generated');return
    out=args.out.resolve();assert out!=HERE and HERE not in out.parents,'Output must be outside the source folder';out.mkdir(parents=True,exist_ok=True)
    target=out/'PrometheusTest';target.mkdir(exist_ok=True)
    files={p.name:p.read_text() for p in sorted((HERE/'PrometheusTest').glob('*')) if p.suffix in ['.ino','.h']}
    files={'PrometheusTest.ino':files.pop('PrometheusTest.ino'),**files}
    for name,text in files.items():(target/name).write_text(text)
    invalidate_stale(out)
    (out/'PROMETHEUS-CODE-CANVAS.html').write_text(code_page(files))
    (out/'PROMETHEUS-ALL-CODE.txt').write_text('PROMETHEUS staged test kit: separate these files into matching Arduino tabs.\nMotor power is NOT approved by this file.\n\n'+''.join('\n===== FILE: '+n+' =====\n'+s+'\n' for n,s in files.items()))
    from guide import create_pdf
    create_pdf(out/'PROMETHEUS-FINAL-TEST-GUIDE.pdf',plan,out)
    invalidate_stale(out,True)
    shutil.copyfile(HERE/'README.md',out/'START-HERE.md')
    manifest={str(p.relative_to(out)):sha(p) for p in list(out.iterdir())+list(target.iterdir()) if p.is_file() and p.suffix in ['.pdf','.html','.txt','.ino','.h','.md']}
    (out/'ARTIFACTS-SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if args.archive:
        archive=out/'PROMETHEUS-FINAL-TEST-KIT.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in out.iterdir():
                if p.is_file() and p!=archive and (p.suffix in ['.pdf','.html','.txt','.md'] or p.name.endswith('VERIFICATION.json') or p.name=='ARTIFACTS-SHA256.json'):z.write(p,p.name)
            for p in target.iterdir():z.write(p,'PrometheusTest/'+p.name)
            for p in HERE.rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:z.write(p,'source/'+str(p.relative_to(HERE)))
        with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps({'pdf':str(out/'PROMETHEUS-FINAL-TEST-GUIDE.pdf'),'code_files':len(files),'out':str(out)}))
if __name__=='__main__':main()
