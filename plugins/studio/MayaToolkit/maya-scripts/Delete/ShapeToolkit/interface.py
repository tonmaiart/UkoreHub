import maya.cmds as mc
import pymel.core as pm
from shiboken2 import wrapInstance
from PySide2.QtWidgets import QWidget, QLabel, QMainWindow
from PySide2.QtCore import QSize, Qt, QObject, QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import *
from PySide2 import QtCore, QtUiTools
from importlib import reload
from shiboken2 import wrapInstance
from maya import OpenMayaUI
import xml.etree.ElementTree as ET
import ast
from TonmaiToolkit.core import Utility,Misc,BlendShape,QuickData,Create,Connection
from TonmaiToolkit.ui.interface_template import ToolkitWindow
from . import func


class MainWindow(ToolkitWindow):
    def __init__(self):
        # load and setup widget
        super(MainWindow, self).__init__("ShapeToolkit")

