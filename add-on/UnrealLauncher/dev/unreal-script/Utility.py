import unreal


def find_material():
    # get all materials in content browser
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    filter = unreal.ARFilter(
        class_names=["Material", "MaterialInstanceConstant"],
        recursive_paths=True,
        package_paths=["/Game"],
    )
    all_materials = [
        material.get_asset() for material in asset_registry.get_assets(filter=filter)
    ]

    print(f"# All Material in Content Browser {all_materials}")

    if all_materials is None:
        all_materials = []
    # get selection in content browser
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()

    for asset in selected_assets:
        if isinstance(asset, unreal.GeometryCache):
            print(
                f" # Search and Assign Material for Geometry Cache : {asset.get_name()}"
            )
            list_material_slot_names = asset.get_editor_property("material_slot_names")
            print(f"- All Exist Slot Name : {list_material_slot_names}")

            if "NoFaceSetName" in list_material_slot_names:
                error_message = (
                    f"Geometry Cache : {asset.get_name()} is have no facesets"
                )
                unreal.EditorDialog.show_message(
                    "No Faceset", error_message, unreal.AppMsgType.OK
                )

            # Store invalid / valid naming material
            list_invalid_slot_name = []
            list_valid_slot_name = []
            for i, slot_name in enumerate(list_material_slot_names):
                if str(slot_name).startswith("M_"):
                    list_valid_slot_name.append([i, str(slot_name)])
                else:
                    list_invalid_slot_name.append([i, str(slot_name)])

            if list_invalid_slot_name:
                unreal.EditorDialog.show_message(
                    "Invalid Slot Name",
                    f"Geometry Cache : {asset.get_name()} contained invalid slot name {list_invalid_slot_name}",
                    unreal.AppMsgType.OK,
                )

            print(f"- Valid Slot Name : {list_valid_slot_name}")
            print(f"- Invalid Slot Name : {list_invalid_slot_name}")

            # Auto Assign Material
            materials_new = asset.get_editor_property("materials")
            list_search_material_failed = []

            for slot_data in list_valid_slot_name:
                index, material_name = slot_data

                for search_material in all_materials:
                    if str(search_material.get_name()).lower() == material_name.lower():
                        # start update materials
                        materials_new[index] = search_material
                        print(
                            "- Assign Material : {} > {}".format(
                                material_name, search_material.get_name()
                            )
                        )
                    else:
                        list_search_material_failed.append(material_name)
                        print(
                            "- Assign Material : {} <Fail to find {}>".format(
                                material_name, search_material.get_name()
                            )
                        )

            asset.set_editor_property("materials", materials_new)

            if list_search_material_failed:
                unreal.EditorDialog.show_message(
                    "Find Material Faild",
                    f"Geometry Cache : {asset.get_name()} Find Material Failed :{list_search_material_failed}",
                    unreal.AppMsgType.OK,
                )
