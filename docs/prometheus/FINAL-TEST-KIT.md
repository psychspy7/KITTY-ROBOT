# PROMETHEUS staged test kit

Download the [18-page test PDF](PROMETHEUS-FINAL-TEST-GUIDE.pdf) or the
[complete test ZIP](PROMETHEUS-FINAL-TEST-KIT.zip). The ZIP includes the PDF,
editable code canvas, combined text, complete Arduino folder, verification
records and reproducible source. Start with the isolated battery voltage and
polarity measurement on PDF page 3; keep the motor source disconnected.

The [source README](../../software/prometheus_test_kit/README.md) explains the
USB/AP-only defaults, stage settings and rebuild commands. The sketch uses one
canonical candidate pin map, real firmware telemetry, explicitly armed short
raised-wheel pulses, local pulse/lease/range checks and latched stop. Front and
optional rear sensor wiring are included. It does not implement autonomous floor
navigation, camera AI or path drawing/execution.

The exact distributed source and an enabled compiler fixture passed Arduino
ESP32 cores 2.0.17 and 3.3.2 for classic ESP32. Twenty-one native cases, twelve
browser fixture groups and eight packaging/rebuild groups pass. The PDF was
rendered and visually inspected. Compound Engineering review used ten lenses;
eight retained findings were independently validated and resolved with targeted
checks. Cross-model review did not run because no different-provider CLI was
available. Hashes and scope are in [the release record](FINAL-TEST-KIT-VERIFICATION.json).

These are software checks. No cloud upload, motor-power test, measured stop
latency, electrical approval or physical fit is claimed. Actual motor ratings,
pack voltage/polarity/arrangement, driver IC/VM/control labels and protection
remain unresolved. All verification flags are false and voltage fields zero in
the delivered Settings.h. A flag is an operator declaration, not an inspection.
