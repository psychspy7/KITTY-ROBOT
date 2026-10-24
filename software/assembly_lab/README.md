# KITTY Assembly Lab

Team Prometheus's offline 3D assembly, wiring and behavior workbench for V7.1. This is a browser simulation, with no physical outputs or device transport. The CAD body is unchanged.

## Open and use

Download **KITTY-ASSEMBLY-LAB.html** and open it in current desktop Chrome or Edge with graphics acceleration enabled. No installer, account, server, internet connection or CDN is needed. Mobile layouts work, but a laptop and mouse give more workspace. GPU draws the scene; CPU evaluates the nominal circuit and kinematics; RAM holds embedded meshes. “Ultra GPU” raises rendering resolution; no dedicated NVIDIA GPU is required. Performance depends on the device, browser and display resolution.

1. **Assemble:** choose a part in the library or click it. Attach restores its nominal design position; detach puts it on the tray. Assembly exercise starts with the base and loose components. Use “Find next unattached part” to guide the sequence. Offset fields, rotation and drag mode allow free placement; moved drive components must return to their mount before simulation arming. See-through covers expose the interior. Exact body meshes are retained; moving components does not edit manufacturing files.
2. **Wire:** select two endpoints or click two terminal markers / pin buttons. Connect, inspect and remove individual wires. Load demo circuit creates a complete 31-wire example. The virtual multimeter calculates nominal DC differences for referenced nodes. Floating and switching outputs are not DC measurements.
3. **Test arena:** choose AA chemistry, arm, then hold a drive control or WASD/arrows. Release stops. Space activates the stop latch; Escape disarms. Front and rear range rays respond to obstacles. Add, drag or edit obstacles. Try motor switch off, command link loss, invalid sensors and emergency stop. They require explicit rearming after restoration. Page blur/hidden status also disarms. Commands expire after 500 ms without renewal. Runtime starts disarmed after loading a project.
4. **Save:** explicit Save project downloads JSON. Open project validates it before replacing the current state. Assembly, offsets, wires, nominal settings and obstacles are preserved; armed state and motion are never saved. The browser may also cache edits locally; file-mode storage availability varies.

An image-first fallback remains when graphics fails. The wire editor, model checks, project import/export and guide remain usable, but 3D assembly and drive controls need WebGL. Retry graphics after enabling browser graphics acceleration. Wireframe depicts geometry, while Wire mode shows electronic connections.

## What the model represents

- Exact V7.1 STL body geometry from the verified dual-ultrasonic viewer; both HC-SR04 positions are present. Bought motors, wheels, phone and caster use the existing reference envelopes. Other boards, two AA holders and optional components are approximate visual objects, not fitted CAD additions.
- Educational **classic ESP32** signal names: driver PWMA/D25, AIN1/D26, AIN2/D27, PWMB/D18, BIN1/D19, BIN2/D21, STBY/D22. Front TRIG/D32 and conditioned ECHO/D33; rear TRIG/D16 and conditioned ECHO/D17. Exact actual board/module and carrier pin order remain unidentified. These are model assignments, not an approved physical pinout.
- Ideal 5 V virtual USB logic source, 3.3 V model regulator, two two-cell holders in series, ideal motor switch and common-ground constraints. Four AA cells model nominal 6 V alkaline or 4.8 V NiMH, without load sag, discharge or internal resistance.
- Two nominal ECHO divider blocks: upper 2.2k, lower 3.2k (2.2k + 1k series), giving 2.963 V for nominal 5 V input. Both blocks together require four 2.2k and two 1k resistors in this example; real counts, tolerances, supply limits and GPIO thresholds require checking. ECHO is treated as its peak/high voltage for wiring checks, not as a continuous physical DC output.
- Selected supply-short, ground, GPIO overvoltage, signal-path and motor-output constraints. The displayed “MODEL READY” means those selected constraints pass. It does not validate arbitrary circuits or every possible electrical error.
- Two-wheel differential-drive kinematics in millimetres, nominal 198 mm wheel track, sampled nine-ray sensor sectors and 140 mm conservative circular collision footprint. Motion and geometry are illustrative; no actual dynamics or stopping-distance claim. Both sensors are sampled independently; acoustic cross-talk and trigger scheduling are not represented.
- Wheel animation, range rays, changing face eyes, movable arena objects and simulated stop/fault behavior.

Optional Uno, servo, IR, microphone, relay, LED, capacitor, breadboard and perfboard have **placement-only behavior** and displayed terminal labels. Their electrical functions, real pin order and physical mounts are unverified. The breadboard does not imply connected strips; only its two shown rail terminals exist in this model. The servo does not actuate the fixed phone neck. The phone is a display envelope; no real camera, speech or AI model runs in this lab.

This is not SPICE, a firmware emulator or a replacement for testing actual components. It cannot compile/upload Arduino code or diagnose the ESP32 USB connection. Motor startup/stall current, driver thermal capacity, regulator behavior, shorts through component internals, tolerances, physical fits, fastener strength, friction, centre of mass, battery protection and electrical transients are outside the model. Follow the hardware intake and staged real tests before wiring or powering KITTY.

## Web / online use

The same single HTML can be served unchanged on a static host. No public deployment is created by building this package. To serve it on your own computer, put the HTML in a folder, open a terminal there, run `py -3 -m http.server 8000 --bind 127.0.0.1` on Windows (or `python3 -m http.server 8000 --bind 127.0.0.1`), and visit `http://127.0.0.1:8000/KITTY-ASSEMBLY-LAB.html`. This is a local address on the computer running that command. Open the HTML directly for the simplest offline use.

## Rebuild and verify

Source requires Python 3 standard library and Node.js for logic tests. Browser checks additionally use Python Playwright and Chromium. Body assets are bundled under `assets/` with provenance and hashes; no CAD regeneration is needed. Source ZIP includes the upstream MIT Three.js and OrbitControls files. Inside this repository the builder reuses `design/v7/advanced-viewer/vendor`.

```text
python build_release.py --out YOUR_OUTPUT_FOLDER
node --test tests/core.test.js
python -B -m unittest discover -s tests -p "test_build.py" -v
python tests/check_browser.py --directory YOUR_OUTPUT_FOLDER
python build_release.py --out YOUR_OUTPUT_FOLDER --archive
```

Evidence records software checks performed in cloud Chromium, not GPU performance or physical operation on your machine. Cloud browser policy blocks direct `file://` navigation; the exact HTML is verified with networking disabled through `set_content` and through local HTTP. Existing print-service ZIP and manufacturing status remain unchanged.
