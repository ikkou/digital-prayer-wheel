#!/usr/bin/env python3
"""Package and validate the v0.5 inscribed master; preserve all v0.4 originals."""

import hashlib, importlib.util, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "delivery", ROOT / "tools/prepare_classic_delivery.py"
)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
d.TAG = "v05"
d.HI_DIR = str(ROOT / ".tmp/classic_v05/render_480")
d.SOURCE_DIR = str(ROOT / "assets/classic_v05/frames")
d.OUT_DIR = str(ROOT / "assets/classic_v05")
d.PACK_PATH = str(ROOT / "assets/classic_v05/animation.dpw")
lettering = json.loads((ROOT / "assets/lettering/mantra_outlines.json").read_text())
d.ART_TEXT = lettering["text"]
original_build_package = d.build_package
review_path = ROOT / "assets/classic_v05/physical_review.json"


def build_reviewed_package():
    if review_path.exists():
        from PIL import Image

        review = json.loads(review_path.read_text())
        digest = hashlib.sha256()
        for i in range(32):
            with Image.open(Path(d.SOURCE_DIR) / ("frame_%03d.png" % i)) as image:
                digest.update(d.rgb565_bytes(image.convert("RGB")))
        if digest.hexdigest() != review["rgb565_payload_sha256"]:
            raise RuntimeError(
                "Artwork differs from the physically reviewed pixels; a new review is required."
            )
        d.FINAL_ARTWORK = True
    original_build_package()


d.build_package = build_reviewed_package
if __name__ == "__main__":
    d.main()
    report_path = ROOT / "assets/classic_v05/classic_v05_verification.json"
    report = json.loads(report_path.read_text())
    audit = json.loads((ROOT / "assets/classic_v05/render_audit.json").read_text())
    assert len(audit["frames"]) == 33
    for i, f in enumerate(audit["frames"]):
        assert f["phase_index"] == i % 32 and f["static_scene_unchanged"]
        assert math.isclose(f["root_z"], -math.radians((i % 32) * 11.25), abs_tol=1e-6)
    from PIL import Image, ImageChops

    with (
        Image.open(Path(d.HI_DIR) / "frame_000.png") as a,
        Image.open(Path(d.HI_DIR) / "frame_032.png") as b,
    ):
        assert (
            ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None
        )
    assert lettering["missing_glyphs"] == 0
    assert (
        lettering["text"]
        == (ROOT / "assets/lettering/mantra_master.txt").read_text().strip()
    )
    assert audit["text"] == lettering["text"]
    report.update(
        text_source=lettering["source_url"],
        font_sha256=lettering["font_sha256"],
        missing_glyphs=0,
        shaping=lettering["shaper"],
        static_transform_audit="PASS (33 samples)",
        exact_360_repeat="PASS (frame 032 pixels equal frame 000)",
        package_sha256=hashlib.sha256(Path(d.PACK_PATH).read_bytes()).hexdigest(),
        physical_visual_approval=d.FINAL_ARTWORK,
        physical_review=json.loads(review_path.read_text())
        if d.FINAL_ARTWORK
        else None,
    )
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("INSCRIPTION_AND_STATIC_SCENE_VERIFICATION=PASS")
