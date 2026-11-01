#pragma once
#include "FeverModel.h"

// Code-native overlay shared by the actual display, preview and host checks.
// All geometry stays in the peripheral annulus, leaving the engraving clear.
template <typename Display>
void drawFeverEffects(Display& d, float angle, float speed, uint32_t nowMs,
                      const FeverFrame& f) {
  constexpr float pi = 3.14159265f;
  const float head = (angle - 90) * pi / 180;
  const float direction = speed < 0 ? -1.f : 1.f;
  const float gain = f.energy;
  const auto color = [&](float brightness, bool blue = false) {
    brightness = fmaxf(0, fminf(1, brightness));
    return blue ? d.color565(80 * brightness, 181 * brightness, 238 * brightness) :
                  d.color565(255 * brightness, 205 * brightness, 115 * brightness);
  };
  if (gain > 0.015f) {
    // Layered comet tails: cumulative stage sets size, speed sets live energy.
    const uint8_t lanes = 1 + f.stage / 2;
    for (uint8_t lane = 0; lane < lanes; ++lane) {
      const float radius = 104.f - lane * 6;
      const float span = (35 + f.stage * 22) * pi / 180;
      const float offset = lane * 0.72f;
      for (uint8_t seg = 0; seg < 12; ++seg) {
        const float tail = seg / 12.f;
        const float a = head - direction * (offset + span * tail);
        const float b = head - direction * (offset + span * (seg + 1) / 12.f);
        const auto c = color(gain * (1 - tail) * (1 - lane * 0.12f), lane == 2);
        for (uint8_t width = 0; width < 2 + f.stage / 2; ++width) {
          const float r = radius - width;
          d.drawLine(lroundf(120 + r * cosf(a)), lroundf(120 + r * sinf(a)),
                     lroundf(120 + r * cosf(b)), lroundf(120 + r * sinf(b)), c);
        }
      }
    }
    // Deterministic sparks: bounded population, no allocation/random generator.
    const uint8_t sparks = 3 + f.stage * 4;
    for (uint8_t i = 0; i < sparks; ++i) {
      const uint32_t period = 1500 + (i % 4) * 250;
      const float age = ((nowMs + i * 173U) % period) / static_cast<float>(period);
      const float a = head + i * 2.3999632f - direction * age * (0.45f + f.stage * 0.1f);
      const float r = 92 + age * 22;
      const float strength = gain * (1 - age) * (0.55f + 0.08f * f.stage);
      if (strength < 0.08f) continue;
      const int x = lroundf(120 + r * cosf(a)), y = lroundf(120 + r * sinf(a));
      const auto c = color(strength, f.stage >= 4 && i % 4 == 0);
      if (f.stage >= 3 && i % 3 == 0) {
        d.fillCircle(x, y, 4, color(strength * .18f));
        d.fillCircle(x, y, 2, c);
        d.fillCircle(x, y, 1, d.color565(255 * strength, 242 * strength, 206 * strength));
      } else d.fillCircle(x, y, 1, c);
      if (f.stage >= 2) {
        d.drawLine(x, y, lroundf(120 + (r - 4) * cosf(a)),
                    lroundf(120 + (r - 4) * sinf(a)), color(strength * .55f));
      }
    }
    // Radial rays at the upper tiers, contained inside the circular LCD.
    if (f.stage >= 3) {
      const uint8_t rays = 8 + f.stage * 2;
      for (uint8_t i = 0; i < rays; ++i) {
        const float a = head + 2 * pi * i / rays;
        const float wave = .5f + .5f * sinf(i * 1.73f + (nowMs % 3200U) * 2 * pi / 3200);
        const float r = 99 - wave * (2 + f.stage);
        d.drawLine(lroundf(120 + r * cosf(a)), lroundf(120 + r * sinf(a)),
                   lroundf(120 + 106 * cosf(a)), lroundf(120 + 106 * sinf(a)),
                   color(gain * (.25f + .55f * wave)));
      }
    }
  }
  // Every full turn sends an expanding wave; tier-up adds a second wave.
  if (f.burstGain > .015f) {
    const uint8_t waves = f.levelUp ? 2 : 1;
    for (uint8_t i = 0; i < waves; ++i) {
      const float p = f.burstProgress - i * .17f;
      if (p < 0) continue;
      const int r = lroundf(90 + 27 * p);
      d.drawCircle(120, 120, r, color(f.burstGain * (1 - i * .2f)));
      d.drawCircle(120, 120, r - 1, color(f.burstGain * .4f));
    }
  }
}
