from cadgen import step
from settings import load
from shapes import hardware_envelopes


@step(out='../STEP/v3_reference_hardware.step')
def v3_reference_hardware():
    return hardware_envelopes(load())


if __name__=='__main__':
    v3_reference_hardware()
