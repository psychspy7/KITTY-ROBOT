---
date: 2026-10-23
topic: kitty-v3-final-detail
focus: One final distinctive and useful refinement to the liked V3 mechanical body
mode: repo-grounded
---

# Ideation: KITTY V3 final detail

## Grounding Context

The current 13-part V3 retains the 166 × 160 mm chassis family, fixed 36 mm neck, landscape phone, passive ears and detachable tail. The user's reported phone 164 × 76 × 8 mm, wheel diameter 62 mm and BO motor 61 × 20 mm remain fixed inputs. Other bought-part fits and print settings are unresolved. The latest request delegates a final creative addition, after approving the direction of V3.

Basis snapshot: commit `89db3e9af807d13ce3574894799ef4f54c0ed62b` (line references below identify that pre-refinement revision). Current source: `design/v3/src/shapes.py`, `design/v3/README.md`, `design/v3/DESIGN-NOTES.md`. There is no institutional learning corpus under `docs/solutions`; dedicated web-search/fetch tools were unavailable, so no external evidence or novelty comparison is claimed. Twenty-one raw ideas were merged into six candidates. Each merged candidate received a fresh-context basis check. All direct bases were checked through line-cited dossiers and targeted reads; reasoned concepts remain proposed rather than measured effects. The two-frame generator had the same total read budget as the single-frame generators, so per-idea verification depth was unequal.

---

## Topic Axes

- Character and visual identity.
- Human handling, assembly and service.
- Print and verification burden.

---

## Ranked Ideas

### 1. Folded Sentinel collar

**Description:** Carry the ear/box-corner facet language into a broad, shallow folded V on the chest and a restrained cuff on the fixed neck. Integrate two generic rear tie eyes into that neck to help route loose phone wiring; actual cable and tie fit remain to be checked. The object should read as one character even when the phone screen is dark.

**Axis:** Character and visual identity.

**Basis:** `direct:` `design/v3/src/shapes.py:93` says the existing raised V follows the sloping chest without thinning the shell; `design/v3/DESIGN-NOTES.md:3` describes the warm faceted body, dark chassis and curled tail. The cap already has triangular insets at `design/v3/src/shapes.py:259`. `reasoned:` repeating one folded shape across existing parts gives visual coherence; providing a generic tie path can help keep loose wires together without claiming an exact connector mount.

**Rationale:** It changes the visible character while using the current parts and hardware envelope. The rear tie detail gives the new collar a practical purpose.

**Downsides:** Extra local print volume and overhang review; cuff strength and actual ties/cables are untested. It does not establish a load-bearing handle.

**Confidence:** 88% for appearance/feasibility as a CAD draft, not physical performance.

**Complexity:** Low.

### 2. Tail service cue

**Description:** Add a small raised arrow on the screw-entry side of the existing tail socket, pointing rearward. It directs the removal gesture after the screw is removed and shares the same angular language as the collar.

**Axis:** Human handling, assembly and service.

**Basis:** `direct:` `design/v3/README.md:88` specifies screw entry from the left, nut from the right and straight rearward removal. `design/v3/src/shapes.py:105` explains the anti-inversion key. The witness-marker family survived the basis check; a simple arrow is the smaller refinement, because the current stepped surfaces are not coplanar for a continuous split-chevron mark.

**Rationale:** It makes an unusual joint easier to understand without altering its key, bore or proposed retention hardware.

**Downsides:** Small relief must be inspected in the selected slicer. An arrow cannot confirm screw retention or physical seating.

**Confidence:** 92% for a readable CAD cue.

**Complexity:** Low.

### 3. First-print tail dock

**Description:** Derive a freestanding test socket from the real keyway and cross-bore. After fit evaluation, it could store the detached tail during maintenance.

**Axis:** Print and verification burden.

**Basis:** `direct:` `design/v3/README.md:35` records a 0.4 mm proposed per-side clearance with a print sample pending; `design/v3/README.md:85` requires small fit samples before a whole-body print. The shared key/socket factories support matched geometry.

**Rationale:** A useful fit sample can reduce the cost of discovering a printer-specific clearance problem.

**Downsides:** Adds an optional accessory and its own stability/print checks. Physical validation is still needed. It is a later print-preparation option rather than a body appearance requirement.

**Confidence:** 84% as a later draft accessory.

**Complexity:** Medium.

### 4. Key profile as visual alphabet

**Description:** Repeat the one-clipped-corner key profile in a few shallow surface details.

**Axis:** Print and verification burden.

**Basis:** `direct:` `design/v3/src/shapes.py:102–107` constructs the asymmetric key. `reasoned:` a shared local section can make visual and fit samples easier to interpret.

**Rationale:** It gives decoration a mechanical source rather than introducing unrelated motifs.

**Downsides:** It largely overlaps the folded collar and may introduce unnecessary asymmetry into the feline front. It is a variant, not an additional feature to stack on top.

**Confidence:** 77%.

**Complexity:** Low.

---

## Rejection Summary

| Candidate or group | Disposition and reason |
| --- | --- |
| Chassis-supported neck / independent shells | Deferred: documented service benefit, but a new structural bridge would require load-path and interior-fit work beyond the requested final refinement; basis verifier rated the proposed solution weak. |
| Finger saddles / carrying coves | Rejected: the shell/cover fasteners have no carrying-load evidence, and the feature would invite an unverified handling action; basis verifier rated it weak. |
| Screen-independent chest posture and negative-space expression | Merged into the folded collar; one coherent torso gesture is stronger than competing marks. |
| Shared clipped silhouette / one-fold motif | Merged into the collar candidate; already partly present in V3. |
| Seam compass, screw-side cue and aircraft witness | Reduced to the tail arrow; underside/seam marks and a split witness introduce more details without resolving service access itself. |
| Composed rear maintenance elevation / finished empty dock | Existing bevelled socket and rounded service openings already address much of this; retained only where the tail cue adds information. |
| Multi-interface proof plate and feature portrait | Merged into the future fit-dock idea; full actual-parts intake should determine which other interfaces need sampling. |
| Optional fit-dock now | Deferred to print preparation; it does not improve the requested visible body and must not enlarge the required 13-piece body set. |
| Repeated asymmetric motifs now | Variant deferred; the collar already supplies the common shape language. |

All 21 raw ideas are represented by these merged groups. Four candidates have sound conceptual bases; two were weak. Only the collar and tail cue form the selected final body treatment. No externally validated uniqueness or physically verified result is implied.
