"""Verify the delivered bundle, source rebuild and stale-evidence rejection."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
import fitz

HERE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(src,out,archive=False):
    cmd=[sys.executable,str(src/'build_kit.py'),'--out',str(out)]
    if archive:cmd.append('--archive')
    return subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();out=args.out.resolve();checks=[]
    for p in (HERE/'PrometheusTest').iterdir():
        if p.suffix in ['.ino','.h']:assert sha(p)==sha(out/'PrometheusTest'/p.name)
    canvas=(out/'PROMETHEUS-CODE-CANVAS.html').read_text();match=re.search(r'<script id="sources" type="application/json">(.*?)</script>',canvas,re.S);assert match
    embedded=json.loads(match[1]);assert set(embedded)=={p.name for p in (HERE/'PrometheusTest').iterdir() if p.suffix in ['.ino','.h']}
    for name,text in embedded.items():assert text==(HERE/'PrometheusTest'/name).read_text()
    checks.append('Arduino folder and editable canvas contain the exact source files')
    manifest=json.loads((out/'ARTIFACTS-SHA256.json').read_text())
    for name,digest in manifest.items():assert sha(out/name)==digest
    checks.append('artifact manifest hashes match delivered PDF, text, canvas and Arduino source')
    doc=fitz.open(out/'PROMETHEUS-FINAL-TEST-GUIDE.pdf');assert len(doc)==18
    text='\n'.join(p.get_text() for p in doc);assert 'Test 01 / battery voltage' in doc[2].get_text();assert 'Motor power' in text or 'MOTOR POWER' in text
    assert 'Front and optional rear ultrasonic' in text and '2.963' in text and 'No raw 5 V ECHO' in text
    for page in doc:
        for block in page.get_text('blocks'):
            x0,y0,x1,y1,*_=block;assert x0>=18 and x1<=page.rect.width-10 and y0>=5 and y1<=page.rect.height-10,(page.number,block)
    checks.append('18-page PDF text bounds, battery-first page and dual-sensor/divider hold instructions')
    archive=out/'PROMETHEUS-FINAL-TEST-KIT.zip'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None;names=z.namelist();assert not any('.stale' in n or '__pycache__' in n for n in names)
        assert 'PROMETHEUS-FINAL-TEST-GUIDE.pdf' in names and 'PrometheusTest/HttpGate.h' in names
        assert not any(n.endswith(('.bin','.elf')) for n in names)
    checks.append('ZIP CRC valid, all sketch tabs present, no stale reports or flash binaries')
    with tempfile.TemporaryDirectory(prefix='prometheus-release-check-') as temp:
        temp=Path(temp)
        with zipfile.ZipFile(archive) as z:z.extractall(temp/'extract')
        portable=temp/'extract/source';rebuilt=temp/'portable-release';rebuilt.mkdir()
        for record in out.glob('*VERIFICATION.json'):
            if record.name=='COMPILE-VERIFICATION.json':shutil.copy2(record,rebuilt/record.name)
        build(portable,rebuilt)
        assert sha(rebuilt/'PROMETHEUS-FINAL-TEST-GUIDE.pdf')==sha(out/'PROMETHEUS-FINAL-TEST-GUIDE.pdf')
        assert sha(rebuilt/'PROMETHEUS-CODE-CANVAS.html')==sha(out/'PROMETHEUS-CODE-CANVAS.html')
        checks.append('extracted source rebuild reproduces exact PDF and code canvas with matching compile record')
        sketch=portable/'PrometheusTest/Settings.h';sketch.write_text(sketch.read_text()+'\n// explicit source mutation fixture\n')
        build(portable,rebuilt,True)
        assert not (rebuilt/'COMPILE-VERIFICATION.json').exists()
        stale_text='\n'.join(p.get_text() for p in fitz.open(rebuilt/'PROMETHEUS-FINAL-TEST-GUIDE.pdf'))
        assert 'Not yet verified' in stale_text
        with zipfile.ZipFile(rebuilt/'PROMETHEUS-FINAL-TEST-KIT.zip') as z:assert 'COMPILE-VERIFICATION.json' not in z.namelist()
        checks.append('changed source removes old successful compile evidence from rebuilt PDF and ZIP')
        plan=json.loads((portable/'pins.json').read_text());p=plan['pins'];p['Ain1'],p['Ain2']=p['Ain2'],p['Ain1'];p['FrontEcho'],p['RearEcho']=p['RearEcho'],p['FrontEcho'];p['Led'],p['Buzzer']=p['Buzzer'],p['Led'];(portable/'pins.json').write_text(json.dumps(plan))
        build(portable,rebuilt);changed=fitz.open(rebuilt/'PROMETHEUS-FINAL-TEST-GUIDE.pdf')
        assert 'Ain1=26' in (portable/'PrometheusTest/RobotPins.h').read_text()
        assert re.search(r'GPIO26\s+AIN1',changed[7].get_text())
        assert 'J -> GPIO17 front / GPIO32 rear' in changed[8].get_text()
        assert 'GPIO13' in changed[9].get_text() and 'Buzzer: GPIO33' in changed[9].get_text()
        assert 'GPIO13 -> 1k' in changed[12].get_text()
        checks.append('pin mutations update generated header, driver/divider/indicator diagrams and stage instructions')
        bad=subprocess.run([sys.executable,str(portable/'build_kit.py'),'--out',str(portable/'nested-output')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        assert bad.returncode!=0 and not (portable/'nested-output').exists()
        checks.append('nested output rejected without recursive source packaging')
    inputs={str(p.relative_to(HERE)):sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.ino','.h','.html','.json','.md']}
    result={'evidence_kind':'software packaging/rebuild checks; no physical robot','passed':len(checks),'checks':checks,'input_sha256':inputs,'artifact_sha256':{'PROMETHEUS-FINAL-TEST-GUIDE.pdf':sha(out/'PROMETHEUS-FINAL-TEST-GUIDE.pdf'),'PROMETHEUS-CODE-CANVAS.html':sha(out/'PROMETHEUS-CODE-CANVAS.html')}}
    (out/'PACKAGE-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(checks),'checks':checks},indent=2))
if __name__=='__main__':main()
