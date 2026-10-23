"""Verify separate first-print gauges and their saved dimensions."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from cadgen import read_step,build123d as bd
from cadgen.geometry import overlap_volume

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from settings import load
from verify_exports import mesh,same

FIT_PARTS=['v7_fit_tail_socket','v7_fit_tail_key','v7_fit_phone_thickness','v7_fit_screws']


def main():
    p=load();saved={};report={'release':'FIT_SAMPLES_NOT_PHYSICAL_FIT_EVIDENCE','parts':{}}
    for name in FIT_PARTS:
        shape=read_step(ROOT/'STEP'/(name+'.step'));solids=list(shape.solids())
        assert len(solids)==1 and solids[0].is_valid and solids[0].volume>0,name
        s=solids[0];saved[name]=s;b=s.bounding_box();same(b.min.Z,0)
        triangles,volume=mesh(ROOT/'STL'/(name+'.stl'))
        assert abs(volume-s.volume)<max(2,s.volume*0.001),name
        assert all(v<=limit for v,limit in zip((b.size.X,b.size.Y,b.size.Z),(p['printer_x'],p['printer_y'],p['printer_z']))),name
        report['parts'][name]={'valid_solids':1,'closed_oriented_mesh':True,'triangles':triangles,
                              'bounds_mm':[round(v,3) for v in (b.size.X,b.size.Y,b.size.Z)],'native_volume_mm3':round(s.volume,3)}
    socket=saved['v7_fit_tail_socket'];key=saved['v7_fit_tail_key'];r=p['tail_thickness']/2
    for x,gap in ((-20,0.3),(0,0.4),(20,0.5)):
        assert not socket.is_inside((x+r+gap-0.01,0,8)),'sample too tight'
        assert socket.is_inside((x+r+gap+0.01,0,8)),'sample too loose'
        assert socket.is_inside((x,-10,10)),'sample blind backing missing'
    assert key.is_inside((10,r-0.01,3)) and not key.is_inside((10,r+0.01,3)),'sample key width'
    assert not key.is_inside((10,r-1,2*r-1)) and key.is_inside((10,-r+1,2*r-1)),'sample key orientation'
    for x in (-20,0,20):
        placed=bd.Pos(x-r,-8,10)*bd.Rot(0,90,0)*bd.Rot(0,0,90)*key
        for withdrawn in (0,10,22):
            sample=(bd.Pos(0,withdrawn,0)*placed).solids()[0]
            assert overlap_volume(sample,socket)<0.01,('sample insertion interference',x,withdrawn)
    gauge=saved['v7_fit_phone_thickness'];half=(p['phone_thickness']+p['fit_gap'])/2
    for sign in (-1,1):
        assert not gauge.is_inside((sign*(half-0.01),0,2)),'phone gauge too tight'
        assert gauge.is_inside((sign*(half+0.01),0,2)),'phone gauge too loose'
    screws=saved['v7_fit_screws']
    for x,d in ((-18,3.2),(-6,3.4),(6,3.6),(18,3.8)):
        assert not screws.is_inside((x+d/2-0.01,3,2)),'screw sample too tight'
        assert screws.is_inside((x+d/2+0.01,3,2)),'screw sample too loose'
    report['sampled_dimensions']={'tail_clearances_per_side_mm':[0.3,0.4,0.5],
        'tail_key_width_mm':p['tail_thickness'],'tail_sample_depth_mm':20,
        'phone_thickness_throat_mm':p['phone_thickness']+p['fit_gap'],
        'screw_diameters_mm':[3.2,3.4,3.6,3.8],'probe_offset_mm':0.01}
    report['sample_key_insertion']='All three saved keyways: full key and handle checked at 0/10/22 mm withdrawal; no overlap above 0.01 mm3'
    report['limits']='Coupons check process/interface dimensions only; not real fit, fastener strength, phone width/height/ports or a full tail joint load test.'
    (ROOT/'checks/fit-samples-verified.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS four first-print sample solids, closed meshes, saved dimensions and assumed bed fit')


if __name__=='__main__':main()
