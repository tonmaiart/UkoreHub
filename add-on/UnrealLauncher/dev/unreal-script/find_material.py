import unreal


def find_material():
    sel = unreal.EditorUtilityLibrary.get_selected_assets()
    for s in sel:
        if isinstance(s, unreal.GeometryCache):
            unreal.log(f"Geometry Cache : {s.get_name()}")

            materials = s.get_editor_property("materials")

            for i, mat in enumerate(materials):
                if mat:
                    unreal.log(f" Slot {i} : {mat.get_name()}")
                else:
                    unreal.log(f" Slot {i} : <None>")


def get_material_by_input_name(material_name):
    # 1. Access the Asset Registry
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    # 2. Filter for Materials only to make the search faster
    # Note: Use 'Material' for base materials or 'MaterialInterface' to include Instances
    filter = unreal.ARFilter(
        class_names=["Material", "MaterialInstanceConstant"], recursive_classes=True
    )

    # 3. Get all assets that match the filter
    all_assets = asset_registry.get_assets(filter)

    # 4. Loop through to find a name match
    for asset_data in all_assets:
        if str(asset_data.asset_name) == material_name:
            # Load the actual object into memory
            material_object = asset_data.get_asset()
            print(f"Found and loaded: {material_object.get_path_name()}")
            return material_object

    print(f"Error: Material with name '{material_name}' not found.")
    return None


def update_parent_material(new_material_name=""):
    sel = unreal.EditorUtilityLibrary.get_selected_assets()
    new_material = get_material_by_input_name(new_material_name)

    for s in sel:
        if isinstance(s, unreal.MaterialInstance):
            s.set_editor_property("parent", new_material)


update_parent_material(new_material_name="MI_Kakfa_Normal")
