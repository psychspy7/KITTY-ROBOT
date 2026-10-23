# Three-minute presentation — Team Prometheus

**0:00–0:25 — The problem.** “We’re building a practical physical AI assistant. Today we'll demonstrate the robot's decision-making software before we attach the real chassis.”

**0:25–1:10 — Navigation.** On the laptop, choose Presentation zone → Navigate. Point to the planned path, steering direction and obstacle map. “This is a digital twin; its path planner knows this test arena, which real hardware would need to learn or measure.”

**1:10–1:40 — Surprise obstacle.** Choose Add obstacle and place a virtual box across the route. Demonstrate immediate path replanning; point to the safety/event logs.

**1:40–2:10 — Chat + personality.** Say “What do you see?” Then “Who made you?” Explain that voice commands use deterministic parsing and the optional language model generates conversation, not motor commands.

**2:10–2:35 — Safety.** Press Emergency Stop and show that navigation is rejected. Press Release to re-arm; it remains stationary until a new command.

**2:35–3:00 — Next milestone.** “We're replacing virtual sensors and wheels with an ESP32, motor controller and real sensor feedback. We will not claim real autonomous navigation until it is physically tested.”

## Backup strategy

- Local demonstration works without cloud AI.
- If the Wi-Fi/network/model fails, movement and safety simulation still work.
- Save a screen recording in advance in case the presentation laptop fails.
- Never present simulated sensor readings as live hardware measurements.
