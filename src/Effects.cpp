#include "Effects.h"
#include "RingIndicator.h"
#include "FeverDrawing.h"

#include <M5Dial.h>

void Effects::draw(float angleDegrees, float speedDegreesPerSecond, float afterglowAgeSeconds,
                   Presentation presentation, uint32_t nowMs) const {
  if (presentation == Presentation::Fever) {
    drawFeverEffects(M5Dial.Display, angleDegrees, speedDegreesPerSecond, nowMs,
                     fever_.frame(nowMs, speedDegreesPerSecond, afterglowAgeSeconds));
  }
  // Position marker is always last so rewards never hide the 12-o'clock cue.
  drawRingIndicator(M5Dial.Display, angleDegrees, speedDegreesPerSecond,
                    afterglowAgeSeconds, presentation == Presentation::Quiet);
}
