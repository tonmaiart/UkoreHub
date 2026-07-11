import math
from tmlib.core import Utility,Format
import os
import maya.cmds as cmds
import maya.mel as mel

import re
from maya.api import OpenMaya as om

def filter_dict2_by_position(dict1, dict2, tolerance=0.1, absolute_match=False):
    """Return match postion by input dict

    Argument
    dict1 : {1:(0,1,5)}
    dict2 : {7:(0,1,5)}

    return {7:1}

    """

    def distance(p1, p2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    result = {}
    for k2, v2 in dict2.items():
        for k1, v1 in dict1.items():
            if absolute_match:
                if v1 == v2:
                    result[k2] = k1
                    break
            else:
                if distance(v1, v2) <= tolerance:
                    result[k2] = k1
                    break  # stop checking once matched
    return result


def import_weight(node_bind, xml_path):
    if "/" in xml_path:
        syntax = "/"
    elif "\\" in xml_path:
        syntax = "\\"
    else:
        raise Exception("Invalid Import Weight Path , Not Found / , or \\")
    file_name = xml_path.split(syntax)[-1]
    file_path = xml_path.replace(syntax + file_name, "")

    cmds.deformerWeights(
        file_name, im=1, method="index", deformer=node_bind, path=file_path
    )


def copy_weight(source, target):
    source_skin_cluster = cmds.ls(cmds.listHistory(source), type="skinCluster")

    if not source_skin_cluster:
        print("Skipped Copy for : {}, Not found SkinWeight Node".format(source))
        return

    source_skin_cluster = source_skin_cluster[0]
    influences = cmds.skinCluster(source_skin_cluster, q=True, influence=True)

    old_skin_cluster = cmds.ls(cmds.listHistory(target), type="skinCluster")

    # preserve old naming of skin cluster
    old_name = None
    if old_skin_cluster:
        old_name = old_skin_cluster[0]
        cmds.rename(old_skin_cluster[0], old_name + "_old")
        cmds.delete(old_name + "_old")

    new_skin_cluster = cmds.skinCluster(
        influences,
        target,
        toSelectedBones=True,
        bindMethod=0,
        skinMethod=0,
        normalizeWeights=1,
    )[0]

    # recall old name
    if old_name:
        new_skin_cluster = cmds.rename(new_skin_cluster, old_name)

    cmds.copySkinWeights(
        sourceSkin=source_skin_cluster,
        destinationSkin=new_skin_cluster,
        noMirror=True,
        surfaceAssociation="closestPoint",
        influenceAssociation=["oneToOne"],
    )


def get_closest_vertex(sources, target, tolerance=0.1, absolute_match=True):
    """
    This Function find closet vertex , to target mesh

    """

    def select_closest(source, target, tolerance=0.01):
        # dict source vtx pos
        dict_target_pos = Utility.get_vertex_data_position(target)
        dict_source_pos = Utility.get_vertex_data_position(source)

        # compare
        dict_result = filter_dict2_by_position(
            dict_source_pos, dict_target_pos, absolute_match=absolute_match
        )

        if len(dict_result) != len(dict_source_pos):
            set_before = set(dict_source_pos.keys())
            set_after = set(dict_result.keys())

            set_missing = set_after.difference(set_before)

            raise Exception(
                "Please Adjust to lower torolence , some vertex are missing to detect : {}".format(
                    list(set_missing)
                )
            )

        # selection
        shape = cmds.listRelatives(target, c=1, s=1)[0]
        dict_match_vertex = {}

        for key, value in dict_result.items():
            dict_match_vertex["{}.vtx[{}]".format(source, value)] = "{}.vtx[{}]".format(
                target, key
            )

        return dict_match_vertex

    dict_output = {}

    for source in sources:
        dict_match_vertex = select_closest(
            source=source, target=target, tolerance=tolerance
        )
        dict_output[str(source)] = dict_match_vertex

    return dict_output


def combine_influence():
    pass


def get_skin_cluster_node(mesh_node):
    """
    Returns the skinCluster node name associated with a given mesh name.

    Args:
        mesh_node (str): The name of the mesh node (transform or shape).

    Returns:
        str or None: The skinCluster node name if found, otherwise None.
    """

    # Handle vertex component (e.g. "mesh.vtx[0]")
    if ".vtx" in str(mesh_node):
        mesh_node = mesh_node.split(".")[0]

    # If shape node, get parent transform
    if cmds.nodeType(mesh_node) in ("mesh", "nurbsSurface", "lattice"):
        parents = cmds.listRelatives(mesh_node, parent=True, fullPath=True)
        if parents:
            mesh_node = parents[0]

    # Validate it's a transform
    if cmds.nodeType(mesh_node) != "transform":
        cmds.error(f"Node '{mesh_node}' is not a valid mesh transform or shape node.")
        return None

    # Find skinCluster from shapes
    skin_cluster_name = None
    shapes = (
        cmds.listRelatives(mesh_node, children=True, shapes=True, fullPath=True) or []
    )
    for shape in shapes:
        find_skin = mel.eval('findRelatedSkinCluster "{}"'.format(shape))
        if find_skin:
            skin_cluster_name = find_skin
            break

    if not skin_cluster_name:
        return None

    # Validate node exists
    if not cmds.objExists(skin_cluster_name):
        cmds.error(f"Found skin cluster '{skin_cluster_name}' but it does not exist.")
        return None

    return skin_cluster_name


def get_skin_cluster_influence(node):
    if cmds.objectType(node) == "transform":
        skin_cluster_node = get_skin_cluster_node(node)
    elif cmds.objectType(node) == "skinCluster":
        skin_cluster_node = node

    if not skin_cluster_node:
        return []

    influences = cmds.skinCluster(skin_cluster_node, q=True, inf=True)

    return influences


def add_multi_skin_cluster(mesh, list_joint, name="skinCluster_add"):
    """
    For add multiple skin cluster for maya older than 2024

    """
    # GET VARIABLES -----------------------------------------
    # first selection must be mesh , all after is joint

    mesh = Utility.make_pynode(mesh)

    list_joint_node = []
    for joint in list_joint:
        list_joint_node.append(Utility.make_pynode(joint))

    def add_for_mesh():
        def get_shape_origin(obj):
            list_shape = cmds.listRelatives(obj, c=1, s=1)

            if not list_shape:
                raise Exception()

            shape_orig = None
            shape = None

            for shape in list_shape:
                if "Orig" in shape:
                    shape_orig = shape
                else:
                    shape = shape

            if shape_orig:
                return shape_orig
            elif shape:
                return shape
            else:
                raise Exception()

        # GET SKIN CLUSTER MAIN -----------------------------------------
        node_skin_cluster_main = get_skin_cluster_node(mesh)
        node_shape_output_main = get_shape_origin(mesh)

        # CREATE TMP MESH -----------------------------------------
        mesh_tmp = cmds.duplicate(mesh, n=mesh + "_tmp")[0]

        # GET SKIN CLUSTER OUTPUT PATH -----------------------------------------
        attr_output_geo = cmds.listConnections(
            "{}.outputGeometry[0]".format(node_skin_cluster_main),
            source=False,
            destination=True,
            plugs=True,
        )

        # GET SKIN CLUSTER NEW -----------------------------------------
        node_skin_cluster_new = cmds.skinCluster(list_joint_node + [mesh_tmp], n=name)

        # CREATE CONNECTION -----------------
        cmds.connectAttr(
            "{}.outMesh".format(node_shape_output_main),
            "{}.originalGeometry[0]".format(node_skin_cluster_new),
            f=1,
        )
        cmds.connectAttr(
            "{}.outputGeometry[0]".format(node_skin_cluster_main),
            "{}.input[0].inputGeometry".format(node_skin_cluster_new),
            f=1,
        )

        if attr_output_geo:
            cmds.connectAttr(
                "{}.outputGeometry[0]".format(node_skin_cluster_new),
                attr_output_geo[0],
                f=1,
            )

        # DELETE TEMP SHAPE -----------------
        cmds.delete(mesh_tmp)

        # print(node_skin_cluster_main,node_skin_cluster_new)
        # cmds.reorderDeformers(node_skin_cluster_main,node_skin_cluster_new,mesh)

        # FINALIZE ------------------------

        # cmds.select(node_skin_cluster_new)

        return node_skin_cluster_new

    def add_for_curve():
        def get_skin_cluster(obj):
            history = cmds.listHistory(
                obj, pdo=True
            )  # Get history, prioritize deformers
            skin_clusters = cmds.ls(
                history, type="skinCluster"
            )  # Filter only skinClusters

            if not skin_clusters:
                cmds.confirmDialog(m="Target Mesh Must Have Main Skin Cluster First!")
                raise Exception()

            return skin_clusters[0]

        def get_shape_origin(obj):
            list_shape = cmds.listRelatives(obj, c=1, s=1)

            if not list_shape:
                raise Exception()

            shape_orig = None
            shape = None

            for shape in list_shape:
                if "Orig" in shape:
                    shape_orig = shape
                else:
                    shape = shape

            if shape_orig:
                return shape_orig
            elif shape:
                return shape
            else:
                raise Exception()

        # GET SKIN CLUSTER MAIN -----------------------------------------
        node_skin_cluster_main = get_skin_cluster(mesh)
        node_shape_output_main = get_shape_origin(mesh)

        # CREATE TMP MESH -----------------------------------------
        mesh_tmp = cmds.duplicate(mesh, n=mesh + "_tmp")[0]

        # GET SKIN CLUSTER OUTPUT PATH -----------------------------------------
        attr_output_geo = cmds.listConnections(
            "{}.outputGeometry[0]".format(node_skin_cluster_main),
            source=False,
            destination=True,
            plugs=True,
        )

        # GET SKIN CLUSTER NEW -----------------------------------------
        node_skin_cluster_new = cmds.skinCluster(list_joint + [mesh_tmp], n=name)
        print("skin cluster result : ", node_skin_cluster_new)
        # CREATE CONNECTION -----------------
        cmds.connectAttr(
            "{}.local".format(node_shape_output_main),
            "{}.originalGeometry[0]".format(node_skin_cluster_new),
            f=1,
        )
        cmds.connectAttr(
            "{}.outputGeometry[0]".format(node_skin_cluster_main),
            "{}.input[0].inputGeometry".format(node_skin_cluster_new),
            f=1,
        )

        if attr_output_geo:
            cmds.connectAttr(
                "{}.outputGeometry[0]".format(node_skin_cluster_new),
                attr_output_geo[0],
                f=1,
            )

        # DELETE TEMP SHAPE -----------------
        cmds.delete(mesh_tmp)

        # cmds.reorderDeformers(node_skin_cluster_main,node_skin_cluster_new,mesh)

        # FINALIZE ------------------------

        return node_skin_cluster_new

    if cmds.objectType(
        cmds.listRelatives(mesh, c=1, s=1)[0], isa="nurbsCurve"
    ) or cmds.objectType(cmds.listRelatives(mesh, c=1, s=1)[0], isa="nurbsSurface"):
        node = add_for_curve()
        return node
    elif cmds.objectType(cmds.listRelatives(mesh, c=1, s=1)[0], isa="mesh"):
        node = add_for_mesh()
        return node
    else:
        raise Exception("not support add multi ski for given")


def remap_and_apply_weights(weight_data, new_surface, new_influences, skinCluster=None):
    """
    Remap existing skin weight data to a new surface and apply it in Maya (PyMEL version).

    :param weight_data: dict, original cv -> {influence: weight}
    :param new_surface: str or PyNode, new NURBS surface shape
    :param new_influences: list[str] or list[PyNode], new influences (must match old count)
    :param skinCluster: str or PyNode, optional skinCluster name (if None, will create one)
    :return: dict, remapped weight data
    """
    new_surface = cmds.PyNode(new_surface)
    new_influences = [cmds.PyNode(x) for x in new_influences]

    # get old influences from the first CV in the data
    old_influences = list(next(iter(weight_data.values())).keys())
    if len(old_influences) != len(new_influences):
        raise ValueError("Number of new influences must match old influences")

    # map old -> new influences
    mapping = dict(zip(old_influences, new_influences))

    # make sure skinCluster exists
    if skinCluster is None:
        skinCluster = cmds.skinCluster(new_influences, new_surface, tsb=True)[0]
    else:
        skinCluster = cmds.PyNode(skinCluster)

    new_data = {}

    for cv, infl_weights in weight_data.items():
        # build new CV name (replace surface name)
        cv_index = cv.split(".")[1]  # e.g. "cv[0][1]"
        cv_str = "{}.{}".format(new_surface.name(), cv_index)
        cv_pynode = cmds.PyNode(cv_str)

        # remap influences
        new_weights = {mapping[infl]: weight for infl, weight in infl_weights.items()}
        new_data[cv_str] = new_weights

        # apply weights
        for infl, w in new_weights.items():
            cmds.skinPercent(skinCluster, cv_pynode, transformValue=[(infl, w)])

    return new_data

def move_weight(weight_percent, source_text, target_text):

        selection = cmds.ls(sl=True, fl=True)
        if not selection:
            return

        print("### Starting Moving Weight ###")
        print("- Weight Percent : ", weight_percent)
        print("- Search : ", source_text)
        print("- Replace With : ", target_text)
        print("- Selection : ", selection)

        # Get skinCluster from the object of the selected component
        obj = selection[0].split(".")[0]
        skin_cluster_node = get_skin_cluster_node(obj)

        if not skin_cluster_node:
            cmds.error("No skinCluster found.")
            return

        all_influence = get_skin_cluster_influence(skin_cluster_node)
        all_influence_text = [str(each) for each in all_influence]

        print("* Skin Cluster All Influences : ", all_influence_text)
        for i, name in enumerate(all_influence_text):
            print("{}. {}".format(i + 1, name))

        dict_pair = {}

        for src_influence_name in all_influence_text:
            if source_text not in src_influence_name:
                continue

            replaced_text = src_influence_name.replace(source_text, target_text)

            if replaced_text not in all_influence_text:
                continue

            dict_pair[src_influence_name] = replaced_text

        print("# Pairing Influence Result : ")
        for src, tgt in dict_pair.items():
            print("- ", src, " > ", tgt)

        if not dict_pair:
            cmds.warning("No matching joint pairs found.")
            return

        print("# Starting Moving Weight")
        skin_percent_q = cmds.skinPercent

        for comp in selection:
            list_inf_value = skin_percent_q(skin_cluster_node, comp, query=True, v=True)

            # Preserve original influence order when zipping — do NOT use sorted list
            dict_weight_data = {str(inf): val for inf, val in zip(all_influence, list_inf_value)}

            for source_jnt, source_jnt_value in dict_weight_data.items():
                if source_jnt_value <= 0 or source_jnt not in dict_pair:
                    continue

                target_jnt = dict_pair[source_jnt]
                target_jnt_value = dict_weight_data.get(target_jnt, 0.0)

                sum_value = source_jnt_value + target_jnt_value
                t_val = weight_percent * sum_value
                s_val = sum_value - t_val

                skin_percent_q(
                    skin_cluster_node,
                    comp,
                    transformValue=[(source_jnt, s_val), (target_jnt, t_val)],
                )

def move_weight_ngskintools(weight_percent, source_text, target_text, selection=None):
    from ngSkinTools2.api import Layers

    if selection is None:
        selection = cmds.ls(selection=True, flatten=True)

    if not selection:
        cmds.warning("No components selected.")
        return

    print("### Starting Moving Weight (ngSkinTools) ###")
    
    # 1. Basic Setup and Validation
    obj = selection[0].split(".")[0]
    # Assuming get_skin_cluster_node is defined elsewhere in your script
    # skin_cluster_node = get_skin_cluster_node(obj) 
    skin_cluster_node = cmds.ls(cmds.listHistory(obj), type='skinCluster')[0]

    if not skin_cluster_node:
        cmds.error("No skinCluster found.")
        return

    layers = Layers(skin_cluster_node)
    if not layers.list():
        cmds.warning("No ngSkinTools layers found. Please initialize layers first.")
        return

    layer = layers.current_layer()
    influences = cmds.skinCluster(skin_cluster_node, query=True, influence=True)
    inf_name_to_idx = {name: i for i, name in enumerate(influences)}
    
    # 2. Build Influence Pairs
    dict_pair = {}
    for src_influence_name in influences:
        if source_text in src_influence_name:
            replaced_text = src_influence_name.replace(source_text, target_text)
            if replaced_text in inf_name_to_idx:
                dict_pair[src_influence_name] = replaced_text

    if not dict_pair:
        cmds.warning("No matching joint pairs found.")
        return

    # 3. Extract Vertex Indices (Native Python list)
    vtx_indices = []
    for comp in selection:
        match = re.search(r'\[(\d+)\]', comp)
        if match:
            vtx_indices.append(int(match.group(1)))

    if not vtx_indices:
        cmds.warning("No vertices found in selection.")
        return

    num_verts = cmds.polyEvaluate(obj, vertex=True)
    
    # 4. Processing Weights using MDoubleArray
    print("# Starting Moving Weight Array Processing")
    
    for source_jnt, target_jnt in dict_pair.items():
        src_idx = inf_name_to_idx.get(source_jnt)
        tgt_idx = inf_name_to_idx.get(target_jnt)

        # Fetch weights and convert to MDoubleArray
        # ngSkinTools returns a list; om.MDoubleArray accepts a list in its constructor
        src_weights = om.MDoubleArray(layer.get_weights(src_idx) or [0.0] * num_verts)
        tgt_weights = om.MDoubleArray(layer.get_weights(tgt_idx) or [0.0] * num_verts)

        changed = False
        
        # We must loop through the selection indices manually
        for idx in vtx_indices:
            s_val = src_weights[idx]
            t_val = tgt_weights[idx]
            
            if s_val > 0:
                total = s_val + t_val
                new_tgt = total * weight_percent
                new_src = total - new_tgt
                
                src_weights[idx] = new_src
                tgt_weights[idx] = new_tgt
                changed = True

        # Only push data back to ngSkinTools if a change occurred
        if changed:
            layer.set_weights(src_idx, list(src_weights))
            layer.set_weights(tgt_idx, list(tgt_weights))

    print("### Move Weight Complete ###")