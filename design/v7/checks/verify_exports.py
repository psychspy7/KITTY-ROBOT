"""Check saved solids, print-part meshes, static overlaps and key passages."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import struct
import sys

from cadgen import build123d as bd, read_scene, read_step
from cadgen.geometry import overlap_volume

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from settings import load, datums, tail_placement

PARTS=['v7_base','v7_cover_front','v7_cover_rear','v7_motor_left','v7_motor_right',
       'v7_battery_tray','v7_electronics_deck','v7_caster_bridge',
       'v7_sensor_bracket','v7_neck','v7_phone_cradle','v7_phone_cap','v7_tail']


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


def verify_tail_joint(p,a,saved,bodies):
    """Probe the saved keyed fit and check withdrawal with the screw removed."""
    tail=(tail_placement(p)*saved['v7_tail']).solids()[0]
    rear=(bd.Pos(0,0,a['deck'])*saved['v7_cover_rear']).solids()[0]
    y=a['tail_y']-p['tail_bolt_inset'];z=p['tail_height']-4;r=p['tail_thickness']/2
    for sign in (-1,1):
        assert tail.is_inside((sign*(r-0.01),y,z)),'missing keyed root wall'
        assert not tail.is_inside((sign*(r+0.01),y,z)),'oversize keyed root'
        assert not rear.is_inside((sign*(r+p['tail_joint_gap']-0.01),y,z)),'insufficient socket gap'
        assert rear.is_inside((sign*(r+p['tail_joint_gap']+0.01),y,z)),'missing socket wall'
    assert not tail.is_inside((r-1,y,p['tail_height']+r-1)),'key corner not clipped'
    assert tail.is_inside((r-1,y,p['tail_height']-r+1)),'key orientation lost'
    assert rear.is_inside((0,a['tail_y']-p['tail_key_length']-0.5,p['tail_height'])),'socket has no blind backing'
    for x in (0,10,-10):
        assert not rear.is_inside((x,y,p['tail_height'])),'socket cross bore blocked'
        assert not tail.is_inside((x,y,p['tail_height'])),'tail cross bore blocked'
    assert not rear.is_inside((-12,p['body_depth']/2-1,44)),'rear service opening blocked'
    assert rear.is_inside((-13.4,a['tail_y']-10,p['tail_height']-8)), 'tail removal arrow missing'
    assert not rear.is_inside((-13.4,y,p['tail_height'])), 'arrow blocks screw-entry access'
    # Tail plastic stays above the service-window band (maximum Z=54 mm).
    assert tail.bounding_box().min.Z>54+20,'tail crosses lower service access'
    failures=[]
    for distance in (0,6,12,18,24,35):
        moved=(bd.Pos(0,distance,0)*tail).solids()[0]
        bounds=moved.bounding_box(optimal=False)
        for label,other,other_bounds in bodies:
            if label=='v7_tail' or not bounds_intersect(bounds,other_bounds):continue
            volume=overlap_volume(moved,other)
            if volume>0.01:failures.append((distance,label,volume))
    assert not failures,('tail removal collision',failures)
    return {'proposed_per_side_gap_mm':p['tail_joint_gap'],
            'saved_flat_gap_probe_tolerance_mm':0.01,
            'key':'one clipped corner, screw axis X',
            'retention':'proposed M3 cross screw and hex nut; hardware/strength/fit unverified',
            'removal':'remove screw, pull straight rearward (+Y)',
            'withdrawal_positions_mm':[0,6,12,18,24,35],
            'withdrawal_interference_failures':[],
            'lower_service_window':'open; tail plastic above Z=74 mm'}


def compare_revision(p,a,saved,bodies,bounds):
    baseline=json.loads((ROOT/'checks'/'baseline-r2.1.json').read_text())
    old_volumes=baseline['native_part_volumes_mm3']
    old_total=sum(old_volumes.values());new_total=sum(s.volume for s in saved.values())
    assert new_total<old_total,'V7 must reduce the total proposed plastic volume'
    neck=saved['v7_neck']
    for x in (-34,34):
        for y in (-23,23):assert not neck.is_inside((x,y,2)),'neck flange bore blocked'
    for x in (-16,16):
        assert not neck.is_inside((x,0,p['neck_height']-1)),'head fastener bore blocked'
    phones=[solid for label,solid,_ in bodies if label=='REFERENCE_ONLY_phone_case_envelope']
    assert len(phones)==1
    phone=phones[0].bounding_box();same(phone.size.X,p['phone_width']);same(phone.size.Z,p['phone_height'])
    phone_centre=(phone.min.Z+phone.max.Z)/2
    same(phone_centre,a['head_bottom']+a['head_height']/2)
    def change(old,new):
        return {'R2.1':round(old,3),'V7':round(new,3),'reduction_percent':round(100*(old-new)/old,2)}
    return {
        'baseline_commit':baseline['source_commit'],
        'metric':'saved native solid volumes; excludes bought-component envelopes',
        'total_printed_solid_volume_mm3':change(old_total,new_total),
        'neck_solid_volume_mm3':change(old_volumes['r2_neck'],neck.volume),
        'tail_solid_volume_mm3':change(old_volumes['r2_tail'],saved['v7_tail'].volume),
        'whole_height_mm':change(baseline['assembled_bounds_mm'][2],bounds.size.Z),
        'whole_depth_mm':change(baseline['assembled_bounds_mm'][1],bounds.size.Y),
        'phone_centre_height_mm':change(baseline['phone_centre_height_mm'],phone_centre),
        'printed_part_count':{'R2.1':len(baseline['parts']),'V7':len(saved)},
        'limits':'Not measured mass, print time, load capacity, thermal performance or physical stability.'}


def verify_branding(p,a,saved):
    """Slice the saved outer relief: ten front glyphs and five rear glyphs."""
    results={}
    slope=(p['body_depth']-p['top_depth'])/(2*(p['cover_top']-p['cover_shoulder']))
    for part,text,z,normal,x_dir,y in (
        ('v7_cover_front','PROMETHEUS',p['team_wordmark_z'],(0,-1,slope),(1,0,0),
         -p['body_depth']/2+slope*(p['team_wordmark_z']-p['cover_shoulder'])),
        ('v7_cover_rear','KITTY',p['robot_wordmark_z'],(0,1,0),(-1,0,0),p['body_depth']/2),
    ):
        face=bd.Plane(origin=(0,y,z-a['deck']),x_dir=x_dir,z_dir=normal)
        # A thin slab lies fully outside the old shell and other reliefs.
        slab=face*bd.Pos(0,0,0.5)*bd.Box(100,12,0.2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
        section=saved[part].intersect(slab)
        glyphs=list(section.solids())
        assert len(glyphs)==len(text),(part,'missing/joined exterior glyphs',len(glyphs))
        assert all(s.is_valid and s.volume>0 for s in glyphs),(part,'invalid wordmark section')
        results[part]={'text':text,'separate_saved_exterior_glyphs':len(glyphs),
                       'slice_outside_shell_mm':[0.5,0.7],
                       'method':'raised lettering fused into the cover; visual spelling/orientation reviewed in native renders'}
    return results


def verify_motor_adjustment(p,a,saved,bodies):
    failures=[];queries=0;washer_areas=[]
    for side,name in ((-1,'v7_motor_left'),(1,'v7_motor_right')):
        own={name,'REFERENCE_ONLY_motor_envelope_'+str(side),'REFERENCE_ONLY_wheel_envelope_'+str(side)}
        group=[(label,solid) for label,solid,_ in bodies if label in own]
        assert len(group)==3,('motor adjustment group',name)
        bolt_x=-side*(p['motor_x']-46)
        for travel in (-p['motor_adjust_y'],0,p['motor_adjust_y']):
            for y in (-25,25):
                bolt=(bd.Pos(bolt_x,y-travel,-1)*bd.Cylinder(p['m3_clearance']/2,p['motor_floor']+2,
                      align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))).solids()[0]
                assert overlap_volume(saved[name],bolt)<0.01,(name,'M3 bolt does not fit slot',travel)
                # Test actual head/washer volumes and bearing area, not only
                # the shaft. The wider cradle needs open rail access here.
                washer=bd.Pos(bolt_x,y-travel,p['motor_floor'])*bd.Cylinder(4,0.8,
                       align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
                head=bd.Pos(bolt_x,y-travel,p['motor_floor']+0.8)*bd.Cylinder(2.75,3,
                     align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
                assert overlap_volume(saved[name],washer.solids()[0])<0.01,(name,'washer blocked',travel)
                assert overlap_volume(saved[name],head.solids()[0])<0.01,(name,'screw head blocked',travel)
                footprint=bd.Pos(bolt_x,y-travel,0)*bd.Cylinder(4,p['motor_floor'],
                          align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
                area=overlap_volume(saved[name],footprint.solids()[0])/p['motor_floor']
                assert area>20,(name,'insufficient sampled washer bearing area',travel,area)
                washer_areas.append(area)
            for label,solid in group:
                moved=(bd.Pos(0,travel,0)*solid).solids()[0]
                bounds=moved.bounding_box(optimal=False)
                for other_label,other,other_bounds in bodies:
                    if other_label in own or not bounds_intersect(bounds,other_bounds):continue
                    queries+=1;volume=overlap_volume(moved,other)
                    if volume>0.01:failures.append((label,travel,other_label,volume))
    assert not failures,('motor adjustment interference',failures)
    for x in (-45,45):
        for dy in (-12,12):assert not saved['v7_base'].is_inside((x,p['electronics_y']+dy,2)),'electronics mounting hole blocked'
    return {'proposed_fore_aft_travel_mm':[-p['motor_adjust_y'],p['motor_adjust_y']],
            'sampled_positions_per_side_mm':[-p['motor_adjust_y'],0,p['motor_adjust_y']],
            'exact_queries':queries,'failures':[],
            'group_moved':'bracket plus its motor and wheel envelopes; opposite side held nominal',
            'slot_checks':'full nominal M3-clearance cylinders clear both saved slots at each sampled position',
            'fastener_access':'8 mm OD x 0.8 mm washer and 5.5 mm OD x 3 mm head envelopes clear the saved rails at all samples',
            'minimum_sampled_washer_bearing_area_mm2':round(min(washer_areas),3),
            'limits':'Sampled positions only; real shaft/hub, cables, fasteners and clamping strength unverified'}


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
        report['parts'][name]={'bounds_mm':[round(s.X,3),round(s.Y,3),round(s.Z,3)],'valid_solids':1,'closed_oriented_mesh':True,'triangles':triangles,'volume_mm3':round(volume,3),'native_volume_mm3':round(solid.volume,3)}
        print('PART PASS',name,flush=True)
    same(saved['v7_base'].bounding_box().size.X,p['body_width'])
    same(saved['v7_base'].bounding_box().size.Y,p['body_depth'])
    same(saved['v7_base'].bounding_box().size.Z,p['base_thickness'])
    same(saved['v7_phone_cradle'].bounding_box().size.X,a['head_width'])
    same(saved['v7_phone_cradle'].bounding_box().size.Y,a['head_height'])
    same(saved['v7_neck'].bounding_box().size.Z,p['neck_height'])
    base=saved['v7_base']
    for x in (-68,68):
        for y in (-65,65):assert not base.is_inside((x,y,2)),('blocked base/cover bore',x,y)
    assert not base.is_inside((0,p['caster_y'],2)),'blocked caster opening'
    neck=saved['v7_neck']
    for z in (1,5,p['neck_height']/2,p['neck_height']-1):
        assert not neck.is_inside((0,0,z)),('blocked cable route',z)
    # The new tie passages must stay open without cutting the main neck wall.
    for x in (-14,14):
        for offset in (-4,0,4):
            assert not neck.is_inside((x+offset,22,14.5)), 'blocked rear tie eye'
        assert neck.is_inside((x,24.5,14.5)), 'missing outer tie-eye web'
        assert neck.is_inside((x,15,17)), 'tie eye detached from neck wall'
    same(neck.bounding_box().size.X,80)
    same(neck.bounding_box().size.Y,58)
    report['rear_neck_tie_eyes']={'count':2,'slot_width_mm':p['neck_tie_slot_width'],
                                  'slot_length_mm':p['neck_tie_slot_length'],
                                  'saved_passages':'open along X; outer webs and wall attachment present',
                                  'limits':'Actual cable/tie fit and strength unverified; not lifting points'}
    report['branding']=verify_branding(p,a,saved)
    sensor=saved['v7_sensor_bracket']
    for x in (-p['sonar_pitch']/2,p['sonar_pitch']/2):
        assert not sensor.is_inside((x,-78.5,p['sonar_z']-a['deck'])),'blocked sonar bore'
    scene=read_scene(ROOT/'STEP'/'v7_complete_draft.step')
    bodies=[]
    for leaf in scene.leaves():
        for solid in leaf.shape().solids():
            assert solid.is_valid and solid.volume>0,leaf.label
            bodies.append((leaf.label,solid,solid.bounding_box(optimal=False)))
    assert len(bodies)==24,('assembly component count',len(bodies))
    report['motor_adjustment']=verify_motor_adjustment(p,a,saved,bodies)
    report['tail_joint']=verify_tail_joint(p,a,saved,bodies)
    failures=[];exact=0;total=0
    for (na,sa,ba),(nb,sb,bb) in combinations(bodies,2):
        total+=1
        if not bounds_intersect(ba,bb):continue
        exact+=1;volume=overlap_volume(sa,sb)
        if volume>0.01:failures.append({'a':na,'b':nb,'overlap_mm3':round(volume,6)})
    report['static_interference']={'body_count':len(bodies),'pairs_considered':total,'exact_queries':exact,'maximum_allowed_mm3':0.01,'failures':failures}
    whole=read_step(ROOT/'STEP'/'v7_complete_draft.step');bounds=whole.bounding_box()
    report['optimization']=compare_revision(p,a,saved,bodies,bounds)
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
