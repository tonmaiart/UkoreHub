import maya.cmds as cmds


def is_attr_connected(attr):
    return bool(cmds.listConnections(attr, s=True, d=True))


def is_attr_exists(attr):
    return cmds.objExists(attr) and cmds.attributeQuery(
        attr.split(".")[-1], node=attr.split(".")[0], exists=True
    )

def break_connection(attr):
    src = cmds.connectionInfo(attr, sourceFromDestination=True)
    if src:
        cmds.disconnectAttr(src, attr)