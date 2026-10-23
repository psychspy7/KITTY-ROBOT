# KITTY V7 — Team PROMETHEUS

V7 is the user's final appearance export of the compact KITTY body. It adds **PROMETHEUS on the front** and **KITTY on the back** as raised geometry fused into the existing cover parts. The rear name sits below the tail mount and above the service openings so the tail does not hide it. Letter spacing keeps the two T bars separate. Letters print in the shell material and can be painted afterward.

The folded chest collar, faceted neck cuff, rear cable-tie eyes, clipped phone bezel and detachable curved tail are retained from V3 Signature. V3 is preserved under `../v3/`. V7 is the requested version label; it does not imply additional fitted revisions or physical prototypes.

## What to print

The delivery ZIP contains **13 separate STL body parts in `STL_PARTS/`**, each with quantity 1. Bought wheels, motors, phone, caster and electronics are excluded from that folder. Use the purchased 62 mm BO wheels. The whole-robot STEP in `REFERENCE_ONLY/` and the HTML model include bought-component stand-ins for viewing; they are not manufacturing objects. No whole-assembly STL is included in the delivery ZIP.

| STL stem | Function |
| --- | --- |
| v7_base | Chassis with shared mounting holes and caster opening |
| v7_cover_front | Front shell, PROMETHEUS, folded collar and sensor brow |
| v7_cover_rear | Rear shell, KITTY, service openings and keyed tail socket |
| v7_motor_left / v7_motor_right | One BO motor channel each; height/shaft/hub fit pending |
| v7_battery_tray | Assumed AA-holder tray with strap slots |
| v7_electronics_deck | Universal tie-slot support; actual board fit pending |
| v7_caster_bridge | Assumed caster support; installed caster dimensions pending |
| v7_sensor_bracket | Sonar support; actual board retention pending |
| v7_neck | Fixed support, cable route, faceted cuff and rear tie eyes |
| v7_phone_cradle | Landscape phone support and fastener pattern |
| v7_phone_cap | Upper phone retainer with passive ears |
| v7_tail | Curved decorative tail with asymmetric key and cross-screw bore |

All coordinates are **millimetres**. Import at 100% scale. Individual STL files use a Z=0 CAD datum; these axes are not a validated slicer setup. Before printing, review `PRINT-REVIEW.md` in the ZIP: turning both cover halves 180 degrees about X reduces internal roof support area; flipping the electronics deck also helps. The neck, details and other pieces still need a slicer support strategy. Do not print these upright by default without reviewing those roofs and overhangs.

## Fit and release state

`release: DRAFT_NOT_FIT_APPROVED` means that the design files are exported and geometrically checked, while the real component fit and printer profile remain unverified. The user's V7 request authorizes the design export; it is not physical fit evidence. No printer job or G-code is included.

User-reported dimensions are phone 164 × 76 × 8 mm, wheel diameter 62 mm and BO motor length/width 61 × 20 mm. Case inclusion, motor height and shaft offsets, wheel width/hub, caster ownership/installed height, AA chemistry/count/holder, exact board/connector dimensions, phone camera/port/cable clearance, fasteners and printer bed/material/nozzle remain unresolved. These values stay named assumptions in `parameters.json`. Use small interface samples before a full-body print.

| Selected design value | Value | Status |
| --- | --- | --- |
| Chassis footprint | 166 × 160 mm | Retained design value |
| Nominal shell wall | 3 mm | Proposed; sampled mesh report included, exhaustive audit pending |
| Fixed neck height | 36 mm | Proposed; no SG90 phone load assumed |
| Rear tie slots | 3.2 × 7 mm | Proposed; actual ties/cables unmeasured |
| Raised lettering relief | 1.0 mm | Proposed; 0.35 mm embedded root, 0.7 mm glyph spacing |
| Tail key/root length | 20 mm | Proposed; one clipped corner prevents inversion |
| Tail clearance per side | 0.4 mm | Native geometry probes passed; physical fit sample pending |
| Cross-screw bore | 3.4 mm | Proposed M3 screw/hex nut; hardware and strength unverified |
| Printer envelope | 220 × 220 × 250 mm | Assumed; individual CAD-axis files fit this envelope |

The complete reference assembly remains 224 × 226.291 × 262.6 mm. Its 24 bodies include 13 proposed plastic pieces and 11 bought-component/display stand-ins. Aqua eyes are display placeholders. The fixed neck spans the cover seam and must be released to remove the covers. It is not a load-tested carrying handle; the tail and tie eyes are not lifting points.

## Verification

- All 13 saved STEP parts: one valid positive-volume solid, Z=0 datum and assumed bed fit.
- All 13 individual STLs: closed, consistently oriented mesh edges and mesh/native volume agreement within max(2 mm³, 0.1%).
- Assembly: 276 pairs across 24 bodies screened; 44 exact overlap queries, no overlap above 0.01 mm³. Moving wheel sweep and real cables are not certified.
- Branding: an exterior slice of each saved cover has ten separated PROMETHEUS glyphs or five KITTY glyphs. Native front, back and detail renders verify spelling, outward orientation and tail visibility.
- Keyed tail: saved gap probes to ±0.01 mm and six sampled rearward removal positions, screw absent, passed. Remove the cross screw, then pull rearward following the arrow.
- Print analysis: all 13 meshes are watertight single bodies with consistent scale. Ray-cast thickness samples and six-axis support-area candidates are recorded in `checks/printability-verified.json`; local thin details, supports, process and slicer settings still need review.
- Viewer: image-first, self-contained HTML; desktop/mobile, opt-in real WebGL and disabled/throwing graphics/JavaScript paths are checked in `checks/viewer-verified.json`.

Total native printed-solid volume is **532,319.009 mm³**, **4.16% below R2.1**. This is geometry, not measured mass, print time, load capacity or stability. The original R2.1 baseline commit and native volumes are retained in `checks/baseline-r2.1.json`.

## Rebuild

Use Python 3.12 and `requirements.txt`, then run from this folder:

```text
python build.py
python src/v7_tail_joint_review.py
python make_snapshots.py --out-dir SNAPSHOT_DIRECTORY
python record_evidence.py --snapshots SNAPSHOT_DIRECTORY
python make_review.py --snapshots SNAPSHOT_DIRECTORY --out-dir OUTPUT_DIRECTORY
python checks/review_browser.py --directory OUTPUT_DIRECTORY --browser-executable CHROMIUM_PATH
```

Cloud interpreter prefix: `CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python`. Snapshot generation accepts `--browser-executable /usr/bin/chromium`. Maintained STEP outputs come from the source models. Conforming STL files are exported from saved native OCCT geometry at 0.003 mm / 0.05 rad; the earlier browser mesh exporter produced nonmatching triangle edges, so this project retains the verified native exporter.

`record_evidence.py` binds the checked geometry and snapshots to source/font and STL hashes. Rerun it only after inspecting the current native snapshots. Ready-to-open copies are `review/index.html` and `review/saved-views.html`. The font is bundled with its license under `assets/`, so lettering does not depend on the viewer machine's fonts.
