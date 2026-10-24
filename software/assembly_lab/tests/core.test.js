"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const K = require("../core.js");
const demo = () => K.loadDemo(K.defaultProject());
test("empty wiring cannot arm; complete virtual circuit can", () => {
  assert.equal(K.diagnose(K.defaultProject()).ready, false);
  assert.equal(K.diagnose(demo()).ready, true);
});
test("series AA chemistry changes the virtual motor rail", () => {
  const p = demo();
  assert.equal(K.diagnose(p).motorVoltage, 6);
  p.settings.chemistry = "nimh";
  assert.ok(Math.abs(K.diagnose(p).motorVoltage - 4.8) < 0.001);
});
test("direct ECHO to GPIO and source shorts are rejected", () => {
  const p = demo();
  K.connect(p, "front.ECHO", "esp.D33");
  assert.equal(K.diagnose(p).ready, false);
  assert.ok(K.diagnose(p).issues.some((i) => i.code === "gpio-voltage"));
  const q = demo();
  K.connect(q, "usb.V5", "usb.GND");
  assert.ok(K.diagnose(q).issues.some((i) => i.code === "short"));
});
test("missing common ground and open switch inhibit the circuit", () => {
  const p = demo();
  p.wires = p.wires.filter((w) => ![w.a, w.b].includes("driver.GND"));
  assert.equal(K.diagnose(p).ready, false);
  const q = demo();
  q.settings.switchOn = false;
  assert.equal(K.diagnose(q).ready, false);
});
test("a GPIO output connected directly to ground is rejected", () => {
  const p = demo();
  K.connect(p, "esp.D25", "usb.GND");
  assert.ok(K.diagnose(p).issues.some((i) => i.code === "signal-rail"));
});
test("nominal echo divider voltage is calculated; unsafe values inhibit", () => {
  const p = demo();
  assert.ok(Math.abs(K.diagnose(p).echoVoltage - (5 * 3200) / 5400) < 0.0001);
  p.settings.rTop = 100;
  assert.equal(K.diagnose(p).ready, false);
});
test("reversed motor leads reverse that model wheel", () => {
  const p = demo();
  for (const w of p.wires) {
    if (w.b === "motorL.P") w.b = "motorL.N";
    else if (w.b === "motorL.N") w.b = "motorL.P";
  }
  assert.equal(K.diagnose(p).leftPolarity, -1);
});
test("malformed imports fail without mutating existing project", () => {
  const p = demo();
  const saved = JSON.stringify(p);
  assert.throws(() =>
    K.validateProject({
      ...p,
      settings: { ...p.settings, maxSpeed: Infinity },
    }),
  );
  assert.throws(() =>
    K.validateProject({ ...p, wires: [{ a: "esp.FAKE", b: "usb.V5" }] }),
  );
  assert.throws(() =>
    K.validateProject({ ...p, obstacles: [{ x: NaN, z: 0, w: 100, d: 100 }] }),
  );
  assert.equal(JSON.stringify(p), saved);
  assert.deepEqual(K.validateProject(JSON.parse(saved)), p);
});
test("wire endpoints and duplicates are bounded", () => {
  const p = K.defaultProject();
  assert.throws(() => K.connect(p, "esp.FAKE", "usb.V5"));
  K.connect(p, "usb.GND", "esp.GND");
  assert.throws(() => K.connect(p, "esp.GND", "usb.GND"));
});
test("motion requires explicit arm; commands expire and do not rearm", () => {
  const c = new K.Controller(demo());
  c.command(1, 1, 0);
  c.tick(0.1, 100);
  assert.equal(c.state.pose.z, 350);
  assert.equal(c.arm(), true);
  c.command(0.5, 0.5, 100);
  c.tick(0.1, 200);
  assert.ok(c.state.pose.z < 350);
  c.tick(0.1, 800);
  assert.equal(c.state.armed, false);
  assert.equal(c.state.left, 0);
  c.command(1, 1, 900);
  c.tick(0.1, 950);
  assert.equal(c.state.armed, false);
});
test("stop, disconnect and sensor loss latch a disarm", () => {
  for (const kind of ["estop", "link", "sensor"]) {
    const c = new K.Controller(demo());
    c.arm();
    c.command(1, 1, 0);
    if (kind === "estop") c.emergencyStop();
    if (kind === "link") c.state.link = false;
    if (kind === "sensor") c.state.sensorValid = false;
    c.tick(0.1, 100);
    assert.equal(c.state.armed, false);
    assert.equal(c.state.left, 0);
  }
});
test("detached drive component inhibits arming", () => {
  const p = demo();
  p.placements.motorL.attached = false;
  assert.equal(new K.Controller(p).arm(), false);
});
test("front and rear obstacles inhibit motion in their respective directions", () => {
  for (const dir of [-1, 1]) {
    const p = demo();
    p.obstacles = [{ x: dir > 0 ? 0 : 50, z: 350 - dir * 210, w: 80, d: 80 }];
    const c = new K.Controller(p);
    c.arm();
    c.command(dir, dir, 0);
    c.tick(0.1, 100);
    assert.equal(c.state.left, 0);
  }
});
test("opposite wheel commands rotate the differential drive in place", () => {
  const p = demo();
  p.obstacles = [];
  const c = new K.Controller(p);
  c.arm();
  c.command(0.5, -0.5, 0);
  c.tick(0.1, 100);
  assert.ok(c.state.pose.yaw > 0);
  assert.equal(c.state.pose.x, 0);
  assert.equal(c.state.pose.z, 350);
});
test("collision guard blocks a side obstacle outside both sensor sectors", () => {
  const p = demo();
  p.obstacles = [{ x: 177, z: 280, w: 80, d: 40 }];
  const c = new K.Controller(p);
  assert.equal(c.arm(), true);
  c.command(1, 1, 0);
  c.tick(0.1, 100);
  assert.deepEqual(c.state.pose, { x: 0, z: 332, yaw: 0 });
  assert.equal(c.state.left, 1);
  assert.equal(c.state.right, 1);
  const blockedPose = { ...c.state.pose };
  assert.deepEqual(
    c.state.ranges,
    K.ranges({ ...p, obstacles: [] }, blockedPose),
  );
  assert.ok(c.state.ranges.front > p.settings.stopDistance);
  assert.ok(c.state.ranges.rear > p.settings.stopDistance);
  c.tick(0.1, 200);
  assert.deepEqual(c.state.pose, blockedPose);
  assert.equal(c.state.left, 0);
  assert.equal(c.state.right, 0);
  assert.equal(c.state.reason, "Conservative footprint collision guard");
});
test("collision guard keeps the 140 mm footprint inside the wall with clear sensors", () => {
  const p = demo();
  p.obstacles = [];
  const c = new K.Controller(p);
  c.state.pose.x = 859;
  assert.equal(c.arm(), true);
  c.command(1, 0.5, 0);
  c.tick(0.1, 100);
  assert.ok(c.state.pose.x > 859 && c.state.pose.x <= 860);
  assert.equal(c.state.left, 1);
  assert.equal(c.state.right, 0.5);
  const blockedPose = { ...c.state.pose };
  assert.ok(c.state.ranges.front > p.settings.stopDistance);
  assert.ok(c.state.ranges.rear > p.settings.stopDistance);
  c.tick(0.1, 200);
  assert.ok(Math.abs(c.state.pose.x) <= 860 && Math.abs(c.state.pose.z) <= 860);
  assert.deepEqual(c.state.pose, blockedPose);
  assert.equal(c.state.left, 0);
  assert.equal(c.state.right, 0);
  assert.equal(c.state.reason, "Conservative footprint collision guard");
});
test("editing a live circuit stops outputs on the next tick", () => {
  const p = demo(),
    c = new K.Controller(p);
  c.arm();
  c.command(0.4, 0.4, 0);
  c.tick(0.1, 100);
  p.wires = [];
  c.tick(0.1, 200);
  assert.equal(c.state.armed, false);
  assert.equal(c.state.right, 0);
});
test("nonfinite motion and excessive steps are rejected or bounded", () => {
  const c = new K.Controller(demo());
  c.arm();
  assert.equal(c.command(NaN, 1, 0), false);
  c.command(1, 1, 0);
  c.tick(100, 100);
  assert.ok(350 - c.state.pose.z <= 20);
});
