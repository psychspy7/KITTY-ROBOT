"""Explicit proposed dimensions and unresolved physical inputs, in millimetres."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    data = json.loads((ROOT / 'parameters.json').read_text())
    if data['units'] != 'mm' or data['release'] != 'DRAFT_NOT_FIT_APPROVED':
        raise ValueError('This entrypoint exports an unmeasured draft only')
    p = data['dimensions']
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or
           not math.isfinite(v) for v in p.values()):
        raise ValueError('Dimensions must be finite numbers')
    for name, value in p.items():
        if name not in ('caster_y','electronics_y') and value <= 0:
            raise ValueError('Expected positive dimension: ' + name)
    if p['sonar_pitch'] <= p['sonar_diameter'] + 2*p['fit_gap']:
        raise ValueError('Clearance-expanded sonar holes overlap')
    if p['base_z'] + p['base_thickness'] + p['motor_floor'] + p['shaft_z'] != p['wheel_diameter']/2:
        raise ValueError('Assumed motor shaft and wheel ground plane disagree')
    if p['wall'] < 3:
        raise ValueError('Draft shell design requires at least 3 mm nominal wall')
    if p['motor_adjust_y'] > 2:
        raise ValueError('Motor travel above +/-2 mm needs a new interference review')
    return p


def datums(p):
    gap = p['fit_gap']
    return {
        'deck': p['base_z'] + p['base_thickness'],
        'head_bottom': p['cover_top'] + p['neck_height'],
        'head_width': p['phone_width'] + 2*gap + 2*p['phone_margin'],
        'head_height': p['phone_height'] + 2*gap + 2*p['phone_margin'],
        'head_depth': p['phone_thickness'] + gap + p['wall'] + 3,
        'wheel_y': p['motor_y'] + p['shaft_y'],
        'axle_z': p['wheel_diameter']/2,
        'tail_y': p['body_depth']/2 + p['tail_socket_projection'],
    }


def tail_placement(p):
    """Flat-print XY profile -> rearward Y/upward Z, thickness along X."""
    from cadgen import build123d as bd
    return (bd.Pos(-p['tail_thickness']/2, datums(p)['tail_y'], p['tail_height'])
            * bd.Rot(0,0,90) * bd.Rot(90,0,0))
