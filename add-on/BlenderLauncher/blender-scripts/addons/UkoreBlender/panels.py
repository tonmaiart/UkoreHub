import bpy

# --------------------
# Widget (UI Panels (Press N in 3D View to display))
# ------------


class PanelMain(bpy.types.Panel):
    bl_label = "Main Tools"
    bl_idname = "PT_Publish"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ukore Blender Tool"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.scale_y = 1.8
        row.operator("main.open_share_directory")
        row.operator("main.save_as")

        col = layout.column(align=True)
        col.scale_y = 1.8
        col.operator("crux.import_or_link", text="Import Published Assets...")

        row = col.row()
        row.prop(scene.my_props, "job_type")
        row.prop(scene.my_props, "job_task")
        row.operator("main.publish_dialog", text="Publish")


class PanelRender(bpy.types.Panel):
    bl_label = "Render"
    bl_idname = "PT_Render"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ukore Blender Tool"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.scale_y = 1.3
        col.operator("render.set_up_outliner", text="Set-up Outliner")
        col.operator("render.update_anim_cache", text="Update Anim Cache...")
        col.operator("render.update_anim_camera", text="Update Camera...")
        col.operator("render.link_mesh_data", text="Link Selected Mesh Data")


class PanelTools(bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "PT_Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ukore Blender Tool"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.scale_y = 1.3

        col.label(text="File")

        col.operator("publish.save_increment", text="Save Increment")
        col.operator("wm.check_link_update", text="Update All Link File")

        col.label(text="To Maya")

        col.operator("rig.write_weight_to_maya", text="Write Weight to Maya")
        col.operator("rig.read_weight_from_maya", text="Read Weight from Maya")

        col.label(text="Misc")

        col.operator("common.override_collection")
        col.operator("render.reload_scripts")


class PanelModel(bpy.types.Panel):
    bl_label = "Model"
    bl_idname = "PT_Model"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ukore Blender Tool"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        # box.label(text="Import Published Model")

        col = box.column(align=True)
        col.scale_y = 1.3
        col.operator(
            "crux.publish_model_proxy", text="Publish Model Proxy", icon="IMPORT"
        )
        col.operator("crux.publish_model_hi", text="Publish Model Hi", icon="IMPORT")
        col.operator(
            "crux.publish_model_texture", text="Publish Model Texture", icon="IMPORT"
        )


class PanelMap(bpy.types.Panel):
    bl_label = "Map"
    bl_idname = "PT_Map"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Ukore Blender Tool"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        # box.label(text="Import Published Model")

        col = box.column(align=True)
        col.scale_y = 1.3
        col.operator(
            "crux.publish_map_layout", text="Publish Map Layout", icon="IMPORT"
        )
        col.operator("crux.publish_map_hi", text="Publish Map Hi", icon="IMPORT")


# List of all panel classes to register
panel_classes = [
    PanelMain,
    PanelRender,
    PanelTools,
    # PanelModel,
    # PanelMap,
]
