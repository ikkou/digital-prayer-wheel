#!/usr/bin/env python3
"""Shape a source-verified Tibetan inscription into immutable vector outlines."""

import hashlib, json, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / ".tools/lettering"), str(ROOT / ".tools/imaging")]
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from PIL import Image, ImageDraw

TEXT = "ཨོཾ་མ་ཎི་པདྨེ་ཧཱུྃ།"
FONT = ROOT / "assets/lettering/fonts/NotoSerifTibetan-SemiBold.ttf"
OUT = ROOT / "assets/lettering"


class FlattenPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contours = []
        self.current = []

    def _moveTo(self, p):
        self.current = [p]

    def _lineTo(self, p):
        self.current.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, 17):
            t = i / 16
            s = 1 - t
            self.current.append(
                tuple(
                    s**3 * p0[j]
                    + 3 * s * s * t * p1[j]
                    + 3 * s * t * t * p2[j]
                    + t**3 * p3[j]
                    for j in (0, 1)
                )
            )

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        for i in range(1, 13):
            t = i / 12
            s = 1 - t
            self.current.append(
                tuple(s * s * p0[j] + 2 * s * t * p1[j] + t * t * p2[j] for j in (0, 1))
            )

    def _closePath(self):
        if len(self.current) > 2:
            self.contours.append(self.current)
        self.current = []

    def _endPath(self):
        self._closePath()


def main():
    fontdata = FONT.read_bytes()
    tt = TTFont(FONT)
    glyphset = tt.getGlyphSet()
    for c in TEXT:
        if ord(c) not in tt.getBestCmap():
            raise RuntimeError("Missing character " + hex(ord(c)))
    face = hb.Face(fontdata)
    font = hb.Font(face)
    hb.ot_font_set_funcs(font)
    buf = hb.Buffer()
    buf.add_str(TEXT)
    buf.guess_segment_properties()
    buf.language = "bo"
    hb.shape(font, buf)
    x = 0
    y = 0
    glyphs = []
    allpts = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        if info.codepoint == 0:
            raise RuntimeError("Shaping returned .notdef")
        name = tt.getGlyphName(info.codepoint)
        pen = FlattenPen(glyphset)
        glyphset[name].draw(pen)
        contours = [
            [
                [round(px + x + pos.x_offset, 4), round(py + y + pos.y_offset, 4)]
                for px, py in contour
            ]
            for contour in pen.contours
        ]
        allpts += [p for contour in contours for p in contour]
        glyphs.append(
            dict(
                glyph=name,
                gid=info.codepoint,
                cluster=info.cluster,
                advance=pos.x_advance,
                contours=contours,
            )
        )
        x += pos.x_advance
        y += pos.y_advance
    bounds = [
        min(p[0] for p in allpts),
        min(p[1] for p in allpts),
        max(p[0] for p in allpts),
        max(p[1] for p in allpts),
    ]
    manifest = dict(
        text=TEXT,
        transliteration="oṃ maṇi padme hūṃ",
        script="Tibetan Uchen",
        source_url="https://www.lotsawahouse.org/tibetan-masters/nyoshul-lungtok/prayer-to-avalokiteshvara",
        source_version="1.1-20240520",
        source_line="six-syllable mantra, first occurrence",
        unicode_normalization="exact source sequence, not normalized",
        codepoints=[f"U+{ord(c):04X} {unicodedata.name(c)}" for c in TEXT],
        font=FONT.name,
        font_sha256=hashlib.sha256(fontdata).hexdigest(),
        font_license="SIL OFL 1.1 (fonts/OFL.txt)",
        shaper="HarfBuzz via uharfbuzz " + hb.__version__,
        fonttools_version=__import__("fontTools").__version__,
        advance=x,
        bounds=bounds,
        glyphs=glyphs,
        missing_glyphs=0,
        policy="Whole inscription shaped as one run; padme subjoined form and all vowel/diacritic offsets retained. No invented syllable split.",
    )
    manifest["font_download_url"] = (
        "https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSerifTibetan/NotoSerifTibetan-SemiBold.ttf"
    )
    manifest["font_version"] = tt["name"].getDebugName(5)
    (OUT / "mantra_master.txt").write_text(TEXT + "\n", encoding="utf-8")
    (OUT / "mantra_outlines.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )
    scale = 1200 / (bounds[2] - bounds[0])
    height = int((bounds[3] - bounds[1]) * scale) + 100
    image = Image.new("RGB", (1280, height + 80), "#080d18")
    draw = ImageDraw.Draw(image)
    contours = [c for g in glyphs for c in g["contours"]]

    def area(c):
        return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(c, c[1:] + c[:1])) / 2

    reference = area(max(contours, key=lambda c: abs(area(c))))
    for c in sorted(contours, key=lambda c: abs(area(c)), reverse=True):
        coords = [
            (40 + (px - bounds[0]) * scale, 50 + (bounds[3] - py) * scale)
            for px, py in c
        ]
        draw.polygon(coords, fill="#e0bd75" if area(c) * reference > 0 else "#080d18")
    draw.text(
        (40, height + 20),
        "Verified source text / Noto Serif Tibetan SemiBold / HarfBuzz outlines",
        fill="#e0bd75",
    )
    image.save(OUT / "mantra_outline_proof.png")
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in ["text", "advance", "bounds", "missing_glyphs", "font_sha256"]
            },
            ensure_ascii=False,
        )
    )
    print("glyphs", [(g["glyph"], g["cluster"]) for g in glyphs])


if __name__ == "__main__":
    main()
