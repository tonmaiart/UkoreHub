from tmlib.core import Scene, Transform, Utility, Connection, Create
import maya.api.OpenMaya as om
import maya.cmds as cmds
import math


def create_control(
    name,
    axis="y",
    size=1.0,
    match=None,
    constraint=None,
    parent=None,
    roo=None,
    guide_ball=None,
    matchGimbal=True,
    mirror_freeze_group=False,
    freeze_group=False,
    connect_match=False,
    display_rotate_order=False,
    connect_rotate_order=True,
    color="red",
    shape="cube",
):
    """
    This function create controller
    """

    dict_normal_vector = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}

    # create control
    if cmds.objExists(name):
        raise Exception("node_name : {} is already exist in scene".format(name))

    # defalut shape
    cmds.circle(ch=False, n=name, nr=dict_normal_vector[Scene.del_neg(axis)])

    # add attribute rotate order
    if display_rotate_order:
        cmds.setAttr("{}.rotateOrder".format(name), cb=1)
        cmds.setAttr("{}.rotateOrder".format(name), k=1)

    if connect_rotate_order and constraint:
        cmds.connectAttr("{}.rotateOrder".format(name), "{}.rotateOrder".format(match))

    # guide ball case
    if guide_ball:
        cmds.matchTransform(name, guide_ball, scl=1)

    # customize shape and color
    if shape == "cube":
        clone_shape([name, "ThreeD_Cube"])
    elif shape == "sphere":
        clone_shape([name, "ThreeD_Sphere"])
    else:
        raise Exception("Invalid Input Shape")

    if color == "red":
        set_curve_color(list_target=[name], rgb=[1, 0, 0])
    elif color == "blue":
        set_curve_color(list_target=[name], rgb=[0, 0, 1])
    elif color == "green":
        set_curve_color(list_target=[name], rgb=[0, 1, 0])
    elif color == "yellow":
        set_curve_color(list_target=[name], rgb=[1, 1, 0])
    elif color == "purple":
        set_curve_color(list_target=[name], rgb=[1, 0, 1])
    elif color == "aqua":
        set_curve_color(list_target=[name], rgb=[0, 1, 1])
    else:
        raise Exception("Invalid Input Color")

    cmds.makeIdentity(name, a=1, s=1)
    cmds.xform(name, ws=1, s=(size, size, size))
    cmds.makeIdentity(name, a=1, s=1)

    # set rotate order line width and color
    if roo:
        set_rotate_order([name], rotate_order=roo)
    elif matchGimbal and match:
        try:
            cmds.setAttr(name + ".rotateOrder", cmds.getAttr(match + ".rotateOrder"))
        except:
            pass

    # optional : match to given
    if match:
        cmds.matchTransform(name, match)

    # optional : freeze
    if freeze_group:
        grp_frz = freeze_group_classic(name, custom_freeze_group_name)[0]

        # optional : mirror scale
        if mirror_freeze_group:
            cmds.setAttr("{}.s".format(grp_frz), -1, -1, -1, typ="double3")
    # optional : parent to given
    if parent is not None:
        if freeze_group:
            cmds.parent(grp_frz, parent)
        else:
            cmds.parent(name, parent)

    # optional : connect to match
    if connect_match:
        Connection.connect(name, match, typ="all")

    # optional : constraint to match
    if constraint == "point":
        cmds.pointConstraint(name, match, mo=0)
    elif constraint == "orient":
        cmds.orientConstraint(name, match, mo=0)
    elif constraint == "parent":
        cmds.parentConstraint(name, match, mo=0)
    elif constraint == "scale":
        cmds.scaleConstraint(name, match, mo=0)

    return name


def create_null_shape(object, name):
    # create locator
    node_shape = cmds.createNode("nurbsSurface", n=name)
    node_transform = cmds.listRelatives(node_shape, p=1, f=1)[0]

    cmds.setAttr(node_shape + ".v", 0)

    # parent shape to object
    cmds.parent(node_shape, object, s=1, r=1)
    cmds.delete(node_transform)

    # generate class_instance to rename
    object_path = (
        cmds.listRelatives(object, p=1, f=1)[0]
        if cmds.listRelatives(object, p=1, f=1)
        else object
    )
    return_path = "{}|{}".format(object, Scene.cut(node_shape))

    return return_path


def create_wrap_pin(
    wrap_mesh="",
    pin_transform=[],
    method=0,
    custom_wrap_mesh="",
    auto_uv=False,
    use_rotate=True,
):
    """Connect pin transform to given object (use wrap deformer to prevent uv changing) , pin postion

    method
    0 - Connect to given transform and maintain old transform

    """

    # create return group
    grp_output = cmds.group(em=1, n="{}_output".format(wrap_mesh))
    grp_no_transform = cmds.group(em=1, n="{}_wrap_no_transform".format(wrap_mesh))

    # create / get wrap geo
    if custom_wrap_mesh:
        wrap_geo = custom_wrap_mesh
    else:
        wrap_geo = cmds.duplicate(wrap_mesh, n=wrap_mesh + "_wrap_output")[0]

    # auto unwrap uv
    if auto_uv:
        shape = cmds.listRelatives(wrap_geo, shapes=True)[0]
        cmds.polyAutoProjection(shape, ch=True)

    # create wrap deformer
    wrap_deformer, wrap_base = create_wrap_deformer(wrap_geo, wrap_mesh)

    if custom_wrap_mesh:
        cmds.parent(wrap_base, grp_no_transform)
    else:
        cmds.parent(wrap_geo, wrap_base, grp_no_transform)

    # create uv pin node
    node_uv_pin = create_uv_pin(wrap_geo)

    for i, transform in enumerate(pin_transform):
        # node_decomp = cmds.createNode("decomposeMatrix")
        node_pick_matrix = cmds.createNode("pickMatrix")

        grp_pin_output = cmds.group(em=1, p=grp_output)

        u, v = Transform.get_nearest_polygon_parameter(wrap_geo, transform)
        cmds.setAttr("{}.coordinate[{}].coordinateU.".format(node_uv_pin, i), u)
        cmds.setAttr("{}.coordinate[{}].coordinateV".format(node_uv_pin, i), v)

        cmds.connectAttr(
            "{}.outputMatrix[{}]".format(node_uv_pin, i),
            "{}.inputMatrix".format(node_pick_matrix),
        )
        cmds.connectAttr(
            "{}.outputMatrix".format(node_pick_matrix),
            "{}.offsetParentMatrix".format(grp_pin_output),
        )

        node_pick_matrix.useRotate.set(use_rotate)
        cmds.parent(transform, grp_pin_output)
        # cmds.pointConstraint(grp_pin_output,transform,mo=1)

    return grp_output, grp_no_transform


def create_freeze_group(
    selection, typ="grp", match_rotate_order=True, match_object=None, rename=None
):
    """
    match_object : Match to given object name

    """
    list_type = ["grp", "loc", "jnt", "ctrl"]

    def get_offset_group_name(object):
        # detect type in selection
        replace_type = None
        for word in object.split("_"):
            if word in list_type:
                replace_type = word
                break

        # Create a new group with a specific naming convention
        if rename:  # rename case
            grp_freeze_name = rename
        elif replace_type:  # auto replace case
            grp_freeze_name = object.replace(replace_type, typ)
        else:  # append case
            grp_freeze_name = "{}_{}".format(obj, typ)

        # check word in scene
        if cmds.objExists(grp_freeze_name):
            raise Exception(
                'Freeze Group Output Name "{}" already exist in the scene, please change to others typ'.format(
                    grp_freeze_name
                )
            )

        return grp_freeze_name

    def match_rotate_order_func():
        if not match_rotate_order:
            return

        cmds.setAttr(grp_freeze + ".rotateOrder", cmds.getAttr(obj + ".rotateOrder"))

    def match_object_func():
        if match_object:
            cmds.parent(grp_freeze, match_object)
        else:
            cmds.parent(grp_freeze, obj)

        # match to target
        Transform.reset_transform(grp_freeze)
        cmds.parent(grp_freeze, w=1)

    if not selection:
        raise Exception("No Input Given.")

    list_output_offset_group = []

    for obj in selection:
        grp_freeze = cmds.group(em=True, n=get_offset_group_name(object=obj))

        match_rotate_order_func()  # match rotate order
        match_object_func()  # match position , rotate and scale

        # parent freeze group under obj parent
        parent_obj = cmds.listRelatives(obj, p=1, f=1)
        (
            cmds.parent(grp_freeze, parent_obj[0]) if parent_obj else None
        )  # parent to its parent

        # Parent the object under the freeze group
        cmds.parent(obj, grp_freeze)

        list_output_offset_group.append(grp_freeze)

    return list_output_offset_group


def draw_curve(
    list_items, curve_name, parent=None, rebuild=True, d=3, s=5, rebuild_degree=3
):
    list_bind_pos = [cmds.xform(pos, ws=1, t=1, q=1) for pos in list_items]
    curve = cmds.curve(p=list_bind_pos, n=curve_name, d=d)

    if parent:
        cmds.parent(curve, parent)

    if rebuild:
        return_curve = cmds.rebuildCurve(
            curve,
            ch=0,
            rpo=1,
            rt=0,
            end=1,
            kr=0,
            kcp=0,
            kep=1,
            kt=0,
            s=s,
            d=rebuild_degree,
            tol=0,
        )[0]
    else:
        return_curve = curve

    return return_curve


def draw_nurbs(
    list_ref_object,
    name="newSurface",
    rebuild=False,
    parent=None,
    loftDegree=1,
    d=1,
    sv=4,
    su=1,
    du=1,
    dv=1,
    size=3,
):
    """This function create ribbon plane reference position from list of input"""

    # create curve along the input list
    curve1 = draw_curve(
        list_items=list_ref_object, curve_name="crv1", d=d, rebuild=False
    )
    curve2 = draw_curve(
        list_items=list_ref_object, curve_name="crv2", d=d, rebuild=False
    )

    for curve in [curve1, curve2]:
        if curve == curve1:
            move = size / 2
        elif curve == curve2:
            move = -(size / 2)
        cv_amount = cmds.getAttr(curve + ".spans") + cmds.getAttr(curve + ".degree")
        cmds.select("{}.cv[0:{}]".format(curve, cv_amount - 1))
        cmds.move(move, x=1, ls=1, cs=1, wd=1, r=1)
    cmds.select(cl=1)

    # loft surface from curve
    ribbon = cmds.loft(curve1, curve2, ch=0, rb=0, d=loftDegree, n=name)
    cmds.delete(curve1, curve2)

    # parent to new one
    if parent:
        cmds.parent(ribbon, parent)

    # rebuild curve
    if rebuild:
        cmds.rebuildSurface(ribbon, ch=0, rpo=1, su=su, du=du, sv=sv, dv=dv, kr=0)

    # reverse u and v
    cmds.reverseSurface(ribbon, d=3, ch=0, rpo=1)

    return ribbon[0]


def insert_joint(list_joint, count, typ=0, rename=None):
    list_return = []

    for parent in list_joint:
        recent_jnt = None

        pos_parent = cmds.xform(parent, t=1, ws=1, q=1)
        rad_parent = cmds.getAttr(parent + ".radius")

        child = cmds.listRelatives(parent, typ="joint", c=1)[0]
        pos_child = cmds.xform(child, t=1, ws=1, q=1)

        for i in range(count):
            tmp_crv = cmds.curve(d=1, p=[pos_parent, pos_child])
            poc = cmds.createNode("pointOnCurveInfo")
            cmds.connectAttr(
                tmp_crv + ".worldSpace[0]", poc + ".inputCurve", force=True
            )

            cmds.select(cl=1)
            jnt = cmds.joint(n=cut(parent) + "_twist_" + str(i + 1).zfill(2))

            list_return.append(jnt)
            cmds.setAttr(jnt + ".radius", rad_parent)

            cmds.connectAttr(poc + ".position", jnt + ".translate", force=True)
            param = (1 / (count + 1)) * (i + 1)
            cmds.setAttr(poc + ".parameter", param)

            cmds.matchTransform(jnt, parent, rot=1, scl=0, pos=0)
            cmds.makeIdentity(jnt, r=1, a=1, jo=0)
            cmds.delete(tmp_crv)

            if typ == 0:  # parent to parent
                cmds.parent(jnt, parent)

            elif typ == 1:  # chain parent"
                if recent_jnt == None:
                    cmds.parent(jnt, parent)
                else:
                    cmds.parent(jnt, recent_jnt)
                recent_jnt = jnt

        if len(list_joint) == 1:
            cmds.parent(child, recent_jnt)

    if rename is not None:
        for i, jnt in enumerate(list_return):
            list_return[i] = cmds.rename(jnt, rename[i])

    return list_return


def create_rivet(target):
    """"""

    if ".vtx" not in str(target):
        target = "{}.vtx[0]".format(str(target))

    cmds.select(target)

    cmds.Rivet()
    # uvPinOut = cmds.ls(sl=True, l=1)
    # uvPin = uvPinOut.pop(0)
    # return [uvPin, uvPinOut]


def create_uv_pin(transform=None, components=[0]):
    """
    This function creates uvPin-constrained Locators on specified objects and components
    object is provided by the kwarg name (string)
    components are provided by kwarg components (mesh objects (list): [int], nurbsSurface objects (list of lists): [[int,int]])
    """

    if Utility.is_py_node(transform):
        transform_node = cmds.PyNode(transform)
    else:
        transform_node = transform

    # check if there already is a shape origin node
    shapeOrig = None
    shapes = cmds.listRelatives(transform_node, c=True, s=True)

    if len(shapes) > 1:
        for s in shapes:
            io = cmds.getAttr("{0}.intermediateObject".format(s))
            if io == 1:
                shapeOrig = s
            else:
                shape = s

    # check if the shapes are the right type
    typ = cmds.objectType(shapes[0])

    # defining attriubtes based on objectType
    if typ == "mesh":
        componentPrefix = ".vtx"
        cAttr = ".inMesh"
        cAttr2 = ".worldMesh[0]"
        cAttr3 = ".outMesh"
    elif typ == "nurbsSurface":
        componentPrefix = ".cv"
        cAttr = ".create"
        cAttr2 = ".worldSpace[0]"
        cAttr3 = ".local"
        if components == [0]:
            components = [[0, 0]]
    elif typ == "nurbsCurve":
        componentPrefix = ".cv"
        cAttr = ".create"
        cAttr2 = ".worldSpace[0]"
        cAttr3 = ".local"
        if components == [0]:
            components = [[0, 1]]
    else:
        cmds.error("object provided needs to be Mesh or Nurbssurface")

    # create shape origin if there isn't one
    if shapeOrig == None:
        shape = shapes[0]
        dup = cmds.duplicate(shape)
        shapeOrig = cmds.listRelatives(dup, c=True, s=True)
        cmds.parent(shapeOrig, transform_node, s=True, r=True)
        cmds.delete(dup)
        shapeOrig = cmds.rename(shapeOrig, "{0}Orig".format(shape))

        # check if inMesh attr has connection
        inConn = cmds.listConnections(
            "{0}{1}".format(shape, cAttr), p=True, c=True, d=True
        )

        if inConn:
            cmds.connectAttr(inConn[0], "{0}{1}".format(shapeOrig, cAttr))

        cmds.connectAttr(
            "{0}{1}".format(shapeOrig, cAttr2), "{0}{1}".format(shape, cAttr), f=True
        )
        cmds.setAttr("{0}.intermediateObject".format(shapeOrig), 1)

    # create uvPin Node
    pin = cmds.createNode("uvPin", name="{0}_uvPin".format(transform_node))

    cmds.connectAttr("{0}{1}".format(shape, cAttr2), "{0}.deformedGeometry".format(pin))
    cmds.connectAttr(
        "{0}{1}".format(shapeOrig, cAttr3), "{0}.originalGeometry".format(pin)
    )

    return pin


def draw_curve_circle(list_object, start_cv_index=0, name="curve"):
    circle_transform = cmds.circle(s=len(list_object), ch=0, n=name, d=1)[0]
    circle_shape = cmds.listRelatives(circle_transform, c=1, s=1)[0]

    cv_amount = cmds.getAttr(circle_shape + ".spans")

    # match cv position
    for i in range(cv_amount):
        pos = cmds.xform(list_object[i], q=1, t=1, ws=1)
        cmds.xform("{}.cv[{}]".format(circle_shape, i), t=pos, ws=1)

    # match last cv to the first cv
    pos = cmds.xform(list_object[0], q=1, t=1, ws=1)
    cmds.xform("{}.cv[{}]".format(circle_shape, cv_amount), t=pos, ws=1)

    return circle_transform


def create_sticky_gpt(
    list_base_position,
    list_zipped_position,
    list_zipped_output,
    list_attr_zip,
    list_attr_distance,
    name="sticky",
    offset=0,
    unit_conversion=10,
):
    """
    Constraint-based sticky lips (simplified).
    Supports left/right zipper attributes and odd/even counts.
    """

    count = len(list_base_position)
    half = int(math.ceil(count / 2.0))
    isOdd = count % 2 != 0

    # --- unit conversion ---
    def convert(attr):
        uc = cmds.createNode("unitConversion", n=f"{name}_uc")
        uc.conversionFactor.set(1.0 / unit_conversion)
        attr >> uc.input
        return uc.output

    left_zip, right_zip = [convert(a) for a in list_attr_zip]
    left_dist, right_dist = list_attr_distance

    # --- build sticky side ---
    def build_side(attr_zip, attr_dist, side_tag):
        remap = cmds.createNode("remapValue", n=f"{name}_{side_tag}_rmv")
        remap.outputMax.set(half + 1)
        remap.inputMax.set(1)
        attr_zip >> remap.inputValue

        clamps = []
        for i in range(half):
            md = cmds.createNode("multDoubleLinear", n=f"{name}_{side_tag}{i}_mdl")
            adl = cmds.createNode("addDoubleLinear", n=f"{name}_{side_tag}{i}_adl")
            pma = cmds.createNode("plusMinusAverage", n=f"{name}_{side_tag}{i}_pma")
            cmp = cmds.createNode("clamp", n=f"{name}_{side_tag}{i}_cmp")

            md.input1.set(i + offset)
            attr_dist >> md.input2
            md.output >> adl.input2
            remap.outValue >> pma.input1D[0]
            adl.output >> pma.input1D[1]
            pma.output1D >> cmp.inputR
            cmp.maxR.set(1)

            clamps.append(cmp)
        return clamps

    left_clamps = build_side(left_zip, left_dist, "L")
    right_clamps = build_side(right_zip, right_dist, "R")

    # --- connect constraint ---
    def connect(base, zipped, output, driver, tag):
        cns = cmds.parentConstraint(base, zipped, output, mo=1, n=f"{name}_{tag}_pC")[0]
        w = cmds.parentConstraint(cns, q=1, wal=1)
        driver.outputR >> cns.attr(w[1])

        rev = cmds.createNode("reverse", n=f"{name}_{tag}_rev")
        driver.outputR >> rev.inputX
        rev.outputX >> cns.attr(w[0])

    # right side
    for i, cmp in enumerate(right_clamps[:-1] if isOdd else right_clamps):
        connect(
            list_base_position[i],
            list_zipped_position[i],
            list_zipped_output[i],
            cmp,
            f"R{i}",
        )

    # left side
    for i, cmp in enumerate(left_clamps[:-1] if isOdd else left_clamps):
        j = -(i + 1)
        connect(
            list_base_position[j],
            list_zipped_position[j],
            list_zipped_output[j],
            cmp,
            f"L{i}",
        )

    # center if odd
    if isOdd:
        mid = half - 1
        pma = cmds.createNode("plusMinusAverage", n=f"{name}_mid_pma")
        left_clamps[-1].outputR >> pma.input1D[0]
        right_clamps[-1].outputR >> pma.input1D[1]

        cmp = cmds.createNode("clamp", n=f"{name}_mid_cmp")
        pma.output1D >> cmp.inputR
        cmp.maxR.set(1)

        connect(
            list_base_position[mid],
            list_zipped_position[mid],
            list_zipped_output[mid],
            cmp,
            "MID",
        )


def create_sticky_both(
    list_base_position,
    list_zipped_position,
    list_zipped_output,
    list_attr_zip,
    list_attr_distance,
    config_parent=None,
    name=None,
    offset=0,
    unit_conversion=10,
    list_attr_separate=None,
):
    def create_clamp_list_node(attr_zip):

        if attr_zip == attr_zip_left:
            attr_distance = list_attr_distance[0]
            option_shape_path = list_attr_distance[0].split(".")[0]
            option_shape = Create.add_option_shape(option_shape_path, "zipper_option")

        elif attr_zip == attr_zip_right:
            attr_distance = list_attr_distance[1]
            option_shape_path = list_attr_distance[1].split(".")[0]
            option_shape = Create.add_option_shape(option_shape_path, "zipper_option")

        list_clamp_output = []

        # prepare remap and transform node
        node_remap = cmds.createNode("remapValue", n="{}_remap_rmv".format(name))
        cmds.setAttr(node_remap + ".outputMax", amount_clamp + 1)
        cmds.setAttr(node_remap + ".inputMax", 1)
        cmds.connectAttr(attr_zip, node_remap + ".inputValue")

        # create sticky systems
        for i in range(amount_clamp):
            node_md_distance = cmds.createNode(
                "multDoubleLinear", n="{}_zipper_mdl".format(name)
            )
            cmds.connectAttr(attr_distance, node_md_distance + ".input2")
            cmds.setAttr(node_md_distance + ".input1", i + offset)

            node_adl_add = cmds.createNode(
                "addDoubleLinear", n="{}_zipper_adl".format(name)
            )
            cmds.connectAttr(
                "{}.output".format(node_md_distance), node_adl_add + ".input2"
            )
            cmds.addAttr(
                option_shape,
                ln=list_zipped_output[i],
                at="float",
                dv=1,
                k=1,
                min=0,
                max=2,
            )
            cmds.connectAttr(
                "{}.{}".format(option_shape, list_zipped_output[i]),
                "{}.input1".format(node_adl_add),
            )

            node_pma_output = cmds.createNode(
                "plusMinusAverage", n="{}_zipper_pma".format(name)
            )
            cmds.setAttr(node_pma_output + ".operation", 2)
            cmds.connectAttr(node_remap + ".outValue", node_pma_output + ".input1D[0]")
            cmds.connectAttr(node_adl_add + ".output", node_pma_output + ".input1D[1]")

            node_clamp = cmds.createNode("clamp", n="{}_zipper_cmp".format(name))
            cmds.connectAttr(node_pma_output + ".output1D", node_clamp + ".inputR")
            cmds.setAttr(node_clamp + ".maxR", 1)

            list_clamp_output.append(node_clamp)

        return list_clamp_output

    def apply_sticky():
        def connect_constraint(index, node_clamp):
            constraint = cmds.parentConstraint(
                list_base_position[index],
                list_zipped_position[index],
                list_zipped_output[index],
                mo=1,
            )[0]
            list_weight = cmds.parentConstraint(constraint, q=1, wal=1)

            cmds.connectAttr(node_clamp + ".outputR", constraint + "." + list_weight[1])

            node_reverse = cmds.createNode("reverse", n="{}_zipper_rev".format(name))
            cmds.connectAttr(node_clamp + ".outputR", node_reverse + ".inputX")
            cmds.connectAttr(
                node_reverse + ".outputX", constraint + "." + list_weight[0]
            )

        # right connect
        for i, node_clamp in enumerate(list_attr_clamp_right):
            if i == amount_clamp - 1:
                pass
                # connect_constraint(i, node_clamp)
            else:
                connect_constraint(i, node_clamp)

        # left connect
        for i, node_clamp in enumerate(list_attr_clamp_left):
            if i == amount_clamp - 1:
                pass
            else:
                connect_constraint(-1 * (i + 1), node_clamp)

        # between connect
        if isOdd:
            node_pma_sum = cmds.createNode(
                "plusMinusAverage", n="{}_betweenSum_pma".format(name)
            )
            cmds.connectAttr(
                list_attr_clamp_right[-1] + ".outputR", node_pma_sum + ".input1D[0]"
            )
            cmds.connectAttr(
                list_attr_clamp_left[-1] + ".outputR", node_pma_sum + ".input1D[1]"
            )

            node_clamp_sum = cmds.createNode(
                "clamp", n="{}_betweenClamp_cmp".format(name)
            )
            cmds.connectAttr(node_pma_sum + ".output1D", node_clamp_sum + ".inputR")

            cmds.setAttr(node_clamp_sum + ".minR", 0)
            cmds.setAttr(node_clamp_sum + ".maxR", 1)

            # i = amount_clamp - 1
            connect_constraint(amount_clamp - 1, node_clamp_sum)

    # declare viaravbles
    amount = len(list_base_position)

    if amount % 2 == 0:
        amount_clamp = int(amount / 2)
        isOdd = False
    else:
        amount_clamp = int(math.ceil(amount / 2))
        isOdd = True

    # conversion attr zip
    list_attr_conversion = []
    for attr in list_attr_zip:
        node_uc = cmds.createNode("unitConversion", n="{}_zipper_ud".format(name))
        cmds.setAttr(node_uc + ".conversionFactor", 1 / unit_conversion)
        cmds.connectAttr(attr, "{}.input".format(node_uc))

        list_attr_conversion.append("{}.output".format(node_uc))

    attr_zip_left, attr_zip_right = list_attr_conversion

    list_attr_clamp_left = create_clamp_list_node(attr_zip_left)
    list_attr_clamp_right = create_clamp_list_node(attr_zip_right)

    apply_sticky()


def create_sticky_matrix(
    list_base_position,
    listB,
    list_zipped_output,
    attr_zipper="transform1.sticky",
    attr_size="transform1.distance",
    name="zipper",
    isMirror=True,
):
    if not (len(list_base_position) == len(listB) == len(listB)):
        raise Exception("Input list have different member amount!")

    amount = len(list_base_position)
    index_mirror = (amount / 2) + 1 if amount % 2 == 0 else math.ceil(amount / 2) + 1

    list_sr_node = []

    for i in range(amount):
        objA = list_base_position[i]
        objB = listB[i]
        objC = list_zipped_output[i]

        # blend matrix conenction
        node_blend_matrix = cmds.createNode(
            "blendMatrix", n="{}{}_bm".format(name, i + 1)
        )

        cmds.connectAttr(
            "{}.worldMatrix[0]".format(objA), "{}.inputMatrix".format(node_blend_matrix)
        )
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(objB),
            "{}.target[0].targetMatrix".format(node_blend_matrix),
        )
        cmds.connectAttr(
            "{}.outputMatrix".format(node_blend_matrix),
            "{}.offsetParentMatrix".format(objC),
        )

        Transform.reset_transform(objC)

        if isMirror and i >= (index_mirror - 1):
            node_sr = list_sr_node[index_mirror - i]

            cmds.connectAttr(
                "{}.outValueX".format(node_sr), "{}.envelope".format(node_blend_matrix)
            )

        else:
            node_set_range = cmds.createNode(
                "setRange", n="sr_{}{}".format(name, i + 1)
            )
            node_md = cmds.createNode("multiplyDivide", n="md_{}{}".format(name, i + 1))
            node_pma = cmds.createNode(
                "plusMinusAverage", n="pma_{}{}".format(name, i + 1)
            )

            input_min = (i) * (1 / amount)
            input_max = (i + 1) * (1 / amount)
            value_mult = i

            # set range connection
            cmds.connectAttr(attr_zipper, "{}.valueX".format(node_set_range))
            cmds.setAttr("{}.minX".format(node_set_range), 0)
            cmds.setAttr("{}.maxX".format(node_set_range), 1)
            cmds.connectAttr(
                "{}.outValueX".format(node_set_range),
                "{}.envelope".format(node_blend_matrix),
            )

            # multiply + pma node
            cmds.connectAttr(attr_size, "{}.input1X".format(node_md))
            cmds.connectAttr(attr_size, "{}.input1Y".format(node_md))

            cmds.setAttr("{}.input2X".format(node_md), value_mult)
            cmds.setAttr("{}.input2Y".format(node_md), value_mult)

            cmds.connectAttr(
                "{}.outputX".format(node_md), "{}.input3D[0].input3Dx".format(node_pma)
            )
            cmds.connectAttr(
                "{}.outputY".format(node_md), "{}.input3D[0].input3Dy".format(node_pma)
            )

            cmds.setAttr("{}.input3D[1].input3Dx".format(node_pma), input_min)
            cmds.setAttr("{}.input3D[1].input3Dy".format(node_pma), input_max)

            cmds.connectAttr(
                "{}.output3Dx".format(node_pma), "{}.oldMinX".format(node_set_range)
            )
            cmds.connectAttr(
                "{}.output3Dy".format(node_pma), "{}.oldMaxX".format(node_set_range)
            )

            # append
            list_sr_node.append(node_set_range)


def create_sticky_old(
    list_base_position,
    list_zipped_position,
    list_zipped_output,
    attr_zip="transform1.sticky",
    attr_distance="transform1.distance",
    config_parent=None,
    name=None,
    offset=0,
    unit_conversion=10,
    list_attr_separate=None,
):
    def connect_constraint(index, node_clamp):
        constraint = cmds.parentConstraint(
            list_base_position[index],
            list_zipped_position[index],
            list_zipped_output[index],
            mo=1,
        )[0]
        list_weight = cmds.parentConstraint(constraint, q=1, wal=1)

        cmds.connectAttr(node_clamp + ".outputR", constraint + "." + list_weight[1])

        node_reverse = cmds.createNode("reverse")
        cmds.connectAttr(node_clamp + ".outputR", node_reverse + ".inputX")
        cmds.connectAttr(node_reverse + ".outputX", constraint + "." + list_weight[0])

    def attr_zip_converision_unit():
        # convert conversion factor
        node_uc = cmds.createNode("unitConversion")
        cmds.setAttr(node_uc + ".conversionFactor", 1 / unit_conversion)
        cmds.connectAttr(attr_zip, "{}.input".format(node_uc))

        return "{}.output".format(node_uc)

    def create_sticky_systems():
        # prepare remap and transform node
        node_remap = cmds.createNode("remapValue")
        cmds.setAttr(node_remap + ".outputMax", amount_clamp + 1)
        cmds.setAttr(node_remap + ".inputMax", 1)
        cmds.connectAttr(attr_zip, node_remap + ".inputValue")

        node_adjust = cmds.createNode("transform", n="{}_configSticky".format(name))
        cmds.parent(node_adjust, config_parent)

        # create sticky systems
        for i in range(amount_clamp):
            node_md_distance = cmds.createNode("multDoubleLinear")
            cmds.connectAttr(attr_distance, node_md_distance + ".input2")
            cmds.setAttr(node_md_distance + ".input1", i + offset)

            node_adl_add = cmds.createNode("addDoubleLinear")
            cmds.connectAttr(
                "{}.output".format(node_md_distance), node_adl_add + ".input2"
            )
            cmds.addAttr(
                node_adjust,
                ln=list_zipped_output[i],
                at="float",
                dv=1,
                k=1,
                min=0,
                max=2,
            )
            cmds.connectAttr(
                "{}.{}".format(node_adjust, list_zipped_output[i]),
                "{}.input1".format(node_adl_add),
            )

            node_pma_output = cmds.createNode("plusMinusAverage")
            cmds.setAttr(node_pma_output + ".operation", 2)
            cmds.connectAttr(node_remap + ".outValue", node_pma_output + ".input1D[0]")
            cmds.connectAttr(node_adl_add + ".output", node_pma_output + ".input1D[1]")

            node_clamp = cmds.createNode("clamp")
            cmds.connectAttr(node_pma_output + ".output1D", node_clamp + ".inputR")
            cmds.setAttr(node_clamp + ".maxR", 1)

            list_clamp_output.append(node_clamp)

    def apply_sticky():
        # create constraint and connect to target
        for i, node_clamp in enumerate(list_clamp_output):
            if i == amount_clamp - 1:
                connect_constraint(i, node_clamp)
            else:
                connect_constraint(i, node_clamp)
                connect_constraint(-1 * (i + 1), node_clamp)

    # declare viaravbles
    amount = len(list_base_position)
    list_clamp_output = []

    if amount % 2 == 0:
        amount_clamp = int(amount / 2)
        isOdd = False
    else:
        amount_clamp = int(math.ceil(amount / 2))
        isOdd = True

    attr_zip = attr_zip_converision_unit()
    create_sticky_systems()
    apply_sticky()


def create_zipper_both(
    list_upper_target=[],
    list_lower_target=[],
    list_upper_driver=[],
    list_lower_driver=[],
    list_upper_target_right=[],
    list_lower_target_right=[],
    list_upper_driver_right=[],
    list_lower_driver_right=[],
    controller_left=None,
    controller_right=None,
    auto_create_entire_list=True,
):

    if auto_create_entire_list:
        list_upper_target_right = list_upper_target[::-1]
        list_lower_target_right = list_lower_target[::-1]
        list_upper_driver_right = list_upper_driver[::-1]
        list_lower_driver_right = list_lower_driver[::-1]

    left_node = create_zipper_simple(
        list_upper_target=list_upper_target,
        list_lower_target=list_lower_target,
        list_upper_driver=list_upper_driver,
        list_lower_driver=list_lower_driver,
        controller=controller_left,
        matrix_connection=False,
    )

    right_node = create_zipper_simple(
        list_upper_target=list_upper_target_right,
        list_lower_target=list_lower_target_right,
        list_upper_driver=list_upper_driver_right,
        list_lower_driver=list_lower_driver_right,
        controller=controller_right,
        matrix_connection=False,
    )

    output_node = create_zipper_simple(
        list_upper_target=list_upper_target_right,
        list_lower_target=list_lower_target_right,
        list_upper_driver=list_upper_driver_right,
        list_lower_driver=list_lower_driver_right,
        controller=None,
        zip_connection=False,
    )

    count = len(list_lower_driver_right)
    for i in range(count):
        node_add = cmds.createNode("addDoubleLinear")
        node_clamp = cmds.createNode("clamp")

        left_node.zipEach[i] >> node_add.input1
        right_node.zipEach[count - i - 1] >> node_add.input2
        node_add.output >> node_clamp.inputR
        node_clamp.maxR.set(1)
        node_clamp.outputR >> output_node.zipEach[i]


def create_zipper_simple(
    list_upper_target=[],
    list_lower_target=[],
    list_upper_driver=[],
    list_lower_driver=[],
    controller=None,
    zip_connection=True,
    matrix_connection=True,
):

    if len(list_upper_driver) != len(list_lower_driver):
        raise Exception("Upper and Lower Target of Sticker must match savme count.")

    # create data centric node
    node_metadata = cmds.createNode("transform", n="zipper_data")

    # create matrix attribute
    cmds.addAttr(node_metadata, ln="upperInMatrix", at="matrix", multi=True)
    cmds.addAttr(node_metadata, ln="lowerInMatrix", at="matrix", multi=True)
    cmds.addAttr(node_metadata, ln="betweenMatrix", at="matrix", multi=True)
    cmds.addAttr(node_metadata, ln="upperOffsetMatrix", at="matrix", multi=True)
    cmds.addAttr(node_metadata, ln="lowerOffsetMatrix", at="matrix", multi=True)
    cmds.addAttr(node_metadata, ln="upperOutputMatrix", at="matrix", multi=True)
    cmds.addAttr(node_metadata, ln="lowerOutputMatrix", at="matrix", multi=True)

    # create zip attribute
    cmds.addAttr(node_metadata, ln="zipEach", at="float", min=0, max=1, multi=True)
    cmds.addAttr(node_metadata, ln="zipValue", at="float", min=0, max=1)
    cmds.addAttr(node_metadata, ln="zipRemap", at="float", min=0, max=1, multi=True)

    # add attribute to controller
    if controller:
        cmds.addAttr(controller, ln="zip", k=True, min=0, max=10)

        zip_conversion_attr = Connection.connect_conversion(
            input1="{}.zip".format(controller),
            conversion=0.1,
            output="{}.zipValue".format(node_metadata),
        )

    i = 0

    for upper_driver, lower_driver, upper_target, lower_target in zip(
        list_upper_driver, list_lower_driver, list_upper_target, list_lower_target
    ):

        ###############################
        #### Zip Connection
        ###############################

        if zip_connection:
            node_remap = cmds.createNode("remapValue")

            node_metadata.zipValue >> node_remap.inputValue

            value_remap = 1 / len(list_upper_driver)
            value_remap = (value_remap * i) + value_remap

            node_metadata.zipRemap[i].set(value_remap)
            node_metadata.zipRemap[i] >> node_remap.inputMax

            node_remap.outValue >> node_metadata.zipEach[i]

        ###############################
        #### Matrix Connection
        ###############################

        if matrix_connection:
            # connection in matrix
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(upper_driver),
                "{}.upperInMatrix[{}]".format(node_metadata, i),
            )
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(lower_driver),
                "{}.lowerInMatrix[{}]".format(node_metadata, i),
            )

            # create between matrix
            node_blendMatrix = cmds.createNode("blendMatrix")
            cmds.connectAttr(
                "{}.upperInMatrix[{}]".format(node_metadata, i),
                "{}.inputMatrix".format(node_blendMatrix),
            )
            cmds.connectAttr(
                "{}.lowerInMatrix[{}]".format(node_metadata, i),
                "{}.target[0].targetMatrix".format(node_blendMatrix),
            )
            cmds.setAttr("{}.target[0].weight".format(node_blendMatrix), 0.5)
            cmds.connectAttr(
                "{}.outputMatrix".format(node_blendMatrix),
                "{}.betweenMatrix[{}]".format(node_metadata, i),
            )

            matrix_between = om.MMatrix(node_metadata.betweenMatrix[i].get())

            # create output upper matrix
            matrix_a = om.MMatrix(node_metadata.upperInMatrix[i].get())
            matrix_offset = matrix_between.inverse() * matrix_a
            node_metadata.upperOffsetMatrix[i].set(matrix_offset)

            node_mult_matrix = cmds.createNode("multMatrix")
            node_metadata.betweenMatrix[i] >> node_mult_matrix.matrixIn[0]
            node_metadata.upperOffsetMatrix[i] >> node_mult_matrix.matrixIn[1]
            node_mult_matrix.matrixSum >> node_metadata.upperOutputMatrix[i]

            # create output lower matrix
            matrix_a = om.MMatrix(node_metadata.lowerInMatrix[i].get())
            matrix_offset = matrix_between.inverse() * matrix_a
            node_metadata.lowerOffsetMatrix[i].set(matrix_offset)

            node_mult_matrix = cmds.createNode("multMatrix")
            node_metadata.betweenMatrix[i] >> node_mult_matrix.matrixIn[0]
            node_metadata.lowerOffsetMatrix[i] >> node_mult_matrix.matrixIn[1]
            node_mult_matrix.matrixSum >> node_metadata.lowerOutputMatrix[i]

            # create upper dummy locator to switch constraint
            loc_upper = cmds.spaceLocator(n="{}_upper_loc".format(upper_target))
            node_metadata.upperOutputMatrix[i] >> loc_upper.offsetParentMatrix

            constraint = cmds.parentConstraint(
                loc_upper, upper_driver, upper_target, mo=False
            )
            node_reverse = cmds.createNode("reverse")

            node_metadata.zipEach[i] >> constraint.w0
            node_metadata.zipEach[i] >> node_reverse.inputX
            node_reverse.outputX >> constraint.w1

            # create lower dummy locator to switch constraint
            loc_lower = cmds.spaceLocator(n="{}_lower_loc".format(lower_target))
            node_metadata.lowerOutputMatrix[i] >> loc_lower.offsetParentMatrix

            constraint = cmds.parentConstraint(
                loc_lower, lower_driver, lower_target, mo=False
            )
            node_reverse = cmds.createNode("reverse")

            node_metadata.zipEach[i] >> constraint.w0
            node_metadata.zipEach[i] >> node_reverse.inputX
            node_reverse.outputX >> constraint.w1

        # update loop count
        i += 1

    return node_metadata


def create_stretchy_joint(
    loc_start_dist,
    loc_pole_dist,
    loc_end_dist,
    controller_attr,
    axis_forward,
    list_stretch_joints,
    stretch_with_fixed_angle=False,
    name_tag="Limb",
):
    """
    stretch_with_fixed_angle(bool)
    list_stretch_joints(list) : List of Stretch Joint, The Last Joint Wont Stretch

    """

    def create_pole_lock():
        # # blend color lock pole
        # node_bc_lock = cmds.createNode("blendColors", n="{}_stretchBlend_bc".format(name_tag))
        # cmds.connectAttr("{}.output3Dx".format(node_pma_stretch), "{}.color2R".format(node_bc_lock))
        # cmds.connectAttr("{}.output3Dy".format(node_pma_stretch), "{}.color2G".format(node_bc_lock))
        # cmds.connectAttr(attr_elbow_lock, "{}.blender".format(node_bc_lock))

        for i in range(len_stretch_joint):
            if i + 1 >= len_stretch_joint:
                continue
            else:
                node_dist = cmds.createNode(
                    "distanceBetween",
                    n="{}_{}_dist".format(name_tag, list_stretch_joints[i]),
                )
                cmds.connectAttr(
                    "{}.translate".format(list_stretch_joints[i]),
                    "{}.point1".format(node_dist),
                )
                cmds.connectAttr(
                    "{}.translate".format(list_stretch_joints[i + 1]),
                    "{}.point2".format(node_dist),
                )

                list_node_dist_for_pole_lock.append(node_dist)

        # Pole Lock ----------------------------------
        # node_md_lock = cmds.createNode("multiplyDivide", n="{}_lockConversion_mdv".format(name_tag))
        # cmds.setAttr("{}.input2X".format(node_md_lock), invert_value)
        # cmds.setAttr("{}.input2Y".format(node_md_lock), invert_value)
        # cmds.connectAttr("{}.distance".format(node_dist_up), "{}.input1X".format(node_md_lock))
        # cmds.connectAttr("{}.distance".format(node_dist_low), "{}.input1Y".format(node_md_lock))
        # cmds.connectAttr("{}.outputX".format(node_md_lock), "{}.color1R".format(node_bc_lock))
        # cmds.connectAttr("{}.outputY".format(node_md_lock), "{}.color1G".format(node_bc_lock))

    def apply_stretch_to_joint():
        # Connect to output ------------------------------
        for stretch_joint in dict_attr_stretch_output.keys():
            attr_output = dict_attr_stretch_output[stretch_joint]

            cmds.connectAttr(
                attr_output, "{}.t{}".format(stretch_joint, axis_forward_abs)
            )

    def connect_stretch():
        # Stretch ----------------------------------
        # connection distance
        node_distance = cmds.createNode(
            "distanceBetween", n="{}_autoStretchLength_dist".format(name_tag)
        )
        cmds.connectAttr(
            "{}.translate".format(loc_start_dist),
            "{}.point1".format(node_distance),
        )
        cmds.connectAttr(
            "{}.translate".format(loc_end_dist), "{}.point2".format(node_distance)
        )

        # connection normalize
        node_md_normalize = cmds.createNode(
            "multiplyDivide", n="{}_stretchLengthNormalize_md".format(name_tag)
        )
        cmds.connectAttr(
            "{}.distance".format(node_distance), "{}.input1X".format(node_md_normalize)
        )
        factor = 1 / value_full_length
        cmds.setAttr("{}.input2X".format(node_md_normalize), factor)

        # condition
        node_condition = cmds.createNode(
            "condition", n="{}_autoStretch_cond".format(name_tag)
        )
        cmds.setAttr("{}.operation".format(node_condition), 2)
        cmds.connectAttr(
            "{}.distance".format(node_distance), "{}.firstTerm".format(node_condition)
        )
        cmds.setAttr("{}.secondTerm".format(node_condition), value_full_length)
        cmds.connectAttr(
            "{}.outputX".format(node_md_normalize),
            "{}.colorIfTrueR".format(node_condition),
        )

        # mdv stretch connection

        for i in range(len_stretch_joint):
            if i == 0:
                continue

            stretch_joint = list_stretch_joints[i]
            # multiply stretch factor
            node_md_stretch = cmds.createNode(
                "multDoubleLinear", n="{}_{}Stretch_mdl".format(name_tag, stretch_joint)
            )
            cmds.connectAttr(
                "{}.outColorR".format(node_condition),
                "{}.input1".format(node_md_stretch),
            )
            cmds.setAttr(
                "{}.input2".format(node_md_stretch),
                cmds.getAttr("{}.t{}".format(stretch_joint, axis_forward_abs)),
            )  # translate multiply

            # by pass
            node_bc_bypass = cmds.createNode(
                "blendTwoAttr",
                n="{}_{}StretchByPass_bc".format(name_tag, stretch_joint),
            )
            cmds.connectAttr(
                attr_auto_stretch, "{}.attributesBlender".format(node_bc_bypass)
            )
            cmds.connectAttr(
                node_md_stretch + ".output", "{}.input[1]".format(node_bc_bypass)
            )
            cmds.setAttr(
                "{}.input[0]".format(node_bc_bypass),
                cmds.getAttr("{}.output".format(node_md_stretch)),
            )

            # stretch adjust
            node_pma_stretch = cmds.createNode(
                "plusMinusAverage", n="{}_stretchAdd_pma".format(name_tag)
            )

            # stretch invert ( in right arm case )
            attr_adjust_stretch = list_attr_arm_adjust_stretch[i - 1]
            Connection.connect_conversion(
                input1=attr_adjust_stretch,
                conversion=invert_value,
                output="{}.input1D[1]".format(node_pma_stretch),
            )
            cmds.connectAttr(
                "{}.output".format(node_bc_bypass),
                "{}.input1D[0]".format(node_pma_stretch),
            )

            # return attr output
            dict_attr_stretch_output[stretch_joint] = node_pma_stretch + ".output1D"

    len_stretch_joint = len(list_stretch_joints)
    list_node_dist_for_pole_lock = []
    list_node_blend_for_pole_lock = []
    attr_auto_stretch = "{}.autoStretch".format(controller_attr)
    list_attr_arm_adjust_stretch = []
    dict_attr_stretch_output = {}

    # attribute
    for i in range(len_stretch_joint - 1):
        attr_arm_adjust_stretch = "{}.LimbStretch{}".format(controller_attr, i + 1)
        cmds.addAttr(controller_attr, k=1, ln="LimbStretch{}".format(i + 1), at="float")
        list_attr_arm_adjust_stretch.append(attr_arm_adjust_stretch)

    attr_elbow_lock = "{}.elbowLock".format(controller_attr)
    # add_attribute_divider(controller_attr, "Stretch")
    cmds.addAttr(controller_attr, k=1, ln="elbowLock", at="float", min=0, max=1)
    cmds.addAttr(controller_attr, k=1, ln="autoStretch", at="float", min=0, max=1)

    if "-" in axis_forward:
        axis_forward_abs = del_neg(axis_forward)
        invert_value = -1
    else:
        axis_forward_abs = axis_forward
        invert_value = 1

    if stretch_with_fixed_angle:
        value_full_length = Transform.get_distance_two(loc_start_dist, loc_end_dist)
    else:
        value_full_length = 0

        for i in range(len_stretch_joint):
            if i + 1 >= len_stretch_joint:
                continue
            else:
                value_full_length += Transform.get_distance_two(
                    list_stretch_joints[i], list_stretch_joints[i + 1]
                )

    connect_stretch()
    apply_stretch_to_joint()
    # create_pole_lock()


def create_switch_fk_ik_chain(
    target_joints,
    grp_fk_joints,
    grp_ik_joints,
    attr_switch,
    grp_ik_controls,
    grp_fk_controls,
    attribute_switch_range=1,
    tag_name="limb",
    list_append_keyword=["Fk", "Ik"],
):

    def duplicate_joints():
        # duplicate joints to fk group and ik group (include it's parent)
        for i, typ in enumerate(list_append_keyword):
            # change group
            parent_path = grp_fk_joints if i == 0 else grp_ik_joints
            recent = None

            # parent offset joint
            parent_joint = cmds.listRelatives(target_joints[0], p=1, f=1)

            if parent_joint:
                tmp = cmds.duplicate(parent_joint[0], n=parent_joint[0] + typ, po=1)[0]

                # unlock translate,rotate,scale
                Transform.lock_attributes(tmp, t=1, r=1, s=1, v=1, l=0, k=1)

                cmds.parent(tmp, parent_path)
                cmds.parentConstraint(parent_joint[0], tmp)
                recent = tmp

            # limb joint
            for joint in target_joints:
                tmp = cmds.duplicate(joint, n=joint + typ, po=1)[0]
                (
                    cmds.parent(tmp, parent_path)
                    if recent is None
                    else cmds.parent(tmp, recent)
                )
                recent = tmp

    def connect_switch_joints():
        # create switch systems , use blendColor Node
        node_reverse = cmds.createNode("reverse", n="rev_{}Switch".format(tag_name))
        cmds.connectAttr(attr_switch, "{}.inputX".format(node_reverse))

        list_name_fk_joint = [joint + list_append_keyword[0] for joint in target_joints]
        list_name_ik_joint = [joint + list_append_keyword[1] for joint in target_joints]

        for i, joint in enumerate(target_joints):
            for data in [["t", "Pos"], ["r", "Rot"]]:
                attr = data[0]
                keyword = data[1]

                node_blend = cmds.createNode(
                    "blendColors", n="{}_blend{}{}_blc".format(tag_name, joint, keyword)
                )
                cmds.connectAttr(attr_switch, "{}.blender".format(node_blend))
                cmds.connectAttr(
                    "{}.{}".format(list_name_ik_joint[i], attr),
                    "{}.color1".format(node_blend),
                )
                cmds.connectAttr(
                    "{}.{}".format(list_name_fk_joint[i], attr),
                    "{}.color2".format(node_blend),
                )
                cmds.connectAttr(
                    "{}.output".format(node_blend), "{}.{}".format(joint, attr)
                )

        for i, joint in enumerate(target_joints):
            source_joint = list_name_fk_joint[i]

            cmds.connectAttr(
                "{}.rotateOrder".format(source_joint), "{}.rotateOrder".format(joint)
            )

    def connect_switch_visibility():
        # connect visibility
        node_rev = cmds.createNode("reverse", n="{}_switchVis_rev".format(tag_name))
        cmds.connectAttr(attr_switch, "{}.inputX".format(node_rev))
        cmds.connectAttr("{}.inputX".format(node_rev), "{}.v".format(grp_ik_controls))
        cmds.connectAttr("{}.outputX".format(node_rev), "{}.v".format(grp_fk_controls))

    def remove_none(list_joint):
        list_return = []
        for joint in list_joint:
            if joint:
                list_return.append(joint)

        for joint in list_return:
            if not cmds.objExists(joint):
                raise Exception("{} Not Found".format(joint))

        return list_return

    if attribute_switch_range <= 0:
        raise Exception(
            "Invalid Attribute Switch Range Input , Must be greater than zero. got {}".format(
                attribute_switch_range
            )
        )

    target_joints = remove_none(target_joints)

    duplicate_joints()
    connect_switch_joints()
    connect_switch_visibility()


def create_twist_chain(
    list_twist, end_target, axis="y", invert=False, invert_list_twist=False
):
    if invert_list_twist:
        list_twist.reverse()

    for i in range(len(list_twist)):
        twist_transform = list_twist[i]
        node_md = cmds.createNode("multiplyDivide", n="md_{}".format(twist_transform))

        invert_value = 1 if invert is False else -1
        cmds.setAttr("{}.operation".format(node_md), 1)

        cmds.setAttr(
            "{}.input1{}".format(node_md, axis.upper()),
            (1 / (len(list_twist) - 1)) * i * invert_value,
        )
        cmds.connectAttr(
            "{}.r{}".format(end_target, axis),
            "{}.input2{}".format(node_md, axis.upper()),
        )
        cmds.connectAttr(
            "{}.output{}".format(node_md, axis.upper()),
            "{}.r{}".format(twist_transform, axis),
        )


def create_wire_curve(crv_target, crv_control, name, zeroOffset=False):
    output = cmds.wire(crv_target, n=name, gw=0, en=1, ce=0, li=0, w=crv_control)
    wr_node = output[0]

    if zeroOffset == True:
        cmds.setAttr(wr_node + ".scale[0]", 0)

    return wr_node


def create_finger_rig(
    list_finger_joint,
    hand_space,
    axis_pole="y",
    move_pole_distance=5.0,
    parent=None,
    tag_name="finger",
    mirror_control_scale=False,
    is_thumb=False,
):
    def create_finger_ik():
        def create_thumb():
            # create ik handle and pole vector
            ik_handle = cmds.ikHandle(
                sj=list_chain_ik[0], ee=list_chain_ik[2], sol="ikRPsolver"
            )[0]
            cmds.parent(ik_handle, list_finger_control[2])

            cmds.setAttr(
                "{}.t{}".format(list_finger_control[1], axis_pole), move_pole_distance
            )
            Create.create_freeze_group(list_finger_control[1], "grpOff")

            cmds.poleVectorConstraint(list_finger_control[1], ik_handle)

            cmds.pointConstraint(list_finger_control[0], list_chain_ik[0])

            # add blend space option
            cmds.addAttr(list_finger_control[2], ln="world", k=1, min=0, max=1)
            attr_world = "{}.world".format(list_finger_control[2])

            Connection.create_switch_float(
                list_space=[config.loc_root, hand_space],
                object=list_finger_control[2],
                controller=attr_world,
                typ="parent",
            )

            # constraint auto pole
            cmds.pointConstraint(
                list_finger_control[0],
                list_finger_control[2],
                cmds.listRelatives(list_finger_control[1], p=1)[0],
                mo=1,
            )

        def create_finger():
            cmds.addAttr(list_finger_control[3], ln="lockFingerTip", k=1, min=0, max=1)
            attr_lock = "{}.lockFingerTip".format(list_finger_control[3])

            list_no_lock_chain = [
                "{}_NoLock".format(joint) for joint in list_finger_joint
            ]
            list_lock_chain = ["{}_Lock".format(joint) for joint in list_finger_joint]

            duplicate_joints(list_append_keyword=["NoLock", "Lock"])
            create_switch_systems(
                list_lock_chain,
                list_no_lock_chain,
                list_chain_ik,
                attr_switch=attr_lock,
            )

            # Lock Case -----------------------------------
            # create ik handle and pole vector
            ik_handle = cmds.ikHandle(
                sj=list_lock_chain[0], ee=list_lock_chain[2], sol="ikRPsolver"
            )[0]
            cmds.parent(ik_handle, list_finger_control[2])

            cmds.setAttr(
                "{}.t{}".format(list_finger_control[1], axis_pole), move_pole_distance
            )

            cmds.poleVectorConstraint(list_finger_control[1], ik_handle)

            cmds.pointConstraint(list_finger_control[0], list_lock_chain[0])

            # No Lock Case ------------------------------------------
            # create ik handle and pole vector
            ik_handle = cmds.ikHandle(
                sj=list_no_lock_chain[0], ee=list_no_lock_chain[3], sol="ikRPsolver"
            )[0]
            cmds.parent(ik_handle, list_finger_control[2])

            cmds.setAttr(
                "{}.t{}".format(list_finger_control[1], axis_pole), move_pole_distance
            )

            cmds.poleVectorConstraint(list_finger_control[1], ik_handle)

            cmds.pointConstraint(list_finger_control[0], list_no_lock_chain[0])

            # constraint auto pole
            cmds.pointConstraint(
                list_finger_control[0],
                list_finger_control[3],
                cmds.listRelatives(list_finger_control[1], p=1)[0],
                mo=1,
            )

            # parent chain -------------------------------
            cmds.parent(list_finger_control[2], list_finger_control[3])

            # constraint auto pole -------------------------------------
            freeze_group_classic(list_finger_control[1], "grpOff")
            cmds.pointConstraint(
                list_finger_control[0],
                list_finger_control[3],
                cmds.listRelatives(list_finger_control[1], p=1)[0],
                mo=1,
            )

            cmds.orientConstraint(list_finger_control[2], list_lock_chain[2])

            # add blend space option ------------------------
            cmds.addAttr(list_finger_control[3], ln="world", k=1, min=0, max=1)
            attr_world = "{}.world".format(list_finger_control[3])

            Connection.create_switch_float(
                list_space=[config.loc_root, hand_space],
                object=list_finger_control[3],
                controller=attr_world,
                typ="parent",
                tag_name=tag_name,
            )

            # connect lock finger tip
            cmds.connectAttr(attr_lock, "{}.v".format(list_finger_control[2]))

        if is_thumb:
            len_fix = 3
        else:
            len_fix = 4

        if len(list_finger_joint) != len_fix:
            cmds.confirmDialog(
                m="Error to create finger ik, Input must be {} joints , get {} joint : {}".format(
                    len_fix, len(list_finger_joint), list_finger_joint
                )
            )

            raise Exception()

        # create ik control
        list_finger_control = ["{}_{}".format(joint, ctrl) for joint in list_chain_ik]

        for i in range(len_fix):
            control_name = list_finger_control[i]
            joint_name = list_chain_ik[i]

            create_control(
                name=control_name,
                match=joint_name,
                freeze_group=True,
                parent=grp_ik_control,
                display_rotate_order=False,
                size=0.5,
                color="purple",
            )

        if is_thumb:
            create_thumb()
        else:
            create_finger()

        # make finalize
        for control in list_finger_control:
            Utility.lock_attribute(control, r=1, s=1, v=1, l=1, k=0)

        if is_thumb:
            Utility.lock_attribute(list_finger_control[-1], r=1, l=0, k=1)

        else:
            Utility.lock_attribute(list_finger_control[-1], r=1, l=0, k=1)
            Utility.lock_attribute(list_finger_control[-2], r=1, l=0, k=1)

    def create_fingers_fk():
        # fk function
        recent_control = None

        for i in range(len(list_chain_fk)):
            if i == len(list_chain_fk) - 1:
                continue

            joint_name = list_chain_fk[i]
            control_name = "{}_fk_{}".format(list_chain_fk[i], ctrl)

            create_control(
                name=control_name,
                match=joint_name,
                display_rotate_order=False,
                freeze_group=True,
                mirror_freeze_group=mirror_control_scale,
                constraint="parent",
                size=0.5,
                color="red",
            )

            grp_offset = cmds.listRelatives(control_name, p=1)[0]

            # chain in hierarchy
            if recent_control:
                cmds.parent(grp_offset, recent_control)
            else:
                cmds.parent(grp_offset, grp_fk_control)

            recent_control = control_name

            Utility.lock_attribute(control_name, t=1, r=0, s=1, v=1, k=0, l=1)

    def duplicate_joints(list_append_keyword=["Fk", "Ik"]):
        list_return = []
        # duplicate joints to fk group and ik group (include it's parent)
        for i, typ in enumerate(list_append_keyword):
            # change group
            list_return_each = []
            parent_path = cmds.group(
                em=1, p=grp_finger_rig, n="{}_{}_joint_{}".format(tag_name, typ, grp)
            )

            recent = None

            # parent offset joint
            parent_joint = cmds.listRelatives(list_finger_joint[0], p=1, f=1)

            if parent_joint:
                tmp = cmds.duplicate(
                    parent_joint[0],
                    n="{}_Root{}".format(cut(parent_joint[0]), typ),
                    po=1,
                )[0]
                cmds.parent(tmp, parent_path)
                cmds.parentConstraint(parent_joint[0], tmp)
                recent = tmp

            # limb joint
            for joint in list_finger_joint:
                tmp = cmds.duplicate(joint, n="{}_{}".format(cut(joint), typ), po=1)[0]
                (
                    cmds.parent(tmp, parent_path)
                    if recent is None
                    else cmds.parent(tmp, recent)
                )
                recent = tmp

                list_return_each.append(tmp)

            list_return.append(list_return_each)

    def create_switch_systems(
        list_object1,
        list_object2,
        list_object_result,
        attr_switch,
        grp_object1_control=None,
        grp_object2_control=None,
    ):
        # create switch systems , use blendColor Node
        node_reverse = cmds.createNode("reverse", n=cname(tag_name, "switch", "rev"))
        cmds.connectAttr(attr_switch, "{}.inputX".format(node_reverse))

        for i, joint in enumerate(list_object_result):
            for data in [["t", "Pos"], ["r", "Rot"]]:
                attr = data[0]
                keyword = data[1]

                node_blend = cmds.createNode(
                    "blendColors", n="{}_blend{}{}_blc".format(tag_name, joint, keyword)
                )
                cmds.connectAttr(attr_switch, "{}.blender".format(node_blend))
                cmds.connectAttr(
                    "{}.{}".format(list_object1[i], attr),
                    "{}.color1".format(node_blend),
                )
                cmds.connectAttr(
                    "{}.{}".format(list_object2[i], attr),
                    "{}.color2".format(node_blend),
                )
                cmds.connectAttr(
                    "{}.output".format(node_blend), "{}.{}".format(joint, attr)
                )

        # connect visibility
        if grp_object1_control:
            cmds.connectAttr(
                "{}.inputX".format(node_reverse), "{}.v".format(grp_object1_control)
            )
        if grp_object2_control:
            cmds.connectAttr(
                "{}.outputX".format(node_reverse), "{}.v".format(grp_object2_control)
            )

    def create_finger_main_control():
        create_control(
            name=ctrl_main,
            parent=grp_finger_rig,
            freeze_group=True,
            display_rotate_order=False,
            color="yellow",
            size=0.6,
        )

        cmds.parentConstraint(list_finger_joint[0], ctrl_main)
        cmds.addAttr(ctrl_main, ln="FkIk", k=1, min=0, max=1)

    grp_finger_rig = cmds.group(em=1, n="{}_rig_{}".format(tag_name, grp))

    grp_fk_control = cmds.group(
        em=1, p=grp_finger_rig, n="{}_fk_control_{}".format(tag_name, grp)
    )
    grp_ik_control = cmds.group(
        em=1, p=grp_finger_rig, n="{}_ik_control_{}".format(tag_name, grp)
    )

    list_chain_ik = ["{}_Ik".format(joint) for joint in list_finger_joint]
    list_chain_fk = ["{}_Fk".format(joint) for joint in list_finger_joint]

    ctrl_main = "{}_main_{}".format(tag_name, ctrl)
    attr_switch = "{}.FkIk".format(ctrl_main)

    if parent:
        cmds.parent(grp_finger_rig, parent)

    create_finger_main_control()

    # blend joint for fk / ik
    duplicate_joints(list_append_keyword=["Fk", "Ik"])
    create_switch_systems(
        list_chain_ik,
        list_chain_fk,
        list_finger_joint,
        attr_switch=attr_switch,
        grp_object1_control=grp_ik_control,
        grp_object2_control=grp_fk_control,
    )

    create_fingers_fk()
    create_finger_ik()

    Utility.lock_attribute(ctrl_main, t=1, r=1, s=1, v=1, k=0, l=1)


def absolute_poly_bridge_edge():
    selection = cmds.ls(sl=1, fl=1)

    if len(selection) % 2 != 0:
        return

    part_A = selection[0 : int(len(selection) / 2)]
    part_B = selection[int(len(selection) / 2) : :]

    print(len(part_A), len(part_B))

    for i in range(len(part_A)):
        cmds.polyBridgeEdge(part_A[i], part_B[i], divisions=0)


def create_line_annotate(list_object, name="line", parent=None, color_index=13):
    list_attr_position = []

    if not parent:
        parent = list_object[0]

    parent_inv_matrix_attr = "{}.worldInverseMatrix[0]".format(parent)

    for i, obj in enumerate(list_object):
        # multMatrix per CV
        node_mm = cmds.createNode("multMatrix", name="{}_mm_{}".format(name, i))
        node_dcm = cmds.createNode("decomposeMatrix", name="{}_dcm_{}".format(name, i))

        cmds.connectAttr("{}.worldMatrix[0]".format(obj),    "{}.matrixIn[0]".format(node_mm))
        cmds.connectAttr(parent_inv_matrix_attr,             "{}.matrixIn[1]".format(node_mm))
        cmds.connectAttr("{}.matrixSum".format(node_mm),     "{}.inputMatrix".format(node_dcm))

        list_attr_position.append("{}.outputTranslate".format(node_dcm))

    # create curve
    list_point = [(0, 0, 0) for _ in range(len(list_attr_position))]
    curve_transform = cmds.curve(p=list_point, d=1, n="{}_crv".format(name))
    curve_shape = cmds.listRelatives(curve_transform, children=True, shapes=True)[0]

    # connect position
    for i, attr_pos in enumerate(list_attr_position):
        cmds.connectAttr(attr_pos, "{}.controlPoints[{}]".format(curve_shape, i))

    # parent shape under parent transform
    cmds.setAttr("{}.inheritsTransform".format(curve_transform), False)
    cmds.parent(curve_shape, parent, shape=True, relative=True)
    cmds.delete(curve_transform)

    # set override color
    cmds.setAttr("{}.overrideEnabled".format(curve_shape), True)
    cmds.setAttr("{}.overrideColor".format(curve_shape), color_index)

    # set line width
    return curve_shape

def create_blend_joint_world_space(jointA, jointB):
    def create_fake_orient_rotation():
        node_mm_parent = cmds.createNode("multMatrix", n="parent_mm")
        node_mm_parent = cmds.createNode("multMatrix", n="parent_mm")
        node_mm_parent = cmds.createNode("multMatrix", n="parent_mm")

    output_joint = cmds.createNode("joint", n="joint_output")

    # get parent local orient

    return output_joint


def create_world_vector(objectA, objectB):
    """Create vector in world space"""

    locatorA = cmds.spaceLocator(n="{}_vecPointA".format(objectA))
    locatorB = cmds.spaceLocator(n="{}_vecPointB".format(objectB))

    Utility.match_parent(locatorA, objectA)
    Utility.match_parent(locatorB, locatorA)

    locatorA_shape = cmds.listRelatives(locatorA, c=1, s=1)[0]
    locatorB_shape = cmds.listRelatives(locatorB, c=1, s=1)[0]

    cmds.xform(locatorB, os=True, t=(1, 0, 0))

    constraint = cmds.aimConstraint(objectB, locatorA, aim=[1, 0, 0])

    cmds.delete(constraint)

    node_pma = cmds.createNode("plusMinusAverage")
    node_pma.operation.set(2)

    locatorA_shape.worldPosition[0] >> node_pma.input3D[0]
    locatorB_shape.worldPosition[0] >> node_pma.input3D[1]

    locatorA.visibility.set(False)
    # locatorB.visibility.set(False)

    # Utility.lock_attribute(locatorA, t=True, r=True, s=True, v=True)
    # Utility.lock_attribute(locatorB, t=True, r=True, s=True, v=True)

    return [node_pma.output3D, locatorA]


def create_skirt_auto_rot_simple(
    leg_data,
    skirtA,
    skirtB=None,
    attr_output="skirtA_L1_ctl.rz",
    axis="z",
    # offset_amount=-120,
    invert_direction=False,
    invert_collision=False,
    clamp_value=[0, 120],
    intensity=1,
):

    if invert_collision:
        offset_amount = -120
    else:
        offset_amount = 120

    if intensity <= 0:
        raise Exception("Intensity value must greater than 0")
    leg_vector_attr, locatorA = leg_data

    # create skirt vector to world 90 degree if skirt b is empty
    if not skirtB:
        skirtB = cmds.spaceLocator(n="tmp")
        cmds.matchTransform(skirtB, skirtA)
        cmds.xform(skirtB, ws=True, r=True, t=(0, -1, 0))
        skirt_vector_attr, locatorB = Create.create_world_vector(skirtA, skirtB)
        # remove tmp skrit B

        cmds.delete(skirtB)

    else:
        skirt_vector_attr, locatorB = Create.create_world_vector(skirtA, skirtB)

    if axis.lower() == "x":
        offset_rotate = (offset_amount, 0, 0)
    elif axis.lower() == "y":
        offset_rotate = (0, offset_amount, 0)
    elif axis.lower() == "z":
        offset_rotate = (0, 0, offset_amount)
    else:
        raise Exception("error")

    locator_B_child = cmds.listRelatives(locatorB, c=1, typ="transform")[0]
    cmds.parent(locator_B_child, w=1)

    Transform.reset_transform(locatorB)
    cmds.parent(locator_B_child, locatorB)

    cmds.rotate(
        locatorB,
        offset_rotate[0],
        offset_rotate[1],
        offset_rotate[2],
        r=True,
        os=True,
        fo=True,
    )

    # Get Angle Between
    node_angle = cmds.createNode("angleBetween")

    leg_vector_attr >> node_angle.vector1
    skirt_vector_attr >> node_angle.vector2

    node_clamp = cmds.createNode("clamp")

    node_angle.angle >> node_clamp.inputR

    # Add Value
    node_add = cmds.createNode("addDoubleLinear")

    node_clamp.outputR >> node_add.input1

    # Set Clamp Value

    value1, value2 = clamp_value

    if value1 > value2:
        min_value = value2
        max_value = value1
    else:
        min_value = value1
        max_value = value2

    node_clamp.minR.set(min_value)
    node_clamp.maxR.set(max_value)

    node_add.input2.set(-1 * (node_clamp.outputR.get()))

    # apply connection
    if invert_direction is True:
        intensity *= -1
    elif invert_direction is False:
        intensity *= 1

    Connection.connect_conversion(
        input1=node_add.output, conversion=intensity, output=attr_output
    )


def create_skirt_auto_rot(
    leg_data,
    skirtA,
    skirtB=None,
    attr_output="skirtA_L1_ctl.rz",
    axis="z",
    offset_amount=-120,
    invert=False,
    clamp_value=[0, 120],
    intensity=1,
):
    if invert is True:
        invert_drive = -1 * intensity
    elif invert is False:
        invert_drive = 1 * intensity

    leg_vector_attr, locatorA = leg_data

    # create skirt vector to world 90 degree if skirt b is empty
    if not skirtB:
        skirtB = cmds.spaceLocator(n="tmp")
        cmds.matchTransform(skirtB, skirtA)
        cmds.xform(skirtB, ws=True, r=True, t=(0, -1, 0))
        skirt_vector_attr, locatorB = Create.create_world_vector(skirtA, skirtB)
        # remove tmp skrit B

        cmds.delete(skirtB)

    else:
        skirt_vector_attr, locatorB = Create.create_world_vector(skirtA, skirtB)

    if axis.lower() == "x":
        offset_rotate = (offset_amount, 0, 0)
    elif axis.lower() == "y":
        offset_rotate = (0, offset_amount, 0)
    elif axis.lower() == "z":
        offset_rotate = (0, 0, offset_amount)
    else:
        raise Exception("error")

    locator_B_child = cmds.listRelatives(locatorB, c=1, typ="transform")[0]
    cmds.parent(locator_B_child, w=1)

    Transform.reset_transform(locatorB)
    cmds.parent(locator_B_child, locatorB)

    cmds.rotate(
        locatorB,
        offset_rotate[0],
        offset_rotate[1],
        offset_rotate[2],
        r=True,
        os=True,
        fo=True,
    )

    # Get Angle Between
    node_angle = cmds.createNode("angleBetween")

    leg_vector_attr >> node_angle.vector1
    skirt_vector_attr >> node_angle.vector2

    node_clamp = cmds.createNode("clamp")

    node_angle.angle >> node_clamp.inputR

    # Add Value
    node_add = cmds.createNode("addDoubleLinear")

    node_clamp.outputR >> node_add.input1

    # Set Clamp Value

    value1, value2 = clamp_value

    if value1 > value2:
        min_value = value2
        max_value = value1
    else:
        min_value = value1
        max_value = value2

    node_clamp.minR.set(min_value)
    node_clamp.maxR.set(max_value)

    node_add.input2.set(-1 * (node_clamp.outputR.get()))

    # apply connection

    Connection.connect_conversion(
        input1=node_add.output, conversion=invert_drive, output=attr_output
    )


def create_blend_joint(joint, joint_parent=None):
    joint_blend = cmds.createNode("joint", n="{}_blend".format(joint))

    # create node
    node_pair_blend = cmds.createNode("pairBlend")
    cmds.matchTransform(joint_blend, joint)
    cmds.parent(joint_blend, cmds.listRelatives(joint, p=1)[0])

    cmds.makeIdentity(joint_blend, a=1, r=1)
    node_pair_blend.weight.set(0.5)
    node_pair_blend.rotInterpolation.set(1)

    cmds.connectAttr("{}.t".format(joint), "{}.inTranslate1".format(node_pair_blend))
    cmds.connectAttr("{}.r".format(joint), "{}.inRotate1".format(node_pair_blend))
    cmds.connectAttr("{}.t".format(joint), "{}.inTranslate2".format(node_pair_blend))

    cmds.connectAttr("{}.outRotate".format(node_pair_blend), "{}.r".format(joint_blend))

    return joint_blend, node_pair_blend


def create_support_joint(
    joint_blend,
    node_pair_blend,
    joint,
    offset=1,
    intensity=0.1,
    axis_push="y",
    axis_aim="x",
    rotate=60,
):
    """
    typ : bone,soft,both
    """

    # create joint support
    if rotate < 0:
        min = rotate
        max = 0

    elif rotate > 0:
        min = 0
        max = rotate
    else:
        min = 0
        max = 0

    index = 1

    while True:
        joint_name = "{}_support_{}".format(joint, index)

        if cmds.objExists(joint_name):
            index += 1
        else:
            break

    joint_support = cmds.createNode("joint", n="{}_support_{}".format(joint, index))

    axis_rot = Scene.get_exist_axis([axis_aim, axis_push])
    axis_push = axis_push
    index = 1

    # create support joint
    Utility.match_parent(joint_support, joint_blend)
    cmds.makeIdentity(joint_support, a=1, r=1)

    # add attribute to joint
    cmds.addAttr(joint_support, ln="biasX", dv=0, k=True)
    cmds.addAttr(joint_support, ln="biasY", dv=0, k=True)
    cmds.addAttr(joint_support, ln="biasZ", dv=0, k=True)

    cmds.addAttr(joint_support, ln="min".format(index), dv=min, k=True)
    cmds.addAttr(joint_support, ln="max".format(index), dv=max, k=True)
    cmds.addAttr(joint_support, ln="offset".format(index), dv=offset, k=True)

    cmds.addAttr(joint_support, ln="currentRotate".format(index), k=True)

    cmds.connectAttr(
        "{}.outRotate{}".format(node_pair_blend, axis_rot.upper()),
        "{}.currentRotate".format(joint_support, index),
    )

    # connection
    node_clamp = cmds.createNode("clamp")
    node_mdl = cmds.createNode("multDoubleLinear")
    node_adl = cmds.createNode("addDoubleLinear")

    cmds.connectAttr(
        "{}.outRotate{}".format(node_pair_blend, axis_rot.upper()),
        "{}.inputR".format(node_clamp),
    )
    cmds.connectAttr(
        "{}.min".format(joint_support, index),
        "{}.minR".format(node_clamp),
    )
    cmds.connectAttr(
        "{}.max".format(joint_support, index),
        "{}.maxR".format(node_clamp),
    )

    cmds.connectAttr("{}.outputR".format(node_clamp), "{}.input1".format(node_mdl))
    cmds.connectAttr(
        "{}.bias{}".format(joint_support, axis_push.upper()),
        "{}.input2".format(node_mdl),
    )

    cmds.connectAttr("{}.output".format(node_mdl), "{}.input1".format(node_adl))
    cmds.connectAttr(
        "{}.offset".format(joint_support, index),
        "{}.input2".format(node_adl),
    )

    cmds.connectAttr(
        "{}.output".format(node_adl), "{}.t{}".format(joint_support, axis_push)
    )

    # connect bias value
    axis_left = Scene.get_exist_axis([axis_push])
    for axis in axis_left:
        node_mdl = cmds.createNode("multDoubleLinear")

        node_clamp.outputR >> node_mdl.input1
        cmds.connectAttr(
            "{}.bias{}".format(joint_support, axis.upper()),
            "{}.input2".format(node_mdl),
        )
        cmds.connectAttr(
            "{}.output".format(node_mdl),
            "{}.translate{}".format(joint_support, axis.upper()),
        )

    # set default value
    cmds.setAttr("{}.bias{}".format(joint_support, axis_push.upper()), intensity)

    # add joint to mgear sets
    try:
        defSet = cmds.PyNode("rig_deformers_grp")
        cmds.sets(defSet, add=joint_support)
    except:
        pass

    return


def create_volume_joint(
    joint,
    offset=1,
    intensity=0.1,
    axis_push="y",
    axis_aim="x",
    rotate=60,
    joint_parent=None,
):
    """
    typ : bone,soft,both
    """

    # create joint blend
    joint_blend, node_pair_blend = create_blend_joint(joint=joint)

    # create joint support
    if rotate < 0:
        min = rotate
        max = 0

    elif rotate > 0:
        min = 0
        max = rotate
    else:
        min = 0
        max = 0

    index = 1

    while True:
        joint_name = "{}_support_{}".format(joint, index)

        if cmds.objExists(joint_name):
            index += 1
        else:
            break

    joint_support = cmds.createNode("joint", n="{}_support_{}".format(joint, index))

    axis_rot = Scene.get_exist_axis([axis_aim, axis_push])
    axis_push = axis_push
    index = 1

    # create support joint
    Utility.match_parent(joint_support, joint_blend)
    cmds.makeIdentity(joint_support, a=1, r=1)

    # add attribute to joint
    cmds.addAttr(joint_support, ln="biasX", dv=0, k=True)
    cmds.addAttr(joint_support, ln="biasY", dv=0, k=True)
    cmds.addAttr(joint_support, ln="biasZ", dv=0, k=True)

    cmds.addAttr(joint_support, ln="min".format(index), dv=min, k=True)
    cmds.addAttr(joint_support, ln="max".format(index), dv=max, k=True)
    cmds.addAttr(joint_support, ln="offset".format(index), dv=offset, k=True)

    cmds.addAttr(joint_support, ln="currentRotate".format(index), k=True)

    cmds.connectAttr(
        "{}.outRotate{}".format(node_pair_blend, axis_rot.upper()),
        "{}.currentRotate".format(joint_support, index),
    )

    # connection
    node_clamp = cmds.createNode("clamp")
    node_mdl = cmds.createNode("multDoubleLinear")
    node_adl = cmds.createNode("addDoubleLinear")

    cmds.connectAttr(
        "{}.outRotate{}".format(node_pair_blend, axis_rot.upper()),
        "{}.inputR".format(node_clamp),
    )
    cmds.connectAttr(
        "{}.min".format(joint_support, index),
        "{}.minR".format(node_clamp),
    )
    cmds.connectAttr(
        "{}.max".format(joint_support, index),
        "{}.maxR".format(node_clamp),
    )

    cmds.connectAttr("{}.outputR".format(node_clamp), "{}.input1".format(node_mdl))
    cmds.connectAttr(
        "{}.bias{}".format(joint_support, axis_push.upper()),
        "{}.input2".format(node_mdl),
    )

    cmds.connectAttr("{}.output".format(node_mdl), "{}.input1".format(node_adl))
    cmds.connectAttr(
        "{}.offset".format(joint_support, index),
        "{}.input2".format(node_adl),
    )

    cmds.connectAttr(
        "{}.output".format(node_adl), "{}.t{}".format(joint_support, axis_push)
    )

    # connect bias value
    axis_left = Scene.get_exist_axis([axis_push])
    for axis in axis_left:
        node_mdl = cmds.createNode("multDoubleLinear")

        node_clamp.outputR >> node_mdl.input1
        cmds.connectAttr(
            "{}.bias{}".format(joint_support, axis.upper()),
            "{}.input2".format(node_mdl),
        )
        cmds.connectAttr(
            "{}.output".format(node_mdl),
            "{}.translate{}".format(joint_support, axis.upper()),
        )

    # set default value
    cmds.setAttr("{}.bias{}".format(joint_support, axis_push.upper()), intensity)

    # add joint to mgear sets
    try:
        defSet = cmds.PyNode("rig_deformers_grp")
        cmds.sets(defSet, add=joint_support)
    except:
        pass

    return


def create_corrective_joint_four(
    joint,
    dict_data={
        1: {
            "axis": "z",
            "axis_push": "y",
            "factor": 0.1,
            "offset": 3,
            "min": 0,
            "max": 60,
        },
        2: {
            "axis": "y",
            "axis_push": "z",
            "factor": 0.1,
            "offset": 3,
            "min": 0,
            "max": 60,
        },
    },
    position_driver=None,
):

    # create joint
    joint_blend = cmds.createNode("joint", n="{}_blend".format(joint))

    # create node
    node_pair_blend = cmds.createNode("pairBlend")
    cmds.matchTransform(joint_blend, joint)
    cmds.parent(joint_blend, cmds.listRelatives(joint, p=1)[0])

    cmds.makeIdentity(joint_blend, a=1, r=1)
    node_pair_blend.weight.set(0.5)
    node_pair_blend.rotInterpolation.set(1)

    cmds.connectAttr("{}.t".format(joint), "{}.inTranslate1".format(node_pair_blend))
    cmds.connectAttr("{}.r".format(joint), "{}.inRotate1".format(node_pair_blend))
    cmds.connectAttr("{}.t".format(joint), "{}.inTranslate2".format(node_pair_blend))

    cmds.connectAttr("{}.outRotate".format(node_pair_blend), "{}.r".format(joint_blend))

    if position_driver:
        Connection.constraint_matrix(
            [position_driver, joint_blend], method="point", mo=False
        )
    else:
        cmds.connectAttr(
            "{}.outTranslate".format(node_pair_blend), "{}.t".format(joint_blend)
        )

    # create support joint
    for i, index in enumerate(dict_data.keys()):
        factor = dict_data[index]["factor"]
        axis = dict_data[index]["axis"]
        axis_push = dict_data[index]["axis_push"]
        offset = dict_data[index]["offset"]
        min = dict_data[index]["min"]
        max = dict_data[index]["max"]

        # create support joint
        joint_support = cmds.createNode("joint", n="{}_support_{}".format(joint, index))

        Utility.match_parent(joint_support, joint_blend)
        cmds.makeIdentity(joint_support, a=1, r=1)

        cmds.setAttr("{}.r{}".format(joint_support, axis), 90 * i)
        cmds.makeIdentity(joint_support, a=1, r=1)

        # add attribute to joint
        cmds.addAttr(
            joint_support, ln="joint_{}_factor".format(index), dv=factor, k=True
        )
        cmds.addAttr(
            joint_support, ln="joint_{}_min_rotate".format(index), dv=min, k=True
        )
        cmds.addAttr(
            joint_support, ln="joint_{}_max_rotate".format(index), dv=max, k=True
        )
        cmds.addAttr(
            joint_support, ln="joint_{}_offset".format(index), dv=offset, k=True
        )

        cmds.addAttr(joint_support, ln="joint_{}_current_rotate".format(index), k=True)

        cmds.connectAttr(
            "{}.outRotate{}".format(node_pair_blend, axis.upper()),
            "{}.joint_{}_current_rotate".format(joint_support, index),
        )

        # connection
        node_clamp = cmds.createNode("clamp")
        node_mdl = cmds.createNode("multDoubleLinear")
        node_adl = cmds.createNode("addDoubleLinear")

        cmds.connectAttr(
            "{}.outRotate{}".format(node_pair_blend, axis.upper()),
            "{}.inputR".format(node_clamp),
        )
        cmds.connectAttr(
            "{}.joint_{}_min_rotate".format(joint_support, index),
            "{}.minR".format(node_clamp),
        )
        cmds.connectAttr(
            "{}.joint_{}_max_rotate".format(joint_support, index),
            "{}.maxR".format(node_clamp),
        )

        cmds.connectAttr("{}.outputR".format(node_clamp), "{}.input1".format(node_mdl))
        cmds.connectAttr(
            "{}.bias{}".format(joint_support, axis_push.upper()),
            "{}.input2".format(node_mdl),
        )

        cmds.connectAttr("{}.output".format(node_mdl), "{}.input1".format(node_adl))
        cmds.connectAttr(
            "{}.joint_{}_offset".format(joint_support, index),
            "{}.input2".format(node_adl),
        )

        cmds.connectAttr(
            "{}.output".format(node_adl), "{}.t{}".format(joint_support, axis_push)
        )

        # add joint to mgear sets
        try:
            defSet = cmds.PyNode("rig_deformers_grp")
            cmds.sets(defSet, add=joint_support)
        except:
            pass

    return


def create_corrective_joint(
    block1,
    block2,
    joint_push,
    axis_push,
    axis_forward,
    axis_side,
    new_min_max=[0, 5],
    old_min_max=[0, 120],
    invert_angle=False,
    parent=None,
    tag_name="name",
):
    """
    Create Corrective Push Joint for wrist

    """

    def create_dummy_output():
        Transform.match_transform(locator_dummy, joint_push)
        # cmds.parent(locator_dummy,grp_corrective_joint)
        grp_frz = create_freeze_group([locator_dummy])[0]

        cmds.parentConstraint(locator_dummy, joint_push)

    def parent_by_matrix(locator, target):
        node_mult_matrix = cmds.createNode("multMatrix")
        cmds.connectAttr(
            "{}.worldMatrix[0]".format(target),
            "{}.inMatrix[0]".format(node_mult_matrix),
        )
        cmds.connectAttr(
            "{}.parentInverseMatrix[0]".format(locator),
            "{}.inMatrix[1]".format(node_mult_matrix),
        )

        node_decomp_matrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(
            "{}.outMatrix".format(node_mult_matrix),
            "{}.inMatrix".format(node_decomp_matrix),
        )
        cmds.connectAttr(
            "{}.outTranslate".format(node_decomp_matrix), "{}.translate".format(locator)
        )

    def create_vector_position():
        grp_loc1 = create_freeze_group([locator_1])[0]
        grp_loc2 = create_freeze_group([locator_2])[0]
        grp_zero = create_freeze_group([locator_zero])[0]

        # position vector zero
        cmds.parentConstraint(block2, grp_zero)

        # position vector 1
        constraint = cmds.parentConstraint(block2, grp_loc1)
        cmds.delete(constraint)
        cmds.parentConstraint(block1, grp_loc1, mo=1)

        cmds.setAttr("{}.t{}".format(locator_1, axis_forward_abs), -1)  # move

        # position vector 2
        cmds.parentConstraint(block2, grp_loc2)
        cmds.setAttr("{}.t{}".format(locator_2, axis_forward_abs), 1)  # move
        grp_rot = create_freeze_group([locator_2], "grpRot", match_object=locator_zero)[
            0
        ]  # rotate for make 120

        if invert_angle:
            cmds.setAttr("{}.r{}".format(grp_rot, axis_side_abs), -60)
        else:
            cmds.setAttr("{}.r{}".format(grp_rot, axis_side_abs), 60)

    def create_angle_between():
        # create vector 1
        node_pma_vector1 = cmds.createNode(
            "plusMinusAverage", n=Scene.cname(tag_name, "vector1", "pma")
        )
        cmds.setAttr("{}.operation".format(node_pma_vector1), 2)
        cmds.connectAttr(
            "{}.worldPosition".format(cmds.listRelatives(locator_1, c=1, s=1)[0]),
            "{}.input3D[0]".format(node_pma_vector1),
        )
        cmds.connectAttr(
            "{}.worldPosition".format(cmds.listRelatives(locator_zero, c=1, s=1)[0]),
            "{}.input3D[1]".format(node_pma_vector1),
        )
        attr_vector1 = "{}.output3D".format(node_pma_vector1)

        # create vector 2
        node_pma_vector2 = cmds.createNode(
            "plusMinusAverage", n=Scene.cname(tag_name, "vector2", "pma")
        )
        cmds.setAttr("{}.operation".format(node_pma_vector2), 2)
        cmds.connectAttr(
            "{}.worldPosition".format(cmds.listRelatives(locator_2, c=1, s=1)[0]),
            "{}.input3D[0]".format(node_pma_vector2),
        )
        cmds.connectAttr(
            "{}.worldPosition".format(cmds.listRelatives(locator_zero, c=1, s=1)[0]),
            "{}.input3D[1]".format(node_pma_vector2),
        )
        attr_vector2 = "{}.output3D".format(node_pma_vector2)

        # invert vector
        # if invert_angle:
        node_md_invert = cmds.createNode(
            "multiplyDivide", n=Scene.cname(tag_name, "invertVector", "md")
        )
        cmds.connectAttr(attr_vector1, "{}.input1".format(node_md_invert))
        cmds.setAttr("{}.input2".format(node_md_invert), -1, -1, -1, typ="double3")
        attr_vector1 = "{}.output".format(node_md_invert)

        # angle between
        node_angle_between = cmds.createNode(
            "angleBetween", n=Scene.cname(tag_name, "anglePush", "ab")
        )
        cmds.connectAttr(attr_vector1, "{}.vector1".format(node_angle_between))
        cmds.connectAttr(attr_vector2, "{}.vector2".format(node_angle_between))

        # set range
        new_min, new_max = new_min_max
        # old_min,old_max = old_min_max

        node_set_range = cmds.createNode(
            "setRange", n=Scene.cname(tag_name, "remap", "sr")
        )
        cmds.connectAttr(
            "{}.angle".format(node_angle_between), "{}.valueX".format(node_set_range)
        )
        cmds.setAttr("{}.minX".format(node_set_range), new_min)
        cmds.setAttr("{}.maxX".format(node_set_range), new_max)

        # if invert_angle:
        cmds.setAttr("{}.oldMinX".format(node_set_range), 60)
        cmds.setAttr("{}.oldMaxX".format(node_set_range), 180)
        # else:
        #     cmds.setAttr("{}.oldMinX".format(node_set_range),0)
        #     cmds.setAttr("{}.oldMaxX".format(node_set_range),120)

        # connect to output
        cmds.connectAttr(
            "{}.outValueX".format(node_set_range),
            "{}.t{}".format(locator_dummy, axis_push),
        )

    def create_hierarchy():
        def create_position_output():
            node_decompose_output = cmds.createNode(
                "decomposeMatrix", n=Scene.cname(tag_name, "MatchTransform", "dcm")
            )
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(block2),
                "{}.inputMatrix".format(node_decompose_output),
            )
            cmds.connectAttr(
                "{}.outputTranslate".format(node_decompose_output),
                "{}.translate".format(grp_base_orient),
            )
            cmds.connectAttr(
                "{}.outputRotate".format(node_decompose_output),
                "{}.rotate".format(grp_base_orient),
            )
            cmds.connectAttr(
                "{}.outputScale".format(node_decompose_output),
                "{}.scale".format(grp_base_orient),
            )

        def create_avg_orient_output():
            node_decompose_block1 = cmds.createNode(
                "decomposeMatrix",
                n=Scene.cname(tag_name, "{}Rotate".format(block1), "dcm"),
            )
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(block1),
                "{}.inputMatrix".format(node_decompose_block1),
            )

            node_decompose_block2 = cmds.createNode(
                "decomposeMatrix",
                n=Scene.cname(tag_name, "{}Rotate".format(block2), "dcm"),
            )
            cmds.connectAttr(
                "{}.worldMatrix[0]".format(block2),
                "{}.inputMatrix".format(node_decompose_block2),
            )

            node_pair_blend = cmds.createNode(
                "pairBlend", n=Scene.cname(tag_name, "AvgRotate", "pb")
            )
            cmds.setAttr("{}.rotInterpolation".format(node_pair_blend), 1)
            cmds.setAttr("{}.weight".format(node_pair_blend), 0.5)
            cmds.connectAttr(
                "{}.outputRotate".format(node_decompose_block1),
                "{}.inRotate1".format(node_pair_blend),
            )
            cmds.connectAttr(
                "{}.outputRotate".format(node_decompose_block2),
                "{}.inRotate2".format(node_pair_blend),
            )

            node_compose_matrix = cmds.createNode(
                "composeMatrix", n=Scene.cname(tag_name, "AvgRotate", "cm")
            )
            cmds.connectAttr(
                "{}.outRotate".format(node_pair_blend),
                "{}.inputRotate".format(node_compose_matrix),
            )

            node_mult_matrix = cmds.createNode(
                "multMatrix", n=Scene.cname(tag_name, "offsetMatrix", "mm")
            )
            cmds.connectAttr(
                "{}.outputMatrix".format(node_compose_matrix),
                "{}.matrixIn[0]".format(node_mult_matrix),
            )
            cmds.connectAttr(
                "{}.parentInverseMatrix".format(grp_avg_orient),
                "{}.matrixIn[1]".format(node_mult_matrix),
            )

            node_decompose_output = cmds.createNode(
                "decomposeMatrix", n=Scene.cname(tag_name, "OutputAvgRotate", "dcm")
            )
            cmds.connectAttr(
                "{}.matrixSum".format(node_mult_matrix),
                "{}.inputMatrix".format(node_decompose_output),
            )
            cmds.connectAttr(
                "{}.outputRotate".format(node_decompose_output),
                "{}.rotate".format(grp_avg_orient),
            )

        cmds.group(em=1, n=grp_corrective_joint)
        cmds.setAttr("{}.inheritsTransform".format(grp_corrective_joint), False)

        cmds.group(em=1, n=grp_base_orient, p=grp_corrective_joint)
        cmds.group(em=1, n=grp_avg_orient, p=grp_base_orient)

        cmds.parent(grp_corrective_joint, parent) if parent else None

        cmds.spaceLocator(n=locator_1)
        cmds.spaceLocator(n=locator_2)
        cmds.spaceLocator(n=locator_zero)
        cmds.spaceLocator(n=locator_dummy)

        cmds.parent(locator_dummy, grp_avg_orient)
        cmds.parent(locator_zero, locator_1, locator_2, grp_corrective_joint)

        create_position_output()
        create_avg_orient_output()

    # variables
    grp_corrective_joint = Scene.cname(tag_name, "Corrective")
    grp_base_orient = Scene.cname(tag_name, "BaseOrient")
    grp_avg_orient = Scene.cname(tag_name, "AvgOrient")

    locator_dummy = Scene.cname(tag_name, "dummy")
    locator_1 = Scene.cname(tag_name, "pos1")
    locator_2 = Scene.cname(tag_name, "pos2")
    locator_zero = Scene.cname(tag_name, "posZro")

    axis_forward_abs = Scene.del_neg(axis_forward)
    axis_side_abs = Scene.del_neg(axis_side)

    # build
    create_hierarchy()

    create_dummy_output()
    create_vector_position()

    create_angle_between()


def create_ik_reverse(
    control_setting,
    control_parent_ik,
    control_parent_fk,
    axis_foot_three,
    list_locator_pivot,
    ball_joint,
    toe_joint,
    jnt_ball_fk,
    jnt_toe_fk,
    jnt_ball_ik,
    jnt_toe_ik,
    ankle_joint_ik,
    parent,
    list_parent_reverse=[],
    name_tag="Foot",
    invert_toe_twist_value=False,
    invert_middle_twist_value=False,
    invert_roll_side_axis=False,
    invert_side_roll_value=False,
    invert_heel_twist_value=False,
    invert_roll_axis=False,
    invert_roll_value=False,
    auto_roll_default_value=0,
):

    def create_ik_function():
        def create_attributes():
            # anim attributes
            Utility.add_attribute_divider(control_setting, "IkPivot")

            cmds.addAttr(
                attr_foot_pitch.split(".")[0],
                ln=attr_foot_pitch.split(".")[1],
                at="float",
                k=1,
            )
            cmds.addAttr(
                attr_bank.split(".")[0], ln=attr_bank.split(".")[1], at="float", k=1
            )
            cmds.addAttr(
                attr_toe_pitch.split(".")[0],
                ln=attr_toe_pitch.split(".")[1],
                at="float",
                k=1,
            )
            cmds.addAttr(
                attr_heel_twist.split(".")[0],
                ln=attr_heel_twist.split(".")[1],
                at="float",
                k=1,
            )
            cmds.addAttr(
                attr_toe_twist.split(".")[0],
                ln=attr_toe_twist.split(".")[1],
                at="float",
                k=1,
            )

            # config attributes
            # add_attribute_divider(option_shape, name="Ik_config".format(name_tag))
            cmds.addAttr(
                attr_roll_ball_end.split(".")[0],
                ln=attr_roll_ball_end.split(".")[1],
                at="float",
                k=1,
                dv=auto_roll_default_value,
            )

        def create_hierarchy():
            # create group hierarchy
            grp_local_reverse = cmds.group(
                em=1, n="{}_reverse_ik_grp".format(name_tag), p=parent
            )
            cmds.connectAttr(
                control_parent_ik + ".rotateOrder",
                grp_local_reverse + ".rotateOrder",
                f=1,
            )
            cmds.parentConstraint(control_parent_ik, grp_local_reverse)

            # break connection
            Utility.break_transform_attribute(ankle_joint_ik, rot=True)

            # create reversed chain joint
            cmds.select(cl=1)
            for i, joint in enumerate(list_pivot_joint):
                joint.visibility.set(False)
                cmds.matchTransform(joint, list_pivot_match[i], pos=1)
                cmds.matchTransform(joint, jnt_ball_ik, rot=1)
                cmds.makeIdentity(joint, a=1, s=1, r=1)

            cmds.parent(list_pivot_joint[0], grp_local_reverse)

            # orient constraint piv to ik joint

            loc_ball_orient = cmds.spaceLocator(n="{}_ballOrient_loc".format(name_tag))
            loc_ball_orient.visibility.set(False)
            constraint = cmds.parentConstraint(jnt_ball_ik, loc_ball_orient)
            cmds.delete(constraint)
            cmds.parent(loc_ball_orient, piv_outer)
            constraint_toe_orient.append(
                cmds.orientConstraint(loc_ball_orient, jnt_ball_ik)
            )

            loc_ankle_orient = cmds.spaceLocator(
                n="{}_ankleOrient_loc".format(name_tag)
            )
            loc_ankle_orient.visibility.set(False)
            cmds.connectAttr(
                control_parent_ik + ".rotateOrder",
                loc_ankle_orient + ".rotateOrder",
                f=1,
            )
            constraint = cmds.parentConstraint(jnt_ankle_ik, loc_ankle_orient)
            cmds.delete(constraint)
            cmds.parent(loc_ankle_orient, piv_ball)
            cmds.orientConstraint(loc_ankle_orient, jnt_ankle_ik)

            # parent ankle,pos end to piv
            for object in list_parent_reverse:
                if cmds.objExists(object):
                    Utility.break_transform_attribute(object, pos=True, rot=True)
                    cmds.parentConstraint(piv_ankle, object, mo=1)

        def create_connection():
            def connect_side_roll():
                if invert_roll_side_axis:
                    first_target = piv_outer
                    second_target = piv_inner
                else:
                    first_target = piv_inner
                    second_target = piv_outer

                if invert_side_roll_value:
                    node_mdl_invert = cmds.createNode(
                        "multDoubleLinear", n="{}_rollSide_mdl".format(name_tag)
                    )
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(attr_bank, "{}.input1".format(node_mdl_invert))
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_bank

                # Bank
                cmds.setAttr(
                    "{}.minRot{}LimitEnable".format(
                        first_target, axis_foot_forward.upper()
                    ),
                    1,
                )
                cmds.setAttr(
                    "{}.minRot{}Limit".format(first_target, axis_foot_forward.upper()),
                    0,
                )

                cmds.setAttr(
                    "{}.maxRot{}LimitEnable".format(
                        second_target, axis_foot_forward.upper()
                    ),
                    1,
                )
                cmds.setAttr(
                    "{}.maxRot{}Limit".format(second_target, axis_foot_forward.upper()),
                    0,
                )

                cmds.connectAttr(
                    attr_output, "{}.r{}".format(first_target, axis_foot_forward)
                )
                cmds.connectAttr(
                    attr_output, "{}.r{}".format(second_target, axis_foot_forward)
                )

            def connect_base_twist():
                if invert_heel_twist_value:
                    node_mdl_invert = cmds.createNode(
                        "multDoubleLinear", n="{}_baseTwist_mdl".format(name_tag)
                    )
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(
                        attr_heel_twist, "{}.input1".format(node_mdl_invert)
                    )
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_heel_twist

                cmds.connectAttr(
                    attr_output, "{}.r{}".format(piv_heel_twist, axis_foot_twist)
                )

            def connect_tip_twist():
                if invert_toe_twist_value:
                    node_mdl_invert = cmds.createNode(
                        "multDoubleLinear", n="{}_tipTwist_mdl".format(name_tag)
                    )
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(
                        attr_toe_twist, "{}.input1".format(node_mdl_invert)
                    )
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_toe_twist

                cmds.connectAttr(attr_output, "{}.r{}".format(piv_end, axis_foot_twist))

            def connect_middle_twist():
                if invert_middle_twist_value:
                    node_mdl_invert = cmds.createNode(
                        "multDoubleLinear", n="{}_tipTwist_mdl".format(name_tag)
                    )
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(
                        attr_toe_pitch, "{}.input1".format(node_mdl_invert)
                    )
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_toe_pitch

                # Toe tap
                node_adl_toe_tap = cmds.createNode(
                    "addDoubleLinear", n="{}_tipTwist_adl".format(name_tag)
                )

                cmds.connectAttr(
                    "{}.constraintRotate{}".format(
                        constraint_toe_orient[0], axis_foot_side.upper()
                    ),
                    "{}.input1".format(node_adl_toe_tap),
                )
                cmds.connectAttr(attr_output, "{}.input2".format(node_adl_toe_tap))

                cmds.connectAttr(
                    "{}.output".format(node_adl_toe_tap),
                    "{}.r{}".format(jnt_ball_ik, axis_foot_side),
                    f=1,
                )

            def connect_roll():
                def connect_roll_back():
                    if invert_roll_axis:
                        value_cond_operation = 4
                    else:
                        value_cond_operation = 2

                    # Roll Out
                    node_cond_roll_out = cmds.createNode(
                        "condition", n="{}_rollOut_cond".format(name_tag)
                    )
                    cmds.setAttr(
                        "{}.operation".format(node_cond_roll_out), value_cond_operation
                    )

                    cmds.setAttr("{}.colorIfFalseR".format(node_cond_roll_out), 0)
                    cmds.connectAttr(
                        attr_output, "{}.firstTerm".format(node_cond_roll_out)
                    )
                    cmds.connectAttr(
                        attr_output, "{}.colorIfTrueR".format(node_cond_roll_out)
                    )

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_out),
                        "{}.r{}".format(piv_heel_roll, axis_foot_side),
                    )

                def connect_roll_front():
                    # Roll In --------------------------
                    if invert_roll_axis:
                        value_condition = 4
                    else:
                        value_condition = 2

                    # node roll in
                    node_cond_roll_in = cmds.createNode(
                        "condition", n="{}_rollIn_cond".format(name_tag)
                    )
                    cmds.setAttr(
                        "{}.operation".format(node_cond_roll_in), value_condition
                    )

                    cmds.connectAttr(
                        attr_output, "{}.firstTerm".format(node_cond_roll_in)
                    )
                    cmds.setAttr("{}.colorIfTrueR".format(node_cond_roll_in), 0)
                    cmds.connectAttr(
                        attr_output, "{}.colorIfFalseR".format(node_cond_roll_in)
                    )

                    # roll ball
                    node_cond_roll_ball = cmds.createNode(
                        "condition", n="{}_rollBall_cond".format(name_tag)
                    )
                    cmds.setAttr(
                        "{}.operation".format(node_cond_roll_ball), value_condition
                    )

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_in),
                        "{}.firstTerm".format(node_cond_roll_ball),
                    )
                    cmds.connectAttr(
                        attr_roll_ball_end, "{}.secondTerm".format(node_cond_roll_ball)
                    )

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_in),
                        "{}.colorIfTrueR".format(node_cond_roll_ball),
                    )
                    cmds.connectAttr(
                        attr_roll_ball_end,
                        "{}.colorIfFalseR".format(node_cond_roll_ball),
                    )

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_ball),
                        "{}.r{}".format(piv_ball, axis_foot_side),
                    )

                    # roll end
                    node_cond_roll_end = cmds.createNode(
                        "condition", n="{}_rollEnd_cond".format(name_tag)
                    )
                    cmds.setAttr(
                        "{}.operation".format(node_cond_roll_end), value_condition
                    )

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_in),
                        "{}.firstTerm".format(node_cond_roll_end),
                    )
                    cmds.connectAttr(
                        attr_roll_ball_end, "{}.secondTerm".format(node_cond_roll_end)
                    )

                    node_pma_roll_end_offset = cmds.createNode(
                        "plusMinusAverage", n="{}_rollEndOffset_pma".format(name_tag)
                    )
                    cmds.setAttr("{}.operation".format(node_pma_roll_end_offset), 2)

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_in),
                        "{}.input1D[0]".format(node_pma_roll_end_offset),
                    )
                    cmds.connectAttr(
                        attr_roll_ball_end,
                        "{}.input1D[1]".format(node_pma_roll_end_offset),
                    )
                    cmds.connectAttr(
                        "{}.output1D".format(node_pma_roll_end_offset),
                        "{}.colorIfFalseR".format(node_cond_roll_end),
                    )

                    cmds.connectAttr(
                        "{}.outColorR".format(node_cond_roll_end),
                        "{}.r{}".format(piv_end, axis_foot_side),
                    )

                if invert_roll_value:
                    attr_output = Connection.connect_conversion(
                        input1=attr_foot_pitch, conversion=-1, name=name_tag
                    )
                else:
                    attr_output = attr_foot_pitch

                connect_roll_back()
                connect_roll_front()

            connect_base_twist()
            connect_tip_twist()
            connect_middle_twist()
            connect_side_roll()
            connect_roll()

        # variables
        jnt_ankle_ik = ankle_joint_ik
        constraint_toe_orient = []

        # add option shape to control ankle ik
        # option_shape = add_option_shape(object=control_setting, name="{}_option".format(name_tag))

        # define all variables
        attr_foot_pitch = control_setting + ".roll"
        attr_bank = control_setting + ".sideRoll"
        attr_heel_twist = control_setting + ".baseTwist"
        attr_toe_twist = control_setting + ".tipTwist"
        attr_toe_pitch = control_setting + ".middleRoll"
        attr_roll_ball_end = control_setting + ".rollBallEnd"

        piv_heel_twist = cmds.joint(n="{}_heelTwist_piv".format(name_tag))
        piv_end = cmds.joint(n="{}_end_piv".format(name_tag))
        piv_heel_roll = cmds.joint(n="{}_heelRoll_piv".format(name_tag))
        piv_inner = cmds.joint(n="{}_inner_piv".format(name_tag))
        piv_outer = cmds.joint(n="{}_outer_piv".format(name_tag))
        piv_ball = cmds.joint(n="{}_ball_piv".format(name_tag))
        piv_ankle = cmds.joint(n="{}_ankle_piv".format(name_tag))

        match_inner, match_outer, match_heel, match_end = list_locator_pivot

        list_pivot_match = [
            match_heel,
            match_end,
            match_heel,
            match_inner,
            match_outer,
            jnt_ball_ik,
            jnt_ankle_ik,
        ]
        list_pivot_joint = [
            piv_heel_twist,
            piv_end,
            piv_heel_roll,
            piv_inner,
            piv_outer,
            piv_ball,
            piv_ankle,
        ]

        # main operation
        create_attributes()
        create_hierarchy()
        create_connection()

    def create_fk_function():
        # create control ball fk
        Create.create_control(
            name="{}_{}".format(ctrl, jnt_ball_fk),
            match=jnt_ball_fk,
            parent=control_parent_fk,
            constraint="parent",
            freeze_group=True,
        )

    # get pivot of foot
    axis_foot_forward, axis_foot_side, axis_foot_twist = [
        axis for axis in axis_foot_three
    ]
    loc_inner_piv, loc_outer_piv, loc_heel_piv, loc_end_piv = list_locator_pivot

    create_ik_function()
    # create_fk_function()


def create_locator_on_curve(amount, list_curve, size=0.5):
    """
    This Function Use to create locator on given curve

    Return
    locators the created

    """

    locators = []

    for curve in list_curve:
        if not Utility.is_py_node(curve):
            curve = cmds.PyNode(curve)

        curve_transform = curve
        curve_shape = cmds.listRelatives(curve_transform, c=1, s=1, typ="nurbsCurve")[0]

        if "crv_" in curve_transform:
            main_name = curve_transform.replace("crv_", "")
        else:
            main_name = curve_transform

        for i in range(amount):
            locator = cmds.spaceLocator(
                n="loc_" + main_name + "_" + str(i + 1).zfill(2)
            )
            node = cmds.createNode("pointOnCurveInfo")

            if amount == 1:
                param = 0.5
            else:
                param = i * (1 / (amount - 1))

            # connect locator
            node.turnOnPercentage.set(True)
            node.parameter.set(param)

            curve_shape.worldSpace >> node.inputCurve
            node.position >> locator.translate

            locators.append(locator)

    return locators


def ribbon_plane(name, ref, faxis="y", sub=5, drv=3, snap=0):
    """Create a ribbon plane which have follicles attach along surface and was bind skin by driver joint

    Args:
        name (str) : The ribbon node_name
        ref (list) : The list of reference joints
        faxis (str) : forward axis x,y,z
        sub (int) : amount of follicles and sub joints
        drv (int) : amount of driver joints
        snap (int) : 0 = Do not snap ,1 = snap one per one ,2 = division method

    Return:
        1) (list) sub joints
        2) (list) driver joints
        3) (str) nurbs transform
        4) (list) follicles
    """
    # calculate lengths from main joints
    width = 0
    for i in range(len(ref) - 1):
        node_distance = cmds.createNode("distanceBetween")
        cmds.connectAttr(ref[i] + ".worldMatrix[0]", node_distance + ".inMatrix1")
        cmds.connectAttr(ref[i + 1] + ".worldMatrix[0]", node_distance + ".inMatrix2")
        width += cmds.getAttr(node_distance + ".distance")
        cmds.delete(node_distance)

    # create ribbon plane
    nrb_shape = cmds.listRelatives(
        cmds.nurbsPlane(
            n="nrb_" + name + "_ribbon",
            ax=(0, 0, 1),
            w=width,
            lr=0.05,
            u=sub - 1,
            v=1,
            ch=0,
        ),
        c=1,
    )[0]

    # create follicles
    list_flc = []
    for i in range(1, sub + 1):
        flc_shape = cmds.createNode("follicle", n=f"flc_{name}_shape_{i}")
        cmds.setAttr(flc_shape + ".simulationMethod", 0)
        cmds.setAttr(flc_shape + ".parameterV", 0.5)

        value = 1 / (sub - 1)
        cmds.setAttr(flc_shape + ".parameterU", value * (i - 1))
        cmds.connectAttr(nrb_shape + ".local", flc_shape + ".inputSurface")
        cmds.connectAttr(nrb_shape + ".worldMatrix[0]", flc_shape + ".inputWorldMatrix")

        flc_transform = cmds.rename(
            cmds.listRelatives(flc_shape, p=1, f=1)[0], f"flc_{name}_{i}"
        )
        cmds.connectAttr(flc_shape + ".outRotate", flc_transform + ".rotate")
        cmds.connectAttr(flc_shape + ".outTranslate", flc_transform + ".translate")
        list_flc.append(flc_transform)

    # create joint sub
    list_jntSub = []
    for i in range(sub):
        # create sub joint
        jntSub = cmds.joint(n=f"jnt_sub_{name}_ribbon_{i + 1}", rad=0.5)
        cmds.matchTransform(jntSub, list_flc[i], pos=1, rot=0, scl=0)
        list_jntSub.append(jntSub)

    if faxis == "x":
        oj = "xyz"
    elif faxis == "y":
        oj = "yxz"
    elif faxis == "z":
        oj = "zyx"

    # orient joint and separate joint
    cmds.joint(list_jntSub[0], e=1, oj=oj, sao="xup", ch=1, zso=1)
    cmds.joint(list_jntSub[-1], e=1, oj="none", ch=1, zso=1)

    for i in range(sub):
        cmds.parent(list_jntSub[i], list_flc[i])

    # move all bind joint to follicles group
    grp_flc = cmds.group(em=1, n=f"grp_flc_{name}")
    for i in range(sub):
        cmds.parent(list_flc[i], grp_flc)

    # create drv joints
    grp_drv = cmds.group(em=1, n=f"grp_jntDrv_{name}")
    offset = cmds.xform(list_jntSub[0], q=1, ws=1, t=1)[0]
    list_jntDrv = []

    for i in range(drv):
        drv_value = (i * (width / (drv - 1))) + offset
        cmds.select(cl=1)
        jntDrv = cmds.joint(n=f"jnt_drv_{name}_ribbon_{i + 1}")
        cmds.matchTransform(jntDrv, list_jntSub[0], rot=1)
        cmds.setAttr(jntDrv + ".radius", cmds.getAttr(jntSub + ".radius") * 3)
        cmds.setAttr(jntDrv + ".translateX", drv_value)
        cmds.parent(jntDrv, grp_drv)
        list_jntDrv.append(jntDrv)

    # bind skin to nurb
    cmds.skinCluster(nrb_shape, list_jntDrv, ih=1, mi=2, n=f"skinCluster_{name}_ribbon")

    if snap == 1 and drv == len(ref):
        for i in range(drv):
            cmds.matchTransform(list_jntDrv[i], ref[i])

    # snap division method
    elif (len(ref) * 2) - 1 == drv:
        count = 0
        for i in range(drv):
            # divide case
            if (i + 1) % 2 == 0:
                rot = cmds.xform(ref[count - 1], q=1, ws=1, ro=1)
                pos1 = cmds.xform(ref[count - 1], q=1, ws=1, t=1)
                pos2 = cmds.xform(ref[count], q=1, ws=1, t=1)

                avg_pos = [0, 0, 0]
                for axis in range(3):
                    avg_pos[axis] = (pos1[axis] + pos2[axis]) / 2

                cmds.xform(list_jntDrv[i], ws=1, t=avg_pos, ro=rot)

            # point case
            else:
                cmds.matchTransform(list_jntDrv[i], ref[count])
                count += 1

    return list_jntSub, list_jntDrv, nrb_shape, list_flc
