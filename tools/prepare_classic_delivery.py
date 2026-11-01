"""Downsample Blender masters, build CLASSIC v0.4 previews, and verify DPW1 RGB565."""

import argparse
import array
import hashlib
import json
import os
import statistics
import struct
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".tools", "imaging"))
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

TAG = "v04"
ART_TEXT = "none; geometric ornament only"
FINAL_ARTWORK = False
COUNT = 32
SIZE = (240, 240)
STEP = 360.0 / COUNT
PARTITION_BUDGET = 4_128_768
HI_DIR = os.path.join(ROOT, ".tmp", "classic_" + TAG, "render_480")
SOURCE_DIR = os.path.join(ROOT, "assets", "incoming", "classic")
OUT_DIR = os.path.join(ROOT, "assets", "classic")
PACK_PATH = os.path.join(ROOT, "assets", "built", "classic", "animation.dpw")


def font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def rgb565_bytes(image):
    pixels = array.array("H")
    for red, green, blue in image.convert("RGB").getdata():
        pixels.append(((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3))
    if sys.byteorder != "little":
        pixels.byteswap()
    return pixels.tobytes()


def mean_abs_diff(a, b):
    diff = ImageStat.Stat(ImageChops.difference(a, b))
    return sum(diff.mean[:3]) / 3.0


def build_contact_sheet(frames, path):
    columns = 8
    tile_w, tile_h = 270, 278
    sheet = Image.new("RGB", (columns * tile_w, 4 * tile_h + 56), (4, 7, 17))
    draw = ImageDraw.Draw(sheet)
    title_font = font(21)
    label_font = font(16)
    draw.text(
        (24, 17),
        "DIGITAL PRAYER WHEEL   /   CLASSIC " + TAG + "   /   32 × 11.25°",
        fill=(222, 191, 134),
        font=title_font,
    )
    for index, image in enumerate(frames):
        x = (index % columns) * tile_w
        y = 56 + (index // columns) * tile_h
        draw.rounded_rectangle(
            (x + 9, y + 7, x + 261, y + 271),
            radius=9,
            fill=(8, 12, 26),
            outline=(88, 65, 37),
            width=1,
        )
        sheet.paste(image, (x + 15, y + 13))
        draw.text(
            (x + 18, y + 255),
            "%02d    %6.2f°" % (index, index * STEP),
            fill=(228, 196, 139),
            font=label_font,
        )
    sheet.save(path, "PNG", optimize=True)


def convert_frames():
    if not os.path.isdir(HI_DIR):
        raise SystemExit("Blender masters not found: " + HI_DIR)
    os.makedirs(SOURCE_DIR, exist_ok=True)
    frames = []
    for index in range(COUNT):
        source_path = os.path.join(HI_DIR, "frame_%03d.png" % index)
        if not os.path.isfile(source_path):
            raise SystemExit("Missing high-resolution master: " + source_path)
        with Image.open(source_path) as source:
            if source.size != (480, 480):
                raise SystemExit(
                    "Expected 480x480 Blender master: %s (%r)"
                    % (source_path, source.size)
                )
            image = source.convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)
        dest = os.path.join(SOURCE_DIR, "frame_%03d.png" % index)
        image.save(dest, "PNG", optimize=True)
        frames.append(image)
    return frames


def make_previews(frames):
    os.makedirs(OUT_DIR, exist_ok=True)
    contact = os.path.join(OUT_DIR, "classic_" + TAG + "_contact_sheet.png")
    build_contact_sheet(frames, contact)
    # Explicit 0..31..0 order shows the closing one-step transition.
    preview_frames = frames + [frames[0]]
    gif_path = os.path.join(OUT_DIR, "classic_" + TAG + "_rotation_preview.gif")
    preview_frames[0].save(
        gif_path,
        save_all=True,
        append_images=preview_frames[1:],
        duration=105,
        loop=0,
        optimize=False,
        disposal=2,
    )
    return contact, gif_path


def make_frame_archive():
    archive_path = os.path.join(OUT_DIR, "classic_" + TAG + "_png_frames.zip")
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as archive:
        for index in range(COUNT):
            path = os.path.join(SOURCE_DIR, "frame_%03d.png" % index)
            archive.write(path, arcname=os.path.basename(path))
    return archive_path


def build_package():
    temp_contact = os.path.join(ROOT, ".tmp", "classic_" + TAG, "importer_contact.png")
    cmd = [
        sys.executable,
        os.path.join(ROOT, "tools", "import_artwork.py"),
        "--source-dir",
        SOURCE_DIR,
        "--frame-count",
        str(COUNT),
        "--encoding",
        "rgb565",
        "--output",
        PACK_PATH,
        "--contact-sheet",
        temp_contact,
    ]
    if FINAL_ARTWORK:
        cmd.append("--final-artwork")
    subprocess.run(cmd, check=True, cwd=ROOT)


def verify(frames):
    issues = []
    archive_path = os.path.join(OUT_DIR, "classic_" + TAG + "_png_frames.zip")
    contact_path = os.path.join(OUT_DIR, "classic_" + TAG + "_contact_sheet.png")
    preview_path = os.path.join(OUT_DIR, "classic_" + TAG + "_rotation_preview.gif")
    names = sorted(
        name
        for name in os.listdir(SOURCE_DIR)
        if name.startswith("frame_") and name.endswith(".png")
    )
    expected = ["frame_%03d.png" % index for index in range(COUNT)]
    if names != expected:
        issues.append(
            "source frame set mismatch: %d PNGs, expected exactly %d"
            % (len(names), COUNT)
        )
    for index in range(COUNT):
        path = os.path.join(SOURCE_DIR, "frame_%03d.png" % index)
        with Image.open(path) as image:
            if image.size != SIZE:
                issues.append("frame %03d size is %r" % (index, image.size))
    if os.path.isfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as archive:
            if archive.namelist() != expected:
                issues.append("PNG archive members do not match ordered 32-frame set")
    else:
        issues.append("PNG archive missing")
    if os.path.isfile(contact_path):
        with Image.open(contact_path) as contact:
            if contact.size != (2160, 1168):
                issues.append("contact-sheet dimensions invalid: %r" % (contact.size,))
    else:
        issues.append("contact sheet missing")
    if os.path.isfile(preview_path):
        with Image.open(preview_path) as preview:
            if preview.n_frames != COUNT + 1 or preview.size != SIZE:
                issues.append(
                    "rotation preview must be 240x240 with 33 frames (0..31..0)"
                )
    else:
        issues.append("rotation preview missing")
    if not os.path.isfile(PACK_PATH):
        issues.append("DPW1 pack was not created")
        return issues, {}
    data = open(PACK_PATH, "rb").read()
    if len(data) > PARTITION_BUDGET:
        issues.append("pack exceeds 4,128,768-byte partition")
    if len(data) < 18 or data[:4] != b"DPW1":
        issues.append("DPW1 header invalid")
        return issues, {"package_bytes": len(data)}
    version, width, height, count, encoding, flags, declared = struct.unpack(
        "<HHHHBBI", data[4:18]
    )
    if (version, width, height, count, encoding) != (1, 240, 240, 32, 0):
        issues.append(
            "unexpected header: %r" % ((version, width, height, count, encoding),)
        )
    if bool(flags & 1) != FINAL_ARTWORK:
        issues.append("final-artwork flag does not match the release review state")
    if declared != len(data):
        issues.append("header length does not match actual pack length")
    table_end = 18 + COUNT * 8
    expected_offset = table_end
    for index in range(COUNT):
        offset, length = struct.unpack_from("<II", data, 18 + index * 8)
        if offset != expected_offset or length != 240 * 240 * 2:
            issues.append(
                "frame %03d offset/length invalid: %d/%d" % (index, offset, length)
            )
            break
        image = frames[index]
        if data[offset : offset + length] != rgb565_bytes(image):
            issues.append("frame %03d differs from little-endian RGB565 source" % index)
            break
        expected_offset += length
    if expected_offset != len(data):
        issues.append("payload tail or package truncation detected")

    adjacent = [mean_abs_diff(frames[i], frames[i + 1]) for i in range(COUNT - 1)]
    seam = mean_abs_diff(frames[-1], frames[0])
    median_step = statistics.median(adjacent)
    ratio = seam / median_step if median_step else 0.0
    # Compare seam magnitude against interior one-frame steps, not against zero.
    seam_ok = median_step > 0 and 0.5 <= ratio <= 2.0
    if not seam_ok:
        issues.append(
            "loop seam difference %.4f is not comparable to median step %.4f (ratio %.3f)"
            % (seam, median_step, ratio)
        )
    stats = {
        "package_bytes": len(data),
        "partition_budget_bytes": PARTITION_BUDGET,
        "partition_spare_bytes": PARTITION_BUDGET - len(data),
        "frame_count": count,
        "dimensions": [width, height],
        "degrees_per_frame": STEP,
        "encoding": "RGB565 little-endian, row-major",
        "flags": flags,
        "final_artwork": bool(flags & 1),
        "expected_rgb565_payload_bytes": COUNT * 240 * 240 * 2,
        "median_adjacent_rgb_mean_abs_delta": median_step,
        "seam_31_to_00_rgb_mean_abs_delta": seam,
        "seam_to_median_step_ratio": ratio,
        "seam_continuity_check": "PASS" if seam_ok else "REVIEW",
        "png_archive_members": COUNT,
        "rotation_preview_frames": COUNT + 1,
        "contact_sheet_size": [2160, 1168],
        "camera_background_lighting": "fixed by static scene objects in Blender master",
        "rotation": "all wheel parts parented to WheelRoot; Z rotation = -index*11.25 degrees",
        "religious_text": ART_TEXT,
    }
    return issues, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-package", action="store_true")
    args = parser.parse_args()
    frames = convert_frames()
    contact, preview = make_previews(frames)
    archive = make_frame_archive()
    if not args.skip_package:
        build_package()
    issues, stats = verify(frames)
    stats["contact_sheet"] = os.path.relpath(contact, ROOT)
    stats["rotation_preview"] = os.path.relpath(preview, ROOT)
    stats["png_archive"] = os.path.relpath(archive, ROOT)
    stats["source_directory"] = os.path.relpath(SOURCE_DIR, ROOT)
    stats["asset_sha256"] = {}
    for index in range(COUNT):
        path = os.path.join(SOURCE_DIR, "frame_%03d.png" % index)
        with open(path, "rb") as item:
            stats["asset_sha256"][os.path.basename(path)] = hashlib.sha256(
                item.read()
            ).hexdigest()
    report_path = os.path.join(OUT_DIR, "classic_" + TAG + "_verification.json")
    with open(report_path, "w", encoding="utf-8") as report:
        json.dump(stats, report, indent=2)
        report.write("\n")
    print(json.dumps(stats, indent=2))
    print("VERIFICATION=" + ("PASS" if not issues else "FAIL"))
    for issue in issues:
        print("ERROR=" + issue)
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
