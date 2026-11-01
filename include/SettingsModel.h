#pragma once

#include <stdint.h>
#include "Presentation.h"

constexpr uint16_t kDialCountsPerPhysicalTurn = 64;
constexpr int32_t kDialCountsPerDetent = 4;  // 16 positions, 64 decoded transitions/rev
constexpr uint8_t kSettingsItemCount = 2;  // SOUND and EFFECTS; mapping is read-only
inline uint8_t nextSettingsItem(uint8_t current, bool forward) {
  return (current + (forward ? 1 : kSettingsItemCount - 1)) % kSettingsItemCount;
}

// Calibration helper; no longer exposed as a tap-to-change exhibition setting.
inline uint16_t nextCountsPerRevolution(uint16_t current) {
  switch (current) {
    case 256: return 64;
    case 64: return 128;
    case 128: return 256;
    default: return 64;
  }
}
