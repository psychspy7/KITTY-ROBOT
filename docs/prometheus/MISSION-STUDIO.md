# PROMETHEUS / KITTY Mission Studio

The current selection demo is a working **software prototype**. The physical
robot is still being built. No physical device transport is included.

Download [the complete offline studio and editable source](PROMETHEUS-MISSION-STUDIO-COMPLETE.zip).
Extract the ZIP, then open `PROMETHEUS-MISSION-STUDIO.html` in desktop Chrome or
Edge with graphics acceleration enabled. No internet or model installation is
needed. Press **Play guided demo** for the English 2:12 presentation.

The release preserves the V7.1 body meshes and adds virtual front ultrasonic
plus IR, rear ultrasonic, and a planned third corner ultrasonic on a scanning
servo. It includes a 54-wire editor and nominal voltage probes, attach/detach
inspection, exploded assembly, geometric sensing, differential-drive motion,
known-prior occupancy/A* routing, obstacle insertion, fault/stop controls, and
an actual rendered-RGB colour-marker tracker. The phone face, indicators and
optional browser buzzer follow the simulation state.

The laptop-brain workspace shows the intended phone/perception/control flow
and editable KITTY prompt. Default chat uses labelled offline rules. The ZIP
also contains a loopback server for an already installed Ollama model; no
weights are bundled. Typed STOP is local and does not wait for inference.
Model output is limited to text and supported simulation intents.

A separate AeroKitty study animates four-wheel drive, folding wheel/rotor pods,
takeoff, flight and landing. This is a concept animation without aerodynamics,
a fitted airframe or a real flight controller.

**Record video** saves a composed 1920x1080 WebM with 3D, camera, map, face,
English captions and persistent prototype/concept labels. Browser narration is
not mixed into that file. The included MP4 is a silent captioned
backup from the same renderer. The ZIP supplies its English narration script
and SRT captions, plus reproducible video-render tooling.

Source, runtime limits and test commands are in
[software/mission_studio/README.md](../../software/mission_studio/README.md).
The release verification records bind checks to the tested HTML and source
hashes. Real phone audio/camera operation, local-model inference, user GPU
performance, electrical loads and physical robot operation are unverified.
Current print files and commissioning firmware are unchanged.

Verification: 25 Node cases, 23 Python cases and 28 real Chromium check groups
passed. Browser checks include decoded recording frames, rendered-pixel follow,
edited project round-trip, stop/cancellation and graphics failure. See
[review resolutions](MISSION-STUDIO-REVIEW.json), the
[release verification](MISSION-STUDIO-VERIFICATION.json), and the ZIP evidence.
