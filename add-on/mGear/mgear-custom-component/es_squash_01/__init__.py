from venv import create
import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.shifter import component
import math

from TonmaiToolkit.core import Create

from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive

import maya.api.OpenMaya as om


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        def create_controller():
            # control tip fk
            t = transform.getTransformFromPos(self.guide.pos["middle"])
            self.control_headTipFk = self.addCtl(
                self.grp_transform,
                "tipFk",
                t,
                color=16,
                iconShape="circle",
                w=0.5 * self.size,
                h=0.5 * self.size,
                d=0.5 * self.size,
            )

            # control tip handle
            t = transform.getTransformFromPos(self.guide.pos["tip"])
            self.control_headTip = self.addCtl(
                self.control_headTipFk,
                "tip",
                t,
                color=16,
                iconShape="sphere",
                w=0.1 * self.size,
                h=0.1 * self.size,
                d=0.1 * self.size,
            )

            # control bot fk
            t = transform.getTransformFromPos(self.guide.pos["middle"])
            self.control_headBotFk = self.addCtl(
                self.grp_transform,
                "buttomFk",
                t,
                color=16,
                iconShape="circle",
                w=0.5 * self.size,
                h=0.5 * self.size,
                d=0.5 * self.size,
            )

            # control bot handle
            t = transform.getTransformFromPos(self.guide.pos["bottom"])
            self.control_headBot = self.addCtl(
                self.control_headBotFk,
                "bottom",
                t,
                color=16,
                iconShape="sphere",
                w=0.1 * self.size,
                h=0.1 * self.size,
                d=0.1 * self.size,
            )

            # control squash middle
            t = transform.getTransformFromPos(self.guide.pos["middle"])
            self.control_headMid = self.addCtl(
                self.grp_transform,
                "middle",
                t,
                color=16,
                iconShape="cube",
                w=0.1 * self.size,
                h=0.1 * self.size,
                d=0.1 * self.size,
            )

            # add npo for all control
            list_return = mgear.rigbits.addNPO(
                [
                    self.control_headMid,
                    self.control_headBotFk,
                    self.control_headTip,
                    self.control_headBot,
                    self.control_headTipFk,
                ]
            )
            self.transform2Lock.extend(list_return)

        def create_bind_locator():
            # Create Loc Bind
            self.loc_base = primitive.addLocator(
                self.grp_locator_bind,
                self.getName("base_loc"),
                m=self.guide.tra["root"],
            )

            self.loc_tip = primitive.addLocator(
                self.grp_locator_bind,
                self.getName("headTip_loc"),
                m=self.guide.tra["root"],
            )
            self.loc_bottom = primitive.addLocator(
                self.grp_locator_bind,
                self.getName("headBot_loc"),
                m=self.guide.tra["root"],
            )

            # Create loc joint
            self.jnt_pos.append(
                {
                    "obj": self.loc_base,
                    "name": "base",
                    "newActiveJnt": "parent_relatives_joint",
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )

            self.jnt_pos.append(
                {
                    "obj": self.loc_tip,
                    "name": "tip",
                    "newActiveJnt": "base",
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )

            self.jnt_pos.append(
                {
                    "obj": self.loc_bottom,
                    "name": "bottom",
                    "newActiveJnt": "base",
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )

        # Create hierarchy
        self.grp_transform = pm.group(
            em=1, n=self.getName("transform_grp"), p=self.root
        )
        self.grp_locator_bind = pm.group(em=1, n=self.getName("locator_bind_grp"))

        self.grp_no_transform = pm.group(
            em=1, n=self.getName("no_transform_grp"), p=self.root
        )
        self.grp_no_transform.inheritsTransform.set(False)

        if self.settings["localRig"]:
            pm.parent(self.grp_locator_bind, self.grp_no_transform)
        else:
            pm.parent(self.grp_locator_bind, self.grp_transform)

        create_controller()
        create_bind_locator()

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        """Set the relation beetween object from guide to rig"""

        def connect_auto_scale(object1, object2, output):
            node_mult_matrix_01 = pm.createNode(
                "multMatrix", name=self.getName("{}_multMatrix".format(object1))
            )
            pm.connectAttr(
                "{}.worldMatrix[0]".format(object1),
                "{}.matrixIn[0]".format(node_mult_matrix_01),
            )
            pm.connectAttr(
                "{}.worldInverseMatrix[0]".format(self.root),
                "{}.matrixIn[1]".format(node_mult_matrix_01),
            )

            node_mult_matrix_02 = pm.createNode(
                "multMatrix", name=self.getName("{}_multMatrix".format(object2))
            )
            pm.connectAttr(
                "{}.worldMatrix[0]".format(object2),
                "{}.matrixIn[0]".format(node_mult_matrix_02),
            )
            pm.connectAttr(
                "{}.worldInverseMatrix[0]".format(self.root),
                "{}.matrixIn[1]".format(node_mult_matrix_02),
            )

            node_distance_between = pm.createNode(
                "distanceBetween", name=self.getName("distanceBetween")
            )
            pm.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_01),
                "{}.inMatrix1".format(node_distance_between),
            )
            pm.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_02),
                "{}.inMatrix2".format(node_distance_between),
            )
            distance_value = mc.getAttr("{}.distance".format(node_distance_between))
            multiply_value = 1 / distance_value

            node_mult_stretch = pm.createNode(
                "multDoubleLinear", name=self.getName("multDoubleLinear")
            )
            pm.connectAttr(
                "{}.distance".format(node_distance_between),
                "{}.input1".format(node_mult_stretch),
            )
            pm.setAttr("{}.input2".format(node_mult_stretch), multiply_value)
            attr_stretch_scale = "{}.output".format(node_mult_stretch)

            node_mult_squash = pm.createNode(
                "multiplyDivide", name=self.getName("multiplyDivide")
            )
            pm.setAttr("{}.operation".format(node_mult_squash), 2)
            pm.setAttr("{}.input1X".format(node_mult_squash), distance_value)
            pm.connectAttr(
                "{}.distance".format(node_distance_between),
                "{}.input2X".format(node_mult_squash),
            )

            attr_squash_scale = "{}.outputX".format(node_mult_squash)

            pm.connectAttr(attr_stretch_scale, "{}.sy".format(output))
            pm.connectAttr(attr_squash_scale, "{}.sx".format(output))
            pm.connectAttr(attr_squash_scale, "{}.sz".format(output))

        def set_up_ik_handle():
            # create aim joint
            pm.select(clear=1)
            jnt_head_up_01 = pm.joint(name="jnt_head_up_01")
            jnt_head_up_02 = pm.joint(name="jnt_head_up_02")

            pm.select(cl=1)
            jnt_head_low_01 = pm.joint(n="jnt_head_low_01")
            jnt_head_low_02 = pm.joint(n="jnt_head_low_02")

            jnt_head_up_01.visibility.set(False)
            jnt_head_up_02.visibility.set(False)
            jnt_head_low_01.visibility.set(False)
            jnt_head_low_02.visibility.set(False)

            # match transform joint
            locator_tip_translate = pm.spaceLocator(name="loc_headTip_translate")
            locator_tip_translate.visibility.set(False)

            list_ik_start_root.append(locator_tip_translate)
            pm.xform(locator_tip_translate, ws=1, t=self.guide.pos["middle"])
            pm.parent(locator_tip_translate, self.control_headMid)

            pm.xform(jnt_head_up_01, ws=1, t=self.guide.pos["middle"])
            posA = self.guide.pos["middle"]
            posB = self.guide.pos["tip"]
            distance = math.sqrt(
                ((posA[0] - posB[0]) ** 2)
                + ((posA[1] - posB[1]) ** 2)
                + ((posA[2] - posB[2]) ** 2)
            )
            pm.setAttr("{}.ty".format(jnt_head_up_02), distance)

            pm.parent(jnt_head_up_01, locator_tip_translate)

            pm.connectAttr(self.control_headTipFk + ".t", locator_tip_translate + ".t")

            # snap low position joint
            locator_bot_translate = pm.spaceLocator(name="loc_headBot_translate")
            locator_bot_translate.visibility.set(False)

            list_ik_start_root.append(locator_bot_translate)
            pm.xform(locator_bot_translate, ws=1, t=self.guide.pos["middle"])
            pm.parent(locator_bot_translate, self.control_headMid)

            pm.xform(jnt_head_low_01, ws=1, t=self.guide.pos["middle"])
            posA = self.guide.pos["middle"]
            posB = self.guide.pos["bottom"]
            distance = math.sqrt(
                ((posA[0] - posB[0]) ** 2)
                + ((posA[1] - posB[1]) ** 2)
                + ((posA[2] - posB[2]) ** 2)
            )
            pm.setAttr("{}.ty".format(jnt_head_low_02), distance)

            pm.parent(jnt_head_low_01, locator_bot_translate)

            pm.connectAttr(self.control_headBotFk + ".t", locator_bot_translate + ".t")

            # use ik handle
            ik_handle_up, ik_handle_up_eff = pm.ikHandle(
                n="ik_handle_up",
                sol="ikSCsolver",
                sj=jnt_head_up_01,
                ee=jnt_head_up_02,
            )
            ik_handle_low, ik_handle_low_eff = pm.ikHandle(
                n="ik_handle_low",
                sol="ikSCsolver",
                sj=jnt_head_low_01,
                ee=jnt_head_low_02,
            )

            pm.parent(ik_handle_up, self.control_headTip)
            pm.xform(ik_handle_up, ws=1, t=self.guide.pos["tip"])

            pm.parent(ik_handle_low, self.control_headBot)
            pm.xform(ik_handle_low, ws=1, t=self.guide.pos["bottom"])

            # recreate ik handle and freeze joint
            pm.getAttr(jnt_head_up_01 + ".r")
            pm.getAttr(jnt_head_low_01 + ".r")

            pm.delete(ik_handle_up, ik_handle_low, ik_handle_up_eff, ik_handle_low_eff)
            pm.makeIdentity(jnt_head_up_01, a=1, r=1)
            pm.makeIdentity(jnt_head_low_01, a=1, r=1)

            ik_handle_up_new = pm.ikHandle(
                n=self.getName("up_ikHandle"),
                sol="ikSCsolver",
                sj=jnt_head_up_01,
                ee=jnt_head_up_02,
            )[0]
            ik_handle_low_new = pm.ikHandle(
                n=self.getName("low_ikHandle"),
                sol="ikSCsolver",
                sj=jnt_head_low_01,
                ee=jnt_head_low_02,
            )[0]

            ik_handle_up_new.visibility.set(False)
            ik_handle_low_new.visibility.set(False)

            pm.parent(ik_handle_up_new, self.control_headTip)
            pm.xform(ik_handle_up_new, ws=1, t=self.guide.pos["tip"])

            pm.parent(ik_handle_low_new, self.control_headBot)
            pm.xform(ik_handle_low_new, ws=1, t=self.guide.pos["bottom"])

            mgear.core.attribute.lockAttribute(ik_handle_up_new)
            mgear.core.attribute.lockAttribute(ik_handle_low_new)

            # apply to bind locator
            if self.settings["localRig"]:
                # Connect Tip
                node_mm = pm.createNode(
                    "multMatrix", n=self.getName("inverse_world_tip_mm")
                )
                node_mm_offset = pm.createNode(
                    "multMatrix", n=self.getName("offset_tip_mm")
                )

                pm.connectAttr(
                    "{}.worldMatrix[0]".format(jnt_head_up_01),
                    "{}.matrixIn[0]".format(node_mm),
                )
                pm.connectAttr(
                    "{}.worldInverseMatrix[0]".format(self.root),
                    "{}.matrixIn[1]".format(node_mm),
                )

                matrix_current = om.MMatrix(
                    transform.getFilteredTransform(
                        pm.getAttr("{}.matrixSum".format(node_mm)),
                        rotation=False,
                        scaling=False,
                    )
                )
                matrix_target = om.MMatrix(
                    transform.getTransformFromPos(self.guide.pos["middle"])
                )
                matrix_offset = matrix_current.inverse() * matrix_target

                pm.connectAttr(
                    "{}.matrixSum".format(node_mm),
                    "{}.matrixIn[0]".format(node_mm_offset),
                )
                pm.setAttr("{}.matrixIn[1]".format(node_mm_offset), matrix_offset)

                attr_loc_tip_matrix = "{}.matrixSum".format(node_mm_offset)

                # Connect Bottom
                node_mm = pm.createNode(
                    "multMatrix", n=self.getName("inverse_world_bottom_mm")
                )
                node_mm_offset = pm.createNode(
                    "multMatrix", n=self.getName("offset_bottom_mm")
                )
                pm.connectAttr(
                    "{}.worldMatrix[0]".format(jnt_head_low_01),
                    "{}.matrixIn[0]".format(node_mm),
                )
                pm.connectAttr(
                    "{}.worldInverseMatrix[0]".format(self.root),
                    "{}.matrixIn[1]".format(node_mm),
                )

                matrix_current = om.MMatrix(
                    transform.getFilteredTransform(
                        pm.getAttr("{}.matrixSum".format(node_mm)),
                        rotation=False,
                        scaling=False,
                    )
                )
                matrix_target = om.MMatrix(
                    transform.getTransformFromPos(self.guide.pos["middle"])
                )
                matrix_offset = matrix_current.inverse() * matrix_target

                pm.connectAttr(
                    "{}.matrixSum".format(node_mm),
                    "{}.matrixIn[0]".format(node_mm_offset),
                )
                pm.setAttr("{}.matrixIn[1]".format(node_mm_offset), matrix_offset)

                attr_loc_bottom_matrix = "{}.matrixSum".format(node_mm_offset)

                node_dcm = pm.createNode("decomposeMatrix")
                pm.connectAttr(
                    "{}.worldInverseMatrix".format(self.root),
                    "{}.inputMatrix".format(node_dcm),
                )

            else:
                node_mm = pm.createNode("multMatrix")
                pm.connectAttr(
                    "{}.worldMatrix[0]".format(jnt_head_up_01),
                    "{}.matrixIn[0]".format(node_mm),
                )
                pm.connectAttr(
                    "{}.parentInverseMatrix[0]".format(self.loc_tip),
                    "{}.matrixIn[1]".format(node_mm),
                )
                attr_loc_tip_matrix = "{}.matrixSum".format(node_mm)

                node_mm = pm.createNode("multMatrix")
                pm.connectAttr(
                    "{}.worldMatrix[0]".format(jnt_head_low_01),
                    "{}.matrixIn[0]".format(node_mm),
                )
                pm.connectAttr(
                    "{}.parentInverseMatrix[0]".format(self.loc_bottom),
                    "{}.matrixIn[1]".format(node_mm),
                )
                attr_loc_bottom_matrix = "{}.matrixSum".format(node_mm)

            # connect to locator bind
            list_attr = [attr_loc_tip_matrix, attr_loc_bottom_matrix]
            locator_bind = [self.loc_tip, self.loc_bottom]

            for attr, locator in zip(list_attr, locator_bind):
                node_dcm = pm.createNode("decomposeMatrix", n="decomp_dcm")

                pm.connectAttr(
                    attr,
                    "{}.inputMatrix".format(node_dcm),
                )
                pm.connectAttr(
                    "{}.outputTranslate".format(node_dcm),
                    "{}.translate".format(locator),
                )
                pm.connectAttr(
                    "{}.outputRotate".format(node_dcm),
                    "{}.rotate".format(locator),
                )

            list_ik_handle.extend([ik_handle_up_new, ik_handle_low_new])

        list_ik_handle = []
        list_ik_start_root = []

        set_up_ik_handle()

        # create auto stretch
        connect_auto_scale(list_ik_start_root[0], list_ik_handle[0], self.loc_tip)
        connect_auto_scale(list_ik_start_root[1], list_ik_handle[1], self.loc_bottom)

        primitive.addTransform(self.root, self.getName("fk1_npo"))

    def setRelation(self):

        if self.settings["localRig"]:
            # top loc relative
            loc_top_local_relative = pm.spaceLocator(
                n=self.getName("top_local_relative_loc")
            )
            loc_top_local_relative.setParent(self.grp_no_transform)

            node_mm = pm.createNode("multMatrix")
            node_dcm = pm.createNode("decomposeMatrix")

            pm.connectAttr(
                "{}.worldMatrix".format(self.loc_tip), "{}.matrixIn[0]".format(node_mm)
            )
            matrix_world_inverse = pm.getAttr(
                "{}.worldInverseMatrix[0]".format(self.root)
            )
            pm.setAttr(
                "{}.matrixIn[1]".format(node_mm), matrix_world_inverse, typ="matrix"
            )
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.root),
                "{}.matrixIn[2]".format(node_mm),
            )

            pm.connectAttr(
                "{}.matrixSum".format(node_mm), "{}.inputMatrix".format(node_dcm)
            )
            pm.connectAttr(
                "{}.outputTranslate".format(node_dcm),
                "{}.translate".format(loc_top_local_relative),
            )
            pm.connectAttr(
                "{}.outputRotate".format(node_dcm),
                "{}.rotate".format(loc_top_local_relative),
            )
            pm.connectAttr(
                "{}.outputScale".format(node_dcm),
                "{}.scale".format(loc_top_local_relative),
            )

            # bottom loc relative
            loc_bottom_local_relative = pm.spaceLocator(
                n=self.getName("bottom_local_relative_loc")
            )
            loc_bottom_local_relative.setParent(self.grp_no_transform)

            node_mm = pm.createNode("multMatrix")
            node_dcm = pm.createNode("decomposeMatrix")

            pm.connectAttr(
                "{}.worldMatrix".format(self.loc_tip), "{}.matrixIn[0]".format(node_mm)
            )
            matrix_world_inverse = pm.getAttr(
                "{}.worldInverseMatrix[0]".format(self.root)
            )
            pm.setAttr(
                "{}.matrixIn[1]".format(node_mm), matrix_world_inverse, typ="matrix"
            )
            pm.connectAttr(
                "{}.worldMatrix".format(self.root),
                "{}.matrixIn[2]".format(node_mm),
            )

            pm.connectAttr(
                "{}.matrixSum".format(node_mm), "{}.inputMatrix".format(node_dcm)
            )
            pm.connectAttr(
                "{}.outputTranslate".format(node_dcm),
                "{}.translate".format(loc_bottom_local_relative),
            )
            pm.connectAttr(
                "{}.outputRotate".format(node_dcm),
                "{}.rotate".format(loc_bottom_local_relative),
            )
            pm.connectAttr(
                "{}.outputScale".format(node_dcm),
                "{}.scale".format(loc_bottom_local_relative),
            )

            self.relatives["middle"] = self.control_headMid
            self.relatives["bottom"] = loc_bottom_local_relative
            self.relatives["root"] = self.grp_transform
            self.relatives["tip"] = loc_top_local_relative

        else:
            self.relatives["middle"] = self.control_headMid
            self.relatives["bottom"] = self.loc_bottom
            self.relatives["root"] = self.grp_transform
            self.relatives["tip"] = self.loc_tip

    # @param self
    def addConnection(self):
        """Add more connection definition to the set"""

        self.connections["standard"] = self.connect_standard
        self.connections["orientation"] = self.connect_orientation
        self.connections["parent"] = self.connect_parent

    def connect_orientation(self):
        """orientation connection definition for the component"""
        self.connect_orientCns()

    def connect_standard(self):
        """standard connection definition for the component"""
        self.connect_standardWithSimpleIkRef()

    def connect_parent(self):
        self.connect_standardWithSimpleIkRef()
