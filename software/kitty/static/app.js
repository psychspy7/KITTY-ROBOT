'use strict';
const $ = id => document.getElementById(id);
let state = null, connected = false, chatting = false, lastReply = '', speaking = false;
if (location.pathname === '/face') document.body.classList.add('face-only');

function notice(message) {
  $('notice').textContent = message;
  $('notice').style.display = message ? 'block' : 'none';
}

function face() {
  const requested = $('expression').value;
  let expression = !connected ? 'sleeping' : (requested === 'auto' ? state.face : requested);
  if (connected && chatting) expression = 'thinking';
  if (connected && speaking) expression = 'speaking';
  if (connected && ['ESTOP', 'FAULT'].includes(state.mode)) expression = 'alert';
  $('face').dataset.expression = expression;
  $('face').setAttribute('aria-label', `KITTY ${expression}`);
  $('expressionLabel').textContent = connected ? expression.toUpperCase() : 'DISCONNECTED';
  const center = connected && state.observation ? state.observation.center_x : 0;
  $('face').style.setProperty('--look', `${Math.round(center * 9)}px`);
}

function update(s) {
  state = s; connected = true;
  $('connection').textContent = 'LOCAL PREVIEW CONNECTED';
  $('mode').textContent = s.mode;
  $('reason').textContent = s.reason;
  $('age').textContent = s.frame_age_ms === null ? '—' : `${s.frame_age_ms} ms`;
  $('command').textContent = `${s.command.linear_m_s.toFixed(2)} m/s · ${s.command.angular_rad_s.toFixed(2)} rad/s · preview only`;
  $('truth').textContent = `${s.fixture.running ? 'DEVELOPER FIXTURE RUNNING' : 'NO LIVE CAMERA'} · PHYSICAL OUTPUT DISABLED`;
  face();
}

async function post(path, data) {
  const response = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  if (result.state) update(result.state);
  return result;
}

async function action(name, extra = {}) {
  try { notice(''); await post('/api/action', {action: name, ...extra}); }
  catch (error) { notice(error.message); }
}
$('run').onclick = () => action('run_fixture', {scenario: $('scenario').value});
for (const button of document.querySelectorAll('[data-action]')) button.onclick = () => action(button.dataset.action);
$('expression').onchange = face;
$('fullscreen').onclick = async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await $('face').requestFullscreen();
  } catch { notice('Full screen is unavailable in this browser. Face view still works.'); }
};

function bubble(text, kind) {
  const p = document.createElement('p'); p.className = kind; p.textContent = text;
  $('chatLog').append(p); $('chatLog').scrollTop = $('chatLog').scrollHeight;
  while ($('chatLog').children.length > 20) $('chatLog').firstElementChild.remove();
}
$('chatForm').onsubmit = async event => {
  event.preventDefault();
  const text = $('chatInput').value.trim();
  if (!text || chatting) return;
  chatting = true; face(); bubble(text, 'question'); $('chatInput').value = '';
  const submit = $('chatForm').querySelector('button'); submit.disabled = true;
  try {
    const result = await post('/api/chat', {text});
    lastReply = result.reply; bubble(lastReply, 'reply');
    if ($('speak').checked && 'speechSynthesis' in window) {
      speechSynthesis.cancel();
      const speech = new SpeechSynthesisUtterance(lastReply);
      speech.onstart = () => { speaking = true; face(); };
      speech.onend = speech.onerror = () => { speaking = false; face(); };
      speechSynthesis.speak(speech);
    }
  } catch (error) { notice(error.message); }
  finally { chatting = false; submit.disabled = false; face(); }
};

async function poll() {
  try {
    const response = await fetch('/api/state', {cache: 'no-store'});
    if (!response.ok) throw new Error('Preview unavailable');
    update(await response.json());
  } catch {
    connected = false; $('connection').textContent = 'DISCONNECTED';
    $('truth').textContent = 'STATE UNAVAILABLE · PHYSICAL OUTPUT DISABLED';
    face();
  } finally { setTimeout(poll, 150); }
}
poll();
