from cadgen import step
from rear_sensor import rear_settings, rear_hardware


@step(out='../STEP/v7_rear_sensor_reference.step')
def v7_rear_sensor_reference():
    return rear_hardware(rear_settings())


if __name__ == '__main__':
    v7_rear_sensor_reference()
