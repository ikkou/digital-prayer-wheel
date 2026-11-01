# Third-party notices

## Bundled font

`assets/lettering/fonts/NotoSerifTibetan-SemiBold.ttf` is distributed under the
SIL Open Font License 1.1. The full copyright notice and license are preserved
in [`assets/lettering/fonts/OFL.txt`](assets/lettering/fonts/OFL.txt).
Font provenance and the exact source URL/hash are recorded in
`assets/lettering/mantra_outlines.json` and [`docs/INSCRIPTION.md`](docs/INSCRIPTION.md).

## Build dependencies

The following are fetched by the build/tools and are not vendored in this tree:

| Dependency | Pinned version | License / source |
| --- | --- | --- |
| M5Dial | 1.0.3 | See upstream; no standalone license file at the checked version: https://github.com/m5stack/M5Dial |
| M5Unified | 0.2.29 | MIT, https://github.com/m5stack/M5Unified |
| M5GFX | 0.2.36 | MIT, https://github.com/m5stack/M5GFX |
| Arduino-ESP32 | 2.0.17 via espressif32 6.12.0 | See https://github.com/espressif/arduino-esp32 |
| PlatformIO Core | 6.1.19 | Apache-2.0, https://github.com/platformio/platformio-core |
| Pillow | 11.3.0 | HPND, https://github.com/python-pillow/Pillow |
| uharfbuzz | 0.51.7 | Apache-2.0, https://github.com/harfbuzz/uharfbuzz |
| fonttools | 4.60.2 | MIT, https://github.com/fonttools/fonttools |

Blender 5.1.2 was used to build the scene and render the artwork.
Blender is licensed under GPL-3.0-or-later: https://www.blender.org/about/license/.
The scene and generated artwork are project assets, not Blender application code.

## Project license status

No project-wide reuse license has been selected for the original source code,
documentation or artwork. Public hosting does not itself grant an open-source
license. The bundled font remains subject to its own license above.
