import mgear.rigbits
import mgear.shifter.custom_step as cstp
from mgear import rigbits,animbits
import pymel.core as pm
import maya.cmds as mc
from mgear.core import attribute
from TonmaiToolkit import utils
from importlib import reload
import TonmaiToolkit.toolkits.ControllerEditor.func as func_ce
import TonmaiToolkit.toolkits.PolishManager.func as func_pm

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
        self.name = "post_durian"


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

        self.blend_enum_space()
        self.set_proper_name()
        self.add_gimick_joints()
        self.set_visibility()


    def blend_enum_space(self):
        dict_enum_space = {"arm_L0_root_fk_ctl":["arm_L0_root_fk_ctl",["master_C0_ctl","chest_C0_ctl", "cog_C0_ctl","world_ctl","clavicle_L0_ctl"],["Master","Chest", "Cog","World","Clavicle"],"orient"],
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

    def set_proper_name(self):
        dict_rename_data = {
            "leg": [["root", "upper"], ["elbow", "knee"], ["wrist", "foot"]],
            "arm": [["root", "upper"], ["elbow", "elbow"], ["wrist", "hand"]]
        }

        controls = utils.get_objects_in_set("rig_controllers_grp")

        for ctl in controls:
            for start_keyword in dict_rename_data.keys():
                for data in dict_rename_data[start_keyword]:
                    old_name = data[0]
                    new_name = data[1]

                    if ctl.startswith(start_keyword) and old_name in utils.cut(ctl):
                        mc.rename(ctl,ctl.replace(old_name,new_name))



    def add_gimick_joints(self):
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

        dict_add_support_joint = {
            "arm_L0_wrist_jnt":[["z",-0.1]],
            "arm_L0_elbow_jnt":[["z",-0.1]]
                      }


        for key in dict_add_support_joint.keys():
            for side in ["_L0_", "_R0_"]:
                joint = key.replace("_L0_", side)

                joint_node = pm.PyNode(joint)

                # create blend joint
                joint_blend = mgear.rigbits.addBlendedJoint(joint_node)

                for data in dict_add_support_joint[key]:
                    translate_axis,translate_value = data

                    # create support joint
                    joint_support = mgear.rigbits.addSupportJoint(joint_blend,select=False)[0]

                    # set attribute value
                    pm.setAttr("{}.t{}".format(joint_support,translate_axis),translate_value)

    def set_visibility(self):
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

        # backup controller
        func_ce.backup_recall()

        # hide index ctrl
        list_finalize = ["index_L0_fk0_ctlShape"]

        for obj in list_finalize:
            for side in ["_L0_", "_R0_"]:
                target_obj = obj.replace("_L0_", side)

                if not mc.objExists(target_obj):
                    raise Exception("{} not found in finalize".format(target_obj))

                # function
                pm.setAttr("{}.v".format(target_obj),0)

        # hide attribute
        # List of attributes to lock and hide
        attributes = [
            "IkPivot",
            "roll",
            "sideRoll",
            "middleRoll",
            "baseTwist",
            "tipTwist",
            "rollBallEnd"
        ]

        # Target control
        control = "arm_L0_hand_ik_ctl"

        # Iterate and apply setAttr for each attribute
        for obj in [control]:
            for side in ["_L0_", "_R0_"]:
                target_obj = obj.replace("_L0_", side)

                # main function
                for attr in attributes:
                    full_attr = f"{target_obj}.{attr}"
                    mc.setAttr(full_attr, lock=True, keyable=False, channelBox=False)

        # Remove all mgear node
        func_pm.clean_mgear_mult_matrix()
        func_pm.clean_mgear_matrix_constraint()




