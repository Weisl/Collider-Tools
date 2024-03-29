import bpy
from bpy.app.handlers import persistent

from . import naming_preset
from . import preferences
from . import keymap

from .preferences import update_panel_category
from ..pyshics_materials.material_functions import set_default_active_mat
from ..groups.user_groups import set_default_group_values

classes = (
    naming_preset.COLLISION_preset,
    preferences.BUTTON_OT_change_key,
    preferences.CollisionAddonPrefs,
    keymap.REMOVE_OT_hotkey,
)

@persistent
def _load_handler(dummy):
    set_default_active_mat()
    set_default_group_values()



def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    update_panel_category(None, bpy.context)

    # Pointer Properties have to be initialized after classes

    keymap.add_keymap()
    bpy.app.handlers.load_post.append(_load_handler)

def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    keymap.remove_keymap()
    bpy.app.handlers.load_post.remove(_load_handler)
