# V7 mesh and print-orientation review

These measurements apply to the 13 separate body-part STLs in the V7 package. Each is one watertight body, has millimetre-consistent scale, and has a complete tool report. Native-solid validity, oriented mesh edges, volume agreement and assembly checks are recorded separately in GEOMETRY-VERIFICATION.json.

The actual printer, material, nozzle and layer height are unknown. The tool used the default 45-degree support threshold. FDM/FFF is a candidate process, not a confirmed print profile. No G-code or print job is included.

## Measured facts

Thickness is ray-cast surface sampling with a 2,000-sample request per part, not an exhaustive wall map. Minimum readings can include bevels, rims and raised details. Support area measures downward-facing mesh faces below 45 degrees, excluding faces on the plate; it is not support-material usage or a slicer result. Orientation candidates are the six axis rotations only.

| Part | Sampled min mm | Sampled p05 mm | Current support area mm² | Lowest-area axis candidate | Candidate support area mm² | Candidate height mm |
| --- | --- | --- | --- | --- | --- | --- |
| v7_base | 4.000 | 4.000 | 0.00 | current_plus_z | 0.00 | 4.00 |
| v7_cover_front | 1.647 | 2.327 | 8609.64 | flip_180_x | 809.43 | 100.00 |
| v7_cover_rear | 1.685 | 2.121 | 9337.39 | flip_180_x | 1274.40 | 100.00 |
| v7_motor_left | 2.000 | 2.000 | 48.00 | current_plus_z | 48.00 | 22.00 |
| v7_motor_right | 2.000 | 2.000 | 48.00 | current_plus_z | 48.00 | 22.00 |
| v7_battery_tray | 2.500 | 2.500 | 84.00 | current_plus_z | 84.00 | 27.00 |
| v7_electronics_deck | 3.000 | 3.000 | 4065.87 | flip_180_x | 0.00 | 26.00 |
| v7_caster_bridge | 4.000 | 4.000 | 1394.16 | rot_plus_90_x | 139.13 | 32.00 |
| v7_sensor_bracket | 3.000 | 3.000 | 81.62 | rot_plus_90_x | 16.28 | 14.00 |
| v7_neck | 1.128 | 3.710 | 941.98 | current_plus_z | 941.98 | 36.00 |
| v7_phone_cradle | 1.800 | 3.000 | 536.29 | current_plus_z | 536.29 | 14.80 |
| v7_phone_cap | 0.800 | 7.400 | 0.00 | current_plus_z | 0.00 | 11.40 |
| v7_tail | 4.300 | 10.814 | 149.67 | current_plus_z | 149.67 | 12.00 |

## Findings for print preparation

- Watertightness: all 13 meshes pass the mesh tool's check (`mesh.watertight`, `mesh.body_count`) and the independent closed, oriented-edge check.
- Sampled walls: every `wall_thickness.p05_mm` exceeds the default FDM supported/unsupported wall limits of 1.2/1.6 mm. Local sampled minima on the rear cover, neck and phone cap are thinner; inspect those exact `thinnest_samples` locations in the slicer. This is not an exhaustive minimum-wall or strength approval.
- Supports: the covers have large horizontal internal roofs in their supplied CAD orientation. Flipping them 180 degrees about X substantially reduces measured support area without changing their 100 mm build height. The electronics deck also benefits from this flip. The caster bridge and sensor bracket have lower-area 90-degree-X candidates. These are slicer-review candidates; the delivered STLs retain their documented CAD axes and Z=0 datum.
- Residual support needs remain on the shell details, neck and other parts. Confirm supports, first-layer contact, brim, fit tolerances and fastener holes in the selected slicer. Neither a zero-area reading nor a low support ratio proves a successful print.
- Hole diameter, minimum positive feature and maximum bridge are not measured by this tool. Small lettering, tail cue, joints and ear tips need slicer review. The saved CAD verifies the proposed hole/key geometry; printer-specific clearance still needs fit samples.

## Limits and alternate processes

The comparison limits come from `text-to-cad:dfam-check/references/process-limits.md`: FDM supported wall 1.2 mm, unsupported wall 1.6 mm, self-supporting angle 45 degrees. These are generic defaults; the printer/material datasheet takes precedence.

The sampled p05 thickness values also exceed that table's wall defaults for SLA/DLP, SLS and MJF, but these are not process approvals. SLA/DLP needs its own 30-degree support measurement; SLS/MJF need powder-escape review rather than these support-angle findings. No metal-print assessment was performed.

Measurement source: `text-to-cad:dfam-check/scripts/dfam_tool.py`, run on the exact current STL files. Individual JSON reports and six-axis orientation candidates are in `dfam/`; summary.json binds the measurements to STL SHA-256 hashes. Runtime packages: trimesh, numpy, rtree, scipy, networkx and lxml. No model rescaling was performed.
