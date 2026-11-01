"""Prepare an externally produced wheel sequence for the mapped assets partition.

Input: assets/incoming/classic/frame_000.png ... ordered square PNG/JPEG frames.
Output: assets/built/classic/animation.dpw plus a contact sheet for visual review.
"""

import json
import os
import struct
import sys
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".tools", "imaging"))
from PIL import Image, ImageOps

SOURCE = os.path.join(ROOT, "assets", "incoming", "classic")
DEVICE_DIR = os.path.join(ROOT, "assets", "built", "classic")
CONTACT = os.path.join(ROOT, "assets", "classic", "contact_sheet.png")
DEFAULT_FRAME_COUNT = 32
MAX_FRAME_BYTES = 48 * 1024
WIDTH = 240
HEIGHT = 240


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        default=SOURCE,
        help="directory containing the ordered source frames",
    )
    parser.add_argument(
        "--frame-count",
        type=int,
        default=DEFAULT_FRAME_COUNT,
        help="number of ordered frames (1-360)",
    )
    parser.add_argument(
        "--encoding",
        choices=("jpeg", "rgb565"),
        default="jpeg",
        help="on-device encoding; RGB565 uses little-endian 16-bit pixels",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(DEVICE_DIR, "animation.dpw"),
        help="output DPW1 package path",
    )
    parser.add_argument(
        "--contact-sheet", default=CONTACT, help="path for the review contact sheet"
    )
    parser.add_argument(
        "--final-artwork",
        action="store_true",
        help="set the package flag after reviewing the contact sheet and confirming this is the finished sequence",
    )
    args = parser.parse_args()
    if args.frame_count < 1 or args.frame_count > 360:
        raise SystemExit("Frame count must be between 1 and 360")
    source_dir = os.path.abspath(args.source_dir)
    frames = []
    columns = 8
    rows = (args.frame_count + columns - 1) // columns
    preview = Image.new("RGB", (WIDTH * columns, HEIGHT * rows), (5, 8, 18))
    for index in range(args.frame_count):
        path = os.path.join(source_dir, "frame_%03d.png" % index)
        if not os.path.isfile(path):
            alternate = os.path.join(source_dir, "frame_%03d.jpg" % index)
            if not os.path.isfile(alternate):
                raise SystemExit("Missing frame %03d. Expected %s" % (index, path))
            path = alternate
        image = Image.open(path)
        if image.width != image.height:
            raise SystemExit("Frame %03d must be square; got %r" % (index, image.size))
        image = ImageOps.exif_transpose(image).convert("RGBA")
        if image.size != (WIDTH, HEIGHT):
            image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        matte = Image.new("RGBA", image.size, (5, 10, 23, 255))
        matte.alpha_composite(image)
        rgb = matte.convert("RGB")
        if args.encoding == "jpeg":
            import io

            stream = io.BytesIO()
            rgb.save(stream, "JPEG", quality=91, subsampling=0, optimize=True)
            encoded = stream.getvalue()
            if len(encoded) > MAX_FRAME_BYTES:
                raise SystemExit(
                    "Frame %03d is %d bytes (limit %d). Lower JPEG quality/detail or reduce frame count."
                    % (index, len(encoded), MAX_FRAME_BYTES)
                )
        else:
            from array import array

            rgb565 = array("H")
            for red, green, blue in rgb.getdata():
                rgb565.append(((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3))
            if sys.byteorder != "little":
                rgb565.byteswap()
            encoded = rgb565.tobytes()
        frames.append(encoded)
        preview.paste(
            matte.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS),
            ((index % columns) * WIDTH, (index // columns) * HEIGHT),
        )

    header_size = 18
    table_end = header_size + args.frame_count * 8
    offsets = []
    cursor = table_end
    for frame in frames:
        offsets.append((cursor, len(frame)))
        cursor += len(frame)
    artwork_flags = 1 if args.final_artwork else 0
    encoding_code = 1 if args.encoding == "jpeg" else 0
    header = b"DPW1" + struct.pack(
        "<HHHHBBI",
        1,
        WIDTH,
        HEIGHT,
        args.frame_count,
        encoding_code,
        artwork_flags,
        cursor,
    )
    if len(header) != header_size:
        raise SystemExit("Internal package header size mismatch")

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    temp_path = out_path + ".tmp"
    with open(temp_path, "wb") as out:
        out.write(header)
        for offset, size in offsets:
            out.write(struct.pack("<II", offset, size))
        for frame in frames:
            out.write(frame)
    os.replace(temp_path, out_path)

    contact_path = os.path.abspath(args.contact_sheet)
    os.makedirs(os.path.dirname(contact_path), exist_ok=True)
    preview.save(contact_path, "PNG", optimize=True)
    profile = {
        "format": "DPW1/" + args.encoding.upper(),
        "version": 1,
        "width": WIDTH,
        "height": HEIGHT,
        "frame_count": args.frame_count,
        "degrees_per_frame": 360 / args.frame_count,
        "total_package_bytes": cursor,
        "largest_frame_bytes": max(map(len, frames)),
        "raw_rgb565_bytes": WIDTH * HEIGHT * 2 * args.frame_count,
        "final_artwork": args.final_artwork,
        "loop": "frame_%03d -> frame_000 is the same one-frame rotation step as all other intervals"
        % (args.frame_count - 1),
    }
    with open(os.path.splitext(out_path)[0] + ".json", "w", encoding="utf-8") as out:
        json.dump(profile, out, indent=2)
        out.write("\n")
    print(
        "Packed %d %s frames: %d bytes total, largest frame %d bytes"
        % (args.frame_count, args.encoding.upper(), cursor, max(map(len, frames)))
    )
    print(
        "Raw RGB565 reference: %d bytes; target partition budget: 4,128,768 bytes"
        % profile["raw_rgb565_bytes"]
    )
    print("Package: %s" % out_path)
    print("Review sequence before upload: %s" % contact_path)


if __name__ == "__main__":
    main()
