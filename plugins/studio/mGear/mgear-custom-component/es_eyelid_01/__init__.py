from tkinter.messagebox import NO
from typing import KeysView

# from es_eyelid_01.guide import Guide
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
import string

class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        def create_bind_locator():
            # create joint
            self.loc_root = primitive.addLocator(
                name=self.getName("root_loc"),
                parent=self.grp_bind_locator,
                m=self.guide.tra["root"],
            )
            self.jnt_pos.append(
                {
                    "obj": self.loc_root,
                    "name": "root",
                    "newActiveJnt": "parent_relative_jnt",
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )
            self.dict_bind_loc["root"] = self.loc_root

            # create lid joint for inner and outer
            dict_data = [
                ["InUp", self.list_inner_upper_pos],
                ["InLow", self.list_inner_lower_pos],
                ["OutUp", self.list_outer_upper_pos],
                ["OutLow", self.list_outer_lower_pos],
            ]

            for data in dict_data:
                keyword, list_pos = data
                group = pm.group(em=1,name=keyword+"_bind_loc",p=self.grp_bind_locator)

                for i, pos in enumerate(list_pos):
                    name = self.getName("{}_{}".format(keyword, i + 1))
                    loc_bind = primitive.addLocator(
                        name=name,
                        parent=group,
                        m=transform.getTransformFromPos(pos),
                    )
                    self.jnt_pos.append(
                        {
                            "obj": loc_bind,
                            "name": name,
                            "newActiveJnt": 0,
                            "gearMulMatrix": False,
                            "vanilla_nodes": True,
                        }
                    )
                    self.dict_bind_loc[keyword].append(loc_bind)

            # create bind locator for between
            if self.between_joint_amount >= 1:
                list_bind_in_up_locator = self.dict_bind_loc["InUp"]
                list_bind_in_low_locator = self.dict_bind_loc["InLow"]
                list_bind_out_up_locator = self.dict_bind_loc["OutUp"]
                list_bind_out_low_locator = self.dict_bind_loc["OutLow"]

                for i in range(self.between_joint_amount):
                    # create key name
                    uppercase_letters = list(string.ascii_uppercase)
                    key_name_up = uppercase_letters[i]+"Up"
                    key_name_low = uppercase_letters[i]+"Low"

                    # create group
                    grp_name_up = pm.group(em=1, name=key_name_up + "_bind_loc", p=self.grp_bind_locator)
                    grp_name_low = pm.group(em=1, name=key_name_low + "_bind_loc", p=self.grp_bind_locator)

                    # create dictionary keyname
                    self.dict_bind_loc[key_name_up] = []
                    self.dict_bind_loc[key_name_low] = []

                    # create up bind locator and append to dictionary
                    for j in range(len(list_bind_in_up_locator)):
                        # get pos up
                        posA = pm.xform(list_bind_in_up_locator[j],q=1,ws=1,t=1)
                        posB = pm.xform(list_bind_out_up_locator[j],q=1,ws=1,t=1)
                        posUp = Transform.get_linear_position_division(posA=posA,
                                                                     posB=posB,
                                                                     division=self.between_joint_amount)[i]

                        # get pos low
                        posA = pm.xform(list_bind_in_low_locator[j],q=1,ws=1,t=1)
                        posB = pm.xform(list_bind_out_low_locator[j],q=1,ws=1,t=1)
                        posLow = Transform.get_linear_position_division(posA=posA,
                                                                     posB=posB,
                                                                     division=self.between_joint_amount)[i]

                        # create up bind locator and append to dictionary
                        name = self.getName("{}_{}".format(key_name_up, j + 1))
                        loc_bind = primitive.addLocator(
                            name=name,
                            parent=grp_name_up,
                            m=transform.getTransformFromPos(posUp),
                        )
                        self.jnt_pos.append(
                            {       
                                "obj": loc_bind,
                                "name": name,
                                "newActiveJnt": 0,
                                "gearMulMatrix": False,
                                "vanilla_nodes": True,
                            }
                        )
                        self.dict_bind_loc[key_name_up].append(loc_bind)

                        # create low bind locator and append to dictionary
                        name = self.getName("{}_{}".format(key_name_low, j + 1))
                        loc_bind = primitive.addLocator(
                            name=name,
                            parent=grp_name_low,
                            m=transform.getTransformFromPos(posLow),
                        )
                        self.jnt_pos.append(
                            {
                                "obj": loc_bind,
                                "name": name,
                                "newActiveJnt": 0,
                                "gearMulMatrix": False,
                                "vanilla_nodes": True,
                            }
                        )
                        self.dict_bind_loc[key_name_low].append(loc_bind)


        # Create Hierarchy
        if self.side == "L":
            self.scale_vector = (1,1,1)
        elif self.side == "R":
            self.scale_vector = (-1,1,1)

        self.between_joint_amount = 2

        self.dict_bind_loc = {
            "root": None,
            "InUp": [],
            "InLow": [],
            "OutUp": [],
            "OutLow": [],
        }

        curve_inner_upper = self.settings["UpInLidCrv"]
        curve_inner_lower = self.settings["LowInLidCrv"]
        curve_outer_upper = self.settings["UpOutLidCrv"]
        curve_outer_lower = self.settings["LowOutLidCrv"]


        curve_inner_upper_spans = pm.getAttr(
            "{}.spans".format(
                pm.listRelatives(curve_inner_upper, c=1, s=1, typ="nurbsCurve")[0]
            )
        )+1
        curve_inner_lower_spans = pm.getAttr(
            "{}.spans".format(
                pm.listRelatives(curve_inner_lower, c=1, s=1, typ="nurbsCurve")[0]
            )
        )+1
        curve_outer_upper_spans = pm.getAttr(
            "{}.spans".format(
                pm.listRelatives(curve_outer_upper, c=1, s=1, typ="nurbsCurve")[0]
            )
        )+1
        curve_outer_lower_spans = pm.getAttr(
            "{}.spans".format(
                pm.listRelatives(curve_outer_lower, c=1, s=1, typ="nurbsCurve")[0]
            )
        )+1

        print("spans : ",curve_inner_upper_spans)


        self.list_inner_upper_pos = [
            pm.xform("{}.ep[{}]".format(curve_inner_upper, i), q=1, ws=1, t=1)
            for i in range(curve_inner_upper_spans)
        ]
        self.list_inner_lower_pos = [
            pm.xform("{}.ep[{}]".format(curve_inner_lower, i), q=1, ws=1, t=1)
            for i in range(curve_inner_lower_spans)
        ]

        self.list_outer_upper_pos = [
            pm.xform("{}.ep[{}]".format(curve_outer_upper, i), q=1, ws=1, t=1)
            for i in range(curve_outer_upper_spans)
        ]
        self.list_outer_lower_pos = [
            pm.xform("{}.ep[{}]".format(curve_outer_lower, i), q=1, ws=1, t=1)
            for i in range(curve_outer_lower_spans)
        ]

        # Create Main Lid Ctrl
        self.main_ctrl = self.addCtl(
            parent=self.root,
            name="mainLid",
            m=transform.setMatrixScale(transform.getTransformFromPos(self.guide.pos["root"]),self.scale_vector) ,
            color=19,
            iconShape="cube",
        )
        Create.create_freeze_group([self.main_ctrl])


        # Create Hierarchy
        self.grp_transform = pm.group(em=1, n=self.getName("transform_grp"), p=self.main_ctrl)
        self.grp_eye_curves = pm.group(em=1, n=self.getName("eyeCurves_grp"),p=self.grp_transform)
        self.grp_loc_aim = pm.group(em=1, n=self.getName("aim_loc_grp"),p=self.grp_transform)
        self.grp_controllers = pm.group(em=1, n=self.getName("ctrls_grp"),p=self.grp_transform)
        self.grp_slide_joints = pm.group(em=1, n=self.getName("slide_joints_grp"),p=self.grp_transform)
        self.grp_bind_locator = pm.group(em=1, n=self.getName("bind_locator_grp"),p=self.grp_transform)
        self.grp_main_ctrl = pm.group(em=1,n=self.getName("MainControl_grp"),p=self.grp_transform)

        self.grp_no_transform = pm.group(em=1, n=self.getName("still_grp"), p=self.root)
        self.grp_no_transform.inheritsTransform.set(False)
        self.grp_eye_curves_still = pm.group(em=1, n=self.getName("eyeCurvesStill_grp"),p=self.grp_no_transform)
        self.grp_no_transform.visibility.set(False)


        # Create Main Control
        self.ctrl_main_up = self.addCtl(
            parent=self.grp_main_ctrl,
            name="mainUp",
            m=transform.setMatrixScale(transform.getTransformFromPos(self.list_inner_upper_pos[int(math.floor(len(self.list_inner_upper_pos)/2))]),scl=self.scale_vector),
            color=18,
            iconShape="cube",
        )

        self.ctrl_main_low = self.addCtl(
            parent=self.grp_main_ctrl,
            name="mainLow",
            m=transform.setMatrixScale(transform.getTransformFromPos(self.list_inner_lower_pos[int(math.floor(len(self.list_inner_lower_pos)/2))]),scl=self.scale_vector),
            color=18,
            iconShape="cube",
        )

        # self.main_in_ctrl = self.addCtl(
        #     parent=self.grp_main_ctrl,
        #     name="mainIn",
        #     m=transform.setMatrixScale(transform.getTransformFromPos(Transform.get_linear_position_division(self.list_inner_upper_pos[0],self.list_inner_lower_pos[0],division=1)[0]),scl=self.scale_vector),
        #     color=18,
        #     iconShape="cube",
        # )

        # self.main_out_ctrl = self.addCtl(
        #     parent=self.grp_main_ctrl,
        #     name="mainOut",
        #     m=transform.setMatrixScale(transform.getTransformFromPos(Transform.get_linear_position_division(self.list_inner_upper_pos[-1],self.list_inner_lower_pos[-1],division=1)[0]),scl=self.scale_vector),
        #     color=18,
        #     iconShape="cube",
        # )


        Create.create_freeze_group([self.ctrl_main_up,self.ctrl_main_low])

        create_bind_locator()

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        def create_aim_target_locator(list_pos, name, parent=None, average=False):
            """
            Create locators from list of pos

            Return:
            1) (list) Locators
            """

            def find_average():
                pos_average = [0, 0, 0]
                for p in list_pos:
                    for i in range(3):
                        pos_average[i] += p[i]
                for i in range(3):
                    pos_average[i] = pos_average[i] / len(list_pos)

                return pos_average

            list_locators = []

            # eyelid case
            if average == False:
                for p in list_pos:
                    loc = pm.spaceLocator(n=name)
                    pm.xform(loc, ws=1, t=p)

                    list_locators.append(loc)

            # eyeball case
            elif average == True:
                if len(list_pos) == 1:
                    single = pm.xform(pm.spaceLocator(n=name), ws=1, t=list_pos)

                    list_locators.append(single)

                else:
                    loc = pm.spaceLocator(n=name)

                    pos = find_average()
                    pm.xform(loc, ws=1, t=pos)

                    list_locators.append(loc)

            if parent != None:
                pm.parent(list_locators, parent)

            return list_locators

        def create_joint_chain(name, pos_center, list_pos_tip, parent):
            list_joint_A = []
            list_joint_B = []

            pm.select(cl=1)

            for i, loc in enumerate(list_pos_tip):
                no = str(i + 1)
                pos_end = list_pos_tip[i]

                pm.select(cl=1)
                jnt_start = pm.joint(p=pos_center,n="jnt_{}_start_{}".format(name,no))
                jnt_end = pm.joint(p=pos_end,n="jnt_{}_end_{}".format(name,no))

                pm.joint(jnt_start, e=1, oj="yxz", secondaryAxisOrient="xup", ch=1, zso=1)

                pm.parent(jnt_start, parent)
                list_joint_A.append(jnt_start)
                list_joint_B.append(jnt_end)


            return list_joint_A,list_joint_B

        def create_aim_joints(suffix, name, loc_center, locators, parent, jnt_size=0.01):
            """
            input loc of center as loc Start , list of lid locs as ls_locEnd
            Args:
            1)suffix
            2)loc_center
            3)locators

            Return:
            1)list of joint aim root
            """

            print("loc center : ", loc_center)

            joints_root = []
            joints_bind = []
            pos_center = pm.xform(loc_center, q=1, ws=1, t=1)
            pm.select(cl=1)

            for index, loc in enumerate(locators):
                no = str(index + 1)
                pos_end = pm.xform(loc, q=1, ws=1, t=1)
                pm.select(cl=1)
                jnt_start = pm.joint(
                    p=pos_center,
                    rad=jnt_size,
                    n="jnt_" + suffix + "_" + name + "Lid_start_" + no,
                )
                jnt_end = pm.joint(
                    p=pos_end,
                    rad=jnt_size,
                    n="jnt_" + suffix + "_" + name + "_eyeLid_end_" + no,
                )

                pm.joint(
                    jnt_start, e=1, oj="yxz", secondaryAxisOrient="xup", ch=1, zso=1
                )
                pm.aimConstraint(
                    loc,
                    jnt_start,
                    mo=1,
                    weight=1,
                    aimVector=(0, 1, 0),
                    upVector=(0, 0, 1),
                    worldUpType="object",
                    worldUpObject=loc_center,
                )

                pm.parent(jnt_start, parent)
                joints_root.append(jnt_start)
                joints_bind.append(jnt_end)

            return joints_root,joints_bind

        def create_pin_curve(
            ls_loc=None, name="crv_newCurve", w=1, color=(0, 0, 0), parent=None
        ):
            """Create high curve which pin locator to the curve ,Return Transform of Curve
            Args:
            ls_loc = (list) selection

            Returns:
            1)crv_shape = (str) hight curve
            """
            if type(ls_loc) != list:
                ls_loc = pm.ls(os=1)

            # create curve
            list_pos = []
            for s in ls_loc:
                pos_s = pm.xform(s, q=1, t=1, ws=1)
                list_pos.append(pos_s)

            crv_obj = pm.curve(n=name, d=1, p=list_pos)
            crv_shp = pm.listRelatives(crv_obj, c=1, s=1, f=1)[0]
            pm.setAttr(f"{crv_shp}.lineWidth", w)
            pm.setAttr(f"{crv_shp}.overrideEnabled", 1)
            pm.setAttr(f"{crv_shp}.overrideRGBColors", 1)
            pm.setAttr(f"{crv_shp}.overrideColorRGB", color[0], color[1], color[2])

            # pin curve
            clean_node = []

            for s in ls_loc:
                dcm_node = pm.createNode("decomposeMatrix", name=s + "_dcm")
                poc_node = pm.createNode("pointOnCurveInfo", name=s + "_poc")
                npc_node = pm.createNode("nearestPointOnCurve", name=s + "_npc")

                # prepare dcm node
                pm.connectAttr(s + ".worldMatrix", dcm_node + ".inputMatrix")

                # prepare npc node
                pm.connectAttr(dcm_node + ".outputTranslate", npc_node + ".inPosition")
                pm.connectAttr(crv_shp + ".worldSpace", npc_node + ".inputCurve")

                # connect to poc node
                pm.connectAttr(crv_shp + ".worldSpace", poc_node + ".inputCurve")

                param = pm.getAttr(npc_node + ".parameter")
                pm.setAttr(poc_node + ".parameter", param)

                pm.connectAttr(poc_node + ".result.position", s + ".translate")

                # append unused node to clean list
                clean_node.append(dcm_node)
                clean_node.append(npc_node)

            pm.select(cl=1)

            for node in clean_node:
                pm.delete(node)

            pm.parent(crv_obj, parent)

            return crv_obj

        def create_bind_curve(crv, name, parent):
            """This Function rebuild hight to low curve and create pointOnCurve node

            Arg:
            1)crv
            2)name

            Return:
            1)ls_poc_node = (list) point on curve nodes which will be position of driver joint
            2)crv_shape = (str) shape of output low curve
            3)center_poc = (str) center point on curve node

            """
            # rebuild crv
            print("curve : ", crv)
            crv_tr = pm.rebuildCurve(crv, d=3, rt=0, s=4, rpo=0, n=name)[0]

            # create joints along crv and calculate position
            ls_node_name = ["inner", "main1", "main2", "main3", "outer"]
            ls_poc_node = []

            for node in ls_node_name:
                ls_poc_node.append(
                    pm.createNode("pointOnCurveInfo", n="poc_" + name + node)
                )

            # conenct poc to low curve and enable percentage
            for node in ls_poc_node:
                pm.connectAttr(crv_tr + ".worldSpace[0]", node + ".inputCurve")
                pm.setAttr(node + ".turnOnPercentage", 1)

            if parent:
                pm.parent(crv_tr, parent)

            return ls_poc_node, crv_tr, ls_poc_node[2]

        def CreateWireCurve(crv_target, crv_control, name, zeroOffset=False):
            output = pm.wire(crv_target, n=name, gw=0, en=1, ce=0, li=0, w=crv_control)
            wr_node = output[0]

            if zeroOffset == True:
                pm.setAttr(wr_node + ".scale[0]", 0)

            return wr_node


        def create_driver_joints_v2(crv_up, crv_down,parent,suffix
        ):
            """This function is create the drive joint to drive the input curves (you can change the specific postion of center curve) and calcurate"""

            def AveragePosition(ls_poc, param):
                """This Function average position of point on curve ,reference from param

                Returns:
                position list of output traslation for each poc"""
                pm.setAttr(ls_poc[0] + ".parameter", 0)
                pm.setAttr(ls_poc[1] + ".parameter", param / 2)
                pm.setAttr(ls_poc[2] + ".parameter", param)
                pm.setAttr(ls_poc[3] + ".parameter", param + (param / 2))
                pm.setAttr(ls_poc[4] + ".parameter", 1)

                ls_position = []
                for poc in ls_poc:
                    ls_position.append(pm.getAttr(poc + ".position"))

                return ls_position

            controller_amount = 5

            list_uplid_ctrl_pos =  [Transform.get_position_from_curve_param(crv_up,param=param) for param in [0,0.25,0.5,0.75,1]]
            list_lowlid_ctrl_pos = [Transform.get_position_from_curve_param(crv_down,param=param) for param in [0.25,0.5,0.75]]

            # create driver joints at position and bind
            ls_drv_jnt_up = []
            ls_drv_jnt_low = []

            ls_drv_jnt_up_name = ["In","Up1","Up2","Up3","Out"]
            ls_drv_jnt_low_name = ["Low1","Low2","Low3"]

            for i,name in enumerate(ls_drv_jnt_up_name+ls_drv_jnt_low_name):
                pos = (list_uplid_ctrl_pos+list_lowlid_ctrl_pos)[i]
                control = self.addCtl(
                    parent=parent,
                    name="{}_{}_{}".format(suffix,name,i + 1),
                    m=transform.setMatrixScale(transform.getTransformFromPos(pos),scl=self.scale_vector),
                    color=17,
                    iconShape="cube",
                    size=0.01,
                )
                Create.create_freeze_group([control])
                joint = pm.createNode("joint", n=self.getName("{}_{}_{}_jnt".format(suffix,name,i + 1)))
                pm.setAttr("{}.drawStyle".format(joint), 2)
                Utility.match_parent(joint, control)

                if name in ls_drv_jnt_up_name:
                    ls_drv_jnt_up.append(joint)
                elif name in ls_drv_jnt_low_name:
                    ls_drv_jnt_low.append(joint)

            # bind skin cluster
            pm.skinCluster(
                crv_up,
                ls_drv_jnt_up + [ls_drv_jnt_low[0], ls_drv_jnt_low[-1]],
                mi=3,
                name="bind_up_crv_skinCluster",
            )
            pm.skinCluster(
                crv_down,
                ls_drv_jnt_low + [ls_drv_jnt_up[0], ls_drv_jnt_up[-1]],
                mi=3,
                name="bind_down_crv_skinCluster",
            )


            return ls_drv_jnt_up,ls_drv_jnt_low


        def CreateBlendShape(
            bln_child=None, dup_crv=None, name="blinkHeight", attr_height=None
        ):
            # duplicate target and create blendshape
            crv_target = pm.duplicate(dup_crv, n="crv_" + name)[0]
            bln_child.append(crv_target)
            blendshape = pm.blendShape(bln_child)[0]

            node_uc = pm.shadingNode("unitConversion", au=1, n="uc_" + name)
            pm.setAttr(node_uc + ".conversionFactor", 0.1)

            # create node and connect attr_height to blendshape
            rev_node = pm.shadingNode("reverse", au=1, name="rev_" + name)
            pm.connectAttr(attr_height, node_uc + ".input")
            pm.connectAttr(node_uc + ".output", blendshape + ".weight[0]")
            pm.connectAttr(node_uc + ".output", rev_node + ".input.inputX")
            pm.connectAttr(rev_node + ".output.outputX", blendshape + ".weight[1]")

            return crv_target

        def connect_to_bind_locator():
            # Inner Joint Connect
            for i, joint in enumerate(list_inner_up_slide_output):
                pm.parent(self.dict_bind_loc["InUp"][i],joint)
                # Connection.constraint_matrix(
                #     [joint, self.dict_bind_loc["InUp"][i]],
                #     method="parent",
                #     mo=False,
                # )
            for i, joint in enumerate(list_inner_low_slide_output):
                pm.parent(self.dict_bind_loc["InLow"][i],joint)
                # Connection.constraint_matrix(
                #     [joint, self.dict_bind_loc["InLow"][i]],
                #     method="parent",
                #     mo=False,
                # )


            return
        def parent_between_bind_locator():
            # Outer Joint Connect
            for i,joint in enumerate(list_outer_up_slide_output):
                pm.parent(self.dict_bind_loc["OutUp"][i],joint)

                # Connection.constraint_matrix(
                #     [joint,self.dict_bind_loc["OutUp"][i]],
                #     method="parent",
                #     mo=False
                # )

            for i,joint in enumerate(list_outer_low_slide_output):
                pm.parent(self.dict_bind_loc["OutLow"][i],joint)

                # Connection.constraint_matrix(
                #     [joint,self.dict_bind_loc["OutLow"][i]],
                #     method="parent",
                #     mo=False
                # )

            # Between Connect
            list_alphabet = list(string.ascii_uppercase)

            for i in range(self.between_joint_amount):
                for part in ["Up","Low"]:
                    for j in range(len( self.dict_bind_loc["{}{}".format(list_alphabet[i],part)])):
                        locA = dict_between_bind_joint["{}{}".format(list_alphabet[i],part)][j]
                        locB = self.dict_bind_loc["{}{}".format(list_alphabet[i],part)][j]

                        pm.parent(locB,locA)
                        # Connection.constraint_matrix(
                        #     [locA,locB],
                        #     method="parent",
                        #     mo=False
                        # )
            
            pm.parent(self.dict_bind_loc["root"],self.grp_slide_joints)
        """Main Operation"""
        """This Function Create Eye Rig for 1 side
        Args:
        0)loc_center = (list) name of center ball
        1)ls_upVtx = (list) all position of uplid
        2)ls_downVtx = (list) all position of downlid
        3)suffix = (str)
        4)params = (list) center's position of up and down lid

        Returns:
        None
        """

        # Variables
        list_outer_up_slide_output = []
        list_outer_low_slide_output = []
        dict_between_bind_joint = {}

        grp_inner_aim_locator = pm.group(em=1,n="grp_inner_aim_locator",p=self.grp_loc_aim)


        # create locator for pivot , list upper locator , list lower locator
        loc_center = primitive.addLocator(self.grp_loc_aim,name=self.getName("pivot_loc"),m=self.guide.tra["root"])
        list_inner_up_aim_loc = create_aim_target_locator(list_pos=self.list_inner_upper_pos, name=f"loc_inner_up_aimTarget",parent=grp_inner_aim_locator)
        list_inner_low_aim_loc = create_aim_target_locator(list_pos=self.list_inner_lower_pos, name=f"loc_inner_low_aimTarget",parent=grp_inner_aim_locator)

        # create joint and aim joint to locators
        grp_inner_aim_joints = pm.group(em=1,n="inner_aim_joints_grp",p=self.grp_slide_joints)

        list_inner_up_slide_root,list_inner_up_slide_output = create_aim_joints(
            loc_center=loc_center,
            locators=list_inner_up_aim_loc,
            suffix=self.getName(),
            jnt_size=1,
            name="InUp",
            parent=grp_inner_aim_joints,
        )
        list_inner_low_slide_root,list_inner_low_slide_output = create_aim_joints(
            loc_center=loc_center,
            locators=list_inner_low_aim_loc,
            suffix=self.getName(),
            jnt_size=1,
            name="InLow",
            parent=grp_inner_aim_joints,
        )

        # create high curve which locators was pinned by them
        grp_inner_curve_transform = pm.group(em=1,n="grp_inner_curve",p=self.grp_eye_curves)
        grp_inner_curve_no_transform = pm.group(em=1,n="grp_inner_curve_still",p=self.grp_eye_curves_still)

        crv_inner_up_pin = Create.draw_curve(list_items=list_inner_up_aim_loc,
                                                curve_name=self.getName("InnerUpPinCrv"),
                                                parent=grp_inner_curve_no_transform,
                                                rebuild=False,
                                                d=1)

        crv_inner_low_pin = Create.draw_curve(list_items=list_inner_low_aim_loc,
                                                curve_name=self.getName("InnerLowPinCrv"),
                                                parent=grp_inner_curve_no_transform,
                                                rebuild=False,
                                                d=1)

        crv_inner_up_bind = Create.draw_curve(list_items=list_inner_up_aim_loc,
                                                curve_name=self.getName("InnerUpBindCrv"),
                                                parent=grp_inner_curve_no_transform,
                                                rebuild=True,
                                                d=3)

        crv_inner_low_bind = Create.draw_curve(list_items=list_inner_low_aim_loc,
                                                curve_name=self.getName("InnerLowBindCrv"),
                                                parent=grp_inner_curve_no_transform,
                                                rebuild=True,
                                                d=3)
        

        # pin target locator to pin curve
        Connection.pin_to_curve(
            list_pin=list_inner_up_aim_loc,
            curve=crv_inner_up_pin,
            maintain_offset=False,
            prevent_double_transform=True
        )

        Connection.pin_to_curve(
            list_pin=list_inner_low_aim_loc,
            curve=crv_inner_low_pin,
            maintain_offset=False,
            prevent_double_transform=True
        )

        # create wire deformer for up and down curve
        ls_wireUp = CreateWireCurve(
            crv_control=crv_inner_low_bind,
            crv_target=crv_inner_low_pin,
            name=f"WR_downLidHigh",
        )
        ls_wireDown = CreateWireCurve(
            crv_control=crv_inner_up_bind,
            crv_target=crv_inner_up_pin,
            name=f"WR_upLidHigh",
        )

        # create attribute to control
        pm.addAttr(self.main_ctrl, ln="blink", at="float", max=1, min=0, k=1)
        pm.addAttr(self.main_ctrl, ln="blinkHeight", at="float", max=10, min=0, k=1)

        attr_blink = "{}.blink".format(self.main_ctrl)
        attr_blink_height = "{}.blinkHeight".format(self.main_ctrl)

        # create blend shape and connect node
        crv_blinkHeight = CreateBlendShape(
            bln_child=[crv_inner_up_bind, crv_inner_low_bind],
            dup_crv=crv_inner_low_bind,
            name=f"_blinkHeight",
            attr_height=attr_blink_height,
        )

        # create wire and zero offset to up and down curve
        pm.setAttr(attr_blink_height, 10)
        if pm.getAttr(attr_blink_height) == 10:
            crv_UpBlink = pm.duplicate(crv_inner_up_pin, n=f"crv_UpBlink")
            wire_crv_blinkUp = CreateWireCurve(
                crv_UpBlink,
                crv_control=crv_blinkHeight,
                name=f"WR_crv_blinkUp",
                zeroOffset=1,
            )

        # set attribute height to 10
        pm.setAttr(attr_blink_height, 0)
        if pm.getAttr(attr_blink_height) == 0:
            crv_DownBlink = pm.duplicate(crv_inner_low_pin, n=f"crv_DownBlink")
            wire_crv_blinkDown = CreateWireCurve(
                crv_DownBlink,
                crv_control=crv_blinkHeight,
                name=f"WR_crv_blinkDown",
                zeroOffset=1,
            )

        # create blendshape for up,down blink to up,down high
        bsn_crv_UpBlink = pm.blendShape(
            crv_UpBlink, crv_inner_up_pin, n=f"BLN_upLidHigh"
        )[0]
        bsn_crv_DownBlink = pm.blendShape(
            crv_DownBlink, crv_inner_low_pin, n=f"BLN_downLidHigh"
        )[0]

        # connect blink attributes to blendshape
        pm.connectAttr(attr_blink, bsn_crv_UpBlink + ".weight[0]")
        pm.connectAttr(attr_blink, bsn_crv_DownBlink + ".weight[0]")

        # connect size of locator to dropoffDistance of wire deformer
        dcm_node_scale = pm.createNode("decomposeMatrix", name="dcm_dropoffDistance")
        pm.connectAttr(
            self.grp_transform + ".worldMatrix", dcm_node_scale + ".inputMatrix"
        )
        pm.connectAttr(
            dcm_node_scale + ".outputScale.outputScaleY",
            wire_crv_blinkUp + ".dropoffDistance[0]",
        )
        pm.connectAttr(
            dcm_node_scale + ".outputScale.outputScaleY",
            wire_crv_blinkDown + ".dropoffDistance[0]",
        )

        grp_inner_controller = pm.group(em=1,n=self.getName("InnerControl"),p=self.grp_controllers)
        list_inner_up_driver_joint, list_inner_low_driver_joint = create_driver_joints_v2(
            crv_up=crv_inner_up_bind,
            crv_down=crv_inner_low_bind,
            parent=grp_inner_controller,
            suffix="Inner",

        )

        # set parent
        pm.parent(
            crv_inner_up_bind, crv_inner_low_bind, crv_blinkHeight, self.grp_eye_curves_still
        )
        

        
        ################################################
        ########## Create Manual Close Blend Shape ######
        #################################################


        crv_inner_up_close = Create.draw_curve(list_items=list_inner_up_aim_loc,
                                                curve_name=self.getName("inner_up_close_crv"),
                                                parent=grp_inner_curve_no_transform,
                                                rebuild=True,
                                                d=3)
        crv_inner_low_close = Create.draw_curve(list_items=list_inner_low_aim_loc,
                                                curve_name=self.getName("inner_low_close_crv"),
                                                parent=grp_inner_curve_no_transform,
                                                rebuild=True,
                                                d=3)
        
        Transform.match_cvs(crv_inner_up_close,crv_inner_low_bind)
        Transform.match_cvs(crv_inner_low_close,crv_inner_up_bind)

        bsn_inner_up_close = pm.blendShape(crv_inner_up_close,crv_inner_up_bind,at=True,bf=True)[0]
        bsn_inner_low_close = pm.blendShape(crv_inner_low_close,crv_inner_low_bind,at=True,bf=True)[0]


        ################################################
        ########## Main Controller ##################
        #################################################

        loc_main_up_ctrl = primitive.addLocator(self.ctrl_main_up.getParent(),name=self.getName("mainUpLoc"),m=transform.getTransform(self.ctrl_main_up))
        loc_main_low_ctrl = primitive.addLocator(self.ctrl_main_low.getParent(),name=self.getName("mainLowLoc"),m=transform.getTransform(self.ctrl_main_low))
        # loc_main_in_ctrl = primitive.addLocator(self.main_in_ctrl.getParent(),name=self.getName("mainInLoc"),m=transform.getTransform(self.main_in_ctrl))
        # loc_main_out_ctrl = primitive.addLocator(self.main_out_ctrl.getParent(),name=self.getName("mainOutLoc"),m=transform.getTransform(self.main_out_ctrl))
        
        # list_constraint =[
        #     [loc_main_up_ctrl,list_inner_up_driver_joint[1]],
        #     [loc_main_up_ctrl,list_inner_up_driver_joint[2]],
        #     [loc_main_up_ctrl,list_inner_up_driver_joint[3]],
        #     [loc_main_low_ctrl,list_inner_low_driver_joint[0]],
        #     [loc_main_low_ctrl,list_inner_low_driver_joint[1]],
        #     [loc_main_low_ctrl,list_inner_low_driver_joint[2]],
        # ]

        # # loc main up
        # for list_data in list_constraint:
        #     objA,objB = list_data

        #     constraint_main = pm.parentConstraint(objA,objB,mo=True)
        #     pm.disconnectAttr("{}.parentInverseMatrix[0]".format(objB), "{}.constraintParentInverseMatrix".format(constraint_main))

        # Connection.connect(self.ctrl_main_up,loc_main_up_ctrl,typ="rotate")
        # pm.connectAttr(self.ctrl_main_up+".tx",loc_main_up_ctrl+".tx")
        # Connection.connect_conversion(
        #     input1=self.ctrl_main_up+".ty",
        #     conversion=-1,
        #     output="{}.{}".format(bsn_inner_up_close,crv_inner_up_close)
        # )

        # Connection.connect(self.ctrl_main_low,loc_main_low_ctrl,typ="rotate")
        # pm.connectAttr(self.ctrl_main_low+".tx",loc_main_low_ctrl+".tx")
        # Connection.connect_conversion(
        #     input1=self.ctrl_main_low+".ty",
        #     conversion=1,
        #     output="{}.{}".format(bsn_inner_low_close,crv_inner_low_close)
        # )

        ####################################
        ###### Outer rig ####################
        ####################################
        grp_outer_aim_locator = pm.group(em=1,n="outer_aim_locators_grp",p=self.grp_loc_aim)
        grp_outer_aim_joints = pm.group(em=1,n="outer_aim_joints_grp",p=self.grp_slide_joints)
        grp_outer_curve = pm.group(em=1,n="grp_outer_curve",p=self.grp_eye_curves)
        grp_outer_curve_no_transform = pm.group(em=1,n="grp_outer_curve_still",p=self.grp_eye_curves_still)

        list_outer_upper_aim_loc = create_aim_target_locator(list_pos=self.list_outer_upper_pos, name=f"loc_outer_up_aimTarget",parent=grp_outer_aim_locator)
        list_outer_lower_aim_loc = create_aim_target_locator(list_pos=self.list_outer_lower_pos, name=f"loc_outer_low_aimTarget",parent=grp_outer_aim_locator)

        list_outer_up_slide_root,list_outer_up_slide_output = create_aim_joints(
            loc_center=loc_center,
            locators=list_outer_upper_aim_loc,
            suffix=self.getName(),
            jnt_size=1,
            name="OutUp",
            parent=grp_outer_aim_joints,
        )

        list_outer_low_slide_root,list_outer_low_slide_output = create_aim_joints(
            loc_center=loc_center,
            locators=list_outer_lower_aim_loc,
            suffix=self.getName(),
            jnt_size=1,
            name="OutDown",
            parent=grp_outer_aim_joints,
        )

        # create pin curve and bind curve
        crv_outer_up_pin = Create.draw_curve(list_items=list_outer_upper_aim_loc,
                                                curve_name=self.getName("OuterUpPinCrv"),
                                                parent=grp_outer_curve_no_transform,
                                                rebuild=False,
                                                d=1)

        crv_outer_low_pin = Create.draw_curve(list_items=list_outer_lower_aim_loc,
                                                curve_name=self.getName("OuterLowPinCrv"),
                                                parent=grp_outer_curve_no_transform,
                                                rebuild=False,
                                                d=1)

        crv_outer_up_bind = Create.draw_curve(list_items=list_outer_upper_aim_loc,
                                                curve_name=self.getName("OuterUpBindCrv"),
                                                parent=grp_outer_curve_no_transform,
                                                rebuild=True,
                                                d=3)

        crv_outer_low_bind = Create.draw_curve(list_items=list_outer_lower_aim_loc,
                                                curve_name=self.getName("OuterLowBindCrv"),
                                                parent=grp_outer_curve_no_transform,
                                                rebuild=True,
                                                d=3)


        # pin target locator to pin curve
        Connection.pin_to_curve(
            list_pin=list_outer_upper_aim_loc,
            curve=crv_outer_up_pin,
            maintain_offset=False,
            prevent_double_transform=True
        )

        Connection.pin_to_curve(
            list_pin=list_outer_lower_aim_loc,
            curve=crv_outer_low_pin,
            maintain_offset=False,
            prevent_double_transform=True
        )

        # create wire deformer to make bind curve drive pin curve
        CreateWireCurve(
            crv_control=crv_outer_up_bind,
            crv_target=crv_outer_up_pin,
            name="upOuterPin_wire",
        )
        CreateWireCurve(
            crv_control=crv_outer_low_bind,
            crv_target=crv_outer_low_pin,
            name="lowOuterPin_wire",
        )

        # create controller for outer lid
        grp_outer_controller = pm.group(em=1,n=self.getName("OuterControl"),p=self.grp_controllers)

        create_driver_joints_v2(
            crv_up=crv_outer_up_bind,
            crv_down=crv_outer_low_bind,
            parent=grp_outer_controller,
            suffix="Outer"
        )



        #################################################
        ####### Between Constraint ######################
        ##################################################

        dict_between_bind_joint = {}
        dict_between_root_joint = {}
        pos_center = pm.xform(loc_center,q=1, ws=1, t=1)
        list_alphabet = list(string.ascii_uppercase)

        for i in range(self.between_joint_amount):
            grp_between_chain_joint = pm.group(em=1,n="{}_aim_joint_grp".format(list_alphabet[i]),p=self.grp_slide_joints)

            # Create aim joint
            key_name_up = "{}{}".format(list_alphabet[i],"Up")
            list_pos_tip = [pm.xform(locator,q=1,ws=1,t=1) for locator in self.dict_bind_loc[key_name_up]]
            dict_between_root_joint[key_name_up],dict_between_bind_joint[key_name_up]= create_joint_chain(
                pos_center=pos_center,
                list_pos_tip=list_pos_tip,
                name=key_name_up,
                parent=grp_between_chain_joint,
            )

            key_name_low = "{}{}".format(list_alphabet[i],"Low")
            list_pos_tip = [pm.xform(locator,q=1,ws=1,t=1) for locator in self.dict_bind_loc[key_name_low]]
            dict_between_root_joint[key_name_low],dict_between_bind_joint[key_name_low] = create_joint_chain(
                pos_center=pos_center,
                list_pos_tip=list_pos_tip,
                name=key_name_low,
                parent=grp_between_chain_joint)

            # Pair blend
            for j in range(len(list_outer_upper_aim_loc)):
                input_rot1 = list_inner_up_slide_root[j]+".rotate"
                input_rot2 = list_outer_up_slide_root[j]+".rotate"
                weight = (1/(2+1))*(i+1)

                print("input rot 1 : ",input_rot1)
                node_pair_blend = pm.createNode("pairBlend")

                pm.connectAttr(input_rot1,"{}.inRotate1".format(node_pair_blend))
                pm.connectAttr(input_rot2,"{}.inRotate2".format(node_pair_blend))

                pm.setAttr("{}.rotInterpolation".format(node_pair_blend),1)
                pm.setAttr("{}.weight".format(node_pair_blend),weight)

                pm.connectAttr("{}.outRotate".format(node_pair_blend),"{}.rotate".format(dict_between_root_joint[key_name_up][j]))

            for j in range(len(list_outer_lower_aim_loc)):
                input_rot1 = list_inner_low_slide_root[j]+".rotate"
                input_rot2 = list_outer_low_slide_root[j]+".rotate"
                weight = (1/(2+1))*(i+1)

                node_pair_blend = pm.createNode("pairBlend")

                pm.connectAttr(input_rot1,"{}.inRotate1".format(node_pair_blend))
                pm.connectAttr(input_rot2,"{}.inRotate2".format(node_pair_blend))

                pm.setAttr("{}.rotInterpolation".format(node_pair_blend),1)
                pm.setAttr("{}.weight".format(node_pair_blend),weight)

                pm.connectAttr("{}.outRotate".format(node_pair_blend),"{}.rotate".format(dict_between_root_joint[key_name_low][j]))

        parent_between_bind_locator()
        
        # bind to locator
        connect_to_bind_locator()

        # Set visibility
        self.grp_loc_aim.visibility.set(False)
        self.grp_slide_joints.visibility.set(False)


    def setRelation(self):
        """Set the relation beetween object from guide to rig"""

        self.relatives["root"] = self.dict_bind_loc["root"]
        self.jointRelatives["root"] = 0

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
