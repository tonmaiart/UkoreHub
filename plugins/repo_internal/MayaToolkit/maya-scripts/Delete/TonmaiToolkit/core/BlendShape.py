from TonmaiToolkit.core import Misc, Utility, QuickData, File
from TonmaiToolkit import config
import pymel.core as pm
import maya.api.OpenMaya as om
import os
import maya.cmds as mc


def rename_blendshape_target(blendshape_node, old_name, new_name):
    aliases = mc.aliasAttr(blendshape_node, q=True) or []
    for i in range(0, len(aliases), 2):
        if aliases[i] == old_name:
            plug = f"{blendshape_node}.{aliases[i+1]}"
            # remove old alias first
            mc.aliasAttr(plug, remove=True)
            # set new alias
            mc.aliasAttr(new_name, plug)
            return
    mc.warning(f"Target '{old_name}' not found in {blendshape_node}")


def create_operated_corrective_shape(
    object_A="base", object_B="target", operation="add"
):

    def get_vertex_positions_from_duplicate(obj_name):
        """Duplicate an object, get its vertex positions, then delete the duplicate."""
        dup = pm.duplicate(obj_name, name="tmp_vtx_extract")[0]
        positions = {}
        vtx_count = pm.polyEvaluate(dup, vertex=True)

        for i in range(vtx_count):
            pos = pm.xform(f"{dup}.vtx[{i}]", q=1, os=1, t=True)
            positions[i] = tuple(pos)

        pm.delete(dup)  # delete the temporary duplicate
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

    obj_result = pm.duplicate(object_A)[0]

    for i, pos in enumerate(vtxs_result):
        pm.xform("{}.vtx[{}]".format(obj_result, i), os=1, t=pos)

    pm.select(obj_result)

    try:
        pm.setAttr(obj_result + ".v", True)
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

    target_mesh_node = pm.PyNode(target_mesh)
    target_mesh_name = target_mesh_node.shortName()
    base_mesh_node = pm.PyNode(base_mesh)
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
            pm.error("Please Export Skin of {} First.".format(split_weight_mesh))

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
            pm.error("L joint and R joint not found in .json file.")

        # create new dict
        dict_get_weight[joint_name] = []
        new_dict = {}

        for each_dict in dict_weight["points"]:
            new_dict[each_dict["index"]] = each_dict["value"]

        dict_get_weight[joint_name] = new_dict

    # duplicate L and R side
    l_side_geo = pm.duplicate(base_mesh, n="{}_{}".format(target_mesh_name, L_keyword))[
        0
    ]
    r_side_geo = pm.duplicate(base_mesh, n="{}_{}".format(target_mesh_name, R_keyword))[
        0
    ]

    pm.setAttr("{}.v".format(l_side_geo), True)
    pm.setAttr("{}.v".format(r_side_geo), True)

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


def mirror_blendshape(axis="x"):
    """
    Use for flip curve shape cv

    """
    if axis == "x":
        mirror_index = 0
    elif axis == "y":
        mirror_index = 1
    elif axis == "z":
        mirror_index = 2

    for source in pm.ls(sl=1):
        if pm.objExists(source.replace(config.L, config.R)) and config.L in source:
            bshp_opposite = source.replace(config.L, config.R)
        elif pm.objExists(source.replace(config.R, config.L)) and config.R in source:
            bshp_opposite = source.replace(config.R, config.L)

        amount_cv_source = pm.getAttr(source + ".spans") + pm.getAttr(
            source + ".degree"
        )
        amount_cv_opposite = pm.getAttr(bshp_opposite + ".spans") + pm.getAttr(
            bshp_opposite + ".degree"
        )

        for i in range(amount_cv_source):
            source_cv = i
            opposite_cv = (amount_cv_source - 1) - i

            pos_cv_source = pm.xform(
                "{}.cv[{}]".format(source, source_cv), os=1, q=1, t=1
            )

            pos_cv_source[mirror_index] = pos_cv_source[mirror_index] * -1

            pm.xform(
                "{}.cv[{}]".format(bshp_opposite, opposite_cv), os=1, t=pos_cv_source
            )


def get_meshes_with_blendshape(blendshape_node):
    """
    Returns a list of mesh transform nodes that are deformed by the given blendShape node.
    """
    if not pm.objExists(blendshape_node):
        return []

    result = []

    # Get all mesh shape nodes in the scene
    mesh_shapes = pm.ls(type="mesh")

    for shape in mesh_shapes:
        history = pm.listHistory(shape, pruneDagObjects=True)
        if blendshape_node in history:
            transform = shape.getParent()
            result.append(transform)

    return result


def get_input_mesh_from_blend_shape(blendshape_node):
    original_geom = pm.listConnections(
        "{}.originalGeometry[0]".format(blendshape_node), source=True, destination=False
    )

    if original_geom:
        return original_geom[0]
    else:
        raise Exception("Error Blend Shape Node")


def get_blendshapes_from_mesh(mesh_name):
    """
    Finds and returns blendshape deformer nodes connected to a given mesh using PyMEL.

    Args:
        mesh_name (str): The name of the mesh to inspect.

    Returns:
        list: A list of PyMEL BlendShape nodes. Returns an empty list if none are found.
    """

    if not Utility.is_py_node(mesh_name):
        mesh_node = pm.PyNode(mesh_name)
    else:
        mesh_node = mesh_name

    # Find nodes of type 'BlendShape' in the mesh's history
    # The 'isinstance' check is a more robust and Pythonic way to filter node types
    blendshape_nodes = [
        node
        for node in mesh_node.history()
        if isinstance(node, pm.nodetypes.BlendShape)
    ]

    if not blendshape_nodes:
        False

    return blendshape_nodes


def add_or_create_blend_shape_node_v2(
    list_target_mesh, input_mesh=None, node_name="blendshape"
):

    # find exist input mesh node if not input
    if not input_mesh:
        input_mesh = get_input_mesh_from_blend_shape(node_name)

    # query target all
    list_all_target = pm.blendShape(node_name, q=1, t=1)

    # create blend shape node method
    if not pm.objExists(node_name):

        node_name = pm.blendShape(
            list_target_mesh, input_mesh, n=node_name, o="local", at=True
        )

    # add blend shape node method
    elif pm.objExists(node_name):

        for target in list_target_mesh:
            list_target_name = pm.blendShape(node_name, q=True, t=True) or []

            # only add when target not added case
            if target in list_target_name:
                pm.warning(
                    "Skipped Shape {}, because already exist in {}".format(
                        target, node_name
                    )
                )

            elif not pm.objExists(target):
                raise Exception("{} Mesh Not Found to Add Blend Shape".format(target))

            else:
                index = len(list_target_name)
                pm.blendShape(
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
    if not pm.objExists(node_name):

        node_name = pm.blendShape(
            list_target_mesh, input_mesh, n=node_name, o="local", at=True
        )

    # add blend shape node method
    elif pm.objExists(node_name):

        for target in list_target_mesh:
            list_target_name = pm.blendShape(node_name, q=True, t=True) or []

            # only add when target not added case
            if target not in list_target_name:

                if not pm.objExists(target):
                    raise Exception(
                        "{} Mesh Not Found to Add Blend Shape".format(target)
                    )

                # index = len(list_target_name)
                # pm.blendShape(
                #     node_name, edit=True, target=(input_mesh, index, target, 1.0)
                # )

    return node_name


def create_blend_shape(
    bln_child=None, dup_crv=None, name="blinkHeight", attr_height=None
):
    # duplicate target and create blendshape
    crv_target = pm.duplicate(dup_crv, n="crv_" + name)[0]
    bln_child.append(crv_target)
    blendshape = pm.blendShape(bln_child)[0]

    node_uc = pm.shadingNode("unitConversion", au=1, n="uc_" + name)
    pm.setAttr(node_uc + ".conversionFactor", 0.1)

    # create node and connect attr_height to blendshape
    rev_node = pm.shadingNode("reverse", au=1, name="rev_" + name)
    pm.connectAttr(attr_height, node_uc + ".input")
    pm.connectAttr(node_uc + ".output", blendshape + ".weight[0]")
    pm.connectAttr(node_uc + ".output", rev_node + ".input.inputX")
    pm.connectAttr(rev_node + ".output.outputX", blendshape + ".weight[1]")

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
    list_color = ["config.R", "G", "B"]

    [pm.duplicate(curve_lips, n=name) for name in list_all_blendshape]
    [pm.setAttr(curve + ".v", 0) for curve in list_all_blendshape]

    # create blendshape
    node_bsn = pm.blendShape(
        list_all_blendshape, curve_lips, o="local", n=node_name, foc=1
    )[0]

    [pm.addAttr(node_bsn, ln=name, at="float", k=1, dv=1) for name in list_custom_attr]
    [
        pm.addAttr(node_bsn, ln=name, at="float", k=1, dv=1, min=0, max=1)
        for name in list_enable_attr
    ]

    # positive case
    for name in ["positive", "negative"]:
        node_md_divide = pm.createNode("multiplyDivide", n="md_div{}".format(name))
        node_md_invert = pm.createNode("multiplyDivide", n="md_invert{}".format(name))
        node_md_mult = pm.createNode("multiplyDivide", n="md_mult{}".format(name))
        node_clamp = pm.createNode("clamp", n="clp_{}".format(name))
        node_md_enable = pm.createNode("multiplyDivide", n="md_enable{}".format(name))

        if name == "positive":
            list_attr_custom = list_custom_attr[0:3]
            list_attr_input = list_input[0:3]
            list_attr_weight = list_all_blendshape[0:3]
            list_attr_envelope = list_enable_attr[0:3]

            pm.setAttr(node_clamp + ".max", 1, 1, 1, typ="double3")
            pm.setAttr(node_md_invert + ".input2", 1, 1, 1, typ="double3")

        elif name == "negative":
            list_attr_custom = list_custom_attr[3:6]
            list_attr_input = list_input[3:6]
            list_attr_weight = list_all_blendshape[3:6]
            list_attr_envelope = list_enable_attr[3:6]
            pm.setAttr(node_clamp + ".min", -1, -1, -1, typ="double3")
            pm.setAttr(node_md_invert + ".input2", -1, -1, -1, typ="double3")

        else:
            raise Exception("list attr error to find")

        # connect md divide node
        pm.setAttr("{}.operation".format(node_md_divide), 2)
        pm.setAttr("{}.input2".format(node_md_divide), 1, 1, 1, typ="double3")
        [
            pm.connectAttr(
                "{}.{}".format(node_bsn, list_attr_custom[i]),
                "{}.input1{}".format(node_md_divide, list_axis[i]),
            )
            for i in range(3)
        ]

        # connect md mult node
        [
            pm.connectAttr(
                list_attr_input[i], "{}.input2{}".format(node_md_mult, list_axis[i])
            )
            for i in range(3)
        ]
        pm.connectAttr(
            "{}.output".format(node_md_divide), "{}.input1".format(node_md_mult)
        )

        # connect clamp node
        [
            pm.connectAttr(
                "{}.output{}".format(node_md_mult, list_axis[i]),
                "{}.input{}".format(node_clamp, list_color[i]),
            )
            for i in range(3)
        ]

        # fix negative value
        pm.connectAttr(
            "{}.output".format(node_clamp), "{}.input1".format(node_md_invert)
        )

        # connect md enable node
        pm.connectAttr(
            "{}.output".format(node_md_invert), "{}.input2".format(node_md_enable)
        )
        [
            pm.connectAttr(
                "{}.{}".format(node_bsn, list_attr_envelope[i]),
                "{}.input1{}".format(node_md_enable, list_axis[i]),
            )
            for i in range(3)
        ]

        # connect to blendshape weight
        [
            pm.connectAttr(
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
    if not pm.objExists(blendshape_node):
        pm.warning(f"BlendShape node '{blendshape_node}' does not exist.")
        return False

    # Get all the weight attributes in the blendShape node
    weight_attributes = pm.listAttr(f"{blendshape_node}.weight", m=True)
    if not weight_attributes:
        pm.warning(f"No targets found in blendShape node '{blendshape_node}'.")
        return False

    # Ensure the target exists in the blendShape node
    if target_name not in weight_attributes:
        pm.warning(
            f"Target '{target_name}' not found in blendShape node '{blendshape_node}'."
        )
        return False

    # Get the index of the target
    target_index = weight_attributes.index(target_name)

    # Remove the blendShape target input
    try:
        pm.removeMultiInstance(
            f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}]", b=True
        )
    except RuntimeError as e:
        pm.warning(f"Failed to remove target '{target_name}': {e}")
        return False

    return True


def flip_blendshape_target_by_name(blendshape_node, target_name, axis="x"):
    """Flip Blend Shape Target"""

    if axis not in ["x", "y", "z"]:
        pm.warning("Invalid axis. Use 'x', 'y', or 'z'.")
        return

    # Get the blendShape geometry
    blendshape_geo = pm.listConnections(
        f"{blendshape_node}.outputGeometry[0]", source=False, destination=True
    )
    if not blendshape_geo:
        pm.error("Unable to find blendshape geometry.")
        return

    # Ensure we have the actual shape node
    blendshape_geo = pm.listRelatives(
        blendshape_geo[0], shapes=True, noIntermediate=True
    )
    if not blendshape_geo:
        pm.error("Unable to find the valid geometry shape for the blendShape.")
        return

    blendshape_geo = blendshape_geo[0]

    # Find the target index by name
    all_targets = pm.aliasAttr(blendshape_node, query=True)
    if not all_targets:
        pm.error("No targets found in the blendShape node.")
        return

    target_index = None
    for i in range(0, len(all_targets), 2):  # Even indices contain target names
        if all_targets[i] == target_name:
            target_index = int(all_targets[i + 1].split("[")[-1][:-1])
            break

    if target_index is None:
        pm.error(
            f"Target '{target_name}' not found in blendShape node '{blendshape_node}'."
        )
        return

    # Duplicate and flip the target geometry
    flipped_target = pm.duplicate(blendshape_geo, name=f"{blendshape_geo}_flipped")[0]

    # Flip the geometry along the specified axis
    axis_index = {"x": 0, "y": 1, "z": 2}[axis]
    scale_vector = [1, 1, 1]
    scale_vector[axis_index] = -1
    pm.scale(scale_vector[0], scale_vector[1], scale_vector[2], flipped_target)
    pm.makeIdentity(flipped_target, apply=True, scale=True)

    # Reassign flipped geometry as the new blendShape target
    pm.blendShape(
        blendshape_node,
        edit=True,
        target=(blendshape_geo, target_index, flipped_target, 1.0),
    )

    # Optional cleanup
    pm.delete(flipped_target)


def get_blendshape_nodes(obj):
    """
    Return all blendShape nodes connected to the given object (including referenced objects).
    """
    if not isinstance(obj, pm.PyNode):
        obj = pm.PyNode(obj)

    # Get shapes (non-intermediate)
    shapes = obj.getShapes(noIntermediate=True)
    if not shapes:
        return []

    blends = []
    for shape in shapes:
        # Check upstream history
        history = shape.listHistory(future=False, pruneDagObjects=True)
        for node in history:
            if isinstance(node, pm.nodetypes.BlendShape) and node not in blends:
                blends.append(node)

        # Direct connections (sometimes safer with references)
        for conn in shape.inputs(type="blendShape"):
            if conn not in blends:
                blends.append(conn)

    return blends


def get_blendshape_target_data_as_list(blendshape_node, target_name):
    if not pm.objExists(blendshape_node):
        pm.warning(f"BlendShape node '{blendshape_node}' does not exist.")
        return None

    weight_attrs = pm.listAttr(f"{blendshape_node}.weight", m=True)
    if not weight_attrs or target_name not in weight_attrs:
        pm.warning(
            f"Target '{target_name}' not found in blendShape node '{blendshape_node}'."
        )
        return None

    target_index = weight_attrs.index(target_name)

    # Get base geometry
    base_geo = pm.listConnections(
        f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem[6000].inputGeomTarget",
        s=True,
        d=False,
    )
    if base_geo:
        base_geo = base_geo[0]
    else:
        base_geo = None

    # Get target object
    target_obj = pm.listConnections(
        f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem[6000].inputGeomTarget",
        s=True,
        d=False,
    )
    if target_obj:
        target_obj = target_obj[0]
    else:
        target_obj = None

    # Get weight value
    weight_value = pm.getAttr(f"{blendshape_node}.weight[{target_index}]")

    return [base_geo, target_index, target_obj, weight_value]


def query_all_blend_shape_input(blendshape_name):
    try:
        blendshape = pm.PyNode(blendshape_name)
        if blendshape.type() != "blendShape":
            return

        alias_list = pm.aliasAttr(
            blendshape, query=True
        )  # returns [alias1, attr1, alias2, attr2, ...]
        if not alias_list:
            return

        # Extract only the alias names (every even index)
        target_names = alias_list[::2]

        return target_names

    except Exception as e:
        print("Error:", e)


def scan_local_geo_by_name(list_geo_group=[], geo_key_name=[]):
    dict_blendshape_target = {}

    # create dict target key
    for key in geo_key_name:
        dict_blendshape_target[key] = []

    list_group_childs = pm.listRelatives(list_geo_group, c=1, ad=1, typ="transform")

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
            pm.warning(
                "{} is already have blendShape node, skipped to add blendshape".format(
                    input_geo
                )
            )
            continue

        # create blendshape

        node_bs = pm.blendShape(list_target_geo, input_geo, at=True)[0]
        list_weight_name = pm.blendShape(node_bs, q=1, target=True)

        for i, name in enumerate(list_weight_name):
            pm.setAttr("{}.{}".format(node_bs, name, i), 1)
