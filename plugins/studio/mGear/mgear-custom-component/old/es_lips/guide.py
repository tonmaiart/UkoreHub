from functools import partial
import pymel.core as pm

from mgear.shifter.component import guide
from mgear.core import pyqt
from mgear.vendor.Qt import QtWidgets, QtCore

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget

from . import settingsUI as sui #for maya python 3 case , import ui class from settingUI.py

AUTHOR = "Natchapon Srisuk"
URL = "www.natchaponsrisuk.com"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_lips"
NAME = "lips" #this name must match with your component folder , and Do not have any syntax.
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

        self.save_transform = ["root","bigScale","controller","jaw"]

        self.save_transform += ["up_piv_{}".format(i+1) for i in range(7)]
        self.save_transform += ["up_01_{}".format(i+1) for i in range(7)]
        self.save_transform += ["up_02_{}".format(i+1) for i in range(7)]
        self.save_transform += ["up_03_{}".format(i+1) for i in range(7)]

        self.save_transform += ["low_piv_{}".format(i+1) for i in range(5)]
        self.save_transform += ["low_01_{}".format(i+1) for i in range(5)]
        self.save_transform += ["low_02_{}".format(i+1) for i in range(5)]
        self.save_transform += ["low_03_{}".format(i+1) for i in range(5)]


    def addObjects(self):
        """Add the Guide Root, blade and locators"""

        self.root = self.addRoot()

        self.addLoc(name="controller",parent=self.root,position=(0,0,3))
        self.addLoc(name="bigScale",parent=self.root,position=(0,0,2))
        self.addLoc(name="jaw",parent=self.root,position=(0,0,-2))

        for index,part in enumerate(["piv","01","02","03"]):
            list_up_loc = [ self.addLoc("up_{}_{}".format(part,i+1), self.root,position=(0,0,0)) for i in range(7) ]
            list_low_loc = [ self.addLoc("low_{}_{}".format(part,i+1), self.root,position=(0,0,0)) for i in range(5) ]

            # reposition loc
            for list_target in [list_up_loc,list_low_loc]:
                # set tx value
                # value1 = list_target[0].tx.get()
                # value2 = list_target[-1].tx.get()
                # value_sum = value2-value1
                value_offset = (len(list_target)-1) / 2

                for i,locator in enumerate(list_target):
                    locator.tx.set(i-value_offset)

                # set ty,tz value
                for each in list_target:
                    if each ==  list_up_loc[0] or each ==  list_up_loc[-1]:
                        value_y = 0+index
                    elif each in list_up_loc:
                        value_y = 1*(index+1)
                    elif each in list_low_loc:
                        value_y = -1*(index+1)

                    each.ty.set(value_y)
                    each.tz.set(1)

                self.addDispCurve("curve", centers=list_target)

    def addParameters(self):
        """Add the configurations settings"""

        self.pType = self.addParam("mode", "long", 0, 0)
        self.pBlend = self.addParam("blend", "double", 1, 0, 1)
        self.pNeutralPose = self.addParam("neutralpose", "bool", True)
        self.pIkRefArray = self.addParam("ikrefarray", "string", "")
        self.pUseIndex = self.addParam("useIndex", "bool", False)
        self.pParentJointIndex = self.addParam(
            "parentJointIndex", "long", -1, None, None)

        # custom attribute
        self.addParam("enable_zipper","bool",False,keyable=True)
        self.addParam("enable_sliding","bool",False,keyable=True)
        self.addParam("auto_pinch","bool",False,keyable=True)
        self.addParam("ignore_extra_joints","bool",False,keyable=True)
        self.addParam("sliding_object","string","slide_mesh",keyable=True)

class settingsTab(QtWidgets.QDialog, sui.Ui_Form):
    def __init__(self, parent=None):
        super(settingsTab, self).__init__(parent)
        self.setupUi(self)

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
        self.tabs.insertTab(1, self.settingsTab, "Component Settings")

        self.settingsTab.lineEdit_sliding_object.setText(self.root.attr("sliding_object").get())


        # populate component settings
        # self.settingsTab.ikfk_slider.setValue(
        #     int(self.root.attr("blend").get() * 100))
        # self.settingsTab.ikfk_spinBox.setValue(
        #     int(self.root.attr("blend").get() * 100))
        # self.settingsTab.mode_comboBox.setCurrentIndex(
        #     self.root.attr("mode").get())

        # if self.root.attr("neutralpose").get():
        #     self.settingsTab.neutralPose_checkBox.setCheckState(
        #         QtCore.Qt.Checked)
        # else:
        #     self.settingsTab.neutralPose_checkBox.setCheckState(
        #         QtCore.Qt.Unchecked)

        # ikRefArrayItems = self.root.attr("ikrefarray").get().split(",")
        # for item in ikRefArrayItems:
        #     self.settingsTab.ikRefArray_listWidget.addItem(item)

    def create_componentLayout(self):
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        return
        # self.settingsTab.lineEdit_sliding_object.textChanged.connect(
        #     partial(self.updateLineEdit,
        #             self.settingsTab.lineEdit_sliding_object,
        #             "sliding_object"))

        # self.settingsTab.mode_comboBox.currentIndexChanged.connect(
        #     partial(self.updateComboBox,
        #             self.settingsTab.mode_comboBox,
        #             "mode"))
        #
        # self.settingsTab.neutralPose_checkBox.stateChanged.connect(
        #     partial(self.updateCheck,
        #             self.settingsTab.neutralPose_checkBox,
        #             "neutralpose"))
        #        # self.settingsTab.ikRefArrayAdd_pushButton.clicked.connect(
        #     partial(self.addItem2listWidget,
        #             self.settingsTab.ikRefArray_listWidget,
        #             "ikrefarray"))
        # self.settingsTab.ikRefArrayRemove_pushButton.clicked.connect(
        #     partial(self.removeSelectedFromListWidget,
        #             self.settingsTab.ikRefArray_listWidget,
        #             "ikrefarray"))
        # self.settingsTab.ikRefArray_listWidget.installEventFilter(self)

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)