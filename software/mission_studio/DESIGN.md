# PROMETHEUS Mission Studio

The deliverable is an offline, video-ready interactive simulation, alongside a
local optional language-model bridge. It must remain visibly identified as a
software prototype in the viewport, recorded video and exported evidence.

The current simulated robot retains the V7.1 body and two driven wheels. It has
front ultrasonic + short-range digital IR, rear ultrasonic and an additional
corner ultrasonic on a scanning servo. The third ultrasonic and its servo mount
are planned virtual additions, not a claim of ownership or a fitted CAD change.
Phone camera/microphone/display, laptop perception/map/brain, ESP32 control and
external amplified speaker are represented in their appropriate roles.

Acceptance:

- A runnable 3D scene, real differential-drive integration, collision guard,
  geometric range sensing, scanning radar, occupancy mapping, A* routing and
  stop/replan behavior. Goals and obstacles are editable.
- A robot-eye RGB view and pixel-based coloured-marker tracker. Scene labels
  and synthetic sensor/map observations remain distinguished from a trained
  detector or real camera evidence.
- A working virtual circuit with editable nets, nominal rail checks, ECHO
  conditioning, servo/IR/indicators and fault injection. It is not SPICE or an
  approved physical wiring plan; previous commissioning firmware is unchanged.
- A live phone face, LED/buzzer responses, laptop decision trace, prompted
  conversation with labelled offline rules, and optional actual local model
  responses through an explicitly configured loopback service.
- Guided demonstration, camera presets, recording with visible HUD/captions,
  snapshots, project export/import, performance controls and a graphics-failure
  fallback. No CDN or mandatory account/model download.
- A separate future concept with four driving wheels, folding wheel/rotor pods
  and animated takeoff/flight/landing. It must be labelled a concept animation,
  with no claim of aerodynamic, structural or flight-controller validation.

No physical device transport, serial output, GPIO writes or autonomous hardware
actions belong in this studio. Optional AI does not bypass the simulator's
mission guard or clear a stop latch. No claim of winning/selection is made.
