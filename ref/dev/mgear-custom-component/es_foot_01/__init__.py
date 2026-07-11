from doctest import FAIL_FAST
from re import T
from xmlrpc.client import TRANSPORT_ERROR
import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.shifter import component
import math


from TonmaiToolkit.core import Create, Transform, Connection, Utility


from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        #######################
        ### Create Root Ctl ###
        #######################

        self.ctl_root = pm.group(em=1, p=self.root, n=self.getName("rootSclPiv_grp"))
        pm.addAttr(self.ctl_root, ln="FkIk", k=1, min=0, max=10)
        Create.create_freeze_group([self.ctl_root], "grpOffset")

        ########################
        ### Create Hierarchy ###
        ########################

        self.grp_fk = pm.group(em=1, n=self.getName("Fk"), p=self.ctl_root)
        self.grp_ik = pm.group(em=1, n=self.getName("Ik"), p=self.ctl_root)
        self.grp_main = pm.group(em=1, n=self.getName("Main"), p=self.ctl_root)

        ##############################
        ### Create Bind Locator   ####
        ##############################

        self.jnt_ankle = primitive.addJoint(
            self.grp_main,
            "Ankle_Jnt",
            m=transform.setMatrixScale(self.guide.tra["root"], (1, 1, 1)),
        )
        self.jnt_ball = primitive.addJoint(
            self.jnt_ankle,
            "Ball_Jnt",
            m=transform.setMatrixScale(self.guide.tra["ball"], (1, 1, 1)),
        )
        self.jnt_tip = primitive.addJoint(
            self.jnt_ball,
            "Tip_Jnt",
            m=transform.setMatrixScale(self.guide.tra["tip"], (1, 1, 1)),
        )

        pm.makeIdentity(self.jnt_ankle, a=1, r=1)
        ##############################
        ### Create Fk Joint Chain ####
        ##############################

        self.jnt_ankle_fk = primitive.addJoint(
            self.grp_fk,
            "AnkleFk_Jnt",
            m=transform.setMatrixScale(self.guide.tra["root"], (1, 1, 1)),
        )
        self.jnt_ball_fk = primitive.addJoint(
            self.jnt_ankle_fk,
            "BallFk_Jnt",
            m=transform.setMatrixScale(self.guide.tra["ball"], (1, 1, 1)),
        )
        self.jnt_tip_fk = primitive.addJoint(
            self.jnt_ball_fk,
            "TipFk_Jnt",
            m=transform.setMatrixScale(self.guide.tra["tip"], (1, 1, 1)),
        )

        pm.makeIdentity(self.jnt_ankle_fk, a=1, r=1)

        ##############################
        ### Create Ik Joint Chain ####
        ##############################

        self.jnt_ankle_ik = primitive.addJoint(
            self.grp_ik,
            "AnkleIk_Jnt",
            m=transform.setMatrixScale(self.guide.tra["root"], (1, 1, 1)),
        )
        self.jnt_ball_ik = primitive.addJoint(
            self.jnt_ankle_ik,
            "BallIk_Jnt",
            m=transform.setMatrixScale(self.guide.tra["ball"], (1, 1, 1)),
        )
        self.jnt_tip_ik = primitive.addJoint(
            self.jnt_ball_ik,
            "TipIk_Jnt",
            m=transform.setMatrixScale(self.guide.tra["tip"], (1, 1, 1)),
        )

        pm.makeIdentity(self.jnt_ankle_ik, a=1, r=1)

        # hide all joint chain visibility
        for joint in [self.jnt_ankle, self.jnt_ankle_fk, self.jnt_ankle_ik]:
            joint.visibility.set(False)

        self.jnt_pos.append(
            {
                "obj": self.jnt_ball,
                "name": "ball",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

        #################
        ### Variables ###
        #################

        if self.side == "L":  # L Leg config
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

        elif self.side == "R":  # R Leg config
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

        # Create loc pivot
        loc_inner_piv = primitive.addTransform(
            self.root, self.getName("innerPiv"), self.guide.tra["inner"]
        )
        loc_outer_piv = primitive.addTransform(
            self.root, self.getName("outerPiv"), self.guide.tra["outer"]
        )
        loc_heel_piv = primitive.addTransform(
            self.root, self.getName("heelPiv"), self.guide.tra["heel"]
        )
        loc_end_piv = primitive.addTransform(
            self.root, self.getName("endPiv"), self.guide.tra["tip"]
        )

        control_setting = self.ctl_root
        control_parent_ik = self.ctl_root
        control_parent_fk = self.ctl_root
        axis_foot_three = "zxy"
        list_locator_pivot = [loc_inner_piv, loc_outer_piv, loc_heel_piv, loc_end_piv]
        ball_joint = self.jnt_ball
        toe_joint = self.jnt_tip
        jnt_ball_fk = self.jnt_ball_fk
        jnt_toe_fk = self.jnt_tip_fk
        jnt_ball_ik = self.jnt_ball_ik
        jnt_toe_ik = self.jnt_tip_ik
        ankle_joint_ik = self.jnt_ankle_ik
        parent = self.ctl_root
        list_parent_reverse = []
        name_tag = "Foot"
        invert_roll_axis = self.inverse_roll
        invert_roll_value = self.inverse_roll_value
        invert_roll_side_axis = False
        invert_side_roll_value = True
        invert_toe_twist_value = True
        invert_heel_twist_value = True
        invert_middle_twist_value = self.invert_middle_twist_value
        auto_roll_default_value = self.roll_value

        # get pivot of foot
        axis_foot_forward, axis_foot_side, axis_foot_twist = [
            axis for axis in axis_foot_three
        ]

        loc_inner_piv, loc_outer_piv, loc_heel_piv, loc_end_piv = list_locator_pivot

        constraint_toe_orient = []

        # define all variables
        attr_foot_pitch = control_setting + ".roll"
        attr_bank = control_setting + ".sideRoll"
        attr_heel_twist = control_setting + ".baseTwist"
        attr_toe_twist = control_setting + ".tipTwist"
        attr_toe_pitch = control_setting + ".middleRoll"
        attr_ball_ik = control_setting + ".ballIk"
        attr_roll_ball_end = control_setting + ".rollBallEnd"

        piv_heel_twist = pm.joint(n="{}_heelTwist_piv".format(name_tag))
        piv_end = pm.joint(n="{}_end_piv".format(name_tag))
        piv_heel_roll = pm.joint(n="{}_heelRoll_piv".format(name_tag))
        piv_inner = pm.joint(n="{}_inner_piv".format(name_tag))
        piv_outer = pm.joint(n="{}_outer_piv".format(name_tag))
        piv_ball = pm.joint(n="{}_ball_piv".format(name_tag))
        self.piv_ankle = pm.joint(n="{}_ankle_piv".format(name_tag))

        match_inner, match_outer, match_heel, match_end = list_locator_pivot

        list_pivot_match = [
            match_heel,
            match_end,
            match_heel,
            match_inner,
            match_outer,
            jnt_ball_ik,
            self.jnt_ankle_ik,
        ]
        list_pivot_joint = [
            piv_heel_twist,
            piv_end,
            piv_heel_roll,
            piv_inner,
            piv_outer,
            piv_ball,
            self.piv_ankle,
        ]

        for joint in list_pivot_joint:
            joint.drawStyle.set(2)

        ############################
        #### Create Attribute ######
        ############################

        Utility.add_attribute_divider(control_setting, "IkPivot")

        pm.addAttr(
            attr_foot_pitch.split(".")[0],
            ln=attr_foot_pitch.split(".")[1],
            at="float",
            k=1,
        )
        pm.addAttr(attr_bank.split(".")[0], ln=attr_bank.split(".")[1], at="float", k=1)
        pm.addAttr(
            attr_toe_pitch.split(".")[0],
            ln=attr_toe_pitch.split(".")[1],
            at="float",
            k=1,
        )
        pm.addAttr(
            attr_heel_twist.split(".")[0],
            ln=attr_heel_twist.split(".")[1],
            at="float",
            k=1,
        )
        pm.addAttr(
            attr_toe_twist.split(".")[0],
            ln=attr_toe_twist.split(".")[1],
            at="float",
            k=1,
        )

        pm.addAttr(self.ctl_root, ln="ballIk", k=True)

        # add_attribute_divider(option_shape, name="Ik_config".format(name_tag))
        pm.addAttr(
            attr_roll_ball_end.split(".")[0],
            ln=attr_roll_ball_end.split(".")[1],
            at="float",
            k=1,
            dv=auto_roll_default_value,
        )

        ######################
        ### Connect Switch ###
        ######################
        Connection.connect_switch_joint(
            attr_switch=self.ctl_root + ".FkIk",
            fk_joints=[self.jnt_ankle_fk, self.jnt_ball_fk, self.jnt_tip_fk],
            ik_joints=[self.jnt_ankle_ik, self.jnt_ball_ik, self.jnt_tip_ik],
            bind_joints=[self.jnt_ankle, self.jnt_ball, self.jnt_tip],
            grp_fk=self.grp_fk,
            grp_ik=self.grp_ik,
            max_value=10,
            method="blendColors",
        )

        ############################
        ### Create Ik Connection ###
        ############################

        # create group hierarchy -----------------------------------
        self.grp_ik_pivot = pm.group(em=1, n=self.getName("IkPivot_Grp"), p=parent)
        pm.connectAttr(
            control_parent_ik + ".rotateOrder",
            self.grp_ik_pivot + ".rotateOrder",
            f=1,
        )
        pm.parent(self.grp_ik_pivot, self.grp_ik)

        # break connection -----------------------------------
        Connection.break_connection_transform(ankle_joint_ik, rot=True)

        # create reversed chain joint -----------------------------------
        pm.select(cl=1)
        for pivot_match, joint in zip(list_pivot_match, list_pivot_joint):
            # joint.visibility.set(False)
            pm.matchTransform(joint, pivot_match, pos=1)
            pm.matchTransform(joint, jnt_ball_ik, rot=1)

            pm.makeIdentity(joint, a=1, s=1, r=1)

        pm.parent(list_pivot_joint[0], self.grp_ik_pivot)

        # orient constraint piv to ik joint -----------------------------------
        loc_ball_orient = pm.spaceLocator(n="{}_ballOrient_loc".format(name_tag))
        loc_ball_orient.visibility.set(False)
        constraint = pm.parentConstraint(jnt_ball_ik, loc_ball_orient)
        pm.delete(constraint)
        pm.parent(loc_ball_orient, piv_outer)
        constraint_toe_orient.append(
            pm.orientConstraint(loc_ball_orient, jnt_ball_ik, mo=True)
        )

        loc_ankle_orient = pm.spaceLocator(n="{}_ankleOrient_loc".format(name_tag))
        loc_ankle_orient.visibility.set(False)
        pm.connectAttr(
            control_parent_ik + ".rotateOrder",
            loc_ankle_orient + ".rotateOrder",
            f=1,
        )
        constraint = pm.parentConstraint(self.jnt_ankle_ik, loc_ankle_orient)
        pm.delete(constraint)
        pm.parent(loc_ankle_orient, piv_ball)
        pm.orientConstraint(loc_ankle_orient, self.jnt_ankle_ik, mo=True)

        # parent ankle,pos end to piv
        for object in list_parent_reverse:
            if pm.objExists(object):
                Connection.break_connection_transform(object, pos=True, rot=True)
                pm.parentConstraint(self.piv_ankle, object, mo=1)

        def connect_side_roll():
            if invert_roll_side_axis:
                first_target = piv_outer
                second_target = piv_inner
            else:
                first_target = piv_inner
                second_target = piv_outer

            if invert_side_roll_value:
                node_mdl_invert = pm.createNode(
                    "multDoubleLinear", n="{}_rollSide_mdl".format(name_tag)
                )
                pm.setAttr(node_mdl_invert + ".input2", -1)
                pm.connectAttr(attr_bank, "{}.input1".format(node_mdl_invert))
                attr_output = "{}.output".format(node_mdl_invert)
            else:
                attr_output = attr_bank

            # Bank
            pm.setAttr(
                "{}.minRot{}LimitEnable".format(
                    first_target, axis_foot_forward.upper()
                ),
                1,
            )
            pm.setAttr(
                "{}.minRot{}Limit".format(first_target, axis_foot_forward.upper()),
                0,
            )

            pm.setAttr(
                "{}.maxRot{}LimitEnable".format(
                    second_target, axis_foot_forward.upper()
                ),
                1,
            )
            pm.setAttr(
                "{}.maxRot{}Limit".format(second_target, axis_foot_forward.upper()),
                0,
            )

            pm.connectAttr(
                attr_output, "{}.r{}".format(first_target, axis_foot_forward)
            )
            pm.connectAttr(
                attr_output, "{}.r{}".format(second_target, axis_foot_forward)
            )

        def connect_base_twist():
            if invert_heel_twist_value:
                node_mdl_invert = pm.createNode(
                    "multDoubleLinear", n="{}_baseTwist_mdl".format(name_tag)
                )
                pm.setAttr(node_mdl_invert + ".input2", -1)
                pm.connectAttr(attr_heel_twist, "{}.input1".format(node_mdl_invert))
                attr_output = "{}.output".format(node_mdl_invert)
            else:
                attr_output = attr_heel_twist

            pm.connectAttr(
                attr_output, "{}.r{}".format(piv_heel_twist, axis_foot_twist)
            )

        def connect_tip_twist():
            if invert_toe_twist_value:
                node_mdl_invert = pm.createNode(
                    "multDoubleLinear", n="{}_tipTwist_mdl".format(name_tag)
                )
                pm.setAttr(node_mdl_invert + ".input2", -1)
                pm.connectAttr(attr_toe_twist, "{}.input1".format(node_mdl_invert))
                attr_output = "{}.output".format(node_mdl_invert)
            else:
                attr_output = attr_toe_twist

            pm.connectAttr(attr_output, "{}.r{}".format(piv_end, axis_foot_twist))

        def connect_middle_twist():
            if invert_middle_twist_value:
                node_mdl_invert = pm.createNode(
                    "multDoubleLinear", n="{}_tipTwist_mdl".format(name_tag)
                )
                pm.setAttr(node_mdl_invert + ".input2", -1)
                pm.connectAttr(attr_toe_pitch, "{}.input1".format(node_mdl_invert))
                attr_output = "{}.output".format(node_mdl_invert)
            else:
                attr_output = attr_toe_pitch

            # ball attr
            node_adl_ball = pm.createNode(
                "addDoubleLinear", n="{}_ball_adl".format(name_tag)
            )
            pm.connectAttr(
                "{}.constraintRotate{}".format(
                    constraint_toe_orient[0], axis_foot_side.upper()
                ),
                "{}.input1".format(node_adl_ball),
            )
            pm.connectAttr(attr_output, "{}.input2".format(node_adl_ball))

            pm.connectAttr(
                "{}.output".format(node_adl_ball),
                "{}.r{}".format(jnt_ball_ik, axis_foot_side),
                f=1,
            )

        def connect_roll():
            def connect_roll_back():
                if invert_roll_axis:
                    value_cond_operation = 4
                else:
                    value_cond_operation = 2

                # Roll Out
                node_cond_roll_out = pm.createNode(
                    "condition", n="{}_rollOut_cond".format(name_tag)
                )
                pm.setAttr(
                    "{}.operation".format(node_cond_roll_out),
                    value_cond_operation,
                )

                pm.setAttr("{}.colorIfFalseR".format(node_cond_roll_out), 0)
                pm.connectAttr(attr_output, "{}.firstTerm".format(node_cond_roll_out))
                pm.connectAttr(
                    attr_output, "{}.colorIfTrueR".format(node_cond_roll_out)
                )

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_out),
                    "{}.r{}".format(piv_heel_roll, axis_foot_side),
                )

            def connect_roll_front():
                # Roll In --------------------------
                if invert_roll_axis:
                    value_condition = 4
                else:
                    value_condition = 2

                # node roll in
                node_cond_roll_in = pm.createNode(
                    "condition", n="{}_rollIn_cond".format(name_tag)
                )
                pm.setAttr("{}.operation".format(node_cond_roll_in), value_condition)

                pm.connectAttr(attr_output, "{}.firstTerm".format(node_cond_roll_in))
                pm.setAttr("{}.colorIfTrueR".format(node_cond_roll_in), 0)
                pm.connectAttr(
                    attr_output, "{}.colorIfFalseR".format(node_cond_roll_in)
                )

                # roll ball
                node_cond_roll_ball = pm.createNode(
                    "condition", n="{}_rollBall_cond".format(name_tag)
                )
                pm.setAttr("{}.operation".format(node_cond_roll_ball), value_condition)

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_in),
                    "{}.firstTerm".format(node_cond_roll_ball),
                )
                pm.connectAttr(
                    attr_roll_ball_end,
                    "{}.secondTerm".format(node_cond_roll_ball),
                )

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_in),
                    "{}.colorIfTrueR".format(node_cond_roll_ball),
                )
                pm.connectAttr(
                    attr_roll_ball_end,
                    "{}.colorIfFalseR".format(node_cond_roll_ball),
                )

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_ball),
                    "{}.r{}".format(piv_ball, axis_foot_side),
                )

                # roll end
                node_cond_roll_end = pm.createNode(
                    "condition", n="{}_rollEnd_cond".format(name_tag)
                )
                pm.setAttr("{}.operation".format(node_cond_roll_end), value_condition)

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_in),
                    "{}.firstTerm".format(node_cond_roll_end),
                )
                pm.connectAttr(
                    attr_roll_ball_end,
                    "{}.secondTerm".format(node_cond_roll_end),
                )

                node_pma_roll_end_offset = pm.createNode(
                    "plusMinusAverage",
                    n="{}_rollEndOffset_pma".format(name_tag),
                )
                pm.setAttr("{}.operation".format(node_pma_roll_end_offset), 2)

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_in),
                    "{}.input1D[0]".format(node_pma_roll_end_offset),
                )
                pm.connectAttr(
                    attr_roll_ball_end,
                    "{}.input1D[1]".format(node_pma_roll_end_offset),
                )
                pm.connectAttr(
                    "{}.output1D".format(node_pma_roll_end_offset),
                    "{}.colorIfFalseR".format(node_cond_roll_end),
                )

                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_end),
                    "{}.r{}".format(piv_end, axis_foot_side),
                )

                # attr roll
                node_adl_ball_ik = pm.createNode(
                    "addDoubleLinear", n="{}_ballIk_adl".format(name_tag)
                )
                pm.connectAttr(
                    "{}.outColorR".format(node_cond_roll_ball),
                    "{}.input1".format(node_adl_ball_ik),
                )
                pm.connectAttr(attr_ball_ik, "{}.input2".format(node_adl_ball_ik))
                pm.connectAttr(
                    "{}.output".format(node_adl_ball_ik),
                    "{}.r{}".format(piv_ball, axis_foot_side),
                    f=True,
                )

            if invert_roll_value:
                attr_output = Connection.connect_conversion(
                    input1=attr_foot_pitch, conversion=-1, name=name_tag
                )
            else:
                attr_output = attr_foot_pitch

            connect_roll_back()
            connect_roll_front()

        connect_base_twist()
        connect_tip_twist()
        connect_middle_twist()
        connect_side_roll()
        connect_roll()

        # ########################################
        # ### Add Ctl for moving ik : Optional ###
        # ########################################

        # Create Ik Ctl
        self.ctl_ik = self.addCtl(
            piv_heel_twist,
            "ik",
            transform.getTransformFromPos(self.guide.pos["tip"]),
            color=17,
            iconShape="cube",
            w=0.5 * self.size,
            h=0.5 * self.size,
            d=0.5 * self.size,
        )
        self.ctl_ik.rotateOrder.set(1)

        Create.create_freeze_group([self.ctl_ik])

        Connection.connect_conversion_unit(
            input="{}.rx".format(self.ctl_ik), output=attr_foot_pitch, factor=-30
        )
        Connection.connect_conversion_unit(
            input="{}.rz".format(self.ctl_ik), output=attr_bank, factor=-30
        )

        Utility.add_attribute_divider(self.ctl_ik, "Rig Attribute")
        pm.addAttr(self.ctl_ik, ln="baseTwist", pxy=attr_heel_twist, k=True)
        pm.addAttr(self.ctl_ik, ln="tipTwist", pxy=attr_toe_twist, k=True)
        pm.addAttr(self.ctl_ik, ln="middleRoll", pxy=attr_toe_pitch, k=True)
        pm.addAttr(self.ctl_ik, ln="ballIk", pxy=attr_ball_ik, k=True)

        Utility.add_attribute_divider(self.ctl_ik, "Rig Config")
        pm.addAttr(self.ctl_ik, ln="rollBallEnd", pxy=attr_roll_ball_end, k=True)
        #    pm.setAttr(self.ctl_ik + ".rollBallEnd", k=True)

        pm.setAttr("{}.tx".format(self.ctl_ik), l=True, k=False)
        pm.setAttr("{}.ty".format(self.ctl_ik), l=True, k=False)
        pm.setAttr("{}.tz".format(self.ctl_ik), l=True, k=False)

        pm.setAttr("{}.ry".format(self.ctl_ik), l=True, k=False)

        pm.setAttr("{}.sx".format(self.ctl_ik), l=True, k=False)
        pm.setAttr("{}.sy".format(self.ctl_ik), l=True, k=False)
        pm.setAttr("{}.sz".format(self.ctl_ik), l=True, k=False)

        pm.setAttr("{}.v".format(self.ctl_ik), l=True, k=False)

        pm.delete(list_locator_pivot)

        ###########################
        ####   Create Fk Ctl ######
        ###########################
        self.ctl_ball_fk = self.addCtl(
            self.grp_fk,
            "ballFk",
            transform.getTransform(self.jnt_ball_fk),
            color=17,
            iconShape="cube",
            w=0.5 * self.size,
            h=0.5 * self.size,
            d=0.5 * self.size,
        )

        grp_frz_ball_fk = Create.create_freeze_group([self.ctl_ball_fk])[0]
        Connection.constraint_matrix(
            [self.jnt_ankle_fk, grp_frz_ball_fk], "parent", mo=True
        )

        Connection.constraint_matrix([self.ctl_ball_fk, self.jnt_ball_fk], "parent")

        ##############
        ## Finalize ##
        ##############

        Utility.lock_attribute(self.ctl_ball_fk, t=True, s=True, v=True)

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        """Set the relation beetween object from guide to rig"""
        pass

    def setRelation(self):
        self.relatives["root"] = self.root
        # self.relatives["low"] = self.dict_limb["loc_main"][1]
        # self.relatives["end"] = self.dict_limb["loc_main"][2]
        # self.relatives["eff"] = self.dict_limb["loc_main"][2]

        self.jointRelatives["root"] = 0

    def addConnection(self):
        """Add more connection definition to the set"""

        self.connections["es_leg_01"] = self.connect_es_leg_01

    def connect_es_leg_01(self):
        """Connector for es_leg_01"""

        # If the parent component hasn't been generated we skip the connection
        if self.parent_comp is None:
            return

        pm.parent(self.root, self.parent_comp.root)

        self.parent_comp.ctrl_option.FkIk >> self.ctl_root.FkIk

        ##################
        ### Ik Connect ###
        ##################

        self.parent_comp.ik_handle_limb.setParent(self.piv_ankle)

        pm.pointConstraint(self.parent_comp.dict_limb["loc_ik"][2], self.jnt_ankle_ik)
        # pm.parentConstraint(self.parent_comp.ctl_ik_orient, self.grp_ik_pivot, mo=True)

        Connection.constraint_matrix(
            [self.piv_ankle, self.parent_comp.loc_end_dist], method="point"
        )

        ##################
        ### Fk Connect ###
        ##################

        pm.parentConstraint(
            self.parent_comp.dict_limb["ctrl_fk"][2], self.jnt_ankle_fk, mo=True
        )

        #############
        ## ##########
        #############

        # Apply Orient of ankle to limb ankle, Scale
        #    Connection.break_connection_transform()
        pm.pointConstraint(self.parent_comp.dict_limb["loc_main"][2], self.grp_main)

        pm.orientConstraint(
            self.jnt_ankle,
            self.parent_comp.dict_limb["loc_main"][2],
        )
        return
