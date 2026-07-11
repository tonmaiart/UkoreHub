import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.shifter import component
import math
from maya.api import OpenMaya as om

from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive

from TonmaiToolkit.core import Utility, Misc, Connection, Create


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        def create_main_controller():
            t = transform.getTransformFromPos(self.guide.pos["L_brow_03"])
            self.control_L_main = self.addCtl(
                self.group_transform,
                "L_brow_main",
                t,
                color=6,
                iconShape="cube",
                w=0.25 * self.size,
                h=0.25 * self.size,
                d=0.25 * self.size,
            )

            t = transform.getTransformFromPos(self.guide.pos["R_brow_03"])
            t = transform.setMatrixScale(t, (-1, 1, 1))

            self.control_R_main = self.addCtl(
                self.group_transform,
                "R_brow_main",
                t,
                color=6,
                iconShape="cube",
                w=0.25 * self.size,
                h=0.25 * self.size,
                d=0.25 * self.size,
            )

            list_npo = mgear.rigbits.addNPO([self.control_L_main, self.control_R_main])

        def create_sub_controller():
            # variables --------
            self.list_L_brow_control = []
            self.list_L_brow_name = ["L_brow_01", "L_brow_02", "L_brow_03", "L_brow_04"]

            self.list_R_brow_control = []
            self.list_R_brow_name = ["R_brow_01", "R_brow_02", "R_brow_03", "R_brow_04"]

            list_name = self.list_L_brow_name + self.list_R_brow_name

            # create controller
            for name in list_name:
                if name in self.list_L_brow_name:
                    scale = (1, 1, 1)
                elif name in self.list_R_brow_name:
                    scale = (-1, 1, -1)

                t = transform.getFilteredTransform(
                    self.guide.tra[name], translation=True, rotation=True, scaling=False
                )
                t = transform.setMatrixScale(t, scale)

                control = self.addCtl(
                    self.root,
                    "{}_ctrl".format(name),
                    t,
                    color=6,
                    iconShape="sphere",
                    w=0.15 * self.size,
                    h=0.15 * self.size,
                    d=0.15 * self.size,
                )

                if name in self.list_L_brow_name:
                    self.list_L_brow_control.append(control)
                elif name in self.list_R_brow_name:
                    self.list_R_brow_control.append(control)

            t_between_control = transform.getTransformFromPos(self.guide.pos["root"])
            self.control_between = self.addCtl(
                self.group_transform,
                "between_ctrl",
                t_between_control,
                color=6,
                iconShape="sphere",
                w=0.15 * self.size,
                h=0.15 * self.size,
                d=0.15 * self.size,
            )

            # Create Loc Bind locator
            self.list_L_brow_bind_loc = []
            self.list_R_brow_bind_loc = []

            for name in list_name:
                m = transform.getTransformFromPos(self.guide.pos[name])

                loc = primitive.addTransform(
                    self.group_no_transform, self.getName(name + "_loc"), m=m
                )

                if name in self.list_L_brow_name:
                    self.list_L_brow_bind_loc.append(loc)
                elif name in self.list_R_brow_name:
                    self.list_R_brow_bind_loc.append(loc)

            m = transform.getTransformFromPos(self.guide.pos["root"])
            self.between_brow_bind_loc = primitive.addTransform(
                self.group_no_transform, self.getName("between_loc"), m=m
            )

            # Create Npo
            mgear.rigbits.addNPO(
                self.list_L_brow_control
                + self.list_R_brow_control
                + [self.control_between]
            )

            # Parent controller to main controller
            for control in self.list_L_brow_control + self.list_R_brow_control:
                if control in self.list_L_brow_control:
                    set_value = 1
                    parent = self.control_L_main
                elif control in self.list_R_brow_control:
                    set_value = -1
                    parent = self.control_R_main

                npo = control.getParent()
                npo.scaleX.set(set_value)
                npo.setParent(parent)

            # create base joint
            loc_local = primitive.addTransform(
                self.group_no_transform, self.getName("base_loc"), m=m
            )
            self.jnt_pos.append(
                {
                    "obj": loc_local,
                    "name": "base",
                    "newActiveJnt": "parent_relative_jnt",
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )

            # Create joint
            list_locator_for_joint = (
                self.list_L_brow_bind_loc
                + self.list_R_brow_bind_loc
                + [self.between_brow_bind_loc]
            )
            list_name_for_joint = (
                self.list_L_brow_name + self.list_R_brow_name + ["between"]
            )

            for i, locator in enumerate(list_locator_for_joint):
                self.jnt_pos.append(
                    {
                        "obj": locator,
                        "name": list_name_for_joint[i],
                        "newActiveJnt": 0,
                        "gearMulMatrix": False,
                        "vanilla_nodes": True,
                    }
                )

        # Create hierarchy
        self.group_no_transform = pm.group(
            em=1, name=self.getName("still_grp"), parent=self.root
        )
        self.group_no_transform.inheritsTransform.set(False)

        self.group_transform = pm.group(
            em=1, name=self.getName("transform_grp"), parent=self.root
        )

        create_main_controller()
        create_sub_controller()

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        """Set the relation beetween object from guide to rig"""

        def apply_to_locator_bind():
            list_control = (
                self.list_L_brow_control
                + self.list_R_brow_control
                + [self.control_between]
            )
            list_locator = (
                self.list_L_brow_bind_loc
                + self.list_R_brow_bind_loc
                + [self.between_brow_bind_loc]
            )

            for locator, control in zip(list_locator, list_control):
                if self.settings["localRig"] is True:
                    # create node
                    node_mult_matrix = pm.createNode(
                        "multMatrix", name=self.getName("local_convert_multMatrix")
                    )
                    pm.addAttr(
                        node_mult_matrix,
                        longName="offsetMatrix",
                        dataType="matrix",
                        keyable=True,
                    )

                    # connection - main
                    pm.connectAttr(
                        "{}.worldMatrix".format(control),
                        "{}.matrixIn[0]".format(node_mult_matrix),
                    )
                    pm.connectAttr(
                        "{}.worldInverseMatrix".format(self.root),
                        "{}.matrixIn[1]".format(node_mult_matrix),
                    )

                    # connection - find offset
                    m_control = pm.xform(control, q=1, ws=1, m=1)

                    matrix_sum = pm.getAttr("{}.matrixSum".format(node_mult_matrix))
                    matrix_sum = [item for row in matrix_sum for item in row]

                    m_value1 = om.MMatrix(m_control)
                    m_value2 = om.MMatrix(matrix_sum)
                    m_offset = m_value2.inverse() * m_value1

                    pm.setAttr(
                        "{}.offsetMatrix".format(node_mult_matrix),
                        m_offset,
                        type="matrix",
                    )
                    pm.connectAttr(
                        "{}.offsetMatrix".format(node_mult_matrix),
                        "{}.matrixIn[2]".format(node_mult_matrix),
                    )

                    # connection - apply
                    pm.connectAttr(
                        "{}.matrixSum".format(node_mult_matrix),
                        "{}.offsetParentMatrix".format(locator),
                    )
                    locator.translate.set(0, 0, 0)
                elif self.settings["localRig"] is False:
                    Connection.constraint_matrix([control, locator], method="parent")
                    Connection.constraint_matrix([control, locator], method="scale")

        constraint = pm.pointConstraint(
            self.list_L_brow_control[0],
            self.list_R_brow_control[0],
            self.control_between.getParent(),
            maintainOffset=True,
        )
        pm.pointConstraint(
            self.list_L_brow_control[0],
            self.list_L_brow_control[2],
            self.list_L_brow_control[1].getParent(),
            maintainOffset=True,
        )
        pm.pointConstraint(
            self.list_R_brow_control[0],
            self.list_R_brow_control[2],
            self.list_R_brow_control[1].getParent(),
            maintainOffset=True,
        )

        pm.setAttr(
            "{}.{}W0".format(constraint, Utility.cut(self.list_L_brow_control[0])), 0.25
        )
        pm.setAttr(
            "{}.{}W1".format(constraint, Utility.cut(self.list_R_brow_control[0])), 0.25
        )

        apply_to_locator_bind()
        # connect_blend_between_control()

    def setRelation(self):
        self.relatives["root"] = self.root

    def addConnection(self):
        pass
