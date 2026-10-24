# PROMETHEUS — proposed pin-by-name wiring plan

**Status: PROPOSED; not released for physical wiring or motor power.** The latest photographs do not establish VM, all driver control labels, motor rating/current or the battery output. First perform only `TEST-01-BATTERY-VOLTAGE.md`. A proposed connection table is not evidence that the attached jumpers are correct.

The board photograph shows ESP-32S and Micro-USB. This plan assumes a classic ESP32 carrier actually exposing the numbered GPIOs below. GPIO numbers mean printed IO/GPIO labels, not positions counted from a corner. The red carrier is reported as TB6612FNG-style; its IC marking and every terminal must be checked before use. Wire colours carry no assigned electrical meaning.

## Controller signal candidates

This preserves the earlier physical-controller reference in `software/bench_motion/CONNECTION-GUIDE.md`. The separate 3D Assembly Lab uses an educational preset and is not the physical wiring source of truth. Existing `software/bench_motion/firmware/config.h` remains unassigned (`-1`) with physical output disabled. These values have not been silently applied to firmware.

| ESP32 printed GPIO candidate | Driver/sensor destination by printed label | Existing firmware field | Release condition |
| --- | --- | --- | --- |
| GPIO25 | AIN1 | `Ain1` | Both actual board labels checked |
| GPIO26 | AIN2 | `Ain2` | Both actual board labels checked |
| GPIO27 | PWMA | `Pwma` | Both actual board labels checked |
| GPIO18 | BIN1 | `Bin1` | Both actual board labels checked |
| GPIO19 | BIN2 | `Bin2` | Both actual board labels checked |
| GPIO23 | PWMB | `Pwmb` | Both actual board labels checked |
| GPIO21 | STBY | `Standby` | Check any carrier pull-up/enable jumper and proposed 10 kΩ pulldown to GND |
| GPIO22 | Front HC-SR04 TRIG | `Trigger` | Identify sensor variant and its 3.3 V trigger compatibility |
| GPIO32 | Front ECHO divider junction J | `Echo` | Verified conditioned signal; never raw 5 V ECHO |
| GPIO33 | 1 kΩ series resistor → loose LED anode | `Led` | Identify a low-current indicator LED and its polarity |
| GPIO13, reserved only | Identified buzzer module's compatible input/driver | `Buzzer` | Buzzer type, supply, current, signal voltage/polarity and driver reviewed; leave disconnected until then |

The candidates are distinct and avoid classic ESP32 flash pins 6–11, boot-strapping pins 0/2/5/12/15 and UART0 pins 1/3. This check does not prove the actual carrier exposes them or has no other conflicts. Confirm the module/board documentation before release. It is not a pin-order drawing.

## Driver outputs and power nets — all pending release

Define robot left/right while facing its marked FRONT. Motor channel A is proposed left; B is proposed right. Forward polarity is determined later with raised wheels, not from lead colour.

| Printed driver terminal | Planned net / endpoint | Current status |
| --- | --- | --- |
| AO1 | First left-motor terminal | Verify exact AO1 label and trace actual lead |
| AO2 | Second left-motor terminal | Verify exact AO2 label and trace actual lead |
| BO1 | First right-motor terminal | Verify exact BO1 label and trace actual lead |
| BO2 | Second right-motor terminal | Verify exact BO2 label and trace actual lead; reported bank order is not assumed |
| VCC | ESP32 regulated 3V3 logic rail | Only after the real carrier's VCC function and 3.3 V compatibility are established |
| VM | Protected motor-source positive through fuse and reachable rated cutoff | **Terminal, supply voltage/polarity and load compatibility unconfirmed: leave disconnected** |
| GND, power return | Motor-source negative via suitable direct wire | Only after source polarity and carrier ground terminals are checked |
| GND, logic reference | ESP32 GND and sensor/indicator reference | Verify carrier ground commoning and actual board labels |

```text
Supported USB input ────────────────────────────────── ESP32 Micro-USB

ESP32 3V3 ──────────────────────────────────────────── driver VCC
ESP32 GND ──────────────────────────────────────────── common reference

[motor source voltage/polarity/current NOT CONFIRMED]
 source positive ── rated fuse ── reachable rated cutoff ── driver VM [label pending]
 source negative ──────────────────────────────────────── driver power GND
                           └───────────────────────────── common reference

driver AO1 / AO2 ──────────────────────────────────────── left motor's two terminals
driver BO1 / BO2 ──────────────────────────────────────── right motor's two terminals
```

Motor current must not flow through the ESP32 regulator/headers or unsuitable breadboard/jumper paths. Motor terminals do not connect directly to ESP32 GPIO, 3V3 or GND. The supply positive rails are not joined by this plan. Do not interpret a battery's measured voltage or a driver's peak-current headline as proof of suitable startup/stall capability.

Battery chemistry/cell count/series arrangement, actual open-circuit voltage and polarity, loaded behavior, motor rated voltage/startup/stall requirements, real driver ratings, fuse, switch and wire/connector ratings must be resolved before VM is connected. No regulator or fuse is assumed present. No motor stall test is requested.

Inspect carrier solder joints with power removed; check suspect bridges and terminal continuity using the appropriate unpowered method in a later test. A short continuity beep on a supply with capacitors is not by itself a diagnosis of a permanent short. Do not use resistance/continuity mode on an energized circuit.

## Front HC-SR04 and ECHO conditioning — conditional example

| Sensor label | Planned endpoint after variant/power review |
| --- | --- |
| VCC | Confirmed compatible regulated supply; a standard 5 V HC-SR04 would need verified 5 V |
| GND | Common logic reference |
| TRIG | Proposed GPIO22, after input-threshold compatibility check |
| ECHO | Divider/level shifter input; no direct GPIO connection |

For a **confirmed 5 V-output** module, one candidate using previously reported resistor values is:

```text
ECHO ── [2.2 kΩ upper] ── J ── [2.2 kΩ] ── [1 kΩ] ── GND
                          │
                          └── proposed GPIO32
```

The two lower resistors are in series: 3.2 kΩ. Nominal J is `5 × 3.2 / (2.2 + 3.2) = 2.963 V`. Assuming a 4.75–5.25 V high signal and independent ±5% resistor tolerances, calculated J is approximately 2.699–3.237 V. These are assumptions/calculations, not measurements. Actual signal drive, supply, resistor tolerances and the identified ESP32's input thresholds/limits must be checked before acceptance. A sensor already producing 3.3 V ECHO may require a different interface.

This newer resistor candidate avoids depending on the earlier unconfirmed 2 kΩ resistor report. For one front sensor it needs two 2.2 kΩ resistors and one 1 kΩ resistor; the LED needs a separate 1 kΩ resistor. Measure/count them later, isolated and unpowered. No sensor wire is to be connected in the current battery-only test. Both this ECHO candidate and the older draft remain unapproved; do not combine them.

## Indicators and unresolved interfaces

Proposed loose LED circuit: GPIO33 → separate 1 kΩ resistor → LED anode; LED cathode → GND. Verify polarity; lead length alone is not reliable after trimming. This is not a circuit for an unknown high-power LED/module.

Leave the buzzer disconnected. A two-wire transducer and a three-pin module require different review; some need a transistor driver or tone waveform, and some module inputs expose 5 V. Identify the actual part before deciding its VCC, ground, signal and active polarity. GPIO13 is only reserved, not an instruction to connect it directly.

The reported capacitor's value, voltage rating, polarity and carrier decoupling need checking before choosing its placement. No arbitrary regulator, protection circuit or noise capacitor is inferred from the photos.

The second reported HC-SR04 is not assigned new physical GPIOs here. Front operation is verified first; then identify and condition a rear module and stagger triggers. One forward sensor does not authorize blind reverse or scanning rotations in uncleared space.

## What makes this releasable

Record actual pin identities, supply measurements and motor/driver compatibility; update one matched schematic, table and firmware configuration; inspect unpowered wiring; then test logic/sensors and disabled outputs before bounded raised-wheel motor tests. Internet access, a drawn path or a passing 3D simulation does not substitute for these observations. Current motor-power status remains **DISCONNECTED**.
