from cadgen import step
from finish import part
from settings import load
from shapes import battery_tray


@step(out='../STEP/v3_battery_tray.step')
def v3_battery_tray():
    p = load()
    return part(battery_tray(p), p)


if __name__ == '__main__':
    v3_battery_tray()
