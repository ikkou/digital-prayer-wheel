#pragma once

#include "AppTypes.h"

class TouchGestureDetector {
 public:
  TouchGesture poll(bool pressed, uint32_t nowMs) {
    TouchGesture gesture = TouchGesture::None;
    if (pressed != touchDown_ && static_cast<uint32_t>(nowMs - lastTransitionAt_) >= kDebounceMs) {
      lastTransitionAt_ = nowMs;
      touchDown_ = pressed;
      if (pressed) {
        touchStartedAt_ = nowMs;
        longPressSent_ = false;
      } else if (!longPressSent_) {
        gesture = TouchGesture::ShortTap;
      }
    }

    if (touchDown_ && !longPressSent_ &&
        static_cast<uint32_t>(nowMs - touchStartedAt_) >= kLongPressMs) {
      longPressSent_ = true;
      gesture = TouchGesture::LongPress;
    }
    return gesture;
  }

 private:
  static constexpr uint32_t kDebounceMs = 35;
  static constexpr uint32_t kLongPressMs = 700;
  bool touchDown_ = false;
  bool longPressSent_ = false;
  uint32_t touchStartedAt_ = 0;
  uint32_t lastTransitionAt_ = 0;
};
