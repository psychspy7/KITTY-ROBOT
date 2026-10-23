"""Check saved solids, print-part meshes, static overlaps and key passages."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import struct
import sys

from cadgen import read_scene, read_step
from cadgen.geometry import overlap_volume, closest_points

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from settings import load, datums

PARTS=['r2_base','r2_cover_front','r2_cover_rear','r2_motor_left','r2_motor_right',
       'r2_battery_tray','r2_electronics_deck','r2_caster_bridge',
       'r2_sensor_bracket','r2_neck','r2_phone_cradle','r2_phone_cap']


def mesh(path):
    data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*n and n>0,path
    edges=Counter();volume=0
    for i in range(n):
        f=struct.unpack_from('<12fH',data,84+50*i)
        a,b,c=[tuple(f[j:j+3]) for j in (3,6,9)]
        assert all(math.isfinite(v) for point in (a,b,c) for v in point),path
        for u,v in ((a,b),(b,c),(c,a)):edges[(u,v)]+=1
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    assert all(count==1 and edges[(v,u)]==1 for (u,v),count in edges.items()),(path,'open/nonmanifold/inconsistently oriented mesh edge')
    assert volume>0,(path,'nonpositive signed mesh volume')
    return n,volume


def same(a,b,tolerance=1e-5):
    assert abs(a-b)<=tolerance,(a,b,tolerance)


def bounds_intersect(a,b):
    return all(min(getattr(a.max,k),getattr(b.max,k))-max(getattr(a.min,k),getattr(b.min,k))>1e-6 for k in ('X','Y','Z'))


def main():
    p=load();a=datums(p);report={'release':'DRAFT_NOT_FIT_APPROVED','parts':{},'unverified':['physical fit','strength','material/nozzle/slicing','actual mass and stability','moving wheel sweep and sensor coverage']}
    saved={}
    for name in PARTS:
        shape=read_step(ROOT/'STEP'/(name+'.step'));solids=list(shape.solids())
        assert len(solids)==1 and solids[0].is_valid and solids[0].volume>0,name
        solid=solids[0];saved[name]=solid;b=solid.bounding_box();s=b.size
        same(b.min.Z,0)
        assert all(x<=y for x,y in zip((s.X,s.Y,s.Z),(p['printer_x'],p['printer_y'],p['printer_z']))),name
        triangles,volume=mesh(ROOT/'STL'/(name+'.stl'))
        assert abs(volume-solid.volume)<max(2,solid.volume*0.001),(name,'mesh/native volume',volume,solid.volume)
        report['parts'][name]={'bounds_mm':[round(s.X,3),round(s.Y,3),round(s.Z,3)],'valid_solids':1,'closed_oriented_mesh':True,'triangles':triangles,'volume_mm3':round(volume,3)}
        print('PART PASS',name,flush=True)
    same(saved['r2_base'].bounding_box().size.X,p['body_width'])
    same(saved['r2_base'].bounding_box().size.Y,p['body_depth'])
    same(saved['r2_base'].bounding_box().size.Z,p['base_thickness'])
    same(saved['r2_phone_cradle'].bounding_box().size.X,a['head_width'])
    same(saved['r2_phone_cradle'].bounding_box().size.Y,a['head_height'])
    same(saved['r2_neck'].bounding_box().size.Z,p['neck_height'])
    base=saved['r2_base']
    for x in (-68,68):
        for y in (-65,65):assert not base.is_inside((x,y,2)),('blocked base/cover bore',x,y)
    assert not base.is_inside((0,p['caster_y'],2)),'blocked caster opening'
    neck=saved['r2_neck']
    for z in (1,5,p['neck_height']/2,p['neck_height']-1):
        assert not neck.is_inside((0,0,z)),('blocked cable route',z)
    sensor=saved['r2_sensor_bracket']
    for x in (-p['sonar_pitch']/2,p['sonar_pitch']/2):
        assert not sensor.is_inside((x,-78.5,p['sonar_z']-a['deck'])),'blocked sonar bore'
    scene=read_scene(ROOT/'STEP'/'r2_complete_draft.step')
    bodies=[]
    for leaf in scene.leaves():
        for solid in leaf.shape().solids():
            assert solid.is_valid and solid.volume>0,leaf.label
            bodies.append((leaf.label,solid,solid.bounding_box(optimal=False)))
    assert len(bodies)==23,('assembly component count',len(bodies))
    failures=[];exact=0;total=0
    for (na,sa,ba),(nb,sb,bb) in combinations(bodies,2):
        total+=1
        if not bounds_intersect(ba,bb):continue
        exact+=1;volume=overlap_volume(sa,sb)
        if volume>0.01:failures.append({'a':na,'b':nb,'overlap_mm3':round(volume,6)})
    report['static_interference']={'body_count':len(bodies),'pairs_considered':total,'exact_queries':exact,'maximum_allowed_mm3':0.01,'failures':failures}
    whole=read_step(ROOT/'STEP'/'r2_complete_draft.step');bounds=whole.bounding_box()
    report['assembled_bounds_mm']=[round(x,3) for x in (bounds.size.X,bounds.size.Y,bounds.size.Z)]
    report['assembly_mesh']='View-only multishell assembly; not a single-piece manufacturing mesh'
    same(bounds.min.Z,0)
    report['key_passages']='base/cover bores, caster opening, neck cable route and sonar bores checked'
    (ROOT/'tmp').mkdir(exist_ok=True)
    (ROOT/'tmp'/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['static_interference'],indent=2))
    if failures:raise SystemExit(1)
    print('PASS saved part solids/meshes, key dimensions/passages and static assembly interference')


if __name__=='__main__':main()
