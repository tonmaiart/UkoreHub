from EasySkeleton import config
from EasySkeleton.config import *
import inspect, re, importlib, math, configparser
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om
import traceback
from EasySkeleton import utils
from PySide2 import QtWidgets, QtCore, QtUiTools, QtGui




def convert_class_path_to_class_instance(class_path):
    if not class_path:
        raise Exception("Class Path Invalid Input, Get {}".format(class_path))

    module_path, class_name = class_path.rsplit('.', 1)  # Split module class_instance and class node_name

    try:
        module = importlib.import_module(module_path)  # Import the module
        get_attr = getattr(module, class_name)

        return get_attr
    except:
        return False
def create_network_node(instance):
    """
    Create Network Node and Assign Main Attribute

    """
    # execute class instance
    class_instance = instance()

    # generate node_name
    node_name = class_instance.name
    del class_instance

    if not node_name:
        cmds.confirmDialog(m="Invalid Item Name In Instance, Check The Rig Modules. get {}".format(node_name))
        Exception("Invalid Item Name In Instance, Check The Rig Modules. get {}".format(node_name))

    while cmds.objExists(node_name):
        node_name += "_1"

    # create network node
    cmds.createNode("network", n=node_name)

    # add main attribute
    cmds.addAttr(node_name, k=1, ln="name", dt="string")
    cmds.addAttr(node_name, k=1, ln="enable", at="bool")
    cmds.addAttr(node_name, k=1, ln="isBuild", at="bool")
    cmds.addAttr(node_name, k=1, ln="class", dt="string")
    cmds.addAttr(node_name, k=1, ln="parent", dt="string")
    cmds.addAttr(node_name, k=1, ln="control_scale", at="float", min=0, max=1)
    cmds.addAttr(node_name, k=1, ln="debug_mode", at="bool")
    cmds.addAttr(node_name, k=1, ln="mirror_control_scale", at="bool")

    # set default value
    cmds.setAttr(node_name + ".name", node_name, typ="string")
    cmds.setAttr(node_name + ".isBuild", False)
    cmds.setAttr(node_name + ".enable", True)
    cmds.setAttr(node_name + ".class", str(instance).split("'")[1], typ="string")
    cmds.setAttr(node_name + ".control_scale", 0.4)

    return node_name
def convert_string_to_list(input_str):
    """
    Converts a string representation of a list into an actual Python list.

    Args:
    - input_str (str): The string representation of a list. Example: '["a","b","c"]'

    Returns:
    - list: The converted Python list. Example: ['a', 'b', 'c']
    """
    # Remove the leading and trailing brackets and spaces
    cleaned_str = input_str[1:-1]
    list_return = cleaned_str.split(",")

    for i, item in enumerate(list_return):
        member = item.replace("\"", "").replace("\'", "").replace(" ", "")
        list_return[i] = member

    return list_return

def get_variables_from_class(class_path):
    """
    Return Structure

    dict_output[ tab_name ] = [attribute]

    each attribute can be difference type such as input,label


    """

    def get_tab_name():
        # assign new tab_name
        if "# @" in line:
            strip_text = line.strip()
            new_tab_name = strip_text.replace("# @", "")

            # assign new key name to dict
            if new_tab_name not in dict_output:
                dict_output[new_tab_name] = []

                return new_tab_name

            else:
                return False

    def get_attribute():
        # ignore if no tab name for attribute
        if not tab_name:
            return

        # attribute type : input
        if "=" in line and "self." in line:
            try:
                dict_output[tab_name].append(line.split("=")[0].replace("", "").replace(" ", "").replace("self.", ""))
            except:
                pass

        # attribute type : seperator
        elif "# -" in line:
            dict_output[tab_name].append("blank")

        # attribute type : label
        elif "# $" in line:
            try:
                dict_output[tab_name].append("label:" + line.replace("# $", "".replace(" ", "")))
            except:
                pass

        # attribute type : script
        elif "# #" in line:
            try:
                clear_signal = line.replace("# #", "")
                delete_blank = clear_signal.replace(" ", "")
                final = ("script:{}".format(delete_blank))

                dict_output[tab_name].append(final)

            except:
                pass

        # attribute type : can be locked
        if "# *" in line:
            lock_variables = line.replace("# *", "").replace(" ", "")
            dict_lock[lock_variables] = []

            for var in dict_output[tab_name][::-1]:
                if var == lock_variables:
                    break

                dict_lock[lock_variables].append(var)

    # get all tab dictionary
    source_code = inspect.getsource(class_path.__init__)
    lines = source_code.splitlines()
    dict_output = {}
    dict_lock = {}

    tab_name = None

    # Loop through the lines to associate comments with variables
    for line in lines:
        # update key name
        new_tab_name = get_tab_name()

        if new_tab_name:
            tab_name = new_tab_name

        get_attribute()


    return dict_output, dict_lock

def generate_nice_name(text):
    # Replace underscores with spaces
    formatted_string = text.replace("_", " ")
    # Add a space before each uppercase letter that's not at the start
    formatted_string = re.sub(r"(?<!^)([A-Z])", r" \1", formatted_string)
    # Capitalize each word
    nice_name = " ".join(word.capitalize() for word in formatted_string.split())
    return nice_name


def add_attribute_to_node_name(node_name):
    """
    Add All Required Attribute from dict attribute

    """

    def add_attr_for_each_type(var_name,var_value,var_type):
        is_maya_attribute_exist = cmds.attributeQuery(var_name, node=node_name, exists=True)

        if is_maya_attribute_exist:
            current_maya_type = cmds.getAttr('{}.{}'.format(node_name, var_name), type=True)

            # skip for path
            if current_maya_type == "string" and var_type == "path" and is_maya_attribute_exist:
                return

            # delete attribute if attribute if wrong variable type
            elif is_maya_attribute_exist and current_maya_type != var_type:
                cmds.deleteAttr("{}.{}".format(node_name,var_name))

            # skip if already exist attribute
            elif is_maya_attribute_exist:
                # update enum for exist
                if var_type == "enum":
                    cmds.addAttr(f"{node_name}.{var_name}", edit=True, enumName=":".join(var_value))
                return

        # add attribute
        if var_type == "long":
            cmds.addAttr(node_name,k=1, ln=var_name, at="long", dv=var_value)

        elif var_type == "float":
            cmds.addAttr(node_name,k=1, ln=var_name, at="float", dv=var_value)

        elif var_type == "string" or var_type == "path":
            if type(var_value) != str:
                cmds.confirmDialog(m="Error, String type require string type : Check Docs , Module {} , Attr Name {}, Attr Value {}".format(node_name,var_name,var_value))
                raise Exception("string Type Require string type : Check Docs")

            cmds.addAttr(node_name,k=1, ln=var_name, dt="string")
            cmds.setAttr(node_name + "." + var_name, var_value, typ="string")

        elif var_type == "bool":
            if type(var_value) is not bool:
                cmds.confirmDialog(m="Attribute {} have invalid type, must be boolean , get {}".format(var_name,var_value))
                raise Exception("Attribute {} have invalid type, must be boolean , get {}".format(var_name,var_value))

            cmds.addAttr(node_name,k=1, ln=var_name, at="bool")
            cmds.setAttr(node_name + "." + var_name, var_value)

        elif var_type == "stringArray":
            if type(var_value) != list:
                cmds.confirmDialog(m="stringArray Type Require List Type : Check Docs")
                raise Exception("stringArray Type Require List Type : Check Docs")

            cmds.addAttr(node_name,k=1, ln=var_name, dt="stringArray")
            cmds.setAttr("{}.{}".format(node_name, var_name), type="stringArray", *([len(var_value)] + var_value))

        elif var_type == "enum":
            if type(var_value) != list:
                cmds.confirmDialog(m="enum type required list type : attribute {},get {}".format(var_name,var_value))
                raise Exception("enum type required list type : attribute {},get {}".format(var_name,var_value))

            cmds.addAttr(node_name,k=1, ln=var_name,en=":".join(var_value), at="enum")
            cmds.setAttr("{}.{}".format(node_name,var_name),0)

        elif var_type == "script":
            cmds.addAttr(node_name,k=1, ln=var_name, at="bool")
            cmds.setAttr(node_name + "." + var_name, False)

    class_path = cmds.getAttr("{}.class".format(node_name))
    instance_path = convert_class_path_to_class_instance(class_path)

    if not instance_path:
        return

    class_instance = instance_path()

    # create other variable
    dict_attribute = get_dict_attribute_by_class(class_instance)

    for attribute_name in dict_attribute.keys():
        if not hasattr(class_instance,attribute_name):
            continue

        attribute_type = dict_attribute[attribute_name][0]
        attribute_value = getattr(class_instance, attribute_name)

        add_attr_for_each_type(attribute_name,attribute_value,attribute_type)

    del class_instance

def get_dict_attribute_by_class(class_instance):
    """
    return dictionary that will have attribute name as key

    variables_dict[attribute_name] = [data_type,description]
    """

    docstring = class_instance.__doc__
    variables_dict = {}

    # all var type support
    list_type_valid = ["string","stringArray","long","float","bool","path","enum","script"]

    # Regular expression to match variable name, type, and description
    pattern = r'(\w+)\s*\(([\w\[\], ]+)\)\s*:\s*(.+)'

    # Split the docstring by lines and search for variable lines
    if docstring:
        for line in docstring.split('\n'):

            match = re.match(pattern, line.strip())

            if match:
                var_name = match.group(1)
                var_type = match.group(2)
                var_description = match.group(3)

                # if type invalid
                if var_type not in list_type_valid:
                    var_type = "None"

                # update variable dict
                variables_dict[var_name] = [var_type,var_description]

    return variables_dict







@utils.undoable
def create_rig(rig_name ="CharacterRig"):
    if is_rig_structures():
        cmds.confirmDialog("Already Rig in Scene")
    else:
        cmds.file(config.root_file+"/base.ma", i=1,force=True,  typ="mayaAscii",gn=rig_name)

def is_rig_structures():
    if cmds.objExists(config.ctrl_main):
        return True
    else:
        return False

def load_ui(ui_path):
    loader = QtUiTools.QUiLoader()
    ui = QtCore.QFile(ui_path)
    ui.open(QtCore.QFile.ReadOnly)
    ui_return = loader.load(ui)
    ui.close()

    return ui_return
def deleteControl(control):
    if cmds.workspaceControl(control, q=1, exists=1):
        cmds.deleteUI(control, control=True)
@utils.undoable
def add_mesh():
    selection = cmds.ls(sl=1)

    if selection:
        cmds.parent(selection, config.grp_mesh)

def debug(string,is_debug=False):
    if is_debug:
        print(string)

@utils.undoable
def add_global_joint():
    selection = cmds.ls(sl=1)

    if selection:
        cmds.parent(selection, config.grp_skin)

@utils.undoable
def add_local_joint():
    selection = cmds.ls(sl=1)

    if selection:
        cmds.parent(selection, config.grp_local)

@utils.undoable
def delete_rig():
    # backup global joint
    list_joint_global = cmds.listRelatives(config.grp_skin, ad=1, typ="joint")

    if list_joint_global:
        grp_joint_output = cmds.group(em=1, n="global_joints")

        # break all connection for joint
        [utils.break_connection(joint, pos=True, rot=True, scl=True) for joint in list_joint_global]

        for joint in cmds.listRelatives(config.grp_skin, c=1):
            cmds.parent(joint, grp_joint_output)

    # backup local joint
    list_joint_local = cmds.listRelatives(config.grp_local, ad=1, typ="joint")

    if list_joint_local:
        grp_joint_output = cmds.group(em=1, n="local_joints")

        # break all connection for joint
        [utils.break_connection(joint, pos=True, rot=True, scl=True) for joint in list_joint_local]

        for joint in cmds.listRelatives(config.grp_local, c=1):
            cmds.parent(joint, grp_joint_output)

    # backup mesh
    list_mesh = cmds.listRelatives(config.grp_mesh, c=1)

    if list_mesh:
        grp_mesh_output = cmds.group(em=1, n="meshes")

        for mesh in list_mesh:
            cmds.parent(mesh, grp_mesh_output)

    cmds.delete(cmds.listRelatives(config.grp_skin,p=1))
def rig_manage(add_model=False,add_joint=False,select_rig=False,add_rig=False,toggle_joint_vis=False,toggle_joint_axis=False,delete_rig=False,add_joint_local=False):
    importlib.reload(config)
    cmds.undoInfo(openChunk=True)
    selection = cmds.ls(sl=1)

    if is_rig_structures():
        if toggle_joint_vis:
            vis_value = cmds.getAttr(config.grp_skin + ".v")

            if vis_value:
                cmds.setAttr(config.grp_skin + ".v", 0)
            else:
                cmds.setAttr(config.grp_skin + ".v", 1)

        elif toggle_joint_axis:
            list_joint = cmds.listRelatives(config.grp_skin, ad=1, typ="joint")

            if not list_joint:
                return None

            list_on = []

            for joint in list_joint:
                list_on.append(cmds.getAttr(joint + ".displayLocalAxis"))

            if True in list_on:
                for joint in list_joint:
                    cmds.setAttr(joint + ".displayLocalAxis", 0)
            else:
                for joint in list_joint:
                    cmds.setAttr(joint + ".displayLocalAxis", 1)

    else:
        if add_rig:
            create_rig()


    cmds.undoInfo(closeChunk=True)
