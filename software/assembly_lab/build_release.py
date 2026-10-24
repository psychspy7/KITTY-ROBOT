"""Build the browser workbench without network access or CAD regeneration."""
from __future__ import annotations
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile

HERE = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--archive',action='store_true')
    args=parser.parse_args()
    out=args.out.resolve()
    if out==HERE:parser.error('--out must not be the source directory')
    out.mkdir(parents=True,exist_ok=True)
    archive_path=out/'KITTY-ASSEMBLY-LAB-COMPLETE.zip'
    vendor=HERE/'vendor'
    if not vendor.exists(): vendor=HERE.parents[1]/'design/v7/advanced-viewer/vendor'
    provenance=json.loads((HERE/'assets/provenance.json').read_text())
    for name,digest in provenance['assets_sha256'].items():
        assert sha(HERE/'assets'/name)==digest, 'Asset changed: '+name
    model=json.loads(gzip.decompress((HERE/'assets/model.json.gz').read_bytes()))
    assert len(model['parts'])==28 and model['physicalFitVerified'] is False
    for part in model['parts']:
        assert hashlib.sha256(base64.b64decode(part['mesh'])).hexdigest()==part['sha256'],part['id']
    three=(vendor/'three.min.js').read_text();orbit=(vendor/'OrbitControls.js').read_text()
    orbit=re.sub(r'import\s*\{([\s\S]*?)\}\s*from\s*[\'"]three[\'"];',r'const {\1} = THREE;',orbit,count=1)
    orbit=re.sub(r'export\s*\{\s*OrbitControls\s*\};?','window.OrbitControls = OrbitControls;',orbit)
    page=(HERE/'index.html.in').read_text()
    values={'__STYLE__':(HERE/'style.css').read_text(),'__MODEL__':json.dumps(model,separators=(',',':')),
            '__THREE__':three,'__ORBIT__':orbit,'__CORE__':(HERE/'core.js').read_text(),'__APP__':(HERE/'app.js').read_text(),
            '__FALLBACK__':'data:image/png;base64,'+base64.b64encode((HERE/'assets/chassis.png').read_bytes()).decode()}
    for key,value in values.items():
        if key not in ('__STYLE__','__FALLBACK__'):value=value.replace('</script','<\\/script')
        page=page.replace(key,value)
    # Upstream Three.js intentionally contains window.__THREE__.
    assert not re.search(r'__(?:STYLE|MODEL|ORBIT|CORE|APP|FALLBACK)__',page)
    target=out/'KITTY-ASSEMBLY-LAB.html';target.write_text(page)
    (out/'START-HERE.md').write_text((HERE/'README.md').read_text())
    output_in_source=HERE in out.parents
    source_files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p)
                  and p!=archive_path and not (output_in_source and out in p.parents)]
    evidence={'html_sha256':sha(target),'html_bytes':target.stat().st_size,'source_sha256':{str(p.relative_to(HERE)):sha(p) for p in source_files},'cad_geometry_changed':False,'physical_outputs':False,'firmware_emulated':False,'circuit_model':'nominal DC source constraints and explicit expected signal paths','motion_model':'differential drive, sampled 2D rays, conservative circular footprint'}
    (out/'BUILD-PROVENANCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    if args.archive:
        with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED,compresslevel=8) as z:
            z.write(target,target.name);z.write(out/'START-HERE.md','START-HERE.md')
            for p in source_files:
                z.write(p,'source/'+str(p.relative_to(HERE)))
            if vendor.parent!=HERE:
                for p in vendor.iterdir():
                    if p.is_file():z.write(p,'source/vendor/'+p.name)
            for p in out.glob('*VERIFICATION.json'):z.write(p,p.name)
            z.write(out/'BUILD-PROVENANCE.json','BUILD-PROVENANCE.json')
        with zipfile.ZipFile(archive_path) as z:assert z.testzip() is None
    print(json.dumps({'html':str(target),'bytes':target.stat().st_size,'sha256':sha(target)}))
if __name__=='__main__':main()
