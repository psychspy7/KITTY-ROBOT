from cadgen import step, stl
from geometry import base_plate
from parameters import load


@step(out='../STEP/draft_base.step')
@stl(out='../STL/draft_base.stl', mesh_tolerance=1e-4, mesh_angular_tolerance=0.1)
def draft_base():
    return base_plate(load('parameters.example.json', require_measured=False))


if __name__ == '__main__':
    draft_base()
