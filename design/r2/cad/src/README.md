# Model catalog

All draft entrypoints use `parameters.example.json`, whose values are illustrative fixtures. Run from this CAD project directory using the pinned CAD interpreter.

| Entrypoint | STEP and STL stem | Purpose |
| --- | --- | --- |
| `draft_base.py` | `draft_base` | Base-plate generator with a four-hole example pattern |
| `draft_phone_cradle.py` | `draft_phone_cradle` | Open-top cradle factory with a large back opening |
| `draft_motor_coupon.py` | `draft_motor_coupon` | Cross-section fit coupon; not a motor mount |
| `draft_sensor_coupon.py` | `draft_sensor_coupon` | Two-transducer opening coupon; not a complete sensor bracket |
| `measured_base.py` | `measured_base` | Measured-input entrypoint; intentionally blocked until intake is complete |

Outputs are under `STEP/` and `STL/`; generated formats and scratch files are ignored by Git. Factories are in `geometry.py`; standard-library parameter intake/validation is in `parameters.py`. The complete motor mounting, neck attachment, caster mount, body cover, battery restraint, electronics mounts and actual camera/USB access are later fitted-CAD work, not implied by these draft parts.
