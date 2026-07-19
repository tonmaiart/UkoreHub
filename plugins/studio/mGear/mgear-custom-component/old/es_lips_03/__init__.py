import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from TonmaiToolkit.utils import match_parent
from mgear.rigbits.facial_rigger.constraints import namePrefix
from mgear.shifter import component, log_window
import math
import maya.api.OpenMaya as om
from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive
import math
from TonmaiToolkit import utils


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""



        # User Setting Input
        self.slide_plane = self.settings["sliding_object"]
        self.enable_extra_loop = self.settings["extra_loop"]
        self.enable_auto_pinch = self.settings["auto_pinch"]
        self.enable_slide_plane = self.settings["enable_sliding"]
        self.extra_loop_amount = self.settings["loop_amount"]
        self.enable_slide_orient = True

        # Create Hierarchy Groups
        self.nurbs_plane_loop = None

        self.grp_no_transform = pm.group(em=1,n=self.getName("no_transform_grp"),p=self.root)
        self.grp_no_transform.inheritsTransform.set(False)

        self.grp_control = pm.group(em=1,n=self.getName("all_control_grp"))
        pm.parent(self.grp_control,self.root)

        self.grp_joint_main = pm.group(em=1,n=self.getName("joint_driver_grp"),p=self.grp_no_transform)

        self.grp_bind_loc = pm.group(em=1,n=self.getName("loc_bind_grp"),p=self.grp_no_transform)
        self.grp_slide_locator_aim = pm.group(em=1,n=self.getName("loc_aim_grp"),p=self.grp_no_transform)
        self.grp_slide_locator_result = pm.group(em=1,n=self.getName("loc_slide_grp"),p=self.grp_no_transform)

        self.grp_extra_bind_loc = pm.group(em=1, n=self.getName("loc_extra_bind_grp"), p=self.grp_no_transform)
        self.grp_extra_slide_locator_aim = pm.group(em=1, n=self.getName("loc_extra_aim_grp"), p=self.grp_no_transform)
        self.grp_extra_slide_locator_result = pm.group(em=1, n=self.getName("loc_extra_slide_grp"), p=self.grp_no_transform)

        self.grp_corner_loc = pm.group(em=1, n=self.getName("loc_corner_grp"), p=self.grp_no_transform)

        self.grp_dummy_joints = pm.group(em=1,n=self.getName("dummy_joint_grp"),p=self.grp_no_transform)
        # Build Variables
        self.loop_blend_factor = 1/self.extra_loop_amount

        self.curve_lip_main = None
        self.curve_lip_mid = None

        self.dict_main = {"upper_control":[],
                          "lower_control":[],
                          "upper_joint":[],
                          "lower_joint":[],
                          "upper_name":["L_main","up_main","R_main"],
                          "lower_name":["low_main"]
                          }

        self.dict_mid = {"upper_control":[],
                         "lower_control":[],
                         "upper_joint":[],
                         "lower_joint":[],
                         "upper_name":["R_up_corner","R_up","C_up","L_up","L_up_corner"],
                         "lower_name":["R_low","C_low","L_low"]
                         }

        self.dict_rim = {"upper_control": [],
                         "lower_control": [],
                         "upper_joint": [],
                         "lower_joint": [],
                         "upper_name": [text for text in self.guide.tra.keys() if "up_rim" in text],
                         "lower_name": [text for text in self.guide.tra.keys() if "low_rim" in text],
                         "upper_pin": [],
                         "lower_pin": [],
                         "upper_piv": [text for text in self.guide.tra.keys() if "up_piv" in text],
                         "lower_piv": [text for text in self.guide.tra.keys() if "low_piv" in text],
                         "upper_piv_m":[],
                         "lower_piv_m": [],
                         }

        for key in self.guide.tra.keys():
            if "up_piv" in key:
                self.dict_rim["upper_piv_m"].append(self.guide.tra[key])
            elif "low_piv" in key:
                self.dict_rim["lower_piv_m"].append(self.guide.tra[key])

        self.dict_sub = {
            "01":{"upper_control":[],"lower_control":[],"upper_joint":[],"lower_joint":[],
                  "upper_name":[text for text in self.guide.tra.keys() if "up_01" in text],
                  "lower_name":[text for text in self.guide.tra.keys() if "low_01" in text],"upper_pin":[],"lower_pin":[]},
            "02": {"upper_control": [], "lower_control": [], "upper_joint": [], "lower_joint": [],
                   "upper_name": [text for text in self.guide.tra.keys() if "up_02" in text],
                   "lower_name": [text for text in self.guide.tra.keys() if "low_02" in text],"upper_pin":[],"lower_pin":[]},
            "03": {"upper_control": [], "lower_control": [], "upper_joint": [], "lower_joint": [],
                   "upper_name": [text for text in self.guide.tra.keys() if "up_03" in text],
                   "lower_name": [text for text in self.guide.tra.keys() if "low_03" in text],"upper_pin":[],"lower_pin":[]}
        }


        self.dict_corner = {"upper_corner":[],
                            "upper_corner_m":[],
                            "lower_corner":[],
                            "lower_corner_m":[]
                            }

        for key in self.guide.tra.keys():
            if "up_corner" in key:
                self.dict_corner["upper_corner"].append(primitive.addLocator(self.grp_corner_loc,key+"_loc",m=self.guide.tra[key]))
                self.dict_corner["upper_corner_m"].append(self.guide.tra[key])
            elif "low_corner" in key:
                self.dict_corner["lower_corner"].append(primitive.addLocator(self.grp_corner_loc,key+"_loc",m=self.guide.tra[key]))
                self.dict_corner["lower_corner_m"].append(self.guide.tra[key])


        # create extra dict
        self.dict_extra = {}

        if self.enable_extra_loop:
            for i in range(self.extra_loop_amount):
                self.dict_extra[i] = {"upper_control": [],
                                      "lower_control": [],
                                      "upper_joint": [],
                                      "lower_joint": [],
                                      "upper_name": ["up_corner_{}_{}".format(i+1,j+1) for j in range(7)],
                                      "lower_name": ["low_corner_{}_{}".format(i+1,j+1) for j in range(5)],
                                      "upper_pin":[],
                                      "lower_pin":[]}

        def create_bind_joints():
            def create_extra_loop():
                if not self.enable_extra_loop:
                    return

                for loop_count in range(self.extra_loop_amount):
                    list_joint_rim = self.dict_rim["upper_joint"] + self.dict_rim["lower_joint"]
                    list_corner_guide = self.dict_corner["upper_corner"]+self.dict_corner["lower_corner"]
                    list_name = self.dict_extra[loop_count]["upper_name"] + self.dict_extra[loop_count]["lower_name"]

                    # create locator and snap position
                    for i,name in enumerate(list_name):
                        locator = primitive.addLocator(self.grp_extra_bind_loc, self.getName("{}_loc".format(name)), m=transform.getTransformFromPos((0,0,0)))

                        # snap position
                        utils.transform_to_between_object(list_joint_rim[i], list_corner_guide[i], locator, percentage=loop_count * self.loop_blend_factor)

                        if name in self.dict_extra[loop_count]["upper_name"]:
                            self.dict_extra[loop_count]["upper_joint"].append(locator)
                        elif name in self.dict_extra[loop_count]["lower_name"]:
                            self.dict_extra[loop_count]["lower_joint"].append(locator)

                    # create joint
                    for i, locator in enumerate(self.dict_extra[loop_count]["upper_joint"] + self.dict_extra[loop_count]["lower_joint"]):
                        self.jnt_pos.append({
                            "obj": locator,
                            "name": list_name[i],
                            "newActiveJnt": False,
                            "gearMulMatrix": False,
                            "vanilla_nodes": True
                        })

            # create local base joint
            self.jnt_pos.append({
                "obj": primitive.addLocator(self.grp_bind_loc, self.getName("base_loc"), m=transform.getTransform(self.root)),
                "name": "base",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True
            })

            # create rim joint
            list_name = self.dict_rim["upper_name"]+self.dict_rim["lower_name"]

            # create locator and update to dict rim joint
            for name in list_name:
                m_pos = transform.getTransformFromPos(self.guide.pos[name])

                if name in self.dict_rim["upper_name"]:
                    self.dict_rim["upper_joint"].append(
                        primitive.addLocator(self.grp_bind_loc, self.getName("{}_loc".format(name)), m=m_pos)
                    )
                elif name in self.dict_rim["lower_name"]:
                    self.dict_rim["lower_joint"].append(
                        primitive.addLocator(self.grp_bind_loc, self.getName("{}_loc".format(name)), m=m_pos)
                    )

            # create joint
            for i,locator in enumerate(self.dict_rim["upper_joint"]+self.dict_rim["lower_joint"]):
                self.jnt_pos.append({
                    "obj": locator,
                    "name": list_name[i],
                    "newActiveJnt": False,
                    "gearMulMatrix": False,
                    "vanilla_nodes": True
                })

            # create jaw loc
            self.loc_jaw = primitive.addLocator(self.grp_bind_loc, self.getName("jaw_loc"), m=transform.setMatrixScale(self.guide.tra["jaw"],(1,1,1)))
            mgear.rigbits.addNPO([self.loc_jaw])

            self.jnt_pos.append({
                "obj": self.loc_jaw,
                "name": "jaw",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True
            })

            # create inner loc
            self.loc_inner = primitive.addLocator(self.grp_bind_loc, self.getName("inner_loc"), m=transform.setMatrixScale(self.guide.tra["inner"],(1,1,1)))
            mgear.rigbits.addNPO([self.loc_inner])

            self.jnt_pos.append({
                "obj": self.loc_inner,
                "name": "inner",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True
            })

            # create extra loop joint
            create_extra_loop()

        def create_curve():
            """
            Create Curve for driven rim joints
            """

            # get position
            list_upper_pos = []
            for name in self.dict_rim["upper_name"]:
                list_upper_pos.append(self.guide.pos[name])

            list_lower_pos = []
            for name in self.dict_rim["lower_name"]:
                list_lower_pos.append(self.guide.pos[name])

            list_all_post = list_upper_pos+list_lower_pos[::-1]

            # create curve
            self.curve_lip_main  = pm.circle(n=self.getName("main_crv"),s=len(list_all_post),d=3,ch=0)[0]
            self.curve_lip_main.setParent(self.grp_no_transform)

            # snap position
            for i,pos in enumerate(list_all_post):
                pm.xform("{}.cv[{}]".format(self.curve_lip_main,i),ws=1,t=pos)

        def create_main_joint():
            """

            Create Main Joint that will bind to drive curve.

            """

            # create main joint
            self.L_main_joint = pm.joint(name=self.getName("L_main_jnt"))
            pm.select(cl=0)

            self.R_main_joint = pm.joint(name=self.getName("R_main_jnt"))
            pm.select(cl=0)

            self.up_main_joint = pm.joint(name=self.getName("up_main_jnt"))
            pm.select(cl=0)

            self.low_main_joint = pm.joint(name=self.getName("low_main_jnt"))
            pm.select(cl=0)

            # snap position L,R
            pm.xform(self.L_main_joint,ws=1,m=transform.getTransform(self.dict_rim["upper_joint"][-1]))
            pm.xform(self.R_main_joint,ws=1,m=transform.getTransform(self.dict_rim["upper_joint"][0]))

            # snap position Up,Low
            for list_data in [["upper_joint",self.up_main_joint],["lower_joint",self.low_main_joint]]:
                part,joint = list_data

                if len(self.dict_rim[part])%2 == 0:
                    loc = pm.spaceLocator()
                    i = int(len(self.dict_rim[part])/2)
                    pm.pointConstraint(self.dict_rim[part][i],self.dict_rim[part][i-1],loc)

                    m_pos = transform.getTransform(loc)
                    pm.delete(loc)
                else:
                    i = math.floor(len(self.dict_rim[part])/2)
                    m_pos = transform.getTransform(self.dict_rim[part][i])

                pm.xform(joint,ws=1,m=m_pos)

            # update value to dict main
            self.dict_main["upper_joint"] = [self.L_main_joint,self.up_main_joint,self.R_main_joint]
            self.dict_main["lower_joint"] = [self.low_main_joint]

            # parent to joint main grp
            pm.parent(self.dict_main["upper_joint"]+self.dict_main["lower_joint"],self.grp_joint_main)

        def create_control_set():
            def create_sub_control():
                speed = 0.2

                list_pos = [(-1.5, 0, 0), (-1, 0.25, 0),(-0.7, 0.25, 0), (0, 0.25, 0), (0.7, 0.25, 0),(1, 0.25, 0), (1.5, 0, 0)]
                for i in range(len(self.dict_rim["upper_name"])):
                    control = self.addCtl(self.ctrl_big,
                                          self.getName(self.dict_rim["upper_name"][i]),
                                          m=transform.getTransformFromPos(list_pos[i]),
                                          color=9,
                                          iconShape="cube",
                                          w=0.15 * self.size,
                                          h=0.15 * self.size,
                                          d=0.15 * self.size
                                          )

                    control.scale.set(speed,speed,speed)

                    self.dict_rim["upper_control"].append(control)

                list_pos = [(-1, -0.25, 0),(-0.7, -0.25, 0), (0, -0.25, 0), (0.7, -0.25, 0),(1, -0.25, 0)]

                for i in range(len(self.dict_rim["lower_name"])):
                    control = self.addCtl(self.ctrl_big,
                                          self.getName(self.dict_rim["lower_name"][i]),
                                          m=transform.getTransformFromPos(list_pos[i]),
                                          color=9,
                                          iconShape="cube",
                                          w=0.15 * self.size,
                                          h=0.15 * self.size,
                                          d=0.15 * self.size
                                          )
                    control.scale.set(speed,speed,speed)

                    self.dict_rim["lower_control"].append(control)

            def create_big_control():
                # create big control
                self.ctrl_big = self.addCtl(self.grp_control,
                                            "mouth_box",
                                            m=transform.getTransform(self.grp_control),
                                            color=16,
                                            iconShape="square",
                                            )

            def create_main_control():
                # create main controller
                for list_name in [self.dict_main["upper_name"], self.dict_main["lower_name"]]:
                    if list_name == self.dict_main["upper_name"]:
                        list_pos = [(1.5, 0, 0), (0, 0.5, 0), (-1.5, 0, 0)]
                    elif list_name == self.dict_main["lower_name"]:
                        list_pos = [(0, -0.5, 0)]

                    list_control = []

                    for i, name in enumerate(list_name):
                        control = self.addCtl(self.ctrl_big,
                                              name,
                                              m=transform.getTransformFromPos(list_pos[i]),
                                              color=17,
                                              iconShape="square",
                                              w=0.2 * self.size,
                                              h=0.2 * self.size,
                                              d=0.2 * self.size
                                              )
                        list_control.append(control)
                        control.scale.set(0.5, 0.5, 0.5)

                    if list_name == self.dict_main["upper_name"]:
                        self.dict_main["upper_control"] = list_control
                    elif list_name == self.dict_main["lower_name"]:
                        self.dict_main["lower_control"] = list_control


            create_big_control()
            create_main_control()
            create_sub_control()

            # add npo
            mgear.rigbits.addNPO([self.ctrl_big]+self.dict_main["upper_control"]+self.dict_main["lower_control"]+self.dict_rim["upper_control"]+self.dict_rim["lower_control"])

            # parent sub control to main control
            for i in range(4):
                if i == 0: # L
                    list_control = self.dict_rim["upper_control"][4:]+self.dict_rim["lower_control"][3:]
                    list_control_npo = [control.getParent() for control in list_control]
                    ctrl_main = self.dict_main["upper_control"][0]
                    name = "L"

                elif i == 1: # R
                    list_control = self.dict_rim["upper_control"][0:3] + self.dict_rim["lower_control"][0:2]
                    list_control_npo = [control.getParent() for control in list_control]
                    ctrl_main = self.dict_main["upper_control"][2]
                    name = "R"

                elif i == 2: # UP
                    list_control = [self.dict_rim["upper_control"][3]]
                    list_control_npo = [control.getParent() for control in list_control]
                    ctrl_main = self.dict_main["upper_control"][1]
                    name = "up"

                elif i == 3:  # LOW
                    list_control = [self.dict_rim["lower_control"][2]]
                    list_control_npo = [control.getParent() for control in list_control]
                    ctrl_main = self.dict_main["lower_control"][0]
                    name = "low"

                pm.parent(list_control_npo,ctrl_main)

                node_pm = pm.createNode("pickMatrix",n=self.getName("{}_inverse_pm".format(name)))

                node_pm.useTranslate.set(False)

                pm.connectAttr("{}.inverseMatrix".format(ctrl_main),"{}.inputMatrix".format(node_pm))

                for grp_npo in list_control_npo:
                    pm.connectAttr("{}.outputMatrix".format(node_pm),"{}.offsetParentMatrix".format(grp_npo))

            # snap big controller
            pm.xform(self.ctrl_big.getParent(),ws=1,m=self.guide.tra["controller"])


        def create_jaw_ctl():
            # create controller
            self.ctrl_jaw = self.addCtl(self.grp_control,
                                  "jaw",
                                  m=transform.setMatrixScale(self.guide.tra["jaw"],(1,1,1)),
                                  color=17,
                                  iconShape="square",
                                  w=0.6 * self.size,
                                  h=0.6 * self.size,
                                  d=0.6 * self.size
                                  )
            mgear.rigbits.addNPO([self.ctrl_jaw])

            # direct connection control to locator
            pm.connectAttr("{}.t".format(self.ctrl_jaw),"{}.t".format(self.loc_jaw))
            pm.connectAttr("{}.r".format(self.ctrl_jaw),"{}.r".format(self.loc_jaw))
            pm.connectAttr("{}.s".format(self.ctrl_jaw),"{}.s".format(self.loc_jaw))
        def create_inner_ctl():
            # create controller
            self.ctrl_inner = self.addCtl(self.grp_control,
                                  "inner",
                                  m=transform.setMatrixScale(self.guide.tra["inner"],(1,1,1)),
                                  color=17,
                                  iconShape="cube",
                                  w=0.4 * self.size,
                                  h=0.4 * self.size,
                                  d=0.4 * self.size
                                  )
            mgear.rigbits.addNPO([self.ctrl_inner])

            # direct connection control to locator
            pm.connectAttr("{}.t".format(self.ctrl_inner),"{}.t".format(self.loc_inner))
            pm.connectAttr("{}.r".format(self.ctrl_inner),"{}.r".format(self.loc_inner))
            pm.connectAttr("{}.s".format(self.ctrl_inner),"{}.s".format(self.loc_inner))

        def create_nurbs_plane_loop():
            if not self.enable_extra_loop:
                return

            list_crv = []
            list_key = [0,self.extra_loop_amount-1]

            for key in list_key:
                list_position = []

                for joint in self.dict_extra[key]["upper_joint"]+self.dict_extra[key]["lower_joint"][::-1]:
                    list_position.append(pm.xform(joint,q=1,ws=1,t=1))

                # create curve
                curve = pm.circle(n=self.getName("loop_crv"), s=len(list_position), d=3, ch=0)[0]
                curve.setParent(self.grp_no_transform)

                # snap position
                for key, pos in enumerate(list_position):
                    pm.xform("{}.cv[{}]".format(curve, key), ws=1, t=pos)

                # append curve
                list_crv.append(curve)

            # loft
            self.nurbs_plane_loop =  pm.loft(list_crv,ch=0,n="plane_loop_nurbs",d=1)[0]
            self.nurbs_plane_loop.setParent(self.grp_no_transform)
            print(self.nurbs_plane_loop)

        create_curve()

        create_bind_joints()

        create_main_joint()

        create_control_set()

        create_jaw_ctl()
        create_inner_ctl()

        create_nurbs_plane_loop()

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        def create_uv_pin_curve_node():
            self.node_uvPin_curve = pm.createNode("uvPin", n=self.getName("curve_uvPin"))
            self.node_uvPin_curve.normalizedIsoParms.set(False)
            pm.connectAttr("{}.worldSpace[0]".format(self.curve_lip_main),
                           "{}.deformedGeometry".format(self.node_uvPin_curve))
            self.index_uvPin_curve = 0

        def create_uv_pin_surface_node():
            if not self.enable_slide_plane: # ( if slide plane not enable )
                return

            if not pm.objectType(pm.listRelatives(self.slide_plane,c=1,s=1)[0],isa="nurbsSurface"):
                pm.error("Slide Plane must be nurbsSurface")


            self.node_uvPin_surface = pm.createNode("uvPin",n=self.getName("surface_uvPin"))
            self.node_uvPin_surface.normalizedIsoParms.set(False)
            pm.connectAttr("{}.worldSpace[0]".format(self.slide_plane),"{}.deformedGeometry".format(self.node_uvPin_surface))
            self.index_uvPin_surface = 0

        def create_uv_pin_surface_loop_node():
            if not self.enable_extra_loop: # ( if slide plane not enable )
                return

            self.node_uvPin_loop = pm.createNode("uvPin",n=self.getName("surface_uvPin"))
            self.node_uvPin_loop.normalizedIsoParms.set(False)
            pm.connectAttr("{}.worldSpace[0]".format(self.nurbs_plane_loop),"{}.deformedGeometry".format(self.node_uvPin_loop))
            self.index_uvPin_loop = 0

        def create_jaw_between_attr_matrix():
            # create node blend jaw 0.5
            node_bm_jaw = pm.createNode("blendMatrix", n=self.getName("jaw_between_bm"))
            node_mm_jaw_between = pm.createNode("multMatrix", n=self.getName("jaw_between_offset_mm"))

            pm.connectAttr("{}.worldMatrix".format(self.ctrl_jaw),
                           "{}.target[0].targetMatrix".format(node_bm_jaw))
            pm.setAttr("{}.target[0].weight".format(node_bm_jaw), 0.5)

            m_current = om.MMatrix(pm.getAttr("{}.outputMatrix".format(node_bm_jaw)))
            m_target = om.MMatrix(transform.setMatrixScale(self.guide.tra["jaw"],(1,1,1)))
            m_offset = m_current.inverse()*m_target

            pm.setAttr("{}.matrixIn[1]".format(node_mm_jaw_between), m_offset,typ="matrix")
            pm.connectAttr("{}.outputMatrix".format(node_bm_jaw), "{}.matrixIn[0]".format(node_mm_jaw_between))

            return "{}.matrixSum".format(node_mm_jaw_between)

        def create_attr_big_control_transform():
            # create node big rotate
            node_mm_big_rotate = pm.createNode("multMatrix",n=self.getName("big_rotate_mm"))
            node_pm_big_rotate = pm.createNode("pickMatrix", n=self.getName("big_rotate_pm"))

            node_pm_big_rotate.useTranslate.set(False)
            node_pm_big_rotate.useScale.set(False)
            node_pm_big_rotate.useShear.set(False)

            pm.connectAttr("{}.matrix".format(self.ctrl_big), "{}.inputMatrix".format(node_pm_big_rotate))
            pm.connectAttr("{}.outputMatrix".format(node_pm_big_rotate),"{}.matrixIn[0]".format(node_mm_big_rotate))
            pm.setAttr("{}.matrixIn[1]".format(node_mm_big_rotate),transform.setMatrixScale(self.guide.tra["root"],(1,1,1)))

            return "{}.matrixSum".format(node_mm_big_rotate)

        def create_sliding_locator():

            factor = 1/3

            # create layer pin aim
            for index,part in enumerate(self.list_part):
                list_joint = self.dict_sub[part]["upper_joint"]+self.dict_sub[part]["lower_joint"]
                list_locator = []

                for i,name in enumerate(self.dict_sub[part]["upper_name"]+self.dict_sub[part]["lower_name"]):
                    control = (self.dict_rim["upper_control"] + self.dict_rim["lower_control"])[i]
                    joint_bind = list_joint[i]

                    # CREATE AIM LOC --------------------
                    loc_aim = pm.spaceLocator(n="{}_aim_loc".format(name))
                    list_locator.append(loc_aim)
                    loc_aim.setParent(self.grp_slide_locator_aim)

                    pm.matchTransform(loc_aim,joint_bind)

                    if part == "01": # connect pin position directly
                        node_pma = pm.createNode("plusMinusAverage")
                        node_dm_get_surface_pos = pm.createNode("decomposeMatrix",n=self.getName("{}_get_surface_pos".format(name)))

                        # get slide pos
                        pm.setAttr("{}.coordinate[{}].coordinateU".format(self.node_uvPin_curve,self.index_uvPin_curve),get_closest_param(str(loc_aim),str(self.curve_lip_main)))

                        pm.connectAttr("{}.outputMatrix[{}]".format(self.node_uvPin_curve,self.index_uvPin_curve),"{}.inputMatrix".format(node_dm_get_surface_pos))
                        pm.connectAttr("{}.outputTranslate".format(node_dm_get_surface_pos), "{}.input3D[0]".format(node_pma))

                        # get control pos
                        node_dm_get_ctrl_pos = pm.createNode("decomposeMatrix",n=self.getName("{}_get_ctrl_pos".format(name)))

                        pm.connectAttr("{}.matrix".format(control),"{}.inputMatrix".format(node_dm_get_ctrl_pos))

                        pm.connectAttr("{}.outputTranslateX".format(node_dm_get_ctrl_pos),"{}.input3D[1].input3Dx".format(node_pma))
                        pm.connectAttr("{}.outputTranslateY".format(node_dm_get_ctrl_pos),"{}.input3D[1].input3Dy".format(node_pma))

                        # apply
                        pm.connectAttr("{}.output3D".format(node_pma),"{}.translate".format(loc_aim))

                        self.index_uvPin_curve+=1

                    else: # constraint percentage
                        list_01_loc = self.dict_rim["upper_pin"] + self.dict_rim["lower_pin"]
                        list_name = self.dict_sub[part]["upper_name"]+self.dict_sub[part]["lower_name"]

                        # blend matrix
                        node_bm = pm.createNode("blendMatrix",n=self.getName("{}_blend_bm".format(name)))
                        node_mm_offset = pm.createNode("multMatrix",n=self.getName("{}_blend_offset_mm".format(name)))

                        target_01 = list_01_loc[i]
                        target_output = loc_aim


                        pm.connectAttr("{}.worldMatrix".format(target_01),"{}.target[0].targetMatrix".format(node_bm))
                        pm.setAttr("{}.target[0].weight".format(node_bm),0.5)

                        pm.connectAttr("{}.outputMatrix".format(node_bm),"{}.matrixIn[0]".format(node_mm_offset))
                        pm.connectAttr("{}.matrixSum".format(node_mm_offset),"{}.offsetParentMatrix".format(target_output))

                        attribute.reset_SRT([target_output])

                        # Example matrices
                        m_target = om.MMatrix(self.guide.tra[list_name[i]])
                        m_between = om.MMatrix(pm.getAttr("{}.outputMatrix".format(node_bm)))

                        result = m_between.inverse()*m_target
                        result = [value for value in result]

                        pm.setAttr("{}.matrixIn[1]".format(node_mm_offset),result,typ="matrix")


                    # CREASE SLIDING PIN RESULT (CONNECT TO SLIDE LOCATOR )--------------------
                    loc_result = pm.spaceLocator(n="{}_slide_loc".format(name))

                    # prepare offset group
                    pm.parent(loc_result,self.grp_slide_locator_result)

                    if self.enable_slide_plane:
                        node_cpos = pm.createNode("closestPointOnSurface",n=self.getName("{}_closest_point_cpos".format(name)))
                        node_pm = pm.createNode("pickMatrix", n=self.getName("{}_get_pos_matrix_pm".format(name)))
                        node_get_translate = pm.createNode("decomposeMatrix",n=self.getName("{}_get_translate_dm".format(name)))

                        # connection input  --------
                        pm.connectAttr("{}.worldMatrix[0]".format(loc_aim), "{}.inputMatrix".format(node_get_translate))

                        pm.connectAttr("{}.outputTranslate".format(node_get_translate),"{}.inPosition".format(node_cpos))
                        pm.connectAttr("{}.worldSpace[0]".format(self.slide_plane), "{}.inputSurface".format(node_cpos))

                        # get uv pin ---------------
                        pm.connectAttr("{}.parameterU".format(node_cpos),"{}.coordinate[{}].coordinateU".format(self.node_uvPin_surface,self.index_uvPin_surface))
                        pm.connectAttr("{}.parameterV".format(node_cpos),"{}.coordinate[{}].coordinateV".format(self.node_uvPin_surface,self.index_uvPin_surface))

                        pm.connectAttr("{}.outputMatrix[{}]".format(self.node_uvPin_surface,self.index_uvPin_surface),"{}.inputMatrix".format(node_pm))

                        self.index_uvPin_surface+=1

                        node_pm.useRotate.set(False)
                        node_pm.useShear.set(False)
                        node_pm.useScale.set(False)

                        attr_translate = "{}.outputMatrix".format(node_pm)
                    else:
                        node_pm = pm.createNode("pickMatrix", n=self.getName("{}_get_pos_matrix_pm".format(name)))

                        # connection input  --------
                        pm.connectAttr("{}.worldMatrix[0]".format(loc_aim),"{}.inputMatrix".format(node_pm))

                        node_pm.useRotate.set(False)
                        node_pm.useShear.set(False)
                        node_pm.useScale.set(False)

                        attr_translate = "{}.outputMatrix".format(node_pm)

                    if part == "01":
                        node_mm_output = pm.createNode("multMatrix",n=self.getName("{}_output_slide_mm".format(name)))

                        if self.enable_slide_plane:
                            # CTRL MAIN > LOC RESULT
                            node_cm = pm.createNode("composeMatrix",n=self.getName("{}_get_tz_cm".format(name)))

                            pm.connectAttr("{}.tz".format(control),"{}.inputTranslateZ".format(node_cm))
                            pm.connectAttr("{}.outputMatrix".format(node_cm),"{}.matrixIn[0]".format(node_mm_output))

                        # CTRL MAIN > SUB JOINT NPO
                        node_pm_rot = pm.createNode("pickMatrix",n=self.getName("{}_pick_rotate_pm".format(name)))

                        pm.connectAttr("{}.matrix".format(control),"{}.inputMatrix".format(node_pm_rot))
                        node_pm_rot.useTranslate.set(False)
                        node_pm_rot.useScale.set(False)
                        node_pm_rot.useShear.set(False)

                        pm.connectAttr("{}.outputMatrix".format(node_pm_rot),"{}.matrixIn[1]".format(node_mm_output))

                        pm.connectAttr(attr_translate,"{}.matrixIn[2]".format(node_mm_output))

                        pm.connectAttr("{}.matrixSum".format(node_mm_output),"{}.offsetParentMatrix".format(loc_result))

                        # CTRL MAIN > SUB JOINT (rotate roll m,b mouth)
                        list_loc_bind = self.dict_rim["upper_joint"]+self.dict_rim["lower_joint"]
                        if name in self.dict_rim["upper_name"]:
                            if i != 0 and i != len(self.dict_sub[part]["upper_control"])-1:
                                pm.connectAttr("{}.rx".format(self.dict_main["upper_control"][1]),"{}.rx".format(list_loc_bind[i]))

                        elif name in self.dict_rim["lower_name"]:
                            pm.connectAttr("{}.rx".format(self.dict_main["lower_control"][0]),
                                           "{}.rx".format(list_loc_bind[i]))

                    else:
                        pm.connectAttr(attr_translate,"{}.offsetParentMatrix".format(loc_result))

                    # LOC RESULT > LOCATOR BIND (01,02,03)
                    if part == "01": # Add extra controller behaviour
                        def connect_locator_orient(i):
                            node_pm_jaw_rotate = pm.createNode("pickMatrix",n=self.getName("{}_get_jaw_orient_pm".format(name)))

                            node_pm_jaw_rotate.useScale.set(False)
                            node_pm_jaw_rotate.useShear.set(False)

                            if name in self.dict_sub[part]["lower_name"]:
                                pm.connectAttr("{}.worldMatrix".format(self.loc_jaw),"{}.inputMatrix".format(node_pm_jaw_rotate))
                                node_pm_jaw_rotate.useTranslate.set(False)
                            elif name == self.dict_sub[part]["upper_name"][0] or name == self.dict_sub[part]["upper_name"][-1]:
                                pm.connectAttr(self.attr_m_jaw_between,"{}.inputMatrix".format(node_pm_jaw_rotate))
                                node_pm_jaw_rotate.useTranslate.set(False)

                            attr_jaw_transform = "{}.outputMatrix".format(node_pm_jaw_rotate)

                            pm.connectAttr(attr_jaw_transform,"{}.matrixIn[{}]".format(node_mm_result,i))

                        def connect_big_ctrl_scl(i):
                            pm.connectAttr(self.dict_scale_big[joint_bind],"{}.matrixIn[{}]".format(node_mm_result,i))


                        def connect_locator_position(i):
                            pm.connectAttr("{}.worldMatrix[0]".format(loc_result),"{}.matrixIn[{}]".format(node_mm_result,i))

                        def connect_main_ctrl_tz(i):
                            # CONNECT MAIN TZ (main push in,out)
                            node_cm_push = pm.createNode("composeMatrix",n=self.getName("{}_main_push_pos_cm".format(name,i)))

                            if name in self.dict_rim["upper_name"]:
                                if i == 0:
                                    pm.connectAttr("{}.tz".format(self.dict_main["upper_control"][2]),"{}.inputTranslateZ".format(node_cm_push))
                                elif i == len(self.dict_sub[part]["upper_control"])-1:
                                    pm.connectAttr("{}.tz".format(self.dict_main["upper_control"][0]),"{}.inputTranslateZ".format(node_cm_push))
                                else:
                                    pm.connectAttr("{}.tz".format(self.dict_main["upper_control"][1]),"{}.inputTranslateZ".format(node_cm_push))

                            elif name in self.dict_rim["lower_name"]:
                                pm.connectAttr("{}.tz".format(self.dict_main["lower_control"][0]),"{}.inputTranslateZ".format(node_cm_push))

                            pm.connectAttr("{}.outputMatrix".format(node_cm_push),"{}.matrixIn[{}]".format(node_mm_result,i))

                        def connect_big_ctrl_tz(i):
                            # CONNECT BIG TZ (big push in,out)
                            node_cm_push_big = pm.createNode("composeMatrix",n=self.getName("{}_big_push_cm".format(name)))

                            pm.connectAttr("{}.tz".format(self.ctrl_big),"{}.inputTranslateZ".format(node_cm_push_big))
                            pm.connectAttr("{}.outputMatrix".format(node_cm_push_big),"{}.matrixIn[{}]".format(node_mm_result,i))

                        def connect_manual_pinch_orient(i):
                            # CONNECT MANUAL PINCH ORIENT
                            if control in self.dict_manual_pinch.keys():
                                pm.connectAttr(self.dict_manual_pinch[control],"{}.matrixIn[{}]".format(node_mm_result,i))

                        def connect_auto_pinch_orient(i):
                            if self.enable_auto_pinch:
                                if control in self.dict_auto_pinch.keys():
                                    pm.connectAttr(self.dict_auto_pinch[control],"{}.matrixIn[{}]".format(node_mm_result,i))

                        # connect to mult matrix node
                        node_mm_result = pm.createNode("multMatrix",n=self.getName("{}_result_mm".format(name)))

                        list_order = [
                            connect_locator_orient,
                            connect_locator_position,

                            # connect_big_ctrl_scl,
                                      connect_main_ctrl_tz,
                                      connect_big_ctrl_tz
                            # connect_manual_pinch_orient,
                                      # connect_auto_pinch_orient
                                      ]

                        for i in range(len(list_order)):
                            list_order[i](i)

                        # # connect big rotate
                        # node_mm_offset_rotate = pm.createNode("multMatrix",n=self.getName("{}_rotate_big_mm".format(name)))
                        #
                        # pm.connectAttr("{}.matrixSum".format(node_mm_big_rotate),"{}.matrixIn[0]".format(node_mm_offset_rotate))
                        # pm.connectAttr("{}.matrixSum".format(node_mm_result),"{}.matrixIn[1]".format(node_mm_offset_rotate))

                        # connect offset
                        node_mm_offset = pm.createNode("multMatrix",n=self.getName("{}_offset_mm".format(name)))

                        m_target = om.MMatrix(transform.setMatrixScale(self.guide.tra[name], (1, 1, 1)))
                        m_current = om.MMatrix(pm.getAttr("{}.matrixSum".format(node_mm_result)))

                        pm.setAttr("{}.matrixIn[0]".format(node_mm_offset), m_current.inverse() * m_target,
                                   typ="matrix")
                        pm.connectAttr("{}.matrixSum".format(node_mm_result), "{}.matrixIn[1]".format(node_mm_offset))

                        # apply
                        pm.connectAttr("{}.matrixSum".format(node_mm_offset),"{}.offsetParentMatrix".format(joint_bind))
                        attribute.reset_SRT([joint_bind])

                    # apply to around mouth joint
                    else:
                        node_mm_result = pm.createNode("multMatrix",
                                                              n=self.getName("{}_extra_mult".format(name)))
                        pm.addAttr(node_mm_result, ln="offset_match", at="matrix", k=1)

                        m_loc_slide = om.MMatrix(pm.getAttr("{}.worldMatrix".format(loc_result)))
                        m_loc_bind = om.MMatrix(self.guide.tra[name])

                        if name in self.dict_sub[part]["lower_name"] or name == self.dict_sub[part]["upper_name"][0] or name == self.dict_sub[part]["upper_name"][-1]:
                            if name == self.dict_sub[part]["upper_name"][0] or name == self.dict_sub[part]["upper_name"][-1]:
                                attr_jaw = self.attr_m_jaw_between
                            else:
                                attr_jaw = "{}.worldMatrix".format(self.loc_jaw)

                            # 0 connect offset matrix
                            m_jaw = om.MMatrix(pm.getAttr(attr_jaw))

                            m_offset_match = m_loc_bind*(m_jaw*m_loc_slide).inverse()

                            pm.setAttr("{}.offset_match".format(node_mm_result),m_offset_match,typ="matrix")
                            pm.connectAttr("{}.offset_match".format(node_mm_result),"{}.matrixIn[0]".format(node_mm_result))

                            # 1 - connect result
                            pm.connectAttr("{}.worldMatrix[0]".format(loc_result),"{}.matrixIn[1]".format(node_mm_result))

                            # 2 - connect jaw matrix
                            pm.connectAttr(attr_jaw,"{}.matrixIn[2]".format(node_mm_result))

                        else:
                            m_current = om.MMatrix(pm.getAttr("{}.worldMatrix[0]".format(loc_result)))
                            m_offset_match = m_loc_bind*m_current.inverse()

                            pm.setAttr("{}.offset_match".format(node_mm_result),m_offset_match,typ="matrix")

                            pm.connectAttr("{}.offset_match".format(node_mm_result),"{}.matrixIn[0]".format(node_mm_result))
                            pm.connectAttr("{}.worldMatrix[0]".format(loc_result),"{}.matrixIn[1]".format(node_mm_result))

                        # apply value
                        pm.connectAttr("{}.matrixSum".format(node_mm_result),"{}.offsetParentMatrix".format(joint_bind))

                        attribute.reset_SRT([joint_bind])

                # update value
                self.dict_sub[part]["upper_pin"] = list_locator[0:len(self.dict_sub[part]["lower_joint"])]
                self.dict_sub[part]["lower_pin"] = list_locator[len(self.dict_sub[part]["lower_joint"])::]

        def set_driver_blend_shape_v2(transform_name,
                                      name_tag="setDriver",
                                      list_axis_up_out=["y", "x"]):
            """
            @param transform_name:
            @type transform_name:
            @param list_axis_up_out:
            @type list_axis_up_out:
            @param name_tag:
            @type name_tag:
            @param list_attr_output: list of up, down,in,out,upOut,upIn,downOut,downIn output attr
            @type list_attr_output:
            @return:
            @rtype:
            """
    
            def get_output_between(attr_A, attr_B):
                node_mdl = pm.createNode("multDoubleLinear", n="{}_avg_md".format(name_tag))
                pm.connectAttr(attr_A, node_mdl + ".input1")
                pm.connectAttr(attr_B, node_mdl + ".input2")
                return node_mdl + ".output"
    
            def get_normalize_output(attr_A, attr_B, attr_target):
                # normalize attr direct
                node_adl_normalized = pm.createNode("addDoubleLinear", n="{}_normalize_weight_adl".format(name_tag))
                pm.connectAttr(attr_A, node_adl_normalized + ".input1")
                pm.connectAttr(attr_B, node_adl_normalized + ".input2")
    
                node_pma_subtract = pm.createNode("plusMinusAverage", n="{}_normalize_offset_pma".format(name_tag))
                pm.setAttr(node_pma_subtract + ".operation", 2)
                pm.connectAttr(attr_target, node_pma_subtract + ".input1D[0]")
                pm.connectAttr(node_adl_normalized + ".output", node_pma_subtract + ".input1D[1]")
    
                return node_pma_subtract + ".output1D"
    
            axis_up, axis_out = list_axis_up_out
    
            # create attr input
            node_sr_range_positive = pm.createNode("setRange", n="{}_posClamp_sr".format(name_tag))
    
            for axis in list_axis_up_out:
                pm.connectAttr("{}.t{}".format(transform_name, axis),
                                 "{}.value{}".format(node_sr_range_positive, axis.upper()))
    
                pm.setAttr("{}.oldMin{}".format(node_sr_range_positive, axis.upper()), 0)
                pm.setAttr("{}.oldMax{}".format(node_sr_range_positive, axis.upper()), 1)
    
                pm.setAttr("{}.min{}".format(node_sr_range_positive, axis.upper()), 0)
                pm.setAttr("{}.max{}".format(node_sr_range_positive, axis.upper()), 1)
    
            node_sr_range_negative = pm.createNode("setRange", n="{}_negClamp_sr".format(name_tag))
            node_md_negative_invert = pm.createNode("multiplyDivide", n="{}_invertClamp_md".format(name_tag))
    
            pm.setAttr(node_md_negative_invert + ".input2", -1, -1, -1, typ="double3")
    
            for axis in list_axis_up_out:
                pm.connectAttr("{}.t{}".format(transform_name, axis),
                                 "{}.value{}".format(node_sr_range_negative, axis.upper()))
    
                pm.setAttr("{}.oldMin{}".format(node_sr_range_negative, axis.upper()), -1)
                pm.setAttr("{}.oldMax{}".format(node_sr_range_negative, axis.upper()), 0)
    
                pm.setAttr("{}.min{}".format(node_sr_range_negative, axis.upper()), -1)
                pm.setAttr("{}.max{}".format(node_sr_range_negative, axis.upper()), 0)
    
                pm.connectAttr("{}.outValue{}".format(node_sr_range_negative, axis.upper()),
                                 "{}.input1{}".format(node_md_negative_invert, axis.upper()))
    
            # get attr direct
            attr_up = "{}.outValue{}".format(node_sr_range_positive, axis_up.upper())
            attr_out = "{}.outValue{}".format(node_sr_range_positive, axis_out.upper())
            attr_down = "{}.output{}".format(node_md_negative_invert, axis_up.upper())
            attr_in = "{}.output{}".format(node_md_negative_invert, axis_out.upper())
    
            # get attr between
            attr_up_out = get_output_between(attr_up, attr_out)
            attr_up_in = get_output_between(attr_up, attr_in)
            attr_down_out = get_output_between(attr_down, attr_out)
            attr_down_in = get_output_between(attr_down, attr_in)
    
            # connect attr direct
            attr_up_norm = get_normalize_output(attr_up_out, attr_up_in, attr_up)
            attr_out_norm = get_normalize_output(attr_up_out, attr_down_out, attr_out)
            attr_down_norm = get_normalize_output(attr_down_in, attr_down_out, attr_down)
            attr_in_norm = get_normalize_output(attr_up_in, attr_down_in, attr_in)


            return {"up":attr_up_norm,
                    "down":attr_down_norm,
                    "in":attr_in_norm,
                    "out":attr_out_norm,
                    "up-out":attr_up_out,
                    "up-in":attr_up_in,
                    "down-out":attr_down_out,
                    "down-in":attr_down_in}

        def create_pinch_control():
            # Manual Pinch ---------------------------------------------------------------------
            for control in self.dict_main["upper_control"]+self.dict_main["lower_control"]:
                if control == self.dict_main["lower_control"][0]:
                    keyword = "LOW"
                    list_target = ((self.dict_rim["lower_control"][1],-0.025),
                                   (self.dict_rim["lower_control"][3], 0.025))

                elif control == self.dict_main["upper_control"][1]:
                    keyword = "UP"
                    list_target = ((self.dict_rim["upper_control"][2],-0.025),
                                   (self.dict_rim["upper_control"][4], 0.025))

                elif control == self.dict_main["upper_control"][0]:
                    keyword = "L"
                    list_target = ((self.dict_rim["upper_control"][5], -0.01),
                                   (self.dict_rim["lower_control"][4], -0.01))

                elif control == self.dict_main["upper_control"][2]:
                    keyword = "R"
                    list_target = ((self.dict_rim["upper_control"][1], 0.01),
                                   (self.dict_rim["lower_control"][0], 0.01))
                else:
                    continue

                # create node
                for data in list_target:
                    driven,value = data

                    node_mdl = pm.createNode("multDoubleLinear",n=self.getName("{}_main_rz_mdl".format(keyword)))
                    node_cm = pm.createNode("composeMatrix",n=self.getName("{}_main_rz_cm".format(keyword)))

                    pm.connectAttr("{}.rz".format(control),"{}.input1".format(node_mdl))
                    pm.setAttr("{}.input2".format(node_mdl),value)

                    pm.connectAttr("{}.output".format(node_mdl),"{}.inputTranslateY".format(node_cm))

                    self.dict_manual_pinch[driven] = "{}.outputMatrix".format(node_cm)

            # Auto Pinch
            for control in self.dict_main["upper_control"]+self.dict_main["lower_control"]:
                if control == self.dict_main["upper_control"][0]:
                    keyword = "L"
                    dict_target = {
                        self.dict_rim["upper_control"][5]:(("up-out",-0.5),("up",-1),("down-out",0.5),("down",1)),
                        self.dict_rim["lower_control"][4]:(("up-out",-0.5),("up",-1),("down-out",0.5),("down",1))
                        }

                    dict_attr_driven = set_driver_blend_shape_v2(control, keyword)

                elif control == self.dict_main["upper_control"][2]:
                    keyword = "R"
                    dict_target = {
                        self.dict_rim["upper_control"][1]:(("up-out",-0.5),("up",-1),("down-out",0.5),("down",1)),
                        self.dict_rim["lower_control"][0]:(("up-out",-0.5),("up",-1),("down-out",0.5),("down",1))
                        }

                    dict_attr_driven = set_driver_blend_shape_v2(control, keyword)

                else:
                    continue

                # create node
                for driven in dict_target.keys():
                    node_mm = pm.createNode("multMatrix",n=self.getName("{}_main_auto_sum_rz_mm").format(keyword))

                    for i,data in enumerate(dict_target[driven]):
                        typ,value = data

                        node_mdl = pm.createNode("multDoubleLinear",n=self.getName("{}_main_auto_rz_mdl".format(keyword)))
                        node_cm = pm.createNode("composeMatrix",n=self.getName("{}_main_auto_rz_cm".format(keyword)))

                        pm.connectAttr(dict_attr_driven[typ],"{}.input1".format(node_mdl))
                        pm.setAttr("{}.input2".format(node_mdl),value)

                        pm.connectAttr("{}.output".format(node_mdl),"{}.inputTranslateY".format(node_cm))

                        pm.connectAttr("{}.outputMatrix".format(node_cm),"{}.matrixIn[{}]".format(node_mm,i))

                    self.dict_auto_pinch[driven] = "{}.matrixSum".format(node_mm)

        def connect_sub_joint():
            list_locator = self.dict_rim["upper_joint"]+self.dict_rim["lower_joint"]

            for i,control in enumerate(self.dict_rim["upper_control"]+self.dict_rim["lower_control"]):
                locator = list_locator[i]

                pm.connectAttr("{}.matrix".format(control),"{}.offsetParentMatrix".format(locator))

        def add_for_curve(mesh,list_joint,name="skinCluster_add"):
            def get_skin_cluster(obj):
                history = pm.listHistory(obj, pdo=True)  # Get history, prioritize deformers
                skin_clusters = pm.ls(history, type="skinCluster")  # Filter only skinClusters

                if not skin_clusters:
                    pm.confirmDialog(m="Target Mesh Must Have Main Skin Cluster First!")
                    raise Exception()

                return skin_clusters[0]

            def get_shape_origin(obj):
                list_shape = pm.listRelatives(obj, c=1, s=1)

                if not list_shape:
                    raise Exception()

                shape_orig = None
                shape = None

                for shape in list_shape:
                    if "Orig" in shape:
                        shape_orig = shape
                    else:
                        shape = shape

                if shape_orig:
                    return shape_orig
                elif shape:
                    return shape
                else:
                    raise Exception()

            # GET SKIN CLUSTER MAIN -----------------------------------------
            node_skin_cluster_main = get_skin_cluster(mesh)
            node_shape_output_main = get_shape_origin(mesh)

            # CREATE TMP MESH -----------------------------------------
            mesh_tmp = pm.duplicate(mesh, n=mesh + "_tmp")[0]

            # GET SKIN CLUSTER OUTPUT PATH -----------------------------------------
            attr_output_geo = pm.listConnections("{}.outputGeometry[0]".format(node_skin_cluster_main), source=False,
                                                   destination=True, plugs=True)

            # GET SKIN CLUSTER NEW -----------------------------------------
            node_skin_cluster_new = pm.skinCluster(list_joint + [mesh_tmp], n=name)

            # CREATE CONNECTION -----------------
            pm.connectAttr("{}.local".format(node_shape_output_main),
                             "{}.originalGeometry[0]".format(node_skin_cluster_new), f=1)
            pm.connectAttr("{}.outputGeometry[0]".format(node_skin_cluster_main),
                             "{}.input[0].inputGeometry".format(node_skin_cluster_new), f=1)

            if attr_output_geo:
                pm.connectAttr("{}.outputGeometry[0]".format(node_skin_cluster_new), attr_output_geo[0], f=1)

            # DELETE TEMP SHAPE -----------------
            pm.delete(mesh_tmp)

            pm.reorderDeformers(node_skin_cluster_main, node_skin_cluster_new, mesh)

            return node_skin_cluster_new

        def bind_skin_curve():
            def auto_paint_weight():
                """

                for auto paint weight curve

                """
                curve_shape = pm.listRelatives(self.curve_lip_main, c=1, s=1)[0]

                # Auto-Paint Weight
                weights = {
                    'cv[0]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 1.0,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 0.0
                    },
                    'cv[1]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.2,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 0.8
                    },
                    'cv[2]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 1.0
                    },
                    'cv[3]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 1.0
                    },
                    'cv[4]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 1.0
                    },
                    'cv[5]': {
                        self.L_main_joint: 0.2,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 0.8
                    },
                    'cv[6]': {
                        self.L_main_joint: 1.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 0.0,
                        self.up_main_joint: 0.0
                    },
                    'cv[7]': {
                        self.L_main_joint: 0.2,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 0.8,
                        self.up_main_joint: 0.0
                    },
                    'cv[8]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 1.0,
                        self.up_main_joint: 0.0
                    },
                    'cv[9]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 1.0,
                        self.up_main_joint: 0.0
                    },
                    'cv[10]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.0,
                        self.low_main_joint: 1.0,
                        self.up_main_joint: 0.0
                    },
                    'cv[11]': {
                        self.L_main_joint: 0.0,
                        self.R_main_joint: 0.2,
                        self.low_main_joint: 0.8,
                        self.up_main_joint: 0.0
                    }
                }

                # Apply weights
                for cv, joint_weights in weights.items():
                    cv_component = f'{curve_shape}.{cv}'
                    pm.skinPercent(self.skinCluster_mid, cv_component, transformValue=list(joint_weights.items()))

            # bind main
            self.skinCluster_mid = pm.skinCluster(self.curve_lip_main,self.dict_main["upper_joint"]+self.dict_main["lower_joint"],
                           n=self.getName("main_skinCluster"), mi=1, ih=1, tsb=1, dr=0.1,
                           bm=3)

            auto_paint_weight()

        def get_closest_param(obj, curve):
            """
            Snaps an object to the closest point on a curve using Maya API 2.0.

            :param obj: Name of the object to snap.
            :param curve: Name of the NURBS curve.
            """
            if not pm.objExists(obj) or not pm.objExists(curve):
                pm.warning("Object or curve does not exist.")
                return

            # Get object world position
            obj_pos = pm.xform(obj, q=True, ws=True, t=True)
            point = om.MPoint(obj_pos)

            # Get MFnNurbsCurve from curve name
            sel = om.MSelectionList()
            sel.add(curve)
            dag_path = sel.getDagPath(0)
            curve_fn = om.MFnNurbsCurve(dag_path)

            # Get closest param on curve
            param = curve_fn.closestPoint(point, space=om.MSpace.kWorld)[1]

            # Get position at that param
            #closest_point = curve_fn.getPointAtParam(param, om.MSpace.kWorld)

            # Snap object to that position
            #pm.xform(obj, ws=True, t=(closest_point.x, closest_point.y, closest_point.z))

            return param  # optional: return parameter value if needed

        def connect_main_control_to_main_joint():
            list_joint = self.dict_main["upper_joint"]+self.dict_main["lower_joint"]
            list_name = self.dict_main["upper_name"]+self.dict_main["lower_name"]

            for i,control in enumerate(self.dict_main["upper_control"]+self.dict_main["lower_control"]): # iterate all controls
                joint = list_joint[i]

                if control == self.dict_main["lower_control"][0]:
                    ctrl_part = "lower"
                elif control == self.dict_main["upper_control"][0] or control == self.dict_main["upper_control"][
                    -1]:
                    ctrl_part = "between"
                else:
                    ctrl_part = "upper"

                # create compose matrix node
                node_cm = pm.createNode("composeMatrix",n=self.getName("{}_cm".format(list_name[i])))
                node_mm = pm.createNode("multMatrix", n=self.getName("{}_big_mm".format(list_name[i])))
                node_mm_offset = pm.createNode("multMatrix", n=self.getName("{}_offset_mm".format(list_name[i])))

                # tx,ty enable by default
                pm.connectAttr("{}.tx".format(control),"{}.inputTranslateX".format(node_cm))
                pm.connectAttr("{}.ty".format(control),"{}.inputTranslateY".format(node_cm))

                if not self.enable_slide_plane: # tz enable if not slide
                    pm.connectAttr("{}.tz".format(control), "{}.inputTranslateZ".format(node_cm))

                pm.connectAttr("{}.s".format(control),"{}.inputScale".format(node_cm))

                # connect mult value
                pm.connectAttr("{}.outputMatrix".format(node_cm),"{}.matrixIn[0]".format(node_mm))

                if ctrl_part == "lower":
                    pm.connectAttr("{}.worldMatrix[0]".format(self.ctrl_jaw),"{}.matrixIn[1]".format(node_mm))
                elif ctrl_part == "between":
                    pm.connectAttr(self.attr_m_jaw_between,"{}.matrixIn[1]".format(node_mm))

                pm.connectAttr(self.attr_m_big_control_drive_main,"{}.matrixIn[2]".format(node_mm))

                # connect offset value
                m_current = om.MMatrix(pm.getAttr(node_mm+".matrixSum"))
                m_target = om.MMatrix(pm.getAttr(joint + ".worldMatrix[0]"))
                m_offset = m_current.inverse() * m_target

                pm.setAttr("{}.matrixIn[0]".format(node_mm_offset),m_offset,typ="matrix")
                pm.connectAttr(node_mm+".matrixSum",node_mm_offset+".matrixIn[1]")

                # apply to joint
                pm.connectAttr("{}.matrixSum".format(node_mm_offset), "{}.offsetParentMatrix".format(joint))
                attribute.reset_SRT([joint])

        def create_big_control_driver_main_joint():
            node_cm = pm.createNode("composeMatrix",n=self.getName("big_control_cm"))
            node_mm_offset = pm.createNode("multMatrix",n=self.getName("big_control_offset_mm"))

            pm.connectAttr("{}.tx".format(self.ctrl_big),"{}.inputTranslateX".format(node_cm))
            pm.connectAttr("{}.ty".format(self.ctrl_big),"{}.inputTranslateY".format(node_cm))

            pm.connectAttr("{}.rz".format(self.ctrl_big),"{}.inputRotateZ".format(node_cm))

            m_current = om.MMatrix(pm.getAttr(node_cm+".outputMatrix"))
            m_target = om.MMatrix(transform.setMatrixScale(self.guide.tra["root"],(1,1,1)))
            m_offset = m_current.inverse() * m_target

            pm.connectAttr(node_cm+".outputMatrix",node_mm_offset+".matrixIn[0]")
            pm.setAttr(node_mm_offset+".matrixIn[1]",m_offset,typ="matrix")

            return node_mm_offset+".matrixSum"

        def create_scale_big_attr():
            list_name = self.dict_rim["upper_name"]+self.dict_rim["lower_name"]
            list_piv_m = self.dict_rim["upper_piv_m"]+self.dict_rim["lower_piv_m"]
            list_control = self.dict_rim["upper_control"]+self.dict_rim["lower_control"]
            dict_return = {}

            for i,loc in enumerate(self.dict_rim["upper_joint"]+self.dict_rim["lower_joint"]):
                name = list_name[i]
                m_piv = transform.setMatrixScale(list_piv_m[i],(1,1,1))
                control = list_control[i]

                if name in self.dict_rim["upper_name"]:
                    if i == 0:
                        control_main = self.dict_main["upper_control"][2]
                    elif i == len(self.dict_rim["upper_control"]) - 1:
                        control_main = self.dict_main["upper_control"][0]
                    else:
                        control_main = self.dict_main["upper_control"][1]
                elif name in self.dict_rim["lower_name"]:
                    control_main = self.dict_main["lower_control"][0]

                # create node
                node_mm = pm.createNode("multMatrix",n=self.getName("{}_scale_mm".format(name)))

                node_pm_scale_sub = pm.createNode("pickMatrix",n=self.getName("{}_sub_scale_pm".format(name)))
                node_pm_scale_sub.useTranslate.set(False)
                node_pm_scale_sub.useRotate.set(False)
                node_pm_scale_sub.useShear.set(False)

                node_pm_scale_main = pm.createNode("pickMatrix",n=self.getName("{}_main_scale_pm".format(name)))
                node_pm_scale_main.useTranslate.set(False)
                node_pm_scale_main.useRotate.set(False)
                node_pm_scale_main.useShear.set(False)

                # connect
                pm.connectAttr("{}.matrix".format(control), "{}.inputMatrix".format(node_pm_scale_sub))
                pm.connectAttr("{}.matrix".format(control_main), "{}.inputMatrix".format(node_pm_scale_main))

                pm.connectAttr("{}.outputMatrix".format(node_pm_scale_sub), "{}.matrixIn[0]".format(node_mm))
                pm.connectAttr("{}.outputMatrix".format(node_pm_scale_main), "{}.matrixIn[1]".format(node_mm))
                pm.setAttr("{}.matrixIn[2]".format(node_mm),m_piv,typ="matrix")

                dict_return[loc] = "{}.matrixSum".format(node_mm)

            return dict_return

        def finalize():
            if not self.WIP:
                self.grp_slide_locator_aim.visibility.set(False)
                self.grp_slide_locator_result.visibility.set(False)
                self.grp_bind_loc.visibility.set(False)
                self.grp_joint_main.visibility.set(False)
                self.curve_lip_main.visibility.set(False)

                attribute.lockAttribute(self.ctrl_big,["sz"])

                for control in [self.dict_main["upper_control"][0],self.dict_main["upper_control"][-1]]:
                    attribute.lockAttribute(control, ["sx","sz"])

                for control in self.controlers:
                    attribute.lockAttribute(control, ["v"])

        def create_rim_loop():
            """
            Constraint between rim ctl to rim joint
            """
            # create layer pin aim
            list_joint = self.dict_rim["upper_joint"] + self.dict_rim["lower_joint"]
            list_loc_aim = []

            for i, name in enumerate(self.dict_rim["upper_name"] + self.dict_rim["lower_name"]):
                control = (self.dict_rim["upper_control"] + self.dict_rim["lower_control"])[i]
                joint_bind = list_joint[i]

                # CREATE AIM LOC --------------------
                loc_aim = pm.spaceLocator(n="{}_aim_loc".format(name))
                list_loc_aim.append(loc_aim)
                loc_aim.setParent(self.grp_slide_locator_aim)

                pm.matchTransform(loc_aim, joint_bind)

                # connect pin position directly ------------------
                node_pma = pm.createNode("plusMinusAverage")
                node_dm_get_surface_pos = pm.createNode("decomposeMatrix",
                                                        n=self.getName("{}_get_surface_pos".format(name)))

                # get slide pos
                pm.setAttr(
                    "{}.coordinate[{}].coordinateU".format(self.node_uvPin_curve, self.index_uvPin_curve),
                    get_closest_param(str(loc_aim), str(self.curve_lip_main)))

                pm.connectAttr("{}.outputMatrix[{}]".format(self.node_uvPin_curve, self.index_uvPin_curve),
                               "{}.inputMatrix".format(node_dm_get_surface_pos))
                pm.connectAttr("{}.outputTranslate".format(node_dm_get_surface_pos),
                               "{}.input3D[0]".format(node_pma))

                # get control pos
                node_dm_get_ctrl_pos = pm.createNode("decomposeMatrix",
                                                     n=self.getName("{}_get_ctrl_pos".format(name)))

                pm.connectAttr("{}.matrix".format(control), "{}.inputMatrix".format(node_dm_get_ctrl_pos))

                pm.connectAttr("{}.outputTranslateX".format(node_dm_get_ctrl_pos),
                               "{}.input3D[1].input3Dx".format(node_pma))
                pm.connectAttr("{}.outputTranslateY".format(node_dm_get_ctrl_pos),
                               "{}.input3D[1].input3Dy".format(node_pma))

                # apply
                pm.connectAttr("{}.output3D".format(node_pma), "{}.translate".format(loc_aim))

                self.index_uvPin_curve += 1

                # CREASE SLIDING PIN RESULT (CONNECT TO SLIDE LOCATOR )--------------------
                loc_result = pm.spaceLocator(n="{}_slide_loc".format(name))

                # prepare offset group
                pm.parent(loc_result, self.grp_slide_locator_result)

                if self.enable_slide_plane:
                    node_cpos = pm.createNode("closestPointOnSurface",
                                              n=self.getName("{}_closest_point_cpos".format(name)))
                    node_pm = pm.createNode("pickMatrix", n=self.getName("{}_get_pos_matrix_pm".format(name)))
                    node_get_translate = pm.createNode("decomposeMatrix",
                                                       n=self.getName("{}_get_translate_dm".format(name)))

                    # connection input  --------
                    pm.connectAttr("{}.worldMatrix[0]".format(loc_aim),
                                   "{}.inputMatrix".format(node_get_translate))

                    pm.connectAttr("{}.outputTranslate".format(node_get_translate),
                                   "{}.inPosition".format(node_cpos))
                    pm.connectAttr("{}.worldSpace[0]".format(self.slide_plane),
                                   "{}.inputSurface".format(node_cpos))

                    # get uv pin ---------------
                    pm.connectAttr("{}.parameterU".format(node_cpos),
                                   "{}.coordinate[{}].coordinateU".format(self.node_uvPin_surface,
                                                                          self.index_uvPin_surface))
                    pm.connectAttr("{}.parameterV".format(node_cpos),
                                   "{}.coordinate[{}].coordinateV".format(self.node_uvPin_surface,
                                                                          self.index_uvPin_surface))

                    pm.connectAttr(
                        "{}.outputMatrix[{}]".format(self.node_uvPin_surface, self.index_uvPin_surface),
                        "{}.inputMatrix".format(node_pm))

                    self.index_uvPin_surface += 1

                    if self.enable_slide_orient:
                        node_pm.useRotate.set(True)
                    else:
                        node_pm.useRotate.set(False)

                    node_pm.useShear.set(False)
                    node_pm.useScale.set(False)

                    attr_translate = "{}.outputMatrix".format(node_pm)
                else:
                    node_pm = pm.createNode("pickMatrix", n=self.getName("{}_get_pos_matrix_pm".format(name)))

                    # connection input  --------
                    pm.connectAttr("{}.worldMatrix[0]".format(loc_aim), "{}.inputMatrix".format(node_pm))

                    node_pm.useRotate.set(False)
                    node_pm.useShear.set(False)
                    node_pm.useScale.set(False)

                    attr_translate = "{}.outputMatrix".format(node_pm)

                # connect -------------------
                node_mm_output = pm.createNode("multMatrix",
                                               n=self.getName("{}_output_slide_mm".format(name)))

                if self.enable_slide_plane:
                    # CTRL MAIN > LOC RESULT
                    node_cm = pm.createNode("composeMatrix", n=self.getName("{}_get_tz_cm".format(name)))

                    pm.connectAttr("{}.tz".format(control), "{}.inputTranslateZ".format(node_cm))
                    pm.connectAttr("{}.outputMatrix".format(node_cm),
                                   "{}.matrixIn[0]".format(node_mm_output))

                # CTRL MAIN > SUB JOINT NPO
                node_pm_rot = pm.createNode("pickMatrix", n=self.getName("{}_pick_rotate_pm".format(name)))

                pm.connectAttr("{}.matrix".format(control), "{}.inputMatrix".format(node_pm_rot))
                node_pm_rot.useTranslate.set(False)
                node_pm_rot.useScale.set(False)
                node_pm_rot.useShear.set(False)

                pm.connectAttr("{}.outputMatrix".format(node_pm_rot),
                               "{}.matrixIn[1]".format(node_mm_output))

                pm.connectAttr(attr_translate, "{}.matrixIn[2]".format(node_mm_output))

                pm.connectAttr("{}.matrixSum".format(node_mm_output),
                               "{}.offsetParentMatrix".format(loc_result))

                # CTRL MAIN > SUB JOINT (rotate roll m,b mouth)
                list_loc_bind = self.dict_rim["upper_joint"] + self.dict_rim["lower_joint"]
                if name in self.dict_rim["upper_name"]:
                    if i != 0 and i != len(self.dict_rim["upper_control"]) - 1:
                        pm.connectAttr("{}.rx".format(self.dict_main["upper_control"][1]),
                                       "{}.rx".format(list_loc_bind[i]))

                elif name in self.dict_rim["lower_name"]:
                    pm.connectAttr("{}.rx".format(self.dict_main["lower_control"][0]),
                                   "{}.rx".format(list_loc_bind[i]))


                # COMBINE ALL MULT MATRIX INPUT --------------------
                def connect_locator_orient(i):
                    node_pm_jaw_rotate = pm.createNode("pickMatrix",
                                                       n=self.getName("{}_get_jaw_orient_pm".format(name)))

                    node_pm_jaw_rotate.useScale.set(False)
                    node_pm_jaw_rotate.useShear.set(False)

                    if name in self.dict_rim["lower_name"]:
                        pm.connectAttr("{}.worldMatrix".format(self.loc_jaw),
                                       "{}.inputMatrix".format(node_pm_jaw_rotate))
                        node_pm_jaw_rotate.useTranslate.set(False)
                    elif name == self.dict_rim["upper_name"][0] or name == \
                            self.dict_rim["upper_name"][-1]:
                        pm.connectAttr(self.attr_m_jaw_between, "{}.inputMatrix".format(node_pm_jaw_rotate))
                        node_pm_jaw_rotate.useTranslate.set(False)

                    attr_jaw_transform = "{}.outputMatrix".format(node_pm_jaw_rotate)

                    pm.connectAttr(attr_jaw_transform, "{}.matrixIn[{}]".format(node_mm_result, i))

                def connect_big_ctrl_scl(i):
                    pm.connectAttr(self.dict_scale_big[joint_bind],
                                   "{}.matrixIn[{}]".format(node_mm_result, i))

                def connect_locator_position(i):
                    pm.connectAttr("{}.worldMatrix[0]".format(loc_result),
                                   "{}.matrixIn[{}]".format(node_mm_result, i))

                def connect_main_ctrl_tz(i):
                    # CONNECT MAIN TZ (main push in,out)
                    node_cm_push = pm.createNode("composeMatrix",
                                                 n=self.getName("{}_main_push_pos_cm".format(name, i)))

                    if name in self.dict_rim["upper_name"]:
                        if i == 0:
                            pm.connectAttr("{}.tz".format(self.dict_main["upper_control"][2]),
                                           "{}.inputTranslateZ".format(node_cm_push))
                        elif i == len(self.dict_rim["upper_control"]) - 1:
                            pm.connectAttr("{}.tz".format(self.dict_main["upper_control"][0]),
                                           "{}.inputTranslateZ".format(node_cm_push))
                        else:
                            pm.connectAttr("{}.tz".format(self.dict_main["upper_control"][1]),
                                           "{}.inputTranslateZ".format(node_cm_push))

                    elif name in self.dict_rim["lower_name"]:
                        pm.connectAttr("{}.tz".format(self.dict_main["lower_control"][0]),
                                       "{}.inputTranslateZ".format(node_cm_push))

                    pm.connectAttr("{}.outputMatrix".format(node_cm_push),
                                   "{}.matrixIn[{}]".format(node_mm_result, i))

                def connect_big_ctrl_tz(i):
                    # CONNECT BIG TZ (big push in,out)
                    node_cm_push_big = pm.createNode("composeMatrix",
                                                     n=self.getName("{}_big_push_cm".format(name)))

                    pm.connectAttr("{}.tz".format(self.ctrl_big),
                                   "{}.inputTranslateZ".format(node_cm_push_big))
                    pm.connectAttr("{}.outputMatrix".format(node_cm_push_big),
                                   "{}.matrixIn[{}]".format(node_mm_result, i))

                def connect_manual_pinch_orient(i):
                    # CONNECT MANUAL PINCH ORIENT
                    if control in self.dict_manual_pinch.keys():
                        pm.connectAttr(self.dict_manual_pinch[control],
                                       "{}.matrixIn[{}]".format(node_mm_result, i))

                def connect_auto_pinch_orient(i):
                    if self.enable_auto_pinch:
                        if control in self.dict_auto_pinch.keys():
                            pm.connectAttr(self.dict_auto_pinch[control],
                                           "{}.matrixIn[{}]".format(node_mm_result, i))

                list_order = [
                    connect_locator_orient,
                    connect_locator_position,
                    # connect_big_ctrl_scl,
                    connect_main_ctrl_tz,

                    connect_big_ctrl_tz
                ]

                node_mm_result = pm.createNode("multMatrix", n=self.getName("{}_result_mm".format(name)))

                for i in range(len(list_order)):
                    list_order[i](i)

                m_output_slide = "{}.matrixSum".format(node_mm_result)

                # pick matrix
                node_pm= pm.createNode("pickMatrix")
                node_pm.useRotate.set(False)
                pm.connectAttr(m_output_slide,node_pm+".inputMatrix")
                m_output_slide = node_pm+".outputMatrix"

                # CONNECT OFFSET WITH GROUP -----------------
                grp_offset = pm.group(em=1,n=self.getName(name+"_offset"))
                grp_offset.setParent(self.grp_bind_loc)
                pm.connectAttr(m_output_slide,"{}.offsetParentMatrix".format(grp_offset))
                pm.parent(joint_bind,grp_offset)

            # update value
            self.dict_rim["upper_pin"] = list_loc_aim[0:len(self.dict_rim["lower_joint"])]
            self.dict_rim["lower_pin"] = list_loc_aim[len(self.dict_rim["lower_joint"])::]

        def create_extra_loop():
            """
            Constraint behaviour of extra loop joint

            """
            if not self.enable_extra_loop:
                return

            # create layer pin aim
            for loop_count in range(1,self.extra_loop_amount-1):
                for i,name in enumerate(self.dict_extra[loop_count]["upper_name"]+self.dict_extra[loop_count]["lower_name"]):
                    control = (self.dict_rim["upper_control"] + self.dict_rim["lower_control"])[i]
                    list_loc_rim = self.dict_rim["upper_pin"] + self.dict_rim["lower_pin"]

                    joint_bind = (self.dict_extra[loop_count]["upper_joint"] + self.dict_extra[loop_count]["lower_joint"])[i]
                    list_name = self.dict_extra[loop_count]["upper_name"]+self.dict_extra[loop_count]["lower_name"]
                    list_extra_joint = self.dict_extra[loop_count]["upper_joint"]+self.dict_extra[loop_count]["lower_joint"]

                    # CREATE AIM LOC ----------------------------
                    loc_aim = pm.spaceLocator(n="{}_aim_loc".format(name))
                    loc_aim.setParent(self.grp_extra_slide_locator_aim)

                    pm.matchTransform(loc_aim,joint_bind)

                    # Pin Loc Aim to surface ---------------
                    u,v = utils.get_nearest_param(curve=self.nurbs_plane_loop,object=loc_aim,typ="surface")

                    pm.setAttr("{}.coordinate[{}].coordinateU".format(self.node_uvPin_loop,self.index_uvPin_loop),u)
                    pm.setAttr("{}.coordinate[{}].coordinateV".format(self.node_uvPin_loop,self.index_uvPin_loop),v)

                    attr_m_aim = "{}.outputMatrix[{}]".format(self.node_uvPin_loop, self.index_uvPin_loop)

                    # visualize locator aim
                    pm.connectAttr(attr_m_aim,"{}.offsetParentMatrix".format(loc_aim))
                    attribute.reset_SRT([loc_aim])

                    self.index_uvPin_loop += 1

                    # Apply sliding pin
                    node_dm_get_pos = pm.createNode("decomposeMatrix")
                    node_cpos = pm.createNode("closestPointOnSurface")
                    node_uvPin = pm.createNode("uvPin")

                    node_uvPin.normalizedIsoParms.set(False)

                    pm.connectAttr(attr_m_aim,"{}.inputMatrix".format(node_dm_get_pos))

                    pm.connectAttr("{}.outputTranslate".format(node_dm_get_pos),"{}.inPosition".format(node_cpos))
                    pm.connectAttr("{}.worldSpace[0]".format(self.slide_plane),"{}.inputSurface".format(node_cpos))

                    pm.connectAttr("{}.parameterU".format(node_cpos),"{}.coordinate[0].coordinateU".format(node_uvPin))
                    pm.connectAttr("{}.parameterV".format(node_cpos),"{}.coordinate[0].coordinateV".format(node_uvPin))
                    pm.connectAttr("{}.worldSpace[0]".format(self.slide_plane),"{}.deformedGeometry".format(node_uvPin))

                    m_output_slide = node_uvPin+".outputMatrix[0]"

                    # pick matrix
                    node_pm= pm.createNode("pickMatrix")
                    node_pm.useRotate.set(False)
                    pm.connectAttr(m_output_slide,node_pm+".inputMatrix")
                    m_output_slide = node_pm+".outputMatrix"

                    # apply value
                    grp_offset = pm.group(em=1, n=self.getName(name + "_offset"))
                    grp_offset.setParent(self.grp_extra_bind_loc)
                    pm.connectAttr(m_output_slide, "{}.offsetParentMatrix".format(grp_offset))
                    pm.parent(joint_bind, grp_offset)

                    # # CREASE SLIDING PIN RESULT (CONNECT TO SLIDE LOCATOR )--------------------
                    # loc_result = pm.spaceLocator(n="{}_slide_loc".format(name))
                    #
                    # # prepare offset group
                    # pm.parent(loc_result,self.grp_slide_locator_result)
                    #
                    # if self.enable_slide_plane:
                    #     node_cpos = pm.createNode("closestPointOnSurface",n=self.getName("{}_closest_point_cpos".format(name)))
                    #     node_pm = pm.createNode("pickMatrix", n=self.getName("{}_get_pos_matrix_pm".format(name)))
                    #     node_get_translate = pm.createNode("decomposeMatrix",n=self.getName("{}_get_translate_dm".format(name)))
                    #
                    #     # connection input  --------
                    #     pm.connectAttr(attr_m_aim, "{}.inputMatrix".format(node_get_translate))
                    #
                    #     pm.connectAttr("{}.outputTranslate".format(node_get_translate),"{}.inPosition".format(node_cpos))
                    #     pm.connectAttr("{}.worldSpace[0]".format(self.slide_plane), "{}.inputSurface".format(node_cpos))
                    #
                    #     # get uv pin ---------------
                    #     pm.connectAttr("{}.parameterU".format(node_cpos),"{}.coordinate[{}].coordinateU".format(self.node_uvPin_surface,self.index_uvPin_surface))
                    #     pm.connectAttr("{}.parameterV".format(node_cpos),"{}.coordinate[{}].coordinateV".format(self.node_uvPin_surface,self.index_uvPin_surface))
                    #
                    #     pm.connectAttr("{}.outputMatrix[{}]".format(self.node_uvPin_surface,self.index_uvPin_surface),"{}.inputMatrix".format(node_pm))
                    #
                    #     self.index_uvPin_surface+=1
                    #
                    #     node_pm.useRotate.set(False)
                    #     node_pm.useShear.set(False)
                    #     node_pm.useScale.set(False)
                    #
                    #     attr_translate = "{}.outputMatrix".format(node_pm)
                    # else:
                    #     node_pm = pm.createNode("pickMatrix", n=self.getName("{}_get_pos_matrix_pm".format(name)))
                    #
                    #     # connection input  --------
                    #     pm.connectAttr(attr_m_aim,"{}.inputMatrix".format(node_pm))
                    #
                    #     node_pm.useRotate.set(False)
                    #     node_pm.useShear.set(False)
                    #     node_pm.useScale.set(False)
                    #
                    #     attr_translate = "{}.outputMatrix".format(node_pm)
                    #
                    # # connect output translate to locator result
                    # pm.connectAttr(attr_translate,"{}.offsetParentMatrix".format(loc_result))
                    #
                    # # extended
                    # node_mm_result = pm.createNode("multMatrix",
                    #                                       n=self.getName("{}_extra_mult".format(name)))
                    # pm.addAttr(node_mm_result, ln="offset_match", at="matrix", k=1)
                    #
                    # m_loc_slide = om.MMatrix(pm.getAttr("{}.worldMatrix".format(loc_result)))
                    # m_loc_bind = om.MMatrix(transform.getTransform(list_extra_joint[i]))
                    #
                    # if name in self.dict_extra[loop_count]["lower_name"] or name == self.dict_extra[loop_count]["upper_name"][0] or name == self.dict_extra[loop_count]["upper_name"][-1]:
                    #     if name == self.dict_extra[loop_count]["upper_name"][0] or name == self.dict_extra[loop_count]["upper_name"][-1]:
                    #         attr_jaw = self.attr_m_jaw_between
                    #     else:
                    #         attr_jaw = "{}.worldMatrix".format(self.loc_jaw)
                    #
                    #     # 0 connect offset matrix
                    #     m_jaw = om.MMatrix(pm.getAttr(attr_jaw))
                    #
                    #     m_offset_match = m_loc_bind*(m_jaw*m_loc_slide).inverse()
                    #
                    #     pm.setAttr("{}.offset_match".format(node_mm_result),m_offset_match,typ="matrix")
                    #     pm.connectAttr("{}.offset_match".format(node_mm_result),"{}.matrixIn[0]".format(node_mm_result))
                    #
                    #     # 1 - connect result
                    #     pm.connectAttr("{}.worldMatrix[0]".format(loc_result),"{}.matrixIn[1]".format(node_mm_result))
                    #
                    #     # 2 - connect jaw matrix
                    #     pm.connectAttr(attr_jaw,"{}.matrixIn[2]".format(node_mm_result))
                    #
                    # else:
                    #     m_current = om.MMatrix(pm.getAttr("{}.worldMatrix[0]".format(loc_result)))
                    #     m_offset_match = m_loc_bind*m_current.inverse()
                    #
                    #     pm.setAttr("{}.offset_match".format(node_mm_result),m_offset_match,typ="matrix")
                    #
                    #     pm.connectAttr("{}.offset_match".format(node_mm_result),"{}.matrixIn[0]".format(node_mm_result))
                    #     pm.connectAttr("{}.worldMatrix[0]".format(loc_result),"{}.matrixIn[1]".format(node_mm_result))
                    #
                    # # apply value
                    # grp_offset = pm.group(em=1, n=self.getName(name + "_offset"))
                    # grp_offset.setParent(self.grp_extra_bind_loc)
                    # pm.connectAttr("{}.matrixSum".format(node_mm_result), "{}.offsetParentMatrix".format(grp_offset))
                    # pm.parent(joint_bind, grp_offset)

        def setup_loop_surface():
            if not self.enable_extra_loop:
                return

            # create dummy joint
            list_joint = []
            for loc in self.dict_rim["upper_joint"]+self.dict_rim["lower_joint"]+self.dict_corner["upper_corner"]+self.dict_corner["lower_corner"]:
                pm.select(cl=1)
                joint = pm.joint(n=loc+"_dummy")
                npo = mgear.rigbits.addNPO(joint)[0]
                npo.setParent(self.grp_dummy_joints)

                pm.connectAttr(loc+".worldMatrix[0]",npo+".offsetParentMatrix")

                list_joint.append(joint)

            self.grp_dummy_joints.visibility.set(False)

            # bind skin
            self.skinCluster_mid = pm.skinCluster(self.nurbs_plane_loop,list_joint,
                           n=self.getName("nurbs_loop_skinCluster"), mi=1, ih=1, tsb=1, dr=10,
                           bm=3)

            print("joints rim : ",self.dict_rim["upper_joint"])

        # pinch data
        self.dict_auto_pinch = {}
        self.dict_manual_pinch = {}

        # create common use attribute matrix
        self.attr_m_jaw_between = create_jaw_between_attr_matrix()
        self.attr_m_big_control = create_attr_big_control_transform()
        self.attr_m_big_control_drive_main = create_big_control_driver_main_joint()

        self.dict_scale_big = create_scale_big_attr()

        # prepare uv pin node
        create_uv_pin_curve_node()
        create_uv_pin_surface_node()
        create_uv_pin_surface_loop_node()

        # main operation

        bind_skin_curve()

        connect_main_control_to_main_joint()

        create_rim_loop()

        setup_loop_surface()
        create_extra_loop()

        finalize()

    def setRelation(self):
        """Set the relation beetween object from guide to rig"""

        self.relatives["root"] = self.root
        self.relatives["jaw"] = self.ctrl_jaw

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


