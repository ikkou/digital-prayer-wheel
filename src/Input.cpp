#include "Input.h"

#include <M5Dial.h>

void Input::begin() {
  previousEncoder_ = static_cast<int32_t>(M5Dial.Encoder.read());
}

InputFrame Input::poll(uint32_t nowMs) {
  M5Dial.update();

  InputFrame frame;
  frame.nowMs = nowMs;
  const int32_t encoderNow = static_cast<int32_t>(M5Dial.Encoder.read());
  frame.encoderDelta = encoderNow - previousEncoder_;
  frame.encoderCount = encoderNow;
  previousEncoder_ = encoderNow;

  const m5::touch_detail_t touch = M5Dial.Touch.getDetail();
  frame.gesture = touchDetector_.poll(touch.isPressed(), nowMs);
  return frame;
}
