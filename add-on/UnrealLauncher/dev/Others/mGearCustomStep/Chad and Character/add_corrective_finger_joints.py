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

        self.create_finger_corrective()
        self.create_knee_corrective()
        self.create_elbow_corrective()

        self.create_wrist_corrective()
        self.create_thigh_corrective()
        self.create_shoulder_corrective()
        return

    def create_thigh_corrective(self):
        left_joint = "leg_L0_0_jnt"
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

    def create_wrist_corrective(self):
        left_joint = "arm_L0_end_jnt"
        right_joint = left_joint.replace("_L","_R")

        for joint in [left_joint,right_joint]:
            sJnt = pm.PyNode(joint)

            blend_joint = rigbits.addBlendedJoint(sJnt)

            dict_support_joint = {"support_joint_up":["ry","tz",1,5,90],
                                  "support_joint_down":["ry","tz",-1,-5,-90],
                                  "support_joint_front":["rz","ty",-1,-5,-90],
                                  "support_joint_back":["rz","ty",1,5,90]}

            for support_joint_name in dict_support_joint.keys():
                attr_driver,attr_driven,base_value,driven_value,driver_value = dict_support_joint[support_joint_name]

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
                mc.setAttr("{}.type".format(node_shape),1)
                mc.connectAttr("{}.{}".format(joint,attr_driver), "{}.input[0]".format(node_shape))

                mc.setAttr("{}.poses[0].poseInput[0]".format(node_shape), 0)
                mc.setAttr("{}.poses[0].poseValue[0]".format(node_shape), 0)

                mc.setAttr("{}.poses[1].poseInput[0]".format(node_shape), driver_value)
                mc.setAttr("{}.poses[1].poseValue[0]".format(node_shape), driven_value)

                mc.setAttr("{}.poses[2].poseInput[0]".format(node_shape), driver_value*-1)
                mc.setAttr("{}.poses[2].poseValue[0]".format(node_shape), driven_value)

                mc.connectAttr("{}.output[0]".format(node_shape), "{}.{}".format(support_joint,attr_driven))

    def create_finger_corrective(self):
        left_joint_list = ['thumb_L0_1_jnt', 'thumb_L0_2_jnt', 'finger_L0_0_jnt', 'finger_L0_2_jnt', 'finger_L0_1_jnt', 'finger_L1_0_jnt', 'finger_L1_2_jnt', 'finger_L1_1_jnt', 'finger_L2_0_jnt', 'finger_L2_2_jnt', 'finger_L2_1_jnt', 'finger_L3_0_jnt', 'finger_L3_2_jnt', 'finger_L3_1_jnt']
        right_joint_list = [joint.replace("_L","_R") for joint in left_joint_list]

        # iterate to create blended joint
        for list_joint in [left_joint_list,right_joint_list]:
            for joint in list_joint:
                sJnt = pm.PyNode(joint)

                blend_joint = rigbits.addBlendedJoint(sJnt)

                support_joint_in = rigbits.addSupportJoint(blend_joint)[0]
                support_joint_out = rigbits.addSupportJoint(blend_joint)[0]

                pm.setAttr(str(support_joint_out)+".ty",1)
                pm.setAttr(str(support_joint_in)+".ty",-1)

                # create offset group
                mgear.rigbits.addNPO([support_joint_in,support_joint_out])

                # create weight driver
                dict_driven = {support_joint_in:-1,
                               support_joint_out:1}

                for support_joint in dict_driven.keys():
                    # create weight driver node
                    node_shape = mc.createNode("weightDriver",n="{}_weightDriverShape".format(support_joint))

                    node_shape_parent = mc.listRelatives(node_shape,p=1)[0]
                    joint_parent=  mc.listRelatives(joint,p=1)[0]

                    mc.parent(node_shape_parent,joint_parent)

                    # mc.rename(node_shape,"{}_weightDriver".format(support_joint))

                    # connection and set attribute
                    mc.setAttr("{}.type".format(node_shape),1)
                    mc.connectAttr("{}.rz".format(joint),"{}.input[0]".format(node_shape))

                    mc.setAttr("{}.poses[0].poseInput[0]".format(node_shape),0)
                    mc.setAttr("{}.poses[0].poseValue[0]".format(node_shape),0)

                    mc.setAttr("{}.poses[1].poseInput[0]".format(node_shape),90)
                    mc.setAttr("{}.poses[1].poseValue[0]".format(node_shape),dict_driven[support_joint])

                    mc.connectAttr("{}.output[0]".format(node_shape),"{}.ty".format(support_joint))

    def create_knee_corrective(self):
        knee_joint_L = "leg_L0_4_jnt"
        knee_joint_R = "leg_R0_4_jnt"

        for knee_joint in [knee_joint_L,knee_joint_R]:
            mc.select(cl=1)
            support_joint_in = mc.joint(n="{}_support_joint_in".format(knee_joint))
            mc.select(cl=1)
            support_joint_out = mc.joint(n="{}_support_joint_out".format(knee_joint))

            mc.parent(support_joint_out,support_joint_in,knee_joint)
            attribute.reset_SRT(objects=[support_joint_out,support_joint_in])
            mc.setAttr(support_joint_out+".jointOrient",0,0,0,typ="double3")
            mc.setAttr(support_joint_in+".jointOrient",0,0,0,typ="double3")

            pm.setAttr(support_joint_out + ".ty", 4)
            pm.setAttr(support_joint_in + ".ty", -4)

            # create offset group
            mgear.rigbits.addNPO([pm.PyNode(support_joint_in), pm.PyNode(support_joint_out)])

            # create weight driver
            dict_driven = {support_joint_in: -8,
                           support_joint_out: 8}

            for support_joint in dict_driven.keys():
                # create weight driver node
                node_shape = mc.createNode("weightDriver", n="{}_weightDriverShape".format(support_joint))

                node_shape_parent = mc.listRelatives(node_shape, p=1)[0]
                joint_parent = mc.listRelatives(knee_joint, p=1)[0]

                mc.parent(node_shape_parent, joint_parent)

                # mc.rename(node_shape,"{}_weightDriver".format(support_joint))

                # connection and set attribute
                mc.setAttr("{}.type".format(node_shape), 1)
                mc.connectAttr("{}.rz".format(knee_joint), "{}.input[0]".format(node_shape))

                mc.setAttr("{}.poses[0].poseInput[0]".format(node_shape), 0)
                mc.setAttr("{}.poses[0].poseValue[0]".format(node_shape), 0)

                mc.setAttr("{}.poses[1].poseInput[0]".format(node_shape), -90)
                mc.setAttr("{}.poses[1].poseValue[0]".format(node_shape), dict_driven[support_joint])

                mc.connectAttr("{}.output[0]".format(node_shape), "{}.ty".format(support_joint))

    def create_elbow_corrective(self):
        arm_joint_L = "arm_L0_4_jnt"
        arm_joint_R = "arm_R0_4_jnt"

        for arm_joint in [arm_joint_L,arm_joint_R]:
            mc.select(cl=1)
            support_joint_in = mc.joint(n="{}_support_joint_in".format(arm_joint))
            mc.select(cl=1)
            support_joint_out = mc.joint(n="{}_support_joint_out".format(arm_joint))

            mc.parent(support_joint_out,support_joint_in,arm_joint)
            attribute.reset_SRT(objects=[support_joint_out,support_joint_in])
            mc.setAttr(support_joint_out+".jointOrient",0,0,0,typ="double3")
            mc.setAttr(support_joint_in+".jointOrient",0,0,0,typ="double3")

            pm.setAttr(support_joint_out + ".ty", 4)
            pm.setAttr(support_joint_in + ".ty", -4)

            # create offset group
            mgear.rigbits.addNPO([pm.PyNode(support_joint_in), pm.PyNode(support_joint_out)])

            # create weight driver
            dict_driven = {support_joint_in: -8,
                           support_joint_out: 8}

            for support_joint in dict_driven.keys():
                # create weight driver node
                node_shape = mc.createNode("weightDriver", n="{}_weightDriverShape".format(support_joint))

                node_shape_parent = mc.listRelatives(node_shape, p=1)[0]
                joint_parent = mc.listRelatives(arm_joint, p=1)[0]

                mc.parent(node_shape_parent, joint_parent)

                # mc.rename(node_shape,"{}_weightDriver".format(support_joint))

                # connection and set attribute
                mc.setAttr("{}.type".format(node_shape), 1)
                mc.connectAttr("{}.rz".format(arm_joint), "{}.input[0]".format(node_shape))

                mc.setAttr("{}.poses[0].poseInput[0]".format(node_shape), 0)
                mc.setAttr("{}.poses[0].poseValue[0]".format(node_shape), 0)

                mc.setAttr("{}.poses[1].poseInput[0]".format(node_shape), -90)
                mc.setAttr("{}.poses[1].poseValue[0]".format(node_shape), dict_driven[support_joint])

                mc.connectAttr("{}.output[0]".format(node_shape), "{}.ty".format(support_joint))