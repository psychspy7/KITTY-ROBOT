from cadgen import build123d as bd, step
from settings import load, datums, tail_placement
from v3_base import v3_base
from v3_cover_front import v3_cover_front
from v3_cover_rear import v3_cover_rear
from v3_motor_left import v3_motor_left
from v3_motor_right import v3_motor_right
from v3_battery_tray import v3_battery_tray
from v3_electronics_deck import v3_electronics_deck
from v3_caster_bridge import v3_caster_bridge
from v3_sensor_bracket import v3_sensor_bracket
from v3_neck import v3_neck
from v3_phone_cradle import v3_phone_cradle
from v3_phone_cap import v3_phone_cap
from v3_tail import v3_tail


@step(out='../STEP/v3_printed_assembly.step')
def v3_printed_assembly():
    p=load();a=datums(p)
    head=bd.Pos(0,8,a['head_bottom']+a['head_height']/2)*bd.Rot(90,0,0)
    placed=[
        bd.Pos(0,0,p['base_z'])*v3_base(),
        bd.Pos(0,0,a['deck'])*v3_cover_front(),
        bd.Pos(0,0,a['deck'])*v3_cover_rear(),
        bd.Pos(-p['motor_x'],p['motor_y'],a['deck'])*v3_motor_left(),
        bd.Pos(p['motor_x'],p['motor_y'],a['deck'])*v3_motor_right(),
        bd.Pos(0,p['battery_y'],a['deck'])*v3_battery_tray(),
        bd.Pos(0,-32,a['deck'])*v3_electronics_deck(),
        bd.Pos(0,p['caster_y'],a['deck'])*v3_caster_bridge(),
        bd.Pos(0,0,a['deck'])*v3_sensor_bracket(),
        bd.Pos(0,0,p['cover_top'])*v3_neck(),
        head*v3_phone_cradle(),
        head*bd.Pos(0,0,3.4)*v3_phone_cap(),
        tail_placement(p)*v3_tail(),
    ]
    return bd.Compound(children=placed,label='V3_DRAFT_printed_parts_assembly_NOT_one_piece_print')


if __name__=='__main__':
    v3_printed_assembly()
