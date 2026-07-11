from functools import partial

from mgear.shifter.component import guide
from mgear.core import pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

# from . import settingsUI as sui #for maya python 3 case , import ui class from settingUI.py

import os

from TonmaiToolkit.core import File

AUTHOR = "Natchapon Srisuk"
URL = "www.natchaponsrisuk.com"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_torso"
NAME = "torso" #this name must match with your component folder , and Do not have any syntax.
DESCRIPTION = "Lips Rig"


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

        self.save_transform = ["root","hips","spineStart","spineEnd","chestPos"]

    def addObjects(self):
        """Add the Guide Root, blade and locators"""

        self.root = self.addRoot()

        self.loc_hips = self.addLoc("hips",parent=self.root,position=(0,1.2,0),width=0.5,color=17)
        self.loc_spineStart = self.addLoc("spineStart",parent=self.loc_hips,position=(0,1.5,0),width=0.5,color=17)
        self.loc_spineEnd = self.addLoc("spineEnd",parent=self.loc_spineStart,position=(0,6,0),width=0.5,color=17)
        self.loc_chestPos = self.addLoc("chestPos",parent=self.loc_spineEnd,position=(0,6.1,0),color=6,width=0.25)

        self.addDispCurve("curve",[self.loc_hips,self.loc_spineStart,self.loc_spineEnd,self.loc_chestPos])

    def addParameters(self):
        """Add the configurations settings"""

        self.pType = self.addParam("mode", "long", 0, 0)
        self.pBlend = self.addParam("blend", "double", 1, 0, 1)
        self.pNeutralPose = self.addParam("neutralpose", "bool", True)
        self.pIkRefArray = self.addParam("ikrefarray", "string", "")
        self.pUseIndex = self.addParam("useIndex", "bool", False)
        self.pParentJointIndex = self.addParam("parentJointIndex", "long", -1, None, None)

        # add custom parameter
        self.addParam("enable_breast_rig", "bool", False,keyable=True)
        self.addParam("spine_amount", "long", 5,keyable=True)

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

        self.populateCheck(self.settingsTab.ui.checkBox_enable_breast_rig, "enable_breast_rig")
        self.settingsTab.ui.spinBox_spine_amount.setValue(self.root.attr("spine_amount").get())

        self.settingsTab.ui.checkBox_enable_breast_rig.stateChanged.connect(
            partial(self.updateCheck,
                    self.settingsTab.ui.checkBox_enable_breast_rig,
                    "enable_breast_rig"))

        self.settingsTab.ui.spinBox_spine_amount.valueChanged.connect(
            partial(self.updateSpinBox,
                    self.settingsTab.ui.spinBox_spine_amount,
                    "spine_amount")
        )

    def create_componentLayout(self):

        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        pass

        # self.settingsTab.ui.ikfk_slider.valueChanged.connect(
        #     partial(self.updateSlider, self.settingsTab.ui.ikfk_slider, "blend"))
        # self.settingsTab.ui.ikfk_spinBox.valueChanged.connect(
        #     partial(self.updateSlider, self.settingsTab.ui.ikfk_spinBox, "blend"))
        #
        # self.settingsTab.ui.mode_comboBox.currentIndexChanged.connect(
        #     partial(self.updateComboBox,
        #             self.settingsTab.ui.mode_comboBox,
        #             "mode"))
        #
        # self.settingsTab.ui.neutralPose_checkBox.stateChanged.connect(
        #     partial(self.updateCheck,
        #             self.settingsTab.ui.neutralPose_checkBox,
        #             "neutralpose"))
        #        # self.settingsTab.ui.ikRefArrayAdd_pushButton.clicked.connect(
        #     partial(self.addItem2listWidget,
        #             self.settingsTab.ui.ikRefArray_listWidget,
        #             "ikrefarray"))
        # self.settingsTab.ui.ikRefArrayRemove_pushButton.clicked.connect(
        #     partial(self.removeSelectedFromListWidget,
        #             self.settingsTab.ui.ikRefArray_listWidget,
        #             "ikrefarray"))
        # self.settingsTab.ui.ikRefArray_listWidget.installEventFilter(self)



    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ui.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)