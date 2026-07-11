import maya.cmds as cmds

def create_cone_driver():
    """
    Create a cone driver dot product
    """

    node_cone = cmds.createNode("implicitCone",n="driverCone")
    node_locator = cmds.createNode("locator",n="Target")
    group = cmds.group(em=1,n="ConeDriver_Grp")
    cmds.parent(node_cone,node_locator,group)

    # get basis of cone
    node_get_basis = cmds.createNode("vectorProduct",n="vp_get_basis_cone")
    cmds.connectAttr(cmds.listRelatives(node_cone,p=1)[0]+".worldMatrix[0]","{}.matrix".format(node_get_basis))
    cmds.setAttr("{}.input1".format(node_get_basis),0,0,-1,typ="double3")
    cmds.setAttr("{}.normalizeOutput".format(node_get_basis),True)
    cmds.setAttr("{}.operation".format(node_get_basis),3)

    # node_dot_product = cmds.createNode("vectorProduct",n="vp_dot_product")
    # cmds.setAttr("{}.normalizeOutput".format(node_dot_product),True)
    # cmds.setAttr("{}.operation".format(node_dot_product),1)

    # get vector from translate
    node_get_basis_target = cmds.createNode("vectorProduct",n="vp_get_basis_target")
    cmds.connectAttr("{}.worldMatrix[0]".format(node_locator),"{}.matrix".format(node_get_basis_target))
    cmds.setAttr("{}.input1".format(node_get_basis_target),0,1,0,typ="double3")
    cmds.setAttr("{}.normalizeOutput".format(node_get_basis_target),True)
    cmds.setAttr("{}.operation".format(node_get_basis_target),3)

    # get angle between
    node_angleBetween = cmds.createNode("angleBetweenDL",n="ab_angle")
    cmds.connectAttr("{}.output".format(node_get_basis),"{}.vector1".format(node_angleBetween))
    cmds.connectAttr("{}.output".format(node_get_basis_target),"{}.vector2".format(node_angleBetween))

    # get half angle
    node_half_cone_angle = cmds.createNode("multiplyDL")
    cmds.connectAttr("{}.coneAngle".format(node_cone),"{}.input[0]".format(node_half_cone_angle))
    cmds.setAttr("{}.input[1]".format(node_half_cone_angle),0.5)

    # divide ratio 
    node_divide = cmds.createNode("divideDL")
    cmds.connectAttr("{}.angle".format(node_angleBetween),"{}.input1".format(node_divide))
    cmds.connectAttr("{}.output".format(node_half_cone_angle),"{}.input2".format(node_divide))

    node_subtract = cmds.createNode("subtractDL")
    cmds.setAttr("{}.input1".format(node_subtract),1)
    cmds.connectAttr("{}.output".format(node_divide),"{}.input2".format(node_subtract))


    # create condition node
    node_condition = cmds.createNode("condition",n="cd_condition")
    cmds.setAttr("{}.operation".format(node_condition),4)
    cmds.setAttr("{}.colorIfFalseR".format(node_condition),0)
    cmds.connectAttr("{}.output".format(node_subtract),"{}.colorIfTrueR".format(node_condition))

    cmds.connectAttr("{}.angle".format(node_angleBetween),"{}.firstTerm".format(node_condition))
    cmds.connectAttr("{}.output".format(node_half_cone_angle),"{}.secondTerm".format(node_condition))

    # return node
    

    pass