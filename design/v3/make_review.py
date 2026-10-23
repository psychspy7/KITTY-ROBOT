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
    images={'ISO':'assembly-hero','FRONT':'assembly-front','REAR':'assembly-rear-angle',
            'SIDE':'assembly-side','INSIDE':'interior','JOINT':'v3_tail_joint_review'}
    for key,name in images.items():
        raw=(args.snapshots/(name+'.png')).read_bytes()
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Expected saved CAD PNG: '+name)
        template=template.replace('__'+key+'_IMAGE__','data:image/png;base64,'+base64.b64encode(raw).decode())
    report=json.loads((ROOT/'checks'/'last-verified.json').read_text())
    template=template.replace('__SIZE__',' × '.join(f'{v:g}' for v in report['assembled_bounds_mm']))
    template=template.replace('__PART_COUNT__',str(len(report['parts'])))
    metrics=report['optimization']
    template=template.replace('__VOLUME_REDUCTION__',f"{metrics['total_printed_solid_volume_mm3']['reduction_percent']:.2f}")
    for token,key in [('HEIGHT','whole_height_mm'),('DEPTH','whole_depth_mm')]:
        metric=metrics[key]
        template=template.replace('__OLD_'+token+'__',f"{metric['R2.1']:.1f}")
        template=template.replace('__NEW_'+token+'__',f"{metric['V3']:.1f}")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    for stem,mesh in [('KITTY-V3-REVIEW',True),('KITTY-V3-SAVED-VIEWS',False)]:
        data=base64.b64encode((ROOT/'STL'/'v3_complete_draft.stl').read_bytes()).decode() if mesh else ''
        page=template.replace('__MESH_DATA__',data).replace('__BODY_CLASS__','' if mesh else 'no-mesh')
        path=args.out_dir/(stem+'.html');path.write_text(page,encoding='utf-8')
        print(json.dumps({'path':str(path),'bytes':path.stat().st_size,'interactive_mesh':mesh}))


if __name__=='__main__':main()
