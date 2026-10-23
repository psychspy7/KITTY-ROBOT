from cadgen import step
from finish import part
from settings import load
from shapes import caster_bridge


@step(out='../STEP/r2_caster_bridge.step')
def r2_caster_bridge():
    p = load()
    return part(caster_bridge(p), p)


if __name__ == '__main__':
    r2_caster_bridge()
