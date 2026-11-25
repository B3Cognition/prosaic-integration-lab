"""Create the Observatory core in Blender; no service or model calls.

Run: blender --background --factory-startup --python authoring/runtime_core.py
Outputs a packed .blend, a browser-ready .glb, a preview and an asset manifest.
"""
from pathlib import Path
import hashlib
import json
import math

import bpy
import numpy as np
from mathutils import Vector, noise


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (.015, .02, .025)


def surface(a, p, offset=0):
    direction = Vector((math.sin(p) * math.cos(a), math.sin(p) * math.sin(a), math.cos(p)))
    warp = noise.noise_vector(direction * 2.3)
    fold = math.sin(a * 17 + math.sin(p * 7) * 2.3 + warp.x * 3)
    groove = math.exp(-fold * fold * 19)
    cross_fold = math.sin(p * 28 + a * .7 + warp.y * 3)
    r = .745 * (1 + noise.noise(direction * 3.7) * .045 - groove * .07 + cross_fold * .018)
    r += offset
    point = direction * r
    point.x *= 1.02 + math.sin(p * 3) * .035
    point.y *= .97
    point.z *= 1.14
    return point


bpy.ops.mesh.primitive_uv_sphere_add(segments=192, ring_count=128, radius=1)
core = bpy.context.object
core.name = 'Runtime sculpted cortex'
for vertex in core.data.vertices:
    p = math.acos(max(-1, min(1, vertex.co.z)))
    a = math.atan2(vertex.co.y, vertex.co.x)
    vertex.co = surface(a, p)
for polygon in core.data.polygons:
    polygon.use_smooth = True

material = bpy.data.materials.new('Cortex | copper ceramic')
material.use_nodes = True
core.data.materials.append(material)
nodes, links = material.node_tree.nodes, material.node_tree.links
principled = nodes.get('Principled BSDF')
principled.inputs['Metallic'].default_value = .48
principled.inputs['Roughness'].default_value = .4
principled.inputs['Coat Weight'].default_value = .25
principled.inputs['Coat Roughness'].default_value = .32

# Bake real mesh self-occlusion. The final packed base colour retains this detail
# in the browser without requiring Blender procedural nodes or real-time AO.
ao = bpy.data.images.new('Runtime baked occlusion', width=1024, height=1024)
ao.colorspace_settings.name = 'Non-Color'
target = nodes.new('ShaderNodeTexImage')
target.image = ao
nodes.active = target
bpy.context.view_layer.objects.active = core
core.select_set(True)
scene.render.bake.margin = 8
print('PROSAIC_ASSET: baking 1024px ambient occlusion', flush=True)
bpy.ops.object.bake(type='AO')
ao_pixels = np.array(ao.pixels[:], dtype=np.float32).reshape(1024, 1024, 4)

w = h = 1024
u, v = np.meshgrid(np.linspace(0, 1, w, dtype=np.float32), np.linspace(0, 1, h, dtype=np.float32))
rng = np.random.default_rng(71)
grain = rng.random((h, w), dtype=np.float32)
vein = (np.sin(u * 560 + np.sin(v * 70) * 5) + np.sin(v * 820 + u * 13)) * .2
height = vein + grain * .22
dy, dx = np.gradient(height)
normal = np.stack((-dx * 1.1, -dy * 1.1, np.ones_like(dx)), axis=-1)
normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
ao_factor = .42 + .58 * np.clip(ao_pixels[:, :, 0], 0, 1)
variation = .82 + .12 * np.sin(u * 110 + v * 25) + grain * .1
base = np.stack((variation * .72, variation * .255, variation * .13, np.ones_like(u)), axis=-1)
base[:, :, :3] *= ao_factor[:, :, None]
normal_pixels = np.concatenate((normal * .5 + .5, np.ones((h, w, 1), dtype=np.float32)), axis=-1)
rough = .34 + grain * .14 + vein * .08
rough_pixels = np.stack((rough, rough, rough, np.ones_like(u)), axis=-1)


def packed_texture(name, pixels, non_color=False):
    image = bpy.data.images.new(name, width=w, height=h)
    image.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    image.pixels.foreach_set(pixels.astype(np.float32).ravel())
    image.pack()
    node = nodes.new('ShaderNodeTexImage')
    node.image = image
    return node


base_node = packed_texture('Runtime | baked copper colour + occlusion', base)
links.new(base_node.outputs['Color'], principled.inputs['Base Color'])
rough_node = packed_texture('Runtime | ceramic roughness', rough_pixels, True)
links.new(rough_node.outputs['Color'], principled.inputs['Roughness'])
normal_node = packed_texture('Runtime | microfibre tangent normal', normal_pixels, True)
normal_map = nodes.new('ShaderNodeNormalMap')
normal_map.inputs['Strength'].default_value = .6
links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
nodes.remove(target)
bpy.data.images.remove(ao)

traces = bpy.data.materials.new('Conductive traces | warm metal')
traces.use_nodes = True
trace_bsdf = traces.node_tree.nodes.get('Principled BSDF')
trace_bsdf.inputs['Base Color'].default_value = (.7, .37, .1, 1)
trace_bsdf.inputs['Metallic'].default_value = .78
trace_bsdf.inputs['Roughness'].default_value = .3
asset_objects = [core]
for index in range(14):
    curve = bpy.data.curves.new('Conductive surface track', 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = .0032
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    count = 220
    spline.points.add(count - 1)
    for j in range(count):
        t = j / (count - 1)
        a = index / 14 * math.tau + math.sin(t * math.pi * 5 + index) * .13
        p = .14 + t * (math.pi - .28)
        co = surface(a, p, .009)
        spline.points[j].co = (*co, 1)
    obj = bpy.data.objects.new('Conductive filament %02d' % index, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(traces)
    asset_objects.append(obj)

# Convert and join filaments so the browser receives two efficient mesh objects.
bpy.ops.object.select_all(action='DESELECT')
for obj in asset_objects[1:]:
    obj.select_set(True)
bpy.context.view_layer.objects.active = asset_objects[1]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.join()
filaments = bpy.context.object
filaments.name = 'Runtime conductive filaments'
for polygon in filaments.data.polygons:
    polygon.use_smooth = True
asset_objects = [core, filaments]

# Export only the specimen; studio lights and camera belong to the .blend file.
bpy.ops.object.select_all(action='DESELECT')
for obj in asset_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = core
glb = OUT / 'runtime-core.glb'
bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
    export_animations=False, export_tangents=True, export_image_format='AUTO',
    export_copyright='Prosaic Observatory: locally authored procedural asset')


def area(name, location, power, color, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.shape, data.size = power, color, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()


area('Warm key', (2.8, -3, 3), 420, (1, .79, .6), 3)
area('Cyan rim', (-2, 1.5, 1.5), 500, (.35, .8, 1), 2)
area('Soft fill', (-1, -3, -.4), 100, (1, .5, .3), 2)
camera_data = bpy.data.cameras.new('Specimen portrait')
camera = bpy.data.objects.new('Specimen portrait', camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (2.1, -3.2, 1.6)
camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera_data.lens = 60
scene.camera = camera
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.filepath = str(OUT / 'runtime-core-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'runtime-core.blend'))
print('PROSAIC_ASSET: rendering specimen preview', flush=True)
bpy.ops.render.render(write_still=True)
manifest = {
    'blenderVersion': bpy.app.version_string,
    'generator': 'authoring/runtime_core.py',
    'meshes': len(asset_objects),
    'triangles': sum(len(polygon.vertices) - 2 for obj in asset_objects for polygon in obj.data.polygons),
    'textures': '1024px packed colour with Cycles-baked AO, roughness and tangent normal',
    'glbSha256': hashlib.sha256(glb.read_bytes()).hexdigest(),
    'glbBytes': glb.stat().st_size,
}
(OUT / 'runtime-core.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('PROSAIC_ASSET_COMPLETE', json.dumps(manifest), flush=True)
