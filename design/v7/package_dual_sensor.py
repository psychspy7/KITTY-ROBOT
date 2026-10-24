"""Prepare exact V7.1 service meshes and an STL-only shop ZIP with one PDF."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent
BASE=Path('/workspace/outputs/kitty-robot/v7-print-service')
OUT=Path('/workspace/outputs/kitty-robot/v7-dual-ultrasonic')
BODY=['v7_base','v7_cover_front','v7_cover_rear','v7_motor_left','v7_motor_right',
      'v7_electronics_deck','v7_caster_bridge','v7_sensor_bracket','v7_neck',
      'v7_phone_cradle','v7_phone_cap','v7_tail','v7_rear_sensor_bracket']
SAMPLES=['v7_fit_tail_socket','v7_fit_tail_key','v7_fit_phone_thickness','v7_fit_screws','v7_fit_rear_sensor_face']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    original=json.loads((BASE/'ARTIFACTS-SHA256.json').read_text())
    for folder in ('STL_PARTS','FIT_TEST_FIRST','STEP_PARTS'): (OUT/folder).mkdir(parents=True,exist_ok=True)
    for name in BODY+['v7_battery_tray']+SAMPLES:
        group='FIT_TEST_FIRST' if name in SAMPLES else 'STL_PARTS'
        relative=group+'/'+name+'.stl'
        new=name in ('v7_rear_sensor_bracket','v7_fit_rear_sensor_face')
        source=ROOT/'STL'/(name+'.stl') if new else BASE/relative
        if not new:assert sha(source)==original[relative],relative
        shutil.copyfile(source,OUT/relative)
        step=ROOT/'STEP'/(name+'.step') if new else BASE/'STEP_PARTS'/(name+'.step')
        shutil.copyfile(step,OUT/'STEP_PARTS'/(name+'.step'))
    geometry=json.loads((ROOT/'checks/rear-sensor-verified.json').read_text())
    for relative,digest in geometry['source_sha256'].items():assert sha(ROOT/relative)==digest,relative
    assert not geometry['static_interference']['failures']
    for name,digest in geometry['STL_sha256'].items():
        group='FIT_TEST_FIRST' if name in SAMPLES else 'STL_PARTS'
        assert sha(OUT/group/(name+'.stl'))==digest,name
    shutil.copyfile(ROOT/'checks/rear-sensor-verified.json',OUT/'REAR-GEOMETRY-VERIFICATION.json')
    shutil.copyfile(ROOT/'rear-sensor-parameters.json',OUT/'REAR-SENSOR-ASSUMPTIONS.json')
    for stem in ('v7_rear_sensor_bracket','v7_fit_rear_sensor_face'):
        measure=json.loads((OUT/'dfam'/(stem+'.json')).read_text())
        assert not measure['partial'] and measure['mesh']['watertight']
        assert measure['wall_thickness']['p05_mm']>=1.6
    page=(ROOT/'shop-instructions-dual.html.in').read_text()
    page=page.replace('__PART_LIST__',''.join('<li><code>'+html.escape(name)+'.stl</code><b>× 1</b></li>' for name in BODY))
    (OUT/'PRINT-INSTRUCTIONS.html').write_text(page)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True)
        context=browser.new_context(offline=True);tab=context.new_page();tab.set_content(page,wait_until='load')
        tab.pdf(path=str(OUT/'PRINT-INSTRUCTIONS.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
        context.close();browser.close()
    info=subprocess.check_output(['pdfinfo',str(OUT/'PRINT-INSTRUCTIONS.pdf')],text=True)
    assert any(line.split(':',1)[1].strip()=='1' for line in info.splitlines() if line.startswith('Pages:')),info
    write_manifest()
    print('Prepared 14 body meshes (one optional), five gauges and one-page shop PDF.')


def write_manifest():
    entries={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()
             and p.name!='ARTIFACTS-SHA256.json' and p.suffix!='.zip'}
    (OUT/'ARTIFACTS-SHA256.json').write_text(json.dumps(entries,indent=2)+'\n')


def archive():
    target=OUT/'KITTY-V7.1-FRONT-AND-REAR-SENSORS-SHOP.zip'
    entries={}
    for name in BODY:entries['ROBOT_PARTS/'+name+'.stl']=OUT/'STL_PARTS'/(name+'.stl')
    for name in SAMPLES:entries['FIT_TEST_FIRST/'+name+'.stl']=OUT/'FIT_TEST_FIRST'/(name+'.stl')
    entries['OPTIONAL_DO_NOT_PRINT/v7_battery_tray.stl']=OUT/'STL_PARTS/v7_battery_tray.stl'
    entries['PRINT-INSTRUCTIONS.pdf']=OUT/'PRINT-INSTRUCTIONS.pdf'
    assert len(entries)==20
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in entries.items():z.write(path,name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and set(z.namelist())==set(entries)
        for name,path in entries.items():assert z.read(name)==path.read_bytes(),name
    result={'file':target.name,'sha256':sha(target),'bytes':target.stat().st_size,'entries':20,
            'STL_files':19,'main_robot_parts':13,'optional_tray_files':1,'fit_samples':5,
            'instruction_PDF_pages':1,'front_sensor_mount':True,'rear_sensor_mount':True,
            'purchased_hardware_STLs':0,'archive_CRC':'passed'}
    (OUT/'SHOP-ZIP-VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n')
    write_manifest()
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',action='store_true')
    args=parser.parse_args()
    if args.archive:archive()
    else:prepare()
