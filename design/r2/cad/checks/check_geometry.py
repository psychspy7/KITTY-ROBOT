"""Check saved draft STEP/STL outputs; requires the pinned CAD environment."""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import struct

from cadgen import read_step

ROOT = Path(__file__).resolve().parents[1]


def mesh_check(path):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    assert len(data) == 84 + count * 50, f'{path}: expected binary STL'
    edges, volume = Counter(), 0.0
    for index in range(count):
        values = struct.unpack_from('<12fH', data, 84 + 50 * index)
        a, b, c = [tuple(values[start:start + 3]) for start in (3, 6, 9)]
        assert all(math.isfinite(v) for vertex in (a, b, c) for v in vertex)
        for u, v in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((u, v)))] += 1
        volume += (a[0] * (b[1]*c[2] - b[2]*c[1])
                   + a[1] * (b[2]*c[0] - b[0]*c[2])
                   + a[2] * (b[0]*c[1] - b[1]*c[0])) / 6
    assert count > 0 and all(n == 2 for n in edges.values()), f'{path}: open/nonmanifold edges'
    assert volume > 0, f'{path}: inverted or zero-volume mesh'
    return {'triangles': count, 'closed_edges': True, 'signed_volume_mm3': round(volume, 3)}


def main():
    p = json.loads((ROOT / 'parameters.example.json').read_text())
    m, d = p['dimensions'], p['design']
    gap, wall, t = d['fit_clearance_mm'], d['wall_mm'], d['plate_mm']
    phone_w, phone_h = m['phone_width_mm'] + 2*gap + 2*wall, m['phone_height_mm'] + 2*gap + 2*wall
    motor_w, motor_h = m['motor_width_mm'] + 2*gap, m['motor_height_mm'] + 2*gap
    sonar_d = m['sonar_can_diameter_mm'] + 2*gap
    sizes = {
        'draft_base': (d['base_width_mm'], d['base_depth_mm'], t),
        'draft_phone_cradle': (phone_w, phone_h, m['phone_thickness_mm'] + gap + wall),
        'draft_motor_coupon': (motor_w + 2*wall, motor_h + 2*wall, t),
        'draft_sensor_coupon': (m['sonar_pitch_mm'] + sonar_d + 2*wall, sonar_d + 2*wall, t),
    }
    volumes = {
        'draft_base': (d['base_width_mm'] * d['base_depth_mm'] - 4*math.pi*(d['fastener_clearance_mm']/2)**2)*t,
        'draft_motor_coupon': ((motor_w + 2*wall)*(motor_h + 2*wall) - motor_w*motor_h)*t,
        'draft_sensor_coupon': ((m['sonar_pitch_mm'] + sonar_d + 2*wall)*(sonar_d + 2*wall) - 2*math.pi*(sonar_d/2)**2)*t,
    }
    report = {'status': 'draft_geometry_checked', 'physical_fit': 'NOT_VERIFIED', 'parts': {}}
    for name, expected in sizes.items():
        shape = read_step(ROOT / 'STEP' / (name + '.step'))
        solids = shape.solids()
        assert len(solids) == 1 and solids[0].is_valid and solids[0].volume > 0, name
        size = shape.bounding_box().size
        actual = (size.X, size.Y, size.Z)
        assert all(abs(a-b) < 1e-5 for a, b in zip(actual, expected)), (name, actual, expected)
        volume = shape.volume
        if name in volumes:
            assert abs(volume - volumes[name]) < 1e-3, (name, 'through-hole/coupon volume')
        mesh = mesh_check(ROOT / 'STL' / (name + '.stl'))
        assert abs(mesh['signed_volume_mm3'] - volume) < 1, (name, 'mesh volume')
        report['parts'][name] = {'bounds_mm': [round(x, 3) for x in actual], 'solid_count': 1, **mesh}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
