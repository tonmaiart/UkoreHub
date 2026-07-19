from tmlib.core import QuickData, File, Math, SkinWeight
import maya.api.OpenMaya as om
import os
import maya.cmds as cmds
import maya.api.OpenMayaAnim as omAnim


def get_local_positions_fast(mesh_name):
    """
    Get local vertex positions using API 2.0.
    Returns: tuple of (x, y, z) tuples.
    """
    try:
        selection_list = om.MSelectionList()
        selection_list.add(mesh_name)
        # Get the DAG path for the mesh
        dag_path = selection_list.getDagPath(0)
        # Initialize the Mesh Function Set
        mfn_mesh = om.MFnMesh(dag_path)
    except:
        om.MGlobal.displayError(f"Failed to find mesh: {mesh_name}")
        return tuple()

    # Pull all points at once in Object Space (Local)
    # Using om.MSpace.kObject is key for local coordinates
    points = mfn_mesh.getPoints(om.MSpace.kObject)

    # Convert the MPointArray to a tuple of (x, y, z)
    # List comprehension + slicing is handled at the C-level for speed
    return tuple((p.x, p.y, p.z) for p in points)


def set_mesh_vertex(mesh_name, vertexs):
    for i, pos in enumerate(vertexs):
        cmds.xform("{}.vtx[{}]".format(mesh_name, i), os=1, t=pos)


def get_corrective_shape_vertexs(current, target, base):
    """Get Only Corrective shape vertex
    
    Args:
    current : Mesh for reference current joint based deform shape
    target : Mesh for Static Blend Shape
    base : the default base shape for skin cluster and blend shape

    Return : 
    arrays of vector for each vertex for corrective shape result
    """
    base_vertex_positions = get_local_positions_fast(base)
    current_vertex_positions = get_local_positions_fast(current)
    target_vertex_positions = get_local_positions_fast(target)

    result_subtract = Math.subtract_vector_array(
        target_vertex_positions, current_vertex_positions
    )

    result_sum_base = Math.add_vector_array(base_vertex_positions, result_subtract)

    return result_sum_base


def create_corrective_shape(current, target, base):
    """
    Create New Corrective Shape from Static Shape , the result of mesh will be corrective shape which must be combine the shape to the exist skin cluster

    Args:
    current : Mesh for reference current joint based deform shape
    target : Mesh for Static Blend Shape
    base : the default base shape for skin cluster and blend shape
    update : Mesh that will update shape to corrective form
    """

    dup_geo = cmds.duplicate(base, n=f"{target}_CorrectiveShape")[0]

    update_corrective_shape(
        dup_geo,target=target,base=base,current=current
    )

    return dup_geo


def update_corrective_shape(current, target, base, update):
    """
    Update Shape to Exist Mesh , the result of mesh will be corrective shape which must be combine the shape to the exist skin cluster

    Args:
    current : Mesh for reference current joint based deform shape
    target : Mesh for Static Blend Shape
    base : the default base shape for skin cluster and blend shape
    update : Mesh that will update shape to corrective form
    """

    set_mesh_vertex(update, get_corrective_shape_vertexs(current, target, base))


def get_influence_weights_tuple(skin_cluster_name, joint_name):

    # 1. Selection and Function Set
    sel = om.MSelectionList()
    try:
        sel.add(skin_cluster_name)
        skin_fn = omAnim.MFnSkinCluster(sel.getDependNode(0))
    except Exception as e:
        return tuple()

    # 2. Find influence logical index
    inf_objects = skin_fn.influenceObjects()

    inf_index = -1
    for i, inf in enumerate(inf_objects):
        inf_short = inf.partialPathName().split("|")[-1]
        joint_short = joint_name.split("|")[-1]
        if inf_short == joint_short:
            inf_index = i
            break

    if inf_index == -1:
        return tuple()

    # 3. Component Setup (All Vertices)
    path = skin_fn.getPathAtIndex(0)
    vtx_count = om.MFnMesh(path).numVertices

    comp_fn = om.MFnSingleIndexedComponent()
    vtx_comps = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(range(vtx_count))

    weights, num_inf = skin_fn.getWeights(path, vtx_comps)

    return tuple(weights[inf_index::num_inf])


def get_morph_shape_position(
    base_mesh="Base_Geo",
    target_mesh="Head_Dimpler",
    tuple_skin_weight=[],
):
    # Get vertex positions
    tuple_base_vertex_postion = get_local_positions_fast(base_mesh)
    tuple_target_vertex_postion = get_local_positions_fast(target_mesh)

    vector_array = []

    print(base_mesh,tuple_base_vertex_postion)
    print(target_mesh,tuple_target_vertex_postion)

    for i in range(len(tuple_base_vertex_postion)):

        b_p = om.MVector(tuple_base_vertex_postion[i])
        t_p = om.MVector(tuple_target_vertex_postion[i])
        weight = tuple_skin_weight[i]

        # Blend: weight=0 stays at base, weight=1 goes full target
        new_pos = b_p + (t_p - b_p) * weight
        vector_array.append(new_pos)  # ← append ทุก vertex เสมอ

    return vector_array


def update_split_shape(
    split_weight_mesh="BlendShapeSplitWeight",
    base_mesh="Base_Geo",
    target_mesh="Head_Dimpler",
    use_custom_influences=False,
    custom_influences=["jnt_L_weight", "jnt_R_weight"],
    list_update_mesh=[],
):
    """
    Update Splitted Shape to exist

    Args:
    split_weight_mesh : Mesh that have skin weight on it.
    base_mesh : base of default mesh (you to reference when revert shape).
    target_mesh : Mesh that is target prefer shape.
    list_update_mesh : The target mesh for update shape.
    """

    # =================
    # Prepare Variables
    # =================

    if use_custom_influences is False:
        influences = SkinWeight.get_skin_cluster_influence(split_weight_mesh)
    elif use_custom_influences is True:
        influences = custom_influences

    ###########################################
    #### Main Operation for split weight ######
    ###########################################

    skin_cluster_name = SkinWeight.get_skin_cluster_node(split_weight_mesh)

    for i, joint_name in enumerate(influences):
        # get skin weight value for each vertex
        tuple_skin_weight = get_influence_weights_tuple(skin_cluster_name, joint_name)
        print("skin_cluster_name : ", skin_cluster_name)
        print("joint_name : ", joint_name)
        print("tuple_skin_weight : ", tuple_skin_weight)

        morph_positions = get_morph_shape_position(
            base_mesh=base_mesh,
            target_mesh=target_mesh,
            tuple_skin_weight=tuple_skin_weight,
        )

        # set dup geo vertex
        set_mesh_vertex(list_update_mesh[i], morph_positions)


def create_split_shape(
    split_weight_mesh="BlendShapeSplitWeight",
    base_mesh="Base_Geo",
    target_mesh="Head_Dimpler",
    use_custom_influences=False,
    custom_influences=["jnt_L_weight", "jnt_R_weight"],
):
    """
    Create Left and Right side geo which splited from main blendshape geo
    """

    # =================
    # Prepare Variables
    # =================

    if use_custom_influences is False:
        influences = SkinWeight.get_skin_cluster_influence(split_weight_mesh)
    elif use_custom_influences is True:
        influences = custom_influences

    ###########################################
    #### Main Operation for split weight ######
    ###########################################

    skin_cluster_name = SkinWeight.get_skin_cluster_node(split_weight_mesh)
    list_dup_geo = []

    for joint_name in influences:
        # get skin weight value for each vertex
        tuple_skin_weight = get_influence_weights_tuple(skin_cluster_name, joint_name)
        morph_positions = get_morph_shape_position(
            base_mesh=base_mesh,
            target_mesh=target_mesh,
            tuple_skin_weight=tuple_skin_weight,
        )

        # create new mesh by duplicate base mesh
        dup_geo = cmds.duplicate(base_mesh, n=f"{target_mesh}_{joint_name}")[0]
        list_dup_geo.append(dup_geo)
        cmds.setAttr("{}.v".format(dup_geo), True)
        cmds.matchTransform(dup_geo, target_mesh)

        # set dup geo vertex
        set_mesh_vertex(dup_geo, morph_positions)

    return list_dup_geo


def rename_blendshape_target(blendshape_node, old_name, new_name):
    aliases = cmds.aliasAttr(blendshape_node, q=True) or []
    for i in range(0, len(aliases), 2):
        if aliases[i] == old_name:
            plug = f"{blendshape_node}.{aliases[i+1]}"
            # remove old alias first
            cmds.aliasAttr(plug, remove=True)
            # set new alias
            cmds.aliasAttr(new_name, plug)
            return
    cmds.warning(f"Target '{old_name}' not found in {blendshape_node}")


def create_operated_corrective_shape(
    object_A="base", object_B="target", operation="add"
):

    def get_vertex_positions_from_duplicate(obj_name):
        """Duplicate an object, get its vertex positions, then delete the duplicate."""
        dup = cmds.duplicate(obj_name, name="tmp_vtx_extract")[0]
        positions = {}
        vtx_count = cmds.polyEvaluate(dup, vertex=True)

        for i in range(vtx_count):
            pos = cmds.xform(f"{dup}.vtx[{i}]", q=1, os=1, t=True)
            positions[i] = tuple(pos)

        cmds.delete(dup)  # delete the temporary duplicate
        return positions

    def vector_list_operation(list1, list2, operation=operation):
        """
        Perform element-wise addition or subtraction between
        two lists of 3D vectors.

        Args:
            list1 (list of tuple): List of (x, y, z) vectors.
            list2 (list of tuple): List of (x, y, z) vectors.
            operation (str): 'add' or 'sub'.

        Returns:
            list of tuple: Resulting list of (x, y, z) vectors.
        """
        if len(list1) != len(list2):
            raise ValueError(
                f"List lengths must match. Got {len(list1)} vs {len(list2)}."
            )

        results = []
        for v1, v2 in zip(list1, list2):
            if len(v1) != 3 or len(v2) != 3:
                raise ValueError("All vectors must be 3D tuples/lists.")
            if operation == "add":
                results.append((v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2]))
            elif operation == "sub":
                results.append((v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2]))
            else:
                raise ValueError("Operation must be 'add' or 'sub'.")
        return results

    vtxs_A = get_vertex_positions_from_duplicate(object_A).values()
    vtxs_B = get_vertex_positions_from_duplicate(object_B).values()

    # get list result
    vtxs_result = vector_list_operation(vtxs_A, vtxs_B, operation=operation)
    vtxs_result = vector_list_operation(vtxs_A, vtxs_result, operation=operation)

    obj_result = cmds.duplicate(object_A)[0]

    for i, pos in enumerate(vtxs_result):
        cmds.xform("{}.vtx[{}]".format(obj_result, i), os=1, t=pos)

    cmds.select(obj_result)

    try:
        cmds.setAttr(obj_result + ".v", True)
    except:
        pass

    return obj_result


def split_blendshape(
    L_joint="jnt_L_weight",
    R_joint="jnt_R_weight",
    split_weight_mesh="BlendShapeSplitWeight",
    base_mesh="Base_Geo",
    target_mesh="Head_Dimpler",
    L_keyword="Left",
    R_keyword="Right",
    custom_weight_data=None,
):
    """
    Create Left and Right side geo which splited from main blendshape geo
    """

    # variables
    dict_base_geo_vtxs = {}
    dict_target_geo_vtxs = {}

    target_mesh_node = cmds.PyNode(target_mesh)
    target_mesh_name = target_mesh_node.shortName()
    base_mesh_node = cmds.PyNode(base_mesh)
    source_vtxs = base_mesh_node.vtx
    source_count = len(source_vtxs)

    MSelectionList = om.MSelectionList()

    # get target mesh vertex position
    MSelectionList.add(target_mesh_name)
    source_MDagPath = MSelectionList.getDagPath(0)
    source_MFnMesh = om.MFnMesh(source_MDagPath)
    MSelectionList.clear()
    list_target_geo_position = source_MFnMesh.getPoints()

    for i, pos in enumerate(list_target_geo_position):
        dict_target_geo_vtxs[i] = list(pos)[0:3]

    # get base mesh dict weight
    MSelectionList.add(base_mesh)
    source_MDagPath = MSelectionList.getDagPath(0)
    source_MFnMesh = om.MFnMesh(source_MDagPath)
    MSelectionList.clear()
    list_base_position = source_MFnMesh.getPoints()

    for i, pos in enumerate(list_base_position):
        dict_base_geo_vtxs[i] = list(pos)[0:3]

    # get json path
    if custom_weight_data:
        dict_data = custom_weight_data
    else:
        quick_data_path = QuickData.get_quick_data_dir()
        json_path = os.path.join(
            quick_data_path, "Skin", "{}.json".format(split_weight_mesh)
        )

        # check is path exist
        if not os.path.exists(json_path):
            cmds.error("Please Export Skin of {} First.".format(split_weight_mesh))

        # load json data
        dict_data = File.load_json_file_to_dict(json_path)

    ###########################################
    #### Main Operation for split weight ######
    ###########################################

    skin_cluster_name = ""
    dict_get_weight = {}

    for dict_weight in dict_data["deformerWeight"]["weights"]:
        skin_cluster_name = dict_weight["deformer"]
        joint_name = dict_weight["source"]

        if not (joint_name == L_joint or joint_name == R_joint):
            cmds.error("L joint and R joint not found in .json file.")

        # create new dict
        dict_get_weight[joint_name] = []
        new_dict = {}

        for each_dict in dict_weight["points"]:
            new_dict[each_dict["index"]] = each_dict["value"]

        dict_get_weight[joint_name] = new_dict

    # duplicate L and R side
    l_side_geo = cmds.duplicate(
        base_mesh, n="{}_{}".format(target_mesh_name, L_keyword)
    )[0]
    r_side_geo = cmds.duplicate(
        base_mesh, n="{}_{}".format(target_mesh_name, R_keyword)
    )[0]

    cmds.setAttr("{}.v".format(l_side_geo), True)
    cmds.setAttr("{}.v".format(r_side_geo), True)

    # copy to l and r side
    for joint_name in [L_joint, R_joint]:
        if joint_name == L_joint:
            target_geo = l_side_geo
        elif joint_name == R_joint:
            target_geo = r_side_geo

        list_key_of_weight = dict_get_weight[joint_name].keys()

        for i in range(source_count):
            if dict_target_geo_vtxs[i] != dict_base_geo_vtxs[i]:
                MSelectionList.clear()
                MSelectionList.add(str(target_geo))
                Target_MDagPath = MSelectionList.getDagPath(0)
                Target_MFnMesh = om.MFnMesh(Target_MDagPath)

                if i in list_key_of_weight:
                    percent = dict_get_weight[joint_name][i]
                else:
                    percent = 0

                base_pos = om.MVector(dict_base_geo_vtxs[i])
                target_pos = om.MVector(dict_target_geo_vtxs[i])
                offset_pos = target_pos - base_pos
                set_pos = base_pos + (offset_pos * percent)

                point = om.MPoint(set_pos)
                Target_MFnMesh.setPoint(i, point)

    return [l_side_geo, r_side_geo]


def mirror_blendshape(axis="x", side_L="L", side_R="R"):
    """
    Use for flip curve shape cv

    """
    if axis == "x":
        mirror_index = 0
    elif axis == "y":
        mirror_index = 1
    elif axis == "z":
        mirror_index = 2

    for source in cmds.ls(sl=1):
        if cmds.objExists(source.replace(side_L, side_R)) and side_L in source:
            bshp_opposite = source.replace(side_L, side_R)
        elif cmds.objExists(source.replace(side_R, side_L)) and side_R in source:
            bshp_opposite = source.replace(side_R, side_L)

        amount_cv_source = cmds.getAttr(source + ".spans") + cmds.getAttr(
            source + ".degree"
        )
        amount_cv_opposite = cmds.getAttr(bshp_opposite + ".spans") + cmds.getAttr(
            bshp_opposite + ".degree"
        )

        for i in range(amount_cv_source):
            source_cv = i
            opposite_cv = (amount_cv_source - 1) - i

            pos_cv_source = cmds.xform(
                "{}.cv[{}]".format(source, source_cv), os=1, q=1, t=1
            )

            pos_cv_source[mirror_index] = pos_cv_source[mirror_index] * -1

            cmds.xform(
                "{}.cv[{}]".format(bshp_opposite, opposite_cv), os=1, t=pos_cv_source
            )


def get_meshes_with_blendshape(blendshape_node):
    """
    Returns a list of mesh transform nodes that are deformed by the given blendShape node.
    """
    if not cmds.objExists(blendshape_node):
        return []

    result = []

    # Get all mesh shape nodes in the scene
    mesh_shapes = cmds.ls(type="mesh")

    for shape in mesh_shapes:
        history = cmds.listHistory(shape, pruneDagObjects=True)
        if blendshape_node in history:
            transform = shape.getParent()
            result.append(transform)

    return result


def get_input_mesh_from_blend_shape(blendshape_node):
    original_geom = cmds.listConnections(
        "{}.originalGeometry[0]".format(blendshape_node), source=True, destination=False
    )

    if original_geom:
        return original_geom[0]
    else:
        raise Exception("Error Blend Shape Node")


def get_blendshapes_from_mesh(mesh_name):
    """
    Finds and returns blendshape deformer nodes connected to a given mesh using cmds.

    Args:
        mesh_name (str): The name of the mesh to inspect.

    Returns:
        list: A list of blendshape node names. Returns an empty list if none are found.
    """

    # Get history of the mesh, filtered by blendShape type
    blendshape_nodes = cmds.listHistory(mesh_name, type="blendShape") or []

    if not blendshape_nodes:
        return []

    return blendshape_nodes


def add_or_create_blend_shape_node_v2(
    list_target_mesh, input_mesh=None, node_name="blendshape"
):

    # find exist input mesh node if not input
    if not input_mesh:
        input_mesh = get_input_mesh_from_blend_shape(node_name)

    # query target all
    list_all_target = cmds.blendShape(node_name, q=1, t=1)

    # create blend shape node method
    if not cmds.objExists(node_name):

        node_name = cmds.blendShape(
            list_target_mesh, input_mesh, n=node_name, o="local", at=True
        )

    # add blend shape node method
    elif cmds.objExists(node_name):

        for target in list_target_mesh:
            list_target_name = cmds.blendShape(node_name, q=True, t=True) or []

            # only add when target not added case
            if target in list_target_name:
                cmds.warning(
                    "Skipped Shape {}, because already exist in {}".format(
                        target, node_name
                    )
                )

            elif not cmds.objExists(target):
                raise Exception("{} Mesh Not Found to Add Blend Shape".format(target))

            else:
                index = len(list_target_name)
                cmds.blendShape(
                    node_name, edit=True, target=(input_mesh, index, target, 1.0)
                )

    return node_name


def add_or_create_blend_shape_node(
    list_target_mesh, input_mesh=None, node_name="blendshape"
):

    # find exist input mesh node if not input
    if not input_mesh:
        input_mesh = get_input_mesh_from_blend_shape(node_name)

    # create blend shape node method
    if not cmds.objExists(node_name):

        node_name = cmds.blendShape(
            list_target_mesh, input_mesh, n=node_name, o="local", at=True
        )

    # add blend shape node method
    elif cmds.objExists(node_name):

        for target in list_target_mesh:
            list_target_name = cmds.blendShape(node_name, q=True, t=True) or []

            # only add when target not added case
            if target not in list_target_name:

                if not cmds.objExists(target):
                    raise Exception(
                        "{} Mesh Not Found to Add Blend Shape".format(target)
                    )

                # index = len(list_target_name)
                # cmds.blendShape(
                #     node_name, edit=True, target=(input_mesh, index, target, 1.0)
                # )

    return node_name


def create_blend_shape(
    bln_child=None, dup_crv=None, name="blinkHeight", attr_height=None
):
    # duplicate target and create blendshape
    crv_target = cmds.duplicate(dup_crv, n="crv_" + name)[0]
    bln_child.append(crv_target)
    blendshape = cmds.blendShape(bln_child)[0]

    node_uc = cmds.shadingNode("unitConversion", au=1, n="uc_" + name)
    cmds.setAttr(node_uc + ".conversionFactor", 0.1)

    # create node and connect attr_height to blendshape
    rev_node = cmds.shadingNode("reverse", au=1, name="rev_" + name)
    cmds.connectAttr(attr_height, node_uc + ".input")
    cmds.connectAttr(node_uc + ".output", blendshape + ".weight[0]")
    cmds.connectAttr(node_uc + ".output", rev_node + ".input.inputX")
    cmds.connectAttr(rev_node + ".output.outputX", blendshape + ".weight[1]")

    return crv_target


def create_node_blendshape(
    curve_lips="crv_main",
    node_name="bshp_curve",
    list_input=["joint.tx", "joint.ty", "joint.tz", "joint.tx", "joint.ty", "joint.tz"],
    add=False,
):
    list_word = ["PosX", "PosY", "PosZ", "NegX", "NegY", "NegZ"]
    list_all_blendshape = [curve_lips + word for word in list_word]
    list_custom_attr = [
        "positiveX",
        "positiveY",
        "positiveZ",
        "negativeX",
        "negativeY",
        "negativeZ",
    ]
    list_enable_attr = [
        "envelopePositiveX",
        "envelopePositiveY",
        "envelopePositiveZ",
        "envelopeNegativeX",
        "envelopeNegativeY",
        "envelopeNegativeZ",
    ]

    list_axis = ["X", "Y", "Z"]
    list_color = ["side_R", "G", "B"]

    [cmds.duplicate(curve_lips, n=name) for name in list_all_blendshape]
    [cmds.setAttr(curve + ".v", 0) for curve in list_all_blendshape]

    # create blendshape
    node_bsn = cmds.blendShape(
        list_all_blendshape, curve_lips, o="local", n=node_name, foc=1
    )[0]

    [
        cmds.addAttr(node_bsn, ln=name, at="float", k=1, dv=1)
        for name in list_custom_attr
    ]
    [
        cmds.addAttr(node_bsn, ln=name, at="float", k=1, dv=1, min=0, max=1)
        for name in list_enable_attr
    ]

    # positive case
    for name in ["positive", "negative"]:
        node_md_divide = cmds.createNode("multiplyDivide", n="md_div{}".format(name))
        node_md_invert = cmds.createNode("multiplyDivide", n="md_invert{}".format(name))
        node_md_mult = cmds.createNode("multiplyDivide", n="md_mult{}".format(name))
        node_clamp = cmds.createNode("clamp", n="clp_{}".format(name))
        node_md_enable = cmds.createNode("multiplyDivide", n="md_enable{}".format(name))

        if name == "positive":
            list_attr_custom = list_custom_attr[0:3]
            list_attr_input = list_input[0:3]
            list_attr_weight = list_all_blendshape[0:3]
            list_attr_envelope = list_enable_attr[0:3]

            cmds.setAttr(node_clamp + ".max", 1, 1, 1, typ="double3")
            cmds.setAttr(node_md_invert + ".input2", 1, 1, 1, typ="double3")

        elif name == "negative":
            list_attr_custom = list_custom_attr[3:6]
            list_attr_input = list_input[3:6]
            list_attr_weight = list_all_blendshape[3:6]
            list_attr_envelope = list_enable_attr[3:6]
            cmds.setAttr(node_clamp + ".min", -1, -1, -1, typ="double3")
            cmds.setAttr(node_md_invert + ".input2", -1, -1, -1, typ="double3")

        else:
            raise Exception("list attr error to find")

        # connect md divide node
        cmds.setAttr("{}.operation".format(node_md_divide), 2)
        cmds.setAttr("{}.input2".format(node_md_divide), 1, 1, 1, typ="double3")
        [
            cmds.connectAttr(
                "{}.{}".format(node_bsn, list_attr_custom[i]),
                "{}.input1{}".format(node_md_divide, list_axis[i]),
            )
            for i in range(3)
        ]

        # connect md mult node
        [
            cmds.connectAttr(
                list_attr_input[i], "{}.input2{}".format(node_md_mult, list_axis[i])
            )
            for i in range(3)
        ]
        cmds.connectAttr(
            "{}.output".format(node_md_divide), "{}.input1".format(node_md_mult)
        )

        # connect clamp node
        [
            cmds.connectAttr(
                "{}.output{}".format(node_md_mult, list_axis[i]),
                "{}.input{}".format(node_clamp, list_color[i]),
            )
            for i in range(3)
        ]

        # fix negative value
        cmds.connectAttr(
            "{}.output".format(node_clamp), "{}.input1".format(node_md_invert)
        )

        # connect md enable node
        cmds.connectAttr(
            "{}.output".format(node_md_invert), "{}.input2".format(node_md_enable)
        )
        [
            cmds.connectAttr(
                "{}.{}".format(node_bsn, list_attr_envelope[i]),
                "{}.input1{}".format(node_md_enable, list_axis[i]),
            )
            for i in range(3)
        ]

        # connect to blendshape weight
        [
            cmds.connectAttr(
                "{}.output{}".format(node_md_enable, list_axis[i]),
                "{}.{}".format(node_bsn, list_attr_weight[i]),
            )
            for i in range(3)
        ]

    return list_all_blendshape


def delete_blendshape_target(blendshape_node, target_name):
    """
    Deletes a specified target from a given blendShape node.

    Args:
        blendshape_node (str): The name of the blendShape node.
        target_name (str): The name of the target to delete.

    Returns:
        bool: True if the target was successfully deleted, False otherwise.
    """
    if not cmds.objExists(blendshape_node):
        cmds.warning(f"BlendShape node '{blendshape_node}' does not exist.")
        return False

    # Get all the weight attributes in the blendShape node
    weight_attributes = cmds.listAttr(f"{blendshape_node}.weight", m=True)
    if not weight_attributes:
        cmds.warning(f"No targets found in blendShape node '{blendshape_node}'.")
        return False

    # Ensure the target exists in the blendShape node
    if target_name not in weight_attributes:
        cmds.warning(
            f"Target '{target_name}' not found in blendShape node '{blendshape_node}'."
        )
        return False

    # Get the index of the target
    target_index = weight_attributes.index(target_name)

    # Remove the blendShape target input
    try:
        cmds.removeMultiInstance(
            f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}]", b=True
        )
    except RuntimeError as e:
        cmds.warning(f"Failed to remove target '{target_name}': {e}")
        return False

    return True


def flip_blendshape_target_by_name(blendshape_node, target_name, axis="x"):
    """Flip Blend Shape Target"""

    if axis not in ["x", "y", "z"]:
        cmds.warning("Invalid axis. Use 'x', 'y', or 'z'.")
        return

    # Get the blendShape geometry
    blendshape_geo = cmds.listConnections(
        f"{blendshape_node}.outputGeometry[0]", source=False, destination=True
    )
    if not blendshape_geo:
        cmds.error("Unable to find blendshape geometry.")
        return

    # Ensure we have the actual shape node
    blendshape_geo = cmds.listRelatives(
        blendshape_geo[0], shapes=True, noIntermediate=True
    )
    if not blendshape_geo:
        cmds.error("Unable to find the valid geometry shape for the blendShape.")
        return

    blendshape_geo = blendshape_geo[0]

    # Find the target index by name
    all_targets = cmds.aliasAttr(blendshape_node, query=True)
    if not all_targets:
        cmds.error("No targets found in the blendShape node.")
        return

    target_index = None
    for i in range(0, len(all_targets), 2):  # Even indices contain target names
        if all_targets[i] == target_name:
            target_index = int(all_targets[i + 1].split("[")[-1][:-1])
            break

    if target_index is None:
        cmds.error(
            f"Target '{target_name}' not found in blendShape node '{blendshape_node}'."
        )
        return

    # Duplicate and flip the target geometry
    flipped_target = cmds.duplicate(blendshape_geo, name=f"{blendshape_geo}_flipped")[0]

    # Flip the geometry along the specified axis
    axis_index = {"x": 0, "y": 1, "z": 2}[axis]
    scale_vector = [1, 1, 1]
    scale_vector[axis_index] = -1
    cmds.scale(scale_vector[0], scale_vector[1], scale_vector[2], flipped_target)
    cmds.makeIdentity(flipped_target, apply=True, scale=True)

    # Reassign flipped geometry as the new blendShape target
    cmds.blendShape(
        blendshape_node,
        edit=True,
        target=(blendshape_geo, target_index, flipped_target, 1.0),
    )

    # Optional cleanup
    cmds.delete(flipped_target)


def get_blendshape_nodes(obj):
    """
    Return all blendShape nodes connected to the given object (including referenced objects).
    """
    # Get shapes (non-intermediate)
    shapes = cmds.listRelatives(obj, shapes=True, noIntermediate=True) or []
    if not shapes:
        return []

    blends = []
    for shape in shapes:
        # Check upstream history
        history = cmds.listHistory(shape, future=False, pruneDagObjects=True) or []
        for node in history:
            if cmds.nodeType(node) == "blendShape" and node not in blends:
                blends.append(node)

        # Direct connections (sometimes safer with references)
        connections = (
            cmds.listConnections(
                shape, type="blendShape", source=True, destination=False
            )
            or []
        )
        for conn in connections:
            if conn not in blends:
                blends.append(conn)

    return blends


def get_blendshape_target_data_as_list(blendshape_node, target_name):
    if not cmds.objExists(blendshape_node):
        cmds.warning(f"BlendShape node '{blendshape_node}' does not exist.")
        return None

    weight_attrs = cmds.listAttr(f"{blendshape_node}.weight", m=True)
    if not weight_attrs or target_name not in weight_attrs:
        cmds.warning(
            f"Target '{target_name}' not found in blendShape node '{blendshape_node}'."
        )
        return None

    target_index = weight_attrs.index(target_name)

    # Get base geometry
    base_geo = cmds.listConnections(
        f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem[6000].inputGeomTarget",
        s=True,
        d=False,
    )
    if base_geo:
        base_geo = base_geo[0]
    else:
        base_geo = None

    # Get target object
    target_obj = cmds.listConnections(
        f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem[6000].inputGeomTarget",
        s=True,
        d=False,
    )
    if target_obj:
        target_obj = target_obj[0]
    else:
        target_obj = None

    # Get weight value
    weight_value = cmds.getAttr(f"{blendshape_node}.weight[{target_index}]")

    return [base_geo, target_index, target_obj, weight_value]


def scan_local_geo_by_name(list_geo_group=[], geo_key_name=[]):
    dict_blendshape_target = {}

    # create dict target key
    for key in geo_key_name:
        dict_blendshape_target[key] = []

    list_group_childs = cmds.listRelatives(list_geo_group, c=1, ad=1, typ="transform")

    # add global mesh to dict data
    for child in list_group_childs:
        for key in dict_blendshape_target.keys():
            if key in str(child):
                dict_blendshape_target[key] = dict_blendshape_target[key] + [child]

    return dict_blendshape_target


def add_multi_local_blendshape(list_geo_group=["FclGeo_Grp"], geo_key_name=[]):
    """
    This function create blend shape for multiple local mesh to main mesh

    Be Aware ! Dectecting Global by Scene Hierarchy , Please Reorder the global geo to come first

    """

    dict_blendshape_target = scan_local_geo_by_name(
        list_geo_group=list_geo_group, geo_key_name=geo_key_name
    )

    # add blendshape and turn on
    for key in dict_blendshape_target.keys():
        if len(dict_blendshape_target[key]) <= 1:
            continue

        input_geo = dict_blendshape_target[key][0]
        list_target_geo = dict_blendshape_target[key][1:]

        # check is already have blendshape
        if get_blendshape_nodes(input_geo):
            cmds.warning(
                "{} is already have blendShape node, skipped to add blendshape".format(
                    input_geo
                )
            )
            continue

        # create blendshape

        node_bs = cmds.blendShape(list_target_geo, input_geo, at=True)[0]
        list_weight_name = cmds.blendShape(node_bs, q=1, target=True)

        for i, name in enumerate(list_weight_name):
            cmds.setAttr("{}.{}".format(node_bs, name, i), 1)
