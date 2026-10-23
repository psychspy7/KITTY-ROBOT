from cadgen import step
from finish import part
from settings import load
from shapes import sensor_bracket


@step(out='../STEP/v7_sensor_bracket.step')
def v7_sensor_bracket():
    p = load()
    return part(sensor_bracket(p), p)


if __name__ == '__main__':
    v7_sensor_bracket()
