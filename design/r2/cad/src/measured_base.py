from cadgen import step, stl
from geometry import base_plate
from parameters import load


@step(out='../STEP/measured_base.step')
@stl(out='../STL/measured_base.stl', mesh_tolerance=1e-4, mesh_angular_tolerance=0.1)
def measured_base():
    return base_plate(load())


if __name__ == '__main__':
    measured_base()
