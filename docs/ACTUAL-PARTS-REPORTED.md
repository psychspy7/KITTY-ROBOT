# User-reported parts — 23 October 2026

Latest direct conversation supersedes the older handoff's incomplete list. Ownership and labels are user-reported, not physically inspected or electrically verified.

| Item | Current report |
| --- | --- |
| Controller | ESP32 DEVKIT V1; exact carrier/module, connector and pin layout pending |
| Drivetrain | Two BO motor/wheel units; older wheel estimate about 60 mm, not measured |
| Driver | Two TB6612FNG dual-motor boards; exact carrier and load compatibility pending |
| Range | Two HC-SR04 modules; variant pending |
| Phone | OPPO A57; exact model code/case/camera arrangement pending |
| Servo | SG90; quantity, electrical details and permissible phone load unverified |
| Power | “HW battery” for temporary testing; AA cells intended for final version. Neither is an approved motor supply yet |
| Resistors | 2.2 kohm, 1 kohm, 2 kohm, 10 kohm; counts/tolerances pending |
| Other electronics | Buzzer, LEDs, light module transcribed “LN393”, LM393 sound detector, relay transcribed “KY 199V1”, “Keltro 220 micro” capacitor, three-pin screw terminal and switch |
| Tools/assembly | Multimeter, Type-C/Arduino cables, soldering kit, glue gun, jumper wires, zip ties |
| Spare | Arduino Uno R3; no first-stage task assigned |
| Historical reports | IR sensor, breadboard and PCB were previously reported; current exact variants/counts remain unverified |

Still missing: motor rated voltage/startup/stall current and shaft geometry; wheel/hub and caster dimensions; battery identity/ratings and charger; final AA chemistry/cell count/holder; regulator, fuse and cutoff ratings; wire/connector ratings; capacitor value/voltage/polarity; resistor counts; phone dimensions; printer bed/material/nozzle and fasteners. An identified switch does not establish a rated motor-power cutoff. No final pin assignment, wiring release or fit approval follows from this list.

Initial scope: ESP32, one suitable dual-channel driver, two motors, one front range sensor and a fixed phone mount; extras follow the vision-and-stop core. A single forward sensor does not establish all-direction coverage. USB may supply the identified ESP32 carrier through its supported connector, not arbitrary motors/SG90 loads. Final ECHO conditioning must match the actual module and GPIO limits; no raw 5 V ECHO connection is approved.

Begin with `docs/BENCH-START.md`. Physical setup evidence is still required before powered or flash tests.
