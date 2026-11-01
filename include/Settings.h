#pragma once

#include <Preferences.h>
#include "SettingsModel.h"

struct UserSettings {
  uint16_t countsPerRevolution = kDialCountsPerPhysicalTurn;
  bool muted = false;
  Presentation presentation = Presentation::Fever;
};

class Settings {
 public:
  void begin();
  const UserSettings& value() const { return value_; }
  void setCountsPerRevolution(uint16_t counts);
  void toggleMute();
  void togglePresentation();

 private:
  void persist();
  Preferences preferences_;
  UserSettings value_;
};
