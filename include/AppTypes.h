#pragma once

#include <stdint.h>

enum class AppState : uint8_t { Boot, Idle, Rotation, Afterglow, Settings };
enum class TouchGesture : uint8_t { None, ShortTap, LongPress };

struct InputFrame {
  int32_t encoderDelta = 0;
  int32_t encoderCount = 0;
  TouchGesture gesture = TouchGesture::None;
  uint32_t nowMs = 0;
};
