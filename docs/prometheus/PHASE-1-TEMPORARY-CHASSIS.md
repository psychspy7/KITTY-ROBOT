# PROMETHEUS — Phase 1: unpowered temporary chassis

Continue from the user's working ESP32 upload and `PROMETHEUS_ESP32` AP/web-server proof. This step has no firmware upload or electrical connections. A successful mechanical check does not approve motor power.

## Parts for this activity

- Rigid box base/lid or reinforced flat board; ruler and marker.
- Two BO motors, two matching wheels and the caster.
- Zip ties, suitable small brackets/fasteners or a temporary restraint that holds each motor firmly. Cover sharp edges.
- ESP32, TB6612, breadboard and **empty/disconnected** AA holders for checking the layout.
- Front HC-SR04; reserve rear space for the second reported module.
- Insulating supports/tape for electronics, and ties for cable restraint.

Choose the base around the actual parts. About 200 × 150 mm is a starting layout estimate if available, not a required cut size or a measured fit. A soft box that sags or twists needs reinforcement before mounting motors. Do not add the phone until the bare rolling base is stable.

## One activity: assemble and check the rolling base

1. Disconnect **both USB and all batteries**. Keep loose motor-wire ends separated and insulated. Mark FRONT and a centre line on the base.
2. Fit a wheel to each matching motor shaft without hammering or forcing the gearbox. Put the motors on opposite sides, shafts facing outward. Use a ruler to put the two shaft centres on **one transverse line**, roughly around or a little ahead of the base's middle. Wheels should be parallel, with enough clearance that neither tyre rubs the box, tie ends or cables under slight base flex.
3. Secure each motor body using brackets/ties. A wheel or shaft must not carry the motor's mounting load. Keep restraints clear of the shaft, gear openings, wheel hubs and solder terminals. Glue alone on a flexible box is not dependable motor restraint; avoid permanent glue until the fit is checked.
4. Attach the caster on the rear centre line. Adjust its spacer height so the two tyres and caster all touch a flat surface, without forcing the base to bend. Keep the caster swivel path clear.
5. Place the disconnected holders low, near the centre and **between the drive-wheel line and caster**. Restrain them against sliding. Place ESP32/TB6612 above the base on insulating supports, with driver cooling and ESP32 USB access. Keep the driver near the motor wires and the breadboard away from wheel motion. Reserve a reachable place for the motor-power switch; its rating and circuit are still pending.
6. Reserve a front position for the HC-SR04 with both round transducers facing forward and no base lip in front of them. Reserve a rear position for the second reported sensor. Both remain unwired. Keep the phone, neck/servo and decorative parts off this first mechanical test.
7. Lift and gently rotate each wheel enough to check rubbing; geared motors can resist back-driving, so do not force them to spin freely. Put the base on a flat surface and gently press each corner. Confirm it does not rock or tip and the motor bodies do not move in their restraints. Lift by the base, not the wiring or sensor.

```text
                       FRONT / first forward motion
                         [ front HC-SR04 ]

     bought wheel  [ BO motor ]       [ BO motor ]  bought wheel
           O ============ same shaft-centre line ============ O

                       [ TB6612 ] [ ESP32 ]
                       [ breadboard / space ]
                       [ disconnected holders ]

                              [ caster ]
                    [ reserved rear-sensor position ]
                                REAR
```

This temporary layout uses a rear caster. The separate V7.1 printed design has its own support layout and remains a different assembly; do not drill a printed part using this cardboard sketch.

## Expected result / quick diagnosis

| Observation | What to correct before proceeding |
| --- | --- |
| Base rocks | Caster height, base twist or loose support; establish three stable ground contacts |
| Tyre rubs | Move the motor outward slightly or trim/reinforce the base edge; keep enough hub engagement |
| Motor body twists | Improve brackets/straps and base stiffness; movement here ruins later turn calibration |
| Caster cannot swivel | Move cables/restraints out of its swept area |
| Box tips toward an edge | Reposition the disconnected holder mass lower and inside the support triangle |
| Wheel needs force to fit | Check hub/shaft compatibility; do not hammer the gearbox |

Finish this activity when the motors and caster are secure, wheels clear the base, and the disconnected component layout is stable. Record the base length × width and any rubbing/rocking. Keep all power disconnected.

## Essential information for the next electrical step

Motor model/rated voltage and startup/stall-current specification; TB6612 carrier/chip and pin labels; AA chemistry, cells per holder, series/parallel arrangement and measured pack voltage; wire/connector, switch, fuse and any regulator ratings. Obtain motor current information from its supplier if available; do not lock a motor to make a stall-current measurement.

Later sensor/indicator wiring also needs actual resistor values/counts, HC-SR04 variant and the buzzer module's markings, voltage/current and active/passive type. A four-AA description alone does not establish a suitable supply. Do not connect VM, join two holders, power a motor from an ESP32 header, or connect ECHO directly to a GPIO during this activity.

No code or Serial Monitor output is expected in Phase 1. Powered motor tests follow the reviewed wiring/power plan with the wheels raised.
