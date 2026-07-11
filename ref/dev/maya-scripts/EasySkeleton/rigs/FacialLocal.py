import maya.cmds as cmds
import EasySkeleton.config as config
from EasySkeleton import rig_class
from EasySkeleton.config import *
import EasySkeleton.utils as utils


class Mouth(rig_class.Rig):
    """
    Mouth Curve Based V3

    Variables:
    list_upper_bind (stringArray) : List of Upper Lips Joints , include corner joint ( Sort by Right to Left Side) | Joints Local Type
    list_lower_bind (stringArray) : List of Upper Lips Joints ( Sort by Right to Left Side) | Joints Local Type
    jaw_bind_joint (string) : name of jaw joint

    big_mouth_rotate_pivot(string) : Name of Pivot Guide (Translate) , to create a global mouth control
    list_main_pivot(stringArray) : List of Right , Up , Left , Low Position

    list_curve_up (stringArray) : List of left emotion up curve blend shape name (Sort Up , Down ,In ,Out, UpOut, UpIn, DownOut, DownIn)
    list_curve_low (stringArray) : List of left emotion low curve blend shape name (Sort Up , Down ,In ,Out, UpOut, UpIn, DownOut, DownIn)

    list_mesh_up (stringArray) : List of up mesh
    list_mesh_low (stringArray) : List of low mesh

    list_main_joint(stringArray) : List of Right , Up , Left , Low Joints

    list_mid_joint(stringArray) : List of Right , RightUp,Up , LeftUp,Left ,LowLeft, Low ,LowRight Joints

    list_teeth_up(stringArray) : List of Upper Jaw Parent ,for example up teeth and up gum joints | Joints Global Type (Optional)
    list_teeth_low(stringArray) : List of Lower Jaw Parent ,for example low teeth and low gum joints | Joints Global Type (Optional)
    list_tongue_joints_chain (stringArray) : List of Tongue Joints Chain | Joints Global Type (Optional)

    list_target_left_emotion_shape(stringArray) : List of Left Emotion Shape Target Name (Sort by Up, Down, In, Out, UpOut, UpIn,DownOut, DownIn)
    list_target_roll_mouth_shape(stringArray) : List of Main Controller Rotate Target Name ( Roll In , Roll Out )

    enable_zipper(bool) : enable zipper mouth

    enable_auto_push (bool) : enable_auto_push
    jaw_push_rotate_axis (enum) : jaw_push_rotate_axis
    invert_push_axis (bool) : invert_push_axis
    value_start_push (float) : value_start_push

    curve_up_weight_path(path) : curve_up_weight_path
    curve_low_weight_path(path) : curve_low_weight_path

    enable_curve_blend_shape(bool) : enable curve blend shape
    curve_up_blend_shape_node_name(string) : curve up blend shape node name
    curve_low_blend_shape_node_name(string) : curve up blend shape node name

    enable_mesh_blend_shape (bool) : enable_mesh_blend_shape

    blend_shape_node_name (string) : blend_shape_node_name

    ctrl_main_up_rot_pivot(string) : ctrl_main_up_rot_pivot
    ctrl_main_low_rot_pivot(string) : ctrl_main_low_rot_pivot

    ctrl_main_speed(float) : speed of main control
    """

    def __init__(self):
        super().__init__()
        self.name = "Mouth"

        # @ Setting
        # $ Required ( Required Joints Local )
        self.list_upper_bind = []
        self.list_lower_bind = []
        self.jaw_bind_joint = ""
        # -
        self.big_mouth_rotate_pivot = ""
        self.list_main_pivot = []
        # -
        self.ctrl_main_up_rot_pivot = ""
        self.ctrl_main_low_rot_pivot = ""

        # @ Extra Features
        # $ Inner Mouth Rig ( Required Joints Global )
        self.list_teeth_up = []
        self.list_teeth_low = []
        self.list_tongue_joints_chain = []

        # $ Zipper Feature
        self.enable_zipper = False

        # $ Jaw Push Feature
        self.enable_auto_push = False
        # -
        self.jaw_push_rotate_axis = utils.get_single_axis_enum_pos()
        self.invert_push_axis = False
        self.value_start_push = 0
        # * enable_auto_push

        # $ Auto Import Weight
        self.curve_up_weight_path = ""
        self.curve_low_weight_path = ""

        # $ Curve Blend Shape
        self.enable_curve_blend_shape = False
        # -
        self.curve_up_blend_shape_node_name = ""
        self.curve_low_blend_shape_node_name = ""
        # -
        self.list_curve_up = []
        self.list_curve_low = []
        # *enable_curve_blend_shape

        # $ Mesh Blend Shape
        self.enable_mesh_blend_shape = False
        # -
        self.blend_shape_node_name = ""
        self.list_target_left_emotion_shape = []
        # -
        self.list_target_roll_mouth_shape = []
        # * enable_mesh_blend_shape

        # $ Tuning Speed
        self.ctrl_main_speed = 1.0

        self.parent = None
        self.debug_mode = False
    def core_build(self):
        def create_jaw():
            utils.create_control(name=ctrl_jaw,
                                 match=self.jaw_bind_joint,
                                 parent=self.grp_local_anim,
                                 size=8,
                                 color="yellow")
            utils.freeze_group_classic(ctrl_jaw,"grpCtrl")

            utils.connect(ctrl_jaw, loc_jaw)
            utils.connect(ctrl_jaw, self.jaw_bind_joint, typ="scl")

        def create_local_locator():
            def auto_push():
                # auto jaw push
                if self.enable_auto_push:
                    cmds.connectAttr("{}.r{}".format(loc_jaw, self.jaw_push_rotate_axis), "{}.r{}".format(grp_up_space_sub_loc, self.jaw_push_rotate_axis))

                    if self.invert_push_axis:
                        cmds.setAttr(grp_up_space_sub_loc + ".minRot{}Limit".format(self.jaw_push_rotate_axis.upper()), self.value_start_push)
                        cmds.setAttr(grp_up_space_sub_loc + ".minRot{}LimitEnable".format(self.jaw_push_rotate_axis.upper()), True)
                    else:
                        cmds.setAttr(grp_up_space_sub_loc + ".maxRot{}Limit".format(self.jaw_push_rotate_axis.upper()), self.value_start_push)
                        cmds.setAttr(grp_up_space_sub_loc + ".maxRot{}LimitEnable".format(self.jaw_push_rotate_axis.upper()), True)

            # jaw local locator
            cmds.spaceLocator(n=loc_jaw)
            cmds.parent(loc_jaw, grp_local_locator)
            utils.matchTransform(loc_jaw, self.jaw_bind_joint, pos=1, rot=1)
            utils.freeze_group_classic(loc_jaw)

            cmds.parent(self.jaw_bind_joint, loc_jaw)

            # mouth big locator
            cmds.spaceLocator(n=loc_big_mouth)
            cmds.parent(loc_big_mouth, grp_local_locator)
            utils.matchTransform(loc_big_mouth, self.big_mouth_rotate_pivot, pos=1)
            utils.freeze_group_classic(loc_big_mouth)

            # lips bind locator
            cmds.group(em=1, n=grp_sub_loc_jaw_space, p=loc_big_mouth)

            cmds.group(em=1, n=grp_up_space_sub_loc, p=grp_sub_loc_jaw_space)
            cmds.group(em=1, n=grp_low_space_sub_loc, p=grp_sub_loc_jaw_space)
            cmds.group(em=1, n=grp_avg_space_sub_loc, p=grp_sub_loc_jaw_space)

            # match grp sub jaw space to jaw
            utils.matchTransform(grp_sub_loc_jaw_space, self.jaw_bind_joint, pos=1, rot=1)
            utils.freeze_group_classic(grp_sub_loc_jaw_space)

            # locator connection to jaw space
            utils.connect(loc_jaw, grp_low_space_sub_loc, typ="translate")
            utils.connect(loc_jaw, grp_low_space_sub_loc, typ="rotate")

            utils.connect(loc_jaw, grp_avg_space_sub_loc, typ="translate", translate_multiplier=0.5)
            utils.connect(loc_jaw, grp_avg_space_sub_loc, typ="rotate", rotate_multiplier=0.5)

            list_bind_locator = list_bind_up_locator + list_bind_low_locator
            list_bind_joint = self.list_upper_bind + self.list_lower_bind

            for i, joint in enumerate(list_bind_joint):
                locator = list_bind_locator[i]

                if locator == list_bind_up_locator[0] or locator == list_bind_up_locator[-1]:
                    parent = grp_avg_space_sub_loc
                elif locator in list_bind_up_locator:
                    parent = grp_up_space_sub_loc
                elif locator in list_bind_low_locator:
                    parent = grp_low_space_sub_loc

                cmds.spaceLocator(name=locator)

                utils.matchTransform(locator, joint, pos=1, rot=1)

                cmds.parent(locator, parent)

                utils.freeze_group_classic(locator)
                cmds.parent(joint, locator)

            auto_push()

        def create_hierarchy():
            cmds.group(em=1, n=grp_mouth_curves, p=self.grp_local_still)

            cmds.group(em=1, n=grp_blend_shape, p=self.grp_local_still)
            cmds.setAttr(grp_blend_shape + ".v", 0)

            cmds.group(em=1, n=grp_local_locator, p=self.grp_local_still)

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
            def create_control():
                # create group
                grp_main_up_translate = cmds.group(em=1, n="{}_main_up_translate_grp".format(self.name), p=cmds.listRelatives(ctrl_main_up, p=1)[0])
                grp_main_low_translate = cmds.group(em=1, n="{}_main_low_translate_grp".format(self.name), p=cmds.listRelatives(ctrl_main_low, p=1)[0])

                # connect for group
                utils.connect(ctrl_main_up, grp_main_up_translate, typ="translate")
                utils.connect(ctrl_main_low, grp_main_low_translate, typ="translate")

                # create controls and joint
                for i, joint in enumerate(list_mid_up_joint + list_mid_low_joint):

                    if joint == list_mid_up_joint[0]:
                        parent = ctrl_main_right
                    elif joint == list_mid_up_joint[-1]:
                        parent = ctrl_main_left
                    elif joint in list_mid_up_joint:
                        parent = grp_main_up_translate
                    elif joint in list_mid_low_joint:
                        parent = grp_main_low_translate
                    else:
                        raise Exception("Module Error")

                    control = (list_mid_up_control + list_mid_low_control)[i]
                    utils.create_control(name=control, parent=parent,size=0.5,color="red")

                    cmds.select(cl=1)
                    cmds.joint(n=joint)
                    cmds.parent(joint, control)

                    grp_frz = utils.freeze_group_classic(control)[0]

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
                cmds.setAttr(list_frz_up_control[0] + ".sx", -1)
                cmds.setAttr(list_frz_up_control[1] + ".sx", -1)

                cmds.setAttr(list_frz_low_control[0] + ".sx", -1)
                cmds.setAttr(list_frz_low_control[0] + ".sy", -1)

                cmds.setAttr(list_frz_low_control[1] + ".sy", -1)
                cmds.setAttr(list_frz_low_control[2] + ".sy", -1)

            def create_joint_mid_space():
                # create joint mid space
                grp_joint_mid = cmds.group(em=1, n="{}_mid_local_joint_grp".format(self.name), p=self.grp_local_still)

                grp_front_rot_up_joint = cmds.group(em=1, n="{}_mid_up_jnt_frontRot_grp".format(self.name), p=grp_joint_mid)
                grp_front_rot_low_joint = cmds.group(em=1, n="{}_mid_low_jnt_frontRot_grp".format(self.name), p=grp_joint_mid)
                grp_front_rot_left_joint = cmds.group(em=1, n="{}_{}_mid_jnt_frontRot_grp".format(self.name, L), p=grp_joint_mid)
                grp_front_rot_right_joint = cmds.group(em=1, n="{}_{}_mid_jnt_frontRot_grp".format(self.name, R), p=grp_joint_mid)

                grp_side_rot_up_joint = cmds.group(em=1, n="{}_mid_up_jnt_sideRot_grp".format(self.name), p=grp_front_rot_up_joint)
                grp_side_rot_low_joint = cmds.group(em=1, n="{}_mid_low_jnt_sideRot_grp".format(self.name), p=grp_front_rot_low_joint)
                grp_side_rot_left_joint = cmds.group(em=1, n="{}_{}_mid_jnt_sideRot_grp".format(self.name, L), p=grp_front_rot_left_joint)
                grp_side_rot_right_joint = cmds.group(em=1, n="{}_{}_mid_jnt_sideRot_grp".format(self.name, R), p=grp_front_rot_right_joint)

                # match transform for global
                utils.matchTransform(grp_joint_mid, ctrl_base, pos=True, rot=True, scl=True)

                # match front
                # utils.matchTransform(grp_front_rot_left_joint, ctrl_main_left, pos=True)
                # utils.matchTransform(grp_front_rot_right_joint, ctrl_main_right, pos=True)
                utils.matchTransform(grp_front_rot_up_joint, ctrl_main_up, pos=True)
                utils.matchTransform(grp_front_rot_low_joint, ctrl_main_low, pos=True)

                # freeze group

                # match side
                utils.matchTransform(grp_side_rot_left_joint, ctrl_main_left, pos=True, rot=True, scl=True)
                utils.matchTransform(grp_side_rot_right_joint, ctrl_main_right, pos=True, rot=True, scl=True)
                utils.matchTransform(grp_side_rot_low_joint, self.ctrl_main_low_rot_pivot, pos=True, scl=True)
                utils.matchTransform(grp_side_rot_up_joint, self.ctrl_main_up_rot_pivot, pos=True, scl=True)

                utils.freeze_group_classic([grp_side_rot_left_joint, grp_side_rot_right_joint, grp_side_rot_low_joint, grp_side_rot_up_joint, grp_joint_mid, grp_front_rot_up_joint, grp_front_rot_low_joint,
                     grp_front_rot_left_joint, grp_front_rot_right_joint],grpOff)

                # connection --------------------
                utils.connect(ctrl_base, grp_joint_mid)

                # front rot connection
                cmds.connectAttr(ctrl_main_up + ".rz", grp_front_rot_up_joint + ".rz")
                cmds.connectAttr(ctrl_main_low + ".rz", grp_front_rot_low_joint + ".rz")
                cmds.connectAttr(ctrl_main_left + ".rz", grp_front_rot_left_joint + ".rz")
                cmds.connectAttr(ctrl_main_right + ".rz", grp_front_rot_right_joint + ".rz")

                # side rot connection
                utils.connect(ctrl_main_up, grp_side_rot_up_joint, typ="translate")
                utils.connect(ctrl_main_low, grp_side_rot_low_joint, typ="translate")
                utils.connect(ctrl_main_left, grp_side_rot_left_joint, typ="translate")
                utils.connect(ctrl_main_right, grp_side_rot_right_joint, typ="translate")

                for i, joint in enumerate(list_mid_up_joint + list_mid_low_joint):
                    if joint == list_mid_up_joint[0]:
                        parent = grp_side_rot_right_joint
                    elif joint == list_mid_up_joint[-1]:
                        parent = grp_side_rot_left_joint
                    elif joint in list_mid_up_joint:
                        parent = grp_side_rot_up_joint
                    elif joint in list_mid_low_joint:
                        parent = grp_side_rot_low_joint

                    control = (list_mid_up_control + list_mid_low_control)[i]

                    cmds.parent(joint, parent)
                    utils.freeze_group_classic(joint,grpOff)

                    utils.connect(control, joint, translate_multiplier=2)

            create_control()
            create_joint_mid_space()

        def create_main_controls():
            def create_local_controls_locator():
                for locator in [loc_main_up, loc_main_low, loc_main_left, loc_main_right]:
                    cmds.spaceLocator(n=locator)

                cmds.parent(loc_main_up, grp_up_space)
                cmds.parent(loc_main_low, grp_low_space)
                cmds.parent(loc_main_left, loc_main_right, grp_up_space)

                # match position of locator
                utils.snap_to_curve_by_param(crv_bind_up, loc_main_up, 0.5, True)
                utils.snap_to_curve_by_param(crv_bind_low, loc_main_low, 0.5, True)
                cmds.matchTransform(loc_main_left, self.list_upper_bind[-1])
                cmds.matchTransform(loc_main_right, self.list_upper_bind[0])

                # flip and freeze group
                cmds.xform(loc_main_right, ro=(0, 180, 0), r=1)
                utils.freeze_group_classic([loc_main_up, loc_main_low, loc_main_left, loc_main_right], "grpCtrl")
                cmds.setAttr(cmds.listRelatives(loc_main_right, p=1)[0] + ".s", 1, 1, -1, typ="double3")

            def create_controller():
                grp_control = cmds.group(em=1, p=grp_main_control, n="{}_main_ctl_grp".format(self.name))

                # Create Controller and Locator -----------------------------
                # create controller and parent to group
                [utils.create_control(name=control, parent=grp_control,size=0.3,color="yellow") for control in list_main_control]

                # snap position for controller ----------------------------------
                match_right, match_up, match_left, match_low = self.list_main_pivot
                cmds.matchTransform(ctrl_main_up, match_up, pos=1)
                cmds.matchTransform(ctrl_main_right, match_right, pos=1)
                cmds.matchTransform(ctrl_main_left, match_left, pos=1)
                cmds.matchTransform(ctrl_main_low, match_low, pos=1)

                # parent along space
                cmds.parent(ctrl_main_up, grp_up_space)
                cmds.parent(ctrl_main_low, grp_low_space)
                cmds.parent(ctrl_main_left, ctrl_main_right, grp_corner_space)

                # flip and freeze group
                cmds.xform(ctrl_main_right, ro=(0, 180, 0), r=1)
                list_grp_freeze = utils.freeze_group_classic(list_main_control, "grpCtrlOff")

                for grp_freeze in list_grp_freeze:
                    cmds.setAttr("{}.s".format(grp_freeze), self.ctrl_main_speed, self.ctrl_main_speed, self.ctrl_main_speed, typ="double3")

                cmds.setAttr(cmds.listRelatives(ctrl_main_right, p=1)[0] + ".s", self.ctrl_main_speed, self.ctrl_main_speed, -self.ctrl_main_speed, typ="double3")

                # connect control to locator
                utils.connect(ctrl_main_left, loc_main_left)
                utils.connect(ctrl_main_right, loc_main_right)
                utils.connect(ctrl_main_up, loc_main_up)
                utils.connect(ctrl_main_low, loc_main_low)

            # snap to custom pivot
            if len(self.list_main_pivot) != 4:
                raise Exception("List Custom Main Pivot : Invalid input")

            create_local_controls_locator()
            create_controller()

        def create_bind_controls():
            cmds.group(em=1, n=grp_sub_ctrl, p=grp_bind_control)
            utils.matchTransform(grp_sub_ctrl, ctrl_base, pos=True, rot=True)

            cmds.group(em=1, n=grp_sub_world)
            cmds.parent(grp_sub_world, grp_sub_ctrl)

            # create group space
            grp_space_zero = cmds.group(em=1, n="{}_spaceZro".format(self.name))

            cmds.group(em=1, n=grp_up_space_sub_ctrl, p=grp_space_zero)
            cmds.group(em=1, n=grp_low_space_sub_ctrl, p=grp_space_zero)
            cmds.group(em=1, n=grp_avg_space_sub_ctrl, p=grp_space_zero)

            utils.matchTransform(grp_space_zero, loc_jaw, pos=True, rot=True)

            cmds.parent(grp_space_zero, grp_sub_world)

            # locator connection
            utils.connect(loc_jaw, grp_low_space_sub_ctrl, typ="translate")
            utils.connect(loc_jaw, grp_low_space_sub_ctrl, typ="rotate")

            utils.connect(loc_jaw, grp_avg_space_sub_ctrl, typ="translate", translate_multiplier=0.5)
            utils.connect(loc_jaw, grp_avg_space_sub_ctrl, typ="rotate", rotate_multiplier=0.5)

            # create controller
            list_bind_control = list_bind_up_control + list_bind_low_control
            list_bind_joint = self.list_upper_bind + self.list_lower_bind
            list_bind_locator = list_bind_up_locator + list_bind_low_locator

            for i, control in enumerate(list_bind_control):
                locator = list_bind_locator[i]
                match_target = list_bind_joint[i]

                # parent = grp_sub_world
                if control == list_bind_up_control[0]:
                    parent = grp_avg_space_sub_ctrl
                elif control == list_bind_up_control[-1]:
                    parent = grp_avg_space_sub_ctrl
                elif control in list_bind_up_control:
                    parent = grp_up_space_sub_ctrl
                elif control in list_bind_low_control:
                    parent = grp_low_space_sub_ctrl
                else:
                    raise Exception("Error Module")

                utils.create_control(name=control, match=match_target, parent=parent,size=0.3,color="blue")
                utils.freeze_group_classic(control,grpCtrl)

                utils.connect(control, locator)

        def drive_bind_controls():
            def bind_skin_curve():
                # bind mid joint to curve
                node_bind_up = cmds.skinCluster(list_mid_up_joint, crv_bind_up, ih=1, dr=0.8, bm=3, mi=3)
                node_bind_low = cmds.skinCluster([list_mid_up_joint[0]] + list_mid_low_joint + [list_mid_up_joint[-1]], crv_bind_low, ih=1,
                                                 dr=0.5,
                                                 bm=3,
                                                 mi=3)

                utils.import_weight(node_bind_up, self.curve_up_weight_path) if self.curve_up_weight_path else None
                utils.import_weight(node_bind_low, self.curve_low_weight_path) if self.curve_low_weight_path else None

            def create_grp_pin():
                # constraint translate to items by curve
                for control in list_bind_up_control:
                    grp_pin = cmds.group(em=1, n=control.replace(ctrl, "grpPin"))
                    cmds.matchTransform(grp_pin, control)
                    list_bind_pin_up.append(grp_pin)

                for control in list_bind_low_control:
                    grp_pin = cmds.group(em=1, n=control.replace(ctrl, "grpPin"))
                    cmds.matchTransform(grp_pin, control)
                    list_bind_pin_low.append(grp_pin)

                utils.pin_curve_by_distance(list_bind_pin_up, crv_bind_up, maintainOffset=False)
                utils.pin_curve_by_distance(list_bind_pin_low, crv_bind_low, maintainOffset=False)

            def parent_grp_pin():
                # constraint orient and translate to control offset
                list_grp_pin = list_bind_pin_up + list_bind_pin_low
                list_grp_joint_offset = [cmds.listRelatives(locator, p=1)[0] for locator in list_bind_up_locator + list_bind_low_locator]
                list_grp_control_offset = [cmds.listRelatives(control, p=1)[0] for control in list_bind_up_control + list_bind_low_control]

                for i in range(len(list_grp_pin)):
                    grp_offset = list_grp_joint_offset[i]
                    grp_pin = list_grp_pin[i]

                    # connect to group locator
                    grp_pin_world = cmds.group(em=1, n=grp_pin + "_world")
                    cmds.parent(grp_pin_world, cmds.listRelatives(grp_offset, p=1)[0])
                    cmds.parent(grp_pin, grp_pin_world)

                    cmds.parent(grp_offset, grp_pin)

                    utils.connect(ctrl_base, grp_offset, typ="rotate")

                    # connect translate to group control
                    grp_control_offset = list_grp_control_offset[i]

                    grp_control_offset_world = cmds.group(em=1, n=grp_control_offset + "_world")
                    cmds.parent(grp_control_offset_world, cmds.listRelatives(grp_control_offset, p=1)[0])
                    cmds.parent(grp_control_offset, grp_control_offset_world)

                    utils.connect(grp_pin, grp_control_offset, typ="translate")
                    utils.connect(ctrl_base, grp_control_offset, typ="rotate")

            def connect_rotate_side():
                for joint in self.list_upper_bind[1:len(self.list_upper_bind) - 1] + self.list_lower_bind:
                    grp_rot = utils.freeze_group_classic(joint, "rotIn")[0]

                    if joint in self.list_upper_bind:
                        cmds.connectAttr(ctrl_main_up + ".rx", grp_rot + ".rx")
                    elif joint in self.list_lower_bind:
                        cmds.connectAttr(ctrl_main_low + ".rx", grp_rot + ".rx")

            def connect_scale():
                # create group scale
                cmds.group(em=1, n=grp_up_bind_loc_scale_space)
                cmds.group(em=1, n=grp_low_bind_loc_scale_space)
                # cmds.group(em=1, n=grp_avg_bind_loc_scale_space)

                # match group to ctrl main
                utils.matchTransform(grp_up_bind_loc_scale_space, ctrl_main_up, pos=True, rot=True)
                utils.matchTransform(grp_low_bind_loc_scale_space, ctrl_main_low, pos=True, rot=True)

                # parent group up
                list_child = cmds.listRelatives(grp_up_space_sub_loc, c=1, f=1)
                cmds.parent(grp_up_bind_loc_scale_space, grp_up_space_sub_loc)
                cmds.parent(list_child, grp_up_bind_loc_scale_space)

                # parent group low
                list_child = cmds.listRelatives(grp_low_space_sub_loc, c=1, f=1)
                cmds.parent(grp_low_bind_loc_scale_space, grp_low_space_sub_loc)
                cmds.parent(list_child, grp_low_bind_loc_scale_space)

                # freeze group
                utils.freeze_group_classic([grp_up_bind_loc_scale_space, grp_low_bind_loc_scale_space],grpOff)

                # connect scale
                cmds.connectAttr(ctrl_main_up + ".s", grp_up_bind_loc_scale_space + ".s")
                cmds.connectAttr(ctrl_main_low + ".s", grp_low_bind_loc_scale_space + ".s")

            bind_skin_curve()
            create_grp_pin()
            parent_grp_pin()
            connect_rotate_side()
            connect_scale()

        def create_global_control():
            # create offset group parent
            grp_parent = cmds.group(em=1, n="{}_mouthGlobalAnim".format(grp), p=self.grp_local_anim)

            # create controller and add controller
            utils.create_control(name=ctrl_base, parent=grp_parent,size=5,color="yellow")
            utils.matchTransform(ctrl_base, self.big_mouth_rotate_pivot, pos=True)
            utils.add_option_shape(ctrl_base, shape_mouth_option)

            utils.freeze_group([ctrl_base])

            # create hierarchy
            cmds.group(em=1, n=grp_main_control, p=ctrl_base, r=True)
            cmds.group(em=1, n=grp_mid_control, p=ctrl_base, r=True)

            cmds.group(em=1, n=grp_bind_control)

            cmds.connectAttr(self.grp_local_anim + ".worldMatrix[0]", grp_bind_control + ".offsetParentMatrix")
            cmds.setAttr(grp_bind_control + ".inheritsTransform", 0)
            cmds.parent(grp_bind_control, ctrl_base)

        def create_inner_mouth():
            grp_inner_mouth = cmds.group(em=1, n="{}_inner_grp".format(self.name), p=self.grp_local_anim)

            grp_inner_up_space = cmds.group(em=1, n="{}_innerUpSpace_grp".format(self.name), p=grp_inner_mouth)
            grp_inner_low_space = cmds.group(em=1, n="{}_innerLowSpace_grp".format(self.name), p=grp_inner_mouth)

            cmds.matchTransform(grp_inner_up_space, grp_up_space)
            cmds.matchTransform(grp_inner_low_space, grp_low_space)

            utils.freeze_group_classic([grp_inner_up_space, grp_inner_low_space],grpOff)

            # connect space up to inner up
            utils.connect(grp_up_space_sub_loc, grp_inner_up_space)
            utils.connect(grp_low_space_sub_ctrl, grp_inner_low_space)

            # up teeth
            for joint in self.list_teeth_up:
                control = utils.create_control(name=joint + "_ctrl", match=joint, parent=grp_inner_up_space, constraint="parent")
                utils.freeze_group_classic(control)
            # low teeth
            for joint in self.list_teeth_low:
                control = utils.create_control(name=joint + "_ctrl", match=joint, parent=grp_inner_low_space, constraint="parent")
                utils.freeze_group_classic(control)

            # tongue
            recent_tongue_ctrl = None
            for joint in self.list_tongue_joints_chain:
                tongue_ctrl = utils.create_control(name=joint + "_ctrl", match=joint, constraint="parent")

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

        def create_curve_blend_shape():
            def duplicate_right_side():
                list_shape_flip = list_R_shape_up + list_R_shape_low

                for i, curve in enumerate(list_L_shape_up + list_L_shape_low):
                    flip_curve = list_shape_flip[i]

                    if cmds.objExists(flip_curve):
                        cmds.delete(flip_curve)

                    cmds.duplicate(curve, n=flip_curve)
                    utils.flip_curve(flip_curve)

            def add_blendshape():
                # add blendshape -------------------
                utils.add_or_create_blend_shape_node(list_target_mesh=list_L_shape_up + list_R_shape_up,
                                                     node_name=self.curve_up_blend_shape_node_name)

                utils.add_or_create_blend_shape_node(list_target_mesh=list_L_shape_low + list_R_shape_low,
                                                     node_name=self.curve_low_blend_shape_node_name)

            def connect_blendshape_v2():
                for i in range(2):
                    if i == 0:  # left
                        ctrl_main_driver = ctrl_main_left
                        crv_up_up, crv_up_low, crv_up_in, crv_up_out, crv_up_upOut, crv_up_downOut, crv_up_upIn, crv_up_downIn = list_L_shape_up
                        crv_low_up, crv_low_low, crv_low_in, crv_low_out, crv_low_upOut, crv_low_downOut, crv_low_upIn, crv_low_downIn = list_L_shape_low

                    elif i == 1:  # right
                        ctrl_main_driver = ctrl_main_right
                        crv_up_up, crv_up_low, crv_up_in, crv_up_out, crv_up_upOut, crv_up_downOut, crv_up_upIn, crv_up_downIn = list_R_shape_up
                        crv_low_up, crv_low_low, crv_low_in, crv_low_out, crv_low_upOut, crv_low_downOut, crv_low_upIn, crv_low_downIn = list_R_shape_low

                    attr_up, attr_down, attr_in, attr_out, attr_up_out, attr_up_in, attr_down_out, attr_down_in = utils.set_driver_blend_shape_v2(
                        transform_name=ctrl_main_driver,
                        list_axis_up_out=["y", "x"],
                        name_tag=self.name)

                    dict_connect = {attr_up: [crv_up_up, crv_low_up],
                                    attr_down: [crv_up_low, crv_low_low],
                                    attr_in: [crv_up_in, crv_low_in],
                                    attr_out: [crv_up_out, crv_low_out],

                                    attr_up_out: [crv_up_upOut, crv_low_upOut],
                                    attr_up_in: [crv_up_upIn, crv_low_upIn],
                                    attr_down_out: [crv_up_downOut, crv_low_downOut],
                                    attr_down_in: [crv_up_downIn, crv_low_downIn]
                                    }

                    for attr_connect in dict_connect.keys():
                        for i, curve_target in enumerate(dict_connect[attr_connect]):
                            node_bsn = self.curve_up_blend_shape_node_name if i == 0 else self.curve_low_blend_shape_node_name

                            cmds.connectAttr(attr_connect, "{}.{}".format(node_bsn, curve_target))

            if not self.enable_curve_blend_shape:
                return

            # create curve mouth shape
            list_L_shape_up = self.list_curve_up
            list_L_shape_low = self.list_curve_low
            list_R_shape_up = [utils.flip_keyword(curve, ignore=False) for curve in list_L_shape_up]
            list_R_shape_low = [utils.flip_keyword(curve, ignore=False) for curve in list_L_shape_low]

            duplicate_right_side()
            add_blendshape()
            connect_blendshape_v2()

        def create_mesh_blend_shape():
            def duplicate_right_side():
                 for i, mesh in enumerate(list_L_shape):
                    flip_mesh = list_R_shape[i]

                    if cmds.objExists(flip_mesh):
                        try:
                            utils.copy_shape(source=mesh,target=flip_mesh)
                        except:
                            raise Exception("{} Have not the same topology like {}".format(flip_mesh,mesh))
                    else:
                        cmds.duplicate(mesh, n=flip_mesh)

            def add_blendshape():
                # add blendshape -------------------
                utils.add_or_create_blend_shape_node(list_target_mesh=list_L_shape + list_R_shape,
                                                     node_name=self.blend_shape_node_name)

            def connect_blendshape():
                for i in range(2):
                    if i == 0:  # left
                        ctrl_main_driver = ctrl_main_left
                        list_shape = list_L_shape

                    elif i == 1:  # right
                        ctrl_main_driver = ctrl_main_right
                        list_shape = list_R_shape
                    else:
                        raise Exception("Command Error")

                    mesh_up, mesh_low, mesh_in, mesh_out, mesh_upOut, mesh_downOut, mesh_upIn, mesh_downIn = list_shape

                    attr_up, attr_down, attr_in, attr_out, attr_up_out, attr_up_in, attr_down_out, attr_down_in = utils.set_driver_blend_shape_v2(
                        transform_name=ctrl_main_driver,
                        list_axis_up_out=["y", "x"],
                        name_tag=self.name)

                    dict_connect = {attr_up: [mesh_up],
                                    attr_down: [mesh_low],
                                    attr_in: [mesh_in],
                                    attr_out: [mesh_out],

                                    attr_up_out: [mesh_upOut],
                                    attr_up_in: [mesh_upIn],
                                    attr_down_out: [mesh_downOut],
                                    attr_down_in: [mesh_downIn]
                                    }

                    for attr_connect in dict_connect.keys():
                        for i, mesh_target_name in enumerate(dict_connect[attr_connect]):
                            cmds.connectAttr(attr_connect, "{}.{}".format(self.blend_shape_node_name, mesh_target_name))

                    # flip R Target
                    if i == 1:
                        for mesh in list_shape:
                            utils.flip_blendshape_target_by_name(self.blend_shape_node_name,mesh)


            if not self.enable_mesh_blend_shape:
                return

            # create curve mouth shape
            list_L_shape = self.list_target_left_emotion_shape
            list_R_shape = [utils.flip_keyword(curve, ignore=False) for curve in list_L_shape]

            duplicate_right_side()
            add_blendshape()
            connect_blendshape()

        def make_finalize():
            if self.debug_mode:
                return None

            list_all_control = list_main_control+list_bind_up_control+list_bind_low_control+list_mid_up_control+list_mid_low_control

            [utils.lock_attributes(control, v=1, l=1, k=0) for control in list_all_control]

            # self.add_to_set(list_all_control)

            for control in [ctrl_main_left,ctrl_main_right]:
                cmds.transformLimits(control, tx=(-1, 1), ty=(-1, 1), tz=(-1, 1),etx=(1,1),ety=(1,1),etz=(1,1))
                cmds.setAttr(control+".tz",l=1,k=0)

        def create_group_space():
            # create space group
            cmds.group(em=1, n=grp_corner_space, p=ctrl_base)
            cmds.group(em=1, n=grp_up_space, p=ctrl_base)
            cmds.group(em=1, n=grp_low_space, p=ctrl_base)

            # connect global space
            cmds.matchTransform(grp_corner_space, self.jaw_bind_joint)
            cmds.matchTransform(grp_up_space, self.jaw_bind_joint)
            cmds.matchTransform(grp_low_space, self.jaw_bind_joint)
            utils.freeze_group_classic([grp_corner_space, grp_low_space, grp_up_space], "grpOff")

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

            # # constraint bind group orient by grp space
            # for grp_pin in list_bind_pin_up[1:len(list_bind_pin_up) - 1]:
            #     cmds.orientConstraint(grp_up_space, grp_pin, mo=1)
            #
            # for grp_pin in list_bind_pin_low:
            #     cmds.orientConstraint(grp_low_space, grp_pin, mo=1)
            #
            # for grp_pin in [list_bind_pin_up[0], list_bind_pin_up[-1]]:
            #     cmds.orientConstraint(grp_corner_space, grp_pin, mo=1)

        # prepare hierarchies
        self.jaw_push_rotate_axis = utils.convert_single_axis_enum_pos(self.jaw_push_rotate_axis)

        shape_mouth_option = "{}_option".format(self.name)

        grp_bind_control = "{}_sub_grp".format(self.name)
        grp_main_control = "{}_main_grp".format(self.name)
        grp_mid_control = "{}_mid_grp".format(self.name)
        grp_blend_shape = "{}_curve_blend_shape_grp".format(self.name)
        grp_mouth_curves = "{}_curve_grp".format(self.name)

        grp_sub_ctrl = "{}_sub_control".format(self.name)
        grp_sub_world = "{}_sub_world_space".format(self.name)
        grp_sub_loc_jaw_space = "{}_sub_locator_world_space".format(self.name)

        ctrl_base = utils.cname(None,self.name+"_base",ctrl)
        ctrl_jaw = utils.cname(None,self.jaw_bind_joint,ctrl)

        crv_bind_up = "{}_up_crv".format(self.name)
        crv_bind_low = "{}_low_crv".format(self.name)

        # main controls / main joints
        ctrl_main_left = "{}_{}_emotion_ctrl".format(self.name, L)
        ctrl_main_right = "{}_{}_emotion_ctrl".format(self.name, R)
        ctrl_main_up = "{}_baseUp_ctrl".format(self.name)
        ctrl_main_low = "{}_baseLow_ctrl".format(self.name)

        loc_main_left = "{}_{}_emotion_loc".format(self.name, L)
        loc_main_right = "{}_{}_emotion_loc".format(self.name, R)
        loc_main_up = "{}_baseUp_loc".format(self.name)
        loc_main_low = "{}_baseLow_loc".format(self.name)

        list_main_control = [ctrl_main_right, ctrl_main_up, ctrl_main_left, ctrl_main_low]

        # mid controls
        list_mid_up_control = ["{}_{}_lipMidUp_Corner".format(ctrl, R),
                               "{}_{}_lipMidUp".format(ctrl, R),
                               "{}_{}_lipMidUp".format(ctrl, center),
                               "{}_{}_lipMidUp".format(ctrl, L),
                               "{}_{}_lipMidUp_Corner".format(ctrl, L)]

        list_mid_low_control = ["{}_{}_lipMidLow".format(ctrl, R),
                                "{}_{}_lipMidLow".format(ctrl, center),
                                "{}_{}_lipMidLow".format(ctrl, L)]

        list_mid_up_joint = [name.replace(ctrl, jnt) for name in list_mid_up_control]
        list_mid_low_joint = [name.replace(ctrl, jnt) for name in list_mid_low_control]

        # group
        grp_corner_space = "{}_AvgRotate_grp".format(self.name)
        grp_up_space = "{}_UpRotate_grp".format(self.name)
        grp_low_space = "{}_LowRotate_grp".format(self.name)

        grp_avg_space_sub_loc = "{}_AvgRotLoc_jaw_space_grp".format(self.name)
        grp_up_space_sub_loc = "{}_UpRotLoc_jaw_space_grp".format(self.name)
        grp_low_space_sub_loc = "{}_LowRotLoc_jaw_space_grp".format(self.name)

        grp_avg_bind_loc_scale_space = "{}_AvgRotLoc_main_scale_space_grp".format(self.name)
        grp_up_bind_loc_scale_space = "{}_UpRotLoc_main_scale_space_grp".format(self.name)
        grp_low_bind_loc_scale_space = "{}_LowRotLoc_main_scale_space_grp".format(self.name)

        grp_avg_space_sub_ctrl = "{}_AvgRotCtrl_grp".format(self.name)
        grp_up_space_sub_ctrl = "{}_UpRotCtrl_grp".format(self.name)
        grp_low_space_sub_ctrl = "{}_LowRotCtrl_grp".format(self.name)

        # bind controls
        list_bind_up_control = ["{}_{}".format(joint, ctrl) for joint in self.list_upper_bind]
        list_bind_low_control = ["{}_{}".format(joint, ctrl) for joint in self.list_lower_bind]

        list_bind_up_locator = ["{}_{}".format(joint, loc) for joint in self.list_upper_bind]
        list_bind_low_locator = ["{}_{}".format(joint, loc) for joint in self.list_lower_bind]

        list_bind_pin_up = []
        list_bind_pin_low = []

        grp_local_locator = "{}_local_locator_grp".format(self.name)
        loc_jaw = "{}_loc".format(self.jaw_bind_joint)

        loc_big_mouth = "{}_local_global_locator".format(self.name)

        # build
        create_hierarchy()

        create_local_locator()
        create_global_control()
        create_jaw()

        create_mouth_curves()
        create_group_space()

        create_main_controls()
        create_mid_controls()
        create_bind_controls()

        drive_bind_controls()

        create_inner_mouth()

        create_curve_blend_shape()
        create_mesh_blend_shape()

        make_finalize()


class Brow(rig_class.Rig):
    """
    Create Lips of mouth

    list_L_brow_joint(stringArray) : left brow joints (sort inner > outer)
    list_R_brow_joint(stringArray) : right brow joints (sort inner > outer)

    L_global_pivot(stringArray) : left brow global pivot for flobal control
    R_global_pivot(stringArray) : right brow global pivot for flobal control

    list_L_brow_control_pivot(stringArray) : list of left brow control pivot (sort inner > outer)
    list_R_brow_control_pivot(stringArray) : list of right brow control pivot (sort inner > outer)

    L_global_pivot(string) : name of left global pivot (reference only position)
    R_global_pivot(string) : name of right global pivot (reference only position)

    middle_joint(string) : name of middle joint

    enable_tip_controller(bool) : enable tip controller
    L_brow_tip_pivot(string) : name of pivot of tip
    L_brow_tip_joint(string) : name of pivot of joint
    R_brow_tip_pivot(string) : name of pivot of tip
    R_brow_tip_joint(string) : name of pivot of joint

    unit_multiplier(long) : amount that control translate will multiplier effect to joint translate (if turn off value will be 1)
    """

    def __init__(self):
        super().__init__()

        self.name = "brow"

        # @ Required Input(Local Joint)
        # $ Required (Local Joint)
        # -
        self.list_L_brow_joint = []
        self.list_R_brow_joint = []
        # -
        self.L_global_pivot = ""
        self.R_global_pivot = ""
        # -
        self.list_L_brow_control_pivot = []
        self.list_R_brow_control_pivot = []

        # $ Middle Control (Optional)
        self.middle_joint = ""

        # $ Tip Control (Optional)
        self.enable_tip_controller = True
        self.L_brow_tip_pivot = ""
        self.L_brow_tip_joint = ""
        # -
        self.R_brow_tip_pivot = ""
        self.R_brow_tip_joint = ""
        # *enable_tip_controller

        # @ Developer
        self.debug_mode = False
        # -
        self.parent = ""
        self.unit_multiplier = 2.0

    def core_build(self):
        def create_hierarchy():
            cmds.group(n=grp_local_locator, em=1, p=self.grp_local_still)
            cmds.group(n=grp_local_control, em=1, p=self.grp_local_anim)

        def create_rig():
            def create_locator_space(flip_scale=False):
                # create locator global
                cmds.spaceLocator(n=loc_global)
                utils.matchTransform(loc_global, pivot_global, pos=True)

                # freeze locator
                grp_global_freeze = utils.freeze_group_classic(loc_global)[0]

                if flip_scale:
                    cmds.setAttr(grp_global_freeze + ".s", 1, -1, 1, typ="double3")
                    cmds.setAttr(grp_global_freeze + ".r", 0, 0, 180, typ="double3")

                # apply constraint
                cmds.parent(grp_global_freeze, grp_local_locator)

                # sub locator
                for i in range(len(list_pivot)):
                    joint = list_joint[i]
                    locator = list_locator_space[i]

                    # create locator
                    cmds.spaceLocator(n=locator)
                    utils.matchTransform(locator, joint, pos=True, rot=True)

                    # freeze locator
                    grp_frz = utils.freeze_group_classic(locator)[0]

                    if flip_scale:
                        cmds.setAttr(grp_frz + ".s", 1, -1, 1, typ="double3")
                        cmds.setAttr(grp_frz + ".r", 0, 0, 180, typ="double3")


                    # parent
                    cmds.parent(grp_frz, grp_local_locator)

                    # apply constraint
                    cmds.parent(joint, locator)

                    # parent locator grp
                    cmds.parent(grp_frz,loc_global)

                # tip locator
                if self.enable_tip_controller:
                    cmds.spaceLocator(n=tip_loc)

                    utils.matchTransform(tip_loc, tip_joint, pos=True, rot=True)
                    grp_tip_frz = utils.freeze_group_classic(tip_loc)[0]

                    if flip_scale:
                        cmds.setAttr(grp_tip_frz + ".s", 1, -1, 1, typ="double3")
                        cmds.setAttr(grp_tip_frz + ".r", 0, 0, 180, typ="double3")

                    cmds.parent(grp_tip_frz,loc_global)
                    cmds.parent(tip_joint,tip_loc)

                    # point between brow a and brow b
                    cmds.pointConstraint(list_locator_space[0],list_locator_space[1],grp_tip_frz,mo=1)

            def create_controller(flip_scale=False):
                # each control side ------------------------------------
                # global control
                utils.create_control(name=ctrl_global,parent=grp_local_control)
                utils.matchTransform(ctrl_global, pivot_global, pos=1)

                frz_global = utils.freeze_group_classic(ctrl_global)[0]

                if flip_scale:
                    cmds.setAttr(frz_global + ".s", 1, -1, 1, typ="double3")
                    cmds.setAttr(frz_global + ".r", 0, 0, 180, typ="double3")

                utils.connect(ctrl_global, loc_global, name=self.name)

                # sub controls
                for i in range(len(list_pivot)):
                    joint = list_joint[i]
                    control = list_control[i]
                    pivot = list_pivot[i]
                    locator = list_locator_space[i]

                    utils.create_control(name=control)
                    utils.matchTransform(control, pivot, pos=1, rot=1)

                    grp_frz = utils.freeze_group_classic(control,"GrpOff")[0]

                    if flip_scale:
                        cmds.setAttr(grp_frz + ".s", 1, -1, 1, typ="double3")
                        cmds.setAttr(grp_frz + ".r", 0, 0, 180, typ="double3")

                    cmds.parent(grp_frz, ctrl_global)

                    utils.connect(control, locator, name=self.name, translate_multiplier=self.unit_multiplier)

                # tip controller
                if self.enable_tip_controller:
                    control = utils.create_control(name=tip_ctrl)
                    utils.matchTransform(control, tip_pivot, pos=True, rot=True)

                    grp_tip_frz = utils.freeze_group_classic(control)[0]

                    if flip_scale:
                        cmds.setAttr(grp_tip_frz + ".s", 1, -1, 1, typ="double3")
                        cmds.setAttr(grp_tip_frz + ".r", 0, 0, 180, typ="double3")

                    cmds.parent(grp_tip_frz, list_control[0])

                    utils.connect(control, tip_loc, name=self.name, translate_multiplier=self.unit_multiplier)
                pass

            def create_middle_control():
                # middle locator
                cmds.spaceLocator(n=loc_middle)
                utils.matchTransform(loc_middle, self.middle_joint, pos=1, rot=1)

                cmds.parent(loc_middle, grp_local_locator)
                grp_frz = utils.freeze_group_classic(loc_middle)[0]

                cmds.parent( self.middle_joint,loc_middle)

                cmds.pointConstraint(self.list_L_brow_joint[0], self.list_R_brow_joint[0], grp_frz, mo=1)

                # middle controller
                utils.create_control(name=ctrl_middle, match=self.middle_joint, parent=grp_local_control,connect_match=True)

                utils.freeze_group(ctrl_middle,"grpOff2")
                cmds.pointConstraint(list_L_brow_control[0], list_R_brow_control[0], cmds.listRelatives(ctrl_middle,p=1)[0], mo=1)


            for i in range(2):
                if i == 0:  # L Side
                    ctrl_global = ctrl_L_global_rig
                    pivot_global = self.L_global_pivot
                    list_control = list_L_brow_control
                    list_pivot = self.list_L_brow_control_pivot
                    list_joint = self.list_L_brow_joint
                    loc_global = "global_{}_loc".format(L)
                    list_locator_space = [joint + "_loc" for joint in self.list_L_brow_joint]
                    flip_scale = False

                    tip_ctrl = ctrl_L_tip
                    tip_pivot = self.L_brow_tip_pivot
                    tip_joint = self.L_brow_tip_joint
                    tip_loc = self.L_brow_tip_joint + "_loc"
                elif i == 1:
                    ctrl_global = ctrl_R_global_rig
                    pivot_global = self.R_global_pivot
                    list_control = list_R_brow_control
                    list_pivot = self.list_R_brow_control_pivot
                    list_joint = self.list_R_brow_joint
                    loc_global = "global_{}_loc".format(R)
                    list_locator_space = [joint + "_loc" for joint in self.list_R_brow_joint]
                    flip_scale = True

                    tip_ctrl = ctrl_R_tip
                    tip_pivot = self.R_brow_tip_pivot
                    tip_joint = self.R_brow_tip_joint
                    tip_loc = self.R_brow_tip_joint + "_loc"

                create_locator_space(flip_scale)
                create_controller(flip_scale)

            # create_middle_control() if self.middle_joint else None

        def make_finalize():
            if self.debug_mode:
              return

            list_all_control = list_L_brow_control+list_R_brow_control+[ctrl_middle,ctrl_L_global_rig,ctrl_R_global_rig,ctrl_L_tip,ctrl_R_tip]

            [utils.lock_attributes(control, v=1, k=0, l=1) for control in list_all_control]

        ctrl_L_global_rig = "{}_browAll_{}".format(L, ctrl)
        ctrl_R_global_rig = "{}_browAll_{}".format(R, ctrl)

        list_L_brow_control = [joint + "_ctrl" for joint in self.list_L_brow_joint]
        list_R_brow_control = [joint + "_ctrl" for joint in self.list_R_brow_joint]

        ctrl_L_tip = "{}_{}_tip_{}".format(self.name,L,ctrl)
        ctrl_R_tip = "{}_{}_tip_{}".format(self.name,R,ctrl)

        grp_local_locator = "{}_local_joint".format(self.name)
        grp_local_control = "{}_transform_control".format(self.name)

        loc_middle = self.middle_joint + "_loc"
        ctrl_middle = self.middle_joint + "_ctrl"

        create_hierarchy()
        create_rig()
        make_finalize()

class Secondary(rig_class.Rig):
    """
    Facial Secondary Local

    All in One Rig

    Variables:
    list_left_puff_blend_shape_name(stringArray) : list of left puff blend shape (Puff In and Puff Out)
    head_up_joint(string) : name of up joint
    head_low_joint(string) : name of low joint

    enable_cheeks(bool) : enable_cheeks
    
    left_cheek_joint(string) : ""
    right_cheek_joint(string) : ""

    enable_cheeks_blend_shape(bool) : enable_cheeks_blend_shape

    cheek_blend_shape_node_name(string) : cheek_blend_shape_node_name
    base_mesh(string) : base_mesh

    list_left_puff_blend_shape_name(stringArray) : list left puff blend shape node name

    enable_upper_cheeks(bool) : enable upper cheek
    
    list_left_upper_cheek_joint : list left upper cheek joint
    list_right_upper_cheek_joint : list right upper cheek joint

    enable_nose(bool) : enable_nose

    nose_joint(string) : name of nose joint

    enable_ears(bool) : enable_ears

    list_left_ear_joint(stringArray) : list left ear joint
    list_right_ear_joint(stringArray) : list right ear joint

    """
    def __init__(self):
        super().__init__()

        self.name = "Secondary"

        # @ Main Setting
        # $ Parent (Required)
        self.head_up_joint = ""
        self.head_low_joint = ""
        # -
        self.base_mesh = ""

        # $ Cheeks
        self.enable_cheeks = False
        # -
        self.left_cheek_joint = ""
        self.right_cheek_joint = ""
        # -
        self.enable_cheeks_blend_shape = False
        # -
        self.cheek_blend_shape_node_name = ""
        self.list_left_puff_blend_shape_name = []
        # * enable_cheeks

        # $ Upper Cheeks
        self.enable_upper_cheeks = False
        # -
        self.list_left_upper_cheek_joint = []
        self.list_right_upper_cheek_joint = []

        # $ Nose
        self.enable_nose = False
        # -
        self.nose_joint = ""

        # $ Ears
        self.enable_ears = False
        # -
        self.list_left_ear_joint = []
        self.list_right_ear_joint = []

        self.debug_mode = False

    def core_build(self):
        def build_cheeks():
            def add_cheeks_blend_shape():
                if not self.enable_cheeks_blend_shape:
                    return

                # get variables
                target_L_puff_in,target_L_puff_out = self.list_left_puff_blend_shape_name
                target_R_puff_in, target_R_puff_out = [ utils.flip_keyword(name) for name in self.list_left_puff_blend_shape_name ]

                list_source = [target_L_puff_in,target_L_puff_out]
                list_target = [target_R_puff_in,target_R_puff_out]

                # Create Right Side Mesh
                for i,target in enumerate(list_target):
                    source = list_target[i]

                    if cmds.objExists(target):
                        utils.copy_shape(source,target)
                    else:
                        cmds.duplicate(source,n=target)

                # Add Blendshape
                utils.add_or_create_blend_shape_node(list_target_mesh=list_source+list_target,
                                                     base_mesh=self.base_mesh,
                                                     node_name=self.cheek_blend_shape_node_name)

                # Add Attribute and Connet
                cmds.addAttr(ctrl_left_cheek,ln="puff",k=1,at="float",min=-10,max=10)
                cmds.addAttr(ctrl_right_cheek,ln="puff",k=1,at="float",min=-10,max=10)

                list_connect = [[10,"{}.{}".format(self.cheek_blend_shape_node_name,target_L_puff_out),ctrl_left_cheek + ".puff"],
                                 [-10,"{}.{}".format(self.cheek_blend_shape_node_name, target_L_puff_in),ctrl_left_cheek + ".puff"],
                                 [10,"{}.{}".format(self.cheek_blend_shape_node_name, target_R_puff_out),ctrl_right_cheek + ".puff"],
                                 [-10,"{}.{}".format(self.cheek_blend_shape_node_name, target_R_puff_in),ctrl_right_cheek + ".puff"],
                                ]

                for list_data in list_connect:
                    driver_value , output_attr , input_attr =  list_data

                    utils.set_driver_blend_shape_single(input_attr=input_attr,
                                                        driver_value=driver_value,
                                                        output_attr=output_attr,
                                                        name_tag=self.name)

            def add_cheek_control():
                # create local control
                cmds.spaceLocator(n=loc_left_cheek)
                cmds.spaceLocator(n=loc_right_cheek)

                utils.matchTransform(loc_left_cheek,self.left_cheek_joint,pos=True,rot=True)
                utils.matchTransform(loc_right_cheek,self.right_cheek_joint,pos=True,rot=True)

                cmds.parent(loc_left_cheek, loc_right_cheek, grp_locator_cheeks)
                utils.freeze_group_classic([loc_left_cheek, loc_right_cheek])

                # create controls
                utils.create_control(name=ctrl_left_cheek, match=self.left_cheek_joint, parent=grp_cheek_anim,freeze_group=True,custom_freeze_group_name=grpCtrl)
                utils.create_control(name=ctrl_right_cheek, match=self.right_cheek_joint, parent=grp_cheek_anim,freeze_group=True,custom_freeze_group_name=grpCtrl)

                utils.connect(ctrl_left_cheek, loc_left_cheek)
                utils.connect(ctrl_right_cheek, loc_right_cheek)

                # flip scale for right side
                cmds.setAttr(cmds.listRelatives(ctrl_right_cheek, p=1)[0] + ".s", -1, -1, -1, typ="double3")
                cmds.setAttr(cmds.listRelatives(loc_right_cheek, p=1)[0] + ".s", -1, -1, -1, typ="double3")

                # parent joint to locator
                cmds.parent(self.left_cheek_joint, loc_left_cheek)
                cmds.parent(self.right_cheek_joint, loc_right_cheek)

            if not self.enable_cheeks:
                return

            if not utils.is_descendant_of(self.left_cheek_joint,grp_local):
                raise Exception("left cheek joint and right cheek joint require local joints")


            # variables
            ctrl_left_cheek = "{}_{}".format(self.left_cheek_joint,ctrl)
            ctrl_right_cheek = "{}_{}".format(self.right_cheek_joint,ctrl)

            loc_left_cheek = "{}_{}".format(self.left_cheek_joint,loc)
            loc_right_cheek = "{}_{}".format(self.right_cheek_joint,loc)

            # create hierarchy
            grp_locator_cheeks = cmds.group(em=1,n="cheeks_local_grp",p=self.grp_local_still)
            grp_cheek_anim = cmds.group(em=1,n="cheek_control_grp",p=grp_head_low_parent)


            add_cheek_control()
            add_cheeks_blend_shape()
        def build_ears():
            def create_local(list_joint,list_locator):
                parent = None

                for i,joint in enumerate(list_joint):
                    locator = list_locator[i]

                    # create locator
                    cmds.spaceLocator(n=locator)
                    utils.matchTransform(locator,joint,pos=True,rot=True)

                    grp_frz = utils.freeze_group_classic(locator)[0]

                    # flip grp frz
                    if joint in self.list_right_ear_joint:
                        # flip scale for right side
                        # cmds.setAttr(grp_frz+ ".r", 1, -1, 1, typ="double3")
                        cmds.setAttr(grp_frz+ ".s", -1, -1, -1, typ="double3")

                    # parent
                    if parent:
                        cmds.parent(grp_frz, parent)
                    else:
                        cmds.parent(grp_frz, self.grp_local_still)

                    # parent joint to locator
                    cmds.parent(joint,locator)

                    parent = joint

            def create_control(list_control,list_locator):
                if list_control == list_ctrl_left_ears:
                    list_joint = self.list_left_ear_joint
                elif list_control == list_ctrl_right_ears:
                    list_joint = self.list_right_ear_joint
                else:
                    raise Exception("Command Error")

                parent_control = None
                for i, control in enumerate(list_control):
                    joint = list_joint[i]
                    locator = list_locator[i]

                    utils.create_control(name=control, match=joint, freeze_group=True,custom_freeze_group_name=grpCtrl)
                    utils.connect(control,locator)
                    grp_frz = cmds.listRelatives(control, p=1)[0]

                    # flip scale for right side
                    if control in list_ctrl_right_ears:
                        cmds.setAttr( grp_frz+ ".s", -1, -1, -1, typ="double3")

                    # parent to chain
                    if not parent_control:
                        cmds.parent(grp_frz, grp_anim_ears)
                    else:
                        cmds.parent(grp_frz, parent_control)

                    # set new variables
                    parent_control = control

            if not self.enable_ears:
                return

            # variables
            list_ctrl_left_ears = ["{}_ctrl".format(joint) for joint in self.list_left_ear_joint]
            list_ctrl_right_ears = ["{}_ctrl".format(joint) for joint in self.list_right_ear_joint]

            list_loc_left_ears = ["{}_loc".format(joint) for joint in self.list_left_ear_joint]
            list_loc_right_ears = ["{}_loc".format(joint) for joint in self.list_right_ear_joint]

            # create hierarchy
            grp_anim_ears = cmds.group(em=1, n="ears_control_grp", p=grp_head_up_parent)

            create_local(self.list_left_ear_joint,list_loc_left_ears)
            create_local(self.list_right_ear_joint,list_loc_right_ears)

            # create controls
            create_control(list_ctrl_left_ears,list_loc_left_ears)
            create_control(list_ctrl_right_ears,list_loc_right_ears)

        def build_nose():
            if not self.enable_nose:
                return None

            # variables
            ctrl_nose = "{}_ctrl".format(self.nose_joint)

            # hierarchy
            cmds.parent(self.nose_joint,self.grp_local_still)
            utils.freeze_group_classic(self.nose_joint)

            # create control
            utils.create_control(ctrl_nose,parent=grp_head_low_parent,match=self.nose_joint,connect_match=True,freeze_group=True)

        def build_upper_cheeks():
            def create_local(list_joint):
                parent = None

                for joint in list_joint:
                    if parent is None:
                        cmds.parent(joint, self.grp_local_still)
                    else:
                        cmds.parent(joint, parent)

                    utils.freeze_group_classic(joint)

                    parent = joint

                    if joint in self.list_right_upper_cheek_joint:
                        # flip scale for right side
                        cmds.setAttr(cmds.listRelatives(joint, p=1)[0] + ".s", -1, -1, -1, typ="double3")

            def create_control(list_control):
                if list_control == list_ctrl_left_upper_cheeks:
                    list_joint = self.list_left_upper_cheek_joint
                elif list_control == list_ctrl_right_upper_cheeks:
                    list_joint = self.list_right_upper_cheek_joint
                else:
                    raise Exception("Command Error")

                parent_control = None
                for i, control in enumerate(list_control):
                    joint = list_joint[i]

                    if parent_control == None:
                        parent = grp_anim_upper_cheeks
                    else:
                        parent = parent_control

                    utils.create_control(name=control, match=joint, connect_match=True, parent=parent, freeze_group=True)

                    if control in list_ctrl_right_upper_cheeks:
                        # flip scale for right side
                        cmds.setAttr(cmds.listRelatives(control, p=1)[0] + ".s", -1, -1, -1, typ="double3")

                    parent_control = control

            if not self.enable_ears:
                return

            # variables
            list_ctrl_left_upper_cheeks = ["{}_ctrl".format(joint) for joint in self.list_left_upper_cheek_joint]
            list_ctrl_right_upper_cheeks = ["{}_ctrl".format(joint) for joint in self.list_right_upper_cheek_joint]

            # create hierarchy
            grp_anim_upper_cheeks = cmds.group(em=1, n="upper_cheeks_control_grp", p=grp_head_up_parent)

            create_local(self.list_left_upper_cheek_joint)
            create_local(self.list_right_upper_cheek_joint)

            # create controls
            create_control(list_ctrl_left_upper_cheeks)
            create_control(list_ctrl_right_upper_cheeks)

        if not self.head_up_joint or not self.head_low_joint:
            raise Exception("Head Joint must be input")

        # set group
        grp_head_up_parent = cmds.group(em=1,n="{}_up_parent_grp".format(self.name),p=self.grp_local_anim)
        grp_head_low_parent = cmds.group(em=1,n="{}_low_parent_grp".format(self.name),p=self.grp_local_anim)

        cmds.parentConstraint(self.head_up_joint,grp_head_up_parent)
        cmds.parentConstraint(self.head_low_joint,grp_head_low_parent)

        build_cheeks()
        build_ears()
        build_nose()
        build_upper_cheeks()

    def core_unbuild(self):
        pass

class Eyelid(rig_class.Rig):
    """
    Create Eye Lid systems

    Variables:
    list_jnt_lid_upper (stringArray) : List of Upper Lid Joint (Sort by Inner to Outer ,Include Corner Joint)
    list_jnt_lid_lower (stringArray) : List of Upper Lid Joint (Sort by Inner to Outer)

    list_main_control_pivot (stringArray) : List of Inner , Up , Outer , Low Pivot of main control (Reference only postion)

    axis_forward(string) : axis direction of aiming forward. for example "x"
    axis_pole(string) : axis direction of elbow that aiming to pole controller. for example "x","-x"
    default_switch_value(string) : Default value of Fk/Ik Switch ,Fk(0) ,Ik (1)
    """

    def __init__(self):
        super().__init__()

        self.name = "{}_EyeLid".format(L)

        # @ Required Input
        # $ Joint (Global Joint)
        self.jnt_eye_ball = ""
        self.jnt_eye_global = ""

        # $ Joint (Local Joint)
        self.list_jnt_lid_upper = []
        self.list_jnt_lid_lower = []

        # -
        self.axis_up_eye_ball = "y"
        self.axis_aim_eye_ball = "z"

        # -
        self.list_main_control_pivot = []

        # $ Parent
        self.parent = ""

        # @ Blend Shape


        # $ Curve Blend Shape
        self.enable_curve_blend_shape = False
        # -
        self.curve_blendshape_up_rotate_in = ""
        self.curve_blendshape_up_rotate_out = ""
        self.curve_blendshape_up_push = ""
        # -
        self.curve_blendshape_down_rotate_in = ""
        self.curve_blendshape_down_rotate_out = ""
        self.curve_blendshape_low_push = ""
        # * enable_curve_blend_shape

        # $ Mesh Blend Shape
        self.enable_mesh_blend_shape = False
        # -
        self.mesh_blend_shape_node_name = ""
        self.target_blendshape = ""
        # -
        self.mesh_blendshape_up_push_volume = ""
        self.mesh_blendshape_up_rotate_in = ""
        self.mesh_blendshape_up_rotate_out = ""

        # -
        self.mesh_blendshape_down_push_volume = ""
        self.mesh_blendshape_down_rotate_in = ""
        self.mesh_blendshape_down_rotate_out = ""
        # * enable_mesh_blend_shape

        # $ Blend Shape Values Setting
        self.value_up_control_drive = 3
        self.value_down_control_drive = 3
        # -
        self.value_up_rotate_in = 45
        self.value_down_rotate_in = 45

        # @ Features
        # $ Auto Fleshy Features
        self.enable_auto_fleshy = False
        # -
        self.value_fleshy_up_intensity = 0.2
        self.value_fleshy_side_intensity = 0.2
        # *enable_auto_fleshy

        # $ Add Outer Eye Lid
        self.list_upper_outer_joint = []
        self.list_lower_outer_joint = []

        # @ Auto Import Curve Weight
        self.curve_up_weight_path = ""
        self.curve_low_weight_path = ""

        # @ Developer
        self.debug_mode = False
        # -
        self.mirror_control_scale = False
        self.sync_option_shape_path = ""
        self.preserve_corner_joint_curve = True

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
            def create_control_each():

                # Create Controller --------------------------------------------------
                # create ctrl global
                utils.create_control(name=ctrl_global, match=self.jnt_eye_global, parent=self.grp_local_anim,freeze_group=True,connect_match=True)

                if self.mirror_control_scale:
                    cmds.setAttr("{}.s".format(cmds.listRelatives(ctrl_global,p=1)[0]), -1, -1, -1, typ="double3")

            def create_hierarchy():
                # add attribute to option shape
                utils.add_option_shape(ctrl_global, ctrl_global_option)

                cmds.addAttr(ctrl_global_option, ln=attr_driver_up.split(".")[-1], at="float", k=1, dv=3)
                cmds.addAttr(ctrl_global_option, ln=attr_driver_low.split(".")[-1], at="float", k=1, dv=3)

                # add global control hierarchy
                # create group under control
                cmds.group(em=1, n=grp_sub_control.format(self.name), p=ctrl_global)
                cmds.setAttr(grp_sub_control + ".inheritsTransform", 0)


                cmds.group(em=1, n=grp_main_control, p=ctrl_global)

                cmds.group(em=1, n=grp_fleshy_up_down, p=grp_main_control)
                cmds.group(em=1, n=grp_fleshy_side, p=grp_main_control)


                cmds.matchTransform(grp_main_control, ctrl_global)

            create_control_each()
            create_hierarchy()

        def create_fleshy():
            # connect fleshy
            if not self.enable_auto_fleshy:
                return

            cmds.addAttr(ctrl_global_option, ln=attr_fleshy_vertical.split(".")[-1], dv=self.value_fleshy_up_intensity, at="float", k=1)
            cmds.addAttr(ctrl_global_option, ln=attr_fleshy_horizontal.split(".")[-1], dv=self.value_fleshy_side_intensity, at="float", k=1)

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
            utils.freeze_group_classic(grp_orient_space)

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

                node_bsn = utils.add_or_create_blend_shape_node(list_target_mesh=[blendshape], base_mesh=[target], node_name="{}_bsn".format(target))

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
            create_blendshape_each(self.curve_blendshape_up_rotate_in, crv_bind_up, -45, attr_driver=ctrl_main_up + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blendshape_up_rotate_in else None
            create_blendshape_each(self.curve_blendshape_up_rotate_out, crv_bind_up, 45, attr_driver=ctrl_main_up + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blendshape_up_rotate_out else None
            create_blendshape_each(self.curve_blendshape_down_rotate_in, crv_bind_low, -45, attr_driver=ctrl_main_low + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blendshape_down_rotate_in else None
            create_blendshape_each(self.curve_blendshape_down_rotate_out, crv_bind_low, 45, attr_driver=ctrl_main_low + ".rz", isClamp=True,
                                   custom_clamp_length=[0, None]) if self.curve_blendshape_down_rotate_out else None

            create_blendshape_each(self.curve_blendshape_up_push, crv_bind_up, self.value_up_control_drive, attr_driver=ctrl_main_up + ".ty",
                                   isClamp=True) if self.curve_blendshape_up_push else None
            create_blendshape_each(self.curve_blendshape_low_push, crv_bind_low, self.value_down_control_drive, attr_driver=ctrl_main_low + ".ty",
                                   isClamp=True) if self.curve_blendshape_low_push else None

            # mesh blendshape
            create_blendshape_each(self.mesh_blendshape_up_push_volume, self.target_blendshape, self.value_up_control_drive,
                                   attr_driver=ctrl_main_up + ".ty") if self.mesh_blendshape_up_push_volume else None
            create_blendshape_each(self.mesh_blendshape_down_push_volume, self.target_blendshape, self.value_down_control_drive,
                                   attr_driver=ctrl_main_low + ".ty") if self.mesh_blendshape_down_push_volume else None

            create_blendshape_each(self.mesh_blendshape_up_rotate_in, self.target_blendshape, self.value_up_rotate_in,
                                   attr_driver=ctrl_main_up + ".rz") if self.mesh_blendshape_up_rotate_in else None
            create_blendshape_each(self.mesh_blendshape_up_rotate_out, self.target_blendshape, self.value_up_rotate_in * -1,
                                   attr_driver=ctrl_main_up + ".rz") if self.mesh_blendshape_up_rotate_out else None

            create_blendshape_each(self.mesh_blendshape_down_rotate_in, self.target_blendshape, self.value_down_rotate_in,
                                   attr_driver=ctrl_main_low + ".rz") if self.mesh_blendshape_down_rotate_in else None
            create_blendshape_each(self.mesh_blendshape_down_rotate_out, self.target_blendshape, self.value_down_rotate_in * -1,
                                   attr_driver=ctrl_main_low + ".rz") if self.mesh_blendshape_down_rotate_out else None

        def create_main_control():
            def create_each_control():
                # create upper,lower main ctrl

                utils.create_control(name=ctrl_main_up, parent=grp_fleshy_up_down)
                utils.create_control(name=ctrl_main_low, parent=grp_fleshy_up_down)

                utils.create_control(name=ctrl_main_outer, parent=grp_fleshy_side)
                utils.create_control(name=ctrl_main_inner, parent=grp_fleshy_side)

            def match_all_control():
                # match position of pivot
                pivot_ctrl_inner_main, pivot_ctrl_up_main, pivot_ctrl_outer_main, pivot_ctrl_low_main = self.list_main_control_pivot

                cmds.matchTransform(ctrl_main_up, pivot_ctrl_up_main, pos=1)
                cmds.matchTransform(ctrl_main_low, pivot_ctrl_low_main, pos=1)
                cmds.matchTransform(ctrl_main_inner, pivot_ctrl_inner_main, pos=1)
                cmds.matchTransform(ctrl_main_outer, pivot_ctrl_outer_main, pos=1)

                list_main_ctrl = [ctrl_main_up, ctrl_main_outer, ctrl_main_inner, ctrl_main_low]
                list_main_joint = [jnt_main_up, jnt_main_outer, jnt_main_inner, jnt_main_low]
                for i, joint in enumerate(list_main_joint):
                    cmds.joint(name=joint)
                    utils.match_parent(joint, list_main_ctrl[i])

                utils.freeze_group_classic(list_main_ctrl)

            create_each_control()
            match_all_control()
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

        def create_bind_control():
            def create_joint_chain(list_joint, list_control,list_locator):
                for i, joint in enumerate(list_joint):
                    locator = list_locator[i]
                    control = list_control[i]

                    # create joint chain
                    cmds.select(cl=1)
                    grp_aim = cmds.group(em=1,n="{}_aim_{}".format(joint,grp))
                    cmds.matchTransform(grp_aim, self.jnt_eye_ball,pos=True)
                    cmds.makeIdentity(grp_aim, a=1, s=1, r=1)

                    cmds.parent(grp_aim, grp_slide_joint)

                    # create ik handle
                    loc_aim = cmds.spaceLocator(n=joint + "_aim_loc")

                    # create controller
                    utils.create_control(name=control, parent=grp_sub_control, match=joint)

                    cmds.parent(loc_aim, control)

                    # parent locator offset group under jnt b
                    cmds.parent(cmds.listRelatives(locator,p=1)[0],grp_aim)

                    if self.mirror_control_scale:
                        aim = [0, 0, -1]
                        u = [-1, 0, 0]
                        wu = [-1, 0, 0]
                    else:
                        aim = [0, 0, 1]
                        u = [1, 0, 0]
                        wu = [1, 0, 0]

                    cmds.aimConstraint(loc_aim, grp_aim, mo=1, aim=aim, u=u, wuo=loc_aim_up_space, wut="objectrotation", wu=wu)

            create_joint_chain(self.list_jnt_lid_upper, list_bind_up_control,list_loc_lid_upper)
            create_joint_chain(self.list_jnt_lid_lower, list_bind_low_control,list_loc_lid_lower)

        def create_hierarchy():
            cmds.group(em=1, n=grp_curves, p=self.grp_local_still)

            cmds.spaceLocator(n=loc_aim_up_space)
            utils.match_parent(loc_aim_up_space, self.grp_local_anim)

        def create_locator_space():
            list_joint = self.list_jnt_lid_upper+self.list_jnt_lid_lower+self.list_upper_outer_joint+self.list_lower_outer_joint+[self.jnt_eye_global]
            list_locator = list_loc_lid_upper+list_loc_lid_lower+list_loc_lid_upper_outer+list_loc_lid_lower_outer+[loc_eye_global]

            for i,joint in enumerate(list_joint):
                locator = list_locator[i]

                cmds.spaceLocator(n=locator)
                utils.matchTransform(locator,joint,pos=True,rot=True)

                cmds.parent(locator,self.grp_local_still)

                cmds.parent(joint,locator)

            cmds.parent(list_loc_lid_upper+list_loc_lid_lower,self.jnt_eye_global)

            # create hierarchy
            cmds.group(em=1, n=grp_slide_joint)
            utils.match_parent(grp_slide_joint,self.jnt_eye_global)

            # freeze all locator
            utils.freeze_group_classic(list_locator)


        # variables
        list_axis_side = ["x", "y", "z"]
        list_axis_side.remove(self.axis_up_eye_ball)
        list_axis_side.remove(self.axis_aim_eye_ball)
        axis_side = list_axis_side[0]

        list_loc_lid_upper = [joint + "_loc" for joint in self.list_jnt_lid_upper]
        list_loc_lid_lower = [joint + "_loc" for joint in self.list_jnt_lid_lower]

        list_loc_lid_upper_outer = [joint + "_loc" for joint in self.list_upper_outer_joint]
        list_loc_lid_lower_outer = [joint + "_loc" for joint in self.list_lower_outer_joint]

        loc_eye_global = self.jnt_eye_global + "_loc"

        grp_sub_up_control = "{}_sub_up_control_grp".format(self.name)
        grp_sub_low_control = "{}_sub_low_control_grp".format(self.name)

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

        grp_fleshy_up_down = "{}_fleshy_up_down_grp".format(self.name)
        grp_fleshy_side = "{}_fleshy_side_grp".format(self.name)

        # create groups
        grp_main_control = "{}_mainCtl_grp".format(self.name)
        grp_sub_control = "{}_subCtl_grp".format(self.name)
        grp_slide_joint = "{}_slideCtl_grp".format(self.name)

        grp_curves = "{}_curves_grp".format(self.name)

        attr_fleshy_vertical = "{}.fleshyX".format(ctrl_global_option)
        attr_fleshy_horizontal = "{}.fleshyY".format(ctrl_global_option)
        attr_fleshy_z = "{}.fleshyZ".format(ctrl_global_option)
        attr_driver_up = "{}.closedUpValue".format(ctrl_global_option)
        attr_driver_low = "{}.closedLowValue".format(ctrl_global_option)

        list_up_drive_output_grp = ["{}_grpDriveUp".format(joint) for joint in self.list_jnt_lid_upper]
        list_low_drive_output_grp = ["{}_grpDriveLow".format(joint) for joint in self.list_jnt_lid_lower]

        list_ctrl_lid_upper = []
        list_ctrl_lid_lower = []

        # Build
        create_hierarchy()
        create_locator_space()
        create_curves()

        # set_joint_scale_compensate()
        #
        create_global_control()
        create_main_control()

        create_fleshy()

        create_bind_control()
        # pin_bind_controls()

        # extra
        # create_blendshape()
        #
        # create_outer_joints()

        make_finalize()