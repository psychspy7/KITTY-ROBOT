# KITTY V7 offline 3D Studio

One downloadable HTML file contains Three.js, orbit controls, all mesh data and four saved native CAD views. It needs no server, CDN, fetches, account or installation. Open the downloaded HTML in current Chrome or Edge with browser graphics acceleration enabled. WebGL uses the renderer selected by the browser; the page requests a high-performance adapter but cannot force a particular physical GPU.

The viewer offers assembled, exploded and separated print-part layouts; studio, wireframe, X-ray and blueprint surfaces; transparent covers; XYZ section cuts; part selection, hiding, isolation and focus; view presets, dimensions, labels, turntable, render quality, PNG capture and exact per-part STL downloads. Left drag orbits, right drag pans, scrolling/pinching zooms. F fits, W switches wireframe and R resets. The renderer settles when idle and pauses while the document is hidden.

The 13 printable meshes are byte-identical to the V7 service-kit exports. The optional internal tray starts hidden, leaving 12 production parts. Eleven saved native hardware/display envelopes are view-only; the unselected AA-holder envelope also starts hidden. Reference hardware has no STL download control. No wheels, motors or electronics are added to the print set. All thirteen mesh placement bounds are checked against the saved native STEP assembly. No design geometry changes.

Dimensions describe the currently visible layout, including illustrative explosion offsets or a selected part's original CAD axes; they are not new fit measurements. Sections are uncapped surface cuts. Wireframe is mesh structure, not electrical wiring. Exploded positions show the part breakdown, not a validated assembly sequence. Physical fit, bought components and printer profiles remain unverified; use the original fit-first service instructions before large prints.

If JavaScript or WebGL is unavailable, four embedded native CAD images and CSS-only view controls remain usable. Graphics context loss returns to these images. A restored context reinitializes the renderer; retry is also available.

Build in the existing CAD environment after producing the verified V7 service kit:

```sh
CADGEN_CACHE_DIR=/workspace/.kitty-cad-cache CADGEN_DAEMON=0 \
  /workspace/.kitty-cad-env/bin/python design/v7/advanced-viewer/build_viewer.py \
  --service /workspace/outputs/kitty-robot/v7-print-service \
  --out /workspace/outputs/kitty-robot/v7-3d-studio
/workspace/.kitty-cad-env/bin/python design/v7/advanced-viewer/check_browser.py \
  --directory /workspace/outputs/kitty-robot/v7-3d-studio
```

`MODEL-PROVENANCE.json` records mesh/source hashes and poses. `BROWSER-VERIFICATION.json` records real Chromium checks on the exact HTML, with networking disabled and desktop/mobile/fallback captures. This cloud browser restricts direct file navigation, so verification loads the exact complete HTML with `set_content`; the delivered artifact contains no external assets. Cloud software WebGL verifies behavior, not the user's physical GPU performance.

Third-party runtime: Three.js 0.160.1, official npm tarball `https://registry.npmjs.org/three/-/three-0.160.1.tgz`, archive SHA256 `d462f9bb4a53d0a75f5ebba49ec1c69847f166cd1bd6cbfdd98ce0b5b7988609`. Original sources and MIT notice are under `vendor`. The builder adapts OrbitControls' import/export into the same inline classic-script runtime; no import map or module server is needed. The license is also embedded in the HTML.

V7.1 is an additive rear-sensor variant. Pass `--dual-ultrasonic` to the builder and browser checker with the new service/output folder. It loads the saved 28-body native assembly, including fourteen printable body meshes (one optional) and rear PCB/transducer references. The print layout therefore contains thirteen required pieces. The V7.1 output uses an explicit dual-ultrasonic filename and current native fallback images. See `../REAR-ULTRASONIC.md` for mounting, assumptions and generation commands.
