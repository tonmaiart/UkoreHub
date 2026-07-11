from TonmaiToolkit import config
from TonmaiToolkit.core import (
    Utility,
    Transform,
    Misc,
    Connection,
    SkinWeight,
    Controller,
    File,
    QuickData,
    BlendShape,
)
from TonmaiToolkit.menu import Help
from TonmaiToolkit.module.PySide import QtCore, QtGui, QtWidgets, QAction

import os, importlib, webbrowser, inspect, configparser, re, json
from TonmaiToolkit.ui.interface_template import ToolkitWindow
import pymel.core as pm
import xml.etree.ElementTree as ET
import maya.cmds as mc
import ast
import time

Help.reload_scripts()


class MainWindow(ToolkitWindow):
    def __init__(self):
        # Set-up Interface
        super(MainWindow, self).__init__("FaceRig")

        self.set_up_controller_widget()

    def set_up_controller_widget(self):

        def set_button_icon(button, name):
            path = os.path.join(icon_path, "{}.png".format(name))
            button.setIcon(QtGui.QIcon(path))
            button.setIconSize(QtCore.QSize(70, 70))
            button.setText("")

        def switch_basic():
            is_checked = self.ui.pushButton_basic_switch.isChecked()

            if is_checked:
                self.ui.pushButton_basic_switch.setText("Open")
            else:
                self.ui.pushButton_basic_switch.setText("Basic")

            pass

        def set_pose(name):
            is_checked = self.ui.pushButton_basic_switch.isChecked()

            if is_checked:
                name = "open_" + name

            pm.currentTime(dict_keyframe_pose[name])

        dict_keyframe_pose = {
            # Basic Mouth
            "up": 10,
            "dn": 20,
            "in": 30,
            "out": 40,
            "up_in": 50,
            "dn_in": 60,
            "up_out": 70,
            "dn_out": 80,
            "puff": 90,
            "cheek": 100,
            "up_roll_out": 110,
            "low_roll_out": 120,
            "up_roll_in": 130,
            "low_roll_in": 140,
            # Open Mouth
            "open_up": 230,
            "open_dn": 240,
            "open_in": 250,
            "open_out": 260,
            "open_up_in": 270,
            "open_dn_in": 280,
            "open_up_out": 290,
            "open_dn_out": 300,
        }
        icon_path = os.path.join(config.TOOLKIT_PATH, "FaceRig", "icons")
        selection = pm.ls(sl=1)

        self.ui.pushButton_basic_switch.clicked.connect(switch_basic)

        set_button_icon(self.ui.pushButton_up_in, "up_in")
        set_button_icon(self.ui.pushButton_up, "up")
        set_button_icon(self.ui.pushButton_up_out, "up_out")

        set_button_icon(self.ui.pushButton_in, "in")
        set_button_icon(self.ui.pushButton_out, "out")

        set_button_icon(self.ui.pushButton_dn_in, "dn_in")
        set_button_icon(self.ui.pushButton_dn, "dn")
        set_button_icon(self.ui.pushButton_dn_out, "dn_out")

        # connect
        self.ui.pushButton_up_in.clicked.connect(lambda x: set_pose("up_in"))
        self.ui.pushButton_in.clicked.connect(lambda x: set_pose("in"))
        self.ui.pushButton_dn_in.clicked.connect(lambda x: set_pose("dn_in"))

        self.ui.pushButton_up.clicked.connect(lambda x: set_pose("up"))
        self.ui.pushButton_dn.clicked.connect(lambda x: set_pose("dn"))

        self.ui.pushButton_up_out.clicked.connect(lambda x: set_pose("up_out"))
        self.ui.pushButton_out.clicked.connect(lambda x: set_pose("out"))
        self.ui.pushButton_dn_out.clicked.connect(lambda x: set_pose("dn_out"))
