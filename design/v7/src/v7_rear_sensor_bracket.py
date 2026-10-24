from cadgen import step
from settings import load
from finish import part
from rear_sensor import rear_settings, rear_bracket


@step(out='../STEP/v7_rear_sensor_bracket.step')
def v7_rear_sensor_bracket():
    p = load()
    return part(rear_bracket(p,rear_settings()),p)


if __name__ == '__main__':
    v7_rear_sensor_bracket()
