from tmlib.core import Transform,Attribute
import maya.api.OpenMaya as om
import maya.cmds as cmds
import re


def duplicate_orig_shape(obj, n):

    obj = cmds.duplicate(obj, n=n)

    child = cmds.listRelatives(obj, c=1, typ="transform")

    if child:
        cmds.delete(child)

    shapes = cmds.listRelatives(obj, c=1, s=1)
    has_orig = any("Orig" in item.shortName() for item in shapes)

    if has_orig:
        exist_orig = None

        for shape in shapes:
            shape_name = shape.shortName()

            if "Orig" in shape_name and exist_orig is None:
                exist_orig = shape_name
                cmds.setAttr("{}.intermediateObject".format(shape_name), False)

            else:
                cmds.delete(shape)

    rename_shape_proper(obj)

    return obj


def morph_shape(source, list_target):
    """
    Copies the shape of the first selected mesh (source) to one or more target meshes.
    Maintains the user's original selection and displays a status message.

    Usage:
        1. Select the source mesh first.
        2. Then select one or more target meshes.
        3. Run this function.
    """

    if type(list_target) != list:
        raise Exception("input of list target must be list")

    source_vtx_count = cmds.polyEvaluate(source, vertex=True)

    MSelectionList = om.MSelectionList()

    # get point position of source
    MSelectionList.add(source)
    source_MDagPath = MSelectionList.getDagPath(0)
    source_MFnMesh = om.MFnMesh(source_MDagPath)
    MSelectionList.clear()

    list_pos_source_vtxs = source_MFnMesh.getPoints()

    # Copy source positions to each target
    for target in list_target:
        target_vtx_count = cmds.polyEvaluate(target, vertex=True)

        if target_vtx_count != source_vtx_count:
            raise ValueError(
                f"Vertex count mismatch between {source} and {target}"
            )

        # copy point
        MSelectionList.add(target)
        target_MDagPath = MSelectionList.getDagPath(0)
        target_MFnMesh = om.MFnMesh(target_MDagPath)

        for i, point in enumerate(list_pos_source_vtxs):
            target_MFnMesh.setPoint(i, list_pos_source_vtxs[i])

        MSelectionList.clear()

def get_cvs(shape):
    """ Return cvs amount of given nurbsCurve Shape"""
    spans = cmds.getAttr(f"{shape}.spans")
    degree = cmds.getAttr(f"{shape}.degree")
    cvs = spans+degree

    return cvs,spans,degree

def flip_curve(curve, flip_axis="x", world=True):
    """Flip Curve Position by reverse CV"""

    def odd_method():
        middle_index = cv_amount // 2

        list_first_block_pos = [
            cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
            for i in range(middle_index)
        ]
        value_middle = cmds.xform(
            "{}.cv[{}]".format(curve_shape, middle_index), q=1, ws=ws, os=os, t=1
        )
        list_second_block_pos = [
            cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
            for i in range(middle_index + 1, cv_amount)
        ]

        # debug

        for i, pos in enumerate(
            list_first_block_pos + [value_middle] + list_second_block_pos
        ):
            pass

        # apply new value
        list_first_block_pos_new = list_second_block_pos[::-1]
        list_second_block_pos_new = list_first_block_pos[::-1]

        list_first_block_pos_new = [
            flip_position(pos) for pos in list_first_block_pos_new
        ]
        value_middle = flip_position(value_middle)
        list_second_block_pos_new = [
            flip_position(pos) for pos in list_second_block_pos_new
        ]

        for i, pos in enumerate(
            list_first_block_pos_new + [value_middle] + list_second_block_pos_new
        ):
            cmds.xform("{}.cv[{}]".format(curve_shape, i), ws=ws, os=os, t=pos)

    def even_method():
        middle_index = cv_amount / 2

        list_first_block_pos = [
            cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
            for i in range(middle_index + 1)
        ]
        list_second_block_pos = [
            cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
            for i in range(middle_index + 1, cv_amount)
        ]

        # debug

        for i, pos in enumerate(list_first_block_pos + list_second_block_pos):
            pass

        # apply new value
        list_first_block_pos_new = list_second_block_pos[::-1]
        list_second_block_pos_new = list_first_block_pos[::-1]

        list_first_block_pos_new = [
            flip_position(pos) for pos in list_first_block_pos_new
        ]
        list_second_block_pos_new = [
            flip_position(pos) for pos in list_second_block_pos_new
        ]

        for i, pos in enumerate(list_first_block_pos_new + list_second_block_pos_new):
            cmds.xform("{}.cv[{}]".format(curve_shape, i), ws=ws, os=os, t=pos)

    def flip_position(position):
        if flip_axis == "x":
            return [position[0] * -1, position[1], position[2]]
        elif flip_axis == "y":
            return [position[0], position[1] * -1, position[2]]
        elif flip_axis == "z":
            return [position[0], position[1], position[2] * -1]

    # prepare
    curve_shape = cmds.listRelatives(curve, c=1, s=1, typ="nurbsCurve")

    if curve_shape:
        curve_shape = curve_shape[0]
    else:
        return None

    if world:
        ws = True
        os = False
    elif not world:
        ws = False
        os = True

    cv_amount = cmds.getAttr(f"{curve_shape}.spans") + cmds.getAttr(
        f"{curve_shape}.degree"
    )

    # check is curve is odd
    if cv_amount % 2 != 0:
        odd_method()
    else:
        even_method()


def add_attribute_divider(object_name: str, name: str, divider_bar="+++++"):
    """
    Add Blank Attribute With Divider Head Name

    object_name(str) : name of target object
    name(str) : name of head name
    divider_bar(str) : string text of divider
    """

    if Attribute.is_attr_exists("{}.{}".format(object_name,name.replace(" ",""))):
        cmds.deleteAttr("{}.{}".format(object_name,name.replace(" ","")))
        
    cmds.addAttr(
        object_name,
        nn=divider_bar,
        ln=name.replace(" ", ""),
        at="enum",
        en="{}".format(name),
        k=1,
    )
    cmds.setAttr(object_name + "." + name, cb=1, l=1)


def connect_matching_attributes(source, target, unit_conversion=None):
    if not cmds.objExists(source) or not cmds.objExists(target):
        return

    source_attrs = cmds.listAttr(source, keyable=True, unlocked=True) or []
    target_attrs = cmds.listAttr(target, keyable=True, unlocked=True) or []
    matching_attrs = set(source_attrs) & set(target_attrs)

    for attr in matching_attrs:
        source_attr = f"{source}.{attr}"
        target_attr = f"{target}.{attr}"

        if (
            cmds.getAttr(source_attr, type=True) in ["double", "float"]
            and unit_conversion
        ):
            mult_node = cmds.createNode(
                "multiplyDivide", name=f"{source}_{attr}_convert"
            )
            cmds.setAttr(f"{mult_node}.input2X", unit_conversion)
            cmds.connectAttr(source_attr, f"{mult_node}.input1X", force=True)
            source_attr = f"{mult_node}.outputX"

        if not cmds.isConnected(source_attr, target_attr):
            cmds.connectAttr(source_attr, target_attr, force=True)

    return None


def cut(path: str, hierarchy=True, attr=False, namespace=False):
    """
    Use to cut path to get only short name for hierarchy or attribute

    path(str) : path , for example
                object : group|object > object,
                attribute : group|object.translateX > translateX
    attr(bool) : if True will return cut attribute , if False will return cut object

    """

    path = str(path)

    if hierarchy:
        if "|" in path:
            path = path.split("|")[-1]

    if attr:
        if "." in path:
            path = path.split(".")[-1]

    if namespace:
        if ":" in path:
            path = path.split(":")[-1]

    return path


def get_curve_position(amount, curve):
    list_position = []
    list_poc = []
    curve_transform = curve
    curve_shape = cmds.listRelatives(curve_transform, c=1, s=1, typ="nurbsCurve")[0]

    if "crv_" in curve_transform:
        main_name = curve_transform.replace("crv_", "")
    else:
        main_name = curve_transform

    for i in range(amount):
        node = cmds.shadingNode(
            "pointOnCurveInfo",
            au=1,
            n="poc_" + main_name + "_tmp_" + str(i + 1).zfill(2),
        )

        if amount == 1:
            param = 0.5
        else:
            param = i * (1 / (amount - 1))

        cmds.connectAttr(curve_shape + ".worldSpace[0]", node + ".inputCurve")
        cmds.setAttr(node + ".parameter", param)
        cmds.setAttr(node + ".turnOnPercentage", 1)

        list_poc.append(node)
        list_position.append(cmds.getAttr(node + ".position"))

    cmds.delete(list_poc)

    return list_position


def lock_attribute(
    transform: str = "transform_name",
    r: int = 0,
    s: int = 0,
    t: int = 0,
    v: int = 0,
    l: int = 1,
    k: int = None,
):
    """
    Locks or unlocks the specified transform attributes on a Maya node.

    Parameters:
        transform (str): Name of the transform node.
        r (int): If 1, lock/unlock rotation attributes (rx, ry, rz).
        s (int): If 1, lock/unlock scale attributes (sx, sy, sz).
        t (int): If 1, lock/unlock translation attributes (tx, ty, tz).
        v (int): If 1, lock/unlock visibility attribute (v).
        l (int): Lock state. 1 = lock, 0 = unlock. Default is 1.
        k (int or None): Keyable state. If None, will be automatically set to opposite of lock.

    Returns:
        None
    """

    if not cmds.objExists(transform):
        return

    # Determine keyable state based on lock flag if not explicitly provided
    if k is None:
        k = 0 if l else 1

    def set_attrs(attrs):
        for attr in attrs:
            cmds.setAttr(f"{transform}.{attr}", lock=l, keyable=k)

    if r:
        set_attrs(["rx", "ry", "rz"])
    if t:
        set_attrs(["tx", "ty", "tz"])
    if s:
        set_attrs(["sx", "sy", "sz"])
    if v:
        cmds.setAttr(f"{transform}.v", lock=l, keyable=k)

    return None


def match_parent(target, parent):
    """Match transform and parent"""

    Transform.match_transform(target, parent)
    cmds.parent(target, parent)

    return target


def rename_shape_proper(control):
    """Use to rename shape node properly name"""

    list_shape = cmds.listRelatives(control, c=1, s=1, typ="nurbsCurve", f=1)
    for i, shape in enumerate(list_shape):
        cmds.rename(shape, "{}Shape".format(cut(control)))


def set_rotate_order(list_target, rotate_order):
    dict_rotate_order = {"xyz": 0, "yzx": 1, "zxy": 2, "xzy": 3, "yxz": 4, "zyx": 5}

    for target in list_target:
        cmds.setAttr("{}.rotateOrder".format(target), dict_rotate_order[rotate_order])


def show_rotate_order(object):
    object_node = make_pynode(object)

    cmds.setAttr("{}.rotateOrder".format(object_node), l=0, k=1)


def get_vertex_data_position(mesh):
    """return dictionary of vertex id as keys , and its world position as values

    Return

    {0:(1,1,1,)}

    """

    if cmds.objectType(mesh) == "mesh":
        shape = mesh
    else:
        shape = cmds.listRelatives(mesh, c=1, s=1)[0]

    # dict target vtx pos
    vtx_count = cmds.polyEvaluate(shape, vertex=True)
    dict_target_pos = {}

    for i in range(vtx_count):
        dict_target_pos[i] = cmds.xform("{}.vtx[{}]".format(shape, i), q=1, t=1, ws=1)

    return dict_target_pos
