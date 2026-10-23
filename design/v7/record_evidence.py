"""Bind verified native exports and saved review images to their inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshots',type=Path,required=True)
    parser.add_argument('--visual-review-note',default='Visual inspection not recorded; snapshot creation alone is not an appearance check.')
    args=parser.parse_args()
    report=json.loads((ROOT/'tmp/verification.json').read_text())
    assert not report['static_interference']['failures']
    assert len(report['parts'])==13 and len(report['branding'])==2
    report['revision']=json.loads((ROOT/'parameters.json').read_text())['revision']
    report['mesh_export']='native OCCT via build123d.export_stl; 0.003 mm / 0.05 rad'
    inputs=[ROOT/'parameters.json',*sorted((ROOT/'src').glob('*.py')),
            ROOT/'assets/DejaVuSans-Bold.ttf']
    report['input_sources_sha256']={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    scripts=[ROOT/'build.py',ROOT/'build_fit_samples.py',ROOT/'checks/verify_exports.py',
             ROOT/'checks/verify_fit_samples.py',ROOT/'make_snapshots.py',ROOT/'record_evidence.py']
    report['verification_sources_sha256']={str(p.relative_to(ROOT)):sha(p) for p in scripts}
    report['STL_sha256']={p.name:sha(p) for p in sorted((ROOT/'STL').glob('*.stl'))}
    report['fit_samples_report_sha256']=sha(ROOT/'checks/fit-samples-verified.json')
    report['printability_report_sha256']=sha(ROOT/'checks/printability-verified.json')
    report['delivery_groups']={'body_part_files':13,'optional_internal_tray':'v7_battery_tray',
                               'separate_first_print_samples':4,'bought_hardware_print_files':0}
    images=sorted(args.snapshots.glob('*.png'))
    assert len(images)>=24,'Expected the complete native snapshot packet'
    report['review_snapshots_sha256']={p.name:sha(p) for p in images}
    report['visual_review']=args.visual_review_note
    (ROOT/'checks/last-verified.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Saved current export, source/font and snapshot hashes')


if __name__=='__main__':main()
