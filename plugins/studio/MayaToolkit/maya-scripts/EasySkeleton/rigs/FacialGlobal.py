from EasySkeleton import utils
from EasySkeleton.config import *
import maya.cmds as cmds
from EasySkeleton import rig_class
from importlib import reload
import math

class Mouth(rig_class.Rig):
    """
    Mouth Curve Based

    Variables:
    eye_ball_joint (string) : Eye ball joint name

    amount_eye_slide_joint (long) : Number of eye slide joints

    locator_start_radius (string) : Locator start radius
    locator_end_radius (string) : Locator end radius
    flip_scale (bool) : Flip scale toggle

    list_pupil_joint (stringArray) : List of pupil joint names

    joint_iris_loop_edge (string) : Iris loop edge joint name
    joint_pupil_loop_edge (string) : Pupil loop edge joint name

    enable_specular_rig (bool) : Enable specular rigging
    specular_joint (string) : Specular joint name
    specular_pitch_axis (string) : Specular pitch axis
    specular_yaw_axis (string) : Specular yaw axis
    specular_pitch_axis_invert (bool) : Invert pitch axis
    specular_yaw_axis_invert (bool) : Invert yaw axis
    value_unit_conversion (float) : Value for unit conversion
    specular_roll_axis_invert (bool) : Invert roll axis

    left_eye_joint (string) : Left eye joint name
    left_eye_aim_axis (string) : Aim axis for left eye
    left_eye_up_axis (string) : Up axis for left eye

    right_eye_joint (string) : Right eye joint name
    right_eye_aim_axis (string) : Aim axis for right eye
    right_eye_up_axis (string) : Up axis for right eye

    distance (long) : Distance value
    distance_direction (string) : Direction of the distance

    left_eye_control_pivot (string) : Pivot control for left eye
    right_eye_control_pivot (string) : Pivot control for right eye

    jnt_mouth_global (string) : Mouth global joint name

    list_upper_bind (stringArray) : List of upper bind joint names
    list_lower_bind (stringArray) : List of lower bind joint names

    jnt_jaw (string) : Jaw joint name

    use_custom_main_pivot (bool) : Use custom main pivot toggle
    list_custom_main_pivot (stringArray) : List of custom main pivot names

    parent (string) : Parent node name

    list_teeth_up (stringArray) : List of upper teeth names
    list_teeth_low (stringArray) : List of lower teeth names

    list_tongue_joints_chain (stringArray) : List of tongue joint chain names

    enable_curve_blendshape (bool) : Enable curve blend shape toggle
    list_curve_up (stringArray) : List of upper curve names
    list_curve_low (stringArray) : List of lower curve names

    value_up (long) : Value for upward movement
    value_down (long) : Value for downward movement
    value_out (long) : Value for outward movement
    value_in (long) : Value for inward movement

    clamp_top (bool) : Clamp top movement
    clamp_down (bool) : Clamp down movement
    clamp_in (bool) : Clamp inward movement
    clamp_out (bool) : Clamp outward movement

    enable_mesh_blend_shape (bool) : Enable mesh blend shape toggle
    list_shape_up (stringArray) : List of upper shape names
    list_shape_low (stringArray) : List of lower shape names
    list_shape_in (stringArray) : List of inward shape names
    list_shape_out (stringArray) : List of outward shape names

    shape_up_driven_value (long) : Driven value for upper shape
    shape_down_driven_value (long) : Driven value for lower shape
    shape_in_driven_value (long) : Driven value for inward shape
    shape_out_driven_value (long) : Driven value for outward shape

    list_target_shape (stringArray) : List of target shape names
    exist_blendshape_mesh (string) : Existing blend shape mesh name

    enable_auto_push (bool) : Enable auto push toggle
    jaw_push_rotate_axis (string) : Rotation axis for jaw push
    invert_push_axis (bool) : Invert push axis toggle
    value_start_push (long) : Start value for push

    axis_side_push_in (string) : Axis for inward side push
    side_parent_intensity (float) : Intensity for parent side movement
    side_control_intensity (float) : Intensity for control side movement

    curve_up_weight_path(path) : File class_instance for upper curve weights
    curve_low_weight_path(path) : File class_instance for lower curve weights

    enable_zipper (bool) : Enable zipper toggle
    mirror_control_scale (bool) : Mirror scale controls toggle
    debug_mode (bool) : Debug mode toggle

    """

    def __init__(self):
        super().__init__()
        self.name = "Mouth"

        # @ Setting
        # $ Global Joint
        self.jnt_mouth_global = ""
        # -

        self.list_upper_bind = []
        self.list_lower_bind = []

        # -
        self.jnt_jaw = ""

        # $ Guide Pivot
        self.use_custom_main_pivot = False
        self.list_custom_main_pivot = []
        # * use_custom_main_pivot

        # $ Inner Mouth
        self.list_teeth_up = []
        self.list_teeth_low = []

        self.list_tongue_joints_chain = []

        # @ Optional
        # $ Curve Blend Shape
        self.enable_curve_blendshape = False
        # -
        self.list_curve_up = []
        self.list_curve_low = []

        # -
        self.value_up = 3
        self.value_down = -3
        self.value_out = 3
        self.value_in = -3
        # -
        self.clamp_top = True
        self.clamp_down = True
        self.clamp_in = True
        self.clamp_out = True
        # *enable_curve_blendshape

        # $ Mesh Blend Shape
        self.enable_mesh_blend_shape = False
        # -
        self.list_shape_up = []
        self.list_shape_low = []
        self.list_shape_in = []
        self.list_shape_out = []
        # -
        self.shape_up_driven_value = 3
        self.shape_down_driven_value = -3
        self.shape_in_driven_value = -3
        self.shape_out_driven_value = 3
        # -
        self.list_target_shape = []
        # -
        self.exist_blendshape_mesh = ""
        # *enable_mesh_blend_shape

        # $ Auto Jaw Push
        self.enable_auto_push = True
        self.jaw_push_rotate_axis = "x"
        self.invert_push_axis = False
        self.value_start_push = 0
        # * enable_auto_push

        # $ Main Controls Adjustment
        self.axis_side_push_in = "z"
        self.side_parent_intensity = 0.3
        self.side_control_intensity = 1.5

        # $ Auto Import Curve Skin Weight
        self.curve_up_weight_path = ""
        self.curve_low_weight_path = ""

        # $ Others
        self.enable_zipper = True
        self.mirror_control_scale = True
        self.debug_mode = False

    def core_build(self):
        def create_hierarchy():
            cmds.group(em=1, n=grp_mouth_curves, p=self.grp_local_still)

            cmds.group(em=1, n=grp_blendshape, p=grp_mouth_curves)
            cmds.setAttr(grp_blendshape + ".v", 0)

            cmds.group(em=1, n=grp_main_control, p=self.grp_local_anim)
            cmds.group(em=1, n=grp_mid_control, p=self.grp_local_anim)

            cmds.group(em=1, n=grp_bind_control, p=self.grp_local_anim)

        def create_mouth_curves():
            # sub curve
            degree = 3
            rebuild = True
            spans = 6
            rebuild_degree = 3

            # up curve
            for name in [crv_bind_up]:
                utils.draw_curve(list_items=self.list_upper_bind, curve_name=name, parent=grp_mouth_curves, d=degree, rebuild=rebuild, s=spans, rebuild_degree=rebuild_degree)
                cmds.rename(cmds.listRelatives(name, c=1, s=1, typ="nurbsCurve")[0], name + "Shape")

            # low curve
            for name in [crv_bind_low]:
                utils.draw_curve(list_items=[self.list_upper_bind[0]] + self.list_lower_bind + [self.list_upper_bind[-1]], curve_name=name, parent=grp_mouth_curves, d=degree, rebuild=rebuild,
                                 s=spans,
                                 rebuild_degree=rebuild_degree)
                cmds.rename(cmds.listRelatives(name, c=1, s=1, typ="nurbsCurve")[0], name + "Shape")

        def create_mid_controls():
            grp_mid_up_space = cmds.group(em=1, n="{}_midUpSpace_{}".format(self.name, grp), p=grp_mid_control)
            grp_mid_low_space = cmds.group(em=1, n="{}_midLowSpace_{}".format(self.name, grp), p=grp_mid_control)

            cmds.parentConstraint(self.jnt_jaw, grp_mid_low_space, mo=1)

            # create controls
            [utils.create_control(name=control, parent=grp_mid_up_space,size=0.8,color="blue") for control in list_mid_up_control]
            [utils.create_control(name=control, parent=grp_mid_low_space,size=0.8,color="blue") for control in list_mid_low_control]

            # snap ctrl to position
            amount = 5
            for i in range(amount):
                utils.snap_to_curve_by_param(crv_bind_up, list_mid_up_control[i], i * (1 / (amount - 1)), True)

                if i in range(1, amount - 1):
                    utils.snap_to_curve_by_param(crv_bind_low, list_mid_low_control[i - 1], i * (1 / (amount - 1)), True)

            # freeze group
            list_frz_up_control = utils.freeze_group(list_mid_up_control, prefix="grpCtrl")
            list_frz_low_control = utils.freeze_group(list_mid_low_control, prefix="grpCtrl")

            # flip scale
            if self.mirror_control_scale:
                cmds.setAttr(list_frz_up_control[0] + ".sx", -1)
                cmds.setAttr(list_frz_up_control[1] + ".sx", -1)

                cmds.setAttr(list_frz_low_control[0] + ".sx", -1)
                cmds.setAttr(list_frz_low_control[0] + ".sy", -1)

                cmds.setAttr(list_frz_low_control[1] + ".sy", -1)
                cmds.setAttr(list_frz_low_control[2] + ".sy", -1)

            # create joints and parent to control
            list_mid_control = list_mid_up_control + list_mid_low_control
            list_mid_joint = list_mid_up_joint + list_mid_low_joint
            for i in range(8):
                control = list_mid_control[i]
                joint = list_mid_joint[i]
                cmds.joint(n=joint)
                utils.match_parent(joint, control)

        def create_main_controls():
            list_main_control = [ctrl_main_up, ctrl_main_low, ctrl_main_left, ctrl_main_right]
            list_main_locator = [loc_main_up, loc_main_low, loc_main_left, loc_main_right]
            list_main_joint = [jnt_main_up, jnt_main_low, jnt_main_left, jnt_main_right]

            # Create Hierarchy ---------------------------------------------------------
            grp_global_space = cmds.group(em=1, n="{}_globalDrv_grp".format(self.name), p=grp_main_control)
            cmds.matchTransform(grp_global_space, self.jnt_mouth_global)

            # create jaw space group
            cmds.group(em=1, n=grp_corner_space, p=grp_global_space)
            cmds.group(em=1, n=grp_up_space, p=grp_global_space)
            cmds.group(em=1, n=grp_low_space, p=grp_global_space)

            # connect global space
            cmds.matchTransform(grp_corner_space, self.jnt_jaw)
            cmds.matchTransform(grp_up_space, self.jnt_jaw)
            cmds.matchTransform(grp_low_space, self.jnt_jaw)
            utils.freeze_group_classic([grp_corner_space, grp_low_space, grp_up_space], "grpOff")

            utils.freeze_group(grp_global_space)

            # auto jaw push
            if self.enable_auto_push:
                cmds.connectAttr("{}.r{}".format(self.jnt_jaw, self.jaw_push_rotate_axis), "{}.r{}".format(grp_up_space, self.jaw_push_rotate_axis))

                if self.invert_push_axis:
                    cmds.setAttr(grp_up_space + ".minRot{}Limit".format(self.jaw_push_rotate_axis.upper()), self.value_start_push)
                    cmds.setAttr(grp_up_space + ".minRot{}LimitEnable".format(self.jaw_push_rotate_axis.upper()), True)
                else:
                    cmds.setAttr(grp_up_space + ".maxRot{}Limit".format(self.jaw_push_rotate_axis.upper()), self.value_start_push)
                    cmds.setAttr(grp_up_space + ".maxRot{}LimitEnable".format(self.jaw_push_rotate_axis.upper()), True)

            # Global Space Connection ----------------------------------------------------
            cmds.connectAttr("{}.translate".format(ctrl_mouth_global), "{}.translate".format(grp_global_space))
            cmds.connectAttr("{}.rotate".format(ctrl_mouth_global), "{}.rotate".format(grp_global_space))

            # Jaw Space Connection -------------------------------------------------------
            # jaw low space connection
            cmds.connectAttr(ctrl_jaw + ".t", grp_low_space + ".t")
            cmds.connectAttr(ctrl_jaw + ".r", grp_low_space + ".r")

            # jaw corner space connection
            node_corner_tsl = cmds.createNode("multiplyDivide", n="{}_cornerJawTsl_md".format(self.name))
            node_corner_rot = cmds.createNode("multiplyDivide", n="{}_cornerJawRot_md".format(self.name))

            cmds.setAttr(node_corner_tsl + ".input2", 0.5, 0.5, 0.5, typ="double3")
            cmds.setAttr(node_corner_rot + ".input2", 0.5, 0.5, 0.5, typ="double3")

            cmds.connectAttr(ctrl_jaw + ".t", node_corner_tsl + ".input1")
            cmds.connectAttr(ctrl_jaw + ".r", node_corner_rot + ".input1")

            cmds.connectAttr(node_corner_tsl + ".output", grp_corner_space + ".t")
            cmds.connectAttr(node_corner_rot + ".output", grp_corner_space + ".r")

            # constraint bind group orient by grp space
            for grp_pin in list_bind_pin_up[1:len(list_bind_pin_up) - 1]:
                cmds.orientConstraint(grp_up_space, grp_pin, mo=1)

            for grp_pin in list_bind_pin_low:
                cmds.orientConstraint(grp_low_space, grp_pin, mo=1)

            for grp_pin in [list_bind_pin_up[0], list_bind_pin_up[-1]]:
                cmds.orientConstraint(grp_corner_space, grp_pin, mo=1)

            # create driver locator ----------------------------
            [cmds.spaceLocator(n=name) for name in list_main_locator]

            # snap position of locator
            utils.snap_to_curve_by_param(crv_bind_up, loc_main_up, 0.5, True)
            utils.snap_to_curve_by_param(crv_bind_low, loc_main_low, 0.5, True)
            cmds.matchTransform(loc_main_left, self.list_upper_bind[-1])
            cmds.matchTransform(loc_main_right, self.list_upper_bind[0])

            # snap to custom pivot
            if self.use_custom_main_pivot:
                if len(self.list_custom_main_pivot) != 4:
                    raise Exception("List Custom Main Pivot : invalid input")

                match_right, match_up, match_left, match_low = self.list_custom_main_pivot
                cmds.matchTransform(loc_main_up, match_up, rot=1)
                cmds.matchTransform(loc_main_right, match_right, rot=1)
                cmds.matchTransform(loc_main_left, match_left, rot=1)
                cmds.matchTransform(loc_main_low, match_low, rot=1)

            # create controls + locator
            for i in range(4):
                control = list_main_control[i]
                locator = list_main_locator[i]
                joint = list_main_joint[i]

                # create control
                utils.create_control(name=control,size=1,color="yellow", parent=grp_main_control, match=locator)

                cmds.select(cl=1)

                # constraint corner control
                if control is ctrl_main_left or control is ctrl_main_right:  # corner case
                    cmds.parent(control, grp_corner_space)
                elif control is ctrl_main_up:
                    cmds.parent(control, grp_up_space)
                elif control is ctrl_main_low:
                    cmds.parent(control, grp_low_space)

                utils.freeze_group_classic(control, "grpCtrl")
                cmds.parent(locator, cmds.listRelatives(control, p=1)[0])

                if control in [ctrl_main_left, ctrl_main_right]:
                    for axis in "xyz":
                        if axis == self.axis_side_push_in:
                            node_mdl = cmds.createNode("multDoubleLinear", n="{}_sidePush_mdl".format(self.name))

                            cmds.connectAttr("{}.t{}".format(control, self.axis_side_push_in), "{}.input1".format(node_mdl))
                            cmds.setAttr("{}.input2".format(node_mdl), self.side_control_intensity)
                            cmds.connectAttr("{}.output".format(node_mdl), "{}.t{}".format(locator, self.axis_side_push_in))

                        else:
                            cmds.connectAttr("{}.t{}".format(control, axis), "{}.t{}".format(locator, axis))

                    cmds.connectAttr(control + ".r", locator + ".r")

                else:
                    # parent locator and connection
                    cmds.connectAttr(control + ".t", locator + ".t")
                    cmds.connectAttr(control + ".r", locator + ".r")

            # flip mirror control if required
            if self.mirror_control_scale:
                cmds.setAttr(cmds.listRelatives(ctrl_main_right, p=1)[0] + ".s", -1, -1, -1, typ="double3")
                cmds.setAttr(cmds.listRelatives(ctrl_main_low, p=1)[0] + ".s", 1, -1, 1, typ="double3")

        def create_bind_controls():
            # create controller
            [utils.create_control(name=list_bind_up_control[i],constraint="parent", match=joint, parent=grp_bind_control,size=0.5,color="purple") for i, joint in enumerate(self.list_upper_bind)]
            [utils.create_control(name=list_bind_low_control[i],constraint="parent", match=joint, parent=grp_bind_control,size=0.5,color="purple") for i, joint in enumerate(self.list_lower_bind)]
            # utils.freeze_group_classic(list_bind_up_control + list_bind_low_control, "grpCtrl")

        def pin_bind_controls():
            # bind mid joint to curve
            node_bind_up = cmds.skinCluster(list_mid_up_joint, crv_bind_up, ih=1, dr=0.8, bm=3, mi=3)
            node_bind_low = cmds.skinCluster([list_mid_up_joint[0]] + list_mid_low_joint + [list_mid_up_joint[-1]], crv_bind_low, ih=1,
                                             dr=0.5,
                                             bm=3,
                                             mi=3)

            utils.import_weight(node_bind_up, self.curve_up_weight_path) if self.curve_up_weight_path else None
            utils.import_weight(node_bind_low, self.curve_low_weight_path) if self.curve_low_weight_path else None

            # constraint translate to items by curve
            for control in list_bind_up_control:
                grp_pin = cmds.group(em=1, n=control.replace(ctrl, "grpPin"), p=grp_bind_control)
                cmds.matchTransform(grp_pin, control)
                list_bind_pin_up.append(grp_pin)

            for control in list_bind_low_control:
                grp_pin = cmds.group(em=1, n=control.replace(ctrl, "grpPin"), p=grp_bind_control)
                cmds.matchTransform(grp_pin, control)
                list_bind_pin_low.append(grp_pin)

            utils.pin_curve_by_distance(list_bind_pin_up, crv_bind_up, maintainOffset=False)
            utils.pin_curve_by_distance(list_bind_pin_low, crv_bind_low, maintainOffset=False)

            # create scale constraint space
            grp_space = cmds.group(em=1, n="{}_bind_scale_space_grp".format(self.name), p=grp_bind_control)
            cmds.scaleConstraint(self.grp_local_anim, grp_space)

            # constraint orient and translate to control offset
            list_grp_pin = list_bind_pin_up + list_bind_pin_low
            list_grp_offset = utils.freeze_group_classic(list_bind_up_control + list_bind_low_control, "grpOff")

            for i in range(len(list_grp_pin)):
                grp_offset = list_grp_offset[i]
                grp_pin = list_grp_pin[i]

                cmds.parent(grp_offset, list_grp_pin[i])

                cmds.connectAttr(grp_space + ".s", grp_pin + ".s")

        def create_jaw():
            utils.create_control(name=ctrl_jaw,
                                 match=self.jnt_jaw,
                                 constraint="parent",
                                 parent=self.grp_local_anim,
                                 size=3,
                                 color="yellow")
            utils.freeze_group_classic(ctrl_jaw)

        def create_global_control():
            # create offset group parent
            grp_parent = cmds.group(em=1, n="{}_mouthGlobalAnim".format(grp), p=self.grp_local_anim)

            # create controller and add controller
            utils.create_control(name=ctrl_mouth_global, parent=grp_parent, match=self.jnt_mouth_global,size=3.5,color="green", constraint="parent")
            shape_option = utils.add_option_shape(ctrl_mouth_global, mouth_option_shape)

            utils.freeze_group([ctrl_mouth_global])

            return shape_option

        def pin_mid_controls():
            list_mid_up_grp = utils.freeze_group_classic(list_mid_up_control)
            list_mid_low_grp = utils.freeze_group_classic(list_mid_low_control)

            target_right, target_up_right, target_up, target_up_left, target_left = list_mid_up_grp
            target_low_right, target_low, target_low_left = list_mid_low_grp

            driver_up, driver_left, driver_right, driver_low = [loc_main_up, loc_main_left, loc_main_right, loc_main_low]

            # up constraint
            cmds.parentConstraint(driver_up, target_up)

            # low constraint
            cmds.parentConstraint(driver_low, target_low)

            # corner constraint
            cmds.parentConstraint(driver_left, target_left, mo=1)
            cmds.parentConstraint(driver_right, target_right, mo=1)

            # other constraint
            center_parent_intensity = 1 - self.side_parent_intensity

            constraint = cmds.parentConstraint(driver_up, driver_right, target_up_right, mo=1)[0]
            cmds.setAttr("{}.{}W0".format(constraint, driver_up), center_parent_intensity)
            cmds.setAttr("{}.{}W1".format(constraint, driver_right), self.side_parent_intensity)
            cmds.setAttr(constraint + ".interpType", 0)

            constraint = cmds.parentConstraint(driver_up, driver_left, target_up_left, mo=1)[0]
            cmds.setAttr("{}.{}W0".format(constraint, driver_up), center_parent_intensity)
            cmds.setAttr("{}.{}W1".format(constraint, driver_left), self.side_parent_intensity)
            cmds.setAttr(constraint + ".interpType", 0)

            constraint = cmds.parentConstraint(driver_low, driver_right, target_low_right, mo=1)[0]
            cmds.setAttr("{}.{}W0".format(constraint, driver_low), center_parent_intensity)
            cmds.setAttr("{}.{}W1".format(constraint, driver_right), self.side_parent_intensity)
            cmds.setAttr(constraint + ".interpType", 0)

            constraint = cmds.parentConstraint(driver_low, driver_left, target_low_left, mo=1)[0]
            cmds.setAttr("{}.{}W0".format(constraint, driver_low), center_parent_intensity)
            cmds.setAttr("{}.{}W1".format(constraint, driver_left), self.side_parent_intensity)
            cmds.setAttr(constraint + ".interpType", 0)

        def create_inner_mouth():
            grp_inner_mouth = cmds.group(em=1, n="{}_inner_grp".format(self.name), p=self.grp_local_anim)

            grp_inner_up_space = cmds.group(em=1, n="{}_innerUpSpace_grp".format(self.name), p=grp_inner_mouth)
            grp_inner_low_space = cmds.group(em=1, n="{}_innerLowSpace_grp".format(self.name), p=grp_inner_mouth)

            cmds.matchTransform(grp_inner_up_space, grp_up_space)
            cmds.matchTransform(grp_inner_low_space, grp_low_space)

            utils.freeze_group_classic(grp_inner_up_space,grpOff)
            utils.freeze_group_classic(grp_inner_low_space,grpOff)

            # connect space up to inner up
            cmds.connectAttr("{}.rotate".format(grp_up_space), "{}.rotate".format(grp_inner_up_space))
            cmds.connectAttr("{}.rotate".format(grp_low_space), "{}.rotate".format(grp_inner_low_space))

            # up teeth
            for joint in self.list_teeth_up:
                control = utils.create_control(name=joint + "_ctrl", match=joint, parent=grp_inner_up_space,size=0.5, constraint="parent")
                utils.freeze_group_classic(control)
            # low teeth
            for joint in self.list_teeth_low:
                control = utils.create_control(name=joint + "_ctrl", match=joint, parent=grp_inner_low_space,size=0.5, constraint="parent")
                utils.freeze_group_classic(control)

            # tongue
            recent_tongue_ctrl = None
            for joint in self.list_tongue_joints_chain:
                tongue_ctrl = utils.create_control(name=joint + "_ctrl", match=joint,size=0.5,color="blue",shape="sphere",constraint="parent")

                if recent_tongue_ctrl:
                    cmds.parent(tongue_ctrl, recent_tongue_ctrl)
                else:
                    cmds.parent(tongue_ctrl, grp_inner_low_space)
                utils.freeze_group_classic(tongue_ctrl)
                recent_tongue_ctrl = tongue_ctrl

        def create_zipper():
            if len(self.list_upper_bind) - 2 != len(self.list_lower_bind):
                raise Exception("Zipper Method not support for not equal upper and lower bind joints")

            # create hierarchy
            grp_zipper = cmds.group(em=1, n="{}_zipTarget_grp".format(self.name), p=self.grp_local_anim)
            zip_amount = len(list_bind_low_control)

            # add attribute for left control
            cmds.addAttr(ctrl_main_right, ln="zip", at="float", k=1, min=0, max=10)
            cmds.addAttr(ctrl_main_right, ln="zipScale", at="float", k=0, dv=0.75, min=0, max=1)

            cmds.addAttr(ctrl_main_left, ln="zip", at="float", k=1, min=0, max=10)
            cmds.addAttr(ctrl_main_left, ln="zipScale", at="float", k=0, dv=0.75, min=0, max=1)

            # sticky low locator -----------------------------------------------------
            list_low_down = []
            list_low_top = []
            list_low_output = []

            for i in range(zip_amount):
                loc_low_top = cmds.spaceLocator(n="loc_zipLowTop_{}".format(i + 1))[0]
                loc_low_down = cmds.spaceLocator(n="loc_zipLowDown_{}".format(i + 1))[0]
                loc_low_output = cmds.spaceLocator(n="loc_zipLowOutput_{}".format(i + 1))[0]

                # position up and low locator
                utils.match_parent(loc_low_top, cmds.listRelatives(list_bind_up_control[1: len(list_bind_up_control) - 1][i], p=1)[0])
                utils.match_parent(loc_low_down, cmds.listRelatives(list_bind_low_control[i], p=1)[0])

                # position output locator
                cmds.parent(loc_low_output, grp_zipper)
                cmds.pointConstraint(loc_low_down, loc_low_top, loc_low_output)
                cmds.orientConstraint(cmds.listRelatives(list_bind_low_control[i], p=1)[0], loc_low_output)

                list_low_output.append(loc_low_output)
                list_low_down.append(loc_low_down)
                list_low_top.append(loc_low_top)

            # sticky up locator -----------------------------------------------------

            list_up_down = []
            list_up_top = []
            list_up_output = []

            for i in range(zip_amount):
                loc_up_top = cmds.spaceLocator(n="loc_zipUpTop_{}".format(i + 1))[0]
                loc_up_down = cmds.spaceLocator(n="loc_zipUpDown_{}".format(i + 1))[0]
                loc_up_output = cmds.spaceLocator(n="loc_zipUpOutput_{}".format(i + 1))[0]

                # position up and low locator
                utils.match_parent(loc_up_down, cmds.listRelatives(list_bind_low_control[i], p=1)[0])
                utils.match_parent(loc_up_top, cmds.listRelatives(list_bind_up_control[1: len(list_bind_up_control) - 1][i], p=1)[0])
                cmds.parent(loc_up_output, grp_zipper)

                # position output locator
                cmds.pointConstraint(loc_up_down, loc_up_top, loc_up_output)
                cmds.orientConstraint(cmds.listRelatives(list_bind_up_control[i], p=1)[0], loc_up_output)

                list_up_output.append(loc_up_output)
                list_up_down.append(loc_up_down)
                list_up_top.append(loc_up_top)

            utils.freeze_group_classic(list_up_output + list_low_output)

            # Sticky Lows -------------------------------------------------------------------
            utils.create_sticky_both(list_base_position=list_low_down,
                                     list_zipped_position=list_low_output,
                                     list_zipped_output=utils.freeze_group_classic(list_bind_low_control, "grpZip"),
                                     list_attr_zip=[ctrl_main_left + ".zip", ctrl_main_right + ".zip"],
                                     list_attr_distance=[ctrl_main_left + ".zipScale", ctrl_main_right + ".zipScale"],
                                     name="zipLow",
                                     config_parent=self.grp_local_anim,
                                     unit_conversion=10
                                     )

            # sticky tops -------------------------------------------------------------------
            utils.create_sticky_both(list_base_position=list_up_top,
                                     list_zipped_position=list_up_output,
                                     list_zipped_output=utils.freeze_group_classic(list_bind_up_control[1:len(list_bind_up_control) - 1], "grpZip"),
                                     list_attr_zip=[ctrl_main_left + ".zip", ctrl_main_right + ".zip"],
                                     list_attr_distance=[ctrl_main_left + ".zipScale", ctrl_main_right + ".zipScale"],
                                     name="zipUp",
                                     config_parent=self.grp_local_anim,
                                     unit_conversion=10
                                     )

        def create_mouth_curve_blendshape():
            # create curve mouth shape
            if self.enable_curve_blendshape:
                list_shape_up = self.list_curve_up
                list_shape_low = self.list_curve_low
            else:
                list_shape_up = ["crv_{}_up_top".format(L),
                                 "crv_{}_up_down".format(L),
                                 "crv_{}_up_in".format(L),
                                 "crv_{}_up_out".format(L)]
                list_shape_low = ["crv_{}_low_top".format(L),
                                  "crv_{}_low_down".format(L),
                                  "crv_{}_low_in".format(L),
                                  "crv_{}_low_out".format(L)]

                for curve in list_shape_up:
                    cmds.duplicate(crv_bind_up, n=curve)

                for curve in list_shape_low:
                    cmds.duplicate(crv_bind_low, n=curve)

                cmds.parent(list_shape_up, list_shape_low, grp_blendshape)

            if not self.enable_curve_blendshape:
                return None

            # Duplicate for Right side ------------------------------------
            list_shape_up_flip = [curve.replace(L, R) for curve in list_shape_up]
            list_shape_low_flip = [curve.replace(L, R) for curve in list_shape_low]

            [cmds.duplicate(curve, n=(list_shape_up_flip + list_shape_low_flip)[i]) for i, curve in enumerate(list_shape_up + list_shape_low)]
            [utils.flip_curve(curve) for curve in list_shape_up_flip + list_shape_low_flip]

            # create blendshape -------------------
            bsn_up = cmds.blendShape(list_shape_up, list_shape_up_flip, crv_bind_up, n="{}_up_bsn".format(self.name), o="local", at=1)[0]
            bsn_low = cmds.blendShape(list_shape_low, list_shape_low_flip, crv_bind_low, n="{}_low_bsn".format(self.name), o="local", at=1)[0]

            crv_left_up_top_bshp, crv_left_up_down_bshp, crv_left_up_in_bshp, crv_left_up_out_bshp = list_shape_up
            crv_left_low_top_bshp, crv_left_low_down_bshp, crv_left_low_in_bshp, crv_left_low_out_bshp = list_shape_low

            crv_R_up_top_bshp, crv_R_up_down_bshp, crv_R_up_in_bshp, crv_R_up_out_bshp = list_shape_up_flip
            crv_R_low_top_bshp, crv_R_low_down_bshp, crv_R_low_in_bshp, crv_R_low_out_bshp = list_shape_low_flip

            # set driver left up ------------------------------------------------------------
            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".ty",
                                                driver_value=self.value_up,
                                                output_attr=bsn_up + "." + crv_left_up_top_bshp,
                                                clamp=self.clamp_top)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".ty",
                                                driver_value=self.value_down,
                                                output_attr=bsn_up + "." + crv_left_up_down_bshp,
                                                clamp=self.clamp_down)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".tx",
                                                driver_value=self.value_in,
                                                output_attr=bsn_up + "." + crv_left_up_in_bshp,
                                                clamp=self.clamp_in)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".tx",
                                                driver_value=self.value_up,
                                                output_attr=bsn_up + "." + crv_left_up_out_bshp,
                                                clamp=self.clamp_out)

            # set driver left low
            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".ty",
                                                driver_value=self.value_up,
                                                output_attr=bsn_low + "." + crv_left_low_top_bshp,
                                                clamp=self.clamp_top)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".ty",
                                                driver_value=self.value_down,
                                                output_attr=bsn_low + "." + crv_left_low_down_bshp,
                                                clamp=self.clamp_down)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".tx",
                                                driver_value=self.value_in,
                                                output_attr=bsn_low + "." + crv_left_low_in_bshp,
                                                clamp=self.clamp_in)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_left + ".tx",
                                                driver_value=self.value_up,
                                                output_attr=bsn_low + "." + crv_left_low_out_bshp,
                                                clamp=self.clamp_out)

            # set driver right up -----------------------------------------------------------------
            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".ty",
                                                driver_value=self.value_up,
                                                output_attr=bsn_up + "." + crv_R_up_top_bshp,
                                                clamp=self.clamp_top)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".ty",
                                                driver_value=self.value_down,
                                                output_attr=bsn_up + "." + crv_R_up_down_bshp,
                                                clamp=self.clamp_down)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".tx",
                                                driver_value=self.value_in,
                                                output_attr=bsn_up + "." + crv_R_up_in_bshp,
                                                clamp=self.clamp_in)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".tx",
                                                driver_value=self.value_up,
                                                output_attr=bsn_up + "." + crv_R_up_out_bshp,
                                                clamp=self.clamp_out)

            # set driver right low
            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".ty",
                                                driver_value=self.value_up,
                                                output_attr=bsn_low + "." + crv_R_low_top_bshp,
                                                clamp=self.clamp_top)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".ty",
                                                driver_value=self.value_down,
                                                output_attr=bsn_low + "." + crv_R_low_down_bshp,
                                                clamp=self.clamp_down)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".tx",
                                                driver_value=self.value_in,
                                                output_attr=bsn_low + "." + crv_R_low_in_bshp,
                                                clamp=self.clamp_in)

            utils.set_driver_blend_shape_single(input_attr=ctrl_main_right + ".tx",
                                                driver_value=self.value_up,
                                                output_attr=bsn_low + "." + crv_R_low_out_bshp,
                                                clamp=self.clamp_out)

        def create_mouth_mesh_blend_shape():
            if not self.enable_mesh_blend_shape:
                return None

            # add blendshape
            node_bsn = utils.add_or_create_blend_shape_node(list_target_mesh=self.list_shape_out + self.list_shape_up + self.list_shape_in + self.list_shape_low,
                                                            node_name="{}_bsn".format(self.list_target_shape))

            # add attributes
            attr_up_drive_value = "up_shape_driver_value"
            attr_up_drive_value_path = mouth_option_shape + "." + attr_up_drive_value

            attr_down_drive_value = "down_shape_driver_value"
            attr_down_drive_value_path = mouth_option_shape + "." + attr_down_drive_value

            attr_in_drive_value = "in_shape_driver_value"
            attr_in_drive_value_path = mouth_option_shape + "." + attr_in_drive_value

            attr_out_drive_value = "out_shape_driver_value"
            attr_out_drive_value_path = mouth_option_shape + "." + attr_out_drive_value

            # add new attribute
            cmds.addAttr(mouth_option_shape, ln=attr_up_drive_value, at="float", k=1, dv=1 / self.shape_up_driven_value)
            cmds.addAttr(mouth_option_shape, ln=attr_down_drive_value, at="float", k=1, dv=1 / self.shape_down_driven_value)
            cmds.addAttr(mouth_option_shape, ln=attr_in_drive_value, at="float", k=1, dv=1 / self.shape_in_driven_value)
            cmds.addAttr(mouth_option_shape, ln=attr_out_drive_value, at="float", k=1, dv=1 / self.shape_out_driven_value)

            # LEFT and right loops
            for i in range(2):
                # left
                if i == 0:
                    ctrl_main_driver = ctrl_main_left
                # right
                elif i == 1:
                    ctrl_main_driver = ctrl_main_right

                shape_up = self.list_shape_up[i]
                shape_low = self.list_shape_low[i]
                shape_in = self.list_shape_in[i]
                shape_out = self.list_shape_out[i]

                attr_driver_up = "{}.t{}".format(ctrl_main_driver, "y")
                attr_driver_in = "{}.t{}".format(ctrl_main_driver, "x")
                attr_driver_out = "{}.t{}".format(ctrl_main_driver, "x")
                attr_driver_low = "{}.t{}".format(ctrl_main_driver, "y")

                # set driven key
                utils.set_driver_node_fixed(attr_driver=attr_driver_up,
                                            attr_driven="{}.{}".format(node_bsn, shape_up),
                                            driven_value=attr_up_drive_value_path,
                                            name=self.name + "UpShape",
                                            clamp_length=[0, 1])

                utils.set_driver_node_fixed(attr_driver=attr_driver_low,
                                            attr_driven="{}.{}".format(node_bsn, shape_low),
                                            driven_value=attr_down_drive_value_path,
                                            name=self.name + "DownShape",
                                            clamp_length=[0, 1])

                utils.set_driver_node_fixed(attr_driver=attr_driver_in,
                                            attr_driven="{}.{}".format(node_bsn, shape_in),
                                            driven_value=attr_in_drive_value_path,
                                            name=self.name + "InShape",
                                            clamp_length=[0, 1])

                utils.set_driver_node_fixed(attr_driver=attr_driver_out,
                                            attr_driven="{}.{}".format(node_bsn, shape_out),
                                            driven_value=attr_out_drive_value_path,
                                            name=self.name + "OutShape",
                                            clamp_length=[0, 1])

        def make_finalize():
            if self.debug_mode:
                return None

            [utils.lock_attributes(control, s=1, v=1, l=1, k=0) for control in list_bind_up_control + list_bind_low_control]

            [utils.lock_attributes(control, s=1, v=1, l=1, k=0) for control in list_mid_up_control + list_mid_low_control]

            [utils.lock_attributes(control, s=1, v=1, l=1, k=0) for control in [ctrl_main_up, ctrl_main_left, ctrl_main_right, ctrl_main_low]]

            utils.lock_attributes(ctrl_mouth_global, v=1, k=0, l=1)

            cmds.setAttr(grp_mouth_curves + ".v", 0)

        # prepare hierarchies
        mouth_option_shape = "{}_option".format(self.name)
        grp_bind_control = "{}_sub_grp".format(self.name)
        grp_main_control = "{}_main_grp".format(self.name)
        grp_mid_control = "{}_mid_grp".format(self.name)
        grp_blendshape = "{}_curveBsn_grp".format(self.name)
        grp_mouth_curves = "{}_curve_grp".format(self.name)
        ctrl_mouth_global = "{}_global_ctrl".format(self.name)
        ctrl_jaw = "{}_ctrl".format(self.jnt_jaw)

        crv_bind_up = "{}_up_crv".format(self.name)
        crv_bind_low = "{}_low_crv".format(self.name)

        # main controls / main joints
        ctrl_main_left = "{}_{}_emotion_ctrl".format(self.name, L)
        ctrl_main_right = "{}_{}_emotion_ctrl".format(self.name, R)
        ctrl_main_up = "{}_baseUp_ctrl".format(self.name)
        ctrl_main_low = "{}_baseLow_ctrl".format(self.name)

        jnt_main_left = "{}_{}_emotion_jnt".format(self.name, L)
        jnt_main_right = "{}_{}_emotion_jnt".format(self.name, R)
        jnt_main_up = "{}_baseUp_jnt".format(self.name)
        jnt_main_low = "{}_baseLow_jnt".format(self.name)

        loc_main_left = "{}_{}_emotion_loc".format(self.name, L)
        loc_main_right = "{}_{}_emotion_loc".format(self.name, R)
        loc_main_up = "{}_baseUp_loc".format(self.name)
        loc_main_low = "{}_baseLow_loc".format(self.name)

        # mid controls
        list_mid_up_control = ["{}_{}_upMidLip2".format(ctrl, R),
                               "{}_{}_upMidLip1".format(ctrl, R),
                               "{}_{}_upMidLip".format(ctrl, center),
                               "{}_{}_upMidLip1".format(ctrl, L),
                               "{}_{}_upMidLip2".format(ctrl, L)]

        list_mid_low_control = ["{}_{}_lowMidLip1".format(ctrl, R),
                                "{}_{}_lowMidLip".format(ctrl, center),
                                "{}_{}_lowMidLip1".format(ctrl, L)]

        list_mid_up_joint = [name.replace(ctrl, jnt) for name in list_mid_up_control]
        list_mid_low_joint = [name.replace(ctrl, jnt) for name in list_mid_low_control]

        grp_corner_space = "{}_CornerDrv_grp".format(self.name)
        grp_up_space = "{}_baseUpDrv_grp".format(self.name)
        grp_low_space = "{}_baseLowDrv_grp".format(self.name)

        # bind controls
        list_bind_up_control = ["{}_{}".format(joint, ctrl) for joint in self.list_upper_bind]
        list_bind_low_control = ["{}_{}".format(joint, ctrl) for joint in self.list_lower_bind]

        list_bind_pin_up = []
        list_bind_pin_low = []

        grp_local_locator = "{}_local_locator_grp".format(grp)

        create_hierarchy()
        create_global_control()
        create_jaw()

        create_mouth_curves()

        create_bind_controls()

        create_mid_controls()
        pin_bind_controls()

        create_main_controls()
        pin_mid_controls()

        create_inner_mouth()

        create_zipper() if self.enable_zipper else None

        create_mouth_curve_blendshape()
        create_mouth_mesh_blend_shape()

        make_finalize()

class FacialSecondaryGlobal(rig_class.Rig):
    """
    Create Lips of mouth

    blend_shape_node_name(string) :  blend_shape_node_name
    mesh_blend_shape_target(string) :  mesh_blend_shape_target

    L_cheek_joint(string) : cheek joint
    L_enable_puff_blend_shape(bool) : enable puff blend shape
    L_list_blend_shape(stringArray) :  puff_in_blend_shape , puff_out_blend_shape

    R_cheek_joint(string) : cheek joint
    R_enable_puff_blend_shape(bool) : enable puff blend shape
    R_list_blend_shape(stringArray) :  puff_in_blend_shape , puff_out_blend_shape

    L_list_left_ear_chain(stringArray) : L_list_left_ear_chain
    R_list_left_ear_chain(stringArray) : R_list_left_ear_chain

    enable_nose_joint(bool) : enable_nose_joint
    L_nose_wing_joint(string) : L_nose_wing_joint
    R_nose_wing_joint(string) : R_nose_wing_joint
    nose_base_joint(string) : nose_base_joint
    nose_tip_joint(string) : nose_tip_joint
    """

    def __init__(self):
        super().__init__()

        self.name = "FacialSecondary"

        # @ Setting
        # $ Main Setting
        self.mesh_blend_shape_target = ""
        self.blend_shape_node_name = ""

        # $ Left Cheek
        self.L_cheek_joint = ""
        # -
        self.L_enable_puff_blend_shape = False
        self.L_list_blend_shape = []
        # * L_enable_puff_blend_shape

        # $ Right Cheek
        self.R_cheek_joint = ""
        # -
        self.R_enable_puff_blend_shape = False
        self.R_list_blend_shape = []
        # * R_enable_puff_blend_shape

        # $ Nose
        self.enable_nose_joint = False
        self.L_nose_wing_joint = ""
        self.R_nose_wing_joint = ""
        self.nose_base_joint = ""
        self.nose_tip_joint = ""
        # * enable_nose_joint

        # $ Left Ear
        self.L_list_left_ear_chain = []

        # $ Right Ear
        self.R_list_left_ear_chain = []

        self.parent = None
        self.debug_mode = False

    def core_build(self):
        def add_blend_shape():
            if not self.enable_puff_blend_shape:
                return

            if not cmds.objExists(self.puff_out_blend_shape) or not cmds.objExists(self.puff_in_blend_shape):
                raise Exception("Blend Shape Mesh Not Exist")

            cmds.addAttr(ctrl_cheek, ln="puff", min=-10, max=10, at="float", k=1)

            # out blend shape
            utils.set_blend_shape_expression(node_name=self.blend_shape_node_name,
                                             mesh_target=self.puff_out_blend_shape,
                                             mesh_base=self.mesh_blend_shape_target,
                                             driver_value=10,
                                             driver_attr=ctrl_cheek + ".puff",
                                             clamp_length=[0, 1],
                                             module_name=self.name)

            # in blend shape
            utils.set_blend_shape_expression(node_name=self.blend_shape_node_name,
                                             mesh_target=self.puff_in_blend_shape,
                                             mesh_base=self.mesh_blend_shape_target,
                                             driver_value=-10,
                                             driver_attr=ctrl_cheek + ".puff",
                                             clamp_length=[0, 1],
                                             module_name=self.name)

        def create_controls():
            utils.create_control(name=ctrl_cheek, match=self.cheek_joint, parent=self.grp_local_anim)
            grp_frz = utils.freeze_group_classic(ctrl_cheek, "grpCtrl")[0]

            cmds.setAttr(grp_frz + ".s", -1, -1, -1, typ="double3") if self.mirror_control_scale else None

            cmds.parentConstraint(ctrl_cheek, self.cheek_joint)
            cmds.connectAttr(ctrl_cheek + ".s", self.cheek_joint + ".s")

        def finalize():
            if not self.debug_mode:
                return None

            utils.lock_attributes(ctrl_cheek, v=1, l=1, k=0)

        ctrl_cheek = self.cheek_joint + "_ctrl"

        create_controls()
        add_blend_shape()
        finalize()

class Cheek(rig_class.Rig):
    """
    Create Lips of mouth

    cheek_joint(string) : cheek joint
    puff_in_blend_shape(string) :  puff_in_blend_shape
    puff_out_blend_shape(string) :  puff_out_blend_shape

    blend_shape_node_name(string) :  blend_shape_node_name
    mesh_blend_shape_target(string) :  mesh_blend_shape_target

    enable_puff_blend_shape(bool) : enable puff blendshape
    """

    def __init__(self):
        super().__init__()

        self.name = "LFT_Cheek"

        # @ Required
        # $ Global Joint
        self.cheek_joint = ""
        # $ Mesh Blend Shape
        self.enable_puff_blend_shape = False
        # -

        self.blend_shape_node_name = ""
        self.mesh_blend_shape_target = ""
        # -
        self.puff_in_blend_shape = ""
        self.puff_out_blend_shape = ""

        # * enable_puff_blend_shape

        self.debug_mode = False
        self.mirror_control_scale = False

    def core_build(self):
        def add_blend_shape():
            if not self.enable_puff_blend_shape:
                return

            if not cmds.objExists(self.puff_out_blend_shape) or not cmds.objExists(self.puff_in_blend_shape):
                raise Exception("Blend Shape Mesh Not Exist")

            cmds.addAttr(ctrl_cheek, ln="puff", min=-10, max=10, at="float", k=1)

            # out blend shape
            utils.set_blend_shape_expression(node_name=self.blend_shape_node_name,
                                             mesh_target=self.puff_out_blend_shape,
                                             mesh_base=self.mesh_blend_shape_target,
                                             driver_value=10,
                                             driver_attr=ctrl_cheek + ".puff",
                                             clamp_length=[0, 1],
                                             module_name=self.name)

            # in blend shape
            utils.set_blend_shape_expression(node_name=self.blend_shape_node_name,
                                             mesh_target=self.puff_in_blend_shape,
                                             mesh_base=self.mesh_blend_shape_target,
                                             driver_value=-10,
                                             driver_attr=ctrl_cheek + ".puff",
                                             clamp_length=[0, 1],
                                             module_name=self.name)

        def create_controls():
            utils.create_control(name=ctrl_cheek, match=self.cheek_joint, parent=self.grp_local_anim)
            grp_frz = utils.freeze_group_classic(ctrl_cheek, "grpCtrl")[0]

            cmds.setAttr(grp_frz + ".s", -1, -1, -1, typ="double3") if self.mirror_control_scale else None

            cmds.parentConstraint(ctrl_cheek, self.cheek_joint)
            cmds.connectAttr(ctrl_cheek + ".s", self.cheek_joint + ".s")

        def finalize():
            if not self.debug_mode:
                return None

            utils.lock_attributes(ctrl_cheek, v=1, l=1, k=0)

        ctrl_cheek = self.cheek_joint + "_ctrl"

        create_controls()
        add_blend_shape()
        finalize()


class Eyebrows(rig_class.Rig):
    """
    Create Lips of mouth

    list_left_brow_joints (stringArray) : left brow joints (sort inner > outer)
    list_right_brow_joints (stringArray) : right brow joints (sort inner > outer)

    middle_joint (string) : The Joint that will always point constraint between left and right brow.

    left_all_mover_pos_pivot (string) : the position of base control
    right_all_mover_pos_pivot (string) : the position of base control

    use_custom_base_control_position(bool) : Use Custom Base Control Position
    """

    def __init__(self):
        super().__init__()

        self.name = "Eyebrows"

        # @ Required
        # $ Global Joint
        self.list_left_brow_joints = []
        self.list_right_brow_joints = []
        self.middle_joint = ""

        # $ Custom Base Control Position
        self.use_custom_base_control_position = False
        self.left_all_mover_pos_pivot = ""
        self.right_all_mover_pos_pivot = ""
        # * use_custom_base_control_position

        self.debug_mode = False
        self.parent = ""

    def core_build(self):
        def create_base_control():
            # all mover control
            utils.create_control(name=ctrl_left_all_mover,
                                 parent=self.grp_local_anim,
                                 freeze_group=True,
                                 size=1.4,
                                 color="yellow")

            utils.create_control(name=ctrl_right_all_mover,
                                 parent=self.grp_local_anim,
                                 freeze_group=True,
                                 size=1.4,
                                 color="yellow")

            # flip right control
            cmds.setAttr(cmds.listRelatives(ctrl_right_all_mover,p=1)[0]+".sx",-1)

            # match position
            if self.use_custom_base_control_position:
                cmds.matchTransform(cmds.listRelatives(ctrl_left_all_mover,p=1)[0], self.left_all_mover_pos_pivot, pos=1)
                cmds.matchTransform(cmds.listRelatives(ctrl_right_all_mover,p=1)[0], self.right_all_mover_pos_pivot, pos=1)

            else:
                index_left = int(math.floor(float(len(self.list_left_brow_joints)/2)))
                index_right = int(math.floor(float(len(self.list_right_brow_joints)/2)))

                cmds.matchTransform(cmds.listRelatives(ctrl_left_all_mover,p=1)[0],self.list_left_brow_joints[index_left], pos=1)
                cmds.matchTransform(cmds.listRelatives(ctrl_right_all_mover,p=1)[0],self.list_right_brow_joints[index_right], pos=1)

        def create_control():
            # main control
            list_joints = self.list_left_brow_joints + self.list_right_brow_joints

            for i, control in enumerate(list_left_brow_control + list_right_brow_control):
                if control in list_right_brow_control:
                    mirror_freeze_group=True
                else:
                    mirror_freeze_group=False

                utils.create_control(control, match=list_joints[i],freeze_group=True,mirror_freeze_group=mirror_freeze_group, parent=self.grp_local_anim, constraint="parent")
                cmds.connectAttr(control + ".s", list_joints[i] + ".s")


            # parent main control to all mover control
            [cmds.parent(cmds.listRelatives(control,p=1)[0], ctrl_left_all_mover) for control in list_left_brow_control]
            [cmds.parent(cmds.listRelatives(control,p=1)[0], ctrl_right_all_mover) for control in list_right_brow_control]

        def create_middle_control():
            # middle control
            utils.create_control(name=ctrl_middle, match=self.middle_joint,constraint="parent", parent=self.grp_local_anim,size=0.8,color="blue",freeze_group=True)
            cmds.pointConstraint(list_left_brow_control[0], list_right_brow_control[0], utils.freeze_group_classic(ctrl_middle,"grpPoint"),mo=1)

        def finalize():
            if self.debug_mode:
                return None

            utils.lock_attributes(ctrl_left_all_mover, s=1, v=1)
            utils.lock_attributes(ctrl_right_all_mover, s=1, v=1)
            [utils.lock_attributes(control,s=1, v=1) for control in list_left_brow_control + list_right_brow_control]

        if not self.left_all_mover_pos_pivot or not self.right_all_mover_pos_pivot:
            cmds.confirmDialog(m="Require attributes ,{}".format(self.name))
        # grp_main_control
        list_left_brow_control = [utils.cname(None,joint,ctrl) for joint in self.list_left_brow_joints]
        list_right_brow_control = [utils.cname(None,joint,ctrl) for joint in self.list_right_brow_joints]

        ctrl_left_all_mover = utils.cname(self.name,"Left_Base",ctrl)
        ctrl_right_all_mover =  utils.cname(self.name,"Right_Base",ctrl)

        ctrl_middle = utils.cname(None,self.middle_joint,ctrl)

        create_base_control()
        create_control()
        create_middle_control()
        finalize()


class EyeLidCurveBased(rig_class.Rig):
    """
    Create Eye Lid systems

    Variables:
    jnt_eye_ball(string) : ""
    jnt_eye_global(string) : ""

    list_jnt_lid_upper(stringArray) : []
    list_jnt_lid_lower(stringArray) : []

    axis_up_eye_ball(enum) : "y"
    axis_aim_eye_ball(enum) : "z"

    list_main_control_pivot(stringArray) : []

    value_up_control_drive(float) : 3
    value_down_control_drive(float) : 3

    value_up_rotate_in(float) : 45
    value_down_rotate_in(float) : 45

    curve_blend_shape_up_rotate_in(string) : ""
    curve_blend_shape_up_rotate_out(string) : ""
    curve_blend_shape_up_push(string) : ""

    curve_blend_shape_down_rotate_in(string) : ""
    curve_blend_shape_down_rotate_out(string) : ""
    curve_blend_shape_low_push(string) : ""

    target_blend_shape(string) : ""

    mesh_blend_shape_up_push_volume(string) : ""
    mesh_blend_shape_up_rotate_in(string) : ""
    mesh_blend_shape_up_rotate_out(string) : ""

    mesh_blend_shape_down_push_volume(string) : ""
    mesh_blend_shape_down_rotate_in(string) : ""
    mesh_blend_shape_down_rotate_out(string) : ""

    enable_auto_fleshy(bool): False
    
    value_fleshy_up_intensity(float): 0.2
    value_fleshy_side_intensity(float): 0.2

    list_upper_outer_joint(stringArray) : []
    list_lower_outer_joint(stringArray) : []

    curve_up_weight_path(path): ""
    curve_low_weight_path(path): ""

    sync_option_shape_path(string): ""
    preserve_corner_joint_curve(bool): True

    list_eye_global_constraint(stringArray) : []
    """

    def __init__(self):
        self.name = "{}_EyeLid".format(L)

        # @ Setting
        # $ Global Joints
        self.jnt_eye_ball = ""
        self.jnt_eye_global = ""
        # -
        self.list_jnt_lid_upper = []
        self.list_jnt_lid_lower = []

        # -
        self.list_main_control_pivot = []

        # $ Axis Eye Aim
        self.axis_up_eye_ball = utils.get_single_axis_enum_pos()
        self.axis_aim_eye_ball = utils.get_single_axis_enum_pos()

        # $ Auto Fleshy
        self.enable_auto_fleshy = False
        # -
        self.value_fleshy_up_intensity = 0.2
        self.value_fleshy_side_intensity = 0.2
        # *enable_auto_fleshy

        # @ Optional
        # $ Blend Shape Values Setting
        self.value_up_control_drive = 3
        self.value_down_control_drive = 3

        self.value_up_rotate_in = 45
        self.value_down_rotate_in = 45

        # $ Curve Blend Shape
        self.curve_blend_shape_up_rotate_in = ""
        self.curve_blend_shape_up_rotate_out = ""
        self.curve_blend_shape_up_push = ""
        # -
        self.curve_blend_shape_down_rotate_in = ""
        self.curve_blend_shape_down_rotate_out = ""
        self.curve_blend_shape_low_push = ""

        # $ Mesh Blend Shape
        self.target_blend_shape = ""
        # -
        self.mesh_blend_shape_up_push_volume = ""
        self.mesh_blend_shape_up_rotate_in = ""
        self.mesh_blend_shape_up_rotate_out = ""

        # -
        self.mesh_blend_shape_down_push_volume = ""
        self.mesh_blend_shape_down_rotate_in = ""
        self.mesh_blend_shape_down_rotate_out = ""



        # $ Outer Eye Lid
        self.list_upper_outer_joint = []
        self.list_lower_outer_joint = []

        # $ Auto Import Curve Weight
        self.curve_up_weight_path = ""
        self.curve_low_weight_path = ""

        # $ Optional
        self.sync_option_shape_path = ""
        self.preserve_corner_joint_curve = True

        self.list_eye_global_constraint = []

        self.parent = ""
        self.mirror_control_scale = False
        self.debug_mode = False

    def core_build(self):
        def create_outer_joints():
            grp_outer_control = cmds.group(n="{}_outer_grp".format(self.name), em=1, p=ctrl_global)

            for joint in self.list_upper_outer_joint + self.list_lower_outer_joint:
                control = joint + "_ctrl"
                utils.create_control(control, match=joint, parent=grp_outer_control, constraint="parent")

                utils.freeze_group_classic(control)

        def set_joint_scale_compensate():
            # set scale compensate for lid joints
            for joint in self.list_jnt_lid_upper + self.list_jnt_lid_lower + [self.jnt_eye_global, self.jnt_eye_ball]:
                cmds.setAttr(joint + ".segmentScaleCompensate", 0)

        def create_global_control():
            # Create Controller --------------------------------------------------
            # create ctrl global
            utils.create_control(name=ctrl_global, match=self.jnt_eye_global, parent=self.grp_local_anim,color="yellow",size=3.5)
            grp_frz = utils.freeze_group_classic(ctrl_global, "grpFrz")[0]
            cmds.setAttr("{}.s".format(grp_frz), -1, -1, -1, typ="double3") if self.mirror_control_scale else None

            cmds.parentConstraint(ctrl_global, self.jnt_eye_global, mo=1)

            if self.list_eye_global_constraint:
                for each in self.list_eye_global_constraint:
                    cmds.parentConstraint(ctrl_global, each, mo=1)

            # create option shape
            utils.add_option_shape(ctrl_global, ctrl_global_option)

            cmds.addAttr(ctrl_global_option, ln=attr_fleshy_vertical.split(".")[-1], dv=self.value_fleshy_up_intensity, at="float", k=1)
            cmds.addAttr(ctrl_global_option, ln=attr_fleshy_horizontal.split(".")[-1], dv=self.value_fleshy_side_intensity, at="float", k=1)
            cmds.addAttr(ctrl_global_option, ln=attr_driver_up.split(".")[-1], at="float", k=1, dv=3)
            cmds.addAttr(ctrl_global_option, ln=attr_driver_low.split(".")[-1], at="float", k=1, dv=3)

            # connect scale
            cmds.scaleConstraint(ctrl_global, self.jnt_eye_global, mo=1)

        def create_eye_ball_control():
            # Create Controller --------------------------------------------------
            # create ctrl global
            utils.create_control(name=ctrl_eye_ball, match=self.jnt_eye_ball, parent=ctrl_global,size=3,color="blue")
            # grp_frz = utils.freeze_group_classic(ctrl_eye_ball, "grpFrz")[0]
            # cmds.setAttr("{}.s".format(grp_frz), 1, 1, -1, typ="double3") if self.mirror_control_scale else None

            # cmds.parentConstraint(ctrl_eye_ball, self.jnt_eye_ball, mo=1)

            utils.reset_all_transform(ctrl_eye_ball)
            grp_frz = utils.freeze_group_classic(ctrl_eye_ball, "grpFrz")[0]

            # create group under control
            cmds.group(em=1, n=grp_sub_control.format(self.name), p=ctrl_eye_ball)
            cmds.setAttr(grp_sub_control + ".inheritsTransform", 0)

            cmds.group(em=1, n=grp_slide_joint, p=ctrl_eye_ball)

            cmds.group(em=1, n=grp_main_control, p=ctrl_eye_ball)

            cmds.group(em=1, n=grp_fleshy_up_down, p=grp_main_control)
            cmds.group(em=1, n=grp_fleshy_side, p=grp_main_control)

            # cmds.matchTransform(grp_sub_control, ctrl_eye_ball)
            cmds.matchTransform(grp_slide_joint, ctrl_eye_ball)
            cmds.matchTransform(grp_main_control, ctrl_eye_ball)

            # connect fleshy
            if self.enable_auto_fleshy:
                node_fleshy_up_md = cmds.createNode("multiplyDivide", n="{}_fleshy_up_md".format(self.name))
                cmds.connectAttr(self.jnt_eye_ball + ".r", node_fleshy_up_md + ".input1")
                cmds.connectAttr(attr_fleshy_vertical, node_fleshy_up_md + ".input2X")
                cmds.connectAttr(attr_fleshy_vertical, node_fleshy_up_md + ".input2Y")
                cmds.connectAttr(attr_fleshy_vertical, node_fleshy_up_md + ".input2Z")

                cmds.connectAttr(node_fleshy_up_md + ".output", grp_fleshy_up_down + ".r")

                node_fleshy_side_md = cmds.createNode("multiplyDivide", n="{}_fleshy_up_md".format(self.name))
                cmds.connectAttr(self.jnt_eye_ball + ".r", node_fleshy_side_md + ".input1")
                cmds.connectAttr(attr_fleshy_horizontal, node_fleshy_side_md + ".input2X")
                cmds.connectAttr(attr_fleshy_horizontal, node_fleshy_side_md + ".input2Y")
                cmds.connectAttr(attr_fleshy_horizontal, node_fleshy_side_md + ".input2Z")

                cmds.connectAttr(node_fleshy_side_md + ".output", grp_fleshy_side + ".r")

            # connect scale
            cmds.scaleConstraint(ctrl_eye_ball, self.jnt_eye_ball, mo=1)

        def create_curves():
            # sub curve
            degree = 2
            rebuild = True
            spans = 6
            rebuild_degree = 3

            # up curve
            for name in [crv_bind_up]:
                utils.draw_curve(list_items=self.list_jnt_lid_upper, curve_name=name, parent=grp_curves, d=degree, rebuild=rebuild, s=spans, rebuild_degree=rebuild_degree)
                cmds.rename(cmds.listRelatives(name, c=1, s=1, typ="nurbsCurve")[0], name + "Shape")

            # low curve
            for name in [crv_bind_low]:
                utils.draw_curve(list_items=[self.list_jnt_lid_upper[0]] + self.list_jnt_lid_lower + [self.list_jnt_lid_upper[-1]], curve_name=name, parent=grp_curves, d=degree, rebuild=rebuild,
                                 s=spans,
                                 rebuild_degree=rebuild_degree)
                cmds.rename(cmds.listRelatives(name, c=1, s=1, typ="nurbsCurve")[0], name + "Shape")

        def pin_bind_controls():
            list_bind_pin_up = []
            list_bind_pin_low = []

            # bind mid joint to curve
            node_bind_up = cmds.skinCluster(jnt_main_inner, jnt_main_up, jnt_main_outer, crv_bind_up, ih=1, dr=10, bm=3, mi=3)
            node_bind_low = cmds.skinCluster(jnt_main_inner, jnt_main_low, jnt_main_outer, crv_bind_low, ih=1, dr=10, bm=3, mi=3)

            # auto import weight
            utils.import_weight(node_bind_up, self.curve_up_weight_path) if self.curve_up_weight_path else None
            utils.import_weight(node_bind_low, self.curve_low_weight_path) if self.curve_low_weight_path else None

            # constraint translate to items by curve
            for control in list_bind_up_control:
                grp_pin = cmds.group(em=1, n=control.replace(ctrl, "grpPin"), p=grp_sub_control)
                cmds.matchTransform(grp_pin, control)
                list_bind_pin_up.append(grp_pin)

            for control in list_bind_low_control:
                grp_pin = cmds.group(em=1, n=control.replace(ctrl, "grpPin"), p=grp_sub_control)
                cmds.matchTransform(grp_pin, control)
                list_bind_pin_low.append(grp_pin)

            utils.pin_curve_by_distance(list_bind_pin_up, crv_bind_up, maintainOffset=False)
            utils.pin_curve_by_distance(list_bind_pin_low, crv_bind_low, maintainOffset=False)

            # create scale constraint space
            grp_scale_space = cmds.group(em=1, n="{}_bind_scale_space_grp".format(self.name), p=grp_sub_control)
            cmds.scaleConstraint(self.grp_local_anim, grp_scale_space)

            grp_orient_space = cmds.group(em=1, n="{}_bind_orient_space_grp".format(self.name), p=grp_sub_control)
            cmds.orientConstraint(ctrl_eye_ball, grp_orient_space)
            utils.freeze_group_classic(grp_orient_space,"grpOrient")

            # constraint orient and translate to control offset
            list_grp_pin = list_bind_pin_up + list_bind_pin_low
            list_bind_control = list_bind_up_control + list_bind_low_control

            for i in range(len(list_grp_pin)):
                control = list_bind_control[i]
                grp_pin = list_grp_pin[i]

                cmds.parent(control, grp_pin)
                grp_frz = utils.freeze_group_classic(control)[0]

                cmds.orientConstraint(ctrl_eye_ball, grp_pin, mo=1)

                cmds.scaleConstraint(self.grp_local_anim, grp_pin, mo=1)

                # cmds.connectAttr(grp_scale_space + ".s", grp_pin + ".s")
                # cmds.connectAttr(grp_orient_space + ".r", grp_pin + ".r")

                if self.mirror_control_scale:
                    cmds.setAttr(grp_frz + ".s", -1, -1, -1, typ="double3")

        def create_blendshape():
            def create_blendshape_each(blendshape, target, driver_value, attr_driver, isClamp=True, custom_clamp_length=[0, 1]):
                if not target:
                    raise Exception("Target Blendshape Invalid")

                # add new attribute
                attr_factor_name = "{}_intensity".format(blendshape)
                attr_factor_path = "{}.{}_intensity".format(ctrl_global_option, blendshape)

                cmds.addAttr(ctrl_global_option, ln=attr_factor_name, at="float", k=1, dv=1 / driver_value)

                node_bsn = utils.add_or_create_blend_shape_node(list_target_mesh=[blendshape], node_name="{}_bsn".format(target))

                if isClamp:
                    clamp_length = custom_clamp_length
                else:
                    clamp_length = None

                utils.set_driver_node_fixed(attr_driver=attr_driver,
                                            attr_driven="{}.{}".format(node_bsn, blendshape),
                                            driven_value=attr_factor_path,
                                            name=self.name + "UpShape",
                                            clamp_length=clamp_length)

            # curve blendshape
            create_blendshape_each(self.curve_blend_shape_up_rotate_in, crv_bind_up, -45, attr_driver=ctrl_main_up + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blend_shape_up_rotate_in else None
            create_blendshape_each(self.curve_blend_shape_up_rotate_out, crv_bind_up, 45, attr_driver=ctrl_main_up + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blend_shape_up_rotate_out else None
            create_blendshape_each(self.curve_blend_shape_down_rotate_in, crv_bind_low, -45, attr_driver=ctrl_main_low + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blend_shape_down_rotate_in else None
            create_blendshape_each(self.curve_blend_shape_down_rotate_out, crv_bind_low, 45, attr_driver=ctrl_main_low + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blend_shape_down_rotate_out else None

            create_blendshape_each(self.curve_blend_shape_up_push, crv_bind_up, self.value_up_control_drive, attr_driver=ctrl_main_up + ".ty",
                                   isClamp=True) if self.curve_blend_shape_up_push else None
            create_blendshape_each(self.curve_blend_shape_low_push, crv_bind_low, self.value_down_control_drive, attr_driver=ctrl_main_low + ".ty",
                                   isClamp=True) if self.curve_blend_shape_low_push else None

            # mesh blendshape
            create_blendshape_each(self.mesh_blend_shape_up_push_volume, self.target_blend_shape, self.value_up_control_drive,
                                   attr_driver=ctrl_main_up + ".ty") if self.mesh_blend_shape_up_push_volume else None
            create_blendshape_each(self.mesh_blend_shape_down_push_volume, self.target_blend_shape, self.value_down_control_drive,
                                   attr_driver=ctrl_main_low + ".ty") if self.mesh_blend_shape_down_push_volume else None

            create_blendshape_each(self.mesh_blend_shape_up_rotate_in, self.target_blend_shape, self.value_up_rotate_in,
                                   attr_driver=ctrl_main_up + ".rz") if self.mesh_blend_shape_up_rotate_in else None
            create_blendshape_each(self.mesh_blend_shape_up_rotate_out, self.target_blend_shape, self.value_up_rotate_in * -1,
                                   attr_driver=ctrl_main_up + ".rz") if self.mesh_blend_shape_up_rotate_out else None

            create_blendshape_each(self.mesh_blend_shape_down_rotate_in, self.target_blend_shape, self.value_down_rotate_in,
                                   attr_driver=ctrl_main_low + ".rz") if self.mesh_blend_shape_down_rotate_in else None
            create_blendshape_each(self.mesh_blend_shape_down_rotate_out, self.target_blend_shape, self.value_down_rotate_in * -1,
                                   attr_driver=ctrl_main_low + ".rz") if self.mesh_blend_shape_down_rotate_out else None

        def create_main_control():
            # create upper,lower main ctrl
            list_main_ctrl = [ctrl_main_up, ctrl_main_outer, ctrl_main_inner, ctrl_main_low]

            utils.create_control(name=ctrl_main_up, parent=grp_fleshy_up_down,size=0.3,color="yellow")
            utils.create_control(name=ctrl_main_low, parent=grp_fleshy_up_down,size=0.3,color="yellow")

            utils.create_control(name=ctrl_main_outer, parent=grp_fleshy_side,size=0.3,color="yellow")
            utils.create_control(name=ctrl_main_inner, parent=grp_fleshy_side,size=0.3,color="yellow")

            # match position of pivot
            pivot_ctrl_inner_main, pivot_ctrl_up_main, pivot_ctrl_outer_main, pivot_ctrl_low_main = self.list_main_control_pivot

            cmds.matchTransform(ctrl_main_up, pivot_ctrl_up_main, pos=1)
            cmds.matchTransform(ctrl_main_low, pivot_ctrl_low_main, pos=1)
            cmds.matchTransform(ctrl_main_inner, pivot_ctrl_inner_main, pos=1)
            cmds.matchTransform(ctrl_main_outer, pivot_ctrl_outer_main, pos=1)

            cmds.matchTransform(ctrl_main_low, self.jnt_eye_ball, rot=1)
            cmds.matchTransform(ctrl_main_up, self.jnt_eye_ball, rot=1)
            cmds.matchTransform(ctrl_main_inner, self.jnt_eye_ball, rot=1)
            cmds.matchTransform(ctrl_main_outer, self.jnt_eye_ball, rot=1)

            old_value_aim = cmds.getAttr(ctrl_main_up + ".r{}".format(self.axis_aim_eye_ball))
            old_value_up = cmds.getAttr(ctrl_main_up + ".r{}".format(self.axis_up_eye_ball))

            # cmds.setAttr(ctrl_main_up + ".r{}".format(self.axis_aim_eye_ball), old_value_aim + 180)
            # cmds.setAttr(ctrl_main_up + ".r{}".format(self.axis_up_eye_ball), old_value_up + 180)

            list_grp_freeze = utils.freeze_group_classic(list_main_ctrl)

            # if self.mirror_control_scale:
            #     for group in list_grp_freeze:
            #         cmds.setAttr("{}.s".format(group), -1, -1, -1, typ="double3")

            for i, joint in enumerate([jnt_main_up, jnt_main_outer, jnt_main_inner, jnt_main_low]):
                cmds.joint(name=joint)
                utils.match_parent(joint, list_main_ctrl[i])

        def make_finalize():
            if self.sync_option_shape_path:
                utils.connect_matching_attributes(self.sync_option_shape_path, ctrl_global_option)

            if self.debug_mode:
                return None

            utils.lock_attributes(ctrl_global, v=1, l=1, k=0)
            utils.lock_attributes(ctrl_eye_ball, v=1, l=1, k=0)

            [utils.lock_attributes(control, v=1, r=1, l=1, k=0) for control in list_bind_up_control + list_bind_low_control]
            [cmds.setAttr(control + ".tz", l=1, k=0) for control in list_bind_up_control + list_bind_low_control]

            [cmds.setAttr(control + ".tz", l=1, k=0) for control in [ctrl_main_up, ctrl_main_low, ctrl_main_outer, ctrl_main_inner]]
            [cmds.setAttr(control + ".rx", l=1, k=0) for control in [ctrl_main_up, ctrl_main_low, ctrl_main_outer, ctrl_main_inner]]
            [cmds.setAttr(control + ".ry", l=1, k=0) for control in [ctrl_main_up, ctrl_main_low, ctrl_main_outer, ctrl_main_inner]]

            [utils.lock_attributes(control, v=1, s=1, l=1, k=0) for control in list_ctrl_lid_upper + list_ctrl_lid_lower]

        def create_slider_joint():
            def create_joint(list_joint, list_control):
                for i, joint in enumerate(list_joint):
                    # create joint chain
                    cmds.select(cl=1)
                    jnt_A = cmds.joint(n=joint + "_slideA_jnt")
                    jnt_B = cmds.joint(n=joint + "_slideB_jnt")

                    cmds.matchTransform(jnt_A, self.jnt_eye_ball)
                    cmds.matchTransform(jnt_B, joint)

                    cmds.makeIdentity(jnt_A, a=1, s=1, r=1)

                    cmds.parent(jnt_A, grp_slide_joint)

                    # create ik handle
                    loc_aim = cmds.spaceLocator(n=joint + "_aim_loc")
                    cmds.matchTransform(loc_aim, jnt_B, pos=1)

                    # create controller
                    control = utils.create_control(name=list_control[i], parent=grp_sub_control, match=joint,size=0.25,color="blue")

                    cmds.parent(loc_aim, control)

                    cmds.parentConstraint(jnt_B, joint)

                    if self.mirror_control_scale:
                        aim = [0, 0, -1]
                        u = [-1, 0, 0]
                        wu = [-1, 0, 0]
                    else:
                        aim = [0, 0, 1]
                        u = [1, 0, 0]
                        wu = [1, 0, 0]

                    cmds.aimConstraint(loc_aim, jnt_A, mo=1, aim=aim, u=u, wuo=loc_aim_up_space, wut="objectrotation", wu=wu)

            create_joint(self.list_jnt_lid_upper, list_bind_up_control)
            create_joint(self.list_jnt_lid_lower, list_bind_low_control)

        def create_hierarchy():
            cmds.group(em=1, n=grp_curves, p=self.grp_local_still)

            cmds.spaceLocator(n=loc_aim_up_space)
            utils.match_parent(loc_aim_up_space, self.grp_local_anim)

        # variables
        self.axis_up_eye_ball = utils.convert_single_axis_enum_pos(self.axis_up_eye_ball)
        self.axis_aim_eye_ball = utils.convert_single_axis_enum_pos(self.axis_aim_eye_ball)
        axis_side = utils.get_exist_axis(self.axis_up_eye_ball,self.axis_aim_eye_ball)

        grp_sub_up_control = "{}_sub_up_control_grp".format(self.name)
        grp_sub_low_control = "{}_sub_low_control_grp".format(self.name)

        ctrl_eye_ball = "{}_{}_eyeBall".format(ctrl, self.name)
        ctrl_global = "{}_{}_AllMover".format(ctrl, self.name)

        ctrl_main_up = "{}_mainUp_{}".format(self.name, ctrl)
        ctrl_main_low = "{}_mainLow_{}".format(self.name, ctrl)
        ctrl_main_inner = "{}_mainInner_{}".format(self.name, ctrl)
        ctrl_main_outer = "{}_mainOuter_{}".format(self.name, ctrl)

        jnt_main_up = "{}_mainUp_{}".format(self.name, jnt)
        jnt_main_low = "{}_mainLow_{}".format(self.name, jnt)
        jnt_main_inner = "{}_mainInner_{}".format(self.name, jnt)
        jnt_main_outer = "{}_mainOuter_{}".format(self.name, jnt)

        crv_bind_up = "{}_bindUp_crv".format(self.name)
        crv_bind_low = "{}_bindLow_crv".format(self.name)

        attr_blink_up_output = None
        attr_blink_low_output = None

        list_slider_joint_up = []
        list_slider_joint_low = []

        loc_aim_up_space = "{}_aim_up_space_loc".format(self.name)

        list_bind_up_control = [joint + "_ctrl" for joint in self.list_jnt_lid_upper]
        list_bind_low_control = [joint + "_ctrl" for joint in self.list_jnt_lid_lower]

        # add custom attribute key
        ctrl_global_option = "{}_optionShape".format(self.name)

        attr_fleshy_vertical = "{}.fleshyX".format(ctrl_global_option)
        attr_fleshy_horizontal = "{}.fleshyY".format(ctrl_global_option)
        attr_fleshy_z = "{}.fleshyZ".format(ctrl_global_option)
        attr_driver_up = "{}.closedUpValue".format(ctrl_global_option)
        attr_driver_low = "{}.closedLowValue".format(ctrl_global_option)

        grp_fleshy_up_down = "{}_fleshy_up_down_grp".format(self.name)
        grp_fleshy_side = "{}_fleshy_side_grp".format(self.name)

        # create groups
        grp_main_control = "{}_mainCtl_grp".format(self.name)
        grp_sub_control = "{}_subCtl_grp".format(self.name)
        grp_slide_joint = "{}_slideCtl_grp".format(self.name)

        grp_curves = "{}_curves_grp".format(self.name)

        list_up_drive_output_grp = ["{}_grpDriveUp".format(joint) for joint in self.list_jnt_lid_upper]
        list_low_drive_output_grp = ["{}_grpDriveLow".format(joint) for joint in self.list_jnt_lid_lower]

        list_ctrl_lid_upper = []
        list_ctrl_lid_lower = []

        # Build
        create_hierarchy()
        create_curves()

        set_joint_scale_compensate()

        create_global_control()
        create_eye_ball_control()

        create_main_control()

        create_slider_joint()
        pin_bind_controls()

        # extra
        create_blendshape()

        create_outer_joints()

        make_finalize()


class EyeLash(rig_class.Rig):
    """
    Create Eye Lid systems

    Variables:
eye_ball_joint (string) : Eye ball joint name

amount_eye_slide_joint (long) : Number of eye slide joints

locator_start_radius (string) : Locator start radius
locator_end_radius (string) : Locator end radius
flip_scale (bool) : Flip scale toggle

list_pupil_joint (stringArray) : List of pupil joint names

joint_iris_loop_edge (string) : Iris loop edge joint name
joint_pupil_loop_edge (string) : Pupil loop edge joint name

enable_specular_rig (bool) : Enable specular rigging
specular_joint (string) : Specular joint name
specular_pitch_axis (string) : Specular pitch axis
specular_yaw_axis (string) : Specular yaw axis
specular_pitch_axis_invert (bool) : Invert pitch axis
specular_yaw_axis_invert (bool) : Invert yaw axis
value_unit_conversion (float) : Value for unit conversion
specular_roll_axis_invert (bool) : Invert roll axis

left_eye_joint (string) : Left eye joint name
left_eye_aim_axis (string) : Aim axis for left eye
left_eye_up_axis (string) : Up axis for left eye

right_eye_joint (string) : Right eye joint name
right_eye_aim_axis (string) : Aim axis for right eye
right_eye_up_axis (string) : Up axis for right eye

distance (long) : Distance value
distance_direction (string) : Direction of the distance

left_eye_control_pivot (string) : Pivot control for left eye
right_eye_control_pivot (string) : Pivot control for right eye

jnt_mouth_global (string) : Mouth global joint name

list_upper_bind (stringArray) : List of upper bind joint names
list_lower_bind (stringArray) : List of lower bind joint names

jnt_jaw (string) : Jaw joint name

use_custom_main_pivot (bool) : Use custom main pivot toggle
list_custom_main_pivot (stringArray) : List of custom main pivot names

parent (string) : Parent node name

list_teeth_up (stringArray) : List of upper teeth names
list_teeth_low (stringArray) : List of lower teeth names

list_tongue_joints_chain (stringArray) : List of tongue joint chain names

enable_curve_blendshape (bool) : Enable curve blend shape toggle
list_curve_up (stringArray) : List of upper curve names
list_curve_low (stringArray) : List of lower curve names

value_up (long) : Value for upward movement
value_down (long) : Value for downward movement
value_out (long) : Value for outward movement
value_in (long) : Value for inward movement

clamp_top (bool) : Clamp top movement
clamp_down (bool) : Clamp down movement
clamp_in (bool) : Clamp inward movement
clamp_out (bool) : Clamp outward movement

enable_mesh_blend_shape (bool) : Enable mesh blend shape toggle
list_shape_up (stringArray) : List of upper shape names
list_shape_low (stringArray) : List of lower shape names
list_shape_in (stringArray) : List of inward shape names
list_shape_out (stringArray) : List of outward shape names

shape_up_driven_value (long) : Driven value for upper shape
shape_down_driven_value (long) : Driven value for lower shape
shape_in_driven_value (long) : Driven value for inward shape
shape_out_driven_value (long) : Driven value for outward shape

list_target_shape (stringArray) : List of target shape names
exist_blendshape_mesh (string) : Existing blend shape mesh name

enable_auto_push (bool) : Enable auto push toggle
jaw_push_rotate_axis (string) : Rotation axis for jaw push
invert_push_axis (bool) : Invert push axis toggle
value_start_push (long) : Start value for push

axis_side_push_in (string) : Axis for inward side push
side_parent_intensity (float) : Intensity for parent side movement
side_control_intensity (float) : Intensity for control side movement

curve_up_weight_path (string) : File class_instance for upper curve weights
curve_low_weight_path (string) : File class_instance for lower curve weights

enable_zipper (bool) : Enable zipper toggle
mirror_control_scale (bool) : Mirror scale controls toggle
debug_mode (bool) : Debug mode toggle

list_bind_joint (stringArray) : List of bind joint names
list_vertices_name (stringArray) : List of vertices names

parent (string) : Parent node name
parent_rotate_root (string) : Parent rotate root node

target_blend_shape (string) : Target blend shape name
custom_exist_blendshape_node (string) : Custom existing blend shape node name

mesh_blend_shape_up_push_volume (string) : Mesh blend shape for upward push volume
mesh_blend_shape_up_rotate_in (string) : Mesh blend shape for upward inward rotation
mesh_blend_shape_up_rotate_out (string) : Mesh blend shape for upward outward rotation

ctrl_main_up (string) : Main control for upward movement
ctrl_global (string) : Global control name

value_up_control_drive (long) : Control drive value for upward movement
value_up_rotate_in (long) : Rotate in value for upward movement

debug_mode (bool) : Debug mode toggle


    """

    def __init__(self):
        super().__init__()

        self.name = "{}_eyeLash".format(L)

        # @ Required
        # $ Global Joint
        self.list_bind_joint = []
        # $ Vertices
        self.list_vertices_name = []
        # -
        self.parent_rotate_root = ""

        # $ Mesh Blend Shape
        self.target_blend_shape = ""
        self.custom_exist_blendshape_node = ""
        # -
        self.mesh_blend_shape_up_push_volume = ""
        self.mesh_blend_shape_up_rotate_in = ""
        self.mesh_blend_shape_up_rotate_out = ""
        # -
        self.ctrl_main_up = ""
        self.ctrl_global = ""
        # -
        self.value_up_control_drive = 5
        self.value_up_rotate_in = 45

        self.debug_mode = False
        self.parent = ""

    def core_build(self):
        def create_blendshape():
            def create_blendshape_each(blendshape, target, driver_value, attr_driver, isClamp=True, custom_clamp_length=[0, 1]):
                # add new attribute
                attr_factor_name = "{}_intensity".format(blendshape)
                attr_factor_path = "{}.{}_intensity".format(ctrl_global_option, blendshape)

                cmds.addAttr(ctrl_global_option, ln=attr_factor_name, at="float", k=1)
                cmds.setAttr(attr_factor_path, 1 / driver_value)

                node_name = self.custom_exist_blendshape_node if self.custom_exist_blendshape_node else "{}_bsn".format(self.name)

                node_bsn = utils.add_or_create_blend_shape_node(list_target_mesh=[blendshape], base_mesh=target, node_name=node_name)

                if isClamp:
                    clamp_length = custom_clamp_length
                else:
                    clamp_length = None

                utils.set_driver_node_fixed(attr_driver=attr_driver,
                                            attr_driven="{}.{}".format(node_bsn, blendshape),
                                            driven_value=attr_factor_path,
                                            name=self.name + "UpShape",
                                            clamp_length=clamp_length)

            # add option control
            ctrl_global_option = utils.add_option_shape(list_bind_control[0], "{}_eyelash_setting".format(self.name))

            # mesh blendshape
            create_blendshape_each(self.mesh_blend_shape_up_push_volume, self.target_blend_shape, self.value_up_control_drive,
                                   attr_driver=self.ctrl_main_up + ".ty") if self.mesh_blend_shape_up_push_volume else None
            create_blendshape_each(self.mesh_blend_shape_up_rotate_in, self.target_blend_shape, self.value_up_rotate_in,
                                   attr_driver=self.ctrl_main_up + ".rz") if self.mesh_blend_shape_up_rotate_in else None
            create_blendshape_each(self.mesh_blend_shape_up_rotate_out, self.target_blend_shape, self.value_up_rotate_in * -1,
                                   attr_driver=self.ctrl_main_up + ".rz") if self.mesh_blend_shape_up_rotate_out else None

        list_new_vertices = []
        for item in self.list_vertices_name:
            list_new_vertices += utils.extract_vertices(item)

        self.list_vertices_name = list_new_vertices

        if len(self.list_bind_joint) != len(self.list_vertices_name):
            raise Exception("Invalid")

        grp_bind_control = "{}_control_grp".format(self.name)
        grp_joint_slide = "{}_slider_grp".format(self.name)
        grp_aim_locator = "{}_aim_grp".format(self.name)
        loc_aim_up_space = "{}_up_loc".format(self.name)

        joint_amount = len(self.list_bind_joint)

        list_joint_slide_A = []
        list_joint_slide_B = []
        list_rivet = []

        list_bind_control = [joint + "_ctrl" for joint in self.list_bind_joint]

        # create hierarchy
        cmds.group(em=1, n=grp_joint_slide, p=self.grp_local_anim)
        cmds.group(em=1, n=grp_aim_locator, p=self.grp_local_anim)
        cmds.group(em=1, n=grp_bind_control, p=self.grp_local_anim)

        cmds.parentConstraint(self.parent, self.grp_local_anim)
        cmds.parentConstraint(self.parent_rotate_root, grp_joint_slide)

        cmds.spaceLocator(n=loc_aim_up_space)
        cmds.parent(loc_aim_up_space, self.grp_local_anim)

        # create controller
        for i in range(joint_amount):
            utils.create_control(name=list_bind_control[i], match=self.list_bind_joint[i], parent=grp_bind_control, constraint="parent")

        # create slider joint
        for joint in self.list_bind_joint:
            cmds.select(cl=1)
            jointA = cmds.joint(n=joint + "SliderA")
            jointB = cmds.joint(n=joint + "SliderB")

            cmds.matchTransform(jointA, self.parent_rotate_root, pos=1)
            cmds.matchTransform(jointB, joint, pos=1)

            cmds.parent(jointA, grp_joint_slide)

            list_joint_slide_A.append(jointA)
            list_joint_slide_B.append(jointB)

        # create aim target
        for i in range(joint_amount):
            vertices_path = self.list_vertices_name[i]
            cmds.select(vertices_path)

            pin, output = utils.returnRivet()

            print(pin, output)
            output = cmds.rename(output, "{}_rivet_{}".format(self.name, i + 1))
            cmds.parent(output, grp_aim_locator)

            list_rivet.append(output)

            # aim constraint
            cmds.aimConstraint(output, list_joint_slide_A[i], mo=1, aim=[0, 0, 1], u=[1, 0, 0], wuo=loc_aim_up_space, wut="objectrotation", wu=[1, 0, 0])

        # apply
        for i in range(joint_amount):
            grp_offset_drive = utils.freeze_group_classic(list_bind_control[i])[0]
            grp_offset = utils.freeze_group_classic(grp_offset_drive, "grpDrv")[0]

            cmds.orientConstraint(list_joint_slide_A[i], grp_offset, mo=1)
            cmds.pointConstraint(list_rivet[i], grp_offset, mo=1)

        create_blendshape()

class EyeDetail(rig_class.Rig):
    """
    Eye Global Aim

    Will Aim Global Eye

    Variables:
    eye_ball_joint (string) : An Eyeball Joint

    amount_eye_slide_joint (long) : Amount of Eye Slide Joint Based On Spherical

    locator_start_radius (string) : locator_start_radius
    locator_end_radius (string) :locator_end_radius
    flip_scale (bool) :flip_scale

    list_pupil_joint (stringArray) :list_pupil_joint

    joint_iris_loop_edge (string) :joint_iris_loop_edge
    joint_pupil_loop_edge (string) :joint_pupil_loop_edge

    enable_specular_rig (bool) :enable_specular_rig
    specular_joint (string) :specular_joint
    specular_pitch_axis (string) :specular_pitch_axis
    specular_yaw_axis (string) :specular_yaw_axis
    specular_pitch_axis_invert (bool) :specular_pitch_axis_invert
    specular_yaw_axis_invert (bool) :specular_yaw_axis_invert
    value_unit_conversion (float) :value_unit_conversion
    specular_roll_axis_invert (bool) :specular_roll_axis_invert

    """

    def __init__(self):
        super().__init__()

        # @ Setting
        # $ Required Input
        self.name = "LFT_EyeDetail"
        self.eye_ball_joint = ""

        # -
        self.amount_eye_slide_joint = 10

        # $ Scale Radius Finding
        self.locator_start_radius = ""
        self.locator_end_radius = ""
        self.flip_scale = False
        # $ Pupils Rig
        self.list_pupil_joint = []

        # -
        self.joint_iris_loop_edge = ""
        self.joint_pupil_loop_edge = ""

        # $ Specular Rig
        self.enable_specular_rig = False
        # -
        self.specular_joint = ""
        # -
        self.specular_pitch_axis = "x"
        self.specular_yaw_axis = "y"
        # -
        self.specular_pitch_axis_invert = False
        self.specular_yaw_axis_invert = False
        #-
        self.value_unit_conversion = 1.0
        # -
        self.specular_roll_axis_invert = False
        # * enable_specular_rig

        self.debug_mode = False
    def core_build(self):
        def make_finalize():
            if self.debug_mode:
                return

            if self.enable_specular_rig:
                cmds.setAttr(ctrl_spec_main+".rx",l=1,k=0)
                cmds.setAttr(ctrl_spec_main+".ry",l=1,k=0)
                cmds.setAttr(ctrl_spec_main+".v",l=1,k=0)
                cmds.setAttr(ctrl_spec_main+".sz",l=1,k=0)

            utils.lock_attributes(ctrl_iris, v=1, s=1, r=1, t=1, l=1, k=0)

        def create_hierarchy():
            cmds.group(n=grp_eyeball_parent, em=1, p=self.grp_local_anim)
            cmds.group(n=grp_rot_piv, em=1, p=grp_eyeball_parent)

            cmds.group(n=grp_result_all, em=1, p=grp_eyeball_parent)

            cmds.parentConstraint(self.eye_ball_joint,grp_eyeball_parent)
            cmds.scaleConstraint(self.eye_ball_joint,grp_eyeball_parent)


        def rig_specular():
            if not self.enable_specular_rig:
                return

            # create ctrl
            cmds.spaceLocator(n=loc_specular)
            utils.matchAllTransform(loc_specular, self.specular_joint)
            cmds.parentConstraint(loc_specular,self.specular_joint)
            cmds.parent(loc_specular,grp_rot_piv)
            utils.freeze_group_classic(loc_specular)

            # create control main
            utils.create_control(ctrl_spec_main,parent=grp_eyeball_parent)
            cmds.addAttr(ctrl_spec_main,ln="specularScale",at="float",min=0)

            utils.matchTransform(ctrl_spec_main,self.specular_joint,pos=True)

            utils.freeze_group_classic(ctrl_spec_main)

            # connect control main to grp rotate
            list_connect = [["tx","r"+self.specular_yaw_axis,-1 if self.specular_yaw_axis_invert else 1],
                            ["ty","r"+self.specular_pitch_axis,-1 if self.specular_pitch_axis_invert else 1]]


            for data in list_connect:
                input,output,value = data

                node_uc = cmds.createNode("unitConversion")
                cmds.setAttr(node_uc+".conversionFactor",value*self.value_unit_conversion)
                cmds.connectAttr("{}.{}".format(ctrl_spec_main,input),"{}.input".format(node_uc))
                cmds.connectAttr("{}.output".format(node_uc),"{}.{}".format(grp_rot_piv,output))

            axis_roll = "xyz".replace(self.specular_pitch_axis,"").replace(self.specular_yaw_axis,"")

            if self.specular_roll_axis_invert:
                utils.connect_attr_conversion(input1="{}.rz".format(ctrl_spec_main,axis_roll),
                                              conversion=-1,
                                              output="{}.r{}".format(loc_specular,axis_roll) )
            else:
                cmds.connectAttr("{}.rz".format(ctrl_spec_main,axis_roll),"{}.r{}".format(loc_specular,axis_roll) )


            cmds.connectAttr(ctrl_spec_main+".tz",loc_specular+".tz")

            cmds.scaleConstraint(ctrl_spec_main,self.specular_joint)

        def rig_eye_slide():
            def create_grp_result(joint_name,value=0):
                grp_result = cmds.group(em=1,n=joint_name+"_result_grp",p=grp_result_all)

                axis_scale = "xyz"
                axis_translate = "z"

                axis_scale = axis_scale.replace(axis_translate,"")

                # match group result to eyeball position
                utils.matchTransform(grp_result,self.eye_ball_joint,pos=True,rot=True)
                utils.freeze_group_classic(grp_result)

                cmds.addAttr(grp_result,ln="offset_value",dv=value,at="float",k=1,min=0,max=1)

                attr_input = grp_result+".offset_value"
                node_md = cmds.createNode("multiplyDivide")
                node_euler = cmds.createNode("eulerToQuat")

                # connection
                cmds.connectAttr(attr_input,"{}.input1X".format(node_md))
                cmds.setAttr(node_md+".input2X",180)

                cmds.connectAttr(node_md+".outputX",node_euler+".inputRotateX")

                cmds.connectAttr(node_euler+".outputQuatX","{}.t{}".format(grp_result,axis_translate))

                for axis in axis_scale:
                    cmds.connectAttr(node_euler+".outputQuatW","{}.s{}".format(grp_result,axis))

                return grp_result

            def connect_scale_intensity(attr_scale,grp_result,value=0.0):
                node_adl_offset = cmds.createNode("addDoubleLinear")
                node_mdl_multiplier = cmds.createNode("multDoubleLinear")

                # connection
                utils.connect_attr_conversion(input1=attr_scale,output=node_mdl_multiplier+".input1",conversion=-0.1)
                cmds.setAttr(node_mdl_multiplier+".input2",value)

                value_current = cmds.getAttr(grp_result+".offset_value")
                value_multiply_output = cmds.getAttr(node_mdl_multiplier+".output")

                cmds.connectAttr(node_mdl_multiplier+".output",node_adl_offset+".input1")
                cmds.setAttr(node_adl_offset+".input2",(value_multiply_output-value_current)*-1)

                cmds.connectAttr(node_adl_offset+".output",grp_result+".offset_value")

            def connect_scale_intensity_double(attr_scale1, attr_scale2, grp_result, value1, value2):
                def create_single_mult(attr_scale, value):
                    node_mdl_multiplier = cmds.createNode("multDoubleLinear")

                    # connection
                    utils.connect_attr_conversion(input1=attr_scale, output=node_mdl_multiplier + ".input1", conversion=-0.1)

                    cmds.setAttr(node_mdl_multiplier+".input2",value)

                    value_multiply_output = cmds.getAttr(node_mdl_multiplier + ".output")

                    return  node_mdl_multiplier+".output",value_multiply_output

                value_grp_result = cmds.getAttr(grp_result + ".offset_value")

                attr_mult1,value_mult_output1 = create_single_mult(attr_scale1, value1)
                attr_mult2,value_mult_output2 = create_single_mult(attr_scale2, value2)

                node_adl_sum = cmds.createNode("addDoubleLinear")
                node_adl_offset = cmds.createNode("addDoubleLinear")

                # connect sum
                cmds.connectAttr(attr_mult1,node_adl_sum+".input1")
                cmds.connectAttr(attr_mult2,node_adl_sum+".input2")

                # connect offset
                value_sum = cmds.getAttr(node_adl_sum+".output")

                cmds.connectAttr(node_adl_sum+".output",node_adl_offset+".input1")
                cmds.setAttr(node_adl_offset+".input2",(value_sum-value_grp_result)*-1)
                cmds.connectAttr(node_adl_offset+".output",grp_result + ".offset_value")

            def connect_to_joints():
                # variables
                pupil_joint_loops_index = self.list_pupil_joint.index(self.joint_pupil_loop_edge)
                iris_joint_loops_index = self.list_pupil_joint.index(self.joint_iris_loop_edge)

                # create iris controller
                utils.create_control(ctrl_iris, parent=grp_eyeball_parent)
                utils.matchTransform(ctrl_iris, self.joint_iris_loop_edge, pos=True)
                utils.freeze_group_classic(ctrl_iris)
                cmds.addAttr(ctrl_iris, ln="irisScale", at="float", k=1, dv=10, min=0)
                cmds.addAttr(ctrl_iris, ln="pupilScale", at="float", k=1, dv=10, min=0)

                attr_iris_scale = ctrl_iris + ".irisScale"
                attr_pupil_scale = ctrl_iris + ".pupilScale"

                print("total amount : ", self.amount_eye_slide_joint)
                print("pupil loop index : ", pupil_joint_loops_index)
                print("iris loop index : ", iris_joint_loops_index)
                # print("scale radius : ", current_radius)

                index_pupil = 0
                index_white_eye = 0
                index_iris = 0

                for i in range(self.amount_eye_slide_joint-1):
                    grp_result = list_grp_result[i]

                    # outside iris
                    if i < iris_joint_loops_index:
                        value_factor = (index_white_eye * (1 / iris_joint_loops_index))

                        connect_scale_intensity(attr_iris_scale, grp_result, value=value_factor)

                        index_white_eye += 1

                    # inside iris
                    elif iris_joint_loops_index <= i < pupil_joint_loops_index:
                        amount_pupils_loops_left = pupil_joint_loops_index - iris_joint_loops_index


                        value1 = (index_pupil * (1 / (amount_pupils_loops_left)))
                        value2 = 1 - value1

                        print("amount pupil left : ",amount_pupils_loops_left)
                        print("value : ",value1)
                        print("---")

                        connect_scale_intensity_double(attr_scale1=attr_pupil_scale,
                                                       attr_scale2=attr_iris_scale,
                                                       grp_result=grp_result,
                                                       value1=value1,
                                                       value2=value2)

                        index_pupil += 1


                    # pupil
                    elif i >= pupil_joint_loops_index:
                        value_factor = 1 - (index_iris * (1 / (self.amount_eye_slide_joint - iris_joint_loops_index)))

                        connect_scale_intensity(attr_pupil_scale, grp_result, value=value_factor)
                        #
                        # print("value factor : ", value_factor)
                        # print("joint scale : ", self.list_pupil_joint[i])
                        # print("grp result : ", grp_result)
                        # print("---")

                        index_iris += 1

            list_grp_result = []

            for i,joint in enumerate(self.list_pupil_joint):
                grp_result = create_grp_result(joint_name= joint)
                cmds.setAttr(grp_result+".offset_value",i*(1/(self.amount_eye_slide_joint-1)))

                list_grp_result.append(grp_result)

            # set scale of grp result
            cmds.setAttr(grp_result_all+".s",current_radius,current_radius,current_radius,typ="double3")

            # constraint to joint
            for i,grp_result in enumerate(list_grp_result):
                joint = self.list_pupil_joint[i]
                cmds.parentConstraint(grp_result,joint,mo=1)
                cmds.scaleConstraint(grp_result,joint,mo=1)

            connect_to_joints()

        loc_specular = "{}_{}".format(self.specular_joint,loc)
        ctrl_spec_main = "{}_main_{}".format(self.specular_joint,ctrl)
        grp_eyeball_parent = "{}_eyeBallParent_grp".format(self.name)
        grp_rot_piv ="{}_eyeBallSpc_grp".format(self.name)
        ctrl_iris= "{}_iris_{}".format(self.name,ctrl)
        grp_result_all = "{}_result_all_grp".format(self.name)

        current_radius = utils.get_distance_two(self.locator_start_radius, self.locator_end_radius)

        if self.flip_scale:
            current_radius *= -1

        if self.amount_eye_slide_joint != len(self.list_pupil_joint):
            raise Exception("Invalid input , Amount of input must be {} , get {}".format(self.amount_eye_slide_joint,len(self.list_pupil_joint)))

        create_hierarchy()
        rig_specular()
        rig_eye_slide()
        make_finalize()

class EyeGlobalAim(rig_class.Rig):
    """
    Eye Global Aim

    Will Aim Global Eye

    Variables:
    left_eye_joint (string) : Left eye joint
    left_eye_aim_axis (string) : Axis that joint will aiming forward locator.
    left_eye_up_axis (string) : Axis that up of joint will aiming up.

    right_eye_joint (string) : Right eye joint
    right_eye_aim_axis (string) : Axis that joint will aiming forward locator. ( by default will be negative axis of left side).
    right_eye_up_axis (string) : Axis that up of joint will aiming up. ( by default will be negative axis of left side).

    left_eye_control_pivot (string) : The Pivot that left eye controller will position at (Reference only position).
    right_eye_control_pivot (string) : The Pivot that right eye controller will position at (Reference only position).
    """

    def __init__(self):
        super().__init__()

        # @ Required
        self.name = "GlobalEye"
        # $ Left Eye ( Global Joint )
        self.left_eye_joint = ""
        self.left_eye_aim_axis = "z"
        self.left_eye_up_axis = "y"

        # $ Right Eye ( Global Joint )
        self.right_eye_joint = ""
        self.right_eye_aim_axis = "-z"
        self.right_eye_up_axis = "-y"

        # $ Guide Pivot
        self.left_eye_control_pivot = ""
        self.right_eye_control_pivot = ""

        self.parent = ""
        self.debug_mode = False

    def core_build(self):
        def create_global_control():
            utils.create_control(name=ctrl_global, parent=self.grp_local_anim,size=1.5,color="yellow")

            constraint = cmds.pointConstraint(self.left_eye_control_pivot, self.right_eye_control_pivot, ctrl_global)
            cmds.delete(constraint)

            utils.freeze_group([ctrl_global])

        def create_eyeball_controls():
            # create eyeball control
            for i, joint in enumerate([self.left_eye_joint, self.right_eye_joint]):
                control = [left_eye_control, right_eye_control][i]
                locator = [left_eye_locator, right_eye_locator][i]
                pivot = [self.left_eye_control_pivot, self.right_eye_control_pivot][i]

                # create control and match position
                utils.create_control(name=control, parent=ctrl_global,shape="sphere",size=0.8)
                cmds.matchTransform(control, pivot, pos=1)

                utils.freeze_group_classic(control)

                # create space locator
                cmds.spaceLocator(n=locator)
                utils.match_parent(locator, control)

        def create_aim_constraint():
            # left aim constraint
            aim = utils.get_axis_double3(self.left_eye_aim_axis)
            up = utils.get_axis_double3(self.left_eye_up_axis)
            cmds.aimConstraint(left_eye_locator, self.left_eye_joint, mo=1, aim=aim, u=up, wu=up, wut="objectrotation", wuo=object_rotate_up)

            # right aim constraint
            aim = utils.get_axis_double3(self.right_eye_aim_axis)
            up = utils.get_axis_double3(self.right_eye_up_axis)
            cmds.aimConstraint(right_eye_locator, self.right_eye_joint, mo=1, aim=aim, u=up, wu=up, wut="objectrotation", wuo=object_rotate_up)

        def create_locator_up():
            grp_offset = cmds.group(em=1, n="{}_{}LocUpOffset".format(grp, self.name), p=self.grp_local_anim)
            cmds.setAttr("{}.inheritsTransform".format(grp_offset), 0)

            if self.parent:
                parent = self.parent
            else:
                parent = self.grp_local_anim

            cmds.connectAttr("{}.worldMatrix[0]".format(parent), "{}.offsetParentMatrix".format(grp_offset))

            cmds.spaceLocator(n=object_rotate_up)
            utils.match_parent(object_rotate_up, grp_offset)

        def create_space_switch():
            # create attribute and group
            grp_blend = utils.freeze_group([ctrl_global], prefix="grpBlend")[0]
            cmds.addAttr(ctrl_global, ln="localSpace", min=0, max=1, at="float", k=1)
            attr_switch = "{}.localSpace".format(ctrl_global)

            # create switch systems , use blendColor Node
            node_reverse = cmds.createNode("reverse", n="rev_{}Switch".format(self.name))

            cmds.connectAttr(attr_switch, "{}.inputX".format(node_reverse))

            constraint = cmds.parentConstraint(loc_root, self.grp_local_anim, grp_blend, mo=1)[0]
            cmds.connectAttr("{}.outputX".format(node_reverse), "{}.{}W0".format(constraint, loc_root))
            cmds.connectAttr(attr_switch, "{}.{}W1".format(constraint,self.grp_local_anim))

        def finalize():
            if self.debug_mode:
                return

            utils.lock_attributes(ctrl_global, v=1, s=1, k=0, l=1)
            utils.lock_attributes(left_eye_control, v=1, s=1, k=0, l=1)
            utils.lock_attributes(right_eye_control, v=1, s=1, k=0, l=1)

        ctrl_global = "{}_ctrl".format(self.name)
        object_rotate_up = "{}_ObjRotUp_loc".format(self.name)

        left_eye_control = self.left_eye_joint + "_ctrl"
        right_eye_control = self.right_eye_joint + "_ctrl"

        left_eye_locator = self.left_eye_joint + "_loc"
        right_eye_locator = self.right_eye_joint + "_loc"

        # build
        create_global_control()
        create_eyeball_controls()
        create_locator_up()
        create_aim_constraint()
        create_space_switch()
        finalize()

        cmds.select(cl=1)
