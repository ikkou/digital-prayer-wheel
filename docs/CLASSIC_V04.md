# CLASSIC v0.4 asset production

## Master scene

`assets/classic/classic_master_v04.blend` is the editable Blender scene. The
reproducible generator is `tools/render_classic_blender.py`. It builds an
antique-brass lathed drum, eight curved repoussé plaques with geometric lotus
rosettes, turned collars, pins and paired finials. Metallic Principled shaders
use procedural micro-bump, beveled relief meshes and an ambient-occlusion node.
Fixed softboxes and a fixed indigo-black backdrop provide the studio reflections.
No religious text is embedded.

The orthographic camera, background and lighting stay fixed. All wheel parts are
children of `WheelRoot`; frame `i` uses root Z rotation `-i * 11.25°` so the
sequence advances clockwise in the rendered view. The first physical Dial turn
must still be visually checked to confirm that the device's encoder sign matches
this direction.

Blender 5.1.2 on this macOS host crashes during Metal device selection when
started headless, before executing Python. The script was therefore executed in
Blender's GUI Python Console (focus a 3D View, press Shift+F4, then run):

```python
exec(compile(open('/Users/ikkou/Dev/digital-prayer-wheel/tools/render_classic_blender.py').read(), '/Users/ikkou/Dev/digital-prayer-wheel/tools/render_classic_blender.py', 'exec'), {'__file__':'/Users/ikkou/Dev/digital-prayer-wheel/tools/render_classic_blender.py', '__name__':'__main__'})
```

The master renders 32 fixed-view 480×480 Cycles CPU images at 40 samples with
denoising. `tools/prepare_classic_delivery.py` downsamples each to 240×240 with
Lanczos, creates the contact sheet and loop preview, invokes the packer, and
verifies the resulting bytes.

## Device pack contract

- Source: `assets/incoming/classic/frame_000.png` … `frame_031.png`.
- Dimensions: exactly 240×240 RGB PNG; opaque indigo background.
- Rotation: frame `i` is `i × 11.25°`; fixed camera and fixed lighting; no trails,
  particles or afterglow in the still frames.
- Device pack: `assets/built/classic/animation.dpw`, DPW1 v1, raw RGB565, row-major,
  little-endian 16-bit R5G6B5 pixels.
- 32-frame size: 3,686,674 bytes including header and index, within the
  4,128,768-byte assets partition.
- The `final_artwork` flag remains unset until the physical display is reviewed.

Run the production conversion and checks with:

```sh
python3 tools/prepare_classic_delivery.py
```

Outputs include `assets/classic/classic_v04_contact_sheet.png`,
`assets/classic/classic_v04_rotation_preview.gif` (0→31→0), and
`assets/classic/classic_v04_png_frames.zip`, and
`assets/classic/classic_v04_verification.json`. The verifier checks exact file
count and dimensions, DPW1 header and bounds, partition capacity, payload bytes
against little-endian RGB565 re-encoding, and the 31→0 image-difference magnitude
against the median adjacent-frame step.

After reviewing the art, flash the data partition without replacing firmware:

```sh
python3 tools/flash_asset_pack.py --port /dev/cu.usbmodem101
```

The serial port may differ on another host. Confirm clockwise and counterclockwise
turns, stop behavior, color/contrast and clipping on the physical circular LCD.
