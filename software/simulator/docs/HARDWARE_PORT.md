# Physical integration status

This simulator does not contain a working hardware adapter, ESP32 firmware, phone camera/audio bridge, or motor transport. The browser command demo and Python simulator remain software-only. Do not connect motors or flash a board from this sketch.

The team's reported parts and unresolved variants are listed in [`../../../docs/ACTUAL-PARTS-REPORTED.md`](../../../docs/ACTUAL-PARTS-REPORTED.md). The current conceptual signal and power boundaries are in [`../../../docs/CIRCUIT-AND-SYSTEM.md`](../../../docs/CIRCUIT-AND-SYSTEM.md). That document is not wiring-ready and intentionally assigns no pins or component values.

Before adding a physical adapter, confirm the exact ESP32, TB6612 board, sensor modules/counts, motors, battery, protection, regulator, and wiring. Measure logic levels and motor current. Add one reviewed schematic, a matching GPIO/config table, a bounded host/controller message contract, and local timeout/STOP handling. Keep the adapter separate from simulation and disabled by default. An AI-generated string or virtual map pixel must never become a motor command directly.

