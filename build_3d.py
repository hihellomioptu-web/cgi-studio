import bpy, math, os

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.frame_start = 1
scene.frame_end = 12
scene.render.image_settings.file_format = 'PNG'

# Enable real-time shadows
if hasattr(scene.eevee, "use_shadows"):
    scene.eevee.use_shadows = True

# World & Volumetric Atmosphere
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs.default_value = (0.01, 0.03, 0.04, 1)

def mat(name, col, met=0.1, rough=0.4, emit=(0,0,0,1), estr=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = estr
    return m

m_ocean = mat("Ocean", (0.01, 0.18, 0.24, 1), 0.1, 0.25)
m_hull  = mat("Hull", (0.22, 0.10, 0.04, 1), 0.0, 0.65)
m_sail  = mat("Sail", (0.92, 0.85, 0.72, 1), 0.0, 0.8)
m_cross = mat("Cross", (0.85, 0.05, 0.05, 1), 0.1, 0.4, (0.8, 0.02, 0.02, 1), 1.5)
m_gold  = mat("Gold", (1.0, 0.7, 0.1, 1), 0.95, 0.12, (1.0, 0.55, 0.05, 1), 2.5)

# Ocean Plane (receives shadows)
bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(m_ocean)

# Build 3D Stylized Carrack Ship + Stylized Character Figure on Deck
def build_ship(x, y, scale=1.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.35*scale))
    hull = bpy.context.active_object
    hull.scale = (0.7*scale, 2.2*scale, 0.45*scale)
    hull.data.materials.append(m_hull)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.05*scale, depth=2.6*scale, location=(x, y, 1.5*scale))
    mast = bpy.context.active_object
    mast.data.materials.append(m_hull)

    bpy.ops.mesh.primitive_plane_add(size=1.4*scale, location=(x, y+0.12*scale, 1.7*scale))
    sail = bpy.context.active_object
    sail.rotation_euler = (math.radians(90), 0, 0)
    sail.data.materials.append(m_sail)

    # Stylized 3D Character Figure on Deck (Body + Head)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12*scale, depth=0.45*scale, location=(x, y-0.5*scale, 0.85*scale))
    body = bpy.context.active_object
    body.data.materials.append(m_cross)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11*scale, location=(x, y-0.5*scale, 1.2*scale))
    head = bpy.context.active_object
    head.data.materials.append(m_gold)

build_ship(0, 0, 1.2)
build_ship(-2.4, 2.2, 0.85)
build_ship(2.5, 2.5, 0.85)

# Hard Key Sun Light with Shadows + Cool Rim Light
bpy.ops.object.light_add(type='SUN', location=(6, -6, 10))
sun = bpy.context.active_object
sun.data.energy = 4.5
sun.data.color = (1.0, 0.78, 0.45)
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(35))

bpy.ops.object.light_add(type='POINT', location=(-5, 6, 4))
rim = bpy.context.active_object
rim.data.energy = 1200
rim.data.color = (0.1, 0.85, 0.95)

# Orbiting Camera
bpy.ops.object.camera_add(location=(0, -7.5, 3.0))
cam = bpy.context.active_object
scene.camera = cam

for f in range(1, 13):
    ang = (f / 12.0) * math.pi * 0.65 - 0.5
    cam.location = (math.sin(ang)*7.2, -math.cos(ang)*7.2, 2.6 + (f*0.08))
    direction = bpy.mathutils.Vector((0, 0.4, 1.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert(data_path="location", frame=f)
    cam.keyframe_insert(data_path="rotation_euler", frame=f)

os.makedirs("renders_3d", exist_ok=True)
scene.render.filepath = os.path.abspath("renders_3d/f_")
bpy.ops.render.render(animation=True)
