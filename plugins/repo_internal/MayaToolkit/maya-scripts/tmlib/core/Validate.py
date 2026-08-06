import maya.cmds as cmds


def get_materials_from_object(object):
    materials = set()

    # convert selection to shapes / faces

    shapes = cmds.listRelatives(object, shapes=True, fullPath=True) or []
    # components = cmds.filterExpand(object, sm=34) or []

    # # case 1: face selection
    # for face in components:

    #     sgs = cmds.listConnections(face, type="shadingEngine") or []

    #     for sg in sgs:
    #         mats = cmds.listConnections(sg + ".surfaceShader") or []
    #         materials.update(mats)

    # case 2: object selection

    for shape in shapes:
        sgs = cmds.listConnections(shape, type="shadingEngine") or []
        # print("face : ", shape)
        for sg in sgs:
            print("sg : ", sg)
            mats = cmds.listConnections(sg + ".surfaceShader") or []
            materials.update(mats)

    return list(materials)


def validate_material_face_set(selection):
    def assign_material_to_faces(material, faces):
        """
        Assigns a specific material to a list of face strings.
        Example input: 'lambert2', ['pCube2.f[2]', 'pCube2.f[3]']
        """

        # print("Input Assgin Materail : ", material, faces)

        # 1. Verify the material exists
        if not cmds.objExists(material):
            cmds.warning(f"Material '{material}' does not exist.")
            return

        # 2. Find or Create the Shading Engine (SG)
        # Materials connect to SGs via the .outColor attribute
        sgs = cmds.listConnections(f"{material}.outColor", type="shadingEngine") or []

        if not sgs:
            sg = cmds.sets(
                renderable=True, noSurfaceShader=True, empty=True, name=f"{material}SG"
            )
            cmds.connectAttr(f"{material}.outColor", f"{sg}.surfaceShader", f=True)
            # print(f"Created new Shading Group: {sg}")
        else:
            sg = sgs[0]

        # 3. Assign the faces to the Shading Group
        # Using forceElement ensures it overrides any previous material assignments
        if faces:
            cmds.sets(faces, edit=True, forceElement=sg)
            # print(f"Assigned {material} to {len(faces)} {faces}faces.")
        else:
            cmds.warning("Face list is empty. Nothing assigned.")

    def query_material_data(objects):
        dict_material = {}

        for obj in objects:
            all_faces = cmds.ls(f"{obj}.f[*]", fl=True)

            shapes = cmds.listRelatives(obj, s=True, f=True) or []
            shading_groups = cmds.listConnections(shapes, type="shadingEngine") or []
            # Remove duplicates
            shading_groups = list(set(shading_groups))

            is_found_face = False

            # Check Material from face sets
            for face in all_faces:
                # 3. Check which Shading Group this specific face belongs to
                for sg in shading_groups:
                    if cmds.sets(face, im=sg):  # 'im' stands for 'isMember'
                        # 4. Find the Material (Surface Shader) attached to that SG
                        mats = cmds.listConnections(f"{sg}.surfaceShader")

                        if mats:
                            assigned_mat = mats[0]

                            if assigned_mat not in dict_material:
                                dict_material[assigned_mat] = []

                            dict_material[assigned_mat].append(face)

                            # print("found : ", assigned_mat, face)
                            is_found_face = True
                        else:
                            print("not found mats for face", face)
                        break

            # handle not found face sets
            if is_found_face is False:
                get_mat = get_materials_from_object(obj)[0]

                if get_mat not in dict_material:
                    dict_material[get_mat] = []

                dict_material[get_mat] += all_faces

        return dict_material

    def assign_material_to_objects(material, objects):
        # get faces from current selection

        sel = objects

        # convert selection to faces

        faces = cmds.polyListComponentConversion(sel, toFace=True)

        faces = cmds.filterExpand(faces, sm=34) or []

        if not faces:

            cmds.warning("No faces found in selection.")

            return

        # get / create shadingEngine

        sgs = cmds.listConnections(material + ".outColor", type="shadingEngine") or []

        if not sgs:

            sg = cmds.sets(
                renderable=True, noSurfaceShader=True, empty=True, name=material + "SG"
            )

            cmds.connectAttr(material + ".outColor", sg + ".surfaceShader", f=True)

        else:

            sg = sgs[0]

        # IMPORTANT: assign via selected faces only

        cmds.select(faces, r=True)

        try:
            cmds.sets(e=True, forceElement=sg)
        except:
            pass

    selection = selection
    print("### Validate Material Face Set ###")

    # query data
    dict_material = query_material_data(selection)

    # cleanup material
    assign_material_to_objects("lambert1", selection)

    # debug dict material
    print("Material Face Set Data: ")
    for material_name in dict_material.keys():
        faces_target = dict_material[material_name]

        list_models = set()
        for face in faces_target:
            model = face.split(".f[")[0]
            list_models.add(model)

        print(f"- Material: {material_name}, Model: {list_models}")

    # reassign material
    for material_name in dict_material.keys():
        faces_target = dict_material[material_name]

        assign_material_to_faces(material_name, faces_target)


def cleanup_materials():
    """
    Remove all material in the scene
    """
    # 1. Define the protected defaults
    defaults = ["initialShadingGroup", "initialParticleSE"]

    # 2. Get all Shading Groups in the scene
    # This is the "class" equivalent of finding materials
    shading_groups = cmds.ls(type="shadingEngine")

    # Filter out the defaults
    custom_groups = [sg for sg in shading_groups if sg not in defaults]

    if not custom_groups:
        print("Scene is already clean!")
        return

    for sg in custom_groups:
        # 3. Find everything assigned to this material
        members = cmds.sets(sg, q=True)

        if members:
            # Reassign members to the default Maya shader
            # 'forceElement' acts like a 'move to' command
            cmds.sets(members, edit=True, forceElement="initialShadingGroup")

        # 4. Find the actual Material (Lambert, Blinn, etc.) attached to the group
        # Material -> Shading Group -> Mesh
        material = cmds.listConnections(sg + ".surfaceShader")

        # 5. Delete the Group and the Material
        try:
            if material:
                cmds.delete(material)
            # Some groups might be read-only or referenced
            if cmds.objExists(sg):
                cmds.delete(sg)
        except:
            print(f"Skipped {sg} (likely a read-only or referenced node)")

    print("All custom materials removed. Scene reset to default Lambert.")


def fix_material_names(selection):
    if not selection:
        cmds.warning("Please Input objects to validate.")
        return

    # 2. Find unique Shading Engines and Materials
    shapes = cmds.listRelatives(selection, ad=True, type="mesh", fullPath=True) or []
    shading_groups = list(set(cmds.listConnections(shapes, type="shadingEngine") or []))

    if not shading_groups:
        cmds.warning("No shading groups found on selected objects.")
        return

    mat_fix_list = []  # For UI and renaming
    sg_fix_list = []  # For silent background renaming

    for sg in shading_groups:
        # Get the material
        materials = cmds.listConnections(f"{sg}.surfaceShader")
        if not materials:
            continue

        mat = materials[0]

        # Determine "Base Name" by stripping existing prefixes if they exist
        base_name = mat
        if mat.startswith("MTL_"):
            base_name = mat[4:]
        elif mat.startswith("M_"):
            base_name = mat[2:]

        target_mat = f"MTL_{base_name}"
        target_sg = f"M_{base_name}"

        # Track Material changes for the UI
        if mat != target_mat:
            mat_fix_list.append((mat, target_mat))

        # Track SG changes for background processing
        if sg != target_sg:
            sg_fix_list.append((sg, target_sg))

    # 3. Handle UI and Renaming
    if mat_fix_list:

        # Rename Materials (Confirmed)
        for old, new in mat_fix_list:
            try:
                cmds.rename(old, new)
            except Exception as e:
                cmds.warning(f"Failed to rename Material {old}: {e}")

        # Rename Shading Engines (Silent/Forced)
        for old, new in sg_fix_list:
            try:
                cmds.rename(old, new)
            except Exception as e:
                cmds.warning(f"Failed to rename Shading Engine {old}: {e}")

        cmds.inViewMessage(
            amg='<span style="color:#72ff72;">✔ Materials and SGs updated.</span>',
            pos="midCenter",
            fade=True,
            fst=1500,
        )

    # If materials are fine but SGs need work, just do SGs silently
    elif sg_fix_list:
        for old, new in sg_fix_list:
            cmds.rename(old, new)
        cmds.inViewMessage(
            amg='<span style="color:#72ff72;">✔ Shading Engines updated silently.</span>',
            pos="midCenter",
            fade=True,
            fst=1500,
        )

    else:
        # Everything is already correct
        cmds.inViewMessage(
            amg='<span style="color:#72ff72;">✔ All Material/SG names are valid.</span>',
            pos="midCenter",
            fade=True,
            fst=2000,
        )
