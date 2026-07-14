from functools import partial
import pymel.core as pm

import mgear.core.transform
from mgear.shifter.component import guide
from mgear.core import pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from TonmaiToolkit.core import File

import os

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

# from . import settingsUI as sui #for maya python 3 case , import ui class from settingUI.py

AUTHOR = "Natchapon Srisuk"
URL = "https://www.facebook.com/natchapon.srisuk.2025"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_foot_01"  # this name must match with your component folder ,
NAME = "foot"  # and Do not have any syntax.
DESCRIPTION = (
    "Foot Rig with reverse ik systems. Have Roll ik controller for easier animate."
)


class Guide(guide.ComponentGuide):
    """Component Guide Class"""

    compType = TYPE
    compName = NAME
    description = DESCRIPTION
    compSide = "L"

    author = AUTHOR
    url = URL
    email = EMAIL
    version = VERSION

    connectors = ["es_leg_01"]

    def postInit(self):
        """Initialize the position for the guide"""

        self.save_transform = [
            "root",
            "inner",
            "outer",
            "heel",
            "ball",
            "tip",
        ]

    def addObjects(self):
        """Add the Guide Root, blade and locators"""
        self.root = self.addRoot()

        self.loc_inner = self.addLoc(
            name="inner", parent=self.root, position=(-1, -1, 0)
        )
        self.loc_outer = self.addLoc(
            name="outer", parent=self.root, position=(1, -1, 0)
        )
        self.loc_heel = self.addLoc(name="heel", parent=self.root, position=(0, -1, -2))
        self.loc_ball = self.addLoc(name="ball", parent=self.root, position=(0, -1, 2))
        self.loc_tip = self.addLoc(name="tip", parent=self.root, position=(0, -1, 3))

        self.addDispCurve("crv", [self.root, self.loc_inner])
        self.addDispCurve("crv", [self.root, self.loc_outer])
        self.addDispCurve("crv", [self.root, self.loc_heel])
        self.addDispCurve("crv", [self.root, self.loc_ball])
        self.addDispCurve("crv", [self.loc_ball, self.loc_tip])

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

        # add custom parameter
        self.addParam("fk_as_start", "bool", False, keyable=True)
        self.addParam("use_world_pole", "bool", True, keyable=True)
        self.addParam("ribbon_up_enable", "bool", True, keyable=True)
        self.addParam("ribbon_low_enable", "bool", True, keyable=True)
        self.addParam("is_arm", "bool", False, keyable=True)
        self.addParam("pole_distance", "float", 1.5, keyable=True)
        # self.addParam("enable_effector_control", "bool", True,keyable=True)

        self.addEnumParam("world_pole_axis", ["x", "y", "z", "-x", "-y", "-z"], 5)


class settingsTab(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)

        dir_path = os.path.dirname(__file__)
        ui_path = os.path.join(dir_path, "settingsUI.ui")
        self.ui = File.load_ui(ui_path)

        # self.setupUi(self.ui)


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

        # populate connections in main settings
        for cnx in Guide.connectors:
            self.mainSettingsTab.connector_comboBox.addItem(cnx)
        cBox = self.mainSettingsTab.connector_comboBox
        self.connector_items = [cBox.itemText(i) for i in range(cBox.count())]
        currentConnector = self.root.attr("connector").get()
        if currentConnector not in self.connector_items:
            self.mainSettingsTab.connector_comboBox.addItem(currentConnector)
            self.connector_items.append(currentConnector)
            pm.displayWarning(
                "The current connector: %s, is not a valid "
                "connector for this component. "
                "Build will Fail!!"
            )
        comboIndex = self.connector_items.index(currentConnector)
        self.mainSettingsTab.connector_comboBox.setCurrentIndex(comboIndex)

        # populate component setting
        self.populateCheck(self.settingsTab.ui.checkBox_fk_as_start, "fk_as_start")
        self.populateCheck(
            self.settingsTab.ui.checkBox_use_world_pole, "use_world_pole"
        )
        self.populateCheck(
            self.settingsTab.ui.checkBox_ribbon_up_enable, "ribbon_up_enable"
        )
        self.populateCheck(
            self.settingsTab.ui.checkBox_ribbon_low_enable, "ribbon_low_enable"
        )

        self.settingsTab.ui.doubleSpinBox_pole_distance.setValue(
            self.root.attr("pole_distance").get()
        )
        self.settingsTab.ui.comboBox_world_pole_axis.setCurrentIndex(
            self.root.attr("world_pole_axis").get()
        )

    def create_componentLayout(self):
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        self.settingsTab.ui.checkBox_fk_as_start.stateChanged.connect(
            partial(
                self.updateCheck,
                self.settingsTab.ui.checkBox_fk_as_start,
                "fk_as_start",
            )
        )
        self.settingsTab.ui.checkBox_use_world_pole.stateChanged.connect(
            partial(
                self.updateCheck,
                self.settingsTab.ui.checkBox_use_world_pole,
                "use_world_pole",
            )
        )
        self.settingsTab.ui.checkBox_ribbon_up_enable.stateChanged.connect(
            partial(
                self.updateCheck,
                self.settingsTab.ui.checkBox_ribbon_up_enable,
                "ribbon_up_enable",
            )
        )
        self.settingsTab.ui.checkBox_ribbon_low_enable.stateChanged.connect(
            partial(
                self.updateCheck,
                self.settingsTab.ui.checkBox_ribbon_low_enable,
                "ribbon_low_enable",
            )
        )

        self.settingsTab.ui.doubleSpinBox_pole_distance.valueChanged.connect(
            partial(
                self.updateSpinBox,
                self.settingsTab.ui.doubleSpinBox_pole_distance,
                "pole_distance",
            )
        )

        self.settingsTab.ui.comboBox_world_pole_axis.currentIndexChanged.connect(
            partial(
                self.updateComboBox,
                self.settingsTab.ui.comboBox_world_pole_axis,
                "world_pole_axis",
            )
        )

        self.mainSettingsTab.connector_comboBox.currentIndexChanged.connect(
            partial(
                self.updateConnector,
                self.mainSettingsTab.connector_comboBox,
                self.connector_items,
            )
        )

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ui.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)
