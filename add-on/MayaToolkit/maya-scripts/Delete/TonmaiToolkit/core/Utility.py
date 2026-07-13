from TonmaiToolkit.core import Transform

import maya.cmds as mc
import pymel.core as pm
import re

import pymel.core as pm
import maya.api.OpenMaya as om


def duplicate_orig_shape(obj, n):

    obj = pm.duplicate(obj, n=n)

    child = pm.listRelatives(obj, c=1, typ="transform")

    if child:
        pm.delete(child)

    shapes = pm.listRelatives(obj, c=1, s=1)
    has_orig = any("Orig" in item.shortName() for item in shapes)

    if has_orig:
        exist_orig = None

        for shape in shapes:
            shape_name = shape.shortName()

            if "Orig" in shape_name and exist_orig is None:
                exist_orig = shape_name
                pm.setAttr("{}.intermediateObject".format(shape_name), False)

            else:
                pm.delete(shape)

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

    # convert to pynode
    source_node = make_pynode(source)
    list_target_node = make_pynode(list_target)

    source_vtxs = source_node.vtx
    source_count = len(source_vtxs)

    MSelectionList = om.MSelectionList()

    # get point position of source
    MSelectionList.add(str(source_node))
    source_MDagPath = MSelectionList.getDagPath(0)
    source_MFnMesh = om.MFnMesh(source_MDagPath)
    MSelectionList.clear()

    list_pos_source_vtxs = source_MFnMesh.getPoints()

    # Copy temp_copy positions to each target
    for target in list_target_node:
        target_vtxs = target.vtx

        if len(target_vtxs) != source_count:
            raise ValueError(
                f"Vertex count mismatch between {source_node} and {target}"
            )

        # copy point
        MSelectionList.add(str(target))
        Target_MDagPath = MSelectionList.getDagPath(0)
        Target_MFnMesh = om.MFnMesh(Target_MDagPath)

        for i, point in enumerate(list_pos_source_vtxs):
            Target_MFnMesh.setPoint(i, list_pos_source_vtxs[i])

    return


def flip_curve(curve, flip_axis="x", world=True):
    """Flip Curve Position by reverse CV"""

    def odd_method():
        middle_index = cv_amount // 2

        list_first_block_pos = [
            pm.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
            for i in range(middle_index)
        ]
        value_middle = pm.xform(
            "{}.cv[{}]".format(curve_shape, middle_index), q=1, ws=ws, os=os, t=1
        )
        list_second_block_pos = [
            pm.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
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
            pm.xform("{}.cv[{}]".format(curve_shape, i), ws=ws, os=os, t=pos)

    def even_method():
        middle_index = cv_amount / 2

        list_first_block_pos = [
            pm.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
            for i in range(middle_index + 1)
        ]
        list_second_block_pos = [
            pm.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=ws, os=os, t=1)
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
            pm.xform("{}.cv[{}]".format(curve_shape, i), ws=ws, os=os, t=pos)

    def flip_position(position):
        if flip_axis == "x":
            return [position[0] * -1, position[1], position[2]]
        elif flip_axis == "y":
            return [position[0], position[1] * -1, position[2]]
        elif flip_axis == "z":
            return [position[0], position[1], position[2] * -1]

    # prepare
    curve_shape = pm.listRelatives(curve, c=1, s=1, typ="nurbsCurve")

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

    cv_amount = pm.getAttr(f"{curve_shape}.spans") + pm.getAttr(f"{curve_shape}.degree")

    # check is curve is odd
    if cv_amount % 2 != 0:
        odd_method()
    else:
        even_method()


def add_attribute_divider(object_name: str, name: str, divider_bar="--------"):
    """
    Add Blank Attribute With Divider Head Name

    object_name(str) : name of target object
    name(str) : name of head name
    divider_bar(str) : string text of divider
    """

    pm.addAttr(
        object_name,
        ln=name.replace(" ", ""),
        nn=divider_bar,
        at="enum",
        en="{}".format(name),
        k=1,
    )
    pm.setAttr(object_name + "." + name, cb=1, l=1)


def connect_matching_attributes(source, target, unit_conversion=None):
    if not pm.objExists(source) or not pm.objExists(target):
        return

    source_attrs = pm.listAttr(source, keyable=True, unlocked=True) or []
    target_attrs = pm.listAttr(target, keyable=True, unlocked=True) or []
    matching_attrs = set(source_attrs) & set(target_attrs)

    for attr in matching_attrs:
        source_attr = f"{source}.{attr}"
        target_attr = f"{target}.{attr}"

        if (
            pm.getAttr(source_attr, type=True) in ["double", "float"]
            and unit_conversion
        ):
            mult_node = pm.createNode("multiplyDivide", name=f"{source}_{attr}_convert")
            pm.setAttr(f"{mult_node}.input2X", unit_conversion)
            pm.connectAttr(source_attr, f"{mult_node}.input1X", force=True)
            source_attr = f"{mult_node}.outputX"

        if not pm.isConnected(source_attr, target_attr):
            pm.connectAttr(source_attr, target_attr, force=True)

    return None


def cut(path: str, attr: bool = False):
    """
    Use to cut path to get only short name for hierarchy or attribute

    path(str) : path , for example
                object : group|object > object,
                attribute : group|object.translateX > translateX
    attr(bool) : if True will return cut attribute , if False will return cut object

    """

    path = str(path)

    if attr == True:
        if "." in path:
            return path.split(".")[-1]
        else:
            return path
    elif attr == False:
        if "|" in path:
            return path.split("|")[-1]
        else:
            return path


def flip_keyword(input, ignore=False, L="L_", R="R_"):
    """Use to flip given keyworld"""

    # error handle
    if type(input) is not str:
        return input

    keywords = [L, R]

    if keywords[0] in input:
        return input.replace(keywords[0], keywords[1])
    elif keywords[1] in input:
        return input.replace(keywords[1], keywords[0])
    elif ignore is True:
        return input
    elif ignore is False:
        raise Exception(
            "Can not find the opposite side of {}, Please Make Sure the side keyword must be {} (Left) or {} (Right).".format(
                input, L, R
            )
        )


def get_curve_position(amount, curve):
    list_position = []
    list_poc = []
    curve_transform = curve
    curve_shape = pm.listRelatives(curve_transform, c=1, s=1, typ="nurbsCurve")[0]

    if "crv_" in curve_transform:
        main_name = curve_transform.replace("crv_", "")
    else:
        main_name = curve_transform

    for i in range(amount):
        node = pm.shadingNode(
            "pointOnCurveInfo",
            au=1,
            n="poc_" + main_name + "_tmp_" + str(i + 1).zfill(2),
        )

        if amount == 1:
            param = 0.5
        else:
            param = i * (1 / (amount - 1))

        pm.connectAttr(curve_shape + ".worldSpace[0]", node + ".inputCurve")
        pm.setAttr(node + ".parameter", param)
        pm.setAttr(node + ".turnOnPercentage", 1)

        list_poc.append(node)
        list_position.append(pm.getAttr(node + ".position"))

    pm.delete(list_poc)

    return list_position


def get_objects_in_set(set_name: str):
    """
    Return all object that in given sets name

    Args:
        set_name (str): The name of set
    """

    if mc.objExists(set_name) and mc.objectType(set_name) == "objectSet":
        return mc.sets(set_name, q=True) or []
    else:
        return []


def is_child_of(child_name, parent_name):
    """
    Checks if a given object is a child of another specified object.

    Parameters:
        child_name (str): The name of the potential child object.
        parent_name (str): The name of the potential parent object.

    Returns:
        bool: True if `child_name` is a child of `parent_name`, otherwise False.
    """
    if not pm.objExists(child_name):
        print(f"Object '{child_name}' does not exist.")
        return False

    if not pm.objExists(parent_name):
        print(f"Object '{parent_name}' does not exist.")
        return False

    # Get the full hierarchy of the parent
    all_descendants = (
        pm.listRelatives(parent_name, allDescendents=True, fullPath=True) or []
    )

    # Check if the child is in the hierarchy
    child_full_path = pm.ls(child_name, long=True)
    if child_full_path and child_full_path[0] in all_descendants:
        return True

    return False


def is_descendant_of(descendant_name, ancestor_name):
    """
    Checks if a given object is any descendant (child, grandchild, etc.) of another specified object.

    Parameters:
        descendant_name (str): The name of the potential descendant object.
        ancestor_name (str): The name of the potential ancestor object.

    Returns:
        bool: True if `descendant_name` is a descendant of `ancestor_name`, otherwise False.
    """
    if not pm.objExists(descendant_name):
        print(f"Object '{descendant_name}' does not exist.")
        return False

    if not pm.objExists(ancestor_name):
        print(f"Object '{ancestor_name}' does not exist.")
        return False

    # Get the full hierarchy of the ancestor
    all_descendants = (
        pm.listRelatives(ancestor_name, allDescendents=True, fullPath=True) or []
    )

    # Check if the descendant is in the hierarchy
    descendant_full_path = pm.ls(descendant_name, long=True)
    if descendant_full_path and descendant_full_path[0] in all_descendants:
        return True

    return False


def is_py_node(obj):
    """
    Detect whether input is a PyNode or a list/tuple of PyNodes.
    Returns:
        - If input is a single item: True/False
        - If input is list/tuple: list of True/False
    """
    if isinstance(obj, (list, tuple)):
        return [isinstance(o, pm.general.PyNode) for o in obj]
    else:
        return isinstance(obj, pm.general.PyNode)


def PyNode(node):
    if is_py_node(node):
        return node
    else:
        return pm.PyNode(node)


def make_pynode(obj):
    """
    Convert input into PyNode(s).

    Args:
        obj (str | pm.PyNode | list): Node name, PyNode, or list of them.

    Returns:
        pm.PyNode | list[pm.PyNode]: PyNode or list of PyNodes.
    """
    if isinstance(obj, (list, tuple)):
        return [pm.PyNode(o) if not isinstance(o, pm.PyNode) else o for o in obj]
    else:
        return pm.PyNode(obj) if not isinstance(obj, pm.PyNode) else obj


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
    if not pm.objExists(transform):
        return

    # Determine keyable state based on lock flag if not explicitly provided
    if k is None:
        k = 0 if l else 1

    def set_attrs(attrs):
        for attr in attrs:
            pm.setAttr(f"{transform}.{attr}", lock=l, keyable=k)

    if r:
        set_attrs(["rx", "ry", "rz"])
    if t:
        set_attrs(["tx", "ty", "tz"])
    if s:
        set_attrs(["sx", "sy", "sz"])
    if v:
        pm.setAttr(f"{transform}.v", lock=l, keyable=k)

    return None


def match_parent(target, parent):
    """Match transform and parent"""

    Transform.match_transform(target, parent)
    pm.parent(target, parent)

    return target


def rename_shape_proper(control):
    """Use to rename shape node properly name"""

    list_shape = pm.listRelatives(control, c=1, s=1, typ="nurbsCurve", f=1)
    for i, shape in enumerate(list_shape):
        pm.rename(shape, "{}Shape".format(cut(control)))


def set_rotate_order(list_target, rotate_order):
    if rotate_order == "xyz":
        key = 0
    elif rotate_order == "yzx":
        key = 1
    elif rotate_order == "zxy":
        key = 2
    elif rotate_order == "xzy":
        key = 3
    elif rotate_order == "yxz":
        key = 4
    elif rotate_order == "zyx":
        key = 5

    for target in list_target:
        pm.setAttr(target + ".rotateOrder", key)


def sort_by_type(list_target, typ="transform"):
    """
    Use to sort by type (anim_curve,transform,etc)

    only sort of list target (not include in children automatically)

    list_target(list) : target nodes.
    typ(str) : name of type ,anim_curve ,nurbsCurve, etc.

    """

    def get_anim_curve():
        def find_valid_controls(list_input=None):
            """
            Filter transform nodes according to these rules:

            1. Base name (namespace‑stripped) contains 'ctrl' **or** 'ctl'
            2. Base name does **NOT** start with 'ctrlBck'
            3. Base name does **NOT** contain 'crv'
            4. Node type is NOT 'joint'
            5. Node does **NOT** have a custom attribute called 'isGearGuide'
            6. Node has at least one non‑intermediate child of type 'nurbsCurve'
            7. None of the node's parents (at any level) have a base name of 'GRP_SHAPE'

            Args:
                list_input (Iterable[str | pm.PyNode] | None):
                    • List of nodes to test.
                    • If None or empty, uses the current selection;
                      if nothing selected, uses all transforms in the scene.

            Returns:
                list[pm.nt.Transform]: the nodes that pass every test (also selected in the viewport).
            """
            # Resolve the initial list of transforms to inspect
            if list_input:
                candidate_nodes = pm.ls(list_input, type="transform")
            else:
                candidate_nodes = pm.ls(type="transform")

            # get advanced skeleton sets

            if pm.objExists("ControlSet"):
                list_control_set = pm.sets("ControlSet", q=True)
            else:
                list_control_set = []

            valid_controls = []

            for node in candidate_nodes:
                base_name = node.name().split(":")[-1]  # strip all namespaces

                # Rule 1: must contain 'ctrl' or 'ctl' , ignore for advance skeleton case
                if node in list_control_set:
                    pass
                elif "ctrl" not in base_name.lower() and "ctl" not in base_name.lower():
                    continue

                # Rule 2: exclude names starting with 'ctrlBck' (case‑sensitive)
                if base_name.startswith("ctrlBck"):
                    continue

                # Rule 3: exclude names containing 'crv'
                if "crv" in base_name.lower():
                    continue

                # Rule 4: skip joints
                if node.nodeType() == "joint":
                    continue

                # Rule 5: skip nodes with the attr 'isGearGuide'
                if node.hasAttr("isGearGuide"):
                    continue

                # Rule 6: must have a nurbsCurve child
                shapes = node.getShapes(noIntermediate=True) or []
                if not any(shape.nodeType() == "nurbsCurve" for shape in shapes):
                    continue

                # Rule 7: no parent named 'GRP_SHAPE' (namespace‑agnostic)
                if any(
                    p.name().split(":")[-1] == "GRP_SHAPE" for p in node.getAllParents()
                ):
                    continue

                # Passed every test ➜ keep it
                valid_controls.append(node)

            # Select the results in the viewport
            # pm.select(valid_controls, replace=True)
            # pm.inViewMessage(
            #     amg="Found <hl>{}</hl> valid controls".format(len(valid_controls)),
            #     pos="midCenter", fade=True
            # )

            return valid_controls

        return find_valid_controls(list_target)

    def get_custom(input):
        list_selected_return = []
        list_type = pm.ls(typ=typ)

        for sel in list_target:
            if sel in list_type:
                list_selected_return.append(sel)

        # list_selected_return.reverse()
        # list_selected_return =

        return list_selected_return

    # variables for return selected
    if typ == "anim_curve":
        list_return = get_anim_curve()
    else:
        list_return = get_custom(typ)

    return list_return


def show_rotate_order(object):
    object_node = make_pynode(object)

    pm.setAttr("{}.rotateOrder".format(object_node), l=0, k=1)


def split_camel_pascal(text):
    """
    Converts camelCase or PascalCase strings into space-separated words.

    Examples:
        "controllerEditor" → "Controller Editor"
        "ControllerEditor" → "Controller Editor"

    Args:
        text (str): The camelCase or PascalCase string.

    Returns:
        str: A human-readable string with spaces between words.
    """
    if not text:
        return ""
    words = re.sub(r"(?<!^)(?=[A-Z])", " ", text)
    return words[0].upper() + words[1:]


def get_all_vertices(mesh_name):
    """
    Retrieves all vertices of a given mesh.

    Args:
        mesh_name (str): The name of the mesh.

    Returns:
        list: A list of PyNode objects representing the vertices of the mesh.
            Returns an empty list if the mesh does not exist.
    """
    if not pm.objExists(mesh_name):
        pm.warning(f"Mesh '{mesh_name}' does not exist.")
        return []

    mesh_node = pm.PyNode(mesh_name)
    # Using the .vtx attribute of a PyNode for meshes returns all vertices

    return mesh_node.vtx[:]


def to_camel_case(text):
    """
    Converts a space-separated string to camelCase.

    The first word is in lowercase and each subsequent word is capitalized.

    Args:
        text (str): The input string (e.g., "controller editor").

    Returns:
        str: The converted string in camelCase (e.g., "controllerEditor").
    """
    words = text.strip().split()
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def get_quick_selection_sets():
    """
    Queries the Maya scene for quick selection sets using PyMEL.

    This function excludes shading groups and default Maya sets.

    Returns:
        list: A list of PyMEL ObjectSet nodes that are quick selection sets.
    """
    # Get all nodes of type 'objectSet' as a Python set for efficient filtering
    all_sets = set(pm.ls(type="objectSet"))

    # Initialize an empty set to hold all sets that should be excluded
    sets_to_exclude = set()

    # Find all shading groups by finding sets connected to shading engines
    shading_engines = pm.ls(type="shadingEngine")
    for engine in shading_engines:
        # The .connections() method is a clean way to find connected nodes
        connected_sets = engine.connections(type="objectSet")
        sets_to_exclude.update(connected_sets)

    # Add default Maya sets that are not user-created selection sets
    try:
        sets_to_exclude.add(pm.PyNode("defaultObjectSet"))
        sets_to_exclude.add(pm.PyNode("defaultLightSet"))
    except pm.MayaNodeError:
        # These nodes might not exist in a completely empty scene
        pass

    # Calculate the difference to get only the quick selection sets
    quick_selection_sets = list(all_sets - sets_to_exclude)

    return quick_selection_sets


def get_vertex_data_position(mesh):
    """return dictionary of vertex id as keys , and its world position as values

    Return

    {0:(1,1,1,)}

    """

    if pm.objectType(mesh) == "mesh":
        shape = mesh
    else:
        shape = pm.listRelatives(mesh, c=1, s=1)[0]

    # dict target vtx pos
    vtx_count = pm.polyEvaluate(shape, vertex=True)
    dict_target_pos = {}

    for i in range(vtx_count):
        dict_target_pos[i] = pm.xform("{}.vtx[{}]".format(shape, i), q=1, t=1, ws=1)

    return dict_target_pos


def to_pascal_case(text):
    """
    Converts a space-separated string to PascalCase.

    Each word is capitalized and concatenated without spaces.

    Args:
        text (str): The input string (e.g., "controller editor").

    Returns:
        str: The converted string in PascalCase (e.g., "ControllerEditor").
    """
    words = text.strip().split()
    return "".join(word.capitalize() for word in words)


def to_abbreviation_case(text):
    # Start with the first character
    initials = text[0]

    # Add each uppercase character (start of new word)
    initials += "".join(c for c in text[1:] if c.isupper())

    # Lowercase if needed
    result = initials.lower()

    return result
