# KITTY Sentinel V3 — design review

V3 gives KITTY a more compact, coherent body while retaining the user's reported phone **164 × 76 × 8 mm**, wheels **62 mm diameter** and BO motors **61 × 20 mm length/width**. These measurements are user-reported; case inclusion, motor height/shaft and wheel hubs are unresolved. V3 is a parameterized draft, awaiting appearance and physical fit decisions.

The earlier R2.1 remains in `../r2/complete-draft/`. This V3 project is a separate revision so those review files can still be compared. Its 166 × 160 mm chassis footprint, fixed phone support, two drive wheels and caster arrangement are retained. There are no arms or servo phone loads.

## Changes and measured comparison

| Measure | R2.1 | V3 |
| --- | --- | --- |
| Whole draft width × depth × height | 224 × 239.599 × 281.6 mm | 224 × 226.291 × 262.6 mm |
| Neck height | 55 mm | 36 mm |
| Phone envelope centre above ground | 221.8 mm | 202.8 mm |
| Proposed printed parts | 13 | 13 |
| Total native printed-solid volume | 555,431.435 mm³ | 527,695.245 mm³ |

The solid CAD volume falls **4.99%** overall, **32.97%** for the neck and **19.25%** for the tail. These are measurements of the saved native solids, excluding bought-component stand-ins. They do not establish actual mass, print time, thermal performance, load capacity or stability. The baseline records saved R2.1 native volumes and STEP hashes from commit `d7425bda93082ee0fcb76f3ef628cd512a3fac2b` in `checks/baseline-r2.1.json`.

The shorter, slimmer neck has a smaller clipped flange with the same attachment pattern and cable route. The bezel has clipped outer corners while retaining phone clearance, ear recesses and accent grooves. The body has slightly broader corner facets, rounded side vents and rear service openings, a raised V chest mark and a small protective brow above the rounded sensor aperture. All these features belong to existing parts.

The curved tail sits 6 mm closer to the body and has a shorter key, a bevelled socket and a more compact profile. Its keyway is cut after the socket joins the rear shell, keeping the sloped shell wall clear of insertion. It remains a decorative detachable part, not a handle. Aqua eye shapes in the assembly are **display placeholders**, not printed eyes or proof that the face app is running on hardware.

## Parameters and unresolved interfaces

`parameters.json` records the complete proposed dimensions and measurement status. Coordinate units are millimetres. `tail_reach_scale=0.85` and `tail_rise_scale=0.95` are dimensionless profile factors. Values without a measurement-status entry are design decisions, not measurements.

| Selected design parameter | Value | Source / verification |
| --- | --- | --- |
| Body footprint | 166 × 160 mm | Retained design envelope; actual board/cable fit pending |
| Nominal shell wall | 3 mm | Proposed design; full wall/overhang audit pending |
| Neck height | 36 mm | V3 decision; actual phone loads and material strength pending |
| Tail root thickness | 12 mm | Proposed; sample fit and strength pending |
| Tail root/key length | 20 mm | Proposed; no fastener or retention-load test |
| Tail socket projection datum | 14 mm beyond rear body datum | Proposed; saved assembly checked |
| Tail per-side clearance | 0.4 mm | Saved flat-gap probes to ±0.01 mm; print-fit sample pending |
| M3 clearance bore | 3.4 mm | Proposed; actual screw/nut and printer tolerances pending |
| Usable printer volume | 220 × 220 × 250 mm | Assumed; all individual parts fit this envelope |

Still needed before a fitted print release: motor height and shaft offsets, wheel width/hub, caster ownership/installed dimensions, AA chemistry/cell count/holder, exact board footprints, phone case/camera/ports/cable bends, printer bed/material/nozzle and available fasteners. The rear openings reserve service access; they are not a fitted or rated power-cutoff mount.

## Files and quantities

| Part stem | Quantity | Function |
| --- | --- | --- |
| v3_base | 1 | Chassis, shared holes, caster passage and strap slots |
| v3_cover_front | 1 | Faceted front half, rounded sensor aperture, brow and raised V |
| v3_cover_rear | 1 | Rear half with vents, service access and integrated keyed socket |
| v3_motor_left / v3_motor_right | 1 each | BO channels, shaft windows and tie slots; shaft fit unverified |
| v3_battery_tray | 1 | Low assumed-holder tray; AA holder not selected |
| v3_electronics_deck | 1 | Universal tie-slot deck; actual boards not matched |
| v3_caster_bridge | 1 | Caster support; actual mounting pattern pending |
| v3_sensor_bracket | 1 | Front sonar plate/foot; actual PCB retention pending |
| v3_neck | 1 | Fixed tapered support, cable route and head holes |
| v3_phone_cradle | 1 | Clipped landscape frame, retention, side access and neck fasteners |
| v3_phone_cap | 1 | Removable upper retainer with passive ears |
| v3_tail | 1 | Flat-print curved tail, asymmetric key and cross-screw bore |

`v3_printed_assembly.stl` places the 13 plastic pieces. `v3_complete_draft.stl` adds 11 generic bought-component/display reference bodies. Both are **view-only multishell assemblies**, not single-piece manufacturing meshes. The stand-ins must not be printed as replacement hardware. Supplier catalog lookup was blocked by the cloud HTTPS proxy; no exact vendor-model match is claimed.

## Rebuild and verification

Use Python 3.12 with `requirements.txt`, then run from this directory:

```text
python build.py
python src/v3_tail_joint_review.py
```

In this cloud workspace use `CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python` for the interpreter prefix. STEP models are built by cadgen; conforming meshes are exported directly from saved native OCCT geometry with build123d at **0.003 mm / 0.05 rad** tolerance. This preserves the closed oriented-edge checks; the earlier browser mesh exporter produced nonmatching coplanar triangle edges. No `@stl` exporter is used here.

`checks/verify_exports.py` checks all saved parts for one valid positive-volume solid, Z=0 print datum, assumed bed fit, closed oriented mesh edges and mesh/native volume agreement within max(2 mm³, 0.1%). It checks key holes/passages, the phone envelope and neck attachment bores. All **276 pairs across 24 assembly bodies** are screened by conservative bounds; 42 candidates receive exact intersection checks with a **0.01 mm³** maximum. The keyed fit is probed and removal is checked at 0, 6, 12, 18, 24 and 35 mm rearward with the screw absent. These samples are not a general moving-hardware or full swept-clearance certification.

Generate the offline review with:

```text
python make_review.py --snapshots SNAPSHOT_DIRECTORY --out-dir OUTPUT_DIRECTORY
```

Run `python make_snapshots.py --out-dir SNAPSHOT_DIRECTORY` to generate the review packet from saved STEP files. The cloud instance accepts `--browser-executable /usr/bin/chromium`; other systems can use the Playwright browser installed with cadgen. `--write-job-only` saves the planned native snapshot job without rendering. Run `python checks/review_browser.py --directory OUTPUT_DIRECTORY --browser-executable CHROMIUM_PATH` to repeat the HTML checks over internal HTTP.

Expected native CAD image names: `assembly-hero.png`, `assembly-front.png`, `assembly-rear-angle.png`, `assembly-side.png`, `interior.png`, `v3_tail_joint_review.png`. The main `KITTY-V3-REVIEW.html` embeds these images and a lazy optional assembly mesh; `KITTY-V3-SAVED-VIEWS.html` is the smaller image-only backup. Six saved-view buttons work without JavaScript or WebGL. The committed ready-to-open copies are `review/index.html` and `review/saved-views.html`.

## Assembly review and print decision

1. Resolve the critical interfaces and use small fit samples before committing to a whole-body print. Review each separate part in the selected slicer for supports, orientation, walls and material choice; no G-code or print job is included.
2. Install the caster support, motor channels, battery tray, sensor bracket and electronics deck on the chassis. Check actual shaft/hub alignment, ground contact, restraint and cables.
3. Assemble the cover halves and then the fixed neck. The neck spans the split seam and must be released to service a cover. Cover screws enter from the base underside; nut pockets are accessible from the open interior.
4. Insert the tail and retain it using the proposed M3 cross screw and hex nut. The screw enters from the left and the nut from the right, above the wheel envelope. Remove the screw and pull straight rearward to detach. `v3_tail_joint_review.step` shows a 35 mm exploded separation and omits the screw.
5. Pad and fit the phone, then fasten the top retainer. Check retention, case/button/USB access and recessed head bolts. Verify the actual intended camera view: with the display facing forward, the phone's rear camera points backward.
6. Agree on the appearance and complete fit/slicer review before releasing the final manufacturing set. A successful geometric check or aesthetic approval alone does not establish physical fit or a working autonomous demo.
