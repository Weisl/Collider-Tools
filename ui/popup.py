import bpy
import sys
import io
from .properties_panels import draw_auto_convex_settings


class Thief(io.StringIO):
    def __init__(self, initial):
        super().__init__()
        self.source = initial


def organizeMessage(inp):
    txt = inp.split("\n")
    out = []

    tmp = []
    lastI = -999
    for line in txt:
        i = len(out) - 1

        flag = False
        while i >= 0 and i > lastI:
            if out[i] == line:
                tmp.append(line)
                lastI = i
                flag = True
                break

            i -= 1

        if lastI == i and i == len(out) - 1:
            div = len(out) - len(tmp)
            if isinstance(out[div - 1], int):
                out[div - 1] += 1
            else:
                out.insert(div, 2)

            tmp = []
            lastI = -999
        elif not flag:
            tmp.append(line)
            out += tmp
            tmp = []
    return out


class VIEW3_PT_console_popup(bpy.types.Panel):
    """Tooltip"""
    bl_idname = "VIEW3_PT_console_popup"
    bl_label = "Collider Tools: Console Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_ui_units_x = 30

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()

        col = row.column()
        col.label(text=";asdkfja;sdlfkj;asdlkfj;aslkdf j;lkasdjf; kjasd lkad sj;f lkajds;lksd j;alkj dsf;lksadj f;")

        from datetime import datetime
        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        col.label(text=f"Current Time = {current_time}")
        # if not isinstance(sys.stdout, Thief):
        #     sys.stdout = Thief(sys.stdout)
        # else:
        #     if isinstance(sys.stdout, Thief):
        #         sys.stdout = sys.stdout.source

        col.separator()

        # col.prop(scene, "show_outputs", text="Show Debug outputs")
        # col.prop(scene, "show_errors", text="Show Errors")

        # Prints
        values = sys.stdout.getvalue()
        val = organizeMessage(values)


        if len(val) > 0:
            box = col.box()
            for output in val:
                box.label(text=output)
        else:
                col.label(text="No Debug output to show")

        col.operator("console_output.clear", text="Clear Console Outputs", icon="FILE_REFRESH")

class VIEW3D_PT_auto_convex_popup(bpy.types.Panel):
    """Tooltip"""
    bl_idname = "POPUP_PT_auto_convex"
    bl_label = "Renaming Info"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"

    def draw(self, context):

        layout = self.layout

        colSettings = context.scene.collider_tools
        draw_auto_convex_settings(colSettings, layout)
        layout.label(text='May take up to a few minutes', icon='ERROR')
        layout.operator("collision.vhacd", text="Auto Convex", icon='MESH_ICOSPHERE')

        return
