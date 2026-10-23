# Robot Mind — System Architecture

```text
                    [Laptop browser]
                   map + chat + voice
                          |
                     localhost HTTP
                          |
       +------------------+--------------------+
       |                  |                    |
 [Command Parser]  [Mind Personality]   [Simulation World]
       |                  |                    |
       |             Local rules OR        Digital arena:
       |             Ollama/OpenAI         map, raycasting
       |                  |                    |
       +----> [Validated Command Layer] <------+ 
                          |
                 [Safety Supervisor]
                  - E-stop latch
                  - motion timeout
                  - collision check
                          |
                   [Navigation Planner]
                       A* grid
                          |
                   [Virtual Motors]
                          |
                  Position update + log
```

## Design rules

1. Commands are recognized by deterministic patterns and validated by the controller, **not generated as runnable code by an LLM**.
2. A chat model may describe plans but cannot send drive commands. This remains true if online AI is enabled.
3. Stop works independently of LLM network latency. A persistent emergency-stop state prevents all simulated motion until explicit reset.
4. Map-aware A* navigation is a simulator convenience. Physical-world obstacle avoidance will need measured sensor data and possibly encoders, odometry, mapping, localization, and route replanning.
5. An added obstacle triggers immediate replanning; all movement steps are independently checked for collisions.
6. Chat memory is ephemeral: the most recent conversation exchanges are held in process RAM and lost when the server closes. There is no database.

## Main state machine

- `IDLE` — stationary, accepting commands.
- `NAVIGATING` — route tracking with heading alignment and collision checks.
- `MANUAL_FORWARD`, `MANUAL_BACKWARD`, `MANUAL_LEFT`, `MANUAL_RIGHT` — 1-second bounded commands.
- `ARRIVED` — target reached.
- `BLOCKED` — planner couldn't find path or collision envelope triggered.
- `STOPPED` — emergency-stop latch set, safety state `EMERGENCY STOP`.

## Local API

- `GET /api/state` — current position, simulated sensor readings, path, obstacles, event log and safety state.
- `GET /api/health` — server health.
- `POST /api/action` — JSON `{"action":"go_to_zone","zone":"lab"}` or `{"action":"go_to","x":750,"y":430}`; supports `forward`, `backward`, `left`, `right`, `stop`, `estop`, `reset_estop`, `add_obstacle`, `clear_obstacles`, `reset_world`.
- `POST /api/chat` — JSON `{"text":"Go to the lab"}`. Returns `reply` and state. Commands are parsed before conversation model.

The server is for trusted local demonstration only; don't expose it on the Internet or use it directly as your physical robot network API without authentication and additional safeguards.
