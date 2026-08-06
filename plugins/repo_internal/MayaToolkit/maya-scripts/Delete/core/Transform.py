import math

from TonmaiToolkit.core import Utility

import maya.api.OpenMaya as om
import maya.cmds as mc
import pymel.core as pm

def get_nearest_mesh_parameter(mesh, obj):

    """Return (faceIndex, u, v) of the closest point from object to mesh."""



    # create nodes

    node_closest = pm.createNode("closestPointOnMesh")

    decomp = pm.createNode("decomposeMatrix")



    # connect nodes

    pm.connectAttr(mesh + ".outMesh", node_closest + ".inMesh")

    pm.connectAttr(mesh + ".worldMatrix[0]", node_closest + ".inputMatrix")

    pm.connectAttr(obj + ".worldMatrix[0]", decomp + ".inputMatrix")

    pm.connectAttr(decomp + ".outputTranslate", node_closest + ".inPosition")



    # query values

    face_id = pm.getAttr(node_closest + ".closestFaceIndex")

    u = pm.getAttr(node_closest + ".result.parameterU")

    v = pm.getAttr(node_closest + ".result.parameterV")



    # cleanup

    pm.delete(node_closest, decomp)



    return u, v

def get_distance_two(*args, world=True):
    """Return Distance between given two object"""

    list_object = []

    for arg in args:
        if type(arg) is str:
            list_object.append(arg)
        elif type(arg) is tuple:
            list_object += list(arg)
        elif type(arg) is list:
            list_object += arg
        else:
            raise Exception(arg + ": get distance function error input")

    distance = 0.0
    for i in range(1, len(list_object)):
        # query coordinates
        if world is True:
            ws = 1
            os = 0
        elif world is False:
            ws = 0
            os = 1

        posA = pm.xform(list_object[i - 1], ws=ws, os=os, t=1, q=1)
        posB = pm.xform(list_object[i], ws=ws, os=os, t=1, q=1)

        distance += math.sqrt(
            ((posA[0] - posB[0]) ** 2)
            + ((posA[1] - posB[1]) ** 2)
            + ((posA[2] - posB[2]) ** 2)
        )

    return distance


def get_linear_position_division(posA, posB, division=1):
    """Return world position that locate between given position"""

    list_position = []

    # get unit offset
    v_posA = om.MVector(posA)
    v_posB = om.MVector(posB)

    v_offset = v_posB - v_posA
    v_offset = v_offset / (division + 1)

    for i in range(division):
        v_result = v_posA + (v_offset * (i + 1))
        list_position.append(list(v_result))

    return list_position


def get_nearest_polygon_parameter(mesh, object):
    # create node
    node_closest_point = pm.createNode("closestPointOnMesh")
    decomp = pm.createNode("decomposeMatrix")

    # create node
    shape = pm.listRelatives(mesh, c=1, s=1)[0]

    pm.connectAttr(shape + ".worldMesh[0]", node_closest_point + ".inMesh")
    pm.connectAttr(shape + ".worldMatrix[0]", node_closest_point + ".inputMatrix")

    # connect object position
    pm.connectAttr(object + ".worldMatrix[0]", decomp + ".inputMatrix")
    pm.connectAttr(decomp + ".outputTranslate", node_closest_point + ".inPosition")

    # get parameter
    paramU = pm.getAttr(node_closest_point + ".parameterU")
    paramV = pm.getAttr(node_closest_point + ".parameterV")

    # delete tmp node
    pm.delete(node_closest_point, decomp)

    return paramU, paramV


def get_nearest_nurbs_curve_parameter(curve, object):
    # create node
    npc = pm.createNode("nearestPointOnCurve")
    decomp = pm.createNode("decomposeMatrix")

    # create node
    pm.connectAttr(curve + ".worldSpace[0]", npc + ".inputCurve")
    pm.connectAttr(object + ".worldMatrix[0]", decomp + ".inputMatrix")
    pm.connectAttr(decomp + ".outputTranslate", npc + ".inPosition")

    # get parameter
    param = pm.getAttr(npc + ".parameter")

    # delete tmp node
    pm.delete(npc, decomp)

    return param


def get_nearest_nurbs_surface_parameter(curve, object):
    # create node
    node_closest = pm.createNode("closestPointOnSurface")
    decomp = pm.createNode("decomposeMatrix")

    # connect node
    pm.connectAttr(curve + ".worldSpace[0]", node_closest + ".inputSurface")
    pm.connectAttr(object + ".worldMatrix[0]", decomp + ".inputMatrix")
    pm.connectAttr(decomp + ".outputTranslate", node_closest + ".inPosition")

    # get parameter
    param = [
        pm.getAttr(node_closest + ".parameterU"),
        pm.getAttr(node_closest + ".parameterV"),
    ]

    # delete tmp node
    pm.delete(node_closest, decomp)

    return param


def get_offset_matrix(m_target, m_current):
    """
    Return matrix value that use to offset to get the target position

    """
    m_current = om.MMatrix(m_current)
    m_target = om.MMatrix(m_target)
    m_offset = m_current.inverse() * m_target

    return m_offset


def get_world_matrix(obj):
    """Return world matrix of given obj"""

    list_target = om.MSelectionList()
    list_target.add(obj)
    matrix = list_target.getDagPath(0).inclusiveMatrix()

    return matrix


def match_transform(target_object, match_object, pos=True, rot=True, scale=True):
    """
    Match the world-space transforms of one Maya object to another using PyMEL.

    Args:
        target_object (str or pm.PyNode): Target object to receive the transform.
        match_object (str or pm.PyNode): Source object to copy the transform from.
        pos (bool): If True, match position.
        rot (bool): If True, match rotation.
        scale (bool): If True, match scale.

    Raises:
        RuntimeError: If either of the specified objects does not exist.

    """
    # Get PyNodes for both
    target = pm.PyNode(target_object)
    source = pm.PyNode(match_object)

    # Match world-space position
    if pos:
        target.setTranslation(source.getTranslation(space="world"), space="world")

    # Match world-space rotation
    if rot:
        target.setRotation(source.getRotation(space="world"), space="world")

    # Match scale (relative)
    if scale:
        target.scale.set(source.scale.get())


def reset_transform(obj, pos=True, rot=True, scl=True):
    """
    Resets the transform attributes of a given object in Maya.

    Parameters:
        obj (str): The name of the object whose transforms will be reset.
        pos (bool): If True, reset translation attributes (tx, ty, tz) to 0. Default is True.
        rot (bool): If True, reset rotation attributes (rx, ry, rz) to 0. Default is True.
        scl (bool): If True, reset scale attributes (sx, sy, sz) to 1. Default is True.

    Returns:
        None
    """
    # Define attribute lists
    translate_attrs = ["tx", "ty", "tz"]
    rotate_attrs = ["rx", "ry", "rz"]
    scale_attrs = ["sx", "sy", "sz"]

    attrs_to_reset = []
    if pos:
        attrs_to_reset += translate_attrs
    if rot:
        attrs_to_reset += rotate_attrs
    if scl:
        attrs_to_reset += scale_attrs

    for attr in attrs_to_reset:
        default_value = 1 if attr in scale_attrs else 0

        if pm.getAttr(f"{obj}.{attr}", se=True):
            pm.setAttr(f"{obj}.{attr}", default_value)

    return None


def rotate_to_grid(obj: str):
    """
    Snaps the world rotation of the given object to the nearest multiple of 90 degrees on each axis.

    Parameters:
        obj (str): The name of the object whose rotation will be snapped.

    Example:
        If an object's world rotation is [87.5, 91.2, 182], it will be snapped to [90, 90, 180].

    Returns:
        None
    """

    def snap_angle(angle):
        return round(angle / 90.0) * 90

    rotation = pm.xform(obj, query=True, worldSpace=True, rotation=True)

    if rotation:
        snapped_rotation = [snap_angle(rot) for rot in rotation]
        pm.xform(obj, worldSpace=True, rotation=snapped_rotation)


def match_cvs(source, target):
    # Get shapes
    source_shapes = pm.listRelatives(source, shapes=True, fullPath=True) or []
    target_shapes = pm.listRelatives(target, shapes=True, fullPath=True) or []

    # Match shape count by index
    for i in range(min(len(source_shapes), len(target_shapes))):
        src_shape = source_shapes[i]
        tgt_shape = target_shapes[i]

        # Get CVs
        src_cvs = pm.ls(f"{src_shape}.cv[*]", flatten=True)
        tgt_cvs = pm.ls(f"{tgt_shape}.cv[*]", flatten=True)

        # Match CV count
        for j in range(min(len(src_cvs), len(tgt_cvs))):
            pos = pm.xform(tgt_cvs[j], q=1, os=True, t=1)
            pm.xform(src_cvs[j], os=True, t=pos)


def transform_to_vertex(target_object, list_vertex):
    # CREATE SKIN CLUSTER --------------------
    pm.select(list_vertex, r=1)
    cluster_handle = pm.cluster()[1]

    # UN-PARENT --------------------
    list_child = pm.listRelatives(target_object, c=1, typ="transform")

    if list_child:
        pm.parent(list_child, w=1)

    pm.matchTransform(target_object, cluster_handle, pos=1)

    if list_child:
        pm.parent(list_child, target_object)

    # DELETE TEMP CLUSTER --------------------
    pm.delete(cluster_handle)


def transform_to_curve_cv(curve: str, object: str, cv_index: int, typ="ep"):
    """Snap given object to cv curve positions"""
    position = pm.xform("{}.{}[{}]".format(curve, typ, cv_index), ws=1, t=1, q=1)
    pm.xform(object, ws=1, t=position)


def transform_to_between_object(parent1, parent2, target, percentage=0.5):
    if percentage > 1 or percentage < 0:
        raise Exception("percentage input must be in range 1 [0.0-1.0]")

    tmp_pcn = pm.pointConstraint(parent1, parent2, target, mo=0)

    pm.setAttr("{}.{}W0".format(tmp_pcn, parent1), 1 - percentage)
    pm.setAttr("{}.{}W1".format(tmp_pcn, parent2), percentage)

    pm.delete(tmp_pcn)


def get_position_from_curve_param(curve, param, turn_on_percentage=False):
    print(curve, param)
    curve_shape = pm.listRelatives(curve, c=1, s=1, typ="nurbsCurve")[0]
    tmp_grp = pm.group(em=1)

    poc = pm.createNode("pointOnCurveInfo")
    pm.setAttr("{}.turnOnPercentage".format(poc), turn_on_percentage)

    pm.connectAttr(curve_shape + ".worldSpace[0]", poc + ".inputCurve")
    pm.setAttr(poc + ".parameter", param)

    position = pm.getAttr("{}.position".format(poc))
    pm.delete(poc)
    pm.delete(tmp_grp)

    return position


def transform_to_surface_parameter(
    source, target, u: float, v: float, percentage: bool = False, snap: str = "parent"
) -> None:
    """
    Snap a target Transform to a NURBS surface at a given U/V.

    Args:
        source (pm.nt.NurbsSurface): The NURBS surface shape.
        target (pm.nt.Transform): The transform to snap.
        u (float): U parameter.
        v (float): V parameter.
        percentage (bool): If True, interpret U/V as 0-1 percentage.
        snap (str): "parent" to match position & rotation, "point" for position only.

    Raises:
        TypeError: If source is not a pm.nt.NurbsSurface or target is not a pm.nt.Transform.
    """

    if not Utility.is_py_node(source):
        source = pm.PyNode(source)

    if not Utility.is_py_node(target):
        target = pm.PyNode(target)

    if source.nodeType() != "nurbsSurface":
        shape = pm.listRelatives(source, c=1, s=1, typ="nurbsSurface")

        if shape:
            source = shape[0]
        else:
            raise Exception("Source have not nurbsSurface")

    # Create utility nodes
    poc = pm.createNode("pointOnSurfaceInfo")
    fmatrix = pm.createNode("fourByFourMatrix")
    decomp = pm.createNode("decomposeMatrix")

    # Connect surface and params
    source.worldSpace[0] >> poc.inputSurface
    poc.parameterU.set(u)
    poc.parameterV.set(v)
    poc.turnOnPercentage.set(percentage)

    # Fill the matrix with surface vectors and position
    poc.positionX >> fmatrix.in30
    poc.positionY >> fmatrix.in31
    poc.positionZ >> fmatrix.in32
    poc.normalX >> fmatrix.in00
    poc.normalY >> fmatrix.in01
    poc.normalZ >> fmatrix.in02
    poc.tangentUx >> fmatrix.in10
    poc.tangentUy >> fmatrix.in11
    poc.tangentUz >> fmatrix.in12
    poc.tangentVx >> fmatrix.in20
    poc.tangentVy >> fmatrix.in21
    poc.tangentVz >> fmatrix.in22

    fmatrix.output >> decomp.inputMatrix

    # Get the results
    translate = decomp.outputTranslate.get()
    rotate = decomp.outputRotate.get()

    # Apply the transformation
    target.translate.set(translate)
    if snap == "parent":
        target.rotate.set(rotate)

    # Clean up utility nodes
    pm.delete([poc, fmatrix, decomp])


def transform_curve(
    amount,
    typ,
    os,
    axis=None,
):
    selection = pm.ls(sl=1)

    x = y = z = 0

    if axis == "x":
        x = 1
    elif axis == "y":
        y = 1
    elif axis == "z":
        z = 1

    # filter shape
    for obj in selection:
        list_shape = pm.listRelatives(obj, c=1, s=1, f=1)
        if list_shape:
            list_curve = []

            for shape in list_shape:
                if pm.objectType(shape) == "nurbsCurve":
                    list_curve.append(shape)

            for curve in list_curve:
                pm.select(curve + ".cv[*]", replace=True)

                if os:
                    ws = 0
                else:
                    ws = 1

                if typ == "move":
                    pm.move(amount, y=y, x=x, z=z, os=os, ws=ws, r=1)
                elif typ == "rotate":
                    pm.rotate(amount, y=y, x=x, z=z, os=os, ws=ws, r=1)
                elif typ == "scale":
                    if not os:
                        pivot = pm.xform(obj, ws=1, q=1, sp=1)
                        pm.scale(1 + amount, 1 + amount, 1 + amount, r=1, p=pivot)
                    else:
                        pm.scale(
                            1 + amount,
                            1 + amount,
                            1 + amount,
                            r=1,
                        )

    pm.select(selection, r=1)


def get_bounding_box_max(object):
    """
    Return max bounding box of object
    """

    # Get the bounding box of the source object
    source_bbox = pm.exactWorldBoundingBox(object)
    source_width = source_bbox[3] - source_bbox[0]
    source_height = source_bbox[4] - source_bbox[1]
    source_depth = source_bbox[5] - source_bbox[2]

    max_size = max(source_width, source_height, source_depth)

    return max_size


def match_bounding_box(source, target, typ="max"):
    """
    Match Source to Target bounding box

    """
    if not pm.objExists(source) or not pm.objExists(target):
        raise ValueError("Source or target object does not exist")

    # Get the bounding box of the source object
    source_bbox = pm.exactWorldBoundingBox(source)
    source_width = source_bbox[3] - source_bbox[0]
    source_height = source_bbox[4] - source_bbox[1]
    source_depth = source_bbox[5] - source_bbox[2]

    # Get the bounding box of the target object
    target_bbox = pm.exactWorldBoundingBox(target)
    target_width = target_bbox[3] - target_bbox[0]
    target_height = target_bbox[4] - target_bbox[1]
    target_depth = target_bbox[5] - target_bbox[2]

    # Calculate the scale factors
    scale_x = target_width / source_width if source_width != 0 else 1
    scale_y = target_height / source_height if source_height != 0 else 1
    scale_z = target_depth / source_depth if source_depth != 0 else 1

    # max type
    if typ == "max":
        max_size = max(scale_x, scale_y, scale_z)

        scale_x = scale_y = scale_z = max_size

    elif typ == "None":
        pass

    # Apply the scale factors to the source object
    pm.xform(source, scale=(scale_x, scale_y, scale_z), r=1, os=True)
