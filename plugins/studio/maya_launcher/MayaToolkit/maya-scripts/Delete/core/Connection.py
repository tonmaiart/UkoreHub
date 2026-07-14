from TonmaiToolkit.core import Transform, Utility, Misc, BlendShape, Create

import maya.cmds as mc
import pymel.core as pm
import maya.api.OpenMaya as om

import math


def create_switch_enum(
    object_driven,
    list_target,
    object_attribute=None,
    list_target_name=None,
    type="parent",
):
    """
    Create Enum Switch Space

    controller : object that will create new enum attribute named "space" for choose space
    list_space : all space target
    list_nice_name : all space target nice name
    object : main target

    """

    def key_target(index):
        # set current enum attr
        pm.setAttr(attr_path, index)

        # set all weight to zero, except the target one
        for i, weight_name in enumerate(list_weight):
            if i == index:
                pm.setAttr(weight_name, 1)
            else:
                pm.setAttr(weight_name, 0)

            # set key
            pm.setDrivenKeyframe(weight_name, cd=attr_path)

    def create_space_locator():
        for i, obj in enumerate(list_target):
            # create space local group and connect matrix
            grp_space_local = pm.group(
                em=1,
                n="{}_{}Space_grp".format(list_target_name[i], object_driven),
                p=grp_space_still,
            )
            pm.connectAttr(
                "{}.worldMatrix[0]".format(obj),
                "{}.offsetParentMatrix".format(grp_space_local),
            )

            # create offset transform group
            grp_space_offset = pm.group(
                em=1,
                n="{}_{}SpaceOff_grp".format(list_target_name[i], object_driven),
                p=grp_space_local,
            )
            loc_space = pm.group(
                n="{}_{}Space_loc".format(list_target_name[i], object_driven),
                em=1,
                p=grp_space_offset,
            )
            # loc_space = pm.spaceLocator(n="{}_{}Space_loc".format(list_nice_name[i], target))[0]

            # snap grp offset to target
            constraint = pm.parentConstraint(object_driven, grp_space_offset)
            pm.delete(constraint)

            list_space_locator.append(loc_space)

    def create_constraint_node():
        # create constraint node

        target_pn = pm.PyNode(object_driven)
        grp_offset_target = Create.create_freeze_group([target_pn])
        maintain_offset = 0

        if type == "parent":
            constraint_name = pm.parentConstraint(
                list_space_locator, grp_offset_target, mo=maintain_offset
            )
            list_weight = pm.parentConstraint(constraint_name, q=1, wal=1)
        elif type == "point":
            constraint_name = pm.pointConstraint(
                list_space_locator, grp_offset_target, mo=maintain_offset
            )
            list_weight = pm.pointConstraint(constraint_name, q=1, wal=1)
        elif type == "orient":
            constraint_name = pm.orientConstraint(
                list_space_locator, grp_offset_target, mo=maintain_offset
            )
            list_weight = pm.orientConstraint(constraint_name, q=1, wal=1)
        else:
            raise Exception("Input Constraint Type is Invalid")

        return constraint_name, list_weight

    # error handling
    if len(list_target_name) != len(list_target):
        raise Exception("Invalid Input Space and Nice Name")

    if not list_target_name:
        list_target_name = list_target

    # variables
    grp_space_still = pm.group(em=1, n="{}_spaceStill_grp".format(object_driven))
    pm.setAttr("{}.inheritsTransform".format(grp_space_still), 0)

    if not object_attribute:
        object_attribute = object_driven

    pm.addAttr(
        object_attribute, ln="space", at="enum", en=":".join(list_target_name), k=1
    )

    list_space_locator = []
    attr_path = "{}.space".format(object_attribute)
    pm.setAttr(attr_path, 0)

    # create space locator
    create_space_locator()

    constraint_name, list_weight = create_constraint_node()

    # set driven key to all weight
    for i in range(len(list_target)):
        key_target(i)

    # set attribute
    pm.setAttr(attr_path, 0)

    pm.parent(grp_space_still, object_driven)
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

    # create attribute
    if at == "enum":
        pm.addAttr(object_attr, ln="space", at="enum", en=":".join(list_nice_name), k=1)

    attr_switch = object_attr + ".space"

    # create space groups
    for item in list_space:
        # create
        locator = pm.spaceLocator(n="{}space{}_loc".format(target, item.capitalize()))[
            0
        ]
        grp_offset = pm.group(
            locator, n="{}_{}space_grp".format(target, item.capitalize())
        )

        # connect world matrix
        pm.setAttr("{}.inheritsTransform".format(grp_offset), 0)
        pm.connectAttr(
            "{}.worldMatrix[0]".format(item), "{}.offsetParentMatrix".format(grp_offset)
        )

        # snap locator to target positiion
        pm.matchTransform(locator, target)

        # append to list
        Utility.lock_attribute(grp_offset, t=1, r=1, s=1, l=1, k=0)
        list_output_group.append(grp_offset)
        list_locator.append(locator)

    # pick Matrix
    if pick:
        node_pick_matrix = pm.createNode(
            "pickMatrix", n="pmx_{}SpaceSwitch".format(target)
        )
        pm.setAttr(node_pick_matrix + ".useTranslate", 0)
        pm.setAttr(node_pick_matrix + ".useRotate", 0)
        pm.setAttr(node_pick_matrix + ".useScale", 0)
        pm.setAttr(node_pick_matrix + ".useShear", 0)

        for option in pick:
            if option == "translate":
                pm.setAttr(node_pick_matrix + ".useTranslate", 1)
            elif option == "rotate":
                pm.setAttr(node_pick_matrix + ".useRotate", 1)
            elif option == "scale":
                pm.setAttr(node_pick_matrix + ".useScale", 1)
            elif option == "shear":
                pm.setAttr(node_pick_matrix + ".useShear", 1)

    # create node connection
    node_mult_matrix = pm.createNode("multMatrix")

    list_parent = pm.listRelatives(grp_blend, p=1)
    if list_parent:
        pm.connectAttr(
            "{}.worldInverseMatrix[0]".format(list_parent[0]),
            "{}.matrixIn[1]".format(node_mult_matrix),
        )

    # create attribute input connection
    if at == "enum":
        node_choice = pm.createNode("choice")
        pm.connectAttr(attr_switch, "{}.selector".format(node_choice))
        [
            pm.connectAttr(
                "{}.worldMatrix[0]".format(list_locator[i]),
                "{}.input[{}]".format(node_choice, i),
            )
            for i in range(len(list_space))
        ]
        pm.connectAttr(
            "{}.output".format(node_choice), "{}.matrixIn[0]".format(node_mult_matrix)
        )
    elif at == "float":
        node_blend_matrix = pm.createNode("blendMatrix")
        pm.connectAttr(attr_switch, "{}.envelope".format(node_blend_matrix))
        pm.connectAttr(
            "{}.worldMatrix[0]".format(list_locator[1]),
            "{}.target[0].targetMatrix".format(node_blend_matrix),
        )
        pm.connectAttr(
            "{}.worldMatrix[0]".format(list_locator[0]),
            "{}.inputMatrix".format(node_blend_matrix),
        )
        pm.connectAttr(
            "{}.outputMatrix".format(node_blend_matrix),
            "{}.matrixIn[0]".format(node_mult_matrix),
        )

    # apply to target grp blend
    if pick:
        pm.connectAttr(
            "{}.matrixSum".format(node_mult_matrix),
            "{}.inputMatrix".format(node_pick_matrix),
        )
        pm.connectAttr(
            "{}.outputMatrix".format(node_pick_matrix),
            "{}.offsetParentMatrix".format(grp_blend),
        )
    else:
        pm.connectAttr(
            "{}.matrixSum".format(node_mult_matrix),
            "{}.offsetParentMatrix".format(grp_blend),
        )

    return list_output_group


def create_switch_float(
    target1, target2, object, controller, attr_name="space", typ="orient"
):
    """
    Create blend space (float attribute)
    """

    node_rev = pm.createNode("reverse", n="node_rev")

    locatorFrz1 = pm.spaceLocator(n="loc_{}SpaceFrz".format(object))
    locatorFrz2 = pm.spaceLocator(n="loc_{}SpaceFrz".format(object))

    locator1 = pm.spaceLocator(n="loc_{}Space".format(object))
    locator2 = pm.spaceLocator(n="loc_{}Space".format(object))

    # parent connection
    pm.setAttr(locatorFrz1 + ".inheritsTransform", 0)
    pm.setAttr(locatorFrz2 + ".inheritsTransform", 0)

    pm.setAttr(locatorFrz1 + ".v", 0)
    pm.setAttr(locatorFrz2 + ".v", 0)

    pm.connectAttr(
        "{}.worldMatrix[0]".format(target1), "{}.offsetParentMatrix".format(locatorFrz1)
    )
    pm.connectAttr(
        "{}.worldMatrix[0]".format(target2), "{}.offsetParentMatrix".format(locatorFrz2)
    )

    pm.parent(locator1, locatorFrz1)
    pm.parent(locator2, locatorFrz2)

    pm.matchTransform(locator1, object)
    pm.matchTransform(locator2, object)

    grp_blend = Create.create_freeze_group([object], "grpBlend")[0]

    pm.parent(locatorFrz1, locatorFrz2, grp_blend)

    # orient constraint
    if typ == "parent":
        cons = pm.parentConstraint(locator1, locator2, grp_blend)
    elif typ == "orient":
        cons = pm.orientConstraint(locator1, locator2, grp_blend)
    elif typ == "point":
        cons = pm.pointConstraint(locator1, locator2, grp_blend)
    else:
        raise Exception("type invalid")

    pm.setAttr("{}.interpType".format(cons), 2)

    # reconnect attribute constraint
    pm.addAttr(controller, ln=attr_name, k=1, min=0, max=1)
    pm.connectAttr(
        "{}.{}".format(controller, attr_name), "{}.{}W0".format(cons, locator1)
    )
    pm.connectAttr("{}.{}".format(controller, attr_name), "{}.inputX".format(node_rev))
    pm.connectAttr("{}.outputX".format(node_rev), "{}.{}W1".format(cons, locator2))


def connect(
    object,
    target,
    typ="all",
    translate_multiplier=1,
    rotate_multiplier=1,
    name="connect",
):
    """
    Use to direct connect given object to target object

    Arguments:

    """
    if not Utility.is_py_node(object):
        object = pm.PyNode(object)

    if not Utility.is_py_node(target):
        target = pm.PyNode(target)

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
            pm.connectAttr(object + ".t", target + ".t")

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
            pm.connectAttr(object + ".r", target + ".r")

    # optional : connect
    if typ == "translate":
        connect_translate()
    elif typ == "rotate":
        connect_rotate()

    elif typ == "scale":
        pm.connectAttr(object + ".s", target + ".s", f=1)

    elif typ == "all":
        connect_translate()

        connect_rotate()
        pm.connectAttr(object + ".s", target + ".s")


def connect_conversion(
    input1, input2=None, output=None, conversion=-1, name="multDoubleLinear"
):
    node = pm.createNode("multDoubleLinear", n="{}_mdl".format(name))
    pm.connectAttr(input1, node + ".input1")

    if input2:
        pm.connectAttr(input2, node + ".input2")
    else:
        pm.setAttr(node + ".input2", conversion)

    if output:
        pm.connectAttr(node + ".output", output)

    return node.output


def connect_conversion_vector(
    list_input1=[],
    list_input2=None,
    list_output=None,
    list_conversion=[1, 1, 1],
    name="conversion",
):
    node = pm.createNode("multiplyDivide", n="{}_conversion_md".format(name))

    list_input_1_name = [".input1X", ".input1Y", ".input1Z"]
    list_output_name = [".outputX", ".outputY", ".outputZ"]

    for i, input in enumerate(list_input1):
        pm.connectAttr(input, node + list_input_1_name[i])

    if list_input2:
        pm.connectAttr(list_input2[0], node + ".input2X")
        pm.connectAttr(list_input2[1], node + ".input2X")
        pm.connectAttr(list_input2[2], node + ".input2X")
    else:
        pm.setAttr(node + ".input2X", list_conversion[0])
        pm.setAttr(node + ".input2Y", list_conversion[1])
        pm.setAttr(node + ".input2Z", list_conversion[2])

    # connect to output
    for i, output_attribute in enumerate(list_output):
        pm.connectAttr(node + list_output_name[i], output_attribute)


def connect_conversion_unit(
    input, output=None, factor=None, name="unitConversion", use_factor_attr=False
):
    node = pm.createNode("unitConversion", n=name)
    pm.connectAttr(input, node + ".input")

    if output:
        pm.connectAttr(node + ".output", output)

    if use_factor_attr:
        pm.connectAttr(factor, "{}.conversionFactor".format(node))
    else:
        pm.setAttr(node + ".conversionFactor", factor)

    return node


def connect_bind_pre_matrix(
    list_joint, skin_cluster, list_transform=None, attribute="parentInverseMatrix"
):
    """Connect world inverse matrix of given list transform to skin cluster pre bind matrix"""

    if not list_transform:
        list_transform = list_joint

    if not Utility.is_py_node(skin_cluster):
        skin_cluster = pm.PyNode(skin_cluster)

    for transform, joint in zip(list_transform, list_joint):
        if not Utility.is_py_node(transform):
            transform = pm.PyNode(transform)
        if not Utility.is_py_node(joint):
            joint = pm.PyNode(joint)

        list_connection_world_matrix = pm.listConnections(
            "{}.worldMatrix[0]".format(str(joint)), p=1
        )

        index = None

        for attr in list_connection_world_matrix:
            attr_path = attr.longName(fullPath=False)

            if skin_cluster.name() in str(attr):
                number = int(attr_path.split("[")[1].rstrip("]"))
                index = number
                break

        # skip if not found index
        if index is None:
            print("not found index for {} , {}".format(transform, joint))
            continue

        # connect bind pre matrix
        pm.connectAttr(
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

    #################################################
    ### create reverse + blend matrix for each joint
    #################################################

    attr_switch = connect_conversion_unit(attr_switch, factor=1 / max_value) + ".output"

    node_rev = pm.createNode("reverse", n="switch_reverse")
    pm.connectAttr(attr_switch, "{}.inputX".format(node_rev))

    for joint_bind, joint_fk, joint_ik in zip(bind_joints, fk_joints, ik_joints):
        if method == "parent":
            constraint = pm.parentConstraint(joint_fk, joint_ik, joint_bind)
            pm.connectAttr(node_rev + ".outputX", "{}.w0".format(constraint))
            pm.connectAttr(node_rev + ".inputX", "{}.w1".format(constraint))
        elif method == "orient":
            constraint = pm.orientConstraint(joint_fk, joint_ik, joint_bind)
            pm.connectAttr(node_rev + ".outputX", "{}.w0".format(constraint))
            pm.connectAttr(node_rev + ".inputX", "{}.w1".format(constraint))
        elif method == "blendColors":
            node_blend_color = pm.createNode("blendColors", n="rotate_blend")
            joint_ik.rotate >> node_blend_color.color2
            joint_fk.rotate >> node_blend_color.color1
            node_rev.outputX >> node_blend_color.blender
            node_blend_color.output >> joint_bind.rotate

            # node_blend_color = pm.createNode("blendColors", n="translate_blend")
            # joint_ik.translate >> node_blend_color.color2
            # joint_fk.translate >> node_blend_color.color1
            # node_rev.outputX >> node_blend_color.blender
            # node_blend_color.output >> joint_bind.translate

    ##########################
    ### connect visibility ###
    ##########################
    if grp_ik:
        node_rev.inputX >> grp_ik.visibility

    if grp_fk:
        node_rev.outputX >> grp_fk.visibility


def constraint_matrix(list_constraint, method="point", mo=False):
    """
    Method : (point,orient,scale,parent)

    This Function create matrix connection like constraint.

    """

    source = list_constraint[0]
    target = list_constraint[1]

    source_node = Utility.make_pynode(source)
    target_node = Utility.make_pynode(target)

    # create node
    node_decomp = pm.createNode("decomposeMatrix")
    node_pick_matrix = pm.createNode("pickMatrix")

    pm.connectAttr(
        "{}.worldMatrix[0]".format(source_node),
        "{}.inputMatrix".format(node_pick_matrix),
    )

    if method == "point":
        node_pick_matrix.useTranslate.set(True)
        node_pick_matrix.useRotate.set(False)
        node_pick_matrix.useScale.set(False)
        node_pick_matrix.useShear.set(False)

    # maintain offset
    if mo:
        node_mult_matrix_offset = pm.createNode("multMatrix", n="offset_mm")

        # get offset matrix from source and target in world space
        source_matrix = om.MMatrix(
            pm.getAttr("{}.outputMatrix".format(node_pick_matrix))
        )
        target_matrix = om.MMatrix(pm.xform(target_node, q=1, ws=1, m=1))

        matrix_offset = target_matrix * source_matrix.inverse()

        pm.setAttr("{}.matrixIn[0]".format(node_mult_matrix_offset), matrix_offset)
        pm.connectAttr(
            "{}.outputMatrix".format(node_pick_matrix),
            "{}.matrixIn[1]".format(node_mult_matrix_offset),
        )

        attr_maintain_offset = "{}.matrixSum".format(node_mult_matrix_offset)
    else:
        attr_maintain_offset = "{}.outputMatrix".format(node_pick_matrix)

    # connect inverse matrix to ignore parent
    node_mult_matrix_inverse = pm.createNode("multMatrix", n="inverse_parent_mm")

    pm.connectAttr(
        attr_maintain_offset, "{}.matrixIn[0]".format(node_mult_matrix_inverse)
    )
    pm.connectAttr(
        "{}.parentInverseMatrix[0]".format(target_node),
        "{}.matrixIn[1]".format(node_mult_matrix_inverse),
    )

    # add offset orient for joint
    if pm.objectType(target_node, isa="joint"):
        joint_orient = target_node.jointOrient.get()

        if joint_orient == [0, 0, 0]:
            pm.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_inverse),
                "{}.inputMatrix".format(node_decomp),
            )

            node_decomp_t = node_decomp
            node_decomp_r = node_decomp

        else:
            pm.connectAttr(
                "{}.matrixSum".format(node_mult_matrix_inverse),
                "{}.inputMatrix".format(node_decomp),
            )

            node_decomp_rot = pm.createNode("decomposeMatrix")

            # Directly make EulerRotation (convert to radians inline)
            euler = om.MEulerRotation(
                math.radians(joint_orient[0]),
                math.radians(joint_orient[1]),
                math.radians(joint_orient[2]),
                om.MEulerRotation.kXYZ,
            )

            # Get 4x4 matrix
            m_offset = euler.asMatrix()
            m_offset = m_offset.inverse()

            node_offset_joint_orient = pm.createNode("multMatrix")

            # m_target = om.MMatrix(target_node.worldMatrix[0].get())
            m_current = om.MMatrix(node_mult_matrix_inverse.matrixSum.get())
            # m_offset = m_target*m_current.inverse()

            node_mult_matrix_inverse.matrixSum >> node_offset_joint_orient.matrixIn[0]
            node_offset_joint_orient.matrixIn[1].set(m_offset)

            node_offset_joint_orient.matrixSum >> node_decomp_rot.inputMatrix

            node_decomp_t = node_decomp
            node_decomp_r = node_decomp_rot

    else:
        pm.connectAttr(
            "{}.matrixSum".format(node_mult_matrix_inverse),
            "{}.inputMatrix".format(node_decomp),
        )

        node_decomp_t = node_decomp
        node_decomp_r = node_decomp

    # connect matrix to output attributes
    if method == "point":
        pm.connectAttr(
            "{}.outputTranslate".format(node_decomp),
            "{}.translate".format(target_node),
            f=1,
        )
    elif method == "orient":
        pm.connectAttr(
            "{}.outputRotate".format(node_decomp), "{}.rotate".format(target_node), f=1
        )
    elif method == "parent":
        pm.connectAttr(
            "{}.outputTranslate".format(node_decomp_t),
            "{}.translate".format(target_node),
            f=1,
        )
        pm.connectAttr(
            "{}.outputRotate".format(node_decomp_r),
            "{}.rotate".format(target_node),
            f=1,
        )
    elif method == "scale":
        pm.connectAttr(
            "{}.outputScale".format(node_decomp), "{}.scale".format(target_node), f=1
        )

    return


def decomp_constraint(parent, object, r=True, t=True):
    node_decomp = pm.createNode("decomposeMatrix", n="decomp")

    pm.connectAttr(parent + ".worldMatrix[0]", node_decomp + ".inputMatrix")

    if r:
        pm.connectAttr(node_decomp + ".outputRotate", object + ".r")
    if t:
        pm.connectAttr(node_decomp + ".outputTranslate", object + ".t")


def set_driver_node_fixed(
    attr_driver,
    attr_driven,
    driven_value,
    name,
    clamp_length=[None, None],
    driven_value_is_fixed=False,
):
    # create driver connection
    node_mdl_mult = pm.createNode("multDoubleLinear", n="{}_mult_mdl".format(name))

    if driven_value_is_fixed:
        pm.setAttr("{}.input2".format(node_mdl_mult), driven_value)
    else:
        pm.connectAttr(driven_value, "{}.input2".format(node_mdl_mult))

    pm.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

    if clamp_length is [None, None]:  # no clamp case
        pm.connectAttr("{}.output".format(node_mdl_mult), attr_driven)

    elif clamp_length[0] and clamp_length[1]:  # clamp both side
        node_clamp = pm.createNode("clamp", n="{}_clamp_cmp".format(name))
        pm.setAttr("{}.minR".format(node_clamp), clamp_length[0])
        pm.setAttr("{}.maxR".format(node_clamp), clamp_length[1])

        pm.connectAttr(
            "{}.output".format(node_mdl_mult), "{}.inputR".format(node_clamp)
        )
        pm.connectAttr("{}.outputR".format(node_clamp), attr_driven)

    else:  # clamp single side
        if clamp_length[0] is not None:
            operation = 2
            value = clamp_length[0]
        elif clamp_length[1] is not None:
            operation = 4
            value = clamp_length[1]
        else:
            raise Exception("Error Calculate")

        node_cond = pm.createNode("condition", n="{}_clamp_cond".format(name))

        pm.connectAttr(
            "{}.output".format(node_mdl_mult), "{}.colorIfTrueR".format(node_cond)
        )
        pm.connectAttr(
            "{}.output".format(node_mdl_mult), "{}.firstTerm".format(node_cond)
        )
        pm.setAttr("{}.secondTerm".format(node_cond), value)

        pm.setAttr("{}.colorIfFalseR".format(node_cond), value)

        pm.setAttr("{}.operation".format(node_cond), operation)

        pm.connectAttr("{}.outColorR".format(node_cond), attr_driven)

    return node_mdl_mult


def set_driver_node_multi_input(list_attr_driver, attr_driven, list_attr_factor, name):
    if len(list_attr_driver) != len(list_attr_factor):
        raise Exception("Invalid Input")

    amount_driver = len(list_attr_driver)

    # input driven
    list_mdl_mult = []
    for i in range(amount_driver):
        attr_driver = list_attr_driver[i]
        attr_factor = list_attr_factor[i]

        node_mdl_mult = pm.createNode(
            "multDoubleLinear", n="{}_mult{}_mdl".format(name, i)
        )
        pm.connectAttr(attr_factor, "{}.input2".format(node_mdl_mult))
        pm.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

        list_mdl_mult.append(node_mdl_mult + ".output")

    # create sum value and connect to output
    node_pma_sum = pm.createNode("plusMinusAverage", n="{}_sum_pma".format(name))

    for i in range(amount_driver):
        attr_mdl = list_mdl_mult[i]

        pm.connectAttr(attr_mdl, "{}.input1D[{}]".format(node_pma_sum, i))

    pm.connectAttr("{}.output1D".format(node_pma_sum), attr_driven)

    return node_pma_sum


def set_driver_node_realtime(
    attr_driver, attr_driven, attr_driver_key, attr_driven_key, name=""
):
    # create connection
    node_md_divide = pm.createNode("multiplyDivide", n="{}divide_md".format(name))
    node_mdl_mult = pm.createNode("multDoubleLinear", n="{}mult_mdl".format(name))

    pm.setAttr("{}.operation".format(node_md_divide), 2)

    pm.connectAttr(attr_driven_key, "{}.input1X".format(node_md_divide))
    pm.connectAttr(attr_driver_key, "{}.input2X".format(node_md_divide))

    pm.connectAttr(
        "{}.outputX".format(node_md_divide), "{}.input2".format(node_mdl_mult)
    )
    pm.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

    # output
    pm.connectAttr("{}.output".format(node_mdl_mult), attr_driven)


def set_blend_shape_expression(
    node_name,
    mesh_target,
    mesh_base,
    driver_value,
    driver_attr,
    clamp_length=[0, 1],
    module_name="SetDriven",
):
    # add new attribute
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

        node_mdl = pm.createNode("multDoubleLinear", n="{}_mdl".format(name_tag))
        pm.connectAttr(input_attr, "{}.input2".format(node_mdl))
        pm.setAttr("{}.input1".format(node_mdl), factor)

        return node_mdl + ".output"

    attr_input1 = get_input_factor(list_input_attr[0], list_driver_value[0])
    attr_input2 = get_input_factor(list_input_attr[1], list_driver_value[1])

    # create clamp node
    node_clamp = pm.createNode("clamp")
    pm.setAttr(node_clamp + ".min", 0, 0, 0, typ="double3")
    pm.setAttr(node_clamp + ".max", 1, 1, 1, typ="double3")

    pm.connectAttr(attr_input1, node_clamp + ".inputR")
    pm.connectAttr(attr_input2, node_clamp + ".inputG")

    # sum
    node_adl_sum = pm.createNode("addDoubleLinear", n="{}_adl".format(name_tag))

    pm.connectAttr(node_clamp + ".outputR", node_adl_sum + ".input1")
    pm.connectAttr(node_clamp + ".outputG", node_adl_sum + ".input2")

    # divide 2
    node_mdl_avg = pm.createNode("multDoubleLinear", n="{}_avg_mdl".format(name_tag))

    pm.connectAttr(node_adl_sum + ".output", node_mdl_avg + ".input1")
    pm.setAttr(node_mdl_avg + ".input2", 0.5)
    pm.connectAttr(node_mdl_avg + ".output", output_attr)


def set_driver_blend_shape_single(
    input_attr=None,
    driver_value=3,
    output_attr=None,
    clamp=False,
    name_tag="setDriverBlendShape",
    driven_value=1,
):
    factor = driven_value / driver_value

    node_mdl = pm.createNode(
        "multDoubleLinear", n="{}_set_blend_shape_mdl".format(name_tag)
    )
    pm.connectAttr(input_attr, "{}.input2".format(node_mdl))
    pm.setAttr("{}.input1".format(node_mdl), factor)

    # is clamp
    if clamp:
        node_clamp = pm.createNode("clamp", n="{}_set_blend_shape_cmp".format(name_tag))
        pm.connectAttr(node_mdl + ".output", node_clamp + ".inputR")
        pm.setAttr(node_clamp + ".minR", 0)
        pm.setAttr(node_clamp + ".maxR", 1)
        pm.connectAttr(node_clamp + ".outputR", output_attr)
    else:
        pm.connectAttr(node_mdl + ".output", output_attr)


def set_diagonal_driver(
    transform_name, axis_up="y", axis_out="x", name_tag="setDriver"
):
    """
    Creates a 2D translation-based driver for blend shapes.

    This function generates Maya nodes to convert the movement of `transform_name`
    (along `axis_up` and `axis_out`) into eight driver attributes for blend shapes:
    'Up', 'Down', 'In', 'Out', 'UpOut', 'UpIn', 'DownOut', and 'DownIn'.

    Cardinal directions (Up, Down, In, Out) are normalized, reducing influence
    in diagonal movements. Diagonal directions (UpOut, UpIn, DownOut, DownIn)
    are an average of their cardinal components.

    Args:
        transform_name (str): The name of the transform driving the system.
        axis_up (str, optional): The "up" axis ('x', 'y', or 'z'). Defaults to "y".
        axis_out (str, optional): The "out" axis ('x', 'y', or 'z'). Defaults to "x".
        name_tag (str, optional): A unique name tag for the created Maya nodes. Defaults to "setDriver".

    Returns:
        pm.PyNode: A transform node with the eight custom float attributes for blend shape connections.

    Example:
        import pymel.core as pm
        driver = pm.spaceLocator(n="myDriver")
        output_node = set_diagonal_driver(driver.name())
        # Connect output_node.Up, output_node.DownOut, etc., to blend shape weights.
    """

    def get_output_between(attr_A, attr_B):
        node_mdl = pm.createNode("multDoubleLinear", n="{}_avg_md".format(name_tag))
        pm.connectAttr(attr_A, node_mdl + ".input1")
        pm.connectAttr(attr_B, node_mdl + ".input2")
        return node_mdl + ".output"

    def get_normalize_output(attr_A, attr_B, attr_target):
        # normalize attr direct
        node_adl_normalized = pm.createNode(
            "addDoubleLinear", n="{}_normalize_weight_adl".format(name_tag)
        )
        pm.connectAttr(attr_A, node_adl_normalized + ".input1")
        pm.connectAttr(attr_B, node_adl_normalized + ".input2")

        node_pma_subtract = pm.createNode(
            "plusMinusAverage", n="{}_normalize_offset_pma".format(name_tag)
        )
        pm.setAttr(node_pma_subtract + ".operation", 2)
        pm.connectAttr(attr_target, node_pma_subtract + ".input1D[0]")
        pm.connectAttr(
            node_adl_normalized + ".output", node_pma_subtract + ".input1D[1]"
        )

        return node_pma_subtract + ".output1D"

    list_axis_up_out = [axis_up, axis_out]
    # create bypass transform
    node_output = pm.createNode("transform", n=name_tag)

    pm.addAttr(node_output, ln="Up", k=1)
    pm.addAttr(node_output, ln="Down", k=1)
    pm.addAttr(node_output, ln="In", k=1)
    pm.addAttr(node_output, ln="Out", k=1)
    pm.addAttr(node_output, ln="UpOut", k=1)
    pm.addAttr(node_output, ln="UpIn", k=1)
    pm.addAttr(node_output, ln="DownOut", k=1)
    pm.addAttr(node_output, ln="DownIn", k=1)

    # create attr input
    node_sr_range_positive = pm.createNode(
        "setRange", n="{}_posClamp_sr".format(name_tag)
    )

    for axis in list_axis_up_out:
        pm.connectAttr(
            "{}.t{}".format(transform_name, axis),
            "{}.value{}".format(node_sr_range_positive, axis.upper()),
        )

        pm.setAttr("{}.oldMin{}".format(node_sr_range_positive, axis.upper()), 0)
        pm.setAttr("{}.oldMax{}".format(node_sr_range_positive, axis.upper()), 1)

        pm.setAttr("{}.min{}".format(node_sr_range_positive, axis.upper()), 0)
        pm.setAttr("{}.max{}".format(node_sr_range_positive, axis.upper()), 1)

    node_sr_range_negative = pm.createNode(
        "setRange", n="{}_negClamp_sr".format(name_tag)
    )
    node_md_negative_invert = pm.createNode(
        "multiplyDivide", n="{}_invertClamp_md".format(name_tag)
    )

    pm.setAttr(node_md_negative_invert + ".input2", -1, -1, -1, typ="double3")

    for axis in list_axis_up_out:
        pm.connectAttr(
            "{}.t{}".format(transform_name, axis),
            "{}.value{}".format(node_sr_range_negative, axis.upper()),
        )

        pm.setAttr("{}.oldMin{}".format(node_sr_range_negative, axis.upper()), -1)
        pm.setAttr("{}.oldMax{}".format(node_sr_range_negative, axis.upper()), 0)

        pm.setAttr("{}.min{}".format(node_sr_range_negative, axis.upper()), -1)
        pm.setAttr("{}.max{}".format(node_sr_range_negative, axis.upper()), 0)

        pm.connectAttr(
            "{}.outValue{}".format(node_sr_range_negative, axis.upper()),
            "{}.input1{}".format(node_md_negative_invert, axis.upper()),
        )

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

    # connect all attr to transform output
    pm.connectAttr(attr_up_norm, "{}.Up".format(node_output))
    pm.connectAttr(attr_down_norm, "{}.Down".format(node_output))
    pm.connectAttr(attr_in_norm, "{}.In".format(node_output))
    pm.connectAttr(attr_out_norm, "{}.Out".format(node_output))
    pm.connectAttr(attr_up_out, "{}.UpOut".format(node_output))
    pm.connectAttr(attr_up_in, "{}.UpIn".format(node_output))
    pm.connectAttr(attr_down_out, "{}.DownOut".format(node_output))
    pm.connectAttr(attr_down_in, "{}.DownIn".format(node_output))

    return node_output


def pin_to_mesh(
    list_pin=None, surface=None, prevent_double_transform=True, maintain_offset=False
):
    """Return list of pin value reference distance from input pin"""

    list_pin = Utility.make_pynode(list_pin)

    surface = Utility.make_pynode(surface)

    # handling error

    if not surface:

        raise Exception("Surface Input not correct")

    if not pm.objExists(surface):

        raise Exception("Not found surface in scene")

    if pm.objectType(surface, isa="transform"):  # get shape of surface

        list_shape = pm.listRelatives(surface, c=1, s=1, typ="mesh")

        if not list_shape:

            raise Exception("not found nurbs surface in input surface")

        else:

            mesh_shape = list_shape[0]

            mesh_transform = surface

    elif pm.objectType(surface, isa="mesh"):

        mesh_transform = pm.listRelatives(surface, p=1, typ="mesh")[0]

        mesh_shape = surface

    # create uv pin node

    node_uv_pin = Create.create_uv_pin(mesh_transform)

    for i, obj in enumerate(list_pin):

        # set param value

        u, v = Transform.get_nearest_mesh_parameter(mesh_transform, obj)

        pm.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)

        pm.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), v)

        attr_matrix_output = "{}.outputMatrix[{}]".format(node_uv_pin, i)

        # if maintain offset

        if maintain_offset:

            node_mm_offset = pm.createNode("multMatrix", n="maintain_offset_mm")

            current_matrix = om.MMatrix(pm.getAttr(attr_matrix_output))

            target_matrix = om.MMatrix(pm.xform(obj, ws=1, m=1, q=1))

            offset_matrix = target_matrix * current_matrix.inverse()

            pm.setAttr(
                "{}.matrixIn[0]".format(node_mm_offset), offset_matrix, typ="matrix"
            )

            pm.connectAttr(attr_matrix_output, "{}.matrixIn[1]".format(node_mm_offset))

            attr_matrix_output = "{}.matrixSum".format(node_mm_offset)

            #

            # loc_current = pm.spaceLocator(n="current")

            # loc_target = pm.spaceLocator(n="target")

            #

            # pm.xform(loc_current,ws=1,m=current_matrix)

            # pm.xform(loc_target,ws=1,m=target_matrix)

        # if prevent double transform

        if prevent_double_transform:

            node_mm = pm.createNode("multMatrix", n="prevent_double_transform_mm")

            pm.connectAttr(
                attr_matrix_output,
                "{}.matrixIn[0]".format(node_mm),
            )

            pm.connectAttr(
                "{}.parentInverseMatrix".format(obj),
                "{}.matrixIn[1]".format(node_mm),
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm)

        # connect to transform of object

        node_dcm = pm.createNode("decomposeMatrix")

        pm.connectAttr(attr_matrix_output, "{}.inputMatrix".format(node_dcm))

        pm.connectAttr(
            "{}.outputTranslate".format(node_dcm), "{}.translate".format(obj), f=1
        )

        pm.connectAttr("{}.outputRotate".format(node_dcm), "{}.rotate".format(obj), f=1)

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

    # create uv pin node
    node_uv_pin = Create.create_uv_pin(surface_transform)

    for i, obj in enumerate(list_pin):
        # set param value
        u = Transform.get_nearest_nurbs_curve_parameter(surface_transform, obj)
        pm.setAttr("{}.normalizedIsoParms".format(node_uv_pin), False)
        pm.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)
        pm.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), 1)
        attr_matrix_output = "{}.outputMatrix[{}]".format(node_uv_pin, i)

        # if maintain offset
        if maintain_offset:
            node_mm_offset = pm.createNode("multMatrix", n="maintain_offset_mm")

            current_matrix = om.MMatrix(pm.getAttr(attr_matrix_output))
            target_matrix = om.MMatrix(pm.xform(obj, ws=1, m=1, q=1))
            offset_matrix = target_matrix * current_matrix.inverse()

            pm.setAttr(
                "{}.matrixIn[0]".format(node_mm_offset), offset_matrix, typ="matrix"
            )
            pm.connectAttr(attr_matrix_output, "{}.matrixIn[1]".format(node_mm_offset))

            attr_matrix_output = "{}.matrixSum".format(node_mm_offset)

        # if prevent double transform
        if prevent_double_transform:
            node_mm = pm.createNode("multMatrix", n="prevent_double_transform_mm")

            pm.connectAttr(
                attr_matrix_output,
                "{}.matrixIn[0]".format(node_mm),
            )
            pm.connectAttr(
                "{}.parentInverseMatrix".format(obj),
                "{}.matrixIn[1]".format(node_mm),
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm)

        # connect to transform of object
        node_dcm = pm.createNode("decomposeMatrix")

        pm.connectAttr(attr_matrix_output, "{}.inputMatrix".format(node_dcm))
        pm.connectAttr(
            "{}.outputTranslate".format(node_dcm), "{}.translate".format(obj), f=1
        )

        if not only_position:
            pm.connectAttr(
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
        grp_offset = pm.group(em=1, n="{}Pin{}_grp".format(name, str(index).zfill(2)))
        if parent:
            pm.parent(grp_offset, parent)

        return grp_offset

    source_shape = pm.listRelatives(curve, c=1, s=1, f=1)[0]
    list_maintainOffset = []

    for i, object in enumerate(list_pin):
        if maintainOffset:
            target = create_offset_group(index=i + 1)
            list_maintainOffset.append(target)
        else:
            target = object

        # get nearest param
        param = Transform.get_nearest_nurbs_curve_parameter(curve=curve, object=object)

        # connect position to target
        poc = pm.createNode("pointOnCurveInfo", n="{}_pin_poc".format(name))
        pm.connectAttr(source_shape + ".worldSpace[0]", poc + ".inputCurve")
        pm.setAttr(poc + ".parameter", param)
        pm.connectAttr(poc + ".position", target + ".translate")

    if maintainOffset:
        return list_maintainOffset


def pin_to_surface(
    list_pin=None, surface=None, prevent_double_transform=True, maintain_offset=False
):
    """Return list of pin value reference distance from input pin"""

    # handling error
    if not surface:
        raise Exception("Surface Input not correct")
    if not pm.objExists(surface):
        raise Exception("Not found surface in scene")

    if pm.objectType(surface, isa="transform"):  # get shape of surface
        list_shape = pm.listRelatives(surface, c=1, s=1, typ="nurbsSurface")
        if not list_shape:
            raise Exception("not found nurbs surface in input surface")
        else:
            surface_shape = list_shape[0]
            surface_transform = surface

    elif pm.objectType(surface, isa="nurbsSurface"):
        surface_transform = pm.listRelatives(surface, p=1, typ="nurbsSurface")[0]
        surface_shape = surface

    # create uv pin node
    node_uv_pin = Create.create_uv_pin(surface_transform)

    for i, obj in enumerate(list_pin):
        # set param value
        u, v = Transform.get_nearest_nurbs_surface_parameter(surface_transform, obj)
        pm.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)
        pm.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), v)
        attr_matrix_output = "{}.outputMatrix[{}]".format(node_uv_pin, i)

        # if maintain offset
        if maintain_offset:
            node_mm_offset = pm.createNode("multMatrix", n="maintain_offset_mm")

            current_matrix = om.MMatrix(pm.getAttr(attr_matrix_output))
            target_matrix = om.MMatrix(pm.xform(obj, ws=1, m=1, q=1))
            offset_matrix = target_matrix * current_matrix.inverse()

            pm.setAttr(
                "{}.matrixIn[0]".format(node_mm_offset), offset_matrix, typ="matrix"
            )
            pm.connectAttr(attr_matrix_output, "{}.matrixIn[1]".format(node_mm_offset))

            attr_matrix_output = "{}.matrixSum".format(node_mm_offset)
            #
            # loc_current = pm.spaceLocator(n="current")
            # loc_target = pm.spaceLocator(n="target")
            #
            # pm.xform(loc_current,ws=1,m=current_matrix)
            # pm.xform(loc_target,ws=1,m=target_matrix)

        # if prevent double transform
        if prevent_double_transform:
            node_mm = pm.createNode("multMatrix", n="prevent_double_transform_mm")

            pm.connectAttr(
                attr_matrix_output,
                "{}.matrixIn[0]".format(node_mm),
            )
            pm.connectAttr(
                "{}.parentInverseMatrix".format(obj),
                "{}.matrixIn[1]".format(node_mm),
            )

            attr_matrix_output = "{}.matrixSum".format(node_mm)

        # connect to transform of object
        node_dcm = pm.createNode("decomposeMatrix")

        pm.connectAttr(attr_matrix_output, "{}.inputMatrix".format(node_dcm))
        pm.connectAttr(
            "{}.outputTranslate".format(node_dcm), "{}.translate".format(obj), f=1
        )
        pm.connectAttr("{}.outputRotate".format(node_dcm), "{}.rotate".format(obj), f=1)

    return node_uv_pin


def pin_to_surface_patch(ribbon, list_pin, parent):
    param_factor = 1 / (len(list_pin) - 1)
    for i, pin in enumerate(list_pin):
        node = pm.createNode("follicle")

        pm.setAttr(node + ".parameterV", param_factor * (i))
        pm.setAttr(node + ".parameterU", 0.5)

        pm.connectAttr(ribbon + ".local", node + ".inputSurface")
        pm.connectAttr(ribbon + ".worldMatrix[0]", node + ".inputWorldMatrix")
        pm.connectAttr(node + ".outRotate", pin + ".rotate")
        pm.connectAttr(node + ".outTranslate", pin + ".translate")

        pm.parent(pm.listRelatives(node, p=1, typ="transform")[0], parent)


def break_connection_transform(obj_name, rot=False, pos=False, scl=False):
    """
    Breaks input connections to specified attributes of an object.

    Parameters:
        obj_name (str): Name of the object.
        rot (bool): If True, disconnects rotate attributes (rotateX, rotateY, rotateZ).
        pos (bool): If True, disconnects translate attributes (translateX, translateY, translateZ).
        scl (bool): If True, disconnects scale attributes (scaleX, scaleY, scaleZ).
    """

    def break_each_attr(plug):
        if pm.connectionInfo(plug, isDestination=True):
            plug = pm.connectionInfo(plug, getExactDestination=True)
            readOnly = pm.ls(plug, ro=True)
            # delete -icn doesn't work if destination attr is readOnly
            if readOnly:
                source = pm.connectionInfo(plug, sourceFromDestination=True)
                pm.disconnectAttr(source, plug)
            else:
                pm.delete(plug, icn=True)

    list_axis = []

    if rot:
        list_axis += ["rx", "ry", "rz"]
    if pos:
        list_axis += ["tx", "ty", "tz"]
    if scl:
        list_axis += ["sx", "sy", "sz"]

    for axis in list_axis:
        attr = "{}.{}".format(obj_name, axis)

        break_each_attr(attr)

    return None
