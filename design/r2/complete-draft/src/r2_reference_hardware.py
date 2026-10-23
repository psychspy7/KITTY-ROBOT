from cadgen import step
from settings import load
from shapes import hardware_envelopes


@step(out='../STEP/r2_reference_hardware.step')
def r2_reference_hardware():
    return hardware_envelopes(load())


if __name__=='__main__':
    r2_reference_hardware()
