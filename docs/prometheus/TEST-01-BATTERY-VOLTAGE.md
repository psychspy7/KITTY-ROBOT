# Test 01 — isolated battery voltage and polarity

This is the next single physical test. It measures the isolated holder/pack only. No motor, driver, ESP32 or sensor is powered by it. A passing measurement does not approve connecting motor power.

## Set up

1. Unplug ESP32 USB. Disconnect every holder/pack lead from the robot, breadboard and driver. Do not rely only on a toggle switch. Keep separate holders separate; do not join them in series or parallel yet. Put the holder and meter on a dry, nonconductive surface, with exposed wire ends separated.
2. Read the cells' labels and count the cells actually installed in each holder. Record exact chemistry/printed voltage where available. Do not insert a different or additional cell just to reach an expected voltage. If no cells are installed, report **empty**; there is no powered-pack reading to interpret yet.
3. Put the **black meter lead in COM** and the **red lead in the voltage socket**, normally labelled V / VΩ / VΩmA. A combined voltage socket can include mA in its label; identify the socket supporting V. Do not use a separate A, mA-only or 10A current socket.
4. Select **DC voltage**, shown as V with a solid line over a dashed line (V⎓). Use auto-ranging if available. On a manual-range meter with an unidentified low-voltage battery pack, begin with its highest DC-voltage range; once a valid reading is known to be below 20 V, a 20 V DC range can give a clearer reading if the meter has that range. Do not select AC V~, A/mA, resistance or continuity. If the dial/jacks are unclear, send a photo of the meter before probing.

## Measure

5. For one disconnected holder, touch the black probe to its marked negative output and the red probe to its marked positive output. If outputs are unmarked, label them A/B for this test and record which probe touches each. Lead colour alone is not polarity proof. Touch only one terminal with each probe; do not bridge the two outputs with a probe tip.
6. Wait for the reading to settle. Record the **number, sign, unit and meter range**. A negative reading means the point under the red probe is at a lower potential than the point under the black probe; record that result before changing anything. Do not connect the robot afterward.
7. Remove the probes and switch the meter off. Keep the battery disconnected and leads insulated/separated. If there are two holders, record them separately using the same method; do not interconnect them.

## Expected output and interpretation

The output is a measured value in DC volts, not a required target. Four alkaline or four NiMH cells are still only examples until actual cells and holder wiring are identified. A no-load measurement does not reveal motor stall current, usable battery current, capacity or voltage under motor load.

| Result | Action within this test |
| --- | --- |
| Stable value and known probe locations | Record it; leave holder disconnected |
| Negative sign | Record sign and probe positions; do not infer polarity from insulation colour |
| `OL` / over-range | Remove probes and check meter instructions/range; report it |
| Zero or unstable | Check selected voltage mode and probe contact; report empty cells or ambiguous wiring rather than changing robot connections |
| Unclear meter dial/socket/holder outputs | Stop this test and provide a close photo for identification |

Never test battery current by putting the meter across the holder in A/mA mode. Never bridge its output wires to make a spark test. This procedure asks only for a voltage measurement.

## Report back

```text
Holder A: ___ cells; label/chemistry ___; printed cell voltage ___
Meter mode/range: ___
Red probe on ___; black probe on ___
Reading including sign and unit: ___
Holder B, if present: same information separately
Motor battery remains disconnected: yes
```

The subsequent physical test will be chosen from this result and the missing driver/motor evidence. No Arduino code or robot Serial Monitor output is needed for this test.
