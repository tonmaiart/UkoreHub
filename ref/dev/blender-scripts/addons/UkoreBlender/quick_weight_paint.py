

import bpy

# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------


class UKORE_OT_QuickWeightPaint(bpy.types.Operator):
    """Selects the linked armature and enters Weight Paint mode immediately"""

    bl_idname = "object.ukore_quick_weight_paint"
    bl_label = "Quick Weight Paint"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object

        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Active object is not a mesh!")
            return {"CANCELLED"}

        # Find Armature modifier
        armature_obj = next(
            (
                mod.object
                for mod in obj.modifiers
                if mod.type == "ARMATURE" and mod.object
            ),
            None,
        )

        if not armature_obj:
            self.report({"WARNING"}, "No Armature modifier found on this mesh!")
            return {"CANCELLED"}

        # Transition Logic
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        armature_obj.select_set(True)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
        return {"FINISHED"}


class UKORE_OT_QuickPoseMode(bpy.types.Operator):
    """Detects linked armature and enters Pose Mode from any related object"""

    bl_idname = "object.ukore_quick_pose_mode"
    bl_label = "Quick Pose Mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}

        armature_obj = None
        if obj.type == "MESH":
            armature_obj = next(
                (
                    mod.object
                    for mod in obj.modifiers
                    if mod.type == "ARMATURE" and mod.object
                ),
                None,
            )
        elif obj.type == "ARMATURE":
            armature_obj = obj

        if not armature_obj:
            self.report({"WARNING"}, "No linked armature detected!")
            return {"CANCELLED"}

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        armature_obj.select_set(True)
        context.view_layer.objects.active = armature_obj

        bpy.ops.object.mode_set(mode="POSE")
        return {"FINISHED"}


# ------------------------------------------------------------------------
# UI Panel (N-Panel / Sidebar)
# ------------------------------------------------------------------------


class UKORE_PT_MainPanel(bpy.types.Panel):
    bl_label = "Rigging Toggles"
    bl_idname = "UKORE_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ukore Tool"  # The name of the vertical tab in the N-panel

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="Mode Switches:")
        col.operator(UKORE_OT_QuickWeightPaint.bl_idname, icon="WPAINT_HLT")
        col.operator(UKORE_OT_QuickPoseMode.bl_idname, icon="POSE_HLT")


# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

classes = (
    UKORE_OT_QuickWeightPaint,
    UKORE_OT_QuickPoseMode,
    UKORE_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
