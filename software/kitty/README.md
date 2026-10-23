# KITTY face and guarded mission preview

Run from this directory with Python 3.10+; standard library only:

```text
python main.py
```

On Windows use `py -3 main.py`. Use the printed local address. Append `/face` for the responsive face-only layout. The server binds to loopback; this does not make it reachable from the physical phone. Phone streaming and a reviewed display/network arrangement remain separate integration work.

## What works

- Animated amber eyes: idle blink, happy, focused, listening, thinking, speaking, sleeping, and fault/stop alert. Expression auditions affect appearance only. Reduced-motion preferences are respected.
- Offline KITTY replies and optional browser speech synthesis. No paid API, model weights or open-ended language model is configured. The original personality prompt remains in `prompts/kitty-personality.txt`; this offline responder is a small deterministic subset, not a trained or integrated model.
- Deterministic controller preview with bounded SI-unit commands, frame/heartbeat expiry, sequence checks, range/target validity, latched faults and emergency stop, explicit rearming, and separate target-range/obstacle-range handling.
- Explicit developer fixtures for centered/offset target, obstacle, arrival and target loss. Inputs are labelled fixtures, not camera or sensor measurements.

## Try it

1. Choose Target centered and Run fixture: preview becomes APPROACHING.
2. Pause feed: it enters FAULT after expiry. Resume feed supplies new data but does not rearm. Use Rearm preview explicitly.
3. Try left/right and obstacle fixtures. An obstacle revokes the preview command.
4. Emergency Stop stays latched through new fixtures. Reset stop leaves it disarmed; run a fixture again deliberately.
5. Audition face expressions. Fault and stop always override an audition. Chat text never arms or moves the preview.

All states report `hardware_enabled: false` and `transport: not_implemented`. There is no serial, Wi-Fi motor adapter, hardware-enable endpoint, ESP32 firmware or camera ingestion in this app. GUI stop tests do not prove physical stopping. The original `software/simulator` remains separate and unchanged.

## Integration contract

`Observation` uses receiver-process monotonic timestamps (seconds), metres, a strictly increasing frame sequence, normalized horizontal target center (-1 left, +1 right), confidence and explicit provenance. A future camera receiver must normalize capture timestamps into that clock, track capture/receive age and target validity, and supply real data; merely passing a fixture is not perception. A future hardware adapter needs independently reviewed protocol/firmware, freshness/acknowledgement, local expiry and physical cutoff, not a connection from arbitrary chat text or simulated map pixels.

Current preview thresholds (0.12 m/s maximum forward, 0.5 rad/s angular, 300 ms freshness, 0.25 m front stop, 0.45 m target arrival) are uncalibrated development values. They are not approved for physical use. Sonar front range alone never establishes target arrival or all-direction clearance. Language processing never runs on the preview stop path.

## Checks

```text
python -B -m unittest discover -s tests -v
```

HTTP tests use an OS-assigned loopback port and real requests. They do not operate devices. Run the original simulator tests separately in their own working directory. Hardware intake: `docs/BENCH-START.md`. CAD parameters and draft export tools: `design/r2/cad/`.
