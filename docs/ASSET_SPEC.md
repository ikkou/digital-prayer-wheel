# CLASSIC artwork handoff

CLASSIC v0.5 is the current physically reviewed artwork. Its Tibetan mantra
inscription is produced by `tools/render_classic_inscribed.py`, using verified
text and shaped font outlines. Details: `docs/INSCRIPTION.md`.
The 32-frame little-endian RGB565 pack is 3,686,674 bytes. The user confirmed
lettering visibility and natural rotation on the Dial, so `final_artwork=true`.
Current sources: `assets/classic_v05/frames/`; deliverables and validation are
in `assets/classic_v05/`. The active package is
`assets/built/classic/animation.dpw`, with provenance in `active.json`.
The former v0.4 geometric artwork remains archived and reproducible.

## Source sequence

- Supply one ordered closed-loop sequence in `assets/incoming/classic/`, named `frame_000.png` through `frame_031.png` for the current 32-frame production candidate. PNG and JPEG sources are accepted. The importer also supports a different count when measured performance justifies it.
- Each file is a square, full-display composition. It is resized to 240×240 with Lanczos filtering and composited over `#050A17` if it has transparency.
- Keep the camera, wheel center, silhouette, lighting and background fixed. Frame 000 is 0°; subsequent frames advance clockwise. For 32 frames, each step is 11.25°, with frame 31 at 348.75°; frame 31 to frame 00 must be the same one-step transition as every other boundary.
- Do not bake speed trails or afterglow into the stills. The firmware draws these in a separate effect layer.
- The reference direction is Sacred Machinery / Digital Ritual: indigo darkness, aged brass, amber and pale gold, detailed engraved geometry and soft reflections, without game-like neon. The art team owns that visual production; no placeholder concept image counts as an animation.

## Package and flash layout

The importer creates `assets/built/classic/animation.dpw`, a packed `DPW1` sequence that is memory-mapped from the ESP32-S3 data partition. Flash the package after uploading the firmware:

```sh
python3 tools/flash_asset_pack.py --port PORT --package assets/classic_v05/animation.dpw
```

Find PORT with `pio device list`. The reviewed v0.5 package is shipped in the
repository and needs no regeneration. `assets/built/` is ignored generated
output for custom imports. Review `assets/classic_v05/classic_v05_contact_sheet.png`
before flashing. New imports remain `final_artwork=false` unless explicitly
marked after physical review; the bundled v0.5 pack is already reviewed.

The 8 MB flash table reserves 4 MiB for the application and 0x3F0000 bytes (4,128,768 bytes) for the `assets` partition at 0x410000. The app maps this partition with `esp_partition_mmap`; no filesystem mount or per-frame file copy is involved. The custom partition subtype is 0x40.

## Format and measured trade-offs

The renderer accepts 240×240 RGB565 frames and baseline JPEG frames through the same replaceable `IFrameAssetSource` interface. RGB565 is the current production candidate because it removes runtime JPEG decode and preserves color and shape deterministically. Frame count and encoding remain subject to final sequence review and high-speed physical testing.

- One RGB565 frame is 115,200 bytes. A 32-frame package is 3,686,674 bytes including the DPW1 header and index, and fits with about 442 KB remaining.
- 35 RGB565 frames fit in the partition; 36 do not. 64 raw RGB565 frames require 7,372,800 bytes before the index and cannot fit beside firmware.
- A diagnostic 32-frame RGB565 package drawn from mapped flash took 14,236 µs for the boot frame on the actual Dial. The previous LittleFS raw-RGB565 path measured about 68 ms/frame; 64 JPEG frames through LittleFS measured about 101 ms/frame. With CLASSIC v0.4 flashed from mapped flash, a physical ring-turn capture reported 30.7–35.5 FPS, 14.1 ms mean draw time, 14.17 ms maximum draw time and 15 ms maximum poll-to-draw latency. The serial capture crossed a full turn and included a reverse step; see `logs/runtime-classic-v04.log`. Mapped JPEG remains unbenchmarked.
- The drawing time is not a 30 FPS claim. Measure frame time and input-to-display delay during real clockwise and counterclockwise turns with the final package before selecting the release format/count.

`import_artwork.py` accepts `--frame-count 1..360`, `--encoding rgb565|jpeg`, `--source-dir`, `--output`, and `--contact-sheet`. For RGB565, each image is packed row-major from top-left to bottom-right as 16-bit RGB565 (`R5 G6 B5`), little-endian, two bytes per pixel, with no alpha channel. JPEG is baseline 4:4:4 JPEG with the importer’s selected quality. Each JPEG frame is limited to 48 KiB. The importer writes the header, per-frame offset/length table and image payloads; it never sets the finished-art flag unless requested.

The 32-frame RGB565 candidate uses 11.25° angular steps and fits the mapped partition with 442,094 bytes spare. A 35-frame RGB565 package fits (4,032,298 bytes); 36 frames exceed the 4,128,768-byte partition. The firmware parser also enforces a hard limit of 360 frames for compressed formats. CLASSIC v0.4 sizes, hashes, binary-layout checks and the 31→0 seam comparison are recorded in `assets/classic/classic_v04_verification.json`.

## DPW1 v1 binary header

| Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | `DPW1` magic |
| 4 | 2 | version (1, little-endian) |
| 6 | 2 | width (240) |
| 8 | 2 | height (240) |
| 10 | 2 | frame count |
| 12 | 1 | encoding (`0` RGB565, `1` JPEG) |
| 13 | 1 | flags (bit 0 means reviewed finished artwork) |
| 14 | 4 | complete package byte length |
| 18 | 8 × frame count | frame data offset and byte length, each little-endian uint32 |
| after table | variable | frame payloads, in index order |

At boot, the source validates dimensions, count, encoding, package bounds and frame sizes before accepting the mapped package. If the package is missing or invalid, the app uses the explicitly labeled diagnostic renderer. `Renderer::setSource()` allows a different asset provider to be substituted without changing rotation mapping, app state, or effects.
