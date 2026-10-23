from cadgen import step
from finish import part
from settings import load
from shapes import cover


@step(out='../STEP/r2_cover_front.step')
def r2_cover_front():
    p = load()
    return part(cover(p, front=True), p)


if __name__ == '__main__':
    r2_cover_front()
