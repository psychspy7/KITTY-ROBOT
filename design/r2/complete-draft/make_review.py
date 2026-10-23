"""Build image-first offline design reviews with optional, lazy STL rendering."""
import argparse
import base64
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots',type=Path,required=True)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args()
    template=(ROOT/'review-template.html.in').read_text(encoding='utf-8')
    images={'ISO':'assembly-iso','FRONT':'assembly-front','REAR':'assembly-back','INSIDE':'interior'}
    for key,name in images.items():
        raw=(args.snapshots/(name+'.png')).read_bytes()
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Expected saved CAD PNG: '+name)
        template=template.replace('__'+key+'_IMAGE__','data:image/png;base64,'+base64.b64encode(raw).decode())
    report=json.loads((ROOT/'checks'/'last-verified.json').read_text())
    template=template.replace('__SIZE__',' × '.join(f'{v:g}' for v in report['assembled_bounds_mm']))
    args.out_dir.mkdir(parents=True,exist_ok=True)
    for stem,mesh in [('KITTY-R2-REVIEW',True),('KITTY-R2-SAVED-VIEWS',False)]:
        data=base64.b64encode((ROOT/'STL'/'r2_complete_draft.stl').read_bytes()).decode() if mesh else ''
        page=template.replace('__MESH_DATA__',data).replace('__BODY_CLASS__','' if mesh else 'no-mesh')
        path=args.out_dir/(stem+'.html');path.write_text(page,encoding='utf-8')
        print(json.dumps({'path':str(path),'bytes':path.stat().st_size,'interactive_mesh':mesh}))


if __name__=='__main__':main()
