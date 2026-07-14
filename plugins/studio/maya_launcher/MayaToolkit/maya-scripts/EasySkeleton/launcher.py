from EasySkeleton.interface import interface
from EasySkeleton import utils,utils_tool
import importlib



def run():
    # Reload each module
    importlib.reload(interface)
    importlib.reload(utils)
    importlib.reload(utils_tool)

    window = interface.MainWindow()
    window.show(dockable=True)
