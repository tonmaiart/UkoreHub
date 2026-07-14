import pymel.core as pm
from maya.cmds import parent
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.shifter import component
import math
import maya.api.OpenMaya as om

from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive

from TonmaiToolkit.core import Utility,Connection,Create,Misc,BlendShape,Transform,SkinWeight

class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        # Create Group Hierarchy -------------------------------
        self.grp_transform = pm.group(em=1, n=self.getName("transform_grp"), p=self.root)
        self.grp_controls = pm.group(em=1, n=self.getName("anim_controller_grp"), p=self.grp_transform)
        self.grp_spine_controls = pm.group(em=1, n=self.getName("spine_controller_grp"), p=self.grp_controls)
        self.grp_loc_bind_output = pm.group(em=1, n=self.getName("bind_locators_grp"), p=self.grp_transform)

        self.grp_no_transform = pm.group(em=1, n=self.getName("no_transform_grp"), p=self.root)
        self.grp_no_transform.inheritsTransform.set(False)

        self.grp_ribbon = pm.group(em=1, n=self.getName("ribbon_grp"), p=self.grp_no_transform)
        self.grp_ik_local_joints = pm.group(em=1, n=self.getName("ik_local_joints_grp"), p=self.grp_no_transform)

        # Declare variables -------------------------------
        self.rbn_ik = ""
        self.rbn_fk = ""
        self.rbn_base = ""
        self.rbn_middle_ik = ""
        self.rbn_output = ""

        self.dict_bind_loc = {}

        self.list_ik_joint = [None,None,None]
        self.list_ik_control = [None,None,None]

        self.list_fk_control = []

        self.jnt_spine_middle = ""
        self.jnt_spine_base_middle = ""

        self.jnt_driver_spine_start = ""
        self.jnt_driver_spine_end = ""

        self.spine_amount = self.settings["spine_amount"]
        self.loc_chest_parent = ""
        self.ctrl_mid = ""

        # ALL FUNCTION -------------------------------
        def create_bind_locator():
            # create list world position
            pos_hips = self.guide.pos["hips"]
            pos_spine_start = self.guide.pos["spineStart"]
            list_between_pos = Transform.get_linear_position_division(posA=self.guide.pos["spineStart"],
                                                                      posB=self.guide.pos["spineEnd"],
                                                                      division=self.spine_amount-2)

            # create locator and joint bind
            list_m_position = [transform.getTransformFromPos(pos) for pos in [pos_hips,pos_spine_start]+list_between_pos+[self.guide.pos["spineEnd"],self.guide.pos["chestPos"]]]
            list_loc_name = ["hips"]+["spine_{}".format(i+1) for i in range(self.spine_amount)]+["chest"]

            dict_create_loc_bind = dict(zip(list_loc_name,list_m_position))

            # create bind skin joints
            recent_joint = None

            for name,m_position in dict_create_loc_bind.items():
                locator = primitive.addLocator(self.grp_loc_bind_output, self.getName("{}_loc".format(name)), m=m_position)

                if recent_joint:
                    joint_parent = len(self.jnt_pos)-1
                else:
                    joint_parent = "parent_relative_jnt"

                self.jnt_pos.append({
                    "obj": locator,
                    "name": name,
                    "newActiveJnt": joint_parent,
                    "gearMulMatrix" : False,
                    "vanilla_nodes" : True
                })

                recent_joint = name
                self.dict_bind_loc[name] = locator

            # create loc chest parent
            self.loc_chest_parent = primitive.addLocator(self.grp_loc_bind_output, self.getName("chest_parent_loc"), m=transform.getTransformFromPos((0,0,0)))

            Connection.constraint_matrix(list_constraint=[self.dict_bind_loc["chest"],self.loc_chest_parent],
                                         method="parent",
                                         mo=False)

        def create_cog_ctrl():
            # create cog control
            self.ctrl_cog = self.addCtl(parent=self.grp_controls,
                                name="cog",
                                m=transform.getTransformFromPos(self.guide.pos["root"]),
                                color=14,
                                iconShape="circle",
                                w=0.7 * self.size,
                                h=0.7 * self.size,
                                d=0.7 * self.size,
                                )
            mgear.rigbits.addNPO([self.ctrl_cog])

        def create_spine_control():
            # create hips, spine 1, spine 2 ctrl

            list_name = ["hips","spine_low","spine_middle"]
            list_pos = [self.guide.pos["hips"],self.guide.pos["spineStart"],Transform.get_linear_position_division(self.guide.pos["spineStart"],self.guide.pos["spineEnd"])[0]]

            for name,pos in zip(list_name,list_pos):
                if name == "hips" or name == "spine_low":
                    parent = self.grp_spine_controls
                else:
                    parent = self.list_fk_control[-1]

                matrix = transform.getTransformFromPos(pos)

                if name == "hips":
                    ctrl_fk = self.addCtl(parent=parent,
                                          name="{}_fk".format(name),
                                          m=matrix,
                                          color=18,
                                          iconShape="square",
                                          w=0.55 * self.size,
                                          h=0.55 * self.size,
                                          d=0.55 * self.size,
                                          )

                else:
                    ctrl_fk = self.addCtl(parent=parent,
                                        name="{}_fk".format(name),
                                        m=matrix,
                                        color=6,
                                        iconShape="square",
                                        w=0.45 * self.size,
                                        h=0.45 * self.size,
                                        d=0.45 * self.size,
                                        )

                self.list_fk_control.append(ctrl_fk)

            mgear.rigbits.addNPO(self.list_fk_control)

        def create_ribbon():
            # create ribbon output
            size = Transform.get_distance_two([self.dict_bind_loc["hips"],self.dict_bind_loc["chest"]])/4

            # create base ribbon
            self.rbn_base = Create.draw_nurbs(
                list_ref_object=[self.dict_bind_loc["spine_{}".format(i+1)] for i in range(self.spine_amount)],
                name="base_ribbon",
                rebuild=True,
                loftDegree=3,
                size=size,
                parent=self.grp_spine_controls,
                du=3,
                dv=3,
                sv=2
            )

            # create fk ribbon
            self.rbn_fk = Create.draw_nurbs(
                list_ref_object=[self.dict_bind_loc["spine_{}".format(i+1)] for i in range(self.spine_amount)],
                name="fk_ribbon",
                rebuild=True,
                loftDegree=3,
                size=size,
                parent=self.grp_ribbon,
                du = 3,
                dv = 3,
                sv=2
            )

            # create middle ribbon
            self.rbn_middle_ik = Create.draw_nurbs(
                list_ref_object=[self.dict_bind_loc["spine_{}".format(i+1)] for i in range(self.spine_amount)],
                name="middle_ribbon",
                rebuild=True,
                loftDegree=3,
                size=size,
                parent=self.grp_ribbon,
                du = 3,
                dv = 3,
                sv=2

            )

            # create output ribbon
            self.rbn_output = Create.draw_nurbs(
                list_ref_object=[self.dict_bind_loc["spine_{}".format(i + 1)] for i in range(self.spine_amount)],
                name="output_ribbon",
                rebuild=True,
                loftDegree=3,
                size=size,
                parent=self.grp_ribbon,
                du=3,
                dv=3,
                sv=2
            )

        def create_spine_driver_joint():
            self.jnt_driver_spine_start = pm.createNode("joint",n="spine_driver_start")
            pm.matchTransform(self.jnt_driver_spine_start,self.list_ik_control[0])
            pm.parent(self.jnt_driver_spine_start,self.grp_spine_controls)
            Create.create_freeze_group([self.jnt_driver_spine_start])


            self.jnt_driver_spine_end = pm.createNode("joint",n="spine_driver_end")
            Utility.match_parent(self.jnt_driver_spine_end,self.list_ik_control[2])

        def create_pelvis_chest_control():
            # create tip pelvis and chest ik control
            for name in ["pelvis","chest"]:
                if name == "pelvis":
                    parent_driver = self.list_fk_control[0]
                    m_pos = transform.setMatrixScale(self.guide.tra["hips"],(1,1,1))

                elif name == "chest":
                    parent_driver = self.list_fk_control[-1]
                    m_pos = transform.setMatrixScale(self.guide.tra["chestPos"],(1,1,1))

                # create controller and parent
                ctrl_ik = self.addCtl(parent=self.grp_spine_controls,
                            name="{}_ik".format(name),
                            m=m_pos,
                            color=13,
                            iconShape="cube",
                            w=0.7 * self.size,
                            h=0.7 * self.size,
                            d=0.7 * self.size
                            )

                # constraint to npo's ctrl grp
                npo = mgear.rigbits.addNPO([ctrl_ik])[0]
                Connection.constraint_matrix(
                    [parent_driver,npo],
                    method="parent",
                    mo=True
                )

                if name == "pelvis":
                    self.list_ik_control[0] = ctrl_ik

                elif name == "chest":
                    self.list_ik_control[2] = ctrl_ik


        def create_middle_control():
            # create grp middle rig
            grp_middle_rig = pm.group(em=1,n=self.getName("midSpine_grp"),p=self.grp_spine_controls)

            # create control
            m_match = transform.getTransformFromPos(Transform.get_linear_position_division(posA=self.guide.pos["spineStart"],posB=self.guide.pos["spineEnd"])[0])
            self.ctrl_mid = self.addCtl(parent=grp_middle_rig,
                                  name=self.getName("MidIk"),
                                  m=m_match,
                                  color=21,
                                  iconShape="circle",
                                  w=0.5 * self.size,
                                  h=0.5 * self.size,
                                  d=0.5 * self.size)
            Create.create_freeze_group([self.ctrl_mid])

            # create middle joint
            self.jnt_spine_base_middle = pm.createNode("joint",name=self.getName("spine_base_middle_jnt"))
            pm.xform(self.jnt_spine_base_middle,ws=1,t=self.guide.pos["spineStart"])

            self.jnt_spine_middle = pm.createNode("joint",name=self.getName("spine_middle_jnt"))
            pm.xform(self.jnt_spine_middle,ws=1,m=m_match)

            # parent
            pm.parent(self.jnt_spine_base_middle, grp_middle_rig)
            pm.parent(self.jnt_spine_middle,self.ctrl_mid)

            # Shape and skinCluster
            shape = pm.listRelatives(self.rbn_middle_ik,c=1,s=1)[0]


            # Define the weights for each CV
            # weights = {
            #     'cv[0][0]': {
            #         self.jnt_spine_middle: 0.0,
            #         jnt_bot: 1.0,
            #         jnt_tip: 0.0
            #     },
            #     'cv[0][1]': {
            #         self.jnt_spine_middle: 0.0,
            #         jnt_bot: 1.0,
            #         jnt_tip: 0.0
            #     },
            #     'cv[1][0]': {
            #         self.jnt_spine_middle: 0.5,
            #         jnt_bot: 0.5,
            #         jnt_tip: 0.0
            #     },
            #     'cv[1][1]': {
            #         self.jnt_spine_middle: 0.5,
            #         jnt_bot: 0.5,
            #         jnt_tip: 0.0
            #     },
            #     'cv[2][0]': {
            #         self.jnt_spine_middle: 1.0,
            #         jnt_bot: 0.0,
            #         jnt_tip: 0.0
            #     },
            #     'cv[2][1]': {
            #         self.jnt_spine_middle: 1.0,
            #         jnt_bot: 0.0,
            #         jnt_tip: 0.0
            #     },
            #     'cv[3][0]': {
            #         self.jnt_spine_middle: 0.5,
            #         jnt_bot: 0.0,
            #         jnt_tip: 0.5
            #     },
            #     'cv[3][1]': {
            #         self.jnt_spine_middle: 0.5,
            #         jnt_bot: 0.0,
            #         jnt_tip: 0.5
            #     },
            #     'cv[4][0]': {
            #         self.jnt_spine_middle: 0.0,
            #         jnt_bot: 0.0,
            #         jnt_tip: 1.0
            #     },
            #     'cv[4][1]': {
            #         self.jnt_spine_middle: 0.0,
            #         jnt_bot: 0.0,
            #         jnt_tip: 1.0
            #     }
            # }

            # Apply weights
            # for cv, joint_weights in weights.items():
            #     component = f'{shape}.{cv}'
            #     pm.skinPercent(skinCluster_middle, component, transformValue=list(joint_weights.items()))

            self.list_ik_control[1] = self.ctrl_mid

        # RUN FUNCTION -------------------------------

        create_bind_locator()

        create_ribbon()

        create_cog_ctrl()
        create_spine_control()
        create_pelvis_chest_control()

        create_middle_control()

        create_spine_driver_joint()

    # =====================================================
    # CONNECTOR
    # =====================================================
    def addOperators(self):
        # $ Global Joints
        self.list_joint_spine = []
        # self.axis_direction = utils.get_triple_axis_enum()
        # -
        self.cog_pivot = ""
        self.use_root_joint_as_pivot = True

        # $ Guide Pivot
        self.list_fk_control_pivot = []
        self.locator_ik_chest_position = ""
        # # quick_create_guide

        # @ Extra Features
        # $ Auto Spine Scale Volume
        self.enable_auto_spine_scale = False
        # -
        self.list_scalable_volume_joint = []
        # -
        self.enable_auto_volume_as_default = True
        self.auto_volume_influence_detect = ["Ik Only", "Ik and Fk"]
        # * enable_auto_spine_scale

        # $ Chest Scale
        self.enable_breath_scale = False
        self.jnt_breath_scale = ""
        # * enable_breath_scale

        # $ Breast
        self.enable_breast_rig = False
        self.L_list_jnt_breast = []
        self.R_list_jnt_breast = []
        # * enable_breast_rig


        def make_finalize():
            if self.WIP:
                return

            Misc.finalize_visibility(self.grp_no_transform)


            for control in self.list_fk_control:
                Utility.lock_attribute(control, v=1, s=1, l=1, k=0)

            Utility.lock_attribute(self.list_ik_control[0], v=1, s=1, l=1, k=0)
            Utility.lock_attribute(self.list_ik_control[1], v=1, l=1, k=0)
            Utility.lock_attribute(self.list_ik_control[2], v=1, l=1, k=0)

            Utility.lock_attribute(self.ctrl_cog, s=1, v=1, l=1, k=0)

            pm.setAttr("{}.sy".format(self.list_ik_control[0]), k=0, l=1)
            pm.setAttr("{}.sy".format(self.list_ik_control[1]), k=0, l=1)
            pm.setAttr("{}.sy".format(self.list_ik_control[2]), k=0, l=1)

            self.grp_ribbon.visibility.set(False)

            for joint in pm.listRelatives(self.root,ad=1,type="joint"):
                joint.visibility.set(False)

            self.rbn_base.visibility.set(False)

            Misc.finalize_visibility(self.grp_loc_bind_output)
            # self.grp_loc_bind_output.visibility.set(False)

        def create_follicle_pin():
            self.list_follicles = Connection.pin_to_surface(
                list_pin=[self.dict_bind_loc["spine_{}".format(i+1)] for i in range(self.spine_amount)],
                surface=self.rbn_output,
                maintain_offset=True,
                prevent_double_transform=True
            )


        def constraint_fk():
            # constraint hips fk
            Connection.constraint_matrix([self.list_ik_control[0],self.dict_bind_loc["hips"]],mo=1,method="parent")
            Connection.constraint_matrix([self.list_ik_control[0],self.dict_bind_loc["hips"]],mo=1,method="scale")

            # constraint ik control to spine joint
            Connection.constraint_matrix([self.list_ik_control[0],self.jnt_driver_spine_start],
                                         method="point",
                                         mo=True)
            Connection.connect(self.list_ik_control[0],self.jnt_driver_spine_start,typ="rotate")

            # constraint chest
            Connection.constraint_matrix([self.list_ik_control[2],self.dict_bind_loc["chest"]],mo=1,method="parent")
            Connection.constraint_matrix([self.list_ik_control[2],self.dict_bind_loc["chest"]],mo=1,method="scale")

        def create_auto_scale_spine():
            def add_attribute():
                # add attribute
                Utility.add_attribute_divider(self.list_ik_control[1], "Volume")
                pm.addAttr(self.list_ik_control[1], ln="autoVolume", at="float", k=1, min=0, max=1)

                if self.enable_auto_volume_as_default:
                    pm.setAttr(self.list_ik_control[1] + ".autoVolume", 0.2)

            def connect_scale_out_factor():
                # get base arc length
                arc_length_name = "baseLength_ald".format(self.name)
                arc_length = pm.createNode("arcLengthDimension")
                transform_name = pm.listRelatives(arc_length, p=1, typ="transform")[0]
                pm.parent(transform_name, self.grp_no_transform)
                pm.rename(transform_name, arc_length_name)

                node_base_length = pm.listRelatives(arc_length_name, c=1, s=1)[0]

                pm.connectAttr("{}.worldSpace[0]".format(self.rbn_base), "{}.nurbsGeometry".format(node_base_length))
                pm.setAttr("{}.uParamValue".format(node_base_length), 1)
                pm.setAttr("{}.vParamValue".format(node_base_length), 0)

                attr_base_length = "{}.arcLength".format(node_base_length)

                # get fk length
                node_pma_length = pm.createNode("plusMinusAverage")
                list_control = [self.list_ik_control[0],self.list_fk_control[1],self.list_fk_control[2],self.list_ik_control[2]]

                for i,control in enumerate(list_control):
                    if i == len(list_control)-1:
                        break

                    next_control = list_control[i+1]

                    node_current_length = pm.createNode("distanceBetween")
                    control.worldMatrix[0] >> node_current_length.inMatrix1
                    next_control.worldMatrix[0] >> node_current_length.inMatrix2

                    pm.connectAttr("{}.distance".format(node_current_length),"{}.input1D[{}]".format(node_pma_length,i))

                attr_current_length = "{}.output1D".format(node_pma_length)

                # multiply scale factor
                node_md_scale = pm.createNode("multiplyDivide", n="{}_preserveVolume_mdv".format(self.name))
                pm.setAttr("{}.operation".format(node_md_scale), 2)

                pm.connectAttr(attr_base_length, "{}.input1X".format(node_md_scale))
                pm.connectAttr(attr_current_length, "{}.input2X".format(node_md_scale))

                return "{}.outputX".format(node_md_scale)
            
            def connect_scale_out_factor_with_arc_length():
                # create arc length
                list_arc_length = []
                for keyword in ["Base", "Output"]:
                    arc_length_name = "{}_spine{}_ald".format(self.name, keyword)
                    arc_length = pm.createNode("arcLengthDimension")
                    transform_name = pm.listRelatives(arc_length, p=1, typ="transform")[0]
                    pm.parent(transform_name, self.grp_no_transform)
                    pm.rename(transform_name, arc_length_name)

                    list_arc_length.append(pm.listRelatives(arc_length_name, c=1, s=1)[0])

                node_base_length, node_output_length = list_arc_length

                # connection arc length node
                pm.connectAttr("{}.worldSpace[0]".format(self.rbn_base), "{}.nurbsGeometry".format(node_base_length))
                pm.setAttr("{}.uParamValue".format(node_base_length), 1)
                pm.setAttr("{}.vParamValue".format(node_base_length), 0)

                # get target ribbon
                ribbon_target = self.rbn_fk

                pm.connectAttr("{}.worldSpace[0]".format(ribbon_target),
                               "{}.nurbsGeometry".format(node_output_length))
                pm.setAttr("{}.uParamValue".format(node_output_length), 1)
                pm.setAttr("{}.vParamValue".format(node_output_length), 0)

                # multiply scale factor
                node_md_scale = pm.createNode("multiplyDivide", n="{}_preserveVolume_mdv".format(self.name))
                pm.setAttr("{}.operation".format(node_md_scale), 2)

                pm.connectAttr("{}.arcLength".format(node_base_length), "{}.input1X".format(node_md_scale))
                pm.connectAttr("{}.arcLength".format(node_output_length), "{}.input2X".format(node_md_scale))

                return "{}.outputX".format(node_md_scale)

            def connect_by_pass_auto_scale():
                # blend attr node
                node_blend = pm.createNode("blendTwoAttr", n=self.getName("autoScaleBlend_bta"))
                pm.connectAttr("{}.autoVolume".format(self.list_ik_control[1]),
                               "{}.attributesBlender".format(node_blend))

                pm.setAttr("{}.input[0]".format(node_blend), 1)
                pm.connectAttr(attr_scale_out_factor, "{}.input[1]".format(node_blend))

                return "{}.output".format(node_blend)

            def connect_scale_to_joint():
                # sum and offset scale value
                node_pma_sum = pm.createNode("plusMinusAverage", n="{}_midScaleSum_pma".format(self.name))

                # connect scale outside
                for axis in "zx":
                    pm.connectAttr("{}.s{}".format(self.list_ik_control[1], axis),
                                   "{}.input3D[0].input3D{}".format(node_pma_sum, axis))

                    pm.connectAttr(attr_scale_out_factor_by_pass,
                                   "{}.input3D[1].input3D{}".format(node_pma_sum, axis))
                    pm.setAttr("{}.input3D[2].input3D{}".format(node_pma_sum, axis), -1)

                # apply scale to spine scalable joint
                for i, joint in enumerate([self.dict_bind_loc["spine_{}".format(i+1)] for i in range(self.spine_amount)]):

                    [pm.connectAttr("{}.output3D.output3D{}".format(node_pma_sum, axis),
                                    "{}.s{}".format(joint, axis)) for axis in "zx"]


            add_attribute()  # add attribute to ik mid control
            attr_scale_out_factor = connect_scale_out_factor()

            attr_scale_out_factor_by_pass = connect_by_pass_auto_scale()

            connect_scale_to_joint()

        def create_breast_rig():
            if not self.enable_breast_rig:
                return

            def create_each_side(list_joint, side=L):
                jnt_ik = pm.createNode("joint",n=self.getName("Breast_{}_IK_tip_jnt"))

                list_breast_joint_driver = [joint + "_driver" for joint in list_joint]
                list_breast_joint_control = [utils.cname(self.name, joint, ctrl) for joint in
                                             list_breast_joint_driver]
                ctrl_ik = utils.cname(self.name, jnt_ik, ctrl)

                # create driver joint
                for i, joint_bind in enumerate(list_joint):
                    joint_driver = list_breast_joint_driver[i]

                    # create joint
                    pm.select(cl=1)
                    pm.joint(n=joint_driver)
                    pm.matchTransform(joint_driver, joint_bind)

                    pm.parent(joint_driver, grp_breast_rig)

                    # constraint driver to bind joint
                    # pm.parentConstraint(joint_driver,joint_bind)

                # create ik driver joint
                pm.select(cl=1)
                pm.joint(n=jnt_ik)
                pm.matchTransform(jnt_ik, list_breast_joint_driver[1], pos=1)

                # create controller
                utils.create_control(name=list_breast_joint_control[0], match=list_breast_joint_driver[0],
                                     parent=grp_breast_rig, color="blue", size=6, freeze_group=True)
                utils.create_control(name=ctrl_ik, match=jnt_ik, parent=list_breast_joint_control[0],
                                     color="yellow", size=3, shape="sphere", freeze_group=True)
                utils.create_control(name=list_breast_joint_control[1], match=list_breast_joint_driver[1],
                                     parent=grp_breast_rig, color="blue", size=2, freeze_group=True)

                # re-parent driver joint chain
                pm.parent(jnt_ik, list_breast_joint_driver[0])
                pm.parent(list_breast_joint_driver[1], jnt_ik)

                # freeze joint
                pm.makeIdentity(jnt_ik, list_breast_joint_driver[0], a=1, r=1)

                # create ik handle
                ik_handle = pm.ikHandle(sj=list_breast_joint_driver[0], ee=jnt_ik, sol="ikSCsolver")[0]
                pm.parent(ik_handle, ctrl_ik)

                grp_frz = utils.freeze_group_classic(list_breast_joint_driver[0])[0]
                pm.parentConstraint(list_breast_joint_control[0], grp_frz)
                pm.parentConstraint(jnt_ik, pm.listRelatives(list_breast_joint_control[1], p=1)[0])

                # constraint to joint bind
                pm.parentConstraint(list_breast_joint_driver[0], list_joint[0])
                pm.pointConstraint(list_breast_joint_control[1], list_joint[1])



            # check joint
            if len(self.L_list_jnt_breast) != 2 or len(self.R_list_jnt_breast) != 2:
                pm.confirmDialog("Invalid Amount of Breast Joint")

            grp_breast_rig = pm.group(em=1, n=utils.cname(self.name, "Breast", grp), p=self.grp_local_anim)
            pm.parentConstraint(self.list_joint_spine[-1], grp_breast_rig)

            create_each_side(self.L_list_jnt_breast, side=L)
            create_each_side(self.R_list_jnt_breast, side=R)

        def create_breath_controls():
            # create control
            ctrl_breath = self.addCtl(parent=self.grp_spine_controls,
                                      name="breath",
                                      m=transform.getTransformFromPos(self.guide.pos["chestPos"]) ,
                                      color=17,
                                      iconShape="cube",
                                      size=1)
            pm.addAttr(ctrl_breath,ln="scaleAmp",k=1,min=0,max=1,dv=0.3)
            pm.addAttr(ctrl_breath,ln="FollowAmp",k=1,min=0,max=1,dv=0.1)
            pm.addAttr(ctrl_breath,ln="RotateAmpSide",k=1,dv=-0.02,min=-1,max=1)
            pm.addAttr(ctrl_breath,ln="RotateAmpFront",k=1,dv=0.02,min=-1,max=1)

            # add npo and constraint
            breath_control_npo = Create.create_freeze_group([ctrl_breath])[0]
            pm.parent(breath_control_npo,self.list_ik_control[2])
            # Connection.constraint_matrix([self.list_fk_control[2],breath_control_npo],
            #                              method="parent",mo=True)
            # Connection.constraint_matrix([self.list_fk_control[2],breath_control_npo],
            #                              method="scale",mo=True)

            grp_breath = Create.create_freeze_group([self.list_ik_control[2]],"BreathScl")[0]


            # rotate amp / tx > rz , tz > rx
            Connection.connect_conversion_unit(input="{}.tx".format(ctrl_breath),
                                               factor="{}.RotateAmpSide".format(ctrl_breath),
                                                output="{}.rz".format(grp_breath),
                                                use_factor_attr=True)

            Connection.connect_conversion_unit(input="{}.tz".format(ctrl_breath),
                                               factor="{}.RotateAmpFront".format(ctrl_breath),
                                                output="{}.rx".format(grp_breath),
                                                use_factor_attr=True)

            # follow amp / ty > ty
            node_uc_follow_amp = Connection.connect_conversion_unit(input="{}.ty".format(ctrl_breath),
                                               factor="{}.FollowAmp".format(ctrl_breath),
                                                                    output="{}.ty".format(grp_breath),
                                                                    use_factor_attr=True)

            # scale amp / ty > scale
            node_uc_scale = Connection.connect_conversion_unit(input="{}.ty".format(ctrl_breath),
                                               factor="{}.scaleAmp".format(ctrl_breath),
                                                               use_factor_attr=True)
            node_pma = pm.createNode("plusMinusAverage")

            pm.connectAttr("{}.output".format(node_uc_scale),"{}.input3D[0].input3Dx".format(node_pma))
            pm.connectAttr("{}.output".format(node_uc_scale),"{}.input3D[0].input3Dy".format(node_pma))
            pm.connectAttr("{}.output".format(node_uc_scale),"{}.input3D[0].input3Dz".format(node_pma))

            pm.setAttr("{}.input3D[1]".format(node_pma),1,1,1,typ="double3")

            pm.connectAttr("{}.output3D".format(node_pma),"{}.s".format(grp_breath))

            # lock attribute
            Utility.lock_attribute(ctrl_breath,r=True,s=True,v=True)
            pm.setAttr("{}.tx".format(ctrl_breath),l=1,k=0)
            pm.setAttr("{}.tz".format(ctrl_breath),l=1,k=0)
            # pm.setAttr("{}.rx".format(ctrl_breath),l=1,k=0)


        def constraint_cog():
            Connection.constraint_matrix([self.ctrl_cog,self.grp_spine_controls],
                                         method="parent",
                                         mo=1)
            Connection.constraint_matrix([self.ctrl_cog,self.grp_spine_controls],
                                         method="scale",
                                         mo=1)
        def create_blend_shape():
            blendshape = pm.blendShape(self.rbn_middle_ik,self.rbn_fk, self.rbn_output, af=1, at=1)[0]
            pm.setAttr("{}.{}".format(blendshape,self.rbn_middle_ik), 0)
            pm.setAttr("{}.{}".format(blendshape,self.rbn_fk), 1)

        def bind_skin_ribbon():
            # bind skin fk to ribbon
            self.skinCluster_fk = pm.skinCluster(self.jnt_driver_spine_start, self.jnt_driver_spine_end, self.rbn_fk,
                           n="{}_fkSurface_skinCluster".format(self.name),
                           mi=2, ih=1, tsb=1, dr=10, bm=3)
            
            old_data = {'fk_ribbon.cv[0][0]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[0][1]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[0][2]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[0][3]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[1][0]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[1][1]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[1][2]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[1][3]': {'spine_driver_start': 1.0, 'spine_driver_end': 0.0}, 'fk_ribbon.cv[2][0]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[2][1]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[2][2]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[2][3]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[3][0]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[3][1]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[3][2]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[3][3]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[4][0]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[4][1]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[4][2]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}, 'fk_ribbon.cv[4][3]': {'spine_driver_start': 0.0, 'spine_driver_end': 1.0}}


            new_data = SkinWeight.remap_and_apply_weights(
            weight_data=old_data,
            new_surface=self.rbn_fk,
            new_influences=[self.jnt_driver_spine_start, self.jnt_driver_spine_end],
            skinCluster=self.skinCluster_fk
        )

        def create_mid_spine_rig():

            # pin control grp
            grp_ctrl_mid_npo = pm.listRelatives(self.ctrl_mid,p=1,typ="transform")[0]
            grp_base_mid_npo = Create.create_freeze_group([self.jnt_spine_base_middle])[0]

            node_uv_pin = Connection.pin_to_surface(
                list_pin=[grp_ctrl_mid_npo],
                surface=self.rbn_fk,
                prevent_double_transform=True,
                maintain_offset=True
            )

            # add multi skin cluster
            skinCluster_middle = SkinWeight.add_multi_skin_cluster(
                mesh=self.rbn_fk,
                list_joint=[self.jnt_spine_base_middle,self.jnt_spine_middle],
                name=self.getName("SpineMid_SkinCluster")
            )            

            print(skinCluster_middle)
            
            # reconnect uv pin to avoid cycling
            self.skinCluster_fk.outputGeometry[0] >> node_uv_pin.deformedGeometry

            # connect bind pre matrix
            Connection.connect_bind_pre_matrix(
                list_transform=[self.ctrl_mid.getParent(),grp_base_mid_npo],
                list_joint=[self.jnt_spine_middle,self.jnt_spine_base_middle],
                skin_cluster=skinCluster_middle,
                attribute="worldInverseMatrix[0]"
            )

            # update skin weight preset
            skin_data = {'fk_ribbon.cv[0][0]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[0][1]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[0][2]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[0][3]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[1][0]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[1][1]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[1][2]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[1][3]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[2][0]': {'torso_C0_spine_middle_jnt': 1.0, 'torso_C0_spine_base_middle_jnt': 0.0}, 'fk_ribbon.cv[2][1]': {'torso_C0_spine_middle_jnt': 1.0, 'torso_C0_spine_base_middle_jnt': 0.0}, 'fk_ribbon.cv[2][2]': {'torso_C0_spine_middle_jnt': 1.0, 'torso_C0_spine_base_middle_jnt': 0.0}, 'fk_ribbon.cv[2][3]': {'torso_C0_spine_middle_jnt': 1.0, 'torso_C0_spine_base_middle_jnt': 0.0}, 'fk_ribbon.cv[3][0]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[3][1]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[3][2]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[3][3]': {'torso_C0_spine_middle_jnt': 0.5, 'torso_C0_spine_base_middle_jnt': 0.5}, 'fk_ribbon.cv[4][0]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[4][1]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[4][2]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}, 'fk_ribbon.cv[4][3]': {'torso_C0_spine_middle_jnt': 0.0, 'torso_C0_spine_base_middle_jnt': 1.0}}

            SkinWeight.remap_and_apply_weights(
                weight_data=skin_data,
                new_surface=self.rbn_fk,
                new_influences=[self.jnt_spine_middle,self.jnt_spine_base_middle],
                skinCluster=skinCluster_middle
            )

        bind_skin_ribbon()

        create_follicle_pin()

        constraint_cog()
        constraint_fk()

        create_mid_spine_rig()

        # scaling
        create_auto_scale_spine()
        create_breath_controls()

        create_blend_shape()

        make_finalize()

    def setRelation(self):
        self.relatives["root"] = self.dict_bind_loc["hips"]
        self.relatives["hips"] = self.dict_bind_loc["hips"]
        self.relatives["spineStart"] = self.dict_bind_loc["spine_1"]
        self.relatives["spineEnd"] = self.loc_chest_parent
        self.relatives["chestPos"] = self.loc_chest_parent

        self.controlRelatives["root"] = self.dict_bind_loc["hips"]

        self.jointRelatives["root"] = 0
        self.jointRelatives["hips"] = 0


        self.jointRelatives["spineEnd"] = -1
        self.jointRelatives["chestPos"] = -1

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


