# Room-check simulator

An interactive, dependency-free browser demonstration of the current supported-command software fixture. Open `index.html`; enter **KITTY, check the room**; run, pause, resume, reset, or stop the task. Optional buzzer audio begins only after a user action.

The fixture has a supplied static map, simulated front/rear range and IR readings, a bounded command parser, a route planner, and a software safety check. The warning state stops virtual motion and beeps before route planning. The planner uses the supplied map; this is not camera perception, SLAM, open-ended AI, a physical sensor test, or a hardware control bridge. `STOP` halts only the simulator.

No external libraries, network calls, model weights, microphone access, or API keys are used.

## Run the checks

From the repository root:

```bash
node software/room-check-demo/test-command.cjs
```

