const assert = require('node:assert/strict');
const { CompanionDemo } = require('./command-controller');

function runToCompletion(sim, limit = 5400) {
  for (let i = 0; i < limit && sim.phase !== 'TASK_COMPLETE'; i += 1) {
    sim.step();
    if (i % 2 === 1) sim.record();
  }
  sim.record();
  return sim.export();
}

const demo = new CompanionDemo();
assert.equal(demo.submit('fly into a wall'), false, 'unsupported commands must be rejected');
assert.equal(demo.phase, 'IDLE', 'rejected input must leave the simulation idle');
assert.equal(demo.submit('KITTY, check the room'), true, 'the documented supported command must be accepted');
assert.equal(demo.phase, 'SCAN', 'the room-check task begins with the scan phase');

const result = runToCompletion(demo);
assert.equal(result.trace.at(-1).reason, 'TASK_COMPLETE', 'the supported task must complete');
assert.equal(result.metrics.taskComplete, true);
assert.equal(result.metrics.collisions, 0, 'the fixture route must have no collisions');
const warning = result.events.find(event => event.type === 'buzzer_warning');
const detour = result.events.find(event => event.type === 'detour_planned');
assert(warning && detour && warning.t < detour.t, 'warning must come before detour planning');
assert(result.trace.some(sample => sample.beep), 'the virtual buzzer state must occur');
assert(result.trace.filter(sample => sample.reason === 'OBSTACLE_WARNING')
  .every(sample => sample.left === 0 && sample.right === 0), 'motion must remain stopped during the warning hold');
assert(result.path.some(point => point.y > 4.9), 'the detour must pass around the wall in the supplied map');

const stopped = new CompanionDemo();
assert.equal(stopped.submit('check room'), true, 'the short supported alias is accepted by the parser');
for (let i = 0; i < 90; i += 1) stopped.step();
assert.equal(stopped.submit('stop'), true);
const stoppedX = stopped.pose.x;
for (let i = 0; i < 90; i += 1) stopped.step();
assert.equal(stopped.pose.x, stoppedX, 'STOP must hold the simulated pose');

const sensorModel = require('./core');
const readings = sensorModel.sense(
  { obstacles: [{ x: 2.48, y: 3.59, w: .1, h: .13 }] },
  { x: 2, y: 3.5, theta: 0 }
);
const blocked = sensorModel.safety(readings, .3, .3);
assert.equal(readings.ir, true, 'the angled fixture obstacle is visible to the virtual IR model');
assert(readings.front > sensorModel.C.stopDistance, 'the same obstacle is outside the front ultrasonic fan');
assert.equal(blocked.left, 0); assert.equal(blocked.right, 0, 'the IR guard must stop forward motion');

console.log('Room-check software simulation checks passed.');
console.log('Accepted command → stopped warning + virtual buzzer → map-based detour → complete; STOP, unsupported input, collision count, and IR guard checked.');
console.log('Software-only result. No physical hardware or sensor was tested.');

