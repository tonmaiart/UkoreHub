from functools import partial
from tkinter.messagebox import NO
from types import ClassMethodDescriptorType

import pymel.core as pm
from pymel.core import datatypes

from mgear.shifter.component import guide
from mgear.core import pyqt, string, transform
from mgear.vendor.Qt import QtWidgets, QtCore

from TonmaiToolkit.core import File, Controller

import os, math

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.app.general.mayaMixin import MayaQDockWidget
import maya.cmds as mc

# from . import settingsUI as sui #for maya python 3 case , import ui class from settingUI.py

AUTHOR = "Natchapon Srisuk"
URL = "www.natchaponsrisuk.com"
EMAIL = "natchapon.contact@gmail.com"
VERSION = "1.0.0"
TYPE = "es_eyelid_01"  # this name must match with your component folder ,
NAME = "eyelid"  # and Do not have any syntax.
DESCRIPTION = (
    "Create a eyelid rig. This Module Can also be swtitch to global/local rigs"
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

    def postInit(self):
        """Initialize the position for the guide"""

        self.save_transform = ["root"]
        # self.addMinMax("uplid_#", 0, -1)
        # self.addMinMax("lowlid_#", 0, -1)

    def addObjects(self):
        """Add the Guide Root, blade and locators"""
        self.root = self.addRoot()

        sphere_mesh = pm.polySphere(ch=False)[0]
        sphere_mesh.setParent(self.root)

        sphere_mesh.overrideDisplayType.set(1)
        sphere_mesh.overrideEnabled.set(True)

        # self.locs_uplid = self.addLocMulti("uplid_#", self.root)
        # self.locs_lowlid = self.addLocMulti("lowlid_#", self.root)

        # self.addDispCurve("uplidCrv", self.locs_uplid)
        # self.addDispCurve("lowlidCrv", self.locs_lowlid)

        # move locs uplid,lowlid up for better looking
        # pm.xform(self.locs_uplid[0], ws=1, t=(0, 2, 0), r=1)
        # pm.xform(self.locs_lowlid[0], ws=1, t=(0, 1, 0), r=1)

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

        # add custom settings parameter
        self.addParam("localRig", "bool", False, keyable=True)
        self.addParam("betweenJointAmount", "long", 1, keyable=True)

        self.addParam("UpInLidCrv", "string", "", keyable=True)
        self.addParam("LowInLidCrv", "string", "", keyable=True)
        self.addParam("UpOutLidCrv", "string", "", keyable=True)
        self.addParam("LowOutLidCrv", "string", "", keyable=True)


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

        self.settingsTab.ui.pushButton_fill_up_in_lid_crv.clicked.connect(
            lambda x: self.create_or_fill("up_in")
        )
        self.settingsTab.ui.pushButton_fill_low_in_lid_crv.clicked.connect(
            lambda x: self.create_or_fill("low_in")
        )
        self.settingsTab.ui.pushButton_fill_up_out_lid_crv.clicked.connect(
            lambda x: self.create_or_fill("up_out")
        )
        self.settingsTab.ui.pushButton_fill_low_out_lid_crv.clicked.connect(
            lambda x: self.create_or_fill("low_out")
        )

        self.settingsTab.ui.pushButton_remove_up_in_lid_crv.clicked.connect(
            lambda x: self.remove_curve("up_in")
        )
        self.settingsTab.ui.pushButton_remove_low_in_lid_crv.clicked.connect(
            lambda x: self.remove_curve("low_in")
        )
        self.settingsTab.ui.pushButton_remove_up_out_lid_crv.clicked.connect(
            lambda x: self.remove_curve("up_out")
        )
        self.settingsTab.ui.pushButton_remove_low_out_lid_crv.clicked.connect(
            lambda x: self.remove_curve("low_out")
        )

        self.settingsTab.ui.pushButton_duplicate_for_mirror_side.clicked.connect(
            lambda x: self.duplicate_to_another_side()
        )

        if mc.selectPref(tso=True, q=True) == 0:
            mc.selectPref(tso=True)

    def create_componentControls(self):
        return

    def populate_componentControls(self):
        """Populate Controls

        Populate the controls values from the custom attributes of the
        component.

        """
        # populate tab
        self.tabs.insertTab(1, self.settingsTab.ui, "Eyelid Settings")

        # populate curve name
        self.settingsTab.ui.lineEdit_fill_up_in_lid_crv.setText(
            self.root.attr("UpInLidCrv").get()
        )
        self.settingsTab.ui.lineEdit_fill_up_out_lid_crv.setText(
            self.root.attr("UpOutLidCrv").get()
        )
        self.settingsTab.ui.lineEdit_fill_low_in_lid_crv.setText(
            self.root.attr("LowInLidCrv").get()
        )
        self.settingsTab.ui.lineEdit_fill_low_out_lid_crv.setText(
            self.root.attr("UpOutLidCrv").get()
        )

    def create_componentLayout(self):
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_layout.addWidget(self.tabs)
        self.settings_layout.addWidget(self.close_button)

        self.setLayout(self.settings_layout)

    def create_componentConnections(self):
        pass

    def eventFilter(self, sender, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            if sender == self.settingsTab.ui.ikRefArray_listWidget:
                self.updateListAttr(sender, "ikrefarray")
            return True
        else:
            return QtWidgets.QDialog.eventFilter(self, sender, event)

    def dockCloseEventTriggered(self):
        pyqt.deleteInstances(self, MayaQDockWidget)

    def duplicate_to_another_side(self):
        for attr_name in ["UpInLidCrv", "LowInLidCrv", "UpOutLidCrv", "LowOutLidCrv"]:
            curve = self.root.attr(attr_name).get()

            if not pm.objExists(curve):
                continue

            curve_dup = pm.duplicate(curve)[0]
            parent = pm.listRelatives(curve_dup, p=1)[0]

            grp_tmp = pm.group(em=1)
            curve_dup.setParent(grp_tmp)

            pm.setAttr(grp_tmp + ".sx", -1)
            pm.makeIdentity(grp_tmp, a=1, s=1)

            pm.parent(curve_dup, parent)
            pm.delete(grp_tmp)

    def remove_curve(self, part=""):
        fill_name = ""
        if part == "up_in":
            self.settingsTab.ui.lineEdit_fill_up_in_lid_crv.setText("")
            self.settingsTab.ui.lineEdit_up_in_lid_vtx.setText("")
            fill_name = self.root.attr("UpInLidCrv").get()

        elif part == "low_in":
            self.settingsTab.ui.lineEdit_fill_low_in_lid_crv.setText("")
            self.settingsTab.ui.lineEdit_low_in_lid_vtx.setText("")
            fill_name = self.root.attr("LowInLidCrv").get()

        elif part == "up_out":
            self.settingsTab.ui.lineEdit_fill_up_out_lid_crv.setText("")
            self.settingsTab.ui.lineEdit_up_out_lid_vtx.setText("")
            fill_name = self.root.attr("UpOutLidCrv").get()

        elif part == "low_out":
            self.settingsTab.ui.lineEdit_fill_low_out_lid_crv.setText("")
            self.settingsTab.ui.lineEdit_low_out_lid_vtx.setText("")
            fill_name = self.root.attr("LowOutLidCrv").get()

        if pm.objExists(fill_name):
            pm.delete(fill_name)

    def create_or_fill(self, part=""):
        def create_curve_from_edge():
            def is_same_position(pos1, pos2, tolerance=0.001):
                """
                Checks if two 3D positions are the same within a given tolerance.

                Args:
                    pos1 (list, tuple, or pm.dt.Vector): The first position [x, y, z].
                    pos2 (list, tuple, or pm.dt.Vector): The second position [x, y, z].
                    tolerance (float): The maximum allowed distance between the two
                                    positions to be considered the same.

                Returns:
                    bool: True if the positions are within the tolerance, False otherwise.
                """
                # Using pymel.core.datatypes.Vector for robust distance calculation
                v1 = pm.dt.Vector(pos1)
                v2 = pm.dt.Vector(pos2)

                # Calculate the distance between the two vectors
                distance = v1.distanceTo(v2)

                return distance <= tolerance

            selection = pm.ls(fl=1, os=True)

            # define up and low curve
            crv_name = "{}_lid_crv".format(part)

            # create new curve
            pm.select(selection, r=True)
            curve = pm.polyToCurve(
                form=2, degree=1, conformToSmoothMeshPreview=1, ch=0
            )[0]

            # Auto parent
            if pm.objExists("guide"):
                pm.parent(curve, "guide")

            # colorize and width
            Controller.set_line_width(5, [curve])

            if "up" in part:
                Controller.set_color([True, 17], [curve])
            elif "low" in part:
                Controller.set_color([True, 14], [curve])

            # Rename
            rename_output = pm.rename(curve, crv_name)

            return rename_output

        def create_curve_from_vertex():
            list_pos = []

            for vtx in selection:
                if ".vtx" not in str(vtx):
                    raise Exception("Selection is not valid vertex")
                else:
                    print(vtx)
                    list_pos.append(pm.xform(vtx, ws=1, q=1, t=1))

            curve = pm.curve(d=1, p=list_pos, n="{}_crv".format(part))

            # colorize and width
            Controller.set_line_width(5, [curve])

            if "up" in part:
                Controller.set_color([True, 17], [curve])
            elif "low" in part:
                Controller.set_color([True, 14], [curve])

            # pm.setAttr(
            #     "{}.dispCV".format(
            #         pm.listRelatives(fill_name, c=1, s=1, typ="nurbsCurve")[0]
            #     ),
            #     True,
            # )

            if pm.objExists("guide"):
                curve.setParent("guide")

            return curve

        if not part:
            return

        selection = pm.ls(fl=1, os=True)

        # create curve manual count
        if not selection:
            cvs = int(input("Input Amount of CV"))
            list_pos = [(i, 0, 0) for i in range(cvs)]
            fill_name = pm.curve(d=1, p=list_pos, n="{}_crv".format(part))
            pm.setAttr(
                "{}.dispCV".format(
                    pm.listRelatives(fill_name, c=1, s=1, typ="nurbsCurve")[0]
                ),
                True,
            )

            if pm.objExists("guide"):
                fill_name.setParent("guide")

        # fill selected curve
        elif len(selection) == 1 and pm.listRelatives(
            selection[0], c=1, s=1, typ="nurbsCurve"
        ):
            fill_name = selection[0]

        # create curve from edge
        elif ".e" in str(selection[0]):
            fill_name = create_curve_from_edge()

        # create curve from vertex
        elif ".vtx" in str(selection[0]):
            fill_name = create_curve_from_vertex()

        fill_name = str(fill_name)
        curve_shape = pm.listRelatives(fill_name, c=1, s=1, typ="nurbsCurve")[0]
        curve_len_vtx = pm.getAttr("{}.spans".format(curve_shape))
        str_curve_len_vtx = str(curve_len_vtx)

        # Fill and update parameter
        if part == "up_in":
            self.settingsTab.ui.lineEdit_fill_up_in_lid_crv.setText(fill_name)
            self.settingsTab.ui.lineEdit_up_in_lid_vtx.setText(str_curve_len_vtx)
            self.root.attr("UpInLidCrv").set(fill_name)

        elif part == "low_in":
            self.settingsTab.ui.lineEdit_fill_low_in_lid_crv.setText(fill_name)
            self.settingsTab.ui.lineEdit_low_in_lid_vtx.setText(str_curve_len_vtx)
            self.root.attr("LowInLidCrv").set(fill_name)

        elif part == "up_out":
            self.settingsTab.ui.lineEdit_fill_up_out_lid_crv.setText(fill_name)
            self.settingsTab.ui.lineEdit_up_out_lid_vtx.setText(str_curve_len_vtx)
            self.root.attr("UpOutLidCrv").set(fill_name)

        elif part == "low_out":
            self.settingsTab.ui.lineEdit_fill_low_out_lid_crv.setText(fill_name)
            self.settingsTab.ui.lineEdit_low_out_lid_vtx.setText(str_curve_len_vtx)
            self.root.attr("LowOutLidCrv").set(fill_name)
