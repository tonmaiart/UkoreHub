import mgear.rigbits
import mgear.shifter.custom_step as cstp
from mgear import rigbits,animbits
import pymel.core as pm
import maya.cmds as mc
from mgear.core import attribute
from TonmaiToolkit import utils
from importlib import reload

reload(utils)

class CustomShifterStep(cstp.customShifterMainStep):
    """Custom Step description
    """

    def setup(self):
        """
        Setting the name property makes the custom step accessible
        in later steps.

        i.e: Running  self.custom_step("add_corrective_finger_joints")  from steps ran after
             this one, will grant this step.
        """
        self.name = "rename_lips"

    def get_objects_in_set(self,set_name):
        if mc.objExists(set_name) and mc.objectType(set_name) == 'objectSet':
            return mc.sets(set_name, q=True) or []
        else:
            print(f"Set '{set_name}' does not exist or is not a valid objectSet.")
            return []

    def set_labelling_joint(self):
        def set_label(joint):
            list_data = [["_C0_", 0,""], ["_L0_", 0,""], ["_R0_", 0,""]]

            for data in list_data:
                keyword = data[0]
                side_index = data[1]
                prefix = data[2]

                if keyword in joint:
                    mc.setAttr(joint+".side",side_index)
                    mc.setAttr(joint+".type",18)
                    mc.setAttr(joint+".otherType",prefix+joint.replace(keyword,"_"),typ="string")
                    break
                else:
                    continue

        # Example usage:
        my_set = "rig_deformers_grp"
        objects = self.get_objects_in_set(my_set)

        for joint in objects:
            print("joint label : ",joint)
            set_label(joint)

    def rename_controller_leg(self):
        controls = self.get_objects_in_set("rig_controllers_grp")
        leg_list_data = [["root", "upper"], ["elbow","knee"], ["wrist","foot"]]

        for ctl in controls:
            for data in leg_list_data:
                keyword = data[0]
                new = data[1]

                if ctl.startswith("leg") and keyword in utils.cut(ctl):
                    mc.rename(ctl,ctl.replace(keyword,new))

    def rename_controller_arm(self):
        controls = self.get_objects_in_set("rig_controllers_grp")
        arm_list_data = [["root", "upper"], ["elbow","elbow"], ["wrist","hand"]]

        for ctl in controls:
            for data in arm_list_data:
                keyword = data[0]
                new = data[1]

                if ctl.startswith("arm") and keyword in utils.cut(ctl):
                    mc.rename(ctl,ctl.replace(keyword,new))

    def run(self):
        """Run method.

            i.e:  self.mgear_run.global_ctl
                gets the global_ctl from shifter rig build base

            i.e:  self.component("control_C0").ctl
                gets the ctl from shifter component called control_C0

            i.e:  self.custom_step("otherCustomStepName").ctlMesh
                gets the ctlMesh from a previous custom step called
                "otherCustomStepName"

        Returns:
            None: None
        """

        list_joint = ["arm_L0_elbow_jnt","arm_L0_wrist_jnt",
                      "thumb_L0_0_jnt","thumb_L0_1_jnt","thumb_L0_2_jnt"]+['index_L0_1_jnt', 'index_L0_2_jnt', 'index_L0_3_jnt', 'middle_L0_1_jnt', 'middle_L0_2_jnt', 'middle_L0_3_jnt',
                     'ring_L0_1_jnt', 'ring_L0_2_jnt', 'ring_L0_3_jnt']+["leg_L0_root_jnt","leg_L0_elbow_jnt","leg_L0_wrist_jnt","leg_L0_eff_jnt"]


        for joint in list_joint:
            for side in ["_L0_", "_R0_"]:
                joint = joint.replace("_L0_",side)

                joint_node = pm.PyNode(joint)
                joint_blend = mgear.rigbits.addBlendedJoint(joint_node)
                joint_support = mgear.rigbits.addSupportJoint(joint_blend,select=False)

        dict_enum_space = {"arm_L0_root_fk_ctl":["arm_L0_root_fk_ctl",["master_C0_ctl","chest_C0_ctl", "cog_C0_ctl","world_ctl"],["Master","Chest", "Cog","World"],"orient"],
                           "arm_L0_wrist_ik_ctl": ["arm_L0_wrist_ik_ctl", ["master_C0_ctl","cog_C0_ctl","chest_C0_ctl","world_ctl"],["Master","Cog", "Chest","World"], "parent"],
                           "leg_L0_root_fk_ctl": ["leg_L0_root_fk_ctl", ["master_C0_ctl","cog_C0_ctl","world_ctl" ],
                                                  ["Master","Cog","World", ], "orient"],
                           "leg_L0_wrist_ik_ctl": ["leg_L0_wrist_ik_ctl", ["master_C0_ctl","cog_C0_ctl","world_ctl" ],
                                                   ["Master","Cog","World", ], "parent"]
        }

        for key in dict_enum_space.keys():
            for side in ["_L0_", "_R0_"]:
                target = key.replace("_L0_",side)
                object_attr = dict_enum_space[key][0].replace("_L0_",side)
                list_space = dict_enum_space[key][1]
                list_nice_name = dict_enum_space[key][2]
                type = dict_enum_space[key][3]

                utils.create_switch_enum(object_attribute=object_attr,
                                         list_target=list_space,
                                         list_target_name=list_nice_name,
                                         object_driven=target,
                                         type=type)


        self.set_labelling_joint()
        self.rename_controller_leg()
        self.rename_controller_arm()