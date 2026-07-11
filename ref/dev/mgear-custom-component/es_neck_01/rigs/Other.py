import maya.cmds as cmds
import EasySkeleton.config as config
from EasySkeleton import rig_class
from EasySkeleton.config import *
import EasySkeleton.utils as utils

class Collider(rig_class.Rig):
    """ Skirt Collide

    Variables :
    node_name(string) : Name of part
    driver(string) : The Center of Gravity that will drive the main collide object.
    parent(string) : The Driver that will drive the collide vectors.
    list_driver_vector(stringArray) : input two object that will define the vector of center collide
    list_pushed_vector(stringArray) : input two object that will define the vector of collide
    list_fk_joints(stringArray) : input list of chain fk
    """

    def __init__(self):
        super().__init__()

        self.name = "collider"

        # @ Setting
        self.driver = ""

        # -
        self.parent = ""
        # -
        self.use_custom_driver_vector = False
        self.list_driver_vector = []
        # *use_custom_driver_vector

        # -
        self.pushed_object_direction = ""

        # -
        self.axis_driven = "x"
        self.pivot_driven = ""

        self.pushed_driven = 90
        self.pushed_intensity = 1.0
        # -
        self.enable_between_driven = False
        self.list_both_driven_attr_path = []
        self.invert_first_value = False
        self.invert_second_value = False
        # *enable_between_driven

        # -
        self.list_fk_joints = []

        # Optional
        self.debug_mode = False

    def core_build(self):
        def create_hierarchy():
            cmds.group(em=1, n=grp_collide_space, p=self.grp_local_rig)
            cmds.group(em=1, n=grp_center_space, p=self.grp_local_rig)

            cmds.group(em=1, n=grp_collide_control, p=self.grp_local_rig)

            cmds.group(em=1, n=grp_driven, p=grp_collide_control)

        def create_center_vector():
            if len(self.list_driver_vector) != 2 and self.use_custom_driver_vector:
                raise Exception("invalid input")

            # constraint grp center space
            cmds.parentConstraint(self.driver, grp_center_space)

            # create locators
            cmds.spaceLocator(n=loc_driver_start)
            cmds.spaceLocator(n=loc_driver_end)

            loc_center_space1_shape = cmds.listRelatives(loc_driver_start, c=1, s=1, typ="locator")[0]
            loc_center_space2_shape = cmds.listRelatives(loc_driver_end, c=1, s=1, typ="locator")[0]

            cmds.parent(loc_driver_start, loc_driver_end, grp_center_space)

            if not self.use_custom_driver_vector:
                cmds.matchTransform(loc_driver_start, self.driver)
                cmds.select(loc_driver_end)
                cmds.move(y=-1, ws=1)
            else:
                cmds.matchTransform(loc_driver_start, self.list_driver_vector[0])
                cmds.matchTransform(loc_driver_end, self.list_driver_vector[1])

            # create vector node (pma)
            cmds.createNode("plusMinusAverage", n=node_pma_center_vector)
            cmds.setAttr(node_pma_center_vector + ".operation", 2)
            cmds.connectAttr(loc_center_space1_shape + ".worldPosition", node_pma_center_vector + ".input3D[0]")
            cmds.connectAttr(loc_center_space2_shape + ".worldPosition", node_pma_center_vector + ".input3D[1]")

        def create_collide_vector():
            # constraint grp center space
            cmds.parentConstraint(self.parent, grp_collide_space)

            # create locators
            loc_collide_space = cmds.spaceLocator(n="{}_collide_space".format(self.name))
            loc_collide_space_shape = cmds.listRelatives(loc_collide_space, c=1, s=1, typ="locator")[0]

            cmds.parent(loc_collide_space, grp_collide_space)

            cmds.matchTransform(loc_collide_space, self.pushed_object_direction)

            # create vector node (pma)
            cmds.createNode("plusMinusAverage", n=node_pma_collide_vector)
            cmds.setAttr(node_pma_collide_vector + ".operation", 2)
            cmds.connectAttr(loc_collide_space_shape + ".worldPosition", node_pma_collide_vector + ".input3D[0]")
            cmds.connectAttr(loc_driver_start + ".worldPosition", node_pma_collide_vector + ".input3D[1]")

        def create_angle_between():
            cmds.createNode("angleBetween", n=node_angle_between)

            cmds.connectAttr(attr_center_vector, node_angle_between + ".vector1")
            cmds.connectAttr(attr_collide_vector, node_angle_between + ".vector2")

        def create_fk_chain():
            # constraint parent to grp control
            cmds.parentConstraint(self.parent, grp_collide_control)

            cmds.matchTransform(grp_driven, self.pivot_driven)
            utils.freeze_group_classic(grp_driven)

            # create chain of fk controls
            recent = None
            for i, joint in enumerate(self.list_fk_joints):
                utils.create_control(name=list_fk_control[i], match=joint, constraint="parent")

                if recent:
                    cmds.parent(list_fk_control[i], recent)
                else:
                    cmds.parent(list_fk_control[i], grp_driven)

                recent = list_fk_control[i]
            utils.freeze_group_classic(list_fk_control)

        def set_driven_node():
            # set driven key by node ---------------------
            # get current angle value
            current_value = cmds.getAttr(attr_angle_between)
            set_value = current_value + self.pushed_driven

            if current_value > set_value:
                min_clamp = set_value
                max_clamp = current_value
            else:
                min_clamp = current_value
                max_clamp = set_value

            # create clamp
            node_clamp = cmds.createNode("clamp", n="{}_range_cmp".format(self.name))

            cmds.setAttr(node_clamp + ".minR", min_clamp)
            cmds.setAttr(node_clamp + ".maxR", max_clamp)
            cmds.connectAttr(attr_angle_between, "{}.inputR".format(node_clamp))

            # create offset
            node_pma = cmds.createNode("plusMinusAverage", n="{}_offset_pma".format(self.name))
            cmds.setAttr("{}.operation".format(node_pma), 2)
            cmds.connectAttr("{}.outputR".format(node_clamp), "{}.input1D[0]".format(node_pma))
            cmds.setAttr("{}.input1D[1]".format(node_pma), current_value)

            # create intensity
            node_mdl_intensity = cmds.createNode("multDoubleLinear", n="{}_intensity_mdl".format(self.name))
            cmds.connectAttr("{}.output1D".format(node_pma), "{}.input1".format(node_mdl_intensity))
            cmds.setAttr("{}.input2".format(node_mdl_intensity), self.pushed_intensity)

            # create switch
            cmds.addAttr(list_fk_control[0], ln="autoCollide", at="float", min=0, max=1, k=1, dv=1)

            node_switch = cmds.createNode("blendTwoAttr", n="{}_blend_bta".format(self.name))
            cmds.connectAttr("{}.output".format(node_mdl_intensity), "{}.input[1]".format(node_switch))
            cmds.setAttr("{}.input[0]".format(node_switch), 0)
            cmds.connectAttr("{}.autoCollide".format(list_fk_control[0]), "{}.attributesBlender".format(node_switch))

            # connect to output
            cmds.connectAttr("{}.output".format(node_switch), "{}.r{}".format(grp_driven, self.axis_driven))

        def set_driven_between():
            node_pma = cmds.createNode("plusMinusAverage", n="{}_sum_pma".format(self.name))
            cmds.connectAttr(self.list_both_driven_attr_path[0], node_pma + ".input1D[0]")
            cmds.connectAttr(self.list_both_driven_attr_path[1], node_pma + ".input1D[1]")

            node_mdl = cmds.createNode("multDoubleLinear", n="{}_avg_mdl".format(self.name))
            cmds.connectAttr(node_pma + ".output1D", node_mdl + ".input1")
            cmds.setAttr("{}.input2".format(node_mdl), 0.5)

            cmds.connectAttr("{}.output".format(node_mdl), "{}.r{}".format(grp_driven, self.axis_driven))

        # Define Variables
        grp_collide_space = "{}_collide_spaces_grp".format(self.name)
        grp_center_space = "{}_center_spaces_grp".format(self.name)

        list_fk_control = ["{}_fk{}_ctrl".format(self.name, i + 1) for i in range(len(self.list_fk_joints))]

        grp_collide_control = "{}_collide_controls_grp".format(self.name)

        grp_driven = "{}_collide_driven_grp".format(self.name)

        node_pma_center_vector = "{}_center_vector_pma".format(self.name)
        attr_center_vector = node_pma_center_vector + ".output3D"

        node_pma_collide_vector = "{}_collide_vector_pma".format(self.name)
        attr_collide_vector = node_pma_collide_vector + ".output3D"

        node_angle_between = "{}_angleResult_agl".format(self.name)
        attr_angle_between = node_angle_between + ".angle"

        loc_driver_start = "{}_centerStart_space".format(self.name)
        loc_driver_end = "{}_centerEnd_space".format(self.name)

        # option_shape = "{}_option".format(self.node_name)
        create_hierarchy()
        create_fk_chain()

        if self.enable_between_driven:
            set_driven_between()
        else:
            create_center_vector()
            create_collide_vector()
            create_angle_between()
            set_driven_node()

class Torso_Ribbon(rig_class.Rig):
    """TorsoRibbon

Create a torso part (using ribbon)

Variables:
name(string) : Name of part
axis_forward(string) : Name of Joint Pelvis
list_joint_spine(stringArray) : list of spine joints
list_fk_control_pivot(stringArray) : list of fk spine controller, first one will be pelvis , the after one will be spine chain , the last one will be chest control (Reference Position ,Orientation)

ribbon_fk_weight(path) : Xml Path
ribbon_ik_weight(path) : Xml Path
ribbon_output_weight(path) : Xml Path

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
    """

    def __init__(self):
        super().__init__()
        # @ Required
        self.name = "torso"

        # $ Axis
        self.axis_direction = utils.get_triple_axis_enum()

        # $ Global Joints
        self.list_joint_spine = []
        self.list_scalable_volume_joint = []

        # $ Guide Pivot
        self.list_fk_control_pivot = []
        self.locator_ik_chest_position = ""
        # # quick_create_guide

        # $ Cog
        self.cog_pivot = ""
        self.use_root_joint_as_pivot = True

        # $ Chest Scale
        self.enable_breath_scale = False
        self.jnt_breath_scale = ""
        # * enable_breath_scale
        # -
        self.enable_auto_volume_as_default = True

        # $ Breast
        self.enable_breast_rig = False
        self.L_list_jnt_breast = []
        self.R_list_jnt_breast = []
        # * enable_breast_rig

        # @ Optional
        # $ Auto Import Skin Weight
        self.ribbon_fk_weight = ""
        self.ribbon_ik_weight = ""
        self.ribbon_output_weight = ""

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
            cmds.group(em=1, n=grp_ribbon, p=self.grp_local_still)
            cmds.group(em=1, n=grp_ik_controls, p=self.grp_local_still)
            cmds.group(em=1, n=grp_fk_controls, p=self.grp_local_anim)

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
            for ribbon in [rbn_ik,rbn_fk, rbn_output, rbn_base]:
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
                                 surface=rbn_output,
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
                if i == len(list_locator_bind)-1:
                    cmds.pointConstraint(list_locator_bind[i],self.list_joint_spine[i])
                    cmds.orientConstraint(list_locator_bind[i],self.list_joint_spine[i])
                    continue

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
            tmp_mid_match_orient = cmds.spaceLocator()[0]
            utils.matchTransform(tmp_mid_match_orient,self.list_joint_spine[0],rot=True)
            utils.snap_to_nearest_90(tmp_mid_match_orient)

            for i in range(3):
                if i == 0:
                    name = "pelvis"
                    ribbon_pin = rbn_fk
                    match_orient = self.list_joint_spine[0]
                elif i == 1:
                    name = "mid"
                    ribbon_pin = rbn_ik
                    match_orient = tmp_mid_match_orient
                elif i == 2:
                    name = "chest"
                    ribbon_pin = rbn_fk
                    match_orient = self.list_joint_spine[-1]
                else:
                    raise Exception("Error")

                ctrl_ik = "{}_ik{}_{}".format(self.name, name, ctrl)
                jnt_ik = "{}_ik{}_{}".format(self.name, name, jnt)
                grp_pin = "{}_IkPin{}_{}".format(self.name, name, grp)

                # create grp pin
                cmds.group(em=1, n=grp_pin, p=grp_ik_controls)

                # create follicle
                flc_name = "{}_IkFlc{}_{}".format(self.name, i + 1, grp)
                utils.snap_to_surface(source=ribbon_pin,
                                      object=grp_pin,
                                      u=i * 0.5,
                                      v=0.5,
                                      percentage=True)
                utils.pin_ribbon(list_pin=[grp_pin],
                                 surface=ribbon_pin,
                                 output_parent=grp_ik_controls,
                                 name=flc_name)

                utils.matchTransform(grp_pin, match_orient, rot=1)
                cmds.parent(grp_pin, flc_name)

                # create controller and parent
                utils.create_control(name=ctrl_ik,
                                     match=grp_pin,
                                     parent=grp_pin,
                                     size=1.8)

                # create joint
                cmds.select(cl=1)
                cmds.joint(n=jnt_ik)
                cmds.select(cl=1)
                utils.match_parent(jnt_ik, grp_pin)
                cmds.makeIdentity(jnt_ik, a=1, r=1)

                # change position for chest
                if i == 2:
                    grp_pivot = cmds.group(em=1, n="{}_ChestPivot_{}".format(self.name, grp), p=cmds.listRelatives(ctrl_ik, p=1)[0])
                    cmds.matchTransform(grp_pivot, self.locator_ik_chest_position)
                    utils.freeze_group_classic(grp_pivot, "grpOff")

                    cmds.parent(jnt_ik, grp_pivot)

                    cmds.matchTransform(ctrl_ik, self.locator_ik_chest_position)
                    utils.freeze_group_classic(ctrl_ik, "grpCtrl")

                    cmds.connectAttr("{}.t".format(ctrl_ik), "{}.t".format(grp_pivot))
                    cmds.connectAttr("{}.r".format(ctrl_ik), "{}.r".format(grp_pivot))

                else:
                    # directly connect ik control to ik joint
                    cmds.connectAttr("{}.t".format(ctrl_ik), "{}.t".format(jnt_ik))
                    cmds.connectAttr("{}.r".format(ctrl_ik), "{}.r".format(jnt_ik))

                # finalize
                list_ik_joints.append(jnt_ik)
                list_ik_controls.append(ctrl_ik)
                list_flc_ik.append(flc_name)

            # bind skin to ik ribbon
            node_skin_ik = cmds.skinCluster(list_ik_joints[0], list_ik_joints[2], rbn_ik, n="{}_ik_skinCluster".format(self.name), mi=2, ih=1, tsb=1, dr=3, bm=3)
            utils.import_weight(node_skin_ik, self.ribbon_ik_weight) if  self.ribbon_ik_weight else None

            # bind skin to output ribbon
            node_skin_output = cmds.skinCluster(list_ik_joints, rbn_output, n="{}_output_skinCluster".format(self.name), mi=3, ih=1, tsb=1, dr=10, bm=3)
            utils.import_weight(node_skin_output, self.ribbon_output_weight) if  self.ribbon_output_weight else None

            # delete temp
            cmds.delete(tmp_mid_match_orient)
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

                cmds.connectAttr("{}.worldSpace[0]".format(rbn_output), "{}.nurbsGeometry".format(node_output_length))
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

        grp_ribbon = "{}_{}Nurbs".format(grp, self.name)
        ctrl_cog = "{}_cog".format(ctrl)

        rbn_output = "{}_output_{}".format(self.name, nrb)
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

        apply_bind_joint_constraint()

        create_auto_scale_spine()
        fix_scale()

        create_breast_rig()

        make_finalize()


class FkChain(rig_class.Rig):
    """
    Create an fk chain

    Variables:

    list_joint_chain(stringArray) : List of Chain Fk
    create_local_orient(enum) : Create Local Orient

    """
    def __init__(self):
        super().__init__()

        # @ Required
        self.name="Fk"
        self.list_joint_chain = []
        # -
        self.create_local_orient = ["Root Control","All Control","Disable"]
        # -
        self.parent = ""
        self.mirror_control_scale = False

    def core_build(self):
        def create_fk_control():
            def create_blend_orient():
                attr_blend_orient = control+".worldOrient"
                cmds.addAttr(control,ln="worldOrient",at="float",min=0,max=1,k=1)

                grp_frz = cmds.listRelatives(control, p=1)[0]
                grp_frz_space = utils.freeze_group_classic(control,"grpSpace")[0]

                utils.create_float_space(list_space=[ctrl_fly,grp_frz],target=grp_frz_space,attr_float=attr_blend_orient)

            parent = None

            for i,control in enumerate(list_fk_control):
                joint = self.list_joint_chain[i]

                if parent:
                    parent_target = parent
                else:
                    parent_target = self.grp_local_anim

                utils.create_control(control,match=joint,constraint="parent",parent=parent_target,freeze_group=True,mirror_freeze_group=self.mirror_control_scale)

                # create only root case
                if self.create_local_orient == 0 and i == 0:
                    create_blend_orient()
                elif self.create_local_orient == 1:
                    create_blend_orient()
                elif self.create_local_orient == 2:
                    pass

                parent = control

        def make_finalize():
            if self.debug_mode:
                return

            [utils.lock_attributes(control, v=1, s=1, k=0, l=1) for control in list_fk_control]

            utils.add_to_set(list_fk_control)

        list_fk_control = [utils.cname(self.name,joint,ctrl) for joint in  self.list_joint_chain]

        create_fk_control()
        make_finalize()