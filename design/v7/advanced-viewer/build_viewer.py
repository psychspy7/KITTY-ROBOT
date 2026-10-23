"""Build a fully offline GPU viewer from the verified V7 meshes and saved STEP.

No CAD design or manufacturing geometry is changed by this presentation tool.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from cadgen import build123d as bd, read_scene

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'src'))
from settings import load, datums, tail_placement


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix(location):
    transform = location.wrapped.Transformation()
    return [[transform.Value(row, column) for column in range(1, 5)]
            for row in range(1, 4)] + [[0, 0, 0, 1]]


def bounds(raw):
    dtype = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    mesh = np.frombuffer(raw, dtype=dtype, offset=84)
    points = mesh['vertices']
    return [points.min(axis=(0, 1)).tolist(), points.max(axis=(0, 1)).tolist()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    service = args.service.resolve()
    manifest = json.loads((service / 'ARTIFACTS-SHA256.json').read_text())
    # Confirm this viewer uses the exact released mesh revisions.
    p = load(); a = datums(p)
    verified = json.loads((ROOT / 'checks/last-verified.json').read_text())
    for relative, digest in verified['input_sources_sha256'].items():
        assert sha(ROOT / relative) == digest, 'CAD input changed after verification: ' + relative
    saved_scene = read_scene(ROOT / 'STEP/v7_complete_draft.step')
    saved_shapes = {leaf.label: leaf.shape() for leaf in saved_scene.leaves()}
    head = bd.Pos(0, 8, a['head_bottom'] + a['head_height']/2) * bd.Rot(90, 0, 0)
    entries = [
        ('v7_base', 'Base chassis', bd.Pos(0, 0, p['base_z']), '#374652', [0, 0, -35]),
        ('v7_cover_front', 'PROMETHEUS · front shell', bd.Pos(0, 0, a['deck']), '#ede9df', [0, -105, 15]),
        ('v7_cover_rear', 'KITTY · rear shell', bd.Pos(0, 0, a['deck']), '#ede9df', [0, 105, 15]),
        ('v7_motor_left', 'Left adjustable motor cradle', bd.Pos(-p['motor_x'], p['motor_y'], a['deck']), '#ed9b4e', [-65, 0, 0]),
        ('v7_motor_right', 'Right adjustable motor cradle', bd.Pos(p['motor_x'], p['motor_y'], a['deck']), '#ed9b4e', [65, 0, 0]),
        ('v7_battery_tray', 'Optional internal battery tray', bd.Pos(0, p['battery_y'], a['deck']), '#8eaa88', [0, 0, 55]),
        ('v7_electronics_deck', 'Electronics deck', bd.Pos(0, p['electronics_y'], a['deck']), '#85aeb4', [0, -25, 72]),
        ('v7_caster_bridge', 'Caster bridge', bd.Pos(0, p['caster_y'], a['deck']), '#71828e', [0, -40, -15]),
        ('v7_sensor_bracket', 'Front range-sensor bracket', bd.Pos(0, 0, a['deck']), '#ed9b4e', [0, -80, 0]),
        ('v7_neck', 'Fixed neck · cable-tie eyes', bd.Pos(0, 0, p['cover_top']), '#e2ddd1', [0, 0, 78]),
        ('v7_phone_cradle', 'Landscape phone cradle', head, '#eee9de', [0, 0, 125]),
        ('v7_phone_cap', 'Removable phone retaining cap', head * bd.Pos(0, 0, 3.4), '#394852', [0, -70, 125]),
        ('v7_tail', 'Detachable keyed tail', tail_placement(p), '#ed9b4e', [0, 145, 45]),
    ]
    parts = []
    for identifier, title, placement, color, explode in entries:
        relative = 'STL_PARTS/' + identifier + '.stl'
        path = service / relative
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == manifest[relative], relative
        local_bounds = bounds(raw)
        lo, hi = np.array(local_bounds)
        corners = np.array([[x, y, z, 1.] for x in (lo[0], hi[0])
                            for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        posed = corners @ np.array(matrix(placement)).T
        native = saved_shapes[identifier].bounding_box()
        actual = np.array([[native.min.X, native.min.Y, native.min.Z],
                           [native.max.X, native.max.Y, native.max.Z]])
        assert np.max(np.abs(np.array([posed[:, :3].min(axis=0), posed[:, :3].max(axis=0)]) - actual)) < .03, identifier
        parts.append(dict(id=identifier, title=title, kind='printed', color=color,
                          optional=identifier == 'v7_battery_tray', pose=matrix(placement),
                          explode=explode, bounds=local_bounds, sha256=digest,
                          mesh=base64.b64encode(raw).decode()))
    # Use the *placed* saved native solids, never illustrative replacement shapes.
    for leaf in saved_scene.leaves():
        if not leaf.label.startswith('REFERENCE_ONLY_'):
            continue
        name = leaf.label
        optional = 'AA_holder' in name
        if 'wheel' in name:
            title, color = 'Purchased wheel · ' + ('left' if name.endswith('-1') else 'right'), '#26333c'
        elif 'motor' in name:
            title, color = 'BO motor envelope · ' + ('left' if name.endswith('-1') else 'right'), '#dab847'
        elif 'phone' in name:
            title, color = 'OPPO phone envelope', '#0e1d26'
        elif 'display_graphic' in name:
            title, color = 'Phone display · eye', '#68e8d2'
        elif 'sonar' in name:
            title, color = 'HC-SR04 transducer envelope', '#adb9c1'
        elif 'caster' in name:
            title, color = 'Purchased caster envelope', '#657582'
        else:
            title, color = 'Unselected AA-holder envelope', '#7b957a'
        target = args.out / (name + '.stl')
        bd.export_stl(leaf.shape(), target, tolerance=.003, angular_tolerance=.05)
        raw = target.read_bytes()
        lo, hi = np.array(bounds(raw))
        centre = (lo + hi) / 2
        explode = [float(np.sign(centre[0]) * 80 if abs(centre[0]) > 50 else 0),
                   float(-55 if 'sonar' in name else 0),
                   float(125 if ('phone' in name or 'display' in name) else 20)]
        parts.append(dict(id=name, title=title, kind='reference', color=color,
                          optional=optional, pose=np.eye(4).tolist(), explode=explode,
                          bounds=[lo.tolist(), hi.tolist()], sha256=sha(target),
                          mesh=base64.b64encode(raw).decode()))
        target.unlink()  # Reference hardware is embedded for viewing only.
    assert len(parts) == 24
    page = (HERE / 'viewer.html.in').read_text()
    three = (HERE / 'vendor/three.min.js').read_text()
    orbit = (HERE / 'vendor/OrbitControls.js').read_text()
    orbit = re.sub(r'import\s*\{([\s\S]*?)\}\s*from\s*[\'"]three[\'"];', r'const {\1} = THREE;', orbit, count=1)
    orbit = re.sub(r'export\s*\{\s*OrbitControls\s*\};?', 'window.OrbitControls = OrbitControls;', orbit)
    assert not re.search(r'^import\s', orbit, flags=re.M)
    replacements = {
        '__THREE__': three, '__ORBIT__': orbit,
        '__APP__': (HERE / 'viewer.js').read_text(),
        '__STYLE__': (HERE / 'viewer.css').read_text(),
        '__MODEL__': json.dumps({'parts': parts, 'revision': 'V7_SERVICE_REVISION_FIT_PENDING',
                               'units': 'mm', 'physicalFitVerified': False}, separators=(',', ':')),
        '__LICENSE__': (HERE / 'vendor/THREE-LICENSE.txt').read_text(),
    }
    for token, stem in [('ISO', 'assembly-hero'), ('FRONT', 'assembly-front'),
                        ('REAR', 'assembly-rear-angle'), ('INSIDE', 'interior')]:
        path = service / 'snapshots' / (stem + '.png')
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == manifest['snapshots/' + stem + '.png']
        replacements['__' + token + '__'] = 'data:image/png;base64,' + base64.b64encode(raw).decode()
    for key, value in replacements.items():
        # Prevent embedded JS/data from terminating its enclosing HTML script.
        if key in ('__THREE__', '__ORBIT__', '__APP__', '__MODEL__'):
            value = value.replace('</script', '<\\/script')
        page = page.replace(key, value)
    target = args.out / 'KITTY-V7-3D-STUDIO.html'
    target.write_text(page)
    evidence = dict(html_sha256=sha(target), bytes=target.stat().st_size,
                    source_sha256={str(f.relative_to(HERE)): sha(f) for f in HERE.rglob('*')
                                   if f.is_file() and '__pycache__' not in str(f)},
                    parts=[{k: v for k, v in part.items() if k != 'mesh'} for part in parts],
                    cad_step_sha256=sha(ROOT / 'STEP/v7_complete_draft.step'),
                    units='mm', changes_to_CAD_geometry=False)
    (args.out / 'MODEL-PROVENANCE.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'file': str(target), 'bytes': target.stat().st_size, 'parts': len(parts)}))


if __name__ == '__main__':
    main()
