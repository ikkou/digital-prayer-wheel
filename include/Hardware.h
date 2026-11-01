#pragma once

#include <Arduino.h>

class Hardware {
 public:
  void begin();
  void printDiagnostics() const;
};
