# KITTY Sentinel R2 — complete draft CAD

This project creates the whole proposed R2 mechanical assembly, rather than the earlier four interface coupons. It uses the user's phone dimensions **164 × 76 × 8 mm**, **62 mm** wheel diameter and **61 × 20 mm** BO motor length/width. These are user-reported dimensions; case inclusion is unconfirmed. All other bought-part interfaces are labelled assumptions in `parameters.json`.

The complete draft is **224 × 171 × 280.6 mm** in the saved assembly. The proposed printed chassis is 166 × 160 mm. The assumed printer volume is 220 × 220 × 250 mm; each individual part fits those bounds. No actual printer, physical fit, material strength, stability or print settings have been verified.

## Files and quantities

| STL stem | Quantity | Purpose |
| --- | --- | --- |
| r2_base | 1 | Chassis plate; shared fastening patterns, caster passage and strap slots |
| r2_cover_front | 1 | Faceted front body half with sensor opening |
| r2_cover_rear | 1 | Removable rear body half with ventilation and service openings |
| r2_motor_left / r2_motor_right | 1 each | BO motor channels with shaft windows and tie slots |
| r2_battery_tray | 1 | Low holder tray and strap paths; AA configuration still unselected |
| r2_electronics_deck | 1 | Raised deck with universal tie slots; no claimed exact PCB pattern |
| r2_caster_bridge | 1 | Raised caster support through the chassis; actual caster mounting pending |
| r2_sensor_bracket | 1 | Front transducer face and chassis foot; actual PCB retention pending |
| r2_neck | 1 | Fixed broad neck, cable passage and head-fastening holes; no SG90 phone load |
| r2_phone_cradle | 1 | Landscape frame with retention lips, rear opening, side access and neck fasteners |
| r2_phone_cap | 1 | Removable top retainer with passive cat corners |

`r2_printed_assembly.stl` places all 12 printed pieces in their assembled positions. **It is a view-only multi-part assembly, not one fused object to slice.** Use individual part files for manufacturing review.

`r2_complete_draft.stl` adds generic envelopes for the wheels, motors, phone, holder, caster, sonar cans and display graphics. **It is a whole-robot preview, not a manufacturing STL.** Those stand-ins do not represent exact purchased-part CAD and must not be printed as replacement hardware. The supplier-catalog lookup was blocked by HTTPS proxy policy; no exact catalog match is claimed.

## Rebuild

Use a separate Python 3.12 environment with `requirements.txt`, or the existing KITTY CAD venv. From this directory:

```text
python build.py
```

This builds the parameterless STEP model entrypoints through cadgen, exports STL directly from the saved native OCCT geometry using build123d (`0.01 mm` linear and `0.1 rad` angular tolerance), and runs `checks/verify_exports.py`. The direct mesh path is intentional: the browser mesh exporter produced nonmatching triangle edges on some coplanar loops. The retained OCCT export passes the unchanged closed, consistently oriented edge checks. Running a single `src/r2_*.py` builds its STEP only; `build.py` is the complete export command.

For this cloud instance, use `CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python build.py`. No global package or home-directory cache changes are needed.

The checks inspect saved files: one valid positive-volume solid per printed part, flat Z=0 datum, stated bounds, assumed bed fit, closed oriented mesh edges, native/mesh volume agreement within max(2 mm³, 0.1%), selected bores/passages, and static interference across all 23 bodies. The 253 pairs are screened by conservative bounds; candidates receive exact intersection-volume checks with a 0.01 mm³ threshold. Moving clearances and actual load capacity are separate physical checks.

`python make_preview.py` creates an offline HTML viewer in `tmp/` from the built STLs. `--snapshots DIRECTORY` optionally embeds matching CAD snapshots named after each part; the assembly image names are `assembly-iso.png` and `printed-assembly.png`. `--out FILE` selects the HTML destination. The delivered viewer includes snapshots, full-robot and printed-only assemblies, individual part selection and exact STL downloads. It needs no network libraries.

## Assembly and print preparation

1. Confirm the remaining dimensions before choosing a print release. Print critical interface samples after printer/material/tolerance choices are known; whole-shell geometry validity is not fit approval.
2. Review each of the 12 part STLs individually. Flat frames and the base can be reviewed back-face down; shell bosses, ledges and retaining lips need support/orientation review in the selected slicer. No G-code or printer job is included. Full wall-thickness/overhang sampling and a slicer review have not been performed.
3. Fit the caster support, motor channels, battery tray, sensor bracket and electronics deck to the chassis. Check actual motor shafts, hubs, ground contact, cable bends and restraint before enclosing anything. Purchased caster, padding, straps, M3 fasteners/nuts and their lengths are not confirmed as owned; the nominal 3.4 mm clearance bores and 6.6 mm corner-diameter nut recesses still need fit samples.
4. Assemble the two cover halves around the interior, then attach the neck and head. The neck flange spans the cover seam; servicing a cover requires releasing the neck fasteners. Base-to-cover screws enter from below, with their nut pockets accessible from the open interior.
5. Fit and pad the phone, then secure the removable top retainer. Confirm retention and button/USB access on the real case. Neck/head fasteners must remain recessed clear of the phone.
6. Verify the actual forward-facing camera view. With the display facing forward, the rear camera points backward; select and test the intended camera. Openings in this draft do not establish unobstructed coverage on an unknown A57 variant.

The rear openings reserve service access, not a fitted or electrically rated cutoff installation. AA chemistry/cell count/current capability, holder, fuse, regulator and actual switch remain electrical decisions. Sensor retention, real cable routing, phone load, wheel clearance throughout motion, chassis mass distribution and stability need physical verification.

No print was sent, purchase made, hardware energized or fit approval inferred by creating these files. The R2 reference remains the aesthetic direction; final appearance and fit need the user's review before printing.
