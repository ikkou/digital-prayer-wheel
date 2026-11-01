#pragma once
#include <stdint.h>

enum class Presentation : uint8_t { Quiet = 0, Glow = 1, Fever = 2 };
inline Presentation nextPresentation(Presentation mode) {
  return static_cast<Presentation>((static_cast<uint8_t>(mode) + 1) % 3);
}
inline const char* presentationName(Presentation mode) {
  return mode == Presentation::Quiet ? "QUIET" : mode == Presentation::Glow ? "GLOW" : "FEVER";
}
