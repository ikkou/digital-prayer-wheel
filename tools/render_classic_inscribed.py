"""CLASSIC v0.5: source-verified Tibetan mantra as curved, bevelled metal relief.

Run with Blender Python. Requires prepare_mantra_lettering.py first. The v0.4
scene builder supplies fixed camera/lighting/finials; this version replaces its
rosettes with the shaped inscription. Default renders all 32 frames. For a
single-frame quality check, set DPW_FRAME_INDICES=[0] in the execution namespace.
"""

import bpy
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "classic_base", os.path.join(ROOT, "tools/render_classic_blender.py")
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.TMP = os.path.join(ROOT, ".tmp/classic_v05")
base.HI_DIR = os.path.join(base.TMP, "render_480")
base.MASTER_PATH = os.path.join(ROOT, "assets/classic_v05/classic_master_v05.blend")
base.PROGRESS_PATH = os.path.join(base.TMP, "render_progress.txt")
os.makedirs(base.HI_DIR, exist_ok=True)
os.makedirs(os.path.dirname(base.MASTER_PATH), exist_ok=True)
# No geometric rosette plaques are built underneath the lettering.
base.make_panel = lambda *args, **kwargs: None


def inscription(scene, root, gold, unused):
    data = json.load(
        open(
            os.path.join(ROOT, "assets/lettering/mantra_outlines.json"),
            encoding="utf-8",
        )
    )
    band = base.principled(
        "v05 | satin recessed bronze inscription ground",
        (0.12, 0.074, 0.035),
        metallic=0.82,
        roughness=0.46,
        noise_bump=0.025,
        noise_scale=120,
        ao_strength=0.08,
    )
    letter = base.principled(
        "v05 | warm gold bevelled inscription",
        (0.58, 0.37, 0.13),
        metallic=0.86,
        roughness=0.38,
        noise_bump=0.009,
        noise_scale=180,
        ao_strength=0.12,
    )
    base.cylinder("Inscription bronze field", 0.929, 1.04, 0, band, root, 192, 0.008)
    xmin, ymin, xmax, ymax = data["bounds"]
    scale = 1.00 / (ymax - ymin)
    radius = 0.943
    text = data["text"]
    # Additional spacing follows existing tsheg separators only; marks and
    # conjunct glyphs keep their exact HarfBuzz offsets within each cluster.
    gap = (math.tau * radius - 0.48 - data["advance"] * scale) / text.count("་")
    first = [
        p for g in data["glyphs"] if g["cluster"] == 0 for c in g["contours"] for p in c
    ]
    center_om = (min(p[0] for p in first) + max(p[0] for p in first)) * 0.5 * scale
    layout = []
    for i, g in enumerate(data["glyphs"]):
        curve = bpy.data.curves.new("Shaped Tibetan glyph " + g["glyph"], "CURVE")
        curve.dimensions = "2D"
        curve.fill_mode = "BOTH"
        curve.resolution_u = 1
        curve.extrude = 0.004
        curve.bevel_depth = 0.0025
        curve.bevel_resolution = 2
        shift = gap * text[: g["cluster"]].count("་") - center_om
        for contour in g["contours"]:
            spline = curve.splines.new("POLY")
            spline.points.add(len(contour) - 1)
            for point, (x, y) in zip(spline.points, contour):
                point.co = (x * scale + shift, (y - (ymin + ymax) * 0.5) * scale, 0, 1)
            spline.use_cyclic_u = True
        obj = bpy.data.objects.new("MANTRA %02d | %s" % (i, g["glyph"]), curve)
        bpy.context.collection.objects.link(obj)
        base.assign(obj, letter)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        obj = bpy.context.object
        # Convert local plane X (reading direction), Y (up), Z (relief depth)
        # to shared cylindrical coordinates without mirroring the inscription.
        for v in obj.data.vertices:
            x, y, depth = v.co
            phi = x / radius
            r = radius + depth
            v.co = (r * math.sin(phi), -r * math.cos(phi), y)
        obj.parent = root
        obj["Source Unicode cluster"] = g["cluster"]
        obj["Shaped glyph"] = g["glyph"]
        obj["Source text"] = text
        obj["Font SHA256"] = data["font_sha256"]
        layout.append(
            dict(
                object=obj.name,
                glyph=g["glyph"],
                cluster=g["cluster"],
                extra_tracking=shift,
                vertices=len(obj.data.vertices),
            )
        )
    # Paired guilloche ribbons sit outside the text's diacritics.
    ribbons = []
    for sign in (-1, 1):
        for offset in (0, math.pi):
            ribbons.append(
                [
                    (phi, sign * (0.59 + 0.025 * math.sin(24 * phi + offset)), 0.945)
                    for phi in [math.tau * j / 768 for j in range(769)]
                ]
            )
    base.add_lines(
        "v05 | braided guilloche borders", ribbons, 0.945, gold, root, 0.004, 2
    )
    scene["Artwork"] = "Digital Prayer Wheel | CLASSIC v0.5 | Tibetan inscription"
    scene["Text policy"] = text
    scene["Text source"] = data["source_url"]
    scene["Text font"] = data["font"]
    scene["Text shaping"] = data["shaper"]
    scene["Reading order"] = (
        "increasing cylinder azimuth; rigid clockwise frame advance reveals successive text"
    )
    record = dict(
        text=text,
        source=data["source_url"],
        font_sha256=data["font_sha256"],
        radius=radius,
        uniform_scale=scale,
        tracking_after_tsheg=gap,
        objects=layout,
    )
    with open(
        os.path.join(ROOT, "assets/classic_v05/inscription_layout.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


base.build_scene(
    scene_transform=inscription, frame_indices=globals().get("DPW_FRAME_INDICES")
)
