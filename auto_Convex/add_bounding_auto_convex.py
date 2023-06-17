import os
import time
from subprocess import Popen

import bmesh
import bpy
from bpy.types import Operator

from ..collider_shapes.add_bounding_primitive import OBJECT_OT_add_bounding_object


def bmesh_join(list_of_bmeshes, list_of_matrices, normal_update=False):
    # sourcery skip: use-contextlib-suppress
    """ takes as input a list of bm references and outputs a single merged bmesh
    allows an additional 'normal_update=True' to force _normal_ calculations.
    """
    bm = bmesh.new()
    add_vert = bm.verts.new
    add_face = bm.faces.new
    add_edge = bm.edges.new

    for bm_to_add, matrix in zip(list_of_bmeshes, list_of_matrices):
        bm_to_add.transform(matrix)

    for bm_to_add in list_of_bmeshes:
        offset = len(bm.verts)

        for v in bm_to_add.verts:
            add_vert(v.co)

        bm.verts.index_update()
        bm.verts.ensure_lookup_table()

        if bm_to_add.faces:
            for face in bm_to_add.faces:
                add_face(tuple(bm.verts[i.index + offset] for i in face.verts))
            bm.faces.index_update()

        if bm_to_add.edges:
            for edge in bm_to_add.edges:
                edge_seq = tuple(bm.verts[i.index + offset]
                                 for i in edge.verts)
                try:
                    add_edge(edge_seq)
                except ValueError:
                    # edge exists!
                    pass
            bm.edges.index_update()

    if normal_update:
        bm.normal_update()

    me = bpy.data.meshes.new("joined_mesh")
    bm.to_mesh(me)

    return me


class VHACD_OT_convex_decomposition(OBJECT_OT_add_bounding_object, Operator):
    bl_idname = 'collision.vhacd'
    bl_label = 'Convex Decomposition'
    bl_description = 'Create multiple convex hull colliders to represent any object using Hierarchical Approximate Convex Decomposition'
    bl_options = {'REGISTER', 'PRESET'}

    @staticmethod
    def overwrite_executable_path(path):
        '''Users can overwrite the default executable path. '''
        # Check executable path
        executable_path = bpy.path.abspath(path)

        return executable_path if os.path.isfile(executable_path) else False

    @staticmethod
    def set_temp_data_path(path):
        '''Set folder to temporarily store the exported data. '''
        # Check data path
        data_path = bpy.path.abspath(path)

        return data_path if os.path.isdir(data_path) else False

    def __init__(self):
        super().__init__()
        self.use_decimation = True
        self.use_geo_nodes_hull = True
        self.use_modifier_stack = True
        self.use_recenter_origin = True
        self.shape = 'convex_shape'

    def invoke(self, context, event):
        super().invoke(context, event)
        # bpy.ops.VIEW3_PT_console_popup('INVOKE_DEFAULT')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        status = super().modal(context, event)
        if status == {'FINISHED'}:
            return {'FINISHED'}
        if status == {'CANCELLED'}:
            return {'CANCELLED'}
        if status == {'PASS_THROUGH'}:
            return {'PASS_THROUGH'}

        # change bounding object settings
        if event.type == 'P' and event.value == 'RELEASE':
            self.my_use_modifier_stack = not self.my_use_modifier_stack
            self.execute(context)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.space_data.shading.color_type = self.color_type
        try:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        except ValueError:
            pass
        return {'CANCELLED'}

    def execute(self, context):

        # CLEANUP
        super().execute(context)
        
        bpy.ops.wm.call_panel(name="VIEW3_PT_console_popup", keep_open=True)

        overwrite_path = self.overwrite_executable_path(
            self.prefs.executable_path)
        vhacd_exe = self.prefs.default_executable_path if not overwrite_path else overwrite_path
        data_path = self.set_temp_data_path(self.prefs.data_path)

        if not vhacd_exe or not data_path:
            if not vhacd_exe:
                self.report({'ERROR'},
                            'V-HACD executable is required for Auto Convex to work. Please follow the installation instructions and try it again')
            if not data_path:
                self.report({'ERROR'}, 'Invalid temporary data path')

            return self.cancel(context)

        for obj in self.selected_objects:
            obj.select_set(False)

        collider_data = []
        meshes = []
        matrices = []

        for obj in self.selected_objects:

            # skip if invalid object
            if not self.is_valid_object(obj):
                continue

            context.view_layer.objects.active = obj

            if self.obj_mode == "EDIT":
                new_mesh = self.get_mesh_Edit(
                    obj, use_modifiers=self.my_use_modifier_stack)
            else:  # mode == "OBJECT":
                new_mesh = self.mesh_from_selection(
                    obj, use_modifiers=self.my_use_modifier_stack)

            if new_mesh == None:
                continue

            if self.creation_mode[self.creation_mode_idx] == 'INDIVIDUAL':
                convex_collision_data = {}
                convex_collision_data['parent'] = obj
                convex_collision_data['mesh'] = new_mesh
                collider_data.append(convex_collision_data)

            # if self.creation_mode[self.creation_mode_idx] == 'SELECTION':
            else:
                meshes.append(new_mesh)
                matrices.append(obj.matrix_world)

        if self.creation_mode[self.creation_mode_idx] == 'SELECTION':
            convex_collision_data = {}
            convex_collision_data['parent'] = self.active_obj

            bmeshes = []

            for mesh in meshes:
                bm_new = bmesh.new()
                bm_new.from_mesh(mesh)
                bmeshes.append(bm_new)

            joined_mesh = bmesh_join(bmeshes, matrices)

            convex_collision_data['mesh'] = joined_mesh
            collider_data = [convex_collision_data]

        bpy.ops.object.mode_set(mode='OBJECT')
        convex_decomposition_data = []

        for convex_collision_data in collider_data:
            parent = convex_collision_data['parent']
            mesh = convex_collision_data['mesh']

            joined_obj = bpy.data.objects.new('debug_joined_mesh', mesh.copy())
            bpy.context.scene.collection.objects.link(joined_obj)

            # Base filename is object name with invalid characters removed
            filename = ''.join(
                c for c in parent.name if c.isalnum() or c in (' ', '.', '_')).rstrip()

            obj_filename = os.path.join(data_path, '{}.obj'.format(filename))

            colSettings = context.scene.collider_tools

            print('\nExporting mesh for V-HACD: {}...'.format(obj_filename))

            joined_obj.select_set(True)

            io_use_addon = True if bpy.app.version < (3, 2, 0) else False
            io_new_export_old_parameters = True if bpy.app.version < (3, 3, 0) else False

            if io_use_addon:
                import addon_utils
                
                # enable the obj addon if it's disabled
                addon_name = 'io_scene_obj'
                addon_utils.check(addon_name)
                success = addon_utils.enable(addon_name)

                # Cancel Operation if addon can't be found
                if not success:
                    self.report(
                        {'ERROR'}, "The obj export addon is needed for the auto convex to work and was not found")
                    return self.cancel(context)

                # Use export addon
                bpy.ops.export_scene.obj(filepath=obj_filename, check_existing=False, filter_glob='*.obj;*.mtl', use_selection=True, use_animation=False, use_mesh_modifiers=True, use_edges=True, use_smooth_groups=False, use_smooth_groups_bitflags=False, use_normals=False,
                                         use_uvs=False, use_materials=False, use_triangles=False, use_nurbs=False, use_vertex_groups=False, use_blen_objects=True, group_by_object=False, group_by_material=False, keep_vertex_order=False, global_scale=1.0, path_mode='AUTO', axis_forward='Y', axis_up='Z')
                
                # Display a warning when Blender uses the small export instead of the fast one! 
                self.report(
                    {'WARNING'}, "This version of Blender uses the slow exporter/importer. Update to version 3.3!")

            elif io_new_export_old_parameters:
                bpy.ops.wm.obj_export(filepath=obj_filename,  check_existing=False, export_selected_objects=True, export_materials=False,
                                      export_uv=False, export_normals=False, forward_axis='Y_FORWARD', up_axis='Z_UP')

            else: # io_new_export
                bpy.ops.wm.obj_export(filepath=obj_filename,  check_existing=False, export_selected_objects=True, export_materials=False,
                        export_uv=False, export_normals=False, forward_axis='Y', up_axis='Z')

            if self.prefs.debug:
                joined_obj.color = (1.0, 0.1, 0.1, 1.0)
                joined_obj.select_set(False)
            else:  # remove debug meshes
                bpy.data.objects.remove(joined_obj)

            exportTime = time.time()

            cmd_line = ('"{}" "{}" -h {} -v {} -o {} -g {} -r {} -e {} -d {} -s {} -f {} -l {} -p {} -g {}').format(vhacd_exe,
                                                                                                                    obj_filename,
                                                                                                                    colSettings.maxHullAmount,
                                                                                                                    colSettings.maxHullVertCount,
                                                                                                                    'obj', 1,
                                                                                                                    colSettings.voxelResolution,
                                                                                                                    self.prefs.vhacd_volumneErrorPercent,
                                                                                                                    self.prefs.vhacd_maxRecursionDepth,
                                                                                                                    "true" if colSettings.vhacd_shrinkwrap else "false",
                                                                                                                    self.prefs.vhacd_fillMode,
                                                                                                                    self.prefs.vhacd_minEdgeLength,
                                                                                                                    "true" if self.prefs.vhacd_optimalSplitPlane else "false",
                                                                                                                    "true")

            print('Running V-HACD...\n{}\n'.format(cmd_line))

            vhacd_process = Popen(cmd_line, bufsize=-1,
                                  close_fds=True, shell=True)
            bpy.data.meshes.remove(mesh)
            vhacd_process.wait()

            # List of new files
            dir_files = os.listdir(data_path)
            obj_list = []
            for file in dir_files:
                if file.endswith('.obj'):
                    obj_path = os.path.join(data_path, file)
                    fileTime = os.path.getmtime(obj_path)

                    # check if file was modified after export
                    if fileTime > exportTime:
                        obj_list.append(obj_path)

            # List of imported objects
            imported = []
            for obj_path in obj_list:
                if io_use_addon:
                    bpy.ops.import_scene.obj(filepath=obj_path, use_edges=True, use_smooth_groups=False, use_split_objects=True, use_split_groups=False,
                                             use_groups_as_vgroups=False, use_image_search=False, split_mode='ON', global_clamp_size=0.0, axis_forward='Y', axis_up='Z')
                elif io_new_export_old_parameters:
                    bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='Y_FORWARD', up_axis='Z_UP')
                else: #io_new_export
                    bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='Y', up_axis='Z')
                
                imported.append(bpy.context.selected_objects)

            # flatten list
            imported = [item for sublist in imported for item in sublist]

            for ob in imported:
                ob.select_set(False)

            convex_collisions_data = {}
            convex_collisions_data['colliders'] = imported
            convex_collisions_data['parent'] = parent
            convex_decomposition_data.append(convex_collisions_data)

        context.view_layer.objects.active = self.active_obj

        for convex_collisions_data in convex_decomposition_data:
            convex_collision = convex_collisions_data['colliders']
            parent = convex_collisions_data['parent']

            for new_collider in convex_collision:
                new_collider.name = super().collider_name(basename=parent.name)

                self.custom_set_parent(context, parent, new_collider)

                if self.creation_mode[self.creation_mode_idx] == 'INDIVIDUAL':
                    new_collider.matrix_world = parent.matrix_world
                    # Apply rotation and scale for custom origin to work.
                    self.apply_transform(
                        new_collider, rotation=True, scale=True)

                collections = parent.users_collection
                self.primitive_postprocessing(
                    context, new_collider, collections)
                self.new_colliders_list.append(new_collider)

        if len(self.new_colliders_list) < 1:
            self.report({'WARNING'}, 'No meshes to process!')
            return {'CANCELLED'}

        super().reset_to_initial_state(context)
        elapsed_time = self.get_time_elapsed()
        super().print_generation_time("Auto Convex Colliders", elapsed_time)
        self.report({'INFO'}, "Auto Convex Colliders: " +
                    str(float(elapsed_time)))

        return {'FINISHED'}
