# Simulator R1H1 — consolidation changes, 23 October 2026

This is a laptop simulation only. No motors, camera or hardware adapter were added.

1. Fixed command precedence: a complete explicit `reset emergency stop` / `release emergency stop` phrase is recognized before the generic emergency-stop phrase. Unrelated text containing that phrase cannot reset the simulator stop. Three regression tests accompany this fix.
2. Default HTTP port is now OS-selected (`ROBOT_PORT=0`), and the console/browser receive the actual selected port. A fixed port is still possible with `ROBOT_PORT`. This avoids relying on port 8765 being free/allowed on this laptop.
3. Health endpoint labels this copy R1H1. The unchanged UI still says R1.0.

Run: `python main.py` (or the supplied Windows launcher). Read the URL printed in the terminal, rather than assuming 8765. Baseline needs only Python 3.10+ standard library. Run tests: `python -m unittest discover -s tests -v`.

The upstream README and optional AI launchers are preserved for context; model names are examples, not freshly verified availability/performance. Neither external AI nor microphone/camera was exercised in this review. Do not configure credentials just to run the simulator.

Original `brain.py` and `main.py` are preserved at `../../90_REFERENCE_ONLY/Original-Software/`. All other imported simulator source bytes are preserved. No Git history or firmware was changed.
