import bpy

from . import naming_preset
from . import preferences
from . import properties
from . import keymap
from .properties import ColliderTools_Properties
from .preferences import update_panel_category


classes = (
    properties.ColliderTools_Properties,
    naming_preset.COLLISION_preset,
    preferences.BUTTON_OT_change_key,
    preferences.CollisionAddonPrefs,
    keymap.REMOVE_OT_hotkey,
)


@persistent
def _load_handler(dummy):
    prefs = bpy.context.preferences.addons[__package__.split('.')[0]].preferences
    default_mat_name = prefs.physics_material_name
  
    mat = bpy.data.materials.get(default_mat_name, material_functions.create_default_material())

    bpy.context.scene.collider_tools.material_list_index = list(bpy.data.materials).index(mat)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    update_panel_category(None, bpy.context)

    # Pointer Properties have to be initialized after classes
    scene = bpy.types.Scene
    scene.collider_tools = bpy.props.PointerProperty(
        type=ColliderTools_Properties)

    keymap.add_keymap()

    bpy.app.handlers.load_post.append(_load_handler)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    scene = bpy.types.Scene
    del scene.collider_tools

    keymap.remove_keymap()

    bpy.app.handlers.load_post.remove(_load_handler)