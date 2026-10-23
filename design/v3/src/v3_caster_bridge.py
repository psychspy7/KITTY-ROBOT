from cadgen import step
from finish import part
from settings import load
from shapes import caster_bridge


@step(out='../STEP/v3_caster_bridge.step')
def v3_caster_bridge():
    p = load()
    return part(caster_bridge(p), p)


if __name__ == '__main__':
    v3_caster_bridge()
