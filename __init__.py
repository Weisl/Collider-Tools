bl_info = {
    "name": "Collider Tools",
    "description": "",
    "author": "Matthias Patscheider",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "wiki_url": "https://weisl.github.io/collider-tools_overview/",
    "tracker_url": "https://github.com/Weisl/Collider-Tools/issues",
    "category": "Object"}

# support reloading sub-modules
if "bpy" in locals():
    import importlib

    importlib.reload(Ui)
    importlib.reload(Operators)
    importlib.reload(Auto_Convex)
    importlib.reload(Preferences)

else:
    from . import Ui
    from . import Operators
    from . import Auto_Convex
    from . import Preferences

import bpy

def scene_my_collision_material_poll(self, material):
    ''' Returns material only if the name contains the physics material identifier specified in the Preferences '''
    if bpy.context.scene.PhysicsIdentifier in material.name:
        return material.name


def register():
    # register variables saved in the blender scene
    scene = bpy.types.Scene

    scene.CollisionMaterials = bpy.props.PointerProperty(
        type=bpy.types.Material,
        poll=scene_my_collision_material_poll,
        name='Physics Material',
        description='Physical Materials are used in game enginges to define different responses of a physical object when interacting with other elements of the game world. They can be used to trigger different audio, VFX or gameplay events depending on the material.'
    )

    scene.PhysicsIdentifier = bpy.props.StringProperty(
        default="",
        description="Filter physics materials out based on their naming.",
        name='Physics Material Filter',
    )

    scene.DefaultMeshMaterial = bpy.props.PointerProperty(
        type=bpy.types.Material,
        name = 'Default Mesh Material',
        description='The default mesh material will be assigned to any mesh that is converted from a collider to a mesh object'
    )

    # call the register function of the sub modules
    Ui.register()
    Operators.register()
    Auto_Convex.register()

    # keymap and Preferences should be last
    Preferences.register()


def unregister():
    scene = bpy.types.Scene

    # delete variables saved in the scenes file
    del scene.CollisionMaterials
    del scene.PhysicsIdentifier
    del scene.DefaultMeshMaterial

    # call unregister function of the sub-modules
    Preferences.unregister()
    Auto_Convex.unregister()
    Operators.unregister()
    Ui.unregister()
