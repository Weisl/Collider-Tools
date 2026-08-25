import bpy

DECIMATE_NAME = 'Collider_decimate'

# EMPTY objects only gained modifier (Geometry Nodes) support in Blender 5.2
# (https://projects.blender.org/blender/blender/pulls/157804, "Object: Add
# Geometry Nodes support for Empty object type") - confirmed both from
# Blender's own 5.2 release notes and by testing directly: obj.modifiers.new()
# on an EMPTY silently returns None on 4.2/5.0/5.1, and only starts working on
# 5.2. Before that, an EMPTY can never carry collider-worthy geometry, so it's
# left out of VALID_OBJECT_TYPES entirely on older Blender rather than relying
# on the 0-vertex fallback elsewhere to make it a no-op.
if bpy.app.version >= (5, 2, 0):
    VALID_OBJECT_TYPES = frozenset({'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'EMPTY'})
else:
    VALID_OBJECT_TYPES = frozenset({'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'})

PRESETFOLDER = "simple_collider"
DEFAULT_PRESET = 'UE-default.py'