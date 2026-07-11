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
        self.name = "add_corrective_finger_joints"

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

        self.create_shoulder_corrective()

    def create_shoulder_corrective(self):
        left_joint = "arm_L0_0_jnt"
        right_joint = left_joint.replace("_L", "_R")

        for joint in [left_joint, right_joint]:
            sJnt = pm.PyNode(joint)

            blend_joint = rigbits.addBlendedJoint(sJnt)

            dict_support_joint = {"support_joint_up": ["ry", "tz", 1, 5, 90],
                                  "support_joint_down": ["ry", "tz", -1, -5, -90],
                                  "support_joint_front": ["rz", "ty", -1, -5, -90],
                                  "support_joint_back": ["rz", "ty", 1, 5, 90]}

            for support_joint_name in dict_support_joint.keys():
                attr_driver, attr_driven, base_value, driven_value, driver_value = dict_support_joint[
                    support_joint_name]

                support_joint = rigbits.addSupportJoint(blend_joint)[0]
                support_joint.rename(support_joint_name)

                # translate and add NPO
                support_joint.setAttr(attr_driven, base_value)
                mgear.rigbits.addNPO([support_joint])

                # create weight driver node
                node_shape = mc.createNode("weightDriver", n="{}_weightDriverShape".format(support_joint))

                node_shape_parent = mc.listRelatives(node_shape, p=1)[0]
                joint_parent = mc.listRelatives(joint, p=1)[0]

                mc.parent(node_shape_parent, joint_parent)

                # connection and set attribute
                mc.setAttr("{}.type".format(node_shape), 1)
                mc.connectAttr("{}.{}".format(joint, attr_driver), "{}.input[0]".format(node_shape))

                mc.setAttr("{}.poses[0].poseInput[0]".format(node_shape), 0)
                mc.setAttr("{}.poses[0].poseValue[0]".format(node_shape), 0)

                mc.setAttr("{}.poses[1].poseInput[0]".format(node_shape), driver_value)
                mc.setAttr("{}.poses[1].poseValue[0]".format(node_shape), driven_value)

                mc.setAttr("{}.poses[2].poseInput[0]".format(node_shape), driver_value * -1)
                mc.setAttr("{}.poses[2].poseValue[0]".format(node_shape), driven_value)

                mc.connectAttr("{}.output[0]".format(node_shape), "{}.{}".format(support_joint, attr_driven))
