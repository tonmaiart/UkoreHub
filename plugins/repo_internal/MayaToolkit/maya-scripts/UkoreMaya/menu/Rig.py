import maya.api.OpenMaya as om
import maya.cmds as cmds

from tmlib.core import Scene, Utility, Transform, Create, Connection


def create_follicle_pin():
    """
    Create follicle at selected 4 point vertex, this method is use wrap deformer to avoid uv update problems. if mesh is too high-poly might cause performance issue.

    """
    selection = cmds.ls(sl=1, fl=1)

    # check input
    if len(selection) != 4:
        raise Exception(
            "Must Select Vertices for 4 vertex ,orderly : top left,top right,bot right,bot left"
        )

    for obj in selection:
        if ".vtx" not in str(obj):
            raise Exception(
                "Must Select Vertices for 4 vertex ,orderly : top left,top right,bot right,bot left"
            )

    # create nurbs plane
    plane = cmds.nurbsPlane(d=1, ch=0, ax=(0, 1, 0), n="pin_plane")[0]
    grp_tmp = cmds.group(em=1)
    Transform.transform_to_vertex(
        target_object=str(grp_tmp), list_vertex=[str(vtx) for vtx in selection]
    )

    # start operation
    flc = Connection.pin_to_surface(
        list_pin=[grp_tmp], surface=plane, output_parent=None, name="pin_plane_flc"
    )[0]

    cmds.delete(grp_tmp)

    # snap position
    dict_target_snap = {
        str(selection[0]): "{}.cv[0][1]".format(plane),
        str(selection[1]): "{}.cv[1][1]".format(plane),
        str(selection[2]): "{}.cv[0][0]".format(plane),
        str(selection[3]): "{}.cv[1][0]".format(plane),
    }

    for vtx in dict_target_snap.keys():
        target = dict_target_snap[vtx]

        position = cmds.xform(vtx, ws=1, t=1, q=1)
        cmds.xform(target, ws=1, t=position)

    # add wrap deformer
    target_obj = str(selection[0]).split(".")[0]
    cmds.select(str(plane), target_obj, r=True)

    cmds.CreateWrap()

    wrap = cmds.ls(typ="wrap")[-1]

    cmds.setAttr("{}.exclusiveBind".format(wrap), True)
    cmds.setAttr("{}.falloffMode".format(wrap), 1)

    # get mesh base
    mesh_base = cmds.listConnections("{}.basePoints[0]".format(wrap), s=1)[0]

    # organize group
    grp_data = cmds.group(n="pin_data_grp", em=1)
    cmds.setAttr("{}.inheritsTransform".format(grp_data), 0)
    cmds.parent(grp_data, flc)
    cmds.setAttr("{}.v".format(grp_data), 0)

    cmds.setAttr("{}.inheritsTransform".format(plane), 0)
    cmds.parent(plane, grp_data)
    cmds.setAttr("{}.v".format(plane), 0)

    cmds.setAttr("{}.inheritsTransform".format(mesh_base), 0)
    cmds.parent(mesh_base, grp_data)
    cmds.setAttr("{}.v".format(mesh_base), 0)

    # selection
    cmds.select(flc)


def create_wrap_pin():
    """
    Create follicle at selected 4 point vertex, this method is use wrap deformer to avoid uv update problems. if mesh is too high-poly might cause performance issue.

    """
    selection = cmds.ls(sl=1, fl=1)

    # create wrap mesh
    mesh = selection[0].split(".")[0]

    # start operation
    flc = Connection.pin_to_surface(
        list_pin=[grp_tmp], surface=plane, output_parent=None, name="pin_plane_flc"
    )[0]

    cmds.delete(grp_tmp)

    # snap position
    dict_target_snap = {
        str(selection[0]): "{}.cv[0][1]".format(plane),
        str(selection[1]): "{}.cv[1][1]".format(plane),
        str(selection[2]): "{}.cv[0][0]".format(plane),
        str(selection[3]): "{}.cv[1][0]".format(plane),
    }

    for vtx in dict_target_snap.keys():
        target = dict_target_snap[vtx]

        position = cmds.xform(vtx, ws=1, t=1, q=1)
        cmds.xform(target, ws=1, t=position)

    # add wrap deformer
    target_obj = str(selection[0]).split(".")[0]
    cmds.select(str(plane), target_obj, r=True)

    cmds.CreateWrap()

    wrap = cmds.ls(typ="wrap")[-1]

    cmds.setAttr("{}.exclusiveBind".format(wrap), True)
    cmds.setAttr("{}.falloffMode".format(wrap), 1)

    # get mesh base
    mesh_base = cmds.listConnections("{}.basePoints[0]".format(wrap), s=1)[0]

    # organize group
    grp_data = cmds.group(n="pin_data_grp", em=1)
    cmds.setAttr("{}.inheritsTransform".format(grp_data), 0)
    cmds.parent(grp_data, flc)
    cmds.setAttr("{}.v".format(grp_data), 0)

    cmds.setAttr("{}.inheritsTransform".format(plane), 0)
    cmds.parent(plane, grp_data)
    cmds.setAttr("{}.v".format(plane), 0)

    cmds.setAttr("{}.inheritsTransform".format(mesh_base), 0)
    cmds.parent(mesh_base, grp_data)
    cmds.setAttr("{}.v".format(mesh_base), 0)

    # selection
    cmds.select(flc)


def match_transform():
    selection = cmds.ls(sl=1)

    object, target = selection

    parent = cmds.listRelatives(object, p=1)
    cmds.parent(object, target)

    # reset attributes
    for i, attr in enumerate(["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]):
        if i > 5:
            value = 1
        else:
            value = 0

        cmds.setAttr("{}.{}".format(object, attr), value, k=1, l=0)

    if parent:
        cmds.parent(object, parent[0])
    else:
        cmds.parent(object, w=1)

    cmds.select(selection)


def freeze_group(grp_name="Grp", prefix="Grp"):
    """
    Create freeze group to selected object to maintain transform.
    """
    # Add all selected objects to lists
    selection_list = om.MSelectionList()
    offset_list = om.MSelectionList()
    offset_paths = []
    dag_paths = []
    user_selected = cmds.ls(sl=True)

    for i, sel in enumerate(user_selected):
        selection_list.add(str(sel))
        dag_paths.append(selection_list.getDagPath(i))

        # Create group
        offset_grp = cmds.createNode("transform")
        offset_list.add(str(offset_grp))
        offset_paths.append(offset_list.getDagPath(i))

    # Iterate through each item in the selection list
    for i in range(selection_list.length()):
        print(dag_paths[i].fullPathName())

        # Match group matrix to the target
        cmds.xform(
            offset_paths[i].fullPathName(),
            ws=True,
            m=cmds.xform(dag_paths[i].fullPathName(), ws=True, q=True, m=True),
        )

        # Parent group to hierarchy if not top-level
        if dag_paths[i].fullPathName().count("|") != 1:
            parent_transform = cmds.listRelatives(
                dag_paths[i].fullPathName(),
                parent=True,
                type="transform",
                fullPath=True,
            )[0]
            cmds.parent(offset_paths[i].fullPathName(), parent_transform)

        # Move target under the new group
        cmds.parent(dag_paths[i].fullPathName(), offset_paths[i].fullPathName())

        # rename group
        if prefix:
            cmds.rename(
                offset_paths[i].fullPathName(),
                grp_name + "_" + dag_paths[i].fullPathName().split("|")[-1],
            )
        elif not prefix:
            cmds.rename(
                offset_paths[i].fullPathName(),
                dag_paths[i].fullPathName().split("|")[-1] + "_" + grp_name,
            )

    # reselect
    cmds.select(cl=1)
    for i in range(len(offset_paths)):
        cmds.select(offset_paths[i].fullPathName(), add=1)

    # display
    cmds.inViewMessage(amg=" Create offset Group ", pos="midCenterBot", fade=1, fst=800)


def auto_constraint(typ="parent"):
    """
    match selected control to selected object, input "single" for one object and "multiple" for many object.
    how to use
    select joint and control (select control for last)

    Args:
    typ : Constraint , "none" by default , input "orient","scale","parent","point"
    """

    # verify selection
    list_control = []
    list_joint = cmds.ls(sl=1, tr=1)
    dict_auto_parent = {}

    for joint in list_joint:
        # create control
        if "|" in joint:
            control_name = joint.split("|")[-1]
        else:
            control_name = joint

        control_name = "{}_ctrl".format(control_name)

        control = cmds.circle(ch=0, n=control_name)[0]
        list_control.append(control)

        # snap control position
        cmds.matchTransform(control, joint)

        # optional constraint:
        if typ == "point":
            cmds.pointConstraint(control, joint)
        elif typ == "orient":
            cmds.orientConstraint(control, joint)
        elif typ == "scale":
            cmds.scaleConstraint(control, joint)
        elif typ == "parent":
            cmds.parentConstraint(control, joint)
        elif typ == "all":
            cmds.parentConstraint(control, joint)
            cmds.scaleConstraint(control, joint)

        joint_parent = cmds.listRelatives(joint, p=1)
        if joint_parent:
            dict_auto_parent[control] = "{}_ctrl".format(Utility.cut(joint_parent[0]))
        else:
            dict_auto_parent[control] = None

    # auto chain
    for control in dict_auto_parent:
        parent = dict_auto_parent[control]
        if parent and cmds.objExists(parent):
            cmds.parent(control, parent)

    cmds.select(list_control, r=1)


def auto_connection(typ="all"):
    def check_attribute_value():
        def check_individual(sel):
            for axis in list_axis:
                # translate and rotate
                for attr in "tr":
                    value = cmds.getAttr("{}.{}{}".format(sel, attr, axis))

                    if value != 0:
                        list_invalid.append(sel)
                        return

                # scale
                attr = "s"
                value = cmds.getAttr("{}.{}{}".format(sel, attr, axis))
                if value != 1:
                    list_invalid.append(sel)
                    return

        for sel in selection:
            check_individual(sel)

    def create_control():
        list_control = []
        dict_auto_parent = {}

        # create control and match transform
        for sel in selection:
            control = cmds.circle(ch=0, n=sel + "_ctrl")[0]
            list_control.append(str(control))

            cmds.matchTransform(control, sel)

            # save parent
            parent_path = cmds.listRelatives(sel, p=1, f=1)

            if parent_path:
                dict_auto_parent[control] = parent_path[0].split("|")[::-1]
            else:
                dict_auto_parent[control] = None

        # auto chain
        for control in dict_auto_parent:
            list_parent = dict_auto_parent[control]

            if list_parent is None:
                continue
            else:
                for parent in list_parent:
                    ctl_parent = parent + "_ctrl"

                    if parent and cmds.objExists(ctl_parent):
                        cmds.parent(control, ctl_parent)
                        break

        # freeze group
        Create.create_freeze_group(list_control)

        # connection
        for i, control in enumerate(list_control):
            for attr in list_attr:
                try:
                    cmds.connectAttr(
                        "{}{}".format(control, attr), "{}{}".format(selection[i], attr)
                    )
                except:
                    raise Exception("Cannot Connect attribute.")

        cmds.select(list_control, r=1)

    def is_continue():
        if list_invalid:
            output = cmds.confirmDialog(
                m="Transform attribute is not clean, {}. Continue will snap.".format(
                    list_invalid
                ),
                button=["Freeze Group", "Yes", "No"],
                defaultButton="Freeze Group",
                cancelButton="No",
                dismissString="No",
            )

            if output == "Freeze Group":
                Create.create_freeze_group(cmds.ls(sl=1, typ="joint"))
                return True
            if output == "Yes":
                return True
            else:
                return False
        else:
            return True

    # get type
    if typ == "all":
        list_attr = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz"]
    elif typ == "translate":
        list_attr = [".tx", ".ty", ".tz"]
    elif typ == "rotate":
        list_attr = [".rx", ".ry", ".rz"]
    elif typ == "scale":
        list_attr = [".sx", ".sy", ".sz"]

    list_axis = "xyz"
    list_invalid = []
    selection = cmds.ls(sl=1)

    check_attribute_value()

    if not is_continue():
        return

    print("Runned")

    create_control()

    cmds.inViewMessage(amg="Quick Controller Local", pos="botCenter", fade=True)


def constraint_matrix():
    selection = cmds.ls(sl=1)

    parenter = selection[0]
    target = selection[1]

    cmds.group()


def copy_shape():
    """
    Copies the shape of the first selected mesh (source) to one or more target meshes.
    Maintains the user's original selection and displays a status message.

    Usage:
        1. Select the source mesh first.
        2. Then select one or more target meshes.
        3. Run this function.
    """

    original_selection = cmds.ls(sl=True)

    if len(original_selection) < 2:
        raise ValueError("Please select one source mesh and one or more target meshes.")

    # variables
    source = original_selection[0]
    targets = original_selection[1:]

    # loading screen
    cmds.progressWindow(
        title="Copying Shape",
        progress=100,
        status="Copying vertex.",
        isInterruptable=True,
    )

    Utility.morph_shape(source=source, list_target=targets)

    cmds.progressWindow(endProgress=1)

    # Maintain the original selection
    cmds.select(original_selection)

    # Final status message
    cmds.inViewMessage(amg="Copy Shape Complete!", pos="botCenter", fade=True)