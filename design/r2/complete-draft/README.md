# KITTY Sentinel R2 — complete draft CAD

This project creates the whole proposed R2 mechanical assembly. It uses the user's phone dimensions **164 × 76 × 8 mm**, **62 mm** wheel diameter and **61 × 20 mm** BO motor length/width. These are user-reported dimensions; case inclusion is unconfirmed. All other bought-part interfaces are labelled assumptions in `parameters.json`.

The complete draft is **224 × 239.599 × 281.6 mm** with the tail installed in the saved assembly. The proposed printed chassis is 166 × 160 mm. The assumed printer volume is 220 × 220 × 250 mm; each individual part fits those bounds. No actual printer, physical fit, material strength, stability or print settings have been verified.

## R2.1 changes for design review

The user chose to keep the current body and add a detachable rear tail with small refinements. The body and reported component envelopes are retained. A curved flat-print tail now fits a socket integrated into the rear cover, above the lower service openings. The passive ears have bevelled tips and recessed details; the lower phone bezel has two shallow accent grooves. These appearance changes are awaiting user review; the final print set is not released.

## Files and quantities

| STL stem | Quantity | Purpose |
| --- | --- | --- |
| r2_base | 1 | Chassis plate; shared fastening patterns, caster passage and strap slots |
| r2_cover_front | 1 | Faceted front body half with sensor opening |
| r2_cover_rear | 1 | Removable rear body half with ventilation, service openings and an integral keyed tail socket |
| r2_motor_left / r2_motor_right | 1 each | BO motor channels with shaft windows and tie slots |
| r2_battery_tray | 1 | Low holder tray and strap paths; AA configuration still unselected |
| r2_electronics_deck | 1 | Raised deck with universal tie slots; no claimed exact PCB pattern |
| r2_caster_bridge | 1 | Raised caster support through the chassis; actual caster mounting pending |
| r2_sensor_bracket | 1 | Front transducer face and chassis foot; actual PCB retention pending |
| r2_neck | 1 | Fixed broad neck, cable passage and head-fastening holes; no SG90 phone load |
| r2_phone_cradle | 1 | Landscape frame with retention lips, rear opening, side access and neck fasteners |
| r2_phone_cap | 1 | Removable top retainer with bevelled passive ears and recessed inner details |
| r2_tail | 1 | Curved detachable tail; asymmetric key and cross-screw bore |

`r2_printed_assembly.stl` places all 13 printed pieces in their assembled positions. **It is a view-only multi-part assembly, not one fused object to slice.** Use individual part files for manufacturing review.

`r2_complete_draft.stl` adds generic envelopes for the wheels, motors, phone, holder, caster, sonar cans and display graphics. **It is a whole-robot preview, not a manufacturing STL.** Those stand-ins do not represent exact purchased-part CAD and must not be printed as replacement hardware. The supplier-catalog lookup was blocked by HTTPS proxy policy; no exact catalog match is claimed.

## Rebuild

Use a separate Python 3.12 environment with `requirements.txt`, or the existing KITTY CAD venv. From this directory:

```text
python build.py
```

This builds the parameterless STEP model entrypoints through cadgen, exports STL directly from the saved native OCCT geometry using build123d (`0.003 mm` linear and `0.05 rad` angular tolerance), and runs `checks/verify_exports.py`. The direct mesh path is intentional: the browser mesh exporter produced nonmatching triangle edges on some coplanar loops. The retained OCCT export passes the closed, consistently oriented edge checks. The finer sampling keeps curved-tail mesh volume within the existing native/mesh tolerance. Running a single `src/r2_*.py` builds its STEP only; `build.py` is the complete export command.

For this cloud instance, use `CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 /workspace/.kitty-cad-env/bin/python build.py`. No global package or home-directory cache changes are needed.

The checks inspect saved files: one valid positive-volume solid per printed part, flat Z=0 datum, stated bounds, assumed bed fit, closed oriented mesh edges, native/mesh volume agreement within max(2 mm³, 0.1%), selected bores/passages, and static interference across all 24 bodies. The 276 pairs are screened by conservative bounds; candidates receive exact intersection-volume checks with a 0.01 mm³ threshold. The saved tail root/socket gap is probed to 0.01 mm and removal is checked at 0, 6, 12, 18, 24 and 35 mm rearward, with the screw absent. General moving clearances and actual load capacity are separate physical checks.

`python make_preview.py` creates an offline HTML viewer in `tmp/` from the built STLs. `--snapshots DIRECTORY` optionally embeds matching CAD snapshots named after each part; the assembly image names are `assembly-iso.png` and `printed-assembly.png`. `--out FILE` selects the HTML destination. The delivered viewer includes snapshots, full-robot and printed-only assemblies, individual part selection and exact STL downloads. It needs no network libraries.

For design approval, prefer `python make_review.py --snapshots DIRECTORY --out-dir DIRECTORY`. This produces `KITTY-R2-REVIEW.html` and a smaller `KITTY-R2-SAVED-VIEWS.html`. Both show six coloured saved CAD views immediately, with native HTML/CSS view controls that work when JavaScript is disabled. The main review adds rotatable 3D only after clicking its button; a failed graphics context leaves the saved view visible. Open a downloaded HTML file in Chrome or Edge. These files review the R2.1 tail revision; they do not approve fit, regenerate geometry or send a print.

## Assembly and print preparation

1. Confirm the remaining dimensions before choosing a print release. Print critical interface samples after printer/material/tolerance choices are known; whole-shell geometry validity is not fit approval.
2. Review each of the 13 part STLs individually. Flat frames and the base can be reviewed back-face down; shell bosses, ledges and retaining lips need support/orientation review in the selected slicer. No G-code or printer job is included. Full wall-thickness/overhang sampling and a slicer review have not been performed.
3. Fit the caster support, motor channels, battery tray, sensor bracket and electronics deck to the chassis. Check actual motor shafts, hubs, ground contact, cable bends and restraint before enclosing anything. Purchased caster, padding, straps, M3 fasteners/nuts and their lengths are not confirmed as owned; the nominal 3.4 mm clearance bores and 6.6 mm corner-diameter nut recesses still need fit samples.
4. Assemble the two cover halves around the interior, then attach the neck and head. The neck flange spans the cover seam; servicing a cover requires releasing the neck fasteners. Base-to-cover screws enter from below, with their nut pockets accessible from the open interior.
5. Fit the detachable tail into the rear socket and retain it with the proposed M3 cross screw and hex nut. Remove that screw and pull rearward to detach. The 12 mm keyed root has 0.4 mm proposed clearance per side. Hardware sizing, strength and a printed fit sample remain unverified; the tail is decorative, not a handle. `r2_tail_joint_review.step` is a view-only exploded pair, displaced 35 mm to explain this connection. Build it separately with `python src/r2_tail_joint_review.py`.
6. Fit and pad the phone, then secure the removable top retainer. Confirm retention and button/USB access on the real case. Neck/head fasteners must remain recessed clear of the phone.
7. Verify the actual forward-facing camera view. With the display facing forward, the rear camera points backward; select and test the intended camera. Openings in this draft do not establish unobstructed coverage on an unknown A57 variant.

The rear openings reserve service access, not a fitted or electrically rated cutoff installation. AA chemistry/cell count/current capability, holder, fuse, regulator and actual switch remain electrical decisions. Sensor retention, real cable routing, phone load, wheel clearance throughout motion, chassis mass distribution and stability need physical verification.

No print was sent, purchase made, hardware energized or fit approval inferred by creating these files. The R2 reference remains the aesthetic direction; final appearance and fit need the user's review before printing.
