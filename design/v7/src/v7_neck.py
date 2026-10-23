from cadgen import step
from finish import part
from settings import load
from shapes import neck


@step(out='../STEP/v7_neck.step')
def v7_neck():
    p = load()
    return part(neck(p), p)


if __name__ == '__main__':
    v7_neck()
