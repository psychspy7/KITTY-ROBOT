# KITTY Sentinel — system and circuit draft

**Status: concept architecture only. Not a wiring diagram, BOM approval, or permission to power the robot.** Exact board variants, sensor count, battery, motor ratings, and physical connections have not been inspected and measured.

## Functional split

1. **Phone (planned):** camera, microphone, speaker, and operator display. The current demo has no phone link, live camera, or speech recognition.
2. **Laptop (planned integration):** optional heavier vision/task planning. In the current demo, the room-check phrase is a small supported text command; it does not call an AI model.
3. **ESP32 (reported owned; variant unknown):** intended local motion controller, sensor polling, command timeout, and motor stop. Its firmware and host link are not present in the current demo.
4. **Sensors (reported owned; models/counts unknown):** a reported HC-SR04 and IR sensor. A front/rear/corner ultrasonic arrangement is a proposed layout until the actual quantities and mounting are confirmed.
5. **TB6612 and BO drive (reported owned; exact revisions and ratings unknown):** intended motor path. No current repo code sends commands to it.

The laptop or a language model may propose a task. A bounded command interface and local ESP32 checks must approve motion. Unknown/expired commands, invalid sensor readings, obstacle conditions, or a link timeout should stop the motors. A physical power disconnect is still required for any real moving test.

## Draft signal and power path

![Draft system and circuit block diagram. Functional relationships only; not wiring-ready.](../hardware/system-architecture.svg)

### Signal path

| Signal | Draft endpoint | Required check before assigning pins |
|---|---|---|
| Phone video/audio | Phone → laptop, future integration | Select an implemented transport and confirm privacy/permissions. No live capture path exists yet. |
| Bounded motion request | Laptop → ESP32, future integration | Define message schema, authentication/physical arming, sequence/timeout, and fail-closed behavior. Protocol and pins are unassigned. |
| HC-SR04 trigger/echo | Sensor → ESP32, if exact module supports it | Confirm module supply and output levels. Never connect a possible 5 V ECHO directly to a 3.3 V ESP32 input; design and measure level conditioning for the actual parts. |
| IR output | IR module → ESP32, if compatible | Identify the board and output type/voltage; measure before connecting. |
| Driver inputs/enable | ESP32 → TB6612, future integration | Confirm board pin labels, logic voltage, motor supply, current rating, and motor stall current. No GPIO map is assigned. |
| Motor outputs | TB6612 → left/right motors | Confirm motor voltage/current, polarity, stall current, and driver thermal/current limits. |

### Power path (concept only)

- A protected battery supply should feed the motor-driver supply through a correctly rated fuse and a reachable physical disconnect.
- A separate, correctly rated regulator should supply the controller and sensors. Choose its voltage/current only after identifying the actual boards and loads.
- Join signal grounds at a planned common reference; keep motor current off a solderless breadboard.
- Do not power motors from ESP32/Uno GPIO or from an unverified logic regulator. Do not energize the circuit until polarity, continuity, shorts, current limits, and the physical cutoff have been checked.
- The reported resistors do not by themselves establish a safe ECHO divider. Select and verify a level-shifter/divider against the actual sensor and ESP32 input limits.

## Reported hardware intake

Team-reported: an ESP32 (variant unknown), TB6612 driver board, Uno R3, BO DC motor(s), BO wheels estimated around 60 mm, one HC-SR04 listing, an IR sensor, resistors, jumper wires, breadboard/PCB, tools, an LED, and an OPPO A57 phone. This is a report, not an inspected inventory or measured specification. The UNO is not assumed to be in the active control loop.

Still needed from the physical parts before a matched schematic: photographs/model markings; quantities; ESP32 and driver revision; motor rated voltage and stall current; battery chemistry/voltage/capacity/BMS; fuse and disconnect; regulator; HC-SR04 and IR output levels; servo model/count if present; wire gauge and connector ratings; measured wheel/body geometry.

## Acceptance boundary

- **Automated evidence:** Python simulator suite and the Node command-demo suite. Both are software-only.
- **Team-reported:** base tested. The repository does not contain a verified full physical autonomous run.
- **Planned:** live phone camera/audio, physical sensors, laptop-to-ESP32 transport, firmware, measured wiring, and integrated autonomous motion.
- **Not included in V1:** flight. The separate wheel-to-rotor V2 is unbuilt and not flight-validated.

Do not treat this document as a wiring sequence. After parts intake, replace the draft with one reviewed schematic, matched GPIO table, and firmware configuration. Until then, leave all hardware adapters disabled and do not flash or power motors.

