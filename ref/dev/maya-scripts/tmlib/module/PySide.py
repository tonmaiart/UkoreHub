# pyside_compat.py
import maya.cmds as cmds
import sys

# Detect Maya version
maya_version = int(cmds.about(version=True))

try:
    if maya_version >= 2025:
        from PySide6 import QtCore, QtGui, QtWidgets
        from PySide6.QtUiTools import QUiLoader
        from shiboken6 import wrapInstance
        import PySide6 as PySideMod

        # QAction lives in QtGui in PySide6
        QAction = QtGui.QAction

    else:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtUiTools import QUiLoader
        from shiboken2 import wrapInstance
        import PySide2 as PySideMod

        # QAction lives in QtWidgets in PySide2
        QAction = QtWidgets.QAction

except ImportError:
    raise ImportError(
        "Could not import the correct PySide version for Maya {}".format(maya_version)
    )

# Optional: Alias PySide2/PySide6 differences
Signal = QtCore.Signal
Slot = QtCore.Slot
