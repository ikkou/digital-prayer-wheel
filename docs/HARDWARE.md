# M5Stack Dial v1.1 hardware

Specification source: [M5Stack Dial v1.1 official product documentation](https://docs.m5stack.com/en/core/Dial_v1.1) and its linked Arduino examples.

| Component | Official specification | Implementation / runtime evidence |
|---|---|---|
| Controller | Stamp-S3A, ESP32-S3FN8, 240 MHz | esptool identified ESP32-S3 QFN56 rev 0.2 |
| Flash / PSRAM | 8 MB flash; PSRAM not listed | Runtime reports 8,388,608 flash bytes and 0 PSRAM |
| LCD | 1.28-inch GC9A01, 240×240, SPI | M5Unified reports board 12, one display, 240×240; user confirmed image is visible |
| Touch | FT3267 | Official M5Unified touch API; physical gesture test pending |
| Encoder | 16 detents, 64 pulses/rev; A=GPIO41, B=GPIO40 | M5Dial API; physical one-turn capture was exactly 64 counts after the mapping correction; user confirmed ring/marker 1:1 |
| Buzzer | onboard | M5Unified `Speaker.tone()`; user confirmed one-revolution beep |
| Battery | 1.25 mm, 2-pin lithium-battery socket with onboard charging circuit | Firmware drives HOLD GPIO46 high at startup; build, flash and boot log verified; battery-only operation has not been physically tested |
| USB | USB-C, USB OTG, USB Serial/JTAG | Host port `/dev/cu.usbmodem1101`; esptool reports USB-Serial/JTAG |
| LCD pins | RS=GPIO4, MOSI=GPIO5, SCK=GPIO6, CS=GPIO7, reset=GPIO8, backlight=GPIO9 | Configured by M5Dial/M5Unified |
| Touch pins | SDA=GPIO11, SCL=GPIO12, INT=GPIO14 | Configured by M5Dial/M5Unified |
| Buzzer pin | GPIO3 | Used through the library speaker API |

The official encoder sample calls `M5Dial.begin(cfg, true, false)` and samples `M5Dial.Encoder.read()` after `M5Dial.update()`. The official touch path uses `M5Dial.Touch.getDetail()` / `isPressed()`. The buzzer sample calls `M5Dial.Speaker.tone(frequency, duration)`.

The Dial v1.1 includes a lithium-battery charging circuit and a 1.25 mm 2-pin
battery socket. In battery-only mode, the official startup sequence requires
HOLD (GPIO46) to be driven high so the power latch remains active. This project
now sets that pin at the start of `Hardware::begin()`. Battery connector
polarity, battery compatibility, charging behavior and runtime still require
verification against the supplied pack before standalone use.

## Battery HOLD firmware verification

On 2026-11-01, the GPIO46 HOLD update built successfully (RAM 25,748 B;
application 515,745 B), was flashed to the connected Dial, and passed esptool
hash verification. Its serial boot log reported
`DPW_POWER_HOLD;gpio=46;state=1`, followed by the M5Dial board/display IDs and
the 240×240 panel. This verifies the startup pin behavior on USB power; the
battery socket has not yet been populated, so standalone power-on and charging
remain unverified.

## External BGM expansion (not implemented)

The onboard GPIO3 buzzer is appropriate for the short revolution cue, not for
music. [M5Unified's speaker configuration](https://github.com/m5stack/M5Unified/blob/master/src/utility/Speaker_Class.hpp) supports an external I²S output
(`pin_data_out`, `pin_bck`, `pin_ws`) and WAV/PCM playback, so a small I²S class-D
amplifier plus speaker is a feasible addition. The official PORT.A/PORT.B pin
maps expose GPIOs for those signals, but the final pin assignment must be
checked against the board schematic before wiring. The current firmware still
uses only the onboard buzzer.

The asset partition is 4,128,768 bytes; the current 32-frame artwork uses
3,686,674 bytes, leaving 442,094 bytes before filesystem/package overhead.
That limits directly stored uncompressed music to a short loop. Longer playback
would need smaller artwork, a compressed-audio decoder/streaming path, or other
storage. The Dial has no PSRAM, and playback current, speaker level and battery
runtime would need measurement after the amplifier is connected.

## Runtime compatibility finding

The connected panel returned `0xffff019a`; M5GFX 0.2.36's stock board autodetection only matched the alternate `0x019a00` byte ordering. The project pre-script adds the observed low-16-bit match, and startup removes only a stale `M5GFX/AUTODETECT` board cache when it is not board 12 (M5Dial). With that correction, the device reports `board=12`, `display_board=12`, one display at 240×240. The workaround is local and narrow; it does not change other M5GFX detection rules.

## Actual device identification

esptool verified ESP32-S3 QFN56 rev 0.2, 8 MB GD flash, 40 MHz crystal, USB-Serial/JTAG and MAC `9c:cc:01:e1:16:84`. After application startup, M5GFX reports the M5Dial board ID and display dimensions. The user confirmed the display is visible and the revolution beep works. The user also reported that a physical ring turn does not yet produce exactly one artwork turn. CLASSIC appearance approval and touch gesture behavior remain open. Encoder-turn mapping was subsequently corrected to 64 decoded counts/revolution and the user confirmed physical 1:1 motion. After the indicator revision was flashed, the user confirmed that the moving marker is easier to see.

## Physical encoder mapping correction — 2026-11-01

The former 256 default applied a quadrature ×4 factor to the documented
64 decoded counts again. An initial roughly one-turn capture ended at 67,
consistent with a near-64 turn and endpoint uncertainty. After adopting the
64-count mapping, the user made another exact physical turn and the log recorded
0→64 counts, displayed angle 0, and `DPW_REVOLUTION` at twelve o'clock. The user
confirmed 「リング1周で目印も1周する」. Settings navigation now uses 4 counts per
detent (16 detents). A one-time NVS mapping-version migration selects 64 while
retaining mute and presentation preferences. A subsequent reboot with the v0.5
asset pack still reports 64 counts per turn. See `logs/runtime-physical-mapping.log`
and `logs/runtime-classic-v05.log`. Reverse-ratio and high-speed stress checks
remain separate from this confirmed clockwise physical-turn test.
