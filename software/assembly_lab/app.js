/* Offline assembly, nominal wiring, and simulated motion. Never contacts hardware. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id),
    K = window.KittyLab,
    model = JSON.parse($("model-data").textContent);
  let project = K.defaultProject(),
    controller = new K.Controller(project),
    mode = "build",
    selected = "v7_base",
    pending = null;
  let renderer,
    scene,
    camera,
    orbit,
    robot,
    bench,
    wiresGroup,
    obstaclesGroup,
    raysGroup,
    selectionBox;
  let ready = false,
    raf = 0,
    last = 0,
    elapsed = 0,
    frames = 0,
    fps = 0,
    lastUI = 0,
    dragPart = false,
    dragObstacles = false,
    drag = null,
    pointerStart = null;
  let drive = null,
    keys = new Set(),
    ghost = true,
    wireframe = false,
    toastTimer,
    hoverPin = null;
  const parts = new Map(),
    pinObjects = [],
    labels = [],
    obstacleObjects = [];
  const stage = $("stage"),
    canvas = $("viewport");
  const requiredBody = model.parts
    .filter((p) => p.kind === "printed" && !p.optional)
    .map((p) => p.id);
  const vec = (a) => new THREE.Vector3(...a);
  function toast(text) {
    $("toast").textContent = text;
    $("toast").classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $("toast").classList.remove("show"), 4200);
  }
  function download(data, name, type) {
    const link = document.createElement("a"),
      url = URL.createObjectURL(new Blob([data], { type }));
    link.href = url;
    link.download = name;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  }
  function persist() {
    try {
      localStorage.setItem("kitty-assembly-lab-v1", JSON.stringify(project));
    } catch {
      /* File-mode storage can be unavailable; explicit save still works. */
    }
  }
  function placement(id) {
    return (
      project.placements[id] ||
      (project.placements[id] = {
        attached: !parts.get(id)?.optional,
        offset: [0, 0, 0],
        rotation: 0,
      })
    );
  }
  function releaseDrive() {
    drive = null;
    keys.clear();
    document
      .querySelectorAll("[data-drive]")
      .forEach((b) => b.classList.remove("pressed"));
    if (controller.state.armed) controller.command(0, 0, performance.now());
  }
  function stop(reason = "Disarmed") {
    releaseDrive();
    controller.stop(reason);
  }
  function edit(action) {
    stop("Project changed · re-arm required");
    action();
    persist();
    updatePlacements();
    rebuildWires();
    updateLibrary();
    showSelected();
    refreshChecks();
  }
  function material(color, extra = {}) {
    return new THREE.MeshStandardMaterial({
      color,
      roughness: 0.65,
      metalness: 0.14,
      ...extra,
    });
  }
  function box(w, h, d, color, x = 0, y = 0, z = 0) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material(color));
    m.position.set(x, y, z);
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  }
  function stlGeometry(item) {
    const raw = atob(item.mesh),
      bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    const v = new DataView(bytes.buffer),
      count = v.getUint32(80, true);
    if (bytes.length !== 84 + 50 * count) throw Error("Invalid embedded mesh");
    const pos = new Float32Array(count * 9);
    for (let i = 0; i < count; i++)
      for (let j = 0; j < 9; j++)
        pos[i * 9 + j] = v.getFloat32(84 + i * 50 + 12 + j * 4, true);
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.applyMatrix4(new THREE.Matrix4().fromArray(item.pose.flat()).transpose());
    // CAD Z-up -> scene Y-up. Swap winding to preserve outward faces after reflection.
    for (let i = 0; i < pos.length; i += 9) {
      for (let j = 0; j < 3; j++) {
        const at = i + j * 3,
          t = pos[at + 1];
        pos[at + 1] = pos[at + 2];
        pos[at + 2] = t;
      }
      for (let a = 0; a < 3; a++) {
        const t = pos[i + 3 + a];
        pos[i + 3 + a] = pos[i + 6 + a];
        pos[i + 6 + a] = t;
      }
    }
    g.computeVertexNormals();
    g.computeBoundingBox();
    g.computeBoundingSphere();
    return g;
  }
  function makePart(id, title, category, optional = false, note = "") {
    const g = new THREE.Group();
    g.userData.part = id;
    robot.add(g);
    const p = {
      id,
      title,
      category,
      optional,
      note,
      group: g,
      nominal: null,
      pins: new Map(),
      meshes: [],
    };
    parts.set(id, p);
    placement(id);
    return p;
  }
  function addMesh(p, m) {
    m.userData.part = p.id;
    p.group.add(m);
    p.meshes.push(m);
  }
  function cadPart(item, id = item.id) {
    let p = parts.get(id);
    if (!p)
      p = makePart(
        id,
        item.title,
        item.kind === "printed" ? "PRINTED BODY" : "PURCHASED HARDWARE",
        item.optional,
        item.kind === "printed"
          ? "Exact V7.1 print mesh. Fit, fasteners and strength require actual hardware checks."
          : "Reference envelope; purchased component, not a print part.",
      );
    const mesh = new THREE.Mesh(stlGeometry(item), material(item.color));
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    addMesh(p, mesh);
    return p;
  }
  function addLabel(text, part, pin = null) {
    const el = document.createElement("button");
    el.className = "part-label" + (pin ? " pin" : "");
    el.textContent = text;
    el.setAttribute("aria-label", pin ? "Connect " + pin : "Select " + text);
    el.onclick = () => (pin ? pickPin(pin) : select(part));
    $("labels").append(el);
    labels.push({ el, part, pin });
    return el;
  }
  function buildComponents() {
    parts.clear();
    pinObjects.length = 0;
    labels.length = 0;
    $("labels").replaceChildren();
    for (const item of model.parts) {
      if (item.id === "REFERENCE_ONLY_AA_holder_NOT_SELECTED") continue;
      let id = item.id;
      if (id.includes("motor_envelope"))
        id = id.endsWith("-1") ? "motorL" : "motorR";
      else if (id.includes("rear_sonar")) id = "rear";
      else if (id.includes("sonar_can")) id = "front";
      else if (id.includes("phone_case") || id.includes("display_graphic"))
        id = "phone";
      cadPart(item, id);
    }
    for (const c of K.components) {
      let p = parts.get(c.id);
      if (!p) {
        p = makePart(
          c.id,
          c.title,
          c.optional ? "OPTIONAL / PLACEMENT ONLY" : "ELECTRONICS",
          c.optional,
          c.note,
        );
        const [w, h, d] = c.size;
        addMesh(p, box(w, h, d, c.color, ...c.pos));
        if (["esp", "driver", "uno", "ir", "mic"].includes(c.id)) {
          addMesh(
            p,
            box(
              w * 0.45,
              3,
              d * 0.35,
              "#18232a",
              c.pos[0],
              c.pos[1] + h / 2 + 1.5,
              c.pos[2],
            ),
          );
        }
        if (c.id === "esp")
          addMesh(
            p,
            box(
              18,
              3,
              17,
              "#b5c2cb",
              c.pos[0],
              c.pos[1] + h / 2 + 2,
              c.pos[2] - 13,
            ),
          );
        if (c.id.startsWith("battery"))
          for (const x of [-7, 7]) {
            const cell = new THREE.Mesh(
              new THREE.CylinderGeometry(6.8, 6.8, 48, 16),
              material("#b8ac7c"),
            );
            cell.rotation.x = Math.PI / 2;
            cell.position.set(c.pos[0] + x, c.pos[1] + 3, c.pos[2]);
            addMesh(p, cell);
          }
        if (c.id === "switch")
          addMesh(
            p,
            box(4, 12, 4, "#e1d9b8", c.pos[0], c.pos[1] + 12, c.pos[2]),
          );
      }
      p.title = c.title;
      p.optional = c.optional;
      p.note =
        c.note ||
        "Nominal component envelope. Actual pin order, dimensions and operation remain unverified.";
      if (c.id === "front") addMesh(p, box(45, 20, 1.6, c.color, ...c.pos));
      const n = c.pins.length,
        half = Math.ceil(n / 2);
      c.pins.forEach((name, i) => {
        let local;
        if (c.id === "front" || c.id === "rear")
          local = new THREE.Vector3(
            c.pos[0] + (i - 1.5) * 5.08,
            c.pos[1] - 12,
            c.pos[2],
          );
        else
          local = new THREE.Vector3(
            c.pos[0] + (i < half ? -1 : 1) * (c.size[0] / 2 + 2),
            c.pos[1] + c.size[1] / 2 + 1,
            c.pos[2] +
              (((i % half) - (half - 1) / 2) * (c.size[2] - 5)) /
                Math.max(1, half - 1),
          );
        const end = c.id + "." + name,
          m = new THREE.Mesh(
            new THREE.SphereGeometry(1.9, 8, 6),
            new THREE.MeshBasicMaterial({
              color:
                name === "GND" || name === "N"
                  ? "#aab7c4"
                  : name === "V5" ||
                      name === "VCC" ||
                      name === "VM" ||
                      name === "P"
                    ? "#ef987f"
                    : "#79efc8",
            }),
          );
        m.position.copy(local);
        m.userData = { part: c.id, pin: end };
        p.group.add(m);
        p.pins.set(end, m);
        pinObjects.push(m);
        addLabel(name, c.id, end);
      });
    }
    for (const p of parts.values()) {
      const b = new THREE.Box3().setFromObject(p.group),
        centre = b.getCenter(new THREE.Vector3());
      p.nominal = centre.clone();
      p.height = b.max.y - b.min.y;
      for (const child of p.group.children) child.position.sub(centre);
      p.group.position.copy(centre);
      addLabel(p.title, p.id);
      if (p.id === "phone") {
        p.eyes = p.meshes.filter(
          (m) =>
            m.geometry.boundingBox &&
            m.geometry.boundingBox.max.x - m.geometry.boundingBox.min.x < 30,
        );
        for (const m of p.eyes) {
          const c = m.geometry.boundingBox.getCenter(new THREE.Vector3());
          m.geometry.translate(-c.x, -c.y, -c.z);
          m.position.add(c);
        }
      }
    }
    updatePlacements();
    updateLibrary();
    showSelected();
  }
  function updatePlacements() {
    if (!ready && !robot) return;
    let slot = 0;
    for (const p of parts.values()) {
      const q = placement(p.id),
        g = p.group;
      if (q.attached) {
        if (g.parent !== robot) robot.add(g);
        g.position.copy(p.nominal).add(vec(q.offset));
      } else {
        if (g.parent !== bench) bench.add(g);
        const i = slot++;
        g.position
          .set(
            ((i % 6) - 2.5) * 100,
            10 + p.height / 2,
            260 + Math.floor(i / 6) * 110,
          )
          .add(vec(q.offset));
      }
      g.rotation.set(0, (q.rotation * Math.PI) / 180, 0);
      for (const m of p.meshes) {
        const cover = p.id === "v7_cover_front" || p.id === "v7_cover_rear";
        m.material.transparent = cover && ghost;
        m.material.opacity = cover && ghost ? 0.13 : 1;
        m.material.depthWrite = !(cover && ghost);
        m.material.wireframe = wireframe;
      }
    }
    if (selectionBox && parts.has(selected))
      selectionBox.setFromObject(parts.get(selected).group);
  }
  function updateLibrary() {
    const query = $("search").value.toLowerCase(),
      list = $("parts-list");
    list.replaceChildren();
    let category = "",
      attached = 0;
    const entries = [...parts.values()].sort((a, b) =>
      a.category.localeCompare(b.category),
    );
    for (const p of entries) {
      if (placement(p.id).attached && !p.optional) attached++;
      if (
        !p.title.toLowerCase().includes(query) &&
        !p.id.toLowerCase().includes(query)
      )
        continue;
      if (p.category !== category) {
        category = p.category;
        const label = document.createElement("div");
        label.className = "section-label";
        label.textContent = category;
        list.append(label);
      }
      const row = document.createElement("button");
      row.className = "part-row" + (p.id === selected ? " selected" : "");
      row.dataset.part = p.id;
      const dot = document.createElement("span");
      dot.className = "part-swatch";
      dot.style.background =
        p.meshes[0]?.material.color.getStyle() || "#72e8ce";
      const name = document.createElement("span");
      name.textContent = p.title;
      const status = document.createElement("small");
      status.textContent = placement(p.id).attached ? "ON ROBOT" : "TRAY";
      row.append(dot, name, status);
      row.onclick = () => select(p.id);
      list.append(row);
    }
    $("assembly-count").textContent = attached + " attached";
  }
  function select(id) {
    if (!parts.has(id)) return;
    selected = id;
    updateLibrary();
    showSelected();
    if (selectionBox) {
      selectionBox.visible = true;
      selectionBox.setFromObject(parts.get(id).group);
    }
  }
  function showSelected() {
    const p = parts.get(selected);
    if (!p) return;
    const q = placement(p.id);
    $("part-title").textContent = p.title;
    $("part-note").textContent = p.note;
    $("attach").disabled =
      q.attached && q.offset.every((n) => n === 0) && q.rotation === 0;
    $("detach").disabled = !q.attached;
    ["x", "y", "z"].forEach((a, i) => ($("offset-" + a).value = q.offset[i]));
    $("pin-title").textContent = p.pins.size
      ? p.title + " terminals"
      : "Select an electronic component for its terminals.";
    $("pin-buttons").replaceChildren();
    for (const end of p.pins.keys()) {
      const b = document.createElement("button");
      b.textContent = end.split(".")[1];
      b.onclick = () => pickPin(end);
      $("pin-buttons").append(b);
    }
  }
  function pinWorld(end) {
    const id = end.split(".")[0],
      m = parts.get(id)?.pins.get(end);
    if (!m) return null;
    return m.getWorldPosition(new THREE.Vector3());
  }
  function disposeGroup(group) {
    if (!group) return;
    for (const c of [...group.children]) {
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
  function wireColor(a, b) {
    if ([a, b].some((e) => e.endsWith(".GND") || e === "batteryB.N"))
      return "#b6c8d4";
    if (
      [a, b].some(
        (e) => /\.(V5|VCC|VM|P|IN|OUT)$/.test(e) && !e.startsWith("div"),
      )
    )
      return "#f1997c";
    return "#6fdfc5";
  }
  function rebuildWires() {
    if (!wiresGroup || !renderer) return;
    disposeGroup(wiresGroup);
    robot.updateWorldMatrix(true, true);
    bench.updateWorldMatrix(true, true);
    project.wires.forEach((w, i) => {
      const a = pinWorld(w.a),
        b = pinWorld(w.b);
      if (!a || !b) return;
      robot.worldToLocal(a);
      robot.worldToLocal(b);
      const h = Math.max(a.y, b.y) + 15 + (i % 5) * 4,
        curve = new THREE.CubicBezierCurve3(
          a,
          new THREE.Vector3(a.x, h, a.z),
          new THREE.Vector3(b.x, h, b.z),
          b,
        );
      const m = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 22, 0.65, 4, false),
        material(wireColor(w.a, w.b), {
          emissive: wireColor(w.a, w.b),
          emissiveIntensity: 0.18,
        }),
      );
      m.userData.wire = i;
      wiresGroup.add(m);
    });
    wiresGroup.visible = $("show-wires").checked;
  }
  function options() {
    for (const id of ["wire-a", "wire-b", "probe-red", "probe-black"]) {
      const select = $(id);
      select.replaceChildren();
      for (const c of K.components) {
        const group = document.createElement("optgroup");
        group.label = c.title;
        for (const pin of c.pins) {
          const o = document.createElement("option");
          o.value = c.id + "." + pin;
          o.textContent = c.id + "." + pin;
          group.append(o);
        }
        select.append(group);
      }
    }
    $("wire-a").value = "usb.V5";
    $("wire-b").value = "esp.V5";
    $("probe-red").value = "driver.VM";
    $("probe-black").value = "driver.GND";
  }
  function pickPin(end) {
    if (mode !== "wire") {
      setMode("wire");
    }
    select(end.split(".")[0]);
    if (!pending) {
      pending = end;
      $("wire-a").value = end;
      $("pending-pin").textContent =
        "Start: " + end + " · choose the second terminal.";
    } else {
      const start = pending;
      pending = null;
      $("wire-b").value = end;
      try {
        edit(() => K.connect(project, start, end));
        toast("Connected " + start + " → " + end);
      } catch (e) {
        toast(e.message);
      }
      $("pending-pin").textContent = "No terminal selected.";
    }
  }
  function meter(diag) {
    const a = diag.voltage($("probe-red").value),
      b = diag.voltage($("probe-black").value);
    $("meter").textContent =
      a === null || b === null
        ? "Floating / switching"
        : (a - b).toFixed(3) + " V DC";
  }
  function refreshChecks() {
    const d = K.diagnose(project),
      list = $("checks-list");
    list.replaceChildren();
    $("check-badge").textContent = d.ready
      ? "MODEL READY"
      : d.issues.length + " ISSUES";
    $("check-badge").style.color = d.ready ? "#72e8ce" : "#efba76";
    const issues = d.ready
      ? [{ text: "Selected model checks pass. The simulation can be armed." }]
      : d.issues;
    for (const i of issues) {
      const el = document.createElement("div");
      el.className = "check-item" + (d.ready ? " ok" : "");
      el.textContent = i.text;
      list.append(el);
    }
    $("wire-count").textContent = project.wires.length + " WIRES";
    $("wire-list").replaceChildren();
    project.wires.forEach((w, i) => {
      const row = document.createElement("div");
      row.className = "wire-row";
      const text = document.createElement("span");
      text.textContent = w.a + " → " + w.b;
      const b = document.createElement("button");
      b.textContent = "×";
      b.setAttribute("aria-label", "Remove wire " + w.a + " to " + w.b);
      b.onclick = () => edit(() => project.wires.splice(i, 1));
      row.append(text, b);
      $("wire-list").append(row);
    });
    $("rail-reading").textContent =
      d.motorVoltage === null ? "— V" : d.motorVoltage.toFixed(2) + " V";
    meter(d);
    return d;
  }
  function setMode(next) {
    stop("Mode changed · re-arm required");
    mode = next;
    pending = null;
    dragPart = false;
    dragObstacles = false;
    stage.classList.remove("placing");
    $("drag-part").textContent = "Drag part: off";
    $("move-obstacle").textContent = "Drag obstacles: off";
    document.querySelectorAll("[data-mode]").forEach((b) => {
      b.classList.toggle("active", b.dataset.mode === next);
      b.setAttribute("aria-pressed", String(b.dataset.mode === next));
    });
    for (const m of ["build", "wire", "test"])
      $(m + "-panel").hidden = m !== next;
    $("drive-overlay").hidden = next !== "test";
    $("mode-hint").textContent =
      next === "build"
        ? "Select a part. Attach it, detach it, or move it around the workbench."
        : next === "wire"
          ? "Connect terminals. Checks respond to your actual virtual netlist."
          : "Arm, then hold a drive control. Obstacles and injected faults affect motion.";
    $("scene-title").textContent =
      next === "test"
        ? "THE TEST ARENA"
        : next === "wire"
          ? "THE WIRING BENCH"
          : "THE ASSEMBLY BENCH";
    $("scene-subtitle").textContent =
      next === "test"
        ? "2 × 2 m virtual room · WASD / arrows to drive"
        : "Drag to orbit · scroll to zoom · right-drag to pan";
    if (robot) {
      robot.position.set(0, 0, 0);
      robot.rotation.y = 0;
      obstaclesGroup.visible = next === "test";
      raysGroup.visible = next === "test";
      updatePlacements();
      rebuildWires();
      setView("iso");
    }
    refreshChecks();
  }
  function setView(view) {
    if (!ready) return;
    const test = mode === "test";
    orbit.target.set(0, test ? 0 : 110, test ? 0 : 30);
    if (view === "top") camera.position.set(0, test ? 1900 : 650, 30.01);
    else
      camera.position.set(
        test ? 1250 : 390,
        test ? 1100 : 300,
        test ? -1250 : -500,
      );
    camera.near = 0.5;
    camera.far = 10000;
    camera.updateProjectionMatrix();
    orbit.update();
  }
  function rebuildObstacles() {
    if (!obstaclesGroup) return;
    disposeGroup(obstaclesGroup);
    obstacleObjects.length = 0;
    $("obstacle-editor").replaceChildren();
    project.obstacles.forEach((o, i) => {
      const m = box(o.w, 180, o.d, "#a07556", o.x, 90, o.z);
      m.userData.obstacle = i;
      obstaclesGroup.add(m);
      obstacleObjects.push(m);
      const row = document.createElement("div");
      row.className = "obstacle-row";
      const label = document.createElement("span");
      label.textContent = "Obstacle " + (i + 1) + " · X / Z mm";
      row.append(label);
      for (const key of ["x", "z"]) {
        const input = document.createElement("input");
        input.type = "number";
        input.min = -900;
        input.max = 900;
        input.step = 10;
        input.value = o[key];
        input.setAttribute("aria-label", "Obstacle " + (i + 1) + " " + key);
        input.onchange = () => {
          const n = Number(input.value);
          if (!Number.isFinite(n) || Math.abs(n) > 900) {
            input.value = o[key];
            return;
          }
          edit(() => (o[key] = n));
          rebuildObstacles();
        };
        row.append(input);
      }
      const del = document.createElement("button");
      del.textContent = "×";
      del.setAttribute("aria-label", "Remove obstacle " + (i + 1));
      del.onclick = () => {
        edit(() => project.obstacles.splice(i, 1));
        rebuildObstacles();
      };
      row.append(del);
      $("obstacle-editor").append(row);
    });
  }
  function sensorRays() {
    for (const [rear, id, index] of [
      [false, "front", 0],
      [true, "rear", 1],
    ]) {
      const c = controller.state.pose,
        range = controller.state.ranges?.[id] ?? 4000,
        angle = c.yaw + (rear ? Math.PI : 0),
        ox = rear ? 50 : 0,
        oz = rear ? 107 : -91,
        x = c.x + Math.cos(c.yaw) * ox - Math.sin(c.yaw) * oz,
        z = c.z + Math.sin(c.yaw) * ox + Math.cos(c.yaw) * oz;
      if (!raysGroup.children[index]) {
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute(
          "position",
          new THREE.BufferAttribute(new Float32Array(18), 3),
        );
        raysGroup.add(
          new THREE.LineSegments(
            geometry,
            new THREE.LineBasicMaterial({
              color: rear ? "#f6bc7e" : "#69ead0",
              transparent: true,
              opacity: 0.6,
            }),
          ),
        );
      }
      const geometry = raysGroup.children[index].geometry,
        attribute = geometry.attributes.position,
        values = attribute.array;
      let n = 0;
      for (const da of [-0.22, 0, 0.22]) {
        const a = angle + da;
        for (const value of [
          x,
          rear ? 72 : 43,
          z,
          x + Math.sin(a) * Math.min(range, 1800),
          rear ? 72 : 43,
          z - Math.cos(a) * Math.min(range, 1800),
        ])
          values[n++] = value;
      }
      attribute.needsUpdate = true;
      geometry.computeBoundingSphere();
    }
  }
  function uiTick() {
    const s = controller.state,
      r = s.ranges || K.ranges(project, s.pose);
    $("front-reading").textContent = (r.front / 10).toFixed(1) + " cm";
    $("rear-reading").textContent = (r.rear / 10).toFixed(1) + " cm";
    $("wheel-reading").textContent =
      Math.round(s.left * 100) + " / " + Math.round(s.right * 100) + " %";
    $("drive-state").textContent = s.estop
      ? "STOP LATCHED"
      : s.armed
        ? "ARMED"
        : "DISARMED";
    $("drive-reason").textContent = s.reason;
    $("arm").disabled =
      !ready ||
      s.armed ||
      s.estop ||
      !s.link ||
      !s.sensorValid ||
      !K.diagnose(project).ready;
    $("status-line").textContent =
      mode === "test"
        ? s.reason + " · virtual only"
        : "Virtual only · no physical outputs";
    if (renderer)
      $("performance").textContent =
        fps +
        " FPS · " +
        Math.round(renderer.info.render.triangles / 1000) +
        "k tri";
  }
  function positionLabels() {
    const rect = stage.getBoundingClientRect(),
      occupied = [];
    const ordered = [...labels].sort(
      (a, b) =>
        Number(!!b.pin && (b.pin === hoverPin || b.pin === pending)) -
          Number(!!a.pin && (a.pin === hoverPin || a.pin === pending)) ||
        Number(b.part === selected) - Number(a.part === selected),
    );
    for (const l of ordered) {
      const p = parts.get(l.part),
        isPin = !!l.pin;
      let show =
        $("show-labels").checked &&
        (isPin
          ? mode === "wire" && (l.pin === hoverPin || l.pin === pending)
          : placement(l.part).attached &&
            (l.part === selected ||
              ["esp", "driver", "front", "rear", "motorL", "motorR"].includes(
                l.part,
              )));
      l.el.hidden = !show;
      if (!show) continue;
      const point = isPin
        ? pinWorld(l.pin)
        : p.group
            .getWorldPosition(new THREE.Vector3())
            .add(new THREE.Vector3(0, p.height / 2 + 9, 0));
      point.project(camera);
      if (
        Math.abs(point.x) > 1 ||
        Math.abs(point.y) > 1 ||
        Math.abs(point.z) > 1
      ) {
        l.el.hidden = true;
        continue;
      }
      const x = ((point.x + 1) / 2) * rect.width,
        y = ((-point.y + 1) / 2) * rect.height;
      if (y < 110 || y > rect.height - 45) {
        l.el.hidden = true;
        continue;
      }
      let lift = occupied.some(
        (o) => Math.abs(o.x - x) < 100 && Math.abs(o.y - y) < 26,
      )
        ? 26
        : 0;
      if (
        occupied.some(
          (o) => Math.abs(o.x - x) < 100 && Math.abs(o.y - (y - lift)) < 26,
        )
      ) {
        l.el.hidden = true;
        continue;
      }
      l.el.style.left = x + "px";
      l.el.style.top = y - lift + "px";
      occupied.push({ x, y: y - lift });
    }
  }
  function frame(now) {
    raf = 0;
    if (!ready || document.hidden) return;
    const dt = last ? Math.min((now - last) / 1000, 0.1) : 0;
    last = now;
    frames++;
    elapsed += dt;
    if (elapsed >= 1) {
      fps = Math.round(frames / elapsed);
      frames = 0;
      elapsed = 0;
    }
    if (mode === "test") {
      let command = drive;
      if (keys.has("w") || keys.has("arrowup")) command = "forward";
      else if (keys.has("s") || keys.has("arrowdown")) command = "back";
      else if (keys.has("a") || keys.has("arrowleft")) command = "left";
      else if (keys.has("d") || keys.has("arrowright")) command = "right";
      if (command && controller.state.armed) {
        const values = {
          forward: [0.7, 0.7],
          back: [-0.55, -0.55],
          left: [-0.45, 0.45],
          right: [0.45, -0.45],
        };
        controller.command(...values[command], now);
      }
      controller.tick(dt, now);
      const s = controller.state;
      robot.position.set(s.pose.x, 0, s.pose.z);
      robot.rotation.y = -s.pose.yaw;
      for (const [id, v] of [
        ["REFERENCE_ONLY_wheel_envelope_-1", s.left],
        ["REFERENCE_ONLY_wheel_envelope_1", s.right],
      ]) {
        const p = parts.get(id);
        if (p && placement(id).attached)
          p.group.rotation.x -= ((v * project.settings.maxSpeed) / 31.25) * dt;
      }
      const phone = parts.get("phone");
      if (phone?.eyes) {
        const blink = now % 4700 < 140;
        for (const m of phone.eyes) {
          m.scale.y = blink ? 0.15 : 1;
          m.material.emissive.set(
            s.estop ? "#ea675d" : s.armed ? "#52d6be" : "#246575",
          );
          m.material.emissiveIntensity = 0.4;
        }
      }
      if (now - lastUI > 120) sensorRays();
    }
    if (now - lastUI > 120) {
      lastUI = now;
      uiTick();
    }
    orbit.update();
    if (selectionBox && parts.has(selected))
      selectionBox.setFromObject(parts.get(selected).group);
    positionLabels();
    renderer.render(scene, camera);
    raf = requestAnimationFrame(frame);
  }
  function resize() {
    if (!ready) return;
    const r = stage.getBoundingClientRect();
    renderer.setSize(r.width, r.height, false);
    camera.aspect = r.width / r.height;
    camera.updateProjectionMatrix();
  }
  function quality() {
    if (!renderer) return;
    const q = $("quality").value;
    renderer.setPixelRatio(
      q === "eco"
        ? 1
        : Math.min(devicePixelRatio || 1, q === "ultra" ? 2.5 : 1.5),
    );
    renderer.shadowMap.enabled = q !== "eco";
    resize();
  }
  function cleanup() {
    cancelAnimationFrame(raf);
    raf = 0;
    orbit?.dispose();
    if (scene) {
      const geos = new Set(),
        mats = new Set();
      scene.traverse((o) => {
        o.shadow?.dispose();
        if (o.geometry) geos.add(o.geometry);
        if (o.material)
          for (const m of Array.isArray(o.material) ? o.material : [o.material])
            mats.add(m);
      });
      geos.forEach((g) => g.dispose());
      mats.forEach((m) => m.dispose());
    }
    renderer?.dispose();
    renderer = null;
  }
  function graphicsFail(message) {
    ready = false;
    stop("Graphics unavailable · disarmed");
    cleanup();
    stage.classList.remove("ready");
    $("gpu-status").textContent = "Saved view / wiring only";
    $("fallback-message").textContent =
      message +
      " Use Chrome/Edge with graphics acceleration, then Retry graphics. Wiring checks and project save remain available.";
    $("labels").replaceChildren();
    uiTick();
  }
  function init() {
    try {
      cleanup();
      renderer = new THREE.WebGLRenderer({
        canvas,
        antialias: true,
        alpha: false,
        preserveDrawingBuffer: true,
      });
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      scene = new THREE.Scene();
      scene.background = new THREE.Color("#142736");
      scene.fog = new THREE.Fog("#142736", 2600, 6000);
      camera = new THREE.PerspectiveCamera(38, 1, 0.5, 10000);
      orbit = new OrbitControls(camera, canvas);
      orbit.enableDamping = true;
      orbit.dampingFactor = 0.09;
      orbit.minDistance = 80;
      orbit.maxDistance = 4000;
      orbit.maxPolarAngle = Math.PI * 0.49;
      scene.add(new THREE.HemisphereLight("#cae7f4", "#334039", 2.5));
      const sun = new THREE.DirectionalLight("#fff0da", 3.2);
      sun.position.set(400, 700, -500);
      sun.castShadow = true;
      sun.shadow.mapSize.set(2048, 2048);
      sun.shadow.camera.left = -650;
      sun.shadow.camera.right = 650;
      sun.shadow.camera.top = 650;
      sun.shadow.camera.bottom = -650;
      sun.shadow.camera.far = 2200;
      sun.shadow.bias = -0.0004;
      scene.add(sun);
      const rim = new THREE.DirectionalLight("#69dce8", 1.8);
      rim.position.set(-500, 250, 500);
      scene.add(rim);
      const ground = box(2200, 3, 2200, "#172b37", 0, -3, 0);
      ground.receiveShadow = true;
      ground.castShadow = false;
      scene.add(ground);
      const grid = new THREE.GridHelper(2000, 40, "#39616e", "#253f4d");
      grid.position.y = -1;
      scene.add(grid);
      robot = new THREE.Group();
      bench = new THREE.Group();
      scene.add(robot, bench);
      wiresGroup = new THREE.Group();
      robot.add(wiresGroup);
      obstaclesGroup = new THREE.Group();
      raysGroup = new THREE.Group();
      scene.add(obstaclesGroup, raysGroup);
      obstaclesGroup.visible = mode === "test";
      raysGroup.visible = mode === "test";
      selectionBox = new THREE.BoxHelper(undefined, "#74e5cf");
      scene.add(selectionBox);
      selectionBox.visible = true;
      buildComponents();
      rebuildWires();
      rebuildObstacles();
      ready = true;
      stage.classList.add("ready");
      $("gpu-status").textContent = "● GPU render / CPU simulation";
      quality();
      setView("iso");
      last = 0;
      lastUI = 0;
      raf = requestAnimationFrame(frame);
    } catch (e) {
      graphicsFail(e.message || "3D graphics could not start.");
    }
  }
  function raycast(event) {
    const rect = canvas.getBoundingClientRect(),
      ray = new THREE.Raycaster();
    ray.setFromCamera(
      new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        (-(event.clientY - rect.top) / rect.height) * 2 + 1,
      ),
      camera,
    );
    return ray;
  }
  function pointerDown(e) {
    if (!ready || e.button !== 0) return;
    pointerStart = [e.clientX, e.clientY];
    const ray = raycast(e);
    if ((dragPart && mode === "build") || (dragObstacles && mode === "test")) {
      const targets = dragObstacles
          ? obstacleObjects
          : parts.get(selected)?.group.children || [],
        hit = ray.intersectObjects(targets, true)[0];
      if (!hit) return;
      stop("Placement changed");
      const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0),
        point = ray.ray.intersectPlane(plane, new THREE.Vector3());
      if (!point) return;
      drag = {
        point,
        obstacle: dragObstacles ? hit.object.userData.obstacle : null,
        offset: dragObstacles
          ? { ...project.obstacles[hit.object.userData.obstacle] }
          : [...placement(selected).offset],
      };
      orbit.enabled = false;
      canvas.setPointerCapture(e.pointerId);
      e.preventDefault();
    }
  }
  function pointerMove(e) {
    if (!ready) return;
    if (!drag) {
      hoverPin =
        mode === "wire"
          ? raycast(e).intersectObjects(pinObjects, false)[0]?.object.userData
              .pin || null
          : null;
      canvas.style.cursor = hoverPin ? "crosshair" : "grab";
      return;
    }
    const point = raycast(e).ray.intersectPlane(
      new THREE.Plane(new THREE.Vector3(0, 1, 0), 0),
      new THREE.Vector3(),
    );
    if (!point) return;
    const dx = point.x - drag.point.x,
      dz = point.z - drag.point.z;
    if (drag.obstacle !== null) {
      const o = project.obstacles[drag.obstacle];
      o.x = Math.round(Math.max(-900, Math.min(900, drag.offset.x + dx)));
      o.z = Math.round(Math.max(-900, Math.min(900, drag.offset.z + dz)));
      const mesh = obstacleObjects[drag.obstacle];
      mesh.position.x = o.x;
      mesh.position.z = o.z;
    } else {
      const q = placement(selected);
      q.offset[0] = Math.round(
        Math.max(-1500, Math.min(1500, drag.offset[0] + dx)),
      );
      q.offset[2] = Math.round(
        Math.max(-1500, Math.min(1500, drag.offset[2] + dz)),
      );
      updatePlacements();
      rebuildWires();
      showSelected();
    }
  }
  function pointerUp(e) {
    if (!ready) return;
    if (drag) {
      drag = null;
      orbit.enabled = true;
      persist();
      refreshChecks();
      rebuildObstacles();
      pointerStart = null;
      return;
    }
    if (
      !pointerStart ||
      Math.hypot(e.clientX - pointerStart[0], e.clientY - pointerStart[1]) > 6
    ) {
      pointerStart = null;
      return;
    }
    pointerStart = null;
    const ray = raycast(e),
      targets =
        mode === "wire"
          ? [...pinObjects, ...[...parts.values()].flatMap((p) => p.meshes)]
          : [...parts.values()].flatMap((p) => p.meshes),
      hits = ray.intersectObjects(targets, false);
    if (hits.length) {
      const h = hits[0].object;
      if (h.userData.pin && mode === "wire") pickPin(h.userData.pin);
      else if (h.userData.part) select(h.userData.part);
    }
  }
  function syncSettings() {
    const s = project.settings;
    $("chemistry").value = s.chemistry;
    $("power-switch").checked = s.switchOn;
    $("r-top").value = s.rTop;
    $("r-bottom").value = s.rBottom;
    $("speed").value = s.maxSpeed;
    $("stop-distance").value = s.stopDistance;
    $("speed-value").textContent = s.maxSpeed + " mm/s";
    $("stop-value").textContent = s.stopDistance + " mm";
  }
  function restore(input) {
    const next = K.validateProject(input);
    stop("Project loaded · disarmed");
    project = next;
    controller = new K.Controller(project);
    for (const id of parts.keys()) placement(id);
    $("link-ok").checked = true;
    $("sensor-ok").checked = true;
    syncSettings();
    persist();
    updatePlacements();
    rebuildWires();
    rebuildObstacles();
    updateLibrary();
    showSelected();
    refreshChecks();
    uiTick();
  }
  function setup() {
    options();
    try {
      const saved = localStorage.getItem("kitty-assembly-lab-v1");
      if (saved) project = K.validateProject(JSON.parse(saved));
    } catch {
      /* Ignore corrupt/unsupported local cache, never import partial state. */
    }
    controller = new K.Controller(project);
    syncSettings();
    document
      .querySelectorAll("[data-mode]")
      .forEach((b) => (b.onclick = () => setMode(b.dataset.mode)));
    $("search").oninput = updateLibrary;
    $("attach").onclick = () =>
      edit(() => {
        const q = placement(selected);
        q.attached = true;
        q.offset = [0, 0, 0];
        q.rotation = 0;
      });
    $("detach").onclick = () =>
      edit(() => {
        placement(selected).attached = false;
        placement(selected).offset = [0, 0, 0];
      });
    $("assemble-all").onclick = () =>
      edit(() => {
        for (const p of parts.values()) {
          const q = placement(p.id);
          q.attached = !p.optional;
          q.offset = [0, 0, 0];
          q.rotation = 0;
        }
      });
    $("exercise").onclick = () => {
      edit(() => {
        for (const p of parts.values()) {
          const q = placement(p.id);
          q.attached = p.id === "v7_base";
          q.offset = [0, 0, 0];
          q.rotation = 0;
        }
        project.wires = [];
      });
      setMode("build");
      toast("Parts are on the tray. Select one and attach it to its mount.");
    };
    $("next-step").onclick = () => {
      const order = [
        "v7_motor_left",
        "motorL",
        "REFERENCE_ONLY_wheel_envelope_-1",
        "v7_motor_right",
        "motorR",
        "REFERENCE_ONLY_wheel_envelope_1",
        "v7_caster_bridge",
        "REFERENCE_ONLY_caster_envelope",
        ...requiredBody,
        "esp",
        "driver",
        "batteryA",
        "batteryB",
        "front",
        "rear",
        "divF",
        "divR",
        "usb",
        "switch",
        "phone",
      ];
      const id = order.find((id) => parts.has(id) && !placement(id).attached);
      if (id) {
        select(id);
        toast("Next: " + parts.get(id).title);
      } else
        toast("All core parts are attached. Continue to the wiring bench.");
    };
    ["x", "y", "z"].forEach(
      (a, i) =>
        ($("offset-" + a).onchange = () => {
          const n = Number($("offset-" + a).value);
          if (!Number.isFinite(n) || Math.abs(n) > 1500) {
            showSelected();
            return;
          }
          edit(() => (placement(selected).offset[i] = n));
        }),
    );
    $("rotate").onclick = () =>
      edit(
        () =>
          (placement(selected).rotation =
            (placement(selected).rotation + 15) % 360),
      );
    $("drag-part").onclick = () => {
      dragPart = !dragPart;
      stage.classList.toggle("placing", dragPart);
      $("drag-part").textContent = "Drag part: " + (dragPart ? "on" : "off");
      toast(
        dragPart
          ? "Drag the selected part across the floor plane. Attach restores its mount."
          : "Orbit controls restored.",
      );
    };
    $("connect").onclick = () => {
      try {
        edit(() => K.connect(project, $("wire-a").value, $("wire-b").value));
        toast("Wire connected.");
      } catch (e) {
        toast(e.message);
      }
    };
    $("cancel-wire").onclick = () => {
      pending = null;
      $("pending-pin").textContent = "No terminal selected.";
    };
    $("demo").onclick = () => {
      edit(() => {
        K.loadDemo(project);
        project.settings.switchOn = true;
        for (const c of K.components.filter((c) => !c.optional)) {
          const q = placement(c.id);
          q.attached = true;
          q.offset = [0, 0, 0];
          q.rotation = 0;
        }
      });
      syncSettings();
      toast(
        "31-wire nominal example loaded. Physical wiring still requires board and power verification.",
      );
    };
    $("clear-wires").onclick = () => edit(() => (project.wires = []));
    for (const id of ["probe-red", "probe-black"])
      $(id).onchange = () => meter(K.diagnose(project));
    for (const [id, key] of [
      ["r-top", "rTop"],
      ["r-bottom", "rBottom"],
    ])
      $(id).onchange = () => {
        const n = Number($(id).value);
        if (!Number.isFinite(n) || n < 100 || n > 100000) {
          syncSettings();
          return;
        }
        edit(() => (project.settings[key] = n));
      };
    $("ghost").onchange = () => {
      ghost = $("ghost").checked;
      updatePlacements();
    };
    $("wireframe").onclick = () => {
      wireframe = !wireframe;
      $("wireframe").classList.toggle("active", wireframe);
      updatePlacements();
    };
    $("show-wires").onchange = () => {
      if (wiresGroup) wiresGroup.visible = $("show-wires").checked;
    };
    $("quality").onchange = quality;
    $("view-iso").onclick = () => setView("iso");
    $("view-top").onclick = () => setView("top");
    $("focus").onclick = () => {
      const p = parts.get(selected);
      if (!ready || !p) return;
      const centre = p.group.getWorldPosition(new THREE.Vector3());
      orbit.target.copy(centre);
      camera.position.copy(centre).add(new THREE.Vector3(150, 140, -210));
      orbit.update();
    };
    $("screenshot").onclick = () => {
      if (!ready) return toast("Start the 3D view first.");
      renderer.render(scene, camera);
      canvas.toBlob((blob) => {
        if (blob) download(blob, "KITTY-LAB.png", "image/png");
      });
    };
    $("arm").onclick = () => {
      if (!ready) return;
      releaseDrive();
      if (controller.arm())
        toast("Virtual robot armed. Hold a drive control; release to stop.");
      else toast("Resolve circuit / assembly checks and reset faults first.");
      uiTick();
    };
    $("disarm").onclick = () => stop();
    $("estop").onclick = () => {
      releaseDrive();
      controller.emergencyStop();
      uiTick();
    };
    $("reset-stop").onclick = () => {
      stop("Stop latch reset · disarmed");
      controller.state.estop = false;
      uiTick();
    };
    $("chemistry").onchange = () =>
      edit(() => (project.settings.chemistry = $("chemistry").value));
    $("power-switch").onchange = () =>
      edit(() => (project.settings.switchOn = $("power-switch").checked));
    for (const [id, key, out, unit] of [
      ["speed", "maxSpeed", "speed-value", " mm/s"],
      ["stop-distance", "stopDistance", "stop-value", " mm"],
    ])
      $(id).oninput = () => {
        edit(() => (project.settings[key] = Number($(id).value)));
        $(out).textContent = project.settings[key] + unit;
      };
    $("link-ok").onchange = () => {
      controller.state.link = $("link-ok").checked;
      if (!controller.state.link) stop("Link lost · re-arm required");
      uiTick();
    };
    $("sensor-ok").onchange = () => {
      controller.state.sensorValid = $("sensor-ok").checked;
      if (!controller.state.sensorValid) stop("Sensor lost · re-arm required");
      uiTick();
    };
    $("add-obstacle").onclick = () => {
      if (project.obstacles.length >= 24) return toast("Maximum 24 obstacles.");
      edit(() =>
        project.obstacles.push({
          x: 450,
          z: -300 + (project.obstacles.length % 4) * 140,
          w: 140,
          d: 140,
        }),
      );
      rebuildObstacles();
    };
    $("reset-arena").onclick = () => {
      stop("Arena reset · disarmed");
      controller = new K.Controller(project);
      project.obstacles = K.defaultProject().obstacles;
      persist();
      rebuildObstacles();
      $("link-ok").checked = true;
      $("sensor-ok").checked = true;
    };
    $("move-obstacle").onclick = () => {
      dragObstacles = !dragObstacles;
      stage.classList.toggle("placing", dragObstacles);
      $("move-obstacle").textContent =
        "Drag obstacles: " + (dragObstacles ? "on" : "off");
    };
    for (const b of document.querySelectorAll("[data-drive]")) {
      b.onpointerdown = (e) => {
        if (mode !== "test" || !controller.state.armed) return;
        drive = b.dataset.drive;
        b.classList.add("pressed");
        b.setPointerCapture(e.pointerId);
        e.preventDefault();
      };
      b.onpointerup = releaseDrive;
      b.onpointercancel = releaseDrive;
      b.onlostpointercapture = releaseDrive;
    }
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        stop("Stopped by Escape");
        return;
      }
      if (
        mode !== "test" ||
        /^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName) ||
        $("guide").open
      )
        return;
      const key = e.key.toLowerCase();
      if (key === " ") {
        e.preventDefault();
        controller.emergencyStop();
        releaseDrive();
      }
      if (
        [
          "w",
          "a",
          "s",
          "d",
          "arrowup",
          "arrowdown",
          "arrowleft",
          "arrowright",
        ].includes(key)
      ) {
        e.preventDefault();
        keys.add(key);
      }
    });
    window.addEventListener("keyup", (e) => {
      keys.delete(e.key.toLowerCase());
      if (!keys.size && !drive && controller.state.armed)
        controller.command(0, 0, performance.now());
    });
    window.addEventListener("blur", () => {
      stop("Window left · re-arm required");
      uiTick();
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        stop("Page hidden · re-arm required");
        cancelAnimationFrame(raf);
        raf = 0;
      } else if (ready && !raf) {
        last = 0;
        raf = requestAnimationFrame(frame);
      }
    });
    window.addEventListener("pagehide", () => stop("Page closed"));
    $("export").onclick = () =>
      download(
        JSON.stringify(project, null, 2),
        "KITTY-ASSEMBLY-PROJECT.json",
        "application/json",
      );
    $("import").onclick = () => $("project-file").click();
    $("project-file").onchange = async () => {
      const file = $("project-file").files[0];
      if (!file) return;
      if (file.size > 256000) {
        toast("Project exceeds 256 KB.");
        $("project-file").value = "";
        return;
      }
      try {
        restore(JSON.parse(await file.text()));
        toast("Project loaded. Runtime starts disarmed.");
      } catch (e) {
        toast("Could not open project: " + e.message);
      } finally {
        $("project-file").value = "";
      }
    };
    $("help").onclick = () => {
      stop("Guide opened · disarmed");
      $("guide").showModal();
    };
    $("close-guide").onclick = () => $("guide").close();
    $("begin").onclick = () => $("guide").close();
    $("retry").onclick = init;
    canvas.addEventListener("pointerdown", pointerDown);
    canvas.addEventListener("pointermove", pointerMove);
    canvas.addEventListener("pointerup", pointerUp);
    canvas.addEventListener("pointercancel", () => {
      drag = null;
      if (orbit) orbit.enabled = true;
      pointerStart = null;
    });
    canvas.addEventListener("webglcontextlost", (e) => {
      e.preventDefault();
      graphicsFail("The graphics context stopped.");
    });
    canvas.addEventListener("webglcontextrestored", init);
    new ResizeObserver(resize).observe(stage);
    init();
    refreshChecks();
    uiTick();
  }
  setup();
  // Read-only snapshots and the same validated loader make verification reproducible.
  window.kittyLab = {
    snapshot: () => ({
      project: K.clone(project),
      runtime: K.clone(controller.state),
      ready,
      mode,
      parts: parts.size,
      selected,
      pending,
      fps,
    }),
    sensorRayPositions: (id) => {
      const index = ["front", "rear"].indexOf(id);
      return Array.from(
        raysGroup?.children[index]?.geometry.attributes.position.array || [],
      );
    },
    load: restore,
    select,
    screenPoint: (id, pin) => {
      if (!ready) return null;
      const p = parts.get(id);
      if (!p) return null;
      const v = pin
        ? pinWorld(pin)
        : p.group.getWorldPosition(new THREE.Vector3());
      if (!v) return null;
      v.project(camera);
      const r = canvas.getBoundingClientRect();
      return {
        x: r.x + ((v.x + 1) / 2) * r.width,
        y: r.y + ((1 - v.y) / 2) * r.height,
      };
    },
  };
})();
