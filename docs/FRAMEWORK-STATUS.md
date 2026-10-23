# KITTY framework verification — 23 October 2026

The separate face/mission workbench runs from `software/kitty` with Python 3.10+ and the standard library. It includes animated expressions, optional browser speech, deterministic offline conversation, labelled observation fixtures and a disarmed mission controller. No live camera, model inference, motor transport or device firmware is implemented. Fixture speeds/distances and watchdog settings are developer values, not calibrated physical limits.

Run `py -3 main.py` from that directory on Windows and open the address it prints on the same computer. Use `python3 main.py` on Linux. The server binds only to loopback; it does not currently serve the OPPO over a LAN. The `/face` layout is prepared for later display integration.

Verification in the cloud instance:

- Original simulator: 10 tests passed.
- KITTY brain and real HTTP integration: 14 tests passed, including stale frames/heartbeat, stop latching, explicit rearm, malformed JSON and foreign-Origin rejection.
- CAD measurement intake: 7 tests passed. Synthetic measured test data are clearly labelled test fixtures, not physical evidence.
- Browser: desktop 1440×1000 and mobile 390×844; no JavaScript errors or horizontal overflow; fixture controls, stale-feed fault, rearm, stop/reset and face-only layout exercised.
- Four illustrative STEP/STL exports: one valid solid each, expected dimensions, selected through-hole volumes, closed STL edges, positive mesh volume and STEP/mesh volume agreement checked. All four CAD snapshots were visually inspected.
- Compound Engineering code review completed. Finding #1 (sonar spacing omitted fit clearance) was fixed after a failing regression reproduced it; below/equal/above-boundary tests pass for example and synthetic measured input. No actionable findings remain unresolved.

The CAD source in `design/r2/cad` is a framework. `draft_base`, `draft_phone_cradle`, `draft_motor_coupon` and `draft_sensor_coupon` use example dimensions. These are not the fitted R2 shell, full mounting system or print-approved parts. The measured-input export remains blocked by null physical dimensions. It still needs motor/shaft/wheel/caster geometry, actual phone/case/camera/port positions, final AA holder and power components, board footprints, fasteners, printer constraints, fit checks and appearance approval.

Start the physical intake with [BENCH-START.md](BENCH-START.md). No powered robot test or flash was performed. The next evidence is actual board/meter/supply identification, motor ratings and measured interfaces. A temporary HW battery and an unspecified AA pack cannot yet establish a compatible motor supply.

Generated draft exports and review images are packaged separately with a committed source snapshot and SHA-256 manifest. Private handoff evidence, credentials, virtual environments and unrelated local tooling changes are excluded.
