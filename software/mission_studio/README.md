# PROMETHEUS / KITTY Mission Studio

An interactive, video-ready **software prototype**, built for Team Prometheus
at KITTY CORP. It includes the V7.1 robot body, a working virtual circuit and
navigation laboratory, a phone face and synthetic camera, a laptop-brain view,
and a separately labelled four-wheel folding/drone concept.

## Open it

Open **PROMETHEUS-MISSION-STUDIO.html** in current desktop Chrome or Edge.
Keep graphics acceleration enabled. No installer, internet, account, Python,
model weights or CDN is required for the standalone simulation.

GPU draws 3D; CPU runs sensing, mapping, planning and the pixel tracker; RAM holds
the embedded meshes. **Auto GPU** reduces resolution and shadows when rendering
is slow. Balanced/High GPU keeps the selected quality. Actual performance on
your computer is not established by the cloud verification.

1. **Play guided demo** runs an English 2 minute 12 second presentation. You can
   pause or scrub chapters. The mission and surprise obstacle use the actual
   simulator/controller; the flying portion is a concept animation.
2. **Mission lab:** Go to marker or click the map to request a goal. Shift-click
   the map to add a crate; + Obstacle inserts one ahead of the route. Hold the
   arrows/WASD to drive manually. Release stops; Space latches STOP. A fault or
   timeout needs Reset and a fresh mission. An unreachable goal can remain
   BLOCKED; do not describe every arbitrary environment as solvable.
3. **Engineering:** inspect or detach components, explode the body, connect or
   remove nets, and compare nominal rail/HIGH-level voltages. Try connecting
   front.ECHO directly to esp.D32 to see the model reject raw 5 V ECHO. Restore
   circuit reinstates all 54 preset wires and components. Circuit edits disarm.
4. **Laptop brain:** inspect the phone-to-laptop-to-controller flow and edit the
   personality prompt. Standalone chat is explicitly **offline demo rules**.
   Real local language-model responses are optional, as explained below.
5. **Future concept:** four-wheel drive, folding wheel/rotor pods, animated
   takeoff/flight/landing and a transformation slider. This is a new visual
   airframe study, not a fitted or flight-validated design.

Drag/zoom in Orbit mode; use Hero, Top, Follow and Robot eye presets. Save/Open
project preserves scene obstacles, circuit and nominal pack voltage, never an
armed state. Exported event logs identify their data as simulation.

## Make the video

Press **Record video**, then **Play guided demo**. Press Stop + save, or let the
guided demo finish. The WebM contains a composed 1920x1080 frame: 3D scene,
camera, map, state, face, English captions and persistent software/concept
labels. It records the rendered frame rate; it cannot manufacture smoothness on
an overloaded GPU. Close other heavy applications and choose a suitable quality.

Browser narration is audible when **English narration** is enabled, but is
**not mixed into the WebM**. Use your screen recorder with system audio, or add
your own narration using PRESENTATION-SCRIPT.md and ENGLISH-CAPTIONS.srt.
Microphone recognition is optional browser speech recognition, may use the
browser's speech service, and is requested only by clicking Mic. Neither actual
phone microphone capture nor speech services were tested on your devices.

PNG exports use the same composed frame. If MediaRecorder is unavailable, use
your normal screen recorder. If WebGL fails, the saved body image and virtual
circuit controls remain available; interactive 3D needs graphics support.

The included **PROMETHEUS-KITTY-GUIDED-DEMO.mp4** is a ready-made
1920x1080 English-captioned backup, sampled from this same simulation. It is
silent; the narration script is supplied for your voiceover. The complete ZIP
contains the interactive studio, reproducible source, verified media and evidence.
The MP4 is also available as a separate download.

Developers with Chromium, Playwright and FFmpeg can reproduce the video with
`python render_video.py --url PRINTED_LOCAL_URL --out OUTPUT_FOLDER --fps 12`.
The tool checks the served HTML against the output build, writes a temporary
movie, probes it, then publishes it with a hash-bound verification record.

## What is implemented

- Differential-drive integration in metres/radians, local manual-command
  expiration, explicit stop/fault latches, geometric range/IR sensing, a servo
  sweep and a conservative circular collision guard.
- Occupancy observations and A* with inflated obstacles. The default scene
  starts with a **known arena geometry prior**; range rays add observations.
  Pose is simulation state, not a localization estimate. This is not SLAM or a
  reconstructed real room. New crates are not silently inserted into the prior.
- An actual pixel threshold/box tracker for the magenta marker in rendered RGB
  frames. It is **not a trained detector** or general person/object recognition.
  Camera-follow requires a current marker; frame loss/staleness stops it. The
  route still uses the known virtual target location; the image is not a metric
  depth/pose estimator. Aim the robot toward the marker before requesting follow.
- The same state drives the phone face, virtual LED and optional synthesized
  buzzer. Phone camera/microphone/display and amplified external speaker have
  distinct roles. No real phone, motor, ESP32 or microphone is connected.
- Selected nominal circuit constraints: intended signal paths, common reference,
  source conflicts, raw ECHO overvoltage, independent output shorts and missing
  nets. Not SPICE, firmware emulation or arbitrary electronic fault diagnosis.

Three ultrasonics are shown: front, rear and a **planned additional corner
sensor** on a servo. Earlier inventory confirmed two; this simulation does not
establish ownership of a third or physical fit of its mount. The IR uses an
explicit nominal 3.3 V I/O model; the real module remains unidentified.

The simulated pin preset retains the commissioning-kit drive/front/rear/LED/
buzzer numbers and adds radar TRIG GPIO4, conditioned ECHO GPIO34, servo GPIO14
and IR GPIO35. These are **simulation assignments**, not a released physical
pinout. Real board conflicts, input levels, wiring, supply/load, protection,
motor stall current and sensor interfaces still require the actual hardware
review. No current print files or physical commissioning firmware are changed.

ECHO conditioner blocks represent upper 2.2k and lower 3.2k (2.2k + 1k series),
2.963 V nominal from a model 5 V HIGH. Probe readings are nominal DC or signal
HIGH levels; floating nodes display N/A. Motor current, transients, fuse trip,
regulator/servo load, acoustics/cross-talk, friction and stopping distance are
not calculated. The fuse and servo 5 V source are ideal model components.

The flying concept needs a new airframe, mass/thrust/structural validation,
flight-rated power, brushless motors/ESCs and an autopilot. BO motors/TB6612 do
not become a drone flight system by folding. Its trajectory and pod movement
are animated, without aerodynamics or physical flight control.

## Optional real local conversation

The ZIP's START-STUDIO-WINDOWS.cmd runs a loopback Python server with the same
HTML. Python 3.10+ standard library is sufficient. Without a configured model,
the page keeps its labelled offline rules.

For an **already installed** Ollama model, run:

```text
python server.py --model YOUR_INSTALLED_MODEL_NAME
```

Or run START-WITH-LOCAL-AI.cmd to select a model returned by your local Ollama
server. These launchers do not download models. If you need to install a model,
use its official runtime instructions and benchmark on your laptop first.
The repository's MODEL-CHOICE.md contains an unbenchmarked starting candidate;
no model is bundled or claimed tested on your Acer.

The bridge calls only http://127.0.0.1:11434/api/chat. It validates output to
plain reply text and a small intent allowlist. Conversation cannot clear the
stop latch, write GPIO/PWM, execute code or reach hardware. Model latency/outage
does not block the simulator's local controller. Configured status is distinct
from a successful inference. Bridge tests use explicit stubs, not a model run. Typed/spoken imperative STOP
is handled locally before any model request. The model receives a bounded
snapshot of virtual range and marker status. Browser cancellation discards late
intents; at most one backend inference runs at a time and may finish or time out
after the browser cancels.

## Build and verify

```text
python build_release.py --out OUTPUT_FOLDER
node --test tests/core.test.js
python -B -m unittest discover -s tests -p "test_*.py" -v
python server.py --directory OUTPUT_FOLDER --no-browser
python tests/check_browser.py --url PRINTED_LOCAL_URL --out OUTPUT_FOLDER
python tests/check_follow.py --url PRINTED_LOCAL_URL --out OUTPUT_FOLDER
python tests/check_graphics.py --url PRINTED_LOCAL_URL --out OUTPUT_FOLDER
python build_release.py --out OUTPUT_FOLDER --archive
```

Output must be outside the source folder. The portable source ZIP includes
Three.js/OrbitControls and their MIT license. Body meshes and fallback render
come from the existing V7.1 Assembly Lab, with hashes retained. Their physical
fit status remains unverified. Generated verification distinguishes cloud
software checks from user-device GPU performance, real inference and hardware.
