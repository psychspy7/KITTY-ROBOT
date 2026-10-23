from cadgen import step, stl
from geometry import sensor_coupon
from parameters import load


@step(out='../STEP/draft_sensor_coupon.step')
@stl(out='../STL/draft_sensor_coupon.stl', mesh_tolerance=1e-4, mesh_angular_tolerance=0.1)
def draft_sensor_coupon():
    return sensor_coupon(load('parameters.example.json', require_measured=False))


if __name__ == '__main__':
    draft_sensor_coupon()
