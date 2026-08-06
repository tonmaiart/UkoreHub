import maya.cmds as cmds
from tmlib.core import Scene, SkinWeight, Utility,Selection


def add_multi_skin_cluster():
    list_selection = cmds.ls(sl=1)
    list_joint = []
    mesh = None

    for sel in list_selection:
        if cmds.objectType(sel, isa="joint"):
            list_joint.append(sel)
        else:
            mesh = sel

    SkinWeight.add_multi_skin_cluster(mesh=mesh, list_joint=list_joint)

    cmds.inViewMessage(amg="<hl>Multi Skin Added</hl>", pos="botCenter", fade=True)


def fast_copy_weight():
    """Copies skin weights
    - If all selection is mesh will copy weight from first selection to all others.
    - If first or last selection is group, it's will copy to all of children mesh in that group.
    - If both selection is group, Will copy by match by pair of name.
    """

    selection = cmds.ls(selection=True)

    if len(selection) < 2:
        cmds.error("Selection required as least two items.")
        return

    source_sel = selection[0]
    target_sels = selection[1:]

    source_geos = []
    target_geos = []
    list_pair_copy = []

    is_multiple_source = False

    # ====================
    # Detecting Source
    # ====================

    # case: mesh is source (single mesh)
    if cmds.listRelatives(source_sel, s=True, children=True):
        is_multiple_source = False
        source_geos.append(source_sel)

    # case: group is source (multiple mesh, match by naming)
    elif not cmds.listRelatives(source_sel, shapes=True, children=True):
        is_multiple_source = True
        
        source_geos += Selection.get_children_mesh(source_sel)
    else:
        cmds.error("First Selection object type invalid , required group or mesh only.")

    print("Multiple Source Copy : ", is_multiple_source)

    # ====================
    # Detecting Targets
    # ====================

    # case : match by name
    for tgt_sel in target_sels:
        if cmds.listRelatives(tgt_sel, s=True, children=True):
            target_geos.append(tgt_sel)
        elif not cmds.listRelatives(tgt_sel, shapes=True, children=True):
            target_geos += Selection.get_children_mesh(tgt_sel)
        else:
            cmds.error(
                "object type invalid {}, required group or mesh only.".format(tgt_sel)
            )

    # ==========================
    # Matching Source > Targets
    # ==========================

    # copy match by name
    if not is_multiple_source:
        for tgt in target_geos:
            list_pair_copy.append([source_geos[0], tgt])

    # copy source to all
    elif is_multiple_source:
        for src in source_geos:
            for tgt in target_geos:
                if Utility.cut(src, hierarchy=True, namespace=True) == Utility.cut(
                    tgt, hierarchy=True, namespace=True
                ):
                    list_pair_copy.append([src, tgt])

    # =================================
    # Confirm Dialog for Match by name
    # =================================
    print("# List Copy Target")
    for each in list_pair_copy:
        print(
            "- {} > {}".format(
                Utility.cut(each[0], hierarchy=True, namespace=False),
                Utility.cut(each[1], hierarchy=True, namespace=False),
                each[1],
            )
        )

    # copy weight
    for each in list_pair_copy:
        SkinWeight.copy_weight(each[0], each[1])

    cmds.inViewMessage(
        amg="<hl>Copy Skin Weight Success!</hl>",
        pos="botCenter",
        fade=True,
    )

    cmds.select(selection)


def create_joint_set():
    """
    Create or reuse a set of joints influencing the selected mesh or skinCluster.
    The set is named "<skinClusterName>_joints".
    Selects the set node itself (not the members) and shows a message.
    """
    selected = cmds.ls(selection=True)

    if not selected:
        cmds.inViewMessage(amg="No object selected.", pos="botCenter", fade=True)
        return

    # create iterate
    list_set_name = []

    for sel in selected:
        if cmds.objectType(sel, isa="skinCluster"):
            skin_cluster = sel
        else:
            skin_cluster = SkinWeight.get_skin_cluster_node(sel)

        if not skin_cluster:
            cmds.inViewMessage(
                amg="No <hl>skinCluster</hl> found on selected object.",
                pos="botCenter",
                fade=True,
            )
            return

        skin_cluster = str(skin_cluster)
        print("Detect Skin Cluster {} : {} ".format(sel, skin_cluster))

        joints = cmds.skinCluster(skin_cluster, query=True, influence=True) or []

        if not joints:
            cmds.inViewMessage(
                amg="No <hl>influencing joints</hl> found.", pos="botCenter", fade=True
            )
            return

        set_name = "{}_joints".format(skin_cluster)

        if cmds.objExists(set_name):
            cmds.delete(set_name)

        cmds.sets(joints, name=set_name)

        # Select only the set node, not its members
        cmds.select(clear=True)
        cmds.select(set_name, replace=True, noExpand=True)

        cmds.inViewMessage(
            amg="Created joint set <hl>{}</hl>.".format(set_name),
            pos="botCenter",
            fade=True,
        )

        list_set_name.append(set_name)

    return list_set_name
