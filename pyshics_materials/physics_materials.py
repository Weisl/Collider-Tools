import bpy
import random
from bpy.props import StringProperty

from .material_functions import assign_physics_material, remove_materials, create_material


class MATERIAL_OT_physics_material_random_color(bpy.types.Operator):
    bl_idname = "material.random_physics_mat_color"
    bl_label = "Random Color"
    bl_description = "Generate random color for the physics material"
    bl_options = {'REGISTER', 'UNDO'}

    generated_color: bpy.props.FloatVectorProperty(
        name="New Color",
        subtype='COLOR',
        default=(1, 1, 1, 0.5),
        size=4,
        min=0, max=1,
        description="color picker")

    def execute(self, context):
        return {"FINISHED"}

class MATERIAL_OT_physics_material_create(bpy.types.Operator):
    bl_idname = "material.create_physics_material"
    bl_label = "Create Physics Material"
    bl_description = "Create Physics Material"
    bl_options = {'REGISTER', 'UNDO'}

    my_baseName: bpy.props.StringProperty(name="Name")

    rgb_controller: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', default=[1, 1, 1, 0.5], size=4, max=1,
                                                  description="Display Color")

    mat_naming_position: bpy.props.EnumProperty(
        name='Physics Material',
        items=(('PREFIX', "Prefix", "Prefix"),
               ('SUFFIX', "Suffix", "Suffix"),
               ('NONE', "None", "None")),
        default='PREFIX',
        description='Add custom naming as prefix or suffix'
    )

    @staticmethod
    def random_color():
        r = random.uniform(0, 1)
        g = random.uniform(0, 1)
        b = random.uniform(0, 1)

        color = (r, g, b, 0.5)
        return color

    def invoke(self, context, event):
        prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        self.mat_naming_position = prefs.material_naming_position
        self.final_name = ""
        if prefs.use_random_color:
            self.rgb_controller = self.random_color()
        else:
            self.rgb_controller = (1, 1, 1, 0.5)

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        prefs = context.preferences.addons[__package__.split('.')[0]].preferences

        row = layout.row()
        row.prop(self, "rgb_controller")
        row = layout.row()
        row.prop(self, "my_baseName")
        row = layout.row()
        row.enabled = False
        row.prop(prefs, "physics_material_filter", text="Filter")
        row = layout.row()
        row.prop(self, 'mat_naming_position', expand=True)

        if self.mat_naming_position == 'PREFIX':
            row = layout.row()
            row.label(
            text="Name = Material Prefix + Basename")
            name = prefs.physics_material_filter + prefs.physics_material_separator + self.my_baseName
        elif self.mat_naming_position == 'SUFFIX':  # self.naming_position == 'SUFFIX':
            row = layout.row()
            row.label(
                text="Name = Basename + Material Suffix")
            name = self.my_baseName + prefs.physics_material_separator + prefs.physics_material_filter
        else:
            name = self.my_baseName

        row = layout.row()
        row.label(text="Name = {}".format(name))
        self.final_name = name

    def execute(self, context):
        create_material(self.final_name, self.rgb_controller)
        return {"FINISHED"}

class MATERIAL_OT_set_physics_material(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "material.set_physics_material"
    bl_label = "Set Physics Material"
    bl_options = {'REGISTER', 'UNDO'}

    physics_material_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.mode == 'EDIT':
                assign_physics_material(obj, self.physics_material_name)
            else:
                try:
                    remove_materials(obj)
                    assign_physics_material(obj, self.physics_material_name)

                except Exception as e:
                    print(f'ERROR assigning physics material: {str(e)}')

        return {'FINISHED'}



