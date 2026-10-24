#pragma once
#include <stddef.h>
#include <stdint.h>
#include <string.h>

namespace prometheus {
enum class RequestState { Wait, Reject, Ready };
constexpr size_t MaxRequestBytes = 2048, MaxHeaderBytes = 1536,
                 MaxBodyBytes = 256;
inline bool headerEquals(const char *p, size_t n, const char *name) {
  if (strlen(name) != n)
    return false;
  for (size_t i = 0; i < n; i++) {
    char c = p[i];
    if (c >= 'A' && c <= 'Z')
      c += 'a' - 'A';
    if (c != name[i])
      return false;
  }
  return true;
}
// Inspect bounded bytes BEFORE WebServer allocates strings or parses a body.
// No dynamic allocation, blocking reads, chunked bodies or multipart uploads.
inline RequestState inspectRequest(const char *data, size_t count) {
  if (count > MaxRequestBytes)
    return RequestState::Reject;
  for (size_t i = 0; i < count; i++)
    if (data[i] == 0)
      return RequestState::Reject;
  size_t end = 0;
  for (size_t i = 3; i < count; i++)
    if (memcmp(data + i - 3, "\r\n\r\n", 4) == 0) {
      end = i + 1;
      break;
    }
  if (!end)
    return count >= MaxHeaderBytes ? RequestState::Reject : RequestState::Wait;
  if (end > MaxHeaderBytes)
    return RequestState::Reject;
  size_t line = 0;
  while (line + 1 < end && memcmp(data + line, "\r\n", 2) != 0)
    line++;
  bool post = line >= 24 && memcmp(data, "POST /api/command HTTP/1.", 24) == 0;
  bool get = line >= 14 && memcmp(data, "GET /", 5) == 0;
  if (!post && !get)
    return RequestState::Reject;
  unsigned body = 0, lengths = 0;
  bool encoded = false;
  for (size_t at = line + 2; at + 2 < end;) {
    size_t next = at;
    while (next + 1 < end && memcmp(data + next, "\r\n", 2) != 0)
      next++;
    size_t colon = at;
    while (colon < next && data[colon] != ':')
      colon++;
    if (colon == next)
      return RequestState::Reject;
    size_t value = colon + 1;
    while (value < next && (data[value] == ' ' || data[value] == '\t'))
      value++;
    if (headerEquals(data + at, colon - at, "transfer-encoding"))
      return RequestState::Reject;
    if (headerEquals(data + at, colon - at, "content-length")) {
      if (++lengths > 1 || value == next)
        return RequestState::Reject;
      for (size_t j = value; j < next; j++) {
        if (data[j] < '0' || data[j] > '9')
          return RequestState::Reject;
        body = body * 10 + unsigned(data[j] - '0');
        if (body > MaxBodyBytes)
          return RequestState::Reject;
      }
    }
    if (headerEquals(data + at, colon - at, "content-type")) {
      constexpr char type[] = "application/x-www-form-urlencoded";
      encoded = next - value == sizeof(type) - 1 &&
                memcmp(data + value, type, sizeof(type) - 1) == 0;
    }
    at = next + 2;
  }
  if (post && (lengths != 1 || !encoded || body == 0))
    return RequestState::Reject;
  if (get && body)
    return RequestState::Reject;
  if (count < end + body)
    return RequestState::Wait;
  return count == end + body ? RequestState::Ready : RequestState::Reject;
}
} // namespace prometheus

#ifdef ARDUINO
#include <WebServer.h>
#include <WiFi.h>
#include <lwip/sockets.h>
// Four independent admission slots prevent one incomplete request from owning
// WebServer's synchronous parser. Approved bytes remain in the socket via PEEK.
class GuardedWebServer : public WebServer {
public:
  explicit GuardedWebServer(int port) : WebServer(port) {}
  void handleClient() {
    WiFiClient incoming = _server.available();
    if (incoming) {
      bool kept = false;
      for (unsigned i = 0; i < 4; i++)
        if (!waiting_[i]) {
          waiting_[i] = incoming;
          started_[i] = millis();
          kept = true;
          break;
        }
      if (!kept)
        incoming.stop();
    }
    char request[prometheus::MaxRequestBytes + 1];
    for (unsigned step = 0; step < 4; step++) {
      unsigned i = (cursor_ + step) % 4;
      WiFiClient &client = waiting_[i];
      if (!client)
        continue;
      if (!client.connected() || uint32_t(millis() - started_[i]) > 350) {
        client.stop();
        continue;
      }
      int n =
          recv(client.fd(), request, sizeof(request), MSG_PEEK | MSG_DONTWAIT);
      if (n <= 0)
        continue;
      auto state = prometheus::inspectRequest(request, static_cast<size_t>(n));
      if (state == prometheus::RequestState::Reject) {
        client.stop();
        continue;
      }
      if (state == prometheus::RequestState::Wait)
        continue;
      _currentClient = client;
      waiting_[i] = WiFiClient();
      cursor_ = (i + 1) % 4;
      // WiFiClient timeout units are seconds on Arduino ESP32 2.x.
      // This is separate from the nonblocking admission deadline above.
      _currentClient.setTimeout(1);
      _currentStatus = HC_WAIT_READ;
      _statusChange = millis();
      WebServer::handleClient();
      _currentClient.stop();
      _currentClient = WiFiClient();
      _currentStatus = HC_NONE;
      return;
    }
  }

private:
  WiFiClient waiting_[4];
  uint32_t started_[4] = {};
  unsigned cursor_ = 0;
};
#endif
