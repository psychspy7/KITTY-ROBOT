from cadgen import step
from settings import load
from finish import part
from rear_sensor import rear_settings, rear_face_coupon


@step(out='../STEP/v7_fit_rear_sensor_face.step')
def v7_fit_rear_sensor_face():
    p = load()
    shape = rear_face_coupon(rear_settings())
    return part(shape,p)


if __name__ == '__main__':
    v7_fit_rear_sensor_face()
