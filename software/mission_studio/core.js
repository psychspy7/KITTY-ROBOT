/* SI units. Browser/Node simulation only; no physical transport. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrometheusSim = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v)),
    angle = (a) => Math.atan2(Math.sin(a), Math.cos(a)),
    finite = Number.isFinite;
  const WORLD = {
    width: 5.6,
    depth: 4.0,
    cell: 0.08,
    radius: 0.165,
    track: 0.18,
    wheelRadius: 0.03125,
  };
  const GPIO = {
    AIN1: 25,
    AIN2: 26,
    PWMA: 27,
    BIN1: 18,
    BIN2: 19,
    PWMB: 23,
    STBY: 21,
    FRONT_TRIG: 22,
    FRONT_ECHO: 32,
    REAR_TRIG: 16,
    REAR_ECHO: 17,
    RADAR_TRIG: 4,
    RADAR_ECHO: 34,
    SERVO: 14,
    IR: 35,
    LED: 33,
    BUZZER: 13,
  };
  function component(id, title, pins, pos, color, kind = "board") {
    return { id, title, pins: pins.split(" "), pos, color, kind };
  }
  const components = [
    component(
      "esp",
      "ESP32 · virtual controller",
      "3V3 GND VIN " +
        Object.values(GPIO)
          .map((n) => "D" + n)
          .join(" "),
      [-0.038, 0.065, 0.035],
      "#278984",
    ),
    component(
      "driver",
      "TB6612 · dual motor stage",
      "VCC VM GND AIN1 AIN2 PWMA BIN1 BIN2 PWMB STBY AO1 AO2 BO1 BO2",
      [0.032, 0.062, 0.03],
      "#cf526d",
    ),
    component(
      "front",
      "Front ultrasonic",
      "VCC GND TRIG ECHO",
      [0, 0.043, -0.086],
      "#449d91",
      "sonar",
    ),
    component(
      "rear",
      "Rear ultrasonic",
      "VCC GND TRIG ECHO",
      [0.05, 0.072, 0.1],
      "#449d91",
      "sonar",
    ),
    component(
      "radar",
      "Corner ultrasonic · planned",
      "VCC GND TRIG ECHO",
      [-0.095, 0.112, -0.055],
      "#63c8d4",
      "sonar",
    ),
    component(
      "servo",
      "Scanning servo · planned mount",
      "5V GND SIG",
      [-0.095, 0.084, -0.055],
      "#5c87da",
      "servo",
    ),
    component(
      "ir",
      "Front IR · nominal 3.3 V I/O",
      "3V3 GND OUT",
      [0.061, 0.052, -0.089],
      "#725fc2",
    ),
    component(
      "divF",
      "Front ECHO conditioning",
      "IN OUT GND",
      [-0.04, 0.079, -0.035],
      "#cfad71",
    ),
    component(
      "divR",
      "Rear ECHO conditioning",
      "IN OUT GND",
      [0.002, 0.079, -0.035],
      "#cfad71",
    ),
    component(
      "divS",
      "Radar ECHO conditioning",
      "IN OUT GND",
      [0.04, 0.079, -0.035],
      "#cfad71",
    ),
    component(
      "battery",
      "AA source · nominal model",
      "PLUS MINUS",
      [0, 0.035, 0.035],
      "#aaa273",
      "battery",
    ),
    component(
      "fuse",
      "Motor fuse · ideal model",
      "IN OUT",
      [-0.072, 0.049, 0.07],
      "#d5ad74",
    ),
    component(
      "cutoff",
      "Motor cutoff · ideal switch",
      "IN OUT",
      [0.075, 0.065, 0.065],
      "#cf8d4b",
    ),
    component(
      "usb",
      "USB 5 V logic · ideal",
      "5V GND",
      [-0.22, 0.025, 0.04],
      "#89a9c7",
    ),
    component(
      "servoRail",
      "Regulated servo 5 V · ideal",
      "5V GND",
      [-0.07, 0.05, -0.005],
      "#748eab",
    ),
    component(
      "motorL",
      "Left BO gearmotor",
      "P N",
      [-0.063, 0.032, 0.02],
      "#dbb947",
      "motor",
    ),
    component(
      "motorR",
      "Right BO gearmotor",
      "P N",
      [0.063, 0.032, 0.02],
      "#dbb947",
      "motor",
    ),
    component(
      "led",
      "Alert LED + 1k · model interface",
      "SIG GND",
      [0.06, 0.094, -0.03],
      "#79e9b3",
      "led",
    ),
    component(
      "buzzer",
      "Buzzer + compatible driver · model",
      "3V3 GND SIG",
      [-0.058, 0.086, 0.044],
      "#26383e",
      "buzzer",
    ),
    component(
      "phone",
      "Phone camera / mic / face",
      "AUDIO CAMERA MIC DISPLAY NET",
      [0, 0.202, 0],
      "#527e82",
      "phone",
    ),
    component(
      "amp",
      "External speaker amplifier · model",
      "5V GND AUDIO SPK+ SPK-",
      [0.056, 0.075, 0.057],
      "#677ac1",
    ),
    component(
      "speaker",
      "External speaker",
      "P N",
      [0.105, 0.066, 0.029],
      "#28343c",
      "speaker",
    ),
  ];
  const wires = [];
  function wire(a, b, type = "signal", label = "") {
    wires.push({ id: "w" + wires.length, a, b, type, label });
  }
  wire("usb.5V", "esp.VIN", "power5");
  wire("usb.GND", "esp.GND", "ground");
  wire("esp.3V3", "driver.VCC", "power3");
  wire("esp.GND", "driver.GND", "ground");
  wire("battery.PLUS", "fuse.IN", "motor");
  wire("fuse.OUT", "cutoff.IN", "motor");
  wire("cutoff.OUT", "driver.VM", "motor");
  wire("battery.MINUS", "driver.GND", "ground");
  for (const n of ["AIN1", "AIN2", "PWMA", "BIN1", "BIN2", "PWMB", "STBY"])
    wire("esp.D" + GPIO[n], "driver." + n, "signal", n);
  for (const [a, b] of [
    ["AO1", "motorL.P"],
    ["AO2", "motorL.N"],
    ["BO1", "motorR.P"],
    ["BO2", "motorR.N"],
  ])
    wire("driver." + a, b, "motor");
  for (const [sensor, div, prefix] of [
    ["front", "divF", "FRONT"],
    ["rear", "divR", "REAR"],
    ["radar", "divS", "RADAR"],
  ]) {
    wire("usb.5V", sensor + ".VCC", "power5");
    wire("esp.GND", sensor + ".GND", "ground");
    wire("esp.D" + GPIO[prefix + "_TRIG"], sensor + ".TRIG");
    wire(sensor + ".ECHO", div + ".IN", "echo5");
    wire(div + ".OUT", "esp.D" + GPIO[prefix + "_ECHO"], "echo3");
    wire("esp.GND", div + ".GND", "ground");
  }
  wire("esp.3V3", "ir.3V3", "power3");
  wire("esp.GND", "ir.GND", "ground");
  wire("ir.OUT", "esp.D" + GPIO.IR, "echo3");
  wire("servoRail.5V", "servo.5V", "power5");
  wire("esp.GND", "servoRail.GND", "ground");
  wire("esp.GND", "servo.GND", "ground");
  wire("esp.D" + GPIO.SERVO, "servo.SIG");
  wire("esp.D" + GPIO.LED, "led.SIG");
  wire("esp.GND", "led.GND", "ground");
  wire("esp.3V3", "buzzer.3V3", "power3");
  wire("esp.GND", "buzzer.GND", "ground");
  wire("esp.D" + GPIO.BUZZER, "buzzer.SIG");
  wire("usb.5V", "amp.5V", "power5");
  wire("esp.GND", "amp.GND", "ground");
  wire("phone.AUDIO", "amp.AUDIO", "audio");
  wire("amp.SPK+", "speaker.P", "audio");
  wire("amp.SPK-", "speaker.N", "audio");
  const terminals = new Set(
    components.flatMap((c) => c.pins.map((p) => c.id + "." + p)),
  );
  function defaultCircuit() {
    return wires.map((w) => ({ ...w }));
  }
  function circuitCheck(net, options = {}) {
    const parent = new Map([...terminals].map((t) => [t, t]));
    const find = (t) => {
      let r = t;
      while (parent.get(r) !== r) r = parent.get(r);
      while (parent.get(t) !== t) {
        const n = parent.get(t);
        parent.set(t, r);
        t = n;
      }
      return r;
    };
    const join = (a, b) => {
      if (parent.has(a) && parent.has(b)) parent.set(find(a), find(b));
    };
    const problems = [];
    for (const w of net) {
      if (!w || !terminals.has(w.a) || !terminals.has(w.b) || w.a === w.b) {
        problems.push("Invalid endpoint");
        continue;
      }
      join(w.a, w.b);
    }
    const connected = (a, b) => find(a) === find(b);
    if (options.cutoff !== false) join("cutoff.IN", "cutoff.OUT");
    join("fuse.IN", "fuse.OUT");
    const sources = [
      ["esp.GND", 0],
      ["battery.MINUS", 0],
      ["usb.GND", 0],
      ["servoRail.GND", 0],
      ["usb.5V", 5],
      ["esp.3V3", 3.3],
      ["battery.PLUS", options.packV === 4.8 ? 4.8 : 6],
      ["servoRail.5V", 5],
      ["ir.OUT", 3.3],
      ["front.ECHO", 5],
      ["rear.ECHO", 5],
      ["radar.ECHO", 5],
    ];
    for (const [sensor, div] of [
      ["front", "divF"],
      ["rear", "divR"],
      ["radar", "divS"],
    ])
      if (
        connected(sensor + ".ECHO", div + ".IN") &&
        connected(div + ".GND", "esp.GND")
      )
        sources.push([div + ".OUT", (5 * 3.2) / 5.4]);
    const rails = new Map();
    for (const [id, v] of sources) {
      const k = find(id);
      if (rails.has(k) && Math.abs(rails.get(k) - v) > 0.15)
        problems.push("Conflicting nominal sources / short at " + id);
      else rails.set(k, v);
    }
    const voltage = (t) => (rails.has(find(t)) ? rails.get(find(t)) : null);
    for (const name of ["FRONT_ECHO", "REAR_ECHO", "RADAR_ECHO", "IR"]) {
      const v = voltage("esp.D" + GPIO[name]);
      if (v !== null && v > 3.6)
        problems.push("GPIO overvoltage at D" + GPIO[name]);
    }
    const missing = wires.filter((w) => !connected(w.a, w.b));
    for (const w of missing)
      if (!(options.cutoff === false && w.a === "cutoff.OUT"))
        problems.push("Missing " + w.a + " → " + w.b);
    const driverOut = [
      "AIN1",
      "AIN2",
      "PWMA",
      "BIN1",
      "BIN2",
      "PWMB",
      "STBY",
      "FRONT_TRIG",
      "REAR_TRIG",
      "RADAR_TRIG",
      "SERVO",
      "LED",
      "BUZZER",
    ];
    for (let i = 0; i < driverOut.length; i++)
      for (let j = i + 1; j < driverOut.length; j++)
        if (
          connected("esp.D" + GPIO[driverOut[i]], "esp.D" + GPIO[driverOut[j]])
        )
          problems.push("Independent GPIO outputs shorted");
    const required = wires.filter(
      (w) =>
        w.a.startsWith("driver.") ||
        w.b.startsWith("driver.") ||
        w.a.startsWith("motor") ||
        w.b.startsWith("motor") ||
        w.type === "motor",
    );
    const drive =
      problems.length === 0 &&
      options.cutoff !== false &&
      required.every((w) => connected(w.a, w.b));
    return {
      ok: problems.length === 0,
      drive,
      problems: [...new Set(problems)],
      voltage,
      connected,
      count: net.length,
    };
  }
  const defaultObstacles = () => [
    {
      id: "plinth",
      x: -0.55,
      z: 0.25,
      w: 0.42,
      d: 1.05,
      h: 0.24,
      color: "#788a9a",
      type: "box",
    },
    {
      id: "crate",
      x: 0.85,
      z: -0.75,
      w: 0.55,
      d: 0.45,
      h: 0.35,
      color: "#d29359",
      type: "box",
    },
    {
      id: "pillar",
      x: 0.85,
      z: 1.05,
      w: 0.3,
      d: 0.3,
      h: 0.48,
      color: "#7c8ea1",
      type: "circle",
    },
  ];
  function ray(pose, a, max, obstacles) {
    let best = max;
    const dx = Math.sin(a),
      dz = -Math.cos(a);
    const box = (minX, maxX, minZ, maxZ) => {
      let lo = 0,
        hi = max;
      for (const [o, d, l, h] of [
        [pose.x, dx, minX, maxX],
        [pose.z, dz, minZ, maxZ],
      ]) {
        if (Math.abs(d) < 1e-9) {
          if (o < l || o > h) return;
        } else {
          let t1 = (l - o) / d,
            t2 = (h - o) / d;
          if (t1 > t2) [t1, t2] = [t2, t1];
          lo = Math.max(lo, t1);
          hi = Math.min(hi, t2);
          if (lo > hi) return;
        }
      }
      if (lo >= 0) best = Math.min(best, lo);
    };
    for (const o of obstacles)
      if (o.type === "circle") {
        const ox = pose.x - o.x,
          oz = pose.z - o.z,
          b = ox * dx + oz * dz,
          c = ox * ox + oz * oz - (o.w / 2) ** 2,
          disc = b * b - c;
        if (disc >= 0) {
          const t = -b - Math.sqrt(disc);
          if (t >= 0) best = Math.min(best, t);
        }
      } else box(o.x - o.w / 2, o.x + o.w / 2, o.z - o.d / 2, o.z + o.d / 2);
    const bx = WORLD.width / 2,
      bz = WORLD.depth / 2;
    for (const [o, d, b] of [
      [pose.x, dx, bx],
      [pose.z, dz, bz],
    ])
      if (Math.abs(d) > 1e-9) {
        const t = ((d > 0 ? b : -b) - o) / d;
        if (t >= 0) best = Math.min(best, t);
      }
    return clamp(best, 0, max);
  }
  function collision(x, z, obstacles, pad = WORLD.radius) {
    if (
      Math.abs(x) > WORLD.width / 2 - pad ||
      Math.abs(z) > WORLD.depth / 2 - pad
    )
      return true;
    return obstacles.some((o) =>
      o.type === "circle"
        ? Math.hypot(x - o.x, z - o.z) < o.w / 2 + pad
        : Math.hypot(
            x - clamp(x, o.x - o.w / 2, o.x + o.w / 2),
            z - clamp(z, o.z - o.d / 2, o.z + o.d / 2),
          ) < pad,
    );
  }
  class MapGrid {
    constructor() {
      this.w = Math.round(WORLD.width / WORLD.cell);
      this.h = Math.round(WORLD.depth / WORLD.cell);
      this.data = new Int8Array(this.w * this.h);
      this.hits = new Float32Array(this.w * this.h);
    }
    cell(x, z) {
      return {
        x: clamp(Math.floor((x + WORLD.width / 2) / WORLD.cell), 0, this.w - 1),
        z: clamp(Math.floor((z + WORLD.depth / 2) / WORLD.cell), 0, this.h - 1),
      };
    }
    seed(obstacles) {
      this.data.fill(0);
      for (let z = 0; z < this.h; z++)
        for (let x = 0; x < this.w; x++) {
          const q = this.point(x, z);
          if (
            obstacles.some((o) =>
              o.type === "circle"
                ? Math.hypot(q.x - o.x, q.z - o.z) <= o.w / 2
                : Math.abs(q.x - o.x) <= o.w / 2 &&
                  Math.abs(q.z - o.z) <= o.d / 2,
            )
          )
            this.data[z * this.w + x] = 2;
        }
    }
    point(x, z) {
      return {
        x: (x + 0.5) * WORLD.cell - WORLD.width / 2,
        z: (z + 0.5) * WORLD.cell - WORLD.depth / 2,
      };
    }
    observe(origin, a, d, max) {
      const step = WORLD.cell * 0.45;
      for (let r = 0; r < d - 0.045; r += step) {
        const c = this.cell(
            origin.x + Math.sin(a) * r,
            origin.z - Math.cos(a) * r,
          ),
          i = c.z * this.w + c.x;
        if (this.data[i] !== 2) this.data[i] = 1;
      }
      if (d < max - 0.025) {
        const c = this.cell(
          origin.x + Math.sin(a) * d,
          origin.z - Math.cos(a) * d,
        );
        this.data[c.z * this.w + c.x] = 2;
      }
    }
    blocked(x, z) {
      const r = Math.ceil((WORLD.radius + 0.025) / WORLD.cell);
      if (x < r || z < r || x >= this.w - r || z >= this.h - r) return true;
      for (let dz = -r; dz <= r; dz++)
        for (let dx = -r; dx <= r; dx++)
          if (
            (dx * dx + dz * dz) * WORLD.cell * WORLD.cell <=
              (WORLD.radius + 0.025) ** 2 &&
            this.data[(z + dz) * this.w + x + dx] === 2
          )
            return true;
      return false;
    }
    plan(start, goal) {
      const s = this.cell(start.x, start.z),
        g = this.cell(goal.x, goal.z);
      if (this.blocked(g.x, g.z)) return [];
      const n = this.w * this.h,
        cost = new Float64Array(n).fill(Infinity),
        prev = new Int32Array(n).fill(-1),
        closed = new Uint8Array(n),
        heap = [];
      const push = (i, f) => {
        heap.push({ i, f });
        let at = heap.length - 1;
        while (at) {
          let p = (at - 1) >> 1;
          if (heap[p].f <= f) break;
          [heap[p], heap[at]] = [heap[at], heap[p]];
          at = p;
        }
      };
      const pop = () => {
        const a = heap[0],
          b = heap.pop();
        if (heap.length) {
          heap[0] = b;
          let k = 0;
          for (;;) {
            let c = k * 2 + 1;
            if (c >= heap.length) break;
            if (c + 1 < heap.length && heap[c + 1].f < heap[c].f) c++;
            if (heap[k].f <= heap[c].f) break;
            [heap[k], heap[c]] = [heap[c], heap[k]];
            k = c;
          }
        }
        return a;
      };
      const si = s.z * this.w + s.x,
        gi = g.z * this.w + g.x;
      cost[si] = 0;
      push(si, 0);
      while (heap.length) {
        const { i } = pop();
        if (closed[i]) continue;
        closed[i] = 1;
        if (i === gi) {
          const path = [];
          for (let j = gi; j !== si; j = prev[j]) {
            if (j < 0) return [];
            path.push(this.point(j % this.w, Math.floor(j / this.w)));
          }
          return path.reverse();
        }
        const x = i % this.w,
          z = Math.floor(i / this.w);
        for (const [dx, dz] of [
          [1, 0],
          [-1, 0],
          [0, 1],
          [0, -1],
          [1, 1],
          [1, -1],
          [-1, 1],
          [-1, -1],
        ]) {
          const nx = x + dx,
            nz = z + dz;
          if (
            this.blocked(nx, nz) ||
            (dx && dz && (this.blocked(x + dx, z) || this.blocked(x, z + dz)))
          )
            continue;
          const ni = nz * this.w + nx,
            v = cost[i] + Math.hypot(dx, dz) * (this.data[ni] === 0 ? 1.12 : 1);
          if (v < cost[ni]) {
            cost[ni] = v;
            prev[ni] = i;
            push(ni, v + Math.hypot(g.x - nx, g.z - nz));
          }
        }
      }
      return [];
    }
  }
  class Simulation {
    constructor() {
      this.reset();
    }
    reset() {
      this.time = 0;
      this.pose = { x: -1.7, z: 1.05, yaw: 0 };
      this.obstacles = defaultObstacles();
      this.circuit = defaultCircuit();
      this.cutoff = true;
      this.packV = 6;
      this.mode = "IDLE";
      this.reason = "Ready for a virtual mission";
      this.goal = null;
      this.path = [];
      this.trail = [];
      this.grid = new MapGrid();
      this.grid.seed(this.obstacles);
      this.radarAngle = 0;
      this.sensors = { front: null, rear: null, radar: null, ir: false };
      this.faults = {
        link: false,
        front: false,
        rear: false,
        radar: false,
        camera: false,
      };
      this.events = [];
      this.wheels = { left: 0, right: 0 };
      this.speed = 0;
      this.turn = 0;
      this.distance = 0;
      this.replans = 0;
      this.lastScan = -1;
      this.lastPlan = -1;
      this.collisionHeld = 0;
      this.noRouteHeld = 0;
      this.vision = { valid: false, at: 0, box: null };
      this.manual = null;
      this.manualAt = 0;
      this.latched = false;
      this.emotion = "curious";
      this.addEvent(
        "System",
        "Software prototype ready. Physical outputs do not exist.",
      );
      this.scan();
    }
    addEvent(kind, text) {
      this.events.unshift({ at: this.time, kind, text });
      this.events.length = Math.min(this.events.length, 80);
    }
    scan() {
      const electrical = circuitCheck(this.circuit, {
        cutoff: this.cutoff,
        packV: this.packV,
      });
      this.electrical = electrical;
      const live = (name) => {
        const spec = {
          front: ["divF", "FRONT"],
          rear: ["divR", "REAR"],
          radar: ["divS", "RADAR"],
        }[name];
        return (
          electrical.connected(name + ".VCC", "usb.5V") &&
          electrical.connected(name + ".GND", "esp.GND") &&
          electrical.connected(
            name + ".TRIG",
            "esp.D" + GPIO[spec[1] + "_TRIG"],
          ) &&
          electrical.connected(name + ".ECHO", spec[0] + ".IN") &&
          electrical.connected(
            spec[0] + ".OUT",
            "esp.D" + GPIO[spec[1] + "_ECHO"],
          ) &&
          electrical.connected(spec[0] + ".GND", "esp.GND") &&
          Math.abs(
            electrical.voltage("esp.D" + GPIO[spec[1] + "_ECHO"]) - 2.963,
          ) < 0.05
        );
      };
      this.radarAngle =
        electrical.connected("servo.SIG", "esp.D" + GPIO.SERVO) &&
        electrical.connected("servo.5V", "servoRail.5V")
          ? Math.sin(this.time * 1.65) * 1.15
          : 0;
      const cone = (name, a, max) => {
        if (this.faults[name] || !live(name)) return null;
        const distances = [-0.12, 0, 0.12].map((d) => {
          const range = ray(this.pose, a + d, max, this.obstacles);
          this.grid.observe(this.pose, a + d, range, max);
          return range;
        });
        return Math.min(...distances);
      };
      this.sensors.front = cone("front", this.pose.yaw, 1.6);
      this.sensors.rear = cone("rear", this.pose.yaw + Math.PI, 1.3);
      this.sensors.radar =
        this.faults.radar || !live("radar")
          ? null
          : ray(
              this.pose,
              this.pose.yaw + this.radarAngle,
              2.2,
              this.obstacles,
            );
      if (this.sensors.radar !== null)
        this.grid.observe(
          this.pose,
          this.pose.yaw + this.radarAngle,
          this.sensors.radar,
          2.2,
        );
      this.sensors.ir =
        ray(this.pose, this.pose.yaw, 0.42, this.obstacles) < 0.4;
      this.lastScan = this.time;
    }

    mission(goal, kind = "NAVIGATE") {
      if (
        this.latched ||
        !goal ||
        ![goal.x, goal.z].every(finite) ||
        Math.abs(goal.x) > 2.45 ||
        Math.abs(goal.z) > 1.65
      )
        return false;
      const c = circuitCheck(this.circuit, {
        cutoff: this.cutoff,
        packV: this.packV,
      });
      if (!c.drive || Object.values(this.faults).some(Boolean)) {
        this.stop(
          "FAULT",
          "Restore the simulated circuit/sensors and reset first",
          true,
        );
        return false;
      }
      if (collision(goal.x, goal.z, this.obstacles, 0.2)) {
        this.addEvent("Planner", "Goal overlaps an obstacle or boundary.");
        return false;
      }
      this.goal = { x: goal.x, z: goal.z };
      this.mode = kind;
      this.reason = "Planning from sensor occupancy";
      this.manual = null;
      this.replan();
      this.emotion = "focused";
      this.addEvent(
        "Mission",
        kind === "FOLLOW"
          ? "Track the coloured camera marker."
          : "Requested a virtual destination.",
      );
      return true;
    }
    replan() {
      if (!this.goal) return;
      this.path = this.grid.plan(this.pose, this.goal);
      this.lastPlan = this.time;
      this.replans++;
      if (!this.path.length) {
        this.speed = this.turn = 0;
        this.reason = "No mapped-clear route; scan/replan required";
      } else this.reason = "A* route · unknown space remains provisional";
    }
    stop(mode = "PAUSED", reason = "Stopped by operator", latch = false) {
      this.speed = this.turn = 0;
      this.manual = null;
      if (this.latched && !latch) return;
      this.mode = mode;
      this.reason = reason;
      this.manual = null;
      if (latch) this.latched = true;
      this.emotion = latch ? "alert" : "calm";
      this.addEvent(mode, reason);
    }
    resetLatch() {
      this.latched = false;
      this.goal = null;
      this.path = [];
      this.stop("IDLE", "Reset complete; a new mission is required");
    }
    command(v, w) {
      if (this.latched || !finite(v) || !finite(w)) return false;
      this.manual = { v: clamp(v, -0.28, 0.32), w: clamp(w, -1.5, 1.5) };
      this.manualAt = this.time;
      this.mode = "MANUAL";
      return true;
    }
    visionFrame(result) {
      this.vision = {
        valid: !!result?.valid,
        at: this.time,
        box: result?.box || null,
      };
    }
    step(dt) {
      dt = clamp(finite(dt) ? dt : 0, 0, 0.05);
      this.time += dt;
      if (this.time - this.lastScan >= 0.075) this.scan();
      const active = ["NAVIGATE", "FOLLOW", "MANUAL"].includes(this.mode);
      if (!active) {
        this.speed = this.turn = 0;
        return;
      }
      const circuit = circuitCheck(this.circuit, {
        cutoff: this.cutoff,
        packV: this.packV,
      });
      if (!circuit.drive) {
        this.stop(
          "FAULT",
          !this.cutoff
            ? "Motor cutoff is open"
            : "Virtual circuit check failed",
          true,
        );
        return;
      }
      if (
        this.faults.link ||
        this.sensors.front === null ||
        this.sensors.rear === null ||
        this.sensors.radar === null
      ) {
        this.stop(
          "FAULT",
          "Command link or enabled range sensor unavailable",
          true,
        );
        return;
      }
      if (
        this.mode === "FOLLOW" &&
        (this.faults.camera ||
          !this.vision.valid ||
          this.time - this.vision.at > 0.6)
      ) {
        this.stop(
          "TARGET LOST",
          "Camera target missing/stale; new request required",
          true,
        );
        return;
      }
      let v = 0,
        w = 0;
      if (this.mode === "MANUAL") {
        if (this.time - this.manualAt > 0.4) {
          this.stop("TIMEOUT", "Manual command lease expired", true);
          return;
        }
        v = this.manual?.v || 0;
        w = this.manual?.w || 0;
      } else if (this.goal) {
        if (
          Math.hypot(this.goal.x - this.pose.x, this.goal.z - this.pose.z) <
          0.14
        ) {
          this.goal = null;
          this.path = [];
          this.stop(
            "ARRIVED",
            "Virtual destination reached; position is simulated",
          );
          this.emotion = "happy";
          return;
        }
        if (this.time - this.lastPlan > 1.1) this.replan();
        this.noRouteHeld = this.path.length ? 0 : this.noRouteHeld + dt;
        if (this.noRouteHeld > 3) {
          this.stop(
            "BLOCKED",
            "No mapped-clear route; choose a new goal after reset",
            true,
          );
          return;
        }
        while (
          this.path.length &&
          Math.hypot(
            this.path[0].x - this.pose.x,
            this.path[0].z - this.pose.z,
          ) < 0.12
        )
          this.path.shift();
        const target = this.path[Math.min(2, this.path.length - 1)];
        if (target) {
          const desired = Math.atan2(
              target.x - this.pose.x,
              -(target.z - this.pose.z),
            ),
            err = angle(desired - this.pose.yaw);
          w = clamp(err * 3.2, -1.5, 1.5);
          v =
            0.34 *
            Math.max(0, Math.cos(err)) *
            (Math.abs(err) > 0.9 ? 0.15 : 1);
        }
      }
      if (v > 0 && (this.sensors.front < 0.38 || this.sensors.ir)) {
        v = 0;
        this.reason = "OBSTACLE · hold translation and rescan";
        this.emotion = "alert";
        if (this.time - this.lastPlan > 0.25) this.replan();
        if (Math.abs(w) < 0.3) w = this.radarAngle >= 0 ? -1.1 : 1.1;
      }
      if (v < 0 && this.sensors.rear < 0.38) {
        v = 0;
        this.reason = "REAR GUARD · reverse inhibited";
        this.emotion = "alert";
      }
      if (this.mode === "FOLLOW" && this.vision.valid && this.vision.box) {
        const b = this.vision.box,
          centre = (b.x + b.w / 2) / 320 - 0.5,
          bearing = Math.atan(centre * 2 * Math.tan((68 * Math.PI) / 360));
        w = clamp(w * 0.65 + bearing * 2.8 * 0.35, -1.5, 1.5);
      }
      const yaw = angle(this.pose.yaw + w * dt),
        x = this.pose.x + Math.sin(yaw) * v * dt,
        z = this.pose.z - Math.cos(yaw) * v * dt;
      if (collision(x, z, this.obstacles)) {
        v = 0;
        this.collisionHeld += dt;
        if (this.collisionHeld > 1) {
          this.stop(
            "BLOCKED",
            "Footprint guard held; reset and choose another route",
            true,
          );
          return;
        }
        this.reason = "Footprint guard · translation stopped";
        if (this.time - this.lastPlan > 0.25) this.replan();
      } else {
        this.collisionHeld = 0;
        this.distance += Math.abs(v * dt);
        this.pose.x = x;
        this.pose.z = z;
      }
      this.pose.yaw = yaw;
      this.speed = v;
      this.turn = w;
      this.wheels.left +=
        ((v - (w * WORLD.track) / 2) * dt) / WORLD.wheelRadius;
      this.wheels.right +=
        ((v + (w * WORLD.track) / 2) * dt) / WORLD.wheelRadius;
      if (
        this.trail.length === 0 ||
        Math.hypot(x - this.trail.at(-1).x, z - this.trail.at(-1).z) > 0.025
      ) {
        this.trail.push({ x: this.pose.x, z: this.pose.z });
        if (this.trail.length > 1600) this.trail.shift();
      }
    }
    export() {
      return {
        format: "prometheus-mission-studio/v1",
        obstacles: this.obstacles.map((o) => ({ ...o })),
        circuit: this.circuit.map((w) => ({ ...w })),
        packV: this.packV,
      };
    }
    import(data) {
      if (
        data?.format !== "prometheus-mission-studio/v1" ||
        !Array.isArray(data.obstacles) ||
        data.obstacles.length > 30 ||
        !Array.isArray(data.circuit) ||
        data.circuit.length > 150
      )
        throw Error("Invalid project format/size");
      const obs = data.obstacles.map((o, i) => {
        if (
          ![o.x, o.z, o.w, o.d, o.h].every(finite) ||
          Math.abs(o.x) > 2.6 ||
          Math.abs(o.z) > 1.8 ||
          o.w < 0.1 ||
          o.w > 1.5 ||
          o.d < 0.1 ||
          o.d > 1.5 ||
          o.h < 0.05 ||
          o.h > 1
        )
          throw Error("Invalid obstacle");
        return {
          id: "import" + i,
          x: o.x,
          z: o.z,
          w: o.w,
          d: o.d,
          h: o.h,
          type: o.type === "circle" ? "circle" : "box",
          color: /^#[a-f0-9]{6}$/i.test(o.color) ? o.color : "#8296a0",
        };
      });
      const net = data.circuit.map((w, i) => {
        if (!terminals.has(w.a) || !terminals.has(w.b) || w.a === w.b)
          throw Error("Invalid wire");
        return {
          id: "importw" + i,
          a: w.a,
          b: w.b,
          type: [
            "power5",
            "power3",
            "ground",
            "motor",
            "signal",
            "echo5",
            "echo3",
            "audio",
          ].includes(w.type)
            ? w.type
            : "signal",
        };
      });
      this.reset();
      this.obstacles = obs;
      this.grid.seed(obs);
      this.circuit = net;
      this.packV = data.packV === 4.8 ? 4.8 : 6;
      this.stop("IDLE", "Project imported; new mission required");
    }
  }
  function detectMarker(rgba, width, height) {
    let minX = width,
      minY = height,
      maxX = -1,
      maxY = -1,
      count = 0;
    for (let y = 0; y < height; y++)
      for (let x = 0; x < width; x++) {
        const i = (y * width + x) * 4,
          r = rgba[i],
          g = rgba[i + 1],
          b = rgba[i + 2];
        if (r > 135 && b > 110 && g < 150 && r > g * 1.4 && b > g * 1.15) {
          count++;
          minX = Math.min(minX, x);
          maxX = Math.max(maxX, x);
          minY = Math.min(minY, y);
          maxY = Math.max(maxY, y);
        }
      }
    const valid = count >= 16 && maxX - minX > 2 && maxY - minY > 2;
    return {
      valid,
      pixels: count,
      box: valid
        ? { x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1 }
        : null,
      confidence: valid
        ? Math.min(1, count / ((maxX - minX + 1) * (maxY - minY + 1)))
        : 0,
    };
  }
  const chapters = [
    {
      at: 0,
      title: "Meet KITTY",
      caption:
        "A phone becomes the face and senses. A laptop does the thinking.",
      view: "hero",
    },
    {
      at: 10,
      title: "One connected system",
      caption:
        "Camera and microphone → laptop perception + prompted brain → guarded ESP32 control.",
      view: "architecture",
    },
    {
      at: 23,
      title: "Inside the prototype",
      caption:
        "Two drive motors. Front ultrasonic + IR. Rear ultrasonic. A third ultrasonic scans on a servo.",
      view: "wiring",
    },
    {
      at: 37,
      title: "Build a local map",
      caption:
        "Range hits update an occupancy grid. The corner servo sweeps a virtual radar.",
      view: "radar",
    },
    {
      at: 48,
      title: "Plan. Move. Replan.",
      caption:
        "A* chooses a route. New obstacles stop translation while the route is reconsidered.",
      view: "mission",
    },
    {
      at: 76,
      title: "Stops are local",
      caption:
        "A lost sensor or command link stops this simulated controller. Reset alone does not restart a mission.",
      view: "safety",
    },
    {
      at: 88,
      title: "A little personality",
      caption:
        "The phone face, obstacle LED, buzzer and external speaker respond to the same state.",
      view: "face",
    },
    {
      at: 100,
      title: "Future / ground to air",
      caption:
        "A separate four-wheel concept: folding wheel/rotor pods, takeoff, flight and landing animation.",
      view: "future",
    },
    {
      at: 125,
      title: "Build the real version next",
      caption:
        "Working software prototype today. Physical sensing, drivetrain and flight validation remain future work.",
      view: "closing",
    },
  ];
  function chapterAt(t) {
    return chapters.findLast((c) => t >= c.at) || chapters[0];
  }
  function futurePose(t) {
    const u = Math.max(0, t - 100),
      fold = clamp((u - 5) / 4, 0, 1) * (1 - clamp(u - 24, 0, 1)),
      lift = clamp((u - 10) / 3, 0, 1) * clamp((24 - u) / 3, 0, 1);
    return {
      fold,
      altitude: lift * 0.95,
      rotor: fold * clamp((u - 8) / 2, 0, 1) * clamp((24 - u) / 2, 0, 1),
      x:
        u < 5
          ? -1 + u * 0.2
          : Math.sin(Math.max(0, u - 13) * 0.3) * 0.65 * lift,
      z: Math.cos(Math.max(0, u - 13) * 0.3) * 0.35 * lift,
      yaw: u < 5 ? Math.PI / 2 : Math.max(0, u - 13) * 0.15 * lift,
      wheel: u < 5 ? u * 4 : 20,
    };
  }
  function isStopRequest(text) {
    return /^\s*(?:please\s+)?(?:stop|halt|emergency(?:\s+stop)?)\b/i.test(
      String(text),
    );
  }
  function offlineReply(text, sim) {
    const s = String(text).slice(0, 1500).toLowerCase();
    let intent = "explain",
      reply =
        "I’m KITTY, Team Prometheus’s software prototype. My sensor readings and movement here are simulated.";
    if (isStopRequest(s)) {
      intent = "stop";
      reply = "Stop requested. A new deliberate mission is needed after reset.";
    } else if (
      /^\s*(?:please\s+)?(?:go|return|move|drive|head|take)\b/.test(s) &&
      /\b(?:home|base)\b/.test(s)
    ) {
      intent = "goal_beta";
      reply =
        "I can request the virtual home. The planner and stop guard still own motion.";
    } else if (
      /^\s*(?:please\s+)?(?:go|navigate|move|drive|head|take)\b/.test(s)
    ) {
      intent = "goal_alpha";
      reply =
        "I can request the magenta destination. The deterministic planner and stop guard decide whether this simulation can move.";
    } else if (/radar|scan/.test(s)) {
      intent = "radar";
      reply =
        "The corner ultrasonic is scanning on a servo. Three range sensors are shown virtually; the third sensor and mount are planned additions.";
    } else if (/fly|drone|future/.test(s)) {
      intent = "future";
      reply =
        "Opening the future concept. This is a folding and flight animation, not a validated flying airframe.";
    } else if (
      /\b(?:hello|hi|hey|made|team|good morning|good afternoon|good evening)\b/.test(
        s,
      )
    ) {
      intent = "hello";
      reply =
        "Hi! I’m KITTY, built by Team Prometheus at KITTY CORP. My dramatic entrance is limited to a sensible speed.";
    } else if (/see|sensor|status/.test(s)) {
      reply = `Virtual camera: ${sim.faults.camera || sim.time - sim.vision.at > 0.6 ? "unavailable or stale" : sim.vision.valid ? "colour marker detected" : "no supported marker"}. Simulation mode: ${sim.mode}. Front range ${sim.sensors.front === null ? "unavailable" : sim.sensors.front.toFixed(2) + " m"}. ${sim.reason}.`;
    }
    return { intent, reply, source: "Offline demo rules · no language model" };
  }
  return {
    WORLD,
    GPIO,
    components,
    terminals,
    wires,
    defaultCircuit,
    circuitCheck,
    defaultObstacles,
    ray,
    collision,
    MapGrid,
    Simulation,
    detectMarker,
    chapters,
    chapterAt,
    futurePose,
    offlineReply,
    isStopRequest,
    clamp,
    angle,
  };
});
