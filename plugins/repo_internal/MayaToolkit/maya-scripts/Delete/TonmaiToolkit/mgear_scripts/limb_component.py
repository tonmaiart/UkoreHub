import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.rigbits.facial_rigger.constraints import namePrefix
from mgear.shifter import component, log_window
import math
import maya.api.OpenMaya as om
from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive
import math
from TonmaiToolkit.core import Utility, Misc, Create, Connection, Transform
from importlib import reload


class Limb(component.Main):
    """Shifter component Class"""

    def __init__(self, rig, guide, is_arm):
        super().__init__(rig=rig, guide=guide)

        self.is_arm = is_arm

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        def create_option_control():
            # create control option
            self.ctrl_option = self.addCtl(
                self.grp_controls,
                "option",
                m=transform.getTransformFromPos((0, 0, 0)),
                color=17,
                iconShape="cube",
                w=0.12 * self.size,
                h=0.12 * self.size,
                d=0.12 * self.size,
            )

            pm.connectAttr(
                "{}.worldMatrix".format(self.dict_limb["loc_main"][2]),
                "{}.offsetParentMatrix".format(self.ctrl_option),
            )
            attribute.reset_SRT([self.ctrl_option])
            attribute.lockAttribute(self.ctrl_option)
            self.ctrl_option.inheritsTransform.set(False)

        def create_fkik_swtich_attribute():
            # create attr switch ----------------------
            pm.addAttr(
                self.ctrl_option,
                ln="FkIk",
                min=0,
                max=self.switch_range,
                at="float",
                k=1,
            )
            node_uc_attr_switch = Connection.connect_conversion_unit(
                input="{}.FkIk".format(self.ctrl_option), factor=1 / self.switch_range
            )
            self.attr_switch = "{}.output".format(node_uc_attr_switch)

        def create_locator_bind():
            def create_ribbon_bind_joints(amount, typ="loc_up"):
                if typ == "loc_up":
                    keyword = "up"
                    matrixA = transform.setMatrixScale(
                        self.guide.tra["root"], self.scale_vector
                    )
                    matrixB = transform.setMatrixScale(
                        self.guide.tra["low"], self.scale_vector
                    )
                elif typ == "loc_low":
                    keyword = "low"
                    matrixA = transform.setMatrixScale(
                        self.guide.tra["low"], self.scale_vector
                    )
                    matrixB = transform.setMatrixScale(
                        self.guide.tra["end"], self.scale_vector
                    )

                list_name = [("{}_{}".format(keyword, i + 1)) for i in range(amount)]

                for i, name in enumerate(list_name):
                    loc_bind = primitive.addLocator(
                        self.grp_bind_loc,
                        self.getName("{}_loc".format(name)),
                        m=matrixA,
                    )

                    if typ == "loc_up":
                        parent_joint = "root"
                    elif typ == "loc_low":
                        parent_joint = "low"

                    self.jnt_pos.append(
                        {
                            "obj": loc_bind,
                            "name": name,
                            "newActiveJnt": None,
                            "gearMulMatrix": False,
                            "vanilla_nodes": True,
                        }
                    )

                    self.dict_ribbon[typ].append(loc_bind)

                # snap position
                between_pos = Transform.get_linear_position_division(
                    posA=transform.getPositionFromMatrix(matrixA),
                    posB=transform.getPositionFromMatrix(matrixB),
                    division=5 - 2,
                )

                list_position = (
                    [transform.getPositionFromMatrix(matrixA)]
                    + between_pos
                    + [transform.getPositionFromMatrix(matrixB)]
                )

                for i, loc_bind in enumerate(self.dict_ribbon[typ]):
                    pm.xform(loc_bind, ws=1, t=list_position[i])

            # create locator bind
            recent_fk = None
            recent_loc_ik = None
            recent_loc_fk = None
            recent_loc_bind = None

            list_joint_chain_name = ["root", "low", "end"]
            for index, name in enumerate(list_joint_chain_name):
                # chain fk control
                if recent_fk:
                    parent_fk = recent_fk
                else:
                    parent_fk = self.grp_fk_controls

                if recent_loc_ik:
                    parent_recent_loc_ik = recent_loc_ik
                else:
                    parent_recent_loc_ik = self.grp_ik_locator

                if recent_loc_fk:
                    parent_recent_loc_fk = recent_loc_fk
                else:
                    parent_recent_loc_fk = self.grp_fk_locator

                if recent_loc_bind:
                    parent_recent_loc_bind = recent_loc_bind
                else:
                    parent_recent_loc_bind = self.grp_bind_loc

                if name == "low":
                    ik_shape = "sphere"
                    ik_size = 0.2
                else:
                    ik_shape = "cube"
                    ik_size = 0.25

                # add loc bind
                loc_bind = primitive.addJoint(
                    parent_recent_loc_bind,
                    self.getName("{}_bind_jnt".format(name)),
                    m=transform.setMatrixScale(self.guide.tra[name], self.scale_vector),
                )
                loc_bind.drawStyle.set(2)

                loc_fk = primitive.addJoint(
                    parent_recent_loc_fk,
                    self.getName("{}_fk_jnt".format(name)),
                    m=transform.setMatrixScale(self.guide.tra[name], self.scale_vector),
                )
                loc_fk.drawStyle.set(2)

                loc_ik = primitive.addJoint(
                    parent_recent_loc_ik,
                    self.getName("{}_ik_jnt".format(name)),
                    m=transform.setMatrixScale(self.guide.tra[name], self.scale_vector),
                )
                loc_ik.drawStyle.set(2)

                pm.makeIdentity(loc_ik, a=1, r=1, s=1)
                pm.makeIdentity(loc_fk, a=1, r=1, s=1)
                pm.makeIdentity(loc_bind, a=1, r=1, s=1)

                ctrl_fk = self.addCtl(
                    parent_fk,
                    name + "_fk",
                    m=transform.setMatrixScale(self.guide.tra[name], self.scale_vector),
                    color=6,
                    iconShape="cube",
                    w=0.25 * self.size,
                    h=0.25 * self.size,
                    d=0.25 * self.size,
                )

                Utility.show_rotate_order(ctrl_fk)
                ctrl_fk.rotateOrder.set(rotate_order)

                mgear.rigbits.addNPO(ctrl_fk)

                recent_fk = ctrl_fk
                recent_loc_ik = loc_ik
                recent_loc_fk = loc_fk
                recent_loc_bind = loc_bind

                ctrl_ik = self.addCtl(
                    self.grp_ik_controls,
                    name + "_ik",
                    m=transform.setMatrixScale(self.guide.tra[name], self.scale_vector),
                    color=13,
                    iconShape=ik_shape,
                    w=ik_size * self.size,
                    h=ik_size * self.size,
                    d=ik_size * self.size,
                )

                # update dictionary
                self.dict_limb["name"].append(name)

                self.dict_limb["loc_main"].append(loc_bind)

                self.dict_limb["loc_fk"].append(loc_fk)
                self.dict_limb["loc_ik"].append(loc_ik)

                self.dict_limb["ctrl_fk"].append(ctrl_fk)
                self.dict_limb["ctrl_ik"].append(ctrl_ik)

                # add joint
                if name == "root":
                    newActiveJnt = "parent_relative_jnt"
                else:
                    newActiveJnt = None  # len(self.jnt_pos) - 1

                if name == "end":
                    self.jnt_pos.append(
                        {
                            "obj": loc_bind,
                            "name": name,
                            "newActiveJnt": newActiveJnt,
                            "gearMulMatrix": False,
                            "vanilla_nodes": True,
                        }
                    )

                # create ribbon joints
                print(self.guide.tra)
                if self.add_up_ribbon and name == "root":
                    create_ribbon_bind_joints(
                        amount=self.amount_up_ribbon, typ="loc_up"
                    )

                if self.add_low_ribbon and name == "low":
                    create_ribbon_bind_joints(
                        amount=self.amount_low_ribbon, typ="loc_low"
                    )

            # create main distance locator
            self.loc_pole_dist = primitive.addLocator(
                self.grp_dist_loc, self.getName("PoleDist_loc")
            )
            self.loc_start_dist = primitive.addLocator(
                self.grp_dist_loc, self.getName("StartDist_loc")
            )
            self.loc_end_dist = primitive.addLocator(
                self.grp_dist_loc, self.getName("EndDist_loc")
            )

        # =====================================================
        # Create Variables
        # =====================================================

        self.dict_ribbon = {"loc_up": [], "loc_low": []}
        self.dict_limb = {
            "name": [],
            "loc_main": [],
            "loc_ik": [],
            "loc_fk": [],
            "ctrl_main": [],
            "ctrl_ik": [],
            "ctrl_fk": [],
        }

        self.mirror_control_scale = False

        self.switch_range = 10

        self.add_up_ribbon = self.settings["ribbon_up_enable"]
        self.add_low_ribbon = self.settings["ribbon_low_enable"]
        self.use_world_pole = self.settings["use_world_pole"]
        self.fk_as_start = self.settings["fk_as_start"]
        self.pole_distance = self.settings["pole_distance"]
        self.world_pole_axis = Misc.convert_single_axis_enum(
            self.settings["world_pole_axis"]
        )

        self.amount_up_ribbon = 5
        self.amount_low_ribbon = 5

        # =====================================================
        # Configuration for Arm,Leg
        # =====================================================

        if self.is_arm and self.side == "L":  # L Arm config
            self.axis_forward = "x"
            self.axis_forward_abs = "x"

            self.axis_pole = "-z"
            self.axis_pole_abs = "z"

            self.axis_piv = "xzy"
            self.inverse_roll = False
            self.inverse_roll_value = True
            self.roll_value = -25

            self.scale_vector = (1, 1, 1)
            self.invert_roll_side_axis = False

            self.invert_middle_twist_value = True

            rotate_order = 0  # "xyz"

        elif self.is_arm and self.side == "R":  # R Arm config
            self.axis_forward = "x"
            self.axis_forward_abs = "x"

            self.axis_pole = "-z"
            self.axis_pole_abs = "z"

            self.axis_piv = "xzy"
            self.inverse_roll = False
            self.inverse_roll_value = True
            self.roll_value = -25

            self.scale_vector = (1, 1, -1)
            self.invert_roll_side_axis = True

            self.invert_middle_twist_value = True

            rotate_order = 0  # "xyz"

        elif not self.is_arm and self.side == "L":  # L Leg config
            self.axis_forward = "-y"
            self.axis_forward_abs = "y"

            self.axis_pole = "z"
            self.axis_pole_abs = "z"

            self.axis_piv = "zxy"
            self.inverse_roll = True
            self.inverse_roll_value = True
            self.roll_value = 25

            self.scale_vector = (1, 1, 1)
            self.invert_roll_side_axis = False

            self.invert_middle_twist_value = True

            rotate_order = 1  # "yzx"

        elif not self.is_arm and self.side == "R":  # R Leg config
            self.axis_forward = "-y"
            self.axis_forward_abs = "y"

            self.axis_pole = "z"
            self.axis_pole_abs = "z"

            self.axis_piv = "zxy"
            self.inverse_roll = False
            self.inverse_roll_value = False
            self.roll_value = -25

            self.scale_vector = (1, 1, -1)
            self.invert_roll_side_axis = True

            self.invert_middle_twist_value = False

            rotate_order = 1  # "yzx"
        else:
            pm.warning("Arm/Leg Component should be set on Left or Right Side.")

        # =====================================================
        # Create Hierarchy Groups
        # =====================================================

        self.grp_local_still = pm.group(em=1, n=self.getName("no_transform_grp"))
        self.grp_local_still.inheritsTransform.set(False)
        self.grp_local_still.setParent(self.root)

        self.grp_transform = pm.group(em=1, n=self.getName("transform_grp"))
        self.grp_transform.setParent(self.root)

        self.grp_dist_loc = pm.group(
            em=1, n=self.getName("loc_distance_grp"), p=self.grp_transform
        )

        self.grp_controls = pm.group(
            em=1, n=self.getName("control_grp"), p=self.grp_transform
        )
        self.grp_ik_controls = pm.group(
            em=1, n=self.getName("ik_ctrl_grp"), p=self.grp_controls
        )
        self.grp_fk_controls = pm.group(
            em=1, n=self.getName("fk_ctrl_grp"), p=self.grp_controls
        )

        self.grp_locator = pm.group(
            em=1, n=self.getName("locator_grp"), p=self.grp_transform
        )
        self.grp_ik_locator = pm.group(
            em=1, n=self.getName("loc_ik_grp"), p=self.grp_locator
        )
        self.grp_fk_locator = pm.group(
            em=1, n=self.getName("loc_fk_grp"), p=self.grp_locator
        )
        self.grp_bind_loc = pm.group(
            em=1, n=self.getName("loc_bind_grp"), p=self.grp_locator
        )

        # =====================================================
        # Run Function
        # =====================================================

        create_locator_bind()
        create_option_control()
        create_fkik_swtich_attribute()

        # =====================================================
        # Create Ik Orient Control
        # =====================================================

        self.ctl_ik_orient = self.addCtl(
            self.dict_limb["ctrl_ik"][2],
            "EndIkOrient",
            m=transform.getTransform(self.dict_limb["ctrl_ik"][2]),
            color=17,
            iconShape="sphere",
            w=0.12 * self.size,
            h=0.12 * self.size,
            d=0.12 * self.size,
        )

        Create.create_freeze_group([self.ctl_ik_orient])
        Utility.lock_attribute(self.ctl_ik_orient, t=1, s=1, v=1)
        self.ctl_ik_orient.rotateOrder.set(rotate_order)

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        def add_ribbon_function():
            def create_ribbon_rig_v2(
                anchor_start,
                anchor_end,
                parent,
                axis_forward,
                axis_pole,
                list_ribbon_joint,
                tag_name="leg",
                enable_auto_twist=True,
                invert_twist_driver=True,
                freeze_anchor_start=False,
                freeze_anchor_end=False,
                invert_twist_anchor=False,
                invert_between_value=False,
                attr_detail_ctrl_vis=None,
                attr_bend_ctrl_vis=None,
            ):

                def create_detail_control():
                    # create all detail control
                    for i in range(division):
                        joint = list_ribbon_joint[i]

                        control = self.addCtl(
                            grp_detail_control,
                            name="{}Dtl{}".format(tag_name, i + 1),
                            m=transform.getTransform(joint),
                            color=14,
                            iconShape="cube",
                            w=0.1 * self.size,
                            h=0.1 * self.size,
                            d=0.1 * self.size,
                        )

                        # update vairables
                        list_sub_control.append(control)

                def create_pin_grp():
                    # create locator pin and align to surface ribbon
                    loc_pin_name = [
                        "{}_Pin_loc".format(joint) for joint in list_ribbon_joint
                    ]

                    for i, name in enumerate(loc_pin_name):
                        grp_pin = pm.createNode("transform", n=name)
                        Transform.transform_to_surface_parameter(
                            nrb_ribbon, grp_pin, u=(1 / (division - 1)) * i, v=0.5
                        )

                        grp_pin.setParent(grp_detail_control)

                        list_flc_offset.append(grp_pin)

                    # Pin locator to ribbon
                    Connection.pin_to_surface(
                        list_pin=list_flc_offset,
                        surface=nrb_ribbon,
                        prevent_double_transform=True,
                        maintain_offset=False,
                    )

                def parent_detail_controls():
                    # create detail controls
                    for i in range(division):
                        control = list_sub_control[i]
                        grp_flc_offset = list_flc_offset[i]

                        pm.parent(control, grp_flc_offset)

                    mgear.rigbits.addNPO(list_sub_control)

                def create_bend_joints():
                    def match_joint():
                        jnt_ref = pm.createNode("joint")
                        jnt_forward = pm.createNode("joint")
                        jnt_pole = pm.createNode("joint")

                        pm.xform(jnt_forward, ws=1, t=(1, 0, 0))
                        pm.xform(jnt_pole, ws=1, t=(0, 0, 1))

                        constraint = pm.aimConstraint(
                            jnt_forward,
                            jnt_ref,
                            aim=Misc.get_axis_double3(axis_forward),
                            u=Misc.get_axis_double3(axis_pole),
                            wut="object",
                            wuo=jnt_pole,
                        )
                        pm.delete(constraint)
                        pm.makeIdentity(jnt_ref, a=1, r=1)

                        joint_orient_axis = jnt_ref.jointOrient.get()

                        pm.delete(jnt_ref, jnt_forward, jnt_pole)

                        return joint_orient_axis

                    def create_cluster():
                        pm.select(nrb_ribbon)
                        lattice_node, lattice_shape, lattice_base = pm.lattice(
                            dv=(3, 2, 2), oc=1
                        )

                        grp_lattice = pm.group(
                            lattice_base,
                            lattice_shape,
                            n=self.getName("lattice_grp"),
                            p=grp_ribbon_still,
                        )

                        for i in range(3):
                            cluster_name = list_cluster[i]

                            pm.select(
                                [
                                    "{}.pt[{}][0:1][0]".format(lattice_shape, i),
                                    "{}.pt[{}][0:1][1]".format(lattice_shape, i),
                                ],
                                r=1,
                            )
                            cluster = pm.cluster(n=cluster_name, rel=False)[1]

                            cluster.visibility.set(False)

                            # grp_frz = freeze_group_classic(cluster)[0]
                            pm.parent(cluster, list_bend_joint[i])

                        lattice_shape.visibility.set(False)
                        lattice_base.visibility.set(False)

                    list_cluster = [
                        self.getName("Start_cluster"),
                        self.getName("Mid_cluster"),
                        self.getName("End_cluster"),
                    ]

                    # create ribbon driver joints
                    list_drive_joint = []
                    list_axis_orient = match_joint()
                    list_bend_joint_name = [
                        "{}_bendStart_jnt".format(tag_name),
                        "{}_bendMid_jnt".format(tag_name),
                        "{}_bendEnd_jnt".format(tag_name),
                    ]
                    # create joint ref

                    for i, name in enumerate(list_bend_joint_name):
                        pm.select(cl=1)
                        joint = pm.joint(n=name, rad=1.5)
                        joint.visibility.set(False)
                        Transform.transform_to_surface_parameter(
                            nrb_ribbon, joint, v=0.5, u=(1 / 2) * i, snap="point"
                        )

                        pm.setAttr(
                            "{}.jointOrient".format(joint),
                            list_axis_orient[0],
                            list_axis_orient[1],
                            list_axis_orient[2],
                            typ="double3",
                        )

                        list_drive_joint.append(joint)
                        list_bend_joint.append(joint)

                    create_cluster()

                    return list_drive_joint

                def create_bend_groups():
                    def create_group_store_aim():
                        # create group store aim
                        Utility.match_parent(grp_store_aim_locator, loc_end)

                        # create group inside ctrl
                        Utility.match_parent(loc_ctrl_corner, grp_store_aim_locator)
                        Utility.match_parent(loc_aim_upRot, grp_store_aim_locator)

                    def match_part():
                        start_drive = loc_start
                        end_drive = loc_ctrl_corner
                        invert = 1
                        parent = grp_bend_control
                        list_driver = list_bend_joint

                        invert_axis = 1 if axis_forward != axis_forward_abs else 1
                        dict_vector_aim = {
                            "x": (1 * invert * invert_axis, 0, 0),
                            "y": (0, 1 * invert * invert_axis, 0),
                            "z": (0, 0, 1 * invert * invert_axis),
                        }
                        dict_vector_up = {
                            "x": (1 * invert * invert_axis, 0, 0),
                            "y": (0, 1 * invert * invert_axis, 0),
                            "z": (0, 0, 1 * invert * invert_axis),
                        }
                        dict_vector_world_up = {
                            "x": (1 * invert, 0, 0),
                            "y": (0, 1 * invert, 0),
                            "z": (0, 0, 1 * invert),
                        }

                        # match all joint driver to group
                        [Utility.match_parent(joint, parent) for joint in list_driver]

                        list_grp_aim = Create.create_freeze_group(list_driver, "grpAim")
                        list_grp_point = Create.create_freeze_group(
                            list_grp_aim, "grpPoint"
                        )

                        # match position
                        Connection.constraint_matrix(
                            [start_drive, list_grp_point[0]], method="point"
                        )
                        Connection.constraint_matrix(
                            [end_drive, list_grp_point[2]], method="point"
                        )
                        pm.pointConstraint(start_drive, end_drive, list_grp_point[1])

                        # aim start and end to mid
                        pm.aimConstraint(
                            list_driver[1],
                            list_grp_aim[0],
                            aim=Misc.get_axis_double3(axis_forward),
                            u=Misc.get_axis_double3(axis_pole),
                            wu=Misc.get_axis_double3(axis_pole),
                            wut="objectrotation",
                            wuo=list_grp_point[0],
                        )
                        pm.aimConstraint(
                            list_driver[1],
                            list_grp_aim[2],
                            aim=[
                                value * -1
                                for value in Misc.get_axis_double3(axis_forward)
                            ],
                            u=Misc.get_axis_double3(axis_pole),
                            wu=Misc.get_axis_double3(axis_pole),
                            wut="objectrotation",
                            wuo=list_grp_point[2],
                        )

                        # aim mid
                        aim_invert = 1
                        pm.aimConstraint(
                            loc_ctrl_corner,
                            list_grp_aim[1],
                            aim=[
                                value * aim_invert
                                for value in Misc.get_axis_double3(axis_forward)
                            ],
                            u=Misc.get_axis_double3(axis_pole),
                            wu=Misc.get_axis_double3(axis_pole),
                            wut="objectrotation",
                            wuo=list_grp_point[1],
                        )

                    create_group_store_aim()

                    # match and constraint bend low and bend up group
                    pm.matchTransform(grp_bend_control, loc_start, pos=1)

                    constraint = pm.aimConstraint(
                        loc_end,
                        grp_bend_control,
                        aim=Misc.get_axis_double3(axis_forward),
                        u=Misc.get_axis_double3(axis_pole_abs),
                        wu=Misc.get_axis_double3(axis_pole_abs),
                        wut="objectrotation",
                        wuo=loc_start,
                    )
                    pm.delete(constraint)

                    Connection.constraint_matrix(
                        [loc_start, grp_bend_control], method="parent", mo=True
                    )

                    match_part()

                def apply_joint_scale():
                    def apply_scale(
                        bend_control, list_detail_control, list_detail_joint
                    ):
                        for i, control in enumerate(list_detail_control):
                            # fix scale control size
                            # grp_scale = freeze_group_classic(control, "grpScl")[0]
                            # pm.connectAttr(grp_get_scale + ".s", grp_scale + ".s")

                            node_pma_add = pm.createNode(
                                "plusMinusAverage",
                                n="{}_bendUpSum_pma".format(tag_name),
                            )
                            pm.connectAttr(
                                "{}.scale".format(control),
                                "{}.input3D[0]".format(node_pma_add),
                            )
                            pm.connectAttr(
                                "{}.scale".format(bend_control),
                                "{}.input3D[1]".format(node_pma_add),
                            )

                            node_pma_minus = pm.createNode(
                                "plusMinusAverage",
                                n="{}_bendUpOffset_pma".format(tag_name),
                            )
                            pm.setAttr("{}.operation".format(node_pma_minus), 2)
                            pm.connectAttr(
                                "{}.output3D".format(node_pma_add),
                                "{}.input3D[0]".format(node_pma_minus),
                            )
                            pm.setAttr(
                                "{}.input3D[1]".format(node_pma_minus),
                                1,
                                1,
                                1,
                                typ="double3",
                            )

                            # connect to ribbon joint
                            pm.connectAttr(
                                "{}.output3D".format(node_pma_minus),
                                "{}.scale".format(list_detail_joint[i]),
                            )

                    apply_scale(
                        list_bend_control[1], list_sub_control, list_ribbon_joint
                    )

                    grp_get_scale = pm.group(
                        em=1,
                        n="{}_scaleSpace_grp".format(tag_name),
                        p=grp_detail_control,
                    )
                    pm.scaleConstraint(grp_ribbon_rig, grp_get_scale)

                    for follicle in list_follicle:
                        grp_scale_output = pm.group(
                            em=1, n="{}_scaleFix_grp".format(follicle)
                        )

                        pm.matchTransform(grp_scale_output, grp_get_scale, rot=1)
                        pm.matchTransform(grp_scale_output, follicle, pos=1)

                        [
                            pm.parent(child, grp_scale_output)
                            for child in pm.listRelatives(
                                follicle, c=1, typ="transform"
                            )
                        ]

                        pm.parent(grp_scale_output, follicle)

                        pm.connectAttr(grp_get_scale + ".s", grp_scale_output + ".s")

                def create_bend_controls():
                    list_control_name = [
                        "{}BendStart".format(tag_name),
                        "{}BendMid".format(tag_name),
                        "{}BendEnd".format(tag_name),
                    ]

                    for i, joint in enumerate(list_bend_joint):
                        # insert controller
                        parent_joint = pm.listRelatives(joint, p=1, typ="transform")
                        if parent_joint:
                            parent_joint = parent_joint[0]
                        else:
                            continue

                        # create controller
                        control = self.addCtl(
                            parent_joint,
                            list_control_name[i],
                            m=transform.getTransform(joint),
                            color=13,
                            iconShape="cube",
                            w=0.18 * self.size,
                            h=0.18 * self.size,
                            d=0.18 * self.size,
                        )

                        # lock y axis
                        pm.setAttr(control + ".sy", l=1, k=0)

                        pm.parent(joint, control)

                        if i != 1 and i != 4:
                            pm.setAttr(control + ".v", 0)

                        list_bend_control.append(control)

                def apply_joint_constraint():
                    for i in range(division):
                        control = list_sub_control[i]
                        joint = list_ribbon_joint[i]

                        Connection.constraint_matrix(
                            [control, joint], method="parent", mo=False
                        )
                        Connection.constraint_matrix(
                            [control, joint], method="scale", mo=True
                        )

                def finalize():
                    try:
                        if not self.WIP:
                            for control in list_bend_control:
                                pm.setAttr(
                                    control + ".s{}".format(axis_forward_abs), l=1, k=0
                                )
                                attribute.lockAttribute(control, ["v"])

                            for control in list_sub_control:
                                attribute.lockAttribute(control, ["v"])

                            attribute.lockAttribute(grp_store_aim_locator, ["v"])

                            pm.setAttr(nrb_ribbon + ".v", 0)

                            # attribute.lockAttribute(grp_ribbon_rig)
                    except:
                        pass

                def quaternion_twist():
                    def create_invert_twist_locator(object):
                        loc_invert_result = pm.spaceLocator(
                            n=self.getName("{}_invertTwist_loc".format(tag_name))
                        )[0]
                        grp_invert_result = pm.group(
                            loc_invert_result, n=self.getName("{}_invertTwist_grp")
                        )
                        pm.setAttr(grp_invert_result + ".inheritsTransform", 0)

                        pm.parent(grp_invert_result, parent)

                        # constraint position
                        node_decomp_matrix = pm.createNode(
                            "decomposeMatrix",
                            n=self.getName("{}_decompPos_dcm".format(tag_name)),
                        )
                        pm.connectAttr(
                            object + ".worldMatrix[0]",
                            node_decomp_matrix + ".inputMatrix",
                        )
                        pm.connectAttr(
                            object + ".rotateOrder",
                            node_decomp_matrix + ".inputRotateOrder",
                        )
                        pm.connectAttr(
                            node_decomp_matrix + ".outputTranslate",
                            grp_invert_result + ".translate",
                        )

                        # connect invert rotate
                        node_euler_to_quat = pm.createNode(
                            "eulerToQuat",
                            n=self.getName("{}_eulerToQuat_etq".format(tag_name)),
                        )
                        pm.connectAttr(
                            object + ".rotate", node_euler_to_quat + ".inputRotate"
                        )
                        pm.connectAttr(
                            object + ".rotateOrder",
                            node_euler_to_quat + ".inputRotateOrder",
                        )

                        node_quat_invert = pm.createNode(
                            "quatInvert",
                            n=self.getName("{}_quatInvert_qi".format(tag_name)),
                        )
                        pm.connectAttr(
                            "{}.outputQuat{}".format(
                                node_euler_to_quat, axis_forward_abs.upper()
                            ),
                            "{}.inputQuat{}".format(
                                node_quat_invert, axis_forward_abs.upper()
                            ),
                        )
                        pm.connectAttr(
                            "{}.outputQuatW".format(node_euler_to_quat),
                            "{}.inputQuatW".format(node_quat_invert),
                        )

                        node_quat_prod = pm.createNode(
                            "quatProd",
                            n=self.getName("{}_quatProd_qp".format(tag_name)),
                        )
                        pm.connectAttr(
                            node_quat_invert + ".outputQuat",
                            node_quat_prod + ".input1Quat",
                        )
                        pm.connectAttr(
                            node_euler_to_quat + ".outputQuat",
                            node_quat_prod + ".input2Quat",
                        )

                        node_quat_to_euler = pm.createNode("quatToEuler")
                        pm.connectAttr(
                            node_quat_prod + ".outputQuat",
                            node_quat_to_euler + ".inputQuat",
                        )
                        pm.connectAttr(
                            object + ".rotateOrder",
                            node_quat_to_euler + ".inputRotateOrder",
                        )

                        # connect output to invert result
                        pm.connectAttr(
                            node_quat_to_euler + ".outputRotate",
                            loc_invert_result + ".rotate",
                        )
                        pm.connectAttr(
                            object + ".rotateOrder", loc_invert_result + ".rotateOrder"
                        )

                        return loc_invert_result

                    def create_euler_output(object):
                        node_offset_euler = pm.createNode(
                            "plusMinusAverage", n=self.getName("{}_offsetEuler_pma")
                        )
                        pm.connectAttr(
                            "{}.r".format(object),
                            "{}.input3D[0]".format(node_offset_euler),
                        )
                        pm.setAttr(
                            "{}.input3D[1]".format(node_offset_euler),
                            pm.getAttr("{}.r".format(object)),
                            typ="double3",
                        )
                        pm.setAttr("{}.operation".format(node_offset_euler), 2)

                        node_euler_to_quat = pm.createNode(
                            "eulerToQuat",
                            n=self.getName("{}_eulerToQuat_etq".format(tag_name)),
                        )
                        pm.connectAttr(
                            "{}.output3D".format(node_offset_euler),
                            node_euler_to_quat + ".inputRotate",
                        )
                        pm.connectAttr(
                            object + ".rotateOrder",
                            node_euler_to_quat + ".inputRotateOrder",
                        )

                        node_quat_to_euler = pm.createNode(
                            "quatToEuler",
                            n=self.getName("{}_quatToEuler_qte".format(tag_name)),
                        )
                        pm.connectAttr(
                            "{}.outputQuat{}".format(
                                node_euler_to_quat, axis_forward_abs.upper()
                            ),
                            node_quat_to_euler
                            + ".inputQuat{}".format(axis_forward_abs.upper()),
                        )
                        pm.connectAttr(
                            "{}.outputQuatW".format(node_euler_to_quat),
                            node_quat_to_euler + ".inputQuatW",
                        )
                        pm.connectAttr(
                            object + ".rotateOrder",
                            node_quat_to_euler + ".inputRotateOrder",
                        )

                        node_offset = pm.createNode("addDoubleLinear")
                        pm.connectAttr(
                            node_quat_to_euler
                            + ".outputRotate{}".format(axis_forward_abs.upper()),
                            node_offset + ".input1",
                        )
                        pm.setAttr(
                            node_offset + ".input2",
                            pm.getAttr(
                                "{}.outputRotate{}".format(
                                    node_quat_to_euler, axis_forward_abs.upper()
                                )
                            )
                            * -1,
                        )

                        return node_offset + ".output"

                    def connect_euler_to_between(invert_value):
                        node_bw = pm.createNode("blendWeighted")
                        pm.connectAttr(attr_start_euler, node_bw + ".input[0]")
                        pm.connectAttr(attr_end_euler, node_bw + ".input[1]")

                        node_division = pm.createNode("multDoubleLinear")
                        pm.connectAttr(node_bw + ".output", node_division + ".input1")

                        if invert_value:
                            pm.setAttr(node_division + ".input2", -0.5)
                        else:
                            pm.setAttr(node_division + ".input2", 0.5)

                        # connect to output
                        grp_frz1 = mgear.rigbits.addNPO(list_bend_control[1])[0]
                        grp_frz2 = mgear.rigbits.addNPO(list_bend_control[1])[0]

                        pm.connectAttr(
                            node_division + ".output",
                            "{}.r{}".format(grp_frz2, axis_forward_abs),
                        )

                    def connect_euler_to_tip(attr_euler, object, invert_value=False):
                        grp_frz1 = mgear.rigbits.addNPO([object])[0]
                        grp_frz2 = mgear.rigbits.addNPO([object])[0]

                        if invert_value:
                            node_mdl_invert = pm.createNode(
                                "multDoubleLinear",
                                n=self.getName("{}_invertFreeze_mdl".format(tag_name)),
                            )
                            pm.connectAttr(
                                attr_euler, "{}.input1".format(node_mdl_invert)
                            )
                            pm.setAttr("{}.input2".format(node_mdl_invert), -1)
                            pm.connectAttr(
                                "{}.output".format(node_mdl_invert),
                                grp_frz2 + ".r{}".format(axis_forward_abs),
                            )
                        else:
                            pm.connectAttr(
                                attr_euler, grp_frz2 + ".r{}".format(axis_forward_abs)
                            )

                    if not enable_auto_twist:
                        return

                    # get euler start and end value
                    if invert_twist_anchor:
                        attr_start_euler = create_euler_output(anchor_start)
                        attr_end_euler = create_euler_output(anchor_end)
                    else:
                        attr_start_euler = create_euler_output(anchor_end)
                        attr_end_euler = create_euler_output(anchor_start)

                    connect_euler_to_between(invert_value=invert_between_value)

                    # connect output to bend control
                    if invert_twist_driver:
                        connect_euler_to_tip(
                            attr_start_euler,
                            list_bend_control[2],
                            invert_value=freeze_anchor_start,
                        )
                        connect_euler_to_tip(
                            attr_end_euler,
                            list_bend_control[0],
                            invert_value=freeze_anchor_end,
                        )
                    else:
                        connect_euler_to_tip(
                            attr_start_euler,
                            list_bend_control[0],
                            invert_value=freeze_anchor_start,
                        )
                        connect_euler_to_tip(
                            attr_end_euler,
                            list_bend_control[2],
                            invert_value=freeze_anchor_end,
                        )

                def connect_visibility():
                    # create attributes
                    # attribute variables
                    attr_detail_vis_control = (
                        list_bend_control[1] + ".detailControlVisibility"
                    )
                    attr_bend_vis_control = (
                        list_bend_control[1] + ".bendControlVisibility"
                    )
                    attr_auto_twist_enable = list_bend_control[1] + ".autoTwistEnable"

                    pm.addAttr(
                        attr_bend_vis_control.split(".")[0],
                        ln=attr_bend_vis_control.split(".")[1],
                        at="enum",
                        en="Hide:Show",
                        k=1,
                        dv=1,
                    )
                    pm.addAttr(
                        attr_detail_vis_control.split(".")[0],
                        ln=attr_detail_vis_control.split(".")[1],
                        at="enum",
                        en="Hide:Show",
                        k=1,
                        dv=1,
                    )

                    pm.connectAttr(attr_bend_vis_control, grp_bend_control + ".v")
                    pm.connectAttr(attr_detail_vis_control, grp_detail_control + ".v")

                    if attr_detail_ctrl_vis:
                        pm.connectAttr(attr_detail_ctrl_vis, attr_detail_vis_control)
                    if attr_bend_ctrl_vis:
                        pm.connectAttr(attr_bend_ctrl_vis, attr_bend_vis_control)

                    pm.setAttr(attr_detail_vis_control, k=0, l=1)
                    pm.setAttr(attr_bend_vis_control, k=0, l=1)

                # error handle
                if not list_ribbon_joint:
                    raise Exception("Input Ribbon Joint Up and Low must Match Count")

                # create hierarchy
                grp_ribbon_rig = pm.group(
                    em=1, n=self.getName("{}BendRig_grp".format(tag_name))
                )
                pm.parent(grp_ribbon_rig, parent)

                grp_ribbon_anim = pm.group(
                    em=1,
                    n=self.getName("{}BendTransform_grp".format(tag_name)),
                    p=grp_ribbon_rig,
                )
                grp_ribbon_still = pm.group(
                    em=1,
                    n=self.getName("{}BendStill_grp".format(tag_name)),
                    p=grp_ribbon_rig,
                )

                grp_bend_control = pm.group(
                    em=1,
                    n=self.getName("{}BendCtl_grp".format(tag_name)),
                    p=grp_ribbon_anim,
                )
                grp_detail_control = pm.group(
                    em=1,
                    n=self.getName("{}DtlCtl_grp".format(tag_name)),
                    p=grp_ribbon_anim,
                )

                # grp_detail_control.inheritsTransform.set(False)
                grp_ribbon_still.inheritsTransform.set(False)

                # group variables
                division = len(list_ribbon_joint)

                grp_store_aim_locator = pm.group(
                    n=self.getName("{}_StoreAim_grp".format(tag_name)), em=1
                )

                loc_aim_upRot = pm.spaceLocator(
                    n=self.getName("{}_AimUpRot_loc".format(tag_name))
                )
                loc_ctrl_corner = pm.spaceLocator(
                    n=self.getName("{}_CornerRbn_loc".format(tag_name))
                )
                loc_start = pm.spaceLocator(
                    n=self.getName("{}_startPin_loc".format(tag_name))
                )
                loc_end = pm.spaceLocator(
                    n=self.getName("{}_endPin_loc".format(tag_name))
                )

                loc_aim_upRot.visibility.set(False)
                loc_ctrl_corner.visibility.set(False)

                loc_start.visibility.set(False)
                loc_end.visibility.set(False)

                pm.parent(loc_start, loc_end, grp_ribbon_anim)

                axis_forward_abs = Misc.del_neg(axis_forward)
                axis_pole_abs = Misc.del_neg(axis_pole)

                # create ribbon plane  reference scale from limb joints
                width_up = Transform.get_distance_two([anchor_start, anchor_end])
                nrb_ribbon = pm.nurbsPlane(
                    w=width_up,
                    lr=0.05,
                    u=4,
                    v=1,
                    d=3,
                    ax=(0, 0, 1),
                    ch=0,
                    n=self.getName("{}_Ribbon_nrb".format(tag_name)),
                )[0]
                pm.parent(nrb_ribbon, grp_ribbon_still)

                # variables
                list_sub_locator = []
                list_sub_control = []

                list_flc_offset = []
                list_follicle = []

                list_bend_control = []
                list_bend_joint = []

                Connection.constraint_matrix(
                    [anchor_start, loc_start], method="parent", mo=False
                )
                Connection.constraint_matrix(
                    [anchor_end, loc_end], method="parent", mo=False
                )

                # create sub control
                create_detail_control()
                create_bend_joints()
                create_pin_grp()

                # bind skin ribbon plane
                create_bend_groups()

                parent_detail_controls()

                create_bend_controls()

                quaternion_twist()

                # apply output to ribbon joints
                apply_joint_constraint()
                connect_visibility()

                #############################
                ## Connect detail scale #####
                #############################
                print(list_sub_control)
                print(list_bend_control)
                for i, ctrl_detail in enumerate(list_sub_control):
                    if i == 0 or i == len(list_sub_control) - 1:
                        continue
                    else:
                        list_bend_control[1].scaleX >> ctrl_detail.getParent().scaleX
                        list_bend_control[1].scaleZ >> ctrl_detail.getParent().scaleZ

                # lock and hide control
                finalize()

                return grp_ribbon_rig

            if not self.add_up_ribbon and not self.add_low_ribbon:
                return
            else:
                # create required variables
                attr_bend_vis = "{}.bendCtrlVis".format(self.ctrl_option)
                attr_dtl_vis = "{}.detailCtrlVis".format(self.ctrl_option)

                pm.addAttr(
                    attr_bend_vis.split(".")[0],
                    k=1,
                    en="Hide:Show",
                    ln=attr_bend_vis.split(".")[1],
                    at="enum",
                )
                pm.addAttr(
                    attr_dtl_vis.split(".")[0],
                    k=1,
                    en="Hide:Show",
                    ln=attr_dtl_vis.split(".")[1],
                    at="enum",
                )

                pm.setAttr(attr_bend_vis, 1)
                pm.setAttr(attr_dtl_vis, 0)

                # create knee control
                self.ctrl_knee_ribbon = self.addCtl(
                    self.grp_controls,
                    "BendMover",
                    m=transform.setMatrixScale(self.guide.tra["low"], (1, 1, 1)),
                    color=14,
                    iconShape="cube",
                    w=0.1 * self.size,
                    h=0.1 * self.size,
                    d=0.1 * self.size,
                )
                mgear.rigbits.addNPO([self.ctrl_knee_ribbon])
                Connection.constraint_matrix(
                    [
                        self.dict_limb["loc_main"][1],
                        pm.listRelatives(self.ctrl_knee_ribbon, p=1)[0],
                    ],
                    method="parent",
                )

                Utility.lock_attribute(self.ctrl_knee_ribbon, r=1, s=1, v=1)

            if self.add_up_ribbon:
                # create ribbon up
                grp_ribbon = create_ribbon_rig_v2(
                    anchor_start=self.dict_limb["loc_main"][0],
                    anchor_end=self.ctrl_knee_ribbon,
                    parent=self.grp_transform,
                    axis_forward=self.axis_forward,
                    axis_pole=self.axis_pole,
                    list_ribbon_joint=self.dict_ribbon["loc_up"],
                    tag_name="Up",
                    enable_auto_twist=True,
                    invert_twist_driver=True,
                    freeze_anchor_end=True,
                    attr_bend_ctrl_vis=attr_bend_vis,
                    attr_detail_ctrl_vis=attr_dtl_vis,
                    invert_between_value=True,
                )

            if self.add_low_ribbon:
                # create ribbon low
                grp_ribbon = create_ribbon_rig_v2(
                    anchor_start=self.ctrl_knee_ribbon,
                    anchor_end=self.dict_limb["loc_main"][2],
                    parent=self.grp_transform,
                    axis_forward=self.axis_forward,
                    axis_pole=self.axis_pole,
                    list_ribbon_joint=self.dict_ribbon["loc_low"],
                    enable_auto_twist=True,
                    tag_name="Low",
                    attr_bend_ctrl_vis=attr_bend_vis,
                    attr_detail_ctrl_vis=attr_dtl_vis,
                    invert_twist_driver=True,
                    # invert_twist_anchor=True
                )

        def make_finalize():
            if self.fk_as_start:
                pm.setAttr(self.ctrl_option + ".FkIk", 0)
            else:
                pm.setAttr(self.ctrl_option + ".FkIk", self.switch_range)

            # self.dict_limb["ctrl_ik"][2].autoStretch.set(0)

            try:
                if self.WIP:
                    return
            except:
                pass

            Misc.finalize_visibility(self.grp_bind_loc)

            # lock fk attr
            for control in self.dict_limb["ctrl_fk"]:
                Utility.lock_attribute(control, s=1, v=1)

            # lock ik attr
            Utility.lock_attribute(self.dict_limb["ctrl_ik"][0], s=1, r=1, v=1)
            Utility.lock_attribute(self.dict_limb["ctrl_ik"][1], s=1, r=1, v=1)
            Utility.lock_attribute(self.dict_limb["ctrl_ik"][2], s=1, v=1)

            # # lock and hide for arm
            # if self.is_arm :
            #     attrs = [
            #         "IkPivot",
            #         "roll",
            #         "sideRoll",
            #         "middleRoll",
            #         "baseTwist",
            #         "tipTwist",
            #         "rollBallEnd"
            #     ]
            # else:
            #     attrs = [
            #         "rollBallEnd"
            #     ]
            #
            # control = self.dict_limb["ctrl_ik"][2]
            #
            # for attr in attrs:
            #     mc.setAttr(f"{control}.{attr}", lock=True, keyable=False, channelBox=False)

            # hide locator
            self.loc_pole_dist.visibility.set(False)
            self.loc_start_dist.visibility.set(False)
            self.loc_end_dist.visibility.set(False)

        def create_fk_function():
            """
            create fk control by matching the limb joints and parent in fk hierarchy form
            """

            for i in range(len(self.dict_limb["loc_fk"])):
                ctrl_fk = self.dict_limb["ctrl_fk"][i]
                loc_fk = self.dict_limb["loc_fk"][i]

                pm.parentConstraint(ctrl_fk, loc_fk, mo=1)
                ctrl_fk.rotateOrder >> loc_fk.rotateOrder

            # add stretch function
            invert = 1 if self.side == "R" else -1

            # add stretch attribute
            [
                pm.addAttr(control, ln="stretch", at="float", k=1)
                for control in self.dict_limb["ctrl_fk"][0:2]
            ]

            for i, control in enumerate(self.dict_limb["ctrl_fk"]):
                if i == 0:
                    continue
                elif i >= 3:
                    break

                before_control = self.dict_limb["ctrl_fk"][i - 1]
                grp_stretch = pm.group(em=1, n="grp_stretch")
                pm.matchTransform(grp_stretch, before_control, rot=1)
                pm.matchTransform(grp_stretch, control, pos=1)

                grp_stretch.setParent(control.getParent())
                control.setParent(grp_stretch)

                mgear.rigbits.addNPO(grp_stretch)
                mgear.rigbits.addNPO(control)

                node_uc = pm.createNode("unitConversion")
                pm.connectAttr(
                    "{}.stretch".format(before_control), "{}.input".format(node_uc)
                )
                pm.setAttr(node_uc + ".conversionFactor", -1 * invert)

                pm.connectAttr(
                    "{}.output".format(node_uc),
                    "{}.t{}".format(grp_stretch, self.axis_forward_abs),
                )

        def create_ik_function():
            def create_control():
                ctrl_start, ctrl_pole, ctrl_end = self.dict_limb["ctrl_ik"][0:3]

                # create pole locator
                # pm.parent(self.loc_pole_dist,self.grp_ik_controls)

                # create world ik parent
                grp_limb_ik_world_parent = pm.group(
                    em=1, n=self.getName("IkWorldParent_grp")
                )
                pm.setAttr("{}.inheritsTransform".format(grp_limb_ik_world_parent), 0)
                pm.connectAttr(
                    "{}.worldMatrix[0]".format(self.root),
                    "{}.offsetParentMatrix".format(grp_limb_ik_world_parent),
                )
                pm.parent(grp_limb_ik_world_parent, self.grp_ik_controls)

                # create ik control
                for i, ctrl_ik in enumerate(self.dict_limb["ctrl_ik"]):
                    ctrl_fk = self.dict_limb["ctrl_fk"][i]
                    loc_ik = self.dict_limb["loc_ik"][i]
                    loc_main = self.dict_limb["loc_main"][i]

                    if i == 1:
                        shape = "sphere"
                        size = 0.5
                    else:
                        shape = "cube"
                        size = 1.4

                    pm.connectAttr(
                        "{}.rotateOrder".format(ctrl_fk),
                        "{}.rotateOrder".format(ctrl_ik),
                        f=1,
                    )
                    pm.connectAttr(
                        "{}.rotateOrder".format(ctrl_ik),
                        "{}.rotateOrder".format(loc_ik),
                        f=1,
                    )

                    # parent to world
                    if i == 1 or i == 2:
                        pm.parent(ctrl_ik, grp_limb_ik_world_parent)

                    if i != 1:
                        grp_frz = mgear.rigbits.addNPO([ctrl_ik])

                        # if self.mirror_control_scale:
                        # pm.setAttr(grp_frz + ".s", -1, -1, -1, typ="double3")

                # align pole vector control ---------------------------
                # create poly plane
                list_point_create = [
                    pm.xform(obj, q=1, ws=1, t=1) for obj in self.dict_limb["loc_ik"]
                ]

                # convert unit
                unit = pm.currentUnit(q=1, l=1)
                if unit == "m":
                    for i, list_point in enumerate(list_point_create):
                        for a, point in enumerate(list_point):
                            list_point_create[i][a] = point * 100

                plane_poly = pm.polyCreateFacet(p=list_point_create)[0]
                loc_world = pm.spaceLocator()
                loc_scale_plane = pm.spaceLocator()

                # match target to pole position
                scale_value = self.pole_distance * self.size

                # snap position
                snap_position = pm.xform("{}.vtx[1]".format(plane_poly), q=1, t=1, ws=1)
                pm.xform(self.loc_pole_dist, ws=1, t=snap_position)

                # match loc scale plane
                pm.xform(loc_scale_plane, ws=1, t=snap_position)
                pm.parent(plane_poly, loc_scale_plane)

                if self.use_world_pole:
                    world_direction_pole_abs = Misc.del_neg(self.world_pole_axis)
                    scale_value = (
                        scale_value * -1
                        if self.world_pole_axis != world_direction_pole_abs
                        else scale_value
                    )
                    dict_vector = {
                        "x": (scale_value, 0, 0),
                        "y": (0, scale_value, 0),
                        "z": (0, 0, scale_value),
                    }

                    pm.xform(
                        self.loc_pole_dist,
                        ws=1,
                        t=dict_vector[world_direction_pole_abs],
                        r=1,
                    )

                elif not self.use_world_pole:
                    pm.xform(plane_poly, cp=1)

                    pm.setAttr(
                        "{}.scale".format(plane_poly),
                        scale_value,
                        scale_value,
                        scale_value,
                        typ="double3",
                    )
                    snap_position = pm.xform(
                        "{}.vtx[1]".format(plane_poly), q=1, t=1, ws=1
                    )
                    pm.xform(self.loc_pole_dist, ws=1, t=snap_position)

                    constraint = pm.normalConstraint(plane_poly, self.loc_pole_dist)
                    pm.delete(constraint)

                    pm.matchTransform(self.loc_pole_dist, loc_world, rot=1)

                # clean temp
                pm.delete(loc_world)
                pm.delete(loc_scale_plane)

                # create pole controller ----------------------------
                pm.matchTransform(self.dict_limb["ctrl_ik"][1], self.loc_pole_dist)

                Connection.constraint_matrix(
                    [self.dict_limb["ctrl_ik"][1], self.loc_pole_dist], method="point"
                )

                grp_pole_offset = mgear.rigbits.addNPO([ctrl_pole])[0]

                # create pole ik handle
                self.ik_handle_limb = pm.ikHandle(
                    n=self.getName("ik_ikHandle"),
                    sol="ikRPsolver",
                    sj=self.dict_limb["loc_ik"][0],
                    ee=self.dict_limb["loc_ik"][2],
                )[0]
                pm.parent(self.ik_handle_limb, self.dict_limb["ctrl_ik"][2])

                pm.setAttr("{}.v".format(self.ik_handle_limb), False)

                pm.poleVectorConstraint(self.loc_pole_dist, self.ik_handle_limb)

                pm.addAttr(
                    attr_ik_twist.split(".")[0],
                    ln=attr_ik_twist.split(".")[1],
                    dv=0,
                    at="float",
                    k=1,
                )
                pm.connectAttr(attr_ik_twist, self.ik_handle_limb + ".twist")

                # constraint start control -------------------------
                Connection.constraint_matrix(
                    [ctrl_start, self.dict_limb["loc_ik"][0]], method="point"
                )

                # finalize ----------------
                Create.create_line_annotate(
                    [
                        self.dict_limb["loc_ik"][1],
                        ctrl_pole,
                        self.dict_limb["loc_ik"][2],
                    ],
                    name=self.name,
                    parent=ctrl_pole,
                )

                # Constraint end control
                constraint = pm.orientConstraint(
                    self.dict_limb["loc_ik"][1],
                    ctrl_end,
                    self.ctl_ik_orient.getParent(),
                )
                pm.addAttr(ctrl_end, ln="autoFkRotate", k=1, min=0, max=10)

                node_reverse = pm.createNode("reverse")

                Connection.connect_conversion_unit(
                    input=ctrl_end.autoFkRotate, factor=0.1, output=node_reverse.inputX
                )

                node_reverse.outputX >> constraint.w1
                node_reverse.inputX >> constraint.w0

                # Connection.constraint_matrix(
                #     [self.ctl_ik_orient, self.dict_limb["loc_ik"][2]],
                #     method="orient",
                #     mo=1,
                # )

                pm.orientConstraint(
                    self.ctl_ik_orient, self.dict_limb["loc_ik"][2], mo=True
                )

            def create_stretchy_v2():
                # create distance locator
                Connection.constraint_matrix(
                    [self.dict_limb["ctrl_ik"][0], self.loc_start_dist], method="point"
                )
                Connection.constraint_matrix(
                    [self.dict_limb["ctrl_ik"][2], self.loc_end_dist], method="point"
                )

                pm.addAttr(
                    self.dict_limb["ctrl_ik"][2],
                    k=1,
                    ln="autoStretch",
                    at="float",
                    min=0,
                    max=1,
                    dv=0,
                )
                pm.addAttr(
                    self.dict_limb["ctrl_ik"][2], k=1, ln="upperStretch", at="float"
                )
                pm.addAttr(
                    self.dict_limb["ctrl_ik"][2], k=1, ln="lowerStretch", at="float"
                )
                pm.addAttr(
                    self.dict_limb["ctrl_ik"][1],
                    k=1,
                    ln="pinIk",
                    at="float",
                    min=0,
                    max=1,
                )

                self.stretch_with_fixed_angle = False

                if self.stretch_with_fixed_angle:
                    value_full_length = Transform.get_distance_two(
                        [self.loc_start_dist, self.loc_end_dist]
                    )
                else:
                    value_full_length = Transform.get_distance_two(
                        [self.dict_limb["loc_ik"][0], self.dict_limb["loc_ik"][1]]
                    ) + Transform.get_distance_two(
                        [self.dict_limb["loc_ik"][1], self.dict_limb["loc_ik"][2]]
                    )

                # Stretch ----------------------------------
                # connection distance
                node_distance = pm.createNode(
                    "distanceBetween", n="{}_autoStretchLength_dist".format(self.name)
                )
                pm.connectAttr(
                    "{}.translate".format(self.loc_start_dist),
                    "{}.point1".format(node_distance),
                )
                pm.connectAttr(
                    "{}.translate".format(self.loc_end_dist),
                    "{}.point2".format(node_distance),
                )

                # connection normalize
                node_md_normalize = pm.createNode(
                    "multiplyDivide", n="{}_stretchLengthNormalize_md".format(self.name)
                )
                pm.connectAttr(
                    "{}.distance".format(node_distance),
                    "{}.input1X".format(node_md_normalize),
                )
                factor = 1 / value_full_length
                pm.setAttr("{}.input2X".format(node_md_normalize), factor)

                # condition
                node_condition = pm.createNode(
                    "condition", n="{}_autoStretch_cond".format(self.name)
                )
                pm.setAttr("{}.operation".format(node_condition), 2)
                pm.connectAttr(
                    "{}.distance".format(node_distance),
                    "{}.firstTerm".format(node_condition),
                )
                pm.setAttr("{}.secondTerm".format(node_condition), value_full_length)
                pm.connectAttr(
                    "{}.outputX".format(node_md_normalize),
                    "{}.colorIfTrueR".format(node_condition),
                )
                pm.connectAttr(
                    "{}.outputX".format(node_md_normalize),
                    "{}.colorIfTrueG".format(node_condition),
                )
                pm.connectAttr(
                    "{}.outputX".format(node_md_normalize),
                    "{}.colorIfTrueB".format(node_condition),
                )

                # mdv stretch connection
                node_md_stretch = pm.createNode(
                    "multiplyDivide", n="{}_stretch_mdv".format(self.name)
                )
                pm.connectAttr(
                    "{}.outColor".format(node_condition),
                    "{}.input1".format(node_md_stretch),
                )
                pm.setAttr(
                    "{}.input2X".format(node_md_stretch),
                    pm.getAttr(
                        "{}.t{}".format(
                            self.dict_limb["loc_ik"][1], self.axis_forward_abs
                        )
                    ),
                )  # forearm translate
                pm.setAttr(
                    "{}.input2Y".format(node_md_stretch),
                    pm.getAttr(
                        "{}.t{}".format(
                            self.dict_limb["loc_ik"][2], self.axis_forward_abs
                        )
                    ),
                )  # wrist translate

                # blend color connection
                node_bc_stretch = pm.createNode(
                    "blendColors", n="{}_stretchBlend_bc".format(self.name)
                )
                pm.connectAttr(
                    "{}.outputX".format(node_md_stretch),
                    "{}.color1R".format(node_bc_stretch),
                )
                pm.connectAttr(
                    "{}.outputY".format(node_md_stretch),
                    "{}.color1G".format(node_bc_stretch),
                )

                output_node_md_stretch = pm.getAttr("{}.output".format(node_md_stretch))
                pm.setAttr(
                    "{}.color2".format(node_bc_stretch),
                    output_node_md_stretch[0],
                    output_node_md_stretch[1],
                    output_node_md_stretch[2],
                    typ="double3",
                )
                pm.connectAttr(
                    "{}.autoStretch".format(self.dict_limb["ctrl_ik"][2]),
                    "{}.blender".format(node_bc_stretch),
                )

                # stretch conversion
                node_md_conversion = pm.createNode(
                    "multiplyDivide", n="{}_stretchConversion_mdv".format(self.name)
                )
                pm.connectAttr(
                    "{}.upperStretch".format(self.dict_limb["ctrl_ik"][2]),
                    "{}.input1X".format(node_md_conversion),
                )
                pm.connectAttr(
                    "{}.lowerStretch".format(self.dict_limb["ctrl_ik"][2]),
                    "{}.input1Y".format(node_md_conversion),
                )
                conversion_factor = (
                    -1 if self.axis_forward_abs != self.axis_forward else 1
                )
                pm.setAttr(
                    "{}.input2".format(node_md_conversion),
                    conversion_factor,
                    conversion_factor,
                    conversion_factor,
                    typ="double3",
                )

                # stretch adjust
                node_pma_stretch = pm.createNode(
                    "plusMinusAverage", n="{}_stretchAdd_pma".format(self.name)
                )
                pm.connectAttr(
                    "{}.output".format(node_bc_stretch),
                    "{}.input3D[0]".format(node_pma_stretch),
                )
                pm.connectAttr(
                    "{}.output".format(node_md_conversion),
                    "{}.input3D[1]".format(node_pma_stretch),
                )

                # blend color lock pole
                node_bc_lock = pm.createNode(
                    "blendColors", n="{}_stretchBlend_bc".format(self.name)
                )
                pm.connectAttr(
                    "{}.output3Dx".format(node_pma_stretch),
                    "{}.color2R".format(node_bc_lock),
                )
                pm.connectAttr(
                    "{}.output3Dy".format(node_pma_stretch),
                    "{}.color2G".format(node_bc_lock),
                )
                pm.connectAttr(
                    "{}.pinIk".format(self.dict_limb["ctrl_ik"][1]),
                    "{}.blender".format(node_bc_lock),
                )

                # Pole Lock ----------------------------------
                node_dist_up = pm.createNode(
                    "distanceBetween", n="{}_lockStart_dist".format(self.name)
                )
                pm.connectAttr(
                    "{}.translate".format(self.loc_start_dist),
                    "{}.point1".format(node_dist_up),
                )
                pm.connectAttr(
                    "{}.translate".format(self.loc_pole_dist),
                    "{}.point2".format(node_dist_up),
                )

                node_dist_low = pm.createNode(
                    "distanceBetween", n="{}_lockEnd_dist".format(self.name)
                )
                pm.connectAttr(
                    "{}.translate".format(self.loc_end_dist),
                    "{}.point1".format(node_dist_low),
                )
                pm.connectAttr(
                    "{}.translate".format(self.loc_pole_dist),
                    "{}.point2".format(node_dist_low),
                )

                node_md_lock = pm.createNode(
                    "multiplyDivide", n="{}_lockConversion_mdv".format(self.name)
                )
                pm.connectAttr(
                    "{}.distance".format(node_dist_up),
                    "{}.input1X".format(node_md_lock),
                )
                pm.connectAttr(
                    "{}.distance".format(node_dist_low),
                    "{}.input1Y".format(node_md_lock),
                )
                pm.connectAttr(
                    "{}.outputX".format(node_md_lock), "{}.color1R".format(node_bc_lock)
                )
                pm.connectAttr(
                    "{}.outputY".format(node_md_lock), "{}.color1G".format(node_bc_lock)
                )
                conversion_value = (
                    -1 if self.axis_forward != self.axis_forward_abs else 1
                )
                pm.setAttr("{}.input2X".format(node_md_lock), conversion_value)
                pm.setAttr("{}.input2Y".format(node_md_lock), conversion_value)

                # Connect to output ------------------------------
                pm.connectAttr(
                    "{}.outputR".format(node_bc_lock),
                    "{}.t{}".format(self.dict_limb["loc_ik"][1], self.axis_forward_abs),
                )
                pm.connectAttr(
                    "{}.outputG".format(node_bc_lock),
                    "{}.t{}".format(self.dict_limb["loc_ik"][2], self.axis_forward_abs),
                )

            # create attributes
            attr_ik_twist = self.dict_limb["ctrl_ik"][2] + ".twistIk"

            # ik function con
            create_control()
            create_stretchy_v2()

        def connect_switch_joint():
            def connect_switch_joints():
                # create switch systems , use blendColor Node
                node_reverse = pm.createNode(
                    "reverse", n=self.getName("switch_reverse")
                )
                pm.connectAttr(self.attr_switch, "{}.inputX".format(node_reverse))

                for i, joint in enumerate(target_joints):
                    node_bm = pm.createNode("blendMatrix", n=self.getName("FkIk_bm"))
                    node_dcm = pm.createNode(
                        "decomposeMatrix", n=self.getName("FkIk_dcm")
                    )
                    node_cm_fk = pm.createNode("composeMatrix", n=self.getName("Fk_cm"))
                    node_cm_ik = pm.createNode("composeMatrix", n=self.getName("Ik_cm"))

                    (
                        self.dict_limb["loc_fk"][i].rotateOrder
                        >> self.dict_limb["loc_ik"][i].rotateOrder
                    )

                    self.dict_limb["loc_fk"][i].translate >> node_cm_fk.inputTranslate
                    self.dict_limb["loc_fk"][i].rotate >> node_cm_fk.inputRotate
                    (
                        self.dict_limb["loc_fk"][i].rotateOrder
                        >> node_cm_fk.inputRotateOrder
                    )

                    self.dict_limb["loc_ik"][i].translate >> node_cm_ik.inputTranslate
                    self.dict_limb["loc_ik"][i].rotate >> node_cm_ik.inputRotate
                    (
                        self.dict_limb["loc_ik"][i].rotateOrder
                        >> node_cm_ik.inputRotateOrder
                    )

                    pm.connectAttr(
                        "{}.outputMatrix".format(node_cm_fk),
                        "{}.inputMatrix".format(node_bm),
                    )
                    pm.connectAttr(
                        "{}.outputMatrix".format(node_cm_ik),
                        "{}.target[0].targetMatrix".format(node_bm),
                    )
                    pm.connectAttr(
                        self.attr_switch, "{}.target[0].weight".format(node_bm)
                    )

                    node_bm.outputMatrix >> node_dcm.inputMatrix
                    node_cm_fk.inputRotateOrder >> node_dcm.inputRotateOrder

                    node_dcm.outputTranslate >> joint.translate
                    node_dcm.outputRotate >> joint.rotate
                    node_dcm.outputScale >> joint.scale
                    node_dcm.inputRotateOrder >> joint.rotateOrder

                    attribute.reset_SRT([joint])

            def connect_switch_visibility():
                # connect visibility
                node_rev = pm.createNode("reverse", n=self.getName("switchVis_reverse"))
                pm.connectAttr(self.attr_switch, "{}.inputX".format(node_rev))
                pm.connectAttr(
                    "{}.inputX".format(node_rev), "{}.v".format(self.grp_ik_controls)
                )
                pm.connectAttr(
                    "{}.outputX".format(node_rev), "{}.v".format(self.grp_fk_controls)
                )

            target_joints = self.dict_limb["loc_main"]

            connect_switch_joints()
            connect_switch_visibility()

        connect_switch_joint()

        create_fk_function()
        create_ik_function()

        add_ribbon_function()

        make_finalize()

        ###############################
        ##### create attr switch ######
        ###############################
        pm.addAttr(
            self.ctrl_option,
            ln="scaleAll",
            min=0,
            dv=1,
            at="float",
            k=1,
        )
        pm.connectAttr(
            self.ctrl_option.scaleAll, self.dict_limb["loc_main"][2].scaleX, f=True
        )
        pm.connectAttr(
            self.ctrl_option.scaleAll, self.dict_limb["loc_main"][2].scaleY, f=True
        )
        pm.connectAttr(
            self.ctrl_option.scaleAll, self.dict_limb["loc_main"][2].scaleZ, f=True
        )

    def setRelation(self):
        """Set the relation beetween object from guide to rig"""

        self.relatives["root"] = self.dict_limb["loc_main"][0]
        self.relatives["low"] = self.dict_limb["loc_main"][1]
        self.relatives["end"] = self.dict_limb["loc_main"][2]
        self.relatives["eff"] = self.dict_limb["loc_main"][2]

        self.jointRelatives["root"] = 0
        self.jointRelatives["low"] = self.amount_up_ribbon - 1
        self.jointRelatives["eff"] = self.amount_up_ribbon + self.amount_low_ribbon

        self.jointRelatives["end"] = len(self.jnt_pos) - 1
