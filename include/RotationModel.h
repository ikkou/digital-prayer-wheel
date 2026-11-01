#pragma once

#include <stdint.h>
#include "SettingsModel.h"

class RotationModel {
 public:
  void setCountsPerRevolution(uint16_t counts);
  void applyDelta(int32_t deltaCounts, uint32_t nowMs);
  void update(uint32_t nowMs);

  float angleDegrees() const { return angleDegrees_; }
  float speedDegreesPerSecond() const { return speedDegreesPerSecond_; }
  bool moving() const { return moving_; }
  // Completed signed full turns from the last 12-o'clock boundary.
  // Reversing cancels partial progress; it never shifts the cue away from zero.
  uint32_t turnsCompleted() const { return turnsCompleted_; }
  uint32_t lastMotionAt() const { return lastMotionAt_; }
  uint16_t countsPerRevolution() const { return countsPerRevolution_; }

 private:
  uint16_t countsPerRevolution_ = kDialCountsPerPhysicalTurn;
  float angleDegrees_ = 0.0f;
  double signedTurnProgressDegrees_ = 0.0;
  float speedDegreesPerSecond_ = 0.0f;
  uint32_t lastMotionAt_ = 0;
  uint32_t lastSampleAt_ = 0;
  uint32_t turnsCompleted_ = 0;
  bool moving_ = false;
};
