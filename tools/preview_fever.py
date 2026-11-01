#!/usr/bin/env python3
"""Inspect production overlay geometry against the reviewed CLASSIC v0.5 PNGs.

Only the host rasterizer differs from M5GFX; geometry runs the real C++ header.
Output is a diagnostic UI preview, not a replacement animation/artwork pack.
"""

from pathlib import Path
import subprocess
import sys
import tempfile

from preview_indicator import ROOT, rgb
from PIL import Image, ImageDraw

CPP = r"""
#include "FeverDrawing.h"
#include "RingIndicator.h"
#include <cstdio>
#include <cstdlib>
struct Display {
  unsigned color565(unsigned char r,unsigned char g,unsigned char b) {
    return ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3);
  }
  void drawCircle(int x,int y,int r,unsigned c) { std::printf("circle %d %d %d %u\n",x,y,r,c); }
  void fillCircle(int x,int y,int r,unsigned c) { std::printf("disk %d %d %d %u\n",x,y,r,c); }
  void drawLine(int x,int y,int x1,int y1,unsigned c) { std::printf("line %d %d %d %d %u\n",x,y,x1,y1,c); }
};
int main(int,char** argv) {
  Display d; FeverModel model;
  const float angle=std::atof(argv[1]),speed=std::atof(argv[2]),age=std::atof(argv[3]);
  const auto turns=std::strtoul(argv[4],nullptr,10), now=std::strtoul(argv[5],nullptr,10);
  model.observeTurns(turns,1000);
  drawFeverEffects(d,angle,speed,now,model.frame(now,speed,age));
  drawRingIndicator(d,angle,speed,age,false);
}
"""


def render(binary, angle, speed, age, turns, now):
    index = int(angle / 11.25) % 32
    im = Image.open(ROOT / f"assets/classic_v05/frames/frame_{index:03d}.png").convert(
        "RGB"
    )
    im.putdata(
        [
            rgb(((r & 248) << 8) | ((g & 252) << 3) | (b >> 3))
            for r, g, b in im.getdata()
        ]
    )
    ops = subprocess.check_output(
        [str(binary), str(angle), str(speed), str(age), str(turns), str(now)], text=True
    )
    d = ImageDraw.Draw(im)
    for line in ops.splitlines():
        kind, *args = line.split()
        v = list(map(int, args))
        c = rgb(v.pop())
        if kind == "line":
            d.line(tuple(v), fill=c)
        else:
            x, y, r = v
            box = (x - r, y - r, x + r, y + r)
            if kind == "disk":
                d.ellipse(box, fill=c)
            else:
                d.ellipse(box, outline=c)
    return im


def main():
    out = ROOT / "assets/diagnostics/fever"
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("START / 0 TURNS", 0, 720, -1, 1400),
        ("LEVEL 1 / 1 TURN", 1, 720, -1, 1400),
        ("LEVEL 2 / 3 TURNS", 3, 720, -1, 1400),
        ("LEVEL 3 / 6 TURNS", 6, 720, -1, 1400),
        ("LEVEL 4 / 10 TURNS", 10, 720, -1, 1400),
        ("MAX / 20 TURNS", 20, 720, -1, 1400),
        ("MAX / REVERSE", 20, -720, -1, 1400),
        ("MAX / STOPPED", 20, 0, 3, 5000),
    ]
    sheet = Image.new("RGB", (264 * 4, 280 * 2), "#070b16")
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
        for i, (label, turns, speed, age, now) in enumerate(cases):
            im = render(binary, 90, speed, age, turns, now)
            im.save(out / f"case_{i:02d}.png")
            x, y = i % 4 * 264 + 12, i // 4 * 280 + 12
            sheet.paste(im, (x, y))
            labels.text((x, y + 244), label, fill="#ecc58b")
        frames = [
            render(binary, (i * 11.25) % 360, 720, -1, 20, 1000 + i * 50)
            for i in range(48)
        ]
        frames[0].save(
            out / "fever_max_preview.gif",
            save_all=True,
            append_images=frames[1:],
            duration=50,
            loop=0,
        )
    sheet.save(out / "comparison.png")
    print(out / "comparison.png")


if __name__ == "__main__":
    main()
