#pragma once
#include <Arduino.h>
const char PROMETHEUS_DASHBOARD[] PROGMEM=R"PROM_DASH(<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>PROMETHEUS · Bench control</title>
    <style>
      :root {
        font-family:
          Segoe UI,
          Arial,
          sans-serif;
        color: #e3eef1;
        background: #0e1922;
        --mint: #75e4c7;
        --muted: #a5bac6;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
      }
      main {
        max-width: 1080px;
        margin: auto;
        padding: 30px 22px;
      }
      header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 15px;
        margin-bottom: 24px;
      }
      .eyebrow {
        color: var(--mint);
        font-size: 10px;
        letter-spacing: 2.6px;
      }
      h1 {
        font-size: 30px;
        margin: 9px 0 5px;
      }
      p {
        color: var(--muted);
        line-height: 1.7;
        font-size: 13px;
      }
      .badge {
        font-size: 10px;
        letter-spacing: 1px;
        color: #ffd1a0;
        border: 1px solid #8e7152;
        padding: 8px;
        border-radius: 5px;
      }
      .notice {
        background: #372d23;
        border: 1px solid #7d6247;
        padding: 13px 17px;
        border-radius: 9px;
        color: #f1d0a7;
      }
      .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
      }
      .card {
        background: #172833;
        border: 1px solid #304957;
        border-radius: 12px;
        padding: 22px;
        margin: 16px 0;
      }
      .card h2 {
        font-size: 15px;
        margin: 0 0 15px;
      }
      .telemetry {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      dt {
        font-size: 10px;
        color: var(--muted);
        letter-spacing: 1px;
      }
      dd {
        margin: 7px 0;
        font-size: 25px;
        color: var(--mint);
        font-family: Consolas, monospace;
      }
      .state {
        display: flex;
        gap: 20px;
        align-items: center;
        justify-content: space-between;
      }
      .state strong {
        font-size: 24px;
      }
      .state small {
        color: var(--muted);
        display: block;
        margin-top: 7px;
        line-height: 1.6;
      }
      button {
        background: #253f4e;
        color: #dfedf3;
        border: 1px solid #57717f;
        border-radius: 7px;
        padding: 12px 14px;
        font: inherit;
        font-size: 12px;
        cursor: pointer;
      }
      button:hover {
        background: #36566a;
      }
      button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      .primary {
        background: #77e3c7;
        color: #092a24;
        font-weight: bold;
        border-color: #77e3c7;
      }
      .danger {
        background: #8c3441;
        border-color: #d27b86;
        color: #fff;
        font-weight: bold;
      }
      .wide {
        width: 100%;
        margin: 10px 0;
      }
      .row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .row button {
        flex: 1;
      }
      .motor-buttons {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 9px;
        margin: 12px 0;
      }
      .muted,
      small {
        font-size: 11px;
        color: var(--muted);
        line-height: 1.7;
      }
      label {
        font-size: 12px;
        display: block;
        margin: 18px 0;
        color: #bdcfd9;
      }
      input[type="range"] {
        width: 100%;
        accent-color: var(--mint);
        margin-top: 12px;
      }
      #log {
        height: 180px;
        overflow: auto;
        white-space: pre-wrap;
        background: #0b1820;
        border-radius: 6px;
        padding: 12px;
        font:
          11px/1.8 Consolas,
          monospace;
      }
      #connection {
        color: #f0be86;
        font-size: 12px;
      }
      footer {
        border-top: 1px solid #304957;
        margin-top: 24px;
        padding-top: 15px;
        color: var(--muted);
        font-size: 10px;
      }
      button:focus-visible,
      input:focus-visible {
        outline: 3px solid #83f9d7;
        outline-offset: 3px;
      }
      @media (max-width: 700px) {
        main {
          padding: 20px 14px;
        }
        .grid {
          grid-template-columns: 1fr;
        }
        h1 {
          font-size: 25px;
        }
        .badge {
          max-width: 120px;
          text-align: center;
          font-size: 8px;
        }
        .state strong {
          font-size: 21px;
        }
        .card {
          padding: 18px;
        }
        dd {
          font-size: 22px;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <span class="eyebrow">TEAM PROMETHEUS × KITTY CORP</span>
          <h1>Bench control</h1>
          <span id="connection">Connecting to ESP32…</span>
        </div>
        <span class="badge">RAISED WHEELS ONLY</span>
      </header>
      <p class="notice">
        This page sends real commands to the ESP32 when its physical setup has
        been configured. Secure the base with wheels off the surface and keep
        the motor-power cutoff reachable. It is not a floor-driving or
        path-following program.
      </p>
      <section class="card state">
        <div>
          <strong id="mode">UNAVAILABLE</strong
          ><small id="reason"
            >Open http://192.168.4.1/ after joining PROMETHEUS_ESP32.</small
          >
        </div>
        <button id="estop" class="danger" disabled>■ LATCH STOP</button>
      </section>
      <div class="grid">
        <div>
          <section class="card">
            <h2>Actual sensor / output telemetry</h2>
            <dl class="telemetry">
              <div>
                <dt>FRONT</dt>
                <dd id="front">N/A</dd>
              </div>
              <div>
                <dt>REAR</dt>
                <dd id="rear">N/A</dd>
              </div>
              <div>
                <dt>LEFT / RIGHT PWM</dt>
                <dd id="pwm">— / —</dd>
              </div>
              <div>
                <dt>PULSE REMAINING</dt>
                <dd id="remaining">— ms</dd>
              </div>
            </dl>
            <p id="sensor-note">
              An unavailable/invalid reading is not a clear path.
            </p>
            <p class="muted">
              PWM is signed 8-bit duty, not measured wheel speed. Battery
              voltage/current and wheel travel are not measured by this sketch.
            </p>
          </section>
          <section class="card">
            <h2>Independent indicator tests</h2>
            <div class="row">
              <button id="led" disabled>LED: 1.5 s</button
              ><button id="beep" disabled>Buzzer: 150 ms</button>
            </div>
            <p class="muted">
              Each output needs its own verified configuration. Unknown buzzer
              stays disconnected.
            </p>
          </section>
        </div>
        <div>
          <section class="card">
            <h2>Motor test sequence</h2>
            <p id="setup-note">
              Motor outputs are locked until the setup checks are recorded in
              Settings.h. Do not change flags simply to unlock this page.
            </p>
            <div class="row">
              <button id="arm" class="primary" disabled>Arm one pulse</button
              ><button id="stop" disabled>Disarm / stop</button
              ><button id="reset" disabled>Reset latch</button>
            </div>
            <label
              >Test PWM duty <output id="duty-value">48 / 255</output
              ><input id="duty" type="range" min="1" max="80" value="48"
            /></label>
            <div class="motor-buttons">
              <button data-action="a+" disabled>A +</button
              ><button data-action="a-" disabled>A −</button
              ><button data-action="b+" disabled>B +</button
              ><button data-action="b-" disabled>B −</button>
            </div>
            <div class="motor-buttons">
              <button data-action="forward" disabled>
                Both + / forward test</button
              ><button data-action="back" disabled>Both − / reverse test</button
              ><button data-action="left" disabled>Left pivot test</button
              ><button data-action="right" disabled>Right pivot test</button>
            </div>
            <p id="pulse-note" class="muted">
              One click runs one bounded pulse; holding does not repeat. Arm
              again for the next test.
            </p>
            <p class="muted">
              Motor A/B physical side and polarity must be observed with lifted
              wheels. One forward sensor cannot protect reverse or swept turning
              space.
            </p>
          </section>
        </div>
      </div>
      <section class="card">
        <h2>Session log</h2>
        <div id="log" role="log" aria-live="polite"></div>
      </section>
      <footer>
        400 ms command lease · 250 ms range freshness · pulse hard limit 250 ms
        · 200 mm initial obstacle threshold · actual stopping behavior must be
        measured. A browser stop does not disconnect battery power.
      </footer>
    </main>
    <script>
      (() => {
        "use strict";
        const $ = (id) => document.getElementById(id),
          actions = [...document.querySelectorAll("[data-action]")];
        let token = "",
          sequence = 0,
          lastSample = 0,
          connected = false,
          needsArm = true,
          polling = false,
          posting = false,
          priorityPosting = 0,
          controlEpoch = 0,
          pageActive = true,
          hb = null,
          state = null,
          first = true;
        const random = new Uint8Array(12);
        crypto.getRandomValues(random);
        const client = Array.from(random, (b) =>
          b.toString(16).padStart(2, "0"),
        ).join("");
        const log = (text) => {
          const el = $("log");
          el.textContent = (
            new Date().toLocaleTimeString() +
            " " +
            text +
            "\n" +
            el.textContent
          ).slice(0, 6000);
        };
        function stopHeartbeat() {
          if (hb) {
            clearInterval(hb);
            hb = null;
          }
        }
        function validate(d) {
          const modes = [
            "LOCKED",
            "DISARMED",
            "ARMED",
            "PULSE",
            "COMPLETE",
            "OBSTACLE",
            "FAULT",
            "ESTOP",
          ];
          if (
            !d ||
            d.transport !== "esp32-hardware-test" ||
            !modes.includes(d.mode) ||
            typeof d.reason !== "string" ||
            !/^[a-f0-9]{32}$/.test(d.token) ||
            !Number.isInteger(d.sequence) ||
            d.sequence < 0 ||
            !Number.isInteger(d.sample_id) ||
            d.sample_id < 0
          )
            throw Error("Invalid device state");
          for (const key of ["front_mm", "rear_mm"])
            if (
              d[key] !== null &&
              (!Number.isInteger(d[key]) || d[key] < 20 || d[key] > 4000)
            )
              throw Error("Invalid range");
          for (const key of [
            "motors_ready",
            "front_enabled",
            "rear_enabled",
            "led_enabled",
            "buzzer_enabled",
          ])
            if (typeof d[key] !== "boolean") throw Error("Invalid setup state");
          for (const key of ["left_pwm", "right_pwm"])
            if (!Number.isInteger(d[key]) || Math.abs(d[key]) > 80)
              throw Error("Invalid PWM");
          if (
            !Number.isInteger(d.remaining_ms) ||
            d.remaining_ms < 0 ||
            d.remaining_ms > 250 ||
            !Number.isInteger(d.pulse_ms) ||
            d.pulse_ms < 50 ||
            d.pulse_ms > 250 ||
            !Number.isInteger(d.default_duty) ||
            d.default_duty < 1 ||
            d.default_duty > 80
          )
            throw Error("Invalid test limits");
          return d;
        }
        function render() {
          const d = state,
            busy = posting || priorityPosting > 0,
            active = d && ["ARMED", "PULSE"].includes(d.mode),
            canPulse =
              connected && d && d.mode === "ARMED" && !needsArm && !busy;
          $("connection").textContent = connected
            ? "Connected to ESP32 · real telemetry"
            : "Disconnected / unavailable";
          $("mode").textContent = connected && d ? d.mode : "UNAVAILABLE";
          $("reason").textContent =
            connected && d
              ? d.reason
              : "Join PROMETHEUS_ESP32 and open http://192.168.4.1/. No movement is enabled by reconnecting.";
          $("front").textContent =
            connected && d && d.front_mm !== null
              ? (d.front_mm / 10).toFixed(1) + " cm"
              : "N/A";
          $("rear").textContent =
            connected && d && d.rear_mm !== null
              ? (d.rear_mm / 10).toFixed(1) + " cm"
              : "N/A";
          $("pwm").textContent =
            connected && d ? d.left_pwm + " / " + d.right_pwm : "— / —";
          $("remaining").textContent =
            connected && d ? d.remaining_ms + " ms" : "— ms";
          $("arm").disabled =
            !connected ||
            !d?.motors_ready ||
            !pageActive ||
            busy ||
            ["FAULT", "ESTOP", "OBSTACLE", "PULSE"].includes(d?.mode);
          $("stop").disabled = !token;
          $("estop").disabled = !token;
          $("reset").disabled = !connected || busy;
          $("led").disabled = !connected || !d?.led_enabled || active || busy;
          $("beep").disabled =
            !connected || !d?.buzzer_enabled || active || busy;
          actions.forEach((b) => (b.disabled = !canPulse));
          $("duty").disabled = !!active;
          if (d && connected) {
            $("setup-note").textContent = d.motors_ready
              ? "Motor setup enabled by operator configuration; this is not an automatic electrical inspection."
              : "LOCKED: confirm board/driver labels, motor/current and supply checks, lifted wheels, and real voltage settings before enabling motor tests.";
            $("pulse-note").textContent =
              "One click: " +
              d.pulse_ms +
              " ms at the selected duty. Hard maximum 250 ms. New arm required after completion.";
            $("sensor-note").textContent =
              (d.front_enabled ? "Front enabled. " : "Front disabled. ") +
              (d.rear_enabled
                ? "Rear enabled."
                : "Rear disabled; bench-only reverse has no rear ranging.");
          }
          if (connected && active && !needsArm && !hb)
            hb = setInterval(() => {
              if (!posting && priorityPosting === 0)
                send("heartbeat").catch(handleFailure);
            }, 100);
          if (!connected || !active || needsArm) stopHeartbeat();
        }
        function apply(d) {
          validate(d);
          if (token && token !== d.token) {
            controlEpoch++;
            sequence = 0;
            lastSample = 0;
            needsArm = true;
            stopHeartbeat();
            log("Device restarted; new deliberate arm required.");
          }
          token = d.token;
          sequence = Math.max(sequence, d.sequence);
          if (d.sample_id < lastSample) return;
          lastSample = d.sample_id;
          const oldMode = state?.mode;
          state = d;
          connected = true;
          if (!["ARMED", "PULSE"].includes(d.mode)) {
            needsArm = true;
            stopHeartbeat();
          }
          if (first) {
            $("duty").value = d.default_duty;
            $("duty-value").textContent = d.default_duty + " / 255";
            first = false;
          }
          if (d.mode !== oldMode) log(d.mode + ": " + d.reason);
          render();
        }
        async function fetchJSON(url, options = {}) {
          const abort = new AbortController(),
            timer = setTimeout(() => abort.abort(), 650);
          try {
            const r = await fetch(url, {
              cache: "no-store",
              ...options,
              signal: abort.signal,
            });
            const d = await r.json();
            if (!r.ok) throw Error(d.error || "HTTP " + r.status);
            return d;
          } finally {
            clearTimeout(timer);
          }
        }
        function cancelled() {
          const e = new Error("Control transaction cancelled");
          e.name = "ControlCancelled";
          return e;
        }
        function cancelControl() {
          controlEpoch++;
          needsArm = true;
          stopHeartbeat();
        }
        function current(epoch, boot) {
          return (
            epoch === controlEpoch &&
            boot === token &&
            pageActive &&
            !document.hidden
          );
        }
        async function send(action, epoch = controlEpoch, priority = false) {
          if (!priority && posting) throw Error("Another command is pending");
          if (!token) throw Error("No device session");
          const boot = token;
          if (priority) priorityPosting++;
          else posting = true;
          render();
          try {
            const body = new URLSearchParams({
              action,
              client,
              seq: String(++sequence),
              duty: $("duty").value,
            });
            const d = await fetchJSON("/api/command", {
              method: "POST",
              headers: {
                "X-Prometheus-Token": boot,
                "Content-Type": "application/x-www-form-urlencoded",
              },
              body,
            });
            if (epoch !== controlEpoch || boot !== token) throw cancelled();
            apply(d);
            return d;
          } catch (e) {
            if (epoch !== controlEpoch || boot !== token) throw cancelled();
            throw e;
          } finally {
            if (priority) priorityPosting--;
            else posting = false;
            render();
          }
        }
        function bestEffortStop(action = "stop") {
          if (!token) return;
          const body = new URLSearchParams({
            action,
            client,
            seq: String(++sequence),
          });
          fetch("/api/command", {
            method: "POST",
            headers: {
              "X-Prometheus-Token": token,
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body,
            keepalive: true,
          }).catch(() => {});
        }
        function fail(error, fallback = "stop") {
          cancelControl();
          connected = false;
          bestEffortStop(fallback);
          render();
          log("Control interrupted: " + error.message);
        }
        function handleFailure(error) {
          if (error.name !== "ControlCancelled") fail(error);
        }
        async function priorityStop(action) {
          cancelControl();
          const epoch = controlEpoch;
          try {
            await send(action, epoch, true);
          } catch (e) {
            if (e.name !== "ControlCancelled") fail(e, action);
          }
        }
        async function poll() {
          if (polling) return;
          polling = true;
          try {
            apply(await fetchJSON("/api/state"));
          } catch (e) {
            if (connected || first) handleFailure(e);
          } finally {
            polling = false;
          }
        }
        $("arm").onclick = async () => {
          cancelControl();
          const epoch = controlEpoch,
            boot = token;
          if (!current(epoch, boot)) return;
          try {
            await send("stop", epoch);
            if (!current(epoch, boot)) throw cancelled();
            await send("arm", epoch);
            if (!current(epoch, boot)) throw cancelled();
            needsArm = false;
            render();
          } catch (e) {
            handleFailure(e);
          }
        };
        for (const id of ["stop", "estop"])
          $(id).onclick = () => priorityStop(id);
        $("reset").onclick = () => {
          cancelControl();
          send("reset").catch(handleFailure);
        };
        for (const id of ["led", "beep"])
          $(id).onclick = () => send(id).catch(handleFailure);
        actions.forEach(
          (b) =>
            (b.onclick = () => send(b.dataset.action).catch(handleFailure)),
        );
        $("duty").oninput = () =>
          ($("duty-value").textContent = $("duty").value + " / 255");
        function leave() {
          pageActive = false;
          cancelControl();
          bestEffortStop();
          render();
        }
        window.addEventListener("blur", leave);
        window.addEventListener("pagehide", leave);
        window.addEventListener("focus", () => {
          pageActive = true;
          render();
        });
        document.addEventListener("visibilitychange", () => {
          if (document.hidden) leave();
          else {
            pageActive = document.hasFocus();
            poll();
          }
        });
        window.addEventListener("keydown", (e) => {
          if (
            e.code === "Space" &&
            !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)
          ) {
            e.preventDefault();
            priorityStop("estop");
          }
        });
        if (
          location.protocol === "http:" &&
          location.hostname === "192.168.4.1"
        ) {
          poll();
          setInterval(() => {
            if (!document.hidden) poll();
          }, 200);
        } else {
          $("connection").textContent =
            "Device-hosted page · open http://192.168.4.1/";
          render();
        }
      })();
    </script>
  </body>
</html>
)PROM_DASH";
