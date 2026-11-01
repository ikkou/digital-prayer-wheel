#include "Audio.h"

#include <M5Dial.h>

namespace {
constexpr uint8_t kCueChannel = 0;
}

void Audio::cue(float frequency, uint32_t duration, bool muted) {
  if (muted) return;
  M5Dial.Speaker.tone(frequency, duration, kCueChannel, true);
}

void Audio::startup(bool muted) { cue(2600, 48, muted); }
void Audio::revolution(bool muted) { cue(2050, 24, muted); }
void Audio::confirm(bool muted) { cue(3050, 18, muted); }

void Audio::update(bool muted) {
  if (muted && !wasMuted_) M5Dial.Speaker.stop(kCueChannel);
  wasMuted_ = muted;
}
