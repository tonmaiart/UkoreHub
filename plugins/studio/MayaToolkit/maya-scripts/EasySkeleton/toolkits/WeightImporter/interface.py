import maya.cmds as cmds
from shiboken2 import wrapInstance
from PySide2.QtWidgets import QWidget, QLabel, QMainWindow
from PySide2.QtCore import QSize, Qt, QObject, QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import *
from PySide2 import QtCore, QtUiTools
from importlib import reload
from shiboken2 import wrapInstance
from maya import OpenMayaUI
import os
import xml.etree.ElementTree as ET
import pymel.core as pm
import EasySkeleton
from EasySkeleton import utils_tool,config
import maya.mel as mel

def get_maya_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)


class MainWindow(QMainWindow):
    # load joint and mesh
    list_bind_joints = []
    mesh_name = None
    xml_file = None
    list_missing_joint = []
    WindowTitle = "Weight Importer 1.3"

    def __init__(self, parent=get_maya_window()):
        # load and setup widget
        super(MainWindow, self).__init__(parent)

        self.ui = utils_tool.load_ui("{}\\WeightImporter\\window.ui".format(config.toolkit_path))

        self.setCentralWidget(self.ui)
        self.setFixedSize(self.ui.size())
        self.setWindowTitle(self.WindowTitle)

        self.ui.pushButton_browse.clicked.connect(self.open_maya_explorer)
        self.ui.pushButton_bind.clicked.connect(self.bind_skin)

        self.ui.pushButton_enter_skin_cluster.clicked.connect(self.set_custom_export_skin_weight)
        self.ui.pushButton_export_weight.clicked.connect(self.export_weight)

        cmds.scriptJob(event=["SelectionChanged", self.auto_load_select], protected=True)
        self.auto_load_select()
    def export_weight(self):
        skin_cluster_node = self.ui.lineEdit_skin_cluster_export.text()

        # export_path = cmds.workspace(fre="export")

        # if not export_path:

        export_path = cmds.workspace(q=1,rd=1)+"\\assets"+ "\\{}.xml".format(skin_cluster_node)

        save_path = cmds.fileDialog2(fileMode=0, dialogStyle=2, fileFilter="XML Files (*.xml)",dir=export_path)

        if save_path:
            # get path
            file_name = save_path.split("/")[-1]
            path = file_name.replace(file_name,"")

            cmds.deformerWeights(save_path,export=True,deformer=skin_cluster_node,format="XML",path=path)

    def set_custom_export_skin_weight(self):
        result = cmds.promptDialog(
            title='Enter Skin Cluster Name',
            message='Enter Skin Cluster Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel',
            tx="")

        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True)
        else:
            raise Exception("was Canceled")

        self.ui.lineEdit_skin_cluster_export.setText(text)

    def auto_load_select(self):
        def get_skin_cluster(mesh):
            # Get the history of the mesh and filter by skinCluster
            history = cmds.listHistory(mesh)
            skin_clusters = cmds.ls(history, type='skinCluster')
            return skin_clusters

        # Get the first selected mesh
        selected = cmds.ls(sl=1)

        if selected:
            skin_clusters = get_skin_cluster(selected[0])

            if skin_clusters:
                self.ui.lineEdit_skin_cluster_export.setText(skin_clusters[0])

    def open_maya_explorer(self, reload=False):
        # browse .xml file
        if reload:
            browse_path = self.xml_file
        else:
            browse_path = cmds.fileDialog2(fileMode=1, dialogStyle=2, fileFilter="XML Files (*.xml)")[0]

        if browse_path:
            # set text to browse bar
            self.xml_file = browse_path
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            self.ui.lineEdit_file.setText(self.xml_file)

            # get list joint
            self.list_bind_joints = []

            # load joint to list
            for weights_node in root.findall('.//weights'):
                self.list_bind_joints.append(
                    weights_node.get('source'))  # Assuming 'source' attribute contains the joint name
            self.list_bind_joints.sort()

            # get mesh name
            for shape_node in root.findall('.//shape'):
                self.mesh_name = shape_node.get('name')
            self.ui.lineEdit_mesh.setText(self.mesh_name)

            # set default skin cluster node name
            print(self.xml_file)

            xml_file_raw = self.xml_file.split("/")[-1]
            xml_file_raw = xml_file_raw.replace(".xml","")
            self.ui.lineEdit_skin_cluster_name.setText(xml_file_raw)

            # load widget
            self.list_missing_joint = []
            for joint in self.list_bind_joints:
                self.list_missing_joint.append(joint) if not cmds.objExists(joint) else None


    def bind_skin(self):
        if self.list_missing_joint:
            raise Exception("Missing Joints : {} , Not Found".format(self.list_missing_joint))
        elif cmds.objExists(self.mesh_name):
            # delete old skin cluster history
            history = cmds.listConnections(self.mesh_name, t="skinCluster")

            if history:
                [ cmds.delete(node) for node in history ]

            # bind skin
            node_skin_cluster = cmds.skinCluster(self.mesh_name, self.list_bind_joints,n=self.ui.lineEdit_skin_cluster_name.text(), tsb=1, ih=1)[0]

            # import weight
            file_name = self.xml_file.split("/")[-1]
            file_path = self.xml_file.replace("/" + file_name, "")

            cmds.deformerWeights(file_name, im=1, method="index", deformer=node_skin_cluster,
                                 path=file_path)

            cmds.confirmDialog(m="Import and Bind Skin Complete!")
        else:
            raise Exception("Bind Target Name : {} , Not Found".format(self.mesh_name))

def show():
    window = MainWindow()
    window.show()
