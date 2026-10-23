from cadgen import step
from finish import part
from settings import load
from shapes import tail


@step(out='../STEP/v7_tail.step')
def v7_tail():
    p=load()
    return part(tail(p),p)


if __name__=='__main__':
    v7_tail()
