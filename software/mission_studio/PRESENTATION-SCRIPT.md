# English presentation / 2:12

Keep the software-prototype label visible. Use the exact implemented terms:
known arena prior, simulated range observations and a pixel colour-marker
tracker. Do not introduce the flying scene as a finished or flight-tested robot.

**0:00 — Meet KITTY.** “This is KITTY, Team Prometheus's vision-based assistant
prototype. The phone provides a face, camera and microphone; the laptop hosts
perception, mapping and the prompted assistant.”

**0:10 — The connected system.** “The laptop requests intent through a guarded
controller. The planned ESP32 and motor driver handle low-level motion.
Conversation never bypasses obstacle checks or a stop latch.”

**0:23 — Inside the prototype.** “Here is the virtual assembly and wiring. We
have front ultrasonic and IR sensing, rear ultrasonic, and a planned third
ultrasonic on a scanning servo. The speaker uses a separate amplifier.”

**0:37 — Map and radar.** “The simulation starts with a known test arena. The
servo sweeps a range ray; front and rear observations update the occupancy
view. The robot-eye camera tracks a coloured marker from rendered pixels.”

**0:48 — Navigation.** “A* plans a route around inflated obstacles. Watch the
new crate: the sensor observations cause the route to be reconsidered. The
controller can stop and report blocked rather than assume a safe path.”

**1:16 — Stops.** “Here we inject command-link loss. Motion stops locally.
Restoring an input does not restart the mission; reset and a new request are
required. These are simulated checks, not measured hardware stopping times.”

**1:28 — Personality.** “The phone face, LED and buzzer reflect the same state.
The default offline replies are labelled. An optional local-model bridge uses
KITTY's prompt and validates the returned intent before the simulator acts.”

**1:40 — Future concept.** “Our future study is AeroKitty: four wheels for ground
travel and folding wheel/rotor pods for a flying configuration. This is a
transformation and flight animation. A real version needs a new flight-rated
airframe, propulsion, power and autopilot, followed by physical validation.”

**2:05 — Next milestone.** “Today we are presenting the working software
prototype. The next milestone is verified physical sensing and drivetrain
integration. Team Prometheus, KITTY CORP.”
