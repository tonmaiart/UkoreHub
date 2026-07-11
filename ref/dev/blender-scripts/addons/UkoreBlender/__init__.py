bl_info = {
    "name": "Ukore Blender",
    "author": "Natchapon Srisuk",
    "version": (1, 0),
    "blender": (5, 1, 0),
    "location": "View3d > Tool",
    "warning": "",
    "wiki_url": "https://www.facebook.com/natchapon.srisuk.2025/",
    "category": "Use for get alembic cache structure , update and replace exist model without changing material.",
}

# import main modules
import os
import sys
import importlib
import bpy

# append paths for external modules
sys.path.append(r"G:\My Drive\Mellowstar\dev\drive-scripts")
sys.path.append(r"G:\My Drive\Mellowstar\dev\maya-scripts")

# import relative modules
from . import properties, operators, operators_render, panels,operators_rig

# import main logic
import UkoreMaya
from UkoreMaya.core import Logic

# reload modules
importlib.reload(Logic)
importlib.reload(properties)
importlib.reload(operators)
importlib.reload(operators_render)
importlib.reload(operators_rig)
importlib.reload(panels)


# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

# รวมคลาสทั้งหมดจากแต่ละไฟล์
all_classes = []
all_classes.extend(operators.operator_classes) # general commands
all_classes.extend(operators_render.operator_classes) # render commands
all_classes.extend(operators_rig.operator_classes) # rig commands
all_classes.extend(panels.panel_classes) # ui interface

def register():
    # Register all classes
    for cls in all_classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            # Catch errors if a class is already registered (e.g., during reload)
            print(f"Warning: Could not register class {cls.__name__}. {e}")

    bpy.types.Scene.my_props = bpy.props.PointerProperty(
        type=operators.operator_classes[0]
    )


def unregister():
    # 1. Unregister all classes in reverse order
    for cls in reversed(all_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            # Ignore errors if a class is not registered
            pass
    del bpy.types.Scene.my_props


if __name__ == "__main__":
    register()
