#pragma once

#include <stdint.h>

class Audio {
 public:
  void startup(bool muted);
  void revolution(bool muted);
  void confirm(bool muted);
  void update(bool muted);

 private:
  void cue(float frequency, uint32_t duration, bool muted);
  bool wasMuted_ = false;
};
