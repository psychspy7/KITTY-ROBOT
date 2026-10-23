from cadgen import step
from finish import part
from settings import load
from shapes import neck


@step(out='../STEP/v3_neck.step')
def v3_neck():
    p = load()
    return part(neck(p), p)


if __name__ == '__main__':
    v3_neck()
