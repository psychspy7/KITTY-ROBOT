from cadgen import step
from finish import part
from settings import load
from shapes import base


@step(out='../STEP/r2_base.step')
def r2_base():
    p = load()
    return part(base(p), p)


if __name__ == '__main__':
    r2_base()
