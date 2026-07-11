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


