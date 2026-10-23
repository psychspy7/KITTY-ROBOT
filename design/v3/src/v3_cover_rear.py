from cadgen import step
from finish import part
from settings import load
from shapes import cover


@step(out='../STEP/v3_cover_rear.step')
def v3_cover_rear():
    p = load()
    return part(cover(p, front=False), p)


if __name__ == '__main__':
    v3_cover_rear()
