from cadgen import step
from finish import part
from settings import load
from shapes import base


@step(out='../STEP/v7_base.step')
def v7_base():
    p = load()
    return part(base(p), p)


if __name__ == '__main__':
    v7_base()
