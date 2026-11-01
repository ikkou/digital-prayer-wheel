#include "Settings.h"

void Settings::begin() {
  preferences_.begin("prayerwheel", false);
  value_.countsPerRevolution = preferences_.getUShort("counts", kDialCountsPerPhysicalTurn);
  // Migration v2 restores the physically confirmed 64-count mapping after an
  // accidental audio-menu edit. Mapping is now read-only in the public menu.
  if (preferences_.getUChar("mapver", 0) < 2) {
    value_.countsPerRevolution = kDialCountsPerPhysicalTurn;
    preferences_.putUShort("counts", value_.countsPerRevolution);
    preferences_.putUChar("mapver", 2);
  }
  if (value_.countsPerRevolution < 32 || value_.countsPerRevolution > 2048) {
    value_.countsPerRevolution = kDialCountsPerPhysicalTurn;
  }
  value_.muted = preferences_.getBool("mute", false);
  // New presentation defaults to FEVER once; subsequent choices are retained.
  const uint8_t mode = preferences_.getUChar("visual", 2);
  value_.presentation = mode <= 2 ? static_cast<Presentation>(mode) : Presentation::Fever;
  if (preferences_.isKey("ambience")) preferences_.remove("ambience");
}

void Settings::persist() {
  preferences_.putUShort("counts", value_.countsPerRevolution);
  preferences_.putBool("mute", value_.muted);
  preferences_.putUChar("visual", static_cast<uint8_t>(value_.presentation));
}

void Settings::setCountsPerRevolution(uint16_t counts) {
  if (counts < 32 || counts > 2048 || counts == value_.countsPerRevolution) return;
  value_.countsPerRevolution = counts;
  persist();
}

void Settings::toggleMute() {
  value_.muted = !value_.muted;
  persist();
}

void Settings::togglePresentation() {
  value_.presentation = nextPresentation(value_.presentation);
  persist();
}
