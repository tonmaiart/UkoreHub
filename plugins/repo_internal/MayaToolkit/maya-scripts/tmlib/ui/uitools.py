import maya.cmds as cmds


def undoable(func):
    def wrapper(*args, **kwargs):
        # Enable undo before the function execution
        undo = cmds.undoInfo(openChunk=True)

        try:
            # Execute the function
            result = func(*args, **kwargs)
        finally:
            # Ensure undo is closed after the function execution
            cmds.undoInfo(closeChunk=True)

        return result

    return wrapper


def deleteControl(control):
    control_name = "{}WorkspaceControl".format(control)

    if cmds.workspaceControl(control_name, q=1, exists=1):
        try:
            cmds.deleteUI(control_name, control=True)
        except:
            pass


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())


def set_layout_disabled(layout, value=False):
    """Disable or enable all child widgets in the given layout."""
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if widget:
            widget.setEnabled(value)
