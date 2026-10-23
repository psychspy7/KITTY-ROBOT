from cadgen import step
from finish import part
from settings import load
from shapes import motor_mount


@step(out='../STEP/r2_motor_right.step')
def r2_motor_right():
    p = load()
    return part(motor_mount(p, side=1), p)


if __name__ == '__main__':
    r2_motor_right()
