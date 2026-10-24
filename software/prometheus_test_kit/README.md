# PROMETHEUS staged test kit

Start with `PROMETHEUS-FINAL-TEST-GUIDE.pdf` in the release ZIP. Code is separate:
open `PrometheusTest/PrometheusTest.ino` in Arduino IDE, keeping all five `.h`
files in that folder. `PROMETHEUS-CODE-CANVAS.html` is a local editable text
viewer with file downloads; it does not upload firmware or connect to hardware.
`PROMETHEUS-ALL-CODE.txt` contains the same files with separators and is not a
single Arduino sketch to paste wholesale.

This kit commissions components with short raised-wheel pulses. It does not
implement floor navigation, path drawing/execution, camera AI or automatic
avoidance. The existing face, simulator and Assembly Lab remain separate.

## Current hold

Motor power is not released. Actual motor voltage/startup/stall-current data,
installed battery chemistry/arrangement/voltage/polarity, complete driver labels
and IC identity, rated protection/cutoff/wires and real connections remain
unverified. The photos and earlier successful ESP32 AP test do not establish
these. Keep batteries disconnected while inspecting or rearranging wiring.

All verification flags in `Settings.h` are false; numeric motor-supply fields
are zero. The default program starts AP/Serial only and does not initialize
robot GPIOs. The first physical test is the isolated battery voltage/polarity
measurement on PDF page 3. Changing a flag records an operator declaration;
the software cannot inspect wiring or measure battery voltage.

## Behavior and setup

Candidate pins are canonical in `pins.json`; generated `RobotPins.h`, PDF tables
and firmware match. They apply only after classic ESP32/carrier identification.
Front and optional rear ECHO conditioning must be checked independently. The
unknown buzzer stays disconnected/disabled. No motors or SG90 on ESP32 3V3.

Board selection for the reported classic ESP-32S carrier: **ESP32 Dev Module**.
Use the port that disappears when that board is unplugged, not a fixed COM
number. Serial Monitor is 115200 baud with Newline. The sketch prints the actual
random AP password stored on that board; SSID is `PROMETHEUS_ESP32` and the page
is `http://192.168.4.1/`. There is no fixed password supplied in this archive.

Once the relevant physical checks are recorded and the matching settings are
enabled, each motor command requires a fresh explicit arm and produces one
150 ms pulse by default. PWM duty is limited to 80/255; this is not a voltage or
current rating. Completion requires a new arm. The local controller checks
400 ms command lease, enabled sensor validity/freshness, direction-dependent
obstacles and latched stop/fault. A browser stop does not cut electrical power.
Use the verified reachable motor cutoff independently.

The AP dashboard displays actual firmware telemetry. Opening `dashboard.html`
from disk does not control a board. Browser tests use explicitly labelled
fixtures and do not establish physical sensor or motor behavior.

## Rebuild and software checks

Python 3 with ReportLab generates the PDF; Pillow/PyMuPDF and Playwright are
used for release inspection, not Arduino runtime dependencies. Arduino code
uses libraries bundled with Espressif's Arduino core.

```sh
python3 build_kit.py --out /tmp/prometheus-release --archive
g++ -std=c++17 -Wall -Wextra -Werror -pedantic tests/safety_test.cpp -o /tmp/prometheus-safety
/tmp/prometheus-safety
```

Use an output directory outside this source directory. The source snapshot
inside the release ZIP can rebuild the PDF and editable code. Verification
JSON records checks actually performed on the delivered source, separately
from the blank physical evidence worksheet. No cloud firmware flash or powered
robot test is claimed.
