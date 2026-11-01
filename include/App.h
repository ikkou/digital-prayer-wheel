#pragma once

#include "AppTypes.h"
#include "Audio.h"
#include "Effects.h"
#include "FrameAssetSource.h"
#include "Hardware.h"
#include "Input.h"
#include "Renderer.h"
#include "RotationModel.h"
#include "Settings.h"

class App {
 public:
  App();
  void begin();
  void update();

 private:
  void processInput(const InputFrame& input);
  void updateState(uint32_t nowMs);
  void draw(uint32_t nowMs);
  void reportMetrics(uint32_t nowMs, uint32_t inputPolledAtMs);
  void openSettings();
  void applySetting();

  Hardware hardware_;
  Input input_;
  RotationModel rotation_;
  PreviewFrameSource previewAssets_;
  FlashMappedFrameSource externalAssets_;
  Renderer renderer_;
  Effects effects_;
  Audio audio_;
  Settings settings_;
  AppState state_ = AppState::Boot;
  uint32_t bootUntil_ = 0;
  uint32_t previousTurnCount_ = 0;
  uint32_t lastDrawAt_ = 0;
  uint32_t lastMotionAt_ = 0;
  uint32_t lastEncoderLogAt_ = 0;
  uint32_t presentationToastUntil_ = 0;
  float lastMotionSpeed_ = 0.0f;
  int32_t settingsDetentAccumulator_ = 0;
  uint8_t settingsSelection_ = 0;
  uint8_t lastFrame_ = 255;
  bool frameDirty_ = true;
  bool settingsDirty_ = true;
  bool hasRotated_ = false;
  Presentation presentation_ = Presentation::Fever;
  bool presentationToastVisible_ = false;
  bool revolutionCuePending_ = false;
  bool encoderStopLogPending_ = false;
  bool feverAnimationVisible_ = false;
#if defined(DPW_RGB565_DIAGNOSTIC)
  bool colorDiagnosticActive_ = false;
#endif
  uint32_t metricsStartedAt_ = 0;
  uint32_t framesDrawn_ = 0;
  uint32_t drawMicrosTotal_ = 0;
  uint32_t drawMicrosMax_ = 0;
  uint32_t pollToDrawMsMax_ = 0;
};
