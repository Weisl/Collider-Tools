import bmesh
import bpy
from bpy.types import Operator

from .add_bounding_primitive import OBJECT_OT_add_bounding_object

class OBJECT_OT_add_mesh_collision(OBJECT_OT_add_bounding_object, Operator):
    """Create a new bounding box object"""
    bl_idname = "mesh.add_mesh_collision"
    bl_label = "Add Mesh Collision"

    def __init__(self):
        super().__init__()
        self.use_decimation = True
        self.use_modifier_stack = True

    def invoke(self, context, event):
        super().invoke(context, event)
        self.type_suffix = self.prefs.meshColSuffix
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        status = super().modal(context, event)
        if status == {'FINISHED'}:
            return {'FINISHED'}
        if status == {'CANCELLED'}:
            return {'CANCELLED'}

        scene = context.scene

        # change bounding object settings
        if event.type == 'P' and event.value == 'RELEASE':
            self.my_use_modifier_stack = not self.my_use_modifier_stack
            self.execute(context)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.remove_objects(self.new_colliders_list)
        self.new_colliders_list = []

        # reset previously stored displace modifiers when creating a new object
        self.displace_modifiers = []

        # Add the active object to selection if it's not selected. This fixes the rare case when the active Edit mode object is not selected in Object mode.
        if context.object not in self.selected_objects:
            self.selected_objects.append(context.object)

        old_objs = set(context.scene.objects)

        for obj in self.selected_objects:

            # skip if invalid object
            if obj is None:
                continue

            # skip non Mesh objects like lamps, curves etc.
            if obj.type != "MESH":
                continue

            context.view_layer.objects.active = obj
            collections = obj.users_collection

            if obj.mode == "EDIT":
                bpy.ops.mesh.duplicate()
                bpy.ops.mesh.separate(type='SELECTED')

            else:  # mode == "OBJECT":
                bpy.ops.object.mode_set(mode='EDIT')

                # Get a BMesh representation
                me = obj.data
                bm = bmesh.from_edit_mesh(me)

                # select all vertices
                self.get_vertices(bm, preselect_all=True)

                bpy.ops.mesh.duplicate()
                bpy.ops.mesh.separate(type='SELECTED')

                pass

            prefs = context.preferences.addons["CollisionHelpers"].preferences
            type_suffix = prefs.boxColSuffix
            new_name = super().collider_name(context, type_suffix)

            bpy.ops.object.mode_set(mode='OBJECT')
            new_collider = context.scene.objects[-1]
            new_collider.name = new_name
            add_modifierstack(self, new_collider)
            # create collision meshes
            self.custom_set_parent(context, obj, new_collider)

            # save collision objects to delete when canceling the operation
            # self.previous_objects.append(new_collider)
            collections = obj.users_collection

            self.primitive_postprocessing(context, new_collider,collections)

            # infomessage = 'Generated collisions %d/%d' % (i, obj_amount)
            # self.report({'INFO'}, infomessage)

        self.new_colliders_list = set(context.scene.objects) - old_objs

        return {'RUNNING_MODAL'}
