"""Build and render the CLASSIC v0.4 Digital Prayer Wheel master in Blender.

Run this from Blender's Python Console (the headless macOS executable currently
crashes during Metal device detection before Python starts):
    exec(compile(open('/path/to/render_classic_blender.py').read(),
    '/path/to/render_classic_blender.py', 'exec'))

The model intentionally uses geometric rosette ornament only; it contains no
religious lettering. Frames are rigid Z-axis rotations with a fixed camera,
lighting, world and backdrop. High-resolution masters are rendered to .tmp and
then downsampled by prepare_classic_delivery.py into 240x240 PNG source frames.
"""

import bpy
import math
import os
from mathutils import Vector


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, ".tmp", "classic_v04")
HI_DIR = os.path.join(TMP, "render_480")
MASTER_PATH = os.path.join(ROOT, "assets", "classic", "classic_master_v04.blend")
PROGRESS_PATH = os.path.join(TMP, "render_progress.txt")
FRAME_COUNT = 32
STEP_DEG = 360.0 / FRAME_COUNT
HI_RES = 480

os.makedirs(HI_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MASTER_PATH), exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.materials,
        bpy.data.curves,
        bpy.data.meshes,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for data in list(datablocks):
            if data.users == 0:
                datablocks.remove(data)


def principled(
    name,
    color,
    metallic=0.0,
    roughness=0.35,
    noise_bump=0.0,
    noise_scale=32.0,
    emission=None,
    emission_strength=0.0,
    ao_strength=0.0,
):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    base_color = bsdf.inputs.get("Base Color")
    base_color.default_value = (*color, 1.0)
    bsdf.inputs.get("Metallic").default_value = metallic
    bsdf.inputs.get("Roughness").default_value = roughness
    if ao_strength > 0.0:
        ao = nodes.new("ShaderNodeAmbientOcclusion")
        ao.inputs.get("Distance").default_value = 0.22
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = ao_strength
        mix.inputs[1].default_value = (*color, 1.0)
        links.new(ao.outputs.get("Color"), mix.inputs[2])
        links.new(mix.outputs.get("Color"), base_color)
    if emission is not None:
        emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get(
            "Emission"
        )
        if emission_input:
            emission_input.default_value = (*emission, 1.0)
        strength_input = bsdf.inputs.get("Emission Strength")
        if strength_input:
            strength_input.default_value = emission_strength
    if noise_bump > 0:
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 3.0
        tex.inputs["Roughness"].default_value = 0.72
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = noise_bump
        bump.inputs["Distance"].default_value = 0.018
        links.new(tex.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def emission_material(name, color, strength=1.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    output = nodes.new("ShaderNodeOutputMaterial")
    emission.inputs.get("Color").default_value = (*color, 1.0)
    emission.inputs.get("Strength").default_value = strength
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def bevel(obj, width=0.025, segments=3):
    mod = obj.modifiers.new("Soft machined edges", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.profile = 0.5
    norm = obj.modifiers.new("Corner-weighted normals", "WEIGHTED_NORMAL")
    norm.keep_sharp = True
    return obj


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def uv_sphere(name, location, scale, mat, parent=None, segments=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    smooth(obj)
    assign(obj, mat)
    if parent:
        obj.parent = parent
    return obj


def torus(name, major, minor, z, mat, parent, major_segments=96, minor_segments=12):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major,
        minor_radius=minor,
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=(0, 0, z),
    )
    obj = bpy.context.object
    obj.name = name
    smooth(obj)
    assign(obj, mat)
    obj.parent = parent
    return obj


def cylinder(name, radius, depth, z, mat, parent, vertices=96, bevel_width=0.02):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=(0, 0, z)
    )
    obj = bpy.context.object
    obj.name = name
    smooth(obj)
    assign(obj, mat)
    if bevel_width:
        bevel(obj, min(bevel_width, depth * 0.2), 3)
    obj.parent = parent
    return obj


def lathe(name, profile, mat, parent, segments=160):
    verts = []
    faces = []
    for radius, z in profile:
        for j in range(segments):
            phi = math.tau * j / segments
            verts.append((radius * math.sin(phi), -radius * math.cos(phi), z))
    for ring in range(len(profile) - 1):
        for j in range(segments):
            a = ring * segments + j
            b = ring * segments + (j + 1) % segments
            c = (ring + 1) * segments + (j + 1) % segments
            d = (ring + 1) * segments + j
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + " surface")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    smooth(obj)
    obj.parent = parent
    return obj


def surface_point(phi, z, radius):
    return (radius * math.sin(phi), -radius * math.cos(phi), z)


def add_lines(name, lines, radius, mat, parent, depth=0.008, resolution=2):
    curve = bpy.data.curves.new(name + " geometry", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = depth
    curve.bevel_resolution = resolution
    for points in lines:
        if len(points) < 2:
            continue
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for point, (phi, z, local_radius) in zip(spline.points, points):
            point.co = (*surface_point(phi, z, local_radius or radius), 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    obj.parent = parent
    return obj


def make_backdrop(material):
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 2.4, 0))
    plane = bpy.context.object
    plane.name = "Static indigo-black cyclorama"
    plane.rotation_euler[0] = math.radians(90)
    assign(plane, material)
    return plane


def add_background_rings(mat):
    # One restrained static ring provides separation from the black field.
    lines = []
    radius = 1.58
    pts = []
    for i in range(193):
        angle = math.tau * i / 192
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        # The backdrop plane is XZ with y=2.4.
        pts.append((x, 2.4, z))
    lines.append(pts)
    curve = bpy.data.curves.new("Static halo geometry", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.004
    curve.bevel_resolution = 2
    for points in lines:
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for item, co in zip(spline.points, points):
            item.co = (*co, 1.0)
    obj = bpy.data.objects.new("Static hairline halo", curve)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    # Tick marks are included as short fixed line splines on the same backdrop.
    ticks = []
    for i in range(16):
        a = math.tau * i / 16
        r0 = 1.565
        r1 = 1.588 if i % 4 == 0 else 1.578
        ticks.append(
            [
                (r0 * math.cos(a), 2.4, r0 * math.sin(a)),
                (r1 * math.cos(a), 2.4, r1 * math.sin(a)),
            ]
        )
    tick_curve = bpy.data.curves.new("Halo ticks geometry", type="CURVE")
    tick_curve.dimensions = "3D"
    tick_curve.bevel_depth = 0.0035
    tick_curve.bevel_resolution = 2
    for points in ticks:
        spline = tick_curve.splines.new("POLY")
        spline.points.add(1)
        for item, co in zip(spline.points, points):
            item.co = (*co, 1.0)
    tick_obj = bpy.data.objects.new("Static halo ticks", tick_curve)
    bpy.context.collection.objects.link(tick_obj)
    assign(tick_obj, mat)


def make_panel(center_phi, panel_mat, parent, relief_lines, gems):
    # Curved plaque follows the drum radius and rotates as part of the rigid root.
    base_r = 0.919
    cols = 8
    rows = 12
    verts = []
    faces = []
    for zi in range(rows + 1):
        z = -0.49 + 0.98 * zi / rows
        for ui in range(cols + 1):
            u = -0.257 + 0.514 * ui / cols
            verts.append(surface_point(center_phi + u, z, base_r))
    for zi in range(rows):
        for ui in range(cols):
            a = zi * (cols + 1) + ui
            b = a + 1
            d = (zi + 1) * (cols + 1) + ui
            c = d + 1
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new("Curved repoussé plaque mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Curved repoussé plaque", mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, panel_mat)
    solid = obj.modifiers.new("Raised plaque backing", "SOLIDIFY")
    solid.thickness = 0.025
    solid.offset = -0.3
    edge = obj.modifiers.new("Rounded plaque edge", "BEVEL")
    edge.width = 0.018
    edge.segments = 3
    normal = obj.modifiers.new("Plaque normals", "WEIGHTED_NORMAL")
    obj.parent = parent

    r = 0.952
    # Paired perimeter rails with clipped corners.
    outline = [
        (-0.20, -0.43),
        (0.20, -0.43),
        (0.237, -0.38),
        (0.237, 0.38),
        (0.20, 0.43),
        (-0.20, 0.43),
        (-0.237, 0.38),
        (-0.237, -0.38),
        (-0.20, -0.43),
    ]
    relief_lines.append([(center_phi + u, z, r) for u, z in outline])
    inner = [
        (-0.184, -0.37),
        (0.184, -0.37),
        (0.195, -0.34),
        (0.195, 0.34),
        (0.184, 0.37),
        (-0.184, 0.37),
        (-0.195, 0.34),
        (-0.195, -0.34),
        (-0.184, -0.37),
    ]
    relief_lines.append([(center_phi + u, z, r + 0.004) for u, z in inner])

    # A restrained six-petal repoussé flower: geometric, not a letterform.
    cx, cz = 0.0, 0.0
    for petal in range(6):
        a = math.tau * petal / 6
        points = []
        for k in range(33):
            t = math.tau * k / 32
            x = 0.092 * math.cos(t)
            y = 0.168 * math.sin(t)
            u = (x * math.cos(a) - y * math.sin(a)) / 0.93
            z = cx + x * math.sin(a) + y * math.cos(a) + cz
            points.append((center_phi + u, z, r + 0.014))
        relief_lines.append(points)

    # A single fine hexagonal cartouche surrounds the flower.
    hexagon = [
        (
            center_phi + 0.145 * math.cos(math.tau * q / 6) / 0.93,
            0.205 * math.sin(math.tau * q / 6),
            r + 0.018,
        )
        for q in range(7)
    ]
    relief_lines.append(hexagon)

    # Tiny raised bosses at four panel corners and a warm cabochon at the center.
    for du in (-0.165, 0.165):
        for z in (-0.33, 0.33):
            gems.append((center_phi + du, z, 0.017, "stud"))
    gems.append((center_phi, 0.0, 0.034, "cabochon"))


def add_orbiting_gems(entries, mat, parent, stud_mat):
    for phi, z, radius, kind in entries:
        x, y, zz = surface_point(phi, z, 0.969 if kind == "cabochon" else 0.959)
        material = mat if kind == "cabochon" else stud_mat
        scale = (radius, radius, radius * 1.15)
        uv_sphere(
            "Amber cabochon" if kind == "cabochon" else "Repoussé stud",
            (x, y, zz),
            scale,
            material,
            parent,
            segments=16,
            rings=10,
        )


def add_finial(parent, gold, dark, amber):
    # Matching upper and lower terminal ornaments composed around the shared Z axis.
    for sign in (-1, 1):
        z0 = sign * 0.91
        lathe(
            "Finial neck",
            [
                (0.10, z0),
                (0.17, sign * 0.97),
                (0.20, sign * 1.04),
                (0.15, sign * 1.10),
                (0.095, sign * 1.16),
                (0.08, sign * 1.20),
            ],
            gold,
            parent,
            segments=96,
        )
        for z, radius, minor in (
            (sign * 0.97, 0.19, 0.022),
            (sign * 1.04, 0.20, 0.028),
            (sign * 1.115, 0.14, 0.020),
            (sign * 1.20, 0.085, 0.016),
        ):
            torus("Finial turned bead", radius, minor, z, gold, parent, 72, 10)
        # Capped lotus bud/seed silhouette. Geometry is mirrored for the lower end.
        prof = [
            (0.075, sign * 1.18),
            (0.115, sign * 1.24),
            (0.135, sign * 1.31),
            (0.105, sign * 1.39),
            (0.062, sign * 1.47),
            (0.0, sign * 1.55),
        ]
        lathe("Lotus-seed finial", prof, gold, parent, segments=96)
        uv_sphere(
            "Finial amber eye",
            (0, -0.12, sign * 1.30),
            (0.045, 0.032, 0.075),
            amber,
            parent,
            segments=20,
            rings=12,
        )
        # Petal ribs run up the bud in eight evenly spaced meridians.
        meridians = []
        for i in range(8):
            phi = math.tau * i / 8
            meridians.append(
                [
                    (phi, sign * z, r)
                    for r, z in (
                        (0.111, 1.23),
                        (0.129, 1.30),
                        (0.102, 1.38),
                        (0.061, 1.46),
                        (0.006, 1.535),
                    )
                ]
            )
        add_lines("Finial fluting", meridians, 0.14, dark, parent, 0.006, 2)


def point_at(obj, point):
    obj.rotation_euler = (
        (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()
    )


def add_area(name, location, target, color, energy, size, shape="DISK", size_y=None):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = color
    data.shape = shape
    data.size = size
    if shape == "RECTANGLE" and size_y:
        data.size_y = size_y
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


def build_scene(scene_transform=None, frame_indices=None):
    clear_scene()
    scene = bpy.context.scene

    gold = principled(
        "01 | antique brushed brass",
        (0.39, 0.27, 0.13),
        metallic=0.88,
        roughness=0.37,
        noise_bump=0.045,
        noise_scale=128,
        ao_strength=0.09,
    )
    pale_gold = principled(
        "02 | softly polished old gold",
        (0.62, 0.45, 0.25),
        metallic=0.88,
        roughness=0.29,
        noise_bump=0.015,
        noise_scale=175,
        ao_strength=0.07,
    )
    dark_gold = principled(
        "03 | recessed bronze patina",
        (0.12, 0.075, 0.038),
        metallic=0.76,
        roughness=0.42,
        noise_bump=0.07,
        noise_scale=82,
        ao_strength=0.12,
    )
    plaque_mat = principled(
        "04 | softly chased bronze",
        (0.18, 0.115, 0.060),
        metallic=0.84,
        roughness=0.39,
        noise_bump=0.045,
        noise_scale=112,
        ao_strength=0.12,
    )
    amber = principled(
        "05 | muted amber inlay",
        (0.25, 0.13, 0.06),
        metallic=0.38,
        roughness=0.32,
        emission=(0.85, 0.25, 0.055),
        emission_strength=0.09,
    )
    # Emission keeps the background fixed and near-black instead of being lifted
    # by the photographic softboxes aimed at the brass object.
    backdrop_mat = emission_material(
        "06 | near-black indigo void", (0.0015, 0.0025, 0.009), 1.0
    )
    halo_mat = principled(
        "07 | quiet static halo",
        (0.07, 0.045, 0.024),
        metallic=0.52,
        roughness=0.56,
        emission=(0.08, 0.045, 0.018),
        emission_strength=0.055,
    )

    world = (
        bpy.data.worlds.new("Indigo-black studio")
        if bpy.data.worlds.get("Indigo-black studio") is None
        else bpy.data.worlds["Indigo-black studio"]
    )
    scene.world = world
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    world_links = world.node_tree.links
    world_nodes.clear()
    bg = world_nodes.new("ShaderNodeBackground")
    world_out = world_nodes.new("ShaderNodeOutputWorld")
    world_links.new(bg.outputs["Background"], world_out.inputs["Surface"])
    bg.inputs.get("Color").default_value = (0.006, 0.009, 0.023, 1)
    bg.inputs.get("Strength").default_value = 0.20
    make_backdrop(backdrop_mat)
    add_background_rings(halo_mat)

    root = bpy.data.objects.new("WheelRoot | rigid Z-axis rotation", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "CIRCLE"
    root.empty_display_size = 0.5

    # Turned main drum with subtle shoulders and a broad cylindrical body.
    drum_profile = [
        (0.70, -0.86),
        (0.82, -0.84),
        (0.88, -0.79),
        (0.91, -0.72),
        (0.92, -0.64),
        (0.92, 0.64),
        (0.91, 0.72),
        (0.88, 0.79),
        (0.82, 0.84),
        (0.70, 0.86),
    ]
    lathe("Main turned prayer-wheel drum", drum_profile, gold, root, segments=192)
    cylinder("Dark recessed under-drum core", 0.79, 1.52, 0, dark_gold, root, 128, 0)

    # Fine turned bands and relief rings create a machined, layered silhouette.
    for z, radius, minor, mat in [
        (-0.84, 0.84, 0.035, pale_gold),
        (-0.78, 0.90, 0.020, dark_gold),
        (-0.72, 0.922, 0.028, pale_gold),
        (-0.66, 0.926, 0.010, dark_gold),
        (-0.56, 0.925, 0.009, pale_gold),
        (0.56, 0.925, 0.009, pale_gold),
        (0.66, 0.926, 0.010, dark_gold),
        (0.72, 0.922, 0.028, pale_gold),
        (0.78, 0.90, 0.020, dark_gold),
        (0.84, 0.84, 0.035, pale_gold),
    ]:
        torus("Turned concentric bead", radius, minor, z, mat, root)

    # Six broad plaques and controlled raised geometric engraving.
    relief = []
    gem_entries = []
    for i in range(6):
        phi = math.tau * i / 6
        make_panel(phi, plaque_mat, root, relief, gem_entries)
    add_lines("Continuous repoussé engraving", relief, 0.95, pale_gold, root, 0.0055, 2)
    add_orbiting_gems(gem_entries, amber, root, pale_gold)

    # Collar, spindle and matching top/bottom finials.
    cylinder("Lower collar", 0.54, 0.15, -0.94, dark_gold, root, 112, 0.025)
    torus("Lower collar lip", 0.53, 0.034, -0.96, pale_gold, root)
    cylinder("Upper collar", 0.54, 0.15, 0.94, dark_gold, root, 112, 0.025)
    torus("Upper collar lip", 0.53, 0.034, 0.96, pale_gold, root)
    cylinder("Central axle", 0.095, 2.38, 0, dark_gold, root, 64, 0.015)
    add_finial(root, gold, dark_gold, amber)

    # Small bolt heads on the two end bands, aligned to the same rotational root.
    for sign in (-1, 1):
        for i in range(16):
            phi = math.tau * i / 16
            x, y, z = surface_point(phi, sign * 0.73, 0.951)
            uv_sphere(
                "Rim pin",
                (x, y, z),
                (0.019, 0.019, 0.019),
                pale_gold,
                root,
                segments=12,
                rings=8,
            )

    # Fixed portrait orthographic camera; all animated geometry is parented to WheelRoot.
    camera_data = bpy.data.cameras.new("Portrait orthographic product camera")
    camera = bpy.data.objects.new("Camera | fixed orthographic", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0.0, -8.2, 0.10)
    point_at(camera, (0.0, 0.0, 0.0))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 3.55
    camera_data.lens = 50
    scene.camera = camera

    # Broad, lower-energy softboxes keep the reflective metal warm and calm.
    add_area(
        "Warm key softbox",
        (-3.1, -4.2, 3.7),
        (0, 0, 0.15),
        (1.0, 0.79, 0.55),
        340,
        4.0,
        "RECTANGLE",
        2.8,
    )
    add_area(
        "Pale gold edge strip",
        (3.5, -2.8, 1.0),
        (0, 0, 0),
        (1.0, 0.88, 0.70),
        190,
        3.0,
        "RECTANGLE",
        1.2,
    )
    add_area(
        "Cool indigo rim",
        (-2.5, 0.6, 1.8),
        (0, 0, 0),
        (0.38, 0.48, 0.72),
        150,
        2.6,
        "DISK",
    )
    add_area(
        "Low warm bounce",
        (0.3, -3.0, -2.5),
        (0, 0, -0.2),
        (1.0, 0.62, 0.36),
        55,
        2.4,
        "DISK",
    )

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 40
    scene.cycles.use_denoising = True
    scene.render.resolution_x = HI_RES
    scene.render.resolution_y = HI_RES
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.render.filepath = "//"
    scene.render.image_settings.compression = 20
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium Low Contrast"
    scene.render.image_settings.color_mode = "RGB"
    scene.camera.data.dof.use_dof = False
    scene.frame_start = 0
    scene.frame_end = FRAME_COUNT - 1
    scene.render.fps = 24

    # Authored frame index i means i*11.25 degrees, clockwise on the rendered face.
    for index in range(FRAME_COUNT):
        angle = math.radians(index * STEP_DEG)
        root.rotation_euler[2] = -angle
        root.keyframe_insert(data_path="rotation_euler", frame=index, index=2)
    scene.frame_set(0)

    scene["Artwork"] = "Digital Prayer Wheel | CLASSIC v0.4"
    scene["Frame contract"] = "32 frames; i * 11.25 degrees; rigid common-Z rotation"
    scene["Camera contract"] = (
        "Fixed orthographic; 480px master rendered then Lanczos to 240px"
    )
    scene["Text policy"] = "No religious lettering is rendered; ornament is geometric"
    scene["Render policy"] = (
        "Cycles CPU / 40 samples / denoised / AgX medium-high contrast"
    )

    if scene_transform is not None:
        scene_transform(scene, root, pale_gold, plaque_mat)
    bpy.ops.wm.save_as_mainfile(filepath=MASTER_PATH)
    print("DPW_MASTER_SAVED=" + MASTER_PATH, flush=True)
    indices = list(range(FRAME_COUNT) if frame_indices is None else frame_indices)
    print("DPW_RENDER_BEGIN frames=%d size=480 samples=40" % len(indices), flush=True)
    with open(PROGRESS_PATH, "w", encoding="utf-8") as progress:
        progress.write("rendering 0/32\n")
    for rendered_number, index in enumerate(indices, 1):
        scene.frame_set(index)
        # Do not rely on f-curve evaluation around the loop endpoint; assign the exact phase.
        root.rotation_euler[2] = -math.radians(index * STEP_DEG)
        scene.render.filepath = os.path.join(HI_DIR, "frame_%03d.png" % index)
        bpy.ops.render.render(write_still=True)
        with open(PROGRESS_PATH, "w", encoding="utf-8") as progress:
            progress.write(
                "rendered %d/%d angle=%.2f\n"
                % (rendered_number, len(indices), index * STEP_DEG)
            )
        print(
            "DPW_RENDER_FRAME=%02d angle=%.2f path=%s"
            % (index, index * STEP_DEG, scene.render.filepath),
            flush=True,
        )
    with open(PROGRESS_PATH, "w", encoding="utf-8") as progress:
        progress.write("complete %d/%d\n" % (len(indices), len(indices)))
    print("DPW_RENDER_COMPLETE", flush=True)


if __name__ == "__main__":
    build_scene()
