import bpy
from . import utils_rig

from importlib import reload
reload(utils_rig)

class WriteWeightToMaya(bpy.types.Operator):
    bl_idname = "rig.write_weight_to_maya"
    bl_label = "Write Weight to Maya"

    def execute(self, context):
        # Logic to write weight data back to Maya
        print("Writing weight data back to Maya...")
        result = utils_rig.export_fbx_animation_to_maya()

        if result is True:
            self.report({'INFO'}, "Weight data exported to Maya successfully!")
            return {'FINISHED'}
        elif result is False:
            return {'CANCELLED'}
        
class WritePoseToMaya(bpy.types.Operator):
    bl_idname = "rig.write_pose_to_maya"
    bl_label = "Write Pose to Maya"

    def execute(self, context):
        # Logic to write pose data back to Maya
        print("Writing pose data back to Maya...")
        return {'FINISHED'}

class ReadWeightFromMaya(bpy.types.Operator):
    bl_idname = "rig.read_weight_from_maya"
    bl_label = "Read Weight from Maya"

    def execute(self, context):
        # Logic to read weight data from Maya

        result = utils_rig.read_weight_from_maya()

        if result is True:
            self.report({'INFO'}, "Weight data readed v2!")

            return {'FINISHED'}
        elif result is False:
            self.report({'ERROR'}, "Failed to read weight data!")

            return {'CANCELLED'}

operator_classes = [WriteWeightToMaya,WritePoseToMaya,ReadWeightFromMaya]