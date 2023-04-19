import bpy
import os
import shutil
from pathlib import Path

from . import properties_panels
from . import popup
from .properties_panels import collider_presets_folder

classes = (
    properties_panels.EXPLORER_OT_open_directory,
    properties_panels.PREFERENCES_OT_open_addon,
    properties_panels.OBJECT_MT_collision_presets,
    properties_panels.VIEW3D_MT_collision_creation,
    properties_panels.VIEW3D_PT_collision_panel,
    properties_panels.VIEW3D_PT_collision_settings_panel,
    properties_panels.VIEW3D_PT_collision_visibility_panel,
    properties_panels.VIEW3D_PT_collision_material_panel,
    properties_panels.VIEW3D_MT_PIE_template,
    popup.VIEW3_PT_console_popup,
)


def get_preset_folder_path():
    path = Path(str(__file__))
    parent = path.parent.parent.parent.absolute()

    collider_presets = str(__package__.split('.')[0])
    return os.path.join(parent, collider_presets, "presets")


def initialize_presets():
    my_presets = collider_presets_folder()

    # Get a list of all the files in your bundled presets folder
    my_bundled_presets = get_preset_folder_path()
    files = os.listdir(my_bundled_presets)

    # Copy them
    for f in files:
        filepath = os.path.join(my_bundled_presets, f)
        shutil.copy2(filepath, my_presets)


def register():
    bpy.types.Scene.show_outputs = bpy.props.BoolProperty(name="Show outputs", default=True)
    bpy.types.Scene.show_errors = bpy.props.BoolProperty(name="Show errors", default=True)
    bpy.types.Scene.console_thief = bpy.props.BoolProperty(name="Show Console", default=True)

    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    initialize_presets()


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.show_outputs
    del bpy.types.Scene.show_errors
    del bpy.types.Scene.console_thief