from cadgen import build123d as bd, step
from settings import load, datums
from r2_base import r2_base
from r2_cover_front import r2_cover_front
from r2_cover_rear import r2_cover_rear
from r2_motor_left import r2_motor_left
from r2_motor_right import r2_motor_right
from r2_battery_tray import r2_battery_tray
from r2_electronics_deck import r2_electronics_deck
from r2_caster_bridge import r2_caster_bridge
from r2_sensor_bracket import r2_sensor_bracket
from r2_neck import r2_neck
from r2_phone_cradle import r2_phone_cradle
from r2_phone_cap import r2_phone_cap


@step(out='../STEP/r2_printed_assembly.step')
def r2_printed_assembly():
    p=load();a=datums(p)
    head=bd.Pos(0,8,a['head_bottom']+a['head_height']/2)*bd.Rot(90,0,0)
    placed=[
        bd.Pos(0,0,p['base_z'])*r2_base(),
        bd.Pos(0,0,a['deck'])*r2_cover_front(),
        bd.Pos(0,0,a['deck'])*r2_cover_rear(),
        bd.Pos(-p['motor_x'],p['motor_y'],a['deck'])*r2_motor_left(),
        bd.Pos(p['motor_x'],p['motor_y'],a['deck'])*r2_motor_right(),
        bd.Pos(0,p['battery_y'],a['deck'])*r2_battery_tray(),
        bd.Pos(0,-32,a['deck'])*r2_electronics_deck(),
        bd.Pos(0,p['caster_y'],a['deck'])*r2_caster_bridge(),
        bd.Pos(0,0,a['deck'])*r2_sensor_bracket(),
        bd.Pos(0,0,p['cover_top'])*r2_neck(),
        head*r2_phone_cradle(),
        head*bd.Pos(0,0,3.4)*r2_phone_cap(),
    ]
    return bd.Compound(children=placed,label='R2_DRAFT_printed_parts_assembly_NOT_one_piece_print')


if __name__=='__main__':
    r2_printed_assembly()
