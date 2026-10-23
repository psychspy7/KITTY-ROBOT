# V7 service revision — measured print review

The exact 13 body STLs and four separate fit-sample STLs were measured. Each is one watertight body with millimetre-consistent scale and a complete report. Native validity, oriented mesh edges, mesh/native volume agreement, adjustment positions, branding, tail gaps and sample dimensions have separate checks.

Actual printer, material, nozzle, layer height and tolerance are unconfirmed. Measurements use the default 45-degree support threshold, with conditional FDM comparison. PETG is a quote option; no slicing or print job has been performed.

## Facts

Thickness is deterministic ray-cast surface sampling, with a request of 2,000 samples per file, not an exhaustive wall audit. Small minima can occur on bevels, reliefs and label edges. Down-facing area below 45 degrees excludes build-plate faces and is not slicer support usage. Six-axis candidates report geometric area and height only.

| Part | Sampled min mm | Sampled p05 mm | Current support area mm² | Lowest-area axis candidate | Candidate support area mm² | Candidate height mm |
| --- | --- | --- | --- | --- | --- | --- |
| v7_base | 4.000 | 4.000 | 0.00 | current_plus_z | 0.00 | 4.00 |
| v7_cover_front | 1.693 | 2.170 | 8609.64 | flip_180_x | 809.43 | 99.75 |
| v7_cover_rear | 1.563 | 2.121 | 9337.39 | flip_180_x | 1274.40 | 99.75 |
| v7_motor_left | 2.000 | 2.000 | 48.00 | current_plus_z | 48.00 | 24.00 |
| v7_motor_right | 2.000 | 2.000 | 48.00 | current_plus_z | 48.00 | 24.00 |
| v7_battery_tray | 2.500 | 2.500 | 84.00 | current_plus_z | 84.00 | 27.00 |
| v7_electronics_deck | 3.000 | 3.000 | 4065.87 | flip_180_x | 0.00 | 26.00 |
| v7_caster_bridge | 4.000 | 4.000 | 1394.16 | rot_plus_90_x | 139.13 | 32.00 |
| v7_sensor_bracket | 3.000 | 3.000 | 81.62 | rot_plus_90_x | 16.28 | 14.00 |
| v7_neck | 1.128 | 3.710 | 941.98 | current_plus_z | 941.98 | 36.00 |
| v7_phone_cradle | 1.800 | 3.000 | 536.29 | current_plus_z | 536.29 | 14.80 |
| v7_phone_cap | 0.800 | 7.400 | 0.00 | current_plus_z | 0.00 | 11.40 |
| v7_tail | 4.300 | 10.814 | 149.67 | current_plus_z | 149.67 | 12.00 |
| v7_fit_tail_socket | 0.125 | 3.500 | 755.24 | rot_plus_90_x | 15.37 | 24.00 |
| v7_fit_tail_key | 4.000 | 12.000 | 0.00 | current_plus_z | 0.00 | 12.00 |
| v7_fit_phone_thickness | 3.000 | 3.000 | 0.00 | current_plus_z | 0.00 | 4.00 |
| v7_fit_screws | 0.108 | 4.000 | 0.00 | current_plus_z | 0.00 | 4.00 |

## Findings and limits

- All 17 meshes pass measured watertightness and single-body checks. Scale flags are clear. Independent closed-oriented-edge and positive native-solid/volume checks also pass.
- Every sampled p05 thickness exceeds 1.6 mm, satisfying the default FDM supported/unsupported wall comparisons of 1.2/1.6 mm for that sampled statistic. Local minima below those numbers remain on the rear shell, neck, cap and engraved samples; inspect the exact `wall_thickness.thinnest_samples` coordinates. The very small sample minima are not a claimed whole-wall thickness. No exhaustive wall or load-strength approval follows.
- Covers need internal-roof support review; their 180-degree-X candidates substantially reduce measured area. The electronics deck also benefits from inversion. The caster and sensor bracket have useful 90-degree-X candidates. The sample socket has horizontal keyways and the sample key lies flat: match their orientations and support strategy to the production socket and tail before treating the fit result as transferable.
- Font/positive-feature width, hole diameter and unsupported span are not measured by this tool. Native checks verify the proposed bores/slots/key clearances, but the service must inspect fine labels, letters, overhangs and fit in its actual slicer. Suggested material, layer height and infill are not tested printer parameters.
- Sample key insertion is checked in all three saved keyways at 0/10/22 mm withdrawal. The two motor groups are sampled at -2/0/+2 mm; those checks are not a continuous swept analysis or physical shaft/hub proof.
- Coupon results are unknown until printed. If 0.4 mm tail clearance or 3.4 mm holes do not fit, update the relevant CAD parameter and regenerate the affected piece; do not scale the entire robot or silently repair the mesh.

Limits source: `text-to-cad:dfam-check/references/process-limits.md`, FDM supported wall 1.2 mm, unsupported wall 1.6 mm, self-supporting angle 45 degrees. A service datasheet/profile supersedes those generic defaults. The sampled p05 values exceed the table's wall defaults for SLA/DLP, SLS and MJF too, but those are not approvals: SLA/DLP needs its own 30-degree support measurements, and powder processes need powder-escape review. No metal process is assessed.

Tool: `text-to-cad:dfam-check/scripts/dfam_tool.py`; runtime dependencies trimesh, numpy, rtree, scipy, networkx and lxml. JSON facts include exact input hashes. Individual measure/orientation reports are in dfam/. No rescaling was performed. Start with PRINT-SERVICE-BRIEF.md.
