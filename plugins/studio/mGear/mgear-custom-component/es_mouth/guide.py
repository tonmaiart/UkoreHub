import os.path
from functools import partial
import pymel.core as pm

from TonmaiToolkit.core import Misc, File, Connection

from mgear.shifter.component import guide
from mgear.core import pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

# from . import settingsUI as sui #for maya python 3 case , import ui class from settingUI.py

AUTHOR = "Natchapon Srisuk"
URL = "www.natchaponsrisuk.com"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_mouth"
NAME = "mouth"  # this name must match with your component folder , and Do not have any syntax.
DESCRIPTION = "Create advance mouth and jaw rig. Please check the component setting tab for more build option."


class Guide(guide.ComponentGuide):
    """Component Guide Class"""

    compType = TYPE
    compName = NAME
    description = DESCRIPTION

    author = AUTHOR
    url = URL
    email = EMAIL
    version = VERSION

    def postInit(self):
        """Initialize the position for the guide"""

        self.list_scl_loc = [
            "R_cornerScl",
            "R_upSclB",
            "R_upSclA",
            "C_upScl",
            "L_upSclA",
            "L_upSclB",
            "L_cornerScl",
            "L_lowSclB",
            "L_lowSclA",
            "C_lowScl",
            "R_lowSclA",
            "R_lowSclB",
        ]
        self.list_rim_loc = [
            "R_cornerRim",
            "R_upRimB",
            "R_upRimA",
            "C_upRim",
            "L_upRimA",
            "L_upRimB",
            "L_cornerRim",
            "L_lowRimB",
            "L_lowRimA",
            "C_lowRim",
            "R_lowRimA",
            "R_lowRimB",
        ]
        self.list_cheek_loc = [
            "R_cornerCheek",
            "R_upCheekB",
            "R_upCheekA",
            "C_upCheek",
            "L_upCheekA",
            "L_upCheekB",
            "L_cornerCheek",
            "L_lowCheekB",
            "L_lowCheekA",
            "C_lowCheek",
            "R_lowCheekA",
            "R_lowCheekB",
        ]

        self.save_transform = [
            "root",
            "centerRotate",
            "controller",
            "jaw",
            "chin",
            "oral",
        ]
        self.save_transform += self.list_scl_loc
        self.save_transform += self.list_rim_loc
        self.save_transform += self.list_cheek_loc

    def addObjects(self):
        """Add the Guide Root, blade and locators"""

        def mirror_left_to_right(obj_list):
            count = len(obj_list)
            if count < 2:
                pm.warning("You must provide at least 2 objects.")
                return

            mid_index = count // 2

            if count % 2 == 1:
                # Odd count: skip the middle item
                right_objs = obj_list[:mid_index]
                left_objs = obj_list[mid_index + 1 :]
            else:
                # Even count: split evenly
                right_objs = obj_list[:mid_index]
                left_objs = obj_list[mid_index:]

            if len(right_objs) != len(left_objs):
                pm.warning("Left and right sides must have the same number of objects.")
                return

            # We reverse the left list so it mirrors in matching order
            left_objs = left_objs[::-1]

            for right_name, left_name in zip(right_objs, left_objs):
                right = pm.PyNode(right_name)
                left = pm.PyNode(left_name)

                # Create multDoubleLinear to invert translateX
                mdl = pm.createNode(
                    "multDoubleLinear", name=f"{left}_to_{right}_mirrorTx_mdl"
                )
                mdl.input2.set(-1)

                # Connect left.tx → mdl.input1 → right.tx
                left.translateX >> mdl.input1
                mdl.output >> right.translateX

                # Connect all other attributes directly
                for attr in [
                    "translateY",
                    "translateZ",
                    "rotateX",
                    "rotateY",
                    "rotateZ",
                    "scaleX",
                    "scaleY",
                    "scaleZ",
                ]:
                    try:
                        getattr(left, attr) >> getattr(right, attr)
                    except Exception:
                        pm.warning(f"Could not connect {left}.{attr} to {right}.{attr}")

        dict_mouth_loc = {}

        self.root = self.addRoot()

        self.addLoc(name="centerRotate", parent=self.root, position=(0, 0, -2))
        self.addLoc(name="oral", parent=self.root, position=(0, 0, -3))

        # create controller loc
        self.addLoc(name="controller", parent=self.root, position=(0, 0, 4))

        # create jaw loc
        loc_jaw = self.addLoc(name="jaw", parent=self.root, position=(0, 0, -4))
        loc_chin = self.addLoc(name="chin", parent=self.root, position=(0, -3, 1))
        self.addDispCurve("curve", centers=[loc_jaw, loc_chin])
        pm.parent(loc_chin, loc_jaw)

        # create rim loc
        list_rim_loc_pos = [
            (-2.0, 0.0, 1.0),
            (-1.0, 1.0, 1.0),
            (-0.5, 1.0, 1.0),
            (0.0, 1.0, 1.0),
            (0.5, 1.0, 1.0),
            (1.0, 1.0, 1.0),
            (2.0, 0.0, 1.0),
            (1.0, -1.0, 1.0),
            (0.5, -1.0, 1.0),
            (0.0, -1.0, 1.0),
            (-0.5, -1.0, 1.0),
            (-1.0, -1.0, 1.0),
        ]
        list_rim_loc = [
            self.addLoc(name, self.root, position=list_rim_loc_pos[i])
            for i, name in enumerate(self.list_rim_loc)
        ]
        self.addDispCurve("curve", centers=list_rim_loc + [list_rim_loc[0]])

        # create scl loc
        list_scl_loc_pos = [
            (-1.5, 0.0, 1.0),
            (-1.0, 0.5, 1.0),
            (-0.5, 0.5, 1.0),
            (0.0, 0.5, 1.0),
            (0.5, 0.5, 1.0),
            (1.0, 0.5, 1.0),
            (1.5, 0.0, 1.0),
            (1.0, -0.5, 1.0),
            (0.5, -0.5, 1.0),
            (0.0, -0.5, 1.0),
            (-0.5, -0.5, 1.0),
            (-1.0, -0.5, 1.0),
        ]
        list_scl_loc = [
            self.addLoc(name, self.root, position=list_scl_loc_pos[i])
            for i, name in enumerate(self.list_scl_loc)
        ]

        for loc_scl, loc_rim in zip(list_scl_loc, list_rim_loc):
            pm.parent(loc_scl, loc_rim)
            self.addDispCurve("curve", centers=[loc_scl, loc_rim])

        # create corner loc
        list_corner_loc_pos = [
            (-2.5, 0.0, 1.0),
            (-2.5, 1.5, 1.0),
            (-1.25, 1.5, 1.0),
            (0.0, 1.5, 1.0),
            (1.25, 1.5, 1.0),
            (2.5, 1.5, 1.0),
            (2.5, 0.0, 1.0),
            (2.5, -1.5, 1.0),
            (1.25, -1.5, 1.0),
            (0.0, -1.5, 1.0),
            (-1.25, -1.5, 1.0),
            (-2.5, -1.5, 1.0),
        ]
        list_cheek_loc = [
            self.addLoc(name, self.root, position=list_corner_loc_pos[i])
            for i, name in enumerate(self.list_cheek_loc)
        ]
        # self.addDispCurve("curve", centers=list_cheek_loc+[list_cheek_loc[0]])

        for loc_cheek, loc_rim in zip(list_cheek_loc, list_rim_loc):
            pm.parent(loc_cheek, loc_rim)
            self.addDispCurve("curve", centers=[loc_cheek, loc_rim])

        # connect invert
        # for part in dict_mouth_loc.keys():
        #     for i in range(2):
        #         list_loc = dict_mouth_loc[part][i]
        #         mirror_left_to_right(list_loc)

        # constraint L to R side
        list_loc_L = []
        list_loc_R = []

        print(len(list_rim_loc))
        print(list_loc_L)
        print(list_loc_R)

        for loc in list_rim_loc + list_cheek_loc + list_scl_loc:
            loc_L = loc.shortName()

            if pm.objExists(loc_L.replace("L_", "R_")) and "L_" in loc_L:
                list_loc_L.append(loc_L)
                list_loc_R.append(loc_L.replace("L_", "R_"))

        for loc_L, loc_R in zip(list_loc_L, list_loc_R):
            loc_L = pm.PyNode(loc_L)
            loc_R = pm.PyNode(loc_R)

            node_decomp_1 = pm.createNode("decomposeMatrix")
            node_decomp_2 = pm.createNode("decomposeMatrix")
            node_md = pm.createNode("multiplyDivide")
            node_compose = pm.createNode("composeMatrix")
            node_mm = pm.createNode("multMatrix")

            loc_L.worldMatrix[0] >> node_decomp_1.inputMatrix
            node_decomp_1.outputTranslate >> node_md.input1

            node_md.input2X.set(-1)

            node_md.output >> node_compose.inputTranslate
            node_compose.outputMatrix >> node_mm.matrixIn[0]
            loc_R.parentInverseMatrix[0] >> node_mm.matrixIn[1]
            node_mm.matrixSum >> node_decomp_2.inputMatrix

            node_decomp_2.outputTranslate >> loc_R.translate

            # pm.pointConstraint(loc_L, loc_R, mo=True)

    def addParameters(self):
        """Add the configurations settings"""

        self.pType = self.addParam("mode", "long", 0, 0)
        self.pBlend = self.addParam("blend", "double", 1, 0, 1)
        self.pNeutralPose = self.addParam("neutralpose", "bool", True)
        self.pIkRefArray = self.addParam("ikrefarray", "string", "")
        self.pUseIndex = self.addParam("useIndex", "bool", False)
        self.pParentJointIndex = self.addParam(
            "parentJointIndex", "long", -1, None, None
        )

        # custom attribute
        self.addParam("enable_zipper", "bool", False, keyable=True)
        self.addParam("enable_sliding", "bool", False, keyable=True)
        self.addParam("auto_pinch", "bool", False, keyable=True)
        self.addParam("extra_loop", "bool", False, keyable=True)
        self.addParam("sliding_object", "string", "slide_mesh", keyable=True)
        self.addParam("loop_amount", "long", 1, keyable=True)


class settingsTab(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)

        dir_path = os.path.dirname(__file__)
        ui_path = os.path.join(dir_path, "settingsUI.ui")
        self.ui = File.load_ui(ui_path)

        # self.setupUi(self.ui)

        self.ui.pushButton_mirror_guide.clicked.connect(self.mirror_guide)

    def mirror_guide(self):
        selection = pm.ls(sl=1)

        for sel in selection:
            if not hasattr(sel, "isGearGuide"):
                raise Exception("Selected are not mGear Guide.")

            if sel.isGearGuide.get() is not True:
                raise Exception("Selected Guide not enable checked.")

            if "L_" not in str(sel):
                raise Exception("Selected Guide is not side L")

            # mirror guide
            world_L_position = pm.xform(sel, q=1, ws=1, t=1)
            world_L_position[0] = world_L_position[0] * -1
            world_R_postion = world_L_position

            pm.xform(str(sel.replace("L_", "R_")), ws=1, t=world_R_postion)


class componentSettings(MayaQWidgetDockableMixin, guide.componentMainSettings):
    def __init__(self, parent=None):
        self.toolName = TYPE
        # Delete old instances of the component settings window.
        pyqt.deleteInstances(self, MayaQDockWidget)

        super(componentSettings, self).__init__(parent=parent)
        self.settingsTab = settingsTab()

        self.setup_componentSettingWindow()
        self.create_componentControls()
        self.populate_componentControls()
        self.create_componentLayout()
        self.create_componentConnections()

    def setup_componentSettingWindow(self):
        self.mayaMainWindow = pyqt.maya_main_window()

        self.setObjectName(self.toolName)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(TYPE)
        self.resize(350, 350)

    def create_componentControls(self):
        return

    def populate_componentControls(self):
        """Populate Controls

        Populate the controls values from the custom attributes of the
        component.

        """
        # populate tab
        self.tabs.insertTab(1, self.settingsTab.ui, "Component Settings")

        self.settingsTab.ui.checkBox_auto_pinch.setChecked(
            self.root.attr("auto_pinch").get()
        )
        self.settingsTab.ui.checkBox_enable_zipper.setChecked(
            self.root.attr("enable_zipper").get()
        )

        self.settingsTab.ui.checkBox_enable_sliding.setChecked(
            self.root.attr("enable_sliding").get()
        )
        self.settingsTab.ui.lineEdit_sliding_object.setText(
            self.root.attr("sliding_object").get()
        )

        self.settingsTab.ui.checkBox_extra_loop.setChecked(
            self.root.attr("extra_loop").get()
        )
        self.settingsTab.ui.spinBox_loop_amount.setValue(
            self.root.attr("loop_amount").get()
        )

    def create_componentLayout(self):
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        self.settingsTab.ui.checkBox_enable_zipper.clicked.connect(
            partial(
                self.updateCheck,
                self.settingsTab.ui.checkBox_enable_zipper,
                "enable_zipper",
            )
        )

        self.settingsTab.ui.checkBox_auto_pinch.clicked.connect(
            partial(
                self.updateCheck, self.settingsTab.ui.checkBox_auto_pinch, "auto_pinch"
            )
        )

        self.settingsTab.ui.checkBox_enable_sliding.clicked.connect(
            partial(
                self.updateCheck,
                self.settingsTab.ui.checkBox_enable_sliding,
                "enable_sliding",
            )
        )

        self.settingsTab.ui.spinBox_loop_amount.valueChanged.connect(
            partial(
                self.updateSpinBox,
                self.settingsTab.ui.spinBox_loop_amount,
                "loop_amount",
            )
        )

        self.settingsTab.ui.checkBox_extra_loop.clicked.connect(
            partial(
                self.updateCheck, self.settingsTab.ui.checkBox_extra_loop, "extra_loop"
            )
        )

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)
