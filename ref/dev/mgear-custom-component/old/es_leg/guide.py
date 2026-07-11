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
URL = "www.natchaponsrisuk.com"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_leg" #this name must match with your component folder ,
NAME = "Leg"  # and Do not have any syntax.
DESCRIPTION = "LimbRig"

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

    def postInit(self):
        """Initialize the position for the guide"""

        self.save_transform = ["root","elbow","wrist","eff","inner","outer","heel","tip"]

    def addObjects(self):
        """Add the Guide Root, blade and locators"""
        self.root = self.addRoot()

        self.position = [(0, -4, 0), (0, -8, 0), (0, -9, 1)]
        self.piv_pos = [(-1,-9,1),(1,-9,1),(0,-9,-0.5),(0,-9,2)]
        self.root.attr("is_arm").set(False)

        self.loc_elbow = self.addLoc(name="elbow",parent=self.root,position=self.position[0])
        self.loc_wrist = self.addLoc(name="wrist",parent=self.loc_elbow,position=self.position[1])
        self.loc_eff = self.addLoc(name="eff",parent=self.loc_wrist,position=self.position[2])

        self.addLoc(name="inner",parent=self.loc_eff,position=self.piv_pos[0])
        self.addLoc(name="outer",parent=self.loc_eff,position=self.piv_pos[1])
        self.addLoc(name="heel",parent=self.loc_eff,position=self.piv_pos[2])
        self.addLoc(name="tip",parent=self.loc_eff,position=self.piv_pos[3])

        self.addDispCurve("crv",[self.root,self.loc_elbow,self.loc_wrist,self.loc_eff])

    def addParameters(self):
        """Add the configurations settings"""

        self.pType = self.addParam("mode", "long", 0, 0)
        self.pBlend = self.addParam("blend", "double", 1, 0, 1)
        self.pNeutralPose = self.addParam("neutralpose", "bool", True)
        self.pIkRefArray = self.addParam("ikrefarray", "string", "")
        self.pUseIndex = self.addParam("useIndex", "bool", False)
        self.pParentJointIndex = self.addParam(
            "parentJointIndex", "long", -1, None, None)

        # add custom parameter
        self.addParam("fk_as_start", "bool", False,keyable=True)
        self.addParam("use_world_pole", "bool", True,keyable=True)
        self.addParam("ribbon_up_enable", "bool", True,keyable=True)
        self.addParam("ribbon_low_enable", "bool", True,keyable=True)
        self.addParam("is_arm", "bool", False,keyable=True)
        self.addParam("pole_distance", "float", 1.5,keyable=True)
        # self.addParam("enable_effector_control", "bool", True,keyable=True)

        self.addEnumParam("world_pole_axis", ["x","y","z","-x","-y","-z"], 2)

class settingsTab(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)

        dir_path = os.path.dirname(__file__)
        ui_path = os.path.join(dir_path,"settingsUI.ui")
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

        # populate component setting
        self.populateCheck(self.settingsTab.ui.checkBox_fk_as_start,"fk_as_start")
        self.populateCheck(self.settingsTab.ui.checkBox_use_world_pole,"use_world_pole")
        self.populateCheck(self.settingsTab.ui.checkBox_ribbon_up_enable,"ribbon_up_enable")
        self.populateCheck(self.settingsTab.ui.checkBox_ribbon_low_enable,"ribbon_low_enable")

        self.settingsTab.ui.doubleSpinBox_pole_distance.setValue(self.root.attr("pole_distance").get())
        self.settingsTab.ui.comboBox_world_pole_axis.setCurrentIndex(self.root.attr("world_pole_axis").get())

    def create_componentLayout(self):
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        self.settingsTab.ui.checkBox_fk_as_start.stateChanged.connect(partial(self.updateCheck,self.settingsTab.ui.checkBox_fk_as_start,"fk_as_start"))
        self.settingsTab.ui.checkBox_use_world_pole.stateChanged.connect(partial(self.updateCheck,self.settingsTab.ui.checkBox_use_world_pole,"use_world_pole"))
        self.settingsTab.ui.checkBox_ribbon_up_enable.stateChanged.connect(partial(self.updateCheck,self.settingsTab.ui.checkBox_ribbon_up_enable,"ribbon_up_enable"))
        self.settingsTab.ui.checkBox_ribbon_low_enable.stateChanged.connect(partial(self.updateCheck,self.settingsTab.ui.checkBox_ribbon_low_enable,"ribbon_low_enable"))

        self.settingsTab.ui.doubleSpinBox_pole_distance.valueChanged.connect(partial(self.updateSpinBox, self.settingsTab.ui.doubleSpinBox_pole_distance, "pole_distance"))

        self.settingsTab.ui.comboBox_world_pole_axis.currentIndexChanged.connect(partial(self.updateComboBox,self.settingsTab.ui.comboBox_world_pole_axis,"world_pole_axis"))

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ui.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)