from cadgen import step
from settings import load
from fit_samples import phone_thickness_sample
from finish import part

@step(out='../STEP/v7_fit_phone_thickness.step')
def v7_fit_phone_thickness():
    p=load()
    return part(phone_thickness_sample(p),p)

if __name__=='__main__':v7_fit_phone_thickness()
