"""Measurement intake independent of the optional CAD kernel."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = (
    'motor_length_mm', 'motor_width_mm', 'motor_height_mm',
    'wheel_diameter_mm', 'wheel_width_mm', 'caster_height_mm',
    'phone_width_mm', 'phone_height_mm', 'phone_thickness_mm',
    'battery_width_mm', 'battery_depth_mm', 'battery_height_mm',
    'sonar_pitch_mm', 'sonar_can_diameter_mm',
    'printer_x_mm', 'printer_y_mm', 'printer_z_mm',
)
DESIGN = ('base_width_mm', 'base_depth_mm', 'plate_mm', 'wall_mm',
          'fit_clearance_mm', 'fastener_clearance_mm', 'phone_rim_mm')


class ParameterError(ValueError):
    pass


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def validate(data, require_measured=True):
    if data.get('schema_version') != 1 or data.get('units') != 'mm':
        raise ParameterError('Expected schema version 1 and millimetres')
    if require_measured and data.get('kind') != 'measured':
        raise ParameterError('Example fixtures cannot be used as measured input')
    dims, design = data.get('dimensions', {}), data.get('design', {})
    invalid = [key for key in DIMENSIONS if not positive(dims.get(key))]
    invalid += [key for key in DESIGN if not positive(design.get(key))]
    if invalid:
        raise ParameterError('Missing/invalid dimensions: ' + ', '.join(invalid))
    if require_measured:
        evidence = data.get('evidence', {})
        missing = [key for key in DIMENSIONS if not isinstance(evidence.get(key), str) or not evidence[key].strip()]
        if missing:
            raise ParameterError('Individual measurement evidence required: ' + ', '.join(missing))
    wall, clear, rim = design['wall_mm'], design['fit_clearance_mm'], design['phone_rim_mm']
    if 2 * rim >= min(dims['phone_width_mm'], dims['phone_height_mm']):
        raise ParameterError('Phone rim consumes the camera/access opening')
    if dims['sonar_pitch_mm'] <= dims['sonar_can_diameter_mm']:
        raise ParameterError('Sonar transducer openings overlap')
    hole = design['fastener_clearance_mm']
    if hole >= 12 or min(design['base_width_mm'], design['base_depth_mm']) <= 24 + hole:
        raise ParameterError('Fastener pattern cannot fit base')
    sizes = [
        (design['base_width_mm'], design['base_depth_mm'], design['plate_mm']),
        (dims['phone_width_mm'] + 2 * (wall + clear), dims['phone_height_mm'] + 2 * (wall + clear), dims['phone_thickness_mm'] + wall + clear),
        (dims['motor_width_mm'] + 2 * (wall + clear), dims['motor_height_mm'] + 2 * (wall + clear), design['plate_mm']),
        (dims['sonar_pitch_mm'] + dims['sonar_can_diameter_mm'] + 2 * wall + 2 * clear, dims['sonar_can_diameter_mm'] + 2 * wall + 2 * clear, design['plate_mm']),
    ]
    for x, y, z in sizes:
        if x > dims['printer_x_mm'] or y > dims['printer_y_mm'] or z > dims['printer_z_mm']:
            raise ParameterError('A part exceeds the printer bed in its declared export orientation')
    return data


def load(name='parameters.measured.json', require_measured=True):
    with (ROOT / name).open(encoding='utf-8') as stream:
        return validate(json.load(stream), require_measured=require_measured)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--example', action='store_true', help='validate labelled example values only')
    args = parser.parse_args()
    try:
        load('parameters.example.json' if args.example else 'parameters.measured.json', not args.example)
    except (ParameterError, OSError, ValueError) as error:
        print(error)
        raise SystemExit(2)
    print('Example input valid; NOT MEASURED' if args.example else 'Measurement fields complete; physical fit/appearance approval still required')
