bl_info = {
    "name": "Quick Weight Paint Toggle",
    "blender": (4, 0, 0),
    "category": "Object",
}


import bpy


class SimpleWeightPaintToggle(bpy.types.Operator):
    """Selects the linked armature and enters Weight Paint mode immediately"""

    bl_idname = "object.quick_weight_paint"
    bl_label = "Quick Weight Paint"

    def execute(self, context):
        obj = context.active_object

        # 1. Check if we actually have a mesh selected
        if not obj or obj.type != "MESH":
            self.report({"WARNING"}, "Active object is not a mesh!")
            return {"CANCELLED"}

        # 2. Find the Armature in the modifiers
        armature_obj = None
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and mod.object:
                armature_obj = mod.object
                break

        if not armature_obj:
            self.report({"WARNING"}, "No Armature modifier found on this mesh!")
            return {"CANCELLED"}

        # 3. The "Magic" sequence
        # We need to ensure the armature is selected but the mesh is the ACTIVE object
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        armature_obj.select_set(True)  # Select Armature
        obj.select_set(True)  # Select Mesh
        context.view_layer.objects.active = obj  # Keep Mesh active

        # 4. Switch to Weight Paint
        bpy.ops.object.mode_set(mode="WEIGHT_PAINT")

        return {"FINISHED"}


def menu_func(self, context):
    # This line creates the actual menu entry
    self.layout.operator(
        SimpleWeightPaintToggle.bl_idname, text=SimpleWeightPaintToggle.bl_label
    )


def register():
    bpy.utils.register_class(SimpleWeightPaintToggle)
    # This adds it to the Object menu automatically
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SimpleWeightPaintToggle)
    # This cleans it up when the addon is disabled
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()
