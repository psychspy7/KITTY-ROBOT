# Team-reported hardware intake

**Status: reported by the team; not independently inspected or measured.** The base has been reported as tested, but full physical autonomous operation is not established by this inventory or by the software tests.

| Part | Reported item | Still to verify |
|---|---|---|
| Controller | ESP32 development board; Arduino Uno R3 also on hand | ESP32 variant/revision; which board is intended for control |
| Motor driver | TB6612 board | Exact board/revision, logic rail, current and thermal limits |
| Drive | BO DC motor(s), BO wheels estimated at about 60 mm | Counts, voltage, stall current, shaft/hub fit, measured wheel diameter |
| Range | HC-SR04 and IR sensor | Exact modules, counts, electrical output levels, mounting coverage |
| Phone | OPPO A57 | Model revision, case dimensions, mount fit, camera/audio integration |
| Other | Resistors marked 220 Ω / 1 kΩ / 10 kΩ, jumper leads, breadboard/PCB, cable ties, multimeter, soldering tools, LED | Quantity, condition, wire/connector ratings, continuity |
| Power / protection | Not confirmed in the intake | Battery chemistry and ratings, charger/BMS, regulator, fuse, physical cutoff |
| Optional scan servo | Mentioned earlier; exact model and quantity unknown | Confirm whether present and rated for intended use |

No final pin map, fitted STL, verified bill of materials, or wiring-ready circuit follows from these reports. Do not use an ESP32 GPIO as a motor power output. A possible 5 V HC-SR04 ECHO must not be connected directly to an ESP32 input; condition and measure the signal for the exact sensor/board. See [`CIRCUIT-AND-SYSTEM.md`](CIRCUIT-AND-SYSTEM.md).

