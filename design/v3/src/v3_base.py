from cadgen import step
from finish import part
from settings import load
from shapes import base


@step(out='../STEP/v3_base.step')
def v3_base():
    p = load()
    return part(base(p), p)


if __name__ == '__main__':
    v3_base()
