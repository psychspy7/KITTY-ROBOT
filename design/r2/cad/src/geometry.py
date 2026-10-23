"""Plain parameterized factories; no geometry is created during import."""
from __future__ import annotations

from cadgen import build123d as bd


def box(x, y, z):
    return bd.Box(x, y, z, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def base_plate(p):
    d = p['design']
    w, h, t = d['base_width_mm'], d['base_depth_mm'], d['plate_mm']
    shape = box(w, h, t)
    for x in (-w / 2 + 12, w / 2 - 12):
        for y in (-h / 2 + 12, h / 2 - 12):
            cutter = bd.Pos(x, y, -t) * bd.Cylinder(d['fastener_clearance_mm'] / 2, t * 3,
                                                   align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
            shape = shape - cutter
    shape.label = 'DRAFT_base_plate_not_fit_approved'
    return shape


def phone_cradle(p):
    m, d = p['dimensions'], p['design']
    wall, gap = d['wall_mm'], d['fit_clearance_mm']
    inner_w, inner_h = m['phone_width_mm'] + 2 * gap, m['phone_height_mm'] + 2 * gap
    w, h = inner_w + 2 * wall, inner_h + 2 * wall
    depth = m['phone_thickness_mm'] + gap + wall
    rim = d['phone_rim_mm']
    shape = box(w, h, wall) - bd.Pos(0, 0, -wall) * box(inner_w - 2 * rim, inner_h - 2 * rim, wall * 3)
    for x in (-inner_w / 2 - wall / 2, inner_w / 2 + wall / 2):
        shape = shape + bd.Pos(x, 0, 0) * box(wall, h, depth)
    shape = shape + bd.Pos(0, -inner_h / 2 - wall / 2, 0) * box(w, wall, depth)
    shape.label = 'DRAFT_phone_cradle_camera_clearance_unverified'
    return shape


def motor_coupon(p):
    m, d = p['dimensions'], p['design']
    gap, wall, t = d['fit_clearance_mm'], d['wall_mm'], d['plate_mm']
    iw, ih = m['motor_width_mm'] + 2 * gap, m['motor_height_mm'] + 2 * gap
    shape = box(iw + 2 * wall, ih + 2 * wall, t) - bd.Pos(0, 0, -t) * box(iw, ih, t * 3)
    shape.label = 'DRAFT_motor_cross_section_coupon_not_mount'
    return shape


def sensor_coupon(p):
    m, d = p['dimensions'], p['design']
    pitch, diameter = m['sonar_pitch_mm'], m['sonar_can_diameter_mm'] + 2 * d['fit_clearance_mm']
    t, wall = d['plate_mm'], d['wall_mm']
    shape = box(pitch + diameter + 2 * wall, diameter + 2 * wall, t)
    for x in (-pitch / 2, pitch / 2):
        shape = shape - bd.Pos(x, 0, -t) * bd.Cylinder(diameter / 2, t * 3,
                                                      align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    shape.label = 'DRAFT_sonar_face_coupon_not_mount'
    return shape
