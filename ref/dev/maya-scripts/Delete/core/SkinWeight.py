import pymel.core as pm
import math
from TonmaiToolkit.core import Utility,File,Misc
import os
import maya.cmds as mc


def filter_dict2_by_position(dict1, dict2, tolerance=0.1,absolute_match=False):
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
        for k1,v1 in dict1.items():
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

    pm.deformerWeights(file_name, im=1, method="index", deformer=node_bind,
                         path=file_path)

def get_closest_vertex(sources,target,tolerance=0.1,absolute_match=True):
    """
    This Function find closet vertex , to target mesh

    """

    def select_closest(source, target, tolerance=0.01):
        # dict source vtx pos
        dict_target_pos = Utility.get_vertex_data_position(target)
        dict_source_pos = Utility.get_vertex_data_position(source)

        # compare
        dict_result = filter_dict2_by_position(dict_source_pos, dict_target_pos, absolute_match=absolute_match)
        
        if len(dict_result) != len(dict_source_pos):
            set_before = set(dict_source_pos.keys())
            set_after = set(dict_result.keys())

            set_missing = set_after.difference(set_before)

            raise Exception("Please Adjust to lower torolence , some vertex are missing to detect : {}".format(list(set_missing)))

        # selection
        shape = pm.listRelatives(target,c=1,s=1)[0]
        dict_match_vertex = {}
        
        for key,value in dict_result.items():
            dict_match_vertex["{}.vtx[{}]".format(source,value)] = "{}.vtx[{}]".format(target,key)

        return dict_match_vertex

    dict_output = {}

    for source in sources:
        dict_match_vertex = select_closest(source=source,target=target,tolerance=tolerance)
        dict_output[str(source)] = dict_match_vertex

    
    return dict_output

def combine_influence():
    pass

def get_skin_cluster_node(mesh_node):
    """
    Returns the PyMEL SkinCluster node associated with a given mesh name.

    Args:
        mesh_node (str): The name of the mesh node (transform or shape).

    Returns:
        pm.nt.SkinCluster or None: The PyMEL SkinCluster node if found, otherwise None.
    """
    
    if ".vtx" in str(mesh_node):
        mesh_node = Utility.make_pynode(mesh_node.split(".")[0])

    if not Utility.is_py_node(mesh_node):
        mesh_node = pm.PyNode(mesh_node)

    if isinstance(mesh_node, pm.nt.Shape):
        mesh_node = mesh_node.getParent()

    if not isinstance(mesh_node, pm.nt.Transform):
        pm.error(f"Node '{mesh_node}' is not a valid mesh transform or shape node.")
        return None

    skin_cluster_name = pm.mel.eval('findRelatedSkinCluster "{}"'.format(mesh_node.fullPath()))

    if not skin_cluster_name:
        return None

    try:
        skin_cluster_node = pm.PyNode(skin_cluster_name)
        return skin_cluster_node
    except pm.MayaNodeError:
        pm.error(f"Found skin cluster '{skin_cluster_name}' but could not convert to PyNode.")
        return None

def get_skin_cluster_influence(node):
    if pm.objectType(node) == "transform":
        skin_cluster_node = get_skin_cluster_node(node)
    elif pm.objectType(node) == "skinCluster":
        skin_cluster_node = node

    if not skin_cluster_node:
        return []

    influences = pm.skinCluster(skin_cluster_node,q=True,inf=True)

    return influences





def add_multi_skin_cluster(mesh,list_joint,name="skinCluster_add"):
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
            list_shape = pm.listRelatives(obj, c=1, s=1)

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
        mesh_tmp = pm.duplicate(mesh,n=mesh+"_tmp")[0]

        # GET SKIN CLUSTER OUTPUT PATH -----------------------------------------
        attr_output_geo = pm.listConnections("{}.outputGeometry[0]".format(node_skin_cluster_main),source=False, destination=True, plugs=True)

        # GET SKIN CLUSTER NEW -----------------------------------------
        node_skin_cluster_new = pm.skinCluster(list_joint_node+[mesh_tmp],n=name)

        # CREATE CONNECTION -----------------
        pm.connectAttr("{}.outMesh".format(node_shape_output_main),"{}.originalGeometry[0]".format(node_skin_cluster_new),f=1)
        pm.connectAttr("{}.outputGeometry[0]".format(node_skin_cluster_main),"{}.input[0].inputGeometry".format(node_skin_cluster_new),f=1)

        if attr_output_geo:
            pm.connectAttr("{}.outputGeometry[0]".format(node_skin_cluster_new),attr_output_geo[0],f=1)

        # DELETE TEMP SHAPE -----------------
        pm.delete(mesh_tmp)

        # print(node_skin_cluster_main,node_skin_cluster_new)
        # pm.reorderDeformers(node_skin_cluster_main,node_skin_cluster_new,mesh)

        # FINALIZE ------------------------

        # pm.select(node_skin_cluster_new)

        return node_skin_cluster_new

    def add_for_curve():
        def get_skin_cluster(obj):
            history = pm.listHistory(obj, pdo=True)  # Get history, prioritize deformers
            skin_clusters = pm.ls(history, type="skinCluster")  # Filter only skinClusters

            if not skin_clusters:
                pm.confirmDialog(m="Target Mesh Must Have Main Skin Cluster First!")
                raise Exception()

            return skin_clusters[0]

        def get_shape_origin(obj):
            list_shape = pm.listRelatives(obj, c=1, s=1)

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
        mesh_tmp = pm.duplicate(mesh,n=mesh+"_tmp")[0]

        # GET SKIN CLUSTER OUTPUT PATH -----------------------------------------
        attr_output_geo = pm.listConnections("{}.outputGeometry[0]".format(node_skin_cluster_main),source=False, destination=True, plugs=True)

        # GET SKIN CLUSTER NEW -----------------------------------------
        node_skin_cluster_new = pm.skinCluster(list_joint+[mesh_tmp],n=name)
        print("skin cluster result : ",node_skin_cluster_new)
        # CREATE CONNECTION -----------------
        pm.connectAttr("{}.local".format(node_shape_output_main),"{}.originalGeometry[0]".format(node_skin_cluster_new),f=1)
        pm.connectAttr("{}.outputGeometry[0]".format(node_skin_cluster_main),"{}.input[0].inputGeometry".format(node_skin_cluster_new),f=1)

        if attr_output_geo:
            pm.connectAttr("{}.outputGeometry[0]".format(node_skin_cluster_new),attr_output_geo[0],f=1)

        # DELETE TEMP SHAPE -----------------
        pm.delete(mesh_tmp)

        # pm.reorderDeformers(node_skin_cluster_main,node_skin_cluster_new,mesh)

        # FINALIZE ------------------------

        return node_skin_cluster_new
    
    if pm.objectType(pm.listRelatives(mesh,c=1,s=1)[0],isa="nurbsCurve") or pm.objectType(pm.listRelatives(mesh,c=1,s=1)[0],isa="nurbsSurface"):
        node = add_for_curve()
        return node
    elif pm.objectType(pm.listRelatives(mesh,c=1,s=1)[0],isa="mesh"):
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
    new_surface = pm.PyNode(new_surface)
    new_influences = [pm.PyNode(x) for x in new_influences]

    # get old influences from the first CV in the data
    old_influences = list(next(iter(weight_data.values())).keys())
    if len(old_influences) != len(new_influences):
        raise ValueError("Number of new influences must match old influences")

    # map old -> new influences
    mapping = dict(zip(old_influences, new_influences))

    # make sure skinCluster exists
    if skinCluster is None:
        skinCluster = pm.skinCluster(new_influences, new_surface, tsb=True)[0]
    else:
        skinCluster = pm.PyNode(skinCluster)

    new_data = {}

    for cv, infl_weights in weight_data.items():
        # build new CV name (replace surface name)
        cv_index = cv.split(".")[1]   # e.g. "cv[0][1]"
        cv_str = "{}.{}".format(new_surface.name(), cv_index)
        cv_pynode = pm.PyNode(cv_str)

        # remap influences
        new_weights = {mapping[infl]: weight for infl, weight in infl_weights.items()}
        new_data[cv_str] = new_weights

        # apply weights
        for infl, w in new_weights.items():
            pm.skinPercent(skinCluster, cv_pynode, transformValue=[(infl, w)])

    return new_data