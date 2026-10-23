# KITTY V7 — printing-service handoff

This package preserves PROMETHEUS on the front and KITTY on the back. It adds fore/aft adjustment to the replaceable BO-motor cradles and separate first-print gauges. The four gauges are process/interface tests, not extra robot body pieces.

**Release: geometrically checked; physical fit not approved. Quote and print the fit stage before the large body parts.** The user cannot absorb a full-body reprint. Provide the actual motors, wheels, phone with case and intended fasteners to the service for a dry fit. The AA holder is not bought; an outside holder is intended, and its mounting adapter can be designed later as a separate part. Do not glue a holder to the covers as the CAD-approved mounting method.

## Stage 1: first-print fit checks

Use the same printer, material and profile intended for the body. The socket sample has horizontal keyways and the key sample lies flat, matching the production socket/tail axis relationships. Match the production print orientations and support-removal method too; an easier reorientation of only the coupons may not reproduce the production fit.

| File | Quantity | What to check |
| --- | --- | --- |
| FIT_TEST_FIRST/v7_fit_tail_socket.stl | 1 | Three labelled keyways: 0.3, 0.4 and 0.5 mm nominal clearance per side |
| FIT_TEST_FIRST/v7_fit_tail_key.stl | 1 | Matching 12 mm key section with pull tab; insert without force |
| FIT_TEST_FIRST/v7_fit_phone_thickness.stl | 1 | 8.8 mm throat for the reported 8 mm phone plus proposed clearance; not a phone width/height or camera/port check |
| FIT_TEST_FIRST/v7_fit_screws.stl | 1 | Labelled 3.2/3.4/3.6/3.8 mm holes with the actual M3 screw |
| STL_PARTS/v7_motor_left.stl | 1 | Actual motor body, gearbox details, shaft window, tie restraint and fasteners; retain this part if it fits |

The production socket currently uses 0.4 mm clearance per side and 3.4 mm M3 holes. A different successful coupon means update the relevant CAD parameter and re-export before printing production parts. Do not scale an entire STL to fix a hole or joint. The sample key checks section/clearance and insertion depth; it is not the complete tail or a joint-strength test.

The phone gauge checks thickness only. Check the full measured phone/case outline, buttons, camera, cable and retention against the cradle STEP before printing that component. The motor cradle reserves 65 × 24 × 20 mm as the upper bounds of the user's estimated motor range, with 0.8 mm side clearance. Shaft height/offset, wheel hub and tyre axial width still require real measurements. Mount travel cannot correct an arbitrary motor shape or shaft height.

## Stage 2: separate robot parts

`STL_PARTS/` contains 13 proposed body parts, quantity 1 each. The left cradle from Stage 1 counts toward this total; do not order it twice. The internal battery tray is optional because the user plans an outside holder. That holder and its restraint have not been selected. Wheels, motors, phone, caster and electronics are bought components and are not supplied as printable meshes.

Import units: millimetres. Scale: 100%. STLs retain CAD axes and Z=0; select the actual build orientation in the slicer. For an FDM quote, PETG is a proposed starting material, with 0.2 mm layers, 4–5 walls and about 35% infill (about 50% for mounts/neck). These are quote inputs, not validated printer settings; the service should use its proven material/profile and the fit-stage results. Review local thin details and clamp loads before accepting the job.

The two covers have internal roofs; the measured 180-degree-X flips reduce support area. The electronics deck also benefits from inversion. The caster bridge and sonar bracket have useful 90-degree-X candidates. See PRINT-REVIEW.md and the per-part reports. Support removal must preserve nut pockets, cable openings, letters and the tail keyway. Do not repair a failed or non-watertight mesh by silently remeshing or changing scale; return the finding for a source correction.

Use separate machine screws and nuts, with flat washers on the slotted motor tabs. Confirm actual head/washer/nut fit and screw length; proposed holes are not a purchased-fastener guarantee. Avoid permanent glue at module joints. Tighten only enough to hold the part; plastic clamp strength is untested. Recheck clamping after initial use.

## Mechanical adjustment and repair

Each motor cradle has a 7.4 × 3.4 mm proposed mounting slot at each base screw: nominal fore/aft centre travel is ±2 mm. Reinforced 14 × 14 mm tabs preserve material around the slots. Rail openings provide proposed 8.8 mm head/washer clearance; checks use an 8 mm OD × 0.8 mm washer and 5.5 mm OD × 3 mm head envelope at the sampled positions. The relocated tie slots avoid those access openings. Actual hardware and clamp strength still require inspection. Native interference checks sample both extremes and the centre with that motor and wheel envelope moved together; actual hardware still needs a dry fit. Slots provide position adjustment before clamping, not a moving suspension joint.

The broader motor envelope moves the motor centres inward to ±63 mm. The electronics deck moves forward to Y=-42 mm with matched base holes. The optional battery tray uses aligned base/tray strap slots; its old side mounting ears were removed to clear the larger cradles. Check actual motor-shaft reach to the purchased wheel hub before approval.

Replace only the failed module where possible; REPAIR-MAP.csv names the file. The curved tail is removable by taking out its cross screw and pulling rearward. The tail socket remains integral with the rear cover: damage to that socket can require a rear-cover reprint. The neck spans the cover seam and must be released for cover removal. This design reduces some reprint costs; it cannot make every possible failure repairable without printing.

## Service acceptance record

- Printer/process/material/nozzle/layer height: __________
- Dimensional tolerance and fit-sample result: __________
- Actual motor body and shaft-centre height: __________
- Wheel diameter/axial width/hub and shaft engagement: __________
- Caster installed height and three-point ground contact: __________
- Actual phone/case/button/camera/USB access and retention: __________
- AA holder and secure external mounting plan: __________
- Fasteners/washer fit, supports, assembly access and quoted part quantities: __________

The user confirmed wheel outside diameter 62.5 mm including the tyre. Motor dimensions remain estimated ranges. No material-strength test, real ground-contact test, physical assembly, powered test or failure-free guarantee is claimed by digital checks.
