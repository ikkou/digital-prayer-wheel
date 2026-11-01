# Digital text / mantra mode proposal

Status: the user selected option 3 (wheel inscription), 2026-11-01. A separate reading/scroll mode remains unselected. The user's scope is to add
an actual digital scripture/mantra mode, initially the six-syllable mantra.

## Text source and storage

The Office of the Dalai Lama identifies the six-syllable mantra of Avalokiteshvara
as “Om mani padme hum”:
https://www.dalailama.com/news/2019/empowerment-of-avalokiteshvara-lord-of-the-world/

Store the verified text as UTF-8 in firmware together with its source, language,
version and a checksum. Rendering should use that same master text. Tibetan
Unicode spelling, punctuation, syllable boundaries, and font licensing still
need verification before shipping a Tibetan-script plate. Use deterministic
PC-side font shaping/rasterization; no AI-generated lettering as a master.

This is an interactive artwork and makes no claim of religious merit.

## Interaction options

1. Reading mode (recommended first): short tap switches CLASSIC / MANTRA.
   Show all six syllables in a balanced, large layout; ring advances the active
   emphasis through six stages across 360 degrees. The text remains stable and
   fully readable when stopped. Reverse input reverses the emphasis. The
   twelve-o'clock cue marks the end of a turn. A separate page can show a
   pronunciation guide/source without crowding the central composition.
2. Digital scroll: map signed angle to a horizontally or vertically moving
   text window. Appropriate for longer verified scripture excerpts; finite
   passages need a clear beginning/end or a deliberate wrap. No automatic
   inertia or unattended scrolling.
3. Wheel inscription: re-render the Blender master with verified glyph artwork
   mapped onto the cylinder. This best integrates with CLASSIC but lettering
   becomes small and occluded. It requires regenerating the coherent 32-frame
   source and does not replace an accessible reading screen.

## Rendering and capacity

Use one verified shaped layout and small glyph/coverage masks, tinted with the
CLASSIC antique-gold palette. Keep the background dark navy and the artwork's
position indicator separate from text. Do not duplicate the full animation.
A 240x240 4-bit coverage mask is 28,800 bytes before compression; a 160x48 mask
is 3,840 bytes. These are design budgets, not measured production assets.
The current asset partition has 442,094 bytes left, and the device has no PSRAM.
Embedded coverage masks need an explicit firmware-flash budget too.

A dedicated reading renderer can use the current angle from RotationModel and
a content manifest (UTF-8 text, source, language, glyph masks/layout). Keep the
existing wheel FrameAssetSource contract unchanged. A short tap currently
switches QUIET/GLOW, so adopting CLASSIC/MANTRA requires moving presentation
intensity to Settings. No gesture mapping is changed until the mode is built.

## Required quality gates

Verify text with an authoritative text and review the raster layout before
packing. Check 240x240 circle-safe bounds, correct marks/ligatures, readable
stroke thickness on the actual Dial, forward/reverse stage transitions,
loop closure and the zero-aligned sound cue. This document is not proof of
religious-text accuracy or an implemented display mode.
