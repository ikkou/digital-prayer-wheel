# CLASSIC v0.5 — six-syllable mantra inscription

The user selected an inscription on the wheel itself. The rendering uses
Tibetan Uchen lettering from an actual shaped font, replacing geometric
rosettes on the cylindrical body. It is raised, bevelled metallic relief,
not a screen overlay or AI-generated imitation of lettering.

## Text and provenance

Master Unicode: `ཨོཾ་མ་ཎི་པདྨེ་ཧཱུྃ།`

Transliteration: oṃ maṇi padme hūṃ.

Textual source: Lotsawa House, *Prayer to Avalokiteśvara* by Nyoshul Lungtok
Tenpé Nyima, version 1.1-20240520, the first mantra occurrence:
https://www.lotsawahouse.org/tibetan-masters/nyoshul-lungtok/prayer-to-avalokiteshvara

The wider mantra identity is corroborated by 84000's *The Basket's Display*:
https://84000.co/translation/toh116

Only the short traditional mantra is used, not modern translated prayer prose.
The terminal Tibetan shad is retained. The `པདྨེ` conjunct and its vowel are
kept together, rather than being broken into invented individual characters to
force six equal panels. Six is the number of spoken syllables, not the number
of Unicode characters or visibly separated glyph groups.

Font: Noto Serif Tibetan SemiBold from the official Noto fonts repository,
under SIL OFL 1.1; font and license are in `assets/lettering/fonts/`.
HarfBuzz shapes the full text as one run. FontTools extracts the resulting
glyph outlines, including conjunct substitutions and mark offsets. The JSON
master records Unicode names, shaped glyph IDs/clusters, dependency versions,
font URL/version and SHA256. Missing glyphs cause generation to fail.

This is source/Unicode/font-based validation, not an expert calligraphic or
religious consecration review. The project remains an interactive artwork and
makes no claim of religious merit.

## Geometry and rendering

`prepare_mantra_lettering.py` generates the text master, flat proof, and vector
outlines. `render_classic_inscribed.py` reuses the v0.4 fixed scene and builds
bevelled 3D glyph meshes. Their filled font contours, holes and exact mark
positions are retained. Uniform glyph scaling preserves letter proportions;
extra space is added only after existing Tibetan tsheg separators. The flat
reading direction maps to increasing cylindrical azimuth without mirroring.

All glyph meshes are children of the same WheelRoot as the drum and finials.
No image is independently regenerated per angle. The model remains fixed in
shape while rotating -11.25 degrees per frame. The camera, backdrop and studio
lighting remain fixed. `render_inscribed_frames.py` records a static-transform
audit and renders frame 32 at the exact frame-0 orientation for comparison.
The dynamic outer indicator and afterglow remain firmware layers.

Reproduce:

1. Install `requirements-dev.txt` in the Python virtual environment described
   in the project README, and keep the bundled font/license. The scripts also
   accept the original project-local `.tools/lettering` setup as a fallback.
2. Run `python3 tools/prepare_mantra_lettering.py`.
3. Run `tools/render_classic_inscribed.py` in Blender Python to build/render
   the complete sequence, or run it with `DPW_FRAME_INDICES=[0]` for a proof.
4. Run `tools/render_inscribed_frames.py` in Blender Python for the additional
   transform audit and exact full-turn repeat render.
5. Run `python3 tools/prepare_inscribed_delivery.py` to downsample, package,
   create previews/ZIP and verify the result.
6. Flash the reviewed package using `tools/flash_asset_pack.py --port PORT
   --package assets/classic_v05/animation.dpw`.

The GUI Python console is used because the installed Blender's background
process previously crashed during Metal initialization. Renders themselves use
Cycles CPU, 40 samples at 480×480, then Lanczos downsampling to 240×240.
The original v0.4 source frames and asset pack remain in the development
workspace; those duplicate historical deliveries are excluded from the public tree.
The user confirmed on the actual Dial that the lettering is visible and the
rotation looks natural (「文字の刻印が見え、回転も自然」). The identical RGB565
pixel payload is now marked reviewed (`final_artwork=true`). The release builder
checks the payload hash in `assets/classic_v05/physical_review.json` before
applying that flag; changed pixels cannot inherit the previous review.
This approves the visual asset; it is not a claim that long-duration or
high-speed firmware qualification is complete.
