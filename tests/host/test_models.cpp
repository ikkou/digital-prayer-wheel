#include "FrameMapping.h"
#include "Rgb565AssetPush.h"
#include "RingIndicator.h"
#include "RotationModel.h"
#include "SettingsModel.h"
#include "FeverModel.h"
#include "FeverDrawing.h"
#include "Presentation.h"
#include "TouchGestureDetector.h"

#include <cmath>
#include <cstdint>
#include <cstdio>

namespace {
int failures = 0;
int checks = 0;

void check(bool condition, const char* description) {
  ++checks;
  if (!condition) {
    ++failures;
    std::fprintf(stderr, "FAIL: %s\n", description);
  }
}

bool near(float actual, float expected, float tolerance = 0.001f) {
  return std::fabs(actual - expected) <= tolerance;
}

class FakeRgb565Display {
 public:
  bool getSwapBytes() const { return swapBytes_; }
  void setSwapBytes(bool swap) { swapBytes_ = swap; }

  void pushImage(int32_t, int32_t, int32_t, int32_t, const uint16_t* pixels) {
    swapWasEnabledForPush = swapBytes_;
    const auto* source = reinterpret_cast<const uint8_t*>(pixels);
    for (size_t i = 0; i < pixelCount; ++i) {
      const uint8_t first = source[i * 2];
      const uint8_t second = source[i * 2 + 1];
      // M5GFX's swap=true RGB565 path emits the logical 16-bit R5G6B5
      // word in the panel's MSB-first SPI order; false copies input bytes.
      wireBytes[i * 2] = swapBytes_ ? second : first;
      wireBytes[i * 2 + 1] = swapBytes_ ? first : second;
    }
  }

  static constexpr size_t pixelCount = 6;
  bool swapWasEnabledForPush = false;
  uint8_t wireBytes[pixelCount * 2] = {};

 private:
  bool swapBytes_ = false;
};

void testRgb565LittleEndianAssetByteOrder() {
  // Red, green, blue, white, black and neutral gray as standard RGB565 words.
  const uint16_t colors[FakeRgb565Display::pixelCount] = {
      0xF800, 0x07E0, 0x001F, 0xFFFF, 0x0000, 0x8410};
  uint8_t packedLittleEndian[FakeRgb565Display::pixelCount * 2] = {};
  uint8_t expectedSpiMsbFirst[FakeRgb565Display::pixelCount * 2] = {};
  for (size_t i = 0; i < FakeRgb565Display::pixelCount; ++i) {
    packedLittleEndian[i * 2] = static_cast<uint8_t>(colors[i] & 0xFF);
    packedLittleEndian[i * 2 + 1] = static_cast<uint8_t>(colors[i] >> 8);
    expectedSpiMsbFirst[i * 2] = static_cast<uint8_t>(colors[i] >> 8);
    expectedSpiMsbFirst[i * 2 + 1] = static_cast<uint8_t>(colors[i] & 0xFF);
  }

  FakeRgb565Display display;
  pushRgb565LittleEndian(display, 0, 0, FakeRgb565Display::pixelCount, 1,
                         packedLittleEndian);
  check(display.swapWasEnabledForPush,
        "little-endian RGB565 asset enables M5GFX conversion for the push");
  check(!display.getSwapBytes(),
        "RGB565 asset push restores the previous M5GFX byte-swap setting");
  bool wireMatchesExpected = true;
  for (size_t i = 0; i < sizeof(expectedSpiMsbFirst); ++i) {
    wireMatchesExpected &= display.wireBytes[i] == expectedSpiMsbFirst[i];
  }
  check(wireMatchesExpected,
        "red/green/blue/white/black/gray reach SPI in RGB565 MSB-first order");

  display.setSwapBytes(true);
  pushRgb565LittleEndian(display, 0, 0, FakeRgb565Display::pixelCount, 1,
                         packedLittleEndian);
  check(display.getSwapBytes(),
        "RGB565 asset push also preserves a previously enabled swap setting");
}

void testFrameMapping() {
  check(frameIndexForAngle(0.0f, 32) == 0, "zero degrees starts at frame 0");
  check(frameIndexForAngle(11.25f, 32) == 1, "clockwise step advances one frame");
  check(frameIndexForAngle(348.75f, 32) == 31, "counterclockwise step selects the prior loop frame");
  check(frameIndexForAngle(-11.25f, 32) == 31, "negative angle wraps to the last frame");
  check(frameIndexForAngle(360.0f, 32) == 0, "360 degrees closes to frame 0");
  check(frameIndexForAngle(-360.0f, 32) == 0, "negative full turn closes to frame 0");
  check(frameIndexForAngle(720.0f + 11.25f, 32) == 1, "multiple turns normalize before selection");
  check(frameIndexForAngle(359.99f, 32) == 31, "angle immediately before loop boundary selects last frame");
  check(frameIndexForAngle(0.0f, 0) == 0, "empty source is handled safely");
}

void testRotationAndRevolutionCues() {
  RotationModel wheel;
  wheel.setCountsPerRevolution(256);
  wheel.applyDelta(256, 100);
  check(near(wheel.angleDegrees(), 0.0f), "one clockwise encoder turn wraps body angle");
  check(wheel.turnsCompleted() == 1, "one clockwise turn produces one revolution event");

  wheel.applyDelta(-128, 200);
  check(near(wheel.angleDegrees(), 180.0f), "reverse input subtracts from body angle");
  check(wheel.speedDegreesPerSecond() < 0.0f, "reverse input retains a negative speed sign");
  check(wheel.turnsCompleted() == 1, "half-turn reverse motion does not lose prior cue count");
  wheel.applyDelta(-128, 400);
  check(near(wheel.angleDegrees(), 0.0f), "second reverse half-turn closes the loop");
  check(wheel.turnsCompleted() == 2, "full reverse travel adds exactly one more cue");

  RotationModel rebound;
  rebound.setCountsPerRevolution(360);
  rebound.applyDelta(400, 100);
  check(rebound.turnsCompleted() == 1, "crossing one full turn emits one event");
  rebound.applyDelta(-50, 200);
  check(rebound.turnsCompleted() == 1, "reversing across the signed-angle boundary does not emit a false event");
  rebound.applyDelta(-310, 300);
  check(rebound.turnsCompleted() == 1, "reversing never emits a cue away from twelve o'clock");
  rebound.applyDelta(-40, 400);
  check(rebound.turnsCompleted() == 2 && near(rebound.angleDegrees(), 0),
        "reverse full turn emits the next cue exactly at twelve o'clock");

  RotationModel rocking;
  rocking.setCountsPerRevolution(360);
  for (int i = 0; i < 20; ++i) {
    rocking.applyDelta(180, 100 + i * 200);
    rocking.applyDelta(-180, 200 + i * 200);
  }
  check(rocking.turnsCompleted() == 0, "partial-turn back-and-forth travel never adds into a full turn");
  rocking.applyDelta(-1, 5000);
  rocking.applyDelta(1, 5100);
  check(rocking.turnsCompleted() == 0, "starting around twelve o'clock does not trigger a false cue");
  rocking.applyDelta(-1080, 5200);
  check(rocking.turnsCompleted() == 3 && near(rocking.angleDegrees(), 0),
        "batched reverse input counts all complete turns at zero-aligned boundaries");
  const uint16_t scales[] = {61, 64, 127, 128, 256, 360, 2048};
  for (uint16_t scale : scales) {
    RotationModel precise;
    precise.setCountsPerRevolution(scale);
    bool premature = false;
    for (uint16_t step = 1; step < scale; ++step) {
      precise.applyDelta(1, step);
      premature |= precise.turnsCompleted() != 0;
    }
    precise.applyDelta(1, scale);
    check(!premature && precise.turnsCompleted() == 1 && near(precise.angleDegrees(), 0),
          "one-count steps reach the forward cue exactly at zero, including nonbinary scales");
    for (uint16_t step = 1; step <= scale; ++step) precise.applyDelta(-1, scale + step);
    check(precise.turnsCompleted() == 2 && near(precise.angleDegrees(), 0),
          "one-count reverse steps return to zero-aligned cue without numeric drift");
  }

  wheel.update(484);
  check(wheel.moving(), "wheel remains moving before the stop timeout");
  wheel.update(485);
  check(!wheel.moving(), "wheel stops after the 85 ms input timeout");
  check(near(wheel.speedDegreesPerSecond(), 0.0f), "stopped wheel has zero reported speed");
}

void testTouchGestureDiscrimination() {
  TouchGestureDetector detector;
  check(detector.poll(false, 0) == TouchGesture::None, "idle touch produces no gesture");
  check(detector.poll(true, 34) == TouchGesture::None, "press edge is debounced");
  check(detector.poll(true, 35) == TouchGesture::None, "stable press starts a tap");
  check(detector.poll(false, 50) == TouchGesture::None, "short release bounce is debounced");
  check(detector.poll(false, 70) == TouchGesture::ShortTap, "debounced release emits one short tap");

  check(detector.poll(true, 105) == TouchGesture::None, "new stable press begins long-press timing");
  check(detector.poll(true, 804) == TouchGesture::None, "699 ms hold is not yet a long press");
  check(detector.poll(true, 805) == TouchGesture::LongPress, "700 ms hold emits a long press");
  check(detector.poll(true, 900) == TouchGesture::None, "held touch does not repeat long-press events");
  check(detector.poll(false, 910) == TouchGesture::None, "release after long press does not also emit a tap");

  TouchGestureDetector wrappedClock;
  const uint32_t pressAt = 0xFFFFFFF0U;
  check(wrappedClock.poll(true, pressAt) == TouchGesture::None, "press starts before millisecond counter wraps");
  check(wrappedClock.poll(true, pressAt + 699U) == TouchGesture::None,
        "short hold remains below threshold across millisecond wrap");
  check(wrappedClock.poll(true, pressAt + 700U) == TouchGesture::LongPress,
        "long press threshold remains correct across millisecond wrap");
}

void testSettingsScaleCycle() {
  RotationModel physical;
  physical.applyDelta(kDialCountsPerPhysicalTurn / 4, 100);
  check(near(physical.angleDegrees(), 90), "default physical quarter-turn maps to virtual quarter-turn");
  physical.applyDelta(3 * kDialCountsPerPhysicalTurn / 4, 200);
  check(near(physical.angleDegrees(), 0) && physical.turnsCompleted() == 1,
        "64 decoded counts map to one zero-aligned virtual revolution");
  check(kDialCountsPerDetent * 16 == kDialCountsPerPhysicalTurn,
        "settings navigation uses four decoded counts per physical detent");
  check(nextCountsPerRevolution(256) == 64, "scale cycle advances 256 to 64");
  check(nextCountsPerRevolution(64) == 128, "scale cycle advances 64 to 128");
  check(nextCountsPerRevolution(128) == 256, "scale cycle closes from 128 to 256");
  check(nextCountsPerRevolution(512) == 64, "unknown stored scale returns to first menu choice");
}

struct IndicatorDisplay {
  int32_t headX = 0, headY = 0;
  int lines = 0;
  int minTrailY = 240, maxTrailY = 0;
  bool inBounds = true;
  uint16_t color565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
  }
  void drawCircle(int32_t, int32_t, int32_t, uint16_t) {}
  void fillCircle(int32_t x, int32_t y, int32_t r, uint16_t) {
    headX = x; headY = y;
    inBounds &= std::hypot(double(x - 120), double(y - 120)) + r < 120;
  }
  void drawLine(int32_t, int32_t y, int32_t, int32_t y1, uint16_t) {
    if (lines++ < 4) return;  // four fixed reference ticks
    if (y < minTrailY) minTrailY = y;
    if (y1 < minTrailY) minTrailY = y1;
    if (y > maxTrailY) maxTrailY = y;
    if (y1 > maxTrailY) maxTrailY = y1;
  }
};

void testRingIndicator() {
  IndicatorDisplay idle;
  drawRingIndicator(idle, 0, 0, 2, false);
  check(idle.headX == 120 && idle.headY == 9, "stationary angular cue remains visible at zero");
  check(idle.lines == 4 && idle.inBounds, "stationary cue has no trail and fits circular display");
  IndicatorDisplay cw, ccw;
  drawRingIndicator(cw, 90, 920, -1, false);
  drawRingIndicator(ccw, 90, -920, -1, false);
  check(cw.headX == 231 && cw.headY == 120 && cw.inBounds,
        "clockwise quarter-turn places cue on right, within circular display");
  check(ccw.headX == cw.headX && ccw.headY == cw.headY,
        "changing speed direction never moves the angular cue");
  check(cw.lines > 4 && cw.minTrailY < 120 && cw.maxTrailY <= 120,
        "clockwise trail lies behind the head");
  check(ccw.lines > 4 && ccw.maxTrailY > 120 && ccw.minTrailY >= 120,
        "reverse trail mirrors behind the head");
  IndicatorDisplay stopped;
  drawRingIndicator(stopped, 90, 920, 1.3f, true);
  check(stopped.lines == 4 && stopped.headX == cw.headX && stopped.headY == cw.headY,
        "afterglow fades completely while stationary angular cue remains");
  IndicatorDisplay wrapped;
  drawRingIndicator(wrapped, 360, 0, 2, true);
  check(wrapped.headX == idle.headX && wrapped.headY == idle.headY,
        "angular cue closes the full-turn loop in quiet presentation");
}
}

struct FeverDisplay {
  unsigned calls = 0;
  bool inBounds = true;
  uint16_t color565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3);
  }
  void point(int x, int y, int radius = 0) {
    inBounds &= std::hypot(double(x - 120), double(y - 120)) + radius < 120;
  }
  void drawLine(int x, int y, int x1, int y1, uint16_t) {
    ++calls; point(x, y); point(x1, y1);
  }
  void drawCircle(int x, int y, int r, uint16_t) { ++calls; point(x, y, r); }
  void fillCircle(int x, int y, int r, uint16_t) { ++calls; point(x, y, r); }
};

void testFever() {
  const uint32_t thresholds[] = {0, 1, 3, 6, 10, 20};
  for (uint8_t i = 0; i < 6; ++i) {
    check(feverStage(thresholds[i]) == i, "exact fever threshold selects expected tier");
    if (i > 0) check(feverStage(thresholds[i] - 1) == i - 1,
                     "tier never increases before its threshold");
  }
  check(feverStage(UINT32_MAX) == 5, "very large totals cap at tier five");
  check(near(feverProgress(4), 1.f / 3), "tier progress interpolates completed turns");
  check(near(feverProgress(20), 1), "maximum tier keeps the progress bar full");
  FeverModel fever;
  check(!fever.burstActive(0), "boot has no fabricated reward burst");
  check(fever.frame(0, 0, 3).energy == 0, "boot is motionless");
  fever.observeTurns(1, 100);
  const FeverFrame first = fever.frame(101, 300, -1);
  check(first.stage == 1 && first.levelUp && first.burstGain > .99f,
        "first full turn rewards the first tier");
  fever.observeTurns(1, 900);
  check(fever.frame(1000, 0, -1).burstProgress > .49f,
        "same total never restarts the burst");
  check(!fever.burstActive(1900), "burst expires at its exact duration");
  fever.observeTurns(2, 2000);
  check(!fever.frame(2000, 300, -1).levelUp, "ordinary turn is not a tier-up");
  check(near(fever.frame(4200, 300, 2.2f).energy, 0), "stopped energy completely fades");
  check(fever.frame(4200, 300, 2.2f).stage == 1, "stopping preserves the session tier");
  check(near(fever.frame(4200, -300, -1).energy, fever.frame(4200, 300, -1).energy),
        "reverse rotation receives equal visual energy");
  check(fever.frame(4200, 900, -1).energy > fever.frame(4200, 100, -1).energy,
        "speed adds energy without replacing cumulative tier");
  fever.observeTurns(20, 5000);
  check(fever.frame(5000, 300, -1).stage == 5, "batched turns reach correct maximum tier");
  fever.observeTurns(0, 5100);
  check(!fever.burstActive(5100) && fever.frame(5100, 0, 3).stage == 0,
        "session reset cannot fabricate a burst");
  FeverModel wrap;
  wrap.observeTurns(3, UINT32_MAX - 100);
  check(wrap.burstActive(99), "burst time survives millis rollover");
  check(!wrap.burstActive(1699), "burst expires correctly after millis rollover");
  bool bounded = true, budgeted = true;
  unsigned previousCalls = 0;
  for (uint8_t stage = 0; stage < 6; ++stage) {
    FeverModel model;
    model.observeTurns(thresholds[stage], 1000);
    FeverDisplay sample;
    drawFeverEffects(sample, 90, 720, 1500, model.frame(1500, 720, -1));
    check(sample.calls >= previousCalls, "higher tier never reduces overlay complexity");
    previousCalls = sample.calls;
    for (int angle = 0; angle < 360; angle += 5) {
      for (int direction = -1; direction <= 1; direction += 2) {
        FeverDisplay d;
        drawFeverEffects(d, angle, direction * 1440, 1500,
                         model.frame(1500, direction * 1440, -1));
        bounded &= d.inBounds;
        budgeted &= d.calls < 260;
      }
    }
  }
  check(bounded, "all tiers and both directions remain inside the round LCD");
  check(budgeted, "overlay primitives remain under a fixed draw-call budget");
  FeverDisplay stopped;
  drawFeverEffects(stopped, 90, 720, 10000, fever.frame(10000, 720, 3));
  check(stopped.calls == 0, "stopped expired effects issue no primitive draws");
  check(nextPresentation(Presentation::Fever) == Presentation::Quiet &&
        nextPresentation(Presentation::Quiet) == Presentation::Glow &&
        nextPresentation(Presentation::Glow) == Presentation::Fever,
        "tap cycles fever, quiet and glow predictably");
  check(nextSettingsItem(0, false) == 1, "reverse menu movement wraps to effects");
  check(nextSettingsItem(1, true) == 0, "forward menu movement wraps to sound");
  check(nextSettingsItem(1, false) == 0, "reverse selects the preceding setting");
}

int main() {
  testFrameMapping();
  testRgb565LittleEndianAssetByteOrder();
  testRotationAndRevolutionCues();
  testTouchGestureDiscrimination();
  testSettingsScaleCycle();
  testRingIndicator();
  testFever();
  if (failures != 0) {
    std::fprintf(stderr, "%d/%d checks failed\n", failures, checks);
    return 1;
  }
  std::printf("PASS: %d host model checks\n", checks);
  return 0;
}
