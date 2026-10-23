from cadgen import step, stl
from geometry import motor_coupon
from parameters import load


@step(out='../STEP/draft_motor_coupon.step')
@stl(out='../STL/draft_motor_coupon.stl', mesh_tolerance=1e-4, mesh_angular_tolerance=0.1)
def draft_motor_coupon():
    return motor_coupon(load('parameters.example.json', require_measured=False))


if __name__ == '__main__':
    draft_motor_coupon()
