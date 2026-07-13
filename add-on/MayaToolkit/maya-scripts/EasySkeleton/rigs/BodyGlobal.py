import maya.cmds as cmds
import EasySkeleton.config as config
from EasySkeleton import rig_class
from EasySkeleton.config import *
import EasySkeleton.utils as utils


class TorsoRibbon(rig_class.Rig):
    """TorsoRibbon

Create a torso part (using ribbon)

Variables:
name(string) : Name of part
axis_forward(string) : Name of Joint Pelvis
list_joint_spine(stringArray) : list of spine joints
list_fk_control_pivot(stringArray) : list of fk spine controller, first one will be pelvis , the after one will be spine chain , the last one will be chest control (Reference Position ,Orientation)

ribbon_fk_weight(path) : Xml Path
ribbon_ik_weight(path) : Xml Path
ribbon_ik_middle_weight(path) : Xml Path

axis_side(string) : axis side

cog_pivot (string) : cog_pivot
use_root_joint_as_pivot (bool): use_root_joint_as_pivot

locator_ik_chest_position(string): Locator of ik chest control (Reference Position ,Orientation)
list_scalable_volume_joint(stringArray): list_scalable_volume_joint

axis_scale_outside(string) : "x"
axis_scale_stretch(string) : "yz"

enable_breath_scale(bool): enable_breath_scale
jnt_breath_scale(string) : jnt_breath_scale

axis_direction(enum) : [Axis Forward,Axis Side,Axis Up]
quick_create_guide(script) : Quick Build Torso Pivot

enable_auto_volume_as_default(bool) : enable_auto_volume_as_default

enable_breast_rig (bool) : False
L_list_jnt_breast (stringArray) : joint breast
R_list_jnt_breast (stringArray) : joint breast

enable_auto_spine_scale(bool) : enable_auto_spine_scale
auto_volume_influence_detect(enum) : Detect Influence Case

select_fk_ribbon(script) : Quick Build Torso Pivot
select_ik_ribbon(script) : Quick Build Torso Pivot
select_ik_middle_ribbon(script) : Quick Build Torso Pivot

    """

    def __init__(self):
        super().__init__()
        # @ Required
        self.name = "torso"

        # $ Global Joints
        self.list_joint_spine = []
        self.axis_direction = utils.get_triple_axis_enum()
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
        self.auto_volume_influence_detect = ["Ik Only","Ik and Fk"]
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

        # $ Auto Import Skin Weight
        self.ribbon_fk_weight = ""
        self.ribbon_ik_weight = ""
        self.ribbon_ik_middle_weight = ""
        # # select_fk_ribbon
        # # select_ik_ribbon
        # # select_ik_middle_ribbon

        self.debug_mode = False

    def quick_create_guide(self):
        self.variables()

        print(self.grp_local_rig)


    def core_build(self):
        def make_finalize():
            if self.debug_mode:
                return

            utils.finalize_visibility(self.grp_local_rig)

            for control in list_fk_controls:
                utils.lock_attributes(control, v=1, s=1, l=1, k=0)

            utils.lock_attributes(list_ik_controls[0], v=1, s=1, l=1, k=0)
            utils.lock_attributes(list_ik_controls[1], v=1, l=1, k=0)
            utils.lock_attributes(list_ik_controls[2], v=1, l=1, k=0)

            utils.lock_attributes(ctrl_cog, s=1, v=1, l=1, k=0)

            cmds.setAttr("{}.s{}".format(list_ik_controls[2], axis_forward_abs), k=0, l=1)
            cmds.setAttr("{}.s{}".format(list_ik_controls[1], axis_forward_abs), k=0, l=1)

            utils.add_notes([ctrl_cog]+list_ik_controls+list_fk_controls)

        def check_input():
            if not self.list_fk_control_pivot:
                raise Exception("List Fk Control Pivot Must Be Input")
            if not self.locator_ik_chest_position:
                raise Exception("Ik Chest Pivot Must Be Input")

        def create_hierarchy():
            cmds.group(em=1, n=grp_fk_controls, p=self.grp_local_anim)
            cmds.group(em=1, n=grp_ik_controls, p=self.grp_local_anim)

            cmds.group(em=1, n=grp_ribbon, p=self.grp_local_still)
            cmds.group(em=1, n=grp_ik_local_joints, p=self.grp_local_still)

        def create_cog():
            utils.create_control(name=ctrl_cog,
                                 match=self.cog_pivot,
                                 parent=self.grp_local_anim,
                                 color="yellow",
                                 size=3)
            cmds.parentConstraint(ctrl_cog, self.cog_pivot) if self.use_root_joint_as_pivot else None
            utils.freeze_group_classic(ctrl_cog)

        def create_ribbon():
            # create ribbon output
            list_point = [cmds.xform(joint, ws=1, t=1, q=1) for joint in self.list_joint_spine]
            crv_1 = cmds.curve(p=list_point, d=1)
            crv_2 = cmds.curve(p=list_point, d=1)
            size = utils.get_distance_two(self.list_joint_spine[0], self.list_joint_spine[1]) / 2
            cmds.xform(crv_1, ws=1, t=(size, 0, 0), r=1)
            cmds.xform(crv_2, ws=1, t=(size * -1, 0, 0), r=1)
            temp_ribbon = cmds.loft(crv_1, crv_2, ch=0, ar=1, po=0, rsn=1, ss=1, u=1)
            cmds.delete(crv_1, crv_2)
            cmds.parent(temp_ribbon,grp_ribbon)

            # rebuild and duplicate
            for ribbon in [rbn_ik,rbn_fk, rbn_base,rbn_middle_ik]:
                cmds.duplicate(temp_ribbon, n=ribbon)

                u_sub = len(self.list_joint_spine) - 1
                cmds.rebuildSurface(ribbon, su=u_sub, sv=1, du=1, dv=1, ch=0, kr=0, rt=0)

                if not utils.is_child_of(ribbon,grp_ribbon):
                    cmds.parent(ribbon, grp_ribbon)

            cmds.delete(temp_ribbon)
        def create_follicle_pin():
            # pin follicle
            grp_follicle = cmds.group(em=1, n="{}_flcSkin_{}".format(self.name, grp), p=self.grp_local_still)

            for i, joint in enumerate(self.list_joint_spine):
                grp_pin = cmds.group(em=1, n="{}_flcOffset{}_{}".format(self.name, i + 1, grp), p=grp_follicle)

                cmds.matchTransform(grp_pin, joint)

                follicle_name = "flc_{}{}".format(self.name, i + 1)
                utils.pin_ribbon(list_pin=[grp_pin],
                                 surface=rbn_fk,
                                 output_parent=grp_follicle,
                                 name=follicle_name)
                cmds.parent(grp_pin, follicle_name)

                # create locator
                locator_name = "{}_{}".format(joint, loc)
                cmds.spaceLocator(n=locator_name)
                utils.matchAllTransform(locator_name, joint)
                cmds.parent(locator_name, grp_pin)

                list_locator_bind.append(locator_name)
                list_flc_skin.append(follicle_name)

        def apply_bind_joint_constraint():
            # constraint locator to bind joints
            for i in range(len(list_locator_bind)):
                # use orient and point constraint for the last (for some reason?)
                if i == 0:
                    cmds.pointConstraint(list_locator_bind[i],self.list_joint_spine[i])
                    cmds.orientConstraint(list_ik_controls[0],self.list_joint_spine[i])

                elif i == len(list_locator_bind)-1:
                    cmds.pointConstraint(list_locator_bind[i],self.list_joint_spine[i])
                    cmds.orientConstraint(list_ik_controls[1],self.list_joint_spine[i])

                else:

                    cmds.parentConstraint(list_locator_bind[i], self.list_joint_spine[i])


        def fix_scale():
            grp_get_scale = cmds.group(em=1, n="{}_scaleSpace_grp".format(self.name), p=self.grp_local_still)
            cmds.scaleConstraint(self.grp_local_anim, grp_get_scale)

            for follicle in list_flc_ik + list_flc_skin:
                grp_scale_output = cmds.group(em=1, n="{}_scaleFix_grp".format(follicle))

                cmds.matchTransform(grp_scale_output, grp_get_scale, rot=1)
                cmds.matchTransform(grp_scale_output, follicle, pos=1)

                [cmds.parent(child, grp_scale_output) for child in cmds.listRelatives(follicle, c=1, typ="transform")]

                cmds.parent(grp_scale_output, follicle)

                cmds.connectAttr(grp_get_scale + ".s", grp_scale_output + ".s")

        def create_fk_controls():
            cmds.parentConstraint(ctrl_cog, grp_fk_controls)

            recent_control = None

            for i in range(len(self.list_fk_control_pivot)):
                ctrl_fk = "{}_SpineFk{}_{}".format(self.name, i + 1, ctrl)
                jnt_fk = "{}_SpineFk{}_{}".format(self.name, i + 1, jnt)

                # create control
                utils.create_control(name=ctrl_fk,
                                     match=self.list_fk_control_pivot[i],
                                     color="blue",
                                     size=2)

                # create joint
                cmds.select(cl=1)
                cmds.joint(n=jnt_fk)

                # start and tip position of joint will be different
                if i == 0:
                    utils.snap_to_surface(source=rbn_fk,
                                          object=jnt_fk,
                                          u=0,
                                          v=0.5,
                                          snap="point")

                elif i == len(self.list_fk_control_pivot) - 1:
                    utils.snap_to_surface(source=rbn_fk,
                                          object=jnt_fk,
                                          u=1,
                                          v=0.5,
                                          snap="point")
                else:
                    cmds.matchTransform(jnt_fk, self.list_fk_control_pivot[i], pos=1)

                cmds.parent(jnt_fk, ctrl_fk)

                # chain in hierarchy (pelvis will be separate out of chain)
                if i == 0 or i == 1:
                    cmds.parent(ctrl_fk, ctrl_cog)
                else:
                    cmds.parent(ctrl_fk, recent_control)

                recent_control = ctrl_fk

                list_fk_joints.append(jnt_fk)
                list_fk_controls.append(ctrl_fk)

            # create tips joint
            jnt_fk = "{}_SpineFkEnd_{}".format(self.name, jnt)
            cmds.select(cl=1)
            cmds.joint(n=jnt_fk)
            cmds.matchTransform(jnt_fk, self.list_joint_spine[-1])
            cmds.parent(jnt_fk, list_fk_controls[-1])
            list_fk_joints.append(jnt_fk)

            # freeze all control
            utils.freeze_group_classic(list_fk_controls)

            # bind skin fk joints to ribbon
            node_skin_fk = cmds.skinCluster(list_fk_joints, rbn_fk, n="{}_fkSurface_skinCluster".format(self.name), mi=2, ih=1, tsb=1, dr=10, bm=3)
            utils.import_weight(node_skin_fk,self.ribbon_fk_weight) if self.ribbon_fk_weight else None

        def create_ik_controls():
            def create_middle_control():
                # create mid ik control
                tmp_mid_match_orient = cmds.spaceLocator()[0]
                utils.matchTransform(tmp_mid_match_orient,self.list_joint_spine[0],rot=True)
                utils.snap_to_nearest_90(tmp_mid_match_orient)

                # create joint
                jnt_blank = cmds.joint()
                cmds.select(cl=1)

                jnt_middle_ik = cmds.joint()
                cmds.select(cl=1)

                # snap joint middle ik position to spine nurbs
                utils.snap_to_surface(rbn_middle_ik,jnt_middle_ik,u=0.5,v=0.5,percentage=True,snap="point")
                print("snapped")

                cmds.parent(jnt_middle_ik,jnt_blank,grp_ik_local_joints)
                utils.freeze_group_classic([jnt_blank,jnt_middle_ik])

                # create grp pin
                flc_name = "{}_MidCtrlIk_{}".format(self.name, flc)
                ctrl_mid = "{}_MidIk_{}".format(self.name, ctrl)

                # create control
                grp_pin = "{}_MidCtrlIk_{}".format(self.name, grpOff)
                cmds.group(em=1, n=grp_pin, p=grp_ik_controls)
                cmds.parentConstraint(list_fk_controls[2],grp_pin)

                utils.create_control(name=ctrl_mid,match=grp_pin,parent=grp_pin,size=1.8)
                utils.connect(ctrl_mid,jnt_middle_ik)

                node_skin_middle = cmds.skinCluster(jnt_blank, jnt_middle_ik, rbn_middle_ik, n="{}_middle_skinCluster".format(self.name), mi=2, ih=1, tsb=1, dr=3, bm=3)
                utils.import_weight(node_skin_middle, self.ribbon_ik_middle_weight) if  self.ribbon_ik_middle_weight else None

                # delete temp
                cmds.delete(tmp_mid_match_orient)

                list_ik_controls.append(ctrl_mid)

            def create_pelvis_chest_control():
                # create tip pelvis and chest ik control
                for i in range(2):
                    if i == 0:
                        name = "pelvis"
                        pin_constraint = list_fk_controls[0]
                    elif i == 1:
                        name = "chest"
                        pin_constraint = list_fk_controls[-1]
                    else:
                        raise Exception()

                    ctrl_ik = "{}_ik{}_{}".format(self.name, name, ctrl)
                    jnt_ik = "{}_ik{}_{}".format(self.name, name, jnt)

                    # create controller and parent
                    utils.create_control(name=ctrl_ik,
                                         match=pin_constraint,
                                         parent=grp_ik_controls,
                                         size=1.8,
                                         freeze_group=True)

                    grp_frz = cmds.listRelatives(ctrl_ik,p=1)[0]
                    cmds.parentConstraint(pin_constraint,grp_frz)

                    # create local joint
                    cmds.select(cl=1)
                    cmds.joint(n=jnt_ik)
                    cmds.select(cl=1)

                    utils.matchAllTransform(jnt_ik,ctrl_ik)
                    cmds.parent(jnt_ik,grp_ik_local_joints)
                    cmds.makeIdentity(jnt_ik, a=1, r=1)
                    utils.freeze_group_classic(jnt_ik,grpOff)

                    utils.connect(ctrl_ik,jnt_ik)

                    # finalize
                    list_ik_joints.append(jnt_ik)
                    list_ik_controls.append(ctrl_ik)
                    # list_flc_ik.append(flc_name)

                # bind skin to ik ribbon
                node_skin_ik = cmds.skinCluster(list_ik_joints[0], list_ik_joints[1], rbn_ik, n="{}_ik_skinCluster".format(self.name), mi=2, ih=1, tsb=1, dr=3, bm=3)
                utils.import_weight(node_skin_ik, self.ribbon_ik_weight) if  self.ribbon_ik_weight else None

            create_pelvis_chest_control()
            create_middle_control()

        def create_auto_scale_spine():
            def add_attribute():
                # add attribute
                utils.add_attribute_divider(list_ik_controls[1], "Volume")
                cmds.addAttr(list_ik_controls[1], ln="autoVolume", at="float", k=1, min=0, max=1)

                if self.enable_auto_volume_as_default:
                    cmds.setAttr(list_ik_controls[1]+".autoVolume",1)

            def connect_scale_out_factor():
                # parent rbn base to grp torso anim
                cmds.parent(rbn_base,self.grp_local_anim)
                utils.freeze_group_classic(rbn_base)

                # create arc length
                list_arc_length = []
                for keyword in ["Base", "Output"]:
                    arc_length_name = "{}_spine{}_ald".format(self.name, keyword)
                    arc_length = cmds.createNode("arcLengthDimension")
                    transform_name = cmds.listRelatives(arc_length, p=1, typ="transform")[0]
                    cmds.parent(transform_name, self.grp_local_still)
                    cmds.rename(transform_name, arc_length_name)

                    list_arc_length.append(cmds.listRelatives(arc_length_name, c=1, s=1)[0])

                node_base_length, node_output_length = list_arc_length

                # connection arc length node
                cmds.connectAttr("{}.worldSpace[0]".format(rbn_base), "{}.nurbsGeometry".format(node_base_length))
                cmds.setAttr("{}.uParamValue".format(node_base_length), 1)
                cmds.setAttr("{}.vParamValue".format(node_base_length), 0)

                if self.auto_volume_influence_detect == 0:
                    ribbon_target =  rbn_ik
                elif self.auto_volume_influence_detect == 1:
                    ribbon_target = rbn_fk
                else:
                    raise Exception("Error")

                cmds.connectAttr("{}.worldSpace[0]".format(ribbon_target), "{}.nurbsGeometry".format(node_output_length))
                cmds.setAttr("{}.uParamValue".format(node_output_length), 1)
                cmds.setAttr("{}.vParamValue".format(node_output_length), 0)

                # multiply scale factor
                node_md_scale = cmds.createNode("multiplyDivide", n="{}_preserveVolume_mdv".format(self.name))
                cmds.setAttr("{}.operation".format(node_md_scale), 2)

                cmds.connectAttr("{}.arcLength".format(node_base_length), "{}.input1X".format(node_md_scale))
                cmds.connectAttr("{}.arcLength".format(node_output_length), "{}.input2X".format(node_md_scale))

                return "{}.outputX".format(node_md_scale)

            def connect_by_pass_auto_scale():
                # blend attr node
                node_blend = cmds.createNode("blendTwoAttr",n=utils.cname(self.name,"autoScaleBlend","bta"))
                cmds.connectAttr("{}.autoVolume".format(list_ik_controls[1]), "{}.attributesBlender".format(node_blend))

                cmds.setAttr("{}.input[0]".format(node_blend),1)
                cmds.connectAttr(attr_scale_out_factor, "{}.input[1]".format(node_blend))

                return "{}.output".format(node_blend)

            def connect_scale_to_joint():
                # sum and offset scale value
                node_pma_sum = cmds.createNode("plusMinusAverage", n="{}_midScaleSum_pma".format(self.name))

                # connect scale outside
                for axis in [axis_side_abs, axis_up_abs]:
                    cmds.connectAttr("{}.s{}".format(list_ik_controls[1], axis), "{}.input3D[0].input3D{}".format(node_pma_sum, axis))

                    cmds.connectAttr(attr_scale_out_factor_by_pass, "{}.input3D[1].input3D{}".format(node_pma_sum, axis))
                    cmds.setAttr( "{}.input3D[2].input3D{}".format(node_pma_sum, axis),-1)


                # apply scale to spine scalable joint
                for i, joint in enumerate(self.list_scalable_volume_joint):
                    # ignore chest joint
                    if joint == self.jnt_breath_scale:
                        continue

                    [cmds.connectAttr("{}.output3D.output3D{}".format(node_pma_sum, axis), "{}.s{}".format(joint, axis)) for axis in [axis_side_abs,axis_up_abs]]

                # # apply scale to chest joint
                # if self.enable_breath_scale:
                #     if not self.jnt_breath_scale:
                #         raise Exception("Invalid Breath Scale Joint")
                #
                #     node_pma_sum = cmds.createNode("plusMinusAverage", n="{}_chestScaleSum_pma".format(self.name))
                #     node_pma_offset = cmds.createNode("plusMinusAverage", n="{}_chestScaleOffset_pma".format(self.name))
                #
                #     for axis in [axis_side_abs,axis_up_abs]:
                #         cmds.connectAttr(output, "{}.input3D[0].input3D{}".format(node_pma_sum, axis))
                #         cmds.connectAttr("{}.s{}".format(list_ik_controls[2], axis), "{}.input3D[1].input3D{}".format(node_pma_sum, axis))
                #
                #         cmds.setAttr(node_pma_offset + ".operation", 2)
                #         cmds.connectAttr("{}.output3D{}".format(node_pma_sum, axis), "{}.input3D[0].input3D{}".format(node_pma_offset, axis))
                #         cmds.setAttr("{}.input3D[1].input3D{}".format(node_pma_offset, axis), 1)
                #
                #         output = "{}.output3D{}".format(node_pma_offset, axis)

            if not self.enable_auto_spine_scale:
                return

            add_attribute() # add attribute to ik mid control
            attr_scale_out_factor = connect_scale_out_factor()

            attr_scale_out_factor_by_pass = connect_by_pass_auto_scale()

            connect_scale_to_joint()

        def create_breast_rig():
            def create_each_side(list_joint,side=L):
                jnt_ik = utils.cname(self.name,"Breast_{}_IK_tip".format(side),jnt)

                list_breast_joint_driver = [joint + "_driver" for joint in list_joint]
                list_breast_joint_control = [utils.cname(self.name,joint,ctrl) for joint in list_breast_joint_driver]
                ctrl_ik = utils.cname(self.name,jnt_ik,ctrl)

                # create driver joint
                for i,joint_bind in enumerate(list_joint):
                    joint_driver = list_breast_joint_driver[i]

                    # create joint
                    cmds.select(cl=1)
                    cmds.joint(n=joint_driver)
                    cmds.matchTransform(joint_driver,joint_bind)

                    cmds.parent(joint_driver,grp_breast_rig)

                    # constraint driver to bind joint
                    # cmds.parentConstraint(joint_driver,joint_bind)

                # create ik driver joint
                cmds.select(cl=1)
                cmds.joint(n=jnt_ik)
                cmds.matchTransform(jnt_ik, list_breast_joint_driver[1],pos=1)

                # create controller
                utils.create_control(name=list_breast_joint_control[0],match=list_breast_joint_driver[0],parent=grp_breast_rig,color="blue",size=6,freeze_group=True)
                utils.create_control(name=ctrl_ik,match=jnt_ik,parent=list_breast_joint_control[0],color="yellow",size=3,shape="sphere",freeze_group=True)
                utils.create_control(name=list_breast_joint_control[1],match=list_breast_joint_driver[1],parent=grp_breast_rig,color="blue",size=2,freeze_group=True)

                # re-parent driver joint chain
                cmds.parent(jnt_ik,list_breast_joint_driver[0])
                cmds.parent(list_breast_joint_driver[1],jnt_ik)

                # freeze joint
                cmds.makeIdentity(jnt_ik,list_breast_joint_driver[0], a=1, r=1)

                # create ik handle
                ik_handle = cmds.ikHandle(sj=list_breast_joint_driver[0],ee=jnt_ik,sol="ikSCsolver")[0]
                cmds.parent(ik_handle,ctrl_ik)

                grp_frz = utils.freeze_group_classic(list_breast_joint_driver[0])[0]
                cmds.parentConstraint(list_breast_joint_control[0],grp_frz)
                cmds.parentConstraint(jnt_ik,cmds.listRelatives(list_breast_joint_control[1],p=1)[0])

                # constraint to joint bind
                cmds.parentConstraint(list_breast_joint_driver[0],list_joint[0])
                cmds.pointConstraint(list_breast_joint_control[1],list_joint[1])

            if not self.enable_breast_rig:
                return

            # check joint
            if len(self.L_list_jnt_breast )!= 2 or len(self.R_list_jnt_breast )!= 2:
                cmds.confirmDialog("Invalid Amount of Breast Joint")

            grp_breast_rig = cmds.group(em=1,n=utils.cname(self.name,"Breast",grp),p=self.grp_local_anim)
            cmds.parentConstraint(self.list_joint_spine[-1],grp_breast_rig)

            create_each_side(self.L_list_jnt_breast,side=L)
            create_each_side(self.R_list_jnt_breast,side=R)


        # defined variables
        axis_forward_abs,axis_side_abs,axis_up_abs  =utils.convert_triple_axis_enum(self.axis_direction)

        grp_fk_controls = "{}_Fk_grp".format(self.name, grp)

        grp_ik_controls = "{}_Ik_grp".format(self.name, grp)
        grp_ik_local_joints = "{}_Ik_local_grp".format(self.name, grp)

        grp_ribbon = "{}_{}Nurbs".format(grp, self.name)
        ctrl_cog = "{}_cog".format(ctrl)

        rbn_middle_ik = "{}_middle_ik_{}".format(self.name, nrb)
        rbn_fk = "{}_fk_{}".format(self.name, nrb)
        rbn_ik = "{}_ik_{}".format(self.name, nrb)
        rbn_base = "{}_base_{}".format(self.name,nrb)

        list_locator_bind = []
        list_fk_joints = []
        list_ik_joints = []

        list_fk_controls = []
        list_ik_controls = []

        list_flc_ik = []
        list_flc_skin = []

        # build
        check_input()
        create_hierarchy()

        create_ribbon()
        create_follicle_pin()
        create_cog()


        create_fk_controls()
        create_ik_controls()

        blendshape = cmds.blendShape(rbn_ik,rbn_middle_ik,rbn_fk,af=1,at=1)[0]
        cmds.setAttr(blendshape+"."+rbn_ik,1)
        cmds.setAttr(blendshape+"."+rbn_middle_ik,1)


        apply_bind_joint_constraint()
        # fix_scale()

        create_auto_scale_spine()

        #
        create_breast_rig()
        #
        make_finalize()

class QuadrupedLimb(rig_class.Rig):
    """BackLeg

Create a BackLeg

Variables:
name(string) : Name of part
list_joint_chain (stringArray) : Required 6 Joints, List Leg Joints,for example [UpLeg , LowLeg, Hock , Ankle ,Ball , Tip Ball]
axis_pole(enum) : Lock and hide unnecessary attributes and object for animators
axis_forward(enum) : Axis of forward Direction
limb_type(enum) : Type of Leg
default_switch(enum) : default_switch
pole_distance(float) : Distance of pole vector
pole_axis_direction(enum) : Axis of Pole Direction

list_ribbon_up_joints (stringArray) : list ribbon of up joints
ignore_start_and_end_joint_for_up (bool) : False

list_ribbon_low_joints (stringArray) : list ribbon of low joints
ignore_start_and_end_joint_for_up (bool) : False

invert_hock_side(bool) : False
invert_hock_forward(bool) : False

enable_clavicle(bool) : enable_clavicle
clavicle_joint(string) : enable_clavicle

clavicle_space_switch(bool) : Enable Space Switch for Clavicle Control.
clavicle_space_target(stringArray) : List of Object Name of space target.
clavicle_space_name(stringArray) :  List of Nice Name of space target.

foot_space_switch(bool): When Checked, Hand Ik Space Switch Enum Attributes will be created.
foot_space_target(stringArray) : List Of Enum Target
foot_space_name(stringArray) : List Of Enum Target Nice Name (Must Match Count with Target,Else Error)

fk_root_space_switch(bool) : If checked, Enable Space Switch for root fk orient,such as shoulder or thigh.
fk_root_space_target(stringArray) : List of object that will be the parent of spaces.
fk_root_space_name(stringArray): List of object that will be the parent of spaces name.

"""

    def __init__(self):
        super().__init__()

        self.name = "{}_Leg".format(L)

        # @ Required
        self.limb_type = ["Front Leg","Back Leg"]
        # -
        self.list_joint_chain = []
        # -
        self.axis_forward = utils.get_single_axis_enum()
        self.axis_pole = utils.get_single_axis_enum()
        self.default_switch = ["FK","IK"]

        # $ Add Clavicle
        self.enable_clavicle = False
        self.clavicle_joint = ""

        # $ Hock Setting
        self.invert_hock_side = False
        self.invert_hock_forward = False

        # $ Pole Setting
        self.pole_distance = 10
        self.pole_axis_direction = utils.get_single_axis_enum_pos()

        # @ Optional
        # $ Fk Root Control Space Switch (Orient)
        self.fk_root_space_switch = False
        self.fk_root_space_target = []
        self.fk_root_space_name = []
        # * fk_root_space_switch

        # $ Ik End Control Space Switch (Parent)
        self.foot_space_switch = False
        self.foot_space_target = []
        self.foot_space_name = []
        # * foot_space_switch

        # $ Clavicle Control Space Switch (Orient)
        self.clavicle_space_switch = False
        self.clavicle_space_target = []
        self.clavicle_space_name = []
        # * clavicle_space_switch

        # $ Ribbon Features
        self.list_ribbon_up_joints = []
        self.ignore_start_and_end_joint_for_up = False
        # -
        self.list_ribbon_low_joints = []
        self.ignore_start_and_end_joint_for_up = False

        self.debug_mode = False
        self.parent = ""
        self.mirror_control_scale = False

    def core_build(self):
        def create_clavicle_control():
            if self.enable_clavicle:
                utils.create_control(name=ctrl_clavicle,
                                     match=self.clavicle_joint,
                                     constraint="parent",
                                     freeze_group=True,
                                     mirror_freeze_group=self.mirror_control_scale,
                                     parent=self.grp_local_anim)


        def check_input():
            if len(self.list_joint_chain) != 6:
                raise Exception("Invalid Amount of Input Joint, Must be 5 , get {}".format(len(self.list_joint_chain)))
            for joint in self.list_joint_chain:
                if not cmds.objExists(joint):
                    raise Exception("Not Found Joint Input {} ".format(joint))

                if not cmds.objectType(joint,isa="joint"):
                    raise Exception("Wrong Input Type : required joint")

        def create_hierarchy():
            cmds.group(em=1,n=grp_limb_parent,p=self.grp_local_anim)

            cmds.group(em=1,n=grp_ik_joint,p=grp_limb_parent)
            cmds.group(em=1,n=grp_fk_joint,p=grp_limb_parent)

            cmds.group(em=1,n=grp_ik_control,p=grp_limb_parent)
            cmds.group(em=1,n=grp_fk_control,p=grp_limb_parent)

        def create_blend_space():
            if self.foot_space_switch:
                grp_output = utils.create_enum_space_classic(object_attr=list_ik_control[3],
                                                             list_space=self.foot_space_target,
                                                             list_nice_name=self.foot_space_name,
                                                             target=list_ik_control[3],
                                                             type="parent")

                cmds.parent(grp_output, self.grp_local_still)


            if self.fk_root_space_switch:
                grp_output = utils.create_enum_space_classic(object_attr=list_fk_control[0],
                                                             list_space=self.fk_root_space_target,
                                                             list_nice_name=self.fk_root_space_name,
                                                             target=list_fk_control[0],
                                                             type="orient")
                cmds.parent(grp_output, self.grp_local_rig)


            if self.clavicle_space_switch:
                grp_output = utils.create_enum_space_classic(list_space=self.clavicle_space_target,
                                         list_nice_name=self.clavicle_space_name,
                                                target=ctrl_clavicle,
                                                type="orient",
                                                object_attr=ctrl_clavicle)

                cmds.parent(grp_output, self.grp_local_rig)

        def make_finalize():
            if self.debug_mode:
                return

            for control in list_fk_control:
                utils.lock_attributes(control, t=1, s=1, v=1, l=1, k=0)

            for control in list_ik_control:
                utils.lock_attributes(control, s=1, v=1, l=1, k=0)

            utils.lock_attributes(list_ik_control[0], r=1, l=1, k=0)
            utils.lock_attributes(list_ik_control[1], r=1, l=1, k=0)
            utils.lock_attributes(list_ik_control[2], r=1, l=1, k=0)

        def create_ik_systems():
            def create_ik_control():
                for i,control in enumerate(list_ik_control[0:4]):
                    # ignore tip joint and ball joint

                    joint = list_ik_joint[i]

                    utils.create_control(control,parent=grp_ik_control,match=joint)

                # reposition the pole control
                move_axis = {"x":(self.pole_distance,0,0),
                             "y":(0,self.pole_distance,0),
                             "z":(0,0,self.pole_distance)}

                cmds.xform(list_ik_control[1],ws=1,ro=(0,0,0))
                cmds.xform(list_ik_control[1],ws=1,t=move_axis[self.pole_axis_direction],r=1)

                # parent pole control to ankle control
                cmds.parent(list_ik_control[1],list_ik_control[3])
                cmds.parent(list_ik_control[2], list_ik_control[3])

                # freeze group for all ik control
                utils.freeze_group_classic(list_ik_control[0:4])

                if self.enable_clavicle:
                    cmds.parentConstraint(self.clavicle_joint,cmds.listRelatives(list_ik_control[0],p=1,typ="transform")[0],mo=1)

            def create_driver_joint_ik():
                # parent offset joint
                duplicate_head = "{}_driver_ik".format(self.list_joint_chain[0])

                if cmds.objExists(duplicate_head):
                    raise Exception("{} is already exist in scene.".format(duplicate_head))

                cmds.duplicate(self.list_joint_chain[0], n=duplicate_head)

                for child in cmds.listRelatives(duplicate_head,f=1,ad=1):
                    cmds.rename(child,utils.cut(child)+"_driver_ik")

                cmds.parent(duplicate_head,grp_ik_joint)

            def create_stretchy_ik():
                list_dist = [loc_dist_start,loc_dist_pole,loc_dist_end]
                [ cmds.spaceLocator(n=locator) for locator in  list_dist]
                cmds.group(list_dist,n=utils.cname(self.name,"distance",grp),p=self.grp_local_anim)

                cmds.pointConstraint(list_ik_control[0],loc_dist_start)
                cmds.pointConstraint(list_ik_control[1],loc_dist_pole)
                cmds.pointConstraint(list_ik_control[3],loc_dist_end)

                utils.create_stretchy_joint(loc_start_dist=loc_dist_start,
                                            loc_pole_dist=loc_dist_pole,
                                            loc_end_dist=loc_dist_end,
                                            controller_attr=list_ik_control[3],
                                            axis_forward=self.axis_forward,
                                            list_stretch_joints=list_ik_joint[0:4],
                                            name_tag=self.name)

            def connect_hock_connection():
                # add group rotate pivot for ankle ik
                grp_rotate_hock_ik = cmds.group(em=1, n="{}_rotate_hock_ik_{}".format(self.name, grp),p=list_ik_control[3])
                utils.matchTransform(grp_rotate_hock_ik, list_ik_driver_joint[3], pos=1)
                grp_frz = utils.freeze_group_classic(grp_rotate_hock_ik)[0]

                cmds.parent(ankle_ik_handle, grp_rotate_hock_ik)

                # if front leg
                if not is_back_leg:
                    cmds.parent(grp_rotate_hock_ik, list_ik_control[3])

                # if back leg
                elif is_back_leg:
                    cmds.parent(grp_frz,list_ik_driver_joint[2])

                # crate hock connection
                list_axis_twist = ["x", "y", "z"]
                list_axis_twist.remove(utils.del_neg(self.axis_forward))

                if self.invert_hock_side:
                    invert_side = -1
                else:
                    invert_side = 1

                if self.invert_hock_forward:
                    invert_forward = -1
                else:
                    invert_forward = 1

                utils.connect_unit_conversion("{}.t{}".format(list_ik_control[2], list_axis_twist[0]), "{}.r{}".format(grp_rotate_hock_ik, list_axis_twist[1]), factor=0.5 * invert_side)
                utils.connect_unit_conversion("{}.t{}".format(list_ik_control[2], list_axis_twist[1]), "{}.r{}".format(grp_rotate_hock_ik, list_axis_twist[0]), factor=0.5 * invert_forward)

            def bend_weight_connection():
                attr_bend = list_ik_control[3] + ".bendWeightLeg"

                cmds.addAttr(attr_bend.split(".")[0],ln=attr_bend.split(".")[1],k=1,min=0,max=10)

                node_mdl_convert = cmds.createNode("multDoubleLinear",n=utils.cname(self.name,"bendLegConversion","mdl"))
                cmds.connectAttr(attr_bend,"{}.input1".format(node_mdl_convert))
                cmds.setAttr("{}.input2".format(node_mdl_convert),0.1)
                attr_bend_convert = "{}.output".format(node_mdl_convert)

                # connect bend up , down by attributes
                node_reverse = cmds.createNode("reverse",n=utils.cname(self.name,"bendLeg","rev"))

                cmds.connectAttr(attr_bend_convert,"{}.inputX".format(node_reverse))

                cmds.connectAttr("{}.outputX".format(node_reverse),"{}.springAngleBias[0].springAngleBias_FloatValue".format(driver_ik_handle))
                cmds.connectAttr(attr_bend_convert,"{}.springAngleBias[1].springAngleBias_FloatValue".format(driver_ik_handle))


            def create_ik_handle():
                # ik handle for driver handle
                cmds.ikHandle(sj=list_ik_driver_joint[0], ee=list_ik_driver_joint[3], n=driver_ik_handle, sol="ikRPsolver")
                cmds.ikHandle(driver_ik_handle,e=1,sol="ikSpringSolver")

                cmds.ikHandle(sj=list_ik_joint[0], ee=list_ik_joint[2], n=ankle_ik_handle, sol="ikRPsolver")
                cmds.ikHandle(sj=list_ik_joint[2], ee=list_ik_joint[3], n=hock_ik_handle, sol="ikSCsolver")

                # parent ik handle
                cmds.parent(driver_ik_handle, list_ik_control[3])
                utils.freeze_group_classic([driver_ik_handle])
                cmds.parent(ankle_ik_handle, list_ik_driver_joint[2])
                cmds.parent(hock_ik_handle, list_ik_driver_joint[3])

                # constraint orient of ankle joint
                cmds.orientConstraint(list_ik_control[3], list_ik_joint[3])

                # parent constraint for root joint
                cmds.parentConstraint(list_ik_control[0], list_ik_driver_joint[0])
                cmds.parentConstraint(list_ik_control[0], list_ik_joint[0])

                # if back leg
                if is_back_leg:
                    cmds.poleVectorConstraint(list_ik_control[1], driver_ik_handle, w=1)

                # if front leg
                else:
                    cmds.poleVectorConstraint(list_ik_control[1], ankle_ik_handle, w=1)
                #
                # pass

            ankle_ik_handle = "{}_ankle_ik_handle".format(self.name)
            driver_ik_handle = "{}_driver_ik_handle".format(self.name)
            hock_ik_handle = "{}_hock_ik_handle".format(self.name)
            list_ik_driver_joint = ["{}_driver_ik".format(joint) for joint in self.list_joint_chain]

            create_driver_joint_ik()
            create_ik_control()

            create_ik_handle()
            #
            connect_hock_connection()
            # create_stretchy_ik()

            bend_weight_connection()
        def create_fk_systems():
            parent = None

            for i,control in enumerate(list_fk_control):
                if control == list_fk_control[-1]:
                    continue

                if not parent:
                    parent = grp_fk_control

                utils.create_control(control,parent=parent,match=list_fk_joint[i],constraint="parent",freeze_group=True,mirror_freeze_group=self.mirror_control_scale)

                parent = control

            # constraint
            if self.enable_clavicle:
                # print(cmds.listRelatives(list_fk_control[0],p=1)[0])
                cmds.parentConstraint(self.clavicle_joint, cmds.listRelatives(list_fk_control[0],p=1)[0], mo=1)

        def create_flag_control():
            utils.create_control(ctrl_setting,parent=self.grp_local_anim,freeze_group=True,display_rotate_order=False)

            cmds.parentConstraint(self.list_joint_chain[3],cmds.listRelatives(ctrl_setting,p=1)[0])

            utils.lock_attributes(ctrl_setting, s=1, r=1, t=1, v=1, k=0, l=1)
        def create_switch_function():
            cmds.addAttr(ctrl_setting,ln=attr_switch.split(".")[-1],k=1,dv=0,min=0,max=1)

            utils.create_switch_fk_ik_chain(target_joints=self.list_joint_chain,
                                            grp_fk_joints=grp_fk_joint,
                                            grp_ik_joints=grp_ik_joint,
                                            grp_fk_controls=grp_fk_control,
                                            grp_ik_controls=grp_ik_control,
                                            attr_switch=attr_switch,
                                            attribute_switch_range=1,
                                            tag_name=self.name)

        def set_default_switch():
            if self.default_switch == 0:
                cmds.setAttr(attr_switch,0)
            else:
                cmds.setAttr(attr_switch,1)

        def add_ribbon_function():
            attr_sub_control = ctrl_option + ".bendCtrlVis"
            attr_detail_control = ctrl_option + ".detailCtrlVis"

            cmds.addAttr(attr_sub_control.split(".")[0],k=1,en="Hide:Show",ln=attr_sub_control.split(".")[1],at="enum")
            cmds.addAttr(attr_detail_control.split(".")[0],k=1,en="Hide:Show",ln=attr_detail_control.split(".")[1],at="enum")

            if self.ribbon_up_enable or self.ribbon_low_enable:
                utils.create_control(ctrl_knee_ribbon,freeze_group=True,parent=self.grp_local_anim)

                cmds.parentConstraint(self.list_limb_joint[1],cmds.listRelatives(ctrl_knee_ribbon,p=1)[0])


            if self.ribbon_up_enable:
                # create ribbon up
                utils.create_ribbon_rig_v2(anchor_start=self.list_limb_joint[0],
                                           anchor_end=ctrl_knee_ribbon,
                                           parent=self.grp_local_anim,
                                           axis_forward=self.axis_forward,
                                           axis_pole=self.axis_pole,
                                           list_ribbon_joint=self.list_up_ribbon_joint,
                                           tag_name=self.name+"_Up",
                                           enable_auto_twist=self.enable_ribbon_up_twist,
                                           invert_twist_driver=True,
                                           freeze_anchor_end=True,
                                           attr_bend_ctrl_vis=attr_sub_control,
                                           attr_detail_ctrl_vis=attr_detail_control,
                                           invert_between_value=True
                                           )

            if self.ribbon_low_enable:
                # create ribbon low
                utils.create_ribbon_rig_v2(anchor_start=ctrl_knee_ribbon,
                                           anchor_end=self.list_limb_joint[2],
                                           parent=self.grp_local_anim,
                                           axis_forward=self.axis_forward,
                                           axis_pole=self.axis_pole,
                                           list_ribbon_joint=self.list_low_ribbon_joint,
                                           enable_auto_twist=self.enable_ribbon_low_twist,
                                           tag_name=self.name+"_Low",
                                           attr_bend_ctrl_vis=attr_sub_control,
                                           attr_detail_ctrl_vis=attr_detail_control,
                                           invert_twist_driver=True
                                           # invert_twist_anchor=True
                                           )

        ctrl_setting = "{}_setting_{}".format(self.name,ctrl)
        attr_switch = ctrl_setting+".fkIk"
        ctrl_clavicle = "{}_{}".format(self.clavicle_joint, ctrl)

        grp_ik_joint = "{}_ik_joint_{}".format(self.name,grp)
        grp_fk_joint = "{}_fk_joint_{}".format(self.name,grp)

        grp_ik_control = "{}_ik_control_{}".format(self.name,grp)
        grp_fk_control = "{}_fk_control_{}".format(self.name,grp)

        list_fk_joint = [joint+"Fk" for joint in self.list_joint_chain]
        list_ik_joint= [joint+"Ik" for joint in self.list_joint_chain]

        list_fk_control = ["{}Fk_{}".format(joint,ctrl) for joint in self.list_joint_chain]
        list_ik_control= ["{}Ik_{}".format(joint,ctrl) for joint in self.list_joint_chain]

        grp_limb_parent = utils.cname(self.name,"limb_parent",grp)

        mel.eval("ikSpringSolver;")
        self.axis_forward = utils.convert_single_axis_enum(self.axis_forward)
        self.axis_pole = utils.convert_single_axis_enum(self.axis_pole)
        self.pole_axis_direction = utils.convert_single_axis_enum_pos(self.pole_axis_direction)

        loc_dist_start,loc_dist_pole,loc_dist_end = [utils.cname(self.name,"startDist",loc),utils.cname(self.name,"poleDist",loc),utils.cname(self.name,"endDist",loc)]

        is_back_leg = True if self.limb_type == 1 else False

        check_input()

        create_hierarchy()

        create_flag_control()
        create_switch_function()

        create_clavicle_control()

        create_fk_systems()
        create_ik_systems()

        make_finalize()

        set_default_switch()
        create_blend_space()
    def core_unbuild(self):
        for joint in self.list_joint_chain:
            # ignore None Type
            if not cmds.objExists(joint):
                continue

            # Break Connection Each Joint
            utils.break_connection(joint,rot=True,pos=True,scl=True)
class Head(rig_class.Rig):
    """Neck

Create a neck part

Variables:
name(string) : Name of part
list_head_joints (stringArray) : List Neck Joints, the head joint will be the last one
axis_forward(enum) : Axis of forward Direction
parent(string) :Name of parent object. for example Chest
debug_mode(bool): If Checked, UnLock and hide unnecessary attributes and object for animators

enable_squash_head(bool) : Enable Squash Head Feature or not.
list_head_squash_joint(stringArray) : Upper and Lower Head Joints.
list_head_squash_handle_piv(stringArray) : Upper and Lower Handle Pivot.
follow_intensity(float) : amount of follow squash handle
"""

    def __init__(self):
        super().__init__()

        self.name = "head"

        # @ Required
        # $ Global Joint
        self.list_head_joints = []
        self.axis_forward = utils.get_single_axis_enum_pos()

        # @ Optional
        # $ Squash Head Feature
        self.enable_squash_head = False
        self.list_head_squash_joint = []
        self.list_head_squash_handle_piv = []
        self.follow_intensity = 1.0
        # * enable_squash_head

        self.parent = ""
        self.debug_mode = False

    def core_build(self):
        def create_local_space():
            # create head local space attributes
            cmds.addAttr(attr_local_head.split(".")[0], ln=attr_local_head.split(".")[1], at="float", min=0,
                         max=1, dv=0, k=1)

            loc_local_space = cmds.spaceLocator(n=utils.cname(self.name,"LocalSpace",loc))[0]
            utils.match_parent(loc_local_space, list_neck_control[-1])

            utils.create_float_space([list_neck_control[-1], ctrl_fly], target=ctrl_head, attr_float=attr_local_head, typ="orient")

        def make_finalize():
            # lock controller attributes
            [utils.lock_attributes(control, s=1, v=1, k=0, l=1) for control in list_neck_control]
            utils.lock_attributes(ctrl_head, s=1, v=1, k=0, l=1)

            # lock freeze group
            [utils.lock_attributes(cmds.listRelatives(control, p=1, typ="transform")[0], s=1, r=1, t=1, v=1, k=0, l=1) for control in list_neck_control + [ctrl_head]]

        def create_squash_head():
            if not self.enable_squash_head:
                return

            def create_squash_head_control():
                utils.create_control(ctrl_head_up_squash,match=jnt_head_up,constraint="parent",parent=grp_squash_head,freeze_group=True)
                utils.create_control(ctrl_head_up_squash_handle,parent=ctrl_head_up_squash)
                utils.matchTransform(ctrl_head_up_squash_handle,piv_head_up,pos=1)
                utils.freeze_group_classic(ctrl_head_up_squash_handle)

                utils.create_control(ctrl_head_low_squash,match=jnt_head_low,constraint="parent",parent=grp_squash_head,freeze_group=True)
                utils.create_control(ctrl_head_low_squash_handle,parent=ctrl_head_low_squash)
                utils.matchTransform(ctrl_head_low_squash_handle,piv_head_low,pos=1)
                utils.freeze_group_classic(ctrl_head_low_squash_handle)

                utils.create_control(ctrl_head_mid_squash,parent=grp_squash_head)
                constraint = cmds.pointConstraint(jnt_head_up,jnt_head_low,ctrl_head_mid_squash)
                cmds.delete(constraint)
                utils.freeze_group_classic(ctrl_head_mid_squash)

                # finalize handle control
                utils.lock_attributes(ctrl_head_up_squash_handle, s=1, r=1, v=1, k=0, l=1)
                utils.lock_attributes(ctrl_head_low_squash_handle, s=1, r=1, v=1, k=0, l=1)

                utils.lock_attributes(ctrl_head_up_squash, s=1, v=1, k=0, l=1)
                utils.lock_attributes(ctrl_head_low_squash, s=1, v=1, k=0, l=1)

                cmds.setAttr("{}.s{}".format(ctrl_head_up_squash,axis_forward_abs),k=1,l=0)
                cmds.setAttr("{}.s{}".format(ctrl_head_low_squash,axis_forward_abs),k=1,l=0)

            def create_aim_locator():
                cmds.select(cl=1)
                cmds.joint(n=jnt_head_up_aim)
                cmds.joint(n=jnt_head_up_aim_tip)

                cmds.select(cl=1)
                cmds.joint(n=jnt_head_low_aim)
                cmds.joint(n=jnt_head_low_aim_tip)

                # match transform joint
                utils.matchAllTransform(jnt_head_up_aim,jnt_head_up)
                cmds.setAttr("{}.t{}".format(jnt_head_up_aim_tip,axis_forward_abs),self.follow_intensity)

                utils.matchAllTransform(jnt_head_low_aim,jnt_head_low)
                cmds.setAttr("{}.t{}".format(jnt_head_low_aim_tip,axis_forward_abs),-1*self.follow_intensity)

                cmds.parent(jnt_head_up_aim,jnt_head_low_aim,ctrl_head_mid_squash)

                # use ik handle
                cmds.ikHandle(n=ik_handle_up,sol="ikSCsolver",sj=jnt_head_up_aim,ee=jnt_head_up_aim_tip)
                cmds.ikHandle(n=ik_handle_low,sol="ikSCsolver",sj=jnt_head_low_aim,ee=jnt_head_low_aim_tip)

                cmds.parent(ik_handle_up,ctrl_head_up_squash_handle)
                cmds.parent(ik_handle_low,ctrl_head_low_squash_handle)

            def create_auto_stretch():
                def create_locator(locator,target):
                    cmds.spaceLocator(n=locator)

                    cmds.parent(locator,grp_local_position)

                    node_mult_matrix = cmds.createNode("multMatrix",n=utils.cname(self.name,"multMatrix","mm"))
                    cmds.connectAttr("{}.worldMatrix[0]".format(target),"{}.matrixIn[0]".format(node_mult_matrix))
                    cmds.connectAttr("{}.parentInverseMatrix[0]".format(locator),"{}.matrixIn[1]".format(node_mult_matrix))

                    node_decompose = cmds.createNode("decomposeMatrix",n=utils.cname(self.name,"decomposeMatrix","dcm"))
                    cmds.connectAttr("{}.matrixSum".format(node_mult_matrix),"{}.inputMatrix".format(node_decompose))

                    # apply to locator
                    cmds.connectAttr("{}.outputTranslate".format(node_decompose),"{}.t".format(locator))

                def connect_auto_scale(position1,position2,output):
                    node_distance_between = cmds.createNode("distanceBetween",n=utils.cname(self.name,"distanceBetween","dist"))
                    cmds.connectAttr(position1+".t","{}.point1".format(node_distance_between))
                    cmds.connectAttr(position2+".t","{}.point2".format(node_distance_between))
                    distance_value = cmds.getAttr( "{}.distance".format(node_distance_between))
                    multiply_value = 1/distance_value

                    node_mult_stretch = cmds.createNode("multDoubleLinear",n=utils.cname(self.name,"multStretch","mdl"))
                    cmds.connectAttr("{}.distance".format(node_distance_between),"{}.input1".format(node_mult_stretch))
                    cmds.setAttr("{}.input2".format(node_mult_stretch),multiply_value)
                    attr_stretch_scale = "{}.output".format(node_mult_stretch)

                    node_mult_squash = cmds.createNode("multiplyDivide",n=utils.cname(self.name,"multSquash","md"))
                    cmds.setAttr("{}.operation".format(node_mult_squash),2)
                    cmds.setAttr("{}.input1X".format(node_mult_squash),distance_value)
                    cmds.connectAttr("{}.distance".format(node_distance_between),"{}.input2X".format(node_mult_squash))
                    attr_squash_scale = "{}.outputX".format(node_mult_squash)

                    for axis in ["x","y","z"]:
                        if axis == axis_forward_abs:
                            cmds.connectAttr(attr_stretch_scale,"{}.s{}".format(output,axis_forward_abs))
                        else:
                            cmds.connectAttr(attr_squash_scale,"{}.s{}".format(output,axis))

                loc_dist_up_1 = utils.cname(self.name,"UpDist1",loc)
                loc_dist_up_2 = utils.cname(self.name,"UpDist2",loc)

                loc_dist_low_1 = utils.cname(self.name,"LowDist1",loc)
                loc_dist_low_2 = utils.cname(self.name,"LowDist2",loc)

                # create locator
                create_locator(loc_dist_up_1,ctrl_head_mid_squash)
                create_locator(loc_dist_up_2,ik_handle_up)

                create_locator(loc_dist_low_1,ctrl_head_mid_squash)
                create_locator(loc_dist_low_2,ik_handle_low)

                # create auto stretch
                connect_auto_scale(loc_dist_up_1,loc_dist_up_2,jnt_head_up)
                connect_auto_scale(loc_dist_low_1,loc_dist_low_2,jnt_head_low)

            def apply_to_joint():
                cmds.parentConstraint(jnt_head_up_aim,jnt_head_up)
                cmds.parentConstraint(jnt_head_low_aim,jnt_head_low)

            jnt_head_up_aim = utils.cname(self.name,"headUpAim",jnt)
            jnt_head_up_aim_tip = utils.cname(self.name,"headUpAimTip",jnt)

            jnt_head_low_aim = utils.cname(self.name,"headLowAim",jnt)
            jnt_head_low_aim_tip = utils.cname(self.name,"headLowAimTip",jnt)

            grp_squash_head = cmds.group(em=1,n=utils.cname(self.name,"SquashHead",grp),p=ctrl_head)
            grp_local_position = cmds.group(em=1,n=utils.cname(self.name,"LocalPosition",grp),p=grp_squash_head)

            axis_forward_abs = utils.del_neg(self.axis_forward)

            jnt_head_up,jnt_head_low = self.list_head_squash_joint
            piv_head_up,piv_head_low = self.list_head_squash_handle_piv

            ctrl_head_mid_squash = utils.cname(self.name,"MiddleSquash",ctrl)

            ctrl_head_up_squash = utils.cname(self.name,"UpSquash",ctrl)
            ctrl_head_low_squash = utils.cname(self.name,"LowSquash",ctrl)

            ctrl_head_up_squash_handle = utils.cname(self.name,"UpSquashHandle",ctrl)
            ctrl_head_low_squash_handle = utils.cname(self.name,"LowSquashHandle",ctrl)


            ik_handle_up = utils.cname(self.name,"UpSquash","ikHandle")
            ik_handle_low = utils.cname(self.name, "LowSquash", "ikHandle")

            create_squash_head_control()
            create_aim_locator()
            apply_to_joint()

            create_auto_stretch()

        def create_neck_controls():
            # create neck controller and chain in fk hierarchy
            ctrl_recent = None
            for joint in list_neck_joints:
                control = utils.create_control(name=utils.cname(None,joint,ctrl),
                                               parent=self.grp_local_anim,
                                               match=joint,
                                               constraint="parent",
                                               color="blue",
                                               size=2.5)

                if ctrl_recent:
                    cmds.parent(control, ctrl_recent)

                ctrl_recent = control
                list_neck_control.append(control)

            utils.freeze_group_classic(list_neck_control, "grpCtrl")

        def create_head_controls():
            grp_head_ctrls = cmds.group(em=1, n="{}_headCtrls".format(grp), p=self.grp_local_anim)

            utils.create_control(name=ctrl_head,
                                 parent=grp_head_ctrls,
                                 match=jnt_head,
                                 color="yellow",
                                 size=3.5)
            utils.freeze_group_classic([ctrl_head], "grpCtrl")
            # scalable
            cmds.parentConstraint(ctrl_head, jnt_head)

            cmds.parentConstraint(list_neck_control[-1], utils.freeze_group_classic(ctrl_head, "grpPar")[0], mo=1)

        self.axis_forward = utils.convert_single_axis_enum_pos(self.axis_forward)

        jnt_head=  self.list_head_joints[-1]
        list_neck_joints = self.list_head_joints[0:len(self.list_head_joints)-1]

        list_neck_control = []
        attr_local_head = ""
        ctrl_head = utils.cname(None,jnt_head,ctrl)
        attr_local_head = ctrl_head + ".localHeadOrient"

        create_neck_controls()
        create_head_controls()

        create_local_space()

        create_squash_head()

        make_finalize() if not self.debug_mode else None



class Limb(rig_class.Rig):
    """Limb

Create Limb Rig Systems for Arm / Leg , Also have Ribbon / Advance Foot and Simple Twist Joint Optional

Variables:
name(string) : Name of your part. for example "L_leg" , "R_arm".
list_limb_joint (stringArray) : Select Three of Limb Joint. for example ["upLeg","lowLeg","footAnkle"].
axis_forward(enum) : Axis Direction of Aiming Axis. for example. for example "x","-x"
axis_pole(enum) : Axis Direction of Pole Axis that aiming to pole controller. for example "x","-x"
ik_is_default_switch(bool): Default value is ik, if uncheck , will be fk
attribute_switch_range(enum): Range of float switch fk/ik , by default will be 1

pole_distance(float):amount of distance between ik pole controller and character.
parent(string) :Name of Parent Object ,for example Pelvis for leg, Clavicle for arm.

foot_enable(bool):Enable Foot Systems.
jnt_ball(string) :name of joint ball.
jnt_toe(string) :name of joint toe.

clavicle_enable (bool): Enable Clavicle Part for arm (If you enable this , you can change the parent attribute to your clavicle's parent ).
jnt_clavicle (string) : Name of Clavicle Joint.

list_foot_pivot(stringArray) : names of inner , outer , heel and end pivot reference (locator).
ribbon_enable(bool): Enable Ribbon Joint Systems.
joint_up_ribbon(stringArray) : List of Upper Ribbon joints.
joint_low_ribbon(stringArray) :List of Lower Ribbon joints.
finalize(bool): Lock and hide unnecessary attributes and object for animators.

use_world_pole(bool): If was checked , the pole control will reference in world axis as "World Direction Pole" attribute.
world_direction_pole(enum) : Input Axis (Not Support Negative axis ,to invert axis change in pole distance instead).

stretch_with_fixed_angle(bool): When Checked , When Stretch and Auto Stretch on the angle of limb will be preserved.

use_custom_fixed_angle_percentage(bool): When Checked,This Will Adjust Fixed Angle Percentage (This only work when stretch_with_fixed_angle enable)
custom_fixed_percentage(long): amount of turn_on_percentage (support in range 1 - 100)

list_ik_pivot(stringArray) : pivot of inner,outer, heel and end (Match only Position, Rotation will Match by jnt ball rotation)
jnt_tip(string) : name of tip joint of ik

ik_base_axis(enum) : List of Absolute Axis for Forward,Side,Twist Orderly

auto_roll_default_value(float) : condition value that auto roll will enable, indicate by pitch attribute

ribbon_up_enable(bool) : enable ribbon system for upper part of limb.
ribbon_low_enable(bool) : enable ribbon system for upper part of limb.
list_low_ribbon_joint(stringArray) : List of low ribbon part that will attach along main joint (Sort by Upper to Lower).
list_up_ribbon_joint(stringArray) : List of up ribbon part that will attach along main joint (Sort by Upper to Lower).

enable_ribbon_up_twist (bool) : enable_ribbon_up_twist
invert_up_twist (bool) : invert_up_twist

enable_ribbon_low_twist (bool) : enable_ribbon_low_twist
invert_low_twist (bool) : invert_low_twist

ik_pivot_enable(bool) : enable ik pivot system (reverse joint).

invert_roll_value(bool) : invert value.
invert_side_roll_value(bool) : invert value.
invert_toe_twist_value(bool) : invert value.
invert_middle_twist_value(bool) : invert value.
invert_heel_twist_value(bool) : invert value.

invert_roll_axis(bool) : invert value.
invert_roll_side_axis(bool) : invert value.

mirror_control_scale(bool) : If checked, Flip all scale of control
debug_mode(bool) : If Checked, Will Display all rig systems locator,curve and joint ,etc.



default_switch(enum) : What Default Type of Kenematic Swictch.

clavicle_space_switch(bool) : Enable Space Switch for Clavicle Control.
list_clavicle_switch_target(stringArray) : List of Object Name of space target.
list_clavicle_switch_name(stringArray) :  List of Nice Name of space target.

hand_space_switch(bool): When Checked, Hand Ik Space Switch Enum Attributes will be created.
list_switch_target(stringArray) : List Of Enum Target
list_switch_name(stringArray) : List Of Enum Target Nice Name (Must Match Count with Target,Else Error)

fk_space_switch(bool) : If checked, Enable Space Switch for root fk orient,such as shoulder or thigh.
list_fk_switch_target(stringArray) : List of object that will be the parent of spaces.
list_fk_switch_name(stringArray): List of object that will be the parent of spaces name.

enable_wrist_corrective(bool) : Enable Wrist Corrective.
list_wrist_joint(stringArray) : List of Wrist Corrective Joints. (Front,Upper,Back,Lower )
wrist_corrective_axis_push(enum) : Axis That Corrective Joint aim forward.
wrist_axis(enum) : Axis of wrist (Forward , Up ,Side).
wrist_corrective_front_invert(bool) : Invert Front Wrist
wrist_corrective_upper_invert(bool) : Invert Upper Wrist
wrist_corrective_back_invert(bool) : Invert Back Wrist
wrist_corrective_lower_invert(bool) : Invert Lower Wrist


enable_elbow_corrective(bool) : Enable Elbow Corrective.
list_elbow_joint(stringArray) : List of Elbow Corrective Joints. (Inside,Outside )
elbow_corrective_axis_push(enum) : Axis That Corrective Joint aim forward.
elbow_axis(enum) : Axis of Elbow (Forward , Up ,Side).

enable_shoulder_corrective(bool) : Enable shoulder Corrective.
list_shoulder_joint(stringArray) : Single Shoulder Push Joint
shoulder_corrective_axis_push(enum) : Axis That Corrective Joint aim forward.
shoulder_axis(enum) : Axis of shoulder (Forward , Up ,Side).
shoulder_corrective_invert(bool) : Invert Direction of Push Shoulder

auto_setup_ribbon_upper_joint(script) : Automatic setup ribbon joints
auto_setup_ribbon_lower_joint(script) : Automatic setup ribbon joints
    """

    def __init__(self):
        super().__init__()

        self.name = "{}_limb".format(L)

        # @ Setting
        # $ Required (Joint Global)
        self.list_limb_joint = []
        # -
        self.axis_forward = utils.get_single_axis_enum()
        self.axis_pole = utils.get_single_axis_enum()
        # -
        self.attribute_switch_range = ["1","10"]
        self.default_switch = ["FK","IK"]

        # $ Clavicle Rig Feature
        self.clavicle_enable = False
        self.jnt_clavicle = ""
        # *clavicle_enable

        # $ Pole Vector Build Behaviour
        self.pole_distance = 5.0
        # -
        self.use_world_pole = False
        self.world_direction_pole = utils.get_single_axis_enum_pos()
        # *use_world_pole
        # -
        self.stretch_with_fixed_angle = False
        self.use_custom_fixed_angle_percentage = False
        # *stretch_with_fixed_angle

        self.custom_fixed_percentage = 0
        # *use_custom_fixed_angle_percentage

        # @ Optional Features
        # $ Reverse Joint for Ik
        self.ik_pivot_enable = False
        # -
        self.list_ik_pivot = []
        # -
        self.jnt_ball = ""
        self.jnt_tip = ""
        # -
        self.ik_base_axis = utils.get_triple_axis_enum()
        # -
        self.invert_roll_axis = False
        self.invert_roll_side_axis = False
        # -
        self.auto_roll_default_value = 0.0
        # -
        self.invert_roll_value = False
        self.invert_side_roll_value = False
        self.invert_toe_twist_value = False
        self.invert_middle_twist_value = False
        self.invert_heel_twist_value = False
        # *ik_pivot_enable

        # $ Fk Root Control Space Switch (Orient)
        self.fk_space_switch = False
        self.list_fk_switch_target = []
        self.list_fk_switch_name = []
        # * fk_space_switch

        # $ Ik End Control Space Switch (Parent)
        self.hand_space_switch = False
        self.list_switch_target = []
        self.list_switch_name = []
        # * hand_space_switch

        # $ Clavicle Control Space Switch (Orient)
        self.clavicle_space_switch = False
        self.list_clavicle_switch_target = []
        self.list_clavicle_switch_name = []
        # * clavicle_space_switch

        # $ Ribbon Feature
        # # auto_setup_ribbon_upper_joint
        self.ribbon_up_enable = False
        self.list_up_ribbon_joint = []
        self.enable_ribbon_up_twist = True
        # *ribbon_up_enable
        # -
        # # auto_setup_ribbon_lower_joint
        self.ribbon_low_enable = False
        self.list_low_ribbon_joint = []
        self.enable_ribbon_low_twist = True
        # *ribbon_low_enable

        # @ Corrective Joints
        # $ Corrective Wrist 4 Joints (Experimental)
        self.enable_wrist_corrective = False
        self.list_wrist_joint = []
        # -
        self.wrist_corrective_axis_push = utils.get_single_axis_enum()
        self.wrist_axis = utils.get_triple_axis_enum()
        # -
        self.wrist_corrective_front_invert = True
        self.wrist_corrective_upper_invert = True
        self.wrist_corrective_back_invert = False
        self.wrist_corrective_lower_invert = False
        # * enable_wrist_corrective

        # $ Corrective Elbow 2 Joints (Experimental)
        self.enable_elbow_corrective = False
        self.list_elbow_joint = []
        # -
        self.elbow_corrective_axis_push = utils.get_single_axis_enum()
        self.elbow_axis = utils.get_triple_axis_enum()
        # * enable_elbow_corrective

        # $ Corrective Shoulder 1 Joints (Experimental)
        self.enable_shoulder_corrective = False
        self.list_shoulder_joint = []
        # -
        self.shoulder_corrective_axis_push = utils.get_single_axis_enum()
        self.shoulder_axis = utils.get_triple_axis_enum()
        # -
        self.shoulder_corrective_invert = False
        # * enable_shoulder_corrective

        self.parent = ""
        self.mirror_control_scale = False
        self.debug_mode = False

    def auto_setup_ribbon_upper_joint(self):
        def get_amount():
            if cmds.getAttr("{}.isBuild".format(self.name)):
                cmds.confirmDialog(m="Only Execute Scripts in Unbuild Mode.")
                raise Exception("Only Execute Scripts in Unbuild Mode.")
            if not self.list_limb_joint:
                cmds.confirmDialog(m="Please input attribute list limb joint first.")
                raise Exception("Please input attribute list limb joint first.")

            result = cmds.promptDialog(
                title='Upper Ribbon Amount',
                message='Enter Amount of Upper Ribbon:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel',
                tx=5)

            if result == 'OK':
                text = cmds.promptDialog(query=True, text=True)
            else:
                raise Exception("was Canceled")

            if not text.isdigit():
                cmds.confirmDialog(m="Invalid Input, Required Amount, Get {}".format(text))
                raise Exception("Invalid Input, Required Amount, Get {}".format(text))

            return int(text)

        def create_ribbon_joint():
            # create joint
            for i,ribbon_joint in enumerate(list_ribbon_joint_name):
                # delete exist joint
                if cmds.objExists(ribbon_joint):
                    list_child = cmds.listRelatives(ribbon_joint,c=1)
                    parent = cmds.listRelatives(ribbon_joint,p=1)

                    if list_child:
                        if parent:
                            cmds.parent(list_child,parent[0])
                        else:
                            cmds.parent(list_child,w=1)

                    cmds.delete(ribbon_joint)

                # create joint
                cmds.select(cl=1)
                cmds.joint(n=ribbon_joint)
                cmds.setAttr("{}.drawStyle".format(ribbon_joint),3)

                utils.matchAllTransform(ribbon_joint, first_joint)

                # parent
                if i == 0:
                    cmds.parent(ribbon_joint,config.grp_skin)
                else:
                    cmds.parent(ribbon_joint,list_ribbon_joint_name[i-1])

            # snap position
            for i,ribbon_joint in enumerate(list_ribbon_joint_name):
                constraint = cmds.pointConstraint(first_joint,second_joint,ribbon_joint)[0]

                factor_w0 = ( 1/((len(list_ribbon_joint_name))-1) )*i
                factor_w1 = 1-factor_w0

                # print(factor_w0)

                cmds.setAttr("{}.{}W0".format(constraint,first_joint),factor_w1)
                cmds.setAttr("{}.{}W1".format(constraint,second_joint),factor_w0)

                cmds.delete(constraint)

            # freeze joint
            cmds.makeIdentity(list_ribbon_joint_name[0],a=1,r=1,)

        def update_attribute():
            cmds.setAttr("{}.ribbon_up_enable".format(self.name),True)
            cmds.setAttr("{}.list_up_ribbon_joint".format(self.name), len(list_ribbon_joint_name), *list_ribbon_joint_name, typ="stringArray")

        amount = get_amount()
        first_joint = self.list_limb_joint[0]
        second_joint = self.list_limb_joint[1]
        list_ribbon_joint_name = ["{}_Rbn_{}".format(first_joint, i + 1) for i in range(amount)]
        create_ribbon_joint()
        update_attribute()

        return True
    def auto_setup_ribbon_lower_joint(self):
        def get_amount():
            if cmds.getAttr("{}.isBuild".format(self.name)):
                cmds.confirmDialog(m="Only Execute Scripts in Unbuild Mode.")
                raise Exception("Only Execute Scripts in Unbuild Mode.")

            if not self.list_limb_joint:
                cmds.confirmDialog(m="Please input attribute list limb joint first.")
                raise Exception("Please input attribute list limb joint first.")

            result = cmds.promptDialog(
                title='Upper Ribbon Amount',
                message='Enter Amount of Upper Ribbon:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel',
                tx=5)

            if result == 'OK':
                text = cmds.promptDialog(query=True, text=True)
            else:
                raise Exception("was Canceled")

            if not text.isdigit():
                cmds.confirmDialog(m="Invalid Input, Required Amount, Get {}".format(text))
                raise Exception("Invalid Input, Required Amount, Get {}".format(text))

            return int(text)

        def create_ribbon_joint():
            # create joint
            for i,ribbon_joint in enumerate(list_ribbon_joint_name):
                # delete exist joint
                if cmds.objExists(ribbon_joint):
                    list_child = cmds.listRelatives(ribbon_joint,c=1)
                    parent = cmds.listRelatives(ribbon_joint,p=1)

                    if list_child:
                        if parent:
                            cmds.parent(list_child,parent[0])
                        else:
                            cmds.parent(list_child,w=1)

                    cmds.delete(ribbon_joint)

                # create joint
                cmds.select(cl=1)
                cmds.joint(n=ribbon_joint)
                cmds.setAttr("{}.drawStyle".format(ribbon_joint),3)
                
                utils.matchAllTransform(ribbon_joint, first_joint)

                # parent
                if i == 0:
                    cmds.parent(ribbon_joint,config.grp_skin)
                else:
                    cmds.parent(ribbon_joint,list_ribbon_joint_name[i-1])

            # snap position
            for i,ribbon_joint in enumerate(list_ribbon_joint_name):
                constraint = cmds.pointConstraint(first_joint,second_joint,ribbon_joint)[0]

                factor_w0 = ( 1/((len(list_ribbon_joint_name))-1) )*i
                factor_w1 = 1-factor_w0

                # print(factor_w0)

                cmds.setAttr("{}.{}W0".format(constraint,first_joint),factor_w1)
                cmds.setAttr("{}.{}W1".format(constraint,second_joint),factor_w0)

                cmds.delete(constraint)

            # freeze joint
            cmds.makeIdentity(list_ribbon_joint_name[0],a=1,r=1,)

        def update_attribute():
            cmds.setAttr("{}.ribbon_low_enable".format(self.name),True)
            cmds.setAttr("{}.list_low_ribbon_joint".format(self.name), len(list_ribbon_joint_name), *list_ribbon_joint_name, typ="stringArray")

        amount = get_amount()
        first_joint = self.list_limb_joint[1]
        second_joint = self.list_limb_joint[2]
        list_ribbon_joint_name = ["{}_Rbn_{}".format(first_joint, i + 1) for i in range(amount)]
        create_ribbon_joint()
        update_attribute()

        return True
    def core_build(self):
        def create_clavicle():
            if not self.clavicle_enable:
                return

            # create clavicle rig group
            utils.create_control(name=ctrl_clavicle,
                                 match=self.jnt_clavicle,
                                 constraint="parent",
                                 parent=grp_clavicle_parent,
                                 size=1.5,
                                 color="purple",
                                 shape="sphere")

            grp_offset = utils.freeze_group_classic(ctrl_clavicle, "grpCtrl")[0]


            # flip scale if required
            cmds.setAttr(grp_offset + ".s", -1, -1, -1, typ="double3") if self.mirror_control_scale else None

            # utils.create_float_space()
            if self.clavicle_space_switch:
                utils.create_enum_space_classic(list_space=self.list_clavicle_switch_target,
                                         list_nice_name=self.list_clavicle_switch_name,
                                                target=grp_offset,
                                                type="orient",
                                                object_attr=ctrl_clavicle)

            # constraint control to joint
            cmds.parentConstraint(ctrl_clavicle, self.jnt_clavicle)

        def clavicle_connet_limb():
            # if clavicle enable : loc parent drive clavicle , clavicle will drive root ik and fk controls
            if not self.clavicle_enable:
                return

            cmds.parentConstraint(ctrl_clavicle, cmds.listRelatives(list_limb_ctrl_ik[0], p=1)[0], mo=1)
            cmds.parentConstraint(ctrl_clavicle, grp_fk_controls, mo=1)


        def create_switch_func():


            target_joints = self.list_limb_joint + list_foot_joint

            utils.create_switch_fk_ik_chain(target_joints=target_joints,
                                            grp_ik_joints=grp_ik_joints,
                                            grp_fk_joints=grp_fk_joints,
                                            grp_ik_controls=grp_ik_controls,
                                            grp_fk_controls=grp_fk_controls,
                                            attr_switch=attr_switch,
                                            attribute_switch_range=self.attribute_switch_range,
                                            tag_name=self.name)



        def create_ik_pivot_function():
            if not self.ik_pivot_enable:
                return

            utils.create_ik_reverse(control_setting=list_limb_ctrl_ik[2],
                                    control_parent_ik=list_limb_ctrl_ik[2],
                                    control_parent_fk=list_limb_ctrl_fk[2],
                                    axis_foot_three=utils.convert_triple_axis_enum(self.ik_base_axis),
                                    list_locator_pivot=self.list_ik_pivot,
                                    ball_joint=self.jnt_ball,
                                    toe_joint=self.jnt_tip,
                                    ankle_joint_ik=list_limb_joint_ik[2],
                                    parent=self.grp_local_anim,
                                    list_parent_reverse=[ik_handle_limb,loc_end_dist],
                                    name_tag=self.name,
                                    invert_roll_axis=self.invert_roll_axis,
                                    invert_roll_value=self.invert_roll_value,
                                    invert_roll_side_axis=self.invert_roll_side_axis,
                                    invert_side_roll_value=self.invert_side_roll_value,
                                    invert_toe_twist_value=self.invert_toe_twist_value,
                                    invert_heel_twist_value=self.invert_heel_twist_value,
                                    invert_middle_twist_value=self.invert_middle_twist_value,
                                    auto_roll_default_value=self.auto_roll_default_value
                                    )

        def add_ribbon_function():
            attr_sub_control = ctrl_option + ".bendCtrlVis"
            attr_detail_control = ctrl_option + ".detailCtrlVis"

            cmds.addAttr(attr_sub_control.split(".")[0],k=1,en="Hide:Show",ln=attr_sub_control.split(".")[1],at="enum")
            cmds.addAttr(attr_detail_control.split(".")[0],k=1,en="Hide:Show",ln=attr_detail_control.split(".")[1],at="enum")

            if self.ribbon_up_enable or self.ribbon_low_enable:
                utils.create_control(ctrl_knee_ribbon,freeze_group=True,parent=self.grp_local_anim)

                cmds.parentConstraint(self.list_limb_joint[1],cmds.listRelatives(ctrl_knee_ribbon,p=1)[0])


            if self.ribbon_up_enable:
                # create ribbon up
                utils.create_ribbon_rig_v2(anchor_start=self.list_limb_joint[0],
                                           anchor_end=ctrl_knee_ribbon,
                                           parent=self.grp_local_anim,
                                           axis_forward=self.axis_forward,
                                           axis_pole=self.axis_pole,
                                           list_ribbon_joint=self.list_up_ribbon_joint,
                                           tag_name=self.name+"_Up",
                                           enable_auto_twist=self.enable_ribbon_up_twist,
                                           invert_twist_driver=True,
                                           freeze_anchor_end=True,
                                           attr_bend_ctrl_vis=attr_sub_control,
                                           attr_detail_ctrl_vis=attr_detail_control,
                                           invert_between_value=True
                                           )

            if self.ribbon_low_enable:
                # create ribbon low
                utils.create_ribbon_rig_v2(anchor_start=ctrl_knee_ribbon,
                                           anchor_end=self.list_limb_joint[2],
                                           parent=self.grp_local_anim,
                                           axis_forward=self.axis_forward,
                                           axis_pole=self.axis_pole,
                                           list_ribbon_joint=self.list_low_ribbon_joint,
                                           enable_auto_twist=self.enable_ribbon_low_twist,
                                           tag_name=self.name+"_Low",
                                           attr_bend_ctrl_vis=attr_sub_control,
                                           attr_detail_ctrl_vis=attr_detail_control,
                                           invert_twist_driver=True
                                           # invert_twist_anchor=True
                                           )


        def make_finalize():
            if self.debug_mode:
                return

            # controller attributes
            utils.lock_attributes(ctrl_option, t=1, r=1, s=1, v=1)

            for control in list_limb_ctrl_fk:
                utils.lock_attributes(control, t=1, s=1, v=1)

            utils.lock_attributes(ctrl_knee_ribbon, s=1, r=1, v=1)

            utils.lock_attributes(list_limb_ctrl_ik[0], s=1, r=1, v=1)
            utils.lock_attributes(list_limb_ctrl_ik[1], s=1, r=1, v=1)
            utils.lock_attributes(list_limb_ctrl_ik[2], s=1, v=1)
            utils.lock_attributes(ctrl_clavicle, s=1, v=1) if self.clavicle_enable else None

            utils.finalize_visibility(self.grp_local_rig)

            utils.add_to_set(list_limb_ctrl_fk+list_limb_ctrl_ik+[ctrl_option])

        def create_hierarchy():
            # cmds.group(em=1)
            cmds.group(em=1,n=grp_clavicle_parent,p=self.grp_local_anim)
            cmds.group(em=1,n=grp_limb_parent,p=self.grp_local_anim)


            cmds.group(em=1, n=grp_ik_controls, p=grp_limb_parent)
            cmds.group(em=1, n=grp_fk_controls, p=grp_limb_parent)
            cmds.group(em=1, n=grp_ik_joints, p=grp_ik_controls)
            cmds.group(em=1, n=grp_fk_joints, p=grp_fk_controls)


        def create_ctrl_option():
            # create control option
            utils.create_control(name=ctrl_option,
                                 parent=grp_limb_parent,
                                 size=1.5,
                                 color="yellow")
            grp_offset = utils.freeze_group_classic([ctrl_option], grpCtrl)[0]

            cmds.addAttr(ctrl_option, ln="scaleAll", at="float", dv=1, k=1)

            # parented by end joint
            cmds.parentConstraint(self.list_limb_joint[2], grp_offset)

            # create attr switch ----------------------
            if self.attribute_switch_range == 0:
                self.attribute_switch_range = 1
            elif self.attribute_switch_range == 1:
                self.attribute_switch_range = 10
            else:
                raise Exception("Invalid Attribute Switch Range Input , got {}".format(self.attribute_switch_range))

            cmds.addAttr(ctrl_option, ln=attr_switch.split(".")[1], min=0, max=self.attribute_switch_range,
                         at="float", k=1)

            # create unit conversion for attribute if not normal 1
            if self.attribute_switch_range != 1:
                return  utils.connect_attr_conversion(input1=attr_switch,conversion=1 / self.attribute_switch_range)
            else:
                return attr_switch

        def create_fk_function():
            """
            create fk control by matching the limb joints and parent in fk hierarchy form
            """

            for i in range(len(self.list_limb_joint)):
                ctrl_fk = list_limb_ctrl_fk[i]
                previous_ctrl_fk = list_limb_ctrl_fk[i - 1]
                jnt_fk = list_limb_joint_fk[i]

                # create controller
                utils.create_control(name=ctrl_fk,
                                     axis=axis_forward_abs,
                                     match=jnt_fk,
                                     parent=grp_fk_controls,
                                     shape="sphere",
                                     size=1.4)

                if self.mirror_control_scale:
                    parent_target = utils.freeze_group_classic(ctrl_fk, "grpCtrl")[0]
                    cmds.setAttr(parent_target + ".s", -1, -1, -1, typ="double3")
                else:
                    parent_target = utils.freeze_group_classic(ctrl_fk, "grpCtrl")[0]

                cmds.parentConstraint(ctrl_fk, jnt_fk)
                cmds.connectAttr("{}.rotateOrder".format(ctrl_fk), "{}.rotateOrder".format(jnt_fk),f=1)

                # parent in hierarchy
                if i != 0:
                    cmds.parent(parent_target, previous_ctrl_fk)

            # add stretch function
            invert = -1 if self.mirror_control_scale else 1

            [cmds.addAttr(control, ln="stretch", at="float", k=1) for control in list_limb_ctrl_fk[0:2]]

            for i, control in enumerate(list_limb_ctrl_fk):
                if i == 0:
                    continue

                before_control = list_limb_ctrl_fk[i - 1]
                grp_stretch = utils.freeze_group_classic(control, "grpStretch")[0]

                if self.axis_forward != axis_forward_abs:
                    node_uc = cmds.createNode("unitConversion")
                    cmds.connectAttr("{}.stretch".format(before_control), "{}.input".format(node_uc))
                    cmds.setAttr(node_uc + ".conversionFactor", -1 * invert)
                    input = "{}.output".format(node_uc)

                else:
                    input = "{}.stretch".format(before_control)

                cmds.connectAttr(input, "{}.t{}".format(grp_stretch, axis_forward_abs))

            # FK SPACE SWITCH
            if self.fk_space_switch:
                grp_output = utils.create_enum_space_classic(object_attr=list_limb_ctrl_fk[0],
                                                             list_space=self.list_fk_switch_target,
                                                             list_nice_name=self.list_fk_switch_name,
                                                             target=list_limb_ctrl_fk[0],
                                                             type="orient")
                cmds.parent(grp_output, self.grp_local_rig)

        def create_ik_function():
            def create_control():
                ctrl_start, ctrl_pole, ctrl_end = list_limb_ctrl_ik

                # create pole locator
                cmds.spaceLocator(n=loc_pole_dist)
                cmds.parent(loc_pole_dist, grp_ik_controls)

                # create world ik parent
                grp_limb_ik_world_parent = utils.cname(self.name, "IkWorldParent", grp)
                cmds.group(em=1, n=grp_limb_ik_world_parent)
                cmds.setAttr("{}.inheritsTransform".format(grp_limb_ik_world_parent), 0)
                cmds.connectAttr("{}.worldMatrix[0]".format(config.loc_root), "{}.offsetParentMatrix".format(grp_limb_ik_world_parent))
                cmds.parent(grp_limb_ik_world_parent, grp_ik_controls)

                # create ik control
                for i, ctrl_ik in enumerate(list_limb_ctrl_ik):
                    ctrl_fk =list_limb_ctrl_fk[i]
                    jnt_ik = list_limb_joint_ik[i]
                    main_joint= self.list_limb_joint[i]

                    if i == 1:
                        shape = "sphere"
                        size = 0.5
                    else:
                        shape = "cube"
                        size = 1.4

                    utils.create_control(name=ctrl_ik,
                                         axis=axis_forward_abs,
                                         match=main_joint,
                                         parent=grp_ik_controls,
                                         display_rotate_order=False,
                                         shape=shape,
                                         size=size)

                    cmds.connectAttr("{}.rotateOrder".format(ctrl_fk), "{}.rotateOrder".format(ctrl_ik), f=1)
                    cmds.connectAttr("{}.rotateOrder".format(ctrl_ik), "{}.rotateOrder".format(jnt_ik), f=1)

                    # parent to world
                    if i == 1 or i == 2:
                        cmds.parent(ctrl_ik, grp_limb_ik_world_parent)

                    if i != 1:
                        grp_frz = utils.freeze_group_classic(ctrl_ik, "grpCtrl")[0]

                        if self.mirror_control_scale:
                            cmds.setAttr(grp_frz + ".s", -1, -1, -1, typ="double3")


                # hide ik control
                cmds.setAttr(list_limb_ctrl_ik[0] + ".v", 0)

                # align pole vector control ---------------------------
                # create poly plane
                list_point_create = [cmds.xform(obj, q=1, ws=1, t=1) for obj in list_limb_joint_ik]

                # convert unit
                unit = cmds.currentUnit(q=1, l=1)
                if unit == "m":
                    for i, list_point in enumerate(list_point_create):
                        for a, point in enumerate(list_point):
                            list_point_create[i][a] = point * 100

                plane_poly = cmds.polyCreateFacet(p=list_point_create)[0]
                loc_world = cmds.spaceLocator()[0]
                loc_scale_plane = cmds.spaceLocator()[0]

                # match target to pole position
                scale_value = self.pole_distance * 2

                # snap position
                snap_position = cmds.xform("{}.vtx[1]".format(plane_poly), q=1, t=1, ws=1)
                cmds.xform(loc_pole_dist, ws=1, t=snap_position)

                # match loc scale plane
                cmds.xform(loc_scale_plane, ws=1, t=snap_position)
                cmds.parent(plane_poly, loc_scale_plane)

                if self.use_world_pole:
                    self.world_direction_pole = utils.convert_single_axis_enum_pos(self.world_direction_pole)
                    world_direction_pole_abs = utils.del_neg(self.world_direction_pole)
                    scale_value = scale_value * -1 if self.world_direction_pole != world_direction_pole_abs else scale_value
                    dict_vector = {"x": (scale_value, 0, 0), "y": (0, scale_value, 0), "z": (0, 0, scale_value)}

                    cmds.xform(loc_pole_dist, ws=1, t=dict_vector[world_direction_pole_abs], r=1)
                    print("use world pole")
                elif not self.use_world_pole:
                    cmds.xform(plane_poly, cp=1)

                    cmds.setAttr("{}.scale".format(plane_poly), scale_value, scale_value, scale_value, typ="double3")
                    snap_position = cmds.xform("{}.vtx[1]".format(plane_poly), q=1, t=1, ws=1)
                    cmds.xform(loc_pole_dist, ws=1, t=snap_position)

                    constraint = cmds.normalConstraint(plane_poly, loc_pole_dist)
                    cmds.delete(constraint)

                    cmds.matchTransform(loc_pole_dist, loc_world, rot=1)

                # clean temp
                cmds.delete(loc_world)
                cmds.delete(loc_scale_plane)

                # create pole controller ----------------------------
                cmds.matchTransform(list_limb_ctrl_ik[1], loc_pole_dist)
                cmds.pointConstraint(list_limb_ctrl_ik[1], loc_pole_dist)

                grp_pole_offset = utils.freeze_group_classic([ctrl_pole], "grpCtrl")[0]
                if self.mirror_control_scale:
                    cmds.setAttr(grp_pole_offset + ".s", -1, 1, 1, typ="double3")

                # create pole ik handle
                cmds.ikHandle(n=ik_handle_limb, sol="ikRPsolver", sj=list_limb_joint_ik[0], ee=list_limb_joint_ik[2])
                cmds.parent(ik_handle_limb,grp_ik_controls)

                cmds.setAttr(ik_handle_limb + ".v", 0)

                cmds.poleVectorConstraint(loc_pole_dist, ik_handle_limb)
                cmds.parentConstraint(ctrl_end, ik_handle_limb)

                cmds.addAttr(attr_ik_twist.split(".")[0], ln=attr_ik_twist.split(".")[1], dv=0, at="float", k=1)
                cmds.connectAttr(attr_ik_twist, ik_handle_limb + ".twist")

                # constraint start control -------------------------
                cmds.pointConstraint(ctrl_start, list_limb_joint_ik[0])

                # finalize ----------------
                grp_line = utils.set_line(list_limb_joint_ik[1], ctrl_pole, name=self.name)
                cmds.setAttr(grp_line + ".inheritsTransform", 0)
                cmds.parent(grp_line, self.grp_local_still)
                cmds.connectAttr(attr_switch, grp_line + ".v")


                cmds.orientConstraint(ctrl_end, list_limb_joint_ik[2], mo=1)

            def create_stretchy_v2():
                # create distance locator
                cmds.spaceLocator(n=loc_start_dist)
                cmds.spaceLocator(n=loc_end_dist)

                cmds.parent(loc_start_dist, loc_end_dist, grp_ik_controls)

                cmds.pointConstraint(list_limb_ctrl_ik[0], loc_start_dist)
                cmds.pointConstraint(list_limb_ctrl_ik[2], loc_end_dist)

                utils.add_attribute_divider(list_limb_ctrl_ik[2], "Stretch")
                cmds.addAttr(list_limb_ctrl_ik[2], k=1, ln="autoStretch", at="float", min=0, max=1)
                cmds.addAttr(list_limb_ctrl_ik[2], k=1, ln="upArmStretch", at="float")
                cmds.addAttr(list_limb_ctrl_ik[2], k=1, ln="lowArmStretch", at="float")
                cmds.addAttr(list_limb_ctrl_ik[1], k=1, ln="elbowLock", at="float", min=0, max=1)

                if self.stretch_with_fixed_angle:
                    value_full_length = utils.get_distance_two(loc_start_dist, loc_end_dist)
                else:
                    value_full_length = utils.get_distance_two(list_limb_joint_ik[0], list_limb_joint_ik[1]) + utils.get_distance_two(list_limb_joint_ik[1],
                                                                                                                                                  list_limb_joint_ik[2])

                # Stretch ----------------------------------
                # connection distance
                node_distance = cmds.createNode("distanceBetween", n="{}_autoStretchLength_dist".format(self.name))
                cmds.connectAttr("{}.translate".format(loc_start_dist), "{}.point1".format(node_distance), )
                cmds.connectAttr("{}.translate".format(loc_end_dist), "{}.point2".format(node_distance))

                # connection normalize
                node_md_normalize = cmds.createNode("multiplyDivide", n="{}_stretchLengthNormalize_md".format(self.name))
                cmds.connectAttr("{}.distance".format(node_distance), "{}.input1X".format(node_md_normalize))
                factor = 1 / value_full_length
                cmds.setAttr("{}.input2X".format(node_md_normalize), factor)

                # condition
                node_condition = cmds.createNode("condition", n="{}_autoStretch_cond".format(self.name))
                cmds.setAttr("{}.operation".format(node_condition), 2)
                cmds.connectAttr("{}.distance".format(node_distance), "{}.firstTerm".format(node_condition))
                cmds.setAttr("{}.secondTerm".format(node_condition), value_full_length)
                cmds.connectAttr("{}.outputX".format(node_md_normalize), "{}.colorIfTrueR".format(node_condition))
                cmds.connectAttr("{}.outputX".format(node_md_normalize), "{}.colorIfTrueG".format(node_condition))
                cmds.connectAttr("{}.outputX".format(node_md_normalize), "{}.colorIfTrueB".format(node_condition))

                # mdv stretch connection
                node_md_stretch = cmds.createNode("multiplyDivide", n="{}_stretch_mdv".format(self.name))
                cmds.connectAttr("{}.outColor".format(node_condition), "{}.input1".format(node_md_stretch))
                cmds.setAttr("{}.input2X".format(node_md_stretch), cmds.getAttr("{}.t{}".format(list_limb_joint_ik[1], axis_forward_abs)))  # forearm translate
                cmds.setAttr("{}.input2Y".format(node_md_stretch), cmds.getAttr("{}.t{}".format(list_limb_joint_ik[2], axis_forward_abs)))  # wrist translate

                # blend color connection
                node_bc_stretch = cmds.createNode("blendColors", n="{}_stretchBlend_bc".format(self.name))
                cmds.connectAttr("{}.outputX".format(node_md_stretch), "{}.color1R".format(node_bc_stretch))
                cmds.connectAttr("{}.outputY".format(node_md_stretch), "{}.color1G".format(node_bc_stretch))

                output_node_md_stretch = cmds.getAttr("{}.output".format(node_md_stretch))[0]
                cmds.setAttr("{}.color2".format(node_bc_stretch), output_node_md_stretch[0], output_node_md_stretch[1], output_node_md_stretch[2], typ="double3")
                cmds.connectAttr("{}.autoStretch".format(list_limb_ctrl_ik[2]), "{}.blender".format(node_bc_stretch))

                # stretch conversion
                node_md_conversion = cmds.createNode("multiplyDivide", n="{}_stretchConversion_mdv".format(self.name))
                cmds.connectAttr("{}.upArmStretch".format(list_limb_ctrl_ik[2]), "{}.input1X".format(node_md_conversion))
                cmds.connectAttr("{}.lowArmStretch".format(list_limb_ctrl_ik[2]), "{}.input1Y".format(node_md_conversion))
                conversion_factor = -1 if axis_forward_abs != self.axis_forward else 1
                cmds.setAttr("{}.input2".format(node_md_conversion), conversion_factor, conversion_factor, conversion_factor, typ="double3")

                # stretch adjust
                node_pma_stretch = cmds.createNode("plusMinusAverage", n="{}_stretchAdd_pma".format(self.name))
                cmds.connectAttr("{}.output".format(node_bc_stretch), "{}.input3D[0]".format(node_pma_stretch))
                cmds.connectAttr("{}.output".format(node_md_conversion), "{}.input3D[1]".format(node_pma_stretch))

                # blend color lock pole
                node_bc_lock = cmds.createNode("blendColors", n="{}_stretchBlend_bc".format(self.name))
                cmds.connectAttr("{}.output3Dx".format(node_pma_stretch), "{}.color2R".format(node_bc_lock))
                cmds.connectAttr("{}.output3Dy".format(node_pma_stretch), "{}.color2G".format(node_bc_lock))
                cmds.connectAttr("{}.elbowLock".format(list_limb_ctrl_ik[1]), "{}.blender".format(node_bc_lock))

                # Pole Lock ----------------------------------
                node_dist_up = cmds.createNode("distanceBetween", n="{}_lockStart_dist".format(self.name))
                cmds.connectAttr("{}.translate".format(loc_start_dist), "{}.point1".format(node_dist_up))
                cmds.connectAttr("{}.translate".format(loc_pole_dist), "{}.point2".format(node_dist_up))

                node_dist_low = cmds.createNode("distanceBetween", n="{}_lockEnd_dist".format(self.name))
                cmds.connectAttr("{}.translate".format(loc_end_dist), "{}.point1".format(node_dist_low))
                cmds.connectAttr("{}.translate".format(loc_pole_dist), "{}.point2".format(node_dist_low))

                node_md_lock = cmds.createNode("multiplyDivide", n="{}_lockConversion_mdv".format(self.name))
                cmds.connectAttr("{}.distance".format(node_dist_up), "{}.input1X".format(node_md_lock))
                cmds.connectAttr("{}.distance".format(node_dist_low), "{}.input1Y".format(node_md_lock))
                cmds.connectAttr("{}.outputX".format(node_md_lock), "{}.color1R".format(node_bc_lock))
                cmds.connectAttr("{}.outputY".format(node_md_lock), "{}.color1G".format(node_bc_lock))
                conversion_value = -1 if self.axis_forward != axis_forward_abs else 1
                cmds.setAttr("{}.input2X".format(node_md_lock), conversion_value)
                cmds.setAttr("{}.input2Y".format(node_md_lock), conversion_value)

                # Connect to output ------------------------------
                cmds.connectAttr("{}.outputR".format(node_bc_lock), "{}.t{}".format(list_limb_joint_ik[1], axis_forward_abs))
                cmds.connectAttr("{}.outputG".format(node_bc_lock), "{}.t{}".format(list_limb_joint_ik[2], axis_forward_abs))

            def create_blend_space():
                if not self.list_switch_target:
                    raise Exception("You must input this field : list_switch_target")
                elif len(self.list_switch_target) != len(self.list_switch_name):
                    raise Exception("List switch target and List switch name doesn't match count")

                output_grp = utils.create_enum_space_classic(object_attr=list_limb_ctrl_ik[2],
                                                             list_space=self.list_switch_target,
                                                             list_nice_name=self.list_switch_name,
                                                             target=list_limb_ctrl_ik[2],
                                                             type="parent")

                cmds.parent(output_grp, self.grp_local_still)

            # create attributes
            attr_ik_stretch = list_limb_ctrl_ik[2] + ".autoStretch"
            attr_ik_volume = list_limb_ctrl_ik[2] + ".autoVolume"
            attr_ik_twist = list_limb_ctrl_ik[2] + ".twistIk"
            attr_ik_snap = list_limb_ctrl_ik[2] + ".snapIk"
            attr_ik_move_pole = list_limb_ctrl_ik[2] + ".autoMovePoleIk"

            attr_length_total = ctrl_option + ".totalLength"
            attr_length_lower = ctrl_option + ".lowLength"
            attr_length_upper = ctrl_option + ".upLength"

            # ik function con
            create_control()
            create_stretchy_v2()

            create_blend_space() if self.hand_space_switch else None

        def set_default_switch():
            # set to default value
            if self.default_switch == 1:
                value_multiplier = 1
            elif self.default_switch == 0:
                value_multiplier = 0
            else:
                raise Exception("Command Error")

            value =  self.attribute_switch_range * value_multiplier
            cmds.setAttr(attr_switch,value)

        def create_wrist_corrective():
            if not self.enable_wrist_corrective:
                return

            list_name = ["Front","Up","Back","Low"]

            # axis_rotate_up,axis_rotate_side = axis_side

            # list_
            #
            # for i,joint in enumerate(self.list_wrist_joint):
            # part_name = list_name[i]

            self.wrist_corrective_axis_push = utils.convert_single_axis_enum(self.wrist_corrective_axis_push)
            self.wrist_axis = utils.convert_triple_axis_enum(self.wrist_axis)

            axis_push_abs = utils.del_neg(self.wrist_corrective_axis_push)
            axis_forward_abs,axis_up_abs,axis_side_abs = self.wrist_axis

            # Up
            utils.create_corrective_joint(block1=self.list_limb_joint[1],
                                          block2=self.list_limb_joint[2],
                                          joint_push=self.list_wrist_joint[1],
                                          axis_push=axis_push_abs,
                                          axis_forward=axis_forward_abs,
                                          axis_side=axis_side_abs,
                                          parent=self.grp_local_still,
                                          tag_name=self.name+"Up",
                                          invert_angle=self.wrist_corrective_upper_invert
                                          )

            # Low
            utils.create_corrective_joint(block1=self.list_limb_joint[1],
                                          block2=self.list_limb_joint[2],
                                          joint_push=self.list_wrist_joint[3],
                                          axis_push=axis_push_abs,
                                          axis_forward=axis_forward_abs,
                                          axis_side=axis_side_abs,
                                          parent=self.grp_local_still,
                                          tag_name=self.name+"Low",
                                          invert_angle=self.wrist_corrective_lower_invert
                                          )

            # Front
            utils.create_corrective_joint(block1=self.list_limb_joint[1],
                                          block2=self.list_limb_joint[2],
                                          joint_push=self.list_wrist_joint[0],
                                          axis_push=axis_push_abs,
                                          axis_forward=axis_forward_abs,
                                          axis_side=axis_up_abs,
                                          parent=self.grp_local_still,
                                          tag_name=self.name+"Front",
                                          invert_angle=self.wrist_corrective_front_invert
                                          )

            # Back
            utils.create_corrective_joint(block1=self.list_limb_joint[1],
                                          block2=self.list_limb_joint[2],
                                          joint_push=self.list_wrist_joint[2],
                                          axis_push=axis_push_abs,
                                          axis_forward=axis_forward_abs,
                                          axis_side=axis_up_abs,
                                          parent=self.grp_local_still,
                                          tag_name=self.name+"Back",
                                          invert_angle=self.wrist_corrective_lower_invert
                                          )

        def create_elbow_corrective():
            if not self.enable_elbow_corrective:
                return

            self.elbow_corrective_axis_push = utils.convert_single_axis_enum(self.elbow_corrective_axis_push)
            self.elbow_axis = utils.convert_triple_axis_enum(self.elbow_axis)

            jnt_push_inside,jnt_push_outside = self.list_elbow_joint
            axis_elbow_forward_abs,axis_elbow_up_abs,axis_elbow_side_abs = self.elbow_axis

            # jnt push inside
            utils.create_corrective_joint(
                block1=self.list_limb_joint[0],
                block2=self.list_limb_joint[1],
                joint_push=jnt_push_inside,
                axis_push=self.elbow_corrective_axis_push,
                axis_forward=axis_elbow_forward_abs,
                axis_side = axis_elbow_up_abs,
                parent=self.grp_local_still,
                invert_angle=True,
                tag_name=self.name+"ElbowInside"
            )

            # jnt push outside
            utils.create_corrective_joint(
                block1=self.list_limb_joint[0],
                block2=self.list_limb_joint[1],
                joint_push=jnt_push_outside,
                axis_push=self.elbow_corrective_axis_push,
                axis_forward=axis_elbow_forward_abs,
                axis_side = axis_elbow_up_abs,
                parent=self.grp_local_still,
                invert_angle=True,
                tag_name=self.name+"ElbowOutside"
            )
        def create_shoulder_corrective():
            if not self.enable_shoulder_corrective:
                return

            if not self.clavicle_enable:
                raise Exception("Require Clavicle Enable")

            self.shoulder_corrective_axis_push = utils.convert_single_axis_enum(self.shoulder_corrective_axis_push)
            self.shoulder_axis = utils.convert_triple_axis_enum(self.shoulder_axis)

            jnt_push_outside = self.list_shoulder_joint[0]
            axis_shoulder_forward_abs,axis_shoulder_up_abs,axis_shoulder_side_abs = self.shoulder_axis

            # jnt push outside
            utils.create_corrective_joint(
                block1=self.jnt_clavicle,
                block2=self.list_limb_joint[0],
                joint_push=jnt_push_outside,
                axis_push=self.shoulder_corrective_axis_push,
                axis_forward=axis_shoulder_forward_abs,
                axis_side = axis_shoulder_side_abs,
                parent=self.grp_local_still,
                invert_angle=self.shoulder_corrective_invert,
                tag_name=self.name+"Shoulder"
            )

        if len(self.list_limb_joint) != 3:
            cmds.confirmDialog(m="List Limb Joint Only Support 3 Joints")
            raise Exception("List Limb Joint Only Support 3 Joints")
        elif self.ik_pivot_enable and self.list_ik_pivot is []:
            cmds.confirmDialog(m="List Foot Pivot is Blank , Please Input Inner , Outer , Heel and End Pivot")
            raise Exception("List Foot Pivot is Blank , Please Input Inner , Outer , Heel and End Pivot")

        # systems config

        list_limb_joint_fk = ["{}Fk".format(joint) for joint in self.list_limb_joint]
        list_limb_joint_ik = ["{}Ik".format(joint) for joint in self.list_limb_joint]

        list_limb_ctrl_fk = ["{}_{}Fk".format(ctrl, joint) for joint in self.list_limb_joint]
        list_limb_ctrl_ik = ["{}_{}Ik".format(ctrl, joint) for joint in self.list_limb_joint]

        self.axis_forward = utils.convert_single_axis_enum(self.axis_forward)
        self.axis_pole = utils.convert_single_axis_enum(self.axis_pole)
        axis_forward_abs = utils.del_neg(self.axis_forward)
        axis_pole_abs = utils.del_neg(self.axis_pole)

        if axis_forward_abs == axis_pole_abs:
            cmds.confirmDialog(m="Axis Forward and Axis Side is the same axis!")
            raise Exception("Axis Forward and Axis Side is the same axis!")

        ik_handle_limb = "ikHandle_{}".format(self.name)

        # foot variables
        if self.ik_pivot_enable:
            list_foot_joint = [self.jnt_ball, self.jnt_tip]  # joint ball and joint toe
        else:
            list_foot_joint = []

        grp_limb_parent = utils.cname(self.name,"LimbParent",grp)
        grp_clavicle_parent = utils.cname(self.name,"ClavicleParent",grp)


        grp_ik_controls = "{}_{}Ik".format(grp, self.name)
        grp_fk_controls = "{}_{}Fk".format(grp, self.name)

        grp_ik_joints = "{}_{}IkJnts".format(grp, self.name)
        grp_fk_joints = "{}_{}FkJnts".format(grp, self.name)

        loc_pole_dist = "{}_{}PoleDist".format(loc, self.name)
        loc_start_dist = "{}_{}StartDist".format(loc, self.name)
        loc_end_dist = "{}_{}EndDist".format(loc, self.name)

        ctrl_option = "{}_{}Setting".format(ctrl, self.name)
        ctrl_clavicle = "{}_{}".format(self.jnt_clavicle,ctrl)

        # system variables
        attr_switch = ctrl_option + ".FkIk"

        ctrl_knee_ribbon = utils.cname(self.name, "KneeRbn", ctrl)

        # Build
        create_hierarchy()
        attr_switch = create_ctrl_option()

        create_switch_func()

        create_clavicle()

        create_fk_function()
        create_ik_function()

        # additional function
        add_ribbon_function()
        create_ik_pivot_function()

        clavicle_connet_limb()

        create_wrist_corrective()
        create_elbow_corrective()
        create_shoulder_corrective()

        make_finalize()
        set_default_switch()


    def core_unbuild(self):
        for joint in self.list_limb_joint+[self.jnt_clavicle,self.jnt_ball,self.jnt_tip]:
            # ignore None Type
            if not cmds.objExists(joint):
                continue

            # Break Connection Each Joint
            utils.break_connection(joint,rot=True,pos=True,scl=True)

class Fingers(rig_class.Rig):
    """Limb

Create Limb Rig Systems for Arm / Leg , Also have Ribbon / Advance Foot and Simple Twist Joint Optional

Variables:
name (string) : Name of your part. for example "L_leg" , "R_arm".
list_limb_joint (string) : Select Three of Limb Joint. for example ["upLeg","lowLeg","footAnkle"].
axis_forward(string) : axis direction of aiming forward. for example "x"
axis_pole(string) : axis direction of elbow that aiming to pole controller. for example "x","-x"
default_switch_value(string) : Default value of Fk/Ik Switch ,Fk(0) ,Ik (1)
pole_distance(float):amount of distance between ik pole controller and character
parent(string) :Name of Parent Object ,for example Pelvis for leg, Clavicle for arm

foot_enable(bool):Enable Foot Systems
jnt_ball(string) :name of joint ball
jnt_toe(string) :name of joint toe

list_foot_pivot(stringArray) : names of inner , outer , heel and end pivot reference (locator)
ribbon_enable(bool): Enable Ribbon Joint Systems
joint_up_ribbon(stringArray) : List of Upper Ribbon joints
joint_low_ribbon(stringArray) :List of Lower Ribbon joints
finalize(bool): Lock and hide unnecessary attributes and object for animators

list_finger_base_joints(stringArray) : List of base joint (Sort by Index > Middle > Ring > Pinky )
list_finger_start_joints(stringArray) : List of start joint (Sort by Index > Middle > Ring > Pinky )

enable_thumb(bool) : If Checked, Thumb Rig Enable.
thumb_base_joint(string) : name of thumb base joint
thumb_start_joint(string) : name of thumb start joint

enable_ik_hand_support(bool)  : If Checked, enable_ik_hand_support.
jnt_ik_middle(string) : name of joint middle ik reverse

enable_cup_control(bool)  : If Checked, enable_cup_control
cup_control_pivot(string) : name of cup control pivot (get translate and orient)

list_finger_keyword(stringArray) : list_finger_keyword
thumb_keyword(string):thumb_keyword

ignore_tip_joint(bool):ignore_tip_joint
mirror_control_scale(bool):mirror_control_scale

debug_mode(bool):debug_mode
axis_pole_finger(enum) : axis of pole finger ik
pole_distance(float) : distance of pole controller

filter_finger_by_keyword(bool) : Filter Finger by Given Keyword.
filter_thumb_by_keyword(bool) : Filter Finger by Given Keyword.

enable_finger_base(bool) : Enable finger base.
enable_thumb_base(bool) : Enable thumb base.

    """

    def __init__(self):
        super().__init__()

        # @ Setting
        self.name = "{}_fingers".format(L)

        # $ Fingers
        self.list_finger_start_joints = []
        # -
        self.enable_finger_base = False
        self.list_finger_base_joints = []
        # * enable_finger_base
        # -
        self.axis_pole_finger = utils.get_single_axis_enum()
        self.pole_distance = 3.0
        # -
        self.filter_finger_by_keyword = False
        self.list_finger_keyword = ["index", "middle", "ring", "pinky"]
        # * filter_finger_by_keyword

        # $ Thumb
        self.enable_thumb = False
        self.thumb_start_joint = ""
        # * enable_thumb
        # -
        self.enable_thumb_base = False
        self.thumb_base_joint = ""
        # * enable_thumb_base
        # -
        self.filter_thumb_by_keyword = False
        self.thumb_keyword = "thumb"
        # * filter_thumb_by_keyword
        # @ Features
        # $ Ik Hand Pin Attach
        self.enable_ik_hand_support = False
        self.jnt_ik_middle = ""

        # $ Cup Controls Feature
        self.enable_cup_control = False
        self.cup_control_pivot = ""

        self.debug_mode = False
        self.parent = ""
        self.mirror_control_scale = False

    def core_build(self):
        def support_ik_hand():
            for i, key in enumerate(dict_fingers_control):
                control_start = dict_fingers_control[key][0]
                parent_control_start = cmds.listRelatives(control_start, p=1, typ="transform")[0]

                grp_matrix_ik = cmds.group(em=1, n=control_start + "_grpParentIk")

                # mult matrix create connection
                node_mm = cmds.createNode("multMatrix", n="{}_mm".format(control_start))
                cmds.connectAttr("{}.worldMatrix[0]".format(self.jnt_ik_middle), "{}.matrixIn[0]".format(node_mm))
                cmds.connectAttr("{}.worldInverseMatrix[0]".format(parent_control_start), "{}.matrixIn[1]".format(node_mm))

                # connect decompose to matrix grp
                node_dcm = cmds.createNode("decomposeMatrix", n="{}_dcm".format(control_start))
                cmds.connectAttr("{}.matrixSum".format(node_mm), "{}.inputMatrix".format(node_dcm))
                cmds.connectAttr("{}.outputTranslate".format(node_dcm), "{}.t".format(grp_matrix_ik))
                cmds.connectAttr("{}.outputRotate".format(node_dcm), "{}.r".format(grp_matrix_ik))
                cmds.connectAttr("{}.outputScale".format(node_dcm), "{}.s".format(grp_matrix_ik))

                # parent control to matrix ik
                cmds.parent(grp_matrix_ik, parent_control_start)

                # fix cup and base controller ------------------------------------------
                grp_cup_fix = cmds.group(em=1, n=control_start + "_grpCup")
                cmds.matchTransform(grp_cup_fix, list_base_fingers_controls[i])
                cmds.parent(grp_cup_fix, grp_matrix_ik)
                cmds.parent(control_start, grp_cup_fix)

                utils.freeze_group_classic(control_start)

                # create pma node
                node_pma = cmds.createNode("plusMinusAverage", n="{}CupResult_pma".format(control_start))
                cmds.connectAttr("{}.r".format(list_cups_groups[i]), "{}.input3D[0]".format(node_pma))
                cmds.connectAttr("{}.r".format(list_base_fingers_controls[i]), "{}.input3D[1]".format(node_pma))

                # connect pma node to output
                utils.freeze_group_classic(grp_cup_fix, "grpCupOff")

                if self.mirror_control_scale:
                    utils.connect_attr_conversion_three(list_input1=["{}.output3Dx".format(node_pma),"{}.output3Dy".format(node_pma),"{}.output3Dz".format(node_pma)],
                                                        list_output=[grp_cup_fix+".rx",grp_cup_fix+".ry",grp_cup_fix+".rz"],
                                                        list_conversion=[-1,-1,-1])
                else:

                    cmds.connectAttr("{}.output3D".format(node_pma), "{}.r".format(grp_cup_fix))

        def is_keyword(word,keywords):
            return any(keyword in word for keyword in keywords)

        def get_finger_list():
            # append fingers chain to dictionary
            for i, start_joint in enumerate(self.list_finger_start_joints):
                # add child joint
                joint_child = sorted(cmds.listRelatives(start_joint, ad=1, typ="joint"))

                if self.enable_finger_base:
                    list_joint_chain = [self.list_finger_base_joints[i],start_joint] + joint_child
                else:
                    list_joint_chain = [start_joint] + joint_child

                # filter
                if self.filter_finger_by_keyword:
                    for joint in list_joint_chain:
                        if not is_keyword(joint,self.list_finger_keyword):
                            list_joint_chain.remove(joint)

                # append
                list_finger_joint.append(list_joint_chain)
        def get_thumb_list():
            if not self.enable_thumb:
                return

            # add child joint
            joint_child = cmds.listRelatives(self.thumb_start_joint, ad=1, typ="joint")
            if joint_child:
                joint_child.reverse()

            if self.enable_thumb_base:
                list_joint_chain = [self.thumb_base_joint,self.thumb_start_joint] + joint_child
            else:
                list_joint_chain = [self.thumb_start_joint]+joint_child

            # filter
            if self.filter_thumb_by_keyword:
                for joint in list_joint_chain:
                    if not is_keyword(joint,self.filter_thumb_by_keyword):
                        list_joint_chain.remove(joint)

            # append
            list_thumb_joint.append(list_joint_chain)


        def create_thumb_control():
            def create_thumb_base_control():
                if not self.enable_thumb_base:
                    return

                for i,list_finger_chain in enumerate(list_thumb_joint):
                    joint_name = list_finger_chain[0]
                    control_name = "{}_{}".format(joint_name,ctrl)

                    utils.create_control(name=control_name,
                                         match=joint_name,
                                         parent=self.grp_local_anim,
                                         freeze_group=True,
                                         mirror_freeze_group=True,
                                         constraint="parent",
                                         size=0.5)

            def create_thumb_control():
                for list_joint_chain in list_thumb_joint:
                    if self.enable_thumb_base:
                        parent = "{}_{}".format(list_joint_chain[0], ctrl)
                    else:
                        parent = self.grp_local_anim

                    if self.enable_thumb_base:
                        del list_joint_chain[0]

                    utils.create_finger_rig(list_finger_joint=list_joint_chain,
                                            hand_space=self.grp_local_anim,
                                            axis_pole=self.axis_pole_finger,
                                            move_pole_distance=self.pole_distance,
                                            parent=parent,
                                            tag_name="{}_{}".format(self.name, list_joint_chain[0]),
                                            mirror_control_scale=self.mirror_control_scale,
                                            is_thumb=True)

            create_thumb_base_control()
            create_thumb_control()

        def create_pose_attributes():
            def add_fist():
                # create fist attributes
                cmds.addAttr(control_pose, ln="fist", k=1)
                invert_value = -1 if self.invert_fist_attribute else 1
                utils.add_attribute_divider(shape_option, "Fist")

                for key in dict_fingers.keys():
                    for i, control in enumerate(dict_fingers[key]):
                        if i < self.start_fist_offset:
                            continue

                        # add custom attribute
                        attr_custom = "{}{}Fist".format(key, i + 1)
                        attr_custom_full = shape_option + "." + attr_custom
                        cmds.addAttr(shape_option, ln=attr_custom, k=1, at="float")
                        cmds.setAttr(attr_custom_full, 5 * invert_value)

                        # connection
                        node_mdl = cmds.createNode("multDoubleLinear", n="{}_{}_mdl".format(self.name, attr_custom))
                        cmds.connectAttr(control_pose + ".fist", node_mdl + ".input1")
                        cmds.connectAttr(attr_custom_full, "{}.input2".format(node_mdl))
                        input_fist = node_mdl + ".output"

                        # connect to output
                        grp_rot = utils.freeze_group_classic(control, add="fistRot")[0]
                        cmds.connectAttr(input_fist, "{}.r{}".format(grp_rot, self.axis_side))

            def add_spread():
                # create spread attributes
                cmds.addAttr(control_pose, ln="spread", k=1)
                utils.add_attribute_divider(shape_option, "Spread")

                invert_value = -1 if self.invert_spread_attribute else 1

                for key in dict_fingers.keys():
                    if key == "thumb" or key == "middle":
                        continue

                    for i, control in enumerate(dict_fingers[key]):
                        if i != self.start_fist_offset:
                            continue

                        # add custom attribute
                        attr_custom = "{}{}Spread".format(key, i + 1)
                        attr_custom_full = shape_option + "." + attr_custom
                        cmds.addAttr(shape_option, ln=attr_custom, k=1, at="float")

                        if key == "index":
                            cmds.setAttr(attr_custom_full, -5 * invert_value)
                        elif key == "ring":
                            cmds.setAttr(attr_custom_full, 2.5 * invert_value)
                        elif key == "pinky":
                            cmds.setAttr(attr_custom_full, 5 * invert_value)

                        # connection
                        node_mdl = cmds.createNode("multDoubleLinear", n="{}_{}_mdl".format(self.name, attr_custom))
                        cmds.connectAttr(control_pose + ".spread", node_mdl + ".input1")
                        cmds.connectAttr(attr_custom_full, "{}.input2".format(node_mdl))
                        input_spread = node_mdl + ".output"

                        grp_rot = utils.freeze_group_classic(control, add="spreadRot")[0]
                        cmds.connectAttr(input_spread, "{}.r{}".format(grp_rot, self.axis_up))

            def add_cup():
                # create fist attributes
                cmds.addAttr(control_pose, ln="cup", k=1)
                invert_value = -1 if self.invert_fist_attribute else 1
                utils.add_attribute_divider(shape_option, "Fist")

                for key in dict_fingers.keys():
                    if key == "index":
                        value_set = 4
                    elif key == "middle":
                        value_set = 3
                    elif key == "ring":
                        value_set = 2
                    elif key == "pinky":
                        value_set = 1
                    elif key == "thumb":
                        continue

                    for i, control in enumerate(dict_fingers[key]):
                        # add custom attribute
                        attr_custom = "{}{}Cup".format(key, i + 1)
                        attr_custom_full = shape_option + "." + attr_custom
                        cmds.addAttr(shape_option, ln=attr_custom, k=1, at="float")
                        cmds.setAttr(attr_custom_full, 5 * invert_value)

                        # connection
                        node_mdl = cmds.createNode("multDoubleLinear", n="{}_{}_mdl".format(self.name, attr_custom))
                        cmds.connectAttr(control_pose + ".cup", node_mdl + ".input1")
                        cmds.connectAttr(attr_custom_full, "{}.input2".format(node_mdl))
                        input_fist = node_mdl + ".output"

                        # connect to output
                        grp_rot = utils.freeze_group_classic(control, add="cupRot")[0]
                        cmds.connectAttr(input_fist, "{}.r{}".format(grp_rot, self.axis_side))

            def add_break():
                pass

            # resample
            dict_fingers = {}
            for control in self.list_fingers_control:
                for name in self.list_fingers_name:
                    if name in control:
                        if name in dict_fingers:  # append to dict
                            dict_fingers[name].append(control)
                        else:  # create a new dict
                            dict_fingers[name] = [control]

            for key in dict_fingers.keys():
                dict_fingers[key].sort()
                print("Dict Fingers Controls : ", dict_fingers[key])

            # create controller
            control_pose = "{}_handPose_{}".format(self.name, ctrl)
            utils.create_control(name=control_pose, match=self.parent, parent=self.grp_local_anim)
            utils.freeze_group_classic(control_pose, "grpCtrl")
            utils.lock_attributes(control_pose, r=1, s=1, t=1, v=1, k=0, l=1)
            utils.add_attribute_divider(control_pose, "Fingers")

            shape_option = utils.add_option_shape(object=control_pose, name="FingersRigSetting")

            add_fist()
            add_spread()
            add_cup()

        def create_fingers_control():
            def create_fingers_base_control():
                if not self.enable_finger_base:
                    return

                for i,list_finger_chain in enumerate(list_finger_joint):
                    joint_name = list_finger_chain[0]
                    control_name = "{}_{}".format(joint_name,ctrl)

                    utils.create_control(name=control_name,
                                         match=joint_name,
                                         parent=self.grp_local_anim,
                                         freeze_group=True,
                                         mirror_freeze_group=True,
                                         constraint="parent",
                                         size=0.5)

            def create_fingers_control():
                for list_joint_chain in list_finger_joint:
                    if self.enable_finger_base:
                        parent = "{}_{}".format(list_joint_chain[0], ctrl)
                    else:
                        parent = self.grp_local_anim

                    if self.enable_finger_base:
                        del list_joint_chain[0]

                    utils.create_finger_rig(list_finger_joint=list_joint_chain,
                                            hand_space=self.grp_local_anim,
                                            axis_pole=self.axis_pole_finger,
                                            move_pole_distance=self.pole_distance,
                                            parent=parent,
                                            tag_name="{}_{}".format(self.name, list_joint_chain[0]),
                                            mirror_control_scale=self.mirror_control_scale)

            create_fingers_base_control()
            create_fingers_control()



        def create_cup_control():
            utils.create_control(name=ctrl_cup, match=self.cup_control_pivot, parent=self.grp_local_anim)
            utils.freeze_group_classic(ctrl_cup, "grpCtrl")

            # create option shape
            cup_option_shape = utils.add_option_shape(ctrl_cup, "CupMultiplierSetting")
            utils.add_attribute_divider(cup_option_shape, "Cup Multiply")
            cmds.addAttr(cup_option_shape, ln="middle", k=1, min=0, max=1, dv=0.25)
            cmds.addAttr(cup_option_shape, ln="ring", k=1, min=0, max=1, dv=0.5)
            cmds.addAttr(cup_option_shape, ln="pinky", k=1, min=0, max=1, dv=1)

            # connection for 3 root joint
            for i, control_target in enumerate(list_base_fingers_controls):
                grp_output = utils.freeze_group_classic(control_target, "grpCup")[0]

                if i == 0:
                    pass
                else:
                    keyword = self.list_finger_keyword[i]

                    node_mdl = cmds.createNode("multiplyDivide", n="{}_{}Cup_mdl".format(self.name, keyword))

                    for axis in ["x", "y", "z"]:
                        cmds.connectAttr("{}.r{}".format(ctrl_cup, axis), "{}.input1{}".format(node_mdl, axis.upper()))
                        cmds.connectAttr("{}.{}".format(cup_option_shape, keyword), "{}.input2{}".format(node_mdl, axis.upper()))

                    # connect to output control
                    cmds.connectAttr("{}.output".format(node_mdl), "{}.r".format(grp_output))

                list_cups_groups.append(grp_output)

        def finalize():
            if self.debug_mode:
                return

            for list_data in  dict_fingers_control.values():
                for control in list_data:
                    utils.lock_attributes(control, s=1, v=1, l=1, k=0)

            for i,control in enumerate(list_thumb_controls):
                if i == 0:
                    utils.lock_attributes(control, s=1, v=1, l=1, t=1, k=0)
                else:
                    utils.lock_attributes(control, s=1, v=1, l=1, k=0)

            for control in list_base_fingers_controls:
                utils.lock_attributes(control, s=1, v=1, l=1, t=1, k=0)

            utils.lock_attributes(ctrl_cup, s=1, v=1, l=1, t=1, k=0)

        if len(self.list_finger_base_joints) == 0 or len(self.list_finger_start_joints) == 0:
            raise Exception("Invalid Input")

        elif len(self.list_finger_base_joints) != len(self.list_finger_start_joints):
            raise Exception("invalid Input")

        # variables
        self.axis_pole_finger = utils.convert_single_axis_enum(self.axis_pole_finger)

        list_finger_joint = []
        list_thumb_joint = []

        ctrl_cup = "{}_cup_ctrl".format(self.name)
        list_cups_groups = []

        # build
        get_finger_list()
        get_thumb_list()

        # create controller
        create_fingers_control()
        create_thumb_control()
        #
        # # extra function
        # create_cup_control() if self.enable_cup_control else None
        # support_ik_hand() if self.enable_ik_hand_support else None
        #
        # finalize()
