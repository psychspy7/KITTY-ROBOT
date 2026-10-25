/* 3D Mission Studio. Every movement and electronic signal is virtual. */
(() => {
  "use strict";
  const K = window.PrometheusSim,
    $ = (id) => document.getElementById(id),
    model = JSON.parse($("model-data").textContent),
    sim = new K.Simulation();
  let renderer,
    scene,
    camera,
    orbit,
    robot,
    arena,
    bench,
    laptop,
    parts = new Map(),
    bodyMeshes = [],
    wheels = [],
    facePlane,
    radarGroup,
    ledMesh,
    wireGroup,
    rayGroup,
    pathLine,
    trailLine,
    obstacleGroup,
    futureGroup,
    futurePods = [],
    futurePhone,
    gridHelper,
    dataGroup,
    dataCurves = [];
  let activeModelAbort = null,
    activeRecognition = null;
  let captureMode = false,
    wiresDirty = false;
  let ready = false,
    mode = "hero",
    cameraMode = "hero",
    explode = false,
    wiresVisible = true,
    xray = false,
    selected = "esp",
    currentFrame = 0,
    lastTime = 0,
    lastUI = 0,
    lastVision = 0,
    lastMap = 0,
    fps = 0,
    frames = 0,
    frameStart = 0,
    quality = 1.25,
    autoQuality = true,
    slowFrames = 0,
    benchLabel;
  let demoPlaying = false,
    demoTime = 0,
    demoChapter = -1,
    demoEvents = new Set(),
    futureTime = 0,
    futurePlaying = false,
    manual = null,
    keys = new Set(),
    lastFault = false,
    programGeneration = 0,
    chatGeneration = 0,
    api = null;
  let recorder = null,
    recordChunks = [],
    recordStarted = 0,
    audioContext = null,
    audioEnabled = false,
    lastBeep = 0,
    narration = false,
    lastSpoken = -1,
    seeking = false;
  const viewCanvas = $("viewport"),
    stage = $("stage"),
    faceCanvas = $("face"),
    faceCtx = faceCanvas.getContext("2d"),
    cameraCanvas = $("camera-feed"),
    cameraCtx = cameraCanvas.getContext("2d"),
    mapCanvas = $("map"),
    mapCtx = mapCanvas.getContext("2d"),
    captureCanvas = $("recording-canvas"),
    captureCtx = captureCanvas.getContext("2d");
  const faceTexture = new THREE.CanvasTexture(faceCanvas),
    eyeCamera = new THREE.PerspectiveCamera(68, 16 / 9, 0.015, 15),
    visionTarget = new THREE.WebGLRenderTarget(320, 180, {
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
    }),
    visionPixels = new Uint8Array(320 * 180 * 4),
    visionImage = cameraCtx.createImageData(320, 180);
  const marker = { x: 1.8, z: -1.1 },
    labelItems = [],
    pinWorld = new Map(),
    partMeshes = [],
    wireObjects = [];
  let markerMesh, markerLight;
  const titles = {
    hero: [
      "VISION-BASED ASSISTANT / VIRTUAL PROTOTYPE",
      "Small robot.<br><em>Connected mind.</em>",
      "Phone senses. Laptop thinks. KITTY responds.",
    ],
    mission: [
      "SENSE → MAP → PLAN → MOVE",
      "A destination.<br><em>A considered route.</em>",
      "A known test arena, synthetic range observations and a guarded planner.",
    ],
    wiring: [
      "COMPONENTS / SIGNALS / POWER",
      "Follow the signal.<br><em>Inside KITTY.</em>",
      "An editable nominal circuit, with a third ultrasonic and servo shown as planned additions.",
    ],
    architecture: [
      "PHONE → LAPTOP → ESP32",
      "The brain lives<br><em>on the laptop.</em>",
      "Perception, mapping and conversation stay separate from the local stop guard.",
    ],
    radar: [
      "ULTRASONIC + IR / OCCUPANCY",
      "Scan the room.<br><em>Read the space.</em>",
      "Front and rear ranging, close IR detection and a sweeping corner sensor.",
    ],
    safety: [
      "DETERMINISTIC GUARD / FAULT LAB",
      "When uncertain,<br><em>KITTY stops.</em>",
      "Fault restoration requires reset and a new mission request.",
    ],
    face: [
      "PHONE DISPLAY / SOUND / SIGNALS",
      "A useful mind.<br><em>A little personality.</em>",
      "Expressions, LED and buzzer share the same controller state.",
    ],
    future: [
      "FUTURE STUDY / AEROKITTY",
      "Grounded today.<br><em>Imagine tomorrow.</em>",
      "Four wheels. Folding wheel/rotor pods. A separate flight concept animation.",
    ],
    closing: [
      "TEAM PROMETHEUS / KITTY CORP",
      "A prototype today.<br><em>A platform tomorrow.</em>",
      "This presentation is a software simulation. Physical validation is the next milestone.",
    ],
  };
  function toast(text) {
    $("toast").textContent = text;
    $("toast").classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => $("toast").classList.remove("show"), 3600);
  }
  function download(data, name, type) {
    const a = document.createElement("a"),
      url = URL.createObjectURL(new Blob([data], { type }));
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }
  function mat(color, extra = {}) {
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.55,
      metalness: 0.18,
      ...extra,
    });
  }
  function box(w, h, d, color, x = 0, y = 0, z = 0, parent = null, extra = {}) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(color, extra));
    m.position.set(x, y, z);
    m.castShadow = true;
    m.receiveShadow = true;
    if (parent) parent.add(m);
    return m;
  }
  function cylinder(r, h, color, x, y, z, parent, segments = 24) {
    const m = new THREE.Mesh(
      new THREE.CylinderGeometry(r, r, h, segments),
      mat(color),
    );
    m.position.set(x, y, z);
    m.castShadow = true;
    if (parent) parent.add(m);
    return m;
  }
  function disposeGroup(group) {
    while (group.children.length) {
      const c = group.children[0];
      group.remove(c);
      c.traverse((o) => {
        o.geometry?.dispose();
        if (o.material) {
          for (const m of Array.isArray(o.material) ? o.material : [o.material])
            m.dispose();
        }
      });
    }
  }
  function line(points, color, parent, width = 1) {
    const g = new THREE.BufferGeometry().setFromPoints(points),
      m = new THREE.Line(
        g,
        new THREE.LineBasicMaterial({
          color,
          transparent: true,
          opacity: 0.8,
          linewidth: width,
        }),
      );
    parent.add(m);
    return m;
  }
  function rounded(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
  }
  function textSprite(text, color = "#d9e8e4", scale = 0.22) {
    const c = document.createElement("canvas");
    c.width = 512;
    c.height = 128;
    const x = c.getContext("2d");
    x.font = "bold 44px Arial";
    x.textAlign = "center";
    x.fillStyle = color;
    x.fillText(text, 256, 82);
    const t = new THREE.CanvasTexture(c),
      s = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: t,
          transparent: true,
          depthWrite: false,
        }),
      );
    s.scale.set(scale, scale / 4, 1);
    return s;
  }
  function geometry(item) {
    const raw = atob(item.mesh),
      bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    const v = new DataView(bytes.buffer),
      n = v.getUint32(80, true),
      p = new Float32Array(n * 9);
    for (let i = 0; i < n; i++)
      for (let j = 0; j < 9; j++)
        p[i * 9 + j] = v.getFloat32(84 + i * 50 + 12 + j * 4, true);
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(p, 3));
    g.applyMatrix4(new THREE.Matrix4().fromArray(item.pose.flat()).transpose());
    for (let i = 0; i < p.length; i += 9) {
      for (let j = 0; j < 3; j++) {
        let k = i + j * 3,
          t = p[k + 1];
        p[k + 1] = p[k + 2];
        p[k + 2] = t;
      }
      for (let j = 0; j < 3; j++) {
        let t = p[i + 3 + j];
        p[i + 3 + j] = p[i + 6 + j];
        p[i + 6 + j] = t;
      }
    }
    g.scale(0.001, 0.001, 0.001);
    g.computeVertexNormals();
    g.computeBoundingBox();
    return g;
  }
  function part(id, title, position) {
    let p = parts.get(id);
    if (p) return p;
    const group = new THREE.Group();
    robot.add(group);
    p = {
      id,
      title,
      group,
      base: new THREE.Vector3(...position),
      objects: [],
      pins: new Map(),
      attached: true,
    };
    group.position.copy(p.base);
    parts.set(id, p);
    return p;
  }
  function registerMesh(p, m) {
    p.group.add(m);
    p.objects.push(m);
    m.userData.part = p.id;
    partMeshes.push(m);
    return m;
  }
  function addLabel(p) {
    const el = document.createElement("button");
    el.className = "scene-label";
    el.textContent = p.title;
    el.onclick = () => selectPart(p.id);
    $("labels").append(el);
    labelItems.push({ p, el });
  }
  function buildRobot() {
    robot = new THREE.Group();
    scene.add(robot);
    for (const item of model.parts) {
      if (
        item.id.includes("display_graphic") ||
        item.id.includes("AA_holder") ||
        item.optional
      )
        continue;
      let id = item.id;
      if (id.includes("motor_envelope"))
        id = id.endsWith("-1") ? "motorL" : "motorR";
      else if (id.includes("rear_sonar")) id = "rear";
      else if (id.includes("sonar_can")) id = "front";
      else if (id.includes("phone_case")) id = "phone";
      const p = part(id, item.title, [0, 0, 0]),
        g = geometry(item),
        m = new THREE.Mesh(g, mat(item.color));
      m.castShadow = true;
      m.receiveShadow = true;
      registerMesh(p, m);
      if (item.kind === "printed") bodyMeshes.push(m);
      if (item.id.includes("wheel_envelope")) {
        const b = g.boundingBox,
          c = b.getCenter(new THREE.Vector3());
        g.translate(-c.x, -c.y, -c.z);
        m.position.copy(c);
        wheels.push(m);
      }
    }
    for (const c of K.components) {
      let p = parts.get(c.id);
      if (!p) {
        p = part(c.id, c.title, c.pos);
        if (c.kind === "sonar") {
          registerMesh(p, box(0.045, 0.02, 0.002, c.color));
          for (const x of [-0.013, 0.013]) {
            const m = cylinder(0.008, 0.012, "#a9c3c8", x, 0, -0.006, null, 24);
            m.rotation.x = Math.PI / 2;
            registerMesh(p, m);
          }
        } else if (c.kind === "battery") {
          registerMesh(p, box(0.065, 0.017, 0.058, "#2c3842"));
          for (const x of [-0.022, -0.007, 0.007, 0.022]) {
            const m = cylinder(
              0.0068,
              0.048,
              x < 0 ? "#b3b5ad" : "#c6aa70",
              x,
              0.01,
              0,
              null,
              16,
            );
            m.rotation.x = Math.PI / 2;
            registerMesh(p, m);
          }
        } else if (c.kind === "speaker") {
          const m = cylinder(0.016, 0.014, "#182b33", 0, 0, 0, null, 28);
          m.rotation.x = Math.PI / 2;
          registerMesh(p, m);
          const ring = new THREE.Mesh(
            new THREE.TorusGeometry(0.013, 0.0015, 6, 30),
            mat("#a2b6ba"),
          );
          ring.position.z = -0.009;
          registerMesh(p, ring);
        } else if (c.kind === "led") {
          ledMesh = new THREE.Mesh(
            new THREE.SphereGeometry(0.004, 12, 8),
            mat("#79e9b3", { emissive: "#5cdda7", emissiveIntensity: 0.5 }),
          );
          registerMesh(p, ledMesh);
        } else {
          const isEsp = c.id === "esp",
            dims = isEsp
              ? [0.028, 0.008, 0.052]
              : c.kind === "servo"
                ? [0.023, 0.024, 0.014]
                : [0.022, 0.005, 0.025];
          registerMesh(p, box(...dims, c.color));
          if (isEsp) {
            registerMesh(
              p,
              box(0.017, 0.003, 0.019, "#c6d0cf", 0, 0.005, -0.009),
            );
            registerMesh(
              p,
              box(0.012, 0.002, 0.014, "#171e27", 0, 0.005, 0.015),
            );
          } else if (c.kind === "servo")
            registerMesh(p, box(0.027, 0.002, 0.005, "#ebeee9", 0, 0.014, 0));
        }
      }
      p.title = c.title;
      const half = Math.ceil(c.pins.length / 2);
      c.pins.forEach((name, i) => {
        const pos = new THREE.Vector3(
          i < half ? -0.016 : 0.016,
          0.008,
          ((i % half) - (half - 1) / 2) * 0.0045,
        );
        if (c.kind === "sonar") pos.set((i - 1.5) * 0.005, 0.012, 0.003);
        if (p.base.length() === 0) pos.add(new THREE.Vector3(...c.pos));
        const pin = new THREE.Mesh(
          new THREE.SphereGeometry(0.0015, 6, 4),
          new THREE.MeshBasicMaterial({
            color: name === "GND" || name === "MINUS" ? "#a6b8bd" : "#d5b973",
          }),
        );
        pin.position.copy(pos);
        p.group.add(pin);
        p.pins.set(c.id + "." + name, pin);
        pin.userData.pin = c.id + "." + name;
        pin.userData.part = c.id;
        partMeshes.push(pin);
      });
      addLabel(p);
    }
    // V7 body CAD is retained; added sensor/servo/IR/speaker geometry is illustrative.
    radarGroup = parts.get("radar").group;
    facePlane = new THREE.Mesh(
      new THREE.PlaneGeometry(0.152, 0.067),
      new THREE.MeshBasicMaterial({ map: faceTexture, side: THREE.DoubleSide }),
    );
    facePlane.position.set(0, 0.2028, -0.0052);
    facePlane.rotation.y = Math.PI;
    robot.add(facePlane);
    const frontBoard = parts.get("front");
    if (frontBoard) {
      const mesh = box(0.045, 0.02, 0.0016, "#287f76", 0, 0.043, -0.08);
      registerMesh(frontBoard, mesh);
    }
    for (const p of parts.values())
      if (p.base.length() === 0) {
        const b = new THREE.Box3().setFromObject(p.group);
        if (!b.isEmpty()) {
          const c = b.getCenter(new THREE.Vector3());
          for (const child of p.group.children) child.position.sub(c);
          p.base.copy(c);
          p.group.position.copy(c);
        }
      }
    wireGroup = new THREE.Group();
    robot.add(wireGroup);
    rebuildWires();
  }
  function buildArena() {
    arena = new THREE.Group();
    scene.add(arena);
    const floor = box(
      K.WORLD.width + 0.35,
      0.06,
      K.WORLD.depth + 0.35,
      "#24333c",
      0,
      -0.055,
      0,
      arena,
      { roughness: 0.86, metalness: 0.12 },
    );
    floor.receiveShadow = true;
    gridHelper = new THREE.GridHelper(6, 60, "#45615c", "#31484d");
    gridHelper.position.y = -0.022;
    arena.add(gridHelper);
    for (const z of [-2.03, 2.03])
      box(5.75, 0.035, 0.018, "#8fa89a", 0, 0.005, z, arena, {
        emissive: "#607e6b",
        emissiveIntensity: 0.15,
      });
    for (const x of [-2.83, 2.83])
      box(0.018, 0.035, 4.05, "#8fa89a", x, 0.005, 0, arena);
    for (let i = 0; i < 8; i++) {
      const t = textSprite(
        i % 2 ? "PROMETHEUS" : "KITTY CORP",
        "#7c9a98",
        0.65,
      );
      t.position.set(-2.3 + i * 0.65, 0.001, 2.16);
      t.material.opacity = 0.5;
      arena.add(t);
    }
    obstacleGroup = new THREE.Group();
    arena.add(obstacleGroup);
    rebuildObstacles();
    markerMesh = new THREE.Group();
    arena.add(markerMesh);
    markerMesh.position.set(marker.x, 0, marker.z);
    const disk = cylinder(0.12, 0.012, "#e46fac", 0, 0.006, 0, markerMesh, 48);
    disk.material.emissive = new THREE.Color("#b93e87");
    disk.material.emissiveIntensity = 0.35;
    const stem = cylinder(0.015, 0.32, "#f85fd0", 0, 0.17, 0, markerMesh, 16);
    stem.material.emissive = new THREE.Color("#fa42bf");
    stem.material.emissiveIntensity = 0.9;
    const ball = new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.085, 1),
      new THREE.MeshBasicMaterial({ color: "#ff57cf" }),
    );
    ball.position.y = 0.38;
    markerMesh.add(ball);
    markerLight = textSprite("GOAL / COLOUR MARKER", "#e6a6d1", 0.6);
    markerLight.position.y = 0.55;
    markerMesh.add(markerLight);
    rayGroup = new THREE.Group();
    scene.add(rayGroup);
    pathLine = line([], 0xa89ce9, scene);
    trailLine = line([], 0x84bdad, scene);
  }
  function rebuildObstacles() {
    if (!obstacleGroup) return;
    disposeGroup(obstacleGroup);
    for (const o of sim.obstacles) {
      let m;
      if (o.type === "circle")
        m = cylinder(
          o.w / 2,
          o.h,
          o.color,
          o.x,
          o.h / 2,
          o.z,
          obstacleGroup,
          32,
        );
      else m = box(o.w, o.h, o.d, o.color, o.x, o.h / 2, o.z, obstacleGroup);
      m.userData.obstacle = o.id;
      if (o.type !== "circle") {
        for (const z of [-1, 1])
          box(
            o.w * 0.85,
            0.012,
            0.016,
            "#d9bb86",
            o.x,
            o.h * 0.55,
            o.z + z * (o.d / 2 + 0.002),
            obstacleGroup,
          );
      }
    }
  }
  function buildBench() {
    bench = new THREE.Group();
    scene.add(bench);
    const platform = cylinder(0.44, 0.035, "#293c43", 0, -0.022, 0, bench, 80);
    platform.receiveShadow = true;
    for (const r of [0.33, 0.38, 0.43]) {
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(r, 0.0009, 4, 100),
        new THREE.MeshBasicMaterial({
          color: "#5d9280",
          transparent: true,
          opacity: 0.55,
        }),
      );
      ring.rotation.x = Math.PI / 2;
      ring.position.y = -0.003;
      bench.add(ring);
    }
    laptop = new THREE.Group();
    bench.add(laptop);
    laptop.position.set(0.38, 0.012, 0.2);
    laptop.rotation.y = -0.38;
    box(0.33, 0.011, 0.22, "#435765", 0, 0, 0, laptop);
    const lid = new THREE.Group();
    lid.position.set(0, 0.012, 0.104);
    laptop.add(lid);
    lid.rotation.x = -0.16;
    box(0.33, 0.218, 0.009, "#31444f", 0, 0.109, 0, lid);
    const display = document.createElement("canvas");
    display.width = 512;
    display.height = 320;
    const ctx = display.getContext("2d");
    ctx.fillStyle = "#10212c";
    ctx.fillRect(0, 0, 512, 320);
    ctx.fillStyle = "#91e2c5";
    ctx.font = "bold 28px Arial";
    ctx.fillText("KITTY / LAPTOP BRAIN", 30, 52);
    ctx.font = "16px Arial";
    for (const [i, t] of [
      "CAMERA + MICROPHONE",
      "↓ perception / occupancy map",
      "↓ bounded intent / A* planner",
      "↓ deterministic stop guard",
      "ESP32 → MOTOR DRIVER",
    ].entries())
      ctx.fillText(t, 30, 100 + i * 38);
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(0.304, 0.189),
      new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(display) }),
    );
    screen.position.set(0, 0.111, -0.005);
    screen.rotation.y = Math.PI;
    lid.add(screen);
    for (let r = 0; r < 4; r++)
      for (let c = 0; c < 12; c++)
        box(
          0.019,
          0.001,
          0.018,
          "#26373f",
          -0.124 + c * 0.022,
          0.006,
          -0.062 + r * 0.024,
          laptop,
        );
    box(0.085, 0.001, 0.035, "#5a6d77", 0, 0.006, -0.094, laptop);
    const lb = textSprite("LAPTOP / PERCEPTION + BRAIN", "#a4dccc", 0.32);
    lb.position.set(0.38, 0.3, 0.19);
    bench.add(lb);
    benchLabel = lb;
    dataGroup = new THREE.Group();
    bench.add(dataGroup);
    for (const points of [
      [
        [0, 0.21, -0.01],
        [0.2, 0.39, 0.03],
        [0.38, 0.16, 0.17],
      ],
      [
        [0.38, 0.14, 0.17],
        [0.2, 0.23, -0.02],
        [-0.038, 0.07, 0.035],
      ],
    ]) {
      const curve = new THREE.QuadraticBezierCurve3(
        ...points.map((p) => new THREE.Vector3(...p)),
      );
      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 30, 0.0012, 5, false),
        new THREE.MeshBasicMaterial({
          color: "#8be4c7",
          transparent: true,
          opacity: 0.7,
        }),
      );
      dataGroup.add(tube);
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.004, 10, 8),
        new THREE.MeshBasicMaterial({ color: "#d2ffe8" }),
      );
      dataGroup.add(dot);
      dataCurves.push({ curve, dot });
    }
  }
  function buildFuture() {
    futureGroup = new THREE.Group();
    scene.add(futureGroup);
    const core = box(0.24, 0.085, 0.28, "#e7e6db", 0, 0.11, 0, futureGroup, {
      metalness: 0.27,
    });
    box(0.15, 0.016, 0.2, "#c18650", 0, 0.159, 0, futureGroup);
    const f = textSprite("PROMETHEUS", "#273d40", 0.16);
    f.position.set(0, 0.1, -0.145);
    futureGroup.add(f);
    futurePhone = new THREE.Group();
    futureGroup.add(futurePhone);
    futurePhone.position.set(0, 0.18, 0);
    box(0.17, 0.075, 0.012, "#152b32", 0, 0.038, 0, futurePhone);
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(0.156, 0.064),
      new THREE.MeshBasicMaterial({ map: faceTexture, side: THREE.DoubleSide }),
    );
    screen.position.set(0, 0.038, -0.0065);
    screen.rotation.y = Math.PI;
    futurePhone.add(screen);
    for (const sx of [-1, 1])
      for (const sz of [-1, 1]) {
        const arm = new THREE.Group();
        futureGroup.add(arm);
        const shaft = box(0.18, 0.015, 0.027, "#667e89", sx * 0.09, 0, 0, arm);
        const pod = new THREE.Group();
        arm.add(pod);
        pod.position.x = sx * 0.18;
        const tyre = new THREE.Mesh(
          new THREE.TorusGeometry(0.052, 0.009, 10, 40),
          mat("#263b43"),
        );
        pod.add(tyre);
        const guard = new THREE.Mesh(
          new THREE.TorusGeometry(0.047, 0.003, 8, 40),
          mat("#a3d3c2"),
        );
        pod.add(guard);
        const hub = cylinder(0.012, 0.023, "#6c8d8e", 0, 0, 0, pod, 20);
        hub.rotation.x = Math.PI / 2;
        const prop = new THREE.Group();
        pod.add(prop);
        for (let a = 0; a < 3; a++) {
          const blade = box(0.008, 0.083, 0.0018, "#8cc8bb", 0, 0, 0, prop);
          blade.rotation.z = (a * Math.PI * 2) / 3;
        }
        const glow = new THREE.Mesh(
          new THREE.TorusGeometry(0.039, 0.0013, 4, 32),
          new THREE.MeshBasicMaterial({
            color: "#81efd0",
            transparent: true,
            opacity: 0.5,
          }),
        );
        pod.add(glow);
        futurePods.push({ arm, pod, prop, sx, sz, glow });
      }
  }
  function init3D() {
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: viewCanvas,
        antialias: true,
        alpha: false,
        preserveDrawingBuffer: true,
        powerPreference: "high-performance",
      });
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, quality));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      faceTexture.colorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.18;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      scene = new THREE.Scene();
      scene.background = new THREE.Color("#17242d");
      scene.fog = new THREE.Fog("#17242d", 3.8, 12);
      camera = new THREE.PerspectiveCamera(42, 1, 0.01, 35);
      camera.position.set(0.7, 0.43, -0.86);
      orbit = new OrbitControls(camera, viewCanvas);
      orbit.target.set(0, 0.12, 0);
      orbit.enableDamping = true;
      orbit.dampingFactor = 0.07;
      orbit.minDistance = 0.28;
      orbit.maxDistance = 9;
      orbit.maxPolarAngle = Math.PI * 0.49;
      orbit.addEventListener("start", () => {
        cameraMode = "orbit";
      });
      scene.add(new THREE.HemisphereLight("#d5f5ee", "#26333f", 1.5));
      const key = new THREE.DirectionalLight("#fff1da", 2.5);
      key.position.set(-2, 4, -3);
      key.castShadow = true;
      key.shadow.mapSize.set(512, 512);
      key.shadow.camera.left = -3;
      key.shadow.camera.right = 3;
      key.shadow.camera.top = 3;
      key.shadow.camera.bottom = -3;
      key.shadow.bias = -0.0004;
      scene.add(key);
      const fill = new THREE.DirectionalLight("#8cbbff", 1.1);
      fill.position.set(3, 2, 2);
      scene.add(fill);
      const rim = new THREE.PointLight("#73e1bf", 0.7, 3);
      rim.position.set(0.2, 0.6, 0.4);
      scene.add(rim);
      buildRobot();
      buildArena();
      buildBench();
      buildFuture();
      ready = true;
      stage.classList.add("ready");
      $("graphics-error").hidden = true;
      resize();
      setMode(mode, false);
      viewCanvas.addEventListener("webglcontextlost", graphicsLost);
      viewCanvas.addEventListener("webglcontextrestored", () => {
        toast(
          "Graphics context restored. Use Retry graphics to rebuild the studio.",
        );
      });
    } catch (e) {
      ready = false;
      stage.classList.remove("ready");
      $("graphics-error").hidden = false;
      $("graphics-message").textContent = "WebGL could not start: " + e.message;
      console.warn("Graphics fallback", e.message);
    }
  }
  function graphicsLost(e) {
    e?.preventDefault();
    if (!ready) return;
    invalidatePending();
    ready = false;
    demoPlaying = false;
    futurePlaying = false;
    releaseManual();
    sim.stop("PAUSED", "Graphics lost; explicit restart required");
    stage.classList.remove("ready");
    $("graphics-error").hidden = false;
    $("graphics-message").textContent =
      "Graphics context lost. Stop/recording cleanup is active; retry to rebuild the scene.";
    stopRecording();
  }
  function resize() {
    if (!renderer || !camera) return;
    const w = stage.clientWidth,
      h = stage.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  function resetDerivedState() {
    lastMap = lastVision = lastBeep = -Infinity;
    lastSpoken = -1;
    syncAttachmentControls();
  }
  function syncAttachmentControls() {
    for (const row of document.querySelectorAll(".component-item")) {
      const p = parts.get(row.dataset.part);
      if (p)
        row.querySelector("button:last-child").textContent = p.attached
          ? "Detach"
          : "Attach";
    }
  }
  function invalidatePending() {
    programGeneration++;
    seeking = false;
    captureMode = false;
    chatGeneration++;
    activeModelAbort?.abort();
    activeModelAbort = null;
    if (activeRecognition) {
      const r = activeRecognition;
      activeRecognition = null;
      try {
        r.abort();
      } catch {}
    }
    $("send-chat").setAttribute("aria-busy", "false");
    $("send-chat").disabled = false;
  }
  function setMode(next, user = true) {
    if (!titles[next]) next = "hero";
    mode = next;
    if (user) {
      invalidatePending();
      demoPlaying = false;
      futurePlaying = false;
      releaseManual();
      sim.stop("PAUSED", "Workspace changed; request a mission to continue");
    }
    const t = titles[next];
    $("eyebrow").textContent = t[0];
    $("scene-title").innerHTML = t[1];
    $("scene-copy").textContent = t[2];
    $("scope-label").textContent =
      next === "future" ? "FUTURE CONCEPT" : "SIMULATION";
    $("view-label").textContent =
      next === "future"
        ? "FOLDING / FLIGHT ANIMATION · NO AERODYNAMIC VALIDATION"
        : next === "wiring"
          ? "SIMULATION PIN PRESET · PHYSICAL WIRING NOT RELEASED"
          : "V7.1 BODY + PLANNED SENSOR ADDITIONS";
    document
      .querySelectorAll("[data-mode]")
      .forEach((b) =>
        b.classList.toggle(
          "active",
          b.dataset.mode === next ||
            (b.dataset.mode === "mission" &&
              ["radar", "safety"].includes(next)) ||
            (b.dataset.mode === "hero" && ["face", "closing"].includes(next)),
        ),
      );
    $("wiring-panel").hidden = next !== "wiring";
    $("architecture-panel").hidden = next !== "architecture";
    $("future-panel").hidden = next !== "future";
    $("mission-panel").hidden = ["wiring", "architecture", "future"].includes(
      next,
    );
    document.querySelector(".console").scrollTop = 0;
    $("camera-heading").textContent =
      next === "future" ? "CONCEPT / TRANSFORMATION" : "PHONE CAMERA → LAPTOP";
    $("camera-source").textContent =
      next === "future" ? "ANIMATION" : "SYNTHETIC RGB";
    $("map-mode").textContent =
      next === "future" ? "CONCEPT TRAJECTORY" : "ARENA PRIOR + RANGE HITS";
    $("fault-panel").hidden =
      next === "future" || next === "wiring" || next === "architecture";
    if (ready) {
      const lab = [
        "hero",
        "wiring",
        "architecture",
        "face",
        "closing",
      ].includes(next);
      bench.visible = lab;
      arena.visible = !lab;
      robot.visible = next !== "future";
      futureGroup.visible = next === "future";
      laptop.visible = next === "architecture";
      if (benchLabel) benchLabel.visible = false;
      if (dataGroup) dataGroup.visible = next === "architecture";
      obstacleGroup.visible = next !== "future";
      markerMesh.visible = next !== "future";
      $("console")?.scrollTo(0, 0);
      wireGroup.visible = next === "wiring" && wiresVisible;
      rayGroup.visible = !lab && next !== "future" && $("show-sensors").checked;
      pathLine.visible = !lab && next !== "future";
      trailLine.visible = pathLine.visible;
      cameraMode =
        next === "mission" || next === "radar" || next === "safety"
          ? "follow"
          : next === "architecture"
            ? "architecture"
            : next === "future"
              ? "future"
              : "hero";
    }
    refresh();
  }
  function selectPart(id) {
    selected = id;
    for (const p of parts.values())
      for (const m of p.objects)
        if (m.material?.emissive) {
          m.material.emissive.set(p.id === id ? "#193a31" : "#000000");
          m.material.emissiveIntensity = p.id === id ? 0.4 : 0;
        }
    labelItems.forEach((l) => l.el.classList.toggle("selected", l.p.id === id));
    $("wire-a").value =
      [...K.terminals].find((t) => t.startsWith(id + ".")) || $("wire-a").value;
    toast(parts.get(id)?.title || id);
  }
  function rebuildWires() {
    if (!wireGroup) return;
    disposeGroup(wireGroup);
    wireObjects.length = 0;
    const color = {
      power5: "#f2ad7e",
      power3: "#e6d28a",
      ground: "#748d9b",
      motor: "#d688ab",
      signal: "#87e5c8",
      echo5: "#ef8783",
      echo3: "#9ecbe8",
      audio: "#ae9dde",
    };
    for (const w of sim.circuit) {
      const pa = endpointPosition(w.a),
        pb = endpointPosition(w.b);
      if (!pa || !pb) continue;
      const mid = pa.clone().lerp(pb, 0.5);
      mid.y =
        Math.max(pa.y, pb.y) + 0.025 + Math.min(0.05, pa.distanceTo(pb) * 0.16);
      const curve = new THREE.QuadraticBezierCurve3(pa, mid, pb),
        m = new THREE.Mesh(
          new THREE.TubeGeometry(curve, 14, 0.00075, 4, false),
          new THREE.MeshBasicMaterial({
            color: color[w.type] || color.signal,
            transparent: true,
            opacity: 0.86,
          }),
        );
      wireGroup.add(m);
      m.userData.wire = w.id;
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.0016, 6, 4),
        new THREE.MeshBasicMaterial({ color: color[w.type] || color.signal }),
      );
      wireGroup.add(dot);
      wireObjects.push({ m, w, curve, dot });
    }
  }
  function endpointPosition(name) {
    const id = name.split(".")[0],
      p = parts.get(id),
      pin = p?.pins.get(name);
    if (!pin) return null;
    const v = pin.position.clone();
    p.group.localToWorld(v);
    return robot.worldToLocal(v);
  }
  function updateRobot(t) {
    for (const d of dataCurves)
      d.dot.position.copy(d.curve.getPoint((t * 0.4) % 1));
    const lab = ["hero", "wiring", "architecture", "face", "closing"].includes(
      mode,
    );
    robot.position.set(lab ? 0 : sim.pose.x, 0, lab ? 0 : sim.pose.z);
    robot.rotation.y = lab ? -0.12 : -sim.pose.yaw;
    const out = mode === "wiring" && explode ? 0.18 : 0;
    for (const [i, p] of [...parts.values()].entries()) {
      const c = K.components.find((c) => c.id === p.id);
      p.group.position.copy(p.base);
      if (out) {
        if (p.id.startsWith("v7_cover")) {
          p.group.position.y += out * 0.28;
          p.group.position.z += out * (p.id.includes("rear") ? 0.95 : -0.95);
        } else if (p.id.startsWith("v7_phone") || p.id === "phone")
          p.group.position.y += out * 0.8;
        else if (c)
          p.group.position.set(
            p.base.x * 1.65,
            p.base.y + out * 0.25,
            p.base.z * 1.4,
          );
      }
      p.group.visible = p.attached;
    }
    if (radarGroup) radarGroup.rotation.y = -sim.radarAngle;
    wheels.forEach(
      (w, i) =>
        (w.rotation.x = -(i === 0 ? sim.wheels.left : sim.wheels.right)),
    );
    if (facePlane) facePlane.visible = parts.get("phone")?.attached !== false;
    if (facePlane)
      facePlane.position.y =
        0.2028 + (mode === "wiring" && explode ? 0.18 * 0.8 : 0);
    const alert =
      sim.latched ||
      sim.sensors.ir ||
      (sim.sensors.front !== null && sim.sensors.front < 0.38);
    const color = alert ? "#f57883" : "#81e4ba",
      ledConnected =
        sim.electrical?.connected("led.SIG", "esp.D" + K.GPIO.LED) &&
        sim.electrical?.connected("led.GND", "esp.GND");
    if (ledMesh) {
      ledMesh.material.color.set(color);
      ledMesh.material.emissive.set(color);
      ledMesh.material.emissiveIntensity = ledConnected
        ? alert
          ? (Math.floor(t * 6) % 2) * 1.8
          : 0.35
        : 0;
    }
    for (const m of bodyMeshes) {
      const cover =
        m.userData.part?.includes("cover") ||
        m.userData.part?.includes("phone_cradle");
      m.material.transparent = xray && cover;
      m.material.opacity = xray && cover ? 0.19 : 1;
      m.material.depthWrite = !(xray && cover);
    }
    for (const o of wireObjects) {
      o.dot.visible =
        wireGroup.visible &&
        (o.w.type !== "motor" || Math.abs(sim.speed) > 0.01);
      o.dot.position.copy(
        o.curve.getPoint(
          (t * (o.w.type === "signal" ? 1.4 : 0.45) +
            Number(o.w.id.replace(/\D/g, "")) * 0.07) %
            1,
        ),
      );
    }
    if (wiresDirty && wireGroup) {
      rebuildWires();
      wiresDirty = false;
    }
    if (mode === "future") {
      const p = K.futurePose(100 + futureTime);
      futureGroup.position.set(p.x, p.altitude, p.z);
      futureGroup.rotation.y = -p.yaw;
      futurePhone.rotation.x = p.fold * -Math.PI * 0.5;
      for (const pod of futurePods) {
        pod.arm.position.set(
          pod.sx * 0.1,
          0.062 + p.fold * 0.05,
          pod.sz * (0.09 + p.fold * 0.09),
        );
        pod.arm.rotation.y = -pod.sz * pod.sx * p.fold * 0.38;
        pod.arm.scale.x = 1 + p.fold * 0.85;
        pod.pod.rotation.order = "ZYX";
        pod.pod.rotation.y = (pod.sx * Math.PI) / 2;
        pod.pod.rotation.x = 0;
        pod.pod.rotation.z = (pod.sx * p.fold * Math.PI) / 2;
        pod.prop.rotation.z = t * p.rotor * 55;
        pod.glow.material.opacity =
          p.rotor > 0.1 ? 0.2 + 0.15 * Math.sin(t * 12) : 0.05;
        if (p.fold < 0.1) pod.prop.rotation.z = p.wheel;
      }
      $("future-alt").textContent = p.altitude.toFixed(2) + " m";
      $("future-fold").textContent = Math.round(p.fold * 100) + "%";
      $("future-seek").value = futureTime;
    }
  }
  function drawFace(t) {
    const c = faceCtx,
      w = faceCanvas.width,
      h = faceCanvas.height,
      alert = sim.latched || sim.emotion === "alert",
      happy = sim.emotion === "happy" || mode === "face",
      thinking = sim.emotion === "thinking";
    c.fillStyle = "#07181c";
    c.fillRect(0, 0, w, h);
    const blink = Math.sin(t * 1.3) > 0.993 ? 0.09 : 1,
      gaze = Math.sin(t * 0.65) * 4;
    for (const x of [95, 205]) {
      const hh = (happy ? 37 : 52) * blink,
        y = 68 + Math.sin(t * 1.5) * 1.5;
      c.save();
      c.translate(x + gaze, y);
      c.rotate(
        alert
          ? x < 150
            ? -0.19
            : 0.19
          : thinking
            ? x < 150
              ? 0.12
              : -0.06
            : 0,
      );
      c.shadowBlur = 15;
      c.shadowColor = alert ? "#fb9c90" : "#79ead6";
      c.fillStyle = alert ? "#f6a08c" : "#8cecd7";
      rounded(c, -18, -hh / 2, 36, hh, Math.min(12, hh / 2));
      c.fill();
      c.restore();
    }
    if (happy) {
      c.strokeStyle = "#81dac9";
      c.lineWidth = 3;
      c.beginPath();
      c.arc(150, 98, 17, 0.18, Math.PI - 0.18);
      c.stroke();
    } else if (thinking) {
      c.fillStyle = "#9bd7cf";
      for (let i = 0; i < 3; i++) {
        c.globalAlpha = 0.3 + 0.7 * (Math.sin(t * 5 - i) > 0);
        c.beginPath();
        c.arc(138 + i * 12, 112, 2.5, 0, Math.PI * 2);
        c.fill();
      }
      c.globalAlpha = 1;
    }
    faceTexture.needsUpdate = true;
  }
  function updateCamera(t, dt) {
    const target = new THREE.Vector3(),
      pos = new THREE.Vector3();
    if (cameraMode === "orbit") {
      orbit.enabled = true;
      orbit.update();
      return;
    }
    orbit.enabled = false;
    const lab = ["hero", "wiring", "architecture", "face", "closing"].includes(
        mode,
      ),
      p = lab ? { x: 0, z: 0, yaw: 0 } : sim.pose;
    if (cameraMode === "top") {
      pos.set(p.x, 0.01 + 4.6, p.z + 0.001);
      target.set(p.x, 0, p.z);
    } else if (cameraMode === "eye") {
      pos.set(p.x, 0.213, p.z);
      target.set(p.x + Math.sin(p.yaw) * 2, 0.19, p.z - Math.cos(p.yaw) * 2);
    } else if (mode === "future") {
      const f = K.futurePose(100 + futureTime);
      target.set(f.x, f.altitude + 0.15, f.z);
      pos.set(f.x + 1.25, f.altitude + 0.62, f.z - 1.65);
    } else if (cameraMode === "follow") {
      target.set(p.x, 0.12, p.z);
      pos.set(
        p.x + Math.sin(p.yaw + 0.7) * 1.08,
        0.72,
        p.z - Math.cos(p.yaw + 0.7) * 1.08,
      );
    } else if (mode === "architecture") {
      target.set(0.16, 0.12, 0.06);
      pos.set(0.85, 0.52, -0.88);
    } else {
      const a =
        demoPlaying || captureMode
          ? mode === "hero"
            ? Math.sin(t * 0.25) * 0.2
            : mode === "wiring"
              ? -0.2 + Math.sin((t - 23) * 0.12) * 0.3
              : 0
          : -0.1;
      const dist = mode === "face" ? 0.4 : mode === "wiring" ? 0.9 : 0.72;
      target.set(0, mode === "face" ? 0.195 : 0.13, 0);
      pos.set(
        Math.sin(a + 0.65) * dist,
        mode === "face" ? 0.24 : mode === "wiring" ? 0.48 : 0.4,
        -Math.cos(a + 0.65) * dist,
      );
    }
    const k = dt <= 0 ? 1 : 1 - Math.exp(-dt * 5);
    camera.position.lerp(pos, k);
    orbit.target.lerp(target, k);
    camera.lookAt(orbit.target);
  }
  function updateRays() {
    disposeGroup(rayGroup);
    if (!rayGroup.visible) return;
    for (const [name, a, max, color] of [
      ["front", sim.pose.yaw, 1.6, 0x8de3ca],
      ["rear", sim.pose.yaw + Math.PI, 1.3, 0x79b5e4],
      ["radar", sim.pose.yaw + sim.radarAngle, 2.2, 0xeeb27c],
    ]) {
      const d = sim.sensors[name];
      if (d === null) continue;
      const from = new THREE.Vector3(sim.pose.x, 0.05, sim.pose.z),
        to = new THREE.Vector3(
          from.x + Math.sin(a) * d,
          0.05,
          from.z - Math.cos(a) * d,
        );
      line([from, to], color, rayGroup);
      const hit = new THREE.Mesh(
        new THREE.SphereGeometry(0.015, 8, 6),
        new THREE.MeshBasicMaterial({ color }),
      );
      hit.position.copy(to);
      rayGroup.add(hit);
    }
  }
  function updatePath() {
    if (!ready || !pathLine) return;
    pathLine.visible =
      !["hero", "wiring", "architecture", "face", "future", "closing"].includes(
        mode,
      ) && $("show-path").checked;
    trailLine.visible = pathLine.visible;
    if (!pathLine.visible) return;
    pathLine.geometry.dispose();
    pathLine.geometry = new THREE.BufferGeometry().setFromPoints(
      [{ x: sim.pose.x, z: sim.pose.z }, ...sim.path].map(
        (p) => new THREE.Vector3(p.x, 0.015, p.z),
      ),
    );
    trailLine.geometry.dispose();
    trailLine.geometry = new THREE.BufferGeometry().setFromPoints(
      sim.trail.map((p) => new THREE.Vector3(p.x, 0.01, p.z)),
    );
  }
  function robotEye() {
    if (!ready || mode === "future") return;
    const p = sim.pose;
    eyeCamera.position.set(p.x, 0.22, p.z - 0.01);
    eyeCamera.lookAt(
      p.x + Math.sin(p.yaw) * 2,
      0.18,
      p.z - Math.cos(p.yaw) * 2,
    );
    const oldRobot = robot.visible,
      oldBench = bench.visible;
    robot.visible = false;
    bench.visible = false;
    const oldArena = arena.visible;
    arena.visible = true;
    renderer.setRenderTarget(visionTarget);
    renderer.render(scene, eyeCamera);
    renderer.readRenderTargetPixels(visionTarget, 0, 0, 320, 180, visionPixels);
    renderer.setRenderTarget(null);
    robot.visible = oldRobot;
    bench.visible = oldBench;
    arena.visible = oldArena;
    for (let y = 0; y < 180; y++)
      for (let x = 0; x < 320; x++) {
        const i = ((179 - y) * 320 + x) * 4,
          j = (y * 320 + x) * 4;
        for (let c = 0; c < 3; c++)
          visionImage.data[j + c] = Math.round(
            Math.pow(visionPixels[i + c] / 255, 1 / 2.2) * 255,
          );
        visionImage.data[j + 3] = 255;
      }
    cameraCtx.putImageData(visionImage, 0, 0);
    const result = K.detectMarker(visionImage.data, 320, 180);
    if (sim.faults.camera) {
      sim.visionFrame({ valid: false });
      cameraCtx.fillStyle = "#111d2ee8";
      cameraCtx.fillRect(0, 0, 320, 180);
      cameraCtx.fillStyle = "#edb49b";
      cameraCtx.font = "12px Arial";
      cameraCtx.fillText("FRAME STALE / INPUT FAULT", 54, 91);
    } else {
      sim.visionFrame(result);
      if (result.box) {
        const b = result.box;
        cameraCtx.strokeStyle = "#a6f3ca";
        cameraCtx.lineWidth = 2;
        cameraCtx.strokeRect(b.x, b.y, b.w, b.h);
        cameraCtx.fillStyle = "#11231de8";
        cameraCtx.fillRect(
          b.x,
          Math.max(0, b.y - 18),
          Math.min(200, 320 - b.x),
          17,
        );
        cameraCtx.fillStyle = "#bcf4dc";
        cameraCtx.font = "9px Arial";
        cameraCtx.fillText(
          "COLOUR MARKER · PIXEL TRACKER",
          b.x + 4,
          Math.max(11, b.y - 6),
        );
      }
    }
    $("vision-status").textContent = sim.faults.camera
      ? "Camera input marked stale"
      : result.valid
        ? "Marker acquired · " + result.pixels + " pixels"
        : "No supported colour marker in frame";
    $("vision-age").textContent = "virtual RGB";
  }

  function drawConceptCamera() {
    const c = cameraCtx,
      p = K.futurePose(100 + futureTime);
    c.fillStyle = "#101e29";
    c.fillRect(0, 0, 320, 180);
    c.strokeStyle = "#35525c";
    for (let x = 0; x < 320; x += 20) {
      c.beginPath();
      c.moveTo(x, 0);
      c.lineTo(x, 180);
      c.stroke();
    }
    for (let y = 0; y < 180; y += 20) {
      c.beginPath();
      c.moveTo(0, y);
      c.lineTo(320, y);
      c.stroke();
    }
    c.fillStyle = "#8de3ca";
    c.font = "10px Arial";
    c.fillText("WHEEL / ROTOR PODS", 14, 22);
    c.save();
    c.translate(160, 94);
    c.fillStyle = "#bed2cc";
    rounded(c, -33, -25, 66, 50, 8);
    c.fill();
    for (const x of [-1, 1])
      for (const z of [-1, 1]) {
        const xx = x * (47 + p.fold * 31),
          yy = z * (31 + p.fold * 14);
        c.strokeStyle = "#9ebfc2";
        c.lineWidth = 3;
        c.beginPath();
        c.moveTo(x * 25, z * 18);
        c.lineTo(xx, yy);
        c.stroke();
        c.strokeStyle = p.fold > 0.5 ? "#98e9d0" : "#e9ba8a";
        c.lineWidth = 2;
        c.beginPath();
        c.ellipse(xx, yy, 14, 5 + p.fold * 9, 0, 0, Math.PI * 2);
        c.stroke();
      }
    c.restore();
    c.fillStyle = "#c8aa89";
    c.font = "9px Arial";
    c.fillText("CONCEPT ANIMATION / NOT FLIGHT VALIDATED", 14, 167);
    $("vision-status").textContent =
      "Pod deployment " + Math.round(p.fold * 100) + "%";
    $("vision-age").textContent = "concept";
  }
  function drawConceptMap() {
    const c = mapCtx,
      w = mapCanvas.width,
      h = mapCanvas.height,
      p = K.futurePose(100 + futureTime);
    c.fillStyle = "#10212b";
    c.fillRect(0, 0, w, h);
    c.strokeStyle = "#456171";
    c.strokeRect(20, 20, w - 40, h - 40);
    c.strokeStyle = "#b79774";
    c.lineWidth = 2;
    c.setLineDash([5, 6]);
    c.beginPath();
    for (let u = 13; u <= 23; u += 0.1) {
      const q = K.futurePose(100 + u),
        x = w / 2 + q.x * 170,
        y = h / 2 + q.z * 170;
      if (u === 13) c.moveTo(x, y);
      else c.lineTo(x, y);
    }
    c.stroke();
    c.setLineDash([]);
    c.fillStyle = "#9be8c9";
    c.beginPath();
    c.arc(w / 2 + p.x * 170, h / 2 + p.z * 170, 7, 0, Math.PI * 2);
    c.fill();
    c.font = "11px Arial";
    c.fillStyle = "#bdd1d8";
    c.fillText("ANIMATED ALTITUDE " + p.altitude.toFixed(2) + " m", 34, 43);
    c.font = "9px Arial";
    c.fillStyle = "#a2b6be";
    c.fillText(
      "Scripted trajectory; no flight dynamics or live sensors",
      25,
      h - 8,
    );
  }

  function drawMap() {
    if (mode === "future") {
      drawConceptMap();
      return;
    }
    const c = mapCtx,
      w = mapCanvas.width,
      h = mapCanvas.height,
      scale = Math.min((w - 28) / K.WORLD.width, (h - 24) / K.WORLD.depth),
      ox = w / 2,
      oz = h / 2;
    const p = (x, z) => [ox + x * scale, oz + z * scale];
    c.fillStyle = "#101e26";
    c.fillRect(0, 0, w, h);
    const size = K.WORLD.cell * scale;
    for (let z = 0; z < sim.grid.h; z++)
      for (let x = 0; x < sim.grid.w; x++) {
        const v = sim.grid.data[z * sim.grid.w + x];
        if (!v) continue;
        const q = sim.grid.point(x, z),
          [a, b] = p(q.x, q.z);
        c.fillStyle = v === 2 ? "#7e9f99" : "#203b3f";
        c.fillRect(a - size / 2, b - size / 2, size + 0.1, size + 0.1);
      }
    c.strokeStyle = "#344951";
    c.strokeRect(
      ox - (K.WORLD.width / 2) * scale,
      oz - (K.WORLD.depth / 2) * scale,
      K.WORLD.width * scale,
      K.WORLD.depth * scale,
    );
    if (sim.path.length) {
      c.strokeStyle = "#b5a6ed";
      c.lineWidth = 2;
      c.beginPath();
      [sim.pose, ...sim.path].forEach((q, i) => {
        const [a, b] = p(q.x, q.z);
        if (i) c.lineTo(a, b);
        else c.moveTo(a, b);
      });
      c.stroke();
    }
    if (sim.goal) {
      const [a, b] = p(sim.goal.x, sim.goal.z);
      c.strokeStyle = "#ee91c6";
      c.lineWidth = 2;
      c.beginPath();
      c.arc(a, b, 7, 0, Math.PI * 2);
      c.stroke();
    }
    for (const [name, a, col] of [
      ["front", sim.pose.yaw, "#8de3ca"],
      ["rear", sim.pose.yaw + Math.PI, "#7cb9dd"],
      ["radar", sim.pose.yaw + sim.radarAngle, "#eeb27c"],
    ]) {
      const d = sim.sensors[name];
      if (d === null) continue;
      const [a0, b0] = p(sim.pose.x, sim.pose.z),
        [a1, b1] = p(
          sim.pose.x + Math.sin(a) * d,
          sim.pose.z - Math.cos(a) * d,
        );
      c.strokeStyle = col;
      c.globalAlpha = 0.7;
      c.beginPath();
      c.moveTo(a0, b0);
      c.lineTo(a1, b1);
      c.stroke();
      c.globalAlpha = 1;
      c.fillStyle = col;
      c.fillRect(a1 - 2, b1 - 2, 4, 4);
    }
    const [x, z] = p(sim.pose.x, sim.pose.z);
    c.save();
    c.translate(x, z);
    c.rotate(sim.pose.yaw);
    c.fillStyle = sim.latched ? "#ee9b8e" : "#a4edd2";
    c.beginPath();
    c.moveTo(0, -9);
    c.lineTo(6, 7);
    c.lineTo(-6, 7);
    c.closePath();
    c.fill();
    c.restore();
    c.fillStyle = "#90abb6";
    c.font = "8px Arial";
    c.fillText(
      "Known arena prior + synthetic sensor hits · SI units",
      12,
      h - 7,
    );
  }
  function refresh() {
    document
      .querySelectorAll("[data-fault]")
      .forEach((el) => (el.checked = !!sim.faults[el.dataset.fault]));
    $("cutoff-open").checked = !sim.cutoff;
    const result = K.circuitCheck(sim.circuit, {
      cutoff: sim.cutoff,
      packV: sim.packV,
    });
    $("state").textContent = mode === "future" ? "FUTURE CONCEPT" : sim.mode;
    $("reason").textContent = sim.reason;
    $("ranges").textContent =
      mode === "future"
        ? "NOT MODELED"
        : [sim.sensors.front, sim.sensors.rear]
            .map((v) => (v === null ? "N/A" : v.toFixed(2) + "m"))
            .join(" / ");
    $("servo-angle").previousElementSibling.textContent =
      mode === "future" ? "POD DEPLOYMENT" : "RADAR SERVO";
    $("servo-angle").textContent =
      mode === "future"
        ? Math.round(K.futurePose(100 + futureTime).fold * 100) + "%"
        : ((sim.radarAngle * 180) / Math.PI).toFixed(0) + "°";
    $("speed").previousElementSibling.textContent =
      mode === "future" ? "FLIGHT MODEL" : "VIRTUAL SPEED";
    $("speed").textContent =
      mode === "future" ? "ANIMATED" : sim.speed.toFixed(2) + " m/s";
    $("circuit-status").textContent = result.drive
      ? "MODEL READY"
      : !sim.cutoff
        ? "CUTOFF OPEN"
        : "CIRCUIT FAULT";
    $("circuit-status").style.color = result.drive ? "#8de3ca" : "#f3ac8f";
    $("circuit-problems").replaceChildren();
    for (const text of result.problems.slice(0, 7)) {
      const p = document.createElement("p");
      p.className = "wire-problem";
      p.textContent = text;
      $("circuit-problems").append(p);
    }
    if (result.problems.length > 7) {
      const p = document.createElement("p");
      p.className = "wire-problem";
      p.textContent =
        "… " + (result.problems.length - 7) + " more missing/invalid nets";
      $("circuit-problems").append(p);
    }
    const probe = (t) => result.voltage(t),
      v1 = probe($("probe-a").value),
      v2 = probe($("probe-b").value);
    $("probe-value").textContent =
      v1 === null || v2 === null
        ? "N/A / floating"
        : (v1 - v2).toFixed(3) + " V nominal";
    $("event-log").replaceChildren();
    for (const e of sim.events.slice(0, 18)) {
      const p = document.createElement("p"),
        b = document.createElement("b");
      b.textContent = e.at.toFixed(1) + "s / " + e.kind + " ";
      p.append(b, document.createTextNode(e.text));
      $("event-log").append(p);
    }
    const ch = K.chapterAt(demoTime);
    $("chapter-name").textContent = ch.title;
    $("demo-time").textContent = formatTime(demoTime) + " / 02:12";
    $("demo-seek").value = demoTime;
    $("demo-play").textContent = demoPlaying
      ? "Ⅱ Pause demo"
      : demoTime > 0 && demoTime < 132
        ? "▶ Resume demo"
        : "▶ Play guided demo";
    $("caption").classList.toggle(
      "visible",
      demoPlaying || seeking || captureMode,
    );
    $("caption").querySelector("span").textContent =
      mode === "future" ? "FUTURE CONCEPT / ANIMATION" : "SOFTWARE PROTOTYPE";
    $("caption").querySelector("p").textContent = ch.caption;
    $("navigate").disabled = sim.latched;
    $("home").disabled = sim.latched;
    $("follow-marker").disabled = sim.latched;
    document
      .querySelectorAll("[data-drive]")
      .forEach((b) => (b.disabled = sim.latched || demoPlaying));
  }
  function formatTime(t) {
    return (
      String(Math.floor(t / 60)).padStart(2, "0") +
      ":" +
      String(Math.floor(t % 60)).padStart(2, "0")
    );
  }
  function populateWiring() {
    for (const id of ["wire-a", "wire-b", "probe-a", "probe-b"]) {
      $(id).replaceChildren();
      for (const t of K.terminals) {
        const o = document.createElement("option");
        o.value = t;
        o.textContent = t;
        $(id).append(o);
      }
    }
    $("probe-a").value = "usb.5V";
    $("probe-b").value = "esp.GND";
    $("wire-a").value = "esp.D22";
    $("wire-b").value = "front.TRIG";
    populateWireList();
    $("component-list").replaceChildren();
    for (const c of K.components) {
      const row = document.createElement("div");
      row.className = "component-item";
      row.dataset.part = c.id;
      const label = document.createElement("span");
      label.textContent = c.title;
      const b = document.createElement("button");
      b.textContent = "Inspect";
      b.onclick = () => selectPart(c.id);
      const detach = document.createElement("button");
      detach.textContent = "Detach";
      detach.onclick = () => {
        const p = parts.get(c.id);
        if (!p) return;
        p.attached = !p.attached;
        detach.textContent = p.attached ? "Detach" : "Attach";
        if (!p.attached)
          sim.circuit = sim.circuit.filter(
            (w) => !w.a.startsWith(c.id + ".") && !w.b.startsWith(c.id + "."),
          );
        circuitChanged();
      };
      row.append(label, b, detach);
      $("component-list").append(row);
    }
  }
  function populateWireList() {
    const el = $("wire-select");
    el.replaceChildren();
    for (const w of sim.circuit) {
      const o = document.createElement("option");
      o.value = w.id;
      o.textContent = w.a + " → " + w.b;
      el.append(o);
    }
    refresh();
  }
  function circuitChanged() {
    invalidatePending();
    demoPlaying = false;
    sim.stop("PAUSED", "Circuit edited; a new mission is required");
    populateWireList();
    rebuildWires();
  }
  function addObstacle(at = null) {
    const p =
      at && Number.isFinite(at.x) && Number.isFinite(at.z)
        ? at
        : sim.path[Math.min(16, sim.path.length - 1)] || { x: 0.2, z: -0.3 };
    let x = p.x,
      z = p.z;
    if (Math.hypot(x - sim.pose.x, z - sim.pose.z) < 0.6) {
      x = sim.pose.x + Math.sin(sim.pose.yaw) * 0.7;
      z = sim.pose.z - Math.cos(sim.pose.yaw) * 0.7;
    }
    x = K.clamp(x, -2.3, 2.3);
    z = K.clamp(z, -1.5, 1.5);
    if (sim.obstacles.length >= 20) {
      toast("Obstacle limit reached. Reset/open a new project.");
      return;
    }
    sim.obstacles.push({
      id: "dynamic" + Date.now(),
      x,
      z,
      w: 0.32,
      d: 0.32,
      h: 0.24,
      color: "#c98c60",
      type: "box",
    });
    sim.addEvent(
      "World",
      "A new virtual crate appeared; sensors must observe it.",
    );
    rebuildObstacles();
    toast("Obstacle added ahead of the route.");
  }
  function resetDemo() {
    programGeneration++;
    demoTime = 0;
    demoChapter = -1;
    demoEvents.clear();
    sim.reset();
    for (const p of parts.values()) p.attached = true;
    explode = false;
    xray = false;
    $("xray").checked = false;
    wiresDirty = true;
    rebuildObstacles();
    rebuildWires();
    populateWireList();
    futureTime = 0;
    resetDerivedState();
    setMode("hero", false);
  }
  function program(t) {
    const ch = K.chapterAt(t),
      index = K.chapters.indexOf(ch);
    if (index !== demoChapter) {
      demoChapter = index;
      explode = ch.view === "wiring";
      wiresDirty = true;
      $("explode").textContent = explode
        ? "Reassemble body"
        : "Explode assembly";
      setMode(ch.view, false);
    }
    if (
      narration &&
      demoPlaying &&
      !seeking &&
      !captureMode &&
      lastSpoken !== index
    ) {
      speak(ch.caption);
      lastSpoken = index;
    }
    if (t >= 48 && !demoEvents.has("mission")) {
      demoEvents.add("mission");
      sim.mission(marker);
    }
    if (t >= 53 && !demoEvents.has("obstacle")) {
      demoEvents.add("obstacle");
      addObstacle();
    }
    if (t >= 76 && !demoEvents.has("fault")) {
      demoEvents.add("fault");
      sim.faults.link = true;
      sim.stop("FAULT", "Demonstration: virtual command link was lost", true);
    }
    if (t >= 83 && !demoEvents.has("restore")) {
      demoEvents.add("restore");
      sim.faults.link = false;
      sim.resetLatch();
      sim.addEvent(
        "Guard",
        "Input restored. Robot remains stationary until a new mission.",
      );
    }
    if (t >= 88 && !demoEvents.has("personality")) {
      demoEvents.add("personality");
      sim.emotion = "happy";
      sim.addEvent(
        "KITTY",
        "Target acquired. My dramatic entrance is limited to a sensible speed.",
      );
    }
    if (t >= 100) {
      futureTime = K.clamp(t - 100, 0, 25);
      if (!demoEvents.has("future")) {
        demoEvents.add("future");
        sim.stop("IDLE", "Future concept animation; no physical flight system");
      }
    }
  }
  function releaseManual() {
    manual = null;
    keys.clear();
    document
      .querySelectorAll("[data-drive]")
      .forEach((b) => b.classList.remove("pressed"));
    if (sim.mode === "MANUAL") sim.stop("PAUSED", "Manual control released");
  }
  function requestMission(goal, kind) {
    invalidatePending();
    demoPlaying = false;
    if (mode !== "mission") setMode("mission", false);
    if (kind === "FOLLOW" && !sim.vision.valid) {
      toast("Aim the robot-eye camera at the magenta marker first.");
      return;
    }
    const ok = sim.mission(goal, kind);
    if (!ok)
      toast(
        sim.latched
          ? "Reset the stop/fault latch before a new mission."
          : "Goal/circuit rejected; inspect the decision trace.",
      );
    refresh();
  }
  function speak(text) {
    if (!narration || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US";
    u.rate = 0.96;
    window.speechSynthesis.speak(u);
  }
  function beep() {
    if (
      !audioEnabled ||
      !sim.electrical?.connected("buzzer.SIG", "esp.D" + K.GPIO.BUZZER)
    )
      return;
    try {
      audioContext =
        audioContext ||
        new (window.AudioContext || window.webkitAudioContext)();
      if (audioContext.state === "suspended") audioContext.resume();
      const o = audioContext.createOscillator(),
        g = audioContext.createGain();
      o.type = "sine";
      o.frequency.setValueAtTime(850, audioContext.currentTime);
      g.gain.setValueAtTime(0.025, audioContext.currentTime);
      g.gain.exponentialRampToValueAtTime(
        0.0001,
        audioContext.currentTime + 0.12,
      );
      o.connect(g);
      g.connect(audioContext.destination);
      o.start();
      o.stop(audioContext.currentTime + 0.13);
    } catch {
      audioEnabled = false;
      $("audio").checked = false;
    }
  }
  function addChat(text, user = false) {
    const p = document.createElement("p");
    p.className = user ? "user-message" : "reply";
    p.textContent = text;
    $("chat-log").append(p);
    while ($("chat-log").children.length > 24)
      $("chat-log").firstChild.remove();
    $("chat-log").scrollTop = $("chat-log").scrollHeight;
  }
  async function chat(text) {
    if (!text.trim()) return;
    if (K.isStopRequest(text)) {
      addChat(text, true);
      stopAll("ESTOP", "Stop requested locally through conversation");
      addChat("Stopped locally. Reset, then request a new mission.");
      $("brain-mode").textContent = "LOCAL STOP GUARD / NO MODEL WAIT";
      return;
    }
    const generation = ++chatGeneration;
    activeModelAbort?.abort();
    activeModelAbort = null;
    addChat(text, true);
    $("send-chat").setAttribute("aria-busy", "true");
    sim.emotion = "thinking";
    let result;
    try {
      if (api?.model) {
        const controller = new AbortController(),
          timer = setTimeout(() => controller.abort(), 16000);
        activeModelAbort = controller;
        try {
          const r = await fetch("/api/brain", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Studio-Token": api.token,
            },
            body: JSON.stringify({
              text,
              prompt: $("system-prompt").value,
              observation: {
                mode: sim.mode,
                reason: sim.reason,
                front_m: sim.sensors.front,
                rear_m: sim.sensors.rear,
                prototype: true,
                sim_time_s: sim.time,
                marker: {
                  valid:
                    !sim.faults.camera &&
                    sim.vision.valid &&
                    sim.time - sim.vision.at <= 0.6,
                  age_s:
                    sim.vision.at > 0
                      ? Math.max(0, sim.time - sim.vision.at)
                      : null,
                  box: sim.vision.box,
                },
              },
            }),
            signal: controller.signal,
          });
          result = await r.json();
          if (!r.ok) throw Error(result.error || "Model request failed");
        } finally {
          clearTimeout(timer);
          if (activeModelAbort === controller) activeModelAbort = null;
        }
      } else result = K.offlineReply(text, sim);
      if (generation !== chatGeneration) return;
      if (
        typeof result.reply !== "string" ||
        ![
          "explain",
          "stop",
          "hello",
          "goal_alpha",
          "goal_beta",
          "radar",
          "dance",
          "future",
        ].includes(result.intent)
      )
        throw Error("Unsupported model intent");
      addChat(result.reply);
      $("brain-mode").textContent = result.source || "Local model";
      sim.addEvent("Brain", result.source + " / " + result.intent);
      applyIntent(result.intent);
      if (narration) speak(result.reply);
    } catch (e) {
      if (generation !== chatGeneration) return;
      addChat(
        "Local model unavailable. " +
          e.message +
          ". The simulation guard remains independent.",
      );
      sim.emotion = sim.latched ? "alert" : "calm";
    } finally {
      if (generation === chatGeneration) {
        $("send-chat").disabled = false;
        $("send-chat").setAttribute("aria-busy", "false");
      }
    }
  }
  function applyIntent(intent) {
    if (intent === "stop") {
      stopAll("ESTOP", "Stop requested through conversation");
      return;
    }
    if (intent === "goal_alpha") requestMission(marker);
    else if (intent === "goal_beta") requestMission({ x: -1.7, z: 1.05 });
    else if (intent === "radar") setMode("radar");
    else if (intent === "future") {
      setMode("future");
      futureTime = 0;
      futurePlaying = true;
    } else if (intent === "hello" || intent === "dance") {
      sim.emotion = "happy";
      sim.addEvent(
        "KITTY",
        "Hello gesture displayed. No dance motor command was issued.",
      );
    } else sim.emotion = sim.latched ? "alert" : "curious";
  }
  function stopAll(state = "ESTOP", reason = "Stop latched by operator") {
    invalidatePending();
    demoPlaying = false;
    futurePlaying = false;
    releaseManual();
    sim.stop(state, reason, true);
    chatGeneration++;
    $("send-chat").disabled = false;
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    refresh();
  }
  function composeFrame() {
    const c = captureCtx,
      W = captureCanvas.width,
      H = captureCanvas.height,
      sx = W / 1920;
    c.save();
    c.scale(sx, sx);
    c.fillStyle = "#0e1922";
    c.fillRect(0, 0, 1920, 1080);
    c.fillStyle = "#8de3ca";
    c.font = "bold 29px Arial";
    c.fillText("PROMETHEUS", 55, 57);
    c.fillStyle = "#8fa8b7";
    c.font = "14px Arial";
    c.fillText("KITTY CORP / VISION-BASED ASSISTANT", 55, 84);
    c.textAlign = "right";
    c.fillStyle = mode === "future" ? "#eeb27c" : "#a6e7cf";
    c.font = "bold 17px Arial";
    c.fillText(
      mode === "future"
        ? "FUTURE CONCEPT / FLIGHT ANIMATION"
        : "SOFTWARE PROTOTYPE / SIMULATED WORLD",
      1865,
      63,
    );
    c.textAlign = "left";
    const vx = 34,
      vy = 116,
      vw = 1318,
      vh = 814;
    c.fillStyle = "#17242d";
    rounded(c, vx, vy, vw, vh, 12);
    c.fill();
    if (ready) {
      const ratio = Math.min(vw / viewCanvas.width, vh / viewCanvas.height),
        dw = viewCanvas.width * ratio,
        dh = viewCanvas.height * ratio;
      c.drawImage(viewCanvas, vx + (vw - dw) / 2, vy + (vh - dh) / 2, dw, dh);
    } else c.drawImage($("fallback"), vx, vy, vw, vh);
    c.fillStyle = "#d6e6e4";
    c.font = "bold 22px Arial";
    c.fillText(
      mode === "future"
        ? "AeroKitty / future concept"
        : demoPlaying || seeking || captureMode
          ? K.chapterAt(demoTime).title
          : mode === "mission"
            ? "Mission lab / live simulation"
            : K.chapterAt(demoTime).title,
      63,
      153,
    );
    c.fillStyle = "#162931e8";
    rounded(c, 65, 842, 1255, 64, 8);
    c.fill();
    c.fillStyle = "#9de5cb";
    c.font = "17px Consolas,monospace";
    const fp = K.futurePose(100 + futureTime);
    c.fillText(
      mode === "future"
        ? `FUTURE CONCEPT     ANIMATED ALTITUDE ${fp.altitude.toFixed(2)} m     POD DEPLOYMENT ${Math.round(fp.fold * 100)}%`
        : `STATE ${sim.mode}     FRONT ${sim.sensors.front?.toFixed(2) ?? "N/A"} m     REAR ${sim.sensors.rear?.toFixed(2) ?? "N/A"} m     SERVO ${((sim.radarAngle * 180) / Math.PI).toFixed(0)}°`,
      86,
      880,
    );
    c.fillStyle = "#91b1be";
    c.font = "12px Arial";
    c.fillText(
      mode === "future"
        ? "FOLDING WHEEL / ROTOR STUDY"
        : "PHONE CAMERA / SYNTHETIC RGB + COLOUR TRACKER",
      1390,
      134,
    );
    c.drawImage(cameraCanvas, 1390, 150, 480, 270);
    c.fillText(
      mode === "future"
        ? "SCRIPTED CONCEPT TRAJECTORY / NO AERODYNAMICS"
        : "OCCUPANCY / KNOWN ARENA PRIOR + SENSOR HITS",
      1390,
      450,
    );
    c.drawImage(mapCanvas, 1390, 466, 480, 316);
    c.drawImage(faceCanvas, 1390, 811, 170, 85);
    c.fillStyle = "#94dbc3";
    c.font = "bold 16px Arial";
    c.fillText("KITTY / LAPTOP BRAIN", 1580, 837);
    c.fillStyle = "#9bb2bf";
    c.font = "13px Arial";
    c.fillText(
      sim.latched
        ? "Local guard / STOP LATCHED"
        : "Perception → intent → guarded control",
      1580,
      865,
    );
    const caption =
      mode === "future"
        ? K.chapterAt(100).caption
        : demoPlaying || seeking || captureMode
          ? K.chapterAt(demoTime).caption
          : sim.reason + " · All movement and sensing are simulated.";
    c.fillStyle = "#92dbc4";
    c.font = "11px Arial";
    c.fillText(
      mode === "future"
        ? "FUTURE STUDY / NOT FLIGHT-VALIDATED"
        : "DIGITAL PROTOTYPE / NO PHYSICAL DEVICE CONTROL",
      55,
      976,
    );
    c.fillStyle = "#d4e2e6";
    c.font = "21px Arial";
    wrapText(c, caption, 55, 1010, 1780, 29, 2);
    c.restore();
  }
  function wrapText(c, text, x, y, width, lineHeight, max = 4) {
    let line = "",
      n = 0;
    for (const word of text.split(" ")) {
      const next = line + word + " ";
      if (c.measureText(next).width > width && line) {
        c.fillText(line, x, y + n * lineHeight);
        line = word + " ";
        if (++n >= max) return;
      } else line = next;
    }
    if (n < max) c.fillText(line, x, y + n * lineHeight);
  }
  function startRecording() {
    let stream = null;
    if (
      !ready ||
      typeof MediaRecorder === "undefined" ||
      !captureCanvas.captureStream
    ) {
      toast("Video recording unavailable. Use your computer screen recorder.");
      return;
    }
    try {
      const type = [
        "video/webm;codecs=vp9",
        "video/webm;codecs=vp8",
        "video/webm",
      ].find((t) => MediaRecorder.isTypeSupported(t));
      if (!type) throw Error("No WebM encoder");
      composeFrame();
      recordChunks = [];
      stream = captureCanvas.captureStream(30);
      recorder = new MediaRecorder(stream, {
        mimeType: type,
        videoBitsPerSecond: 7000000,
      });
      recorder.ondataavailable = (e) => {
        if (e.data.size) recordChunks.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        download(
          new Blob(recordChunks, { type: "video/webm" }),
          "PROMETHEUS-KITTY-DEMO.webm",
          "video/webm",
        );
        recorder = null;
        $("record").classList.remove("recording");
        $("record").innerHTML = "<i></i> Record video";
        toast(
          "WebM saved with captions, map and prototype labels. Audio is not mixed.",
        );
      };
      recorder.start(1000);
      recordStarted = performance.now();
      $("record").classList.add("recording");
      $("record").innerHTML = "<i></i> Stop + save";
      toast("Recording composite video. Press Stop + save when finished.");
    } catch (e) {
      if (recorder) {
        recorder.onstop = null;
        recorder.ondataavailable = null;
        if (recorder.state !== "inactive") {
          try {
            recorder.stop();
          } catch {}
        }
      }
      stream?.getTracks().forEach((track) => track.stop());
      recorder = null;
      $("record").classList.remove("recording");
      $("record").innerHTML = "<i></i> Record video";
      toast("Recording failed: " + e.message);
    }
  }
  function stopRecording() {
    if (recorder && recorder.state !== "inactive") recorder.stop();
  }
  function render(t, dt) {
    // The GL context can disappear before its DOM event is dispatched.
    if (ready && renderer.getContext().isContextLost()) graphicsLost();
    drawFace(t);
    if (ready) {
      updateRobot(t);
      updateCamera(t, dt);
      if (t - lastVision > 0.2) {
        lastVision = t;
        if (mode === "future") drawConceptCamera();
        else robotEye();
      }
      if (t - lastMap > 0.09) {
        lastMap = t;
        updateRays();
        updatePath();
        drawMap();
      }
      renderer.setRenderTarget(null);
      renderer.render(scene, camera);
      if (mode === "wiring") {
        robot.updateMatrixWorld(true);
        let laneLeft = 0,
          laneRight = 0;
        camera.updateMatrixWorld();
        for (const { p, el } of labelItems) {
          el.hidden = !p.attached || !ready;
          const v = p.group.getWorldPosition(new THREE.Vector3());
          v.y += 0.02;
          v.project(camera);
          const inView = Math.abs(v.x) < 1 && Math.abs(v.y) < 1 && v.z < 1;
          const show =
            (inView &&
              ["esp", "driver", "front", "rear", "radar", "servo"].includes(
                p.id,
              )) ||
            (inView && p.id === selected);
          el.hidden = !show;
          const left = p.base.x < 0;
          el.style.left =
            (left
              ? Math.max(145, stage.clientWidth * 0.2)
              : Math.min(stage.clientWidth - 150, stage.clientWidth * 0.82)) +
            "px";
          el.style.top = 270 + (left ? laneLeft++ : laneRight++) * 37 + "px";
        }
      } else labelItems.forEach((l) => (l.el.hidden = true));
    } else drawMap();
    if (recorder) composeFrame();
  }
  function step(dt) {
    if (demoPlaying) {
      demoTime = Math.min(132, demoTime + dt);
      program(demoTime);
      if (demoTime >= 132) {
        demoPlaying = false;
        stopRecording();
      }
    } else if (futurePlaying) {
      futureTime = Math.min(25, futureTime + dt);
      if (futureTime >= 25) futurePlaying = false;
    }
    if (manual && !demoPlaying) {
      const d =
        manual === "forward"
          ? [0.27, 0]
          : manual === "back"
            ? [-0.2, 0]
            : manual === "left"
              ? [0, -1.2]
              : [0, 1.2];
      sim.command(...d);
    }
    sim.step(dt);
    const alert =
      sim.latched ||
      sim.sensors.ir ||
      (sim.sensors.front !== null && sim.sensors.front < 0.38);
    if (alert && audioEnabled && sim.time - lastBeep > 0.8) {
      lastBeep = sim.time;
      beep();
    }
    lastFault = alert;
  }
  function frame(now) {
    currentFrame = requestAnimationFrame(frame);
    const dt = Math.min(0.25, lastTime ? (now - lastTime) / 1000 : 0);
    lastTime = now;
    if (!document.hidden && !seeking && !captureMode) {
      for (let left = dt; left > 1e-6; ) {
        const slice = Math.min(0.025, left);
        step(slice);
        left -= slice;
      }
      render(sim.time, dt);
      if (now - lastUI > 150) {
        lastUI = now;
        refresh();
      }
      frames++;
      if (now - frameStart >= 1000) {
        fps = (frames * 1000) / (now - frameStart);
        frames = 0;
        frameStart = now;
        $("perf").textContent =
          (ready ? "WEBGL" : "FALLBACK") + " / " + Math.round(fps) + " FPS";
        if (autoQuality && ready && fps < 24 && quality > 0.55) {
          quality = Math.max(0.55, quality * 0.76);
          renderer.shadowMap.enabled = false;
          renderer.setPixelRatio(Math.min(devicePixelRatio || 1, quality));
          resize();
        }
      }
    }
  }
  async function seek(t) {
    if (!Number.isFinite(t) || t < 0 || t > 132)
      throw Error("Invalid timeline time");
    chatGeneration++;
    $("send-chat").disabled = false;
    const generation = ++programGeneration;
    seeking = true;
    demoPlaying = false;
    resetDemo();
    const activeGeneration = programGeneration;
    let time = 0;
    while (time < t - 1e-6) {
      if (activeGeneration !== programGeneration) return;
      const end = Math.min(t, time + 5);
      while (time < end - 1e-6) {
        const dt = Math.min(0.05, end - time);
        time += dt;
        demoTime = time;
        program(time);
        sim.step(dt);
      }
      time = end;
      if (activeGeneration !== programGeneration) return;
      await new Promise((r) => setTimeout(r, 0));
    }
    if (activeGeneration !== programGeneration) return;
    demoTime = t;
    program(t);
    futureTime = K.clamp(t - 100, 0, 25);
    render(sim.time, 0);
    refresh();
    composeFrame();
    $("toast").classList.remove("show");
    seeking = false;
  }
  function initializeUI() {
    populateWiring();
    document
      .querySelectorAll("[data-mode]")
      .forEach((b) => (b.onclick = () => setMode(b.dataset.mode)));
    document.querySelectorAll("[data-camera]").forEach(
      (b) =>
        (b.onclick = () => {
          cameraMode = b.dataset.camera;
          toast(
            cameraMode === "orbit"
              ? "Drag to orbit. Scroll to zoom."
              : "Camera: " + b.textContent,
          );
        }),
    );
    $("quality").onchange = () => {
      autoQuality = $("quality").value === "auto";
      quality = autoQuality ? 1.25 : Number($("quality").value);
      if (renderer) {
        renderer.shadowMap.enabled = $("quality").value !== "1";
        renderer.setPixelRatio(Math.min(devicePixelRatio || 1, quality));
        resize();
      }
    };
    $("navigate").onclick = () => requestMission(marker);
    $("home").onclick = () => requestMission({ x: -1.7, z: 1.05 });
    $("follow-marker").onclick = () => requestMission(marker, "FOLLOW");
    $("add-obstacle").onclick = addObstacle;
    $("estop").onclick = () => stopAll();
    $("reset").onclick = () => {
      invalidatePending();
      demoPlaying = false;
      futurePlaying = false;
      releaseManual();
      sim.resetLatch();
      refresh();
    };
    $("show-sensors").onchange = () => {
      if (rayGroup)
        rayGroup.visible =
          $("show-sensors").checked &&
          ![
            "hero",
            "wiring",
            "architecture",
            "face",
            "future",
            "closing",
          ].includes(mode);
    };
    $("show-path").onchange = updatePath;
    $("xray").onchange = () => (xray = $("xray").checked);
    document.querySelectorAll("[data-fault]").forEach(
      (el) =>
        (el.onchange = () => {
          invalidatePending();
          demoPlaying = false;
          sim.faults[el.dataset.fault] = el.checked;
          sim.scan();
          if (el.checked && ["NAVIGATE", "FOLLOW", "MANUAL"].includes(sim.mode))
            sim.stop("FAULT", "Injected " + el.dataset.fault + " fault", true);
          refresh();
        }),
    );
    $("cutoff-open").onchange = () => {
      invalidatePending();
      sim.cutoff = !$("cutoff-open").checked;
      if (!sim.cutoff) sim.stop("FAULT", "Motor cutoff is open", true);
      refresh();
    };
    $("faults-clear").onclick = () => {
      invalidatePending();
      for (const key of Object.keys(sim.faults)) sim.faults[key] = false;
      sim.cutoff = true;
      document
        .querySelectorAll("[data-fault],#cutoff-open")
        .forEach((el) => (el.checked = false));
      sim.scan();
      toast("Inputs restored. Reset and a new mission are still required.");
      refresh();
    };
    for (const b of document.querySelectorAll("[data-drive]")) {
      b.onpointerdown = (e) => {
        e.preventDefault();
        invalidatePending();
        demoPlaying = false;
        if (!["mission", "radar", "safety"].includes(mode))
          setMode("mission", false);
        if (sim.latched) return;
        manual = b.dataset.drive;
        b.classList.add("pressed");
        b.setPointerCapture?.(e.pointerId);
      };
      for (const event of ["pointerup", "pointercancel", "lostpointercapture"])
        b.addEventListener(event, releaseManual);
    }
    window.addEventListener("keydown", (e) => {
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName))
        return;
      if (e.code === "Space") {
        e.preventDefault();
        stopAll();
        return;
      }
      const map = {
        KeyW: "forward",
        ArrowUp: "forward",
        KeyS: "back",
        ArrowDown: "back",
        KeyA: "left",
        ArrowLeft: "left",
        KeyD: "right",
        ArrowRight: "right",
      };
      if (map[e.code]) {
        e.preventDefault();
        invalidatePending();
        if (sim.latched) return;
        keys.add(e.code);
        demoPlaying = false;
        manual = map[e.code];
        if (!["mission", "radar", "safety"].includes(mode))
          setMode("mission", false);
      }
    });
    window.addEventListener("keyup", (e) => {
      if (keys.has(e.code)) {
        keys.delete(e.code);
        releaseManual();
      }
    });
    const leave = () => {
      invalidatePending();
      demoPlaying = false;
      futurePlaying = false;
      releaseManual();
      sim.stop("PAUSED", "Page inactive; explicit restart required");
      chatGeneration++;
      $("send-chat").disabled = false;
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      stopRecording();
      refresh();
    };
    window.addEventListener("blur", leave);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) leave();
    });
    window.addEventListener("pagehide", leave);
    window.addEventListener("resize", resize);
    $("map").onclick = (e) => {
      if (mode === "future") {
        toast(
          "Future trajectory is a concept animation. Use Mission lab for route editing.",
        );
        return;
      }
      const r = mapCanvas.getBoundingClientRect(),
        x = ((e.clientX - r.left) / r.width) * mapCanvas.width,
        z = ((e.clientY - r.top) / r.height) * mapCanvas.height,
        scale = Math.min(
          (mapCanvas.width - 28) / K.WORLD.width,
          (mapCanvas.height - 24) / K.WORLD.depth,
        );
      const point = {
        x: (x - mapCanvas.width / 2) / scale,
        z: (z - mapCanvas.height / 2) / scale,
      };
      if (e.shiftKey) {
        addObstacle(point);
        return;
      }
      requestMission(point);
    };
    $("wire-add").onclick = () => {
      const a = $("wire-a").value,
        b = $("wire-b").value;
      if (a === b) return toast("Choose two different endpoints.");
      if (
        sim.circuit.some(
          (w) => (w.a === a && w.b === b) || (w.a === b && w.b === a),
        )
      )
        return toast("Those endpoints are already connected.");
      sim.circuit.push({ id: "edit" + Date.now(), a, b, type: "signal" });
      circuitChanged();
    };
    $("wire-remove").onclick = () => {
      sim.circuit = sim.circuit.filter((w) => w.id !== $("wire-select").value);
      circuitChanged();
    };
    $("wire-empty").onclick = () => {
      sim.circuit = [];
      circuitChanged();
    };
    $("wire-restore").onclick = () => {
      sim.circuit = K.defaultCircuit();
      for (const p of parts.values()) p.attached = true;
      document
        .querySelectorAll(".component-item button:last-child")
        .forEach((b) => (b.textContent = "Detach"));
      circuitChanged();
    };
    for (const id of ["probe-a", "probe-b"]) $(id).onchange = refresh;
    $("wire-select").onchange = () => {
      for (const o of wireObjects)
        o.m.material.opacity = o.w.id === $("wire-select").value ? 1 : 0.25;
    };
    $("explode").onclick = () => {
      explode = !explode;
      wiresDirty = true;
      $("explode").textContent = explode
        ? "Reassemble body"
        : "Explode assembly";
    };
    $("wire-view").onclick = () => {
      wiresVisible = !wiresVisible;
      if (wireGroup) wireGroup.visible = wiresVisible && mode === "wiring";
      $("wire-view").textContent = wiresVisible ? "Hide wires" : "Show wires";
    };
    $("future-drive").onclick = () => {
      futureTime = 0;
      futurePlaying = true;
    };
    $("future-transform").onclick = () => {
      futureTime = 5;
      futurePlaying = true;
    };
    $("future-seek").oninput = () => {
      futurePlaying = false;
      futureTime = Number($("future-seek").value);
    };
    $("demo-play").onclick = () => {
      if (seeking) return;
      invalidatePending();
      if (demoPlaying) {
        demoPlaying = false;
        sim.stop("PAUSED", "Guided demo paused");
        lastSpoken = -1;
        window.speechSynthesis?.cancel();
      } else {
        if (demoTime >= 132 || demoTime === 0) {
          resetDemo();
          lastSpoken = -1;
        }
        if (
          demoTime >= 48 &&
          demoTime < 76 &&
          sim.mode === "PAUSED" &&
          sim.goal &&
          !sim.latched
        )
          sim.mission({ ...sim.goal });
        demoPlaying = true;
        program(demoTime);
      }
      refresh();
    };
    $("demo-seek").onchange = () => seek(Number($("demo-seek").value));
    $("record").onclick = () => (recorder ? stopRecording() : startRecording());
    $("snapshot").onclick = () => {
      composeFrame();
      captureCanvas.toBlob(
        (b) => download(b, "PROMETHEUS-STUDIO.png", "image/png"),
        "image/png",
      );
    };
    $("project-save").onclick = () =>
      download(
        JSON.stringify(sim.export(), null, 2),
        "PROMETHEUS-PROJECT.json",
        "application/json",
      );
    $("project-open").onclick = () => $("project-file").click();
    $("project-file").onchange = async () => {
      const f = $("project-file").files[0];
      if (!f) return;
      try {
        if (f.size > 150000) throw Error("Project exceeds 150 KB");
        invalidatePending();
        const importGeneration = programGeneration;
        const data = JSON.parse(await f.text());
        if (importGeneration !== programGeneration) return;
        sim.import(data);
        for (const p of parts.values()) p.attached = true;
        resetDerivedState();
        demoPlaying = false;
        futurePlaying = false;
        rebuildObstacles();
        rebuildWires();
        populateWireList();
        setMode("mission", false);
        toast("Project imported in IDLE.");
      } catch (e) {
        toast("Import rejected: " + e.message);
      } finally {
        $("project-file").value = "";
      }
    };
    $("export-events").onclick = () =>
      download(
        JSON.stringify(
          {
            format: "prometheus-sim-evidence/v1",
            physicalOutputs: false,
            events: sim.events,
            pose: sim.pose,
            mode: sim.mode,
          },
          null,
          2,
        ),
        "PROMETHEUS-SIMULATION-EVENTS.json",
        "application/json",
      );
    $("chat-form").onsubmit = (e) => {
      e.preventDefault();
      const text = $("chat-input").value;
      $("chat-input").value = "";
      chat(text);
    };
    $("audio").onchange = () => {
      audioEnabled = $("audio").checked;
      if (audioEnabled) beep();
    };
    $("narration").onchange = () => {
      narration = $("narration").checked;
      if (narration)
        speak("Welcome to KITTY, Team Prometheus’s software prototype.");
      else window.speechSynthesis?.cancel();
    };
    $("voice-input").onclick = () => {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR)
        return toast(
          "Speech recognition is unavailable here. Type a command instead.",
        );
      chatGeneration++;
      activeModelAbort?.abort();
      activeModelAbort = null;
      if (activeRecognition) {
        try {
          activeRecognition.abort();
        } catch {}
      }
      const r = new SR();
      activeRecognition = r;
      r.lang = "en-US";
      r.interimResults = false;
      const voiceGeneration = chatGeneration;
      r.onresult = (e) => {
        if (voiceGeneration === chatGeneration && !document.hidden)
          chat(e.results[0][0].transcript);
      };
      r.onerror = (e) => {
        if (voiceGeneration === chatGeneration)
          toast("Microphone: " + e.error + ". You can type instead.");
      };
      r.onend = () => {
        if (activeRecognition === r) activeRecognition = null;
      };
      try {
        r.start();
      } catch (e) {
        activeRecognition = null;
        toast("Microphone: " + e.message);
      }
      toast(
        "Browser speech recognition requested. This may use your browser’s speech service.",
      );
    };
    $("help-open").onclick = () => $("help").showModal();
    $("prompt-open").onclick = () => $("prompt-dialog").showModal();
    document
      .querySelectorAll("[data-close]")
      .forEach((b) => (b.onclick = () => $(b.dataset.close).close()));
    $("prompt-save").onclick = () => {
      chatGeneration++;
      $("send-chat").disabled = false;
      $("prompt-dialog").close();
      toast(
        "Prompt applied for optional local-model requests. Guard rules remain independent.",
      );
    };
    $("prompt-download").onclick = () =>
      download(
        $("system-prompt").value,
        "KITTY-SYSTEM-PROMPT.txt",
        "text/plain",
      );
    $("retry-gpu").onclick = () => {
      if (ready) return;
      location.reload();
    };
    viewCanvas.addEventListener("click", (e) => {
      if (mode !== "wiring" || !ready) return;
      const r = viewCanvas.getBoundingClientRect(),
        pointer = new THREE.Vector2(
          ((e.clientX - r.left) / r.width) * 2 - 1,
          (-(e.clientY - r.top) / r.height) * 2 + 1,
        ),
        raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(partMeshes, false);
      if (hits.length && hits[0].object.userData.part)
        selectPart(hits[0].object.userData.part);
    });
    if (
      location.protocol === "http:" &&
      ["127.0.0.1", "localhost", "[::1]"].includes(location.hostname)
    )
      fetch("/api/info", { cache: "no-store" })
        .then((r) => {
          if (!r.ok) throw Error("No optional model bridge");
          return r.json();
        })
        .then((info) => {
          if (info.service !== "prometheus-mission-studio") return;
          api = info;
          $("model-info").textContent = info.model
            ? "Local-model bridge configured: " +
              info.model +
              ". Responses are verified per request; this is not a model benchmark."
            : "Local studio server is running with offline rules. Configure an already installed model to use Ollama.";
          if (info.model)
            $("brain-mode").textContent =
              "LOCAL MODEL CONFIGURED / NOT YET QUERIED";
        })
        .catch(() => {});
  }
  initializeUI();
  init3D();
  drawFace(0);
  drawMap();
  refresh();
  currentFrame = requestAnimationFrame(frame);
  // Explicit inspection/capture API. It never exposes a physical adapter.
  function beginCapture(width = 1920) {
    invalidatePending();
    captureMode = true;
    demoPlaying = false;
    futurePlaying = false;
    audioEnabled = false;
    narration = false;
    captureCanvas.width = width;
    captureCanvas.height = Math.round((width * 9) / 16);
    resetDemo();
    captureMode = true;
  }
  function advanceCapture(t) {
    if (!Number.isFinite(t) || t < 0 || t > 132)
      throw Error("Invalid capture time");
    if (t < demoTime) beginCapture(captureCanvas.width);
    captureMode = true;
    for (let x = demoTime; x < t - 1e-6; ) {
      const d = Math.min(0.05, t - x);
      x += d;
      demoTime = x;
      program(x);
      sim.step(d);
    }
    demoTime = t;
    program(t);
    futureTime = K.clamp(t - 100, 0, 25);
    render(sim.time, 0);
    refresh();
    composeFrame();
    return captureCanvas.toDataURL("image/jpeg", 0.9);
  }
  window.PrometheusStudio = {
    sim,
    beginCapture,
    advanceCapture,
    get state() {
      return {
        mode,
        demoPlaying,
        demoTime,
        futureTime,
        ready,
        fps,
        recording: !!recorder,
      };
    },
    setMode,
    seek,
    renderNow: () => {
      render(sim.time, 0);
      refresh();
      composeFrame();
    },
    get frameCanvas() {
      return captureCanvas;
    },
    get renderer() {
      return renderer;
    },
    get diagnostics() {
      return {
        renderedForward: new THREE.Vector3(0, 0, -1)
          .applyQuaternion(robot.quaternion)
          .toArray(),
        radarForward: radarGroup
          ? new THREE.Vector3(0, 0, -1)
              .applyQuaternion(
                radarGroup.getWorldQuaternion(new THREE.Quaternion()),
              )
              .toArray()
          : null,
        parts: parts.size,
        wireMeshes: wireObjects.length,
        futurePods: futurePods.length,
        pixelRatio: renderer?.getPixelRatio(),
        triangles: renderer?.info.render.triangles,
        geometries: renderer?.info.memory.geometries,
        textures: renderer?.info.memory.textures,
      };
    },
    snapshot: () => {
      composeFrame();
      return captureCanvas.toDataURL("image/png");
    },
    stop: stopAll,
  };
})();
