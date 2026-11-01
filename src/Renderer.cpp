#include "Renderer.h"
#include "FrameMapping.h"
#include "Rgb565AssetPush.h"

#include <M5Dial.h>

namespace {
constexpr uint16_t kIndigo = 0x0842;
constexpr uint16_t kBrass = 0xD5A4;
constexpr uint16_t kAmber = 0xFD80;
constexpr uint16_t kMutedInk = 0x8B2D;
}

bool Renderer::begin() const {
  const FrameAssetProfile p = source_->profile();
  return p.width == M5Dial.Display.width() && p.height == M5Dial.Display.height() && p.frameCount > 0;
}

uint16_t Renderer::frameForAngle(float angleDegrees) const {
  const uint16_t count = source_->profile().frameCount;
  return frameIndexForAngle(angleDegrees, count);
}

uint32_t Renderer::drawFrame(uint16_t frameIndex) {
  const uint16_t count = source_->profile().frameCount;
  if (count == 0) return 0;
  frameIndex %= count;  // closes the 360° loop and handles reverse motion through normalized angle
  const uint32_t started = micros();
  if (!source_->drawFrame(M5Dial.Display, frameIndex)) {
    // A failed external frame never masquerades as finished artwork.
    PreviewFrameSource fallback;
    fallback.drawFrame(M5Dial.Display, frameIndex % fallback.profile().frameCount);
  }
  lastDrawMicros_ = micros() - started;
  return lastDrawMicros_;
}

void Renderer::drawBootCaption() {
  auto& display = M5Dial.Display;
  display.setTextDatum(middle_center);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.72f);
  display.setTextColor(kAmber);
  display.drawString("AWAKENING", 120, 210);
}

void Renderer::drawPresentationTag(Presentation presentation) {
  auto& display = M5Dial.Display;
  display.setTextDatum(middle_center);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.56f);
  display.setTextColor(kAmber);
  char text[32];
  snprintf(text, sizeof(text), "CLASSIC  /  %s", presentationName(presentation));
  display.drawString(text, 120, 202);
}

void Renderer::drawFeverStatus(const FeverFrame& fever) {
  auto& d = M5Dial.Display;
  d.setFont(&fonts::Orbitron_Light_24);
  d.setTextDatum(middle_center);
  d.setTextSize(0.48f);
  d.setTextColor(fever.levelUp && fever.burstGain > .1f ? 0xFFDA : kBrass);
  char label[32];
  snprintf(label, sizeof(label), "LV %u  /  %lu TURNS", fever.stage,
           static_cast<unsigned long>(fever.turns));
  d.drawString(label, 120, 215);
  // Segmented progress to the next tier. Cap at stage 5 rather than overflowing.
  const float progress = feverProgress(fever.turns);
  for (uint8_t i = 0; i < 10; ++i) {
    const bool filled = fever.stage == 5 || i < static_cast<uint8_t>(progress * 10);
    d.fillRect(91 + i * 6, 228, 4, 2, filled ? kAmber : kMutedInk);
  }
  if (fever.levelUp && fever.burstGain > .38f) {
    d.setTextSize(.72f);
    d.setTextColor(kAmber);
    d.drawString(fever.stage == 5 ? "FEVER MAX" : "LEVEL UP", 120, 29);
  }
}

void Renderer::drawSettings(uint8_t selected, uint16_t countsPerRevolution, bool muted,
                            Presentation presentation) {
  auto& display = M5Dial.Display;
  display.fillScreen(kIndigo);
  display.drawCircle(120, 120, 116, kBrass);
  display.drawCircle(120, 120, 111, kMutedInk);
  display.drawCircle(120, 120, 105, kMutedInk);
  display.setTextDatum(middle_center);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.72f);
  display.setTextColor(kAmber);
  display.drawString("SETTINGS", 120, 46);

  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.56f);
  display.setTextColor(kBrass);
  display.drawString("RING  /  1:1", 120, 82);
  display.setTextColor(kMutedInk);
  char countLine[24];
  snprintf(countLine, sizeof(countLine), "%u COUNTS / WHEEL TURN", countsPerRevolution);
  display.drawString(countLine, 120, 102);

  display.setTextColor(selected == 0 ? kAmber : kBrass);
  display.drawString(selected == 0 ? ">  SOUND" : "SOUND", 120, 126);
  display.setTextColor(kMutedInk);
  display.drawString(muted ? "MUTED" : "ON", 120, 146);
  display.setTextColor(selected == 1 ? kAmber : kBrass);
  display.drawString(selected == 1 ? ">  EFFECTS" : "EFFECTS", 120, 170);
  display.setTextColor(kMutedInk);
  display.drawString(presentationName(presentation), 120, 190);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.47f);
  display.setTextColor(kBrass);
  display.drawString("RING SELECT  /  TAP APPLY", 120, 216);
}

void Renderer::drawRgb565PathDiagnostic() {
  auto& display = M5Dial.Display;
  static constexpr uint16_t colors[] = {
      0xF800, 0x07E0, 0x001F, 0xFFFF, 0x0000, 0x8410};
  static constexpr const char* labels[] = {"R", "G", "B", "W", "K", "GRAY"};
  constexpr int16_t swatchSize = 20;
  constexpr int16_t firstX = 44;
  constexpr int16_t stepX = 30;
  constexpr int16_t directY = 74;
  constexpr int16_t packedY = 136;

  display.fillScreen(kIndigo);
  display.drawCircle(120, 120, 116, kBrass);
  display.drawCircle(120, 120, 111, kMutedInk);
  display.setTextDatum(middle_center);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.52f);
  display.setTextColor(kAmber);
  display.drawString("RGB565 PATH TEST", 120, 37);
  display.setTextSize(0.43f);
  display.setTextColor(kBrass);
  display.drawString("DIRECT DRAW", 120, 62);
  display.drawString("LITTLE-ENDIAN PACK", 120, 124);

  // The first row uses M5GFX color primitives. The second row is built from
  // the exact little-endian byte layout produced by the artwork packer and
  // drawn through the same adapter as mapped frames.
  uint16_t packedPixels[swatchSize * swatchSize];
  auto* packedBytes = reinterpret_cast<uint8_t*>(packedPixels);
  for (uint8_t i = 0; i < 6; ++i) {
    const int16_t x = firstX + i * stepX;
    display.fillRect(x, directY, swatchSize, swatchSize, colors[i]);
    display.drawRect(x, directY, swatchSize, swatchSize, kBrass);
    display.drawString(labels[i], x + swatchSize / 2, directY + 28);

    const uint8_t low = static_cast<uint8_t>(colors[i] & 0xFF);
    const uint8_t high = static_cast<uint8_t>(colors[i] >> 8);
    for (uint16_t pixel = 0; pixel < swatchSize * swatchSize; ++pixel) {
      packedBytes[pixel * 2] = low;
      packedBytes[pixel * 2 + 1] = high;
    }
    pushRgb565LittleEndian(display, x, packedY, swatchSize, swatchSize,
                           packedBytes);
    display.drawRect(x, packedY, swatchSize, swatchSize, kBrass);
    display.drawString(labels[i], x + swatchSize / 2, packedY + 28);
  }
  display.setTextSize(0.4f);
  display.setTextColor(kAmber);
  display.drawString("SAME COLORS IN BOTH ROWS = PASS", 120, 202);
}
