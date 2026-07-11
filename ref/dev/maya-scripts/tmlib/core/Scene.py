import maya.cmds as cmds
import maya.mel as mel
import os
import maya.api.OpenMaya as om

from tmlib.core import Utility, Transform, Selection


def import_all_references():
    """Import all references and remove namespaces (including nested ones)."""

    while True:
        ref_nodes = cmds.ls(type="reference") or []

        # Remove internal shared node
        ref_nodes = [r for r in ref_nodes if r != "sharedReferenceNode"]

        if not ref_nodes:
            break

        imported_any = False

        for ref_node in ref_nodes:
            try:
                # Skip if not loaded
                if not cmds.referenceQuery(ref_node, isLoaded=True):
                    continue

                # Get file path
                ref_file = cmds.referenceQuery(ref_node, filename=True)

                # Import reference
                cmds.file(ref_file, importReference=True)

                print(f"Imported: {ref_file}")
                imported_any = True

                # Important: break to refresh reference list
                break

            except Exception as e:
                cmds.warning(f"Could not import {ref_node}: {e}")

        if not imported_any:
            break

    # 🔥 Remove all namespaces except UI & shared
    namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []

    for ns in sorted(namespaces, reverse=True):
        if ns in ["UI", "shared"]:
            continue
        try:
            cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
        except:
            pass

    print("All references imported and namespaces cleaned.")


def remove_all_namespaces():
    # Remove all namespaces
    # Set root namespace
    cmds.namespace(setNamespace=":")

    # Collect all namespaces except for the Maya built ins.
    all_namespaces = [
        x
        for x in cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        if x != "UI" and x != "shared"
    ]

    if all_namespaces:
        # Sort by hierarchy, deepest first.
        all_namespaces.sort(key=len, reverse=True)
        for namespace in all_namespaces:
            # When a deep namespace is removed, it also removes the root. So check here to see if these still exist.
            if cmds.namespace(exists=namespace) is True:
                cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)

    cmds.inViewMessage(
        amg="</hl>Remove all namespaces. {}</hl>", pos="botCenter", fade=True
    )


def clear_controller_animation():
    """Clear animation of controller and reset transform it"""
    current_frame = cmds.currentTime(query=True)

    cmds.currentTime(0)

    all_controller = Selection.sort_by_type(
        list_target=cmds.ls(typ="transform"), typ="anim_curve"
    )

    for ctrl in all_controller:
        cmds.cutKey(ctrl)
        # Transform.reset_transform(ctrl)

    cmds.currentTime(current_frame)


def delete_blue_pencil():
    targets = cmds.ls("bluePencil*")
    cmds.delete(targets)


def delete_ng_node():
    targets = cmds.ls("ngSkinToolsData*")
    cmds.delete(targets)


def delete_user_selection_sets():
    targets = cmds.ls(sets=True)
    filter_targets = []

    for t in targets:
        if cmds.nodeType(t) == "objectSet":
            filter_targets.append(t)

    list_default = ["defaultLightSet", "defaultObjectSet"]

    for each in list_default:
        filter_targets.remove(each)

    print("filter target:", filter_targets)
    for t in filter_targets:
        if "Ffd" in t:
            continue
        print("deleting : ", t)
        try:
            cmds.delete(t)
        except:
            pass


def delete_dwpicker_node():
    if cmds.objExists("_dwpicker_data"):
        cmds.delete("_dwpicker_data")


def delete_unused_influences():
    cmds.select(cmds.ls("*_Geo"))

    if not cmds.ls(sl=1):
        return
    else:
        mel.eval("removeUnusedInfluences()")


def delete_unused_node():
    mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')


def show_channel_box_history():
    # get all dependency nodes
    list_all_node = cmds.ls()

    for node in list_all_node:
        plug = "{}.ihi".format(node)
        if cmds.objExists(plug):
            try:
                cmds.setAttr(plug, True)
            except:
                pass

    selection = cmds.ls(sl=1)
    cmds.select(selection, r=1)

    cmds.inViewMessage(
        amg="<hl>Show Channel Box History</hl>", pos="botCenter", fade=True
    )


def hide_channel_box_history():
    # get all dependency nodes
    list_all_node = cmds.ls()

    for node in list_all_node:
        plug = "{}.ihi".format(node)
        if cmds.objExists(plug):
            try:
                cmds.setAttr(plug, False)
            except:
                pass

    selection = cmds.ls(sl=1)
    cmds.select(selection, r=1)

    cmds.inViewMessage(
        amg="<hl>Hide Channel Box History</hl>", pos="botCenter", fade=True
    )


def clean_mgear_matrix_constraint():
    """
    Use to clean mgear matrix constraint by change to maya node
    """

    # get all mgear nodes
    mgear_nodes = cmds.ls(type="mgear_matrixConstraint")

    if not mgear_nodes:
        print("Your scene already clean : Not found any mgear_matrixConstraint nodes.")
        return

    # main operation
    for node in mgear_nodes:
        if not cmds.objExists(node):
            continue

        # find joint and control is exists , if not continue
        joint_node = cmds.listConnections("{}.translate".format(node), d=True)
        ctl_node = cmds.listConnections("{}.driverMatrix".format(node), s=True)

        if not joint_node or not ctl_node:
            continue

        # find joint and control
        joint = joint_node[0]
        ctl = ctl_node[0]

        """ connect scale attribute"""
        node_mult_scl = cmds.createNode("multMatrix")
        node_decomp_scl = cmds.createNode("decomposeMatrix")

        # set matrix 0 : world matrix
        cmds.connectAttr(
            "{}.worldMatrix".format(ctl), "{}.matrixIn[0]".format(node_mult_scl)
        )

        # set matrix 1 : parent inverse matrix's joint
        cmds.connectAttr(
            "{}.parentInverseMatrix".format(joint),
            "{}.matrixIn[1]".format(node_mult_scl),
        )

        # set matrix 2 : scale offset (optional)
        m_scale = scale_to_matrix(cmds.xform(ctl, q=1, ws=1, s=1))
        cmds.setAttr("{}.matrixIn[2]".format(node_mult_scl), m_scale, typ="matrix")

        # connect sum
        cmds.connectAttr(
            "{}.matrixSum".format(node_mult_scl),
            "{}.inputMatrix".format(node_decomp_scl),
        )

        # connect scale
        cmds.connectAttr(
            "{}.outputScale".format(node_decomp_scl), "{}.s".format(joint), f=1
        )

        """ connect other attribute"""
        node_mult = cmds.createNode("multMatrix")
        node_decomp = cmds.createNode("decomposeMatrix")

        # set matrix 0 : world matrix
        cmds.connectAttr(
            "{}.worldMatrix".format(ctl), "{}.matrixIn[0]".format(node_mult)
        )

        # set matrix 1 : parent inverse matrix's joint
        cmds.connectAttr(
            "{}.parentInverseMatrix".format(joint), "{}.matrixIn[1]".format(node_mult)
        )

        # connect sum
        cmds.connectAttr(
            "{}.matrixSum".format(node_mult), "{}.inputMatrix".format(node_decomp)
        )

        # connect all, ignore rotation
        cmds.connectAttr(
            "{}.outputTranslate".format(node_decomp), "{}.t".format(joint), f=1
        )
        cmds.connectAttr(
            "{}.outputShear".format(node_decomp), "{}.shear".format(joint), f=1
        )

        """ connect rotation"""
        node_mult_rot = cmds.createNode("multMatrix")
        node_decomp_rot = cmds.createNode("decomposeMatrix")

        cmds.connectAttr(
            "{}.matrixSum".format(node_mult), "{}.matrixIn[0]".format(node_mult_rot)
        )
        get_matrix = om.MMatrix(cmds.getAttr("{}.matrixSum".format(node_mult)))
        matrix = get_matrix.inverse()

        cmds.setAttr("{}.matrixIn[1]".format(node_mult_rot), matrix, typ="matrix")

        cmds.connectAttr(
            "{}.matrixSum".format(node_mult_rot),
            "{}.inputMatrix".format(node_decomp_rot),
        )

        cmds.connectAttr(
            "{}.outputRotate".format(node_decomp_rot), "{}.r".format(joint), f=1
        )

        cmds.delete(node)

    print("Update : mgear_matrixConstraint nodes {} node.".format(len(mgear_nodes)))


def clean_mgear_mult_matrix():
    """Update all of mgear mult matrix node in scene to maya default mult matrix"""

    mgear_nodes = cmds.ls(type="mgear_mulMatrix")

    if not mgear_nodes:
        print("Your scene already clean : Not found any mgear_mulMatrix nodes.")
        return

    # main operation
    for node in mgear_nodes:
        node_mult = cmds.createNode("multMatrix")
        node_decomp = cmds.createNode("decomposeMatrix")

        joint = cmds.listConnections("{}.matrixA".format(node), s=True)[0]
        ctl = cmds.listConnections("{}.matrixB".format(node), s=True)[0]

        cmds.connectAttr(
            "{}.worldMatrix".format(ctl), "{}.matrixIn[0]".format(node_mult)
        )
        cmds.connectAttr(
            "{}.parentInverseMatrix".format(joint), "{}.matrixIn[1]".format(node_mult)
        )

        cmds.connectAttr(
            "{}.matrixSum".format(node_mult), "{}.inputMatrix".format(node_decomp)
        )

        cmds.connectAttr(
            "{}.outputTranslate".format(node_decomp), "{}.t".format(joint), f=1
        )
        cmds.connectAttr(
            "{}.outputRotate".format(node_decomp), "{}.r".format(joint), f=1
        )

        # delete node
        cmds.delete(node)

    print("Update : mgear_mulMatrix {} node.".format(len(mgear_nodes)))


def lock_anim_grp():
    list_grp_ctrl = []

    for ctl in Utility.sort_by_type(cmds.ls(), typ="anim_curve"):
        parent = cmds.listRelatives(ctl, p=1, typ="transform", f=1)

        if not parent:
            continue
        elif cmds.objectType(parent[0], isa="joint"):
            continue
        elif cmds.objectType(parent[0], isa="transform"):
            try:
                Utility.lock_attribute(
                    transform=parent[0], r=1, s=1, t=1, v=1, l=1, k=0
                )
            except:
                pass

            list_grp_ctrl.append(parent)

    cmds.select(list_grp_ctrl, r=1)


def propergate_faceset_material():
    selection = cmds.ls(sl=True, long=True)
    if not selection:
        cmds.warning("Please select objects to validate.")
        return

    shapes = cmds.listRelatives(selection, ad=True, type="mesh", fullPath=True) or []
    shading_groups = list(set(cmds.listConnections(shapes, type="shadingEngine") or []))

    if not shading_groups:
        cmds.warning("No shading groups found on selected objects.")
        return

    renamed_count = 0

    for sg in shading_groups:
        materials = cmds.listConnections(f"{sg}.surfaceShader")
        if not materials:
            continue

        mat = materials[0]

        # 1. หา Base Name โดยการตัด prefix เดิมออก
        base_name = mat
        if mat.startswith("MTL_"):
            base_name = mat[4:]
        elif mat.startswith("M_"):
            base_name = mat[2:]

        target_mat = f"MTL_{base_name}"
        target_sg = f"M_{base_name}"

        # 2. Rename Material ทันที
        if mat != target_mat:
            try:
                cmds.rename(mat, target_mat)
                renamed_count += 1
            except Exception as e:
                cmds.warning(f"Failed to rename Material {mat}: {e}")

        # 3. Rename Shading Engine ทันที
        if sg != target_sg:
            try:
                cmds.rename(sg, target_sg)
                renamed_count += 1
            except Exception as e:
                cmds.warning(f"Failed to rename Shading Engine {sg}: {e}")

    # 4. แสดงผลลัพธ์
    if renamed_count > 0:
        cmds.inViewMessage(
            amg=f'<span style="color:#72ff72;">✔ Updated {renamed_count} nodes.</span>',
            pos="midCenter",
            fade=True,
            fst=1500,
        )
    else:
        cmds.inViewMessage(
            amg='<span style="color:#72ff72;">✔ All Material/SG names are already valid.</span>',
            pos="midCenter",
            fade=True,
            fst=2000,
        )

def delete_fit_skeleton():
    if cmds.objExists("FitSkeleton"):
        cmds.delete("FitSkeleton")
    
    if cmds.objExists("FaceFitSkeleton"):
        cmds.delete("FaceFitSkeleton")

# def delete_unused_node():

#     mel.eval("MLdeleteUnused")

def set_prefer_angle_advanced_skeleton():
    if cmds.objExists("DeformSet"):
        bind_pose_node = cmds.ls("*bind*")
        cmds.delete(bind_pose_node)

        cmds.select("DeformSet")
        cmds.joint(cmds.ls(sl=1),e=1,spa=1,ch=1)

        cmds.select("DeformSet")
        cmds.dagPose(s=True,bp=True)

def clean_up_scene():
    """Do all stuff to clear the scene"""
    result = cmds.confirmDialog(
        title="Confirm",
        message="Clean-up cannot undoable, This will do\n"
        "\n"
        "- Import All References and clear namespaces\n"
        "- Clear Controller Animation\n"
        "\n"
        "Clear unwanted node\n"
        "- Remove Display Layer, Sets, Blupencil, ngskin\n"
        '- Remove Group "Delete_Grp" , "deleteThis"\n'
        "- Remove unused node\n"
        "\n"
        "Advanced Skeleton\n"
        "- Rename Rig Group Name based by Character\n"
        "- Remove Fit Skeleton\n"
        "- Set skeleton prefered angle\n"
        "- Turn off Joint Visibility",
        button=["Yes", "No"],
        defaultButton="Yes",
        cancelButton="No",
        dismissString="No",
    )

    if result == "Yes":
        # import and remove all namespaces
        import_all_references()
        remove_all_namespaces()
        clear_controller_animation()

        # delete
        delete_fit_skeleton()
        delete_all_display_layers()
        delete_all_delete_grp()
        delete_dwpicker_node()
        delete_blue_pencil()
        delete_ng_node()
        delete_unused_influences()
        # delete_user_selection_sets()
        propergate_faceset_material()
        # delete_unused_node()
        delete_unused_node()
        # clean_mgear_mult_matrix()
        # clean_mgear_matrix_constraint()
        # hide_channel_box_history()
        # lock_anim_grp()

        # rename new rig group
        create_rig_group()
        set_prefer_angle_advanced_skeleton()

        # turn off joint visibility for advance skeleton
        if cmds.objExists("Main"):
            cmds.setAttr("Main.jointVis", False)

        # propergate material

        cmds.inViewMessage(
            amg="<hl>Clean Up Rig Complete!.</hl>", pos="botCenter", fade=True
        )


def delete_all_delete_grp():
    if cmds.objExists("deleteThis"):
        cmds.delete("deleteThis")

    if cmds.objExists("Delete_Grp"):
        cmds.delete("Delete_Grp")


def create_rig_group():
    grp_advance_rig = "Group"
    if not cmds.objExists(grp_advance_rig):
        return

    current_path = cmds.file(q=True, sn=True)
    grp_character_rig = os.path.basename(current_path).split(".")[0].split("_")[0]

    if not cmds.objExists(grp_character_rig):
        cmds.rename(grp_advance_rig, grp_character_rig)
        # cmds.group(em=1, n=grp_character_rig)

    # try to parent
    # try:
    #     cmds.parent(grp_advance_rig, grp_character_rig)
    # except:
    #     pass


def unlock_anim_grp():
    list_grp_ctrl = []

    for ctl in Utility.sort_by_type(cmds.ls(), typ="anim_curve"):
        if not cmds.objExists(ctl):
            continue

        parent = cmds.listRelatives(ctl, p=1, typ="transform", f=1)

        if parent is None:
            continue
        elif cmds.objectType(parent[0], isa="joint"):
            continue
        elif cmds.objectType(parent[0], isa="transform"):
            try:
                Utility.lock_attribute(
                    transform=parent[0], r=1, s=1, t=1, v=1, l=0, k=1
                )
            except:
                pass

            list_grp_ctrl.append(parent)

    cmds.select(list_grp_ctrl, r=1)


def delete_all_display_layers():
    for layer in cmds.ls(type="displayLayer") or []:
        if layer != "defaultLayer":
            cmds.delete(layer)


def finalize_visibility(local_rig_name):
    # lock and hide all transform
    list_joint = cmds.listRelatives(local_rig_name, ad=1, typ="joint", f=1)
    if list_joint:
        for obj in list_joint:
            cmds.setAttr(obj + ".drawStyle", 2)

    list_locator_shape = cmds.listRelatives(local_rig_name, ad=1, typ="locator", f=1)
    if list_locator_shape:
        for obj in list_locator_shape:
            cmds.setAttr(obj + ".v", 0)

    list_follicle_shape = cmds.listRelatives(local_rig_name, ad=1, typ="follicle", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(obj + ".v", 0)

    list_follicle_shape = cmds.listRelatives(
        local_rig_name, ad=1, typ="nurbsSurface", f=1
    )
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(cmds.listRelatives(obj, p=1)[0] + ".v", 0)

    list_follicle_shape = cmds.listRelatives(
        local_rig_name, ad=1, typ="arcLengthDimension", f=1
    )
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(obj + ".v", 0)

    list_follicle_shape = cmds.listRelatives(local_rig_name, ad=1, typ="ikHandle", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(obj + ".v", 0)
