import bpy

from ..pyshics_materials.material_helpers import remove_materials, set_material

def alignObjects(new, old):
    """Align two objects"""
    new.matrix_world = old.matrix_world


def getBoundingBox(obj):
    return obj.bound_box


def setOriginToCenterOfMass(ob):
    """"""
    oldActive = bpy.context.object
    bpy.context.view_layer.objects.active = ob

    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
    bpy.context.view_layer.objects.active = oldActive


def add_displace_mod(ob, strenght):
    # add inflate modifier
    mod = ob.modifiers.new(name="ColliderOffset_disp", type='DISPLACE')
    mod.strength = strenght


def setColliderSettings(self, context, collider, matname):
    collider.display_type = self.my_collision_shading_view
    collider.color = self.my_color
    add_displace_mod(collider, self.my_offset)
    remove_materials(collider)
    set_material(collider, matname)
