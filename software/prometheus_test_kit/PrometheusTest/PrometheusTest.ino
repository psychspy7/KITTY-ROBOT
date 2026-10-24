// Team Prometheus: staged, raised-wheel commissioning. NOT floor navigation.
// Default Settings.h starts AP/Serial only and does not initialize robot GPIOs.
#include <Arduino.h>
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error                                                                         \
    "This candidate GPIO plan requires classic ESP32; do not use on C3/S3/S2."
#endif
#include "Dashboard.h"
#include "HttpGate.h"
#include "RobotPins.h"
#include "SafetyCore.h"
#include "Settings.h"
#include <Preferences.h>
#include <WebServer.h>
#include <WiFi.h>
#include <esp_arduino_version.h>
#include <esp_system.h>
#include <math.h>

GuardedWebServer server(80);
prometheus::Core core(prometheus::Config{});
portMUX_TYPE controlGuard = portMUX_INITIALIZER_UNLOCKED;
bool driverIOReady = false, frontIOReady = false, rearIOReady = false,
     ledIOReady = false, buzzerIOReady = false;
bool serverReady = false, motorSetupReady = false;
volatile unsigned apClients = 0;
uint32_t outputGeneration = 0, lastSequence = 0, stateCounter = 0;
bool ledTest = false, buzzerTest = false;
uint32_t ledTestAt = 0, buzzerTestAt = 0;
char owner[25] = {};
String bootToken, accessPassword;
char serialLine[64];
unsigned serialUsed = 0;

bool pwmAttach(unsigned channel, int pin, unsigned hz) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)channel;
  return ledcAttach(pin, hz, 8);
#else
  double actual = ledcSetup(channel, hz, 8);
  ledcAttachPin(pin, channel);
  return actual > 0;
#endif
}
void pwmWrite(unsigned channel, int pin, unsigned duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)channel;
  ledcWrite(pin, duty);
#else
  (void)pin;
  ledcWrite(channel, duty);
#endif
}
String randomHex(unsigned bytes) {
  static const char hex[] = "0123456789abcdef";
  String value;
  value.reserve(bytes * 2);
  for (unsigned i = 0; i < bytes; i++) {
    unsigned b = esp_random() & 255;
    value += hex[b >> 4];
    value += hex[b & 15];
  }
  return value;
}
// Call only while holding controlGuard. STBY writes are short GPIO operations;
// no LEDC, Wi-Fi, allocation or Serial calls occur inside this critical
// section.
void inhibitIfStoppedLocked() {
  if (driverIOReady &&
      (core.mode != prometheus::Mode::Pulse || (!core.left && !core.right)))
    digitalWrite(pins::Standby, LOW);
}
void applyMotorPair(int left, int right, uint32_t generation) {
  if (!driverIOReady)
    return;
  digitalWrite(pins::Standby, LOW);
  int a = (settings::MotorALeft ? left : right) * settings::MotorASign;
  int b = (settings::MotorALeft ? right : left) * settings::MotorBSign;
  digitalWrite(pins::Ain1, a > 0 ? HIGH : LOW);
  digitalWrite(pins::Ain2, a < 0 ? HIGH : LOW);
  digitalWrite(pins::Bin1, b > 0 ? HIGH : LOW);
  digitalWrite(pins::Bin2, b < 0 ? HIGH : LOW);
  pwmWrite(0, pins::Pwma, static_cast<unsigned>(abs(a)));
  pwmWrite(1, pins::Pwmb, static_cast<unsigned>(abs(b)));
  portENTER_CRITICAL(&controlGuard);
  // A stop/reset/new command arriving during PWM writes invalidates this copy.
  bool current = generation == outputGeneration &&
                 core.mode == prometheus::Mode::Pulse && core.left == left &&
                 core.right == right && (left || right);
  digitalWrite(pins::Standby, current ? HIGH : LOW);
  portEXIT_CRITICAL(&controlGuard);
}
void buzzerOutput(bool on) {
  if (!buzzerIOReady)
    return;
  if (settings::BuzzerMode == settings::BuzzerKind::Passive2kHz)
    pwmWrite(2, pins::Buzzer, on ? 128 : 0);
  else
    digitalWrite(pins::Buzzer, (on == (settings::BuzzerMode ==
                                       settings::BuzzerKind::ActiveHigh))
                                   ? HIGH
                                   : LOW);
}
void controlTask(void *) {
  TickType_t last = xTaskGetTickCount();
  prometheus::Mode previous = prometheus::Mode::Locked;
  uint32_t doneAt = 0;
  bool haveDone = false;
  for (;;) {
    uint32_t now;
    int l, r;
    uint32_t generation;
    prometheus::Mode mode;
    bool alarm, ledExtra, buzzExtra;
    portENTER_CRITICAL(&controlGuard);
    now = millis();
    int oldL = core.left, oldR = core.right;
    core.tick(now);
    if (core.left != oldL || core.right != oldR)
      ++outputGeneration;
    inhibitIfStoppedLocked();
    l = core.left;
    r = core.right;
    mode = core.mode;
    alarm = core.alarm();
    generation = outputGeneration;
    ledExtra = ledTest && uint32_t(now - ledTestAt) < 1500;
    buzzExtra = buzzerTest && uint32_t(now - buzzerTestAt) < 150;
    if (!ledExtra)
      ledTest = false;
    if (!buzzExtra)
      buzzerTest = false;
    portEXIT_CRITICAL(&controlGuard);
    applyMotorPair(l, r, generation);
    if (mode == prometheus::Mode::Complete && previous != mode) {
      doneAt = now;
      haveDone = true;
    }
    unsigned doneAge = now - doneAt;
    bool finishing = haveDone && !alarm && doneAge < 400;
    bool flash = mode == prometheus::Mode::Pulse ? true
                 : alarm                         ? ((now / 150) % 2)
                         : ((now / (apClients ? 1000 : 500)) % 2);
    if (finishing)
      flash = doneAge < 80 || (doneAge >= 160 && doneAge < 240);
    if (ledIOReady)
      digitalWrite(pins::Led,
                   (alarm ? flash : (flash || ledExtra)) ? HIGH : LOW);
    buzzerOutput(buzzExtra || (alarm && (now / 200) % 2) ||
                 (finishing && doneAge < 80));
    previous = mode;
    vTaskDelayUntil(&last, pdMS_TO_TICKS(10));
  }
}
void readSonar(bool rear) {
  int trig = rear ? pins::RearTrig : pins::FrontTrig,
      echo = rear ? pins::RearEcho : pins::FrontEcho;
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long us = pulseIn(echo, HIGH, 25000UL);
  unsigned mm = static_cast<unsigned>(us * 343UL / 2000UL);
  uint32_t now;
  portENTER_CRITICAL(&controlGuard);
  now = millis();
  int oldL = core.left, oldR = core.right;
  core.range(rear, us > 0, mm, now);
  core.tick(now);
  if (oldL != core.left || oldR != core.right)
    ++outputGeneration;
  inhibitIfStoppedLocked();
  portEXIT_CRITICAL(&controlGuard);
}
void sensorTask(void *) {
  for (;;) {
    if (frontIOReady) {
      readSonar(false);
      vTaskDelay(pdMS_TO_TICKS(60));
    }
    if (rearIOReady) {
      readSonar(true);
      vTaskDelay(pdMS_TO_TICKS(60));
    }
    if (!frontIOReady && !rearIOReady)
      vTaskDelay(pdMS_TO_TICKS(60));
  }
}
void headers() {
  server.sendHeader("Cache-Control", "no-store");
  server.sendHeader("X-Content-Type-Options", "nosniff");
  server.sendHeader("Content-Security-Policy",
                    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
                    "frame-ancestors 'none'; base-uri 'none'");
}
bool hostValid() {
  String h = server.hostHeader();
  return h == "192.168.4.1" || h == "192.168.4.1:80";
}
void errorReply(unsigned code, const char *message) {
  headers();
  server.send(code, "application/json",
              String("{\"error\":\"") + message + "\"}");
}
void stateReply() {
  if (!hostValid()) {
    errorReply(403, "Open http://192.168.4.1/");
    return;
  }
  uint32_t now;
  prometheus::Mode mode;
  const char *reason;
  int l, r;
  bool frontValid, rearValid;
  unsigned f, back, remaining;
  uint32_t seq;
  portENTER_CRITICAL(&controlGuard);
  now = millis();
  core.tick(now);
  inhibitIfStoppedLocked();
  mode = core.mode;
  reason = core.reason;
  l = core.left;
  r = core.right;
  frontValid = frontIOReady && core.fresh(core.front, now);
  rearValid = rearIOReady && core.fresh(core.rear, now);
  f = core.front.mm;
  back = core.rear.mm;
  remaining = core.remaining(now);
  seq = lastSequence;
  portEXIT_CRITICAL(&controlGuard);
  char frontText[16], rearText[16];
  if (frontValid)
    snprintf(frontText, sizeof(frontText), "%u", f);
  else
    strcpy(frontText, "null");
  if (rearValid)
    snprintf(rearText, sizeof(rearText), "%u", back);
  else
    strcpy(rearText, "null");
  char json[1200];
  int n = snprintf(
      json, sizeof(json),
      "{\"transport\":\"esp32-hardware-test\",\"mode\":\"%s\",\"reason\":\"%"
      "s\",\"left_pwm\":%d,\"right_pwm\":%d,\"remaining_ms\":%u,\"front_mm\":%"
      "s,\"rear_mm\":%s,\"front_enabled\":%s,\"rear_enabled\":%s,\"led_"
      "enabled\":%s,\"buzzer_enabled\":%s,\"motors_ready\":%s,\"sequence\":%lu,"
      "\"token\":\"%s\",\"stop_mm\":%u,\"default_duty\":%u,\"pulse_ms\":%u,"
      "\"sample_id\":%lu}",
      prometheus::modeName(mode), reason, l, r, remaining, frontText, rearText,
      frontIOReady ? "true" : "false", rearIOReady ? "true" : "false",
      ledIOReady ? "true" : "false", buzzerIOReady ? "true" : "false",
      motorSetupReady ? "true" : "false", static_cast<unsigned long>(seq),
      bootToken.c_str(), prometheus::Core::StopMm, settings::DefaultDuty,
      settings::PulseMs, static_cast<unsigned long>(++stateCounter));
  if (n < 0 || n >= static_cast<int>(sizeof(json))) {
    errorReply(500, "State unavailable");
    return;
  }
  headers();
  server.send(200, "application/json", json);
}
bool decimal(const String &s, uint32_t &value) {
  if (!s.length() || s.length() > 10)
    return false;
  uint64_t n = 0;
  for (unsigned i = 0; i < s.length(); i++) {
    if (s[i] < '0' || s[i] > '9')
      return false;
    n = n * 10 + (s[i] - '0');
    if (n > UINT32_MAX)
      return false;
  }
  value = static_cast<uint32_t>(n);
  return true;
}
bool clientValid(const String &client) {
  if (client.length() != 24)
    return false;
  for (unsigned i = 0; i < 24; i++)
    if (!((client[i] >= '0' && client[i] <= '9') ||
          (client[i] >= 'a' && client[i] <= 'f')))
      return false;
  return true;
}
bool motionPair(const String &action, int &left, int &right) {
  left = right = 0;
  if (action == "a+" || action == "a-" || action == "b+" || action == "b-")
    prometheus::channelPulse(action[0] == 'a', action[1] == '+' ? 1 : -1,
                             settings::MotorALeft, left, right);
  else if (action == "forward")
    left = right = 1;
  else if (action == "back")
    left = right = -1;
  else if (action == "left") {
    left = -1;
    right = 1;
  } else if (action == "right") {
    left = 1;
    right = -1;
  } else
    return false;
  return true;
}
void commandReply() {
  if (!hostValid() || server.header("Origin") != "http://192.168.4.1" ||
      server.header("X-Prometheus-Token") != bootToken) {
    errorReply(403, "Use current robot page and session");
    return;
  }
  if (server.args() > 4) {
    errorReply(413, "Command too large");
    return;
  }
  String client = server.arg("client"), action = server.arg("action");
  uint32_t sequence, duty = settings::DefaultDuty;
  if (!clientValid(client) || !decimal(server.arg("seq"), sequence) ||
      !sequence) {
    errorReply(400, "Invalid client or sequence");
    return;
  }
  int l = 0, r = 0;
  bool motion = motionPair(action, l, r);
  if (motion && (!decimal(server.arg("duty"), duty) || !duty ||
                 duty > prometheus::Core::MaxDuty)) {
    errorReply(400, "Duty must be 1..80");
    return;
  }
  uint32_t now;
  bool ok = false;
  portENTER_CRITICAL(&controlGuard);
  now = millis();
  core.tick(now);
  inhibitIfStoppedLocked();
  bool stopAction = action == "stop" || action == "estop";
  bool ownerOK =
      !core.active() || owner[0] == 0 || strcmp(owner, client.c_str()) == 0;
  if (stopAction) {
    if (sequence > lastSequence)
      lastSequence = sequence;
    if (action == "estop")
      core.estop();
    else
      core.disarm();
    owner[0] = 0;
    ++outputGeneration;
    ok = true;
  } else if (sequence > lastSequence && ownerOK) {
    lastSequence = sequence;
    if (action == "arm") {
      ok = core.arm(now);
      if (ok)
        memcpy(owner, client.c_str(), 25);
      ++outputGeneration;
    } else if (action == "heartbeat")
      ok = strcmp(owner, client.c_str()) == 0 && core.beat(now);
    else if (action == "reset") {
      core.reset();
      owner[0] = 0;
      ++outputGeneration;
      ok = true;
    } else if (motion) {
      ok = strcmp(owner, client.c_str()) == 0 &&
           core.pulse(l, r, duty, settings::PulseMs, now);
      ++outputGeneration;
    } else if (action == "led" && !core.active() && ledIOReady) {
      ledTest = true;
      ledTestAt = now;
      ok = true;
    } else if (action == "beep" && !core.active() && buzzerIOReady) {
      buzzerTest = true;
      buzzerTestAt = now;
      ok = true;
    }
  }
  inhibitIfStoppedLocked();
  portEXIT_CRITICAL(&controlGuard);
  if (!ok) {
    errorReply(409, "Rejected: check setup flags, owner, mode, fresh range and "
                    "sequence; reset after a fault");
    return;
  }
  stateReply();
}
void printStatus() {
  uint32_t now;
  prometheus::Mode mode;
  const char *why;
  prometheus::Range front, rear;
  int l, r;
  portENTER_CRITICAL(&controlGuard);
  now = millis();
  mode = core.mode;
  why = core.reason;
  front = core.front;
  rear = core.rear;
  l = core.left;
  r = core.right;
  portEXIT_CRITICAL(&controlGuard);
  Serial.printf("%s | %s | PWM %d/%d | front ", prometheus::modeName(mode), why,
                l, r);
  if (frontIOReady && front.have && front.valid &&
      uint32_t(now - front.at) <= prometheus::Core::SensorAgeMs)
    Serial.printf("%u mm", front.mm);
  else
    Serial.print("N/A");
  Serial.print(" | rear ");
  if (rearIOReady && rear.have && rear.valid &&
      uint32_t(now - rear.at) <= prometheus::Core::SensorAgeMs)
    Serial.printf("%u mm", rear.mm);
  else
    Serial.print("N/A");
  Serial.println();
}
void serialCommand(const String &line) {
  if (line == "help") {
    Serial.println(
        "status | stop | reset | led | beep | test a+ | test a- | test b+ | "
        "test b- | test forward | test back | test left | test right");
    return;
  }
  if (line == "status") {
    printStatus();
    return;
  }
  String action = line.startsWith("test ") ? line.substring(5) : line;
  int l = 0, r = 0;
  bool motion = line.startsWith("test ") && motionPair(action, l, r);
  bool ok = false;
  uint32_t now;
  portENTER_CRITICAL(&controlGuard);
  now = millis();
  core.tick(now);
  if (line == "stop") {
    core.estop();
    owner[0] = 0;
    ok = true;
  } else if (line == "reset") {
    core.reset();
    owner[0] = 0;
    ok = true;
  } else if (line == "led" && !core.active() && ledIOReady) {
    ledTest = true;
    ledTestAt = now;
    ok = true;
  } else if (line == "beep" && !core.active() && buzzerIOReady) {
    buzzerTest = true;
    buzzerTestAt = now;
    ok = true;
  } else if (motion && !core.active() && core.arm(now)) {
    strcpy(owner, "SERIAL");
    ok = core.pulse(l, r, settings::DefaultDuty, settings::PulseMs, now);
  }
  ++outputGeneration;
  inhibitIfStoppedLocked();
  portEXIT_CRITICAL(&controlGuard);
  Serial.println(
      ok ? "Accepted; bench-only bounded test"
         : "Rejected; see status, setup checks or reset after fault");
  printStatus();
}
void pollSerial() {
  while (Serial.available()) {
    char c = static_cast<char>(Serial.read());
    if (c == '\r' || c == '\n') {
      if (serialUsed) {
        serialLine[serialUsed] = 0;
        String line(serialLine);
        serialUsed = 0;
        line.trim();
        line.toLowerCase();
        serialCommand(line);
      }
    } else if (c >= 32 && c <= 126) {
      if (serialUsed + 1 < sizeof(serialLine))
        serialLine[serialUsed++] = c;
      else {
        serialUsed = 0;
        portENTER_CRITICAL(&controlGuard);
        core.estop();
        ++outputGeneration;
        inhibitIfStoppedLocked();
        portEXIT_CRITICAL(&controlGuard);
        Serial.println("Line too long; stop latched");
      }
    }
  }
}
void setup() {
  Serial.begin(115200);
  static_assert(settings::DefaultDuty > 0 &&
                    settings::DefaultDuty <= prometheus::Core::MaxDuty,
                "Invalid commissioning duty");
  static_assert(settings::PulseMs >= 50 &&
                    settings::PulseMs <= prometheus::Core::MaxPulseMs,
                "Invalid pulse duration");
  static_assert((settings::MotorASign == 1 || settings::MotorASign == -1) &&
                    (settings::MotorBSign == 1 || settings::MotorBSign == -1),
                "Motor signs must be +/-1");
  bool board = settings::BoardPinLabelsVerified;
  if (board && settings::DriverLabelsLogicAndStandbyVerified) {
    pinMode(pins::Standby, OUTPUT);
    digitalWrite(pins::Standby, LOW);
    const int outputs[] = {pins::Ain1, pins::Ain2, pins::Bin1, pins::Bin2};
    for (int pin : outputs) {
      pinMode(pin, OUTPUT);
      digitalWrite(pin, LOW);
    }
    bool a = pwmAttach(0, pins::Pwma, settings::PwmHz),
         b = pwmAttach(1, pins::Pwmb, settings::PwmHz);
    driverIOReady = a && b;
    if (a)
      pwmWrite(0, pins::Pwma, 0);
    if (b)
      pwmWrite(1, pins::Pwmb, 0);
  }
  frontIOReady = board && settings::FrontSensorPowerAndEchoVerified;
  rearIOReady = board && settings::RearSensorPowerEchoAndPinsVerified;
  if (frontIOReady) {
    pinMode(pins::FrontTrig, OUTPUT);
    digitalWrite(pins::FrontTrig, LOW);
    pinMode(pins::FrontEcho, INPUT);
  }
  if (rearIOReady) {
    pinMode(pins::RearTrig, OUTPUT);
    digitalWrite(pins::RearTrig, LOW);
    pinMode(pins::RearEcho, INPUT);
  }
  ledIOReady = board && settings::LedResistorAndPolarityVerified;
  if (ledIOReady) {
    pinMode(pins::Led, OUTPUT);
    digitalWrite(pins::Led, LOW);
  }
  buzzerIOReady = board && settings::BuzzerInterfaceVerified &&
                  settings::BuzzerMode != settings::BuzzerKind::Disconnected;
  if (buzzerIOReady) {
    if (settings::BuzzerMode == settings::BuzzerKind::Passive2kHz)
      buzzerIOReady = pwmAttach(2, pins::Buzzer, 2000);
    else
      pinMode(pins::Buzzer, OUTPUT);
    buzzerOutput(false);
  }
  bool controlOK = xTaskCreate(controlTask, "prom-control", 4096, nullptr, 4,
                               nullptr) == pdPASS;
  bool sensorOK = xTaskCreate(sensorTask, "prom-range", 3072, nullptr, 2,
                              nullptr) == pdPASS;
  if (!controlOK || !sensorOK) {
    Serial.println("Task creation failed; motor configuration remains locked");
    return;
  }
  Preferences store;
  if (!store.begin("promTest", false)) {
    Serial.println("Credential storage failed; motors locked");
    return;
  }
  accessPassword = store.getString("apPass", "");
  if (accessPassword.length() < 12) {
    accessPassword = randomHex(8);
    if (!store.putString("apPass", accessPassword)) {
      store.end();
      Serial.println("Credential save failed; motors locked");
      return;
    }
  }
  store.end();
  bootToken = randomHex(16);
  WiFi.mode(WIFI_AP);
  bool apConfig =
      WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1),
                        IPAddress(255, 255, 255, 0));
  if (!apConfig || !WiFi.softAP(settings::AccessPointName,
                                accessPassword.c_str(), 1, false, 2)) {
    Serial.println("AP failed; motors locked");
    return;
  }
  prometheus::Config config;
  config.motorsReady = prometheus::motorReleaseReady(
      driverIOReady, settings::MotorSupplyRatingsCurrentFuseAndWiringVerified,
      settings::WheelsRaisedAndBaseSecured, settings::MeasuredMotorPackV,
      settings::VerifiedMotorSupplyMinV, settings::VerifiedMotorSupplyMaxV);
  config.frontEnabled = frontIOReady;
  config.rearEnabled = rearIOReady;
  config.allowNoRangeBench = settings::AllowNoRangeRaisedWheelTest &&
                             settings::WheelsRaisedAndBaseSecured;
  motorSetupReady = config.motorsReady;
  portENTER_CRITICAL(&controlGuard);
  core = prometheus::Core(config);
  ++outputGeneration;
  portEXIT_CRITICAL(&controlGuard);
  const char *names[] = {"Host", "Origin", "X-Prometheus-Token"};
  server.collectHeaders(names, 3);
  server.on("/", HTTP_GET, [] {
    if (!hostValid()) {
      errorReply(403, "Open http://192.168.4.1/");
      return;
    }
    headers();
    server.send_P(200, "text/html", PROMETHEUS_DASHBOARD);
  });
  server.on("/api/state", HTTP_GET, stateReply);
  server.on("/api/command", HTTP_POST, commandReply);
  server.onNotFound([] { errorReply(404, "Not found"); });
  server.begin();
  serverReady = true;
  Serial.println("PROMETHEUS bench test; not floor navigation");
  Serial.print("AP: ");
  Serial.println(settings::AccessPointName);
  Serial.print("AP password: ");
  Serial.println(accessPassword);
  Serial.println("Open http://192.168.4.1/ | Serial 115200, Newline | help");
  printStatus();
}
void loop() {
  if (serverReady)
    server.handleClient();
  pollSerial();
  static uint32_t lastPrint = 0, lastClients = 0;
  uint32_t now = millis();
  if (now - lastClients >= 500) {
    lastClients = now;
    apClients = WiFi.softAPgetStationNum();
  }
  if (now - lastPrint >= 1000) {
    lastPrint = now;
    printStatus();
  }
  delay(2);
}
