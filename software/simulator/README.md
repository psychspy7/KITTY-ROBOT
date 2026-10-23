# TEAM PROMETHEUS — ROBOT MIND R1

**A working laptop-first software prototype for the KITTY CORP / Team Prometheus hackathon robot.**

The browser dashboard communicates with a local Python robot controller. No real motors, cameras, or ESP32 are required for the first test. No installation packages are required to run the standard version.

## FIRST RUN (Windows)

1. Extract the entire ZIP to a folder. Do **not** run directly inside the ZIP.
2. Install **Python 3.10 or newer** from https://www.python.org/downloads/ if necessary. On Windows, enable **Add Python to PATH** during installation.
3. Double-click **`start_windows.bat`**. Alternatively open Command Prompt in the extracted folder and run `py -3 main.py` (or `python main.py`).
4. Your browser should open **http://127.0.0.1:8765**. If it doesn't, paste that address manually.
5. Keep the Command Prompt window open while using the simulator. Press **Ctrl+C** to close it.

## FIRST RUN (macOS / Linux)

Open Terminal inside the extracted folder and run:

```bash
python3 main.py
```

Then visit **http://127.0.0.1:8765**. Tested with Python 3.13 and standard-library dependencies only.

## 5-MINUTE DEMO

- Click **Navigate** with **Presentation zone** selected. The robot plans and follows a path around rectangular obstacles.
- Click **Add obstacle**, then click a clear point in the arena ahead of the robot. It replans around the new object.
- Ask in chat: **"What do you see?"** It gives simulated range data honestly, without claiming to see through a camera.
- Click **EMERGENCY STOP**. All motion is disabled until you click **RELEASE**.
- Say **"Go to the lab"**, **"stop"**, **"move forward"**, or **"who made you?"**.
- To test the browser microphone, click ◉ (usually supported by Chromium-based browsers with permission). Enable **Speak replies** to hear text-to-speech, if supported.

## WHAT'S REAL VS SIMULATED

**Real code:** A* grid path planning, virtual sensor ray casting, waypoint following, timed manual movement commands, collision envelope, route replanning, software safety interlocks, emergency-stop state, decision/event logging, command parser, text chat, optional AI model connection.

**Simulated:** Obstacle distance readings, wheel movement, robot location, destinations, environmental awareness. The path planner has access to the complete digital arena map. A physical robot **will not know its map or position without additional localization/vision/odometry hardware and software**. The web browser voice interface is a laptop convenience, not a robot microphone circuit.

**Not implemented:** Actual motor controls, ESP32 firmware, Li-ion charging/power electronics, physical emergency power disconnect, camera-based perception, object identification, SLAM, speech processing on the robot, independent human following, precise navigation in the real world.

**Safety:** A software STOP on a laptop is not a substitute for a *physical* e-stop cutting motor power. Never connect motor voltage to an ESP32 GPIO. Validate motor driver ratings and use a battery fuse, regulator, protection and safe wiring before hardware tests.

## OPTIONAL: ADD A TRUE LANGUAGE MODEL

Without a model, movement, safety, telemetry, and several conversational replies work. For open-ended conversation, select **one** option below.

### Option A — Local Ollama (no cloud AI usage fees)

You must separately install Ollama and download a small supported model once. For example, after installing Ollama, run in a terminal:

```bash
ollama pull qwen2.5:1.5b
ollama serve
```

If Ollama is already running, you do not need to launch `ollama serve` again. Then start the robot with the local-model launcher:

- Windows: **`start_ollama_windows.bat`**
- macOS/Linux: **`./start_ollama_mac_linux.sh`**

This 1.5B example may be manageable on an 8 GB RAM laptop, but latency varies. Larger models require more RAM, disk space and can be slow on CPUs. Model responses may still hallucinate; the safety controller does **not** execute untrusted AI text as movement instructions.

### Option B — OpenAI API (internet + separate API billing required)

Provide an API key only to the local Python server **via an environment variable**. Never paste a secret into the browser chat or hardcode it into a repo.

Windows Command Prompt:

```bat
set ROBOT_LLM_KEY=PASTE_KEY_HERE
set ROBOT_LLM_MODEL=gpt-4.1-mini
py -3 main.py
```

macOS / Linux terminal:

```bash
export ROBOT_LLM_KEY='PASTE_KEY_HERE'
export ROBOT_LLM_MODEL='gpt-4.1-mini'
python3 main.py
```

Replace the example model name with a model available on your API account. This implementation uses the `/v1/responses` API server-side for **conversational text only**, not tool execution or motor control. See https://platform.openai.com/docs/api-reference/responses

**Never include secrets when sharing the ZIP.** There is no key in this distribution.

## HOW IT IS STRUCTURED

```text
Prometheus_Robot_Mind/
├─ main.py                     local HTTP service and dashboard host
├─ brain.py                    planner, simulator, safety, commands, personality, AI adapter
├─ static/
│  ├─ index.html              interface
│  ├─ style.css                visual styling
│  └─ app.js                   arena, interaction, browser voice
├─ tests/test_brain.py         built-in unit tests
├─ docs/
│  ├─ ARCHITECTURE.md          system design
│  ├─ HARDWARE_PORT.md         how to migrate to physical robot
│  └─ DEMO_SCRIPT.md          3-minute prototype demonstration
├─ start_windows.bat
├─ start_mac_linux.sh
├─ start_ollama_windows.bat
└─ start_ollama_mac_linux.sh
```

## RUN TESTS

From the project directory:

```bash
python -m unittest discover -s tests -v
```

## TROUBLESHOOTING

- `python is not recognized`: Install Python and reopen terminal; try `py -3 main.py`.
- Page doesn't open: Keep the Python terminal running, then browse to `http://127.0.0.1:8765`.
- `Address already in use`: You probably have two copies running. Close one or choose a port: `set ROBOT_PORT=8766` on Windows / `ROBOT_PORT=8766 python3 main.py` on Mac/Linux.
- Mic doesn't work: Chrome/Edge often provide browser speech recognition; browser recognition may send audio to a cloud speech service depending on browser implementation. Text chat is the reliable offline alternative.
- Robot won't drive after stopping: Press **RELEASE** if emergency stop is active.
- Online model won't talk: Check API account credit/key/selected model or start Ollama; the command layer still works offline.
- Network note: The web server binds only to **127.0.0.1**, intentionally preventing access from other devices. Do not expose it publicly without proper authentication, CSRF protections, and secure transport.

### Scope
R1 is a **laptop prototype mind**, not a production autonomous robot software stack. The next milestone is ESP32 integration plus wheel odometry, real ultrasonic measurements and a physical kill switch, followed by real-camera perception.
