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
TYPE = "es_mouth_01"
NAME = "mouth"  # this name must match with your component folder , and Do not have any syntax.
DESCRIPTION = "Create simple mouth and jaw rig."


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

        self.list_loc = [
            "R_corner",
            "R_upB",
            "R_upA",
            "C_up",
            "L_upA",
            "L_upB",
            "L_corner",
            "L_lowB",
            "L_lowA",
            "C_low",
            "R_lowA",
            "R_lowB",
        ]

        self.save_transform = [
            "root",
            "centerRotate",
            # "controller",
            "jaw",
            "chin",
            "oral",
        ]

        self.save_transform += self.list_loc

    def addObjects(self):
        """Add the Guide Root, blade and locators"""
        self.root = self.addRoot()
        self.addLoc(name="centerRotate", parent=self.root, position=(0, 0, -2))
        self.addLoc(name="oral", parent=self.root, position=(0, 0, -3))

        # create jaw loc
        loc_jaw = self.addLoc(name="jaw", parent=self.root, position=(0, 0, -4))
        loc_chin = self.addLoc(name="chin", parent=self.root, position=(0, -3, 1))
        self.addDispCurve("curve", centers=[loc_jaw, loc_chin])
        pm.parent(loc_chin, loc_jaw)

        # create  loc
        list__loc_pos = [
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
        list__loc = [
            self.addLoc(name, self.root, position=list__loc_pos[i])
            for i, name in enumerate(self.list_loc)
        ]

        # constraint L to R side
        list_loc_L = []
        list_loc_R = []

        for loc in list__loc:
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
