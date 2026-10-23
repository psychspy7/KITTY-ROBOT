from cadgen import step
from finish import part
from settings import load
from shapes import phone_cap


@step(out='../STEP/v7_phone_cap.step')
def v7_phone_cap():
    p = load()
    return part(phone_cap(p), p)


if __name__ == '__main__':
    v7_phone_cap()
