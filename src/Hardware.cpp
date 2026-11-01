#include "Hardware.h"

#include <M5Dial.h>
#include <Preferences.h>

void Hardware::begin() {
  // Dial v1.1 battery mode uses HOLD (GPIO46) to keep the power latch active.
  // Set it before initializing other peripherals so wake-on-battery stays on.
  pinMode(46, OUTPUT);
  digitalWrite(46, HIGH);
  Serial.begin(115200);
  Serial.println("DPW_POWER_HOLD;gpio=46;state=1");
  // M5GFX caches its display autodetection in NVS. A stale board ID can
  // suppress M5Dial's panel setup, so discard only that library-owned key.
  Preferences graphicsPrefs;
  if (graphicsPrefs.begin("M5GFX", false)) {
    const uint32_t cachedBoard = graphicsPrefs.getUInt("AUTODETECT", 0);
    if (cachedBoard != static_cast<uint32_t>(m5::board_t::board_M5Dial)) {
      graphicsPrefs.remove("AUTODETECT");
    }
    Serial.printf("DPW_M5GFX_CACHE;previous=%lu;cleared=%u\n",
                  static_cast<unsigned long>(cachedBoard),
                  cachedBoard != static_cast<uint32_t>(m5::board_t::board_M5Dial));
    graphicsPrefs.end();
  }
  auto cfg = M5.config();
  cfg.fallback_board = m5::board_t::board_M5Dial;
  M5Dial.begin(cfg, true, false);  // official M5Dial API: encoder enabled, RFID disabled
  Serial.printf("DPW_HARDWARE;board=%d;display_board=%d;displays=%u;width=%d;height=%d\n",
                static_cast<int>(M5.getBoard()), static_cast<int>(M5Dial.Display.getBoard()),
                static_cast<unsigned>(M5.getDisplayCount()), M5Dial.Display.width(), M5Dial.Display.height());
  M5Dial.Display.setBrightness(180);
  M5Dial.Display.fillScreen(0x0862);  // near-black indigo, followed by the rendered art
}

void Hardware::printDiagnostics() const {
  Serial.printf("DPW_READY; board=M5Dial-v1.1-candidate; flash=%u; psram=%u; display=%dx%d; encoder_gpio=A41/B40; touch=FT3267; buzzer=Speaker.tone\n",
                ESP.getFlashChipSize(), ESP.getPsramSize(), M5Dial.Display.width(), M5Dial.Display.height());
  Serial.println("INPUT: rotate ring; short touch=CLASSIC presentation; long touch=settings");
}
