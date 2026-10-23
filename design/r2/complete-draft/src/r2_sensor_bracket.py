from cadgen import step
from finish import part
from settings import load
from shapes import sensor_bracket


@step(out='../STEP/r2_sensor_bracket.step')
def r2_sensor_bracket():
    p = load()
    return part(sensor_bracket(p), p)


if __name__ == '__main__':
    r2_sensor_bracket()
