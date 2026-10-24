"""Replaceable rear HC-SR04 saddle, attached through existing chassis holes."""
from __future__ import annotations

import json
import math
from pathlib import Path

from cadgen import build123d as bd
from shapes import box, cylinder, colored

ROOT = Path(__file__).resolve().parents[1]


def rear_settings():
    data = json.loads((ROOT / 'rear-sensor-parameters.json').read_text())
    assert data['units'] == 'mm' and data['release'] == 'DRAFT_NOT_FIT_APPROVED'
    q = data['dimensions']
    assert all(isinstance(v, (int, float)) and not isinstance(v, bool)
               and math.isfinite(v) and v > 0 for v in q.values())
    assert q['panel_thickness'] >= 3 and q['bridge_thickness'] >= 3
    assert q['can_pitch'] > q['can_diameter'] + 2*q['radial_clearance']
    return q


def mount_bottom(p, q):
    return p['base_z'] - q['bridge_thickness']


def rear_panel(q):
    cx = (q['panel_left_x'] + q['panel_right_x'])/2
    width = q['panel_right_x'] - q['panel_left_x']
    y = q['panel_back_y'] + q['panel_thickness']/2
    panel = (bd.Pos(cx, y, q['sensor_z']) * bd.extrude(
        bd.Plane.XZ * bd.RectangleRounded(width, q['panel_height'], 3),
        amount=q['panel_thickness']/2, both=True))
    for x in (q['sensor_x']-q['can_pitch']/2, q['sensor_x']+q['can_pitch']/2):
        panel -= (bd.Pos(x, y-5, q['sensor_z']) * bd.Rot(-90,0,0)
                  * cylinder(q['can_diameter']/2+q['radial_clearance'], 10))
    for x in (q['sensor_x']-25.5, q['sensor_x']+25.5):
        slot = bd.Plane.XZ * bd.SlotOverall(q['tie_slot_length'], q['tie_slot_width'], rotation=90)
        panel -= bd.Pos(x, y, q['sensor_z']) * bd.extrude(slot, amount=6, both=True)
    # Header and cable leave below the middle of the PCB, between the saddles.
    panel -= box(16, 16, 9.5, q['sensor_x'], y, q['sensor_z']-18.5)
    return panel


def rear_bracket(p, q):
    bottom = mount_bottom(p,q)
    shape = box(q['bridge_width'], q['bridge_depth'], q['bridge_thickness'],
                0, q['bridge_y'], bottom)
    foot = bd.Polygon((64,65),(73,62),(85,90),(85,101),(77,101),(77,93),align=None)
    shape += bd.Pos(0,0,bottom) * bd.extrude(foot, amount=q['bridge_thickness'])
    post_bottom = p['base_z']
    shape += box(q['post_width'],q['post_depth'],q['sensor_z']+10-post_bottom,
                 q['post_x'],q['post_back_y']+q['post_depth']/2,post_bottom)
    brace = bd.Plane.YZ * bd.Polygon((78,post_bottom),(99,post_bottom),(99,q['sensor_z']+4),align=None)
    shape += bd.Pos(q['post_x']-q['post_width']/2,0,0) * bd.extrude(brace,amount=q['post_width'])
    shape += rear_panel(q)
    board_bottom = q['sensor_z']-q['board_height']/2
    for x in (q['sensor_x']-19, q['sensor_x']+19):
        shape += box(8,11,3,x,93.5,board_bottom-3)
    for x in (q['sensor_x']-21,q['sensor_x']+21):
        shape += box(3,1.4,3,x,95.3,board_bottom)
    for x in (-68,68):
        shape -= cylinder(p['m3_clearance']/2, q['bridge_thickness']+2,x,q['bridge_y'],bottom-1)
    # A transverse hole in the outer post provides cable strain relief.
    shape -= (bd.Pos(q['post_x']-6,q['post_back_y']+q['post_depth']/2,40)
              * bd.Rot(0,90,0) * cylinder(p['m3_clearance']/2,12))
    return colored(shape,'rear_sensor_saddle_DRAFT_generic_HCSR04','#DE9E59')


def rear_face_coupon(q):
    """Stable upright gauge using the same panel axes as the complete bracket."""
    shape = rear_panel(q)
    for left,right in ((q['panel_left_x'],q['sensor_x']-8),
                       (q['sensor_x']+8,q['panel_right_x'])):
        shape += box(right-left,10,4.5,(left+right)/2,
                     q['panel_back_y']+q['panel_thickness']/2,
                     q['sensor_z']-q['panel_height']/2-4.5)
    return colored(shape,'rear_sensor_face_fit_coupon_NOT_robot_part','#DE9E59')


def rear_hardware(q):
    x = q['sensor_x']; z = q['sensor_z']; y = q['board_back_y']
    board = box(q['board_width'],q['board_thickness'],q['board_height'],
                x,y+q['board_thickness']/2,z-q['board_height']/2)
    board += box(38,6,14,x,y-3,z-7)
    board += box(14,5,8,x,y+.8,z-18)
    result = [colored(board,'REFERENCE_ONLY_rear_sonar_PCB_envelope','#507D70')]
    for side in (-1,1):
        can = (bd.Pos(x+side*q['can_pitch']/2,y+q['board_thickness'],z)
               * bd.Rot(-90,0,0) * cylinder(q['can_diameter']/2,q['can_length']))
        result.append(colored(can,'REFERENCE_ONLY_rear_sonar_can_'+('left' if side<0 else 'right'),'#A4AFB5'))
    return bd.Compound(children=result,label='REFERENCE_ONLY_rear_HCSR04_assumed_envelopes')
