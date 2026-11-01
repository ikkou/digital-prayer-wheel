#pragma once

#include <math.h>
#include <stdint.h>

// Select a uniform frame from the wheel's normalized angle; exact 360° wraps to frame 0.
inline uint16_t frameIndexForAngle(float angleDegrees, uint16_t frameCount) {
  if (frameCount == 0) return 0;
  float normalized = fmodf(angleDegrees, 360.0f);
  if (normalized < 0.0f) normalized += 360.0f;
  uint16_t frame = static_cast<uint16_t>(normalized * frameCount / 360.0f);
  return frame < frameCount ? frame : 0;
}
