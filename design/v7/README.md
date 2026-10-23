# KITTY V7 — print-service revision

PROMETHEUS on the front and KITTY on the back are retained as raised geometry in the covers. This revision addresses the user's request to limit full-body reprints: replaceable modules, slotted motor mounts, and four separate first-print interface samples. The previous V7 appearance package is preserved outside this project; this service revision is the current export.

**Geometry checked; physical fit not approved.** Give the printing service `PRINT-SERVICE-BRIEF.md` and begin with its first-print stage. The source release stays `DRAFT_NOT_FIT_APPROVED`; a manifold STL does not prove that real hardware fits.

## What changed

- Motor estimates are now 61–65 × 22–24 × 18–20 mm. The cradles reserve the 65 × 24 × 20 mm upper envelope plus 0.8 mm side clearance. Motor centres move to X=±63 mm to clear the shell.
- Each motor tab is 14 × 14 mm with a proposed 7.4 × 3.4 mm mounting slot, giving ±2 mm fore/aft centre travel. Rail openings clear an 8 mm OD × 0.8 mm washer and a 5.5 mm OD × 3 mm head envelope at the sampled positions; tie slots sit away from these openings. Clamp using matching separate fasteners and washers; actual strength and hardware fit are untested.
- The electronics deck moves to Y=-42 mm, with matching base holes, so it clears the larger cradles.
- The optional internal AA tray loses its wide mounting ears and uses the existing aligned tray/base strap slots. The user intends an outside AA holder, not yet bought; that external restraint is not designed or approved.
- Wheel outside diameter is corrected to 62.5 mm including the tyre. Axial tyre width/hub and shaft location remain unmeasured. The 9 mm shaft-centre assumption determines the proposed 16.25 mm base datum; real three-point ground contact still needs verification.
- Four separate samples check tail clearance, key section, phone thickness and screw-hole process fit. They do not replace hardware measurements or a dry fit.

## Delivery folders and quantities

`STL_PARTS/` contains the same 13 proposed body part files, each independently replaceable. Quantity is 1 except that `v7_battery_tray` is optional for the current outside-holder intent. The first left cradle counts toward the production quantity if it fits. No purchased wheel, motor, phone, caster or electronics mesh belongs in this folder.

| Body STL stem | Function |
| --- | --- |
| v7_base | Chassis and matched module holes/strap slots |
| v7_cover_front | Front cover, PROMETHEUS and folded collar |
| v7_cover_rear | Rear cover, KITTY, service windows and integral tail socket |
| v7_motor_left / v7_motor_right | Adjustable, individually replaceable BO cradles |
| v7_battery_tray | Optional internal strap tray; holder unselected |
| v7_electronics_deck | Universal tie-slot deck |
| v7_caster_bridge | Separate caster support; real installed height pending |
| v7_sensor_bracket | Separate sonar support; real board retention pending |
| v7_neck | Fixed phone support, cable route, cuff and rear tie eyes |
| v7_phone_cradle | Separate landscape phone frame |
| v7_phone_cap | Removable phone retainer and passive ears |
| v7_tail | Removable curved tail with keyed root |

`FIT_TEST_FIRST/` contains four additional sample STLs: `v7_fit_tail_socket`, `v7_fit_tail_key`, `v7_fit_phone_thickness`, and `v7_fit_screws`. The socket sample labels 0.3/0.4/0.5 mm clearance per side. The current production socket is 0.4 mm. The phone sample has an 8.8 mm throat and checks thickness only. Screw samples are 3.2/3.4/3.6/3.8 mm; production holes are 3.4 mm. Match the production print orientations and profile when checking the samples.

The package also contains native individual STEP files, source, evidence, a first-stage order list, a part/replacement map and a 1:1 paper phone outline with a 100 mm calibration line. The whole-robot STEP and embedded preview mesh are viewing references, not a one-piece print. There is no full-assembly STL or G-code in the service package.

## Process and assembly notes

Use millimetres and 100% scale. The STLs retain CAD axes and Z=0; select actual build orientations in the slicer. Inverting the cover halves and electronics deck reduces measured internal-roof support area. PETG/FDM is a proposed quote option; service-specific material/nozzle/layer/strength/tolerance choices require its validated profile and fit-stage results. `PRINT-REVIEW.md` separates mesh facts from these unverified choices.

Keep screws/ties accessible and avoid permanent glue at replaceable interfaces. The neck spans the cover seam and must be released to remove the covers. Remove the tail cross screw before pulling rearward. Its socket remains integral with the rear cover; damage there may require one rear-cover reprint. Mounts, phone retainer, caster bridge and other small modules can be replaced without printing the entire body. No design can make every unknown failure repairable without replacement parts.

The rear window is reserved access, not a fitted or rated cutoff mount. Do not use the tail, neck or tie eyes as carrying handles. Actual phone load/retention, USB/button/camera access, AA-holder restraint and real motor/caster ground contact remain unresolved.

## Evidence

The body checks cover all 13 saved native parts: one valid solid, positive volume, Z=0, assumed 220 × 220 × 250 mm bed fit, closed consistently oriented mesh edges, and mesh/native volume agreement within max(2 mm³, 0.1%). Branding slices retain ten front glyphs and five rear glyphs. The 24-body reference assembly passes 276-pair static screening (40 exact queries), maximum 0.01 mm³ overlap. The two motors are separately sampled at -2/0/+2 mm with their motor/wheel envelopes moved together; full nominal M3-clearance cylinders clear both slots. This samples positions, not every possible moving configuration.

Tail gaps are probed to ±0.01 mm and withdrawal is sampled at six positions with the screw absent. The four samples pass their own valid-solid, oriented-mesh, native-volume, bed and dimension probes. Thickness/support measurements and actual CAD renders are retained. The self-contained viewer is checked on desktop/mobile and without JavaScript or working WebGL.

Total native printed-body solid volume, including the optional tray, is 532,972.917 mm³, 4.04% below the saved R2.1 baseline. This is geometry, not measured mass, cost, print time, strength or stability.

## Remaining inputs

The phone is user-reported 164 × 76 × 8 mm, case inclusion unconfirmed. Motor ranges and the wheel diameter above are user reports, not inspected parts. Unknowns remain motor shape/shaft/hub, wheel axial width, installed caster dimensions, AA chemistry/count/holder/restraint, board/connector envelopes, phone case/ports/camera, fasteners and printer/material/nozzle/profile. User-requested common yellow-motor catalog checks were blocked by HTTPS proxy 403, including a retry; no matching vendor drawing or shaft datum was obtained. See `checks/reference-research.json`.

## Rebuild

Use Python 3.12 and `requirements.txt`, then from this folder:

```text
python build.py
python build_fit_samples.py
python src/v7_tail_joint_review.py
python make_snapshots.py --out-dir SNAPSHOT_DIRECTORY
python record_evidence.py --snapshots SNAPSHOT_DIRECTORY --visual-review-note YOUR_ACTUAL_INSPECTION_NOTE
python make_review.py --snapshots SNAPSHOT_DIRECTORY --out-dir OUTPUT_DIRECTORY
python checks/review_browser.py --directory OUTPUT_DIRECTORY --browser-executable CHROMIUM_PATH
```

Cloud interpreter prefix: `CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python`. Snapshot generation accepts `--browser-executable /usr/bin/chromium`. Native OCCT exports use 0.003 mm / 0.05 rad mesh tolerances; the earlier browser exporter did not preserve matching triangle edges. The font and license are bundled. Geometric and browser checks are reproducible; physical fit and printing are not claimed.
