import re
import maya.cmds as cmds
import maya.api.OpenMaya as om


def natural_sort(input_list):
    """
    Sorts a list of strings in natural order.
    Example: ['apple1', 'apple12', 'apple2'] -> ['apple1', 'apple2', 'apple12']
    """

    def natural_key(s):
        return [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", s)
        ]

    return sorted(input_list, key=natural_key)


def get_children_mesh(sel):
    """Get Children mesh transforms"""
    list_return = []

    for node in cmds.listRelatives(sel, ad=True, type="transform", f=True):
        if cmds.listRelatives(node, shapes=True, children=True, type="mesh"):
            list_return.append(node)

    return list_return


def sort_by_type(list_target, typ="transform"):
    """
    Use to sort by type (animCurve, transform, nurbsCurve, etc)

    Only sort from given list_target (does NOT include children automatically)

    Args:
        list_target (list): target nodes
        typ (str): node type name (animCurve, transform, etc)
    """

    # ------------------------------
    # ANIM CURVE / CONTROL FILTER
    # ------------------------------
    def get_anim_curve():

        # Resolve candidate transforms
        if list_target:
            candidate_nodes = cmds.ls(list_target, type="transform") or []
        else:
            candidate_nodes = cmds.ls(type="transform") or []

        # Collect control sets (AdvancedSkeleton support)
        list_control_set = []

        # safer way to detect sets with wildcard
        control_sets = cmds.ls("*:ControlSet", type="objectSet") or []
        control_sets += cmds.ls("ControlSet", type="objectSet") or []
        control_sets += cmds.ls("*:FaceControlSet", type="objectSet") or []
        control_sets += cmds.ls("FaceControlSet", type="objectSet") or []

        for cset in control_sets:
            members = cmds.sets(cset, q=True) or []
            list_control_set.extend(members)

        valid_controls = []

        for node in candidate_nodes:

            # strip namespace
            base_name = node.split(":")[-1]

            # Valid if inside control set and has shape
            shapes = cmds.listRelatives(node, shapes=True) or []

            if node in list_control_set and shapes:
                valid_controls.append(node)
                continue

            # Valid if name contains ctrl / ctl
            lower_name = base_name.lower()
            if "ctrl" in lower_name or "ctl" in lower_name:
                valid_controls.append(node)
                continue

        return valid_controls

    # ------------------------------
    # GENERIC TYPE FILTER
    # ------------------------------
    def get_custom():
        list_selected_return = []

        list_type = cmds.ls(type=typ) or []

        for sel in list_target or []:
            if sel in list_type:
                list_selected_return.append(sel)

        return list_selected_return

    # ------------------------------
    # MAIN LOGIC
    # ------------------------------
    if typ.lower() in ["anim_curve", "animcurve"]:
        list_return = get_anim_curve()
    else:
        list_return = get_custom()

    print("list return len :", len(list_return))
    return list_return


def get_quick_selection_sets():
    """
    Queries the Maya scene for quick selection sets using PyMEL.

    This function excludes shading groups and default Maya sets.

    Returns:
        list: A list of PyMEL ObjectSet nodes that are quick selection sets.
    """
    # Get all nodes of type 'objectSet' as a Python set for efficient filtering
    all_sets = set(cmds.ls(type="objectSet"))

    # Initialize an empty set to hold all sets that should be excluded
    sets_to_exclude = set()

    # Find all shading groups by finding sets connected to shading engines
    shading_engines = cmds.ls(type="shadingEngine")
    for engine in shading_engines:
        # The .connections() method is a clean way to find connected nodes
        connected_sets = engine.connections(type="objectSet")
        sets_to_exclude.update(connected_sets)

    # Add default Maya sets that are not user-created selection sets
    try:
        sets_to_exclude.add(cmds.PyNode("defaultObjectSet"))
        sets_to_exclude.add(cmds.PyNode("defaultLightSet"))
    except cmds.MayaNodeError:
        # These nodes might not exist in a completely empty scene
        pass

    # Calculate the difference to get only the quick selection sets
    quick_selection_sets = list(all_sets - sets_to_exclude)

    return quick_selection_sets


def get_both_side(list_name, sides=True):
    results = set()

    for name in list_name:
        if sides:
            results.add(name)

        if "_L" in name:
            results.add(name.replace("_L", "_R"))
        elif "_R" in name:
            results.add(name.replace("_R", "_L"))

    return sorted(list(results))


def is_child_of(child_name, parent_name):
    """
    Checks if a given object is a child of another specified object.

    Parameters:
        child_name (str): The name of the potential child object.
        parent_name (str): The name of the potential parent object.

    Returns:
        bool: True if `child_name` is a child of `parent_name`, otherwise False.
    """
    if not cmds.objExists(child_name):
        print(f"Object '{child_name}' does not exist.")
        return False

    if not cmds.objExists(parent_name):
        print(f"Object '{parent_name}' does not exist.")
        return False

    # Get the full hierarchy of the parent
    all_descendants = (
        cmds.listRelatives(parent_name, allDescendents=True, fullPath=True) or []
    )

    # Check if the child is in the hierarchy
    child_full_path = cmds.ls(child_name, long=True)
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
    if not cmds.objExists(descendant_name):
        print(f"Object '{descendant_name}' does not exist.")
        return False

    if not cmds.objExists(ancestor_name):
        print(f"Object '{ancestor_name}' does not exist.")
        return False

    # Get the full hierarchy of the ancestor
    all_descendants = (
        cmds.listRelatives(ancestor_name, allDescendents=True, fullPath=True) or []
    )

    # Check if the descendant is in the hierarchy
    descendant_full_path = cmds.ls(descendant_name, long=True)
    if descendant_full_path and descendant_full_path[0] in all_descendants:
        return True

    return False


def find_flip_object(sel, left="_L", right="_R", get_dict=False):
    result = []
    result_dict = {}
    if not sel:
        return None

    for obj in sel:
        # Flip from L → R
        if obj.endswith(left):
            flipped = obj[: -len(left)] + right

        # Flip from R → L
        elif obj.endswith(right):
            flipped = obj[: -len(right)] + left

        else:
            # No side keyword → ignore
            continue

        # Check if counterpart exists
        if cmds.objExists(flipped):
            result.append(flipped)
            result_dict[obj] = flipped

    if get_dict:
        return result_dict
    else:
        return result


def get_objects_in_set(set_name: str):
    """
    Return all object that in given sets name

    Args:
        set_name (str): The name of set
    """

    if cmds.objExists(set_name) and cmds.objectType(set_name) == "objectSet":
        return cmds.sets(set_name, q=True) or []
    else:
        return []


def get_all_vertices(mesh_name):
    """
    Retrieves all vertices of a given mesh.

    Args:
        mesh_name (str): The name of the mesh.

    Returns:
        list: A list of PyNode objects representing the vertices of the mesh.
            Returns an empty list if the mesh does not exist.
    """
    if not cmds.objExists(mesh_name):
        cmds.warning(f"Mesh '{mesh_name}' does not exist.")
        return []

    mesh_node = cmds.PyNode(mesh_name)
    # Using the .vtx attribute of a PyNode for meshes returns all vertices

    return mesh_node.vtx[:]


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
