import mgear.rigbits
import mgear.shifter.custom_step as cstp
from mgear import rigbits,animbits
import pymel.core as pm
import maya.cmds as mc
from mgear.core import attribute

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

        dict_rename = {
            "lips_C0_up_01_1_jnt": "lips_C0_up_01_L_3_jnt",
            "lips_C0_up_01_2_jnt": "lips_C0_up_01_L_2_jnt",
            "lips_C0_up_01_3_jnt": "lips_C0_up_01_L_1_jnt",
            "lips_C0_up_01_4_jnt": "lips_C0_up_01_C_jnt",
            "lips_C0_up_01_5_jnt": "lips_C0_up_01_R_1_jnt",
            "lips_C0_up_01_6_jnt": "lips_C0_up_01_R_2_jnt",
            "lips_C0_up_01_7_jnt": "lips_C0_up_01_R_3_jnt",

            "lips_C0_low_01_1_jnt": "lips_C0_low_01_L_2_jnt",
            "lips_C0_low_01_2_jnt": "lips_C0_low_01_L_1_jnt",
            "lips_C0_low_01_3_jnt": "lips_C0_low_01_C_jnt",
            "lips_C0_low_01_4_jnt": "lips_C0_low_01_R_1_jnt",
            "lips_C0_low_01_5_jnt": "lips_C0_low_01_R_2_jnt",

            "lips_C0_up_02_1_jnt": "lips_C0_up_02_L_3_jnt",
            "lips_C0_up_02_2_jnt": "lips_C0_up_02_L_2_jnt",
            "lips_C0_up_02_3_jnt": "lips_C0_up_02_L_1_jnt",
            "lips_C0_up_02_4_jnt": "lips_C0_up_02_C_jnt",
            "lips_C0_up_02_5_jnt": "lips_C0_up_02_R_1_jnt",
            "lips_C0_up_02_6_jnt": "lips_C0_up_02_R_2_jnt",
            "lips_C0_up_02_7_jnt": "lips_C0_up_02_R_3_jnt",

            "lips_C0_low_02_1_jnt": "lips_C0_low_02_L_2_jnt",
            "lips_C0_low_02_2_jnt": "lips_C0_low_02_L_1_jnt",
            "lips_C0_low_02_3_jnt": "lips_C0_low_02_C_jnt",
            "lips_C0_low_02_4_jnt": "lips_C0_low_02_R_1_jnt",
            "lips_C0_low_02_5_jnt": "lips_C0_low_02_R_2_jnt",

            "lips_C0_up_03_1_jnt": "lips_C0_up_03_L_3_jnt",
            "lips_C0_up_03_2_jnt": "lips_C0_up_03_L_2_jnt",
            "lips_C0_up_03_3_jnt": "lips_C0_up_03_L_1_jnt",
            "lips_C0_up_03_4_jnt": "lips_C0_up_03_C_jnt",
            "lips_C0_up_03_5_jnt": "lips_C0_up_03_R_1_jnt",
            "lips_C0_up_03_6_jnt": "lips_C0_up_03_R_2_jnt",
            "lips_C0_up_03_7_jnt": "lips_C0_up_03_R_3_jnt",

            "lips_C0_low_03_1_jnt": "lips_C0_low_03_L_2_jnt",
            "lips_C0_low_03_2_jnt": "lips_C0_low_03_L_1_jnt",
            "lips_C0_low_03_3_jnt": "lips_C0_low_03_C_jnt",
            "lips_C0_low_03_4_jnt": "lips_C0_low_03_R_1_jnt",
            "lips_C0_low_03_5_jnt": "lips_C0_low_03_R_2_jnt"
        }

        for keys in dict_rename.keys():
            if mc.objExists(keys):
                mc.rename(keys,dict_rename[keys])
