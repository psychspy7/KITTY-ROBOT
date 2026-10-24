# V7.1: front and rear ultrasonic mounting

The V7.1 assembly adds a removable rear HC-SR04 carrier while preserving the original thirteen V7 body meshes, including the optional internal tray. There are now fourteen available body STL files, thirteen ordered by default. Wheels, motors, caster, phone and sensors remain purchased parts. The updated shop ZIP contains only nineteen STLs (fourteen body files including the optional tray, plus five gauges) and one instruction-page PDF.

The rear sensor points along +Y, offset to X=50 mm beside the tail, with transducer centres at Z=72 mm. The carrier shares the two existing rear base/cover M3 holes at X=±68, Y=65 mm. Its 3 mm bridge sits under the base; the existing body pieces need no modification. Two side tie slots, lower corner saddles, front spacers, a central header notch and an outer-post strain-relief eye retain a generic sensor module without assuming its mounting-hole pattern. The sensor and ties must be fitted to the detached bracket first; remove the carrier before servicing the module or removing the rear cover. Two bolts require additional grip length for the 3 mm bridge and actual washer stack. Check the actual bolt engagement, component clearance and ground clearance before assembly.

Geometry assumptions are explicit in `rear-sensor-parameters.json`: generic 45 × 20 × 1.6 mm PCB, 16 mm transducers on 26 mm centres, 12 mm can projection, a conservative component/header envelope and 17.6 mm printed can openings. They are not a verified vendor match. The added upright face gauge tests the same holes, ties and header opening with the real sensor. Print the gauge and carrier using matching part directions/profile/support removal. The rear bracket is a small independently replaceable part if the actual module needs correction. Actual sensor coverage, print tolerances, fasteners, strength and electrical operation remain unverified. The unidentified IR sensor and outside AA holder still require their own mounting decisions.

Checks read the saved native assembly: individual solids and oriented STL edges, module/case intersections, existing-bolt/head/washer paths, motor adjustment extremes, rear service-opening approach corridors, KITTY wordmark visibility, sampled tail withdrawal, bracket withdrawal and two rearward geometric sight envelopes. The sight-envelope check uses a 20-degree half-angle over 200 mm; it does not measure acoustic performance. Match each digital result to the declared generic sensor envelope, not to unmeasured actual hardware.

Build from `design/v7` using the existing CAD Python environment:

```sh
CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python src/v7_dual_ultrasonic.py
CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python src/v7_fit_rear_sensor_face.py
CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python checks/verify_rear_sensor.py
CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python make_rear_snapshots.py
```

Run the DfAM skill's exact-mesh `measure` and six-axis `orientations` commands for both new meshes at the conditional FDM 45° angle. Keep complete reports under the output folder's `dfam/`. Then prepare, view and package:

```sh
/workspace/.kitty-cad-env/bin/python package_dual_sensor.py
CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python advanced-viewer/build_viewer.py --dual-ultrasonic --service /workspace/outputs/kitty-robot/v7-dual-ultrasonic --out /workspace/outputs/kitty-robot/v7-dual-ultrasonic
/workspace/.kitty-cad-env/bin/python advanced-viewer/check_browser.py --dual-ultrasonic --directory /workspace/outputs/kitty-robot/v7-dual-ultrasonic
/workspace/.kitty-cad-env/bin/python package_dual_sensor.py --archive
```

The original V7 assembly, service package and viewer remain historical artifacts. Use the explicitly named V7.1 front-and-rear shop ZIP and dual-ultrasonic HTML for this revision. No powered test, firmware upload or print job is performed by these tools.
