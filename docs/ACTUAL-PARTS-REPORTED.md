# User-reported parts —23October2026

ESP32;TB6612;HC-SR04;UnoR3;BO DC motor(s);BO wheels approximately60mm diameter (user estimate);IR sensor;220ohm,1kohm,10kohm resistors;M-M,F-F,M-Fjumpers;cable ties;breadboard;PCB;multimeter;soldering kit;LED;OPPOA57phone;laptop. All are user-reported, not inspected photographs or measured variants.

Controller/driver pin labels, motor voltage/stall current/shaft offset, wheel exact size/hub, caster type/height, actual power pack/charger/fuse/cutoff, phone model code/case, available resistor counts, and printer bed remain unknown. A servo was mentioned previously but its model/quantity remains unknown. No assumption of a fitted mount or finalized circuit follows from this list.

Plan: ESP32 control, BO drivetrain, HC-SR04 range guard, OPPO camera/face/audio; Uno spare. Do not add wiring complexity just to use every owned board. Exact voltage conditioning must be matched to HC-SR04/ESP32 and measured available resistors; raw ECHO must not feed a GPIO.
