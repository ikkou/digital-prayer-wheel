#pragma once
#include <math.h>
#include <stdint.h>

inline uint8_t feverStage(uint32_t turns) {
  return turns >= 20 ? 5 : turns >= 10 ? 4 : turns >= 6 ? 3 :
         turns >= 3 ? 2 : turns >= 1 ? 1 : 0;
}
inline uint32_t feverNextTarget(uint8_t stage) {
  constexpr uint32_t targets[] = {1, 3, 6, 10, 20, 20};
  return targets[stage < 5 ? stage : 5];
}
inline float feverProgress(uint32_t turns) {
  const uint8_t stage = feverStage(turns);
  if (stage == 5) return 1.0f;
  const uint32_t previous = stage == 0 ? 0 : feverNextTarget(stage - 1);
  return static_cast<float>(turns - previous) / (feverNextTarget(stage) - previous);
}

struct FeverFrame {
  uint32_t turns = 0;
  uint8_t stage = 0;
  float energy = 0;
  float burstProgress = 1;
  float burstGain = 0;
  bool levelUp = false;
};

class FeverModel {
 public:
  static constexpr uint32_t kBurstMs = 1800;
  void observeTurns(uint32_t turns, uint32_t nowMs) {
    if (turns == turns_) return;
    levelUp_ = feverStage(turns) > feverStage(turns_);
    hasBurst_ = turns > turns_;
    burstAt_ = nowMs;
    turns_ = turns;
  }
  bool burstActive(uint32_t nowMs) const {
    return hasBurst_ && static_cast<uint32_t>(nowMs - burstAt_) < kBurstMs;
  }
  FeverFrame frame(uint32_t nowMs, float speed, float afterglowAgeSeconds) const {
    FeverFrame f;
    f.turns = turns_;
    f.stage = feverStage(turns_);
    const float decay = afterglowAgeSeconds < 0 ? 1 :
        fmaxf(0, 1 - afterglowAgeSeconds / 2.2f);
    const float motion = 0.45f + 0.55f * fminf(1, fabsf(speed) / 720);
    f.energy = decay * decay * motion;
    f.levelUp = levelUp_;
    if (burstActive(nowMs)) {
      f.burstProgress = static_cast<float>(static_cast<uint32_t>(nowMs - burstAt_)) / kBurstMs;
      f.burstGain = (1 - f.burstProgress) * (levelUp_ ? 1 : 0.6f);
    }
    return f;
  }
 private:
  uint32_t turns_ = 0;
  uint32_t burstAt_ = 0;
  bool hasBurst_ = false;
  bool levelUp_ = false;
};
