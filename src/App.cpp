#include "App.h"
#include "SettingsModel.h"

#include <M5Dial.h>

namespace {
constexpr uint32_t kBootDurationMs = 720;
constexpr uint32_t kFrameIntervalMs = 33;
constexpr uint32_t kAfterglowDurationMs = 1250;
constexpr int32_t kCountsPerDetent = kDialCountsPerDetent;
constexpr uint32_t kMetricsIntervalMs = 5000;
}

App::App() : renderer_(previewAssets_) {}

void App::begin() {
  hardware_.begin();
  settings_.begin();
  rotation_.setCountsPerRevolution(settings_.value().countsPerRevolution);
  presentation_ = settings_.value().presentation;
  input_.begin();
  if (externalAssets_.begin()) {
    renderer_.setSource(externalAssets_);
    Serial.println("DPW_ASSET_SOURCE=FLASH_MMAP");
  } else {
    renderer_.setSource(previewAssets_);
    Serial.println("DPW_ASSET_SOURCE=PREVIEW_NOT_FINAL");
  }
  if (!renderer_.begin()) Serial.println("DPW_RENDERER_ERROR=DISPLAY_OR_FRAME_COUNT_MISMATCH");
  Serial.printf("DPW_ROTATION_SCALE;counts_per_wheel_turn=%u;encoder_count=%ld\n",
                rotation_.countsPerRevolution(), static_cast<long>(M5Dial.Encoder.read()));
  Serial.println("DPW_CUE_MODE=12_OCLOCK_NET_TURN");
  Serial.printf("DPW_AUDIO;bgm=removed;muted=%u\n", settings_.value().muted);
  Serial.printf("DPW_PRESENTATION=%s;fever_thresholds=1,3,6,10,20;counter=session\n",
                presentationName(presentation_));
  bootUntil_ = millis() + kBootDurationMs;
  audio_.startup(settings_.value().muted);
  hardware_.printDiagnostics();
  const FrameAssetProfile profile = renderer_.assetProfile();
  Serial.printf("DPW_ASSET;frames=%u;encoding=%u;storage=%u;bytes=%lu;max_frame=%lu;final=%u\n",
                profile.frameCount, static_cast<unsigned>(profile.encoding),
                static_cast<unsigned>(profile.storage), static_cast<unsigned long>(profile.bytes),
                static_cast<unsigned long>(profile.largestFrameBytes), profile.finalArtwork);
  const uint32_t bootFrameUs = renderer_.drawFrame(0);
  const uint32_t indicatorStartedUs = micros();
  effects_.draw(0.0f, 0.0f, 3.0f, presentation_, millis());
  Serial.printf("DPW_INDICATOR;version=2;draw_us=%lu;persistent=1\n",
                static_cast<unsigned long>(micros() - indicatorStartedUs));
  Serial.printf("DPW_BOOT_FRAME;draw_us=%lu;encoding=%u;bytes=%lu\n",
                static_cast<unsigned long>(bootFrameUs), static_cast<unsigned>(profile.encoding),
                static_cast<unsigned long>(profile.bytes));
  if (profile.finalArtwork) renderer_.drawBootCaption();
#if defined(DPW_RGB565_DIAGNOSTIC)
  renderer_.drawRgb565PathDiagnostic();
  colorDiagnosticActive_ = true;
  Serial.println("DPW_RGB565_DIAGNOSTIC=SHOWING;rotate_or_touch_to_exit");
#endif
  metricsStartedAt_ = millis();
}

void App::update() {
  const uint32_t now = millis();
  const InputFrame input = input_.poll(now);
#if defined(DPW_RGB565_DIAGNOSTIC)
  if (colorDiagnosticActive_) {
    if (input.encoderDelta == 0 && input.gesture == TouchGesture::None) return;
    colorDiagnosticActive_ = false;
    frameDirty_ = true;
    Serial.println("DPW_RGB565_DIAGNOSTIC=EXITED");
  }
#endif
  processInput(input);
  rotation_.update(now);
  if (input.encoderDelta == 0 && !rotation_.moving() && encoderStopLogPending_) {
    Serial.printf("DPW_ENCODER_STOP;count=%ld\n", static_cast<long>(input.encoderCount));
    encoderStopLogPending_ = false;
  }
  updateState(now);
  draw(now);
  if (revolutionCuePending_) {
    if (state_ != AppState::Settings) {
      audio_.revolution(settings_.value().muted);
      Serial.printf("DPW_REVOLUTION;reference=12_oclock;turns=%lu;angle_deci=%ld\n",
                    static_cast<unsigned long>(rotation_.turnsCompleted()),
                    static_cast<long>(rotation_.angleDegrees() * 10.0f));
    }
    revolutionCuePending_ = false;
  }
  audio_.update(settings_.value().muted);
  reportMetrics(millis(), input.nowMs);
}

void App::processInput(const InputFrame& input) {
  if (state_ == AppState::Settings) {
    if (input.encoderDelta != 0) {
      settingsDetentAccumulator_ += input.encoderDelta;
      while (settingsDetentAccumulator_ >= kCountsPerDetent) {
        settingsSelection_ = nextSettingsItem(settingsSelection_, true);
        settingsDetentAccumulator_ -= kCountsPerDetent;
        settingsDirty_ = true;
      }
      while (settingsDetentAccumulator_ <= -kCountsPerDetent) {
        settingsSelection_ = nextSettingsItem(settingsSelection_, false);
        settingsDetentAccumulator_ += kCountsPerDetent;
        settingsDirty_ = true;
      }
    }
    if (input.gesture == TouchGesture::ShortTap) applySetting();
    if (input.gesture == TouchGesture::LongPress) {
      state_ = AppState::Idle;
      frameDirty_ = true;
    }
    return;
  }

  if (input.encoderDelta != 0) {
    rotation_.applyDelta(input.encoderDelta, input.nowMs);
    encoderStopLogPending_ = true;
    hasRotated_ = true;
    lastMotionAt_ = input.nowMs;
    lastMotionSpeed_ = rotation_.speedDegreesPerSecond();
    frameDirty_ = true;
    if (rotation_.turnsCompleted() > previousTurnCount_) {
      const uint8_t oldStage = feverStage(previousTurnCount_);
      previousTurnCount_ = rotation_.turnsCompleted();
      revolutionCuePending_ = true;
      effects_.observeTurns(previousTurnCount_, input.nowMs);
      Serial.printf("DPW_FEVER;turns=%lu;stage=%u;level_up=%u;next=%lu\n",
                    static_cast<unsigned long>(previousTurnCount_), feverStage(previousTurnCount_),
                    feverStage(previousTurnCount_) > oldStage,
                    static_cast<unsigned long>(feverNextTarget(feverStage(previousTurnCount_))));
    }
    if (static_cast<uint32_t>(input.nowMs - lastEncoderLogAt_) >= 250) {
      Serial.printf("DPW_ENCODER;count=%ld;delta=%ld;angle_deci=%ld;dir=%d;turns=%lu\n",
                    static_cast<long>(input.encoderCount), static_cast<long>(input.encoderDelta),
                    static_cast<long>(rotation_.angleDegrees() * 10.0f), input.encoderDelta > 0 ? 1 : -1,
                    static_cast<unsigned long>(rotation_.turnsCompleted()));
      lastEncoderLogAt_ = input.nowMs;
    }
  }

  if (input.gesture == TouchGesture::ShortTap) {
    settings_.togglePresentation();
    presentation_ = settings_.value().presentation;
    presentationToastUntil_ = input.nowMs + 900;
    presentationToastVisible_ = true;
    frameDirty_ = true;
    audio_.confirm(settings_.value().muted);
    Serial.printf("DPW_PRESENTATION=%s\n", presentationName(presentation_));
  } else if (input.gesture == TouchGesture::LongPress) {
    openSettings();
  }
}

void App::updateState(uint32_t nowMs) {
  if (state_ == AppState::Settings) return;
  if (static_cast<int32_t>(bootUntil_ - nowMs) > 0 && !hasRotated_) {
    state_ = AppState::Boot;
    return;
  }
  if (rotation_.moving()) {
    state_ = AppState::Rotation;
  } else if (hasRotated_ && static_cast<uint32_t>(nowMs - lastMotionAt_) < kAfterglowDurationMs) {
    state_ = AppState::Afterglow;
  } else {
    state_ = AppState::Idle;
  }
}

void App::draw(uint32_t nowMs) {
  if (state_ == AppState::Settings) {
    if (settingsDirty_) {
      renderer_.drawSettings(settingsSelection_, settings_.value().countsPerRevolution,
                             settings_.value().muted, presentation_);
      settingsDirty_ = false;
    }
    return;
  }

  if (state_ == AppState::Boot && !hasRotated_) return;
  const uint16_t frame = renderer_.frameForAngle(rotation_.angleDegrees());
  const bool afterglowActive = state_ == AppState::Afterglow &&
      static_cast<uint32_t>(nowMs - lastDrawAt_) >= kFrameIntervalMs;
  const bool frameChanged = frame != lastFrame_;
  const bool feverAnimation = presentation_ == Presentation::Fever &&
      ((hasRotated_ && static_cast<uint32_t>(nowMs - lastMotionAt_) < 2200) || effects_.burstActive(nowMs));
  if (feverAnimationVisible_ && !feverAnimation) frameDirty_ = true;
  if (presentationToastVisible_ && static_cast<int32_t>(nowMs - presentationToastUntil_) >= 0) {
    frameDirty_ = true;
    presentationToastVisible_ = false;
  }
  const bool due = frameDirty_ || frameChanged || afterglowActive ||
      (feverAnimation && static_cast<uint32_t>(nowMs - lastDrawAt_) >= kFrameIntervalMs) ||
      (state_ == AppState::Rotation && static_cast<uint32_t>(nowMs - lastDrawAt_) >= kFrameIntervalMs);
  if (!due) return;
  if (state_ == AppState::Afterglow && static_cast<uint32_t>(nowMs - lastDrawAt_) < kFrameIntervalMs) return;

  const uint32_t drawStartedUs = micros();
  renderer_.drawFrame(frame);
  if (state_ == AppState::Boot) renderer_.drawBootCaption();
  const float age = rotation_.moving() ? -1.0f :
      hasRotated_ ? static_cast<uint32_t>(nowMs - lastMotionAt_) / 1000.0f : 3.0f;
  const float speed = rotation_.moving() ? rotation_.speedDegreesPerSecond() : lastMotionSpeed_;
  effects_.draw(rotation_.angleDegrees(), speed, age, presentation_, nowMs);
  if (presentation_ == Presentation::Fever) renderer_.drawFeverStatus(effects_.feverFrame(nowMs, speed, age));
  if (presentationToastVisible_) renderer_.drawPresentationTag(presentation_);
  // Measure the full frame, including the indicator/effects and any caption.
  const uint32_t drawMicros = micros() - drawStartedUs;
  ++framesDrawn_;
  drawMicrosTotal_ += drawMicros;
  if (drawMicros > drawMicrosMax_) drawMicrosMax_ = drawMicros;
  lastFrame_ = frame;
  lastDrawAt_ = nowMs;
  frameDirty_ = false;
  feverAnimationVisible_ = feverAnimation;
}

void App::reportMetrics(uint32_t nowMs, uint32_t inputPolledAtMs) {
  const uint32_t pollToDrawMs = nowMs - inputPolledAtMs;
  if (pollToDrawMs > pollToDrawMsMax_) pollToDrawMsMax_ = pollToDrawMs;
  const uint32_t elapsed = nowMs - metricsStartedAt_;
  if (elapsed < kMetricsIntervalMs) return;
  const uint32_t fpsTimes10 = elapsed == 0 ? 0 : framesDrawn_ * 10000U / elapsed;
  const uint32_t averageDrawUs = framesDrawn_ == 0 ? 0 : drawMicrosTotal_ / framesDrawn_;
  const FrameAssetProfile p = renderer_.assetProfile();
  Serial.printf("DPW_METRICS;fps_x10=%lu;draw_avg_us=%lu;draw_max_us=%lu;poll_to_draw_max_ms=%lu;frames=%u;encoding=%u;storage=%u;asset_bytes=%lu;max_frame=%lu;display=%ux%u;flash=%lu;psram=%lu;heap=%lu;counts_per_wheel_turn=%u\n",
                static_cast<unsigned long>(fpsTimes10), static_cast<unsigned long>(averageDrawUs),
                static_cast<unsigned long>(drawMicrosMax_), static_cast<unsigned long>(pollToDrawMsMax_),
                p.frameCount, static_cast<unsigned>(p.encoding), static_cast<unsigned>(p.storage),
                static_cast<unsigned long>(p.bytes), static_cast<unsigned long>(p.largestFrameBytes),
                static_cast<unsigned>(M5Dial.Display.width()), static_cast<unsigned>(M5Dial.Display.height()),
                static_cast<unsigned long>(ESP.getFlashChipSize()), static_cast<unsigned long>(ESP.getPsramSize()),
                static_cast<unsigned long>(ESP.getFreeHeap()), rotation_.countsPerRevolution());
  metricsStartedAt_ = nowMs;
  framesDrawn_ = 0;
  drawMicrosTotal_ = 0;
  drawMicrosMax_ = 0;
  pollToDrawMsMax_ = 0;
}

void App::openSettings() {
  state_ = AppState::Settings;
  settingsSelection_ = 0;
  settingsDetentAccumulator_ = 0;
  settingsDirty_ = true;
  Serial.println("DPW_SETTINGS=OPEN");
}

void App::applySetting() {
  if (settingsSelection_ == 0) {
    settings_.toggleMute();
    Serial.printf("DPW_MUTE=%s\n", settings_.value().muted ? "ON" : "OFF");
  } else {
    settings_.togglePresentation();
    presentation_ = settings_.value().presentation;
    Serial.printf("DPW_PRESENTATION=%s\n", presentationName(presentation_));
  }
  settingsDirty_ = true;
  audio_.confirm(settings_.value().muted);
}
