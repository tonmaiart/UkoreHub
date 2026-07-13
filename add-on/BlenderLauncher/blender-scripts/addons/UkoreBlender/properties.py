import bpy

# ------------------------------------------------------------------------
# Item for folder entries
# ------------------------------------------------------------------------
class SIMPLE_FolderItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()


# ------------------------------------------------------------------------
# UI List for Folder Entries
# ------------------------------------------------------------------------
class SIMPLE_UL_FolderList(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # We can ignore most arguments since we only display the item name and icon
        layout.label(text=item.name, icon="FILE_FOLDER")


# List of all property and UI list classes to register
property_classes = [
    SIMPLE_FolderItem,
    SIMPLE_UL_FolderList,
]

# Function to register custom properties (must be called from __init__.py)
def register_props():
    bpy.types.Scene.simple_folder_path = bpy.props.StringProperty(
        name="Folder Path", subtype='DIR_PATH', default=""
    )
    bpy.types.Scene.simple_folder_items = bpy.props.CollectionProperty(
        type=SIMPLE_FolderItem
    )
    bpy.types.Scene.simple_folder_index = bpy.props.IntProperty(
        name="Folder Index", default=0
    )

def unregister_props():
    del bpy.types.Scene.simple_folder_path
    del bpy.types.Scene.simple_folder_items
    del bpy.types.Scene.simple_folder_index