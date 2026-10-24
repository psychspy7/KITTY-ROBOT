"""Native saved-STEP review captures for the V7.1 rear sensor addition."""
from pathlib import Path
import json
from cadgen import read_scene

ROOT=Path(__file__).resolve().parent


def main():
    out=Path('/workspace/outputs/kitty-robot/v7-dual-ultrasonic/snapshots')
    out.mkdir(parents=True,exist_ok=True)
    scene=read_scene(ROOT/'STEP/v7_dual_ultrasonic.step')
    leaves=scene.leaves()
    jobs=[]
    def add(stem,views,hide=None,display=None):
        job={'input':str(ROOT/'STEP'/(stem+'.step')),'mode':'view',
             'outputs':[{'path':str(out/(name+'.png')),'camera':camera} for name,camera in views],
             'output':{'sizeProfile':'simple','padding':.12}}
        if hide:job['selection']={'hide':hide}
        if display:job['display']=display
        jobs.append(job)
    rear={'position':[260,370,225],'target':[0,40,115],'up':[0,0,1]}
    add('v7_dual_ultrasonic',[('assembly-iso','iso'),('assembly-front','front'),('assembly-rear-angle',rear),
                            ('assembly-back','back')])
    add('v7_dual_ultrasonic',[('assembly-hero','iso')],display={'mode':'render',
        'camera':{'projection':'orthographic'},'lighting':{'quality':'preview','exposure':.5},
        'floor':{'placement':'lowest','opacity':.15},'background':{'color':'#F0F4FA'}})
    add('v7_dual_ultrasonic',[('interior','iso')],hide=[l.ref for l in leaves if l.label in ('v7_cover_front','v7_cover_rear')])
    retained={'v7_base','v7_cover_rear','v7_tail','v7_rear_sensor_bracket'}
    add('v7_dual_ultrasonic',[('rear-mount-installed',{'position':[230,330,180],'target':[25,80,70],'up':[0,0,1]})],
        hide=[l.ref for l in leaves if l.label not in retained and not l.label.startswith('REFERENCE_ONLY_rear_sonar')])
    add('v7_rear_sensor_bracket',[('rear-bracket',{'position':[210,310,160],'target':[15,80,30],'up':[0,0,1]}),
                                  ('rear-bracket-back',{'position':[-180,-250,170],'target':[20,80,30],'up':[0,0,1]})])
    add('v7_fit_rear_sensor_face',[('rear-fit-gauge',{'position':[140,250,130],'target':[50,97,16],'up':[0,0,1]})])
    path=ROOT/'tmp/rear-snapshot-jobs.json'
    path.write_text(json.dumps({'jobs':jobs},indent=2)+'\n')
    from playwright.async_api import BrowserType
    launch=BrowserType.launch
    async def configured_launch(self,**kwargs):
        kwargs['executable_path']='/usr/bin/chromium'
        return await launch(self,**kwargs)
    BrowserType.launch=configured_launch
    from cadgen.cli.step_snapshot import main as snapshot
    raise SystemExit(snapshot(['--job',str(path),'--json']))


if __name__=='__main__':main()
