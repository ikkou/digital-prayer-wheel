# Validation record

Do not mark a capability complete without evidence. This record separates serial/build confirmation from checks that still require physical operation.
Current checkpoint (2026-11-01): CLASSIC v0.5 Tibetan inscription is physically
reviewed and running on the Dial (`final=1`). Physical ring/marker 1:1 mapping
and the twelve-o'clock cue are user-confirmed. The latest host suite passes
72 checks. See the final sections below for current evidence; earlier
measurements and pending notes are retained as dated development history.
Long-duration operation, sustained high-speed rendering and battery-only use
are not claimed complete.


## P0 — hardware, build and flash

| Check | Result | Evidence |
|---|---|---|
| Official project target and dependencies | Pass | PlatformIO, Arduino, `m5stack-stamps3`; M5Dial 1.0.3, M5Unified/M5GFX |
| M5Dial LCD initialization | Pass | Runtime `board=12;display_board=12;displays=1;width=240;height=240` |
| Flash / PSRAM | Pass | Runtime `flash=8388608;psram=0` |
| Firmware build | Pass | Latest indicator revision: app 516,153 / 4,194,304 B; static RAM 25,748 / 327,680 B |
| Firmware upload | Pass | esptool verified bootloader, partition table and app hashes; hard reset completed |
| Custom asset partition | Pass | 3,686,676-byte package flashed at 0x410000; esptool hash verified |
| Mapped external frame source | Pass | Runtime `DPW_ASSET_SOURCE=FLASH_MMAP`; 32 frames, RGB565, 3,686,674 package bytes, `final=0` |
| Rendered frame on actual LCD driver | Pass | Runtime `DPW_BOOT_FRAME;draw_us=14246;encoding=0`; user confirmed that the physical LCD is showing an image |
| M5GFX cache / panel ID compatibility | Pass | Runtime cache reset then board 12; see [`HARDWARE.md`](HARDWARE.md) |

## Render measurements

| Path | Data | Measured draw time | Status |
|---|---|---:|---|
| LittleFS + JPEG | 64 diagnostic frames, 2,178,743 B | about 101 ms/frame | Below 30 FPS target |
| LittleFS + RGB565 | 32 diagnostic frames, 3,686,674 B | about 68 ms/frame | Below 30 FPS target |
| Direct mapped flash + RGB565 | 32 CLASSIC v0.4 frames, 3,686,674 B | 14.1 ms average; 14.17 ms max | Physical ring-turn serial capture: 30.7–35.5 FPS, poll-to-draw max 15 ms |

The first two rows are comparative baselines from an earlier firmware build. The latest build maps the raw package directly and avoids the LittleFS buffer/copy path. Mapped JPEG is supported by code but has not been benchmarked. The CLASSIC run crossed one complete revolution and logged a reverse encoder step; visual confirmation of the displayed direction remains pending.

## Host-side model checks

`python3 tools/run_host_tests.py` compiled the hardware-independent models with Clang C++11 and passed 51 checks. Coverage includes angle normalization and frame wrap, clockwise/counterclockwise frame steps, cumulative travel-based revolution events, stop timeout and signed speed, touch debounce / short tap / one-shot long press / millisecond wrap, the encoder-scale menu cycle, and the little-endian RGB565 asset-push conversion for red, green, blue, white, black and gray. These checks do not substitute for touch, audio, display or NVS validation on the Dial.

Code review: `App::update()` polls `M5Dial.update()`, encoder and touch before rendering, with no explicit waits or per-frame filesystem reads. The full-screen panel transfer is synchronous; the mapped RGB565 boot frame took 14.24 ms. This keeps a single measured draw under the 50 ms response target, but effect-overlay cost and sustained high-speed input scheduling still need a physical-turn measurement.

## RGB565 display-path correction

The attached physical-device recording showed coherent wheel geometry but
lavender/pink highlights and a gray-green background. The rendered PNG's low
RGB565 quantization error does not explain those colors. Source inspection found
that the packer writes little-endian RGB565 while M5GFX's default
`pushImage(uint16_t*)` path treats bytes as already bus-ordered. The mapped
frame source now enables M5GFX RGB565 conversion only around that synchronous
push and restores the previous setting afterward. The JPEG path and all other
display drawing remain unchanged.

The known-color diagnostic firmware previously built and flashed successfully.
The direct-fill / packed-pixel swatch comparison was not explicitly confirmed by
the user. The current device runs normal CLASSIC firmware with the scoped
RGB565 correction. Review of sampled frames from both user recordings confirms
that IMG_1907.MOV's lavender/cyan colors and gray-green background changed to a
gold wheel and dark navy background in IMG_1912.MOV. The latter still shows very
bright highlights; camera exposure prevents a definitive judgment of actual
panel clipping. The artwork remains unapproved (`final_artwork=false`).

## P1 — artwork

The reproducible Blender master and CLASSIC v0.4 sequence are present. The 32 PNG frames are exactly 240×240; the little-endian RGB565 package is 3,686,674 bytes and leaves 442,094 bytes in the assets partition. The 31→0 image-difference magnitude is 1.064× the median adjacent step. The animation, contact sheet and JSON checks are in `assets/classic/`; the pack was flashed and serial-verified. A physical recording revealed the color-path issue above, so CLASSIC v0.4 is not yet approved. The package keeps `final_artwork=false`.

## User-operated checks still needed

- Review the corrected CLASSIC v0.4 image on the lit circular panel for color, detail and clipping. The package stays marked `final_artwork=false` until this review.
- Confirm clockwise direction against a clockwise ring turn; the rendered sequence advances clockwise. Turn counterclockwise and stop as well. Serial output is tagged `DPW_ENCODER`.
- Short-tap once; confirm the presentation tag changes. Hold touch for about 700 ms; confirm Settings opens. Serial tags are `DPW_PRESENTATION` and `DPW_SETTINGS`.
- The user confirmed the revolution beep. Check startup cue, mute and silence through Settings.
- The current ring-turn capture measured 30.7–35.5 FPS, 14.1 ms average draw and a 15 ms maximum poll-to-draw delay. Repeat during both directions after confirming the visual direction; goals are 30 FPS and under 50 ms.
- Change a setting, reboot and confirm it persists.

The application and device are currently running. The serial monitor can be attached with:

```sh
PLATFORMIO_CORE_DIR="$PWD/.pio-core" PYTHONPATH="$PWD/.tools/platformio" \
python3 .tools/platformio/bin/platformio device monitor \
  --port /dev/cu.usbmodem1101 --baud 115200 --rts 0 --dtr 0
```

## Recorded implementation decision

Only CLASSIC is installed, so a short tap currently toggles QUIET/GLOW effect intensity within CLASSIC instead of cycling to an unavailable theme. This keeps the tap useful without presenting an unfinished theme as complete. The setting persists in NVS. If theme cycling becomes meaningful after another finished theme is supplied, this mapping should be revisited.

Revolution cues now count accumulated absolute encoder travel in degrees while the displayed wheel angle remains signed and reversible. This avoids a false cue when reversing across the 0° boundary. The behavior is covered by host checks; actual cue audibility still needs listening confirmation.

## Video review and indicator revision — 2026-11-01

Both named user recordings were found in Downloads. IMG_1912.MOV is 23.60 s;
12 frames sampled at two-second intervals and a close crop at 4 s were inspected
alongside a 4 s frame from IMG_1907.MOV. This was a sampled-frame review, not
an independent listening test or a complete temporal/flicker analysis.
The corrected recording shows gold/white metal and a dark blue background.
The outer double ornament is thin, and the moving angular cue is hard to
distinguish. The user explicitly identified the moving arc/marker as the problem.
Extracts are under `.tmp/video-review/`.

The overlay now uses an 8-pixel gold marker with a pale center and dark border,
a brass track and four reference ticks. The marker remains at the exact input
angle after stopping. A single 3-pixel trail lies behind the direction of motion
and fades independently; small particle dots were removed to make the cue
unambiguous. QUIET changes trail intensity without dimming the position marker.
No source PNG or flashed artwork package was modified.

Production geometry is shared in `include/RingIndicator.h`. The reproducible
host raster preview (`python3 tools/preview_indicator.py`) is at
`assets/diagnostics/indicator_revision/comparison.png`; it is a host preview,
not a photograph of the new device screen. Eight new checks cover cue location,
round-display bounds, loop closure, reverse-trail side and stopped visibility;
all 51 checks passed (`logs/host-indicator.log`). Build and upload passed with
esptool hash verification (`logs/build-indicator.log`, `logs/flash-indicator.log`).

Runtime (`logs/runtime-indicator.log`) reports `DPW_INDICATOR;version=2`,
1,786 microseconds for the stationary overlay, a 12,079 microsecond raw frame,
and one 13,656 microsecond complete draw with a 13 ms poll-to-draw maximum.
Metrics now include overlay/caption cost in addition to the image transfer.
These are startup/idle measurements; sustained rotation with the new trail,
physical-turn/virtual-turn calibration remain pending. The user then operated the updated Dial and explicitly confirmed that the moving marker is easier to see (「見やすくなった」). This confirms indicator legibility for that use; CLASSIC artwork approval remains separate.
The application was left running with its serial port closed.

## Twelve-o'clock revolution cue — 2026-11-01

The user requested the cue at twelve o'clock. Absolute travelled distance could
trigger the previous cue at another angle after a reversal. The model now keeps
signed partial progress relative to the last zero-angle boundary; reversing
cancels partial progress, and each net +360 or -360 degrees emits a turn event.
Partial rocking and immediate zero-boundary reversals do not count as turns.
Double precision and a small rounding tolerance keep zero alignment consistent
for both binary and nonbinary encoder scales. Batched input can count multiple
turns but emits at most one audible notification per rendered update; the marker
can already lie past zero when several counts arrive in the same poll.

The pending notification is played after drawing the corresponding position.
Host checks passed 69 cases, including fractional count scales, aborted turns,
reversals, zero jitter and batched full turns (`logs/host-zero-cue.log`). Build
passed with app 517,329 B and static RAM 25,756 B (`logs/build-zero-cue.log`).
Upload passed with esptool hash verification (`logs/flash-zero-cue.log`).
The user then turned the ring and confirmed the audible cue at the displayed
twelve-o'clock position (「0時で鳴る」). Zero-position cue timing is physically
confirmed for that operation. This does not establish the physical-ring /
virtual-wheel 1:1 ratio, reverse-direction audibility or high-speed timing.

This replaces the prior absolute-travel counting decision above.

## Physical 1:1 mapping and inscribed CLASSIC v0.5 — 2026-11-01

The physical-turn ratio is now 64 decoded counts per revolution, not 256.
The user confirmed physical ring 1 turn = screen marker 1 turn, with a measured
0→64 count and a zero-angle revolution event. This supersedes earlier notes
that physical-turn calibration is pending. The 64-count setting survives the
asset-flash reboot; settings navigation uses four counts per detent. A one-time
NVS migration changes only the encoder mapping. Host checks passed 72 cases
(`logs/host-physical-mapping.log`); the firmware upload passed hash verification
(`logs/flash-physical-mapping.log`).

The user selected wheel inscription, so no separate MANTRA reading mode was
added. CLASSIC v0.5 uses source-verified Tibetan Unicode shaped by HarfBuzz with
Noto Serif Tibetan SemiBold and converted into curved, bevelled gold geometry.
See `INSCRIPTION.md` and `assets/lettering/mantra_outlines.json` for source and
font provenance. No missing glyphs were found; the original padme conjunct
and vowel/diacritic positions are preserved. This is source/font validation,
not a claim of independent expert calligraphic review.

The 32-frame source, master, contact sheet, GIF and package are in
`assets/classic_v05/`. A 33-sample render audit passed fixed local transforms,
fixed camera/light state, and exact -index×11.25° root phases. Frame 32 (exact
360° repeat) matches frame 0 pixel for pixel. The 31→0 step difference is
1.0461× the median interior step. Every frame was verified as 240×240 and every
package payload matched its source's little-endian RGB565 bytes. The package
is 3,686,674 bytes within the 4,128,768-byte partition; SHA256 is
`0fead8360c1801f9f3eedda5c4c8a994a2ad6ac4d6fbafdd4d8e458b1dcbc8b7`.
Reports: `logs/package-classic-v05.log`,
`assets/classic_v05/classic_v05_verification.json`.

The new asset pack was flashed with hash verification (`logs/flash-classic-v05.log`).
Runtime `logs/runtime-classic-v05.log` confirms the mapped 32-frame pack and
240×240 display; raw boot draw was 12,045 µs, overlay 1,774 µs, and one complete
frame 13,678 µs. These are startup/idle samples, not sustained-rotation FPS.
The active build package is updated; v0.4 is retained as `animation_v04.dpw`
and its original PNGs/master. The user subsequently confirmed the new lettering and natural rotation; the approved package now sets final_artwork=true (see release record below). The app is running and serial
port closed.

## Reviewed v0.5 release

User feedback: 「文字の刻印が見え、回転も自然」. The reviewed pixel-payload
SHA256 is recorded in `assets/classic_v05/physical_review.json`. The release
builder enables the reviewed-artwork flag only when generated pixels still
match that hash. Final package SHA256: `9b483a188286b83aa35b9bf2f39bcd258c5fb1aeb6e30c824a75b820232fa167`.
Only the header review flag changed from the physically reviewed candidate.
`logs/flash-classic-v05-approved.log` records hash-verified upload, and
`logs/runtime-classic-v05-approved.log` reports 32 RGB565 frames, `final=1`,
240×240, and persisted 64-count mapping. Boot raw draw was 12,051 µs, overlay
1,775 µs; one complete draw was 13,720 µs with 13 ms poll-to-draw maximum.
No sustained-rotation or endurance claim is inferred from those idle readings.
The app is running and all serial readers have been closed.

## Optional onboard soundscape — 2026-11-01

Added `SOUNDSCAPE / RITUAL` as a third Settings row; default OFF and retained
under NVS `ambience`. Global mute stops both ambience voices and cue playback.
This uses no recording/partition change and leaves the reviewed CLASSIC pixel
package unchanged (SHA256 `9b483a188286b83aa35b9bf2f39bcd258c5fb1aeb6e30c824a75b820232fa167`).

The hardware-independent suite passes 93 checks (`logs/host-soundscape.log`),
including timing, fade, cue ducking/recovery, enable/mute/disable, scheduling
stalls, uint32 millis rollover and correct bidirectional three-row navigation.
Build succeeds without compiler warnings/errors: app 518,721 B, static RAM
25,780 B (`logs/build-soundscape.log`). Binary SHA256
`71c6441d8018238c4c2ce057c17d35fc6999152eb8c896b0c0fc16d4c7e91c4a`.
Firmware upload to `/dev/cu.usbmodem1101` succeeded and esptool verified the
written hash (`logs/flash-soundscape.log`). No art partition was rewritten.

The phrase is an original, sparse synthesized chime rather than a traditional
chant, authentic bell recording or claim of religious sound reproduction.
Physical listening, simultaneous rotation/cue audibility and persistence after
changing the new setting remain pending. Host checks do not establish acoustic
quality or sustained device performance. See `AUDIO_EXPANSION.md` and the
runtime evidence appended in `logs/runtime-soundscape.log`.

### Soundscape revision 2, after physical feedback

The user heard the initial prototype and reported 「聞こえるけれどノイズっぽい」.
That trial is rejected acoustically. Revision 2 removes the second voice,
raises the register and shortens the tail to 700 ms; it still requires listening
and is not approved BGM. Settings now select only SOUND or SOUNDSCAPE, with the
confirmed physical 1:1 mapping shown read-only. One-time mapping migration v2
restores 64 from an accidental 128-count selection during the earlier menu trial.

93 checks pass (`logs/host-soundscape-v2.log`). Final build/upload succeeded
(`logs/build-soundscape-v2.log`, `logs/flash-soundscape-v2.log`); app 518,421 B,
static RAM 25,780 B. Binary SHA256
`92cc8669938c0078b5a735179103ff6d16f83a545e850ee8d57d4b2a73914dae`.
The runtime log confirms 240×240, approved mapped artwork, 64 counts per turn,
soundscape OFF and mute OFF (`logs/runtime-soundscape-v2.log`). Thus the second
version is installed but not yet acoustically checked. Existing artwork hash
is unchanged. An idle frame sample was 13,718 µs / 13 ms poll-to-draw;
no sustained-rotation or endurance result follows from that sample.

## FEVER visual progression / buzzer BGM removed — 2026-11-01

User request: reject buzzer BGM and add increasingly extravagant visuals as
turns accumulate. The BGM synth/header/menu/playback path is removed. Existing
boot, confirmation and 12-o'clock short cues remain. FEVER is the default new
presentation, with QUIET and GLOW selectable by short tap or Settings/EFFECTS.
The calibrated 64-count mapping and reviewed CLASSIC v0.5 pack are preserved.

Levels increase at 1 / 3 / 6 / 10 / 20 session full turns. Full-turn waves,
tier-up captions, comets, sparks and rays are layered separately from body
rotation. Both directions use the original net-full-turn counter. Effects
fade to zero after stopping; level remains for the session and resets on boot.
No per-turn settings/flash writes are performed. Design and controls: `FEVER.md`.

113 host checks pass (`logs/host-fever.log`), covering all thresholds, large
totals, burst expiry/duplicate events, reverse energy, fade to zero, timer wrap,
geometry across all tiers/both directions, and the existing input/render tests.
The production header was also inspected with the host raster preview:
`assets/diagnostics/fever/comparison.png` / `fever_max_preview.gif`.
These previews omit the actual M5GFX runtime text and do not constitute a
physical display-quality or FPS measurement.

Build succeeds without warnings/errors (`logs/build-fever.log`): app 522,337 B,
static RAM 25,772 B. Binary SHA256
`f7ba25251cc78e639bf5c9b743095c53f48b3d3d1555a74ece8a0aae54bd31b8`.
Upload to `/dev/cu.usbmodem1101` completed with verified flash hash
(`logs/flash-fever.log`). The asset partition was not written. Asset SHA256
remains `9b483a188286b83aa35b9bf2f39bcd258c5fb1aeb6e30c824a75b820232fa167`.

Runtime `logs/runtime-fever.log` confirms 240×240, 32 mapped reviewed frames,
64 counts per wheel turn, `bgm=removed`, FEVER mode and the configured thresholds.
Idle full-frame sample: 15,734 µs, 15 ms poll-to-draw; heap 343,376 B.
Physical tier progression, preferred extravagance and high-tier sustained FPS
remain pending user operation; idle FPS=0 is expected because idle has no redraws.
