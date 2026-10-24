# PROMETHEUS physical continuation

The user requests staged development of a real temporary-box robot: ESP32-hosted path-drawing dashboard, approximate calibrated motion, manual control, range stopping, indicators, watchdogs and cautious obstacle handling. Start with the unpowered chassis activity in `PHASE-1-TEMPORARY-CHASSIS.md`; electrical specifications and setup evidence gate powered motor work.

## User-reported working baseline

Earlier description: ESP32-WROOM-32, approximately 38 pins. Latest photographs show an **ESP-32S**-marked module and Micro-USB carrier; full board revision/pin identities remain pending. Arduino IDE `ESP32 Dev Module`; successful compile/upload and execution on COM8 during testing; Serial Monitor 115200; Wi-Fi scan; `PROMETHEUS_ESP32` AP; Android association and the ESP32 web page at `http://192.168.4.1/` are user-reported. Keep AP mode. The failed earlier phone-hotspot station test does not require restarting the successful AP proof. No cloud-assisted flash or physical motor/sensor test is claimed.

## Existing implementation to build on

`software/bench_motion/` already exists as uncommitted work. Preserve it and the other preexisting work. Reading it identified a useful starting point, not a completed implementation of this expanded request:

| Area | Present in the existing source | Remaining work for this request |
| --- | --- | --- |
| Drawing/planning | Centimetre-grid route drawing; measured forward speed and separate turn-rate inputs; bounded timed segments | Dashboard refinement, progress and clearly labelled estimated trace; actual calibration |
| Controller | Separate C++ route core, startup disarm, command/sensor expiry, obstacle stop, stop latch | Pause/resume semantics, requested manual controls/speed modes and their tests |
| Range | Front sonar task and invalid/stale handling | Independently verify actual sensor wiring and readings; decide on the reported rear sensor before guarded reverse floor motion |
| Motion adapter | TB6612 direction/PWM/STBY mapping behind disabled configuration | Match actual carrier, power supply, motor polarity and reviewed GPIO table; raised-wheel verification |
| Indicators | LED/alarm output with optional verified active-buzzer drive | Identify buzzer and implement/test requested concise status indications |
| Network/API | ESP32 AP + local HTTP, per-boot session and bounded command validation | Retain requested `PROMETHEUS_ESP32` naming; Arduino IDE package and documented current endpoints |
| Build | Existing project uses PlatformIO/Arduino ESP32 2.0.17 | Arduino IDE sketch/export and a fresh compile check of the actual delivered sources; do not claim uploaded firmware |
| Avoidance | Stop/wait and optional clear-reading resume | No scan/detour implementation is currently present; do not describe this as autonomous bypass |

The previous software build/test observations remain historical; this documentation-only intake update did not rebuild or upload that firmware. `software/assembly_lab/` is a separate browser simulation and must not be treated as physical controller firmware.

## Intended physical control boundaries

- Host the lightweight dashboard on the ESP32 AP, with actual telemetry from firmware. Internet and a GPU are not required for that control page.
- Convert explicitly scaled path geometry to calibrated bounded timed commands. Display the plan separately from an elapsed-time estimate; neither is measured localization.
- Stop locally on startup, command expiry, invalid/stale range, stop activation or disarm. Reconnection alone must not restart motion. A reachable independent motor-power cutoff remains required.
- A fixed forward sonar cannot certify either side, reverse space, the robot's swept rotation area or floor edges. Scanning by turning the robot still requires independently cleared rotation space. Do not enable blind detours or claim a clear forward sample proves side clearance.
- A future bounded, operator-authorized scan can compare stopped measurements. If a bypass cannot establish safe progression or route recovery, enter BLOCKED / REPLAN REQUIRED. Original-route recovery needs positioning evidence; do not silently treat an altered estimated pose as ground truth.
- The second HC-SR04 was reported earlier. Verify it before requiring it. Rear integration can improve reverse ranging but does not establish side or edge coverage.
- Calibrate at the actual PWM, supply, floor and robot load. Add encoders for measured wheel travel; an IMU can help heading but cannot by itself establish absolute position.

## Current next action

The user's latest immediate request is pin-by-pin electrical planning. A held candidate is in `WIRING-PLAN-PENDING-POWER.md`; the next single physical test is isolated holder DC voltage/polarity in `TEST-01-BATTERY-VOLTAGE.md`. Chassis fit/stability completion is still not reported. Obtain actual motor/driver/supply/protection details before releasing the candidate table or connecting motor power. Phone mounting, final printed body, autonomous detours and floor-route execution follow the applicable staged tests.
