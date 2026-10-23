from cadgen import build123d as bd, step
from settings import load, datums, tail_placement
from v7_base import v7_base
from v7_cover_front import v7_cover_front
from v7_cover_rear import v7_cover_rear
from v7_motor_left import v7_motor_left
from v7_motor_right import v7_motor_right
from v7_battery_tray import v7_battery_tray
from v7_electronics_deck import v7_electronics_deck
from v7_caster_bridge import v7_caster_bridge
from v7_sensor_bracket import v7_sensor_bracket
from v7_neck import v7_neck
from v7_phone_cradle import v7_phone_cradle
from v7_phone_cap import v7_phone_cap
from v7_tail import v7_tail


@step(out='../STEP/v7_printed_assembly.step')
def v7_printed_assembly():
    p=load();a=datums(p)
    head=bd.Pos(0,8,a['head_bottom']+a['head_height']/2)*bd.Rot(90,0,0)
    placed=[
        bd.Pos(0,0,p['base_z'])*v7_base(),
        bd.Pos(0,0,a['deck'])*v7_cover_front(),
        bd.Pos(0,0,a['deck'])*v7_cover_rear(),
        bd.Pos(-p['motor_x'],p['motor_y'],a['deck'])*v7_motor_left(),
        bd.Pos(p['motor_x'],p['motor_y'],a['deck'])*v7_motor_right(),
        bd.Pos(0,p['battery_y'],a['deck'])*v7_battery_tray(),
        bd.Pos(0,p['electronics_y'],a['deck'])*v7_electronics_deck(),
        bd.Pos(0,p['caster_y'],a['deck'])*v7_caster_bridge(),
        bd.Pos(0,0,a['deck'])*v7_sensor_bracket(),
        bd.Pos(0,0,p['cover_top'])*v7_neck(),
        head*v7_phone_cradle(),
        head*bd.Pos(0,0,3.4)*v7_phone_cap(),
        tail_placement(p)*v7_tail(),
    ]
    return bd.Compound(children=placed,label='V7_DRAFT_printed_parts_assembly_NOT_one_piece_print')


if __name__=='__main__':
    v7_printed_assembly()
