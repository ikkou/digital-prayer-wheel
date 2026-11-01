#!/usr/bin/env python3
"""Raster preview of the production RingIndicator.h geometry on actual frames."""

import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".tools/imaging"))
from PIL import Image, ImageDraw

CPP = r"""
#include "RingIndicator.h"
#include <cstdio>
#include <cstdlib>
struct Display {
  unsigned color565(unsigned char r, unsigned char g, unsigned char b) {
    return ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3);
  }
  void drawCircle(int x,int y,int r,unsigned c) { std::printf("circle %d %d %d %u\n",x,y,r,c); }
  void fillCircle(int x,int y,int r,unsigned c) { std::printf("disk %d %d %d %u\n",x,y,r,c); }
  void drawLine(int x,int y,int x1,int y1,unsigned c) { std::printf("line %d %d %d %d %u\n",x,y,x1,y1,c); }
};
int main(int, char** argv) {
  Display d;
  drawRingIndicator(d, std::atof(argv[1]), std::atof(argv[2]), std::atof(argv[3]), std::atoi(argv[4]));
}
"""


def rgb(word):
    r, g, b = (word >> 11) & 31, (word >> 5) & 63, word & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def main():
    out = ROOT / "assets/diagnostics/indicator_revision"
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("BEFORE / STOP", 0, 0, 2, 0),
        ("NEW / STOP", 0, 0, 2, 0),
        ("CW / 90 DEG", 90, 920, -1, 0),
        ("CCW / 90 DEG", 90, -920, -1, 0),
        ("AFTERGLOW", 90, 920, 0.5, 0),
        ("STOP / QUIET", 90, 0, 2, 1),
    ]
    sheet = Image.new("RGB", (3 * 264, 2 * 278), "#070b16")
    labels = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        source, binary = Path(tmp) / "preview.cpp", Path(tmp) / "preview"
        source.write_text(CPP)
        subprocess.run(
            [
                "clang++",
                "-std=c++11",
                "-I",
                str(ROOT / "include"),
                str(source),
                "-o",
                str(binary),
            ],
            check=True,
        )
        for i, (label, angle, speed, age, quiet) in enumerate(cases):
            index = int(angle / 11.25) % 32
            im = Image.open(
                ROOT / f"assets/classic_v05/frames/frame_{index:03d}.png"
            ).convert("RGB")
            # Quantize the source as the real RGB565 pack does.
            im.putdata(
                [
                    rgb(((r & 248) << 8) | ((g & 252) << 3) | (b >> 3))
                    for r, g, b in im.getdata()
                ]
            )
            if i:
                ops = subprocess.check_output(
                    [str(binary), str(angle), str(speed), str(age), str(quiet)],
                    text=True,
                )
                draw = ImageDraw.Draw(im)
                for op in ops.splitlines():
                    kind, *args = op.split()
                    values = list(map(int, args))
                    color = rgb(values.pop())
                    if kind == "line":
                        draw.line(tuple(values), fill=color)
                    else:
                        x, y, r = values
                        bounds = (x - r, y - r, x + r, y + r)
                        if kind == "circle":
                            draw.ellipse(bounds, outline=color)
                        else:
                            draw.ellipse(bounds, fill=color)
                (out / f"case_{i:02d}_commands.txt").write_text(ops)
            im.save(out / f"case_{i:02d}.png")
            x, y = i % 3 * 264 + 12, i // 3 * 278 + 12
            sheet.paste(im, (x, y))
            labels.text((x, y + 244), label, fill="#dcc18b")
    sheet.save(out / "comparison.png")
    print(out / "comparison.png")


if __name__ == "__main__":
    main()
