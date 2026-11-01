#pragma once

#include "FrameAssetSource.h"
#include "Presentation.h"
#include "FeverModel.h"

#include <stdint.h>

class Renderer {
 public:
  explicit Renderer(IFrameAssetSource& source) : source_(&source) {}
  void setSource(IFrameAssetSource& source) { source_ = &source; }
  bool begin() const;
  uint16_t frameForAngle(float angleDegrees) const;
  uint32_t drawFrame(uint16_t frameIndex);
  void drawBootCaption();
  void drawPresentationTag(Presentation presentation);
  void drawFeverStatus(const FeverFrame& fever);
  void drawSettings(uint8_t selected, uint16_t countsPerRevolution, bool muted, Presentation presentation);
  void drawRgb565PathDiagnostic();
  FrameAssetProfile assetProfile() const { return source_->profile(); }
  uint32_t lastDrawMicros() const { return lastDrawMicros_; }

 private:
  IFrameAssetSource* source_;
  uint32_t lastDrawMicros_ = 0;
};
