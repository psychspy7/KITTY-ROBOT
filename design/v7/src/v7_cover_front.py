from cadgen import step
from finish import part
from settings import load
from shapes import cover


@step(out='../STEP/v7_cover_front.step')
def v7_cover_front():
    p = load()
    return part(cover(p, front=True), p)


if __name__ == '__main__':
    v7_cover_front()
