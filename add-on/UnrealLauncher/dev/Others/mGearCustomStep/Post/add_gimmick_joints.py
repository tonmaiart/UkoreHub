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
        self.name = "add_gimmick_joints"

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