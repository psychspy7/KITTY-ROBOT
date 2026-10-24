/* Browser-only, nominal circuit constraints and kinematic motion. No device I/O. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.KittyLab = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const spec = (
    id,
    title,
    pins,
    pos,
    size,
    color,
    optional = false,
    note = "",
  ) => ({ id, title, pins: pins.split(" "), pos, size, color, optional, note });
  const components = [
    spec(
      "esp",
      "ESP32 · classic preset",
      "V5 V3 GND D18 D19 D21 D22 D23 D25 D26 D27 D32 D33 D16 D17",
      [-27, 52, -42],
      [27, 9, 52],
      "#178a82",
      false,
      "Educational classic ESP32 pin names; your exact board is unidentified. No firmware emulation.",
    ),
    spec(
      "driver",
      "TB6612FNG · motor driver",
      "VCC VM GND STBY AIN1 AIN2 PWMA BIN1 BIN2 PWMB AO1 AO2 BO1 BO2",
      [25, 52, -40],
      [24, 7, 26],
      "#be577d",
      false,
      "Nominal logic model; stall current, thermal limits and carrier pin layout are not simulated.",
    ),
    spec(
      "front",
      "HC-SR04 · front",
      "VCC GND TRIG ECHO",
      [0, 43, -78],
      [45, 20, 2],
      "#2b9d96",
      false,
      "Virtual cone samples the arena; actual range and acoustic cross-talk are unverified.",
    ),
    spec(
      "rear",
      "HC-SR04 · rear",
      "VCC GND TRIG ECHO",
      [50, 72, 94],
      [45, 20, 2],
      "#2b9d96",
    ),
    spec(
      "motorL",
      "BO motor · left",
      "P N",
      [-63, 32.25, 20],
      [24, 20, 65],
      "#dabb4d",
    ),
    spec(
      "motorR",
      "BO motor · right",
      "P N",
      [63, 32.25, 20],
      [24, 20, 65],
      "#dabb4d",
    ),
    spec(
      "batteryA",
      "AA holder A · 2 cells",
      "P N",
      [-40, 36, 27],
      [31, 17, 58],
      "#8c956d",
      false,
      "Assumed two-cell envelope; actual holders, chemistry and mounting are unverified.",
    ),
    spec(
      "batteryB",
      "AA holder B · 2 cells",
      "P N",
      [4, 36, 27],
      [31, 17, 58],
      "#8c956d",
      false,
      "Series link gives four cells total. Model ignores internal resistance and discharge.",
    ),
    spec(
      "switch",
      "Motor power switch",
      "IN OUT",
      [61, 65, 57],
      [12, 14, 18],
      "#d3894c",
      false,
      "Ideal switch in the virtual motor rail; real rating is unknown.",
    ),
    spec(
      "usb",
      "USB logic source · model 5 V",
      "V5 GND",
      [-125, 70, -50],
      [24, 12, 30],
      "#7f98b0",
      false,
      "Ideal virtual USB 5 V source, separate from motor AA supply.",
    ),
    spec(
      "divF",
      "Front ECHO divider",
      "IN OUT GND",
      [-15, 62, -61],
      [19, 5, 11],
      "#bc9766",
      false,
      "Nominal divider: upper 2.2k; lower 3.2k (2.2k + 1k in series). Counts and real tolerances need checking.",
    ),
    spec(
      "divR",
      "Rear ECHO divider",
      "IN OUT GND",
      [21, 62, -61],
      [19, 5, 11],
      "#bc9766",
      false,
      "This block represents three resistors, not a component you already own.",
    ),
    spec(
      "servo",
      "SG90 · placement only",
      "VCC GND SIG",
      [-170, 15, 60],
      [23, 23, 13],
      "#5688c4",
      true,
      "Placement and wiring notes only. No servo load or torque model; phone neck stays fixed.",
    ),
    spec(
      "ir",
      "IR module · unidentified",
      "VCC GND OUT",
      [170, 12, -60],
      [18, 9, 32],
      "#435d97",
      true,
      "Type unknown: no detection behavior or verified pin assignment.",
    ),
    spec(
      "mic",
      "Microphone · unidentified",
      "VCC GND OUT",
      [170, 12, -15],
      [20, 8, 30],
      "#365e9a",
      true,
      "Placement only; this module is not assumed to provide speech audio.",
    ),
    spec(
      "relay",
      "Relay · placement only",
      "VCC GND IN COM NO NC",
      [170, 15, 35],
      [28, 18, 43],
      "#346bb0",
      true,
      "No relay/contact or coil-current simulation.",
    ),
    spec(
      "uno",
      "Uno R3 · spare",
      "V5 GND D2 D3",
      [170, 13, 100],
      [54, 14, 69],
      "#257d8a",
      true,
      "Placement only; does not emulate an AVR or flash firmware.",
    ),
    spec(
      "led",
      "LED · placement only",
      "A K",
      [-170, 9, -10],
      [8, 10, 8],
      "#ed7a68",
      true,
      "Use a suitable series resistor in real hardware. No LED current model.",
    ),
    spec(
      "capacitor",
      "220 µF · placement only",
      "P N",
      [-170, 10, -45],
      [10, 18, 10],
      "#4a6d8b",
      true,
      "Voltage rating/polarity unverified. No transient/capacitance model.",
    ),
    spec(
      "breadboard",
      "Breadboard · placement only",
      "RAIL_P RAIL_N",
      [-170, 7, 140],
      [55, 10, 85],
      "#cbd3d8",
      true,
      "No implicit breadboard strips: only the two displayed rail terminals exist in this model.",
    ),
    spec(
      "perfboard",
      "Perfboard · placement only",
      "PAD1 PAD2",
      [170, 5, 180],
      [50, 3, 65],
      "#aa8656",
      true,
      "No implicit copper tracks. Two displayed pads only.",
    ),
  ];
  const catalogue = Object.fromEntries(components.map((c) => [c.id, c]));
  const endpoints = new Set(
    components.flatMap((c) => c.pins.map((p) => c.id + "." + p)),
  );
  const mechanical = [
    "v7_base",
    "v7_motor_left",
    "v7_motor_right",
    "REFERENCE_ONLY_wheel_envelope_-1",
    "REFERENCE_ONLY_wheel_envelope_1",
    "REFERENCE_ONLY_caster_envelope",
  ];
  const clone = (v) => JSON.parse(JSON.stringify(v));
  function defaultProject() {
    const placements = {};
    for (const c of components)
      placements[c.id] = {
        attached: !c.optional,
        offset: [0, 0, 0],
        rotation: 0,
      };
    for (const id of mechanical)
      placements[id] = { attached: true, offset: [0, 0, 0], rotation: 0 };
    return {
      format: "kitty-assembly-lab",
      version: 1,
      wires: [],
      placements,
      settings: {
        chemistry: "alkaline",
        switchOn: true,
        rTop: 2200,
        rBottom: 3200,
        maxSpeed: 180,
        stopDistance: 180,
      },
      obstacles: [
        { x: 0, z: -410, w: 240, d: 130 },
        { x: -440, z: 0, w: 160, d: 260 },
        { x: 390, z: 150, w: 150, d: 190 },
      ],
    };
  }
  const demoPairs = [
    ["usb.V5", "esp.V5"],
    ["usb.GND", "esp.GND"],
    ["esp.V3", "driver.VCC"],
    ["usb.GND", "driver.GND"],
    ["batteryA.N", "batteryB.P"],
    ["batteryB.N", "usb.GND"],
    ["batteryA.P", "switch.IN"],
    ["switch.OUT", "driver.VM"],
    ["esp.D22", "driver.STBY"],
    ["esp.D25", "driver.PWMA"],
    ["esp.D26", "driver.AIN1"],
    ["esp.D27", "driver.AIN2"],
    ["esp.D18", "driver.PWMB"],
    ["esp.D19", "driver.BIN1"],
    ["esp.D21", "driver.BIN2"],
    ["driver.AO1", "motorL.P"],
    ["driver.AO2", "motorL.N"],
    ["driver.BO1", "motorR.P"],
    ["driver.BO2", "motorR.N"],
    ["usb.V5", "front.VCC"],
    ["usb.GND", "front.GND"],
    ["esp.D32", "front.TRIG"],
    ["front.ECHO", "divF.IN"],
    ["divF.OUT", "esp.D33"],
    ["usb.GND", "divF.GND"],
    ["usb.V5", "rear.VCC"],
    ["usb.GND", "rear.GND"],
    ["esp.D16", "rear.TRIG"],
    ["rear.ECHO", "divR.IN"],
    ["divR.OUT", "esp.D17"],
    ["usb.GND", "divR.GND"],
  ];
  function connect(p, a, b) {
    if (!endpoints.has(a) || !endpoints.has(b) || a === b)
      throw Error("Choose two different known terminals.");
    if (p.wires.length >= 160) throw Error("Maximum 160 wires.");
    if (
      p.wires.some((w) => (w.a === a && w.b === b) || (w.a === b && w.b === a))
    )
      throw Error("Those terminals are already connected.");
    p.wires.push({ a, b });
    return p;
  }
  function loadDemo(p) {
    p.wires = [];
    for (const [a, b] of demoPairs) connect(p, a, b);
    return p;
  }
  function validateProject(input) {
    if (!input || input.format !== "kitty-assembly-lab" || input.version !== 1)
      throw Error("Unsupported KITTY project format.");
    const p = defaultProject(),
      s = input.settings;
    if (
      !s ||
      !["alkaline", "nimh"].includes(s.chemistry) ||
      typeof s.switchOn !== "boolean"
    )
      throw Error("Invalid power settings.");
    for (const [key, lo, hi] of [
      ["rTop", 100, 100000],
      ["rBottom", 100, 100000],
      ["maxSpeed", 30, 300],
      ["stopDistance", 160, 500],
    ]) {
      if (!Number.isFinite(s[key]) || s[key] < lo || s[key] > hi)
        throw Error("Invalid " + key);
    }
    p.settings = {
      chemistry: s.chemistry,
      switchOn: s.switchOn,
      rTop: s.rTop,
      rBottom: s.rBottom,
      maxSpeed: s.maxSpeed,
      stopDistance: s.stopDistance,
    };
    if (!Array.isArray(input.wires) || input.wires.length > 160)
      throw Error("Invalid wire list.");
    for (const w of input.wires) {
      if (!w || typeof w.a !== "string" || typeof w.b !== "string")
        throw Error("Invalid terminal.");
      connect(p, w.a, w.b);
    }
    if (
      !input.placements ||
      typeof input.placements !== "object" ||
      Array.isArray(input.placements) ||
      Object.keys(input.placements).length > 100
    )
      throw Error("Invalid placements.");
    for (const [id, v] of Object.entries(input.placements)) {
      if (
        !/^(v7_[a-z_]+|REFERENCE_ONLY_[A-Za-z0-9_.-]+|[A-Za-z][A-Za-z0-9]{0,20})$/.test(
          id,
        ) ||
        ["constructor", "prototype", "__proto__"].includes(id) ||
        !v ||
        typeof v.attached !== "boolean" ||
        !Array.isArray(v.offset) ||
        v.offset.length !== 3 ||
        v.offset.some((n) => !Number.isFinite(n) || Math.abs(n) > 1500) ||
        !Number.isFinite(v.rotation) ||
        Math.abs(v.rotation) > 3600
      )
        throw Error("Invalid component placement.");
      p.placements[id] = {
        attached: v.attached,
        offset: [...v.offset],
        rotation: v.rotation,
      };
    }
    if (!Array.isArray(input.obstacles) || input.obstacles.length > 24)
      throw Error("Maximum 24 obstacles.");
    p.obstacles = input.obstacles.map((o) => {
      if (
        !o ||
        !Number.isFinite(o.x) ||
        !Number.isFinite(o.z) ||
        Math.abs(o.x) > 900 ||
        Math.abs(o.z) > 900 ||
        !Number.isFinite(o.w) ||
        !Number.isFinite(o.d) ||
        o.w < 40 ||
        o.w > 500 ||
        o.d < 40 ||
        o.d > 500
      )
        throw Error("Invalid obstacle.");
      return { x: o.x, z: o.z, w: o.w, d: o.d };
    });
    return p;
  }
  function diagnose(p) {
    const parents = new Map([...endpoints].map((e) => [e, e]));
    const find = (e) => {
      let r = e;
      while (parents.get(r) !== r) r = parents.get(r);
      return r;
    };
    const join = (a, b) => parents.set(find(a), find(b));
    for (const w of p.wires)
      if (endpoints.has(w.a) && endpoints.has(w.b)) join(w.a, w.b);
    if (p.settings.switchOn) join("switch.IN", "switch.OUT");
    const same = (a, b) => find(a) === find(b),
      issues = [];
    const add = (code, text) => {
      if (!issues.some((i) => i.code === code && i.text === text))
        issues.push({ code, text });
    };
    const adj = new Map();
    const source = (a, b, volts) => {
      a = find(a);
      b = find(b);
      if (!adj.has(a)) adj.set(a, []);
      if (!adj.has(b)) adj.set(b, []);
      adj.get(b).push([a, volts]);
      adj.get(a).push([b, -volts]);
    };
    source("usb.V5", "usb.GND", 5);
    const half = p.settings.chemistry === "nimh" ? 2.4 : 3;
    source("batteryA.P", "batteryA.N", half);
    source("batteryB.P", "batteryB.N", half);
    function solve() {
      const values = new Map(),
        absolute = new Set();
      const start = find("usb.GND");
      for (const seed of [start, ...adj.keys()]) {
        if (values.has(seed)) continue;
        values.set(seed, 0);
        const queue = [seed];
        if (seed === start) absolute.add(seed);
        for (let i = 0; i < queue.length; i++) {
          const n = queue[i];
          for (const [next, d] of adj.get(n) || []) {
            const value = values.get(n) + d;
            if (values.has(next)) {
              if (Math.abs(values.get(next) - value) > 0.05)
                add("short", "Conflicting voltage sources / supply short.");
            } else {
              values.set(next, value);
              queue.push(next);
              if (absolute.has(n)) absolute.add(next);
            }
          }
        }
      }
      return (e) => (absolute.has(find(e)) ? values.get(find(e)) : null);
    }
    let voltage = solve();
    const near = (v, n) => v !== null && Math.abs(v - n) < 0.12;
    const powered = near(voltage("esp.V5"), 5) && near(voltage("esp.GND"), 0);
    if (powered) source("esp.V3", "esp.GND", 3.3);
    voltage = solve();
    for (const id of ["front", "rear"])
      if (near(voltage(id + ".VCC"), 5) && near(voltage(id + ".GND"), 0))
        source(id + ".ECHO", id + ".GND", 5);
    voltage = solve();
    const echoVoltage =
      (5 * p.settings.rBottom) / (p.settings.rTop + p.settings.rBottom);
    for (const id of ["divF", "divR"])
      if (near(voltage(id + ".IN"), 5) && near(voltage(id + ".GND"), 0))
        source(id + ".OUT", id + ".GND", echoVoltage);
    voltage = solve();
    if (!powered)
      add("logic-power", "ESP32 needs the virtual USB 5 V and common ground.");
    if (!near(voltage("driver.VCC"), 3.3))
      add("driver-logic", "Driver VCC must reach the model ESP32 3.3 V rail.");
    if (!near(voltage("driver.GND"), 0))
      add("ground", "Motor driver ground is missing.");
    const motorVoltage = voltage("driver.VM");
    if (motorVoltage === null || motorVoltage < 2.5 || motorVoltage > 13.5)
      add(
        "motor-power",
        "Motor rail is absent / outside the model range. Check the AA series link, ground and switch.",
      );
    for (const pin of catalogue.esp.pins.filter((pin) => pin.startsWith("D"))) {
      const v = voltage("esp." + pin);
      if (v !== null && v > 3.45)
        add(
          "gpio-voltage",
          "ESP32 " +
            pin +
            " receives " +
            v.toFixed(2) +
            " V in the nominal model.",
        );
      if (!["D33", "D17"].includes(pin) && v !== null)
        add(
          "signal-rail",
          "GPIO output " + pin + " is connected to a driven rail.",
        );
    }
    for (const [a, b] of demoPairs.filter(
      ([a, b]) =>
        a.startsWith("esp.D") && !["front.TRIG", "rear.TRIG"].includes(b),
    )) {
      if (!same(a, b))
        add(
          "signal",
          a + " → " + b + " is missing or assigned to a different model pin.",
        );
    }
    for (const id of ["front", "rear"]) {
      const d = id === "front" ? "divF" : "divR",
        trig = id === "front" ? "D32" : "D16",
        echo = id === "front" ? "D33" : "D17";
      if (!near(voltage(id + ".VCC"), 5) || !near(voltage(id + ".GND"), 0))
        add(
          "sensor-power",
          catalogue[id].title + " needs 5 V and common ground.",
        );
      if (
        !same("esp." + trig, id + ".TRIG") ||
        !same(id + ".ECHO", d + ".IN") ||
        !same(d + ".OUT", "esp." + echo) ||
        !near(voltage(d + ".GND"), 0)
      )
        add(
          "sensor-signal",
          "Check " + id + " TRIG, ECHO divider and ESP32 signal paths.",
        );
    }
    if (echoVoltage < 2.6 || echoVoltage > 3.3)
      add(
        "divider",
        "ECHO divider leaves the conservative 2.6–3.3 V nominal model window.",
      );
    const polarity = (id, o1, o2) =>
      same("driver." + o1, id + ".P") && same("driver." + o2, id + ".N")
        ? 1
        : same("driver." + o1, id + ".N") && same("driver." + o2, id + ".P")
          ? -1
          : 0;
    const leftPolarity = polarity("motorL", "AO1", "AO2"),
      rightPolarity = polarity("motorR", "BO1", "BO2");
    if (!leftPolarity || !rightPolarity)
      add(
        "motor-leads",
        "Connect both motor terminals to their matching driver output pairs.",
      );
    const outputs = [
      "driver.AO1",
      "driver.AO2",
      "driver.BO1",
      "driver.BO2",
      ...catalogue.esp.pins
        .filter((pin) => pin.startsWith("D"))
        .map((pin) => "esp." + pin),
    ];
    for (let i = 0; i < outputs.length; i++) {
      const v = voltage(outputs[i]);
      if (outputs[i].startsWith("driver.") && v !== null)
        add("output-rail", "A motor output is connected to a supply rail.");
      for (let j = i + 1; j < outputs.length; j++)
        if (same(outputs[i], outputs[j]))
          add(
            "signal-short",
            "Output pins are shorted: " + outputs[i] + " / " + outputs[j],
          );
    }
    for (const id of [
      ...components.filter((c) => !c.optional).map((c) => c.id),
      ...mechanical,
    ]) {
      const v = p.placements[id];
      if (
        v &&
        (!v.attached ||
          Math.hypot(...v.offset) > 0.1 ||
          Math.abs(v.rotation % 360) > 0.1)
      )
        add(
          "assembly",
          (catalogue[id]?.title || id) +
            " is detached or moved away from its nominal mount.",
        );
    }
    return {
      ready: issues.length === 0,
      issues,
      motorVoltage,
      echoVoltage,
      leftPolarity,
      rightPolarity,
      voltage: (e) => (endpoints.has(e) ? voltage(e) : null),
      net: (e) => (endpoints.has(e) ? find(e) : null),
    };
  }
  function rayBox(x, z, dx, dz, o) {
    let lo = 0,
      hi = 4000;
    for (const [p, d, mn, mx] of [
      [x, dx, o.x - o.w / 2, o.x + o.w / 2],
      [z, dz, o.z - o.d / 2, o.z + o.d / 2],
    ]) {
      if (Math.abs(d) < 1e-9) {
        if (p < mn || p > mx) return Infinity;
      } else {
        let a = (mn - p) / d,
          b = (mx - p) / d;
        if (a > b) [a, b] = [b, a];
        lo = Math.max(lo, a);
        hi = Math.min(hi, b);
        if (lo > hi) return Infinity;
      }
    }
    return lo;
  }
  function ranges(p, pose) {
    const walls = [
        { x: 0, z: -1010, w: 2020, d: 20 },
        { x: 0, z: 1010, w: 2020, d: 20 },
        { x: -1010, z: 0, w: 20, d: 2020 },
        { x: 1010, z: 0, w: 20, d: 2020 },
      ],
      objects = [...p.obstacles, ...walls];
    const read = (rear) => {
      const a = pose.yaw,
        c = Math.cos(a),
        s = Math.sin(a),
        ox = rear ? 50 : 0,
        oz = rear ? 107 : -91;
      const x = pose.x + c * ox - s * oz,
        z = pose.z + s * ox + c * oz;
      let best = 4000;
      for (let n = -4; n <= 4; n++) {
        const angle = a + (rear ? Math.PI : 0) + n * 0.055,
          dx = Math.sin(angle),
          dz = -Math.cos(angle);
        for (const o of objects) best = Math.min(best, rayBox(x, z, dx, dz, o));
      }
      return Math.max(0, best);
    };
    return { front: read(false), rear: read(true) };
  }
  function collides(p, x, z) {
    const radius = 140;
    if (Math.abs(x) > 1000 - radius || Math.abs(z) > 1000 - radius) return true;
    return p.obstacles.some(
      (o) =>
        Math.hypot(
          x - Math.max(o.x - o.w / 2, Math.min(x, o.x + o.w / 2)),
          z - Math.max(o.z - o.d / 2, Math.min(z, o.z + o.d / 2)),
        ) < radius,
    );
  }
  class Controller {
    constructor(project) {
      this.project = project;
      this.state = {
        pose: { x: 0, z: 350, yaw: 0 },
        armed: false,
        estop: false,
        link: true,
        sensorValid: true,
        left: 0,
        right: 0,
        reason: "Disarmed",
        distance: 0,
      };
      this.request = [0, 0];
      this.lastCommand = -Infinity;
      this.lastValidation = null;
    }
    arm() {
      if (
        this.state.estop ||
        !this.state.link ||
        !this.state.sensorValid ||
        !diagnose(this.project).ready
      )
        return false;
      this.state.armed = true;
      this.state.reason = "Armed · hold a drive control";
      this.lastCommand = -Infinity;
      return true;
    }
    stop(reason = "Disarmed") {
      this.state.armed = false;
      this.state.left = 0;
      this.state.right = 0;
      this.request = [0, 0];
      this.state.reason = reason;
    }
    emergencyStop() {
      this.state.estop = true;
      this.stop("Emergency stop latched");
    }
    command(left, right, now) {
      if (
        ![left, right, now].every(Number.isFinite) ||
        Math.abs(left) > 1 ||
        Math.abs(right) > 1
      ) {
        this.stop("Invalid command");
        return false;
      }
      if (!this.state.armed) return false;
      this.request = [left, right];
      this.lastCommand = now;
      return true;
    }
    tick(dt, now) {
      if (!Number.isFinite(dt) || !Number.isFinite(now) || dt < 0) {
        this.stop("Invalid clock");
        return;
      }
      dt = Math.min(dt, 0.1);
      const s = this.state;
      this.lastValidation = diagnose(this.project);
      s.ranges = ranges(this.project, s.pose);
      if (!s.armed) return;
      if (!this.lastValidation.ready || s.estop || !s.link || !s.sensorValid) {
        this.stop(
          s.estop
            ? "Emergency stop latched"
            : !s.link
              ? "Link lost"
              : !s.sensorValid
                ? "Sensor lost"
                : "Wiring / assembly changed",
        );
        return;
      }
      if (this.lastCommand === -Infinity) {
        s.left = 0;
        s.right = 0;
        return;
      }
      if (now - this.lastCommand > 500 || now < this.lastCommand) {
        this.stop("Command timeout · re-arm required");
        return;
      }
      let [l, r] = this.request;
      l *= this.lastValidation.leftPolarity;
      r *= this.lastValidation.rightPolarity;
      if (
        (Math.max(l, r) > 0 &&
          s.ranges.front < this.project.settings.stopDistance) ||
        (Math.min(l, r) < 0 &&
          s.ranges.rear < this.project.settings.stopDistance)
      ) {
        s.left = 0;
        s.right = 0;
        s.reason = "Obstacle guard · release / change direction";
        return;
      }
      const speed = this.project.settings.maxSpeed,
        v = ((l + r) / 2) * speed,
        w = ((l - r) * speed) / 198,
        a = s.pose.yaw + (w * dt) / 2,
        nx = s.pose.x + Math.sin(a) * v * dt,
        nz = s.pose.z - Math.cos(a) * v * dt;
      if (collides(this.project, nx, nz)) {
        s.left = 0;
        s.right = 0;
        s.reason = "Conservative footprint collision guard";
        return;
      }
      s.pose.x = nx;
      s.pose.z = nz;
      s.pose.yaw = (s.pose.yaw + w * dt) % (2 * Math.PI);
      s.distance += Math.abs(v * dt);
      s.left = l;
      s.right = r;
      s.reason = l || r ? "Driving · virtual only" : "Armed · stopped";
      s.ranges = ranges(this.project, s.pose);
    }
  }
  return {
    components,
    catalogue,
    mechanical,
    defaultProject,
    loadDemo,
    connect,
    diagnose,
    validateProject,
    Controller,
    ranges,
    clone,
  };
});
