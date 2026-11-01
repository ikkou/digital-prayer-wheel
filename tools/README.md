# Development tools

Run Python tools from the repository root after installing `requirements-dev.txt`.
Run scripts importing `bpy` inside Blender 5.1.2 instead of the system Python.

| Task | Entry point |
| --- | --- |
| Host model checks | `python tools/run_host_tests.py` (C++11 compiler required) |
| Convert an ordered PNG sequence into DPW1 | `python tools/import_artwork.py --help` |
| Flash the shipped artwork | `python tools/flash_asset_pack.py --port PORT --package assets/classic_v05/animation.dpw` |
| Shape the bundled Tibetan font into outlines | `python tools/prepare_mantra_lettering.py` |
| Build the CLASSIC v0.5 3D scene and render | Blender: `tools/render_classic_inscribed.py` |
| Audit/rerender the saved master, including the exact 360° repeat | Blender: `tools/render_inscribed_frames.py` |
| Package and audit the rendered v0.5 sequence | `python tools/prepare_inscribed_delivery.py` |
| Preview FEVER geometry on the reviewed PNGs | `python tools/preview_fever.py` |
| Preview the position marker | `python tools/preview_indicator.py` |

`render_classic_blender.py` supplies the common fixed-camera scene builder used
by the v0.5 renderer. `prepare_classic_delivery.py` supplies common conversion
and verification helpers. Their default v0.4 outputs and the diagnostic frame
generator are retained development tools, not the active shipped artwork.

The full render/package workflow writes intermediates under `.tmp/` and requires
the 480×480 renders. It is unnecessary for building/flashing the already reviewed
32-frame pack. Rebuilding changed artwork does not inherit the old physical
review: the delivery builder checks the RGB565 payload hash before marking it
reviewed. See [`docs/INSCRIPTION.md`](../docs/INSCRIPTION.md).

`m5gfx_gc9a01_id_patch.py` is invoked by PlatformIO before compilation and applies
the small probe-ID compatibility patch only to the downloaded M5GFX dependency.
