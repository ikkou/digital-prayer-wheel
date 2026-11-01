#include "RotationModel.h"

#include <math.h>

void RotationModel::setCountsPerRevolution(uint16_t counts) {
  if (counts >= 32 && counts <= 2048) countsPerRevolution_ = counts;
}

void RotationModel::applyDelta(int32_t deltaCounts, uint32_t nowMs) {
  if (deltaCounts == 0) return;
  const uint32_t elapsed = lastSampleAt_ == 0 ? 0 : nowMs - lastSampleAt_;
  const double deltaDegrees = static_cast<double>(deltaCounts) * 360.0 / countsPerRevolution_;
  constexpr double epsilon = 1.0e-7;
  const double progress = signedTurnProgressDegrees_ + deltaDegrees;
  const int64_t turns = static_cast<int64_t>(trunc(
      (progress + (progress < 0.0 ? -epsilon : epsilon)) / 360.0));
  signedTurnProgressDegrees_ = progress - static_cast<double>(turns) * 360.0;
  if (fabs(signedTurnProgressDegrees_) < epsilon) signedTurnProgressDegrees_ = 0.0;
  turnsCompleted_ += static_cast<uint32_t>(turns < 0 ? -turns : turns);
  double angle = fmod(signedTurnProgressDegrees_, 360.0);
  if (angle < 0.0) angle += 360.0;
  angleDegrees_ = static_cast<float>(angle);
  if (angleDegrees_ >= 360.0f) angleDegrees_ = 0.0f;
  speedDegreesPerSecond_ = elapsed == 0 ? 0.0f : deltaDegrees * 1000.0f / elapsed;
  lastMotionAt_ = nowMs;
  lastSampleAt_ = nowMs;
  moving_ = true;
}

void RotationModel::update(uint32_t nowMs) {
  if (moving_ && static_cast<uint32_t>(nowMs - lastMotionAt_) >= 85) {
    moving_ = false;
    speedDegreesPerSecond_ = 0.0f;
  }
}
