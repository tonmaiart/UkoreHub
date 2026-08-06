from tmlib.core import Utility, Validate, Selection
from tmlib.ui import uitools

import maya.cmds as cmds
import maya.mel as mel
import os
import platform
import subprocess


@uitools.undoable
def export_multiple_separated():
    # 1. Validation
    selection = cmds.ls(sl=True, long=True)
    if not selection:
        cmds.warning("Please select the objects you want to export.")
        return

    # 2. Setup Directory
    current_file_path = cmds.file(q=True, sceneName=True)
    start_dir = (
        os.path.dirname(current_file_path)
        if current_file_path
        else cmds.workspace(q=True, rootDirectory=True)
    )

    export_root = cmds.fileDialog2(
        dialogStyle=2, fileMode=3, startingDirectory=start_dir, okCaption="Export Here"
    )
    if not export_root:
        return

    root_path = export_root[0]

    # 3. Export Logic (Loop)
    mel.eval("FBXResetExport()")
    for obj in selection:
        short_name = obj.split("|")[-1].split(":")[-1]
        file_path = os.path.join(root_path, f"{short_name}.fbx").replace("\\", "/")

        # Record original transform
        orig_pos = cmds.xform(obj, q=True, ws=True, translation=True)
        orig_rot = cmds.xform(obj, q=True, ws=True, rotation=True)

        try:
            # Zero out
            cmds.xform(obj, ws=True, translation=(0, 0, 0), rotation=(0, 0, 0))
            cmds.select(obj, replace=True)
            mel.eval(f'FBXExport -f "{file_path}" -s')
        finally:
            # Restore
            cmds.xform(obj, ws=True, translation=orig_pos, rotation=orig_rot)

    # 4. Cleanup & Open Folder
    cmds.select(selection)
    if platform.system() == "Windows":
        os.startfile(root_path)
    else:
        subprocess.Popen(
            ["open" if platform.system() == "Darwin" else "xdg-open", root_path]
        )

    cmds.inViewMessage(
        amg='<span style="color:#72ff72;">✔ Multiple Export Complete</span>',
        pos="midCenter",
        fade=True,
        fst=1500,
    )


@uitools.undoable
def export_single_combined():
    # 1. Validation
    selection = cmds.ls(sl=True, long=True)
    if not selection:
        cmds.warning("Please select the objects you want to export.")
        return

    # 2. Setup starting directory and default name
    current_file_path = cmds.file(q=True, sceneName=True)
    if current_file_path:
        start_dir = os.path.dirname(current_file_path)
        default_name = os.path.basename(current_file_path).split(".")[0]
    else:
        start_dir = cmds.workspace(q=True, rootDirectory=True)
        default_name = "Combined_Export"

    # 3. Open Browse Dialog
    # fileMode=0: returns a single file name (editable in the dialog)
    export_path = cmds.fileDialog2(
        fileFilter="FBX (*.fbx)",
        dialogStyle=2,
        fileMode=0,
        startingDirectory=os.path.join(start_dir, default_name),
        okCaption="Export",
        caption="Export Combined FBX",
    )

    if not export_path:
        print("Export cancelled.")
        return

    full_path = export_path[0]

    # Ensure the file ends with .fbx
    if not full_path.lower().endswith(".fbx"):
        full_path += ".fbx"

    root_path = os.path.dirname(full_path)

    # 4. Export Logic
    cmds.select(selection)
    mel.eval("FBXResetExport()")
    # Force specific FBX settings if needed (e.g. Smoothing Groups)
    mel.eval("FBXExportSmoothingGroups -v true")
    mel.eval(f'FBXExport -f "{full_path}" -s')

    # 5. Cleanup & Open Folder
    cmds.select(selection)
    if platform.system() == "Windows":
        os.startfile(root_path)
    else:
        subprocess.Popen(
            ["open" if platform.system() == "Darwin" else "xdg-open", root_path]
        )

    cmds.inViewMessage(
        amg=f'<span style="color:#72ff72;">✔ Exported: {os.path.basename(full_path)}</span>',
        pos="midCenter",
        fade=True,
        fst=2000,
    )


@uitools.undoable
def export_advanced_fbx_package():
    # 1. Validation
    selection = cmds.ls(sl=True, long=True)
    if not selection:
        cmds.warning("Please select the objects you want to export.")
        return

    # 2. Setup Directory
    current_file_path = cmds.file(q=True, sceneName=True)
    start_dir = (
        os.path.dirname(current_file_path)
        if current_file_path
        else cmds.workspace(q=True, rootDirectory=True)
    )

    export_root = cmds.fileDialog2(
        dialogStyle=2, fileMode=3, startingDirectory=start_dir, okCaption="Export Here"
    )
    if not export_root:
        return

    root_path = export_root[0]
    combined_dir = os.path.join(root_path, "Single")
    separated_dir = os.path.join(root_path, "Multiple")

    # Create subfolders if they don't exist
    for folder in [combined_dir, separated_dir]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # 3. Export COMBINED
    # Uses the scene name or "Combined_Export" if scene is unsaved
    scene_name = (
        os.path.basename(current_file_path).split(".")[0]
        if current_file_path
        else "Combined_Export"
    )
    combined_file = os.path.join(combined_dir, f"{scene_name}.fbx").replace("\\", "/")

    cmds.select(selection)
    mel.eval("FBXResetExport()")
    mel.eval(f'FBXExport -f "{combined_file}" -s')
    print(f"Combined export finished: {combined_file}")

    # 4. Export SEPARATED (Zeroed out)
    for obj in selection:
        # Get Short Name for filename
        short_name = obj.split("|")[-1].split(":")[-1]
        sep_file_path = os.path.join(separated_dir, f"{short_name}.fbx").replace(
            "\\", "/"
        )

        # Record original transformation
        orig_pos = cmds.xform(obj, q=True, ws=True, translation=True)
        orig_rot = cmds.xform(obj, q=True, ws=True, rotation=True)

        try:
            # Move to Origin (0,0,0)
            cmds.xform(obj, ws=True, translation=(0, 0, 0))
            cmds.xform(obj, ws=True, rotation=(0, 0, 0))

            # Export individual
            cmds.select(obj, replace=True)
            mel.eval(f'FBXExport -f "{sep_file_path}" -s')

        finally:
            # Always move back to original position even if export fails
            cmds.xform(obj, ws=True, translation=orig_pos)
            cmds.xform(obj, ws=True, rotation=orig_rot)

    # 5. Cleanup and Open Folder
    cmds.select(selection)

    if platform.system() == "Windows":
        os.startfile(root_path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", root_path])


@uitools.undoable
def validate_facesets():
    selection = cmds.ls(sl=1)
    Validate.validate_material_face_set(selection)


@uitools.undoable
def check_and_select_multi_uv():
    # 1. Get current selection
    selection = cmds.ls(sl=True, long=True, type="transform")
    if not selection:
        cmds.warning("Please select objects to check.")
        return

    problem_objects = []

    # 2. Analyze UV sets
    for obj in selection:
        shapes = (
            cmds.listRelatives(obj, s=True, ni=True, type="mesh", fullPath=True) or []
        )
        for shape in shapes:
            uv_sets = cmds.polyUVSet(shape, q=True, allUVSets=True) or []
            if len(uv_sets) > 1:
                problem_objects.append(obj)
                break

    # 3. If everything is clean
    if not problem_objects:
        cmds.inViewMessage(
            amg='<span style="color:#72ff72;">✔ Clean: All selected meshes have only 1 UV set.</span>',
            pos="midCenter",
            fade=True,
            fst=2500,
        )
        return

    # 4. Format the list for the dialog
    num_problems = len(problem_objects)
    obj_names_short = [o.split("|")[-1] for o in problem_objects]

    display_limit = 15
    display_list = "\n".join(obj_names_short[:display_limit])
    if num_problems > display_limit:
        display_list += f"\n... and {num_problems - display_limit} more."

    # 5. Create Dialog with 'OK' as default
    confirm = cmds.confirmDialog(
        title="UV Set Count Check",
        message=f"Found {num_problems} object(s) with multiple UV sets:\n\n{display_list}\n\nSelect them?",
        button=["OK", "Cancel"],
        defaultButton="OK",
        cancelButton="Cancel",
        dismissString="Cancel",
    )

    # 6. Action
    if confirm == "OK":
        cmds.select(problem_objects, r=True)
        # Final feedback
        cmds.inViewMessage(
            amg=f'<span style="color:#ffff72;">Selected {num_problems} problem objects.</span>',
            pos="midCenter",
            fade=True,
            fst=2000,
        )
    else:
        print("User cancelled selection change.")


@uitools.undoable
def clean_uvmap():
    sel = cmds.ls(sl=True, long=True, type="transform")
    if not sel:
        cmds.warning("No objects selected")
        return

    processed_count = 0
    target_name = "UVMap"

    for obj in sel:
        # Get shape node
        shapes = (
            cmds.listRelatives(obj, s=True, ni=True, type="mesh", fullPath=True) or []
        )
        if not shapes:
            continue

        for shape in shapes:
            uv_sets = cmds.polyUVSet(shape, q=True, allUVSets=True) or []

            # 1. Skip if only one set exists and it's already named correctly
            if len(uv_sets) == 1 and uv_sets[0] == target_name:
                continue

            # 2. Identify Source (newest data) and Destination (the base set)
            source_uv = uv_sets[-1]
            dest_uv = uv_sets[0]

            # 3. Copy data to the base set
            # Using the MEL-style flags which are more reliable for this specific command
            if source_uv != dest_uv:
                try:
                    cmds.polyCopyUV(
                        shape, uvSetNameInput=source_uv, uvSetName=dest_uv, ch=False
                    )
                except Exception as e:
                    cmds.warning(f"Could not copy UVs for {obj}: {e}")

            # 4. Set base set as current
            cmds.polyUVSet(shape, currentUVSet=True, uvSet=dest_uv)

            # 5. Delete all other sets (skipping the first one)
            for i in range(len(uv_sets) - 1, 0, -1):
                try:
                    cmds.polyUVSet(shape, delete=True, uvSet=uv_sets[i])
                except RuntimeError:
                    # This catches the 'Default set cannot be deleted' error
                    pass

            # 6. Rename the final remaining set to "UVMap"
            remaining = cmds.polyUVSet(shape, q=True, allUVSets=True)
            if remaining:
                try:
                    # Rename the first one found (usually the only one left)
                    cmds.polyUVSet(
                        shape, rename=True, uvSet=remaining[0], newUVSet=target_name
                    )
                except RuntimeError:
                    # Usually happens if it's already named UVMap
                    pass

            processed_count += 1
            print(f"Unified: {obj.split('|')[-1]} -> {target_name}")

    # Restore selection
    cmds.select(sel)

    if processed_count > 0:
        cmds.inViewMessage(
            amg=f'<span style="color:#72ff72;">✔ Unified UVs for {processed_count} objects.</span>',
            pos="midCenter",
            fade=True,
            fst=2000,
        )


@uitools.undoable
def validate_and_fix_material_names():
    Validate.fix_material_names(cmds.ls(sl=1))


@uitools.undoable
def move_to_grid_from_biggest_bbox(items_per_row=5, padding=0.05):
    sel = cmds.ls(sl=True, long=True)
    if not sel:
        cmds.warning("No objects selected")
        return

    # --------------------------------------
    # Sort selection by name
    # --------------------------------------
    sel = sorted(sel, key=lambda x: x.split("|")[-1])

    # --------------------------------------
    # Find biggest WIDTH (X axis)
    # --------------------------------------
    max_width = 0.0

    for obj in sel:
        bbox = cmds.exactWorldBoundingBox(obj)
        width = bbox[3] - bbox[0]
        max_width = max(max_width, width)

    cell = max_width + padding

    # --------------------------------------
    # Grid placement
    # --------------------------------------
    for i, obj in enumerate(sel):
        row = i // items_per_row
        col = i % items_per_row

        target_min_x = col * cell
        target_min_z = row * cell

        bbox = cmds.exactWorldBoundingBox(obj)

        offset_x = target_min_x - bbox[0]
        offset_z = target_min_z - bbox[2]

        cmds.xform(obj, ws=True, r=True, t=(offset_x, 0, offset_z))


@uitools.undoable
def flip_selection(left="_L", right="_R"):

    sel = cmds.ls(sl=True) or []
    if not sel:
        return

    result = Utility.find_flip_object(left=left, right=right)

    # Apply selection and show message
    if result:
        cmds.select(result, r=True)
        cmds.inViewMessage(
            amg=f"<hl>Flipped Selection</hl>: {len(result)} object(s)",
            pos="midCenter",
            fade=True,
        )

        return result
    else:
        cmds.inViewMessage(amg="No flipped object found.", pos="midCenter", fade=True)

        return None


@uitools.undoable
def reset_selected_attrs():
    def get_selected_channelbox_attrs():
        cb = "mainChannelBox"
        result = []

        sel = cmds.ls(sl=True) or []

        # 1. Transform attrs
        main_attrs = cmds.channelBox(cb, q=True, selectedMainAttributes=True) or []
        for node in sel:
            for attr in main_attrs:
                if cmds.attributeQuery(attr, node=node, exists=True):
                    result.append(f"{node}.{attr}")

        # 2. Shape attrs
        shape_attrs = cmds.channelBox(cb, q=True, selectedShapeAttributes=True) or []
        for node in sel:
            if cmds.nodeType(node) == "transform":
                shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True) or []
                for shape in shapes:
                    for attr in shape_attrs:
                        if cmds.attributeQuery(attr, node=shape, exists=True):
                            result.append(f"{shape}.{attr}")

        # 3. History / deformer attrs
        hist_attrs = cmds.channelBox(cb, q=True, selectedHistoryAttributes=True) or []
        for node in sel:
            if cmds.nodeType(node) == "transform":
                shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True) or []
                for shape in shapes:
                    for hist in cmds.listHistory(shape, pruneDagObjects=True) or []:
                        for attr in hist_attrs:
                            if cmds.attributeQuery(attr, node=hist, exists=True):
                                result.append(f"{hist}.{attr}")

        # 4. Output node attrs
        out_attrs = cmds.channelBox(cb, q=True, selectedOutputAttributes=True) or []
        for node in sel:
            if cmds.nodeType(node) == "transform":
                shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True) or []
                for shape in shapes:
                    for conn in cmds.listConnections(shape, s=False, d=True) or []:
                        for attr in out_attrs:
                            if cmds.attributeQuery(attr, node=conn, exists=True):
                                result.append(f"{conn}.{attr}")

        return result

    selected_attributes = get_selected_channelbox_attrs()

    if not selected_attributes:
        cmds.warning("Please select an object and an attribute in the Channel Box.")
        return

    for path in selected_attributes:
        obj, attr = path.split(".", 1)

        default_value = cmds.attributeQuery(attr, node=obj, listDefault=True)

        if default_value:
            cmds.setAttr(path, default_value[0])
            cmds.inViewMessage(
                amg="<hl>Reset Selected Attr</hl>", pos="botCenter", fade=True
            )


@uitools.undoable
def reset_transform():
    """
    Resets the transform values of all selected transform nodes.

    - Translates and rotates (tx, ty, tz, rx, ry, rz) are set to 0.
    - Scales (sx, sy, sz) are set to 1.
    - Locked attributes are skipped.
    """
    attrs_zero = ["tx", "ty", "tz", "rx", "ry", "rz"]
    attrs_one = ["sx", "sy", "sz"]

    for node in cmds.ls(selection=True, type="transform"):
        for attr in attrs_zero:
            if not cmds.getAttr("{}.{}".format(node, attr), lock=True):
                try:

                    cmds.setAttr("{}.{}".format(node, attr), 0)
                except:
                    pass

        for attr in attrs_one:
            if not cmds.getAttr("{}.{}".format(node, attr), lock=True):
                try:
                    cmds.setAttr("{}.{}".format(node, attr), 1)
                except:
                    pass

    cmds.inViewMessage(amg="<hl>Reset Transform</hl>", pos="botCenter", fade=True)


@uitools.undoable
def smart_parent():
    """
    Parents multiple selected transform nodes into a hierarchy chain.

    The first selected object becomes the child of the second,
    the second becomes the child of the third, and so on.
    (Assumes first is the lowest, last is the top in hierarchy.)

    Example:
        Select: A, B, C
        Result: A -> B -> C (C is the top-most parent)
    """
    selection = cmds.ls(selection=True, type="transform")

    if len(selection) < 2:
        cmds.warning("Select at least two transform nodes.")
        return

    for i in range(len(selection) - 1):
        try:
            cmds.parent(selection[i], selection[i + 1])
        except Exception as e:
            cmds.warning(
                "Failed to parent {} to {}: {}".format(
                    selection[i], selection[i + 1], e
                )
            )

    # Re-select the original objects in the same order
    cmds.select(clear=True)
    for obj in selection:
        cmds.select(obj, add=True)

    cmds.inViewMessage(amg="Smart Parent", pos="botCenter", fade=True)


@uitools.undoable
def lock_attribute():
    """
    Locks common transform attributes on selected transform nodes.

    The following attributes will be locked and hidden from the channel box:
    - Translate: tx, ty, tz
    - Rotate: rx, ry, rz
    - Scale: sx, sy, sz
    - Visibility: v
    """
    targets = cmds.ls(selection=True)
    attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]

    for obj in targets:
        for attr in attrs:
            obj.setAttr(attr, lock=True, keyable=False)

    cmds.inViewMessage(
        amg="Locked Attributes for: <hl>{}</hl>".format(
            ", ".join(str(t) for t in targets)
        ),
        pos="botCenter",
        fade=True,
    )


@uitools.undoable
def unlock_attribute():
    """
    Unlocks common transform attributes on selected transform nodes.

    The following attributes will be unlocked and made keyable:
    - Translate: tx, ty, tz
    - Rotate: rx, ry, rz
    - Scale: sx, sy, sz
    - Visibility: v
    """
    targets = cmds.ls(selection=True)
    attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]

    for obj in targets:
        for attr in attrs:
            obj.setAttr(attr, lock=False, keyable=True)

    cmds.inViewMessage(
        amg="Unlocked Attributes for: <hl>{}</hl>".format(
            ", ".join(str(t) for t in targets)
        ),
        pos="botCenter",
        fade=True,
    )


@uitools.undoable
def sort_by_type(typ="transform"):
    """
    Selects all objects of a given type under the current selection (or all scene objects if nothing is selected).

    Args:
        typ (str): The type of object to filter by.
                   Accepted values: 'transform', 'joint', 'anim_curve', 'nurbsCurve', etc.
    """

    # find list target
    if not cmds.ls(sl=1):
        list_target = cmds.ls()
    else:
        list_target = []
        list_target.extend(cmds.ls(sl=1))

        for obj in cmds.ls(sl=1):
            list_target.extend(cmds.listRelatives(obj, ad=1)[::-1])

    # variables for return selected
    if typ == "anim_curve":
        list_selected_return = Selection.sort_by_type(list_target=list_target, typ=typ)
    elif typ == "transform":
        list_selected_return = Selection.sort_by_type(list_target=list_target, typ=typ)
    elif typ == "joint":
        list_selected_return = Selection.sort_by_type(list_target=list_target, typ=typ)
    elif typ == "nurbsCurve":
        list_selected_return = Selection.sort_by_type(list_target=list_target, typ=typ)
    elif typ == "custom":
        custom_typ = input("Input Custom Type")
        list_selected_return = Selection.sort_by_type(
            list_target=list_target, typ=custom_typ
        )
    else:
        raise Exception("Command Error")

    # select the sorted
    cmds.select(cl=1)
    for obj in list_selected_return:
        cmds.select(obj, add=1)

    # popup to screen
    cmds.inViewMessage(amg="Sorted {}".format(typ), pos="botCenter", fade=True)
