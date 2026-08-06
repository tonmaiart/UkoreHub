from EasySkeleton import config
from EasySkeleton.config import *
import re
import math
import maya.cmds as cmds
import maya.mel as mel

def undoable(func):
    def wrapper(*args, **kwargs):
        # Enable undo before the function execution
        undo = cmds.undoInfo(openChunk=True)

        try:
            # Execute the function
            result = func(*args, **kwargs)
        finally:
            # Ensure undo is closed after the function execution
            cmds.undoInfo(closeChunk=True)

        return result

    return wrapper


def set_width():
    def get_width_user():
        result = cmds.promptDialog(
            title='Enter Scale Size Percentage',
            message='Enter Scale Size Percentage :',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel',
            tx=1)

        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True)
        else:
            raise Exception("was Canceled")

        if not text.isdigit():
            cmds.confirmDialog(m="Invalid Input, Required Amount, Get {}".format(text))
            raise Exception("Invalid Input, Required Amount, Get {}".format(text))

        return float(text)

    line_width = get_width_user()
    list_shape = []

    # filter shape
    for sel in cmds.ls(sl=1):
        list_child = cmds.listRelatives(sel, c=1, s=1, f=1)

        if list_child:
            for child in list_child:
                if cmds.objectType(child) == "nurbsCurve":
                    list_shape.append(child)

    # apply color
    if list_shape:
        for shape in list_shape:
            cmds.setAttr(shape + ".lineWidth", line_width)

def get_curve_data(shape_path):
    """return the list shape data (spans, degree, list_position) reference by input shape node_name

    shape_path : [str] shape node_name or path"""

    list_shape_data = []
    spans = cmds.getAttr("{}.spans".format(shape_path))
    degree = cmds.getAttr("{}.degree".format(shape_path))
    cv_amount = spans + degree
    list_position = []

    for i in range(cv_amount):
        local_translate = cmds.xform("{}.cv[{}]".format(shape_path, i), os=1, t=1, q=1)
        local_translate = ["%.4f" % value for value in local_translate]
        list_position.append(local_translate)

    list_shape_data.append(spans)
    list_shape_data.append(degree)
    list_shape_data.append(list_position)

    return list_shape_data

def set_proper_shape_name(control):
    list_shape = cmds.listRelatives(control, c=1, s=1, typ="nurbsCurve", f=1)
    for i, shape in enumerate(list_shape):
        cmds.rename(shape, "{}Shape".format(cut(control)))

@undoable
def clone_shape(selection =None ):
    if not selection:
        selection = cmds.ls(sl=1, typ="transform", l=1)

    # sort shape
    list_target = selection[0:len(selection) - 1]
    ref = selection[-1]
    list_ref_shape = cmds.listRelatives(selection[-1], c=1, s=1, typ="nurbsCurve", f=1)  # get ref shape of reference shape
    ref_width = cmds.getAttr(list_ref_shape[0] + ".lineWidth")

    # clear all shape of base_mesh
    for target in list_target:
        for list_delete in cmds.listRelatives(target, c=1, s=1, typ="nurbsCurve", f=1):
            if list_delete:
                cmds.delete(list_delete)

    # apply
    for target in list_target:
        dup_transform = cmds.duplicate(ref)[0]
        dup_shapes = cmds.listRelatives(dup_transform, c=1, s=1, f=1, typ="nurbsCurve")
        if dup_shapes:
            for shape in dup_shapes:
                cmds.setAttr("{}.lineWidth".format(shape), ref_width)
                cmds.parent(shape, target, r=1, s=1)

        cmds.delete(dup_transform)

    for target in list_target:
        set_proper_shape_name(target)

def isolate_edit(snap: bool, isolate: bool):
    selection = cmds.ls(sl=1)
    cmds.select(cl=1)

    for sel in selection:
        if cmds.objectType(sel, isa="nurbsCurve"):
            cmds.select(sel, add=1)

        child_shape = cmds.listRelatives(sel, c=1, s=1, f=1)

        if child_shape:
            cmds.select(child_shape, add=1)

    current_select = cmds.ls(sl=1, typ="nurbsCurve")
    if current_select:
        if isolate:  # isolate
            current_panel = cmds.getPanel(withFocus=True)
            cmds.isolateSelect(current_panel, s=1)
            cmds.isolateSelect(current_panel, addSelected=True)

        if snap:  # Frame the selected objects in the viewport
            cmds.viewFit()

    mel.eval("changeSelectMode -component;")

    # for shape in current_select:
    for shape in current_select:
        data = get_curve_data(shape)
        cmds.select("{}.cv[0:{}]".format(shape, data[0] + data[1] - 1), add=1)

def isolate_clear():
    current_panel = cmds.getPanel(withFocus=True)
    cmds.isolateSelect(current_panel, s=0)

    list_transform = []
    selection = cmds.ls(sl=1)
    if selection:
        for sel in selection:
            # cv case
            if ".cv" in sel:
                sel = sel.split(".cv")[0]
                list_transform.append(sel)

            # shape case
            elif cmds.objectType(sel, isa="nurbsCurve"):
                list_transform.append(cmds.listRelatives(sel, p=1, typ="transform")[0])

            # transform case
            elif cmds.objectType(sel, isa="transform"):
                list_transform.append(sel)

    mel.eval("changeSelectMode -object;")
    cmds.select(list_transform)


@undoable
def clone_to_opposite():
    def get_opposite_control():
        list_all_transform = cmds.ls(typ="transform")
        list_return = []

        for transform in list_all_transform:
            if config.L in transform:
                list_return.append(transform)
            # if (transform.startswith(ctrl) or transform.endswith(ctrl)) and "bck" not in transform and config.L in transform:
            #     list_return.append(transform)

        return list_return

    list_control =  cmds.ls(sl=1) #get_opposite_control()
    list_opposite_selected = []

    for control in list_control:
        # define new node_name
        if config.L in control:
            ctrl_opposite = control.replace(config.L, config.R)
        else:
            ctrl_opposite = control.replace(config.R, config.L)


        if not cmds.objExists(ctrl_opposite):
            cmds.warning("{} not found for mirror control".format(ctrl_opposite))
            continue

        list_opposite_selected.append(ctrl_opposite)

        # create temp control and clear child
        ctrl_tmp = cmds.duplicate(control)[0]
        lock_attributes(ctrl_tmp, r=1, s=1, t=1, v=1, k=1, l=0)

        if cmds.listRelatives(ctrl_tmp,p=1):
            cmds.parent(ctrl_tmp, w=1)

        target_child = cmds.listRelatives(ctrl_tmp, c=1, typ="transform", f=1)
        if target_child:
            cmds.delete(target_child)

        # mirror scale of tmp ctrl
        cmds.setAttr(ctrl_tmp + ".s", -1, -1, -1, typ="double3")
        cmds.makeIdentity(ctrl_tmp, s=1, a=1)

        # clear opposite control shapes
        delete_shapes = cmds.listRelatives(ctrl_opposite, c=1, s=1, f=1, typ="nurbsCurve")
        if delete_shapes:
            cmds.delete(delete_shapes)

        # re parent to opposite control
        list_shape_parent = cmds.listRelatives(ctrl_tmp, c=1, s=1, f=1, typ="nurbsCurve")
        if list_shape_parent:
            cmds.parent(list_shape_parent, ctrl_opposite, s=1, r=1)
        cmds.delete(ctrl_tmp)

    cmds.select(list_opposite_selected,r=1)
@undoable
def flip_shape(axis: str):
    cmds.undoInfo(ock=1)
    selection = cmds.ls(sl=1, typ="transform", l=1)

    for sel in selection:
        tmp_transform = cmds.duplicate(sel)[0]

        list_child = cmds.listRelatives(tmp_transform,c=1,typ="transform",f=1)

        if list_child:
            cmds.delete(list_child)

        lock_attributes(tmp_transform,s=1,l=0)


        cmds.setAttr("{}.s{}".format(tmp_transform, axis), -1)


        cmds.makeIdentity(tmp_transform, a=1, s=1)



        cmds.select(sel, tmp_transform)
        clone_shape()
        cmds.delete(tmp_transform)

    cmds.select(selection)
    cmds.undoInfo(cck=1)


@undoable
def set_curve_color(list_target, index=None, rgb=None, clear=False):
    list_shape = []

    # filter shape
    for sel in list_target:
        # sel shape
        if cmds.objectType(sel, isa="nurbsCurve"):
            list_shape.append(sel)

        # child shape
        list_child = cmds.listRelatives(sel, c=1, s=1, f=1)

        if list_child:
            for child in list_child:
                if cmds.objectType(child) == "nurbsCurve":
                    list_shape.append(child)

    # apply color
    if list_shape:
        for shape in list_shape:
            if clear:
                cmds.setAttr(shape + ".overrideEnabled", 0)
                continue

            else:
                cmds.setAttr(shape + ".overrideEnabled", 1)

                if index:
                    cmds.setAttr(shape + ".overrideColor", index)
                if rgb:
                    cmds.setAttr(shape + ".overrideRGBColors", 1)
                    cmds.setAttr(shape + ".overrideColorR", rgb[0])
                    cmds.setAttr(shape + ".overrideColorG", rgb[1])
                    cmds.setAttr(shape + ".overrideColorB", rgb[2])

def add_attribute_divider(object_name:str, name:str,divider_bar = "--------"):
    """
    Add Blank Attribute With Divider Head Name

    object_name : name of target object
    name : name of head name
    """

    cmds.addAttr(object_name, ln=name.replace(" ", ""), nn=divider_bar, at="enum", en="{}".format(name), k=1)
    cmds.setAttr(object_name + "." + name, cb=1, l=1)

def add_notes(list_object, notes="unbuild_target"):
    attr_notes = "rig_attributes.delete_target"
    node, attr = attr_notes.split(".")
    if not cmds.objExists(node):
        cmds.group(em=1, n=node, p=grp_still)
        cmds.addAttr(node, ln=attr, dt="string")
        cmds.setAttr(node + ".v", 0)

    for object in list_object:
        old_text = cmds.getAttr(attr_notes)
        if old_text:
            new_text = old_text + object + "."
        else:
            new_text = object + "."

        cmds.setAttr(attr_notes, new_text, typ="string")


def add_option_shape(object, name):
    # create locator
    node_shape = cmds.createNode("nurbsSurface", n=name)
    node_transform = cmds.listRelatives(node_shape, p=1, f=1)[0]

    cmds.setAttr(node_shape + ".v", 0)

    # parent shape to object
    cmds.parent(node_shape, object, s=1, r=1)
    cmds.delete(node_transform)

    # generate class_instance to rename
    object_path = cmds.listRelatives(object, p=1, f=1)[0] if cmds.listRelatives(object, p=1, f=1) else object
    return_path = "{}|{}".format(object, cut(node_shape))

    return return_path


def add_or_create_blend_shape_node(list_target_mesh, node_name="blendshape"):
    def get_base_mesh(blendshape_node):
        original_geom = cmds.listConnections(blendshape_node + '.originalGeometry[0]', source=True, destination=False)

        if original_geom:
            return original_geom[0]
        else:
            raise Exception("Error Blend Shape Node")

    base_mesh = get_base_mesh(node_name)
    # print(base_mesh)

    # create blend shape node method
    if not cmds.objExists(node_name):
        node_name = cmds.blendShape(list_target_mesh, base_mesh, n=node_name, o="local", at=True)

    # add blend shape node method
    elif cmds.objExists(node_name):

        for target in list_target_mesh:
            list_target_name = cmds.blendShape(node_name, q=True, t=True) or []

            # only add when target not added case
            if target not in list_target_name:
                if not cmds.objExists(target):
                    raise Exception("{} Mesh Not Found to Add Blend Shape".format(target))

                index = len(list_target_name)
                cmds.blendShape(node_name, edit=True, target=(base_mesh, index, target, 1.0))

    return node_name


def add_to_set(list_add, set_name=config.all_controller_sets):
    if not cmds.objExists(set_name):
        cmds.sets(n=set_name)

    # for object in list_add:
    cmds.sets(list_add,add=set_name)

def attach_curve(amount, list_curve, size=.5):
    list_return = []
    for curve in list_curve:
        curve_transform = curve
        curve_shape = cmds.listRelatives(
            curve_transform, c=1, s=1, typ="nurbsCurve")[0]

        if "crv_" in curve_transform:
            main_name = curve_transform.replace("crv_", "")
        else:
            main_name = curve_transform

        for i in range(amount):
            locator = cmds.spaceLocator(
                n="loc_" + main_name + "_" + str(i + 1).zfill(2))[0]
            node = cmds.shadingNode(
                "pointOnCurveInfo", au=1, n="poc_" + main_name + "_" + str(i + 1).zfill(2))

            if amount == 1:
                param = 0.5
            else:
                param = i * (1 / (amount - 1))

            list_return.append(locator)

    return list_return

def remove_bck_members(set_name=config.all_controller_sets):
    if cmds.objExists(set_name) and cmds.objectType(set_name) == 'objectSet':
        members = cmds.sets(set_name, q=True) or []
        bck_members = [obj for obj in members if obj.endswith("_bck")]

        if bck_members:
            cmds.sets(bck_members, remove=set_name)



def backup_control(typ="update", grp_backup=config.grp_controller_backup):
    def backup_update():
        """Create backup transform"""

        remove_bck_members()

        # Get all transform nodes in the scene
        if not cmds.objExists(config.all_controller_sets):
            return

        list_control = cmds.sets(config.all_controller_sets, q=True)
        list_control_backup = []

        # create backup group
        if not cmds.objExists(grp_backup):
            cmds.group(em=1, n=grp_backup)
            cmds.setAttr(grp_backup + ".v", 0)
            cmds.setAttr(grp_backup + ".hiddenInOutliner", 1)

        # add shape to transforms
        for control in list_control:
            if cmds.objectType(control, isa="transform"):
                ctrl_backup = "{}_bck".format(control)
                list_control_backup.append(ctrl_backup)

                # clear old backup control in transform if exist
                if cmds.objExists(ctrl_backup):
                    cmds.delete(ctrl_backup)

                # create backup
                cmds.duplicate(control, n=ctrl_backup)
                cmds.parent(ctrl_backup, grp_backup)

                # delete duplicate child
                list_duplicate_child = cmds.listRelatives(ctrl_backup, c=1, f=1)
                if list_duplicate_child:
                    for child in list_duplicate_child:
                        if not cmds.objectType(child, i="nurbsCurve"):
                            cmds.delete(child)

        remove_bck_members()

    def backup_delete():
        if cmds.objExists(grp_backup):
            list_child = cmds.listRelatives(grp_backup, c=1)
            cmds.delete(list_child)

    def backup_recall():
        list_child_backup = None
        if cmds.objExists(grp_backup):
            list_child_backup = cmds.listRelatives(grp_backup, c=1)

        if list_child_backup:
            for ctrl_backup in list_child_backup:
                ctrl_target = ctrl_backup.replace("_bck", "")

                if cmds.objExists(ctrl_target):
                    # clear shape in control target
                    list_clear_shape = cmds.listRelatives(ctrl_target, c=1, s=1, f=1, typ="nurbsCurve")

                    if list_clear_shape:
                        for shape in list_clear_shape:
                            cmds.delete(shape)

                    # duplicate control backup and parent shape to control target
                    ctrl_tmp = cmds.duplicate(ctrl_backup)
                    ctrl_tmp_shape = cmds.listRelatives(ctrl_tmp, c=1, s=1, f=1,typ="nurbsCurve")

                    if ctrl_tmp_shape:
                        for shape in ctrl_tmp_shape:
                            cmds.parent(shape, ctrl_target, s=1, r=1)
                        cmds.delete(ctrl_tmp)

                    # rename proper
                    list_shape = cmds.listRelatives(ctrl_target, c=1, s=1, typ="nurbsCurve", f=1)
                    if list_shape:
                        for i, shape in enumerate(list_shape):
                            cmds.rename(shape, "{}Shape".format(cut(ctrl_target)))

    if typ == "update":
        backup_update()

    elif typ == "recall":
        backup_recall()

    elif typ == "delete":
        backup_delete()

def break_connection(obj_name, rot=False, pos=False, scl=False):
    def break_each_attr(plug):
        if cmds.connectionInfo(plug, isDestination=True):
            plug = cmds.connectionInfo(plug, getExactDestination=True)
            readOnly = cmds.ls(plug, ro=True)
            # delete -icn doesn't work if destination attr is readOnly
            if readOnly:
                source = cmds.connectionInfo(plug, sourceFromDestination=True)
                cmds.disconnectAttr(source, plug)
            else:
                cmds.delete(plug, icn=True)
    """
    Breaks input connections to specified attributes of an object.

    Parameters:
        obj_name (str): Name of the object.
        rot (bool): If True, disconnects rotate attributes (rotateX, rotateY, rotateZ).
        pos (bool): If True, disconnects translate attributes (translateX, translateY, translateZ).
        scl (bool): If True, disconnects scale attributes (scaleX, scaleY, scaleZ).
    """
    list_axis = []

    if rot:
        list_axis += ["rx", "ry", "rz"]
    if pos:
        list_axis += ["tx", "ty", "tz"]
    if scl:
        list_axis += ["sx", "sy", "sz"]


    for axis in list_axis:
        attr = "{}.{}".format(obj_name,axis)

        # code_text = "CBdeleteConnection \"{}\";".format(attr)
        # mel.eval(code_text)

        break_each_attr(attr)

def check_neg(input):
    list_input = []

    if type(input) is list:
        list_input = input
    elif type(input) is str:
        list_input.append(input)
    else:
        raise Exception("Invalid Input")

    for item in list_input:
        if "-" in item:
            raise Exception("Must Be Absolute Axis , {}".format(item))


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())


def cname(tag_name=None, name=None, type=None, position=None):
    if tag_name is None:
        new_name = "{}_{}".format(name, type)
    else:
        new_name = "{}_{}_{}".format(tag_name,name,type)

    return new_name

def connect(object, target, typ="all", translate_multiplier=1, rotate_multiplier=1, name="connect"):
    def connect_translate():
        if translate_multiplier != 1:
            connect_attr_conversion_three(list_input1=[object + ".tx", object + ".ty", object + ".tz"],
                                          list_conversion=[translate_multiplier, translate_multiplier, translate_multiplier],
                                          list_output=[target + ".tx", target + ".ty", target + ".tz"],
                                          name=name)

        else:
            cmds.connectAttr(object + ".t", target + ".t")

    def connect_rotate():
        if rotate_multiplier != 1:
            connect_attr_conversion_three(list_input1=[object + ".rx", object + ".ry", object + ".rz"],
                                          list_conversion=[rotate_multiplier, rotate_multiplier, rotate_multiplier],
                                          list_output=[target + ".rx", target + ".ry", target + ".rz"],
                                          name=name)

        else:
            cmds.connectAttr(object + ".r", target + ".r")

    # optional : connect
    if typ == "translate":
        connect_translate()
    elif typ == "rotate":
        connect_rotate()

    elif typ == "scale":
        cmds.connectAttr(object + ".s", target + ".s")

    elif typ == "all":
        connect_translate()

        connect_rotate()
        cmds.connectAttr(object + ".s", target + ".s")

def connect_attr_conversion(input1, input2=None, output=None, conversion=-1, name="multDoubleLinear"):
    node = cmds.createNode("multDoubleLinear", n=cname(name,"conversion","mdl"))
    cmds.connectAttr(input1, node + ".input1")

    if input2:
        cmds.connectAttr(input2, node + ".input2")
    else:
        cmds.setAttr(node + ".input2", conversion)

    if output:
        cmds.connectAttr(node + ".output", output)

    return node + ".output"


def connect_attr_conversion_three(list_input1=[], list_input2=None, list_output=None, list_conversion=[1, 1, 1], name="conversion"):
    node = cmds.createNode("multiplyDivide", n="{}_conversion_md".format(name))

    list_input_1_name = [".input1X", ".input1Y", ".input1Z"]
    list_output_name = [".outputX", ".outputY", ".outputZ"]

    for i, input in enumerate(list_input1):
        cmds.connectAttr(input, node + list_input_1_name[i])

    if list_input2:
        cmds.connectAttr(list_input2[0], node + ".input2X")
        cmds.connectAttr(list_input2[1], node + ".input2X")
        cmds.connectAttr(list_input2[2], node + ".input2X")
    else:
        cmds.setAttr(node + ".input2X", list_conversion[0])
        cmds.setAttr(node + ".input2Y", list_conversion[1])
        cmds.setAttr(node + ".input2Z", list_conversion[2])

    # connect to output
    for i, output_attribute in enumerate(list_output):
        cmds.connectAttr(node + list_output_name[i], output_attribute)


def connect_matching_attributes(source, target, unit_conversion=None):
    if not cmds.objExists(source) or not cmds.objExists(target):
        return

    source_attrs = cmds.listAttr(source, keyable=True, unlocked=True) or []
    target_attrs = cmds.listAttr(target, keyable=True, unlocked=True) or []
    matching_attrs = set(source_attrs) & set(target_attrs)

    for attr in matching_attrs:
        source_attr = f"{source}.{attr}"
        target_attr = f"{target}.{attr}"

        if cmds.getAttr(source_attr, type=True) in ['double', 'float'] and unit_conversion:
            mult_node = cmds.createNode('multiplyDivide', name=f"{source}_{attr}_convert")
            cmds.setAttr(f"{mult_node}.input2X", unit_conversion)
            cmds.connectAttr(source_attr, f"{mult_node}.input1X", force=True)
            source_attr = f"{mult_node}.outputX"

        if not cmds.isConnected(source_attr, target_attr):
            cmds.connectAttr(source_attr, target_attr, force=True)

def connect_unit_conversion(input, output, factor, name="unitConversion"):
    node = cmds.createNode("unitConversion", n=name)
    cmds.connectAttr(input, node + ".input")
    cmds.connectAttr(node + ".output", output)
    cmds.setAttr(node + ".conversionFactor",factor)




def convert_single_axis_enum(index):
    return ["x","y","z","-x","-y","-z"][index]

def convert_single_axis_enum_pos(index):
    return ["x","y","z"][index]

def convert_triple_axis_enum(index):
    return ["xyz","xzy","yxz","yzx","zyx","zxy"][index]

def copy_shape(source,target):
    source_vtxs = cmds.ls(f'{source}.vtx[*]', fl=True)
    target_vtx = cmds.ls(f'{target}.vtx[*]', fl=True)

    if len(source_vtxs) != len(target_vtx):
        raise ValueError("Two Models have different vertex counts.")

    for i, source_vtx in enumerate(source_vtxs):
        source_pos = cmds.pointPosition(source_vtx, local=True)
        target_pos = cmds.pointPosition(target_vtx[i], local=True)

        if source_pos != target_pos:
            cmds.move(source_pos[0], source_pos[1], source_pos[2], target_vtx[i], ls=True)


def create_finger_rig(list_finger_joint,hand_space,axis_pole="y", move_pole_distance=5.0,parent=None,tag_name="finger",mirror_control_scale=False,is_thumb=False):
    def create_finger_ik():
        def create_thumb():
            # create ik handle and pole vector
            ik_handle = cmds.ikHandle(sj=list_chain_ik[0], ee=list_chain_ik[2], sol="ikRPsolver")[0]
            cmds.parent(ik_handle, list_finger_control[2])

            cmds.setAttr("{}.t{}".format(list_finger_control[1], axis_pole), move_pole_distance)
            freeze_group_classic(list_finger_control[1], "grpOff")

            cmds.poleVectorConstraint(list_finger_control[1], ik_handle)

            cmds.pointConstraint(list_finger_control[0], list_chain_ik[0])

            # add blend space option
            cmds.addAttr(list_finger_control[2], ln="world", k=1, min=0, max=1)
            attr_world = "{}.world".format(list_finger_control[2])

            create_float_space(list_space=[config.loc_root, hand_space],
                               target=list_finger_control[2],
                               attr_float=attr_world,
                               typ="parent")

            # constraint auto pole
            cmds.pointConstraint(list_finger_control[0], list_finger_control[2], cmds.listRelatives(list_finger_control[1], p=1)[0], mo=1)

        def create_finger():
            cmds.addAttr(list_finger_control[3], ln="lockFingerTip", k=1, min=0, max=1)
            attr_lock = "{}.lockFingerTip".format(list_finger_control[3])

            list_no_lock_chain =  ["{}_NoLock".format(joint) for joint in list_finger_joint ]
            list_lock_chain =  ["{}_Lock".format(joint) for joint in list_finger_joint ]

            duplicate_joints(list_append_keyword=["NoLock","Lock"])
            create_switch_systems(list_lock_chain,
                                  list_no_lock_chain,
                                  list_chain_ik,
                                  attr_switch=attr_lock,
                                  )

            # Lock Case -----------------------------------
            # create ik handle and pole vector
            ik_handle = cmds.ikHandle(sj=list_lock_chain[0], ee=list_lock_chain[2], sol="ikRPsolver")[0]
            cmds.parent(ik_handle, list_finger_control[2])

            cmds.setAttr("{}.t{}".format(list_finger_control[1], axis_pole), move_pole_distance)

            cmds.poleVectorConstraint(list_finger_control[1], ik_handle)

            cmds.pointConstraint(list_finger_control[0], list_lock_chain[0])

            # No Lock Case ------------------------------------------
            # create ik handle and pole vector
            ik_handle = cmds.ikHandle(sj=list_no_lock_chain[0], ee=list_no_lock_chain[3], sol="ikRPsolver")[0]
            cmds.parent(ik_handle, list_finger_control[2])

            cmds.setAttr("{}.t{}".format(list_finger_control[1], axis_pole), move_pole_distance)

            cmds.poleVectorConstraint(list_finger_control[1], ik_handle)

            cmds.pointConstraint(list_finger_control[0], list_no_lock_chain[0])

            # constraint auto pole
            cmds.pointConstraint(list_finger_control[0], list_finger_control[3], cmds.listRelatives(list_finger_control[1], p=1)[0], mo=1)

            # parent chain -------------------------------
            cmds.parent(list_finger_control[2], list_finger_control[3])

            # constraint auto pole -------------------------------------
            freeze_group_classic(list_finger_control[1], "grpOff")
            cmds.pointConstraint(list_finger_control[0], list_finger_control[3], cmds.listRelatives(list_finger_control[1], p=1)[0], mo=1)

            cmds.orientConstraint(list_finger_control[2], list_lock_chain[2])

            # add blend space option ------------------------
            cmds.addAttr(list_finger_control[3], ln="world", k=1, min=0, max=1)
            attr_world = "{}.world".format(list_finger_control[3])

            create_float_space(list_space=[config.loc_root, hand_space],
                               target=list_finger_control[3],
                               attr_float=attr_world,
                               typ="parent",
                               tag_name=tag_name)

            # connect lock finger tip
            cmds.connectAttr(attr_lock,"{}.v".format(list_finger_control[2]))

        if is_thumb:
            len_fix = 3
        else:
            len_fix = 4

        if len(list_finger_joint) != len_fix:
            cmds.confirmDialog(m="Error to create finger ik, Input must be {} joints , get {} joint : {}".format(len_fix,len(list_finger_joint), list_finger_joint))

            raise Exception()

        # create ik control
        list_finger_control = ["{}_{}".format(joint, ctrl) for joint in list_chain_ik]

        for i in range(len_fix):
            control_name = list_finger_control[i]
            joint_name = list_chain_ik[i]

            create_control(name=control_name,
                           match=joint_name,
                           freeze_group=True,
                           parent=grp_ik_control,
                           display_rotate_order=False,
                           size=0.5,
                           color="purple")

        if is_thumb:
            create_thumb()
        else:
            create_finger()

        # make finalize
        for control in list_finger_control:
            lock_attributes(control, r=1, s=1, v=1, l=1, k=0)

        if is_thumb:
            lock_attributes(list_finger_control[-1], r=1, l=0, k=1)

        else:
            lock_attributes(list_finger_control[-1], r=1, l=0, k=1)
            lock_attributes(list_finger_control[-2], r=1, l=0, k=1)


    def create_fingers_fk():
        # fk function
        recent_control = None

        for i in range(len(list_chain_fk)):
            if i == len(list_chain_fk)-1:
                continue

            joint_name = list_chain_fk[i]
            control_name = "{}_fk_{}".format(list_chain_fk[i], ctrl)

            create_control(name=control_name,
                                 match=joint_name,
                                 display_rotate_order=False,
                                 freeze_group=True,
                                 mirror_freeze_group=mirror_control_scale,
                                 constraint="parent",
                           size=0.5,
                           color="red")

            grp_offset = cmds.listRelatives(control_name, p=1)[0]

            # chain in hierarchy
            if recent_control:
                cmds.parent(grp_offset, recent_control)
            else:
                cmds.parent(grp_offset, grp_fk_control)

            recent_control = control_name

            lock_attributes(control_name, t=1, r=0, s=1, v=1, k=0, l=1)

    def duplicate_joints(list_append_keyword = ["Fk","Ik"]):
        list_return = []
        # duplicate joints to fk group and ik group (include it's parent)
        for i, typ in enumerate(list_append_keyword):
            # change group
            list_return_each = []
            parent_path = cmds.group(em=1, p=grp_finger_rig, n="{}_{}_joint_{}".format(tag_name,typ, grp))

            recent = None

            # parent offset joint
            parent_joint = cmds.listRelatives(list_finger_joint[0], p=1, f=1)

            if parent_joint:
                tmp = cmds.duplicate(parent_joint[0], n="{}_Root{}".format(cut(parent_joint[0]),typ), po=1)[0]
                cmds.parent(tmp, parent_path)
                cmds.parentConstraint(parent_joint[0], tmp)
                recent = tmp

            # limb joint
            for joint in list_finger_joint:
                tmp = cmds.duplicate(joint, n="{}_{}".format(cut(joint),typ), po=1)[0]
                cmds.parent(tmp, parent_path) if recent is None else cmds.parent(tmp, recent)
                recent = tmp

                list_return_each.append(tmp)

            list_return.append(list_return_each)
    def create_switch_systems(list_object1,list_object2,list_object_result,attr_switch,grp_object1_control=None,grp_object2_control=None):
        # create switch systems , use blendColor Node
        node_reverse = cmds.createNode("reverse", n= cname(tag_name,"switch","rev"))
        cmds.connectAttr(attr_switch, "{}.inputX".format(node_reverse))

        for i, joint in enumerate(list_object_result):
            for data in [["t", "Pos"], ["r", "Rot"]]:
                attr = data[0]
                keyword = data[1]

                node_blend = cmds.createNode("blendColors", n="{}_blend{}{}_blc".format(tag_name, joint, keyword))
                cmds.connectAttr(attr_switch, "{}.blender".format(node_blend))
                cmds.connectAttr("{}.{}".format(list_object1[i], attr), "{}.color1".format(node_blend))
                cmds.connectAttr("{}.{}".format(list_object2[i], attr), "{}.color2".format(node_blend))
                cmds.connectAttr("{}.output".format(node_blend), "{}.{}".format(joint, attr))

        # connect visibility
        if grp_object1_control:
            cmds.connectAttr("{}.inputX".format(node_reverse), "{}.v".format(grp_object1_control))
        if grp_object2_control:
            cmds.connectAttr("{}.outputX".format(node_reverse), "{}.v".format(grp_object2_control))

    def create_finger_main_control():
        create_control(name=ctrl_main,
                       parent=grp_finger_rig,
                       freeze_group=True,
                       display_rotate_order=False,
                       color="yellow",
                       size=0.6)

        cmds.parentConstraint(list_finger_joint[0],ctrl_main)
        cmds.addAttr(ctrl_main,ln="FkIk",k=1,min=0,max=1)


    grp_finger_rig = cmds.group(em=1,n="{}_rig_{}".format(tag_name,grp))

    grp_fk_control = cmds.group(em=1,p=grp_finger_rig,n="{}_fk_control_{}".format(tag_name,grp))
    grp_ik_control = cmds.group(em=1,p=grp_finger_rig,n="{}_ik_control_{}".format(tag_name,grp))

    list_chain_ik = [ "{}_Ik".format(joint) for joint in list_finger_joint ]
    list_chain_fk = [ "{}_Fk".format(joint) for joint in list_finger_joint ]

    ctrl_main = "{}_main_{}".format(tag_name,ctrl)
    attr_switch = "{}.FkIk".format(ctrl_main)

    if parent:
        cmds.parent(grp_finger_rig,parent)

    create_finger_main_control()

    # blend joint for fk / ik
    duplicate_joints(list_append_keyword=["Fk","Ik"])
    create_switch_systems(list_chain_ik,
                          list_chain_fk,
                          list_finger_joint,
                          attr_switch=attr_switch,
                          grp_object1_control=grp_ik_control,
                          grp_object2_control=grp_fk_control)

    create_fingers_fk()
    create_finger_ik()

    lock_attributes(ctrl_main, t=1, r=1, s=1, v=1, k=0, l=1)


def create_control(
        name,
        axis='y',
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
        custom_freeze_group_name=grp):

    '''
    This function create controller
    '''

    dict_normal_vector = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}

    # create control
    if cmds.objExists(name):
        raise Exception("node_name : {} is already exist in scene".format(name))

    # defalut shape
    cmds.circle(ch=False, n=name, nr=dict_normal_vector[del_neg(axis)])

    # add attribute rotate order
    if display_rotate_order:
        cmds.setAttr("{}.rotateOrder".format(name), cb=1)
        cmds.setAttr("{}.rotateOrder".format(name), k=1)

    if connect_rotate_order and constraint:
        cmds.connectAttr("{}.rotateOrder".format(name),"{}.rotateOrder".format(match))

    # guide ball case
    if guide_ball:
        cmds.matchTransform(name, guide_ball, scl=1)

    # customize shape and color
    if shape == "cube":
        clone_shape([name,"ThreeD_Cube"])
    elif shape == "sphere":
        clone_shape([name,"ThreeD_Sphere"])
    else:
        raise Exception("Invalid Input Shape")

    if color == "red":
        set_curve_color(list_target=[name],
                        rgb=[1,0,0])
    elif color == "blue":
        set_curve_color(list_target=[name],
                        rgb=[0,0,1])
    elif color == "green":
        set_curve_color(list_target=[name],
                        rgb=[0,1,0])
    elif color == "yellow":
        set_curve_color(list_target=[name],
                        rgb=[1,1,0])
    elif color == "purple":
        set_curve_color(list_target=[name],
                        rgb=[1,0,1])
    elif color == "aqua":
        set_curve_color(list_target=[name],
                        rgb=[0,1,1])
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
        grp_frz = freeze_group_classic(name,custom_freeze_group_name)[0]

        # optional : mirror scale
        if mirror_freeze_group:
            cmds.setAttr("{}.s".format(grp_frz), -1, -1, -1, typ="double3")
            print("Freeze")
    # optional : parent to given
    if parent is not None:
        if freeze_group:
            cmds.parent(grp_frz, parent)
        else:
            cmds.parent(name,parent)

    # optional : connect to match
    if connect_match:
        connect(name,match,typ="all")

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


def create_corrective_joint(block1,
                            block2,
                            joint_push,
                            axis_push,
                            axis_forward,
                            axis_side,
                            new_min_max = [0,5],
                            old_min_max = [0,120],
                            invert_angle=False,
                            parent=None,
                            tag_name="name"):
    """
    Create Corrective Push Joint for wrist

    """

    def create_dummy_output():
        matchAllTransform(locator_dummy,joint_push)
        # cmds.parent(locator_dummy,grp_corrective_joint)
        grp_frz = freeze_group_classic(locator_dummy)[0]

        cmds.parentConstraint(locator_dummy,joint_push)

    def parent_by_matrix(locator,target):
        node_mult_matrix=  cmds.createNode("multMatrix")
        cmds.connectAttr("{}.worldMatrix[0]".format(target),"{}.inMatrix[0]".format(node_mult_matrix))
        cmds.connectAttr("{}.parentInverseMatrix[0]".format(locator),"{}.inMatrix[1]".format(node_mult_matrix))

        node_decomp_matrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr("{}.outMatrix".format(node_mult_matrix),"{}.inMatrix".format(node_decomp_matrix))
        cmds.connectAttr("{}.outTranslate".format(node_decomp_matrix),"{}.translate".format(locator))

    def create_vector_position():
        grp_loc1 = freeze_group_classic(locator_1)[0]
        grp_loc2 = freeze_group_classic(locator_2)[0]
        grp_zero = freeze_group_classic(locator_zero)[0]

        # position vector zero
        cmds.parentConstraint(block2,grp_zero)

        # position vector 1
        constraint =  cmds.parentConstraint(block2,grp_loc1)
        cmds.delete(constraint)
        cmds.parentConstraint(block1,grp_loc1,mo=1)

        cmds.setAttr("{}.t{}".format(locator_1,axis_forward_abs),-1) #move

        # position vector 2
        cmds.parentConstraint(block2,grp_loc2)
        cmds.setAttr("{}.t{}".format(locator_2,axis_forward_abs),1) # move
        grp_rot = freeze_group_classic(locator_2,"grpRot",match_object=locator_zero)[0] # rotate for make 120

        if invert_angle:
            cmds.setAttr("{}.r{}".format(grp_rot,axis_side_abs),-60)
        else:
            cmds.setAttr("{}.r{}".format(grp_rot,axis_side_abs),60)



    def create_angle_between():
        # create vector 1
        node_pma_vector1 = cmds.createNode("plusMinusAverage", n=cname(tag_name, "vector1", "pma"))
        cmds.setAttr("{}.operation".format(node_pma_vector1), 2)
        cmds.connectAttr("{}.worldPosition".format(cmds.listRelatives(locator_1, c=1, s=1)[0]), "{}.input3D[0]".format(node_pma_vector1))
        cmds.connectAttr("{}.worldPosition".format(cmds.listRelatives(locator_zero, c=1, s=1)[0]), "{}.input3D[1]".format(node_pma_vector1))
        attr_vector1 = "{}.output3D".format(node_pma_vector1)

        # create vector 2
        node_pma_vector2 = cmds.createNode("plusMinusAverage", n=cname(tag_name, "vector2", "pma"))
        cmds.setAttr("{}.operation".format(node_pma_vector2), 2)
        cmds.connectAttr("{}.worldPosition".format(cmds.listRelatives(locator_2, c=1, s=1)[0]), "{}.input3D[0]".format(node_pma_vector2))
        cmds.connectAttr("{}.worldPosition".format(cmds.listRelatives(locator_zero, c=1, s=1)[0]), "{}.input3D[1]".format(node_pma_vector2))
        attr_vector2 = "{}.output3D".format(node_pma_vector2)

        # invert vector
        # if invert_angle:
        node_md_invert = cmds.createNode("multiplyDivide", n=cname(tag_name, "invertVector", "md"))
        cmds.connectAttr(attr_vector1, "{}.input1".format(node_md_invert))
        cmds.setAttr("{}.input2".format(node_md_invert), -1, -1, -1, typ="double3")
        attr_vector1 = "{}.output".format(node_md_invert)

        # angle between
        node_angle_between = cmds.createNode("angleBetween", n=cname(tag_name, "anglePush", "ab"))
        cmds.connectAttr(attr_vector1, "{}.vector1".format(node_angle_between))
        cmds.connectAttr(attr_vector2, "{}.vector2".format(node_angle_between))

        # set range
        new_min, new_max = new_min_max
        # old_min,old_max = old_min_max

        node_set_range = cmds.createNode("setRange", n=cname(tag_name, "remap", "sr"))
        cmds.connectAttr("{}.angle".format(node_angle_between), "{}.valueX".format(node_set_range))
        cmds.setAttr("{}.minX".format(node_set_range), new_min)
        cmds.setAttr("{}.maxX".format(node_set_range), new_max)

        # if invert_angle:
        cmds.setAttr("{}.oldMinX".format(node_set_range), 60)
        cmds.setAttr("{}.oldMaxX".format(node_set_range), 180)
        # else:
        #     cmds.setAttr("{}.oldMinX".format(node_set_range),0)
        #     cmds.setAttr("{}.oldMaxX".format(node_set_range),120)

        # connect to output
        cmds.connectAttr("{}.outValueX".format(node_set_range), "{}.t{}".format(locator_dummy, axis_push))


    def create_hierarchy():
        def create_position_output():
            node_decompose_output =cmds.createNode("decomposeMatrix",n=cname(tag_name,"MatchTransform","dcm"))
            cmds.connectAttr("{}.worldMatrix[0]".format(block2),"{}.inputMatrix".format(node_decompose_output))
            cmds.connectAttr("{}.outputTranslate".format(node_decompose_output),"{}.translate".format(grp_base_orient))
            cmds.connectAttr("{}.outputRotate".format(node_decompose_output),"{}.rotate".format(grp_base_orient))
            cmds.connectAttr("{}.outputScale".format(node_decompose_output),"{}.scale".format(grp_base_orient))

        def create_avg_orient_output():
            node_decompose_block1 = cmds.createNode("decomposeMatrix",n=cname(tag_name,"{}Rotate".format(block1),"dcm"))
            cmds.connectAttr("{}.worldMatrix[0]".format(block1),"{}.inputMatrix".format(node_decompose_block1))

            node_decompose_block2 = cmds.createNode("decomposeMatrix",n=cname(tag_name,"{}Rotate".format(block2),"dcm"))
            cmds.connectAttr("{}.worldMatrix[0]".format(block2),"{}.inputMatrix".format(node_decompose_block2))

            node_pair_blend = cmds.createNode("pairBlend",n=cname(tag_name,"AvgRotate","pb"))
            cmds.setAttr("{}.rotInterpolation".format(node_pair_blend),1)
            cmds.setAttr("{}.weight".format(node_pair_blend),0.5)
            cmds.connectAttr("{}.outputRotate".format(node_decompose_block1),"{}.inRotate1".format(node_pair_blend))
            cmds.connectAttr("{}.outputRotate".format(node_decompose_block2),"{}.inRotate2".format(node_pair_blend))

            node_compose_matrix = cmds.createNode("composeMatrix",n=cname(tag_name,"AvgRotate","cm"))
            cmds.connectAttr("{}.outRotate".format(node_pair_blend),"{}.inputRotate".format(node_compose_matrix))

            node_mult_matrix = cmds.createNode("multMatrix",n=cname(tag_name,"offsetMatrix","mm"))
            cmds.connectAttr("{}.outputMatrix".format(node_compose_matrix),"{}.matrixIn[0]".format(node_mult_matrix))
            cmds.connectAttr("{}.parentInverseMatrix".format(grp_avg_orient),"{}.matrixIn[1]".format(node_mult_matrix))

            node_decompose_output =cmds.createNode("decomposeMatrix",n=cname(tag_name,"OutputAvgRotate","dcm"))
            cmds.connectAttr("{}.matrixSum".format(node_mult_matrix),"{}.inputMatrix".format(node_decompose_output))
            cmds.connectAttr("{}.outputRotate".format(node_decompose_output),"{}.rotate".format(grp_avg_orient))


        cmds.group(em=1, n=grp_corrective_joint)
        cmds.setAttr("{}.inheritsTransform".format(grp_corrective_joint),False)

        cmds.group(em=1, n=grp_base_orient,p=grp_corrective_joint)
        cmds.group(em=1, n=grp_avg_orient,p=grp_base_orient)

        cmds.parent(grp_corrective_joint, parent) if parent else None

        cmds.spaceLocator(n=locator_1)
        cmds.spaceLocator(n=locator_2)
        cmds.spaceLocator(n=locator_zero)
        cmds.spaceLocator(n=locator_dummy)

        cmds.parent(locator_dummy,grp_avg_orient)
        cmds.parent(locator_zero, locator_1, locator_2,grp_corrective_joint)

        create_position_output()
        create_avg_orient_output()


    # variables
    grp_corrective_joint = cname(tag_name, "Corrective", grp)
    grp_base_orient = cname(tag_name, "BaseOrient", grp)
    grp_avg_orient = cname(tag_name, "AvgOrient", grp)

    locator_dummy = cname(tag_name,"dummy",loc)
    locator_1 = cname(tag_name,"pos1",loc)
    locator_2 = cname(tag_name,"pos2",loc)
    locator_zero = cname(tag_name,"posZro",loc)

    axis_forward_abs = del_neg(axis_forward)
    axis_side_abs = del_neg(axis_side)

    # build
    create_hierarchy()

    create_dummy_output()
    create_vector_position()

    create_angle_between()

def create_enum_space_classic(object_attr, list_space, list_nice_name, target, type="parent"):
    def key_target(index):
        # set current enum attr
        cmds.setAttr(attr_path, index)

        # set all weight to zero, except the target one
        for i, weight_name in enumerate(list_weight):
            if i == index:
                cmds.setAttr("{}.{}".format(constraint_name, weight_name), 1)
            else:
                cmds.setAttr("{}.{}".format(constraint_name, weight_name), 0)

            # set key
            cmds.setDrivenKeyframe("{}.{}".format(constraint_name, list_weight[i]), cd=attr_path)

    def create_space_locator():
        for i, obj in enumerate(list_space):
            # create space local group and connect matrix
            grp_space_local = cmds.group(em=1, n="{}_{}Space_grp".format(list_nice_name[i], target), p=grp_space_still)
            cmds.connectAttr("{}.worldMatrix[0]".format(obj), "{}.offsetParentMatrix".format(grp_space_local))

            # create offset transform group
            grp_space_offset = cmds.group(em=1, n="{}_{}SpaceOff_grp".format(list_nice_name[i], target), p=grp_space_local)
            loc_space = cmds.group(n="{}_{}Space_loc".format(list_nice_name[i], target), em=1, p=grp_space_offset)
            # loc_space = cmds.spaceLocator(n="{}_{}Space_loc".format(list_nice_name[i], target))[0]

            # snap grp offset to target
            constraint = cmds.parentConstraint(target, grp_space_offset)
            cmds.delete(constraint)

            list_space_locator.append(loc_space)

    def create_constraint_node():
        # create constraint node
        constraint_name = list_weight = None

        grp_offset_target = freeze_group_classic(target, "grpBlend")[0]
        maintain_offset = 0

        if type == "parent":
            constraint_name = cmds.parentConstraint(list_space_locator, grp_offset_target, mo=maintain_offset)[0]
            list_weight = (cmds.parentConstraint(constraint_name, q=1, wal=1))
        elif type == "point":
            constraint_name = cmds.pointConstraint(list_space_locator, grp_offset_target, mo=maintain_offset)[0]
            list_weight = (cmds.pointConstraint(constraint_name, q=1, wal=1))
        elif type == "orient":
            constraint_name = cmds.orientConstraint(list_space_locator, grp_offset_target, mo=maintain_offset)[0]
            list_weight = (cmds.orientConstraint(constraint_name, q=1, wal=1))
        else:
            raise Exception("Input Constraint Type is Invalid")

        return constraint_name, list_weight

    # error handling
    if len(list_nice_name) != len(list_space):
        raise Exception("Invalid Input Space and Nice Name")

    if not list_nice_name or not list_space:
        raise Exception("Invalid Input,Get {},{}".format(list_space,list_nice_name))

    # variables
    grp_space_still = cmds.group(em=1, n="{}_spaceStill_grp".format(target))
    cmds.setAttr("{}.inheritsTransform".format(grp_space_still), 0)

    cmds.addAttr(object_attr, ln="space", at="enum", en=":".join(list_nice_name), k=1)

    list_space_locator = []
    attr_path = "{}.space".format(object_attr)
    cmds.setAttr(attr_path, 0)

    # create space locator
    create_space_locator()

    constraint_name, list_weight = create_constraint_node()

    # set driven key to all weight
    for i in range(len(list_space)):
        key_target(i)

    # set attribute
    cmds.setAttr(attr_path,0)

    return grp_space_still


def create_enum_space_matrix(list_space, list_nice_name, target, object_attr, at="enum", pick=None):
    if len(list_space) != 2 and at == "float":
        raise Exception("list space must have two member : get {}".format(list_space))

    list_output_group = []
    list_locator = []
    grp_blend = freeze_group_classic([target], "grpBlend")[0]

    # create attribute
    if at == "enum":
        cmds.addAttr(object_attr, ln="space", at="enum", en=":".join(list_nice_name), k=1)

    attr_switch = object_attr + ".space"

    # create space groups
    for item in list_space:
        # create
        locator = cmds.spaceLocator(n="{}_{}space{}".format(loc, target, item.capitalize()))[0]
        grp_offset = cmds.group(locator, n="{}_{}space{}".format(grp, target, item.capitalize()))

        # connect world matrix
        cmds.setAttr("{}.inheritsTransform".format(grp_offset), 0)
        cmds.connectAttr("{}.worldMatrix[0]".format(item), "{}.offsetParentMatrix".format(grp_offset))

        # snap locator to target positiion
        cmds.matchTransform(locator, target)

        # append to list
        lock_attributes(grp_offset, t=1, r=1, s=1, l=1, k=0)
        list_output_group.append(grp_offset)
        list_locator.append(locator)

    # pick Matrix
    if pick:
        node_pick_matrix = cmds.createNode("pickMatrix", n="pmx_{}SpaceSwitch".format(target))
        cmds.setAttr(node_pick_matrix + ".useTranslate", 0)
        cmds.setAttr(node_pick_matrix + ".useRotate", 0)
        cmds.setAttr(node_pick_matrix + ".useScale", 0)
        cmds.setAttr(node_pick_matrix + ".useShear", 0)

        for option in pick:
            if option == "translate":
                cmds.setAttr(node_pick_matrix + ".useTranslate", 1)
            elif option == "rotate":
                cmds.setAttr(node_pick_matrix + ".useRotate", 1)
            elif option == "scale":
                cmds.setAttr(node_pick_matrix + ".useScale", 1)
            elif option == "shear":
                cmds.setAttr(node_pick_matrix + ".useShear", 1)

    # create node connection
    node_mult_matrix = cmds.createNode("multMatrix")

    list_parent = cmds.listRelatives(grp_blend, p=1)
    if list_parent:
        cmds.connectAttr("{}.worldInverseMatrix[0]".format(list_parent[0]), "{}.matrixIn[1]".format(node_mult_matrix))

    # create attribute input connection
    if at == "enum":
        node_choice = cmds.createNode("choice")
        cmds.connectAttr(attr_switch, "{}.selector".format(node_choice))
        [cmds.connectAttr("{}.worldMatrix[0]".format(list_locator[i]), "{}.input[{}]".format(node_choice, i)) for i in range(len(list_space))]
        cmds.connectAttr("{}.output".format(node_choice), "{}.matrixIn[0]".format(node_mult_matrix))
    elif at == "float":
        node_blend_matrix = cmds.createNode("blendMatrix")
        cmds.connectAttr(attr_switch, "{}.envelope".format(node_blend_matrix))
        cmds.connectAttr("{}.worldMatrix[0]".format(list_locator[1]), "{}.target[0].targetMatrix".format(node_blend_matrix))
        cmds.connectAttr("{}.worldMatrix[0]".format(list_locator[0]), "{}.inputMatrix".format(node_blend_matrix))
        cmds.connectAttr("{}.outputMatrix".format(node_blend_matrix), "{}.matrixIn[0]".format(node_mult_matrix))

    # apply to target grp blend
    if pick:
        cmds.connectAttr("{}.matrixSum".format(node_mult_matrix), "{}.inputMatrix".format(node_pick_matrix))
        cmds.connectAttr("{}.outputMatrix".format(node_pick_matrix), "{}.offsetParentMatrix".format(grp_blend))
    else:
        cmds.connectAttr("{}.matrixSum".format(node_mult_matrix), "{}.offsetParentMatrix".format(grp_blend))

    return list_output_group


def create_float_space(list_space, target, attr_float, typ="orient",tag_name=None):
    if len(list_space) != 2:
        raise Exception("list space must have two member : get {}".format(list_space))

    node_rev = cmds.createNode("reverse",n=cname(tag_name,"switchSpace","rev"))

    locatorFrz1 = cmds.spaceLocator(n="loc_{}SpaceFrz".format(target))[0]
    locatorFrz2 = cmds.spaceLocator(n="loc_{}SpaceFrz".format(target))[0]

    locator1 = cmds.spaceLocator(n="loc_{}Space".format(target))[0]
    locator2 = cmds.spaceLocator(n="loc_{}Space".format(target))[0]

    # parent connection
    cmds.setAttr(locatorFrz1 + ".inheritsTransform", 0)
    cmds.setAttr(locatorFrz2 + ".inheritsTransform", 0)

    cmds.setAttr(locatorFrz1 + ".v", 0)
    cmds.setAttr(locatorFrz2 + ".v", 0)

    cmds.connectAttr(list_space[0] + ".worldMatrix[0]", locatorFrz1 + ".offsetParentMatrix")
    cmds.connectAttr(list_space[1] + ".worldMatrix[0]", locatorFrz2 + ".offsetParentMatrix")

    cmds.parent(locator1, locatorFrz1)
    cmds.parent(locator2, locatorFrz2)

    cmds.matchTransform(locator1, target)
    cmds.matchTransform(locator2, target)

    grp_blend = freeze_group_classic([target], "grpBlend")[0]

    cmds.parent(locatorFrz1, locatorFrz2, grp_blend)

    # orient constraint
    if typ == "parent":
        cons = cmds.parentConstraint(locator1, locator2, grp_blend)[0]

    elif typ == "orient":
        cons = cmds.orientConstraint(locator1, locator2, grp_blend)[0]

    elif typ == "point":
        cons = cmds.pointConstraint(locator1, locator2, grp_blend)[0]

    else:
        raise Exception("type invalid")

    # reconnect attribute constraint
    cmds.connectAttr(attr_float, "{}.{}W0".format(cons, locator1))

    cmds.connectAttr(attr_float, "{}.inputX".format(node_rev))
    cmds.connectAttr("{}.outputX".format(node_rev), "{}.{}W1".format(cons, locator2))


def create_ik_reverse(control_setting,
                      control_parent_ik,
                      control_parent_fk,
                      axis_foot_three,
                      list_locator_pivot,
                      ball_joint,
                      toe_joint,
                      ankle_joint_ik,
                      parent,
                      list_parent_reverse=[],
                      name_tag = "Foot",
                      invert_toe_twist_value = False,
                      invert_middle_twist_value = False,
                      invert_roll_side_axis= False,
                      invert_side_roll_value = False,
                      invert_heel_twist_value=False,
                      invert_roll_axis=False,
                      invert_roll_value=False,
                      auto_roll_default_value=0):

    def create_ik_function():
        def create_attributes():
            # anim attributes
            add_attribute_divider(control_setting, "IkPivot")

            cmds.addAttr(attr_foot_pitch.split(".")[0], ln=attr_foot_pitch.split(".")[1], at="float", k=1)
            cmds.addAttr(attr_bank.split(".")[0], ln=attr_bank.split(".")[1], at="float", k=1)
            cmds.addAttr(attr_toe_pitch.split(".")[0], ln=attr_toe_pitch.split(".")[1], at="float", k=1)
            cmds.addAttr(attr_heel_twist.split(".")[0], ln=attr_heel_twist.split(".")[1], at="float", k=1)
            cmds.addAttr(attr_toe_twist.split(".")[0], ln=attr_toe_twist.split(".")[1], at="float", k=1)

            # config attributes
            add_attribute_divider(option_shape, name="Ik_config".format(name_tag))
            cmds.addAttr(attr_roll_ball_end.split(".")[0], ln=attr_roll_ball_end.split(".")[1], at="float", k=1, dv=auto_roll_default_value)

        def create_hierarchy():
            # create group hierarchy
            grp_local_reverse = cmds.group(em=1, n="{}_reverse_ik_grp".format(name_tag), p=parent)
            cmds.connectAttr(control_parent_ik+".rotateOrder",grp_local_reverse+".rotateOrder",f=1)
            cmds.parentConstraint(control_parent_ik, grp_local_reverse)

            # break connection
            break_connection(ankle_joint_ik,rot=True)

            # create reversed chain joint
            cmds.select(cl=1)
            for i, joint in enumerate(list_pivot_joint):
                cmds.joint(n=joint)
                cmds.matchTransform(joint, list_pivot_match[i], pos=1)
                cmds.matchTransform(joint, jnt_ball_ik, rot=1)
                cmds.makeIdentity(joint, a=1, s=1, r=1)

            cmds.parent(list_pivot_joint[0], grp_local_reverse)

            # orient constraint piv to ik joint
            loc_ball_orient = cmds.spaceLocator(n="{}_ballOrient_loc".format(name_tag))[0]
            constraint = cmds.parentConstraint(jnt_ball_ik, loc_ball_orient)
            cmds.delete(constraint)
            cmds.parent(loc_ball_orient, piv_outer)
            constraint_toe_orient.append(cmds.orientConstraint(loc_ball_orient, jnt_ball_ik)[0])

            loc_ankle_orient = cmds.spaceLocator(n="{}_ankleOrient_loc".format(name_tag))[0]
            cmds.connectAttr(control_parent_ik+".rotateOrder",loc_ankle_orient+".rotateOrder",f=1)
            constraint = cmds.parentConstraint(jnt_ankle_ik, loc_ankle_orient)
            cmds.delete(constraint)
            cmds.parent(loc_ankle_orient, piv_ball)
            cmds.orientConstraint(loc_ankle_orient, jnt_ankle_ik)


            # parent ankle,pos end to piv
            for object in list_parent_reverse:
                if cmds.objExists(object):
                    break_connection(object,pos=True,rot=True)
                    cmds.parentConstraint(piv_ankle,object,mo=1)



        def create_connection():
            def connect_side_roll():
                if invert_roll_side_axis:
                    first_target = piv_outer
                    second_target = piv_inner
                else:
                    first_target = piv_inner
                    second_target = piv_outer

                if invert_side_roll_value:
                    node_mdl_invert = cmds.createNode("multDoubleLinear", n="{}_rollSide_mdl".format(name_tag))
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(attr_bank, "{}.input1".format(node_mdl_invert))
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_bank

                # Bank
                cmds.setAttr("{}.minRot{}LimitEnable".format(first_target, axis_foot_forward.upper()), 1)
                cmds.setAttr("{}.minRot{}Limit".format(first_target, axis_foot_forward.upper()), 0)

                cmds.setAttr("{}.maxRot{}LimitEnable".format(second_target, axis_foot_forward.upper()), 1)
                cmds.setAttr("{}.maxRot{}Limit".format(second_target, axis_foot_forward.upper()), 0)

                cmds.connectAttr(attr_output, "{}.r{}".format(first_target, axis_foot_forward))
                cmds.connectAttr(attr_output, "{}.r{}".format(second_target, axis_foot_forward))

            def connect_base_twist():
                if invert_heel_twist_value:
                    node_mdl_invert = cmds.createNode("multDoubleLinear", n="{}_baseTwist_mdl".format(name_tag))
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(attr_heel_twist, "{}.input1".format(node_mdl_invert))
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_heel_twist

                cmds.connectAttr(attr_output, "{}.r{}".format(piv_heel_twist, axis_foot_twist))

            def connect_tip_twist():
                if invert_toe_twist_value:
                    node_mdl_invert = cmds.createNode("multDoubleLinear", n="{}_tipTwist_mdl".format(name_tag))
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(attr_toe_twist, "{}.input1".format(node_mdl_invert))
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_toe_twist

                cmds.connectAttr(attr_output, "{}.r{}".format(piv_end, axis_foot_twist))

            def connect_middle_twist():
                if invert_middle_twist_value:
                    node_mdl_invert = cmds.createNode("multDoubleLinear", n="{}_tipTwist_mdl".format(name_tag))
                    cmds.setAttr(node_mdl_invert + ".input2", -1)
                    cmds.connectAttr(attr_toe_pitch, "{}.input1".format(node_mdl_invert))
                    attr_output = "{}.output".format(node_mdl_invert)
                else:
                    attr_output = attr_toe_pitch

                # Toe tap
                node_adl_toe_tap = cmds.createNode("addDoubleLinear", n="{}_tipTwist_adl".format(name_tag))

                cmds.connectAttr("{}.constraintRotate{}".format(constraint_toe_orient[0], axis_foot_side.upper()), "{}.input1".format(node_adl_toe_tap))
                cmds.connectAttr(attr_output, "{}.input2".format(node_adl_toe_tap))

                cmds.connectAttr("{}.output".format(node_adl_toe_tap), "{}.r{}".format(jnt_ball_ik, axis_foot_side), f=1)

            def connect_roll():
                def connect_roll_back():
                    if invert_roll_axis:
                        value_cond_operation = 4
                    else:
                        value_cond_operation = 2

                    # Roll Out
                    node_cond_roll_out = cmds.createNode("condition", n="{}_rollOut_cond".format(name_tag))
                    cmds.setAttr("{}.operation".format(node_cond_roll_out), value_cond_operation)

                    cmds.setAttr("{}.colorIfFalseR".format(node_cond_roll_out), 0)
                    cmds.connectAttr(attr_output, "{}.firstTerm".format(node_cond_roll_out))
                    cmds.connectAttr(attr_output, "{}.colorIfTrueR".format(node_cond_roll_out))

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_out), "{}.r{}".format(piv_heel_roll, axis_foot_side))

                def connect_roll_front():
                    # Roll In --------------------------
                    if invert_roll_axis:
                        value_condition = 4
                    else:
                        value_condition = 2

                    # node roll in
                    node_cond_roll_in = cmds.createNode("condition", n="{}_rollIn_cond".format(name_tag))
                    cmds.setAttr("{}.operation".format(node_cond_roll_in), value_condition)

                    cmds.connectAttr(attr_output, "{}.firstTerm".format(node_cond_roll_in))
                    cmds.setAttr("{}.colorIfTrueR".format(node_cond_roll_in), 0)
                    cmds.connectAttr(attr_output, "{}.colorIfFalseR".format(node_cond_roll_in))

                    # roll ball
                    node_cond_roll_ball = cmds.createNode("condition", n="{}_rollBall_cond".format(name_tag))
                    cmds.setAttr("{}.operation".format(node_cond_roll_ball), value_condition)

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_in), "{}.firstTerm".format(node_cond_roll_ball))
                    cmds.connectAttr(attr_roll_ball_end, "{}.secondTerm".format(node_cond_roll_ball))

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_in), "{}.colorIfTrueR".format(node_cond_roll_ball))
                    cmds.connectAttr(attr_roll_ball_end, "{}.colorIfFalseR".format(node_cond_roll_ball))

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_ball), "{}.r{}".format(piv_ball, axis_foot_side))

                    # roll end
                    node_cond_roll_end = cmds.createNode("condition", n="{}_rollEnd_cond".format(name_tag))
                    cmds.setAttr("{}.operation".format(node_cond_roll_end), value_condition)

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_in), "{}.firstTerm".format(node_cond_roll_end))
                    cmds.connectAttr(attr_roll_ball_end, "{}.secondTerm".format(node_cond_roll_end))

                    node_pma_roll_end_offset = cmds.createNode("plusMinusAverage", n="{}_rollEndOffset_pma".format(name_tag))
                    cmds.setAttr("{}.operation".format(node_pma_roll_end_offset), 2)

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_in), "{}.input1D[0]".format(node_pma_roll_end_offset), )
                    cmds.connectAttr(attr_roll_ball_end, "{}.input1D[1]".format(node_pma_roll_end_offset))
                    cmds.connectAttr("{}.output1D".format(node_pma_roll_end_offset), "{}.colorIfFalseR".format(node_cond_roll_end))

                    cmds.connectAttr("{}.outColorR".format(node_cond_roll_end), "{}.r{}".format(piv_end, axis_foot_side))

                if invert_roll_value:
                    attr_output = connect_attr_conversion(input1=attr_foot_pitch,conversion=-1,name=name_tag)
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
        option_shape = add_option_shape(object=control_setting, name="{}_option".format(name_tag))

        # define all variables
        attr_foot_pitch = control_setting + ".roll"
        attr_bank = control_setting + ".sideRoll"
        attr_heel_twist = control_setting + ".baseTwist"
        attr_toe_twist = control_setting + ".tipTwist"
        attr_toe_pitch = control_setting + ".middleRoll"
        attr_roll_ball_end = option_shape + ".rollBallEnd"

        piv_ankle = "{}_ankle_piv".format(name_tag)
        piv_ball = "{}_ball_piv".format(name_tag)
        piv_outer = "{}_outer_piv".format(name_tag)
        piv_inner = "{}_inner_piv".format(name_tag)
        piv_heel_roll = "{}_heelRoll_piv".format(name_tag)
        piv_end = "{}_end_piv".format(name_tag)
        piv_heel_twist = "{}_heelTwist_piv".format(name_tag)

        match_inner, match_outer, match_heel, match_end = list_locator_pivot

        list_pivot_match = [match_heel, match_end, match_heel, match_inner, match_outer, jnt_ball_ik, jnt_ankle_ik]
        list_pivot_joint = [piv_heel_twist, piv_end, piv_heel_roll, piv_inner, piv_outer, piv_ball, piv_ankle]

        # main operation
        create_attributes()
        create_hierarchy()
        create_connection()

    def create_fk_function():
        # create control ball fk
        create_control(name="{}_{}".format(ctrl, jnt_ball_fk), match=jnt_ball_fk,
                                            parent=control_parent_fk, constraint="parent",freeze_group=True)


    # get pivot of foot
    axis_foot_forward, axis_foot_side, axis_foot_twist = [axis for axis in axis_foot_three]
    loc_inner_piv, loc_outer_piv, loc_heel_piv, loc_end_piv = list_locator_pivot

    jnt_ball_fk, jnt_toe_fk = [joint + "Fk" for joint in [ball_joint,toe_joint]]
    jnt_ball_ik, jnt_toe_ik = [joint + "Ik" for joint in  [ball_joint,toe_joint]]

    create_ik_function()
    create_fk_function()

def create_node_blendshape(curve_lips="crv_main",
                           node_name="bshp_curve",
                           list_input=["joint.tx",
                                       "joint.ty",
                                       "joint.tz",
                                       "joint.tx",
                                       "joint.ty",
                                       "joint.tz"],
                           add=False
                           ):
    list_word = ["PosX", "PosY", "PosZ", "NegX", "NegY", "NegZ"]
    list_all_blendshape = [curve_lips + word for word in list_word]
    list_custom_attr = ["positiveX", "positiveY", "positiveZ", "negativeX", "negativeY", "negativeZ"]
    list_enable_attr = ["envelopePositiveX", "envelopePositiveY", "envelopePositiveZ", "envelopeNegativeX", "envelopeNegativeY", "envelopeNegativeZ"]

    list_axis = ["X", "Y", "Z"]
    list_color = ["R", "G", "B"]

    [cmds.duplicate(curve_lips, n=name) for name in list_all_blendshape]
    [cmds.setAttr(curve + ".v", 0) for curve in list_all_blendshape]

    # create blendshape
    node_bsn = cmds.blendShape(list_all_blendshape, curve_lips, o="local", n=node_name, foc=1)[0]

    [cmds.addAttr(node_bsn, ln=name, at="float", k=1, dv=1) for name in list_custom_attr]
    [cmds.addAttr(node_bsn, ln=name, at="float", k=1, dv=1, min=0, max=1) for name in list_enable_attr]

    # positive case
    for name in ["positive", "negative"]:
        node_md_divide = cmds.createNode("multiplyDivide", n="md_div{}".format(name))
        node_md_invert = cmds.createNode("multiplyDivide", n="md_invert{}".format(name))
        node_md_mult = cmds.createNode("multiplyDivide", n="md_mult{}".format(name))
        node_clamp = cmds.createNode("clamp", n="clp_{}".format(name))
        node_md_enable = cmds.createNode("multiplyDivide", n="md_enable{}".format(name))

        if name is "positive":
            list_attr_custom = list_custom_attr[0:3]
            list_attr_input = list_input[0:3]
            list_attr_weight = list_all_blendshape[0:3]
            list_attr_envelope = list_enable_attr[0:3]

            cmds.setAttr(node_clamp + ".max", 1, 1, 1, typ="double3")
            cmds.setAttr(node_md_invert + ".input2", 1, 1, 1, typ="double3")

        elif name is "negative":
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
        [cmds.connectAttr("{}.{}".format(node_bsn, list_attr_custom[i]), "{}.input1{}".format(node_md_divide, list_axis[i])) for i in range(3)]

        # connect md mult node
        [cmds.connectAttr(list_attr_input[i], "{}.input2{}".format(node_md_mult, list_axis[i])) for i in range(3)]
        cmds.connectAttr("{}.output".format(node_md_divide), "{}.input1".format(node_md_mult))

        # connect clamp node
        [cmds.connectAttr("{}.output{}".format(node_md_mult, list_axis[i]), "{}.input{}".format(node_clamp, list_color[i])) for i in range(3)]

        # fix negative value
        cmds.connectAttr("{}.output".format(node_clamp), "{}.input1".format(node_md_invert))

        # connect md enable node
        cmds.connectAttr("{}.output".format(node_md_invert), "{}.input2".format(node_md_enable))
        [cmds.connectAttr("{}.{}".format(node_bsn, list_attr_envelope[i]), "{}.input1{}".format(node_md_enable, list_axis[i])) for i in range(3)]

        # connect to blendshape weight
        [cmds.connectAttr("{}.output{}".format(node_md_enable, list_axis[i]), "{}.{}".format(node_bsn, list_attr_weight[i])) for i in range(3)]

    return list_all_blendshape




def create_ribbon_rig_v1(anchor_start,
                      anchor_end,
                      parent,
                      axis_forward,
                      axis_pole,
                      list_ribbon_joint,
                      tag_name="leg",
                      enable_auto_twist=True,
                      use_anchor_start_as_twist_driver=True,
                      invert_rotate_twist=False,
                      invert_twist_value=False,
                      freeze_twist_driver=False,
                      attr_detail_ctrl_vis=None,
                      attr_bend_ctrl_vis=None):
    def create_nurbs_plane():
        # create ribbon plane  reference scale from limb joints
        width_up = get_distance_two(loc_start, loc_end)

        cmds.nurbsPlane(w=width_up, lr=0.05, u=4, v=1, d=3, ax=(0, 0, 1), ch=0, n=nrb_ribbon)
        cmds.parent(nrb_ribbon,grp_ribbon_still)
    def create_detail_control():
        # create all detail control
        for i in range(division):
            joint = list_ribbon_joint[i]
            control_name = list_detail_control[i]
            locator_name = list_detail_locator[i]

            create_control(name=control_name, match=joint, parent=grp_detail_control)
            cmds.spaceLocator(n=locator_name)
            match_parent(locator_name, control_name)

    def create_follicles():
        for i in range(division):
            follicle_name = list_follicle[i]
            grp_offset_name = list_flc_offset[i]

            cmds.group(n=grp_offset_name, em=1)

            snap_to_surface(nrb_ribbon, grp_offset_name, u=(1 / (division - 1)) * i, v=0.5)

            cmds.matchTransform(grp_offset_name, list_bend_joint, rot=1)

            pin_ribbon(list_pin=[grp_offset_name], surface=nrb_ribbon, output_parent=grp_detail_control, name=follicle_name)
            match_parent(grp_offset_name, follicle_name)


    def parent_detail_controls():
        # create detail controls
        for i in range(division):
            control = list_detail_control[i]
            grp_flc_offset = list_flc_offset[i]

            cmds.parent(control, grp_flc_offset)

        freeze_group_classic(list_detail_control, grpCtrl)

    def create_bend_joints():
        def match_joint():
            cmds.select(cl=1)
            jnt_ref = cmds.joint()

            cmds.select(cl=1)
            jnt_forward = cmds.joint()
            cmds.xform(jnt_forward, ws=1, t=(1, 0, 0))

            cmds.select(cl=1)
            jnt_pole = cmds.joint()
            cmds.xform(jnt_pole, ws=1, t=(0, 0, 1))
            constraint = cmds.aimConstraint(jnt_forward, jnt_ref, aim=get_axis_double3(axis_forward), u=get_axis_double3(axis_pole), wut="object", wuo=jnt_pole)
            cmds.delete(constraint)
            cmds.makeIdentity(jnt_ref, a=1, r=1)

            joint_orient_axis = cmds.getAttr("{}.jointOrient".format(jnt_ref))[0]

            cmds.delete(jnt_ref, jnt_forward, jnt_pole)
            return joint_orient_axis

        # create ribbon driver joints
        list_drive_joint = []
        list_axis_orient = match_joint()

        # create joint ref
        for i,joint in enumerate(list_bend_joint):
            cmds.select(cl=1)
            joint = cmds.joint(n=joint, rad=1.5)
            snap_to_surface(nrb_ribbon, joint, v=0.5, u=(1 / 2) * i, snap="point")

            cmds.setAttr("{}.jointOrient".format(joint), list_axis_orient[0], list_axis_orient[1], list_axis_orient[2], typ="double3")

            list_drive_joint.append(joint)

        return list_drive_joint

    def create_bend_groups():
        def create_group_store_aim():
            # create group store aim
            cmds.group(em=1,n=grp_store_aim_locator)
            match_parent(grp_store_aim_locator,loc_end)

            # create group inside ctrl
            match_parent(cmds.spaceLocator(n=loc_ctrl_corner)[0], grp_store_aim_locator)
            match_parent(cmds.spaceLocator(n=loc_aim_upRot)[0], grp_store_aim_locator)

        def match_part():
            start_drive = loc_start
            end_drive = loc_ctrl_corner
            invert = 1
            parent = grp_bend_control
            list_driver = list_bend_joint

            invert_axis = 1 if axis_forward != axis_forward_abs else 1
            dict_vector_aim = {"x": (1 * invert * invert_axis, 0, 0),
                               "y": (0, 1 * invert * invert_axis, 0),
                               "z": (0, 0, 1 * invert * invert_axis)
                               }
            dict_vector_up = {"x": (1 * invert * invert_axis, 0, 0),
                              "y": (0, 1 * invert * invert_axis, 0),
                              "z": (0, 0, 1 * invert * invert_axis)
                              }
            dict_vector_world_up = {"x": (1 * invert, 0, 0),
                                    "y": (0, 1 * invert, 0),
                                    "z": (0, 0, 1 * invert)
                                    }

            # match all joint driver to group
            [match_parent(joint, parent) for joint in list_driver]

            list_grp_aim = freeze_group_classic(list_driver, "grpAim")
            list_grp_point = freeze_group_classic(list_grp_aim, "grpPoint")

            # match position
            cmds.pointConstraint(start_drive, list_grp_point[0])
            cmds.pointConstraint(end_drive, list_grp_point[2])
            cmds.pointConstraint(start_drive, end_drive, list_grp_point[1])

            # aim start and end to mid
            cmds.aimConstraint(list_driver[1],
                               list_grp_aim[0],
                               aim=get_axis_double3(axis_forward),
                               u=get_axis_double3(axis_pole),
                               wu=get_axis_double3(axis_pole),
                               wut="objectrotation",
                               wuo=list_grp_point[0])
            cmds.aimConstraint(list_driver[1],
                               list_grp_aim[2],
                               aim=[value * -1 for value in get_axis_double3(axis_forward)],
                               u=get_axis_double3(axis_pole),
                               wu=get_axis_double3(axis_pole),
                               wut="objectrotation",
                               wuo=list_grp_point[2])

            # aim mid
            aim_invert = 1
            cmds.aimConstraint(loc_ctrl_corner,
                               list_grp_aim[1],
                               aim=[value * aim_invert for value in get_axis_double3(axis_forward)],
                               u=get_axis_double3(axis_pole),
                               wu=get_axis_double3(axis_pole),
                               wut="objectrotation",
                               wuo=list_grp_point[1])


        create_group_store_aim()

        # match and constraint bendlow and bend up group
        cmds.matchTransform(grp_bend_control, loc_start, pos=1)

        constraint = cmds.aimConstraint(loc_end,
                                        grp_bend_control,
                                        aim=get_axis_double3(axis_forward),
                                        u=get_axis_double3(axis_pole_abs),
                                        wu=get_axis_double3(axis_pole_abs),
                                        wut="objectrotation",
                                        wuo=loc_start)
        cmds.delete(constraint)


        cmds.parentConstraint(loc_start, grp_bend_control, mo=1)

        match_part()

    def apply_joint_scale():
        def apply_scale(bend_control, list_detail_control, list_detail_joint):
            for i, control in enumerate(list_detail_control):
                # fix scale control size
                # grp_scale = freeze_group_classic(control, "grpScl")[0]
                # cmds.connectAttr(grp_get_scale + ".s", grp_scale + ".s")

                node_pma_add = cmds.createNode("plusMinusAverage", n="{}_bendUpSum_pma".format(tag_name))
                cmds.connectAttr("{}.scale".format(control), "{}.input3D[0]".format(node_pma_add))
                cmds.connectAttr("{}.scale".format(bend_control), "{}.input3D[1]".format(node_pma_add))

                node_pma_minus = cmds.createNode("plusMinusAverage", n="{}_bendUpOffset_pma".format(tag_name))
                cmds.setAttr("{}.operation".format(node_pma_minus), 2)
                cmds.connectAttr("{}.output3D".format(node_pma_add), "{}.input3D[0]".format(node_pma_minus))
                cmds.setAttr("{}.input3D[1]".format(node_pma_minus), 1, 1, 1, typ="double3")

                # connect to ribbon joint
                cmds.connectAttr("{}.output3D".format(node_pma_minus), "{}.scale".format(list_detail_joint[i]))

        apply_scale(list_bend_control[1], list_detail_control, list_ribbon_joint)

        grp_get_scale = cmds.group(em=1, n="{}_scaleSpace_grp".format(tag_name), p=grp_detail_control)
        cmds.scaleConstraint(grp_ribbon_rig, grp_get_scale)

        for follicle in list_follicle:
            grp_scale_output = cmds.group(em=1, n="{}_scaleFix_grp".format(follicle))

            cmds.matchTransform(grp_scale_output, grp_get_scale, rot=1)
            cmds.matchTransform(grp_scale_output, follicle, pos=1)

            [cmds.parent(child, grp_scale_output) for child in cmds.listRelatives(follicle, c=1, typ="transform")]

            cmds.parent(grp_scale_output, follicle)

            cmds.connectAttr(grp_get_scale + ".s", grp_scale_output + ".s")

    def create_bend_controls():
        for i, joint in enumerate(list_bend_joint):
            control = list_bend_control[i]

            # insert controller
            parent_joint = cmds.listRelatives(joint, p=1, typ="transform")
            if parent_joint:
                parent_joint = parent_joint[0]
            else:
                continue

            create_control(name=control, match=joint, parent=parent_joint)

            loc_joint = cmds.spaceLocator(n="{}_{}".format(joint, loc))[0]
            match_parent(loc_joint, parent_joint)

            cmds.parent(joint, loc_joint)

            if i != 1 and i != 4:
                cmds.setAttr(control + ".v", 0)

            # controller connection
            cmds.connectAttr(control + ".t", loc_joint + ".t")
            cmds.connectAttr(control + ".r", loc_joint + ".r")

        # connect attributes
        # create attributes
        cmds.addAttr(attr_bend_vis_control.split(".")[0], ln=attr_bend_vis_control.split(".")[1], at="enum",
                     en="Hide:Show", k=1, dv=1)
        cmds.addAttr(attr_detail_vis_control.split(".")[0], ln=attr_detail_vis_control.split(".")[1], at="enum",
                     en="Hide:Show", k=1, dv=1)

        cmds.connectAttr(attr_bend_vis_control, grp_bend_control + ".v")
        cmds.connectAttr(attr_detail_vis_control, grp_detail_control + ".v")

    def apply_joint_constraint():
        for i in range(division):
            locator = list_detail_locator[i]
            joint = list_ribbon_joint[i]

            cmds.parentConstraint(locator, joint)

    def create_hierarchy():
        # create ribbon grp hierarchy
        cmds.group(em=1,n=grp_ribbon_rig)

        cmds.group(em=1, n=grp_ribbon_still, p=grp_ribbon_rig)
        cmds.group(em=1, n=grp_ribbon_anim, p=grp_ribbon_rig)

        cmds.group(em=1, n=grp_bend_control, p=grp_ribbon_anim)
        cmds.group(em=1, n=grp_detail_control, p=grp_ribbon_anim)

        cmds.setAttr(grp_detail_control + ".inheritsTransform", 0)
        cmds.setAttr(grp_ribbon_still + ".inheritsTransform", 0)

        cmds.spaceLocator(n=loc_start)
        cmds.spaceLocator(n=loc_end)


        cmds.parentConstraint(anchor_start,loc_start)
        cmds.parentConstraint(anchor_end,loc_end)

        cmds.parent(loc_start,loc_end,grp_ribbon_anim)
        cmds.parent(grp_ribbon_rig,parent)

    def finalize():
        for control in list_bend_control:
            cmds.setAttr(control + ".s{}".format(axis_forward_abs), l=1, k=0)
            lock_attributes(control, v=1, l=1, k=0)

        for control in list_detail_control:
            lock_attributes(control, v=1, l=1, k=0)

        lock_attributes(grp_store_aim_locator, v=1, r=1, s=1, l=1, k=0)

        cmds.setAttr(nrb_ribbon+".v",0)

        finalize_visibility(grp_ribbon_rig)

    def create_auto_twist():
        if use_anchor_start_as_twist_driver:
            loc_start_twist = anchor_start
        else:
            loc_start_twist = anchor_end

        if not enable_auto_twist:
            return

        if freeze_twist_driver:
            rotate_order = cmds.getAttr("{}.rotateOrder".format(loc_start_twist))

            cmds.addAttr(attr_auto_twist_enable.split(".")[0],ln=attr_auto_twist_enable.split(".")[1],k=1,min=0,max=1,at="float",dv=1)

            # create grp freeze and parent constraint
            grp_freeze = cmds.group(em=1, n="{}_upTwistFreeze_grp".format(tag_name), p=grp_ribbon_still)
            cmds.setAttr("{}.rotateOrder".format(grp_freeze), rotate_order)
            cmds.parentConstraint(anchor_start, grp_freeze)

            # create grp freeze offset in grp freeze invert
            grp_freeze_offset = freeze_group_classic(grp_freeze, "grp")[0]
            grp_freeze_invert = cmds.group(em=1, n="{}_upTwistFreezeInvert_grp".format(tag_name), p=grp_freeze_offset)
            cmds.setAttr("{}.rotateOrder".format(grp_freeze_invert), rotate_order)

            # connection to invert grp freeze invert
            node_mdl = cmds.createNode("multDoubleLinear", n="{}_TwistInvert".format(tag_name))
            cmds.connectAttr("{}.r{}".format(grp_freeze, axis_forward_abs), "{}.input1".format(node_mdl))
            cmds.setAttr("{}.input2".format(node_mdl), -1)

            # create bypass
            connect_attr_conversion(input1="{}.output".format(node_mdl),input2=attr_auto_twist_enable,output="{}.r{}".format(grp_freeze_invert, axis_forward_abs))

            # connection of twist chain

            twist_target = grp_freeze_invert
        else:
            twist_target = loc_start_twist

        list_twist = freeze_group_classic([control for control in list_detail_control], "grpTwist")

        create_twist_chain(list_twist=list_twist,
                           end_target=twist_target,
                           axis=axis_forward_abs,
                           # invert=invert_twist_value,
                           invert_list_twist=invert_rotate_twist)

    def connect_visibility():
        if attr_detail_ctrl_vis:
            cmds.connectAttr(attr_detail_ctrl_vis,attr_detail_vis_control)
        if attr_bend_ctrl_vis:
            cmds.connectAttr(attr_bend_ctrl_vis,attr_bend_vis_control)

        cmds.setAttr(attr_detail_vis_control,k=0,l=1)
        cmds.setAttr(attr_bend_vis_control,k=0,l=1)

    # error handle
    if not list_ribbon_joint:
        raise Exception("Input Ribbon Joint Up and Low must Match Count")

    # group variables
    division = len(list_ribbon_joint)
    grp_ribbon_rig = cname(tag_name, "RibbonRig", grp)
    grp_ribbon_anim = cname(tag_name, "RibbonAnim", grp)
    grp_ribbon_still = cname(tag_name, "RibbonStill", grp)
    grp_bend_control = cname(tag_name, "BendCtrl", grp)
    grp_detail_control = cname(tag_name, "DetailCtrl", grp)

    nrb_ribbon = cname(tag_name, "Ribbon", nrb)
    grp_store_aim_locator = cname(tag_name, "StoreAim", grp)
    loc_aim_upRot = cname(tag_name,"AimUpRot",loc)
    loc_ctrl_corner = cname(tag_name,"CornerRbn",loc)

    loc_start =  cname(tag_name,"startPin",loc)
    loc_end =  cname(tag_name,"endPin",loc)

    # variables
    axis_forward_abs = del_neg(axis_forward)
    axis_pole_abs = del_neg(axis_pole)

    list_detail_locator = ["{}_{}".format(joint,loc) for joint in list_ribbon_joint]
    list_detail_control = ["{}_{}".format(joint,ctrl) for joint in list_ribbon_joint]

    list_follicle = ["{}_{}Pin".format(flc, joint) for joint in list_ribbon_joint]
    list_flc_offset = ["{}_{}Pin".format(grp, joint) for joint in list_ribbon_joint]

    list_bend_control = ["{}_bendStart_{}".format(tag_name, ctrl),"{}_bendMid_{}".format(tag_name, ctrl) ,"{}_bendEnd_{}".format(tag_name, ctrl)  ]
    list_bend_joint = ["{}_bendStart_{}".format(tag_name, jnt),"{}_bendMid_{}".format(tag_name, jnt) ,"{}_bendEnd_{}".format(tag_name, jnt)  ]

    # attribute variables
    attr_detail_vis_control = list_bend_control[1]+".detailControlVisibility"
    attr_bend_vis_control = list_bend_control[1]+".bendControlVisibility"
    attr_auto_twist_enable = list_bend_control[1]+".autoTwistEnable"

    # create ribbon plane and snap to limb
    create_hierarchy()
    create_nurbs_plane()

    # create sub control
    create_detail_control()
    create_bend_joints()
    create_follicles()

    # bind skin ribbon plane
    cmds.skinCluster(list_bend_joint, nrb_ribbon, ih=1, mi=2, bm=1, dr=8,n="{}Rbn_skinCluster".format(tag_name))

    create_bend_groups()

    parent_detail_controls()

    create_bend_controls()

    # assign twist system
    create_auto_twist()

    # apply output to ribbon joints
    apply_joint_constraint()
    apply_joint_scale()
    connect_visibility()

    # lock and hide control
    finalize()

def create_ribbon_rig_v2(anchor_start,
                         anchor_end,
                         parent,
                         axis_forward,
                         axis_pole,
                         list_ribbon_joint,
                         tag_name="leg",
                         enable_auto_twist=True,
                         invert_twist_driver=True,
                         freeze_anchor_start=False,
                         freeze_anchor_end=False,
                         invert_twist_anchor = False,
                         invert_between_value = False,
                         attr_detail_ctrl_vis=None,
                         attr_bend_ctrl_vis=None):

    def create_nurbs_plane():
        # create ribbon plane  reference scale from limb joints
        width_up = get_distance_two(loc_start, loc_end)

        cmds.nurbsPlane(w=width_up, lr=0.05, u=4, v=1, d=3, ax=(0, 0, 1), ch=0, n=nrb_ribbon)
        cmds.parent(nrb_ribbon,grp_ribbon_still)

    def create_detail_control():
        # create all detail control
        for i in range(division):
            joint = list_ribbon_joint[i]
            control_name = list_detail_control[i]
            locator_name = list_detail_locator[i]

            create_control(name=control_name,
                           match=joint,
                           parent=grp_detail_control,
                           size=0.8,
                           color="blue")
            cmds.spaceLocator(n=locator_name)
            match_parent(locator_name, control_name)

    def create_follicles():
        for i in range(division):
            follicle_name = list_follicle[i]
            grp_offset_name = list_flc_offset[i]

            cmds.group(n=grp_offset_name, em=1)

            snap_to_surface(nrb_ribbon, grp_offset_name, u=(1 / (division - 1)) * i, v=0.5)

            cmds.matchTransform(grp_offset_name, list_bend_joint, rot=1)

            pin_ribbon(list_pin=[grp_offset_name], surface=nrb_ribbon, output_parent=grp_detail_control, name=follicle_name)
            match_parent(grp_offset_name, follicle_name)

    def parent_detail_controls():
        # create detail controls
        for i in range(division):
            control = list_detail_control[i]
            grp_flc_offset = list_flc_offset[i]

            cmds.parent(control, grp_flc_offset)

        freeze_group_classic(list_detail_control, grpCtrl)

    def create_bend_joints():
        def match_joint():
            cmds.select(cl=1)
            jnt_ref = cmds.joint()

            cmds.select(cl=1)
            jnt_forward = cmds.joint()
            cmds.xform(jnt_forward, ws=1, t=(1, 0, 0))

            cmds.select(cl=1)
            jnt_pole = cmds.joint()
            cmds.xform(jnt_pole, ws=1, t=(0, 0, 1))
            constraint = cmds.aimConstraint(jnt_forward, jnt_ref, aim=get_axis_double3(axis_forward), u=get_axis_double3(axis_pole), wut="object", wuo=jnt_pole)
            cmds.delete(constraint)
            cmds.makeIdentity(jnt_ref, a=1, r=1)

            joint_orient_axis = cmds.getAttr("{}.jointOrient".format(jnt_ref))[0]

            cmds.delete(jnt_ref, jnt_forward, jnt_pole)
            return joint_orient_axis

        def create_cluster():
            cmds.select(nrb_ribbon)
            lattice_node, lattice_shape, lattice_base = cmds.lattice(dv=(3, 2, 2), oc=1)

            grp_lattice = cmds.group(lattice_base,lattice_shape,n=cname(tag_name,"lattice",grp),p=grp_ribbon_anim)

            cmds.setAttr(grp_lattice+".inheritsTransform",0)
            cmds.parent(grp_lattice,parent)

            for i in range(3):
                cluster_name = list_cluster[i]

                cmds.select(["{}.pt[{}][0:1][0]".format(lattice_shape, i), "{}.pt[{}][0:1][1]".format(lattice_shape, i)], r=1)
                cluster = cmds.cluster(n=cluster_name,rel=False)[1]

                # grp_frz = freeze_group_classic(cluster)[0]
                cmds.parent(cluster, list_bend_joint[i])

        list_cluster = [cname(tag_name, "Start", "cluster"), cname(tag_name, "Mid", "cluster"), cname(tag_name, "End", "cluster")]


        # create ribbon driver joints
        list_drive_joint = []
        list_axis_orient = match_joint()

        # create joint ref
        for i,joint in enumerate(list_bend_joint):
            cmds.select(cl=1)
            joint = cmds.joint(n=joint, rad=1.5)
            snap_to_surface(nrb_ribbon, joint, v=0.5, u=(1 / 2) * i, snap="point")

            cmds.setAttr("{}.jointOrient".format(joint), list_axis_orient[0], list_axis_orient[1], list_axis_orient[2], typ="double3")

            list_drive_joint.append(joint)

        create_cluster()

        return list_drive_joint

    def create_bend_groups():
        def create_group_store_aim():
            # create group store aim
            cmds.group(em=1,n=grp_store_aim_locator)
            match_parent(grp_store_aim_locator,loc_end)

            # create group inside ctrl
            match_parent(cmds.spaceLocator(n=loc_ctrl_corner)[0], grp_store_aim_locator)
            match_parent(cmds.spaceLocator(n=loc_aim_upRot)[0], grp_store_aim_locator)

        def match_part():

            start_drive = loc_start
            end_drive = loc_ctrl_corner
            invert = 1
            parent = grp_bend_control
            list_driver = list_bend_joint

            invert_axis = 1 if axis_forward != axis_forward_abs else 1
            dict_vector_aim = {"x": (1 * invert * invert_axis, 0, 0),
                               "y": (0, 1 * invert * invert_axis, 0),
                               "z": (0, 0, 1 * invert * invert_axis)
                               }
            dict_vector_up = {"x": (1 * invert * invert_axis, 0, 0),
                              "y": (0, 1 * invert * invert_axis, 0),
                              "z": (0, 0, 1 * invert * invert_axis)
                              }
            dict_vector_world_up = {"x": (1 * invert, 0, 0),
                                    "y": (0, 1 * invert, 0),
                                    "z": (0, 0, 1 * invert)
                                    }

            # match all joint driver to group
            [match_parent(joint, parent) for joint in list_driver]

            list_grp_aim = freeze_group_classic(list_driver, "grpAim")
            list_grp_point = freeze_group_classic(list_grp_aim, "grpPoint")

            # match position
            cmds.pointConstraint(start_drive, list_grp_point[0])
            cmds.pointConstraint(end_drive, list_grp_point[2])
            cmds.pointConstraint(start_drive, end_drive, list_grp_point[1])

            # aim start and end to mid
            cmds.aimConstraint(list_driver[1],
                               list_grp_aim[0],
                               aim=get_axis_double3(axis_forward),
                               u=get_axis_double3(axis_pole),
                               wu=get_axis_double3(axis_pole),
                               wut="objectrotation",
                               wuo=list_grp_point[0])
            cmds.aimConstraint(list_driver[1],
                               list_grp_aim[2],
                               aim=[value * -1 for value in get_axis_double3(axis_forward)],
                               u=get_axis_double3(axis_pole),
                               wu=get_axis_double3(axis_pole),
                               wut="objectrotation",
                               wuo=list_grp_point[2])

            # aim mid
            aim_invert = 1
            cmds.aimConstraint(loc_ctrl_corner,
                               list_grp_aim[1],
                               aim=[value * aim_invert for value in get_axis_double3(axis_forward)],
                               u=get_axis_double3(axis_pole),
                               wu=get_axis_double3(axis_pole),
                               wut="objectrotation",
                               wuo=list_grp_point[1])



        create_group_store_aim()

        # match and constraint bend low and bend up group
        cmds.matchTransform(grp_bend_control, loc_start, pos=1)

        constraint = cmds.aimConstraint(loc_end,
                                        grp_bend_control,
                                        aim=get_axis_double3(axis_forward),
                                        u=get_axis_double3(axis_pole_abs),
                                        wu=get_axis_double3(axis_pole_abs),
                                        wut="objectrotation",
                                        wuo=loc_start)
        cmds.delete(constraint)

        cmds.parentConstraint(loc_start, grp_bend_control, mo=1)

        match_part()

    def apply_joint_scale():
        def apply_scale(bend_control, list_detail_control, list_detail_joint):
            for i, control in enumerate(list_detail_control):
                # fix scale control size
                # grp_scale = freeze_group_classic(control, "grpScl")[0]
                # cmds.connectAttr(grp_get_scale + ".s", grp_scale + ".s")

                node_pma_add = cmds.createNode("plusMinusAverage", n="{}_bendUpSum_pma".format(tag_name))
                cmds.connectAttr("{}.scale".format(control), "{}.input3D[0]".format(node_pma_add))
                cmds.connectAttr("{}.scale".format(bend_control), "{}.input3D[1]".format(node_pma_add))

                node_pma_minus = cmds.createNode("plusMinusAverage", n="{}_bendUpOffset_pma".format(tag_name))
                cmds.setAttr("{}.operation".format(node_pma_minus), 2)
                cmds.connectAttr("{}.output3D".format(node_pma_add), "{}.input3D[0]".format(node_pma_minus))
                cmds.setAttr("{}.input3D[1]".format(node_pma_minus), 1, 1, 1, typ="double3")

                # connect to ribbon joint
                cmds.connectAttr("{}.output3D".format(node_pma_minus), "{}.scale".format(list_detail_joint[i]))

        apply_scale(list_bend_control[1], list_detail_control, list_ribbon_joint)

        grp_get_scale = cmds.group(em=1, n="{}_scaleSpace_grp".format(tag_name), p=grp_detail_control)
        cmds.scaleConstraint(grp_ribbon_rig, grp_get_scale)

        for follicle in list_follicle:
            grp_scale_output = cmds.group(em=1, n="{}_scaleFix_grp".format(follicle))

            cmds.matchTransform(grp_scale_output, grp_get_scale, rot=1)
            cmds.matchTransform(grp_scale_output, follicle, pos=1)

            [cmds.parent(child, grp_scale_output) for child in cmds.listRelatives(follicle, c=1, typ="transform")]

            cmds.parent(grp_scale_output, follicle)

            cmds.connectAttr(grp_get_scale + ".s", grp_scale_output + ".s")

    def create_bend_controls():
        for i, joint in enumerate(list_bend_joint):
            control = list_bend_control[i]

            # insert controller
            parent_joint = cmds.listRelatives(joint, p=1, typ="transform")
            if parent_joint:
                parent_joint = parent_joint[0]
            else:
                continue

            # create controller
            create_control(name=control,
                           match=joint,
                           parent=parent_joint,
                           size=0.9,
                           color="purple")

            cmds.parent(joint,control)

            if i != 1 and i != 4:
                cmds.setAttr(control + ".v", 0)

        # connect attributes
        # create attributes
        cmds.addAttr(attr_bend_vis_control.split(".")[0], ln=attr_bend_vis_control.split(".")[1], at="enum",
                     en="Hide:Show", k=1, dv=1)
        cmds.addAttr(attr_detail_vis_control.split(".")[0], ln=attr_detail_vis_control.split(".")[1], at="enum",
                     en="Hide:Show", k=1, dv=1)

        cmds.connectAttr(attr_bend_vis_control, grp_bend_control + ".v")
        cmds.connectAttr(attr_detail_vis_control, grp_detail_control + ".v")

    def apply_joint_constraint():
        for i in range(division):
            locator = list_detail_locator[i]
            joint = list_ribbon_joint[i]

            cmds.parentConstraint(locator, joint)

    def create_hierarchy():
        # create ribbon grp hierarchy
        cmds.group(em=1,n=grp_ribbon_rig)

        cmds.group(em=1, n=grp_ribbon_still, p=grp_ribbon_rig)
        cmds.group(em=1, n=grp_ribbon_anim, p=grp_ribbon_rig)

        cmds.group(em=1, n=grp_bend_control, p=grp_ribbon_anim)
        cmds.group(em=1, n=grp_detail_control, p=grp_ribbon_anim)

        cmds.setAttr(grp_detail_control + ".inheritsTransform", 0)
        cmds.setAttr(grp_ribbon_still + ".inheritsTransform", 0)

        cmds.spaceLocator(n=loc_start)
        cmds.spaceLocator(n=loc_end)


        cmds.parentConstraint(anchor_start,loc_start)
        cmds.parentConstraint(anchor_end,loc_end)

        cmds.parent(loc_start,loc_end,grp_ribbon_anim)
        cmds.parent(grp_ribbon_rig,parent)

    def finalize():
        for control in list_bend_control:
            cmds.setAttr(control + ".s{}".format(axis_forward_abs), l=1, k=0)
            lock_attributes(control, v=1, l=1, k=0)

        for control in list_detail_control:
            lock_attributes(control, v=1, l=1, k=0)

        lock_attributes(grp_store_aim_locator, v=1, r=1, s=1, l=1, k=0)

        cmds.setAttr(nrb_ribbon+".v",0)

        finalize_visibility(grp_ribbon_rig)


    def connect_visibility():
        if attr_detail_ctrl_vis:
            cmds.connectAttr(attr_detail_ctrl_vis,attr_detail_vis_control)
        if attr_bend_ctrl_vis:
            cmds.connectAttr(attr_bend_ctrl_vis,attr_bend_vis_control)

        cmds.setAttr(attr_detail_vis_control,k=0,l=1)
        cmds.setAttr(attr_bend_vis_control,k=0,l=1)

    def quaternion_twist():
        # loc_start_twist = cmds.spaceLocator(n=cname(tag_name,"startTwist",loc))
        # loc_end_twist = cmds.spaceLocator(n=cname(tag_name,"endTwist",loc))
        #
        # cmds.parent(loc_start_twist,anchor_start)
        # cmds.parent(loc_start_twist,anchor_end)

        def create_invert_twist_locator(object):
            loc_invert_result = cmds.spaceLocator(n=cname(tag_name,"invertTwist",loc))[0]
            grp_invert_result = cmds.group(loc_invert_result,n=cname(tag_name,"invertTwist",grp))
            cmds.setAttr(grp_invert_result+".inheritsTransform",0)

            cmds.parent(grp_invert_result,parent)

            # constraint position
            node_decomp_matrix = cmds.createNode("decomposeMatrix",n=cname(tag_name,"decompPos","dcm"))
            cmds.connectAttr(object+".worldMatrix[0]",node_decomp_matrix+".inputMatrix")
            cmds.connectAttr(object+".rotateOrder",node_decomp_matrix+".inputRotateOrder")
            cmds.connectAttr(node_decomp_matrix+".outputTranslate",grp_invert_result+".translate")

            # connect invert rotate
            node_euler_to_quat = cmds.createNode("eulerToQuat",n=cname(tag_name,"eulerToQuat","etq"))
            cmds.connectAttr(object+".rotate",node_euler_to_quat+".inputRotate")
            cmds.connectAttr(object+".rotateOrder",node_euler_to_quat+".inputRotateOrder")

            node_quat_invert = cmds.createNode("quatInvert",n=cname(tag_name,"quatInvert","qi"))
            cmds.connectAttr("{}.outputQuat{}".format(node_euler_to_quat,axis_forward_abs.upper()),"{}.inputQuat{}".format(node_quat_invert,axis_forward_abs.upper()))
            cmds.connectAttr("{}.outputQuatW".format(node_euler_to_quat),"{}.inputQuatW".format(node_quat_invert))

            node_quat_prod = cmds.createNode("quatProd",n=cname(tag_name,"quatProd","qp"))
            cmds.connectAttr(node_quat_invert+".outputQuat",node_quat_prod+".input1Quat")
            cmds.connectAttr(node_euler_to_quat+".outputQuat",node_quat_prod+".input2Quat")

            node_quat_to_euler = cmds.createNode("quatToEuler")
            cmds.connectAttr(node_quat_prod+".outputQuat",node_quat_to_euler+".inputQuat")
            cmds.connectAttr(object+".rotateOrder",node_quat_to_euler+".inputRotateOrder")

            # connect output to invert result
            cmds.connectAttr(node_quat_to_euler+".outputRotate",loc_invert_result+".rotate")
            cmds.connectAttr(object+".rotateOrder",loc_invert_result+".rotateOrder")

            return loc_invert_result

        def create_euler_output(object):
            node_euler_to_quat = cmds.createNode("eulerToQuat",n=cname(tag_name,"eulerToQuat","etq"))
            cmds.connectAttr(object+".r",node_euler_to_quat+".inputRotate")
            cmds.connectAttr(object+".rotateOrder",node_euler_to_quat+".inputRotateOrder")

            # node_dcm = cmds.createNode("decomposeMatrix",n=cname(tag_name,"decomp","dcm"))
            # cmds.connectAttr(object+".matrix",node_dcm+".inputMatrix")
            # cmds.connectAttr(object+".rotateOrder",node_dcm+".inputRotateOrder")

            node_quat_to_euler = cmds.createNode("quatToEuler",n=cname(tag_name,"quatToEuler","qte"))
            cmds.connectAttr("{}.outputQuat{}".format(node_euler_to_quat,axis_forward_abs.upper()),node_quat_to_euler+".inputQuat{}".format(axis_forward_abs.upper()))
            cmds.connectAttr("{}.outputQuatW".format(node_euler_to_quat),node_quat_to_euler+".inputQuatW")
            cmds.connectAttr(object+".rotateOrder",node_quat_to_euler+".inputRotateOrder")

            node_offset = cmds.createNode("addDoubleLinear")
            cmds.connectAttr(node_quat_to_euler+".outputRotate{}".format(axis_forward_abs.upper()), node_offset + ".input1")
            cmds.setAttr(node_offset + ".input2", cmds.getAttr("{}.outputRotate{}".format(node_quat_to_euler,axis_forward_abs.upper())) * -1)

            return node_offset+".output"

        def connect_euler_to_between(invert_value):
            node_bw = cmds.createNode("blendWeighted")
            cmds.connectAttr(attr_start_euler, node_bw + ".input[0]")
            cmds.connectAttr(attr_end_euler, node_bw + ".input[1]")

            node_division = cmds.createNode("multDoubleLinear")
            cmds.connectAttr(node_bw + ".output", node_division + ".input1")

            if invert_value:
                cmds.setAttr(node_division + ".input2", -0.5)
            else:
                cmds.setAttr(node_division + ".input2", 0.5)

            # connect to output
            grp_frz1 = freeze_group_classic(list_bend_control[1], "grpTwist1")[0]
            grp_frz2 = freeze_group_classic(list_bend_control[1], "grpTwist2")[0]

            cmds.connectAttr(node_division + ".output", "{}.r{}".format(grp_frz2, axis_forward_abs))

        def connect_euler_to_tip(attr_euler,object,invert_value=False):
            grp_frz1 = freeze_group_classic(object,"grp2")[0]
            grp_frz2 = freeze_group_classic(object,"grp1")[0]

            if invert_value:
                node_mdl_invert = cmds.createNode("multDoubleLinear",n=cname(tag_name,"invertFreeze","mdl"))
                cmds.connectAttr(attr_euler,"{}.input1".format(node_mdl_invert))
                cmds.setAttr("{}.input2".format(node_mdl_invert),-1)
                cmds.connectAttr("{}.output".format(node_mdl_invert),grp_frz2+".r{}".format(axis_forward_abs))
            else:
                cmds.connectAttr(attr_euler,grp_frz2+".r{}".format(axis_forward_abs))


        if not enable_auto_twist:
            return

        # if freeze_twist_driver:
        #     # locator_invert = create_invert_twist_locator(anchor_start)
        #     attr_start_euler = create_euler_output(locator_invert)
        # else:

        # get euler start and end value
        if invert_twist_anchor:
            attr_start_euler = create_euler_output(anchor_start)
            attr_end_euler = create_euler_output(anchor_end)
        else:
            attr_start_euler = create_euler_output(anchor_end)
            attr_end_euler = create_euler_output(anchor_start)

        connect_euler_to_between(invert_value=invert_between_value)

        # connect output to bend control
        if invert_twist_driver:
            connect_euler_to_tip(attr_start_euler, list_bend_control[2], invert_value=freeze_anchor_start)
            connect_euler_to_tip(attr_end_euler, list_bend_control[0], invert_value=freeze_anchor_end)
        else:
            connect_euler_to_tip(attr_start_euler,list_bend_control[0],invert_value=freeze_anchor_start)
            connect_euler_to_tip(attr_end_euler,list_bend_control[2],invert_value=freeze_anchor_end)


    # error handle
    if not list_ribbon_joint:
        raise Exception("Input Ribbon Joint Up and Low must Match Count")

    # group variables
    division = len(list_ribbon_joint)
    grp_ribbon_rig = cname(tag_name, "RibbonRig", grp)
    grp_ribbon_anim = cname(tag_name, "RibbonAnim", grp)
    grp_ribbon_still = cname(tag_name, "RibbonStill", grp)
    grp_bend_control = cname(tag_name, "BendCtrl", grp)
    grp_detail_control = cname(tag_name, "DetailCtrl", grp)

    nrb_ribbon = cname(tag_name, "Ribbon", nrb)
    grp_store_aim_locator = cname(tag_name, "StoreAim", grp)
    loc_aim_upRot = cname(tag_name,"AimUpRot",loc)
    loc_ctrl_corner = cname(tag_name,"CornerRbn",loc)

    loc_start =  cname(tag_name,"startPin",loc)
    loc_end =  cname(tag_name,"endPin",loc)

    # variables
    axis_forward_abs = del_neg(axis_forward)
    axis_pole_abs = del_neg(axis_pole)

    list_detail_locator = ["{}_{}".format(joint,loc) for joint in list_ribbon_joint]
    list_detail_control = ["{}_{}".format(joint,ctrl) for joint in list_ribbon_joint]

    list_follicle = ["{}_{}Pin".format(flc, joint) for joint in list_ribbon_joint]
    list_flc_offset = ["{}_{}Pin".format(grp, joint) for joint in list_ribbon_joint]

    list_bend_control = ["{}_bendStart_{}".format(tag_name, ctrl),"{}_bendMid_{}".format(tag_name, ctrl) ,"{}_bendEnd_{}".format(tag_name, ctrl)  ]
    list_bend_joint = ["{}_bendStart_{}".format(tag_name, jnt),"{}_bendMid_{}".format(tag_name, jnt) ,"{}_bendEnd_{}".format(tag_name, jnt)  ]

    # attribute variables
    attr_detail_vis_control = list_bend_control[1]+".detailControlVisibility"
    attr_bend_vis_control = list_bend_control[1]+".bendControlVisibility"
    attr_auto_twist_enable = list_bend_control[1]+".autoTwistEnable"

    # create ribbon plane and snap to limb
    create_hierarchy()
    create_nurbs_plane()

    # create sub control
    create_detail_control()
    create_bend_joints()
    create_follicles()

    # bind skin ribbon plane
    create_bend_groups()

    parent_detail_controls()

    create_bend_controls()

    quaternion_twist()
    # assign twist system
    # create_auto_twist()

    # apply output to ribbon joints
    apply_joint_constraint()
    apply_joint_scale()
    connect_visibility()

    # lock and hide control
    finalize()

def create_sticky_both(list_base_position,
                       list_zipped_position,
                       list_zipped_output,
                       list_attr_zip,
                       list_attr_distance,
                       config_parent=None,
                       name=None,
                       offset=0,
                       unit_conversion=10,
                       list_attr_separate=None):
    def create_clamp_list_node(attr_zip):

        if attr_zip == attr_zip_left:
            attr_distance = list_attr_distance[0]
            option_shape_path = list_attr_distance[0].split(".")[0]
            option_shape = add_option_shape(option_shape_path, "zipper_option")

        elif attr_zip == attr_zip_right:
            attr_distance = list_attr_distance[1]
            option_shape_path = list_attr_distance[1].split(".")[0]
            option_shape = add_option_shape(option_shape_path, "zipper_option")

        list_clamp_output = []

        # prepare remap and transform node
        node_remap = cmds.createNode("remapValue", n="{}_remap_rmv".format(name))
        cmds.setAttr(node_remap + ".outputMax", amount_clamp + 1)
        cmds.setAttr(node_remap + ".inputMax", 1)
        cmds.connectAttr(attr_zip, node_remap + ".inputValue")

        # create sticky systems
        for i in range(amount_clamp):
            node_md_distance = cmds.createNode("multDoubleLinear", n="{}_zipper_mdl".format(name))
            cmds.connectAttr(attr_distance, node_md_distance + ".input2")
            cmds.setAttr(node_md_distance + ".input1", i + offset)

            node_adl_add = cmds.createNode("addDoubleLinear", n="{}_zipper_adl".format(name))
            cmds.connectAttr("{}.output".format(node_md_distance), node_adl_add + ".input2")
            cmds.addAttr(option_shape, ln=list_zipped_output[i], at="float", dv=1, k=1, min=0, max=2)
            cmds.connectAttr("{}.{}".format(option_shape, list_zipped_output[i]), "{}.input1".format(node_adl_add))

            node_pma_output = cmds.createNode("plusMinusAverage", n="{}_zipper_pma".format(name))
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
            constraint = cmds.parentConstraint(list_base_position[index], list_zipped_position[index], list_zipped_output[index], mo=1)[0]
            list_weight = cmds.parentConstraint(constraint, q=1, wal=1)

            cmds.connectAttr(node_clamp + ".outputR", constraint + "." + list_weight[1])

            node_reverse = cmds.createNode("reverse", n="{}_zipper_rev".format(name))
            cmds.connectAttr(node_clamp + ".outputR", node_reverse + ".inputX")
            cmds.connectAttr(node_reverse + ".outputX", constraint + "." + list_weight[0])

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
            node_pma_sum = cmds.createNode("plusMinusAverage", n="{}_betweenSum_pma".format(name))
            cmds.connectAttr(list_attr_clamp_right[-1] + ".outputR", node_pma_sum + ".input1D[0]")
            cmds.connectAttr(list_attr_clamp_left[-1] + ".outputR", node_pma_sum + ".input1D[1]")

            node_clamp_sum = cmds.createNode("clamp", n="{}_betweenClamp_cmp".format(name))
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


def create_sticky_matrix(list_base_position, listB, list_zipped_output, attr_zipper="transform1.sticky", attr_size="transform1.distance", name="zipper", isMirror=True):
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
        node_blend_matrix = cmds.createNode("blendMatrix", n="{}{}_bm".format(name, i + 1))

        cmds.connectAttr("{}.worldMatrix[0]".format(objA), "{}.inputMatrix".format(node_blend_matrix))
        cmds.connectAttr("{}.worldMatrix[0]".format(objB), "{}.target[0].targetMatrix".format(node_blend_matrix))
        cmds.connectAttr("{}.outputMatrix".format(node_blend_matrix), "{}.offsetParentMatrix".format(objC))

        reset_all_transform(objC)

        if isMirror and i >= (index_mirror - 1):
            node_sr = list_sr_node[index_mirror - i]

            cmds.connectAttr("{}.outValueX".format(node_sr), "{}.envelope".format(node_blend_matrix))

        else:
            node_set_range = cmds.createNode("setRange", n="sr_{}{}".format(name, i + 1))
            node_md = cmds.createNode("multiplyDivide", n="md_{}{}".format(name, i + 1))
            node_pma = cmds.createNode("plusMinusAverage", n="pma_{}{}".format(name, i + 1))

            input_min = (i) * (1 / amount)
            input_max = (i + 1) * (1 / amount)
            value_mult = i

            # set range connection
            cmds.connectAttr(attr_zipper, "{}.valueX".format(node_set_range))
            cmds.setAttr("{}.minX".format(node_set_range), 0)
            cmds.setAttr("{}.maxX".format(node_set_range), 1)
            cmds.connectAttr("{}.outValueX".format(node_set_range), "{}.envelope".format(node_blend_matrix))

            # multiply + pma node
            cmds.connectAttr(attr_size, "{}.input1X".format(node_md))
            cmds.connectAttr(attr_size, "{}.input1Y".format(node_md))

            cmds.setAttr("{}.input2X".format(node_md), value_mult)
            cmds.setAttr("{}.input2Y".format(node_md), value_mult)

            cmds.connectAttr("{}.outputX".format(node_md), "{}.input3D[0].input3Dx".format(node_pma))
            cmds.connectAttr("{}.outputY".format(node_md), "{}.input3D[0].input3Dy".format(node_pma))

            cmds.setAttr("{}.input3D[1].input3Dx".format(node_pma), input_min)
            cmds.setAttr("{}.input3D[1].input3Dy".format(node_pma), input_max)

            cmds.connectAttr("{}.output3Dx".format(node_pma), "{}.oldMinX".format(node_set_range))
            cmds.connectAttr("{}.output3Dy".format(node_pma), "{}.oldMaxX".format(node_set_range))

            # append
            list_sr_node.append(node_set_range)


def create_sticky_old(list_base_position,
                      list_zipped_position,
                      list_zipped_output,
                      attr_zip="transform1.sticky",
                      attr_distance="transform1.distance",
                      config_parent=None,
                      name=None,
                      offset=0,
                      unit_conversion=10,
                      list_attr_separate=None):
    def connect_constraint(index, node_clamp):
        constraint = cmds.parentConstraint(list_base_position[index], list_zipped_position[index], list_zipped_output[index], mo=1)[0]
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
            cmds.connectAttr("{}.output".format(node_md_distance), node_adl_add + ".input2")
            cmds.addAttr(node_adjust, ln=list_zipped_output[i], at="float", dv=1, k=1, min=0, max=2)
            cmds.connectAttr("{}.{}".format(node_adjust, list_zipped_output[i]), "{}.input1".format(node_adl_add))

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


def create_stretchy_joint(loc_start_dist,
                          loc_pole_dist,
                          loc_end_dist,
                          controller_attr,
                          axis_forward,
                          list_stretch_joints,
                          stretch_with_fixed_angle = False,
                          name_tag="Limb"
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
                node_dist = cmds.createNode("distanceBetween", n="{}_{}_dist".format(name_tag,list_stretch_joints[i]))
                cmds.connectAttr("{}.translate".format(list_stretch_joints[i]), "{}.point1".format(node_dist))
                cmds.connectAttr("{}.translate".format(list_stretch_joints[i+1]), "{}.point2".format(node_dist))

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

            cmds.connectAttr(attr_output, "{}.t{}".format(stretch_joint, axis_forward_abs))

    def connect_stretch():
        # Stretch ----------------------------------
        # connection distance
        node_distance = cmds.createNode("distanceBetween", n="{}_autoStretchLength_dist".format(name_tag))
        cmds.connectAttr("{}.translate".format(loc_start_dist), "{}.point1".format(node_distance), )
        cmds.connectAttr("{}.translate".format(loc_end_dist), "{}.point2".format(node_distance))

        # connection normalize
        node_md_normalize = cmds.createNode("multiplyDivide", n="{}_stretchLengthNormalize_md".format(name_tag))
        cmds.connectAttr("{}.distance".format(node_distance), "{}.input1X".format(node_md_normalize))
        factor = 1 / value_full_length
        cmds.setAttr("{}.input2X".format(node_md_normalize), factor)

        # condition
        node_condition = cmds.createNode("condition", n="{}_autoStretch_cond".format(name_tag))
        cmds.setAttr("{}.operation".format(node_condition), 2)
        cmds.connectAttr("{}.distance".format(node_distance), "{}.firstTerm".format(node_condition))
        cmds.setAttr("{}.secondTerm".format(node_condition), value_full_length)
        cmds.connectAttr("{}.outputX".format(node_md_normalize), "{}.colorIfTrueR".format(node_condition))

        # mdv stretch connection

        for i in range(len_stretch_joint):
            if i == 0:
                continue

            stretch_joint = list_stretch_joints[i]
            # multiply stretch factor
            node_md_stretch = cmds.createNode("multDoubleLinear", n="{}_{}Stretch_mdl".format(name_tag, stretch_joint))
            cmds.connectAttr("{}.outColorR".format(node_condition), "{}.input1".format(node_md_stretch))
            cmds.setAttr("{}.input2".format(node_md_stretch), cmds.getAttr("{}.t{}".format(stretch_joint, axis_forward_abs)))  # translate multiply

            # by pass
            node_bc_bypass = cmds.createNode("blendTwoAttr", n="{}_{}StretchByPass_bc".format(name_tag, stretch_joint))
            cmds.connectAttr(attr_auto_stretch, "{}.attributesBlender".format(node_bc_bypass))
            cmds.connectAttr(node_md_stretch + ".output", "{}.input[1]".format(node_bc_bypass))
            cmds.setAttr("{}.input[0]".format(node_bc_bypass), cmds.getAttr("{}.output".format(node_md_stretch)))

            # stretch adjust
            node_pma_stretch = cmds.createNode("plusMinusAverage", n="{}_stretchAdd_pma".format(name_tag))

            # stretch invert ( in right arm case )
            attr_adjust_stretch = list_attr_arm_adjust_stretch[i - 1]
            connect_attr_conversion(input1=attr_adjust_stretch, conversion=invert_value, output="{}.input1D[1]".format(node_pma_stretch))
            cmds.connectAttr("{}.output".format(node_bc_bypass), "{}.input1D[0]".format(node_pma_stretch))

            # return attr output
            dict_attr_stretch_output[stretch_joint] = node_pma_stretch + ".output1D"

    len_stretch_joint = len(list_stretch_joints)
    list_node_dist_for_pole_lock = []
    list_node_blend_for_pole_lock = []
    attr_auto_stretch = "{}.autoStretch".format(controller_attr)
    list_attr_arm_adjust_stretch = []
    dict_attr_stretch_output = {}

    # attribute
    for i in range(len_stretch_joint-1):
        attr_arm_adjust_stretch = "{}.LimbStretch{}".format(controller_attr,i+1)
        cmds.addAttr(controller_attr, k=1, ln="LimbStretch{}".format(i+1), at="float")
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
        value_full_length = get_distance_two(loc_start_dist, loc_end_dist)
    else:
        value_full_length = 0

        for i in range(len_stretch_joint):
            if i+1 >= len_stretch_joint:
                continue
            else:
                value_full_length += get_distance_two( list_stretch_joints[i], list_stretch_joints[i+1])


    connect_stretch()
    apply_stretch_to_joint()
    # create_pole_lock()


def create_switch_fk_ik_chain(target_joints,
                              grp_fk_joints,
                              grp_ik_joints,
                              attr_switch,
                              grp_ik_controls,
                              grp_fk_controls,
                              attribute_switch_range=1,
                              tag_name = "limb",
                              list_append_keyword = ["Fk", "Ik"]
                              ):

    def duplicate_joints():
        # duplicate joints to fk group and ik group (include it's parent)
        for i, typ in enumerate(list_append_keyword):
            # change group
            parent_path = grp_fk_joints if  i == 0 else grp_ik_joints
            recent = None

            # parent offset joint
            parent_joint = cmds.listRelatives(target_joints[0], p=1,f=1)

            if parent_joint:
                tmp = cmds.duplicate(parent_joint[0], n=parent_joint[0] + typ, po=1)[0]

                # unlock translate,rotate,scale
                lock_attributes(tmp, t=1, r=1, s=1, v=1, l=0, k=1)

                cmds.parent(tmp, parent_path)
                cmds.parentConstraint(parent_joint[0], tmp)
                recent = tmp

            # limb joint
            for joint in target_joints:
                tmp = cmds.duplicate(joint, n=joint + typ, po=1)[0]
                cmds.parent(tmp, parent_path) if recent is None else cmds.parent(tmp, recent)
                recent = tmp

    def connect_switch_joints():
        # create switch systems , use blendColor Node
        node_reverse = cmds.createNode("reverse", n="rev_{}Switch".format(tag_name))
        cmds.connectAttr(attr_switch, "{}.inputX".format(node_reverse))

        list_name_fk_joint = [joint+ list_append_keyword[0] for joint in target_joints]
        list_name_ik_joint = [joint+ list_append_keyword[1] for joint in target_joints]

        for i, joint in enumerate(target_joints):
            for data in [["t", "Pos"], ["r", "Rot"]]:
                attr = data[0]
                keyword = data[1]

                node_blend = cmds.createNode("blendColors", n="{}_blend{}{}_blc".format(tag_name, joint, keyword))
                cmds.connectAttr(attr_switch, "{}.blender".format(node_blend))
                cmds.connectAttr("{}.{}".format(list_name_ik_joint[i], attr), "{}.color1".format(node_blend))
                cmds.connectAttr("{}.{}".format(list_name_fk_joint[i], attr), "{}.color2".format(node_blend))
                cmds.connectAttr("{}.output".format(node_blend), "{}.{}".format(joint, attr))

        for i, joint in enumerate(target_joints):
            source_joint = list_name_fk_joint[i]

            cmds.connectAttr("{}.rotateOrder".format(source_joint),"{}.rotateOrder".format(joint))

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
        raise Exception("Invalid Attribute Switch Range Input , Must be greater than zero. got {}".format(attribute_switch_range))

    target_joints = remove_none(target_joints)

    duplicate_joints()
    connect_switch_joints()
    connect_switch_visibility()



def create_twist_chain(list_twist, end_target, axis="y", invert=False, invert_list_twist=False):
    if invert_list_twist:
        list_twist.reverse()

    for i in range(len(list_twist)):
        twist_transform = list_twist[i]
        node_md = cmds.createNode("multiplyDivide", n="md_{}".format(twist_transform))

        invert_value = 1 if invert is False else -1
        cmds.setAttr("{}.operation".format(node_md), 1)

        cmds.setAttr("{}.input1{}".format(node_md, axis.upper()), (1 / (len(list_twist) - 1)) * i * invert_value)
        cmds.connectAttr("{}.r{}".format(end_target, axis), "{}.input2{}".format(node_md, axis.upper()))
        cmds.connectAttr("{}.output{}".format(node_md, axis.upper()), "{}.r{}".format(twist_transform, axis))


def CreateBlendShape(bln_child=None, dup_crv=None, name="blinkHeight", attr_height=None):
    # duplicate target and create blendshape
    crv_target = cmds.duplicate(dup_crv, n="crv_" + name)[0]
    bln_child.append(crv_target)
    blendshape = cmds.blendShape(bln_child)[0]

    node_uc = cmds.shadingNode('unitConversion', au=1, n='uc_' + name)
    cmds.setAttr(node_uc + '.conversionFactor', 0.1)

    # create node and connect attr_height to blendshape
    rev_node = cmds.shadingNode('reverse', au=1, name='rev_' + name)
    cmds.connectAttr(attr_height, node_uc + '.input')
    cmds.connectAttr(node_uc + ".output", blendshape + '.weight[0]')
    cmds.connectAttr(node_uc + '.output', rev_node + '.input.inputX')
    cmds.connectAttr(rev_node + '.output.outputX', blendshape + '.weight[1]')

    return crv_target


def CreateWireCurve(crv_target, crv_control, name, zeroOffset=False):
    output = cmds.wire(crv_target, n=name, gw=0, en=1,
                       ce=0, li=0, w=crv_control)
    wr_node = output[0]

    if zeroOffset == True:
        cmds.setAttr(wr_node + '.scale[0]', 0)

    return wr_node


def cut(path, attr=False):
    if attr == True:
        if '.' in path:
            return path.split('.')[-1]
        else:
            return path
    elif attr == False:
        if '|' in path:
            return path.split('|')[-1]
        else:
            return path


def debug(text, isDebug=isDebug):
    if isDebug == 1:
        print(text)


def decomp_constraint(parent, object, r=True, t=True):
    node_decomp = cmds.createNode("decomposeMatrix", n="decomp")

    cmds.connectAttr(parent + ".worldMatrix[0]", node_decomp + ".inputMatrix")

    if r:
        cmds.connectAttr(node_decomp + ".outputRotate", object + ".r")
    if t:
        cmds.connectAttr(node_decomp + ".outputTranslate", object + ".t")


def del_neg(text):
    return text.replace("-", "").replace(" ", "")


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
        cmds.warning(f"Target '{target_name}' not found in blendShape node '{blendshape_node}'.")
        return False

    # Get the index of the target
    target_index = weight_attributes.index(target_name)

    # Remove the blendShape target input
    try:
        cmds.removeMultiInstance(f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}]", b=True)
        print(f"Successfully removed blendShape input for target '{target_name}'.")
    except RuntimeError as e:
        cmds.warning(f"Failed to remove target '{target_name}': {e}")
        return False

    print(f"Successfully deleted target '{target_name}' from blendShape node '{blendshape_node}'.")
    return True

def draw_curve(list_items, curve_name, parent=None, rebuild=True, d=3, s=5, rebuild_degree=3):
    list_bind_pos = [cmds.xform(pos, ws=1, t=1, q=1) for pos in list_items]
    cmds.curve(p=list_bind_pos, n=curve_name, d=d)

    if parent:
        cmds.parent(curve_name, parent)

    if rebuild:
        cmds.rebuildCurve(curve_name, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=s, d=rebuild_degree, tol=0)

    return curve_name


def draw_curve_circle(list_object, start_cv_index=0, name="curve"):
    circle_transform = cmds.circle(s=len(list_object), ch=0, n=name, d=1)[0]
    circle_shape = cmds.listRelatives(circle_transform, c=1, s=1)[0]

    cv_amount = cmds.getAttr(circle_shape + ".spans")

    print(cv_amount)

    # match cv position
    for i in range(cv_amount):
        pos = cmds.xform(list_object[i], q=1, t=1, ws=1)
        cmds.xform("{}.cv[{}]".format(circle_shape, i), t=pos, ws=1)

    # match last cv to the first cv
    pos = cmds.xform(list_object[0], q=1, t=1, ws=1)
    cmds.xform("{}.cv[{}]".format(circle_shape, cv_amount), t=pos, ws=1)

    return circle_transform



def draw_nurbs(joints, name="newSurface", rebuild=False, parent=None, loftDegree=1, d=1, sv=4, su=1, du=1, dv=1,
               size=3):
    '''This function create ribbon plane reference position from list of input
    '''

    # create curve along the input list
    curve1 = draw_curve(list_items=joints, curve_name="crv1", d=d, rebuild=False)
    curve2 = draw_curve(list_items=joints, curve_name="crv2", d=d, rebuild=False)

    for curve in [curve1, curve2]:
        if curve == curve1:
            move = size / 3
        elif curve == curve2:
            move = -(size / 3)
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


def drive_items_by_curve(list_items=None, parent=None, curve=None, name=None):
    # create pin groups
    list_grp_ctrl_joint = []
    list_grp_stick = []
    list_grp_pin = []

    for joint in list_items:
        joint_name = joint.replace(jnt + "_", "")

        grp_pin = cmds.group(em=1, n="pinDrv_{}_grp".format(joint_name), parent=parent)

        loc_ctrl = cmds.spaceLocator(n="drvCtrl_{}_loc".format(joint_name))[0]
        cmds.parent(loc_ctrl, grp_pin)

        grp_ctrl_joint = cmds.group(em=1, n="grp_driveJnt_{}".format(joint_name), p=loc_ctrl)
        grp_sticky_joint = cmds.group(em=1, n="grp_stickJnt_{}".format(joint_name), p=grp_ctrl_joint)
        grp_offset = cmds.group(em=1, n="grp_offsetJnt_{}".format(joint_name), p=grp_sticky_joint)

        cmds.matchTransform(grp_pin, joint)

        list_grp_stick.append(grp_sticky_joint)
        list_grp_pin.append(grp_pin)
        list_grp_ctrl_joint.append(grp_offset)

    # drive group by curves
    pin_curve_by_distance(list_grp_pin, curve)

    # applied group transform to list target
    for i in range(len(list_items)):
        cmds.parentConstraint(list_grp_ctrl_joint[i], list_items[i], mo=1)

    return grp_sticky_joint


def extract_vertices(vertex_range):
    # Use regex to parse the vertex string
    match = re.match(r"(.+)\.vtx\[(\d+):(\d+)\]", vertex_range)
    if not match:
        raise ValueError("Invalid vertex range format.")

    base_name = match.group(1)
    start_idx = int(match.group(2))
    end_idx = int(match.group(3))

    # Generate the list of individual vertices
    return [f"{base_name}.vtx[{i}]" for i in range(start_idx, end_idx + 1)]


# Example usage
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

    list_follicle_shape = cmds.listRelatives(local_rig_name, ad=1, typ="nurbsSurface", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(obj + ".v", 0)

    list_follicle_shape = cmds.listRelatives(local_rig_name, ad=1, typ="arcLengthDimension", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(obj + ".v", 0)

    list_follicle_shape = cmds.listRelatives(local_rig_name, ad=1, typ="ikHandle", f=1)
    if list_follicle_shape:
        for obj in list_follicle_shape:
            cmds.setAttr(obj + ".v", 0)

def flip_blendshape_target_by_name(blendshape_node, target_name, axis='x'):
    if axis not in ['x', 'y', 'z']:
        cmds.warning("Invalid axis. Use 'x', 'y', or 'z'.")
        return

    # Get the blendShape geometry
    blendshape_geo = cmds.listConnections(f"{blendshape_node}.outputGeometry[0]", source=False, destination=True)
    if not blendshape_geo:
        cmds.error("Unable to find blendshape geometry.")
        return

    # Ensure we have the actual shape node
    blendshape_geo = cmds.listRelatives(blendshape_geo[0], shapes=True, noIntermediate=True)
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
            target_index = int(all_targets[i + 1].split('[')[-1][:-1])
            break

    if target_index is None:
        cmds.error(f"Target '{target_name}' not found in blendShape node '{blendshape_node}'.")
        return

    # Duplicate and flip the target geometry
    flipped_target = cmds.duplicate(blendshape_geo, name=f"{blendshape_geo}_flipped")[0]

    # Flip the geometry along the specified axis
    axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
    scale_vector = [1, 1, 1]
    scale_vector[axis_index] = -1
    cmds.scale(scale_vector[0], scale_vector[1], scale_vector[2], flipped_target)
    cmds.makeIdentity(flipped_target, apply=True, scale=True)

    # Reassign flipped geometry as the new blendShape target
    cmds.blendShape(blendshape_node, edit=True, target=(blendshape_geo, target_index, flipped_target, 1.0))

    # Optional cleanup
    cmds.delete(flipped_target)

    print(f"Flipped blendshape target '{target_name}' along the {axis}-axis.")

def flip_curve(curve, flip_axis="x"):
    def odd_method():
        middle_index = (cv_amount // 2)

        list_first_block_pos = [cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=1, t=1) for i in range(middle_index)]
        value_middle = cmds.xform("{}.cv[{}]".format(curve_shape, middle_index), q=1, ws=1, t=1)
        list_second_block_pos = [cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=1, t=1) for i in range(middle_index + 1, cv_amount)]

        # debug
        print("odd method")
        print("len first block:", len(list_first_block_pos))
        print("len second block:", len(list_second_block_pos))

        for i, pos in enumerate(list_first_block_pos + [value_middle] + list_second_block_pos):
            print("cv [{}] : {} | {}".format(i, pos, cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=1, t=1)))

        # apply new value
        list_first_block_pos_new = list_second_block_pos[::-1]
        list_second_block_pos_new = list_first_block_pos[::-1]

        list_first_block_pos_new = [flip_position(pos) for pos in list_first_block_pos_new]
        value_middle = flip_position(value_middle)
        list_second_block_pos_new = [flip_position(pos) for pos in list_second_block_pos_new]

        for i, pos in enumerate(list_first_block_pos_new + [value_middle] + list_second_block_pos_new):
            cmds.xform("{}.cv[{}]".format(curve_shape, i), ws=1, t=pos)

    def even_method():
        middle_index = (cv_amount / 2)

        list_first_block_pos = [cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=1, t=1) for i in range(middle_index + 1)]
        list_second_block_pos = [cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=1, t=1) for i in range(middle_index + 1, cv_amount)]

        # debug
        print("even method")
        print("len first block:", len(list_first_block_pos))
        print("len second block:", len(list_second_block_pos))

        for i, pos in enumerate(list_first_block_pos + list_second_block_pos):
            print("cv [{}] : {} | {}".format(i, pos, cmds.xform("{}.cv[{}]".format(curve_shape, i), q=1, ws=1, t=1)))

        # apply new value
        list_first_block_pos_new = list_second_block_pos[::-1]
        list_second_block_pos_new = list_first_block_pos[::-1]

        list_first_block_pos_new = [flip_position(pos) for pos in list_first_block_pos_new]
        list_second_block_pos_new = [flip_position(pos) for pos in list_second_block_pos_new]

        for i, pos in enumerate(list_first_block_pos_new + list_second_block_pos_new):
            cmds.xform("{}.cv[{}]".format(curve_shape, i), ws=1, t=pos)

    def flip_position(position):
        if flip_axis == "x":
            return [position[0] * -1, position[1], position[2]]
        elif flip_axis == "y":
            return [position[0], position[1] * -1, position[2]]
        elif flip_axis == "z":
            return [position[0], position[1], position[2] * -1]

    # prepare
    curve_shape = cmds.listRelatives(curve, c=1, s=1, typ="nurbsCurve")

    if curve_shape:
        curve_shape = curve_shape[0]
    else:
        return None

    cv_amount = cmds.getAttr(f"{curve_shape}.spans") + cmds.getAttr(f"{curve_shape}.degree")

    # check is curve is odd
    if cv_amount % 2 != 0:
        odd_method()
    else:
        even_method()


def flip_keyword(input, ignore=False):
    # error handle
    if type(input) is not str:
        return input

    keywords = [L, R]

    if keywords[0] in input:
        return input.replace(keywords[0], keywords[1])
    elif keywords[1] in input:
        return input.replace(keywords[1], keywords[0])
    elif ignore is True:
        return input
    elif ignore is False:
        raise Exception("Can not find the opposite side of {}, Please Make Sure the side keyword must be {} (Left) or {} (Right).".format(input,L,R))


def freeze_group(selection, prefix="grp", matchGimbal=True, add=None, float=False, match_object=None):
    if not selection:
        raise Exception("No Input Given.")
    elif type(selection) is str:
        selection = [selection]

    freeze_groups = []

    for obj in selection:
        # Create a new group with a specific naming convention
        index = obj.index("_")
        grp_freeze_name = prefix + obj[index:]
        grp_freeze_name = grp_freeze_name + add.capitalize() if add else grp_freeze_name  # add mode

        grp_freeze = cmds.group(em=True, n=grp_freeze_name)

        # parent freeze group under obj parent
        parent_obj = cmds.listRelatives(obj, p=1, f=1)
        cmds.parent(grp_freeze, parent_obj[0]) if parent_obj else None  # parent to its parent

        # match gimbal case
        if matchGimbal:
            try:
                cmds.setAttr(grp_freeze + ".rotateOrder", cmds.getAttr(obj + ".rotateOrder"))
            except:
                pass

        # Match the group's transforms to the object
        if match_object:
            cmds.matchTransform(grp_freeze, match_object)
        else:
            cmds.matchTransform(grp_freeze, obj)

        # Parent the object under the freeze group
        if not float:
            cmds.parent(obj, grp_freeze)

        freeze_groups.append(grp_freeze)

    return freeze_groups


def freeze_group_classic(selection, typ=grp, match_rotate_order=True, match_object=None, rename=None):
    """
    match_object : Match to given object name

    """
    def get_offset_group_name(object):
        # detect type in selection
        replace_type = None
        for word in object.split("_"):
            if word in list_type:
                replace_type = word
                break

        # Create a new group with a specific naming convention
        if rename: # rename case
            grp_freeze_name = rename
        elif replace_type: # auto replace case
            grp_freeze_name = object.replace(replace_type,typ)
        else: # append case
            grp_freeze_name = "{}_{}".format(obj, typ)

        # check word in scene
        if cmds.objExists(grp_freeze_name):
            raise Exception("Freeze Group Output Name \"{}\" already exist in the scene, please change to others typ".format(grp_freeze_name))

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
        reset_all_transform(grp_freeze)
        cmds.parent(grp_freeze, w=1)

    if not selection:
        raise Exception("No Input Given.")
    elif type(selection) is str:
        selection = [selection]

    list_output_offset_group = []

    for obj in selection:
        grp_freeze = cmds.group(em=True, n=get_offset_group_name(object=obj))

        match_rotate_order_func() # match rotate order
        match_object_func() # match position , rotate and scale

        # parent freeze group under obj parent
        parent_obj = cmds.listRelatives(obj, p=1, f=1)
        cmds.parent(grp_freeze, parent_obj[0]) if parent_obj else None  # parent to its parent

        # Parent the object under the freeze group
        cmds.parent(obj, grp_freeze)

        list_output_offset_group.append(grp_freeze)

    return list_output_offset_group


def get_axis_double3(input, minusValue=True,invert=False):
    list_return = [0, 0, 0]
    list_axis_ref = ["x", "y", "z"]
    list_axis_ref_minus = ["-x", "-y", "-z"]

    dict_axis = {"x": (1, 0, 0),
                 "y": (0, 1, 0),
                 "z": (0, 0, 1),
                 "-x": (-1, 0, 0),
                 "-y": (0, -1, 0),
                 "-z": (0, 0, -1)}


    if input not in dict_axis.keys():
        raise Exception("Invalid Input")

    output = dict_axis[input]

    if invert:
        output = [value*-1 for value in output]

    return output


def get_blendshape_target_data_as_list(blendshape_node, target_name):
    if not cmds.objExists(blendshape_node):
        cmds.warning(f"BlendShape node '{blendshape_node}' does not exist.")
        return None

    weight_attrs = cmds.listAttr(f"{blendshape_node}.weight", m=True)
    if not weight_attrs or target_name not in weight_attrs:
        cmds.warning(f"Target '{target_name}' not found in blendShape node '{blendshape_node}'.")
        return None

    target_index = weight_attrs.index(target_name)

    # Get base geometry
    base_geo = cmds.listConnections(f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem[6000].inputGeomTarget", s=True, d=False)
    if base_geo:
        base_geo = base_geo[0]
    else:
        base_geo = None

    # Get target object
    target_obj = cmds.listConnections(f"{blendshape_node}.inputTarget[0].inputTargetGroup[{target_index}].inputTargetItem[6000].inputGeomTarget", s=True, d=False)
    if target_obj:
        target_obj = target_obj[0]
    else:
        target_obj = None

    # Get weight value
    weight_value = cmds.getAttr(f"{blendshape_node}.weight[{target_index}]")

    return [base_geo, target_index, target_obj, weight_value]

def get_curve_position(amount, curve):
    list_position = []
    list_poc = []
    curve_transform = curve
    curve_shape = cmds.listRelatives(
        curve_transform, c=1, s=1, typ="nurbsCurve")[0]

    if "crv_" in curve_transform:
        main_name = curve_transform.replace("crv_", "")
    else:
        main_name = curve_transform

    for i in range(amount):
        node = cmds.shadingNode("pointOnCurveInfo", au=1,
                                n="poc_" + main_name + "_tmp_" + str(i + 1).zfill(2))

        if amount == 1:
            param = 0.5
        else:
            param = i * (1 / (amount - 1))

        cmds.connectAttr(curve_shape + ".worldSpace[0]", node + ".inputCurve")
        cmds.setAttr(node + ".parameter", param)
        cmds.setAttr(node + ".turnOnPercentage", 1)

        list_poc.append(node)
        list_position.append(cmds.getAttr(node + ".position")[0])

    cmds.delete(list_poc)

    return list_position




def get_distance_two(*args, world=True):
    list_object = []

    for arg in args:
        if type(arg) is str:
            list_object.append(arg)
        elif type(arg) is tuple:
            list_object += list(arg)
        elif type(arg) is list:
            list_object += arg
        else:
            raise Exception(arg + ": get distance function error input")

    distance = 0.0
    for i in range(1, len(list_object)):
        # query coordinates
        if world is True:
            ws = 1
            os = 0
        elif world is False:
            ws = 0
            os = 1

        posA = cmds.xform(list_object[i - 1], ws=ws, os=os, t=1, q=1)
        posB = cmds.xform(list_object[i], ws=ws, os=os, t=1, q=1)

        distance += (math.sqrt(((posA[0] - posB[0]) ** 2) + ((posA[1] - posB[1]) ** 2) + ((posA[2] - posB[2]) ** 2)))

    return distance


def get_exist_axis(*argv):
    list_axis = ["x", "y", "z"]
    list_argv = [arg.replace("-", "") if "-" in arg else arg for arg in argv]

    list_output = list(set(list_axis).difference(set(list_argv)))

    if len(list_output) != 1:
        raise Exception("Cannot find exist axis : {}".format(list_output))
    else:
        return list_axis[0]


def get_nearest_param(curve, object, typ="curve"):
    if typ == "curve":
        # get parameter
        npc = cmds.createNode("nearestPointOnCurve")
        decomp = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(curve + ".worldSpace[0]", npc + ".inputCurve")
        cmds.connectAttr(object + ".worldMatrix[0]", decomp + ".inputMatrix")
        cmds.connectAttr(decomp + ".outputTranslate", npc + ".inPosition")

        param = cmds.getAttr(npc + ".parameter")
        cmds.delete(npc, decomp)

    elif typ == "surface":
        # get parameter
        node_closest = cmds.createNode("closestPointOnSurface")
        decomp = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(curve + ".worldSpace[0]", node_closest + ".inputSurface")

        cmds.connectAttr(object + ".worldMatrix[0]", decomp + ".inputMatrix")
        cmds.connectAttr(decomp + ".outputTranslate", node_closest + ".inPosition")

        param = [cmds.getAttr(node_closest + ".parameterU"), cmds.getAttr(node_closest + ".parameterV")]
        cmds.delete(node_closest, decomp)

    return param


def get_new_name(name, typ=None, replace=True):
    """
    {ModuleName}_{ObjectName}_{Position}
    """
    list_typ = [ctrl,jnt,loc,grp,crv]
    new_name = name

    # update type
    if typ:
        for keyword in list_typ:
            if keyword in new_name:
                new_name = new_name.replace(keyword,typ)

    # update name

    return new_name


def get_rgb_from_index(index):
    """
    Get the RGB color corresponding to a Maya index color.

    :param index: Index color value (integer between 0 and 31).
    :return: A tuple of (R, G, B) values in the range [0, 1].
    :raises ValueError: If the index is not between 0 and 31.
    """
    index_to_rgb = {
        0: (0.0, 0.0, 0.0),
        1: (0.247, 0.247, 0.247),
        2: (0.498, 0.498, 0.498),
        3: (0.608, 0.0, 0.157),
        4: (0.0, 0.016, 0.373),
        5: (0.0, 0.0, 0.561),
        6: (0.0, 0.275, 0.094),
        7: (0.145, 0.0, 0.263),
        8: (0.780, 0.0, 0.780),
        9: (0.537, 0.278, 0.2),
        10: (0.243, 0.133, 0.122),
        11: (0.600, 0.145, 0.0),
        12: (0.392, 0.216, 0.0),
        13: (0.263, 0.275, 0.0),
        14: (0.0, 0.467, 0.0),
        15: (0.0, 0.275, 0.392),
        16: (0.0, 0.18, 0.537),
        17: (0.0, 0.0, 0.612),
        18: (0.216, 0.0, 0.6),
        19: (0.475, 0.0, 0.537),
        20: (0.6, 0.0, 0.325),
        21: (0.627, 0.275, 0.216),
        22: (0.62, 0.51, 0.216),
        23: (0.0, 0.58, 0.0),
        24: (0.255, 0.6, 0.459),
        25: (0.0, 0.6, 0.6),
        26: (0.0, 0.4, 0.6),
        27: (0.325, 0.475, 0.6),
        28: (0.537, 0.537, 0.6),
        29: (0.6, 0.6, 0.6),
        30: (0.784, 0.784, 0.784),
        31: (1.0, 1.0, 1.0),
    }

    if index not in index_to_rgb:
        raise ValueError("Index must be an integer between 0 and 31.")

    return index_to_rgb[index]


def get_single_axis_enum():
    return ["X","Y","Z","-X","-Y","-Z"]

def get_single_axis_enum_pos():
    return ["X","Y","Z"]

def get_triple_axis_enum():
    return ["xyz","xzy","yxz","yzx","zyx","zxy"]

def get_tuple_axis(direction: str):
    # Define a mapping from input string to the corresponding tuple
    direction_map = {
        "x": (1, 0, 0),
        "y": (0, 1, 0),
        "z": (0, 0, 1),
        "-x": (-1, 0, 0),
        "-y": (0, -1, 0),
        "-z": (0, 0, -1),
        # Add more mappings here based on your needs
    }

    # Return the tuple corresponding to the input, or None if the input is not valid
    return direction_map.get(direction, None)



def import_weight(node_bind, xml_path):
    if "/" in xml_path:
        syntax = "/"
    elif "\\" in xml_path:
        syntax = "\\"
    else:
        raise Exception("Invalid Import Weight Path , Not Found / , or \\")
    file_name = xml_path.split(syntax)[-1]
    file_path = xml_path.replace(syntax + file_name, "")

    cmds.deformerWeights(file_name, im=1, method="index", deformer=node_bind,
                         path=file_path)


def insert_joint(list_joint, count, typ=0, rename=None):
    list_return = []

    for parent in list_joint:
        recent_jnt = None

        pos_parent = cmds.xform(parent, t=1, ws=1, q=1)
        rad_parent = cmds.getAttr(parent + '.radius')

        child = cmds.listRelatives(parent, typ="joint", c=1)[0]
        pos_child = cmds.xform(child, t=1, ws=1, q=1)

        for i in range(count):
            tmp_crv = cmds.curve(d=1, p=[pos_parent, pos_child])
            poc = cmds.createNode('pointOnCurveInfo')
            cmds.connectAttr(
                tmp_crv + '.worldSpace[0]', poc + '.inputCurve', force=True)

            cmds.select(cl=1)
            jnt = cmds.joint(n=cut(parent) + "_twist_" + str(i + 1).zfill(2))

            list_return.append(jnt)
            cmds.setAttr(jnt + '.radius', rad_parent)

            cmds.connectAttr(poc + '.position', jnt + '.translate', force=True)
            param = (1 / (count + 1)) * (i + 1)
            cmds.setAttr(poc + '.parameter', param)

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


def is_child_of(child_name, parent_name):
    """
    Checks if a given object is a child of another specified object.

    Parameters:
        child_name (str): The name of the potential child object.
        parent_name (str): The name of the potential parent object.

    Returns:
        bool: True if `child_name` is a child of `parent_name`, otherwise False.
    """
    if not cmds.objExists(child_name):
        print(f"Object '{child_name}' does not exist.")
        return False

    if not cmds.objExists(parent_name):
        print(f"Object '{parent_name}' does not exist.")
        return False

    # Get the full hierarchy of the parent
    all_descendants = cmds.listRelatives(parent_name, allDescendents=True, fullPath=True) or []

    # Check if the child is in the hierarchy
    child_full_path = cmds.ls(child_name, long=True)
    if child_full_path and child_full_path[0] in all_descendants:
        return True

    return False

def is_descendant_of(descendant_name, ancestor_name):
    """
    Checks if a given object is any descendant (child, grandchild, etc.) of another specified object.

    Parameters:
        descendant_name (str): The name of the potential descendant object.
        ancestor_name (str): The name of the potential ancestor object.

    Returns:
        bool: True if `descendant_name` is a descendant of `ancestor_name`, otherwise False.
    """
    if not cmds.objExists(descendant_name):
        print(f"Object '{descendant_name}' does not exist.")
        return False

    if not cmds.objExists(ancestor_name):
        print(f"Object '{ancestor_name}' does not exist.")
        return False

    # Get the full hierarchy of the ancestor
    all_descendants = cmds.listRelatives(ancestor_name, allDescendents=True, fullPath=True) or []

    # Check if the descendant is in the hierarchy
    descendant_full_path = cmds.ls(descendant_name, long=True)
    if descendant_full_path and descendant_full_path[0] in all_descendants:
        return True

    return False




def match_bounding_box(source, target):
    if not cmds.objExists(source) or not cmds.objExists(target):
        raise ValueError("Source or target object does not exist")

    # Get the bounding box of the source object
    source_bbox = cmds.exactWorldBoundingBox(source)
    source_width = source_bbox[3] - source_bbox[0]
    source_height = source_bbox[4] - source_bbox[1]
    source_depth = source_bbox[5] - source_bbox[2]

    # Get the bounding box of the target object
    target_bbox = cmds.exactWorldBoundingBox(target)
    target_width = target_bbox[3] - target_bbox[0]
    target_height = target_bbox[4] - target_bbox[1]
    target_depth = target_bbox[5] - target_bbox[2]

    # Calculate the scale factors
    scale_x = target_width / source_width if source_width != 0 else 1
    scale_y = target_height / source_height if source_height != 0 else 1
    scale_z = target_depth / source_depth if source_depth != 0 else 1

    # Apply the scale factors to the source object
    cmds.scale(scale_x, scale_y, scale_z, source, absolute=True)


def match_parent(target, parent):
    # cmds.matchTransform(target, parent)
    matchAllTransform(target, parent)
    cmds.parent(target, parent)


def matchAllTransformOnly(source,match):
    child_source = cmds.listRelatives(match,c=1)

    if child_source:
        cmds.parent(child_source,w=1)

    matchAllTransform(source,match)

    if child_source:
        cmds.parent(child_source,source)


def matchAllTransform(target_object, match_object):
    matchTransform(target_object,match_object,pos=True,rot=True,scl=True)


def matchTransform(source, match, pos=False, rot=False, scl=False):
    # error handle
    if type(source) != str or type(match) != str:
        raise Exception("Invalid Input ,Must be string , get source {} , get match {}".format(source,match))

    grp_tmp = cmds.group(em=1)

    cmds.parent(grp_tmp, match)

    if cmds.objectType(source,isa="joint") and rot:
        cmds.setAttr("{}.jointOrient".format(source),0,0,0,typ="double3")

    reset_all_transform(grp_tmp)

    source_parent = cmds.listRelatives(source, p=1)
    if source_parent:
        cmds.parent(grp_tmp, source_parent[0])
    else:
        cmds.parent(grp_tmp, w=1)

    if pos:
        output_vector = cmds.getAttr(grp_tmp + ".t")[0]
        cmds.setAttr(source + ".t", output_vector[0], output_vector[1], output_vector[2], typ="double3")
    if rot:
        output_vector = cmds.getAttr(grp_tmp + ".r")[0]
        cmds.setAttr(source + ".r", output_vector[0], output_vector[1], output_vector[2], typ="double3")
    if scl:
        output_vector = cmds.getAttr(grp_tmp + ".s")[0]
        cmds.setAttr(source + ".s", output_vector[0], output_vector[1], output_vector[2], typ="double3")

    cmds.delete(grp_tmp)

def mirror_blendshape(axis="x"):
    if axis == "x":
        mirror_index = 0
    elif axis == "y":
        mirror_index = 1
    elif axis == "z":
        mirror_index = 2

    for source in cmds.ls(sl=1):
        if cmds.objExists(source.replace(L, R)) and L in source:
            bshp_opposite = source.replace(L, R)
        elif cmds.objExists(source.replace(R, L)) and R in source:
            bshp_opposite = source.replace(R, L)

        amount_cv_source = cmds.getAttr(source + ".spans") + cmds.getAttr(source + ".degree")
        amount_cv_opposite = cmds.getAttr(bshp_opposite + ".spans") + cmds.getAttr(bshp_opposite + ".degree")

        for i in range(amount_cv_source):
            source_cv = i
            opposite_cv = (amount_cv_source - 1) - i

            pos_cv_source = cmds.xform("{}.cv[{}]".format(source, source_cv), os=1, q=1, t=1)

            pos_cv_source[mirror_index] = pos_cv_source[mirror_index] * -1

            cmds.xform("{}.cv[{}]".format(bshp_opposite, opposite_cv), os=1, t=pos_cv_source)



def pin_curve_by_distance(list_pin, source, maintainOffset=False, name=None, parent=None,
                        constraint="parent"):

    def create_offset_group(index):
        grp_offset = cmds.group(em=1, n="{}Pin{}_{}".format(name, str(index).zfill(2), grp))
        if parent:
            cmds.parent(grp_offset, parent)

        return grp_offset

    source_shape = cmds.listRelatives(source, c=1, s=1, f=1)[0]
    list_maintainOffset = []

    for i, object in enumerate(list_pin):
        if maintainOffset:
            target = create_offset_group(index=i + 1)
            list_maintainOffset.append(target)
        else:
            target = object

        # get nearest param
        param = get_nearest_param(curve=source, object=object, typ="curve")

        # connect position to target
        poc = cmds.createNode("pointOnCurveInfo", n="{}_pin_poc".format(name))
        cmds.connectAttr(source_shape + ".worldSpace[0]", poc + ".inputCurve")
        cmds.setAttr(poc + ".parameter", param)
        cmds.connectAttr(poc + ".position", target + ".translate")


    if maintainOffset:
        return list_maintainOffset

def pin_ribbon(list_pin=None, surface=None, output_parent=None, name="Follicles"):
    """Return list of pin value reference distance from input pin"""

    # handling error
    if not surface:
        raise Exception("Surface Input not correct")
    if not cmds.objExists(surface):
        raise Exception("Not found surface in scene")
    if not output_parent:
        raise Exception("output_parent not correct")
    if not cmds.objExists(output_parent):
        raise Exception("not found output parent in scene")

    if cmds.objectType(surface, isa="transform"):  # get shape of surface
        list_shape = cmds.listRelatives(surface, c=1, s=1, typ="nurbsSurface")
        if not list_shape:
            raise Exception("not found nurbs surface in input surface")
        else:
            surface_shape = list_shape[0]
            surface_transform = surface

    elif cmds.objectType(surface, isa="nurbsSurface"):
        surface_transform = cmds.listRelatives(surface, p=1, typ="nurbsSurface")[0]
        surface_shape = surface

    index = 1
    list_follicles = []

    for i, object in enumerate(list_pin):

        if len(list_pin) == 1:
            follicle_transform_name = name
            follicle_shape_name = name + "Shape"
        else:
            follicle_transform_name = "{}_pin{}_flc".format(name, i + 1)
            follicle_shape_name = "{}_pin{}_flcShape".format(name, i + 1)

        # create follicle node and connect to surface
        follicle_shape = cmds.createNode("follicle", n=follicle_shape_name)
        follicle_transform = cmds.listRelatives(follicle_shape, p=1, typ="transform")[0]
        cmds.parent(follicle_transform, output_parent)

        cmds.connectAttr("{}.local".format(surface_shape), "{}.inputSurface".format(follicle_shape))
        cmds.connectAttr("{}.worldMatrix[0]".format(surface_shape), "{}.inputWorldMatrix".format(follicle_shape))

        cmds.connectAttr("{}.outRotate".format(follicle_shape), "{}.r".format(follicle_transform))
        cmds.connectAttr("{}.outTranslate".format(follicle_shape), "{}.t".format(follicle_transform))

        # set param value
        cmds.setAttr("{}.v".format(follicle_shape), 0)
        param = get_nearest_param(surface, object, typ="surface")
        cmds.setAttr("{}.parameterU".format(follicle_shape), param[0])
        cmds.setAttr("{}.parameterV".format(follicle_shape), param[1])

        list_follicles.append(follicle_transform)
        cmds.rename(follicle_transform, follicle_transform_name)

    return list_follicles


def pin_ribbon_by_distance(list_pin, source, maintainOffset=False, name=None, parent=None,
                    constraint="parent"):
    def create_offset_group(index):
        grp_offset = cmds.group(em=1, n="{}Pin{}_{}".format(name, str(index).zfill(2), grp))
        if parent:
            cmds.parent(grp_offset, parent)

        return grp_offset

    source_shape = cmds.listRelatives(source, c=1, s=1, f=1)[0]
    list_maintainOffset = []

    cmds.select(source)
    cmds.UVPin()
    node_uvpin = cmds.rename("uvPin1", "{}_uvPin".format(name))
    index = 1

    for i, object in enumerate(list_pin):
        if maintainOffset:
            target = create_offset_group(index=i + 1)
            list_maintainOffset.append(target)
        else:
            target = object

        # setup uv pin
        param = get_nearest_param(source, object, typ="surface")
        cmds.setAttr("{}.coordinate[{}].coordinateU".format(node_uvpin, i), param[0])
        cmds.setAttr("{}.coordinate[{}].coordinateV".format(node_uvpin, i), param[1])
        cmds.setAttr("{}.normalizedIsoParms".format(node_uvpin), 0)

        cmds.connectAttr("{}.outputMatrix[{}]".format(node_uvpin, i), target + ".offsetParentMatrix",
                         f=1)
        reset_all_transform(target)

        if maintainOffset:
            if constraint == "parent":
                cmds.parentConstraint(target, object, mo=1)
            elif constraint == "point":
                cmds.pointConstraint(target, object, mo=1)
            elif constraint == "orient":
                cmds.orientConstraint(target, object, mo=1)
            elif constraint is None:
                pass
        index += 1

    if maintainOffset:
        return list_maintainOffset



def pin_ribbon_by_patch(ribbon, list_pin, parent):
    param_factor = 1 / (len(list_pin) - 1)
    for i, pin in enumerate(list_pin):
        node = cmds.createNode("follicle")

        cmds.setAttr(node + ".parameterV", param_factor * (i))
        cmds.setAttr(node + ".parameterU", 0.5)

        cmds.connectAttr(ribbon + ".local", node + ".inputSurface")
        cmds.connectAttr(ribbon + ".worldMatrix[0]", node + ".inputWorldMatrix")
        cmds.connectAttr(node + ".outRotate", pin + ".rotate")
        cmds.connectAttr(node + ".outTranslate", pin + ".translate")

        cmds.parent(cmds.listRelatives(node, p=1, typ="transform")[0], parent)


def rename_shape_proper(control):
    list_shape = cmds.listRelatives(control, c=1, s=1, typ="nurbsCurve", f=1)
    for i, shape in enumerate(list_shape):
        cmds.rename(shape, "{}Shape".format(cut(control)))


def reset_all_transform(object,pos=True,rot=True,scl=True):
    list_axis = []
    list_axis_scl = ["sx", "sy", "sz"]

    if pos:
        list_axis += ["tx","ty","tz"]
    if rot:
        list_axis += ["rx","ry","rz"]
    if scl:
        list_axis += list_axis_scl



    for i, attr in enumerate(list_axis):
        if attr in list_axis_scl:
            reset_value = 1
        else:
            reset_value = 0

        if cmds.getAttr(object + "." + attr, se=1):
            cmds.setAttr(object + "." + attr, reset_value)



def returnRivet():
    cmds.Rivet()
    uvPinOut = cmds.ls(sl=True, l=1)
    uvPin = uvPinOut.pop(0)
    return [uvPin, uvPinOut]


def ribbon_plane(name, ref, faxis='y', sub=5, drv=3, snap=0):
    """ Create a ribbon plane which have follicles attach along surface and was bind skin by driver joint

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
        node_distance = cmds.createNode('distanceBetween')
        cmds.connectAttr(ref[i] + '.worldMatrix[0]', node_distance + '.inMatrix1')
        cmds.connectAttr(ref[i + 1] + '.worldMatrix[0]',
                         node_distance + '.inMatrix2')
        width += (cmds.getAttr(node_distance + '.distance'))
        cmds.delete(node_distance)

    # create ribbon plane
    nrb_shape = cmds.listRelatives(cmds.nurbsPlane(
        n='nrb_' + name + '_ribbon', ax=(0, 0, 1), w=width, lr=0.05, u=sub - 1, v=1, ch=0), c=1)[0]

    # create follicles
    list_flc = []
    for i in range(1, sub + 1):
        flc_shape = cmds.createNode("follicle", n=f"flc_{name}_shape_{i}")
        cmds.setAttr(flc_shape + '.simulationMethod', 0)
        cmds.setAttr(flc_shape + '.parameterV', 0.5)

        value = 1 / (sub - 1)
        cmds.setAttr(flc_shape + '.parameterU', value * (i - 1))
        cmds.connectAttr(nrb_shape + '.local', flc_shape + '.inputSurface')
        cmds.connectAttr(
            nrb_shape + '.worldMatrix[0]', flc_shape + '.inputWorldMatrix')

        flc_transform = cmds.rename(cmds.listRelatives(
            flc_shape, p=1, f=1)[0], f"flc_{name}_{i}")
        cmds.connectAttr(flc_shape + '.outRotate', flc_transform + '.rotate')
        cmds.connectAttr(flc_shape + '.outTranslate', flc_transform + '.translate')
        list_flc.append(flc_transform)

    # create joint sub
    list_jntSub = []
    for i in range(sub):
        # create sub joint
        jntSub = cmds.joint(n=f'jnt_sub_{name}_ribbon_{i + 1}', rad=0.5)
        cmds.matchTransform(jntSub, list_flc[i], pos=1, rot=0, scl=0)
        list_jntSub.append(jntSub)

    if faxis == 'x':
        oj = 'xyz'
    elif faxis == 'y':
        oj = 'yxz'
    elif faxis == 'z':
        oj = 'zyx'

    # orient joint and separate joint
    cmds.joint(list_jntSub[0], e=1, oj=oj, sao='xup', ch=1, zso=1)
    cmds.joint(list_jntSub[-1], e=1, oj='none', ch=1, zso=1)

    for i in range(sub):
        cmds.parent(list_jntSub[i], list_flc[i])

    # move all bind joint to follicles group
    grp_flc = cmds.group(em=1, n=f'grp_flc_{name}')
    for i in range(sub):
        cmds.parent(list_flc[i], grp_flc)

    # create drv joints
    grp_drv = cmds.group(em=1, n=f'grp_jntDrv_{name}')
    offset = cmds.xform(list_jntSub[0], q=1, ws=1, t=1)[0]
    debug('offset :', offset)
    list_jntDrv = []

    for i in range(drv):
        debug(i)
        drv_value = (i * (width / (drv - 1))) + offset
        cmds.select(cl=1)
        jntDrv = cmds.joint(n=f'jnt_drv_{name}_ribbon_{i + 1}')
        cmds.matchTransform(jntDrv, list_jntSub[0], rot=1)
        cmds.setAttr(jntDrv + '.radius', cmds.getAttr(jntSub + '.radius') * 3)
        cmds.setAttr(jntDrv + '.translateX', drv_value)
        cmds.parent(jntDrv, grp_drv)
        list_jntDrv.append(jntDrv)

    # bind skin to nurb
    cmds.skinCluster(nrb_shape, list_jntDrv, ih=1, mi=2,
                     n=f'skinCluster_{name}_ribbon')

    if snap == 1 and drv == len(ref):
        for i in range(drv):
            cmds.matchTransform(list_jntDrv[i], ref[i])

    # snap division method
    elif (len(ref) * 2) - 1 == drv:
        debug("division method verified")
        count = 0
        for i in range(drv):
            # divide case
            if (i + 1) % 2 == 0:
                debug(
                    f"count {i} : {list_jntDrv[i]} / divide :: {ref[count - 1]} ,{ref[count]} ")
                rot = cmds.xform(ref[count - 1], q=1, ws=1, ro=1)
                pos1 = cmds.xform(ref[count - 1], q=1, ws=1, t=1)
                pos2 = cmds.xform(ref[count], q=1, ws=1, t=1)

                avg_pos = [0, 0, 0]
                debug(f"{ref[count - 1]}:{pos1},{ref[count]}:{pos2}")
                for axis in range(3):
                    avg_pos[axis] = (pos1[axis] + pos2[axis]) / 2
                    debug(f" {pos1[axis]},{pos2[axis]} sum : {avg_pos[axis]}")

                cmds.xform(list_jntDrv[i], ws=1, t=avg_pos, ro=rot)

            # point case
            else:
                debug(f"count {i} : {list_jntDrv[i]} / main :: {ref[count]}")
                cmds.matchTransform(list_jntDrv[i], ref[count])
                count += 1

    return list_jntSub, list_jntDrv, nrb_shape, list_flc

def lock_attributes(transform: str = "transform_name", r: int = 0, s: int = 0, t: int = 0, v: int = 0, l: int = 1, k=None):
    if not cmds.objExists(transform):
        return

    if l == 0:
        l=0
        k=1
    else:
        l=1
        k=0

    if r:
        [cmds.setAttr("{}.{}".format(transform, attr), k=k, l=l) for attr in ("rx", "ry", "rz")]
    if t:
        [cmds.setAttr("{}.{}".format(transform, attr), k=k, l=l) for attr in ("tx", "ty", "tz")]
    if s:
        [cmds.setAttr("{}.{}".format(transform, attr), k=k, l=l) for attr in ("sx", "sy", "sz")]
    if v:
        cmds.setAttr("{}.v".format(transform), k=k, l=l)


def set_blend_shape_expression(node_name,
                               mesh_target,
                               mesh_base,
                               driver_value,
                               driver_attr,
                               clamp_length=[0, 1],
                               module_name="SetDriven"):
    # add new attribute
    add_or_create_blend_shape_node(list_target_mesh=[mesh_target],  node_name=node_name)

    set_driver_node_fixed(attr_driver=driver_attr,
                          attr_driven=node_name + "." + mesh_target,
                          driven_value=1 / driver_value,
                          name=module_name,
                          clamp_length=clamp_length,
                          driven_value_is_fixed=True)


def set_blend_shape_expression_multi(node_name,
                                     list_mesh_target,
                                     mesh_base,
                                     driver_attr_up,
                                     driver_attr_out,
                                     clamp_length=[0, 1],
                                     name_tag="SetDriven",
                                     in_out_driver_value=[-1, 1],
                                     up_down_driver_value=[1, -1]):
    # add new attribute
    add_or_create_blend_shape_node(list_target_mesh=list_mesh_target, base_mesh=mesh_base, node_name=node_name)

    # # set connection ----------------
    # set_driver_node_fixed(attr_driver=driver_attr,
    #                       attr_driven=node_name + "." + mesh_target,
    #                       driven_value=1 / driver_value,
    #                       name=module_name,
    #                       clamp_length=clamp_length,
    #                       driven_value_is_fixed=True)


def set_driver_blend_shape_single(input_attr=None,
                                  driver_value=3,
                                  output_attr=None,
                                  clamp=False,
                                  name_tag="setDriverBlendShape",
                                  driven_value = 1):
    factor = driven_value / driver_value

    node_mdl = cmds.createNode("multDoubleLinear", n="{}_set_blend_shape_mdl".format(name_tag))
    cmds.connectAttr(input_attr, "{}.input2".format(node_mdl))
    cmds.setAttr("{}.input1".format(node_mdl), factor)

    # is clamp
    if clamp:
        node_clamp = cmds.createNode("clamp", n="{}_set_blend_shape_cmp".format(name_tag))
        cmds.connectAttr(node_mdl + ".output", node_clamp + ".inputR")
        cmds.setAttr(node_clamp + ".minR", 0)
        cmds.setAttr(node_clamp + ".maxR", 1)
        cmds.connectAttr(node_clamp + ".outputR", output_attr)
    else:
        cmds.connectAttr(node_mdl + ".output", output_attr)


def set_driver_blend_shape_v2(transform_name,
                              list_axis_up_out=["y", "x"],
                              name_tag="setDriver"):
    """
    @param transform_name:
    @type transform_name:
    @param list_axis_up_out:
    @type list_axis_up_out:
    @param name_tag:
    @type name_tag:
    @param list_attr_output: list of up, down,in,out,upOut,upIn,downOut,downIn output attr
    @type list_attr_output:
    @return:
    @rtype:
    """

    def get_output_between(attr_A, attr_B):
        node_mdl = cmds.createNode("multDoubleLinear", n="{}_avg_md".format(name_tag))
        cmds.connectAttr(attr_A, node_mdl + ".input1")
        cmds.connectAttr(attr_B, node_mdl + ".input2")
        return node_mdl + ".output"

    def get_normalize_output(attr_A, attr_B, attr_target):
        # normalize attr direct
        node_adl_normalized = cmds.createNode("addDoubleLinear", n="{}_normalize_weight_adl".format(name_tag))
        cmds.connectAttr(attr_A, node_adl_normalized + ".input1")
        cmds.connectAttr(attr_B, node_adl_normalized + ".input2")

        node_pma_subtract = cmds.createNode("plusMinusAverage", n="{}_normalize_offset_pma".format(name_tag))
        cmds.setAttr(node_pma_subtract + ".operation", 2)
        cmds.connectAttr(attr_target, node_pma_subtract + ".input1D[0]")
        cmds.connectAttr(node_adl_normalized + ".output", node_pma_subtract + ".input1D[1]")

        return node_pma_subtract + ".output1D"

    axis_up, axis_out = list_axis_up_out

    # create attr input
    node_sr_range_positive = cmds.createNode("setRange", n="{}_posClamp_sr".format(name_tag))

    for axis in list_axis_up_out:
        cmds.connectAttr("{}.t{}".format(transform_name, axis), "{}.value{}".format(node_sr_range_positive, axis.upper()))

        cmds.setAttr("{}.oldMin{}".format(node_sr_range_positive, axis.upper()), 0)
        cmds.setAttr("{}.oldMax{}".format(node_sr_range_positive, axis.upper()), 1)

        cmds.setAttr("{}.min{}".format(node_sr_range_positive, axis.upper()), 0)
        cmds.setAttr("{}.max{}".format(node_sr_range_positive, axis.upper()), 1)

    node_sr_range_negative = cmds.createNode("setRange", n="{}_negClamp_sr".format(name_tag))
    node_md_negative_invert = cmds.createNode("multiplyDivide", n="{}_invertClamp_md".format(name_tag))

    cmds.setAttr(node_md_negative_invert + ".input2", -1, -1, -1, typ="double3")

    for axis in list_axis_up_out:
        cmds.connectAttr("{}.t{}".format(transform_name, axis), "{}.value{}".format(node_sr_range_negative, axis.upper()))

        cmds.setAttr("{}.oldMin{}".format(node_sr_range_negative, axis.upper()), -1)
        cmds.setAttr("{}.oldMax{}".format(node_sr_range_negative, axis.upper()), 0)

        cmds.setAttr("{}.min{}".format(node_sr_range_negative, axis.upper()), -1)
        cmds.setAttr("{}.max{}".format(node_sr_range_negative, axis.upper()), 0)

        cmds.connectAttr("{}.outValue{}".format(node_sr_range_negative, axis.upper()), "{}.input1{}".format(node_md_negative_invert, axis.upper()))

    # get attr direct
    attr_up = "{}.outValue{}".format(node_sr_range_positive, axis_up.upper())
    attr_out = "{}.outValue{}".format(node_sr_range_positive, axis_out.upper())
    attr_down = "{}.output{}".format(node_md_negative_invert, axis_up.upper())
    attr_in = "{}.output{}".format(node_md_negative_invert, axis_out.upper())

    # get attr between
    attr_up_out = get_output_between(attr_up, attr_out)
    attr_up_in = get_output_between(attr_up, attr_in)
    attr_down_out = get_output_between(attr_down, attr_out)
    attr_down_in = get_output_between(attr_down, attr_in)

    # connect attr direct
    attr_up_norm = get_normalize_output(attr_up_out, attr_up_in, attr_up)
    attr_out_norm = get_normalize_output(attr_up_out, attr_down_out, attr_out)
    attr_down_norm = get_normalize_output(attr_down_in, attr_down_out, attr_down)
    attr_in_norm = get_normalize_output(attr_up_in, attr_down_in, attr_in)

    return attr_up_norm, attr_down_norm, attr_in_norm, attr_out_norm, attr_up_out, attr_up_in, attr_down_out, attr_down_in


def set_driver_blendshape(control=None,
                          curve=None,
                          parent=None,
                          parent_config=None,
                          name=None,
                          list_shape_name=["spreadOut", "up", "pullOut", "spreadIn", "down", "pullIn"],
                          node_blendshape=None):
    '''
    create blendshape node for given control , the curve will automatic adjust from control translate
    1) control node_name of controller that drives
    2) curve
    3) list_shape_name

    create 6 of blendshape and return transform node that adjust the range of translation
    '''

    # add blendshape node --------------------------------------------------------------
    old_weight = cmds.blendShape(node_blendshape, q=1, w=1)

    if not old_weight is None:
        amount_old_weight = len(old_weight)
    else:
        amount_old_weight = 0

    list_blendshape_reference = []
    list_blendshape_weight = []
    for i, key_name in enumerate(list_shape_name):
        duplicate_shape = cmds.duplicate(curve, n=key_name + "_" + name)[0]
        list_blendshape_weight.append(node_blendshape + "." + duplicate_shape)

        list_blendshape_reference.append(duplicate_shape)

        geometry = cmds.blendShape(node_blendshape, q=1, g=1)[0]
        cmds.blendShape(node_blendshape, edit=True, t=(geometry, amount_old_weight + i, duplicate_shape, 1.0))

    cmds.group(list_blendshape_reference, n=name + "_grp", p=parent)

    # create clamp node for control --------------------------------------------------------------
    node_clamp_up = "{}_upClamp".format(control)
    node_clamp_down = "{}_downClamp".format(control)

    if not cmds.objExists(node_clamp_up):
        cmds.createNode("clamp", n=node_clamp_up)
        cmds.setAttr(node_clamp_up + ".max", 100, 100, 100, typ="double3")
        cmds.connectAttr(control + ".t", node_clamp_up + ".input")

    if not cmds.objExists(node_clamp_down):
        cmds.createNode("clamp", n=node_clamp_down)
        cmds.setAttr(node_clamp_down + ".min", -100, -100, -100, typ="double3")
        cmds.connectAttr(control + ".t", node_clamp_down + ".input")

    # create config transform -----------------------------------------------------------
    transform_driver = cmds.createNode("transform", n="{}_blendShapeConfig".format(name))
    cmds.parent(transform_driver, parent_config)

    list_attributes = ["xUp", "yUp", "zUp", "xDown", "yDown", "zDown"]
    list_control_attributes = ["x", "y", "z", "x", "y", "z"]
    list_axis_input = ["outputR", "outputG", "outputB", "outputR", "outputG", "outputB"]
    index_axis_input = 0

    for i in range(6):
        if i > 2:
            node_clamp = node_clamp_down
            index_axis_input = (i - 3)
        else:
            node_clamp = node_clamp_up

        attr_config = list_attributes[i]
        attr_control = list_control_attributes[i]
        attr_clamp_output = list_axis_input[i]

        cmds.addAttr(transform_driver, ln=attr_config, at="float", dv=0, k=1)

        # create float math node
        node_divider = cmds.createNode("floatMath")
        cmds.setAttr(node_divider + ".operation", 3)

        # connect control translate attribute to divider
        cmds.connectAttr("{}.{}".format(node_clamp, attr_clamp_output), node_divider + ".floatA")
        # connect config attributes to divider
        cmds.connectAttr("{}.{}".format(transform_driver, attr_config), node_divider + ".floatB")

        # apply output value to blenshape class_instance
        cmds.connectAttr("{}.outFloat".format(node_divider), list_blendshape_weight[i])

        index_axis_input += 1


def set_driver_blendshape_single_avg(list_input_attr=None,
                                     list_driver_value=None,
                                     output_attr=None,
                                     clamp=False,
                                     name_tag="setBlendShape"):
    def get_input_factor(input_attr, driver_value):
        factor = 1 / driver_value

        node_mdl = cmds.createNode("multDoubleLinear", n="{}_mdl".format(name_tag))
        cmds.connectAttr(input_attr, "{}.input2".format(node_mdl))
        cmds.setAttr("{}.input1".format(node_mdl), factor)

        return node_mdl + ".output"

    attr_input1 = get_input_factor(list_input_attr[0], list_driver_value[0])
    attr_input2 = get_input_factor(list_input_attr[1], list_driver_value[1])

    # create clamp node
    node_clamp = cmds.createNode("clamp")
    cmds.setAttr(node_clamp + ".min", 0, 0, 0, typ="double3")
    cmds.setAttr(node_clamp + ".max", 1, 1, 1, typ="double3")

    cmds.connectAttr(attr_input1, node_clamp + ".inputR")
    cmds.connectAttr(attr_input2, node_clamp + ".inputG")

    # sum
    node_adl_sum = cmds.createNode("addDoubleLinear", n="{}_adl".format(name_tag))

    cmds.connectAttr(node_clamp + ".outputR", node_adl_sum + ".input1")
    cmds.connectAttr(node_clamp + ".outputG", node_adl_sum + ".input2")

    # divide 2
    node_mdl_avg = cmds.createNode("multDoubleLinear", n="{}_avg_mdl".format(name_tag))

    cmds.connectAttr(node_adl_sum + ".output", node_mdl_avg + ".input1")
    cmds.setAttr(node_mdl_avg + ".input2", 0.5)
    cmds.connectAttr(node_mdl_avg + ".output", output_attr)


def set_driver_node_fixed(attr_driver, attr_driven, driven_value, name, clamp_length=[None, None], driven_value_is_fixed=False):
    # create driver connection
    node_mdl_mult = cmds.createNode("multDoubleLinear", n="{}_mult_mdl".format(name))

    if driven_value_is_fixed:
        cmds.setAttr("{}.input2".format(node_mdl_mult), driven_value)
    else:
        cmds.connectAttr(driven_value, "{}.input2".format(node_mdl_mult))

    cmds.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

    if clamp_length is [None, None]:  # no clamp case
        cmds.connectAttr("{}.output".format(node_mdl_mult), attr_driven)

    elif clamp_length[0] and clamp_length[1]:  # clamp both side
        node_clamp = cmds.createNode("clamp", n="{}_clamp_cmp".format(name))
        cmds.setAttr("{}.minR".format(node_clamp), clamp_length[0])
        cmds.setAttr("{}.maxR".format(node_clamp), clamp_length[1])

        cmds.connectAttr("{}.output".format(node_mdl_mult), "{}.inputR".format(node_clamp))
        cmds.connectAttr("{}.outputR".format(node_clamp), attr_driven)

    else:  # clamp single side
        if clamp_length[0] is not None:
            operation = 2
            value = clamp_length[0]
        elif clamp_length[1] is not None:
            operation = 4
            value = clamp_length[1]
        else:
            raise Exception("Error Calculate")

        node_cond = cmds.createNode("condition", n="{}_clamp_cond".format(name))

        cmds.connectAttr("{}.output".format(node_mdl_mult), "{}.colorIfTrueR".format(node_cond))
        cmds.connectAttr("{}.output".format(node_mdl_mult), "{}.firstTerm".format(node_cond))
        cmds.setAttr("{}.secondTerm".format(node_cond), value)

        cmds.setAttr("{}.colorIfFalseR".format(node_cond), value)

        cmds.setAttr("{}.operation".format(node_cond), operation)

        cmds.connectAttr("{}.outColorR".format(node_cond), attr_driven)

    return node_mdl_mult


def set_driver_node_multi_input(list_attr_driver, attr_driven, list_attr_factor, name):
    if len(list_attr_driver) != len(list_attr_factor):
        raise Exception("Invalid Input")

    amount_driver = len(list_attr_driver)

    # input driven
    list_mdl_mult = []
    for i in range(amount_driver):
        attr_driver = list_attr_driver[i]
        attr_factor = list_attr_factor[i]

        node_mdl_mult = cmds.createNode("multDoubleLinear", n="{}_mult{}_mdl".format(name, i))
        cmds.connectAttr(attr_factor, "{}.input2".format(node_mdl_mult))
        cmds.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

        list_mdl_mult.append(node_mdl_mult + ".output")

    # create sum value and connect to output
    node_pma_sum = cmds.createNode("plusMinusAverage", n="{}_sum_pma".format(name))

    for i in range(amount_driver):
        attr_mdl = list_mdl_mult[i]

        cmds.connectAttr(attr_mdl, "{}.input1D[{}]".format(node_pma_sum, i))

    cmds.connectAttr("{}.output1D".format(node_pma_sum), attr_driven)

    return node_pma_sum


def set_driver_node_realtime(attr_driver, attr_driven, attr_driver_key, attr_driven_key, name=""):
    # create connection
    node_md_divide = cmds.createNode("multiplyDivide", n="{}divide_md".format(name))
    node_mdl_mult = cmds.createNode("multDoubleLinear", n="{}mult_mdl".format(name))

    cmds.setAttr("{}.operation".format(node_md_divide), 2)

    cmds.connectAttr(attr_driven_key, "{}.input1X".format(node_md_divide))
    cmds.connectAttr(attr_driver_key, "{}.input2X".format(node_md_divide))

    cmds.connectAttr("{}.outputX".format(node_md_divide), "{}.input2".format(node_mdl_mult))
    cmds.connectAttr(attr_driver, "{}.input1".format(node_mdl_mult))

    # output
    cmds.connectAttr("{}.output".format(node_mdl_mult), attr_driven)


def set_layout_disabled(layout,value=False):
    """Disable or enable all child widgets in the given layout."""
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if widget:
            widget.setEnabled(value)

def set_line(start, end, name="line", parent=None):
    grp_line = cmds.group(em=1, n="{}_{}Annotate".format(grp, name))

    # end locator
    locator_end = cmds.spaceLocator(n=loc + "_annotate_" + end + "_end")[0]
    cmds.setAttr(locator_end + ".v", 0)
    cmds.parent(locator_end, grp_line)
    cmds.connectAttr(end + ".worldMatrix[0]", locator_end + ".offsetParentMatrix")

    # start locator
    shape_annotate = cmds.annotate(locator_end)
    transform_annotate = cmds.listRelatives(shape_annotate, p=1, typ="transform")[0]
    cmds.parent(transform_annotate, grp_line)
    cmds.connectAttr(start + ".worldMatrix[0]", transform_annotate + ".offsetParentMatrix")

    # finalize
    cmds.setAttr(shape_annotate + ".overrideEnabled", 1)
    cmds.setAttr(shape_annotate + ".overrideDisplayType", 2)
    cmds.rename(transform_annotate, "annotate_" + start + "_start")
    cmds.select(cl=1)

    if parent:
        cmds.parent(grp_line, parent)

    return grp_line


def set_rotate_order(list_target, rotate_order):
    if rotate_order == "xyz":
        key = 0
    elif rotate_order == "yzx":
        key = 1
    elif rotate_order == "zxy":
        key = 2
    elif rotate_order == "xzy":
        key = 3
    elif rotate_order == "yxz":
        key = 4
    elif rotate_order == "zyx":
        key = 5

    for target in list_target:
        cmds.setAttr(target + ".rotateOrder", key)


def snap_to_between_two_object(parent1, parent2, target):
    tmp_pcn = cmds.pointConstraint(parent1, parent2, target, mo=0)
    cmds.delete(tmp_pcn)


def snap_to_curve_by_cv(curve, object, cv_index, typ="ep"):
    position = cmds.xform("{}.{}[{}]".format(curve, typ, cv_index), ws=1, t=1, q=1)
    cmds.xform(object, ws=1, t=position)


def snap_to_curve_by_param(source, object, param, turn_on_percentage=False):
    tmp_grp = cmds.group(em=1)

    poc = cmds.createNode("pointOnCurveInfo")
    cmds.setAttr("{}.turnOnPercentage".format(poc), turn_on_percentage)

    cmds.connectAttr(source + ".worldSpace[0]", poc + ".inputCurve")
    cmds.setAttr(poc + ".parameter", param)

    cmds.connectAttr(poc + ".position", tmp_grp + ".translate")

    world_pos = cmds.xform(tmp_grp, ws=1, t=1, q=1)
    cmds.xform(object, ws=1, t=world_pos)

    cmds.delete(poc)
    cmds.delete(tmp_grp)

def snap_to_nearest_90(object):
    def snap_angle(angle):
        return round(angle / 90.0) * 90


    rotation = cmds.xform(object, query=True, worldSpace=True, rotation=True)

    if rotation:
        snapped_rotation = [snap_angle(rot) for rot in rotation]
        cmds.xform(object, worldSpace=True, rotation=snapped_rotation)


def snap_to_ribbon_by_param(source, object, param, turn_on_percentage=False):
    cmds.select(source)
    cmds.UVPin()
    node_uvpin = cmds.rename("uvPin1", "uvPinTmp")

    # setup uv pin
    cmds.setAttr("{}.coordinate[{}].coordinateU".format(node_uvpin, 0), param[0])
    cmds.setAttr("{}.coordinate[{}].coordinateV".format(node_uvpin, 0), param[1])

    if turn_on_percentage:
        cmds.setAttr("{}.normalizedIsoParms".format(node_uvpin), 1)

    matrix_output = cmds.getAttr("{}.outputMatrix[{}]".format(node_uvpin, 0))
    cmds.xform(object, ws=1, m=matrix_output)


def snap_to_surface(source, object, u, v, percentage=False, snap="parent"):
    if cmds.objectType(source) == "nurbsSurface":
        shape_surface = source
    elif cmds.objectType(source) == "transform":
        list_shape = cmds.listRelatives(source, c=1, s=1, typ="nurbsSurface")

        if list_shape:
            shape_surface = list_shape[0]
        else:
            raise Exception("not found nurbs surface")
    else:
        raise Exception("Command Error, get source type : {}".format(cmds.objectType(source)))
    poc = cmds.createNode("pointOnSurfaceInfo")
    fmatrix = cmds.createNode("fourByFourMatrix")
    decomp = cmds.createNode("decomposeMatrix")

    cmds.connectAttr("{}.worldSpace[0]".format(shape_surface), "{}.inputSurface".format(poc))
    cmds.setAttr("{}.parameterU".format(poc), u)
    cmds.setAttr("{}.parameterV".format(poc), v)
    cmds.setAttr("{}.turnOnPercentage".format(poc), percentage)

    cmds.connectAttr("{}.positionX".format(poc), "{}.in30".format(fmatrix))
    cmds.connectAttr("{}.positionY".format(poc), "{}.in31".format(fmatrix))
    cmds.connectAttr("{}.positionZ".format(poc), "{}.in32".format(fmatrix))

    cmds.connectAttr("{}.normalX".format(poc), "{}.in00".format(fmatrix))
    cmds.connectAttr("{}.normalY".format(poc), "{}.in01".format(fmatrix))
    cmds.connectAttr("{}.normalZ".format(poc), "{}.in02".format(fmatrix))

    cmds.connectAttr("{}.tangentUx".format(poc), "{}.in10".format(fmatrix))
    cmds.connectAttr("{}.tangentUy".format(poc), "{}.in11".format(fmatrix))
    cmds.connectAttr("{}.tangentUz".format(poc), "{}.in12".format(fmatrix))

    cmds.connectAttr("{}.tangentVx".format(poc), "{}.in20".format(fmatrix))
    cmds.connectAttr("{}.tangentVy".format(poc), "{}.in21".format(fmatrix))
    cmds.connectAttr("{}.tangentVz".format(poc), "{}.in22".format(fmatrix))

    cmds.connectAttr("{}.output".format(fmatrix), "{}.inputMatrix".format(decomp))

    decomp_translate = cmds.getAttr("{}.outputTranslate".format(decomp))[0]
    decomp_rotate = cmds.getAttr("{}.outputRotate".format(decomp))[0]

    cmds.delete(decomp, poc)

    if snap == "point":
        cmds.setAttr("{}.translate".format(object), decomp_translate[0], decomp_translate[1], decomp_translate[2],
                     typ="double3")
    elif snap == "parent":
        cmds.setAttr("{}.translate".format(object), decomp_translate[0], decomp_translate[1], decomp_translate[2],
                     typ="double3")
        cmds.setAttr("{}.rotate".format(object), decomp_rotate[0], decomp_rotate[1], decomp_rotate[2],
                     typ="double3")


def transform_curve(amount, typ, os, axis=None, ):
    selection = cmds.ls(sl=1)

    x = y = z = 0

    if axis == "x":
        x = 1
    elif axis == "y":
        y = 1
    elif axis == "z":
        z = 1

    # filter shape
    for obj in selection:
        list_shape = cmds.listRelatives(obj, c=1, s=1, f=1)
        if list_shape:
            list_curve = []

            for shape in list_shape:
                if cmds.objectType(shape) == "nurbsCurve":
                    list_curve.append(shape)

            for curve in list_curve:
                cmds.select(curve + ".cv[*]", replace=True)

                if os:
                    ws = 0
                else:
                    ws = 1

                if typ == "move":
                    cmds.move(amount, y=y, x=x, z=z, os=os, ws=ws, r=1)
                elif typ == "rotate":
                    cmds.rotate(amount, y=y, x=x, z=z, os=os, ws=ws, r=1)
                elif typ == "scale":
                    if not os:
                        pivot = cmds.xform(obj, ws=1, q=1, sp=1)
                        cmds.scale(1 + amount, 1 + amount, 1 + amount, r=1, p=pivot)
                    else:
                        cmds.scale(1 + amount, 1 + amount, 1 + amount, r=1, )

    cmds.select(selection, r=1)







