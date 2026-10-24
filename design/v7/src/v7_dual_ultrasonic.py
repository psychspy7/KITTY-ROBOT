from cadgen import build123d as bd, step
from settings import load
from rear_sensor import rear_settings, mount_bottom
from v7_complete_draft import v7_complete_draft
from v7_rear_sensor_bracket import v7_rear_sensor_bracket
from v7_rear_sensor_reference import v7_rear_sensor_reference


@step(out='../STEP/v7_dual_ultrasonic.step')
def v7_dual_ultrasonic():
    p = load(); q = rear_settings()
    return bd.Compound(children=[
        v7_complete_draft(),
        bd.Pos(0,0,mount_bottom(p,q))*v7_rear_sensor_bracket(),
        v7_rear_sensor_reference(),
    ],label='V7_1_FRONT_AND_REAR_ULTRASONIC_DRAFT_VIEW_ONLY')


if __name__ == '__main__':
    v7_dual_ultrasonic()
