from tmlib.core import Scene, Utility, Transform, File
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from tmlib.module.PySide import QtWidgets, QtCore, QtGui
import os, importlib, webbrowser, inspect, configparser
import maya.mel as mel
import maya.cmds as cmds
import json
import tmlib


def _short_name(node):
    """Return the short (non-path) name of a node string."""
    return node.split("|")[-1]


def _node_only(attr_or_node):
    """Strip attribute suffix from a node.attr string."""
    return attr_or_node.split(".")[0]


def clone_style(list_target=None):
    """
    Use to clone style of given controllers (line width and color)

    Input list = [target1,target2,...,ref]

    """

    if list_target is None:
        list_target = cmds.ls(sl=1, typ="transform", l=1)

    selection = list_target

    # sort shape, reference is last one
    ref = list_target[-1]
    list_ref_shape = cmds.listRelatives(ref, c=1, s=1, typ="nurbsCurve", f=1)

    list_target = list_target[0 : len(list_target) - 1]

    # get ref line width and color
    line_width = cmds.getAttr(list_ref_shape[0] + ".lineWidth")
    color_data = get_curve_color_data(list_ref_shape[0])

    # apply
    for target in list_target:
        # set color
        set_color(list_input_transform=[target], color_data=color_data)

        # set line width
        set_line_width(list_input_transform=[target], width=line_width)

    cmds.select(selection, r=1)

    cmds.inViewMessage(amg="Clone Style Complete.", pos="botCenter", fade=True)


def get_official_curve_data(index):
    """Get curve shape list data of position from index"""

    dict_curve_data = File.load_json_file_to_dict(
        os.path.join(os.path.dirname(tmlib.__file__), "data", "Controllers.json")
    )

    return dict_curve_data["ctrl_{}".format(str(index).zfill(2))]


def create_curve_from_data(dict_curve_data, name="control"):
    """
    Create curve by given shape data list (list)
    """
    if not dict_curve_data:
        return None

    # get data from dict to list for each shape
    list_shape = []
    list_pos_cv = []
    list_width = []
    list_color = []

    list_spans = []
    list_degree = []
    list_form = []

    for shape_name in dict_curve_data.keys():
        list_shape.append(shape_name)
        list_pos_cv.append(dict_curve_data[shape_name]["cvPositions"])
        list_width.append(dict_curve_data[shape_name]["lineWidth"])
        list_color.append(dict_curve_data[shape_name]["colorData"])
        list_spans.append(dict_curve_data[shape_name]["spans"])
        list_degree.append(dict_curve_data[shape_name]["degree"])
        list_form.append(dict_curve_data[shape_name]["form"])

    temp_curves = []

    # Create each shape as a temporary curve
    for i, list_pos in enumerate(list_pos_cv):
        if len(list_pos) < 2:
            continue

        if list_form[i] == 0:  # simple curve
            crv = cmds.curve(
                p=list_pos, d=list_degree[i]
            )  # degree 1 (linear), change to d=3 for cubic
        elif list_form[i] == 2 and list_degree[i] == 1:
            list_pos = list_pos + [list_pos[0]]
            crv = cmds.curve(
                p=list_pos, d=list_degree[i]
            )  # degree 1 (linear), change to d=3 for cubic
        elif list_form[i] == 2:  # circle
            crv = cmds.circle(s=list_spans[i], d=list_degree[i], ch=0)[0]
            crv_shape = cmds.listRelatives(crv, c=1, s=1)[0]

            # match position of cv
            for j, cv_pos in enumerate(list_pos_cv[i]):
                cmds.xform("{}.cv[{}]".format(crv_shape, j), t=cv_pos, os=1)

        else:
            continue

        temp_curves.append(crv)

    if not temp_curves:
        return None

    # Assign Style
    for i, curve_transform in enumerate(temp_curves):
        curve_shape = cmds.listRelatives(curve_transform, c=1, s=1, typ="nurbsCurve")[0]

        set_color(color_data=list_color[i], list_input_transform=[curve_shape])
        set_line_width(width=list_width[i], list_input_transform=[curve_shape])

    # Parent all shapes under the first curve transform
    main_curve = temp_curves[0]
    for crv in temp_curves[1:]:
        shapes = cmds.listRelatives(crv, shapes=True, fullPath=True)
        for s in shapes:
            cmds.parent(s, main_curve, shape=True, relative=True)
        cmds.delete(crv)

    # Rename main transform
    final_curve = cmds.rename(main_curve, name)

    return final_curve


def open_color_dialog():
    """
    Launch color dialog for set rgb color
    """

    # Open the QColorDialog to choose a color
    color = QtWidgets.QColorDialog.getColor()

    set_color(
        color_data=[
            False,
            [(color.red() / 255), (color.green() / 255), (color.blue() / 255)],
        ]
    )


def set_color(color_data, list_input_transform=None):
    """
    list_input_transform : support for both transform and shape.
    color_data(list) : [bool,integer index or list rgb] for example coloring index = [True,3] , coloring rgb = [False,(2.5,2.5,2.5)] and disable color = [None,None]

    """
    # get input control
    if list_input_transform:
        list_target = [str(obj) for obj in list_input_transform]
    else:
        # get selection
        list_target = cmds.ls(sl=1)

        # refine selection
        for sel in list_target:
            if "." in str(sel):
                isolate_clear()
                break

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
    is_index, color_value = color_data

    if list_shape:
        for shape in list_shape:
            shape = _node_only(str(shape))

            if color_data == [None, None]:
                cmds.setAttr(shape + ".overrideEnabled", False)

            elif is_index:
                cmds.setAttr(shape + ".overrideEnabled", True)
                cmds.setAttr(f"{shape}.overrideRGBColors", 0)
                cmds.setAttr(shape + ".overrideColor", color_value)

            elif not is_index:
                cmds.setAttr(shape + ".overrideEnabled", True)
                cmds.setAttr(f"{shape}.overrideRGBColors", 1)
                cmds.setAttr(
                    shape + ".overrideColorRGB",
                    color_value[0],
                    color_value[1],
                    color_value[2],
                    typ="double3",
                )


def create_control(index):
    selection = cmds.ls(sl=1, typ="transform", l=1)

    if cmds.ls(sl=1):
        replace = True
    else:
        replace = False

    dict_curve_data = get_official_curve_data(index=index)
    item_name = create_curve_from_data(dict_curve_data=dict_curve_data)

    if replace:  # replace mode
        if not selection:
            raise Exception("Please Select Targets before replace shape")

        list_ref_shape = cmds.listRelatives(selection[0], c=1, typ="nurbsCurve")

        line_width = cmds.getAttr(list_ref_shape[0] + ".lineWidth")
        color_index = get_curve_color_data(list_ref_shape[0])

        for sel in selection:
            clone_shape(
                [sel, item_name],
                line_width=line_width,
                color_data=color_index,
                match_bounding_box=True,
            )

        cmds.select(selection, r=1)

        cmds.inViewMessage(amg="Shape Updated.", pos="botCenter", fade=True)

        control = selection
    elif not replace:  # create mode
        cmds.select(cl=1)

        control = cmds.circle(ch=0)[0]
        clone_shape([control, item_name])

        cmds.select(control)

        cmds.inViewMessage(amg="Shape Created.", pos="botCenter", fade=True)

    # delete temp item
    cmds.delete(item_name)

    return control


def isolate_edit(snap=False, isolate=False):
    """Isolate panel , control vertex editing"""

    def get_curve_cv(shape_path):
        """return the list shape data (spans, degree, list_position) reference by input shape name

        shape_path : [str] shape name or path"""

        list_shape_data = []
        spans = cmds.getAttr("{}.spans".format(shape_path))
        degree = cmds.getAttr("{}.degree".format(shape_path))
        cv_amount = spans + degree
        list_position = []

        for i in range(cv_amount):
            local_translate = cmds.xform(
                "{}.cv[{}]".format(shape_path, i), os=1, t=1, q=1
            )
            local_translate = ["%.4f" % value for value in local_translate]
            list_position.append(local_translate)

        list_shape_data.append(spans)
        list_shape_data.append(degree)
        list_shape_data.append(list_position)

        return list_shape_data

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
            currentPanel = cmds.getPanel(withFocus=True)
            cmds.isolateSelect(currentPanel, s=1)
            cmds.isolateSelect(currentPanel, addSelected=True)

        if snap:  # Frame the selected objects in the viewport
            cmds.viewFit()

    mel.eval("changeSelectMode -component;")

    # for shape in current_select:
    for shape in current_select:
        data = get_curve_cv(shape)
        cmds.select("{}.cv[0:{}]".format(shape, data[0] + data[1] - 1), add=1)


def isolate_clear():
    """Deselect and exist from isolate panel , control vertex editing"""

    # currentPanel = cmds.getPanel(withFocus=True)
    # cmds.isolateSelect(currentPanel, s=0)

    list_transform = []
    selection = cmds.ls(sl=1)

    if selection:
        for sel in selection:

            # if sel is cv
            if "." in str(sel):
                sel = sel.split(".")[0]
                list_transform.extend(cmds.listRelatives(sel, p=1))

            # transform case
            elif cmds.objectType(sel, isa="transform"):
                list_transform.append(sel)

    mel.eval("changeSelectMode -object;")
    cmds.select(list_transform)



def flip_shape(axis: str):
    """Flip shape scale by given axis"""
    cmds.undoInfo(ock=1)
    selection = cmds.ls(sl=1, typ="transform", l=1)

    for sel in selection:
        # create tmp transform and clone shape
        tmp_transform = cmds.duplicate(sel)[0]
        clone_shape([tmp_transform, sel])

        if cmds.listRelatives(tmp_transform, c=1, typ="transform"):
            cmds.delete(cmds.listRelatives(tmp_transform, c=1, typ="transform"))

        list_lock = []
        for attr in ["sx", "sy", "sz"]:
            if cmds.getAttr("{}.{}".format(tmp_transform, attr), l=1):
                list_lock.append("sx")
                cmds.setAttr("{}.{}".format(tmp_transform, attr), l=0, k=1)

        cmds.setAttr("{}.s{}".format(tmp_transform, axis), -1)
        cmds.makeIdentity(tmp_transform, a=1, s=1)

        cmds.select(sel, tmp_transform)
        clone_shape()
        cmds.delete(tmp_transform)

    cmds.select(selection)
    cmds.undoInfo(cck=1)


def set_line_width(width, list_input_transform=None):
    """
    Use to set line width of controller by given transform node (if don't have will detect via selection)
    """

    list_shape = []

    # prepare input list
    if list_input_transform is None:
        list_ctrl_target = cmds.ls(sl=1)
    else:
        list_ctrl_target = list_input_transform

    # filter shape
    for sel in list_ctrl_target:
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
            cmds.setAttr(shape + ".lineWidth", width)


def get_curve_color_data(shape):
    """
    Return curve color info based on override settings.

    Returns:
        [None, None]              -> override not enabled
        [True, index]             -> using color index
        [False, (r, g, b)]        -> using RGB color
    """
    if cmds.objectType(shape) != "nurbsCurve":
        raise ValueError(f"{shape} is not a nurbsCurve")

    if not cmds.getAttr(shape + ".overrideEnabled"):
        return [None, None]

    if cmds.getAttr(shape + ".overrideRGBColors"):
        r = cmds.getAttr(shape + ".overrideColorR")
        g = cmds.getAttr(shape + ".overrideColorG")
        b = cmds.getAttr(shape + ".overrideColorB")
        return [False, (r, g, b)]
    else:
        index = cmds.getAttr(shape + ".overrideColor")
        return [True, index]


def match_controller_cv():
    selection = cmds.ls(sl=1)

    ref = selection[-1]
    sources = selection[0 : len(selection) - 1]

    for source in sources:
        Transform.match_cvs(source, ref)


def clone_shape(
    list_input_transform=None,
    line_width=None,
    color_data=None,
    match_bounding_box=False,
):
    """
    Input list = [target1,target2,...,ctrl_ref]

    if line width or color index not have input will use it's ctrl_target color (not clone style)

    color_data = [bool,color_value] , [is_index,color_value]
    """

    if list_input_transform is None:
        list_input_transform = cmds.ls(sl=1, typ="transform", l=1)

    # sort shape
    ctrl_ref = list_input_transform[-1]
    list_ctrl_target = list_input_transform[0 : len(list_input_transform) - 1]

    # preserve sets for advance skeleton controller
    if "AllSet" in cmds.ls(typ="objectSet"):
        advanced_set_exist = True
    else:
        advanced_set_exist = False

    # check is ref control have shape
    if not cmds.listRelatives(ctrl_ref, c=1, s=1, typ="nurbsCurve"):
        return

    # apply for each ctrl_target
    for ctrl_target in list_ctrl_target:
        # collect style of target if no given style input (line width and curve data) ------------------
        target_shape = cmds.listRelatives(ctrl_target, c=1, s=1, typ="nurbsCurve")

        # is advanced shape
        is_advanced_shape = False

        if advanced_set_exist:
            for shape in target_shape:
                if cmds.sets("AllSet", im=shape):
                    is_advanced_shape = True
                    break

        # store connection list
        list_connection = cmds.listConnections(target_shape, p=1, c=1)
        list_connection = [
            [str(item) for item in sublist] for sublist in list_connection
        ]

        if match_bounding_box:
            target_bb_size = Transform.get_bounding_box_max(target_shape)

        if target_shape:
            target_shape = target_shape[0]
            if not line_width:
                line_width = cmds.getAttr("{}.lineWidth".format(target_shape))
            if not color_data:
                color_data = get_curve_color_data(target_shape)

        elif not target_shape:
            if not line_width:
                line_width = 1
            if not color_data:
                color_data = [None, None]

        # clear all shape in ctrl_target node -----------------
        for list_delete in cmds.listRelatives(
            ctrl_target, c=1, s=1, typ="nurbsCurve", f=1
        ):
            if list_delete:
                cmds.delete(list_delete)

        # duplicate shape and transfer shape to target
        dup_transform = cmds.duplicate(ctrl_ref)[0]
        dup_shapes = cmds.listRelatives(dup_transform, c=1, s=1, f=1, typ="nurbsCurve")

        if match_bounding_box:
            dup_bb_size = Transform.get_bounding_box_max(dup_shapes)

            scale_size = target_bb_size / dup_bb_size

            cmds.xform(
                dup_transform, scale=(scale_size, scale_size, scale_size), ws=1, r=1
            )
            cmds.makeIdentity(dup_transform, a=1, s=1)

        if dup_shapes:
            for shape in dup_shapes:
                # parent to transform node
                cmds.parent(shape, ctrl_target, r=1, s=1)

        # set color
        set_color(color_data=color_data, list_input_transform=[ctrl_target])

        # set line width
        set_line_width(list_input_transform=[ctrl_target], width=line_width)

        cmds.delete(dup_transform)

        # rename shape to proper name
        set_proper_shape_name(ctrl_target)

        # reconnection
        if list_connection:
            for connection in list_connection:
                target, source = connection

                if cmds.objectType(_node_only(source)) != "objectSet":
                    try:
                        cmds.connectAttr(str(source), str(target))
                    except:
                        pass
        # Append to sets
        if is_advanced_shape:
            shape_new = cmds.listRelatives(ctrl_target, c=1, s=1, typ="nurbsCurve")

            for shape in shape_new:
                cmds.sets("AllSet", add=shape)

    cmds.select(list_input_transform, r=1)

    cmds.inViewMessage(amg="Clone Shape Complete", pos="botCenter", fade=True)


def mirror_shape(source_side, target_side):
    """Mirror shape from detect side"""

    def mirror_nurbs_curve_cvs(source_curve, target_curve):
        # Validate curve types
        if not all(
            cmds.objectType(shape) == "nurbsCurve"
            for shape in [source_curve, target_curve]
        ):
            raise ValueError("Both source and target must be of type nurbsCurve")

        # Get shape nodes if transform nodes are passed
        def get_shape_node(curve):
            if cmds.objectType(curve) == "transform":
                shapes = cmds.listRelatives(curve, shapes=True, fullPath=True) or []
                for s in shapes:
                    if cmds.objectType(s) == "nurbsCurve":
                        return s
                raise ValueError(f"No nurbsCurve shape found under {curve}")
            return curve

        source_shape = get_shape_node(source_curve)
        target_shape = get_shape_node(target_curve)

        # Get number of CVs
        source_cvs = cmds.getAttr(source_shape + ".cp", size=True)
        target_cvs = cmds.getAttr(target_shape + ".cp", size=True)

        if source_cvs != target_cvs:
            raise ValueError(
                "Source and target curves do not have the same number of CVs"
            )

        # Snap and mirror CVs
        for i in range(source_cvs):
            pos = cmds.xform(
                f"{source_shape}.cv[{i}]", query=True, worldSpace=True, translation=True
            )
            mirrored_pos = [-pos[0], pos[1], pos[2]]
            cmds.xform(
                f"{target_shape}.cv[{i}]", worldSpace=True, translation=mirrored_pos
            )

    def replace_name_part(original_string, new_character, position):
        if position not in ["start", "end"]:
            return "Error: Position must be 'start' or 'end'."

        if position == "start":
            return new_character + original_string[1:]

        elif position == "end":
            return original_string[:-1] + new_character

    if cmds.ls(sl=True):
        mirror_selected = True
    else:
        mirror_selected = False

    # get raw side
    source_side_raw = source_side.replace("*", "")
    target_side_raw = target_side.replace("*", "")

    if source_side.startswith("*") and source_side.endswith("*"):
        replace_typ = "in"
    elif source_side.startswith("*"):
        replace_typ = "end"
    elif source_side.endswith("*"):
        replace_typ = "start"
    else:
        replace_typ = "in"

    # get all controller in scene — use plain cmds, work with string names directly
    list_controller_name = [
        _short_name(ctrl)
        for ctrl in cmds.ls(sl=1, typ="transform") or []
        if cmds.listRelatives(ctrl, c=1, s=1, typ="nurbsCurve")
    ]

    # force exclude advance box control
    list_exclude = [
        # Left (L)
        "EyeRegion_L",
        "ctrlCheek_L",
        "ctrlMouthCorner_L",
        "ctrlEye_L",
        "ctrlNose_L",
        "EyeBrowRegion_L",
        "ctrlBrow_L",
        "ctrlBoxMouthCorner_L",
        "ctrlBoxNose_L",
        "ctrlBoxCheek_L",
        "ctrlBoxEye_L",
        "ctrlBoxBrow_L",
        # Middle/Center (M)
        "ctrlLips_M",
        "ctrlEmotions_M",
        "ctrlMouth_M",
        "ctrlPhonemes_M",
        "NoseRegion_M",
        "LipRegion_M",
        "ctrlBoxMouth_M",
        "ctrlBoxLips_M",
        "ctrlBoxPhonemes_M",
        "ctrlBoxEmotions_M",
        # Right (R) - Transformed from Left (L)
        "EyeRegion_R",
        "ctrlCheek_R",
        "ctrlMouthCorner_R",
        "ctrlEye_R",
        "ctrlNose_R",
        "EyeBrowRegion_R",
        "ctrlBrow_R",
        "ctrlBoxMouthCorner_R",
        "ctrlBoxNose_R",
        "ctrlBoxCheek_R",
        "ctrlBoxEye_R",
        "ctrlBoxBrow_R",
    ]

    list_controller_name = [n for n in list_controller_name if n not in list_exclude]

    # Create Dict Mirror
    dict_mirror = {}

    for control_name in list_controller_name:
        if source_side_raw in control_name and replace_typ == "in":
            dict_mirror[control_name] = control_name.replace(
                source_side_raw, target_side_raw
            )
        elif control_name.startswith(source_side_raw) and replace_typ == "start":
            dict_mirror[control_name] = replace_name_part(
                control_name, target_side_raw, position="start"
            )
        elif control_name.endswith(source_side_raw) and replace_typ == "end":
            dict_mirror[control_name] = replace_name_part(
                control_name, target_side_raw, position="end"
            )

    for source_ctrl, target_ctrl in dict_mirror.items():
        print("- {} > {}".format(source_ctrl, target_ctrl))

    # clone shape and snap  control vertex position
    for source_ctrl, target_ctrl in dict_mirror.items():
        list_shape_source = cmds.listRelatives(source_ctrl, c=1, s=1, typ="nurbsCurve")

        # skip if source control have no shape
        if list_shape_source is None:
            continue
        # match shape in mirror position
        else:
            Transform.match_cvs(target_ctrl, source_ctrl)

            list_shape_target = cmds.listRelatives(
                target_ctrl, c=1, s=1, typ="nurbsCurve"
            )

            # mirror shape of target side
            for i in range(len(list_shape_source)):
                mirror_nurbs_curve_cvs(list_shape_source[i], list_shape_target[i])

    if mirror_selected:
        cmds.inViewMessage(
            amg="Mirror Selected : {} control.".format(len(dict_mirror)),
            pos="botCenter",
            fade=True,
        )
    else:
        cmds.inViewMessage(
            amg="Mirror All : {} control.".format(len(dict_mirror)),
            pos="botCenter",
            fade=True,
        )


def backup_recall(backup_name="backup_control"):
    """Recall backup control"""

    selection = cmds.ls(sl=1)

    list_child_backup = None
    if cmds.objExists(backup_name):
        list_child_backup = cmds.listRelatives(backup_name, c=1)

    if list_child_backup:
        for ctrl_backup in list_child_backup:
            ctrl_target = ctrl_backup.replace("ctrlBck_", "")

            if cmds.objExists(ctrl_target):
                # clear shape in control target
                list_clear_shape = cmds.listRelatives(ctrl_target, c=1, s=1, f=1)

                if list_clear_shape:
                    for shape in list_clear_shape:
                        cmds.delete(shape)

                # duplicate control backup and parent shape to control target
                ctrl_tmp = cmds.duplicate(ctrl_backup)
                ctrl_tmp_shape = cmds.listRelatives(ctrl_tmp, c=1, s=1, f=1)
                if ctrl_tmp_shape:
                    for shape in ctrl_tmp_shape:
                        cmds.parent(shape, ctrl_target, s=1, r=1)
                    cmds.delete(ctrl_tmp)

                # rename proper
                list_shape = cmds.listRelatives(
                    ctrl_target, c=1, s=1, typ="nurbsCurve", f=1
                )
                for i, shape in enumerate(list_shape):
                    cmds.rename(shape, "{}Shape".format(_short_name(ctrl_target)))

    # re-selection
    cmds.select(selection)


def backup_delete():
    """Delete backup control group"""

    try:
        cmds.delete("backup_control")
    except:
        pass


def backup_update(backup_name="backup_control", keyword=["ctl", "ctrl"]):
    """Create backup controller groups"""

    def is_mgear_guide(ctl):
        if cmds.attributeQuery("isGearGuide", node=ctl, exists=True):
            if cmds.getAttr("{}.isGearGuide".format(ctl)):
                return True

        return False

    selection = cmds.ls(sl=1)

    if not selection:
        raise Exception("Must be selection")

    # create backup group if not exist
    if not cmds.objExists(backup_name):
        cmds.group(em=1, n=backup_name)
        cmds.setAttr(backup_name + ".v", 0)

    # auto search for control
    list_anim_ctrl = []

    # ignore some crucial child
    for ctl in selection:
        if (
            not is_mgear_guide(ctl)
            and not Utility.is_child_of(ctl, "GRP_SHAPE")
            and not Utility.is_child_of(ctl, "controllers_org")
            and not Utility.is_child_of(ctl, backup_name)
            and not Utility.is_child_of(ctl, "guide")
            and cmds.listRelatives(ctl, c=1, s=1, typ="nurbsCurve")
        ):
            list_anim_ctrl.append(str(ctl))

    # create backup control
    for ctl in list_anim_ctrl:
        ctl_short = _short_name(ctl)

        if cmds.objExists("ctrlBck_" + ctl_short):
            cmds.delete("ctrlBck_" + ctl_short)

        ctl_bck = cmds.group(em=1, n="ctrlBck_" + ctl_short)
        cmds.parent(ctl_bck, backup_name)

        # duplicate control and parent new shape then delete it
        ctl_dup = cmds.duplicate(ctl)

        cmds.parent(
            cmds.listRelatives(ctl_dup, c=1, s=1, typ="nurbsCurve"), ctl_bck, s=1, r=1
        )
        cmds.delete(ctl_dup)

        set_proper_shape_name(ctl_bck)

    # re-selection
    cmds.select(selection)


def set_proper_shape_name(control):
    """Set shape in given transform node name to proper name"""

    list_shape = cmds.listRelatives(control, c=1, s=1, typ="nurbsCurve", f=1)

    if not list_shape:
        return

    # rename proper
    for i, shape in enumerate(list_shape):
        cmds.rename(shape, "{}Shape".format(_short_name(str(control))))


def as_mirror_control_curves(left_to_right, setName="ControlSet"):
    # confirm build pose
    if not mel.eval("asConfirmIfNotInBuildPose"):
        return

    sel = cmds.ls(sl=True) or []
    controlObjects = cmds.sets(setName, q=True) or []

    for ctrl in controlObjects:
        shapes = cmds.listRelatives(ctrl, s=True) or []
        if not shapes:
            continue

        shape = shapes[0]
        objType = cmds.objectType(shape)

        if objType not in ["nurbsCurve", "nurbsSurface"]:
            continue

        # left / right filter
        if left_to_right:
            if "_L" not in shape:
                continue
        else:
            if "_R" not in shape:
                continue

        # skip joystick face ctrls
        if setName == "FaceControlSet" and shape.startswith("ctrl"):
            continue

        # opposite naming
        if left_to_right:
            oppositeShape = shape.replace("_L", "_R")
            oppositeCtrl = ctrl.replace("_L", "_R")
        else:
            oppositeShape = shape.replace("_R", "_L")
            oppositeCtrl = ctrl.replace("_R", "_L")

        if not cmds.objExists(oppositeShape):
            continue

        # ==============================
        # NURBS SURFACE
        # ==============================
        if objType == "nurbsSurface":
            cvs = cmds.ls(shape + ".cv[0:999][0:999]", fl=True) or []

            for cv in cvs:
                parts = cv.split(".")
                if cmds.objectType(parts[0]) == "transform":
                    cv = shape + "." + parts[1]

                pos = cmds.xform(cv, q=True, ws=True, t=True)
                cmds.xform(
                    cv.replace(shape, oppositeShape),
                    ws=True,
                    t=[-pos[0], pos[1], pos[2]],
                )

            if cmds.attributeQuery(
                "softModControl", node=ctrl, exists=True
            ) or cmds.attributeQuery("clusterControl", node=ctrl, exists=True):
                cmds.reverseSurface(oppositeShape, d=0, ch=0, rpo=True)

            continue

        # ==============================
        # SKIN CAGE CURVES SET
        # ==============================
        if setName == "SkinCageCurvesSet":
            pos = cmds.xform(ctrl, q=True, ws=True, t=True)
            sca = cmds.getAttr(ctrl + ".s")[0]

            cmds.xform(oppositeCtrl, ws=True, t=[-pos[0], pos[1], pos[2]])
            cmds.setAttr(oppositeCtrl + ".s", sca[0], sca[1], sca[2], type="float3")

        # ==============================
        # CURVE CV MIRRORING
        # ==============================
        form = cmds.getAttr(shape + ".form")
        spans = cmds.getAttr(shape + ".spans")
        degree = cmds.getAttr(shape + ".degree")

        if form == 2:
            numCv = spans
        else:
            numCv = spans + degree

        for y in range(numCv + 1):
            pos = cmds.xform(f"{shape}.cv[{y}]", q=True, ws=True, t=True)

            # remap index for skin cage
            z = y
            if y == 0:
                z = 2
            if y == 1:
                z = 3
            if y == 2:
                z = 0
            if y == 3:
                z = 1
            if y == 4:
                z = 2

            if setName == "SkinCageCurvesSet":
                cmds.xform(
                    f"{oppositeShape}.cv[{z}]", ws=True, t=[-pos[0], pos[1], pos[2]]
                )
                if y == 2:
                    cmds.xform(
                        f"{oppositeShape}.cv[4]", ws=True, t=[-pos[0], pos[1], pos[2]]
                    )
            else:
                cmds.xform(
                    f"{oppositeShape}.cv[{y}]", ws=True, t=[-pos[0], pos[1], pos[2]]
                )

        # ==============================
        # MIRROR SLIDE JOINTS
        # ==============================
        if setName == "SkinCageCurvesSet":
            skinInfo = mel.eval(f'asSkinCurveSliderInfo "{ctrl}"')
            haveSlider = [0, 0, 0, 0]

            for y in range(4):
                joint = f"{skinInfo[0]}_{skinInfo[1]}Slider{y}"
                haveSlider[y] = cmds.objExists(joint)

            if any(haveSlider):
                cmds.select(oppositeCtrl, r=True)
                mel.eval("asCreateSliders")

                for y in range(4):
                    slider = f"{skinInfo[0]}_{skinInfo[1]}Slider{y}"

                    if left_to_right:
                        oppSlider = slider.replace("_L", "_R")
                    else:
                        oppSlider = slider.replace("_R", "_L")

                    remap = {0: 2, 1: 3, 2: 0, 3: 1}
                    oppSlider = oppSlider.replace(str(y), str(remap[y]))

                    if cmds.objExists(slider) and cmds.objExists(oppSlider):
                        val = cmds.getAttr(slider + ".slide")
                        cmds.setAttr(oppSlider + ".slide", val)
            else:
                oppInfo = mel.eval(f'asSkinCurveSliderInfo "{oppositeCtrl}"')
                oppHave = [
                    cmds.objExists(f"{oppInfo[0]}_{oppInfo[1]}Slider{i}")
                    for i in range(4)
                ]
                if any(oppHave):
                    cmds.select(oppositeCtrl, r=True)
                    mel.eval("asDeleteSliders")


def as_swap_curve():
    sel = cmds.ls(sl=True)
    if len(sel) < 2:
        cmds.error("Selected both controls to replace, and the new curve to use")

    ctrl_from_edges = False
    sel_shapes = []

    for i, item in enumerate(sel):
        shapes = cmds.listRelatives(item, s=True, f=True) or []
        sel_shapes.append(shapes[0] if shapes else None)

        if "Extra" in item:
            continue

        if ".e[" in item:
            ctrl_from_edges = True
            break

        if not shapes or not cmds.objExists(shapes[0]):
            cmds.error(f'selected object: "{item}" is not a nurbsCurve')

        obj_type = cmds.objectType(shapes[0])
        if obj_type != "nurbsCurve" and obj_type != "nurbsSurface":
            cmds.error(f'selected object: "{item}" is not a nurbsCurve')

    if ctrl_from_edges:
        if cmds.objExists("combinedEdgesAsCurve"):
            cmds.delete("combinedEdgesAsCurve")

        ctrls = []
        cmds.select(cl=True)

        for item in sel:
            if ".e[" in item:
                cmds.select(item, add=True)
            elif cmds.objectType(item) == "transform":
                ctrls.append(item)

        if not ctrls:
            cmds.error("No Controller found in the selection")

        temp_curves = cmds.duplicateCurve(ch=False)
        cmds.delete(temp_curves, ch=True)

        if len(temp_curves) == 1:
            cmds.duplicate(temp_curves[0], n="combinedEdgesAsCurve")
        else:
            cmds.attachCurve(
                temp_curves,
                n="combinedEdgesAsCurve",
                ch=False,
                rpo=False,
                kmk=True,
                m=1,
                bb=0.5,
                bki=False,
                p=0.1,
            )

        cmds.delete(temp_curves)

        temp_xform = cmds.createNode("transform", n="tempXform", p=ctrls[0])
        cmds.parent(temp_xform, w=True)
        cmds.parent("combinedEdgesAsCurve", temp_xform)
        cmds.xform(temp_xform, os=True, t=(0, 0, 0), ro=(0, 0, 0))
        cmds.parent("combinedEdgesAsCurve", w=True)

        cmds.makeIdentity("combinedEdgesAsCurve", apply=True, t=True, r=True, s=True)
        cmds.xform("combinedEdgesAsCurve", ws=True, piv=(0, 0, 0))
        cmds.scale(1.3, 1.3, 1.3, "combinedEdgesAsCurve.cv[*]", r=True, p=(0, 0, 0))

        target_shape = "combinedEdgesAsCurveShape"
        cmds.setAttr(f"{target_shape}.overrideEnabled", 1)
        orig_shapes = cmds.listRelatives(ctrls[0], s=True)
        color = cmds.getAttr(f"{orig_shapes[0]}.overrideColor")
        cmds.setAttr(f"{target_shape}.overrideColor", color)

        cmds.delete(temp_xform)

        cmds.select(ctrls, r=True)
        cmds.select("combinedEdgesAsCurve", add=True)
        as_swap_curve()

        if cmds.objExists("combinedEdgesAsCurve"):
            cmds.delete("combinedEdgesAsCurve")
        cmds.select(ctrls)
        return

    last_item = sel[-1]
    cmds.delete(last_item, ch=True)

    for i in range(len(sel) - 1):
        target_ctrl = sel[i]
        old_shapes = cmds.listRelatives(target_ctrl, s=True, f=True) or []

        shape_was_in_allset = False
        shape_was_in_face_allset = False
        connections = []

        if old_shapes:
            shape = old_shapes[0]
            if cmds.objExists("AllSet"):
                shape_was_in_allset = cmds.sets(shape, im="AllSet")
            if cmds.objExists("FaceAllSet"):
                shape_was_in_face_allset = cmds.sets(shape, im="FaceAllSet")

            connections = cmds.listConnections(shape, s=True, d=False, p=True) or []
            cmds.delete(old_shapes)

        temp_grp = cmds.duplicate(last_item, n="tempXform")[0]
        new_shapes = cmds.listRelatives(temp_grp, s=True, f=True) or []

        all_set_name = "AllSet"
        if cmds.objExists("FaceAllSet"):
            if cmds.sets(target_ctrl, im="FaceAllSet"):
                all_set_name = "FaceAllSet"

        for shape in new_shapes:
            new_shape_name = cmds.rename(shape, f"{target_ctrl}Shape")
            added_shape = cmds.parent(new_shape_name, target_ctrl, add=True, s=True)[0]

            rot = cmds.xform(target_ctrl, q=True, ws=True, ro=True)
            if any(abs(v) > 0.001 for v in rot):
                if not cmds.objExists("combinedEdgesAsCurve"):
                    cmds.rotate(-90, -90, 0, f"{added_shape}.cv[*]", r=True, os=True)

            if shape_was_in_allset or shape_was_in_face_allset:
                cmds.sets(added_shape, add=all_set_name)

            if connections:
                try:
                    cmds.connectAttr(connections[0], f"{added_shape}.v", f=True)
                except:
                    pass

        cmds.delete(temp_grp)

    cmds.dgdirty(a=True)