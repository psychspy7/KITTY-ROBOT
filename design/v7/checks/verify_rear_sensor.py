"""Verify the saved rear mount, sensor envelopes, sight lines and service access."""
from __future__ import annotations
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import sys

from cadgen import build123d as bd, read_scene, read_step
from cadgen.geometry import overlap_volume as native_overlap_volume

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from settings import load, datums
from rear_sensor import rear_settings, mount_bottom
from shapes import box, cylinder, wordmark
from verify_exports import mesh, bounds_intersect


def overlap_volume(a,b):
    return native_overlap_volume(a.solids()[0],b.solids()[0])


def main():
    p = load(); q = rear_settings()
    report = {'revision':'V7.1_DUAL_ULTRASONIC_FIT_PENDING','parts':{}}
    baseline = json.loads((ROOT/'checks/last-verified.json').read_text())
    for relative,digest in baseline['input_sources_sha256'].items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
    report['baseline_CAD_inputs_unchanged'] = True
    for name in ('v7_rear_sensor_bracket','v7_fit_rear_sensor_face'):
        solid = read_step(ROOT/'STEP'/(name+'.step'))
        assert len(solid.solids())==1 and solid.is_valid and solid.volume>0,name
        b=solid.bounding_box(); assert abs(b.min.Z)<1e-6
        assert all(s<=v for s,v in zip((b.size.X,b.size.Y,b.size.Z),(p['printer_x'],p['printer_y'],p['printer_z'])))
        bd.export_stl(solid,ROOT/'STL'/(name+'.stl'),tolerance=.003,angular_tolerance=.05)
        triangles,volume=mesh(ROOT/'STL'/(name+'.stl'))
        assert abs(volume-solid.volume)<max(2,solid.volume*.001)
        report['parts'][name]={'valid_connected_solids':1,'closed_oriented_mesh':True,
            'triangles':triangles,'volume_mm3':round(volume,3),
            'bounds_mm':[round(v,3) for v in (b.size.X,b.size.Y,b.size.Z)]}
        offset = mount_bottom(p,q) if name=='v7_rear_sensor_bracket' else q['sensor_z']-q['panel_height']/2-4.5
        for x in (q['sensor_x']-q['can_pitch']/2,q['sensor_x']+q['can_pitch']/2):
            for delta,expected in ((-.01,False),(.01,True)):
                probe=(x+q['can_diameter']/2+q['radial_clearance']+delta,
                       q['panel_back_y']+1.5,q['sensor_z']-offset)
                assert solid.is_inside(probe)==expected,(name,'can-bore edge',probe)
        for x in (q['sensor_x']-25.5,q['sensor_x']+25.5):
            assert not solid.is_inside((x,q['panel_back_y']+1.5,q['sensor_z']-offset)),(name,'tie slot')
        assert not solid.is_inside((q['sensor_x'],97.5,q['sensor_z']-15-offset)),(name,'header exit')
    scene=read_scene(ROOT/'STEP/v7_dual_ultrasonic.step')
    bodies=[]
    for leaf in scene.leaves():
        for solid in leaf.shape().solids():
            assert solid.is_valid and solid.volume>0,leaf.label
            bodies.append((leaf.label,solid,solid.bounding_box(optimal=False)))
    assert len(bodies)==28,[(name,round(s.volume,1)) for name,s,_ in bodies]
    assert len([name for name,_,_ in bodies if name.startswith('REFERENCE_ONLY_sonar_can_')])==2
    assert len([name for name,_,_ in bodies if name.startswith('REFERENCE_ONLY_rear_sonar_can_')])==2
    assert all(any(name==part for name,_,_ in bodies) for part in ('v7_sensor_bracket','v7_rear_sensor_bracket'))
    report['ultrasonic_modules']={'front':1,'rear':1,'transducers_per_module':2,'printed_mounts':2}
    saved={name:solid for name,solid,_ in bodies}
    failures=[];exact=0
    for (na,sa,ba),(nb,sb,bb) in combinations(bodies,2):
        if not bounds_intersect(ba,bb):continue
        exact+=1;v=overlap_volume(sa,sb)
        if v>.01:failures.append({'a':na,'b':nb,'overlap_mm3':round(v,5)})
    report['static_interference']={'bodies':len(bodies),'pairs':len(bodies)*(len(bodies)-1)//2,
                                    'exact_queries':exact,'failures':failures}
    assert not failures,failures
    bracket=saved['v7_rear_sensor_bracket']
    for x in (-68,68):
        for z in (mount_bottom(p,q)+.5,p['base_z']-.5):
            assert not bracket.is_inside((x,65,z)),('rear mount bore',x,z)
        shank=cylinder(p['m3_clearance']/2,25,x,65,mount_bottom(p,q)-1)
        for name in ('v7_base','v7_cover_rear','v7_rear_sensor_bracket'):
            assert overlap_volume(saved[name],shank)<.01,('bolt path',name,x)
        washer=cylinder(4,.8,x,65,mount_bottom(p,q)-.8)
        head=cylinder(2.75,3,x,65,mount_bottom(p,q)-3.8)
        for name,solid,_ in bodies:
            assert overlap_volume(solid,washer)<.01,('washer',name,x)
            assert overlap_volume(solid,head)<.01,('bolt head',name,x)
    report['mounting']={'shared_existing_bores_mm':[[-68,65],[68,65]],
        'washer_envelope_mm':[8,.8],'head_envelope_mm':[5.5,3],
        'nominal_head_ground_clearance_mm':round(mount_bottom(p,q)-3.8,2),
        'bolt_note':'3 mm extra bracket grip plus actual washer stack; actual screw length/engagement unverified'}
    new=[(n,s,b) for n,s,b in bodies if n=='v7_rear_sensor_bracket' or n.startswith('REFERENCE_ONLY_rear_sonar')]
    assert len(new)==4
    travel_checks=0
    for side,label in ((-1,'left'),(1,'right')):
        group=['v7_motor_'+label,'REFERENCE_ONLY_motor_envelope_'+str(side),'REFERENCE_ONLY_wheel_envelope_'+str(side)]
        for distance in (-p['motor_adjust_y'],0,p['motor_adjust_y']):
            for moving in group:
                moved=(bd.Pos(0,distance,0)*saved[moving]).solids()[0]
                for name,solid,_ in new:
                    travel_checks+=1
                    assert overlap_volume(moved,solid)<.01,('motor travel/new rear module',side,distance,moving,name)
    report['motor_adjustment_against_rear_module']={'positions_mm':[-p['motor_adjust_y'],0,p['motor_adjust_y']],
                                                  'exact_checks':travel_checks,'failures':[]}
    assert not bracket.is_inside((q['post_x'],q['post_back_y']+q['post_depth']/2,40)),'cable-tie eye blocked'
    for x in (q['sensor_x']-19,q['sensor_x']+19):
        assert bracket.is_inside((x,93.5,q['sensor_z']-q['board_height']/2-1)),'lower PCB saddle missing'
    # Service-hole rectangular approach corridors, with a small edge margin.
    for label,x,z,w,h in (('main',-12,44,34,20),('right',43,44,18,16)):
        corridor=box(w+1,65,h+1,x,112.5,z-(h+1)/2)
        for name,solid,_ in new:
            assert overlap_volume(solid,corridor)<.01,('service access',label,name)
    letters=wordmark(p,'KITTY',p['robot_font_size'],p['robot_wordmark_z'],False).bounding_box()
    corridor=box(letters.size.X+1,120,letters.size.Z+1,0,145,(letters.min.Z+letters.max.Z)/2-(letters.size.Z+1)/2)
    for name,solid,_ in new:
        assert overlap_volume(solid,corridor)<.01,('rear branding visibility',name)
    report['service_and_branding']='Both existing rear service openings and rearward KITTY sight corridor clear of new parts/envelopes.'
    tail=saved['v7_tail']
    for distance in (0,6,12,18,24,35):
        moved=(bd.Pos(0,distance,0)*tail).solids()[0]
        for name,solid,_ in new:
            assert overlap_volume(moved,solid)<.01,('tail withdrawal',distance,name)
    report['tail_removal_positions_mm']=[0,6,12,18,24,35]
    for distance in (0,8,16,30):
        for name,solid,_ in new:
            moved=(bd.Pos(0,distance,0)*solid).solids()[0]
            for other,part,_ in bodies:
                if any(other==own for own,_,_ in new):continue
                if not bounds_intersect(moved.bounding_box(optimal=False),part.bounding_box(optimal=False)):continue
                assert overlap_volume(moved,part)<.01,('rear bracket withdrawal',distance,name,other)
    report['bracket_removal_positions_mm']=[0,8,16,30]
    # Assemble the module onto the detached bracket before putting it on the body.
    # The body intentionally is not part of this bench-installation path.
    for distance in (-16,-8,-4,0):
        for name,solid,_ in new:
            if name=='v7_rear_sensor_bracket':continue
            moved=(bd.Pos(0,distance,0)*solid).solids()[0]
            assert overlap_volume(moved,bracket)<.01,('module bench insertion',distance,name)
    report['module_bench_installation_positions_mm']=[-16,-8,-4,0]
    cones=[]
    for side in (-1,1):
        origin=(q['sensor_x']+side*q['can_pitch']/2,
                q['board_back_y']+q['board_thickness']+q['can_length']+.2,q['sensor_z'])
        radius=q['can_diameter']/2;length=q['detection_review_length']
        cone=(bd.Pos(*origin)*bd.Rot(-90,0,0)*bd.Cone(radius,radius+length*math.tan(math.radians(q['assumed_detection_half_angle_deg'])),length,
              align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)))
        for name,solid,b in bodies:
            if bounds_intersect(cone.bounding_box(optimal=False),b):
                assert overlap_volume(cone,solid)<.01,('rear sight envelope',side,name)
        cones.append({'can_x_mm':origin[0],'origin_y_mm':origin[1],'half_angle_deg':q['assumed_detection_half_angle_deg'],'length_mm':length})
    report['rear_sight_envelopes']=cones
    report['limits']='Generic module assumptions; geometric sight envelopes are not measured acoustic coverage. Actual PCB/can/header/tie fit, fasteners, material, print profile and strength require physical checks.'
    inputs=['rear-sensor-parameters.json', 'src/rear_sensor.py', 'src/v7_rear_sensor_bracket.py',
            'src/v7_fit_rear_sensor_face.py', 'src/v7_rear_sensor_reference.py',
            'src/v7_dual_ultrasonic.py', 'checks/verify_rear_sensor.py']
    report['source_sha256']={relative:hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() for relative in inputs}
    report['STL_sha256']={name:hashlib.sha256((ROOT/'STL'/(name+'.stl')).read_bytes()).hexdigest() for name in report['parts']}
    path=ROOT/'checks/rear-sensor-verified.json'
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
