from tmlib.core import Scene, Transform, Utility, BlendShape, Create

import maya.cmds as cmds
import maya.api.OpenMaya as om

import math


def create_switch_enum(
    object_driven,
    list_target,
    object_attribute=None,
    list_target_name=None,
    type="parent",
):
    def key_target(index):
        cmds.setAttr(attr_path, index)
        for i, weight_name in enumerate(list_weight):
            weight_name = constraint_name[0]+"."+weight_name
            print("wieght name : ",weight_name)
            if i == index:
                cmds.setAttr(weight_name, 1)
            else:
                cmds.setAttr(weight_name, 0)
            cmds.setDrivenKeyframe(weight_name, cd=attr_path)

    def create_space_locator():
        for i, obj in enumerate(list_target):
            grp_space_local = cmds.group(
                em=1,
                n="{}_{}Space_grp".format(list_target_name[i], object_driven),
                p=grp_space_still,
            )
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(obj),
                "{}.offsetParentMatrix".format(grp_space_local),
            )
            grp_space_offset = cmds.group(
                em=1,
                n="{}_{}SpaceOff_grp".format(list_target_name[i], object_driven),
                p=grp_space_local,
            )
            loc_space = cmds.group(
                n="{}_{}Space_loc".format(list_target_name[i], object_driven),
                em=1,
                p=grp_space_offset,
            )
            constraint = cmds.parentConstraint(object_driven, grp_space_offset)
            cmds.delete(constraint)
            list_space_locator.append(loc_space)

    def create_constraint_node():
        grp_offset_target = Create.create_freeze_group([object_driven])
        maintain_offset = 0

        if type == "parent":
            constraint_name = cmds.parentConstraint(
                list_space_locator, grp_offset_target, mo=maintain_offset
            )
            list_weight = cmds.parentConstraint(constraint_name, q=1, wal=1)
        elif type == "point":
            constraint_name = cmds.pointConstraint(
                list_space_locator, grp_offset_target, mo=maintain_offset
            )
            list_weight = cmds.pointConstraint(constraint_name, q=1, wal=1)
        elif type == "orient":
            constraint_name = cmds.orientConstraint(
                list_space_locator, grp_offset_target, mo=maintain_offset
            )
            list_weight = cmds.orientConstraint(constraint_name, q=1, wal=1)
        else:
            raise Exception("Input Constraint Type is Invalid")

        return constraint_name, list_weight

    if len(list_target_name) != len(list_target):
        raise Exception("Invalid Input Space and Nice Name")

    if not list_target_name:
        list_target_name = list_target

    grp_space_still = cmds.group(em=1, n="{}_spaceStill_grp".format(object_driven))
    cmds.setAttr("{}.inheritsTransform".format(grp_space_still), 0)

    if not object_attribute:
        object_attribute = object_driven

    cmds.addAttr(
        object_attribute, ln="space", at="enum", en=":".join(list_target_name), k=1
    )

    list_space_locator = []
    attr_path = "{}.space".format(object_attribute)
    print("attr path : ",attr_path)
    cmds.setAttr(attr_path, 0)

    create_space_locator()

    constraint_name, list_weight = create_constraint_node()

    for i in range(len(list_target)):
        key_target(i)

    cmds.setAttr(attr_path, 0)
    cmds.parent(grp_space_still, object_driven)
    return grp_space_still


def create_switch_enum_matrix(
    list_space, list_nice_name, target, object_attr, at="enum", pick=None
):
    """Create enum switch matrix"""

    if len(list_space) != 2 and at == "float":
        raise Exception("list space must have two member : get {}".format(list_space))

    list_output_group = []
    list_locator = []
    grp_blend = Create.create_freeze_group([target], "grpBlend")[0]

    if at == "enum":
        cmds.addAttr(
            object_attr, ln="space", at="enum", en=":".join(list_nice_name), k=1
        )

    attr_switch = object_attr + ".space"

    for item in list_space:
        locator = cmds.spaceLocator(
            n="{}space{}_loc".format(target, item.capitalize())
        )[0]
        grp_offset = cmds.group(
            locator, n="{}_{}space_grp".format(target, item.capitalize())
        )

        cmds.setAttr("{}.inheritsTransform".format(grp_offset), 0)
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(item), "{}.offsetParentMatrix".format(grp_offset)
        )

        cmds.matchTransform(locator, target)

        Utility.lock_attribute(grp_offset, t=1, r=1, s=1, l=1, k=0)
        list_output_group.append(grp_offset)
        list_locator.append(locator)

    if pick:
        node_pick_matrix = cmds.createNode(
            "pickMatrix", n="pmx_{}SpaceSwitch".format(target)
        )
        cmds.setAttr(node_pick_matrix + ".useTranslate", 0)
        cmds.setAttr(node_pick_matrix + ".useRotate", 0)
        cmds.setAttr(node_pick_matrix + ".useScale", 0)
        cmds.setAttr(node_pick_matrix + ".useShear", 0)

        for option in pick:
            if option == "translate":
                cmds.setAttr(node_pick_matrix + ".useTranslate", 1)
            elif option == "rotate":
                cmds.setAttr(node_pick_matrix + ".useRotate", 1)
            elif option == "scale":
                cmds.setAttr(node_pick_matrix + ".useScale", 1)
            elif option == "shear":
                cmds.setAttr(node_pick_matrix + ".useShear", 1)

    node_mult_matrix = cmds.createNode("multMatrix")

    list_parent = cmds.listRelatives(grp_blend, p=1)
    if list_parent:
        cmds.connectAttr(
            "{}.worldInverseMatrix[0]".format(list_parent[0]),
            "{}.matrixIn[1]".format(node_mult_matrix),
        )

    if at == "enum":
        node_choice = cmds.createNode("choice")
        cmds.connectAttr(attr_switch, "{}.selector".format(node_choice))
        [
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(list_locator[i]),
                "{}.input[{}]".format(node_choice, i),
            )
            for i in range(len(list_space))
        ]
        cmds.connectAttr(
            "{}.output".format(node_choice), "{}.matrixIn[0]".format(node_mult_matrix)
        )
    elif at == "float":
        node_blend_matrix = cmds.createNode("blendMatrix")
        cmds.connectAttr(attr_switch, "{}.envelope".format(node_blend_matrix))
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(list_locator[1]),
            "{}.target[0].targetMatrix".format(node_blend_matrix),
        )
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(list_locator[0]),
            "{}.inputMatrix".format(node_blend_matrix),
        )
        cmds.connectAttr(
            "{}.outputMatrix".format(node_blend_matrix),
            "{}.matrixIn[0]".format(node_mult_matrix),
        )

    if pick:
        cmds.connectAttr(
            "{}.matrixSum".format(node_mult_matrix),
            "{}.inputMatrix".format(node_pick_matrix),
        )
        cmds.connectAttr(
            "{}.outputMatrix".format(node_pick_matrix),
            "{}.offsetParentMatrix".format(grp_blend),
        )
    else:
        cmds.connectAttr(
            "{}.matrixSum".format(node_mult_matrix),
            "{}.offsetParentMatrix".format(grp_blend),
        )

    return list_output_group


def create_switch_float(
    target1, target2, object, controller, attr_name="space", typ="orient"
):
    node_rev = cmds.createNode("reverse", n="node_rev")

    locatorFrz1 = cmds.spaceLocator(n="loc_{}SpaceFrz".format(object))
    locatorFrz2 = cmds.spaceLocator(n="loc_{}SpaceFrz".format(object))

    locator1 = cmds.spaceLocator(n="loc_{}Space".format(object))
    locator2 = cmds.spaceLocator(n="loc_{}Space".format(object))

    cmds.setAttr(locatorFrz1 + ".inheritsTransform", 0)
    cmds.setAttr(locatorFrz2 + ".inheritsTransform", 0)

    cmds.setAttr(locatorFrz1 + ".v", 0)
    cmds.setAttr(locatorFrz2 + ".v", 0)

    cmds.connectAttr(
        "{}.worldMatrix[0]".format(target1), "{}.offsetParentMatrix".format(locatorFrz1)
    )
    cmds.connectAttr(
        "{}.worldMatrix[0]".format(target2), "{}.offsetParentMatrix".format(locatorFrz2)
    )

    cmds.parent(locator1, locatorFrz1)
    cmds.parent(locator2, locatorFrz2)

    cmds.matchTransform(locator1, object)
    cmds.matchTransform(locator2, object)

    grp_blend = Create.create_freeze_group([object], "grpBlend")[0]

    cmds.parent(locatorFrz1, locatorFrz2, grp_blend)

    if typ == "parent":
        cons = cmds.parentConstraint(locator1, locator2, grp_blend)
    elif typ == "orient":
        cons = cmds.orientConstraint(locator1, locator2, grp_blend)
    elif typ == "point":
        cons = cmds.pointConstraint(locator1, locator2, grp_blend)
    else:
        raise Exception("type invalid")

    cmds.setAttr("{}.interpType".format(cons), 2)

    cmds.addAttr(controller, ln=attr_name, k=1, min=0, max=1)
    cmds.connectAttr(
        "{}.{}".format(controller, attr_name), "{}.{}W0".format(cons, locator1)
    )
    cmds.connectAttr(
        "{}.{}".format(controller, attr_name), "{}.inputX".format(node_rev)
    )
    cmds.connectAttr("{}.outputX".format(node_rev), "{}.{}W1".format(cons, locator2))


def connect(
    object,
    target,
    typ="all",
    translate_multiplier=1,
    rotate_multiplier=1,
    name="connect",
):
    if not cmds.objExists(object):
        raise RuntimeError("Object does not exist: {}".format(object))
    if not cmds.objExists(target):
        raise RuntimeError("Object does not exist: {}".format(target))

    object = str(object)
    target = str(target)

    def connect_translate():
        if translate_multiplier != 1:
            connect_conversion_vector(
                list_input1=[object + ".tx", object + ".ty", object + ".tz"],
                list_conversion=[
                    translate_multiplier,
                    translate_multiplier,
                    translate_multiplier,
                ],
                list_output=[target + ".tx", target + ".ty", target + ".tz"],
                name=name,
            )
        else:
            cmds.connectAttr(object + ".t", target + ".t")

    def connect_rotate():
        if rotate_multiplier != 1:
            connect_conversion_vector(
                list_input1=[object + ".rx", object + ".ry", object + ".rz"],
                list_conversion=[
                    rotate_multiplier,
                    rotate_multiplier,
                    rotate_multiplier,
                ],
                list_output=[target + ".rx", target + ".ry", target + ".rz"],
                name=name,
            )
        else:
            cmds.connectAttr(object + ".r", target + ".r")

    if typ == "translate":
        connect_translate()
    elif typ == "rotate":
        connect_rotate()
    elif typ == "scale":
        cmds.connectAttr(object + ".s", target + ".s", f=1)
    elif typ == "all":
        connect_translate()
        connect_rotate()
        cmds.connectAttr(object + ".s", target + ".s")


def connect_conversion(
    input1,
    input2=None,
    output=None,
    conversion=-1,
    name="multDoubleLinear",
    clamp=False,
):
    node = cmds.createNode("multDoubleLinear", n="{}_mdl".format(name))
    cmds.connectAttr(input1, node + ".input1", f=True)

    if input2:
        cmds.connectAttr(input2, node + ".input2", f=True)
    else:
        cmds.setAttr(node + ".input2", conversion)

    if clamp:
        result_attr = clamp_connection(str(node + ".output"), max_value=clamp)
    else:
        result_attr = node + ".output"

    if output:
        cmds.connectAttr(result_attr, output, f=True)

    return result_attr


def clamp_connection(input_attr, min_value=0, max_value=1):
    if not cmds.objExists(input_attr):
        raise RuntimeError("Attribute does not exist: {}".format(input_attr))

    node = input_attr.split(".")[0]

    clamp = cmds.createNode("clamp", name="{}_clamp".format(node))

    cmds.connectAttr(input_attr, clamp + ".inputR", force=True)

    cmds.setAttr(clamp + ".minR", min_value)
    cmds.setAttr(clamp + ".maxR", max_value)

    return clamp + ".outputR"


def connect_conversion_vector(
    list_input1=[],
    list_input2=None,
    list_output=None,
    list_conversion=[1, 1, 1],
    name="conversion",
):
    node = cmds.createNode("multiplyDivide", n="{}_conversion_md".format(name))

    list_input_1_name = [".input1X", ".input1Y", ".input1Z"]
    list_output_name = [".outputX", ".outputY", ".outputZ"]

    for i, input in enumerate(list_input1):
        cmds.connectAttr(input, node + list_input_1_name[i])

    if list_input2:
        cmds.connectAttr(list_input2[0], node + ".input2X")
        cmds.connectAttr(list_input2[1], node + ".input2X")
        cmds.connectAttr(list_input2[2], node + ".input2X")
    else:
        cmds.setAttr(node + ".input2X", list_conversion[0])
        cmds.setAttr(node + ".input2Y", list_conversion[1])
        cmds.setAttr(node + ".input2Z", list_conversion[2])

    for i, output_attribute in enumerate(list_output):
        cmds.connectAttr(node + list_output_name[i], output_attribute)


def connect_conversion_unit(
    input, output=None, factor=1, name="unitConversion", use_factor_attr=False
):
    node = cmds.createNode("unitConversion", n=name)
    cmds.connectAttr(input, node + ".input")

    if output:
        cmds.connectAttr(node + ".output", output)

    if use_factor_attr:
        cmds.connectAttr(factor, "{}.conversionFactor".format(node))
    else:
        print("setting node {} {}".format(node, factor))
        cmds.setAttr(node + ".conversionFactor", factor)

    return node


def connect_bind_pre_matrix(
    list_joint, skin_cluster, list_transform=None, attribute="parentInverseMatrix"
):
    """Connect world inverse matrix of given list transform to skin cluster pre bind matrix"""

    if not list_transform:
        list_transform = list_joint

    skin_cluster = str(skin_cluster)

    for transform, joint in zip(list_transform, list_joint):
        transform = str(transform)
        joint = str(joint)

        list_connection_world_matrix = cmds.listConnections(
            "{}.worldMatrix[0]".format(joint), p=1
        )

        index = None

        for attr in list_connection_world_matrix:
            # attr is a plain string like "skinCluster1.matrix[2]"
            if skin_cluster in attr:
                # extract the index from the bracket
                bracket_part = attr.split("[")[-1].rstrip("]")
                index = int(bracket_part)
                break

        if index is None:
            print("not found index for {} , {}".format(transform, joint))
            continue

        cmds.connectAttr(
            "{}.{}".format(transform, attribute),
            "{}.bindPreMatrix[{}]".format(skin_cluster, index),
            f=True,
        )


def connect_switch_joint(
    attr_switch,
    fk_joints,
    ik_joints,
    bind_joints,
    grp_fk=None,
    grp_ik=None,
    max_value=10,
    method="parent",
):
    attr_switch = connect_conversion_unit(attr_switch, factor=1 / max_value) + ".output"

    node_rev = cmds.createNode("reverse", n="switch_reverse")
    cmds.connectAttr(attr_switch, "{}.inputX".format(node_rev))

    for joint_bind, joint_fk, joint_ik in zip(bind_joints, fk_joints, ik_joints):
        joint_bind = str(joint_bind)
        joint_fk = str(joint_fk)
        joint_ik = str(joint_ik)

        if method == "parent":
            constraint = cmds.parentConstraint(joint_fk, joint_ik, joint_bind)
            cmds.connectAttr(node_rev + ".outputX", "{}.w0".format(constraint))
            cmds.connectAttr(node_rev + ".inputX", "{}.w1".format(constraint))
        elif method == "orient":
            constraint = cmds.orientConstraint(joint_fk, joint_ik, joint_bind)
            cmds.connectAttr(node_rev + ".outputX", "{}.w0".format(constraint))
            cmds.connectAttr(node_rev + ".inputX", "{}.w1".format(constraint))
        elif method == "blendColors":
            node_blend_color = cmds.createNode("blendColors", n="rotate_blend")
            cmds.connectAttr(joint_ik + ".rotate", node_blend_color + ".color2")
            cmds.connectAttr(joint_fk + ".rotate", node_blend_color + ".color1")
            cmds.connectAttr(node_rev + ".outputX", node_blend_color + ".blender")
            cmds.connectAttr(node_blend_color + ".output", joint_bind + ".rotate")

    if grp_ik:
        grp_ik = str(grp_ik)
        cmds.connectAttr(node_rev + ".inputX", grp_ik + ".visibility")

    if grp_fk:
        grp_fk = str(grp_fk)
        cmds.connectAttr(node_rev + ".outputX", grp_fk + ".visibility")


def constraint_matrix(list_constraint, method="point", mo=False):
    """
    Method : (point,orient,scale,parent)

    This Function create matrix connection like constraint.

    """

    source = str(list_constraint[0])
    target = str(list_constraint[1])

    # create node
    node_decomp = cmds.createNode("decomposeMatrix")
    node_pick_matrix = cmds.createNode("pickMatrix")

    cmds.connectAttr(
        "{}.worldMatrix[0]".format(source),
        "{}.inputMatrix".format(node_pick_matrix),
    )

    if method == "point":
        cmds.setAttr(node_pick_matrix + ".useTranslate", True)
        cmds.setAttr(node_pick_matrix + ".useRotate", False)
        cmds.setAttr(node_pick_matrix + ".useScale", False)
        cmds.setAttr(node_pick_matrix + ".useShear", False)

    if mo:
        node_mult_matrix_offset = cmds.createNode("multMatrix", n="offset_mm")

        source_matrix = om.MMatrix(
            cmds.getAttr("{}.outputMatrix".format(node_pick_matrix))
        )
        target_matrix = om.MMatrix(cmds.xform(target, q=1, ws=1, m=1))

        matrix_offset = target_matrix * source_matrix.inverse()

        cmds.setAttr("{}.matrixIn[0]".format(node_mult_matrix_offset), matrix_offset)
        cmds.connectAttr(
            "{}.outputMatrix".format(node_pick_matrix),
            "{}.matrixIn[1]".format(node_mult_matrix_offset),
        )

        attr_maintain_offset = "{}.matrixSum".format(node_mult_matrix_offset)
    else:
        attr_maintain_offset = "{}.outputMatrix".format(node_pick_matrix)

    node_mult_matrix_inverse = cmds.createNode("multMatrix", n="inverse_parent_mm")

    cmds.connectAttr(
        attr_maintain_offset, "{}.matrixIn[0]".format(node_mult_matrix_inverse)
    )
    cmds.connectAttr(
        "{}.parentInverseMatrix[0]".format(target),
        "{}.matrixIn[1]".format(node_mult_matrix_inverse),
    )

    if cmds.objectType(target, isa="joint"):
        joint_orient = cmds.getAttr("{}.jointOrient".format(target))[0]

        if list(joint_orient) == [0.0, 0.0, 0.0]:
            cmds.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_inverse),
                "{}.inputMatrix".format(node_decomp),
            )

            node_decomp_t = node_decomp
            node_decomp_r = node_decomp

        else:
            cmds.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_inverse),
                "{}.inputMatrix".format(node_decomp),
            )

            node_decomp_rot = cmds.createNode("decomposeMatrix")

            euler = om.MEulerRotation(
                math.radians(joint_orient[0]),
                math.radians(joint_orient[1]),
                math.radians(joint_orient[2]),
                om.MEulerRotation.kXYZ,
            )

            m_offset = euler.asMatrix()
            m_offset = m_offset.inverse()

            node_offset_joint_orient = cmds.createNode("multMatrix")

            m_current = om.MMatrix(
                cmds.getAttr("{}.matrixSum".format(node_mult_matrix_inverse))
            )

            cmds.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_inverse),
                "{}.matrixIn[0]".format(node_offset_joint_orient),
            )
            cmds.setAttr(
                "{}.matrixIn[1]".format(node_offset_joint_orient), m_offset, typ="matrix"
            )

            cmds.connectAttr(
                "{}.matrixSum".format(node_offset_joint_orient),
                "{}.inputMatrix".format(node_decomp_rot),
            )

            node_decomp_t = node_decomp
            node_decomp_r = node_decomp_rot

    else:
        cmds.connectAttr(
            "{}.matrixSum".format(node_mult_matrix_inverse),
            "{}.inputMatrix".format(node_decomp),
        )

        node_decomp_t = node_decomp
        node_decomp_r = node_decomp

    if method == "point":
        cmds.connectAttr(
            "{}.outputTranslate".format(node_decomp),
            "{}.translate".format(target),
            f=1,
        )
    elif method == "orient":
        cmds.connectAttr(
            "{}.outputRotate".format(node_decomp), "{}.rotate".format(target), f=1
        )
    elif method == "parent":
        cmds.connectAttr(
            "{}.outputTranslate".format(node_decomp_t),
            "{}.translate".format(target),
            f=1,
        )
        cmds.connectAttr(
            "{}.outputRotate".format(node_decomp_r),
            "{}.rotate".format(target),
            f=1,
        )
    elif method == "scale":
        cmds.connectAttr(
            "{}.outputScale".format(node_decomp), "{}.scale".format(target), f=1
        )

    return


def decomp_constraint(parent, object, r=True, t=True):
    node_decomp = cmds.createNode("decomposeMatrix", n="decomp")

    cmds.connectAttr(parent + ".worldMatrix[0]", node_decomp + ".inputMatrix")

    if r:
        cmds.connectAttr(node_decomp + ".outputRotate", object + ".r")
    if t:
        cmds.connectAttr(node_decomp + ".outputTranslate", object + ".t")


def set_driver_node_fixed(
    attr_driver,
    attr_driven,
    driven_value,
    name,
    clamp_length=[None, None],
    driven_value_is_fixed=False,
):
    node_mdl_mult = cmds.createNode("multDoubleLinear", n="{}_mult_mdl".format(name))

    if driven_value_is_fixed:
        cmds.setAttr("{}.input2".format(node_mdl_mult), driven_value)
    else:
        cmds.connectAttr(driven_value, "{}.input2".format(node_mdl_mult))

    cmds.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

    if clamp_length is [None, None]:
        cmds.connectAttr("{}.output".format(node_mdl_mult), attr_driven)

    elif clamp_length[0] and clamp_length[1]:
        node_clamp = cmds.createNode("clamp", n="{}_clamp_cmp".format(name))
        cmds.setAttr("{}.minR".format(node_clamp), clamp_length[0])
        cmds.setAttr("{}.maxR".format(node_clamp), clamp_length[1])

        cmds.connectAttr(
            "{}.output".format(node_mdl_mult), "{}.inputR".format(node_clamp)
        )
        cmds.connectAttr("{}.outputR".format(node_clamp), attr_driven)

    else:
        if clamp_length[0] is not None:
            operation = 2
            value = clamp_length[0]
        elif clamp_length[1] is not None:
            operation = 4
            value = clamp_length[1]
        else:
            raise Exception("Error Calculate")

        node_cond = cmds.createNode("condition", n="{}_clamp_cond".format(name))

        cmds.connectAttr(
            "{}.output".format(node_mdl_mult), "{}.colorIfTrueR".format(node_cond)
        )
        cmds.connectAttr(
            "{}.output".format(node_mdl_mult), "{}.firstTerm".format(node_cond)
        )
        cmds.setAttr("{}.secondTerm".format(node_cond), value)

        cmds.setAttr("{}.colorIfFalseR".format(node_cond), value)

        cmds.setAttr("{}.operation".format(node_cond), operation)

        cmds.connectAttr("{}.outColorR".format(node_cond), attr_driven)

    return node_mdl_mult


def set_driver_node_multi_input(list_attr_driver, attr_driven, list_attr_factor, name):
    if len(list_attr_driver) != len(list_attr_factor):
        raise Exception("Invalid Input")

    amount_driver = len(list_attr_driver)

    list_mdl_mult = []
    for i in range(amount_driver):
        attr_driver = list_attr_driver[i]
        attr_factor = list_attr_factor[i]

        node_mdl_mult = cmds.createNode(
            "multDoubleLinear", n="{}_mult{}_mdl".format(name, i)
        )
        cmds.connectAttr(attr_factor, "{}.input2".format(node_mdl_mult))
        cmds.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

        list_mdl_mult.append(node_mdl_mult + ".output")

    node_pma_sum = cmds.createNode("plusMinusAverage", n="{}_sum_pma".format(name))

    for i in range(amount_driver):
        attr_mdl = list_mdl_mult[i]

        cmds.connectAttr(attr_mdl, "{}.input1D[{}]".format(node_pma_sum, i))

    cmds.connectAttr("{}.output1D".format(node_pma_sum), attr_driven)

    return node_pma_sum


def set_driver_node_realtime(
    attr_driver, attr_driven, attr_driver_key, attr_driven_key, name=""
):
    node_md_divide = cmds.createNode("multiplyDivide", n="{}divide_md".format(name))
    node_mdl_mult = cmds.createNode("multDoubleLinear", n="{}mult_mdl".format(name))

    cmds.setAttr("{}.operation".format(node_md_divide), 2)

    cmds.connectAttr(attr_driven_key, "{}.input1X".format(node_md_divide))
    cmds.connectAttr(attr_driver_key, "{}.input2X".format(node_md_divide))

    cmds.connectAttr(
        "{}.outputX".format(node_md_divide), "{}.input2".format(node_mdl_mult)
    )
    cmds.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

    cmds.connectAttr("{}.output".format(node_mdl_mult), attr_driven)


def set_blend_shape_expression(
    node_name,
    mesh_target,
    mesh_base,
    driver_value,
    driver_attr,
    clamp_length=[0, 1],
    module_name="SetDriven",
):
    BlendShape.add_or_create_blend_shape_node(
        list_target_mesh=[mesh_target], node_name=node_name
    )

    set_driver_node_fixed(
        attr_driver=driver_attr,
        attr_driven=node_name + "." + mesh_target,
        driven_value=1 / driver_value,
        name=module_name,
        clamp_length=clamp_length,
        driven_value_is_fixed=True,
    )


def set_driver_blendshape_single_avg(
    list_input_attr=None,
    list_driver_value=None,
    output_attr=None,
    clamp=False,
    name_tag="setBlendShape",
):
    def get_input_factor(input_attr, driver_value):
        factor = 1 / driver_value

        node_mdl = cmds.createNode("multDoubleLinear", n="{}_mdl".format(name_tag))
        cmds.connectAttr(input_attr, "{}.input2".format(node_mdl))
        cmds.setAttr("{}.input1".format(node_mdl), factor)

        return node_mdl + ".output"

    attr_input1 = get_input_factor(list_input_attr[0], list_driver_value[0])
    attr_input2 = get_input_factor(list_input_attr[1], list_driver_value[1])

    node_clamp = cmds.createNode("clamp")
    cmds.setAttr(node_clamp + ".min", 0, 0, 0, typ="double3")
    cmds.setAttr(node_clamp + ".max", 1, 1, 1, typ="double3")

    cmds.connectAttr(attr_input1, node_clamp + ".inputR")
    cmds.connectAttr(attr_input2, node_clamp + ".inputG")

    node_adl_sum = cmds.createNode("addDoubleLinear", n="{}_adl".format(name_tag))

    cmds.connectAttr(node_clamp + ".outputR", node_adl_sum + ".input1")
    cmds.connectAttr(node_clamp + ".outputG", node_adl_sum + ".input2")

    node_mdl_avg = cmds.createNode("multDoubleLinear", n="{}_avg_mdl".format(name_tag))

    cmds.connectAttr(node_adl_sum + ".output", node_mdl_avg + ".input1")
    cmds.setAttr(node_mdl_avg + ".input2", 0.5)
    cmds.connectAttr(node_mdl_avg + ".output", output_attr)


def set_driver_blend_shape_single(
    input_attr=None,
    driver_value=3,
    output_attr=None,
    clamp=False,
    name_tag="setDriverBlendShape",
    driven_value=1,
):
    factor = driven_value / driver_value

    node_mdl = cmds.createNode(
        "multDoubleLinear", n="{}_set_blend_shape_mdl".format(name_tag)
    )
    cmds.connectAttr(input_attr, "{}.input2".format(node_mdl))
    cmds.setAttr("{}.input1".format(node_mdl), factor)

    if clamp:
        node_clamp = cmds.createNode(
            "clamp", n="{}_set_blend_shape_cmp".format(name_tag)
        )
        cmds.connectAttr(node_mdl + ".output", node_clamp + ".inputR")
        cmds.setAttr(node_clamp + ".minR", 0)
        cmds.setAttr(node_clamp + ".maxR", 1)
        cmds.connectAttr(node_clamp + ".outputR", output_attr)
    else:
        cmds.connectAttr(node_mdl + ".output", output_attr)


def set_diagonal_driver(
    transform_name, axis_up="y", axis_out="x", name_tag="setDriver"
):
    def get_output_between(attr_A, attr_B):
        node_mdl = cmds.createNode("multDoubleLinear", n="{}_avg_md".format(name_tag))
        cmds.connectAttr(attr_A, node_mdl + ".input1")
        cmds.connectAttr(attr_B, node_mdl + ".input2")
        return node_mdl + ".output"

    def get_normalize_output(attr_A, attr_B, attr_target):
        node_adl_normalized = cmds.createNode(
            "addDoubleLinear", n="{}_normalize_weight_adl".format(name_tag)
        )
        cmds.connectAttr(attr_A, node_adl_normalized + ".input1")
        cmds.connectAttr(attr_B, node_adl_normalized + ".input2")

        node_pma_subtract = cmds.createNode(
            "plusMinusAverage", n="{}_normalize_offset_pma".format(name_tag)
        )
        cmds.setAttr(node_pma_subtract + ".operation", 2)
        cmds.connectAttr(attr_target, node_pma_subtract + ".input1D[0]")
        cmds.connectAttr(
            node_adl_normalized + ".output", node_pma_subtract + ".input1D[1]"
        )

        return node_pma_subtract + ".output1D"

    list_axis_up_out = [axis_up, axis_out]
    node_output = cmds.createNode("transform", n=name_tag)

    cmds.addAttr(node_output, ln="Up", k=1)
    cmds.addAttr(node_output, ln="Down", k=1)
    cmds.addAttr(node_output, ln="In", k=1)
    cmds.addAttr(node_output, ln="Out", k=1)
    cmds.addAttr(node_output, ln="UpOut", k=1)
    cmds.addAttr(node_output, ln="UpIn", k=1)
    cmds.addAttr(node_output, ln="DownOut", k=1)
    cmds.addAttr(node_output, ln="DownIn", k=1)

    node_sr_range_positive = cmds.createNode(
        "setRange", n="{}_posClamp_sr".format(name_tag)
    )

    for axis in list_axis_up_out:
        cmds.connectAttr(
            "{}.t{}".format(transform_name, axis),
            "{}.value{}".format(node_sr_range_positive, axis.upper()),
        )

        cmds.setAttr("{}.oldMin{}".format(node_sr_range_positive, axis.upper()), 0)
        cmds.setAttr("{}.oldMax{}".format(node_sr_range_positive, axis.upper()), 1)

        cmds.setAttr("{}.min{}".format(node_sr_range_positive, axis.upper()), 0)
        cmds.setAttr("{}.max{}".format(node_sr_range_positive, axis.upper()), 1)

    node_sr_range_negative = cmds.createNode(
        "setRange", n="{}_negClamp_sr".format(name_tag)
    )
    node_md_negative_invert = cmds.createNode(
        "multiplyDivide", n="{}_invertClamp_md".format(name_tag)
    )

    cmds.setAttr(node_md_negative_invert + ".input2", -1, -1, -1, typ="double3")

    for axis in list_axis_up_out:
        cmds.connectAttr(
            "{}.t{}".format(transform_name, axis),
            "{}.value{}".format(node_sr_range_negative, axis.upper()),
        )

        cmds.setAttr("{}.oldMin{}".format(node_sr_range_negative, axis.upper()), -1)
        cmds.setAttr("{}.oldMax{}".format(node_sr_range_negative, axis.upper()), 0)

        cmds.setAttr("{}.min{}".format(node_sr_range_negative, axis.upper()), -1)
        cmds.setAttr("{}.max{}".format(node_sr_range_negative, axis.upper()), 0)

        cmds.connectAttr(
            "{}.outValue{}".format(node_sr_range_negative, axis.upper()),
            "{}.input1{}".format(node_md_negative_invert, axis.upper()),
        )

    attr_up = "{}.outValue{}".format(node_sr_range_positive, axis_up.upper())
    attr_out = "{}.outValue{}".format(node_sr_range_positive, axis_out.upper())
    attr_down = "{}.output{}".format(node_md_negative_invert, axis_up.upper())
    attr_in = "{}.output{}".format(node_md_negative_invert, axis_out.upper())

    attr_up_out = get_output_between(attr_up, attr_out)
    attr_up_in = get_output_between(attr_up, attr_in)
    attr_down_out = get_output_between(attr_down, attr_out)
    attr_down_in = get_output_between(attr_down, attr_in)

    attr_up_norm = get_normalize_output(attr_up_out, attr_up_in, attr_up)
    attr_out_norm = get_normalize_output(attr_up_out, attr_down_out, attr_out)
    attr_down_norm = get_normalize_output(attr_down_in, attr_down_out, attr_down)
    attr_in_norm = get_normalize_output(attr_up_in, attr_down_in, attr_in)

    cmds.connectAttr(attr_up_norm, "{}.Up".format(node_output))
    cmds.connectAttr(attr_down_norm, "{}.Down".format(node_output))
    cmds.connectAttr(attr_in_norm, "{}.In".format(node_output))
    cmds.connectAttr(attr_out_norm, "{}.Out".format(node_output))
    cmds.connectAttr(attr_up_out, "{}.UpOut".format(node_output))
    cmds.connectAttr(attr_up_in, "{}.UpIn".format(node_output))
    cmds.connectAttr(attr_down_out, "{}.DownOut".format(node_output))
    cmds.connectAttr(attr_down_in, "{}.DownIn".format(node_output))

    return node_output


def pin_to_mesh(
    list_pin=None, surface=None, prevent_double_transform=True, maintain_offset=False
):
    """Return list of pin value reference distance from input pin"""

    list_pin = [str(p) for p in (list_pin or [])]
    surface = str(surface) if surface else None

    if not surface:
        raise Exception("Surface Input not correct")

    if not cmds.objExists(surface):
        raise Exception("Not found surface in scene")

    if cmds.objectType(surface, isa="transform"):
        list_shape = cmds.listRelatives(surface, c=1, s=1, typ="mesh")

        if not list_shape:
            raise Exception("not found nurbs surface in input surface")
        else:
            mesh_shape = list_shape[0]
            mesh_transform = surface

    elif cmds.objectType(surface, isa="mesh"):
        mesh_transform = cmds.listRelatives(surface, p=1, typ="mesh")[0]
        mesh_shape = surface

    node_uv_pin = Create.create_uv_pin(mesh_transform)

    for i, obj in enumerate(list_pin):
        u, v = Transform.get_nearest_mesh_parameter(mesh_transform, obj)

        cmds.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)
        cmds.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), v)

        attr_matrix_output = "{}.outputMatrix[{}]".format(node_uv_pin, i)

        if maintain_offset:
            node_mm_offset = cmds.createNode("multMatrix", n="maintain_offset_mm")

            current_matrix = om.MMatrix(cmds.getAttr(attr_matrix_output))
            target_matrix = om.MMatrix(cmds.xform(obj, ws=1, m=1, q=1))
            offset_matrix = target_matrix * current_matrix.inverse()

            cmds.setAttr(
                "{}.matrixIn[0]".format(node_mm_offset), offset_matrix, typ="matrix"
            )
            cmds.connectAttr(
                attr_matrix_output, "{}.matrixIn[1]".format(node_mm_offset)
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm_offset)

        if prevent_double_transform:
            node_mm = cmds.createNode("multMatrix", n="prevent_double_transform_mm")

            cmds.connectAttr(
                attr_matrix_output,
                "{}.matrixIn[0]".format(node_mm),
            )
            cmds.connectAttr(
                "{}.parentInverseMatrix".format(obj),
                "{}.matrixIn[1]".format(node_mm),
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm)

        node_dcm = cmds.createNode("decomposeMatrix")

        cmds.connectAttr(attr_matrix_output, "{}.inputMatrix".format(node_dcm))
        cmds.connectAttr(
            "{}.outputTranslate".format(node_dcm), "{}.translate".format(obj), f=1
        )
        cmds.connectAttr(
            "{}.outputRotate".format(node_dcm), "{}.rotate".format(obj), f=1
        )

    return node_uv_pin


def pin_to_curve(
    list_pin=None,
    curve=None,
    prevent_double_transform=True,
    maintain_offset=False,
    only_position=True,
):
    """Return list of pin value reference distance from input pin"""

    surface_transform = curve

    node_uv_pin = Create.create_uv_pin(surface_transform)

    for i, obj in enumerate(list_pin):
        obj = str(obj)
        u = Transform.get_nearest_nurbs_curve_parameter(surface_transform, obj)
        cmds.setAttr("{}.normalizedIsoParms".format(node_uv_pin), False)
        cmds.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)
        cmds.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), 1)
        attr_matrix_output = "{}.outputMatrix[{}]".format(node_uv_pin, i)

        if maintain_offset:
            node_mm_offset = cmds.createNode("multMatrix", n="maintain_offset_mm")

            current_matrix = om.MMatrix(cmds.getAttr(attr_matrix_output))
            target_matrix = om.MMatrix(cmds.xform(obj, ws=1, m=1, q=1))
            offset_matrix = target_matrix * current_matrix.inverse()

            cmds.setAttr(
                "{}.matrixIn[0]".format(node_mm_offset), offset_matrix, typ="matrix"
            )
            cmds.connectAttr(
                attr_matrix_output, "{}.matrixIn[1]".format(node_mm_offset)
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm_offset)

        if prevent_double_transform:
            node_mm = cmds.createNode("multMatrix", n="prevent_double_transform_mm")

            cmds.connectAttr(
                attr_matrix_output,
                "{}.matrixIn[0]".format(node_mm),
            )
            cmds.connectAttr(
                "{}.parentInverseMatrix".format(obj),
                "{}.matrixIn[1]".format(node_mm),
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm)

        node_dcm = cmds.createNode("decomposeMatrix")

        cmds.connectAttr(attr_matrix_output, "{}.inputMatrix".format(node_dcm))
        cmds.connectAttr(
            "{}.outputTranslate".format(node_dcm), "{}.translate".format(obj), f=1
        )

        if not only_position:
            cmds.connectAttr(
                "{}.outputRotate".format(node_dcm), "{}.rotate".format(obj), f=1
            )

    return node_uv_pin


def pin_to_curve_v2(
    list_pin,
    curve,
    maintainOffset=False,
    name="PinCurve",
    parent=None,
    constraint="parent",
):
    def create_offset_group(index):
        grp_offset = cmds.group(em=1, n="{}Pin{}_grp".format(name, str(index).zfill(2)))
        if parent:
            cmds.parent(grp_offset, parent)

        return grp_offset

    source_shape = cmds.listRelatives(curve, c=1, s=1, f=1)[0]
    list_maintainOffset = []

    for i, object in enumerate(list_pin):
        if maintainOffset:
            target = create_offset_group(index=i + 1)
            list_maintainOffset.append(target)
        else:
            target = object

        param = Transform.get_nearest_nurbs_curve_parameter(curve=curve, object=object)

        poc = cmds.createNode("pointOnCurveInfo", n="{}_pin_poc".format(name))
        cmds.connectAttr(source_shape + ".worldSpace[0]", poc + ".inputCurve")
        cmds.setAttr(poc + ".parameter", param)
        cmds.connectAttr(poc + ".position", target + ".translate")

    if maintainOffset:
        return list_maintainOffset


def pin_to_surface(
    list_pin=None, surface=None, prevent_double_transform=True, maintain_offset=False
):
    """Return list of pin value reference distance from input pin"""

    if not surface:
        raise Exception("Surface Input not correct")
    if not cmds.objExists(surface):
        raise Exception("Not found surface in scene")

    if cmds.objectType(surface, isa="transform"):
        list_shape = cmds.listRelatives(surface, c=1, s=1, typ="nurbsSurface")
        if not list_shape:
            raise Exception("not found nurbs surface in input surface")
        else:
            surface_shape = list_shape[0]
            surface_transform = surface

    elif cmds.objectType(surface, isa="nurbsSurface"):
        surface_transform = cmds.listRelatives(surface, p=1, typ="nurbsSurface")[0]
        surface_shape = surface

    node_uv_pin = Create.create_uv_pin(surface_transform)

    for i, obj in enumerate(list_pin):
        obj = str(obj)
        u, v = Transform.get_nearest_nurbs_surface_parameter(surface_transform, obj)
        cmds.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)
        cmds.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), v)
        attr_matrix_output = "{}.outputMatrix[{}]".format(node_uv_pin, i)

        if maintain_offset:
            node_mm_offset = cmds.createNode("multMatrix", n="maintain_offset_mm")

            current_matrix = om.MMatrix(cmds.getAttr(attr_matrix_output))
            target_matrix = om.MMatrix(cmds.xform(obj, ws=1, m=1, q=1))
            offset_matrix = target_matrix * current_matrix.inverse()

            cmds.setAttr(
                "{}.matrixIn[0]".format(node_mm_offset), offset_matrix, typ="matrix"
            )
            cmds.connectAttr(
                attr_matrix_output, "{}.matrixIn[1]".format(node_mm_offset)
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm_offset)

        if prevent_double_transform:
            node_mm = cmds.createNode("multMatrix", n="prevent_double_transform_mm")

            cmds.connectAttr(
                attr_matrix_output,
                "{}.matrixIn[0]".format(node_mm),
            )
            cmds.connectAttr(
                "{}.parentInverseMatrix".format(obj),
                "{}.matrixIn[1]".format(node_mm),
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm)

        node_dcm = cmds.createNode("decomposeMatrix")

        cmds.connectAttr(attr_matrix_output, "{}.inputMatrix".format(node_dcm))
        cmds.connectAttr(
            "{}.outputTranslate".format(node_dcm), "{}.translate".format(obj), f=1
        )
        cmds.connectAttr(
            "{}.outputRotate".format(node_dcm), "{}.rotate".format(obj), f=1
        )

    return node_uv_pin


def pin_to_surface_patch(ribbon, list_pin, parent):
    param_factor = 1 / (len(list_pin) - 1)
    for i, pin in enumerate(list_pin):
        node = cmds.createNode("follicle")

        cmds.setAttr(node + ".parameterV", param_factor * (i))
        cmds.setAttr(node + ".parameterU", 0.5)

        cmds.connectAttr(ribbon + ".local", node + ".inputSurface")
        cmds.connectAttr(ribbon + ".worldMatrix[0]", node + ".inputWorldMatrix")
        cmds.connectAttr(node + ".outRotate", pin + ".rotate")
        cmds.connectAttr(node + ".outTranslate", pin + ".translate")

        cmds.parent(cmds.listRelatives(node, p=1, typ="transform")[0], parent)


def break_connection_transform(obj_name, rot=False, pos=False, scl=False, v=False):
    def break_each_attr(plug):
        if cmds.connectionInfo(plug, isDestination=True):
            plug = cmds.connectionInfo(plug, getExactDestination=True)
            readOnly = cmds.ls(plug, ro=True)
            if readOnly:
                source = cmds.connectionInfo(plug, sourceFromDestination=True)
                cmds.disconnectAttr(source, plug)
            else:
                cmds.delete(plug, icn=True)

    list_axis = []

    if rot:
        list_axis += ["rx", "ry", "rz"]
    if pos:
        list_axis += ["tx", "ty", "tz"]
    if scl:
        list_axis += ["sx", "sy", "sz"]
    if v:
        list_axis += ["v"]

    for axis in list_axis:
        attr = f"{obj_name}.{axis}"
        break_each_attr(attr)

    return None