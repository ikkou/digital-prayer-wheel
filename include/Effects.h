#pragma once
#include "FeverModel.h"
#include "Presentation.h"

class Effects {
 public:
  void draw(float angleDegrees, float speedDegreesPerSecond, float afterglowAgeSeconds,
            Presentation presentation, uint32_t nowMs) const;
  void observeTurns(uint32_t turns, uint32_t nowMs) { fever_.observeTurns(turns, nowMs); }
  bool burstActive(uint32_t nowMs) const { return fever_.burstActive(nowMs); }
  FeverFrame feverFrame(uint32_t nowMs, float speed, float age) const { return fever_.frame(nowMs, speed, age); }
 private:
  FeverModel fever_;
};
