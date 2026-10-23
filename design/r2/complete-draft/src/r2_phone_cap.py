from cadgen import step
from finish import part
from settings import load
from shapes import phone_cap


@step(out='../STEP/r2_phone_cap.step')
def r2_phone_cap():
    p = load()
    return part(phone_cap(p), p)


if __name__ == '__main__':
    r2_phone_cap()
