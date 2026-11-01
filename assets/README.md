# Asset layout

## Current release

`classic_v05/` is the canonical, physically reviewed CLASSIC artwork:

- `classic_master_v05.blend`: reproducible 3D master (Blender 5.1.2).
- `frames/frame_000.png` … `frame_031.png`: 240×240 source frames at 11.25° steps.
- `animation.dpw`: 3,686,674-byte reviewed DPW1 RGB565 little-endian pack.
- `animation.json`: device profile.
- Contact sheet and 0→31→0 GIF: visual inspection artifacts.
- Verification/audit/review JSON: provenance, hashes and limits of approval.

Pack SHA256: `9b483a188286b83aa35b9bf2f39bcd258c5fb1aeb6e30c824a75b820232fa167`.

`lettering/` contains the source text, shaped font outlines and the bundled
Noto font/OFL license. `diagnostics/fever/` contains previews of firmware effects;
those previews are not a replacement for physical display review.

## Generated local output

`built/`, `incoming/`, old `classic/` deliveries, duplicate ZIP archives and
Blender backup files are excluded from Git. Existing local copies are preserved.
Provide `--source-dir` explicitly when importing replacement artwork.

See [`docs/ASSET_SPEC.md`](../docs/ASSET_SPEC.md) for the byte layout and
[`tools/README.md`](../tools/README.md) for reproduction commands.
