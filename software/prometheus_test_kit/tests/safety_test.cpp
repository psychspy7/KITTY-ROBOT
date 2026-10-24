#include "../PrometheusTest/HttpGate.h"
#include "../PrometheusTest/SafetyCore.h"
#include "../PrometheusTest/Settings.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
using namespace prometheus;

Config bench() {
  Config c;
  c.motorsReady = true;
  c.allowNoRangeBench = true;
  return c;
}
void clear(Core &c, bool rear = false, uint32_t at = 0) {
  for (unsigned n = 0; n < 3; n++)
    c.range(rear, true, 500, at);
}
int main() {
  unsigned checks = 0;
  {
    assert(!settings::BoardPinLabelsVerified &&
           !settings::DriverLabelsLogicAndStandbyVerified &&
           !settings::MotorSupplyRatingsCurrentFuseAndWiringVerified &&
           !settings::WheelsRaisedAndBaseSecured &&
           !settings::FrontSensorPowerAndEchoVerified &&
           !settings::RearSensorPowerEchoAndPinsVerified &&
           !settings::LedResistorAndPolarityVerified &&
           !settings::BuzzerInterfaceVerified &&
           !settings::AllowNoRangeRaisedWheelTest);
    assert(!motorReleaseReady(false, false, false, settings::MeasuredMotorPackV,
                              settings::VerifiedMotorSupplyMinV,
                              settings::VerifiedMotorSupplyMaxV));
    ++checks;
  }
  {
    assert(motorReleaseReady(true, true, true, 4.8f, 4.0f, 6.0f));
    assert(!motorReleaseReady(false, true, true, 4.8f, 4.0f, 6.0f));
    assert(!motorReleaseReady(true, false, true, 4.8f, 4.0f, 6.0f));
    assert(!motorReleaseReady(true, true, false, 4.8f, 4.0f, 6.0f));
    const float bad[][3] = {{0, 0, 0},
                            {4.8f, -1, 6},
                            {4.8f, 6, 4},
                            {3, 4, 6},
                            {7, 4, 6},
                            {std::numeric_limits<float>::quiet_NaN(), 4, 6},
                            {5, 4, std::numeric_limits<float>::infinity()}};
    for (auto &v : bad)
      assert(!motorReleaseReady(true, true, true, v[0], v[1], v[2]));
    ++checks;
  }
  {
    const std::string get =
        "GET /api/state HTTP/1.1\r\nHost: 192.168.4.1\r\n\r\n";
    assert(inspectRequest(get.data(), get.size()) == RequestState::Ready);
    const std::string post =
        "POST /api/command HTTP/1.1\r\nContent-Type: "
        "application/x-www-form-urlencoded\r\nContent-Length: 5\r\n\r\na=bcd";
    assert(inspectRequest(post.data(), post.size()) == RequestState::Ready);
    assert(inspectRequest(post.data(), post.size() - 2) == RequestState::Wait);
    const std::string prefix = "POST /api/command HTTP/1.1\r\nContent-Type: "
                               "application/x-www-form-urlencoded\r\n";
    for (const std::string &tail :
         {std::string("Content-Length: 257\r\n\r\n"),
          std::string("Content-Length: -1\r\n\r\n"),
          std::string("Transfer-Encoding: chunked\r\n\r\n"),
          std::string("Content-Length: 1\r\nContent-Length: 1\r\n\r\nx")}) {
      std::string bad = prefix + tail;
      assert(inspectRequest(bad.data(), bad.size()) == RequestState::Reject);
    }
    std::string large(2049, 'x');
    assert(inspectRequest(large.data(), large.size()) == RequestState::Reject);
    assert(inspectRequest(large.data(), 1536) == RequestState::Reject);
    ++checks;
  }
  {
    Core c(Config{});
    assert(!c.arm(0));
    assert(!c.pulse(1, 1, 48, 150, 0));
    assert(c.left == 0 && c.right == 0);
    ++checks;
  }
  {
    Core c(bench());
    assert(!c.pulse(1, 1, 48, 150, 0));
    assert(c.arm(0));
    assert(c.pulse(1, 0, 48, 150, 0));
    c.tick(149);
    assert(c.left == 48 && c.right == 0);
    c.tick(150);
    assert(c.mode == Mode::Complete && c.left == 0);
    assert(!c.pulse(1, 1, 48, 150, 151));
    ++checks;
  }
  {
    const int bad[][4] = {{2, 0, 48, 150}, {0, -2, 48, 150}, {0, 0, 48, 150},
                          {1, 1, 81, 150}, {1, 1, 0, 150},   {1, 1, 48, 251},
                          {1, 1, 48, 0},   {1, 1, 48, 49}};
    for (const auto &v : bad) {
      Core c(bench());
      assert(c.arm(0));
      assert(!c.pulse(v[0], v[1], v[2], v[3], 0));
      assert(c.mode == Mode::Fault && c.left == 0 && c.right == 0);
    }
    ++checks;
  }
  {
    Core c(bench());
    c.arm(0);
    c.tick(401);
    assert(c.mode == Mode::Fault);
    assert(!c.beat(402));
    assert(!c.arm(403));
    c.reset();
    assert(c.arm(500));
    ++checks;
  }
  {
    Core c(bench());
    c.arm(0);
    c.pulse(1, 1, 48, 150, 0);
    c.estop();
    c.tick(10);
    assert(c.mode == Mode::Estop && c.left == 0 && c.right == 0);
    c.disarm();
    assert(c.mode == Mode::Estop);
    assert(!c.arm(11));
    c.reset();
    assert(c.arm(12));
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    Core c(cfg);
    assert(!c.arm(0));
    clear(c);
    assert(c.arm(0));
    c.pulse(1, 1, 48, 150, 0);
    c.range(false, true, 200, 10);
    c.tick(10);
    assert(c.mode == Mode::Blocked && c.left == 0);
    clear(c, false, 20);
    assert(!c.arm(20));
    c.reset();
    clear(c, false, 21);
    assert(c.arm(21));
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    Core c(cfg);
    clear(c);
    c.arm(0);
    c.pulse(1, 1, 48, 250, 0);
    c.range(false, false, 0, 10);
    c.tick(10);
    assert(c.mode == Mode::Fault && c.left == 0);
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    Core c(cfg);
    clear(c);
    c.arm(0);
    c.beat(200);
    c.pulse(1, 1, 48, 250, 200);
    c.tick(251);
    assert(c.mode == Mode::Fault && c.left == 0);
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    cfg.rearEnabled = true;
    Core c(cfg);
    clear(c);
    clear(c, true);
    c.arm(0);
    c.pulse(-1, -1, 48, 150, 0);
    c.range(true, true, 190, 10);
    c.tick(10);
    assert(c.mode == Mode::Blocked && c.right == 0);
    ++checks;
  }
  {
    Config cfg;
    cfg.motorsReady = true;
    Core c(cfg);
    assert(!c.arm(0));
    ++checks;
  }
  {
    Core c(bench());
    c.arm(0xFFFFFFF0u);
    c.pulse(1, -1, 48, 100, 0xFFFFFFF0u);
    c.tick(0x20u);
    assert(c.left == 48);
    c.tick(0x60u);
    assert(c.mode == Mode::Complete && c.right == 0);
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    Core c(cfg);
    c.range(false, true, 500, 0);
    c.range(false, true, 500, 0);
    assert(!c.arm(0));
    c.range(false, true, 500, 0);
    assert(c.arm(0));
    ++checks;
  }
  {
    Core c(bench());
    assert(c.arm(0));
    assert(c.pulse(1, 1, 48, 150, 0));
    assert(!c.pulse(1, 1, 48, 150, 100));
    c.tick(150);
    assert(c.mode == Mode::Complete && c.left == 0 && c.right == 0);
    ++checks;
  }
  {
    Core c(bench());
    assert(c.arm(0));
    assert(c.pulse(1, 1, 48, 150, 0));
    assert(!c.pulse(1, 1, 81, 150, 10));
    assert(c.mode == Mode::Fault && c.left == 0 && c.right == 0);
    ++checks;
  }
  {
    Core c(bench());
    assert(c.arm(0));
    assert(c.pulse(1, 1, 48, 150, 0));
    c.disarm();
    assert(c.mode == Mode::Disarmed && c.left == 0 && c.right == 0);
    assert(!c.beat(10));
    assert(!c.pulse(1, 1, 48, 150, 11));
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    Core c(cfg);
    clear(c);
    assert(c.arm(0));
    assert(c.pulse(-1, -1, 48, 150, 0));
    c.range(false, true, 150, 10);
    c.tick(10);
    assert(c.mode == Mode::Pulse);
    c.tick(150);
    assert(c.mode == Mode::Complete);
    ++checks;
  }
  {
    Config cfg = bench();
    cfg.frontEnabled = true;
    Core c(cfg);
    c.range(false, true, 500, 0);
    c.range(false, true, 500, 10);
    c.range(false, true, 500, 1000);
    assert(!c.arm(1000));
    c.range(false, true, 500, 1010);
    c.range(false, true, 500, 1020);
    assert(c.arm(1020));
    ++checks;
  }
  {
    int l, r;
    channelPulse(true, 1, true, l, r);
    assert(l == 1 && r == 0);
    channelPulse(true, -1, false, l, r);
    assert(l == 0 && r == -1);
    channelPulse(false, 1, false, l, r);
    assert(l == 1 && r == 0);
    channelPulse(false, -1, true, l, r);
    assert(l == 0 && r == -1);
    ++checks;
  }
  std::cout << checks << " safety cases passed; native software tests only\n";
}
