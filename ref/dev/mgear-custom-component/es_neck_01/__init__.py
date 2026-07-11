import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.shifter import component
import math

from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        # Create control

        # control base neck 01
        t = transform.getTransformFromPos(self.guide.pos["root"])
        self.control_neck_01 = self.addCtl(
            self.root,
            "neck_01",
            t,
            color=17,
            iconShape="circle",
            w=0.5 * self.size,
            h=0.5 * self.size,
            d=0.5 * self.size,
        )

        # control base neck 02
        posA = self.guide.pos["root"]
        posB = self.guide.pos["head"]
        self.p_neck_02 = [
            (posA[0] + posB[0]) / 2,
            (posA[1] + posB[1]) / 2,
            (posA[2] + posB[2]) / 2,
        ]
        self.m_neck_02 = transform.getTransformFromPos(self.p_neck_02)

        self.control_neck_02 = self.addCtl(
            self.root,
            "neck_02",
            self.m_neck_02,
            color=17,
            iconShape="circle",
            w=0.5 * self.size,
            h=0.5 * self.size,
            d=0.5 * self.size,
        )

        # control head
        t = transform.getTransformFromPos(self.guide.pos["head"])
        self.control_head = self.addCtl(
            self.control_neck_01,
            "head",
            t,
            color=6,
            iconShape="cube",
            w=0.5 * self.size,
            h=0.5 * self.size,
            d=0.5 * self.size,
        )

        # add npo for all control
        list_return = mgear.rigbits.addNPO(
            [self.control_head, self.control_neck_02, self.control_neck_01]
        )

        self.transform2Lock.extend(list_return)

        # Create Loc Bind
        self.loc_neck_01 = primitive.addTransform(
            self.root, self.getName("neck_01_loc")
        )
        self.loc_neck_02 = primitive.addTransform(
            self.root, self.getName("neck_02_loc")
        )
        self.loc_head = primitive.addTransform(
            self.control_head, self.getName("head_loc")
        )

        # set inherits transform
        self.loc_neck_01.inheritsTransform.set(False)
        self.loc_neck_02.inheritsTransform.set(False)
        self.loc_head.inheritsTransform.set(False)

        # Create loc joint
        self.jnt_pos.append(
            {
                "obj": self.loc_neck_01,
                "name": "neck_01",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

        self.jnt_pos.append(
            {
                "obj": self.loc_neck_02,
                "name": "neck_02",
                "newActiveJnt": len(self.jnt_pos) - 1,
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

        self.jnt_pos.append(
            {
                "obj": self.loc_head,
                "name": "head",
                "newActiveJnt": len(self.jnt_pos) - 1,
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        """Set the relation beetween object from guide to rig"""

        def create_neck_systems():
            # # connect matrix to main locator
            # Loc neck 01
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.control_neck_01),
                "{}.offsetParentMatrix".format(self.loc_neck_01),
            )
            self.loc_neck_01.translate.set(0, 0, 0)

            # set up npo of control neck 02
            npo = self.control_neck_02.getParent()
            npo.inheritsTransform.set(False)
            npo.translate.set(0, 0, 0)

            node_blend_matrix = pm.createNode(
                "blendMatrix", name=self.getName("spine_blendMatrix")
            )
            node_decompose_main = pm.createNode(
                "decomposeMatrix", name=self.getName("main_decompose")
            )
            node_pick_rotate = pm.createNode(
                "pickMatrix", name=self.getName("rotate_pickMatrix")
            )
            node_pick_main = pm.createNode(
                "pickMatrix", name=self.getName("main_pickMatrix")
            )
            node_decompose_rotate = pm.createNode(
                "decomposeMatrix", name=self.getName("rotate_decompose")
            )
            node_compose = pm.createNode(
                "composeMatrix", name=self.getName("composeMatrix")
            )
            node_mult_matrix = pm.createNode(
                "multMatrix", name=self.getName("multMatrix")
            )

            # connect >> blend matrix
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.control_neck_01),
                "{}.target[0].targetMatrix".format(node_blend_matrix),
            )
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.control_head),
                "{}.target[1].targetMatrix".format(node_blend_matrix),
            )
            pm.setAttr("{}.target[1].weight".format(node_blend_matrix), 0.5)

            # connect >> mult matrix
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.control_neck_01),
                "{}.inputMatrix".format(node_pick_rotate),
            )
            node_pick_rotate.useTranslate.set(False)
            node_pick_rotate.useScale.set(False)
            node_pick_rotate.useShear.set(False)

            pm.connectAttr(
                "{}.outputMatrix".format(node_blend_matrix),
                "{}.inputMatrix".format(node_pick_main),
            )
            node_pick_main.useRotate.set(False)

            pm.connectAttr(
                "{}.outputMatrix".format(node_pick_rotate),
                "{}.matrixIn[0]".format(node_mult_matrix),
            )
            pm.connectAttr(
                "{}.outputMatrix".format(node_pick_main),
                "{}.matrixIn[1]".format(node_mult_matrix),
            )

            # connect mult matrix >> decompose main
            pm.connectAttr(
                "{}.matrixSum".format(node_mult_matrix),
                "{}.inputMatrix".format(node_decompose_main),
            )

            # connect >> decompose rotate
            pm.connectAttr(
                "{}.outputMatrix".format(node_blend_matrix),
                "{}.inputMatrix".format(node_decompose_rotate),
            )

            # connect decompose main,rotate >> compose
            pm.connectAttr(
                "{}.outputRotateY".format(node_decompose_rotate),
                "{}.inputRotateY".format(node_compose),
            )

            pm.connectAttr(
                "{}.outputRotateX".format(node_decompose_main),
                "{}.inputRotateX".format(node_compose),
            )
            pm.connectAttr(
                "{}.outputRotateZ".format(node_decompose_main),
                "{}.inputRotateZ".format(node_compose),
            )

            pm.connectAttr(
                "{}.outputScale".format(node_decompose_main),
                "{}.inputScale".format(node_compose),
            )
            pm.connectAttr(
                "{}.outputShear".format(node_decompose_main),
                "{}.inputShear".format(node_compose),
            )
            pm.connectAttr(
                "{}.outputTranslate".format(node_decompose_main),
                "{}.inputTranslate".format(node_compose),
            )

            # connect compose >> output
            pm.connectAttr(
                "{}.outputMatrix".format(node_compose),
                "{}.offsetParentMatrix".format(npo),
            )

            # connect to loc 02
            pm.setAttr(self.loc_neck_02 + ".translate", 0, 0, 0, typ="double3")
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.control_neck_02),
                "{}.offsetParentMatrix".format(self.loc_neck_02),
            )

            # Loc neck 03
            pm.connectAttr(
                "{}.worldMatrix[0]".format(self.control_head),
                "{}.offsetParentMatrix".format(self.loc_head),
            )
            self.loc_head.translate.set(0, 0, 0)

        create_neck_systems()

        primitive.addTransform(self.root, self.getName("fk1_npo"))

        self.transform2Lock.extend([self.loc_head, self.loc_neck_01, self.loc_neck_02])

    def setRelation(self):
        self.relatives["head"] = self.control_head
        self.relatives["root"] = self.control_neck_01

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
