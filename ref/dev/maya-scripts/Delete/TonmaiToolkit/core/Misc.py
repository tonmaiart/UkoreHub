import inspect, re, importlib, math, configparser
import maya.cmds as cmds
from TonmaiToolkit.module.PySide import QtWidgets, QtCore, QtGui
import maya.cmds as mc
import pymel.core as pm
import os
from TonmaiToolkit import config
import json

from TonmaiToolkit.core import Utility, Transform
import pymel.core as pm
import maya.cmds as mc
import maya.api.OpenMaya as om


def deleteControl(control):
    control_name = "{}WorkspaceControl".format(control)

    if cmds.workspaceControl(control_name, q=1, exists=1):
        try:
            cmds.deleteUI(control_name, control=True)
        except:
            pass

def undoable_jump_point(func):
    def wrapper(*args, **kwargs):
        # Enable undo before the function execution
        undo = pm.undoInfo(openChunk=True,chunkName="JumpPoint")

        try:
            # Execute the function
            result = func(*args, **kwargs)
        finally:
            # Ensure undo is closed after the function execution
            pm.undoInfo(closeChunk=True)

        return result

    return wrapper

def undoable(func):
    def wrapper(*args, **kwargs):
        # Enable undo before the function execution
        undo = pm.undoInfo(openChunk=True)

        try:
            # Execute the function
            result = func(*args, **kwargs)
        finally:
            # Ensure undo is closed after the function execution
            pm.undoInfo(closeChunk=True)

        return result

    return wrapper


def check_neg(input):
    list_input = []

    if type(input) is list:
        list_input = input
    elif type(input) is str:
        list_input.append(input)
    else:
        raise Exception("Invalid Input")

    for item in list_input:
        if "-" in item:
            raise Exception("Must Be Absolute Axis , {}".format(item))


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())


def cname(tag_name=None, name=None, type=None, position=None):
    if tag_name is None:
        new_name = "{}_{}".format(name, type)
    else:
        new_name = "{}_{}_{}".format(tag_name, name, type)

    return new_name


def finalize_visibility(local_rig_name):
    # lock and hide all transform
    list_joint = pm.listRelatives(local_rig_name, ad=1, typ="joint", f=1)
    if list_joint:
        for obj in list_joint:
            pm.setAttr(obj + ".drawStyle", 2)

    list_locator_shape = pm.listRelatives(local_rig_name, ad=1, typ="locator", f=1)
    if list_locator_shape:
        for obj in list_locator_shape:
            pm.setAttr(obj + ".v", 0)

    list_follicle_shape = pm.listRelatives(local_rig_name, ad=1, typ="follicle", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            pm.setAttr(obj + ".v", 0)

    list_follicle_shape = pm.listRelatives(
        local_rig_name, ad=1, typ="nurbsSurface", f=1
    )
    if list_follicle_shape:
        for obj in list_follicle_shape:
            pm.setAttr(pm.listRelatives(obj, p=1)[0] + ".v", 0)

    list_follicle_shape = pm.listRelatives(
        local_rig_name, ad=1, typ="arcLengthDimension", f=1
    )
    if list_follicle_shape:
        for obj in list_follicle_shape:
            pm.setAttr(obj + ".v", 0)

    list_follicle_shape = pm.listRelatives(local_rig_name, ad=1, typ="ikHandle", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            pm.setAttr(obj + ".v", 0)


def get_exist_axis(list_axis):
    """
    Identifies the axes from {'x', 'y', 'z'} that are present
    in the input arguments.

    Args:
        args (list): A list of strings, typically from sys.argv,
                     representing the command-line arguments.

    Returns:
        str: A string containing the existing axes, or an empty string
             if no axes are present.
    """

    ref_axis = ["x","y","z"]

    for axis in list_axis:
        axis_main = axis.replace("-","")
        ref_axis.remove(axis_main)
    
    return ref_axis[0]



def get_rgb_from_index(index):
    """Return rgb color by given index"""
    """
    Get the RGB color corresponding to a Maya index color.

    :param index: Index color value (integer between 0 and 31).
    :return: A tuple of (R, G, B) values in the range [0, 1].
    :raises ValueError: If the index is not between 0 and 31.
    """
    index_to_rgb = {
        0: (0.0, 0.0, 0.0),
        1: (0.247, 0.247, 0.247),
        2: (0.498, 0.498, 0.498),
        3: (0.608, 0.0, 0.157),
        4: (0.0, 0.016, 0.373),
        5: (0.0, 0.0, 0.561),
        6: (0.0, 0.275, 0.094),
        7: (0.145, 0.0, 0.263),
        8: (0.780, 0.0, 0.780),
        9: (0.537, 0.278, 0.2),
        10: (0.243, 0.133, 0.122),
        11: (0.600, 0.145, 0.0),
        12: (0.392, 0.216, 0.0),
        13: (0.263, 0.275, 0.0),
        14: (0.0, 0.467, 0.0),
        15: (0.0, 0.275, 0.392),
        16: (0.0, 0.18, 0.537),
        17: (0.0, 0.0, 0.612),
        18: (0.216, 0.0, 0.6),
        19: (0.475, 0.0, 0.537),
        20: (0.6, 0.0, 0.325),
        21: (0.627, 0.275, 0.216),
        22: (0.62, 0.51, 0.216),
        23: (0.0, 0.58, 0.0),
        24: (0.255, 0.6, 0.459),
        25: (0.0, 0.6, 0.6),
        26: (0.0, 0.4, 0.6),
        27: (0.325, 0.475, 0.6),
        28: (0.537, 0.537, 0.6),
        29: (0.6, 0.6, 0.6),
        30: (0.784, 0.784, 0.784),
        31: (1.0, 1.0, 1.0),
    }

    if index not in index_to_rgb:
        raise ValueError("Index must be an integer between 0 and 31.")

    return index_to_rgb[index]


def get_single_axis_enum():
    return ["X", "Y", "Z", "-X", "-Y", "-Z"]


def get_single_axis_enum_pos():
    return ["X", "Y", "Z"]


def get_triple_axis_enum():
    return ["xyz", "xzy", "yxz", "yzx", "zyx", "zxy"]


def get_tuple_axis(direction: str):
    # Define a mapping from input string to the corresponding tuple
    direction_map = {
        "x": (1, 0, 0),
        "y": (0, 1, 0),
        "z": (0, 0, 1),
        "-x": (-1, 0, 0),
        "-y": (0, -1, 0),
        "-z": (0, 0, -1),
        # Add more mappings here based on your needs
    }

    # Return the tuple corresponding to the input, or None if the input is not valid
    return direction_map.get(direction, None)


def convert_single_axis_enum(index):
    return ["x", "y", "z", "-x", "-y", "-z"][index]


def convert_single_axis_enum_pos(index):
    return ["x", "y", "z"][index]


def convert_triple_axis_enum(index):
    return ["xyz", "xzy", "yxz", "yzx", "zyx", "zxy"][index]


def del_neg(text):
    return text.replace("-", "").replace(" ", "")


def extract_vertices(vertex_range):
    # Use regex to parse the vertex string
    match = re.match(r"(.+)\.vtx\[(\d+):(\d+)\]", vertex_range)
    if not match:
        raise ValueError("Invalid vertex range format.")

    base_name = match.group(1)
    start_idx = int(match.group(2))
    end_idx = int(match.group(3))

    # Generate the list of individual vertices
    return [f"{base_name}.vtx[{i}]" for i in range(start_idx, end_idx + 1)]


def get_axis_double3(input, minusValue=True, invert=False):
    list_return = [0, 0, 0]
    list_axis_ref = ["x", "y", "z"]
    list_axis_ref_minus = ["-x", "-y", "-z"]

    dict_axis = {
        "x": (1, 0, 0),
        "y": (0, 1, 0),
        "z": (0, 0, 1),
        "-x": (-1, 0, 0),
        "-y": (0, -1, 0),
        "-z": (0, 0, -1),
    }

    if input not in dict_axis.keys():
        raise Exception("Invalid Input")

    output = dict_axis[input]

    if invert:
        output = [value * -1 for value in output]

    return output


def set_layout_disabled(layout, value=False):
    """Disable or enable all child widgets in the given layout."""
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if widget:
            widget.setEnabled(value)


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


"""
Collection of function that deal with polishing rig
"""


def clean_mgear_mult_matrix():
    """Update all of mgear mult matrix node in scene to maya default mult matrix"""

    mgear_nodes = mc.ls(type="mgear_mulMatrix")

    if not mgear_nodes:
        print("Your scene already clean : Not found any mgear_mulMatrix nodes.")
        return

    # main operation
    for node in mgear_nodes:
        node_mult = mc.createNode("multMatrix")
        node_decomp = mc.createNode("decomposeMatrix")

        joint = mc.listConnections("{}.matrixA".format(node), s=True)[0]
        ctl = mc.listConnections("{}.matrixB".format(node), s=True)[0]

        mc.connectAttr("{}.worldMatrix".format(ctl), "{}.matrixIn[0]".format(node_mult))
        mc.connectAttr(
            "{}.parentInverseMatrix".format(joint), "{}.matrixIn[1]".format(node_mult)
        )

        mc.connectAttr(
            "{}.matrixSum".format(node_mult), "{}.inputMatrix".format(node_decomp)
        )

        mc.connectAttr(
            "{}.outputTranslate".format(node_decomp), "{}.t".format(joint), f=1
        )
        mc.connectAttr("{}.outputRotate".format(node_decomp), "{}.r".format(joint), f=1)

        # delete node
        mc.delete(node)

    print("Update : mgear_mulMatrix {} node.".format(len(mgear_nodes)))


def scale_to_matrix(scale=(1, 1, 1)):
    sx, sy, sz = scale
    matrix_list = [sx, 0, 0, 0, 0, sy, 0, 0, 0, 0, sz, 0, 0, 0, 0, 1]
    return om.MMatrix(matrix_list)


def get_scale_from_matrix(matrix):
    """
    Accepts a 4x4 matrix (nested or flat) and returns scale (sx, sy, sz).
    Requires maya.api.OpenMaya (API 2.0)
    """
    # Flatten if nested
    if isinstance(matrix[0], list):
        matrix = [item for row in matrix for item in row]

    # Convert to MMatrix and extract scale
    mtx = om.MMatrix(matrix)
    mtx_transform = om.MTransformationMatrix(mtx)
    return mtx_transform.getScale(om.MSpace.kTransform)


def clean_mgear_matrix_constraint():
    """
    Use to clean mgear matrix constraint by change to maya node
    """

    # get all mgear nodes
    mgear_nodes = mc.ls(type="mgear_matrixConstraint")

    if not mgear_nodes:
        print("Your scene already clean : Not found any mgear_matrixConstraint nodes.")
        return

    # main operation
    for node in mgear_nodes:
        if not mc.objExists(node):
            continue

        # find joint and control is exists , if not continue
        joint_node = mc.listConnections("{}.translate".format(node), d=True)
        ctl_node = mc.listConnections("{}.driverMatrix".format(node), s=True)

        if not joint_node or not ctl_node:
            continue

        # find joint and control
        joint = joint_node[0]
        ctl = ctl_node[0]

        """ connect scale attribute"""
        node_mult_scl = mc.createNode("multMatrix")
        node_decomp_scl = mc.createNode("decomposeMatrix")

        # set matrix 0 : world matrix
        mc.connectAttr(
            "{}.worldMatrix".format(ctl), "{}.matrixIn[0]".format(node_mult_scl)
        )

        # set matrix 1 : parent inverse matrix's joint
        mc.connectAttr(
            "{}.parentInverseMatrix".format(joint),
            "{}.matrixIn[1]".format(node_mult_scl),
        )

        # set matrix 2 : scale offset (optional)
        m_scale = scale_to_matrix(mc.xform(ctl, q=1, ws=1, s=1))
        mc.setAttr("{}.matrixIn[2]".format(node_mult_scl), m_scale, typ="matrix")

        # connect sum
        mc.connectAttr(
            "{}.matrixSum".format(node_mult_scl),
            "{}.inputMatrix".format(node_decomp_scl),
        )

        # connect scale
        mc.connectAttr(
            "{}.outputScale".format(node_decomp_scl), "{}.s".format(joint), f=1
        )

        """ connect other attribute"""
        node_mult = mc.createNode("multMatrix")
        node_decomp = mc.createNode("decomposeMatrix")

        # set matrix 0 : world matrix
        mc.connectAttr("{}.worldMatrix".format(ctl), "{}.matrixIn[0]".format(node_mult))

        # set matrix 1 : parent inverse matrix's joint
        mc.connectAttr(
            "{}.parentInverseMatrix".format(joint), "{}.matrixIn[1]".format(node_mult)
        )

        # connect sum
        mc.connectAttr(
            "{}.matrixSum".format(node_mult), "{}.inputMatrix".format(node_decomp)
        )

        # connect all, ignore rotation
        mc.connectAttr(
            "{}.outputTranslate".format(node_decomp), "{}.t".format(joint), f=1
        )
        mc.connectAttr(
            "{}.outputShear".format(node_decomp), "{}.shear".format(joint), f=1
        )

        """ connect rotation"""
        node_mult_rot = mc.createNode("multMatrix")
        node_decomp_rot = mc.createNode("decomposeMatrix")

        mc.connectAttr(
            "{}.matrixSum".format(node_mult), "{}.matrixIn[0]".format(node_mult_rot)
        )
        get_matrix = om.MMatrix(mc.getAttr("{}.matrixSum".format(node_mult)))
        matrix = get_matrix.inverse()

        mc.setAttr("{}.matrixIn[1]".format(node_mult_rot), matrix, typ="matrix")

        mc.connectAttr(
            "{}.matrixSum".format(node_mult_rot),
            "{}.inputMatrix".format(node_decomp_rot),
        )

        mc.connectAttr(
            "{}.outputRotate".format(node_decomp_rot), "{}.r".format(joint), f=1
        )

        mc.delete(node)

    print("Update : mgear_matrixConstraint nodes {} node.".format(len(mgear_nodes)))


@undoable
def show_channel_box_history():
    # get all dependency nodes
    list_all_node = mc.ls()

    for node in list_all_node:
        plug = "{}.ihi".format(node)
        if mc.objExists(plug):
            try:
                mc.setAttr(plug, True)
            except:
                pass

    selection = pm.ls(sl=1)
    pm.select(selection, r=1)

    mc.inViewMessage(
        amg="<hl>Show Channel Box History</hl>", pos="botCenter", fade=True
    )


@undoable
def hide_channel_box_history():
    # get all dependency nodes
    list_all_node = mc.ls()

    for node in list_all_node:
        plug = "{}.ihi".format(node)
        if mc.objExists(plug):
            try:
                mc.setAttr(plug, False)
            except:
                pass

    selection = pm.ls(sl=1)
    pm.select(selection, r=1)

    mc.inViewMessage(
        amg="<hl>Hide Channel Box History</hl>", pos="botCenter", fade=True
    )


def lock_anim_grp():
    list_grp_ctrl = []

    for ctl in Utility.sort_by_type(pm.ls(), typ="anim_curve"):
        parent = pm.listRelatives(ctl, p=1, typ="transform", f=1)

        if not parent:
            continue
        elif pm.objectType(parent[0], isa="joint"):
            continue
        elif pm.objectType(parent[0], isa="transform"):
            try:
                Utility.lock_attribute(
                    transform=parent[0], r=1, s=1, t=1, v=1, l=1, k=0
                )
            except:
                pass

            list_grp_ctrl.append(parent)

    pm.select(list_grp_ctrl, r=1)


def unlock_anim_grp():
    list_grp_ctrl = []

    for ctl in Utility.sort_by_type(pm.ls(), typ="anim_curve"):
        if not pm.objExists(ctl):
            continue

        parent = pm.listRelatives(ctl, p=1, typ="transform", f=1)

        if parent is None:
            continue
        elif pm.objectType(parent[0], isa="joint"):
            continue
        elif pm.objectType(parent[0], isa="transform"):
            try:
                Utility.lock_attribute(
                    transform=parent[0], r=1, s=1, t=1, v=1, l=0, k=1
                )
            except:
                pass

            list_grp_ctrl.append(parent)

    pm.select(list_grp_ctrl, r=1)


def remove_all_namespaces():
    # Remove all namespaces
    # Set root namespace
    pm.namespace(setNamespace=":")

    # Collect all namespaces except for the Maya built ins.
    all_namespaces = [
        x
        for x in pm.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        if x != "UI" and x != "shared"
    ]

    if all_namespaces:
        # Sort by hierarchy, deepest first.
        all_namespaces.sort(key=len, reverse=True)
        for namespace in all_namespaces:
            # When a deep namespace is removed, it also removes the root. So check here to see if these still exist.
            if pm.namespace(exists=namespace) is True:
                pm.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)

    mc.inViewMessage(
        amg="</hl>Remove all namespaces. {}</hl>", pos="botCenter", fade=True
    )


def import_all_references():
    """Import all references and remove all namespaces (even nested ones)."""

    # Import all references
    while True:
        references = pm.listReferences()

        if references:
            for ref in references:
                if ref.isLoaded():
                    try:
                        ref.importContents()
                    except Exception as e:
                        pm.warning(
                            f"Could not import reference {ref.refNode.name()}: {e}"
                        )
        else:
            break


def clear_controller_animation():
    """Clear animation of controller and reset transform it"""
    current_frame = cmds.currentTime(query=True)

    pm.currentTime(0)

    all_controller = Utility.sort_by_type(
        list_target=pm.ls(typ="transform"), typ="anim_curve"
    )

    for ctrl in all_controller:
        pm.cutKey(ctrl)
        Transform.reset_transform(ctrl)

    pm.currentTime(current_frame)


def clean_up_scene():
    """Do all stuff to clear the scene"""

    import_all_references()
    remove_all_namespaces()
    clean_mgear_mult_matrix()
    clean_mgear_matrix_constraint()
    clear_controller_animation()
    hide_channel_box_history()
    lock_anim_grp()

    mc.inViewMessage(amg="</hl>Clean Up Scene. {}</hl>", pos="botCenter", fade=True)
