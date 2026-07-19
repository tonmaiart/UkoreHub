import maya.api.OpenMaya as om
import maya.cmds as mc
import pymel.core as pm

import mgear.rigbits
from mgear.shifter import component
from mgear.core import attribute, transform, primitive

from TonmaiToolkit.core import Utility, Misc, Connection, BlendShape, Transform, Create


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        ## =======================
        ## Get User Settings
        ## =======================

        self.slide_plane = self.settings["sliding_object"]
        self.enable_extra_loop = self.settings["extra_loop"]
        self.enable_auto_pinch = self.settings["auto_pinch"]
        self.enable_slide_plane = self.settings["enable_sliding"]
        self.extra_loop_amount = self.settings["loop_amount"]
        self.enable_slide_orient = True
        self.nurbs_plane_loop = None

        ## =======================
        ## Create Main Hierarchy
        ## =======================

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
        ### Assign Main Variables
        ################################

        self.list_sub_up_name = [
            "R_corner",
            "R_upB",
            "R_upA",
            "C_up",
            "L_upA",
            "L_upB",
            "L_corner",
        ]
        self.list_sub_low_name = [
            "L_lowB",
            "L_lowA",
            "C_low",
            "R_lowA",
            "R_lowB",
        ]
        self.list_sub_up_control = []
        self.list_sub_low_control = []

        self.list_sub_up_locator = []
        self.list_sub_low_locator = []

        #############################
        ### Create Bind Joints ######
        ##############################

        for name in self.list_sub_up_name + self.list_sub_low_name:
            m_pos = transform.getTransformFromPos(self.guide.pos[name])

            if name in self.list_sub_up_name:
                self.list_sub_up_locator.append(
                    primitive.addLocator(
                        self.grp_bind_loc,
                        self.getName("{}_loc".format(name)),
                        m=m_pos,
                    )
                )
            elif name in self.list_sub_low_name:
                self.list_sub_low_locator.append(
                    primitive.addLocator(
                        self.grp_bind_loc,
                        self.getName("{}_loc".format(name)),
                        m=m_pos,
                    )
                )

        # add locator to jnt pos
        for name, locator in zip(
            self.list_sub_up_name + self.list_sub_low_name,
            self.list_sub_up_locator + self.list_sub_low_locator,
        ):

            print(name, locator)

            self.jnt_pos.append(
                {
                    "obj": locator,
                    "name": name,
                    "newActiveJnt": "component_jnt_org",
                    "gearMulMatrix": False,
                    "vanilla_nodes": True,
                }
            )

        ## =======================
        ## Create Jaw Locator
        ## =======================

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

        ## =======================
        ## Create Oral Locator
        ## =======================

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

        ## =======================
        ## create Jaw Controller
        ## =======================

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

        ## =======================
        ## create Oral Controller
        ## =======================

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
        pm.connectAttr("{}.t".format(self.ctrl_inner), "{}.t".format(self.loc_inner))
        pm.connectAttr("{}.r".format(self.ctrl_inner), "{}.r".format(self.loc_inner))
        pm.connectAttr("{}.s".format(self.ctrl_inner), "{}.s".format(self.loc_inner))

        ## =======================
        ## create Main Controller
        ## =======================

        # create main joint
        self.L_main_joint = pm.createNode("joint", name=self.getName("L_main_jnt"))
        self.R_main_joint = pm.createNode("joint", name=self.getName("R_main_jnt"))
        self.up_main_joint = pm.createNode("joint", name=self.getName("up_main_jnt"))
        self.low_main_joint = pm.createNode("joint", name=self.getName("low_main_jnt"))

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

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        return

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
