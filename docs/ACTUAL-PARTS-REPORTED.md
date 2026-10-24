# User-reported parts — updated 24 October 2026

Latest direct conversation supersedes the older handoff's incomplete list. Ownership and labels are user-reported, not physically inspected or electrically verified.

## Latest approximate inventory — 24 October 2026

The user supplied this list for context, explicitly saying that some items will not be used and more may be added. It is an availability report, not a requirement to install every component or change the printed body. They report approximately 24 hours remaining; the submission deadline has not been independently checked.

| Available item | Quantity / latest report |
| --- | --- |
| Jumper wires | Male-to-male, female-to-female and male-to-female; counts unspecified |
| Zip ties | Count unspecified |
| Toggle switch | Rating and count unspecified |
| Red / green / blue LEDs | Three of each colour |
| RGB LEDs | Three; package/pinout unspecified |
| Microphone module | One; exact type unspecified, previously reported as an LM393 sound detector; usable speech audio is not established |
| HC-SR04 ultrasonic modules | Two; planned front and rear positions |
| Perfboard / prototype PCB | One |
| Resistors | 1 kohm, 10 kohm and 2.2 kohm; counts/tolerances unspecified |
| Servo | One; previously reported as SG90 |
| Breadboard | One |
| Capacitor | One, 220 microfarads; voltage rating and polarity not recorded |
| Relay module | One; exact variant/ratings unverified |
| Arduino Uno R3 | One |
| ESP32 development board | One; previously reported as DevKit V1, exact module/USB bridge/pinout unidentified |
| Three-pin terminal connector | Count/pitch/rating unspecified |
| Infrared sensor | One; type and role unidentified |
| OPPO A57 phone | Existing phone, intended for camera, microphone, speaker and animated screen; these functions are not yet verified together on the actual phone |
| AA holders / cells | Reported as two holders and four AA cells total; holder dimensions, arrangement, chemistry and measured voltage unknown |
| Assembly/test tools | Soldering kit, hot glue gun and digital multimeter; other tools may be available |

The two BO motor/wheel units and two TB6612FNG boards reported earlier remain in the inventory below; their omission from this approximate update is not a withdrawal. Earlier buzzer, light module, 2 kohm resistors and USB cables also remain earlier reports rather than newly reconfirmed items.

Immediate build priority remains: resolve the ESP32 upload/USB identification issue; verify the chosen power arrangement; test sensors and bounded raised-wheel motion; then integrate phone vision, face and control and record the demo. The Uno is an available fallback, not an already-tested replacement. Servo, relay, separate microphone, IR module and extra LEDs are optional until a specific demonstrated function needs them. Both HC-SR04 mounting positions already exist in V7.1; this inventory update does not alter the shop ZIP or approve any electrical connection.

## Consolidated reports and unresolved interfaces

| Item | Current report |
| --- | --- |
| Controller | ESP32 DEVKIT V1; exact carrier/module, connector and pin layout pending |
| Drivetrain | Two BO motor/wheel units; latest user-estimated motor range 61–65 × 22–24 × 18–20 mm and confirmed wheel outside diameter 62.5 mm; shaft/hub/axial wheel width remain unmeasured |
| Driver | Two TB6612FNG dual-motor boards; exact carrier and load compatibility pending |
| Range | Two HC-SR04 modules; front and rear mounting requested; actual PCB/transducer/header variant and fit pending |
| Additional sensor | One IR module confirmed by the user; type/markings and intended role remain unidentified |
| Phone | OPPO A57, intended for camera/microphone/speaker/screen; exact model code/case/camera arrangement and combined operation pending |
| Servo | One servo; earlier SG90 identification, electrical details and permissible phone load unverified |
| Power | Latest report: two AA holders and four AA cells total; arrangement, chemistry, dimensions, voltage and load suitability pending. Earlier “HW battery” was for temporary testing only; neither is an approved motor supply yet |
| Resistors | 2.2 kohm, 1 kohm, 2 kohm, 10 kohm; counts/tolerances pending |
| Other electronics | Buzzer, LEDs, light module transcribed “LN393”, LM393 sound detector, relay transcribed “KY 199V1”, “Keltro 220 micro” capacitor, three-pin screw terminal and switch |
| Tools/assembly | Multimeter, Type-C/Arduino cables, soldering kit, glue gun, jumper wires, zip ties |
| Spare | Arduino Uno R3; no first-stage task assigned |
| Prototyping | One breadboard and one perfboard/prototype PCB reported in the latest inventory |

Still missing: motor rated voltage/startup/stall current and shaft geometry beyond the estimated body dimensions; wheel width/hub and caster dimensions; battery identity/ratings and any applicable charger; AA chemistry/holder wiring/dimensions and measured voltage; regulator, fuse and cutoff ratings; wire/connector ratings; capacitor voltage/polarity; resistor counts; phone case/camera/port details; printer bed/material/nozzle and fasteners. An identified switch does not establish a rated motor-power cutoff. No final pin assignment, wiring release or fit approval follows from this list.

Current intended scope: ESP32, one suitable dual-channel driver, two motors, front and rear range sensors and a fixed phone mount; extras follow the vision-and-stop core. Two range sensors do not establish all-direction coverage. USB may supply the identified ESP32 carrier through its supported connector, not arbitrary motors/SG90 loads. Final ECHO conditioning must match the actual module and GPIO limits; no raw 5 V ECHO connection is approved. Front/rear ultrasonic triggering should be staggered to reduce cross-talk; this has not been tested on the actual robot.

## User-reported dimensions added during complete CAD drafting

The user supplied these values on 23 October 2026. They have not been independently inspected, and phone-case inclusion remains unconfirmed.

| Interface | Reported dimension |
| --- | --- |
| OPPO phone, portrait height × width × thickness | 164 × 76 × 8 mm |
| Wheel diameter | 6.2 cm = 62 mm |
| BO motor length × width | 6.1 × 2 cm = 61 × 20 mm |

The complete draft uses the phone in landscape: its 164 mm long edge runs horizontally. Motor height, shaft height/offset, wheel width/hub fit, caster, AA-holder, camera/ports, actual board footprints, printer and fasteners remain unresolved. See `design/r2/complete-draft/parameters.json` for the exact split between user-reported dimensions and assumptions.

Begin with `docs/BENCH-START.md`. Physical setup evidence is still required before powered or flash tests.

## 24 October 2026: front and rear range mounting

V7.1 adds a separate rear HC-SR04 carrier using existing rear chassis bolts; the front mount remains present. The rear carrier uses a generic 45 × 20 × 1.6 mm PCB envelope and 16 mm transducers on 26 mm centres, with a first-print face gauge and strap retention. These dimensions are explicit design assumptions, not additional user measurements or a verified supplier match. See `design/v7/REAR-ULTRASONIC.md`. This is a mechanical revision; physical sensor fit, both ECHO interfaces, GPIO assignments and staggered triggering still require the actual-parts hardware stage. No rear sensor, IR sensor or motor has been electrically connected or tested by this CAD work.
