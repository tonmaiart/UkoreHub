from EasySkeleton import config,rig_class,utils,utils_tool
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtWidgets, QtCore, QtUiTools, QtGui
import maya.cmds as cmds
import os, importlib, webbrowser, inspect, configparser
import maya.mel as mel

class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    WINDOW_TITLE = "JointPlacementHelper"
    WINDOW_OBJECT = "JointPlacementHelper"

    def __init__(self):
        # Set-up Interface
        super(MainWindow, self).__init__(parent=None)

        def set_up_interface():
            utils_tool.deleteControl(self.WINDOW_OBJECT + "WorkspaceControl")

            self.ui = utils_tool.load_ui("{}\\JointPlacementHelper\\ui.ui".format(config.toolkit_path))

            self.setCentralWidget(self.ui)
            self.setFixedSize(self.ui.size())

            self.setObjectName(self.WINDOW_OBJECT)
            self.setWindowTitle(self.WINDOW_TITLE)

        def set_up_connect():
            self.ui.pushButton_snap_joint_position.clicked.connect(self.snap_joint_position)

        set_up_interface()
        set_up_connect()

    def snap_joint_position(self):
        selection = cmds.ls(sl=1)
        list_vertex = selection[1:len(selection)]
        target_joint = selection[0]

        cmds.select(list_vertex,r=1)
        cluster_handle = cmds.cluster()[1]

        list_child = cmds.listRelatives(target_joint,c=1)
        list_parent = cmds.listRelatives(target_joint,p=1)

        if list_child:
            cmds.parent(list_child,w=1)

        print(target_joint,cluster_handle)
        cmds.matchTransform(target_joint,cluster_handle,pos=1)

        if list_child:
            cmds.parent(list_child,target_joint)

        cmds.delete(cluster_handle)

    def display_plane_axis(self):
        pass