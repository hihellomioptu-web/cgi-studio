import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_bloom = True
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.frame_start, scene.frame_end = 1, 72

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.2, location=(0, 0, 0))
core = bpy.context.active_object
mat = bpy.data.materials.new("Glow")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 0.7, 1.0, 1)
bsdf.inputs["Emission Color"].default_value = (0.0, 0.8, 1.0, 1)
bsdf.inputs["Emission Strength"].default_value = 5.0
core.data.materials.append(mat)

bpy.ops.object.camera_add(location=(5, -5, 3), rotation=(math.radians(65), 0, math.radians(45)))
scene.camera = bpy.context.active_object
bpy.ops.object.light_add(type='SUN', location=(4, -4, 6))
scene.render.filepath = "//output/frame_"
bpy.ops.render.render(animation=True)
