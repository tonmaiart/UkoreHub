import maya.cmds as cmds

from tmlib.core import Create

def toggle_vis(objects):
    filter_objects = []
    # prepare objects
    for obj in objects:
        for prefix in ["", "*:"]:
            obj = "{}{}".format(prefix, obj)
            if cmds.objExists(obj):
                filter_objects.append(obj)

    # if ANY is hidden, turn ALL on. Otherwise turn ALL off.
    any_hidden = any(cmds.getAttr(i + ".v") == 0 for i in filter_objects)
    new_v = True if any_hidden else False

    for obj in filter_objects:
        cmds.setAttr(obj + ".v", new_v)



def create_vector_visualized(start_point, end_point, name="vector", size=0.1, color_index=13):
    """
    Use for visualized vector in maya
    """

    loc_start = cmds.spaceLocator(n=name + "_start")[0]
    loc_start_shape = cmds.listRelatives(loc_start, children=True, shapes=True,f=1)[0]
    cmds.setAttr("{}.localScale".format(loc_start), size, size, size, typ="double3")
    cmds.setAttr("{}.overrideEnabled".format(loc_start_shape), True)
    cmds.setAttr("{}.overrideColor".format(loc_start_shape), color_index)
    cmds.xform(loc_start, ws=True, t=start_point)

    loc_end = cmds.spaceLocator(n=name + "_end")[0]
    loc_end_shape = cmds.listRelatives(loc_end, children=True, shapes=True,f=1)[0]
    cmds.setAttr("{}.localScale".format(loc_end), size, size, size, typ="double3")
    cmds.setAttr("{}.overrideEnabled".format(loc_end_shape), True)
    cmds.setAttr("{}.overrideColor".format(loc_end_shape), color_index)
    cmds.xform(loc_end, ws=True, t=end_point)
    cmds.parent(loc_end, loc_start)
    cmds.setAttr("{}.visibility".format(loc_end), False)

    Create.create_line_annotate([loc_start, loc_end], name=name, color_index=color_index)

def create_point_visualized(point,name="point",size=0.1,color_index=13):
    """
    Use for visualized vector in maya
    """

    loc_start = cmds.spaceLocator(n=name + "_point")[0]
    loc_start_shape = cmds.listRelatives(loc_start, children=True, shapes=True,f=1)[0]
    cmds.setAttr("{}.localScale".format(loc_start), size, size, size, typ="double3")
    cmds.setAttr("{}.overrideEnabled".format(loc_start_shape), True)
    cmds.setAttr("{}.overrideColor".format(loc_start_shape), color_index)
    cmds.xform(loc_start, ws=True, t=point)