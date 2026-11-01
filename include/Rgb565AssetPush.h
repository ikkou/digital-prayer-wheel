#pragma once

#include <stdint.h>

// DPW1 RGB565 frames are packed as little-endian R5G6B5 words. On the
// ESP32-S3, M5GFX's pushImage(uint16_t*) default (swap=false) treats those
// bytes as already bus-ordered and writes them unchanged. Enable its native
// RGB565 conversion only for this synchronous image push, then restore the
// display's previous setting so text/primitives and other renderers are not
// affected.
template <typename Display>
class ScopedRgb565SwapBytes {
 public:
  explicit ScopedRgb565SwapBytes(Display& display)
      : display_(display), previous_(display.getSwapBytes()) {
    display_.setSwapBytes(true);
  }

  ~ScopedRgb565SwapBytes() { display_.setSwapBytes(previous_); }

  ScopedRgb565SwapBytes(const ScopedRgb565SwapBytes&) = delete;
  ScopedRgb565SwapBytes& operator=(const ScopedRgb565SwapBytes&) = delete;

 private:
  Display& display_;
  bool previous_;
};

template <typename Display>
void pushRgb565LittleEndian(Display& display, int32_t x, int32_t y,
                            int32_t width, int32_t height,
                            const uint8_t* pixels) {
  ScopedRgb565SwapBytes<Display> byteOrder(display);
  display.pushImage(x, y, width, height,
                    reinterpret_cast<const uint16_t*>(pixels));
}
