from cadgen import step
from finish import part
from settings import load
from shapes import neck


@step(out='../STEP/r2_neck.step')
def r2_neck():
    p = load()
    return part(neck(p), p)


if __name__ == '__main__':
    r2_neck()
