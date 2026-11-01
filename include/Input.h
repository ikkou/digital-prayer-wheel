#pragma once

#include "AppTypes.h"
#include "TouchGestureDetector.h"

class Input {
 public:
  void begin();
  InputFrame poll(uint32_t nowMs);

 private:
  int32_t previousEncoder_ = 0;
  TouchGestureDetector touchDetector_;
};
