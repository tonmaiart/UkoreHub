from tmlib.core import Format, File
from tmlib.ui import uitools

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from tmlib.module.PySide import QtWidgets, wrapInstance, QtCore
from maya import OpenMayaUI


def get_maya_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class ToolkitWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    def __init__(self, toolkit_name):
        super(ToolkitWindow, self).__init__(parent=get_maya_window())

        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint)

        self.WINDOW_TITLE = Format.split_camel_pascal(toolkit_name)
        self.WINDOW_OBJECT = Format.to_pascal_case(toolkit_name)

        uitools.deleteControl(self.WINDOW_OBJECT)

        self.ui = File.load_ui_external(toolkit_name)

        self.setCentralWidget(self.ui)
        # self.setMinimumSize(self.ui.size())
        self.ui.adjustSize()
        self.adjustSize()

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setObjectName(self.WINDOW_OBJECT)
