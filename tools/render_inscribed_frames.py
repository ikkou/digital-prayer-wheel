"""Render an existing v0.5 master, with rigid-geometry and static-scene audits."""

import bpy, hashlib, json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, ".tmp/classic_v05/render_480")
PROGRESS = os.path.join(ROOT, ".tmp/classic_v05/render_progress.txt")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(
    filepath=os.path.join(ROOT, "assets/classic_v05/classic_master_v05.blend")
)
scene = bpy.context.scene
root = next(o for o in scene.objects if o.name.startswith("WheelRoot"))


def static_state():
    return {
        o.name: {
            "parent": o.parent.name if o.parent else None,
            "local": [[round(v, 8) for v in row] for row in o.matrix_basis],
            "energy": o.data.energy if o.type == "LIGHT" else None,
            "vertices": len(o.data.vertices) if o.type == "MESH" else None,
        }
        for o in scene.objects
        if o != root
    }


reference = static_state()
audit = []
for i in list(range(32)) + [32]:
    phase = i % 32
    scene.frame_set(phase)
    root.rotation_euler[2] = -math.radians(phase * 11.25)
    bpy.context.view_layer.update()
    if static_state() != reference:
        raise RuntimeError("Non-root transform changed at frame " + str(i))
    scene.render.filepath = os.path.join(OUT, "frame_%03d.png" % i)
    bpy.ops.render.render(write_still=True)
    audit.append(
        {
            "frame": i,
            "phase_index": phase,
            "angle_deg": phase * 11.25,
            "root_z": float(root.rotation_euler.z),
            "static_scene_unchanged": True,
        }
    )
    with open(PROGRESS, "w") as f:
        f.write("rendered %d/33; angle=%.2f\n" % (i + 1, phase * 11.25))
    print("DPW_INSCRIBED_FRAME", i, flush=True)
with open(os.path.join(ROOT, "assets/classic_v05/render_audit.json"), "w") as f:
    json.dump(
        {
            "frames": audit,
            "static_scene": reference,
            "camera": scene.camera.name,
            "text": scene["Text policy"],
            "engine": scene.render.engine,
            "samples": scene.cycles.samples,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )
with open(PROGRESS, "w") as f:
    f.write("complete 33/33 (including loop repeat)\n")
