# R2 parametric STL/STEP framework

This is a working CAD source/export framework, not the final R2 body or a fit-approved print set. No physical dimensions have yet been supplied. `parameters.measured.json` therefore contains nulls. `parameters.example.json` is explicitly illustrative and produces only `draft_*` outputs.

## Install and use

The simulator and face workbench do not need these CAD packages. For CAD only, create a separate Python 3.12 environment and install `requirements.txt` (cadgen with snapshot support, pinned to 0.7.10). On Windows:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python src\draft_base.py
.venv\Scripts\python src\draft_phone_cradle.py
.venv\Scripts\python src\draft_motor_coupon.py
.venv\Scripts\python src\draft_sensor_coupon.py
```

Use the equivalent venv interpreter path on Linux/macOS. Run from this CAD directory. This cloud used a separate CAD venv outside the checkout and a writable external CAD cache; neither is installed on the user's laptop by these instructions.

Standard-library intake checks require no CAD installation:

```text
python -B -m unittest discover -s checks -p test_parameters.py -v
python src/parameters.py --example
python src/parameters.py
```

The last command currently exits 2 and names missing measured dimensions. That is intentional. Example fixtures cannot pass the measured-input check. Add a value in millimetres and an individual evidence/source string for every dimension when actual parts are measured. Design dimensions are proposed values and still need revision/approval; filling the JSON does not prove fit, strength or stability.

## Draft geometry checks

After generating all four draft entrypoints, run with the CAD interpreter:

```text
python checks/check_geometry.py
python -m cadgen.cli step snapshot STEP/draft_base.step tmp/base-review.png
```

The retained check reads saved STEP files, checks each intended single solid, bounds, selected through-hole/coupon volumes, STL closed edge topology and positive signed volume. Review each generated part visually as well. Geometric validity is not physical fit or a strength/slicer approval.

`src/README.md` lists the models and their limitations. Fit coupons are geometry templates, not instructions to print before the measured interface and material/nozzle/tolerance choices are reviewed. A fitted release still needs shaft and motor mounting features, caster geometry, phone camera/port positions, AA chemistry/cell count and holder, electronics footprints, wiring/cutoff service access, printer limits and appearance approval. Keep the SG90 out of the phone load path until its capability is established.

The existing R2 concept image remains the appearance direction. This framework does not replace it with an old N20 or BO reference chassis, and does not claim that a new final STL set already fits the purchased parts.
