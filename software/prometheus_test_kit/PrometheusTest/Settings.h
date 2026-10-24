#pragma once
// STOP: these defaults are intentionally locked. They are not observations.
// Complete the PDF's physical checks before enabling the corresponding stage.
namespace settings {
constexpr bool BoardPinLabelsVerified = false;
constexpr bool DriverLabelsLogicAndStandbyVerified = false;
constexpr bool MotorSupplyRatingsCurrentFuseAndWiringVerified = false;
constexpr bool WheelsRaisedAndBaseSecured = false;
// Only for the motor-only stage with physically raised wheels. Never floor use.
constexpr bool AllowNoRangeRaisedWheelTest = false;
constexpr bool FrontSensorPowerAndEchoVerified = false;
constexpr bool RearSensorPowerEchoAndPinsVerified = false;
constexpr bool LedResistorAndPolarityVerified = false;
constexpr bool BuzzerInterfaceVerified = false;
enum class BuzzerKind { Disconnected, ActiveHigh, ActiveLow, Passive2kHz };
constexpr BuzzerKind BuzzerMode = BuzzerKind::Disconnected;

// Enter measured/supplier-supported values; zero is intentionally invalid.
constexpr float MeasuredMotorPackV = 0.0f;
constexpr float VerifiedMotorSupplyMinV = 0.0f;
constexpr float VerifiedMotorSupplyMaxV = 0.0f;
constexpr int MotorASign = 1, MotorBSign = 1; // Determine with lifted wheels.
constexpr bool MotorALeft = true;
constexpr unsigned DefaultDuty =
    48; // 8-bit PWM 0..255. Not a voltage/current rating.
constexpr unsigned PulseMs = 150;
constexpr unsigned PwmHz = 15000;
constexpr const char *AccessPointName = "PROMETHEUS_ESP32";
} // namespace settings
