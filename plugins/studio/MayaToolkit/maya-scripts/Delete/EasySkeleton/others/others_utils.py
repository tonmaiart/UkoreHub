"""
Store all biped utils part of humanoid body

Create by Natchapon Srisuk
"""
import EasySkeleton.utils as utils
import maya.cmds as cmds
import EasySkeleton.config as config
import importlib

importlib.reload(utils)
importlib.reload(config)

from EasySkeleton.config import *

TAB_NAME = "Biped"
MODULE_TYPE = "CLASS"


class Eyelid:
    def __init__(self):
        # declare variables
        self.list_upperLid = []
        self.list_lowerLid = []
        self.jnt_eyeBall = []
        self.ctrl_master = "ctrl_GlobalEyes"
        self.name = ""

        self.attr_blink = "{}.{}Blink".format(self.ctrl_master, self.name)
        self.attr_blink_height = "{}.{}BlinkHeight".format(self.ctrl_master, self.name)

        self._grp_local_still = "{}_{}Still".format(grp, self.name)
        self._grp_local_anim = "{}_{}Anim".format(grp, self.name)
        self._grp_locators = "{}_{}Locator".format(grp, self.name)
        self._grp_eye_curves = "{}_{}Curves".format(grp, self.name)
        self._grp_eye_curves_transform = "{}_{}CurveTransform".format(grp, self.name)

        self._grp_eye_locator_slide = "slideLoc{}_{}".format(grp, self.name)

        self._grp_driver_joints = "{}_{}DrvJnt".format(grp, self.name)
        self._grp_joints_aim = "{}_{}AimJnt".format(grp, self.name)
        self._grp_eyeLidSideCtrl = "{}_{}AllCtrl".format(grp, self.name)

        self._grp_pinOutput = "{}_{}PinOutput".format(grp, self.name)

        self._crv_upperLidHigh = "{}_{}UpLidHigh".format(crv, self.name)
        self._crv_lowerLidHigh = "{}_{}LowLidHigh".format(crv, self.name)

        self._crv_upperLidLow = "{}_{}UpLidLow".format(crv, self.name)
        self._crv_lowerLidLow = "{}_{}LowLidLow".format(crv, self.name)
        self._loc_center = "{}_{}BallCenter".format(loc, self.name)

        self._joints_root_up = []
        self._joint_aim_up = []

        self._joints_root_down = []
        self._joint_aim_down = []

        self._attr_fleshy = "{}.lidFollow".format(self.ctrl_master)

        self.distance = 18

        self.axis_aim = None
        self.axis_up = None
        self.axis_world_up = "y"

    def __create_master_control(self):
        def create_controller():
            utils.create_control(name=self.ctrl_master, axis="z", guide_scale=1, match=self.jnt_eyeBall, parent=self._grp_local_anim)
            # align control position
            cmds.setAttr(self.ctrl_master + ".tx", 0)
            cmds.setAttr(self.ctrl_master + ".tz", self.distance)

            cmds.addAttr(self.ctrl_master, ln="fleshyX", k=1, at="float", min=0, max=1, dv=0.05)
            cmds.addAttr(self.ctrl_master, ln="fleshyY", k=1, at="float", min=0, max=1, dv=0.05)
            cmds.addAttr(self.ctrl_master, ln="fleshyZ", k=1, at="float", min=0, max=1, dv=0.05)

        def create_aim():
            loc_aim_up = "{}_eyeAimUp".format(loc)
            if not cmds.objExists(loc_aim_up):
                grp_offset = cmds.group(em=1, n="grp_eyeAimUp", p=grp_facial_still)

                cmds.spaceLocator(n=loc_aim_up)
                cmds.parent(loc_aim_up, grp_offset)

                cmds.connectAttr("jnt_head" + ".worldMatrix[0]", grp_offset + ".offsetParentMatrix")

            # aim constraints
            aim = utils.get_axis_double3(self.axis_aim)
            up = utils.get_axis_double3(self.axis_up)
            world_up = utils.get_axis_double3(self.axis_world_up)

            cmds.aimConstraint(self.ctrl_master, self.jnt_eyeBall, mo=1, aim=aim, u=up, wu=world_up, wut="objectrotation", wuo=loc_aim_up)

        # create master control and attributes
        if not cmds.objExists(self.ctrl_master):
            create_controller()

        create_aim()

        # cmds.addAttr(self.ctrl_master, ln="blinkL",
        #              k=1, at="float", min=0, max=1)
        # cmds.addAttr(self.ctrl_master, ln="blinkR",
        #              k=1, at="float", min=0, max=1)
        # cmds.addAttr(self.ctrl_master, ln="heightL",
        #              k=1, at="float", min=0, max=10)
        # cmds.addAttr(self.ctrl_master, ln="heightR",
        #              k=1, at="float", min=0, max=10)

        # # create locators
        # loc_eye_aim_up = cmds.spaceLocator(
        #     n=loc + "_eye_aim_upVector")[0]

        # list_eyeBall_joints = [jnt_L_eyeBall, jnt_R_eyeBall]

        # for i, ball in enumerate([guide_L_eyeBall, guide_R_eyeBall]):
        #     # create each controller
        #     ctrl_side = utils.create_control(
        #         node_name=ball.replace("nurbs", ctrl) + "_aimmer", axis="z", guide_scale=1)
        #
        #     pos_x = cmds.xform(list_eyeBall_joints[i], q=1, ws=1, t=1)[0]
        #     pos_y = cmds.xform(ctrl_master, q=1, ws=1, t=1)[1]
        #
        #     cmds.xform(ctrl_side, ws=1, t=(pos_x, pos_y, range))
        #     cmds.parent(ctrl_side, ctrl_master)
        #
        #     # create local locator
        #     loc_local = cmds.spaceLocator(
        #         n=ball.replace("nurbs", loc) + "_local")[0]
        #     cmds.matchTransform(loc_local, list_eyeBall_joints[i])
        #     cmds.parentConstraint(loc_local, list_eyeBall_joints[i])
        #
        #     grp_loc_local = utils.freeze_group([loc_local])[0]
        #
        #     # create aim locator
        #     loc_aim = cmds.spaceLocator(
        #         n=ball.replace("nurbs", loc) + "_aim")[0]
        #     utils.match_parent(loc_aim, ctrl_side)
        #     cmds.aimConstraint(loc_aim, grp_loc_local, mo=1, aim=(0, 0, 1), u=(
        #         0, 1, 0), wut="objectrotation", wu=(0, 1, 0), wuo=loc_eye_aim_up)

    def __create_eyelid_rig(self):
        def create_fleshy():
            list_upperRotGrp = []
            list_lowerRotGrp = []

            for i, joint in enumerate(self.list_upperLid):
                grp_rot_01 = cmds.group(em=1, n=joint.replace(jnt, "grpRot") + "_01")
                grp_rot_02 = cmds.group(em=1, n=joint.replace(jnt, "grpRot") + "_02", p=grp_rot_01)

                cmds.matchTransform(grp_rot_01, self.jnt_eyeBall, pos=1, rot=1)
                cmds.parent(grp_rot_01, self._joints_root_up[i])

                cmds.parent(self._joint_aim_up[i], grp_rot_02)

                list_upperRotGrp.append(grp_rot_02)

            for i, joint in enumerate(self.list_lowerLid):
                grp_rot_01 = cmds.group(em=1, n=joint.replace(jnt, "grpRot") + "_01")
                grp_rot_02 = cmds.group(em=1, n=joint.replace(jnt, "grpRot") + "_02", p=grp_rot_01)

                cmds.matchTransform(grp_rot_01, self.jnt_eyeBall, pos=1, rot=1)
                cmds.parent(grp_rot_01, self._joints_root_down[i])

                cmds.parent(self._joint_aim_down[i], grp_rot_02)

                list_lowerRotGrp.append(grp_rot_02)

            # connect value
            for grp_rot in list_upperRotGrp + list_lowerRotGrp:
                node_floatMath = cmds.createNode("multiplyDivide")

                cmds.connectAttr(self.jnt_eyeBall + ".r", node_floatMath + ".source")
                cmds.connectAttr("{}.{}".format(self.ctrl_master, "fleshyX"), node_floatMath + ".input2X")
                cmds.connectAttr("{}.{}".format(self.ctrl_master, "fleshyY"), node_floatMath + ".input2Y")
                cmds.connectAttr("{}.{}".format(self.ctrl_master, "fleshyZ"), node_floatMath + ".input2Z")

                cmds.connectAttr(node_floatMath + ".output", grp_rot + ".r")

        def aimJoints(name, loc_center, locators, parent, jnt_size=0.01):
            '''
            input loc of center as loc Start , list of lid locs as ls_locEnd
            Args:
            1)suffix
            2)loc_center
            3)locators

            Return:
            1)list of joint aim root
            '''

            joints_root = []
            joints_bind = []
            pos_center = cmds.xform(loc_center, q=1, ws=1, t=1)
            cmds.select(cl=1)

            for index, loc in enumerate(locators):
                no = str(index + 1)
                pos_end = cmds.xform(loc, q=1, ws=1, t=1)
                cmds.select(cl=1)
                jnt_start = cmds.joint(p=pos_center, rad=jnt_size, n="{}_{}{}{}Start".format(jnt, self.name, name, no))
                jnt_end = cmds.joint(p=pos_end, rad=jnt_size, n="{}_{}{}{}End".format(jnt, self.name, name, no))

                cmds.joint(jnt_start, e=1, oj="yxz",
                           secondaryAxisOrient="xup", ch=1, zso=1)
                cmds.aimConstraint(loc, jnt_start, mo=1, weight=1, aimVector=(
                    0, 1, 0), upVector=(0, 0, 1), worldUpType="object", worldUpObject=loc_center)

                cmds.parent(jnt_start, parent)
                joints_root.append(jnt_start)
                joints_bind.append(jnt_end)

            return joints_root, joints_bind

        def create_closet_locators():
            # create output joint
            list_joints_aim = self._joint_aim_up + self._joint_aim_down
            for i in range(len(list_joints_aim)):
                # create bind joint
                jnt_sub_eye = cmds.joint(n=jnt + "{}_{}Eye{}".format(jnt, self.name, (i + 1)), rad=.2)
                self._list_joint_bind_skin.append(jnt_sub_eye)

                node_closestPoint = cmds.shadingNode(
                    "closestPointOnSurface", au=1, n="closetPoint_" + self.name + "_" + str(i + 1).zfill(2))
                node_decomposeMatrix = cmds.shadingNode(
                    "decomposeMatrix", au=1, n="decomposeMatrix_" + self.name + "_" + str(i + 1).zfill(2))

                # create input and output closet locator
                loc_input = cmds.spaceLocator(n="{}_{}ClosetInput{}".format(loc, self.name, i + 1))[0]

                loc_output = cmds.spaceLocator(n="{}_{}ClosetOutput{}".format(loc, self.name, i + 1))[0]

                # parent output to group
                cmds.parent(loc_output, self._grp_eye_locator_slide)

                # parent input to aim joint
                utils.match_parent(loc_input, list_joints_aim[i])

                # convert local input position to world postion
                cmds.connectAttr(
                    loc_input + ".worldMatrix[0]", node_decomposeMatrix + ".inputMatrix")
                cmds.connectAttr(node_decomposeMatrix + ".outputTranslate",
                                 node_closestPoint + ".inPosition")
                # cmds.connectAttr(cmds.listRelatives(guide_eyeBall, c=1, s=1)[
                #                      0] + ".worldSpace[0]", node_closestPoint + ".inputSurface")
                cmds.connectAttr(node_closestPoint + ".position",
                                 loc_output + ".translate")

                cmds.matchTransform(jnt_sub_eye, list_joints_aim[i])
                cmds.parent(jnt_sub_eye, loc_output)

                # constraint joint aim orient to output
                cmds.orientConstraint(list_joints_aim[i], loc_output, mo=1)

        def create_blink_deform():
            # create blendshape and connect node
            crv_blinkHeight = utils.CreateBlendShape(bln_child=[
                self.crv_upperLidLow, self.crv_lowerLidLow], dup_crv=self.crv_lowerLidLow, name=f'{self.name}_blinkHeight',
                attr_height=self.attr_blink_height)

            # create wire and zero offset to up and down curve
            cmds.setAttr(self.attr_blink_height, 10)
            if cmds.getAttr(self.attr_blink_height) == 10:
                crv_UpBlink = cmds.duplicate(
                    self._crv_upperLidHigh, n=f"crv_{self.name}_UpBlink")
                wire_crv_blinkUp = utils.CreateWireCurve(
                    crv_UpBlink, crv_control=crv_blinkHeight, name=f"WR_crv_{self.name}_blinkUp", zeroOffset=1)

            # set attribute height to 10
            cmds.setAttr(self.attr_blink_height, 0)
            if cmds.getAttr(self.attr_blink_height) == 0:
                crv_DownBlink = cmds.duplicate(
                    self._crv_lowerLidHigh, n=f"crv_{self.name}_DownBlink")
                wire_crv_blinkDown = utils.CreateWireCurve(
                    crv_DownBlink, crv_control=crv_blinkHeight, name=f"WR_crv_{self.name}_blinkDown", zeroOffset=1)

            # create blendshape for up,down blink to up,down high
            bln_crv_UpBlink = cmds.blendShape(
                crv_UpBlink, self._crv_upperLidHigh, n=f"BLN_{self.name}_upLidHigh")[0]
            bln_crv_DownBlink = cmds.blendShape(
                crv_DownBlink, self._crv_lowerLidHigh, n=f"BLN_{self.name}_downLidHigh")[0]

            # connect blink attributes to blendshape
            cmds.connectAttr(self.attr_blink, bln_crv_UpBlink + '.weight[0]')
            cmds.connectAttr(self.attr_blink, bln_crv_DownBlink + '.weight[0]')

            # connect size of locator to dropoffDistance of wire deformer
            dcm_node_scale = cmds.createNode(
                'decomposeMatrix', name="dcm_dropoffDistance")
            cmds.connectAttr(self._grp_eyeLidSideCtrl + '.worldMatrix',
                             dcm_node_scale + '.inputMatrix')
            cmds.connectAttr(dcm_node_scale + '.outputScale.outputScaleY',
                             wire_crv_blinkUp + '.dropoffDistance[0]')
            cmds.connectAttr(dcm_node_scale + '.outputScale.outputScaleY',
                             wire_crv_blinkDown + '.dropoffDistance[0]')

            cmds.parent(crv_blinkHeight, self.grp_eye_curves)
            cmds.parent(self.crv_upperLidLow, self.crv_lowerLidLow, self.grp_eye_curves)

        def create_locators():
            # get upper and lower locator
            for i, joint in enumerate(self.list_upperLid):
                locator = list_upper_locator[i]
                cmds.spaceLocator(n=locator)
                cmds.matchTransform(locator, joint)
                cmds.parent(locator, self.grp_locators)

            for i, joint in enumerate(self.list_lowerLid):
                locator = list_lower_locator[i]
                cmds.spaceLocator(n=locator)
                cmds.matchTransform(locator, joint)
                cmds.parent(locator, self.grp_locators)

            # ball center locator
            cmds.spaceLocator(n=self.loc_center)
            cmds.matchTransform(self.loc_center, self.jnt_eyeBall)
            cmds.parent(self.loc_center, self._grp_local_anim)

        def create_curves():
            # create high curve and pin
            utils.draw_curve(list_upper_locator, self._crv_upperLidHigh, parent=self._grp_eye_curves_transform, d=1, rebuild=0)
            utils.draw_curve([list_upper_locator[0]] + list_lower_locator + [list_upper_locator[-1]], self._crv_lowerLidHigh,
                             parent=self._grp_eye_curves_transform, d=1,
                             rebuild=0)

            utils.draw_curve(list_upper_locator, self.crv_upperLidLow, parent=self._grp_eye_curves_transform, d=1, rebuild=1, rd=3)
            utils.draw_curve([list_upper_locator[0]] + list_lower_locator + [list_upper_locator[-1]], self.crv_lowerLidLow,
                             parent=self._grp_eye_curves_transform, d=1, rebuild=1, rd=3)

            utils.pin_curve_by_distance(list_pin=list_upper_locator, source=self._crv_upperLidHigh,
                                  name="upperLidHigh",
                                  maintainOffset=False,
                                  parent=self._grp_pinOutput, typ="curve")
            utils.pin_curve_by_distance(list_pin=list_lower_locator, source=self._crv_lowerLidHigh,
                                  name="lowerLidHigh",
                                  maintainOffset=False,
                                  parent=self._grp_pinOutput, typ="curve")

            # create wire deformer for up and down curve
            ls_wireUp = utils.CreateWireCurve(crv_control=self.crv_lowerLidLow,
                                              crv_target=self._crv_lowerLidHigh, name="WR_{}_downLidHigh".format(self.name))
            ls_wireDown = utils.CreateWireCurve(
                crv_control=self.crv_upperLidLow, crv_target=self._crv_upperLidHigh, name="WR_{}_upLidHigh".format(self.name))

            # create blink deform
            create_blink_deform()

        def create_joint_aim():
            # create joint and aim joint to locators
            self._joints_root_up, self._joint_aim_up = aimJoints(
                loc_center=self.loc_center, locators=list_upper_locator, jnt_size=1, name="upper", parent=self._grp_joints_aim)
            self._joints_root_down, self._joint_aim_down = aimJoints(
                loc_center=self.loc_center, locators=list_lower_locator, jnt_size=1, name="lower", parent=self._grp_joints_aim)

        def create_controller():
            # create driver joint
            list_upperLidDrvJnt = []
            list_lowerLidDrvJnt = []

            for i in range(5):
                cmds.select(cl=1)
                joint = cmds.joint(n="{}_upDrv{}{}".format(jnt, self.name, i + 1), rad=1.5)
                utils.snap_to_curve_by_param(source=self.crv_upperLidLow, object=joint, param=i * (1 / 4), turn_on_percentage=True)
                list_upperLidDrvJnt.append(joint)
            count = 0
            for i in range(1, 4):
                cmds.select(cl=1)
                joint = cmds.joint(n="{}_lowDrv{}{}".format(jnt, self.name, count + 1), rad=1.5)
                utils.snap_to_curve_by_param(source=self.crv_lowerLidLow, object=joint, param=i * (1 / 4), turn_on_percentage=True)
                count += 1
                list_lowerLidDrvJnt.append(joint)
            cmds.parent(list_upperLidDrvJnt, list_lowerLidDrvJnt, self._grp_driver_joints)

            cmds.skinCluster(list_upperLidDrvJnt, self.crv_upperLidLow, ih=1, dr=5, bm=3, mi=2)
            cmds.skinCluster([list_upperLidDrvJnt[0]] + list_lowerLidDrvJnt + [list_upperLidDrvJnt[-1]], self.crv_lowerLidLow,
                             ih=1, dr=5, bm=3, mi=2)

            # create controller and finalize constraints
            grp_mainCtrl = cmds.group(em=1, n="{}_{}Main".format(grpCtrl, self.name), p=self._grp_eyeLidSideCtrl)

            list_upperCtrl = [utils.create_control(name=joint.replace(jnt, ctrl), match=joint, parent=grp_mainCtrl,
                                                   constraint="parent") for joint in list_upperLidDrvJnt]
            list_lowerCtrl = [utils.create_control(name=joint.replace(jnt, ctrl), match=joint, parent=grp_mainCtrl,
                                                   constraint="parent") for joint in list_lowerLidDrvJnt]

            utils.freeze_group(list_upperCtrl + list_lowerCtrl, prefix="grpCtrl")

            cmds.parentConstraint(list_upperCtrl[0], list_upperCtrl[2], cmds.listRelatives(list_upperCtrl[1], p=1)[0], mo=1)
            cmds.parentConstraint(list_upperCtrl[2], list_upperCtrl[4], cmds.listRelatives(list_upperCtrl[3], p=1)[0], mo=1)

            cmds.parentConstraint(list_upperCtrl[0], list_lowerCtrl[1], cmds.listRelatives(list_lowerCtrl[0], p=1)[0], mo=1)
            cmds.parentConstraint(list_upperCtrl[4], list_lowerCtrl[1], cmds.listRelatives(list_lowerCtrl[2], p=1)[0], mo=1)

        def apply_to_bind_joints():
            # apply to joints
            for i, joint in enumerate(self._joint_aim_up):
                cmds.parentConstraint(joint, self.list_upperLid[i], mo=1)
            for i, joint in enumerate(self._joint_aim_down):
                cmds.parentConstraint(joint, self.list_lowerLid[i], mo=1)

        def create_attributes():
            cmds.addAttr(self.attr_blink.split(".")[0], ln=self.attr_blink.split(".")[1], at="float", min=0, max=1, k=1)
            cmds.addAttr(self.attr_blink_height.split(".")[0], ln=self.attr_blink_height.split(".")[1], at="float", min=0, max=10, k=1)

        # declare variables
        list_upper_locator = [self.list_upperLid[i].replace(jnt, loc) for i in range(len(self.list_upperLid))]
        list_lower_locator = [self.list_lowerLid[i].replace(jnt, loc) for i in range(len(self.list_lowerLid))]

        # create locators
        create_attributes()
        create_locators()
        create_joint_aim()
        create_curves()
        create_controller()
        create_fleshy()
        apply_to_bind_joints()

    def __create_hierarchy(self):
        cmds.group(em=1, n=self._grp_local_still, p=grp_facial_still)
        cmds.group(em=1, n=self.grp_locators, p=self._grp_local_still)
        cmds.group(em=1, n=self._grp_eye_locator_slide, p=self._grp_local_still)
        cmds.group(em=1, n=self._grp_pinOutput, p=self._grp_local_still)
        cmds.group(em=1, n=self.grp_eye_curves, p=self._grp_local_still)

        cmds.group(em=1, n=self._grp_local_anim, p=grp_facial_anim)
        cmds.group(em=1, n=self._grp_eyeLidSideCtrl, p=self._grp_local_anim)
        cmds.group(em=1, n=self._grp_joints_aim, p=self._grp_eyeLidSideCtrl)
        cmds.group(em=1, n=self._grp_eye_curves_transform, p=self._grp_eyeLidSideCtrl)
        cmds.group(em=1, n=self._grp_driver_joints, p=self._grp_eyeLidSideCtrl)

    def build(self):
        # create control master and global eye system
        self.__create_hierarchy()
        self.__create_master_control()
        self.__create_eyelid_rig()

    def connect(self, object):
        cmds.parentConstraint(object, self._grp_local_anim, mo=1)

        def add_ribbon_function():
            def create_ribbon():
                # create ribbon plane (upper,lower) reference scale from limb joints
                width_up = utils.get_distance_two(self.list_limb_joint[0], self.list_limb_joint[1])
                width_low = utils.get_distance_two(self.list_limb_joint[1], self.list_limb_joint[2])

                cmds.nurbsPlane(w=width_up, lr=0.05, u=4, v=1, d=3, ax=(0, 0, 1), ch=0, n=rbn_upper)
                cmds.nurbsPlane(w=width_low, lr=0.05, u=4, v=1, d=3, ax=(0, 0, 1), ch=0, n=rbn_lower)

                # reposition for deformer
                utils.match_bounding_box(rbn_lower, rbn_upper)
                cmds.makeIdentity(rbn_lower, s=1, a=1)
                cmds.move(width_up, rbn_lower, x=1, r=1)
                cmds.parent(rbn_upper, rbn_lower, grp_ribbon_still)

            def add_ribbon_deform():
                list_both_twist = []
                list_both_sine = []
                list_blendshape = []

                for ribbon in [rbn_upper, rbn_lower]:
                    if ribbon == rbn_upper:
                        keyname = "Upper"
                    elif ribbon == rbn_lower:
                        keyname = "Lower"

                    twist = cmds.duplicate(ribbon, name=ribbon + "Twist")[0]
                    sine = cmds.duplicate(ribbon, name=ribbon + "Sine")[0]

                    list_both_sine.append(sine)
                    list_both_twist.append(twist)

                    blendshape = cmds.blendShape(twist, sine, ribbon, n="bshp_{}{}Rbn".format(self.name, keyname))[0]
                    list_blendshape.append(blendshape)

                cmds.select(list_both_sine)
                sine_name = "sine_{}".format(self.name)
                sine_handle = cmds.nonLinear(typ="sine", n=sine_name)[1]
                cmds.parent(sine_handle, grp_ribbon_still)

                cmds.rotate(90, sine_handle, z=1, r=1)
                cmds.setAttr(sine_name + ".dropoff", 1)

                utils.add_attribute_divider(ctrl_option, "Sine")
                cmds.addAttr(ctrl_option, ln=attr_sine_enable.split(".")[1], at="float", min=0, max=1, k=1)
                cmds.addAttr(ctrl_option, ln=attr_sine_animation.split(".")[1], at="float", k=1)
                cmds.addAttr(ctrl_option, ln=attr_sine_width.split(".")[1], at="float", k=1, dv=0.4)
                cmds.addAttr(ctrl_option, ln=attr_sine_length.split(".")[1], at="float", k=1, dv=1.5)
                cmds.addAttr(ctrl_option, ln=attr_sine_orient.split(".")[1], at="float", k=1)

                cmds.connectAttr(attr_sine_enable, sine_name + ".envelope")

                cmds.connectAttr(attr_sine_enable, list_blendshape[0] + "." + list_both_sine[0])
                cmds.connectAttr(attr_sine_enable, list_blendshape[1] + "." + list_both_sine[1])

                cmds.connectAttr(attr_sine_width, sine_name + ".amplitude")
                cmds.connectAttr(attr_sine_length, sine_name + ".wavelength")
                cmds.connectAttr(attr_sine_animation, sine_name + ".offset")
                cmds.connectAttr(attr_sine_orient, sine_handle + ".ry")

            def create_detail_control():
                for i in range(10):
                    joint = list_ribbon_joint[i]
                    control_name = list_detail_control[i]
                    locator_name = list_detail_locator[i]

                    utils.create_control(name=control_name, match=joint, parent=grp_detailCtrl)
                    cmds.spaceLocator(n=locator_name)
                    utils.match_parent(locator_name, control_name)

            def create_follicles():
                count = 0
                for i in range(10):
                    ribbon = rbn_lower if i > 4 else rbn_upper
                    print("target ribbon : ", ribbon)
                    follicle_name = list_follicle[i]
                    grp_offset_name = list_flc_offset[i]

                    cmds.group(n=grp_offset_name, em=1)

                    utils.snap_to_surface(ribbon, grp_offset_name, u=(1 / (self.ribbon_division - 1)) * count, v=0.5)

                    cmds.matchTransform(grp_offset_name, list_drvJnt_upper, rot=1)

                    utils.pin_ribbon(list_pin=[grp_offset_name], surface=ribbon, output_parent=grp_detailCtrl, name=follicle_name)
                    utils.match_parent(grp_offset_name, follicle_name)

                    count += 1
                    count = 0 if count == 5 else count

            def parent_detail_controls():
                # create detail controls
                for i in range(10):
                    control = list_detail_control[i]
                    grp_flc_offset = list_flc_offset[i]

                    cmds.parent(control, grp_flc_offset)

                utils.freeze_group_classic(list_detail_control, grpCtrl)

            def create_bend_joints(part=None, ribbon=None):
                def match_joint():
                    if part == "Upper":
                        target_match = self.list_limb_joint[0]
                    elif part == "Lower":
                        target_match = self.list_limb_joint[1]

                    cmds.select(cl=1)
                    jnt_ref = cmds.joint()

                    cmds.select(cl=1)
                    jnt_forward = cmds.joint()
                    cmds.xform(jnt_forward, ws=1, t=(1, 0, 0))

                    cmds.select(cl=1)
                    jnt_pole = cmds.joint()
                    cmds.xform(jnt_pole, ws=1, t=(0, 0, 1))
                    constraint = cmds.aimConstraint(jnt_forward, jnt_ref, aim=utils.get_axis_double3(self.axis_forward), u=utils.get_axis_double3(self.axis_pole), wut="object", wuo=jnt_pole)
                    cmds.delete(constraint)
                    cmds.makeIdentity(jnt_ref, a=1, r=1)

                    joint_orient_axis = cmds.getAttr("{}.jointOrient".format(jnt_ref))[0]

                    cmds.delete(jnt_ref, jnt_forward, jnt_pole)
                    return joint_orient_axis

                # create ribbon driver joints
                list_name = ["Start", "Mid", "End"]
                list_drive_joint = []
                list_axis_orient = match_joint()

                # create joint ref
                for i, name in enumerate(list_name):
                    cmds.select(cl=1)
                    joint = cmds.joint(n="{}_{}{}{}".format(jnt, self.name, part, name), rad=1.5)
                    utils.snap_to_surface(ribbon, joint, v=0.5, u=(1 / 2) * i, snap="point")

                    cmds.setAttr("{}.jointOrient".format(joint), list_axis_orient[0], list_axis_orient[1], list_axis_orient[2], typ="double3")

                    list_drive_joint.append(joint)

                return list_drive_joint

            def create_bend_groups():
                def create_corner_path():
                    utils.create_control(name=ctrl_cornerRbn,
                                         match=self.list_limb_joint[1],
                                         parent=grp_bend_mid)
                    grp_ctrl_cornerRbn = utils.freeze_group_classic([ctrl_cornerRbn], grpCtrl)
                    cmds.pointConstraint(self.list_limb_joint[1], grp_ctrl_cornerRbn)
                    cmds.orientConstraint(self.list_limb_joint[0], grp_ctrl_cornerRbn)

                    # create group inside ctrl
                    utils.match_parent(cmds.spaceLocator(n=loc_ctrl_corner)[0], ctrl_cornerRbn)
                    utils.match_parent(cmds.spaceLocator(n=loc_aim_upRot)[0], ctrl_cornerRbn)

                def match_part(typ):
                    if typ == "Upper":
                        start_drive = self.list_limb_joint[0]
                        end_drive = loc_ctrl_corner
                        invert = 1
                        parent = grp_bend_up
                        list_driver = list_drvJnt_upper
                    elif typ == "Lower":
                        start_drive = loc_ctrl_corner
                        end_drive = self.list_limb_joint[2]
                        invert = -1
                        parent = grp_bend_low
                        list_driver = list_drvJnt_lower

                    else:
                        raise Exception("Invalid Input")

                    invert_axis = 1 if self.axis_forward != axis_forward_abs else 1
                    dict_vector_aim = {"x": (1 * invert * invert_axis, 0, 0),
                                       "y": (0, 1 * invert * invert_axis, 0),
                                       "z": (0, 0, 1 * invert * invert_axis)
                                       }
                    dict_vector_up = {"x": (1 * invert * invert_axis, 0, 0),
                                      "y": (0, 1 * invert * invert_axis, 0),
                                      "z": (0, 0, 1 * invert * invert_axis)
                                      }
                    dict_vector_world_up = {"x": (1 * invert, 0, 0),
                                            "y": (0, 1 * invert, 0),
                                            "z": (0, 0, 1 * invert)
                                            }

                    # match all joint driver to group
                    [utils.match_parent(joint, parent) for joint in list_driver]

                    list_grp_aim = utils.freeze_group_classic(list_driver, "grpAim")
                    list_grp_point = utils.freeze_group_classic(list_grp_aim, "grpPoint")

                    # match position
                    cmds.pointConstraint(start_drive, list_grp_point[0])
                    cmds.pointConstraint(end_drive, list_grp_point[2])
                    cmds.pointConstraint(start_drive, end_drive, list_grp_point[1])

                    # aim start and end to mid
                    cmds.aimConstraint(list_driver[1],
                                       list_grp_aim[0],
                                       aim=utils.get_axis_double3(self.axis_forward),
                                       u=utils.get_axis_double3(self.axis_pole),
                                       wu=utils.get_axis_double3(self.axis_pole),
                                       wut="objectrotation",
                                       wuo=list_grp_point[0])
                    cmds.aimConstraint(list_driver[1],
                                       list_grp_aim[2],
                                       aim=[value * -1 for value in utils.get_axis_double3(self.axis_forward)],
                                       u=utils.get_axis_double3(self.axis_pole),
                                       wu=utils.get_axis_double3(self.axis_pole),
                                       wut="objectrotation",
                                       wuo=list_grp_point[2])

                    # aim mid
                    aim_invert = 1 if typ == "Upper" else -1
                    cmds.aimConstraint(loc_ctrl_corner,
                                       list_grp_aim[1],
                                       aim=[value * aim_invert for value in utils.get_axis_double3(self.axis_forward)],
                                       u=utils.get_axis_double3(self.axis_pole),
                                       wu=utils.get_axis_double3(self.axis_pole),
                                       wut="objectrotation",
                                       wuo=list_grp_point[1])

                grp_bend_up = cmds.group(em=1, n="{}_{}BendUp".format(grp, self.name), p=grp_bendCtrl)
                grp_bend_mid = cmds.group(em=1, n="{}_{}BendMid".format(grp, self.name), p=grp_bendCtrl)
                grp_bend_low = cmds.group(em=1, n="{}_{}BendLow".format(grp, self.name), p=grp_bendCtrl)

                create_corner_path()

                # match and constraint bendlow and bend up group
                cmds.matchTransform(grp_bend_low, self.list_limb_joint[1], pos=1)
                cmds.matchTransform(grp_bend_up, self.list_limb_joint[0], pos=1)

                constraint = cmds.aimConstraint(self.list_limb_joint[1],
                                                grp_bend_up,
                                                aim=utils.get_axis_double3(self.axis_forward),
                                                u=utils.get_axis_double3(axis_pole_abs),
                                                wu=utils.get_axis_double3(axis_pole_abs),
                                                wut="objectrotation",
                                                wuo=self.list_limb_joint[0])
                cmds.delete(constraint)

                constraint = cmds.aimConstraint(self.list_limb_joint[2],
                                                grp_bend_low,
                                                aim=utils.get_axis_double3(self.axis_forward),
                                                u=utils.get_axis_double3(axis_pole_abs),
                                                wu=utils.get_axis_double3(axis_pole_abs),
                                                wut="objectrotation",
                                                wuo=self.list_limb_joint[1])
                cmds.delete(constraint)

                cmds.parentConstraint(self.list_limb_joint[0], grp_bend_up, mo=1)
                cmds.parentConstraint(self.list_limb_joint[1], grp_bend_low, mo=1)

                match_part("Upper")
                match_part("Lower")

            def apply_joint_scale():

                def apply_scale(bend_control, list_detail_control, list_detail_joint):
                    for i, control in enumerate(list_detail_control):
                        # fix scale control size
                        # grp_scale = utils.freeze_group_classic(control, "grpScl")[0]
                        # cmds.connectAttr(grp_get_scale + ".s", grp_scale + ".s")

                        node_pma_add = cmds.createNode("plusMinusAverage", n="{}_bendUpSum_pma".format(self.name))
                        cmds.connectAttr("{}.scale".format(control), "{}.input3D[0]".format(node_pma_add))
                        cmds.connectAttr("{}.scale".format(bend_control), "{}.input3D[1]".format(node_pma_add))

                        node_pma_minus = cmds.createNode("plusMinusAverage", n="{}_bendUpOffset_pma".format(self.name))
                        cmds.setAttr("{}.operation".format(node_pma_minus), 2)
                        cmds.connectAttr("{}.output3D".format(node_pma_add), "{}.input3D[0]".format(node_pma_minus))
                        cmds.setAttr("{}.input3D[1]".format(node_pma_minus), 1, 1, 1, typ="double3")

                        # connect to ribbon joint
                        cmds.connectAttr("{}.output3D".format(node_pma_minus), "{}.scale".format(list_detail_joint[i]))

                apply_scale(list_up_bend_control[1], list_detail_up_control, self.joints_up_ribbon)
                apply_scale(list_low_bend_control[1], list_detail_low_control, self.joints_low_ribbon)

                grp_get_scale = cmds.group(em=1, n="{}_scaleSpace_grp".format(self.name), p=grp_detailCtrl)
                cmds.scaleConstraint(self.grp_local_anim, grp_get_scale)

                for follicle in list_follicle:
                    grp_scale_output = cmds.group(em=1, n="{}_scaleFix_grp".format(follicle))

                    cmds.matchTransform(grp_scale_output, grp_get_scale, rot=1)
                    cmds.matchTransform(grp_scale_output, follicle, pos=1)

                    [cmds.parent(child, grp_scale_output) for child in cmds.listRelatives(follicle, c=1, typ="transform")]

                    cmds.parent(grp_scale_output, follicle)

                    cmds.connectAttr(grp_get_scale + ".s", grp_scale_output + ".s")

            def create_bend_controls():
                for i, joint in enumerate(list_drvJnt_upper + list_drvJnt_lower):

                    control = (list_up_bend_control + list_low_bend_control)[i]

                    # insert controller
                    parent_joint = cmds.listRelatives(joint, p=1, typ="transform")
                    if parent_joint:
                        parent_joint = parent_joint[0]
                    else:
                        continue

                    utils.create_control(name=control, match=joint, parent=parent_joint)

                    loc_joint = cmds.spaceLocator(n="{}_{}".format(joint, loc))[0]
                    utils.match_parent(loc_joint, parent_joint)

                    cmds.parent(joint, loc_joint)

                    if i != 1 and i != 4:
                        cmds.setAttr(control + ".v", 0)

                    # controller connection
                    cmds.connectAttr(control + ".t", loc_joint + ".t")
                    cmds.connectAttr(control + ".r", loc_joint + ".r")

            def apply_joint_constraint():
                for i in range(10):
                    locator = list_detail_locator[i]
                    joint = list_ribbon_joint[i]

                    cmds.parentConstraint(locator, joint)

            def create_hierarchy():
                # create ribbon grp hierarchy
                cmds.group(em=1, n=grp_ribbon_still, p=self.grp_local_still)

                cmds.group(em=1, n=grp_ribbon_controls, p=self.grp_local_anim)

                cmds.group(em=1, n=grp_bendCtrl, p=grp_ribbon_controls)
                cmds.group(em=1, n=grp_detailCtrl, p=grp_ribbon_controls)

                cmds.setAttr(grp_detailCtrl + ".inheritsTransform", 0)

                # create attributes
                cmds.addAttr(attr_sub_control.split(".")[0], ln=attr_sub_control.split(".")[1], at="enum",
                             en="Hide:Show", k=1, dv=1)
                cmds.addAttr(attr_detail_control.split(".")[0], ln=attr_detail_control.split(".")[1], at="enum",
                             en="Hide:Show", k=1, dv=1)

                # connect attributes
                cmds.connectAttr(attr_sub_control, grp_bendCtrl + ".v")
                cmds.connectAttr(attr_detail_control, grp_detailCtrl + ".v")

            def finalize():
                for control in list_up_bend_control + list_low_bend_control:
                    cmds.setAttr(control + ".s{}".format(axis_forward_abs), l=1, k=0)
                    utils.lock_attributes(control, v=1, l=1, k=0)

                for control in list_detail_control:
                    utils.lock_attributes(control, v=1, l=1, k=0)

                utils.lock_attributes(ctrl_cornerRbn, v=1, r=1, s=1, l=1, k=0)

            # error handle
            if len(self.joints_up_ribbon) != len(self.joints_up_ribbon):
                raise Exception("Input Ribbon Joint Up and Low must Match Count")
            elif len(self.joints_up_ribbon) != self.ribbon_division or len(self.joints_low_ribbon) != self.ribbon_division:
                raise Exception("Input Ribbon Joint Up and Low must Match to ribbon division value")

            # global variables
            ctrl_cornerRbn = "{}_{}Rbn".format(ctrl, self.name)
            loc_aim_upRot = "{}_{}AimUpRot".format(loc, self.name)
            loc_ctrl_corner = "{}_{}CornerRbn".format(loc, self.name)
            list_ribbon_joint = self.joints_up_ribbon + self.joints_low_ribbon

            grp_ribbon_controls = "{}_{}Ribbon".format(grp, self.name)
            grp_ribbon_still = "{}_{}RbnNoTransform".format(grp, self.name)

            grp_bendCtrl = "{}_{}BendCtrl".format(grp, self.name)
            grp_detailCtrl = "{}_{}DetailCtrl".format(grp, self.name)

            list_detail_locator = ["{}_{}".format(loc, joint) for joint in list_ribbon_joint]
            list_detail_control = ["{}_{}".format(ctrl, joint) for joint in list_ribbon_joint]
            list_detail_up_control = ["{}_{}".format(ctrl, joint) for joint in self.joints_up_ribbon]
            list_detail_low_control = ["{}_{}".format(ctrl, joint) for joint in self.joints_low_ribbon]

            list_follicle = ["{}_{}Pin".format(flc, joint) for joint in list_ribbon_joint]
            list_flc_offset = ["{}_{}Pin".format(grp, joint) for joint in list_ribbon_joint]
            list_up_bend_control = ["{}_bendUp{}_{}".format(self.name, i + 1, ctrl) for i in range(3)]
            list_low_bend_control = ["{}_bendLow{}_{}".format(self.name, i + 1, ctrl) for i in range(3)]

            # create ribbon plane and snap to limb
            create_hierarchy()
            create_ribbon()
            add_ribbon_deform() if self.ribbon_sine_attribute else None

            # create driver joints
            list_drvJnt_upper = create_bend_joints(part="Upper", ribbon=rbn_upper)
            list_drvJnt_lower = create_bend_joints(part="Lower", ribbon=rbn_lower)

            # create sub control
            create_detail_control()
            create_follicles()

            # bind skin ribbon plane
            cmds.skinCluster(list_drvJnt_upper, rbn_upper, ih=1, mi=2, bm=1, dr=8,
                             n="skinCluster_{}{}Rbn".format(self.name, "Up"))
            cmds.skinCluster(list_drvJnt_lower, rbn_lower, ih=1, mi=2, bm=1, dr=8,
                             n="skinCluster_{}{}Rbn".format(self.name, "Low"))

            create_bend_groups()

            parent_detail_controls()

            create_bend_controls()

            # assign twist system
            if self.is_ribbon_up_twist:
                rotate_order = cmds.getAttr("{}.rotateOrder".format(self.list_limb_joint[0]))
                print("rotate order : ", rotate_order)

                # create grp freeze and parent constraint
                grp_freeze = cmds.group(em=1, n="{}_upTwistFreeze_grp".format(self.name), p=self.grp_local_still)
                cmds.setAttr("{}.rotateOrder".format(grp_freeze), rotate_order)
                cmds.parentConstraint(self.list_limb_joint[0], grp_freeze)

                # create grp freeze offset in grp freeze invert
                grp_freeze_offset = utils.freeze_group_classic(grp_freeze, "grp")[0]
                grp_freeze_invert = cmds.group(em=1, n="{}_upTwistFreezeInvert_grp".format(self.name), p=grp_freeze_offset)
                cmds.setAttr("{}.rotateOrder".format(grp_freeze_invert), rotate_order)

                # connection to invert grp freeze invert
                node_mdl = cmds.createNode("multDoubleLinear", n="{}_upTwistInvert".format(self.name))
                cmds.connectAttr("{}.r{}".format(grp_freeze, axis_forward_abs), "{}.input1".format(node_mdl))
                cmds.setAttr("{}.input2".format(node_mdl), -1)
                cmds.connectAttr("{}.output".format(node_mdl), "{}.r{}".format(grp_freeze_invert, axis_forward_abs))

                # connection of twist chain
                list_twist = utils.freeze_group_classic([control for control in list_detail_control[0:5]], "grpTwist")

                utils.create_twist_chain(list_twist=list_twist,
                                         end_target=grp_freeze_invert,
                                         axis=axis_forward_abs,
                                         invert=False,
                                         invert_list_twist=True)

            if self.is_ribbon_low_twist:
                list_twist = utils.freeze_group_classic([control for control in list_detail_control[5:10]], "grpTwist")

                # invert = True if self.axis_forward_abs != self.axis_forward else False

                utils.create_twist_chain(list_twist=list_twist,
                                         end_target=self.list_limb_joint[2],
                                         axis=axis_forward_abs,
                                         invert=False)

            # apply output to ribbon joints
            apply_joint_constraint()
            apply_joint_scale()

            # lock and hide control
            finalize()


class Torso:
    """
    Create a torso rig by reference from bind joints
    """

    def __init__(self):
        self.module_enable = True
        self.blank_1 = "blank"

        self.name = "torso"
        self.primary_axis = "y"
        self.jnt_pelvis = ""
        self.list_joint_spine = []
        self.jnt_chest = ""
        self.jnt_cog = ""

    def generate_variables(self):
        # declare variables
        self.grp_local_still = "{}_{}Still".format(grp, self.name)
        self.grp_local_anim = "{}_{}Anim".format(grp, self.name)
        self.grp_local_rig = "{}_{}Rig".format(grp, self.name)

        self.list_ik_control = []
        self.list_fk_control = []
        self.list_ik_driver_joints = []
        self.list_fk_driver_joints = []
        self.list_ik_surface_pin = []
        self.list_fk_surface_pin = []
        self.ribbon_torso_fk = "{}_{}Fk".format(nrb, self.name)
        self.ribbon_torso_ik = "{}_{}Ik".format(nrb, self.name)

        self.ctrl_cog = "{}_cog".format(ctrl)
        self.ctrl_pelvis = "{}_pelvis".format(ctrl)
        self.squash_axis = ["x", "y", "z"]
        self.squash_axis.remove(self.primary_axis.replace("-", ""))

    def create_ribbon(self):
        # create ribbon and match ribbon to spine
        list_torso_ribbon = [self.jnt_pelvis] + self.list_joint_spine + [self.jnt_chest]
        width = utils.get_distance_two(list_torso_ribbon)

        # utils.draw_ribbon(list_torso_ribbon, rebuild=False, node_name=self.ribbon_torso_fk, d=3, su=1,
        #                   sv=len(list_torso_ribbon), du=1, dv=3,
        #                   parent=self.grp_local_still, loftDegree=3)

        utils.draw_nurbs(list_torso_ribbon, rebuild=False, name=self.ribbon_torso_ik, d=3, su=1,
                         sv=len(list_torso_ribbon), du=1, dv=3,
                         parent=self.grp_local_still, loftDegree=3)

    def create_hierarchy(self):
        cmds.group(n=self.grp_local_rig, em=1, p=grp_anim)

        cmds.group(n=self.grp_local_anim, em=1, p=self.grp_local_rig)
        cmds.group(n=self.grp_local_still, em=1, p=self.grp_local_rig)
        cmds.setAttr(self.grp_local_still + ".inheritsTransform", 0)

    def create_fk_driver(self):
        # create fk driver joint and match to ribbon
        amount_driver = 4
        grp_joint_driver = cmds.group(em=1, n="{}_driverFk".format(grp),
                                      p=self.grp_local_still)  # driver joints container

        for i in range(amount_driver):  # create driver joint and match position to skin joint
            cmds.select(cl=1)
            jnt_driver = cmds.joint(n="{}_spineFkDrv{}".format(jnt, str(i + 1)), rad=1.5)
            param = (i * (1 / (amount_driver - 1)), 0.5)
            utils.snap_to_curve_by_param(source=self.ribbon_torso_fk, object=jnt_driver, param=param,
                                         typ="surface")
            cmds.parent(jnt_driver, grp_joint_driver)

            cmds.connectAttr(ctrl_main + ".s", jnt_driver + ".s")  # connect scale
            self.list_fk_driver_joints.append(jnt_driver)

        # bind driver joints to control fk ribbon
        cmds.skinCluster(self.list_fk_driver_joints, self.ribbon_torso_fk, n="skinCluster_spineFk", mi=2, ih=1, tsb=1,
                         dr=10)

        cmds.connectAttr(ctrl_main + ".s", grp_joint_driver + ".s")

    def create_fk_controls(self):
        # create controller
        grp_controller = cmds.group(em=1, n="{}_{}FkCtl".format(grp, self.name), p=self.ctrl_cog)
        recent_ctrl = None

        # create fk controller and constraint to joint drivers
        amount_joint_spine = len(self.list_joint_spine)

        for i in range(1, 4):
            jnt_driver = self.list_fk_driver_joints[i]
            control = utils.create_control(name=self.list_joint_spine[i].replace(jnt, ctrl) + "Fk", match=jnt_driver,
                                           parent=grp_controller)

            if recent_ctrl:
                cmds.parent(control, recent_ctrl)

            recent_ctrl = control

            cmds.parentConstraint(control, jnt_driver, mo=1)
            self.list_fk_control.append(control)

            if i == 3:  # constraint orient to tip for chest fk
                cmds.orientConstraint(control, self.list_fk_surface_pin[1])

        utils.freeze_group(self.list_fk_control, prefix=grpCtrl)

        # constraint ctrl spine 1 to ik joint driver
        cmds.parentConstraint(self.ctrl_pelvis, self.list_fk_driver_joints[0], mo=1)

    def apply_fk_output(self):
        # prepare
        grp_pin_output = cmds.group(em=1, n="{}_spineFkPinOutput".format(grp), p=self.grp_local_still)
        list_target_control = self.list_ik_control

        # create pin group output to fk ribbon ( reference from ik position )
        for i, ctrl_target in enumerate(list_target_control):
            grp_pin = cmds.group(em=1, n="{}_fkSurfacePin{}".format(grp, str(i + 1).zfill(2)), p=grp_pin_output)
            cmds.matchTransform(grp_pin, ctrl_target)

            self.list_fk_surface_pin.append(grp_pin)

            cmds.connectAttr(ctrl_main + ".s", grp_pin + ".s")  # connect scale pin group scale

        utils.pin_curve_by_distance(self.list_fk_surface_pin, source=self.ribbon_torso_fk, typ="surface",
                                    maintainOffset=False, name="fkSurface")

        # constraint grp pin to ik offset group
        for i, grp_pin in enumerate(self.list_fk_surface_pin):
            ctrl_target = list_target_control[i]

            grp_offset = utils.freeze_group([ctrl_target], prefix=grpPin)[0]

            cmds.parentConstraint(grp_pin, grp_offset, mo=1)

    def create_ik_driver(self):
        # drive ik curve by ik driver joints and controller
        grp_joints_driver = cmds.group(em=1, n="{}_spineIkDrv".format(grp), p=self.grp_local_still)

        # create joint driver
        for i in range(3):
            cmds.select(cl=1)
            jnt_driver = cmds.joint(n="{}_spineIkDrv{}".format(jnt, str(i + 1), ))
            cmds.parent(jnt_driver, grp_joints_driver)

            utils.snap_to_curve_by_param(object=jnt_driver, source=self.ribbon_torso_ik, param=[i * (1 / (3 - 1)), 0.5],
                                         typ="surface")

            cmds.connectAttr(ctrl_main + ".s", jnt_driver + ".s")
            self.list_ik_driver_joints.append(jnt_driver)

        # skin cluster driver joints to ribbon torso
        cmds.skinCluster(self.list_ik_driver_joints, self.ribbon_torso_ik, mi=2, ih=1, tsb=1, dr=10, bm=0)

    def apply_ik_joints(self):
        grp_pin = cmds.group(em=1, n="{}_spineIkPinOutput".format(grp), p=self.grp_local_still)
        list_joint_spine = [self.jnt_pelvis] + self.list_joint_spine + [self.jnt_chest]

        # create pin group of ribbon torso ik
        self.list_ik_surface_pin.extend(
            utils.pin_curve_by_distance(list_pin=list_joint_spine, source=self.ribbon_torso_ik, typ="surface",
                                        maintainOffset=True,
                                        parent=grp_pin,
                                        constraint=None,
                                        name="ikSurface")[:])

        # apply constraints to joints
        for i, grp_pin in enumerate(self.list_ik_surface_pin):
            # connect scale value to grp pin
            cmds.connectAttr(ctrl_main + ".s", grp_pin + ".s")

            if i == 0:  # pelvis case
                cmds.pointConstraint(grp_pin, list_joint_spine[i], mo=1)

                loc_driver_pelvis = cmds.spaceLocator(n=self.list_ik_driver_joints[0].replace(jnt, loc))
                utils.match_parent(loc_driver_pelvis, self.list_ik_driver_joints[0])
                cmds.orientConstraint(loc_driver_pelvis, list_joint_spine[i], mo=1)
            elif i == len(list_joint_spine) - 1:  # chest case
                cmds.pointConstraint(grp_pin, list_joint_spine[i], mo=1)
                cmds.orientConstraint(self.list_ik_driver_joints[2], list_joint_spine[i], mo=1)
            else:  # spine case
                cmds.parentConstraint(grp_pin, list_joint_spine[i], mo=1)

    def create_ik_waist_constraint(self):
        grp_ctrl_waist_point = utils.freeze_group([self.list_ik_control[0]], prefix="grpPoint")[0]
        cmds.pointConstraint(self.ctrl_pelvis, self.list_ik_control[1], grp_ctrl_waist_point, mo=1)

    def create_ik_controls(self):
        grp_control = cmds.group(em=1, n="{}_spineIkCtrl".format(grp), p=self.ctrl_cog)
        ctrl_waist_ik = "{}_waistIk".format(ctrl)
        ctrl_chest_ik = "{}_chestIk".format(ctrl)

        # create spine and chest controls
        utils.create_control(name=ctrl_waist_ik, match=self.list_ik_driver_joints[1], parent=grp_control, roo="xzy",
                             constraint="parent")
        utils.create_control(name=ctrl_chest_ik, match=self.list_ik_driver_joints[2], parent=grp_control, roo="xzy",
                             constraint="parent")

        self.list_ik_control.append(ctrl_waist_ik)
        self.list_ik_control.append(ctrl_chest_ik)

        utils.freeze_group(self.list_ik_control, prefix=grpCtrl)

        cmds.parentConstraint(self.ctrl_pelvis, self.list_ik_driver_joints[0], mo=1)

    def constraint_between_ik(self):
        # constraint middle ik controller
        grp_offset_between = utils.freeze_group([self.list_ik_control[1]], prefix="grpBetween")[0]

        # connection translate
        node_decompA = cmds.createNode("decomposeMatrix", n="spineA_decomp")
        node_decompB = cmds.createNode("decomposeMatrix", n="spineB_decomp")

        node_pma_pos = cmds.createNode("plusMinusAverage", n="spinePosBetween_pma")
        node_multDivide_pos = cmds.createNode("multiplyDivide", n="spinePosBetween_multDivide")
        node_pma_posOffset = cmds.createNode("plusMinusAverage", n="spinePosBetweenOffset_pma")

        cmds.connectAttr(self.list_ik_control[0] + ".worldMatrix", node_decompA + ".inputMatrix")
        cmds.connectAttr(self.list_ik_control[2] + ".worldMatrix", node_decompB + ".inputMatrix")

        cmds.connectAttr(node_decompA + ".outputTranslate", node_pma_pos + ".input3D[0]")
        cmds.connectAttr(node_decompB + ".outputTranslate", node_pma_pos + ".input3D[1]")

        cmds.connectAttr(node_pma_pos + ".output3D", node_multDivide_pos + ".source")
        cmds.setAttr(node_multDivide_pos + ".match", 0.5, 0.5, 0.5, typ="double3")
        cmds.connectAttr(node_multDivide_pos + ".output", node_pma_posOffset + ".input3D[0]")

        multDivide_output = cmds.getAttr(node_multDivide_pos + ".output")[0]
        cmds.setAttr(node_pma_posOffset + ".operation", 2)
        cmds.setAttr(node_pma_posOffset + ".input3D[1]", multDivide_output[0], multDivide_output[1],
                     multDivide_output[2], typ="double3")
        cmds.connectAttr(node_pma_posOffset + ".output3D", grp_offset_between + ".translate")

        # # connection rotate
        # node_pma_rot = cmds.createNode("plusMinusAverage", n="spineRotBetween_pma")
        # node_multDivide_rot = cmds.createNode("multiplyDivide", n="spineRotBetween_multDivide")
        # node_pma_rotOffset = cmds.createNode("plusMinusAverage", n="spineRotBetweenOffset_pma")
        #
        # cmds.connectAttr(list_ik_control[0] + ".r", node_pma_rot + ".input3D[0]")
        # cmds.connectAttr(list_ik_control[2] + ".r", node_pma_rot + ".input3D[1]")
        #
        # cmds.connectAttr(node_pma_rot + ".output3D", node_multDivide_rot + ".source")
        # cmds.setAttr(node_multDivide_rot + ".match", 0.5, 0.5, 0.5, typ="double3")
        # cmds.connectAttr(node_multDivide_rot + ".output", node_pma_rotOffset + ".input3D[0]")
        #
        # multDivide_output = cmds.getAttr(node_multDivide_rot + ".output")[0]
        # cmds.setAttr(node_pma_rotOffset + ".operation", 2)
        # cmds.setAttr(node_pma_rotOffset + ".input3D[1]", multDivide_output[0], multDivide_output[1],
        #              multDivide_output[2], typ="double3")
        # cmds.connectAttr(node_pma_rotOffset + ".output3D", grp_offset_between + ".r")

    def insert_squash_function(self):
        def getDistanceNode():
            node_pma = cmds.createNode("plusMinusAverage", n="sum_distanceSpine")
            for i in range(len(list_distance_references) - 1):
                node_distance = cmds.createNode("distanceBetween",
                                                n="distBetween_spineCtrl{}".format(str(i + 1).zfill(2)))
                first_worldMatrix = list_distance_references[i] + ".worldMatrix"
                second_worldMatrix = list_distance_references[i + 1] + ".worldMatrix"

                cmds.connectAttr(first_worldMatrix, node_distance + ".inMatrix1")
                cmds.connectAttr(second_worldMatrix, node_distance + ".inMatrix2")
                cmds.connectAttr(node_distance + ".distance", "{}.input1D[{}]".format(node_pma, i))
            return node_pma + ".output1D"

        list_distance_references = [self.ctrl_pelvis, self.list_ik_control[0], self.list_ik_control[1]]

        # add attributes
        ctrl_attribute = self.list_ik_control[0]
        attr_squash = "{}.squash".format(ctrl_attribute)
        attr_squashEnv = "{}.autoSquashEnvelope".format(ctrl_attribute)
        attr_squashTyp = "{}.autoSquashType".format(ctrl_attribute)

        cmds.addAttr(ctrl_attribute, ln=attr_squash.split(".")[1], k=1, dv=0)
        cmds.addAttr(ctrl_attribute, ln=attr_squashEnv.split(".")[1], k=1, min=0, max=1, dv=1)
        cmds.addAttr(ctrl_attribute, ln=attr_squashTyp.split(".")[1], k=1, at="enum",
                     en="None:SquashIn:SquashOut:Both:", dv=3)

        # prepare node
        attr_distance = getDistanceNode()

        node_cond = cmds.createNode("condition", n="cond_spineSquash")
        node_squash = cmds.createNode("floatMath", n="math_spineSquash")
        node_fixScl = cmds.createNode("floatMath", n="math_spineSquashFix")
        node_choice = cmds.createNode("choice", n="choice_spineSquashTyp")
        node_squashAdd = cmds.createNode("floatMath", n="math_spineSquashAdd")
        node_blend = cmds.createNode("blendTwoAttr", n="blend_squashEnv")

        cmds.setAttr(node_squash + ".operation", 3)
        cmds.setAttr(node_fixScl + ".operation", 2)

        # connection
        loc_scale_fix = cmds.spaceLocator(n="{}_spineScaleFix".format(loc))[0]
        cmds.parent(loc_scale_fix, grp_still)
        cmds.connectAttr(ctrl_main + ".sy", loc_scale_fix + ".sy")
        cmds.connectAttr(loc_scale_fix + ".sy", node_fixScl + ".floatA")

        cmds.setAttr(node_fixScl + ".floatB", cmds.getAttr(attr_distance))

        cmds.connectAttr(node_fixScl + ".outFloat", node_squash + ".floatA")
        cmds.connectAttr(attr_distance, node_squash + ".floatB")

        cmds.setAttr(node_choice + ".input[0]", 0)
        cmds.setAttr(node_choice + ".input[1]", 4)
        cmds.setAttr(node_choice + ".input[2]", 2)
        cmds.setAttr(node_choice + ".input[3]", 1)

        cmds.connectAttr(node_squash + ".outFloat", node_cond + ".firstTerm")
        cmds.connectAttr(node_squash + ".outFloat", node_cond + ".colorIfTrueR")
        cmds.setAttr(node_cond + ".secondTerm", 1)
        cmds.connectAttr(attr_squashTyp, node_choice + ".selector")
        cmds.connectAttr(node_choice + ".output", node_cond + ".operation")

        cmds.setAttr(node_blend + ".input[0]", 1)
        cmds.connectAttr(node_cond + ".outColorR", node_blend + ".input[1]")
        cmds.connectAttr(attr_squashEnv, node_blend + ".attributesBlender")

        cmds.connectAttr(node_blend + ".output", node_squashAdd + ".floatA")
        cmds.connectAttr(attr_squash, node_squashAdd + ".floatB")

        utils.add_notes([node_squash, node_squashAdd, node_choice, node_cond, node_blend, node_fixScl])
        for i in range(1, len(self.list_joint_spine) - 1):
            for axis in self.squash_axis:
                cmds.connectAttr(node_squashAdd + ".outFloat", self.list_joint_spine[i] + ".s" + axis)

    def create_ctrl_cog(self):
        # create cog control
        utils.create_control(name=self.ctrl_cog,
                             guide_scale=1,
                             guide_ball=None,
                             match=self.jnt_cog,
                             parent=self.grp_local_anim,
                             shape="plus",
                             constraint="parent"
                             )
        cmds.addAttr(self.ctrl_cog, ln="squashAmount", at="float", min=0, max=1)

        utils.freeze_group([self.ctrl_cog], prefix=grpCtrl)

    def finalize(self):
        for control in self.list_ik_control:
            utils.lock_attributes(control, s=1, v=1)

        for control in self.list_fk_control:
            utils.lock_attributes(control, s=1, v=1)

        utils.lock_attributes(self.ctrl_cog, s=1, v=1)

    def create_ctrl_pelvis(self):
        utils.create_control(name=self.ctrl_pelvis, match=self.jnt_pelvis, parent=self.ctrl_cog)
        utils.freeze_group([self.ctrl_pelvis])

    def pin_follicles(self):
        utils.pin_ribbon(list_pin=self.list_joint_spine)

    def build(self):
        self.generate_variables()
        self.create_hierarchy()

        self.create_ribbon()

        self.create_ctrl_cog()
        self.create_ctrl_pelvis()

        self.create_ik_driver()
        self.create_ik_controls()
        self.apply_ik_joints()

        self.create_fk_driver()
        self.apply_fk_output()
        self.create_fk_controls()

        self.insert_squash_function()

        self.finalize()


class MouthCrease:
    def __init__(self):
        self.name = ""
        self.jnt_jaw = ""

    def build(self):
        cmds.group(em=1, n=grp_outerMouth_sys, p=grp_anim)
        cmds.group(em=1, n=grp_outerMouth_allCtrl, p=grp_anim)

        for self.name in (L, R):
            list_jntDrv = []
            list_outer_bind = ['{}_outMouth_01_jnt'.format(self.name), '{}_outMouth_02_jnt'.format(self.name),
                               '{}_outMouth_03_jnt'.format(self.name),
                               '{}_outMouth_04_jnt'.format(self.name)]

            # create offset group for outer mouth bind joints
            list_grp_constraint = []
            list_grp_offset = []
            for joint in list_outer_bind:
                grp_recent = None
                joint_name = joint.replace("_" + jnt, "")
                for i in range(3):
                    grp_offset = cmds.group(em=1,
                                            n="{}_offset_{}_{}".format(joint_name,
                                                                       str(i + 1).zfill(2),
                                                                       grp), p=grp_outerMouth_allCtrl)
                    if grp_recent:
                        cmds.parent(grp_offset, grp_recent)

                    grp_recent = grp_offset

                    if i == 0:
                        cmds.matchTransform(grp_offset, joint)
                        list_grp_offset.append(grp_offset)
                    elif i == 2:
                        list_grp_constraint.append(grp_offset)

            # pin offset group to curve
            curve_outer = utils.draw_curve(list_outer_bind, "{}_outerMouth_{}".format(self.name, crv), rebuild=True,
                                           parent=grp_outerMouth_sys)
            utils.pin_curve_by_distance(list_pin=list_grp_offset, source=curve_outer)

            # apply to bind joints
            for i, joint in enumerate(list_outer_bind):
                cmds.parentConstraint(list_grp_constraint[i], joint, mo=1)

            # create outerDriver
            for i in range(2):
                cmds.select(cl=1)
                jntDrv = cmds.joint(n="{}_outerDrive_{}_{}".format(self.name, str(i + 1).zfill(2), self._jnt_jaw))
                list_jntDrv.append(jntDrv)
                utils.snap_to_curve_by_param(curve_outer, jntDrv, i)
            cmds.parent(list_jntDrv, grp_outerMouth_sys)

            # finalize
            cmds.parent(list_jntDrv, grp_outerMouth_allCtrl)
            cmds.skinCluster(list_jntDrv, curve_outer, ih=1, dr=5, bm=3, mi=2)
            cmds.parentConstraint(self.jnt_jaw, list_jntDrv[-1], mo=1)


class Braw:
    def __init__(self):
        self.name = ""
        self.list_braw_joint = []
        self.loc_mainCtrl = ""

        self._mid_joints = []
        self._grp_local_anim = ""
        self._grp_local_still = ""
        self._list_braw_ctrl = []
        self._ctrl_main = ""

    def generate_variables(self):
        self._grp_local_anim = "{}_{}Anim".format(grp, self.name)
        self._grp_local_still = "{}_{}Still".format(grp, self.name)
        self._ctrl_main = "{}_{}Main".format(ctrl, self.name)
        self._list_braw_ctrl = [joint.replace(jnt, ctrl) if jnt in joint else "{}_{}".format(ctrl, joint) for joint in self.list_braw_joint]

    def create_braw_rig(self):
        def create_low_curve():
            position = []
            for locator in self.list_braw_joint:
                position.append(cmds.xform(locator, ws=1, t=1, q=1))

            curve = cmds.curve(d=1, p=position)
            curve = cmds.rebuildCurve(
                curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=4, d=3, tol=0)[0]

            curve = cmds.rename(curve, "{}_{}Low".format(crv, self.name))
            cmds.parent(curve, self._grp_local_still)

            return curve

        def tmp():
            pass

            def create_low_joints():
                def create_joint(count, position):
                    # querry parameter
                    cmds.select(cl=1)
                    grp_joint = cmds.group(
                        em=1, n=grp + "_" + self.name + "_braw_low_offset_" + str(count).zfill(2))
                    cmds.parent(grp_joint, self._grp_local_still)
                    joint = cmds.joint(
                        n=jnt + "_" + self.name + "_braw_low_" + str(count).zfill(2))

                    node_npc = cmds.shadingNode("nearestPointOnCurve", au=1)
                    node_poc = cmds.shadingNode("pointOnCurveInfo", au=1)

                    curve_shape = cmds.listRelatives(
                        low_curve, c=1, typ="nurbsCurve")[0]

                    # querry param
                    cmds.connectAttr(curve_shape + ".worldSpace",
                                     node_npc + ".inputCurve")
                    cmds.setAttr(node_npc + ".inPosition",
                                 position[0], position[1], position[2], typ="double3")
                    cmds.connectAttr(node_npc + '.position',
                                     grp_joint + ".translate")
                    param = cmds.getAttr(node_npc + ".parameter")

                    cmds.delete(node_npc)

                    # apply param
                    cmds.connectAttr(
                        curve_shape + ".worldSpace[0]", node_poc + ".inputCurve", f=1)
                    cmds.setAttr(node_poc + ".parameter", param)
                    cmds.connectAttr(node_poc + ".position",
                                     grp_joint + ".translate")

                    cmds.matchTransform(joint, grp_joint)

                    return joint

                # create joint
                low_joints = []
                count = 1

                for i, locator in enumerate(self.list_braw_joint):

                    cmds.select(cl=1)
                    pos = cmds.xform(locator, q=1, ws=1, t=1)
                    low_joints.append(create_joint(count=count, position=pos))
                    count += 1

                    if i != 3:
                        cmds.select(cl=1)

                        pos1 = (cmds.xform(locator, q=1, ws=1, t=1))
                        pos2 = (cmds.xform(
                            self.list_braw_joint[i + 1], q=1, ws=1, t=1))

                        low_joints.append(create_joint(
                            count=count,
                            position=[(pos1[0] + pos2[0]) / 2, (pos1[1] + pos2[1]) / 2, (pos1[2] + pos2[2]) / 2]))

                        count += 1

                return low_joints

            def create_mid_joints():
                list_mid_joints = []
                for i in range(4):
                    cmds.select(cl=1)
                    list_mid_joints.append(cmds.joint(
                        n=jnt + "_" + self.name + "_braw_mid_" + str(i + 1).zfill(2), rad=2))

                count = 0
                for i in range(0, 7, 2):
                    print(low_joints[i])
                    cmds.matchTransform(list_mid_joints[count], low_joints[i])
                    count += 1

                cmds.skinCluster(list_mid_joints, low_curve, mi=2)
                cmds.select(cl=1)
                return list_mid_joints

            def create_mid_controller():
                list_mid_controller = []
                for i, joint in enumerate(mid_joints):
                    ctrl_mid = utils.create_control(
                        name=ctrl + "_" + self.name + "_braw_mid_" + str(i + 1).zfill(2), match=joint, axis="z")
                    cmds.setAttr(joint + ".v", 0)
                    cmds.parent(joint, ctrl_mid)

                    list_mid_controller.append(ctrl_mid)

                cmds.parent(list_mid_controller, grp_braw_allCtrl)
                utils.freeze_group(list_mid_controller)

                return list_mid_controller

            def create_controller_constraint():
                cmds.parentConstraint(mid_controller[0], mid_controller[2], cmds.listRelatives(
                    mid_controller[1], p=1, typ="transform")[0], mo=1)

                cmds.orientConstraint(
                    mid_controller[0], low_controller[0], mo=0)
                cmds.orientConstraint(
                    mid_controller[3], low_controller[6], mo=0)

            def get_list_guide():
                for obj in cmds.listRelatives(self._grp_local_still, c=1, typ="transform"):
                    if guide in obj and self.name in obj:
                        list_guide.append(obj)
                list_guide.sort()

        # parent
        parent_joint = None
        parent_controller = None

        low_amount = 0
        mid_amount = 0

        # get_list_guide()

        # create low joints and low curve
        # low_curve = create_low_curve()

        # # create mid joint and controller
        # mid_joints = create_mid_joints()
        # mid_controller = create_mid_controller()
        #
        # # create constraint
        # create_controller_constraint()

    def create_low_controller(self):
        for i, joint in enumerate(self.list_braw_joint):
            parent = cmds.listRelatives(joint, p=1, typ="transform")[0]
            ctrl_low = utils.create_control(name=self._list_braw_ctrl[i], match=joint, parent=self._ctrl_main)
            cmds.parentConstraint(ctrl_low, joint)

        # cmds.parent(list_low_controller, grp_braw_allCtrl)
        utils.freeze_group(self._list_braw_ctrl)

    def create_hierarchy(self):
        cmds.group(em=1, n=self._grp_local_anim, p=grp_anim)
        cmds.group(em=1, n=self._grp_local_still, p=grp_still)

    def create_main_ctrl(self):
        utils.create_control(name=self._ctrl_main, parent=self._grp_local_anim)

        cmds.matchTransform(self._ctrl_main, self.loc_mainCtrl) if self.loc_mainCtrl is not "" else cmds.matchTransform(self._ctrl_main, self.list_braw_joint[-2])

    def constraint_between_ctrl(self):
        target_index = 1

        grp_constraint = utils.freeze_group([self._list_braw_ctrl[target_index]], prefix="grpPoint")[0]
        cmds.pointConstraint(self._list_braw_ctrl[target_index - 1], self._list_braw_ctrl[target_index + 1], grp_constraint, mo=1)

    def build(self):
        self.generate_variables()
        self.create_hierarchy()
        self.create_main_ctrl()

        self.create_low_controller()
        self.create_braw_rig()
        self.constraint_between_ctrl()


class Nose:
    def __init__(self):
        self.jnt_nose_base = None
        self.jnt_nose_bridge = None
        self.jnt_nose_tip = None
        self.jnt_L_nose_wing = None
        self.jnt_R_nose_wing = None

    def set_joint_name(self, jnt_nose_base, jnt_nose_bridge, jnt_nose_tip, jnt_L_nose_wing, jnt_R_nose_wing):
        self.jnt_nose_base = jnt_nose_base
        self.jnt_nose_bridge = jnt_nose_bridge
        self.jnt_nose_tip = jnt_nose_tip
        self.jnt_L_nose_wing = jnt_L_nose_wing
        self.jnt_R_nose_wing = jnt_R_nose_wing

    def create_hierarchy(self):
        pass

    def build(self):
        pass
