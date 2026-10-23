from cadgen import step
from finish import part
from settings import load
from shapes import phone_cradle


@step(out='../STEP/v7_phone_cradle.step')
def v7_phone_cradle():
    p = load()
    return part(phone_cradle(p), p)


if __name__ == '__main__':
    v7_phone_cradle()
