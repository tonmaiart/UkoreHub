from TonmaiToolkit.core import Utility,Misc,File
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from TonmaiToolkit.module.PySide import QtWidgets,wrapInstance
from maya import OpenMayaUI
import pymel.core as pm

def get_maya_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class ToolkitWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    def __init__(self,toolkit_name):
        super(ToolkitWindow, self).__init__(parent=get_maya_window())

        self.WINDOW_TITLE = Utility.split_camel_pascal(toolkit_name)
        self.WINDOW_OBJECT = Utility.to_pascal_case(toolkit_name)

        Misc.deleteControl(self.WINDOW_OBJECT)

        self.ui = File.load_ui_toolkit(toolkit_name)

        self.setCentralWidget(self.ui)
        self.setMinimumSize(self.ui.size())

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setObjectName(self.WINDOW_OBJECT)


