#pragma once
#include <math.h>
#include <stdint.h>

namespace prometheus {
inline bool motorReleaseReady(bool driverReady, bool electricalVerified,
                              bool wheelsRaised, float measured, float minimum,
                              float maximum) {
  return driverReady && electricalVerified && wheelsRaised &&
         isfinite(measured) && isfinite(minimum) && isfinite(maximum) &&
         minimum > 0 && maximum >= minimum && measured >= minimum &&
         measured <= maximum;
}
enum class Mode {
  Locked,
  Disarmed,
  Armed,
  Pulse,
  Complete,
  Blocked,
  Fault,
  Estop
};
struct Config {
  bool motorsReady = false;
  bool frontEnabled = false;
  bool rearEnabled = false;
  bool allowNoRangeBench = false;
};
struct Range {
  bool have = false, valid = false, blocked = true;
  unsigned mm = 0, clearCount = 0;
  uint32_t at = 0;
};

class Core {
public:
  static constexpr uint32_t LeaseMs = 400, SensorAgeMs = 250;
  static constexpr unsigned MaxPulseMs = 250, MaxDuty = 80, StopMm = 200,
                            ClearMm = 300;
  explicit Core(Config config) : cfg_(config) {
    mode = cfg_.motorsReady ? Mode::Disarmed : Mode::Locked;
    reason = cfg_.motorsReady ? "disarmed" : "motor setup not verified";
  }
  Mode mode = Mode::Locked;
  int left = 0, right = 0;
  const char *reason = "startup";
  Range front, rear;

  void range(bool isRear, bool valid, unsigned mm, uint32_t now) {
    Range &r = isRear ? rear : front;
    if (r.have && uint32_t(now - r.at) > SensorAgeMs) {
      r.clearCount = 0;
      r.blocked = true;
    }
    r.have = true;
    r.valid = valid && mm >= 20 && mm <= 4000;
    r.mm = mm;
    r.at = now;
    if (!r.valid) {
      r.clearCount = 0;
      r.blocked = true;
      return;
    }
    if (mm <= StopMm) {
      r.blocked = true;
      r.clearCount = 0;
    } else if (mm >= ClearMm) {
      if (r.clearCount < 3)
        ++r.clearCount;
      if (r.clearCount >= 3)
        r.blocked = false;
    } else
      r.clearCount = 0;
  }
  bool fresh(const Range &r, uint32_t now) const {
    return r.have && r.valid && uint32_t(now - r.at) <= SensorAgeMs;
  }
  bool active() const { return mode == Mode::Armed || mode == Mode::Pulse; }
  bool alarm() const {
    return mode == Mode::Estop || mode == Mode::Fault || mode == Mode::Blocked;
  }
  bool arm(uint32_t now) {
    tick(now);
    if (!cfg_.motorsReady || (mode != Mode::Disarmed && mode != Mode::Complete))
      return false;
    if (!cfg_.frontEnabled && !cfg_.rearEnabled && !cfg_.allowNoRangeBench) {
      reason = "no range enabled; bench exception not verified";
      return false;
    }
    if ((cfg_.frontEnabled &&
         (!fresh(front, now) || front.blocked || front.clearCount < 3)) ||
        (cfg_.rearEnabled &&
         (!fresh(rear, now) || rear.blocked || rear.clearCount < 3))) {
      reason = "need three fresh clear range samples";
      return false;
    }
    left = right = 0;
    mode = Mode::Armed;
    heartbeatAt_ = now;
    reason = "armed; one bounded pulse only";
    return true;
  }
  bool pulse(int l, int r, unsigned duty, unsigned ms, uint32_t now) {
    tick(now);
    if (l < -1 || l > 1 || r < -1 || r > 1 || (!l && !r) || duty == 0 ||
        duty > MaxDuty || ms < 50 || ms > MaxPulseMs) {
      fault("invalid pulse");
      return false;
    }
    if (mode != Mode::Armed)
      return false;
    if ((cfg_.frontEnabled && (l > 0 || r > 0) && front.blocked) ||
        (cfg_.rearEnabled && (l < 0 || r < 0) && rear.blocked)) {
      block("range obstacle");
      return false;
    }
    left = l * static_cast<int>(duty);
    right = r * static_cast<int>(duty);
    pulseAt_ = heartbeatAt_ = now;
    pulseMs_ = ms;
    mode = Mode::Pulse;
    reason = "raised-wheel test pulse";
    return true;
  }
  bool beat(uint32_t now) {
    tick(now); // A late packet must not revive an expired lease.
    if (!active())
      return false;
    heartbeatAt_ = now;
    return true;
  }
  void disarm() {
    left = right = 0;
    if (alarm())
      return;
    mode = cfg_.motorsReady ? Mode::Disarmed : Mode::Locked;
    reason = "disarmed";
  }
  void estop() {
    left = right = 0;
    mode = Mode::Estop;
    reason = "stop latched; reset then new arm";
  }
  void reset() {
    left = right = 0;
    front.clearCount = rear.clearCount = 0;
    front.blocked = rear.blocked = true;
    mode = cfg_.motorsReady ? Mode::Disarmed : Mode::Locked;
    reason = "reset; fresh checks and new arm required";
  }
  void externalFault(const char *constantReason) { fault(constantReason); }
  unsigned remaining(uint32_t now) const {
    if (mode != Mode::Pulse)
      return 0;
    uint32_t age = now - pulseAt_;
    return age >= pulseMs_ ? 0 : pulseMs_ - age;
  }
  void tick(uint32_t now) {
    if (!active()) {
      left = right = 0;
      return;
    }
    if (!cfg_.motorsReady) {
      fault("motor setup unavailable");
      return;
    }
    if (uint32_t(now - heartbeatAt_) > LeaseMs) {
      fault("command lease expired");
      return;
    }
    if ((cfg_.frontEnabled && !fresh(front, now)) ||
        (cfg_.rearEnabled && !fresh(rear, now))) {
      fault("range invalid or stale");
      return;
    }
    if (mode == Mode::Pulse) {
      if ((cfg_.frontEnabled && (left > 0 || right > 0) && front.blocked) ||
          (cfg_.rearEnabled && (left < 0 || right < 0) && rear.blocked)) {
        block("range obstacle");
        return;
      }
      if (uint32_t(now - pulseAt_) >= pulseMs_) {
        left = right = 0;
        mode = Mode::Complete;
        reason = "pulse complete; new arm required";
      }
    }
  }

private:
  Config cfg_;
  uint32_t heartbeatAt_ = 0, pulseAt_ = 0;
  unsigned pulseMs_ = 0;
  void fault(const char *why) {
    left = right = 0;
    mode = Mode::Fault;
    reason = why;
  }
  void block(const char *why) {
    left = right = 0;
    mode = Mode::Blocked;
    reason = why;
  }
};
inline void channelPulse(bool channelA, int direction, bool motorALeft,
                         int &left, int &right) {
  left = right = 0;
  if (channelA == motorALeft)
    left = direction;
  else
    right = direction;
}
inline const char *modeName(Mode m) {
  switch (m) {
  case Mode::Locked:
    return "LOCKED";
  case Mode::Disarmed:
    return "DISARMED";
  case Mode::Armed:
    return "ARMED";
  case Mode::Pulse:
    return "PULSE";
  case Mode::Complete:
    return "COMPLETE";
  case Mode::Blocked:
    return "OBSTACLE";
  case Mode::Fault:
    return "FAULT";
  case Mode::Estop:
    return "ESTOP";
  }
  return "FAULT";
}
} // namespace prometheus
