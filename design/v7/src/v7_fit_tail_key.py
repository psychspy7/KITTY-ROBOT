from cadgen import step
from settings import load
from fit_samples import tail_key_sample
from finish import part

@step(out='../STEP/v7_fit_tail_key.step')
def v7_fit_tail_key():
    p=load()
    return part(tail_key_sample(p),p)

if __name__=='__main__':v7_fit_tail_key()
