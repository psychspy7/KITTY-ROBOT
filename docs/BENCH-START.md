# Start here: unpowered bench inspection

This guide starts the real component intake. The software preview and CAD framework are separate from physical control. No motor circuit, pin map or firmware flash is approved from the parts names alone. Current authorization to help test is recorded; board, supply and wiring evidence is still needed before a powered test under AGENTS.md.

## 1. Clear the table and identify parts

1. Disconnect the battery and USB. Remove every jumper from the ESP32, motor driver, sensors and servo.
2. Work on a dry, nonconductive surface. Keep loose screws and cut wire ends away from boards.
3. Put out only the ESP32 DEVKIT V1, one TB6612FNG board, one HC-SR04, two motor/wheel units and the meter. Leave the Uno, SG90, relay and other modules aside for this first check.
4. Read the actual board silkscreen. Photograph the ESP32 front/back, including USB connector and pin labels; driver front/back; motor labels or seller specification; battery both sides; and meter dial/lead sockets.
5. Record what the switch says about voltage/current. Record a fuse or regulator as absent/unknown if none is identified. Do not assume the relay substitutes for a motor-power cutoff.

Do not force a Type-C cable into a different connector. Some DEVKIT V1 carriers use Micro-USB, and a cable can supply power without carrying data. The actual board, not its family name, determines the connector and supply inputs.

## 2. Set up the multimeter without an external power source

First identify its model, dial and socket labels. Stop if a lead is damaged or a socket label is unreadable.

| Lead | Socket for the checks below |
| --- | --- |
| Black | COM |
| Red | V/ohm (often marked VΩ or VΩHz) |

Leave A, mA and 10A sockets unused. A current-mode meter can short a supply when placed across its terminals. Do not open the meter or a mains adapter. No wall-socket/mains measurements are part of this project check.

### Continuity: loose leads and an isolated switch

1. With all boards, battery and USB disconnected, select the continuity position identified by the sound-wave symbol in the meter's manual. Some meters share it with diode mode and require a SELECT button; identify that before use.
2. Touch only the two probe tips together. A working continuity mode should beep or show a low resistance. Separate them; it should show open/OL. If it does not, record the exact display rather than guessing.
3. For a two-terminal switch completely removed from any circuit, put one probe on each terminal and toggle it. Record which position is open and which is closed. A continuity pass does not prove its current rating.
4. Do not use this procedure to assume all breadboard power rails are joined: with the board empty, check each intended rail segment. Some rails are split midway.

### Resistance: individual loose resistors

1. Keep the resistor disconnected from every board and power source. Do not test an unknown charged capacitor in resistance/continuity mode.
2. Select ohms. On a manual-ranging meter, a range above the expected value is needed (for example, 20 kohm for the reported 1–10 kohm resistors), subject to its manual. On auto-range, select Ω.
3. Hold one probe against each resistor lead; avoid touching both bare leads with your fingers.
4. Record the value and displayed unit: 1 kohm = 1,000 ohm; 2.2 kohm = 2,200 ohm. Count how many of each value you actually have.
5. Return the dial to OFF after the check.

### DC voltage: a later check after labels are identified

The eventual battery check uses the VΩ socket and DC volts (V with a solid/dashed line), not AC volts or current. Select a range above the battery's labelled maximum; black probe goes to labelled negative and red to positive. This is an explanation of the later procedure, not an instruction to probe an unidentified pack now. A no-load voltage reading does not establish motor-current capability or battery health under load. Do not attempt a locked-motor/stall-current experiment to fill a missing specification.

## 3. Before the first ESP32-only USB check

Provide the board/connector photos and confirm no external wiring is attached. After the physical setup is verified, the first powered check will use only the board's onboard USB connector and a matching data cable to a laptop. It will check device detection, not drive motors. A mains adapter alone cannot establish a serial data connection. No motor, SG90, battery, TB6612 or HC-SR04 is attached during that check.

On Windows, prepare Device Manager and note its current Ports/USB entries. In the project simulator directory, software-only checks can already run:

```bat
py -3 --version
py -3 -m unittest discover -s tests -v
py -3 main.py
```

Python 3.10+ is required. If the Python launcher is absent but a supported `python` command works, substitute `python`. Use the server's printed address, not an assumed fixed port. These commands do not flash the ESP32 or communicate with motors.

## 4. Electrical connections we will resolve next

This is a net checklist, not a pin-number wiring instruction. Do not connect it until exact boards, ratings and the matched schematic/firmware have been checked.

| Connection | Required check |
| --- | --- |
| Motor supply → fuse/cutoff → driver VM | Actual motor rated voltage/startup/stall load, pack limits, driver carrier limits, rated protection, wire/connector ratings and polarity |
| Regulated logic supply → controller/driver logic/sensor supply | Exact carrier's supported input; separate VM from logic VCC; correct voltage for each module; avoid unintended USB/external-supply backfeeding |
| Logic and driver reference grounds | Matched reference-ground plan with motor return paths sized/routed appropriately; no motor current through unsuitable breadboard or ESP32 paths |
| ESP32 control outputs → TB6612 inputs | Verified nonconflicting GPIOs; startup/strapping constraints; matching firmware; STBY held disabled until deliberate arm |
| TB6612 outputs → two motors | Compatible current/thermal limits; independently verified polarity/direction; wheels raised for bounded pulses |
| HC-SR04 trigger/ECHO | Verified variant and supply; ECHO conditioning matched to ESP32 input limits; no raw 5 V ECHO into GPIO |

The ESP32's GPIOs and USB/logic regulator are not an assumed motor or servo supply. The temporary HW battery still needs compatible ratings. Final AA design needs chemistry, cell count, current capability and holder dimensions; “AA” alone does not determine voltage. Do not parallel the two driver boards to invent a higher current rating.

For a resistor divider, the nominal relationship is `Vout = Vin × Rbottom / (Rtop + Rbottom)`. Selecting it requires maximum input voltage, input-high threshold, maximum GPIO voltage and actual resistor values/tolerances. A nominal 3.3 V calculation by itself is not a verified circuit.

## 5. First motor test, after the prerequisites

The subsequent matched firmware must default to disabled outputs. The prepared setup needs a reachable physical motor-power cutoff and a verified supply. Record logic/sensor checks first, then disabled-output checks, then short raised-wheel commands. Verify explicit stop, timeout, reset and reconnect before putting the robot on a cleared indoor floor. The existing simulator or preview cannot prove an ESP32 watchdog or motor stop.

Do not solder, glue components into a chassis, energize motors or upload a legacy sketch while pin/power assumptions are unresolved. Loose mechanical measurements, software development and CAD parameter intake can continue in parallel.

## Reply with one intake batch

- Clear photos: ESP32 front/back; driver front/back; meter dial/sockets; battery label; motor label or specification.
- Written results from the isolated continuity and loose-resistor checks, including units.
- For CAD: motor/shaft/wheel/caster dimensions; OPPO A57 model and dimensions with case; eventual AA-holder dimensions; printer bed/material/nozzle and available fasteners.

Unknowns stay unknown. No powered or mechanical fit result is recorded as passing until actually observed.
