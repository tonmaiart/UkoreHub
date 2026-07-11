from mgear.shifter.component import guide
from mgear.core import pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

from TonmaiToolkit.core import File

import os

AUTHOR = "Natchapon Srisuk"
URL = "www.natchaponsrisuk.com"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_brows"  # this name must match with your component folder , and Do not have any syntax.
NAME = "brows"
DESCRIPTION = "Rig for brows (both left and right side)"


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

        self.save_transform = [
            "root",
            "L_brow_01",
            "L_brow_02",
            "L_brow_03",
            "L_brow_04",
            "R_brow_01",
            "R_brow_02",
            "R_brow_03",
            "R_brow_04",
        ]

    def addObjects(self):
        """Add the Guide Root, blade and locators"""

        self.root = self.addRoot()

        self.L_brow_01 = self.addLoc("L_brow_01", self.root, (1, 0, 0))
        self.L_brow_02 = self.addLoc("L_brow_02", self.root, (1.5, 0, 0))
        self.L_brow_03 = self.addLoc("L_brow_03", self.root, (2, 0, 0))
        self.L_brow_04 = self.addLoc("L_brow_04", self.root, (2.5, 0, 0))

        self.R_brow_01 = self.addLoc("R_brow_01", self.root, (-1, 0, 0))
        self.R_brow_02 = self.addLoc("R_brow_02", self.root, (-1.5, 0, 0))
        self.R_brow_03 = self.addLoc("R_brow_03", self.root, (-2, 0, 0))
        self.R_brow_04 = self.addLoc("R_brow_04", self.root, (-2.5, 0, 0))

        self.R_brow_01.scaleX.set(-1)
        self.R_brow_02.scaleX.set(-1)
        self.R_brow_03.scaleX.set(-1)
        self.R_brow_04.scaleX.set(-1)

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

        # custom param
        self.localRig = self.addParam("localRig", "bool", False, keyable=True)


class settingsTab(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)

        dir_path = os.path.dirname(__file__)
        ui_path = os.path.join(dir_path, "settingsUI.ui")
        self.ui = File.load_ui(ui_path)


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

        return

    def create_componentLayout(self):

        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        pass

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)
