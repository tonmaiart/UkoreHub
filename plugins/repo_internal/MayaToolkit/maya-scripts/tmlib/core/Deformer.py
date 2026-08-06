import maya.cmds as cmds


def create_wrap_deformer(source_wrap, target_wrap):
    """
    Create wrap deformer and return deformer node and geo

    """
    # create wrap deformer
    cmds.select(source_wrap, target_wrap)
    list_wrap_deformers = cmds.ls(type="wrap")
    cmds.CreateWrap()
    list_new_wrap_deformers = cmds.ls(type="wrap")
    wrap_deformer = list(set(list_wrap_deformers) ^ set(list_new_wrap_deformers))[0]
    wrap_mesh = cmds.listConnections(
        "{}.basePoints[0]".format(wrap_deformer), d=False, s=True
    )

    return wrap_deformer, wrap_mesh


def create_shrink_wrap(mesh, target, **kwargs):
    """
    Check available kwargs with parameters below.
    """
    parameters = [
        ("projection", 2),
        ("closestIfNoIntersection", 1),
        ("reverse", 0),
        ("bidirectional", 1),
        ("boundingBoxCenter", 1),
        ("axisReference", 1),
        ("alongX", 0),
        ("alongY", 0),
        ("alongZ", 1),
        ("offset", 0),
        ("targetInflation", 0),
        ("targetSmoothLevel", 0),
        ("falloff", 0),
        ("falloffIterations", 1),
        ("shapePreservationEnable", 0),
        ("shapePreservationSteps", 1),
    ]

    target_shapes = cmds.listRelatives(
        target, f=True, shapes=True, type="mesh", ni=True
    )
    if not target_shapes:
        raise ValueError("The target supplied is not a mesh")
    target_shape = target_shapes[0]

    shrink_wrap = cmds.deformer(mesh, type="shrinkWrap")[0]

    for parameter, default in parameters:
        cmds.setAttr(shrink_wrap + "." + parameter, kwargs.get(parameter, default))

    connections = [
        ("worldMesh", "targetGeom"),
        ("continuity", "continuity"),
        ("smoothUVs", "smoothUVs"),
        ("keepBorder", "keepBorder"),
        ("boundaryRule", "boundaryRule"),
        ("keepHardEdge", "keepHardEdge"),
        ("propagateEdgeHardness", "propagateEdgeHardness"),
        ("keepMapBorders", "keepMapBorders"),
    ]

    for out_plug, in_plug in connections:
        cmds.connectAttr(target_shape + "." + out_plug, shrink_wrap + "." + in_plug)

    return shrink_wrap
