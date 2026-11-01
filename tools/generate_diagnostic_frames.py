"""Create conspicuously temporary frames for storage/decoder verification only."""

import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".tools", "imaging"))
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(ROOT, ".tmp", "preview_frames")
FONT = "/System/Library/Fonts/Supplemental/Didot.ttc"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame-count", type=int, default=64)
    parser.add_argument("--title", default="JPEG / FLASH TEST")
    args = parser.parse_args()
    if args.frame_count < 1 or args.frame_count > 360:
        raise SystemExit("Frame count must be between 1 and 360")
    os.makedirs(OUT, exist_ok=True)
    try:
        title = ImageFont.truetype(FONT, 18)
        small = ImageFont.truetype(FONT, 12)
    except OSError:
        title = small = ImageFont.load_default()
    for index in range(args.frame_count):
        image = Image.new("RGB", (240, 240), (5, 10, 23))
        draw = ImageDraw.Draw(image)
        cx, cy = 120, 116
        draw.ellipse((5, 1, 235, 231), outline=(117, 80, 43), width=2)
        draw.ellipse((18, 14, 222, 218), outline=(77, 66, 61), width=1)
        draw.ellipse((28, 24, 212, 208), outline=(176, 124, 59), width=3)
        draw.ellipse((42, 38, 198, 194), outline=(71, 46, 25), width=6)
        draw.ellipse(
            (56, 52, 184, 180), fill=(12, 20, 38), outline=(178, 130, 69), width=2
        )
        for tick in range(16):
            a = math.tau * tick / 16 - math.pi / 2
            r0, r1 = 81, 91 if tick % 4 == 0 else 86
            draw.line(
                (
                    cx + r0 * math.cos(a),
                    cy + r0 * math.sin(a),
                    cx + r1 * math.cos(a),
                    cy + r1 * math.sin(a),
                ),
                fill=(223, 180, 108) if tick % 4 == 0 else (130, 93, 52),
                width=2,
            )
        a = math.tau * index / args.frame_count - math.pi / 2
        px, py = cx + 99 * math.cos(a), cy + 99 * math.sin(a)
        draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(255, 179, 71))
        draw.ellipse(
            (cx - 31, cy - 31, cx + 31, cy + 31),
            fill=(20, 31, 51),
            outline=(225, 183, 109),
            width=2,
        )
        draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(205, 112, 43))
        draw.text((cx, 25), args.title, font=title, fill=(218, 174, 100), anchor="mm")
        draw.text(
            (cx, 207),
            "DIAGNOSTIC ONLY  /  NOT FINAL",
            font=small,
            fill=(224, 202, 167),
            anchor="mm",
        )
        draw.text(
            (cx, 224),
            "%02d / %02d" % (index + 1, args.frame_count),
            font=small,
            fill=(152, 119, 74),
            anchor="mm",
        )
        image.save(os.path.join(OUT, "frame_%03d.png" % index), "PNG", optimize=True)
    print("Created diagnostic-only source frames in %s" % OUT)


if __name__ == "__main__":
    main()
