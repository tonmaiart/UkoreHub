from re import T
import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from TonmaiToolkit.core import Utility, Misc, Connection, BlendShape, Transform, Create
from mgear.shifter import component, log_window
import math
import maya.api.OpenMaya as om
from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive
import math


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        #########################
        #### Create Hierarchy ###
        ########################

        # User Setting Input
        self.slide_plane = self.settings["sliding_object"]
        self.enable_extra_loop = self.settings["extra_loop"]
        self.enable_auto_pinch = self.settings["auto_pinch"]
        self.enable_slide_plane = self.settings["enable_sliding"]
        self.extra_loop_amount = self.settings["loop_amount"]
        self.enable_slide_orient = True
        self.nurbs_plane_loop = None

        # Create Hierarchy Groups
        self.grp_no_transform = pm.group(
            em=1, n=self.getName("no_transform_grp"), p=self.root
        )
        self.grp_no_transform.inheritsTransform.set(False)

        self.grp_control = pm.group(em=1, n=self.getName("all_control_grp"))
        pm.parent(self.grp_control, self.root)

        self.grp_joint_main = pm.group(
            em=1, n=self.getName("joint_driver_grp"), p=self.grp_no_transform
        )

        self.grp_bind_loc = pm.group(
            em=1, n=self.getName("loc_bind_grp"), p=self.grp_no_transform
        )
        self.grp_slide_locator_aim = pm.group(
            em=1, n=self.getName("loc_aim_grp"), p=self.grp_no_transform
        )
        self.grp_slide_locator_result = pm.group(
            em=1, n=self.getName("loc_slide_grp"), p=self.grp_no_transform
        )

        self.grp_extra_bind_loc = pm.group(
            em=1, n=self.getName("loc_extra_bind_grp"), p=self.grp_no_transform
        )
        self.grp_extra_slide_locator_aim = pm.group(
            em=1, n=self.getName("loc_extra_aim_grp"), p=self.grp_no_transform
        )
        self.grp_extra_slide_locator_result = pm.group(
            em=1, n=self.getName("loc_extra_slide_grp"), p=self.grp_no_transform
        )

        self.grp_corner_loc = pm.group(
            em=1, n=self.getName("loc_corner_grp"), p=self.grp_no_transform
        )

        self.grp_dummy_joints = pm.group(
            em=1, n=self.getName("dummy_joint_grp"), p=self.grp_no_transform
        )

        ################################
        ### Build Variables
        ################################

        self.loop_blend_factor = 1 / self.extra_loop_amount

        self.curve_lip_main = None
        self.curve_lip_mid = None

        self.dict_main = {
            "upper_control": [],
            "lower_control": [],
            "upper_joint": [],
            "lower_joint": [],
            "upper_name": ["L_main", "up_main", "R_main"],
            "lower_name": ["low_main"],
        }

        self.dict_mid = {
            "upper_control": [],
            "lower_control": [],
            "upper_joint": [],
            "lower_joint": [],
            "upper_name": ["R_up_corner", "R_up", "C_up", "L_up", "L_up_corner"],
            "lower_name": ["R_low", "C_low", "L_low"],
        }

        self.dict_bind_joint = {
            "upper_control": [],
            "lower_control": [],
            "upper_joint": [],
            "lower_joint": [],
        }
        self.dict_sub_rig = {
            "upper_control": [],
            "lower_control": [],
            "upper_joint": [],
            "lower_joint": [],
            "upper_name": [
                "R_cornerRim",
                "R_upRimB",
                "R_upRimA",
                "C_upRim",
                "L_upRimA",
                "L_upRimB",
                "L_cornerRim",
            ],
            "lower_name": [
                "R_lowRimB",
                "R_lowRimA",
                "C_lowRim",
                "L_lowRimA",
                "L_lowRimB",
            ],
            "upper_pin": [],
            "lower_pin": [],
            "upper_piv": [text for text in self.guide.tra.keys() if "up_piv" in text],
            "lower_piv": [text for text in self.guide.tra.keys() if "low_piv" in text],
            "upper_piv_m": [],
            "lower_piv_m": [],
        }

        for key in self.guide.tra.keys():
            if "up_piv" in key:
                self.dict_sub_rig["upper_piv_m"].append(self.guide.tra[key])
            elif "low_piv" in key:
                self.dict_sub_rig["lower_piv_m"].append(self.guide.tra[key])

        self.dict_corner = {
            "upper_corner": [],
            "upper_corner_m": [],
            "lower_corner": [],
            "lower_corner_m": [],
        }

        for key in self.guide.tra.keys():
            if "up_corner" in key:
                self.dict_corner["upper_corner"].append(
                    primitive.addLocator(
                        self.grp_corner_loc, key + "_loc", m=self.guide.tra[key]
                    )
                )
                self.dict_corner["upper_corner_m"].append(self.guide.tra[key])
            elif "low_corner" in key:
                self.dict_corner["lower_corner"].append(
                    primitive.addLocator(
                        self.grp_corner_loc, key + "_loc", m=self.guide.tra[key]
                    )
                )
                self.dict_corner["lower_corner_m"].append(self.guide.tra[key])

        # create extra dict
        self.dict_extra = {}

        if self.enable_extra_loop:
            for i in range(self.extra_loop_amount):
                self.dict_extra[i] = {
                    "upper_control": [],
                    "lower_control": [],
                    "upper_joint": [],
                    "lower_joint": [],
                    "upper_name": [
                        "up_corner_{}_{}".format(i + 1, j + 1) for j in range(7)
                    ],
                    "lower_name": [
                        "low_corner_{}_{}".format(i + 1, j + 1) for j in range(5)
                    ],
                    "upper_pin": [],
                    "lower_pin": [],
                }

        #############################
        ### Create Bind Joints ######
        ##############################
        def create_extra_loop():
            if not self.enable_extra_loop:
                return

            for loop_count in range(self.extra_loop_amount):
                list_joint_rim = (
                    self.dict_sub_rig["upper_joint"] + self.dict_sub_rig["lower_joint"]
                )
                list_corner_guide = (
                    self.dict_corner["upper_corner"] + self.dict_corner["lower_corner"]
                )
                list_name = (
                    self.dict_extra[loop_count]["upper_name"]
                    + self.dict_extra[loop_count]["lower_name"]
                )

                # create locator and snap position
                for i, name in enumerate(list_name):
                    locator = primitive.addLocator(
                        self.grp_extra_bind_loc,
                        self.getName("{}_loc".format(name)),
                        m=transform.getTransformFromPos((0, 0, 0)),
                    )

                    # snap position
                    Transform.transform_to_between_object(
                        list_joint_rim[i],
                        list_corner_guide[i],
                        locator,
                        percentage=loop_count * self.loop_blend_factor,
                    )

                    if name in self.dict_extra[loop_count]["upper_name"]:
                        self.dict_extra[loop_count]["upper_joint"].append(locator)
                    elif name in self.dict_extra[loop_count]["lower_name"]:
                        self.dict_extra[loop_count]["lower_joint"].append(locator)

                # create joint
                for i, locator in enumerate(
                    self.dict_extra[loop_count]["upper_joint"]
                    + self.dict_extra[loop_count]["lower_joint"]
                ):
                    self.jnt_pos.append(
                        {
                            "obj": locator,
                            "name": list_name[i],
                            "newActiveJnt": False,
                            "gearMulMatrix": False,
                            "vanilla_nodes": True,
                        }
                    )

        # create local base joint
        self.jnt_pos.append(
            {
                "obj": primitive.addLocator(
                    self.grp_bind_loc,
                    self.getName("base_loc"),
                    m=transform.getTransform(self.root),
                ),
                "name": "base",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

        # create rim joint
        list_name = self.dict_sub_rig["upper_name"] + self.dict_sub_rig["lower_name"]

        # create locator and update to dict rim joint
        for name in list_name:
            m_pos = transform.getTransformFromPos(self.guide.pos[name])

            if name in self.dict_sub_rig["upper_name"]:
                self.dict_bind_joint["upper_joint"].append(
                    primitive.addLocator(
                        self.grp_bind_loc,
                        self.getName("{}_loc".format(name)),
                        m=m_pos,
                    )
                )
            elif name in self.dict_sub_rig["lower_name"]:
                self.dict_bind_joint["lower_joint"].append(
                    primitive.addLocator(
                        self.grp_bind_loc,
                        self.getName("{}_loc".format(name)),
                        m=m_pos,
                    )
                )

        # create joint
        for i, locator in enumerate(
            self.dict_bind_joint["upper_joint"] + self.dict_bind_joint["lower_joint"]
        ):
            self.jnt_pos.append(
                {
                    "obj": locator,
                    "name": list_name[i],
                    "newActiveJnt": False,
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )

        # create jaw loc
        self.loc_jaw = primitive.addLocator(
            self.grp_bind_loc,
            self.getName("jaw_loc"),
            m=transform.setMatrixScale(self.guide.tra["jaw"], (1, 1, 1)),
        )
        mgear.rigbits.addNPO([self.loc_jaw])

        self.jnt_pos.append(
            {
                "obj": self.loc_jaw,
                "name": "jaw",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

        # create inner loc
        self.loc_inner = primitive.addLocator(
            self.grp_bind_loc,
            self.getName("inner_loc"),
            m=transform.setMatrixScale(self.guide.tra["oral"], (1, 1, 1)),
        )
        mgear.rigbits.addNPO([self.loc_inner])

        self.jnt_pos.append(
            {
                "obj": self.loc_inner,
                "name": "oral",
                "newActiveJnt": "parent_relative_jnt",
                "gearMulMatrix": False,
                "vanilla_nodes": True,
            }
        )

        # create extra loop joint
        create_extra_loop()

        def create_main_joint():
            """

            Create Main Joint that will bind to drive curve.

            """

            # create main joint
            self.L_main_joint = pm.createNode("joint", name=self.getName("L_main_jnt"))
            self.R_main_joint = pm.createNode("joint", name=self.getName("R_main_jnt"))
            self.up_main_joint = pm.createNode(
                "joint", name=self.getName("up_main_jnt")
            )
            self.low_main_joint = pm.createNode(
                "joint", name=self.getName("low_main_jnt")
            )

            # snap position L,R
            pm.xform(
                self.L_main_joint,
                ws=1,
                t=Transform.get_position_from_curve_param(
                    self.curve_lip_main,
                    0,
                    turn_on_percentage=True,
                ),
            )
            pm.xform(
                self.R_main_joint,
                ws=1,
                t=Transform.get_position_from_curve_param(
                    self.curve_lip_main, 0.5, turn_on_percentage=True
                ),
            )

            # snap position Up,Low
            pm.xform(
                self.low_main_joint,
                ws=1,
                t=Transform.get_position_from_curve_param(
                    self.curve_lip_main, 0.75, turn_on_percentage=True
                ),
            )
            pm.xform(
                self.up_main_joint,
                ws=1,
                t=Transform.get_position_from_curve_param(
                    self.curve_lip_main,
                    0.25,
                    turn_on_percentage=True,
                ),
            )

            # update value to dict main
            self.dict_main["upper_joint"] = [
                self.L_main_joint,
                self.up_main_joint,
                self.R_main_joint,
            ]
            self.dict_main["lower_joint"] = [self.low_main_joint]

            # parent to joint main grp
            pm.parent(
                self.dict_main["upper_joint"] + self.dict_main["lower_joint"],
                self.grp_joint_main,
            )

        def create_control_set():

            def create_big_control():
                # create big control
                self.ctrl_big = self.addCtl(
                    self.grp_control,
                    "mouth_box",
                    m=transform.getTransform(self.grp_control),
                    color=16,
                    iconShape="square",
                )

            def create_main_control():
                # create main controller
                for list_name in [
                    self.dict_main["upper_name"],
                    self.dict_main["lower_name"],
                ]:
                    if list_name == self.dict_main["upper_name"]:
                        list_pos = [(1.5, 0, 0), (0, 0.5, 0), (-1.5, 0, 0)]
                    elif list_name == self.dict_main["lower_name"]:
                        list_pos = [(0, -0.5, 0)]

                    list_control = []

                    for i, name in enumerate(list_name):
                        control = self.addCtl(
                            self.ctrl_big,
                            name,
                            m=transform.getTransformFromPos(list_pos[i]),
                            color=17,
                            iconShape="square",
                            w=0.2 * self.size,
                            h=0.2 * self.size,
                            d=0.2 * self.size,
                        )
                        list_control.append(control)
                        control.scale.set(0.5, 0.5, 0.5)

                    if list_name == self.dict_main["upper_name"]:
                        self.dict_main["upper_control"] = list_control
                    elif list_name == self.dict_main["lower_name"]:
                        self.dict_main["lower_control"] = list_control

            # create_big_control()
            # create_main_control()
            create_sub_mouth_rig()

            # # add npo
            # mgear.rigbits.addNPO(
            #     [self.ctrl_big]
            #     + self.dict_main["upper_control"]
            #     + self.dict_main["lower_control"]
            #     + self.dict_rim["upper_control"]
            #     + self.dict_rim["lower_control"]
            # )

            # # parent sub control to main control
            # for i in range(4):
            #     if i == 0:  # L
            #         list_control = (
            #             self.dict_rim["upper_control"][4:]
            #             + self.dict_rim["lower_control"][3:]
            #         )
            #         list_control_npo = [control.getParent() for control in list_control]
            #         ctrl_main = self.dict_main["upper_control"][0]
            #         name = "L"

            #     elif i == 1:  # R
            #         list_control = (
            #             self.dict_rim["upper_control"][0:3]
            #             + self.dict_rim["lower_control"][0:2]
            #         )
            #         list_control_npo = [control.getParent() for control in list_control]
            #         ctrl_main = self.dict_main["upper_control"][2]
            #         name = "R"

            #     elif i == 2:  # UP
            #         list_control = [self.dict_rim["upper_control"][3]]
            #         list_control_npo = [control.getParent() for control in list_control]
            #         ctrl_main = self.dict_main["upper_control"][1]
            #         name = "up"

            #     elif i == 3:  # LOW
            #         list_control = [self.dict_rim["lower_control"][2]]
            #         list_control_npo = [control.getParent() for control in list_control]
            #         ctrl_main = self.dict_main["lower_control"][0]
            #         name = "low"

            #     pm.parent(list_control_npo, ctrl_main)

            #     node_pm = pm.createNode(
            #         "pickMatrix", n=self.getName("{}_inverse_pm".format(name))
            #     )

            #     node_pm.useTranslate.set(False)

            #     pm.connectAttr(
            #         "{}.inverseMatrix".format(ctrl_main),
            #         "{}.inputMatrix".format(node_pm),
            #     )

            #     for grp_npo in list_control_npo:
            #         pm.connectAttr(
            #             "{}.outputMatrix".format(node_pm),
            #             "{}.offsetParentMatrix".format(grp_npo),
            #         )

            # snap big controller
            pm.xform(self.ctrl_big.getParent(), ws=1, m=self.guide.tra["controller"])

        def create_jaw_ctl():
            # create controller
            self.ctrl_jaw = self.addCtl(
                self.grp_control,
                "jaw",
                m=transform.setMatrixScale(self.guide.tra["jaw"], (1, 1, 1)),
                color=17,
                iconShape="square",
                w=0.6 * self.size,
                h=0.6 * self.size,
                d=0.6 * self.size,
            )
            mgear.rigbits.addNPO([self.ctrl_jaw])

            # direct connection control to locator
            pm.connectAttr("{}.t".format(self.ctrl_jaw), "{}.t".format(self.loc_jaw))
            pm.connectAttr("{}.r".format(self.ctrl_jaw), "{}.r".format(self.loc_jaw))
            pm.connectAttr("{}.s".format(self.ctrl_jaw), "{}.s".format(self.loc_jaw))

        def create_inner_ctl():
            # create controller
            self.ctrl_inner = self.addCtl(
                self.grp_control,
                "oral",
                m=transform.setMatrixScale(self.guide.tra["oral"], (1, 1, 1)),
                color=17,
                iconShape="cube",
                w=0.4 * self.size,
                h=0.4 * self.size,
                d=0.4 * self.size,
            )
            mgear.rigbits.addNPO([self.ctrl_inner])

            # direct connection control to locator
            pm.connectAttr(
                "{}.t".format(self.ctrl_inner), "{}.t".format(self.loc_inner)
            )
            pm.connectAttr(
                "{}.r".format(self.ctrl_inner), "{}.r".format(self.loc_inner)
            )
            pm.connectAttr(
                "{}.s".format(self.ctrl_inner), "{}.s".format(self.loc_inner)
            )

        def create_nurbs_plane_loop():
            if not self.enable_extra_loop:
                return

            list_crv = []
            list_key = [0, self.extra_loop_amount - 1]

            for key in list_key:
                list_position = []

                for joint in (
                    self.dict_extra[key]["upper_joint"]
                    + self.dict_extra[key]["lower_joint"][::-1]
                ):
                    list_position.append(pm.xform(joint, q=1, ws=1, t=1))

                # create curve
                curve = pm.circle(
                    n=self.getName("loop_crv"), s=len(list_position), d=3, ch=0
                )[0]
                curve.setParent(self.grp_no_transform)

                # snap position
                for key, pos in enumerate(list_position):
                    pm.xform("{}.cv[{}]".format(curve, key), ws=1, t=pos)

                # append curve
                list_crv.append(curve)

            # loft
            self.nurbs_plane_loop = pm.loft(list_crv, ch=0, n="plane_loop_nurbs", d=1)[
                0
            ]
            self.nurbs_plane_loop.setParent(self.grp_no_transform)
            print(self.nurbs_plane_loop)

        # Step 1 : Set-up
        # create_hierarchy()
        # create_variable()

        # Step 2 : Create Curve
        # create_jaw_ctl()
        # create_inner_ctl()
        # create_main_joint()
        # create_control_set()

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        def create_sub_mouth_rig():
            # Create controller
            speed = 0.2
            count = len(self.dict_sub_rig["upper_name"]) + len(
                self.dict_sub_rig["lower_name"]
            )
            for i, name in enumerate(
                self.dict_sub_rig["upper_name"] + self.dict_sub_rig["lower_name"]
            ):

                control = self.addCtl(
                    self.grp_control,
                    self.getName(name),
                    m=transform.getTransformFromPos(
                        Transform.get_position_from_curve_param(
                            self.curve_lip_mid, i * (1 / count), turn_on_percentage=True
                        )
                    ),
                    color=9,
                    iconShape="cube",
                    w=0.15 * self.size,
                    h=0.15 * self.size,
                    d=0.15 * self.size,
                )

                joint = pm.createNode("joint", n=self.getName(name + "JntDriver"))
                Utility.match_parent(joint, control)

                print("created : {}".format(control))

                # control.scale.set(speed, speed, speed)
                Create.create_freeze_group([control])

                if name in self.dict_sub_rig["upper_name"]:
                    self.dict_sub_rig["upper_control"].append(control)
                    self.dict_sub_rig["upper_joint"].append(joint)
                elif name in self.dict_sub_rig["lower_name"]:
                    self.dict_sub_rig["lower_control"].append(control)
                    self.dict_sub_rig["lower_joint"].append(joint)

            # Create Skin Cluster
            self.skinCluster_mid = pm.skinCluster(
                self.curve_lip_mid,
                self.dict_sub_rig["lower_joint"],
                self.dict_sub_rig["upper_joint"],
                n=self.getName("nurbs_loop_skinCluster"),
                mi=1,
                ih=1,
                tsb=1,
                dr=10,
                bm=3,
            )

            # Pin Locator bind to curve
            Connection.pin_to_curve(
                list_pin=self.dict_bind_joint["upper_joint"]
                + self.dict_bind_joint["lower_joint"],
                curve=self.curve_lip_mid,
                maintain_offset=False,
                only_position=True,
                prevent_double_transform=True,
            )

        ######################################
        ###### Create Curve ##################
        ######################################

        # collect positions
        list_all_pos = [self.guide.pos[n] for n in self.dict_sub_rig["upper_name"]] + [
            self.guide.pos[n] for n in reversed(self.dict_sub_rig["lower_name"])
        ]

        # create curve
        self.curve_lip_mid = pm.circle(
            n=self.getName("sub_crv"), s=len(list_all_pos), d=3, ch=0
        )[0]
        self.curve_lip_mid.setParent(self.grp_no_transform)

        # snap cvs
        [
            pm.xform(f"{self.curve_lip_mid}.cv[{i}]", ws=1, t=pos)
            for i, pos in enumerate(list_all_pos)
        ]

        # Step 3 : Create Sub Controllers
        create_sub_mouth_rig()

    def setRelation(self):
        """Set the relation beetween object from guide to rig"""

        self.relatives["root"] = self.root
        # self.relatives["jaw"] = self.ctrl_jaw

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
