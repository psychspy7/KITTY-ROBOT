# Migration from Laptop Simulator to Physical Prototype

This guide is a checklist, not a tested wiring diagram. Final wiring depends on your exact motor, driver, battery and ESP32 board.

## 1. Recommended division

**Laptop/phone:** Personality, speech input and output, high-level intent, status interface. The old OnePlus phone can show the animated face and act as mic/speaker if compatible.

**ESP32:** Low-level motor drive, real sensor polling, command timeout, speed/ramp limits, watchdog and robot heartbeat. On lost Wi-Fi or command timeout it must stop motors by itself.

**Safety hardware:** Normally-closed latching emergency stop wired to motor power-enable/disconnect, battery fuse, a properly rated motor driver, separate regulated logic power, mechanical wheel protection. Do not rely on a browser button for injury prevention.

## 2. Adapter replacing the simulator

Current simulation functions live in `brain.py`. Later, replace them with a hardware adapter:

```python
class RobotHardwareAdapter:
    def read_sensors(self) -> dict:
        # Read validated mm distances, encoders, battery voltage, physical estop state.
        raise NotImplementedError

    def set_motion(self, linear_mps: float, angular_rps: float) -> None:
        # Rate-limit; enforce obstacle boundaries and require an active heartbeat.
        raise NotImplementedError

    def emergency_stop(self) -> None:
        # Assert hardware motor disable; never bypass physical kill switch.
        raise NotImplementedError
```

**Important:** The `RobotBrain` class does **not** yet drive this adapter and you should not connect the hardware based only on this sketch.

## 3. Minimum bill of materials (prototype)

- 1 × ESP32 development board with USB cable
- 2 × identical geared DC motors with verified wheel torque/current ratings
- 2 × compatible drive wheels, plus 1 × caster
- 1 × dual-channel motor driver **rated above motor stall current**, not just running current
- 1 × appropriately protected battery pack and properly matched charger/BMS where required
- 1 × fuse and main power switch; 1 × physical latching emergency cut-off
- 1–2 × ultrasonic distance sensors (e.g., HC-SR04 with a correctly level-shifted 5 V ECHO pin), or a compatible 3.3 V ToF sensor
- 1 × suitable 5 V/3.3 V regulator for logic, based on measured load
- Assorted M3/M4 fasteners, standoffs, insulated wire, reliable connectors, cable ties, structural parts
- Old Android phone with screen and camera (optional independent camera module)

**Caution:** Many popular L298N boards waste power and may not suit your motor current. TB6612FNG boards have limited current capability. Select the driver **after measuring the motor specification**, not by appearance.

## 4. Physical reality check

- Digital map -> real surroundings: requires perception/localization, not implemented in R1.
- Virtual range units -> actual centimeters: require calibrated sensor measurements.
- Virtual target coordinate -> physical target: requires localization or a simplified marked path.
- Full-map A* planning -> real navigation: only valid if you have a trustworthy map and pose estimate.

## 5. Three-day build approach

**Day 1:** Buy ready-made chassis/wheels/motors. Test safe motor drive + fuse/e-stop. Get simulator/voice working on laptop.

**Day 2:** Wire real distance sensor, implement ESP32 failsafe, send sensor data to host. Test stopping before obstacles at walking speed.

**Day 3:** Attach phone and printed mount, integrate a single real demonstration feature, prepare fallback/manual control, rehearse.

For a short hackathon deadline, demo **obstacle detection, safe stop, simple navigation, voice explanation and personality** before attempting SLAM, object tracking or moving arms.
