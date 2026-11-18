import bpy, math

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_bloom = True
scene.eevee.bloom_intensity = 0.35
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = 30

# 12 distinct stylized 3D beats (approx 8 seconds each = 96s total at 30fps, rendered fast via step)
# To render fast in GitHub Actions (~2 mins), we render 288 keyframes (3 fps base) and interpolate/hold in FFmpeg
scene.frame_start = 1
scene.frame_end = 288

# Teal & Amber World Lighting
world = bpy.data.worlds.new("TealAmberWorld")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs.default_value = (0.015, 0.045, 0.055, 1)

def make_mat(name, color, metallic=0.2, roughness=0.4, emission=(0,0,0,1), emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Emission Color"].default_value = emission
    b.inputs["Emission Strength"].default_value = emit_str
    return m

mat_teal = make_mat("TealOcean", (0.02, 0.25, 0.30, 1), 0.1, 0.2)
mat_gold = make_mat("AmberGold", (1.0, 0.65, 0.1, 1), 0.9, 0.15, (1.0, 0.5, 0.05, 1), 2.5)
mat_red  = make_mat("CrimsonAlert", (0.95, 0.08, 0.08, 1), 0.3, 0.3, (1.0, 0.05, 0.05, 1), 4.0)
mat_wood = make_mat("ShipWood", (0.18, 0.09, 0.04, 1), 0.0, 0.7)
mat_gem  = make_mat("KohINoor", (0.85, 0.95, 1.0, 1), 0.1, 0.02, (0.6, 0.85, 1.0, 1), 5.0)

# Stylized Ocean Plane
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.2))
ocean = bpy.context.active_object
ocean.data.materials.append(mat_teal)

# Hero Stage Group (Four Ships / Armada / Plassey Blocks / Treasury / Koh-i-Noor)
ships = []
for i in range(4):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.6, depth=1.8, location=((i-1.5)*1.6, i*0.5, 0))
    s = bpy.context.active_object
    s.rotation_euler = (math.radians(90), 0, math.radians(25))
    s.data.materials.append(mat_wood)
    ships.append(s)

# Central Hero Monument (Gold Coin / Crown / Koh-i-Noor Diamond)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.1, location=(0, 0, 1.4))
hero = bpy.context.active_object
hero.data.materials.append(mat_gold)

# Orbiting Crimson War Rings
bpy.ops.mesh.primitive_torus_add(major_radius=2.3, minor_radius=0.08, location=(0, 0, 1.4))
ring = bpy.context.active_object
ring.data.materials.append(mat_red)

# Animate Hero Transformation & Continuous Camera Push/Orbit
bpy.ops.object.camera_add(location=(0, -8.5, 3.2), rotation=(math.radians(74), 0, 0))
cam = bpy.context.active_object
scene.camera = cam

for f in range(1, 289, 24):
    angle = (f / 288.0) * math.pi * 2
    radius = 8.5 - math.sin(angle) * 2.2
    cam.location = (math.sin(angle) * radius, -math.cos(angle) * radius, 2.8 + math.cos(angle) * 1.1)
    direction = hero.location - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert(data_path="location", frame=f)
    cam.keyframe_insert(data_path="rotation_euler", frame=f)

    hero.rotation_euler = (0, 0, angle * 2)
    hero.keyframe_insert(data_path="rotation_euler", frame=f)
    ring.rotation_euler = (angle, angle * 1.5, 0)
    ring.keyframe_insert(data_path="rotation_euler", frame=f)

    # Switch hero shader to diamond caustic look around 1849 (frame 216)
    if f == 217:
        hero.data.materials[0] = mat_gem

# Hard Amber Key Light + Cool Rim Light
bpy.ops.object.light_add(type='AREA', location=(5, -5, 7))
key = bpy.context.active_object
key.data.energy = 1500
key.data.color = (1.0, 0.72, 0.35)

bpy.ops.object.light_add(type='POINT', location=(-5, 5, 4))
rim = bpy.context.active_object
rim.data.energy = 800
rim.data.color = (0.1, 0.8, 0.9)

scene.render.filepath = "//output/frame_"
bpy.ops.render.render(animation=True)
