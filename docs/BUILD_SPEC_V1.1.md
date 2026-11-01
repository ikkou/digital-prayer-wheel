# Digital Prayer Wheel — Build Spec v1.1

## Project intent

Create a portable digital mani wheel with the purchased M5Stack Dial v1.1. It is an interactive artwork inspired by the Tibetan Buddhist mani wheel; it does not reproduce or claim to confer religious merit. The central idea is that bodily turning gives life to a wheel in digital space. The first release should read as a complete exhibition object, not an electronics demo.

## Hardware and platform

- M5Stack Dial v1.1, ESP32-S3, 1.28-inch 240×240 circular LCD, encoder, touch panel, onboard buzzer, USB-C.
- Do not add external hardware during initial development.
- Verify official pinout, LCD/touch controllers, encoder resolution, buzzer controls, flash, PSRAM and the actual connected board. Do not infer GPIOs.
- Prefer PlatformIO, Arduino, M5Unified and M5GFX. Use the official M5Dial library/examples. Switch to ESP-IDF only for a documented compatibility or performance reason.

## Visual direction and asset constraints

Sacred Machinery / Digital Ritual: near-black indigo, brass and antique gold, amber and pale-gold light, fine engraved geometry and mantra-inspired ornamental marks, soft cinematic reflections. Avoid excessive neon and game-like effects.

The ESP32-S3 is not expected to render complex 3D in real time. Render a coherent closed rotation offline and convert it to a display-ready format. Frame choice must follow encoder angle in either direction. Measure storage, frame rate, decode bandwidth and loop continuity. Do not assume 360 full frames are appropriate. An AI concept image does not count as a rotation sequence. Missing master assets must be listed with exact specifications and production steps.

## Interaction

- Clockwise ring: positive rotation. Counterclockwise: negative rotation. Stop input and the wheel body stops exactly.
- Map counts to virtual degrees through a configurable calibration value.
- Fast rotation may add a restrained trail; low speed should expose detail.
- Separate body frame selection from metal glints, light trails, particles and decaying afterglow. Do not add autonomous body inertia.
- Short touch: cycle installed theme(s). Long touch: settings. In settings, use the ring to select. Debounce touch and distinguish gestures.
- CLASSIC is the only initial finished theme. Keep a theme extension point without shipping unfinished themes.
- States: Boot, Idle, Rotation, Afterglow, Settings.

## Sound and settings

Use the internal buzzer for a short startup cue and a restrained once-per-revolution cue. Include mute. Record actual volume / timbre limitations; an external I2S amp is future work only. Persist user settings in NVS and avoid frequent flash writes.

## Software boundaries

Separate Hardware, Input, RotationModel, Renderer, Effects, Audio, Settings and App. Input sampling must not block behind drawing. Avoid unnecessary dynamic allocations during normal operation.

## Milestones and quality gate

- P0: verify official hardware and local toolchain, build, connect and flash, validate display, encoder, touch and buzzer.
- P1 (primary quality gate): establish the CLASSIC art spec, create the high-quality animation source and device conversion, inspect it at 240×240 on the actual display.
- P2: encoder synchronization, calibration, angle, direction, frame selection and loop boundary.
- P3: restrained effects and afterglow.
- P4: touch, settings, sound and persistence.
- P5: measure frame rate, input latency, memory, flash, boot, long-running stability and angular integrity.

Targets are goals, not results until measured: 30+ FPS, under 50 ms input-to-screen response, visually seamless loop, stable continuous use and persistent settings.

## Execution and reporting

Inspect repository and official documentation before coding. Install necessary dependencies. Build and test autonomously. If a matching physical device is connected, flash and verify it. If not, request only the specific physical action needed. Record design deviations. Never describe unverified behavior as confirmed or lower visual quality to claim completion. Report source, build evidence, actual assets, physical test evidence and unresolved tasks.
