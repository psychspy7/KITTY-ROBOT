from cadgen import step
from settings import load
from fit_samples import screw_sample
from finish import part

@step(out='../STEP/v7_fit_screws.step')
def v7_fit_screws():
    p=load()
    return part(screw_sample(p),p)

if __name__=='__main__':v7_fit_screws()
