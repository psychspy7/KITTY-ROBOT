from cadgen import step, stl
from geometry import phone_cradle
from parameters import load


@step(out='../STEP/draft_phone_cradle.step')
@stl(out='../STL/draft_phone_cradle.stl', mesh_tolerance=1e-4, mesh_angular_tolerance=0.1)
def draft_phone_cradle():
    return phone_cradle(load('parameters.example.json', require_measured=False))


if __name__ == '__main__':
    draft_phone_cradle()
