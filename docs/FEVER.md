# FEVER presentation — 2026-11-01

The user rejected the onboard BGM experiment and asked for increasingly
extravagant visual rewards as the wheel accumulates turns. This is an explicit
extension of the earlier restrained CLASSIC art direction; QUIET and GLOW remain
available. The reviewed wheel PNG sequence and mapped RGB565 pack are unchanged.

## Behavior

| Session full turns | Level | Overlay |
| --- | --- | --- |
| 0 | 0 | Single comet and a few sparks |
| 1 | 1 | First expanding wave and LEVEL UP |
| 3 | 2 | Additional comet, more sparks and particle tails |
| 6 | 3 | Wider trails, star-like sparks and radial rays |
| 10 | 4 | Third comet and restrained cool-blue accent |
| 20+ | 5 | Maximum trail thickness/density, FEVER MAX on reaching level 5 |

Every completed turn emits an expanding peripheral wave. Reaching a new level
emits a second wave plus a temporary LEVEL UP / FEVER MAX caption. Lower caption
shows level and turn total; a segmented bar shows progress to the next threshold.
Speed increases live brightness; accumulated full turns determine the stage.
Both directions count via the existing net signed full-turn/12-o'clock model;
back-and-forth partial travel does not fabricate full revolutions.

The wheel body still selects its frame only from encoder angle. No rotation
inertia, automatic body rotation or frame transformation was added. Overlay
geometry stays outside approximately radius 88; the center engraving is clear.
The position marker is drawn after the effect layers so it remains readable.

Effects fade after stopping; the final clean frame is explicitly drawn when
the animation expires. Level and turn count survive stops and menu navigation
in this boot session, then reset at restart. No per-turn NVS writes are added.
The normal 12-o'clock cue, boot/confirmation beeps and global mute remain.
No background music plays, and the former ambience key is removed once if found.

## Controls

FEVER is the new default when no `visual` preference exists. Short tap cycles
FEVER → QUIET → GLOW → FEVER. The preference is stored only on a change.
Hold 700 ms for Settings; ring selects SOUND or EFFECTS, tap changes its value,
hold again to return. The calibrated 64-count physical 1:1 mapping is read-only.

## Implementation and evidence

- `FeverModel.h`: pure cumulative tiers, burst timing and energy envelope.
- `FeverDrawing.h`: shared production/preview overlay, bounded primitive count.
- `Effects`: overlay integration, with the ordinary ring marker drawn last.
- `App`: observes revolution totals, schedules 33-ms animation frames and clears
  the last fade frame; settings interactions do not change the rotation model.
- `Renderer`: level/turn/progress display and mode selection.
- `Audio`: background synth removed; only short cues remain.

Host suite passes 113 checks (`logs/host-fever.log`). Tests include all tier
boundaries, stage cap, progress interpolation, duplicate/batched totals, reverse
energy, complete fade, retained tier, timer rollover, both-direction geometry
at 5-degree increments, circular bounds and a <260-primitive overlay budget.
Prior angle, zero cue, RGB565, touch and ring-indicator checks also remain.

`python3 tools/preview_fever.py` produces
`assets/diagnostics/fever/comparison.png` and `fever_max_preview.gif` by executing
the actual C++ overlay header on reviewed source frames. The host rasterizer
differs from M5GFX and omits runtime text; this is a UI preview, not measured
hardware performance or new master artwork.

Build succeeds without warnings/errors (`logs/build-fever.log`): app 522,337 B,
static RAM 25,772 B. Binary SHA256:
`f7ba25251cc78e639bf5c9b743095c53f48b3d3d1555a74ece8a0aae54bd31b8`.
Reviewed pack SHA256 remains
`9b483a188286b83aa35b9bf2f39bcd258c5fb1aeb6e30c824a75b820232fa167`.
Device upload, runtime metrics and physical review are recorded separately in
`VALIDATION.md`; no visual approval or sustained FPS claim is inferred here.
