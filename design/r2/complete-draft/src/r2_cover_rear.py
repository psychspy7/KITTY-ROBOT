from cadgen import step
from finish import part
from settings import load
from shapes import cover


@step(out='../STEP/r2_cover_rear.step')
def r2_cover_rear():
    p = load()
    return part(cover(p, front=False), p)


if __name__ == '__main__':
    r2_cover_rear()
