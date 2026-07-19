from tmlib.core import (
    Scene,
    Utility,
    Transform,
    Connection,
    SkinWeight,
    Controller,
    File,
    QuickData,
    BlendShape,
)

from tmlib.ui.interface_template import ToolkitWindow
import pymel.core as pm
import maya.cmds as mc


class MainWindow(ToolkitWindow):
    def __init__(self):
        # Set-up Interface
        super(MainWindow, self).__init__("FlipAnimValue")

        self.ui.pushButton_flip_value.clicked.connect(self.execute_flip_value)
        self.ui.pushButton_uncheck_all.clicked.connect(self.reset_invert_checkboxes)

    def reset_invert_checkboxes(self):
        """Unchecks all transformation inversion checkboxes."""
        checkboxes = [
            self.ui.checkBox_invert_translate_x,
            self.ui.checkBox_invert_translate_y,
            self.ui.checkBox_invert_translate_z,
            self.ui.checkBox_invert_rotate_x,
            self.ui.checkBox_invert_rotate_y,
            self.ui.checkBox_invert_rotate_z,
            self.ui.checkBox_invert_scale_x,
            self.ui.checkBox_invert_scale_y,
            self.ui.checkBox_invert_scale_z,
        ]

        for cb in checkboxes:
            cb.setChecked(False)

    @Scene.undoable
    def execute_flip_value(self):
        selection = mc.ls(sl=1)
        # Get the dictionary: {"Leg_L": "Leg_R", "Arm_L": "Arm_R"}

        middle_keyword = "_M"
        result = Utility.find_flip_object(sel=selection, get_dict=True)

        for sel in selection:
            if sel.endswith(middle_keyword):
                result[sel] = sel

        if not result:
            mc.warning("No matching flip objects found.")
            return

        # Check UI states for inversion (assuming these are the names of your CheckBoxes)
        # Using 'q=True, v=True' to get the boolean state
        invert_tx = self.ui.checkBox_invert_translate_x.isChecked()
        invert_ty = self.ui.checkBox_invert_translate_y.isChecked()
        invert_tz = self.ui.checkBox_invert_translate_z.isChecked()
        invert_rx = self.ui.checkBox_invert_rotate_x.isChecked()
        invert_ry = self.ui.checkBox_invert_rotate_y.isChecked()
        invert_rz = self.ui.checkBox_invert_rotate_z.isChecked()
        invert_sx = self.ui.checkBox_invert_scale_x.isChecked()
        invert_sy = self.ui.checkBox_invert_scale_y.isChecked()
        invert_sz = self.ui.checkBox_invert_scale_z.isChecked()

        # Map attributes to their respective UI invert status
        invert_map = {
            "translateX": invert_tx,
            "translateY": invert_ty,
            "translateZ": invert_tz,
            "rotateX": invert_rx,
            "rotateY": invert_ry,
            "rotateZ": invert_rz,
            "scaleX": invert_sx,
            "scaleY": invert_sy,
            "scaleZ": invert_sz,
        }

        for source, target in result.items():
            if not mc.objExists(source) or not mc.objExists(target):
                continue

            # Get all keyable attributes (Translate, Rotate, Scale, and Custom)
            attrs = mc.listAttr(source, keyable=True) or []

            for attr in attrs:
                full_source = "{}.{}".format(source, attr)
                full_target = "{}.{}".format(target, attr)

                try:
                    # 1. Grab current values
                    val_source = mc.getAttr(full_source)
                    val_target = mc.getAttr(full_target)

                    # 2. Check if this specific attribute needs inversion
                    multiplier = -1 if invert_map.get(attr, False) else 1

                    # 3. Swap and Invert
                    # (L becomes R * mult) and (R becomes L * mult)
                    new_val_source = val_target * multiplier
                    new_val_target = val_source * multiplier

                    # 4. Apply and Keyframe
                    mc.setAttr(full_source, new_val_source)
                    mc.setAttr(full_target, new_val_target)

                    mc.setKeyframe(full_source)
                    mc.setKeyframe(full_target)

                except Exception as e:
                    # Skip locked or non-settable attributes
                    print("Skipping {}: {}".format(attr, e))
