#pragma once

#include <math.h>
#include <stdint.h>

// Shared with the host preview: the position cue never fades with the trail.
template <typename Display>
void drawRingIndicator(Display& display, float angleDegrees, float speedDegreesPerSecond,
                       float afterglowAgeSeconds, bool quietPresentation) {
  constexpr float pi = 3.14159265f;
  constexpr float radius = 111.0f;
  const auto dark = display.color565(3, 6, 13);
  const auto track = display.color565(100, 74, 39);
  const auto tick = display.color565(154, 115, 61);
  const auto gold = display.color565(234, 173, 76);
  const auto core = display.color565(255, 232, 168);
  const float head = (angleDegrees - 90.0f) * pi / 180.0f;
  const float direction = speedDegreesPerSecond < 0.0f ? -1.0f : 1.0f;
  const float speedGain = fminf(1.0f, fabsf(speedDegreesPerSecond) / 920.0f);
  const float decay = afterglowAgeSeconds < 0.0f ? 1.0f :
      (afterglowAgeSeconds > 1.2f ? 0.0f : expf(-afterglowAgeSeconds / 0.48f));
  const float gain = speedGain * decay * (quietPresentation ? 0.4f : 0.85f);

  display.drawCircle(120, 120, 111, track);
  for (uint8_t quarter = 0; quarter < 4; ++quarter) {
    const float phase = (quarter * 90.0f - 90.0f) * pi / 180.0f;
    display.drawLine(lroundf(120 + 114 * cosf(phase)), lroundf(120 + 114 * sinf(phase)),
                     lroundf(120 + 117 * cosf(phase)), lroundf(120 + 117 * sinf(phase)), tick);
  }

  // Reverse motion mirrors the trail; the head uses the unmodified input angle.
  if (gain > 0.025f) {
    const float span = (10.0f + 36.0f * gain) * pi / 180.0f;
    for (uint8_t segment = 16; segment > 0; --segment) {
      const float tail = static_cast<float>(segment) / 16.0f;
      const float phase0 = head - direction * span * tail;
      const float phase1 = head - direction * span * (segment - 1) / 16.0f;
      const float light = gain * (1.0f - tail * 0.8f);
      const auto color = display.color565(static_cast<uint8_t>(100 + 140 * light),
          static_cast<uint8_t>(74 + 104 * light), static_cast<uint8_t>(39 + 37 * light));
      for (uint8_t r = 110; r <= 112; ++r) {
        display.drawLine(lroundf(120 + r * cosf(phase0)), lroundf(120 + r * sinf(phase0)),
                         lroundf(120 + r * cosf(phase1)), lroundf(120 + r * sinf(phase1)), color);
      }
    }
  }

  const int32_t x = lroundf(120 + radius * cosf(head));
  const int32_t y = lroundf(120 + radius * sinf(head));
  display.fillCircle(x, y, 5, dark);
  display.fillCircle(x, y, 4, gold);
  display.fillCircle(x, y, 2, core);
}
