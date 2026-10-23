from cadgen import step
from finish import part
from settings import load
from shapes import tail


@step(out='../STEP/r2_tail.step')
def r2_tail():
    p=load()
    return part(tail(p),p)


if __name__=='__main__':
    r2_tail()
