(() => {
  'use strict';

  const canvas = document.getElementById('simCanvas');
  const ctx = canvas.getContext('2d');
  const input = document.getElementById('commandInput');
  const runButton = document.getElementById('runButton');
  const pauseButton = document.getElementById('pauseButton');
  const stopButton = document.getElementById('stopButton');
  const resetButton = document.getElementById('resetButton');
  const soundEnabled = document.getElementById('soundEnabled');
  const scale = 70;
  const origin = { x: 80, y: 60 };
  let sim = new KittyCommandDemo.CompanionDemo();
  let running = false;
  let paused = false;
  let previousTime = 0;
  let accumulated = 0;
  let frameCount = 0;
  let lastBeep = false;
  let audio = null;
  let manualMessage = '';
  let renderedEventCount = 0;

  function phaseLabel(phase) {
    return ({
      IDLE: 'READY', SCAN: 'TASK CHECK', FOLLOW_COMMAND: 'FOLLOWING TASK',
      OBSTACLE_WARNING: 'PAUSED · OBSTACLE', DETOUR: 'DETOUR',
      TASK_COMPLETE: 'TASK COMPLETE', STOPPED: 'STOPPED',
      NO_ROUTE: 'NO ROUTE', COLLISION_GUARD: 'COLLISION GUARD'
    })[phase] || phase.replaceAll('_', ' ');
  }

  function phaseTone(phase) {
    if (phase === 'OBSTACLE_WARNING' || phase === 'NO_ROUTE') return 'warning';
    if (phase === 'STOPPED' || phase === 'COLLISION_GUARD') return 'stopped';
    if (phase === 'TASK_COMPLETE') return 'done';
    if (phase === 'IDLE') return 'ready';
    return 'active';
  }

  function currentStatus() {
    if (manualMessage) return manualMessage;
    if (sim.phase === 'OBSTACLE_WARNING') return 'Paused for a virtual obstacle warning. A detour is being planned.';
    if (sim.phase === 'DETOUR') return 'Following the detour computed from the supplied test map.';
    if (sim.phase === 'TASK_COMPLETE') return 'Task finished in the software simulation.';
    if (sim.phase === 'STOPPED') return 'Simulator stopped. No physical motor is connected.';
    if (sim.phase === 'SCAN') return 'Checking the supported task and virtual range inputs…';
    if (sim.phase === 'FOLLOW_COMMAND') return 'Following the task route in the fixed map…';
    if (sim.phase === 'NO_ROUTE') return 'The planner found no route in this test fixture.';
    return 'Ready when you are.';
  }

  function fitText(text, x, y, color = '#9fb0b8', size = 10, align = 'left') {
    ctx.fillStyle = color;
    ctx.font = `600 ${size}px ui-monospace, Consolas, monospace`;
    ctx.textAlign = align;
    ctx.fillText(text, x, y);
  }

  function roundedRect(x, y, w, h, radius, fill, stroke) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, radius);
    ctx.fillStyle = fill;
    ctx.fill();
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }

  function drawGrid(now) {
    const w = 12 * scale;
    const h = 7 * scale;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const bg = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    bg.addColorStop(0, '#14232c');
    bg.addColorStop(1, '#101a22');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    roundedRect(origin.x, origin.y, w, h, 8, '#111c24', '#2d414c');

    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(105,137,150,.18)';
    for (let x = 0; x <= 12; x += 1) {
      const px = origin.x + x * scale;
      ctx.beginPath(); ctx.moveTo(px, origin.y); ctx.lineTo(px, origin.y + h); ctx.stroke();
    }
    for (let y = 0; y <= 7; y += 1) {
      const py = origin.y + y * scale;
      ctx.beginPath(); ctx.moveTo(origin.x, py); ctx.lineTo(origin.x + w, py); ctx.stroke();
    }
    for (let x = 0; x <= 12; x += 2) fitText(`${x}m`, origin.x + x * scale, origin.y + h + 18, '#617783', 9, 'center');
    for (let y = 0; y <= 7; y += 1) fitText(`${y}`, origin.x - 17, origin.y + y * scale + 3, '#617783', 9, 'center');
    fitText('SUPPLIED MAP GEOMETRY', origin.x + 1, origin.y - 16, '#79939f', 9);
    fitText('TOP VIEW / SIMULATED', origin.x + w - 2, origin.y - 16, '#79939f', 9, 'right');

    for (const obstacle of sim.world.obstacles) {
      const x = origin.x + obstacle.x * scale;
      const y = origin.y + obstacle.y * scale;
      const ow = obstacle.w * scale;
      const oh = obstacle.h * scale;
      roundedRect(x + 2, y + 3, ow, oh, 5, 'rgba(4,9,12,.23)', null);
      const grad = ctx.createLinearGradient(x, y, x + ow, y + oh);
      grad.addColorStop(0, '#344b58'); grad.addColorStop(1, '#263b47');
      roundedRect(x, y, ow, oh, 5, grad, '#6a8290');
      ctx.fillStyle = 'rgba(159,183,192,.16)';
      for (let s = -oh; s < ow; s += 17) {
        ctx.beginPath(); ctx.moveTo(x + Math.max(0, s), y + Math.max(0, -s));
        ctx.lineTo(x + Math.min(ow, s + oh), y + Math.min(oh, oh + s));
        ctx.strokeStyle = 'rgba(170,194,202,.12)'; ctx.stroke();
      }
    }

    const goal = sim.goal;
    if (goal) {
      const gx = origin.x + goal.x * scale;
      const gy = origin.y + goal.y * scale;
      ctx.beginPath(); ctx.arc(gx, gy, 15 + Math.sin(now / 340) * 2, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(129,222,200,.6)'; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.beginPath(); ctx.arc(gx, gy, 5, 0, Math.PI * 2); ctx.fillStyle = '#81dec8'; ctx.fill();
      fitText('TASK END', gx, gy - 21, '#9fe7d7', 8, 'center');
    }
  }

  function drawPath() {
    const points = sim.path;
    if (!points || points.length < 2) return;
    ctx.beginPath();
    points.forEach((p, i) => {
      const x = origin.x + p.x * scale;
      const y = origin.y + p.y * scale;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.setLineDash(sim.phase === 'DETOUR' || sim.phase === 'TASK_COMPLETE' ? [] : [5, 7]);
    ctx.strokeStyle = sim.phase === 'OBSTACLE_WARNING' ? 'rgba(239,188,104,.68)' : 'rgba(129,222,200,.82)';
    ctx.lineWidth = sim.phase === 'DETOUR' ? 3 : 2;
    ctx.stroke();
    ctx.setLineDash([]);

    const history = sim.trace;
    if (history.length > 1) {
      ctx.beginPath();
      history.forEach((p, i) => {
        const x = origin.x + p.x * scale;
        const y = origin.y + p.y * scale;
        if (!i) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = 'rgba(129,222,200,.3)'; ctx.lineWidth = 1.5; ctx.stroke();
    }
  }

  function drawRangeFans(pose, now) {
    const px = origin.x + pose.x * scale;
    const py = origin.y + pose.y * scale;
    const pulse = 0.5 + 0.5 * Math.sin(now / 240);
    const warning = sim.phase === 'OBSTACLE_WARNING';
    const color = warning ? '239,188,104' : '104,208,190';
    for (const direction of [pose.theta, pose.theta + Math.PI]) {
      const radius = direction === pose.theta ? Math.min(200, Math.max(38, sim.snapshot().front * scale)) : Math.min(130, Math.max(35, sim.snapshot().rear * scale));
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.arc(px, py, radius, direction - .17, direction + .17);
      ctx.closePath();
      ctx.fillStyle = `rgba(${color},${.045 + pulse * .025})`;
      ctx.fill();
      ctx.strokeStyle = `rgba(${color},${.2 + pulse * .18})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    // The narrow forward IR cue is represented as a separate, virtual proximity fan.
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.arc(px, py, 53, pose.theta - .36, pose.theta + .36);
    ctx.closePath();
    ctx.fillStyle = warning ? 'rgba(239,188,104,.10)' : 'rgba(104,208,190,.035)';
    ctx.fill();
  }

  function drawRobot(pose, now) {
    const px = origin.x + pose.x * scale;
    const py = origin.y + pose.y * scale;
    ctx.save();
    ctx.translate(px, py);
    ctx.rotate(pose.theta);

    // A small top-down simulated chassis; this is a graphic, not a physical CAD model.
    ctx.shadowColor = 'rgba(0,0,0,.42)'; ctx.shadowBlur = 15; ctx.shadowOffsetY = 5;
    roundedRect(-22, -16, 44, 32, 10, '#e3ecea', '#ffffff');
    ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    roundedRect(-19, -19, 11, 7, 2, '#0b1116', null);
    roundedRect(8, -19, 11, 7, 2, '#0b1116', null);
    roundedRect(-19, 12, 11, 7, 2, '#0b1116', null);
    roundedRect(8, 12, 11, 7, 2, '#0b1116', null);
    roundedRect(-9, -9, 18, 18, 5, '#a8b9bb', '#92a6aa');
    ctx.beginPath(); ctx.moveTo(15, 0); ctx.lineTo(7, -4); ctx.lineTo(7, 4); ctx.closePath();
    ctx.fillStyle = sim.phase === 'OBSTACLE_WARNING' ? '#efbc68' : '#52c9b1'; ctx.fill();
    if (running) {
      ctx.beginPath(); ctx.arc(0, 0, 28 + Math.sin(now / 180) * 2, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(129,222,200,${.18 + .12 * Math.sin(now / 210)})`; ctx.lineWidth = 1; ctx.stroke();
    }
    ctx.restore();
    fitText('KITTY', px, py + 37, '#ccd8d9', 9, 'center');
  }

  function updateReadouts() {
    const state = sim.snapshot();
    const front = Math.max(0, Math.min(4, state.front));
    const rear = Math.max(0, Math.min(4, state.rear));
    document.getElementById('frontValue').textContent = `${state.front.toFixed(2)} m`;
    document.getElementById('rearValue').textContent = `${state.rear.toFixed(2)} m`;
    document.getElementById('frontBar').style.width = `${front / 4 * 100}%`;
    document.getElementById('rearBar').style.width = `${rear / 4 * 100}%`;
    document.getElementById('irValue').textContent = state.ir ? 'NEAR' : 'CLEAR';
    document.getElementById('irLamp').parentElement.dataset.near = String(state.ir);
    document.getElementById('phaseText').textContent = phaseLabel(sim.phase);
    document.getElementById('phaseBadge').dataset.tone = phaseTone(sim.phase);
    document.getElementById('statusText').textContent = currentStatus();
    document.body.classList.toggle('warning', sim.phase === 'OBSTACLE_WARNING');
    runButton.disabled = running || paused;
    pauseButton.disabled = !running && !paused;
    pauseButton.textContent = paused ? 'Resume' : 'Pause';
    updateSequence();
    updateEvents();
  }

  function updateSequence() {
    const phase = sim.phase;
    const active = phase === 'IDLE' ? null : phase;
    const rank = { SCAN: 1, FOLLOW_COMMAND: 2, OBSTACLE_WARNING: 3, DETOUR: 4, TASK_COMPLETE: 5 };
    const current = phase === 'STOPPED' ? 0 : rank[phase] || 0;
    document.querySelectorAll('.sequence-step').forEach((step, index) => {
      const key = step.dataset.step;
      step.classList.toggle('active', key === active);
      step.classList.toggle('complete', phase === 'TASK_COMPLETE' || (current > 0 && index + 1 < current));
      if (phase === 'STOPPED') step.classList.remove('complete');
    });
  }

  function eventText(event) {
    if (event.type === 'command_accepted') return 'Supported room-check command accepted.';
    if (event.type === 'obstacle_detected') return 'Virtual range input triggered the obstacle pause.';
    if (event.type === 'buzzer_warning') return 'Robot held stopped; virtual buzzer warning.';
    if (event.type === 'detour_planned') return 'Route recomputed using the supplied map.';
    if (event.type === 'task_complete') return 'Supported test task completed.';
    if (event.type === 'command_stop') return 'STOP command halted simulator motion.';
    return event.type.replaceAll('_', ' ');
  }

  function updateEvents() {
    if (renderedEventCount === sim.events.length) return;
    renderedEventCount = sim.events.length;
    const list = document.getElementById('eventList');
    list.replaceChildren();
    for (const event of sim.events.slice(-5)) {
      const item = document.createElement('li');
      if (event.type === 'buzzer_warning' || event.type === 'obstacle_detected') item.className = 'warning';
      const time = document.createElement('span'); time.className = 'event-time'; time.textContent = `${event.t.toFixed(1)}s`;
      const mark = document.createElement('span'); mark.className = 'event-mark';
      const text = document.createElement('span'); text.textContent = eventText(event);
      item.append(time, mark, text); list.append(item);
    }
    if (!sim.events.length) {
      const empty = document.createElement('li'); empty.className = 'empty-event'; empty.textContent = 'Start the command to see the simulator events.'; list.append(empty);
    }
  }

  function draw(now) {
    drawGrid(now);
    drawPath();
    drawRangeFans(sim.pose, now);
    drawRobot(sim.pose, now);
    updateReadouts();
  }

  async function beep() {
    if (!soundEnabled.checked) return;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    audio ||= new AudioContextClass();
    if (audio.state === 'suspended') await audio.resume();
    const oscillator = audio.createOscillator();
    const gain = audio.createGain();
    oscillator.type = 'sine'; oscillator.frequency.value = 880;
    gain.gain.setValueAtTime(.0001, audio.currentTime);
    gain.gain.exponentialRampToValueAtTime(.035, audio.currentTime + .012);
    gain.gain.exponentialRampToValueAtTime(.0001, audio.currentTime + .11);
    oscillator.connect(gain); gain.connect(audio.destination);
    oscillator.start(); oscillator.stop(audio.currentTime + .12);
  }

  function startTask() {
    manualMessage = '';
    if (sim.phase === 'TASK_COMPLETE' || sim.phase === 'STOPPED' || sim.phase === 'COLLISION_GUARD' || sim.phase === 'NO_ROUTE') {
      sim = new KittyCommandDemo.CompanionDemo();
      renderedEventCount = 0;
    }
    const accepted = sim.submit(input.value);
    if (!accepted) {
      manualMessage = 'That phrase is not in this demo’s supported command set.';
      draw(performance.now());
      return;
    }
    paused = false;
    running = true;
    accumulated = 0;
    previousTime = performance.now();
    if (audio && audio.state === 'suspended') audio.resume();
    draw(previousTime);
  }

  runButton.addEventListener('click', startTask);
  input.addEventListener('keydown', event => { if (event.key === 'Enter') startTask(); });
  pauseButton.addEventListener('click', () => {
    if (running) { running = false; paused = true; manualMessage = 'Paused by the operator.'; }
    else if (paused) { running = true; paused = false; manualMessage = ''; previousTime = performance.now(); }
    draw(performance.now());
  });
  stopButton.addEventListener('click', () => {
    sim.submit('STOP'); running = false; paused = false; manualMessage = '';
    draw(performance.now());
  });
  resetButton.addEventListener('click', () => {
    sim = new KittyCommandDemo.CompanionDemo(); running = false; paused = false;
    manualMessage = ''; renderedEventCount = 0; accumulated = 0;
    draw(performance.now());
  });

  function frame(now) {
    if (!previousTime) previousTime = now;
    const elapsed = Math.min(.1, (now - previousTime) / 1000);
    previousTime = now;
    if (running) {
      accumulated += elapsed;
      while (accumulated >= 1 / 60) {
        sim.step();
        frameCount += 1;
        if (frameCount % 6 === 0) sim.record();
        if (sim.beep && !lastBeep) beep();
        lastBeep = sim.beep;
        accumulated -= 1 / 60;
        if (sim.phase === 'TASK_COMPLETE' || sim.phase === 'NO_ROUTE' || sim.phase === 'COLLISION_GUARD' || sim.phase === 'STOPPED') {
          running = false; paused = false; break;
        }
      }
    }
    draw(now);
    requestAnimationFrame(frame);
  }

  draw(0);
  requestAnimationFrame(frame);
})();

