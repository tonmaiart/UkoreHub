from email.mime import base
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
        super(MainWindow, self).__init__("EasyController")

        self.set_up_controller_widget()

    def set_up_controller_widget(self):

        def set_button_icon(button, index):
            path = os.path.join(icon_path, "icon_{}.jpg".format(str(index).zfill(2)))
            button.setIcon(QtGui.QIcon(path))
            button.setIconSize(QtCore.QSize(48, 48))

        def swap_keyword():
            source = self.ui.lineEdit_source.text()
            target = self.ui.lineEdit_target.text()

            self.ui.lineEdit_source.setText(target)
            self.ui.lineEdit_target.setText(source)

        def update_keyword_presets():
            dict_data = {
                0: ["L_", "R_"],
                1: ["*L", "*R"],
                2: ["L0", "R0"],
            }

            current_index = self.ui.comboBox_keyword.currentIndex()

            self.ui.lineEdit_source.setText(dict_data[current_index][0])
            self.ui.lineEdit_target.setText(dict_data[current_index][1])

        icon_path = os.path.join(config.TOOLKIT_PATH, "EasyController", "icons")
        selection = pm.ls(sl=1)

        # set-up icon --------------
        set_button_icon(self.ui.pushButton_icon_1, 1)
        set_button_icon(self.ui.pushButton_icon_2, 2)
        set_button_icon(self.ui.pushButton_icon_3, 3)
        set_button_icon(self.ui.pushButton_icon_4, 4)
        set_button_icon(self.ui.pushButton_icon_5, 5)
        set_button_icon(self.ui.pushButton_icon_6, 6)
        set_button_icon(self.ui.pushButton_icon_7, 7)
        set_button_icon(self.ui.pushButton_icon_8, 8)
        set_button_icon(self.ui.pushButton_icon_9, 9)
        set_button_icon(self.ui.pushButton_icon_10, 10)
        set_button_icon(self.ui.pushButton_icon_11, 11)
        set_button_icon(self.ui.pushButton_icon_12, 12)
        set_button_icon(self.ui.pushButton_icon_13, 13)
        set_button_icon(self.ui.pushButton_icon_14, 14)
        set_button_icon(self.ui.pushButton_icon_15, 15)
        set_button_icon(self.ui.pushButton_icon_16, 16)
        set_button_icon(self.ui.pushButton_icon_17, 17)
        set_button_icon(self.ui.pushButton_icon_18, 18)
        set_button_icon(self.ui.pushButton_icon_19, 19)
        set_button_icon(self.ui.pushButton_icon_20, 20)
        set_button_icon(self.ui.pushButton_icon_21, 21)
        set_button_icon(self.ui.pushButton_icon_22, 22)
        set_button_icon(self.ui.pushButton_icon_23, 23)
        set_button_icon(self.ui.pushButton_icon_24, 24)
        set_button_icon(self.ui.pushButton_icon_25, 25)
        set_button_icon(self.ui.pushButton_icon_26, 26)
        set_button_icon(self.ui.pushButton_icon_27, 27)
        set_button_icon(self.ui.pushButton_icon_28, 28)

        # connect widget --------------
        self.ui.pushButton_icon_1.clicked.connect(
            lambda x: Controller.create_control(1)
        )
        self.ui.pushButton_icon_2.clicked.connect(
            lambda x: Controller.create_control(2)
        )
        self.ui.pushButton_icon_3.clicked.connect(
            lambda x: Controller.create_control(3)
        )
        self.ui.pushButton_icon_4.clicked.connect(
            lambda x: Controller.create_control(4)
        )
        self.ui.pushButton_icon_5.clicked.connect(
            lambda x: Controller.create_control(5)
        )
        self.ui.pushButton_icon_6.clicked.connect(
            lambda x: Controller.create_control(6)
        )
        self.ui.pushButton_icon_7.clicked.connect(
            lambda x: Controller.create_control(7)
        )
        self.ui.pushButton_icon_8.clicked.connect(
            lambda x: Controller.create_control(8)
        )
        self.ui.pushButton_icon_9.clicked.connect(
            lambda x: Controller.create_control(9)
        )
        self.ui.pushButton_icon_10.clicked.connect(
            lambda x: Controller.create_control(10)
        )
        self.ui.pushButton_icon_11.clicked.connect(
            lambda x: Controller.create_control(11)
        )
        self.ui.pushButton_icon_12.clicked.connect(
            lambda x: Controller.create_control(12)
        )
        self.ui.pushButton_icon_13.clicked.connect(
            lambda x: Controller.create_control(13)
        )
        self.ui.pushButton_icon_14.clicked.connect(
            lambda x: Controller.create_control(14)
        )
        self.ui.pushButton_icon_15.clicked.connect(
            lambda x: Controller.create_control(15)
        )
        self.ui.pushButton_icon_16.clicked.connect(
            lambda x: Controller.create_control(16)
        )
        self.ui.pushButton_icon_17.clicked.connect(
            lambda x: Controller.create_control(17)
        )
        self.ui.pushButton_icon_18.clicked.connect(
            lambda x: Controller.create_control(18)
        )
        self.ui.pushButton_icon_19.clicked.connect(
            lambda x: Controller.create_control(19)
        )
        self.ui.pushButton_icon_20.clicked.connect(
            lambda x: Controller.create_control(20)
        )
        self.ui.pushButton_icon_21.clicked.connect(
            lambda x: Controller.create_control(21)
        )
        self.ui.pushButton_icon_22.clicked.connect(
            lambda x: Controller.create_control(22)
        )
        self.ui.pushButton_icon_23.clicked.connect(
            lambda x: Controller.create_control(23)
        )
        self.ui.pushButton_icon_24.clicked.connect(
            lambda x: Controller.create_control(24)
        )
        self.ui.pushButton_icon_25.clicked.connect(
            lambda x: Controller.create_control(25)
        )
        self.ui.pushButton_icon_26.clicked.connect(
            lambda x: Controller.create_control(26)
        )
        self.ui.pushButton_icon_27.clicked.connect(
            lambda x: Controller.create_control(27)
        )
        self.ui.pushButton_icon_28.clicked.connect(
            lambda x: Controller.create_control(28)
        )

        # self.ui.pushButton_color_reset.clicked.connect(lambda x: Controller.set_color([True,0))
        self.ui.pushButton_color_1.clicked.connect(
            lambda x: Controller.set_color([True, 1])
        )
        self.ui.pushButton_color_2.clicked.connect(
            lambda x: Controller.set_color([True, 2])
        )
        self.ui.pushButton_color_3.clicked.connect(
            lambda x: Controller.set_color([True, 3])
        )
        self.ui.pushButton_color_4.clicked.connect(
            lambda x: Controller.set_color([True, 4])
        )
        self.ui.pushButton_color_5.clicked.connect(
            lambda x: Controller.set_color([True, 5])
        )
        self.ui.pushButton_color_6.clicked.connect(
            lambda x: Controller.set_color([True, 6])
        )
        self.ui.pushButton_color_7.clicked.connect(
            lambda x: Controller.set_color([True, 7])
        )
        self.ui.pushButton_color_8.clicked.connect(
            lambda x: Controller.set_color([True, 8])
        )
        self.ui.pushButton_color_9.clicked.connect(
            lambda x: Controller.set_color([True, 9])
        )
        self.ui.pushButton_color_10.clicked.connect(
            lambda x: Controller.set_color([True, 10])
        )
        self.ui.pushButton_color_11.clicked.connect(
            lambda x: Controller.set_color([True, 11])
        )
        self.ui.pushButton_color_12.clicked.connect(
            lambda x: Controller.set_color([True, 12])
        )
        self.ui.pushButton_color_13.clicked.connect(
            lambda x: Controller.set_color([True, 13])
        )
        self.ui.pushButton_color_14.clicked.connect(
            lambda x: Controller.set_color([True, 14])
        )
        self.ui.pushButton_color_15.clicked.connect(
            lambda x: Controller.set_color([True, 15])
        )
        self.ui.pushButton_color_16.clicked.connect(
            lambda x: Controller.set_color([True, 16])
        )
        self.ui.pushButton_color_17.clicked.connect(
            lambda x: Controller.set_color([True, 17])
        )
        self.ui.pushButton_color_18.clicked.connect(
            lambda x: Controller.set_color([True, 18])
        )
        self.ui.pushButton_color_19.clicked.connect(
            lambda x: Controller.set_color([True, 19])
        )
        self.ui.pushButton_color_20.clicked.connect(
            lambda x: Controller.set_color([True, 20])
        )
        self.ui.pushButton_color_21.clicked.connect(
            lambda x: Controller.set_color([True, 21])
        )
        self.ui.pushButton_color_22.clicked.connect(
            lambda x: Controller.set_color([True, 22])
        )
        self.ui.pushButton_color_23.clicked.connect(
            lambda x: Controller.set_color([True, 23])
        )
        self.ui.pushButton_color_24.clicked.connect(
            lambda x: Controller.set_color([True, 24])
        )
        self.ui.pushButton_color_25.clicked.connect(
            lambda x: Controller.set_color([True, 25])
        )
        self.ui.pushButton_color_26.clicked.connect(
            lambda x: Controller.set_color([True, 26])
        )
        self.ui.pushButton_color_27.clicked.connect(
            lambda x: Controller.set_color([True, 27])
        )
        self.ui.pushButton_color_28.clicked.connect(
            lambda x: Controller.set_color([True, 28])
        )
        self.ui.pushButton_color_29.clicked.connect(
            lambda x: Controller.set_color([True, 29])
        )
        self.ui.pushButton_color_30.clicked.connect(
            lambda x: Controller.set_color([True, 30])
        )

        self.ui.pushButton_color_rgb.clicked.connect(
            lambda x: Controller.open_color_dialog()
        )

        # mirror function
        self.ui.pushButton_swap_keyword.clicked.connect(swap_keyword)
        self.ui.lineEdit_source.setText("L_")
        self.ui.lineEdit_target.setText("R_")

        self.ui.pushButton_mirror_shape.clicked.connect(
            lambda x: Controller.mirror_shape(
                source_side=self.ui.lineEdit_source.text(),
                target_side=self.ui.lineEdit_target.text(),
            )
        )

        self.ui.horizontalSlider_line_width.valueChanged.connect(
            lambda x: Controller.set_line_width(
                self.ui.horizontalSlider_line_width.value()
            )
        )

        update_keyword_presets()
        self.ui.comboBox_keyword.currentTextChanged.connect(update_keyword_presets)

        # isolate edit
        self.ui.pushButton_isolateEdit.clicked.connect(
            lambda x: Controller.isolate_edit(False, False)
        )
        self.ui.pushButton_isolateClear.clicked.connect(
            lambda x: Controller.isolate_clear()
        )

        # multiple replace function
        self.ui.pushButton_replace.clicked.connect(lambda x: Controller.clone_shape())
        self.ui.pushButton_clone_style.clicked.connect(
            lambda x: Controller.clone_style()
        )

        # flip function
        self.menu_flip = QtWidgets.QMenu(self)

        action_flip_x = QAction("X", self)
        action_flip_x.triggered.connect(lambda x: Controller.flip_shape("x"))
        self.menu_flip.addAction(action_flip_x)

        action_flip_y = QAction("Y", self)
        action_flip_y.triggered.connect(lambda x: Controller.flip_shape("y"))
        self.menu_flip.addAction(action_flip_y)

        action_flip_z = QAction("Z", self)
        action_flip_z.triggered.connect(lambda x: Controller.flip_shape("z"))
        self.menu_flip.addAction(action_flip_z)

        self.ui.pushButton_flip_controller_shape.setMenu(self.menu_flip)

        self.ui.pushButton_match_cv.clicked.connect(
            lambda x: Controller.match_controller_cv()
        )

        pm.select(selection)
