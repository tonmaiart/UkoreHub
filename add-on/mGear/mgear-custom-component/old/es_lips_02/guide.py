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
TYPE = "es_lips_02"
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

        self.save_transform = ["root","bigScale","controller","jaw","inner"]

        self.save_transform += ["up_piv_{}".format(i+1) for i in range(7)]
        self.save_transform += ["up_rim_{}".format(i+1) for i in range(7)]
        self.save_transform += ["up_corner_{}".format(i+1) for i in range(7)]

        self.save_transform += ["low_piv_{}".format(i+1) for i in range(5)]
        self.save_transform += ["low_rim_{}".format(i+1) for i in range(5)]
        self.save_transform += ["low_corner_{}".format(i+1) for i in range(5)]


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
                left_objs = obj_list[mid_index + 1:]
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
                mdl = pm.createNode('multDoubleLinear', name=f"{left}_to_{right}_mirrorTx_mdl")
                mdl.input2.set(-1)

                # Connect left.tx → mdl.input1 → right.tx
                left.translateX >> mdl.input1
                mdl.output >> right.translateX

                # Connect all other attributes directly
                for attr in ['translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ']:
                    try:
                        getattr(left, attr) >> getattr(right, attr)
                    except Exception:
                        pm.warning(f"Could not connect {left}.{attr} to {right}.{attr}")

        dict_mouth_loc = {}

        self.root = self.addRoot()

        self.addLoc(name="controller",parent=self.root,position=(0,0,3),color=9)
        self.addLoc(name="bigScale",parent=self.root,position=(0,0,1),width=0.1,color=18)
        self.addLoc(name="jaw",parent=self.root,position=(0,0,-2),width=0.5,color=14)
        self.addLoc(name="inner",parent=self.root,position=(0,0,-1.5),width=0.3,color=6)

        for index,part in enumerate(["piv","rim","corner"]):
            if part == "piv":
                color = 18
                width = 0.1
            elif part == "rim":
                color = 17
                width = 0.35
            elif part == "corner":
                color = 13
                width = 0.2

            list_up_loc = [ self.addLoc("up_{}_{}".format(part,i+1), self.root,position=(0,0,0),color=color,width=width) for i in range(7) ]
            list_low_loc = [ self.addLoc("low_{}_{}".format(part,i+1), self.root,position=(0,0,0),color=color,width=width) for i in range(5) ]

            dict_mouth_loc[part] = [list_up_loc,list_low_loc]

            # reposition loc
            for list_target in [list_up_loc,list_low_loc]:
                value_offset = (len(list_target)-1) / 2

                for i,locator in enumerate(list_target):
                    locator.tx.set((i-value_offset)*(index+1)*0.5)

                # set ty,tz value
                for each in list_target:
                    if each ==  list_up_loc[0] or each ==  list_up_loc[-1]:
                        value_y = 0
                    elif each in list_up_loc:
                        value_y = 1*(index+1)*0.5
                    elif each in list_low_loc:
                        value_y = -1*(index+1)*0.5

                    each.ty.set(value_y)
                    each.tz.set(1)

            self.addDispCurve("curve", centers=list_up_loc+list_low_loc[::-1]+[list_up_loc[0]])

        # connect invert
        for part in dict_mouth_loc.keys():
            for i in range(2):
                list_loc = dict_mouth_loc[part][i]
                mirror_left_to_right(list_loc)

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
        self.addParam("extra_loop","bool",False,keyable=True)
        self.addParam("sliding_object","string","slide_mesh",keyable=True)
        self.addParam("loop_amount","long",1,keyable=True)

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

        self.settingsTab.checkBox_auto_pinch.setChecked(self.root.attr("auto_pinch").get())
        self.settingsTab.checkBox_enable_zipper.setChecked(self.root.attr("enable_zipper").get())

        self.settingsTab.checkBox_enable_sliding.setChecked(self.root.attr("enable_sliding").get())
        self.settingsTab.lineEdit_sliding_object.setText(self.root.attr("sliding_object").get())

        self.settingsTab.checkBox_extra_loop.setChecked(self.root.attr("extra_loop").get())
        self.settingsTab.spinBox_loop_amount.setValue(self.root.attr("loop_amount").get())

    def create_componentLayout(self):
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        self.settingsTab.checkBox_enable_zipper.clicked.connect(
            partial(self.updateCheck,
                    self.settingsTab.checkBox_enable_zipper,
                    "enable_zipper"))

        self.settingsTab.checkBox_auto_pinch.clicked.connect(
            partial(self.updateCheck,
                    self.settingsTab.checkBox_auto_pinch,
                    "auto_pinch"))

        self.settingsTab.checkBox_enable_sliding.clicked.connect(
            partial(self.updateCheck,
                    self.settingsTab.checkBox_enable_sliding,
                    "enable_sliding"))

        self.settingsTab.spinBox_loop_amount.valueChanged.connect(
            partial(self.updateSpinBox,
                    self.settingsTab.spinBox_loop_amount,
                    "loop_amount")
        )

        self.settingsTab.checkBox_extra_loop.clicked.connect(
            partial(self.updateCheck,
                    self.settingsTab.checkBox_extra_loop,
                    "extra_loop"))

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)