from cadgen import step
from finish import part
from settings import load
from shapes import caster_bridge


@step(out='../STEP/v7_caster_bridge.step')
def v7_caster_bridge():
    p = load()
    return part(caster_bridge(p), p)


if __name__ == '__main__':
    v7_caster_bridge()
