"""Render the saved V3 STEP documents for design and assembly review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cadgen import read_scene

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--browser-executable',help='Optional installed Chromium path')
    parser.add_argument('--write-job-only',action='store_true')
    args=parser.parse_args();out=args.out_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    scene=read_scene(ROOT/'STEP/v3_complete_draft.step')
    hide=[l.ref for l in scene.leaves() if l.label in ('v3_cover_front','v3_cover_rear')]
    assert len(hide)==2,'Expected both cover occurrences in the saved revision'
    jobs=[]
    def add(stem,outputs,selection=None,display=None):
        job={'input':str(ROOT/'STEP'/(stem+'.step')),'mode':'view',
             'outputs':[{'path':str(out/(name+'.png')),'camera':camera} for name,camera in outputs],
             'output':{'sizeProfile':'simple','padding':0.12}}
        if selection:job['selection']=selection
        if display:job['display']=display
        jobs.append(job)
    add('v3_complete_draft',[('assembly-iso','iso'),('assembly-front','front'),('assembly-side','right'),('assembly-back','back'),('assembly-rear-angle',{'position':[300,400,280],'target':[0,35,130],'up':[0,0,1]})])
    add('v3_complete_draft',[('interior','iso')],selection={'hide':hide})
    add('v3_complete_draft',[('assembly-hero','iso')],display={'mode':'render','camera':{'projection':'orthographic'},'lighting':{'quality':'preview','exposure':0.5},'floor':{'placement':'lowest','opacity':0.15},'background':{'color':'#F0F4FA'}})
    add('v3_printed_assembly',[('printed-assembly','iso')])
    add('v3_reference_hardware',[('reference-hardware','iso')])
    for file in sorted((ROOT/'STEP').glob('v3_*.step')):
        stem=file.stem
        if stem in ('v3_complete_draft','v3_printed_assembly','v3_reference_hardware'):continue
        camera='iso'
        if stem=='v3_tail_joint_review':camera={'position':[-260,400,240],'target':[0,100,80],'up':[0,0,1]}
        if stem=='v3_cover_rear':camera={'position':[-250,340,190],'target':[0,70,50],'up':[0,0,1]}
        if stem=='v3_cover_front':camera={'position':[200,-300,160],'target':[0,-40,55],'up':[0,0,1]}
        add(stem,[(stem,camera)])
    add('v3_neck',[('neck-cable-eyes',{'position':[90,140,90],'target':[0,5,15],'up':[0,0,1]})])
    path=ROOT/'tmp/snapshot-jobs.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({'jobs':jobs},indent=2)+'\n')
    if args.write_job_only:
        print(path);return
    if args.browser_executable:
        from playwright.async_api import BrowserType
        launch=BrowserType.launch
        async def configured_launch(self,**kwargs):
            kwargs['executable_path']=args.browser_executable
            return await launch(self,**kwargs)
        BrowserType.launch=configured_launch
    from cadgen.cli.step_snapshot import main as snapshot
    raise SystemExit(snapshot(['--job',str(path),'--json']))


if __name__=='__main__':main()
