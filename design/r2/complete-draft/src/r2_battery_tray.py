from cadgen import step
from finish import part
from settings import load
from shapes import battery_tray


@step(out='../STEP/r2_battery_tray.step')
def r2_battery_tray():
    p = load()
    return part(battery_tray(p), p)


if __name__ == '__main__':
    r2_battery_tray()
