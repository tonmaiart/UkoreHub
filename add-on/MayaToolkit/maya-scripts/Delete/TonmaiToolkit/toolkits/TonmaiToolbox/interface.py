from email.mime import base
from TonmaiToolkit import config
from TonmaiToolkit.core import (
    Utility,
    Transform,
    Misc,
    Connection,
    SkinWeight,
    Controller,
    File,
    QuickData,
    BlendShape,
)
from TonmaiToolkit.menu import Help
from TonmaiToolkit.module.PySide import QtCore, QtGui, QtWidgets, QAction

import os, importlib, webbrowser, inspect, configparser, re, json
from TonmaiToolkit.ui.interface_template import ToolkitWindow
import pymel.core as pm
import xml.etree.ElementTree as ET
import maya.cmds as mc
import ast
import time

Help.reload_scripts()


class MainWindow(ToolkitWindow):
    def __init__(self):
        # Set-up Interface
        super(MainWindow, self).__init__("TonmaiToolbox")

        self.local_rig_file_path = ""
        self.local_rig_file_name_only = ""
        self.local_rig_file_json = ""

        self.set_up_general_widget()
        self.set_up_quick_data_widget()
        self.set_up_shape_widget()

    def set_up_general_widget(self):
        def setAxisDisplay(display=False, allObj=False):
            # if no joints are selected, do it for all the joints in the scene
            # if allObj flag is True then this will toggle the axis display for all objects in the scene, not just joints.
            if not allObj:
                if len(mc.ls(sl=1, type="joint")) == 0:
                    jointList = mc.ls(type="joint")
                else:
                    jointList = mc.ls(sl=1, type="joint")
                # set the displayLocalAxis attribute to what the user specifies.
                for jnt in jointList:
                    mc.setAttr(jnt + ".displayLocalAxis", display)
            else:
                if len(mc.ls(sl=1)) == 0:
                    objList = mc.ls(transforms=1)
                else:
                    objList = mc.ls(sl=1)
                # set the displayLocalAxis attribute to what the user specifies.
                for obj in objList:
                    mc.setAttr(obj + ".displayLocalAxis", display)


        # rename widget tab
        self.dict_rename_target = {}
        self.dict_rename_output = {}

        # self.ui.pushButton_load_name_object.clicked.connect(self.load_rename_target)

        self.ui.lineEdit_search.textChanged.connect(self.update_rename_list_widget)
        self.ui.lineEdit_replace.textChanged.connect(self.update_rename_list_widget)
        self.ui.lineEdit_prefix.textChanged.connect(self.update_rename_list_widget)
        self.ui.lineEdit_suffix.textChanged.connect(self.update_rename_list_widget)
        self.ui.lineEdit_rename.textChanged.connect(self.update_rename_list_widget)
        self.ui.checkBox_auto_underscore.clicked.connect(self.update_rename_list_widget)

        self.ui.pushButton_quick_fill_rename.clicked.connect(self.quick_load)

        self.ui.pushButton_clear_all_text_box.clicked.connect(
            self.clear_all_rename_text_box
        )
        self.ui.pushButton_apply_name.clicked.connect(self.apply_rename)

        #########################
        # set attributes tab  ###
        #########################

        # self.ui.listWidget_attribute.currentItemChanged.connect(
        #     self.update_attribute_target
        # )
        # self.ui.listWidget_attribute.itemClicked.connect(
        #     self.update_attribute_target
        # )
        self.ui.lineEdit_search_attribute.textChanged.connect(
            self.update_attribute_target
        )

        self.ui.pushButton_false.clicked.connect(
            lambda x: self.set_attribute(0, typ="float")
        )
        self.ui.pushButton_true.clicked.connect(
            lambda x: self.set_attribute(1, typ="float")
        )
        self.ui.pushButton_apply_int_attribute.clicked.connect(
            lambda x: self.set_attribute(self.ui.spinBox_int.value(), typ="float")
        )
        self.ui.pushButton_apply_float_attribute.clicked.connect(
            lambda x: self.set_attribute(
                self.ui.doubleSpinBox_float.value(), typ="float"
            )
        )
        self.ui.comboBox_set_attribute_enum.currentTextChanged.connect(
            lambda x: self.set_attribute(
                self.ui.comboBox_set_attribute_enum.currentIndex(), typ="enum"
            )
        )
        self.ui.pushButton_set_matrix.clicked.connect(
            lambda x: self.set_attribute(
                self.ui.plainTextEdit_matrix_set.toPlainText(), typ="matrix"
            )
        )

        # snap to vertex

        self.DICT_TARGET = {}

        self.ui.pushButton_snap_joint_position.clicked.connect(self.snap_joint_position)

        self.ui.pushButton_add_target.clicked.connect(self.add_object_snap_target)
        self.ui.pushButton_update_vertex.clicked.connect(self.update_vertex_data)

        self.ui.pushButton_remove_all.clicked.connect(self.remove_all)

        self.ui.pushButton_axis_on.clicked.connect(lambda x : setAxisDisplay(display=True))
        self.ui.pushButton_axis_off.clicked.connect(lambda x : setAxisDisplay(display=False))

        self.ui.tabWidget.setCurrentIndex(0)

        # set current index
        self.ui.tabWidget.setCurrentIndex(0)

        ##########################
        #### Weight Puller #######
        ##########################


    def set_up_quick_data_widget(self):
        self.ui.pushButton_build_and_read_current.clicked.connect(
            lambda X: QuickData.build_and_read()
        )
        self.ui.pushButton_build_current.clicked.connect(
            lambda x: QuickData.build_current()
        )
        self.ui.pushButton_remove_rig.clicked.connect(lambda x: QuickData.remove_rig())
        self.ui.pushButton_hero_ctrl.clicked.connect(lambda x: QuickData.hero_ctrl())

        self.ui.pushButton_hero_hi.clicked.connect(lambda x: QuickData.hero_hi())

        # Quick Data
        self.ui.pushButton_create_quick_data_folder.clicked.connect(
            self.create_quick_data_folder
        )
        self.ui.pushButton_open_quick_data_folder.clicked.connect(
            lambda x: QuickData.open_quick_data_folder()
        )
        self.ui.pushButton_reload_quick_data_folder.clicked.connect(
            self.reload_quick_data_folder
        )
        self.reload_quick_data_folder()

        self.dict_skin_cluster_export = {}
        self.dict_skin_cluster_import = {}

        # controller quick data
        self.ui.pushButton_save_shape.clicked.connect(
            lambda x: QuickData.export_shape_quick()
        )
        self.ui.pushButton_read_shape.clicked.connect(
            lambda x: QuickData.import_shape_quick()
        )

        self.ui.pushButton_save_shape_custom.clicked.connect(
            lambda x: QuickData.export_shape_custom()
        )
        self.ui.pushButton_read_shape_custom.clicked.connect(
            lambda x: QuickData.import_shape_custom()
        )

        # skin weight quick data
        self.ui.pushButton_import_skin_quick.clicked.connect(
            lambda x: QuickData.import_skin_quick()
        )
        self.ui.pushButton_export_skin_quick.clicked.connect(
            lambda x: QuickData.export_skin_quick()
        )

        self.ui.pushButton_import_skin_custom.clicked.connect(
            lambda x: QuickData.import_skin_custom()
        )
        self.ui.pushButton_export_skin_custom.clicked.connect(
            lambda x: QuickData.export_skin_custom()
        )

        self.ui.pushButton_backup_all.clicked.connect(
            lambda x: QuickData.backup_controller_and_skin()
        )
        self.ui.pushButton_apply_all.clicked.connect(
            lambda x: QuickData.apply_controller_and_skin()
        )

        # Set Up Menu Clean Up
        self.menu_clean_up = QtWidgets.QMenu(self)
        self.ui.pushButton_quick_clean_up.clicked.connect(Misc.clean_up_scene)

        separator_label = QAction("----- File -----", self)
        separator_label.setEnabled(False)
        self.menu_clean_up.addAction(separator_label)

        self.ui.toolButton_clean_up_scene_extra.setMenu(self.menu_clean_up)
        self.action_import_all_reference = QAction("Import All Reference", self)
        self.action_import_all_reference.triggered.connect(Misc.import_all_references)
        self.menu_clean_up.addAction(self.action_import_all_reference)

        self.action_remove_all_namespace = QAction("Remove All Namespace", self)
        self.action_remove_all_namespace.triggered.connect(Misc.remove_all_namespaces)
        self.menu_clean_up.addAction(self.action_remove_all_namespace)

        self.reload_all_reference = QAction("Reload All Refrence", self)
        self.reload_all_reference.triggered.connect(
            lambda x: QuickData.reload_all_references()
        )
        self.menu_clean_up.addAction(self.reload_all_reference)

        separator_label = QAction("----- mGear -----", self)
        separator_label.setEnabled(False)
        self.menu_clean_up.addAction(separator_label)

        self.action_clean_mgear_node = QAction("Convert mGear node to Maya", self)
        self.action_clean_mgear_node.triggered.connect(
            Misc.clean_mgear_matrix_constraint
        )
        self.action_clean_mgear_node.triggered.connect(Misc.clean_mgear_mult_matrix)
        self.menu_clean_up.addAction(self.action_clean_mgear_node)

        separator_label = QAction("----- Display -----", self)
        separator_label.setEnabled(False)
        self.menu_clean_up.addAction(separator_label)

        self.action_show_channel_box_history = QAction("Show Channel Box History", self)
        self.action_show_channel_box_history.triggered.connect(
            Misc.show_channel_box_history
        )
        self.menu_clean_up.addAction(self.action_show_channel_box_history)

        self.action_hide_channel_box_history = QAction("Hide Channel Box History", self)
        self.action_hide_channel_box_history.triggered.connect(
            Misc.hide_channel_box_history
        )
        self.menu_clean_up.addAction(self.action_hide_channel_box_history)

        separator_label = QAction("----- Lock Group -----", self)
        separator_label.setEnabled(False)
        self.menu_clean_up.addAction(separator_label)

        self.action_lock_anim_grp = QAction("Lock Anim Group", self)
        self.action_lock_anim_grp.triggered.connect(Misc.lock_anim_grp)
        self.menu_clean_up.addAction(self.action_lock_anim_grp)

        self.action_unlock_anim_grp = QAction("Unlock Anim Group", self)
        self.action_unlock_anim_grp.triggered.connect(Misc.unlock_anim_grp)
        self.menu_clean_up.addAction(self.action_unlock_anim_grp)

        separator_label = QAction("----- Clean Up -----", self)
        separator_label.setEnabled(False)
        self.menu_clean_up.addAction(separator_label)

        self.action_clear_anim_curve = QAction("Clear Anim Curve", self)
        self.action_clear_anim_curve.triggered.connect(Misc.clear_controller_animation)
        self.menu_clean_up.addAction(self.action_clear_anim_curve)

        # self.action_clear_ngskin_node = QAction("Clear ngSkinning Node", self)
        # self.action_clear_ngskin_node.triggered.connect(Misc.clear_controller_animation)
        # self.menu_clean_up.addAction(self.action_clear_ngskin_node)

        # Script function
        self.ui.pushButton_edit_script.clicked.connect(
            lambda x: QuickData.create_script()
        )
        # self.ui.pushButton_open_script_folder.clicked.connect(lambda x:QuickData.open_script_folder())
        self.ui.pushButton_run_script.clicked.connect(
            lambda x: QuickData.run_script_file()
        )

        # Local Rig Data import
        self.ui.pushButton_import_rig.clicked.connect(self.import_local_rig)
        self.ui.pushButton_local_rig_browse.clicked.connect(self.browse_local_rig)
        self.ui.pushButton_open_local_rig_config_folder.clicked.connect(
            lambda x: QuickData.open_local_rig_config_folder()
        )
        self.ui.pushButton_edit_local_rig_config.clicked.connect(
            self.edit_local_rig_json
        )
        self.ui.pushButton_add_blend_shape_chain.clicked.connect(
            self.add_blend_shape_chain
        )
        self.ui.pushButton_browse_current_scene.clicked.connect(self.browse_current)
        self.ui.pushButton_jump_point.clicked.connect(lambda x: QuickData.jump_point())

    def set_up_shape_widget(self):

        def load_source_shape_operate():

            self.ui.lineEdit_source_shape_operate.setText(str(pm.ls(sl=1)[0]))

        def load_target_shape_operate():
            self.ui.lineEdit_target_shape_operate.setText(str(pm.ls(sl=1)[0]))

        def operate_shape(operation):
            BlendShape.create_operated_corrective_shape(
                object_A=self.ui.lineEdit_source_shape_operate.text(),
                object_B=self.ui.lineEdit_target_shape_operate.text(),
                operation=operation,
            )

        # variables
        self.base_mesh = None
        self.blend_shape_node = None
        self.dict_target_corrective = {}
        self.weight_mesh = "weight_split_mesh"
        self.grp_data = None
        self.grp_data_keyword = "ShapeToolkit_Grp"

        self.leftCtrl = ""
        self.rightCtrl = ""
        self.shape_Up = ""
        self.shape_Down = ""
        self.shape_In = ""
        self.shape_Out = ""
        self.shape_OutUp = ""
        self.shape_OutDown = ""
        self.shape_InUp = ""
        self.shape_InDown = ""

        # base data
        self.ui.pushButton_load_base_mesh.clicked.connect(self.load_base_mesh)
        self.ui.pushButton_reload_mesh.clicked.connect(self.refresh)
        self.ui.pushButton_select_data_grp.clicked.connect(self.select_data_grp)

        # blend shape driver
        self.ui.pushButton_load_weight_split.clicked.connect(
            self.create_or_select_weight_split
        )

        # corrictive pose
        self.ui.pushButton_add_current_mesh.clicked.connect(self.add_current_mesh)
        self.ui.pushButton_add_target_mesh.clicked.connect(self.add_exist_mesh)

        self.ui.pushButton_update_pose_data.clicked.connect(self.update_pose_data)

        self.ui.pushButton_apply_selected_corrective_shape.clicked.connect(
            lambda x: self.apply_corrective_shape(selected=True)
        )
        # self.ui.pushButton_apply_all_corrective_shape.clicked.connect(lambda x: self.apply_corrective_shape(selected=False))

        self.ui.listWidget_target_corrective.itemClicked.connect(
            self.isolate_full_shape
        )

        self.ui.pushButton_reset_pose.clicked.connect(self.reset_pose)

        self.ui.radioButton_edit_mode.clicked.connect(self.isolate_full_shape)

        self.ui.pushButton_remove_selected.clicked.connect(self.remove_selected)

        self.ui.pushButton_select_node.clicked.connect(self.select_node)

        self.ui.pushButton_load_left_ctrl.clicked.connect(
            lambda x: self.load_shape("LeftCtrl")
        )
        self.ui.pushButton_load_right_ctrl.clicked.connect(
            lambda x: self.load_shape("RightCtrl")
        )
        self.ui.pushButton_load_up.clicked.connect(lambda x: self.load_shape("Up"))
        self.ui.pushButton_load_down.clicked.connect(lambda x: self.load_shape("Down"))
        self.ui.pushButton_load_in.clicked.connect(lambda x: self.load_shape("In"))
        self.ui.pushButton_load_out.clicked.connect(lambda x: self.load_shape("Out"))
        self.ui.pushButton_load_out_up.clicked.connect(
            lambda x: self.load_shape("OutUp")
        )
        self.ui.pushButton_load_out_down.clicked.connect(
            lambda x: self.load_shape("OutDown")
        )
        self.ui.pushButton_load_in_up.clicked.connect(lambda x: self.load_shape("InUp"))
        self.ui.pushButton_load_in_down.clicked.connect(
            lambda x: self.load_shape("InDown")
        )

        self.ui.pushButton_update_blend_shape.clicked.connect(
            self.update_blend_shape_driver
        )
        self.ui.pushButton_exit_isolate.clicked.connect(self.exit_isolate)
        # tools
        self.ui.pushButton_build_split.clicked.connect(self.build_split)

        # auto once refresh
        self.refresh()

        #
        self.ui.pushButton_select_shape_up.clicked.connect(
            lambda x: self.isolate_object("Up")
        )
        self.ui.pushButton_select_shape_down.clicked.connect(
            lambda x: self.isolate_object("Down")
        )
        self.ui.pushButton_select_shape_in.clicked.connect(
            lambda x: self.isolate_object("In")
        )
        self.ui.pushButton_select_shape_out.clicked.connect(
            lambda x: self.isolate_object("Out")
        )

        self.ui.pushButton_select_shape_outUp.clicked.connect(
            lambda x: self.isolate_object("OutUp")
        )
        self.ui.pushButton_select_shape_outDown.clicked.connect(
            lambda x: self.isolate_object("OutDown")
        )
        self.ui.pushButton_select_shape_inUp.clicked.connect(
            lambda x: self.isolate_object("InUp")
        )
        self.ui.pushButton_select_shape_inDown.clicked.connect(
            lambda x: self.isolate_object("InDown")
        )

        # tools
        self.ui.pushButton_fill_source_shape_operate.clicked.connect(
            lambda x: load_source_shape_operate()
        )
        self.ui.pushButton_fill_target_shape_operate.clicked.connect(
            lambda x: load_target_shape_operate()
        )
        self.ui.pushButton_subtract_shape_operate.clicked.connect(
            lambda x: operate_shape("sub")
        )
        self.ui.pushButton_add_shape_operate.clicked.connect(
            lambda x: operate_shape("add")
        )

    # rename function -----------------------------------------
    def quick_load(self):
        self.ui.lineEdit_rename.setText(
            Utility.cut(str(list(self.dict_rename_output.keys())[0]))
        )

    def clear_all_rename_text_box(self):
        self.ui.lineEdit_rename.setText("")
        self.ui.lineEdit_search.setText("")
        self.ui.lineEdit_replace.setText("")
        self.ui.lineEdit_prefix.setText("")
        self.ui.lineEdit_suffix.setText("")

    def update_rename_list_widget(self):
        def add_prefix(input_text):
            prefix = self.ui.lineEdit_prefix.text()

            if prefix and self.ui.checkBox_auto_underscore.isChecked():
                prefix_full = "{}_".format(prefix)
            else:
                prefix_full = prefix

            return_name = prefix_full + input_text

            return return_name

        def add_suffix(input_text):
            prefix = self.ui.lineEdit_suffix.text()

            if prefix and self.ui.checkBox_auto_underscore.isChecked():
                append_text = "_{}".format(prefix)
            else:
                append_text = prefix

            return_name = input_text + append_text

            return return_name

        def get_rename_result(input_text, i):
            list_alphabet = [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
                "I",
                "J",
                "K",
                "L",
                "M",
                "N",
                "O",
                "P",
                "Q",
                "R",
                "S",
                "T",
                "U",
                "V",
                "W",
                "X",
                "Y",
                "Z",
            ]

            rename = self.ui.lineEdit_rename.text()

            # get dict rename

            if rename:
                base_name = rename
            else:
                base_name = input_text

            # alphabet lower
            if "$" in base_name:
                base_name = base_name.replace("$", list_alphabet[i])

            # symbol replace
            if "####" in base_name:
                base_name = base_name.replace("####", str(i + 1).zfill(4))
            if "###" in base_name:
                base_name = base_name.replace("###", str(i + 1).zfill(3))
            if "##" in base_name:
                base_name = base_name.replace("##", str(i + 1).zfill(2))
            if "#" in base_name:  # index
                base_name = base_name.replace("#", str(i + 1))

            return base_name

        def get_replace_result(input_text):
            def string_replace(string, search, replace):
                """Replaces all occurrences of search with replace in string."""
                if not search:
                    return string
                return string.replace(search, replace)

            search = self.ui.lineEdit_search.text()
            replace = self.ui.lineEdit_replace.text()

            new_short_name = string_replace(input_text, search, replace)
            return_name = new_short_name

            return return_name

        selection = pm.ls(sl=1)

        if not selection:
            self.dict_rename_target = {}
            return

        # update rename target
        if selection:
            self.dict_rename_target = {}

            for sel in selection:
                self.dict_rename_target[Utility.cut(str(sel))] = sel

            ##################################
            ######## update list widget ######
            ##################################
            model = QtGui.QStandardItemModel()
            self.ui.listView_rename_output.setModel(model)

            dict_output = {}

            for i, target_node in enumerate(list(self.dict_rename_target.values())):
                base_name = Utility.cut(str(target_node))

                name = get_rename_result(base_name, i)
                name = get_replace_result(name)
                name = add_prefix(name)
                name = add_suffix(name)

                dict_output[target_node] = name

            self.dict_rename_output = dict_output

            if self.dict_rename_output:
                for name in dict_output.values():
                    item = QtGui.QStandardItem(name)
                    model.appendRow(item)

    @Misc.undoable
    def apply_rename(self):
        dict_try_rename = {}

        for node in self.dict_rename_output.keys():
            name = self.dict_rename_output[node]
            output = node.rename(name)

            if output != name:
                dict_try_rename[node] = name

        # try again if rename not complete
        if dict_try_rename:
            for node in dict_try_rename.keys():
                name = dict_try_rename[node]
                node.rename(name)

        pm.inViewMessage(amg="<hl>Rename Apply</hl>", pos="botCenter", fade=True)

    # set attribute function -------------------------------------
    def update_attribute_target(self):
        ######################################
        # update target node in list widget ##
        ######################################

        list_set_attribute_target = pm.ls(sl=1)

        # update target node list
        self.ui.listWidget_node.clear()
        self.ui.listWidget_node.addItems(
            [str(Utility.cut(node)) for node in list_set_attribute_target]
        )

        #######################################
        # update search attribute name list ###
        #######################################

        attr = [item.text() for item in self.ui.listWidget_attribute.selectedItems()]

        print("attrs : ", attr)
        if not attr:
            return
        else:
            attr = attr[0]

        attr_type = None
        for node in list_set_attribute_target:
            attr_path = "{}.{}".format(node, attr)
            attr_obj = pm.Attribute(attr_path)

            # Query the type of the attribute
            attr_type = attr_obj.type()

            print("attr_type : ", attr_type)

        if not attr_type or attr_type == "None":
            return

        if attr_type == "bool":
            self.ui.tabWidget_set_attribute_by_type.setCurrentIndex(0)

        elif (
            attr_type == "float"
            or attr_type == "double"
            or attr_type == "doubleLinear"
            or attr_type == "doubleAngle"
        ):
            self.ui.doubleSpinBox_float.setValue(pm.getAttr(attr_path))
            self.ui.tabWidget_set_attribute_by_type.setCurrentIndex(1)

        elif attr_type == "int":
            self.ui.spinBox_int.setValue(pm.getAttr(attr_path))
            self.ui.tabWidget_set_attribute_by_type.setCurrentIndex(2)

        elif attr_type == "matrix":
            self.ui.tabWidget_set_attribute_by_type.setCurrentIndex(3)

            matrix = pm.getAttr(attr_path)
            self.ui.plainTextEdit_matrix_set.setPlainText(str(matrix))

        elif attr_type == "enum":
            self.ui.tabWidget_set_attribute_by_type.setCurrentIndex(4)

            enumStr = pm.attributeQuery(
                attr, node=list_set_attribute_target[0], listEnum=True
            )[0]
            enumValues = enumStr.split(":")

            self.ui.comboBox_set_attribute_enum.clear()
            self.ui.comboBox_set_attribute_enum.addItems(enumValues)

            self.ui.comboBox_set_attribute_enum.setCurrentIndex(pm.getAttr(attr_path))
        else:
            self.ui.tabWidget_set_attribute_by_type.setCurrentIndex(5)

        ##########################################
        # update_search_attribute_list_widget ####
        ##########################################

        def get_search_output(objs):
            if not objs:
                return []

            # Get all attribute long names of the first object
            list_attrs = []

            for i, obj in enumerate(objs):
                obj_attrs = pm.listAttr(obj)
                list_attrs.append(obj_attrs)

            mutual_attrs = set.intersection(*map(set, list_attrs))
            mutual_attrs = sorted(mutual_attrs)

            # get search result
            search_term = self.ui.lineEdit_search_attribute.text()

            if search_term:
                list_regular_search = []
                list_quick_search = []

                for attr in mutual_attrs:
                    if search_term.lower() == Utility.to_abbreviation_case(attr):
                        list_quick_search.append(attr)
                    elif search_term.lower() in attr.lower():
                        list_regular_search.append(attr)

                mutual_attrs = list_quick_search + list_regular_search

            return mutual_attrs

        """Updates the textScrollList with attributes that contain the search term."""
        self.ui.listWidget_attribute.clear()

        list_search_attr = get_search_output(list_set_attribute_target)

        self.ui.listWidget_attribute.addItems(list_search_attr)
        self.ui.listWidget_attribute.setCurrentRow(0)

    @Misc.undoable
    def set_attribute(self, value, typ="float"):
        """Retrieves the selected attribute and value from the UI and applies it."""
        attr = self.get_current_selected_module_name_single()

        for node in list_set_attribute_target:
            try:
                attr_path = "{}.{}".format(node, attr)

                if typ == "float" or typ == "enum" or typ == "int":
                    pm.setAttr(attr_path, value)

                elif typ == "matrix":
                    value = ast.literal_eval(value)

                    matrix = [elem for row in value for elem in row]

                    if attr == "matrix" or attr == "worldMatrix":
                        pm.xform(node, ws=1, m=matrix)
                    else:
                        pm.setAttr(attr_path, matrix, typ="matrix")

            except Exception as e:
                pm.displayWarning(
                    "Cannot Set Attribute for {}.{} : {}".format(node, attr, e)
                )

    def get_current_selected_module_name_single(self):
        list_item_name = self.get_current_selected_module_name()

        if list_item_name:
            return list_item_name[0]
        else:
            return

    def get_current_selected_module_name(self):
        return [item.text() for item in self.ui.listWidget_attribute.selectedItems()]

    # Snap to vertex funcion
    def remove_all(self):
        self.ui.listWidget_target.clear()
        self.DICT_TARGET = {}

    @Misc.undoable
    def snap_joint_position(self):
        for target_name in self.DICT_TARGET.keys():
            target_node = self.DICT_TARGET[target_name]["Node"]
            vertex_target = self.DICT_TARGET[target_name]["Data"]

            if not vertex_target:
                continue

            Transform.transform_to_vertex(
                target_object=target_node, list_vertex=vertex_target
            )

        pm.inViewMessage(amg="Snap All to selected vertex", pos="midCenter", fade=True)

    def update_snap_object_list_widget(self):
        selection = pm.ls(sl=1)

        if selection:
            single = selection[0]
        else:
            return

        try:
            for i in range(self.ui.listWidget_target.count()):
                item = self.ui.listWidget_target.item(i)
                item_text = item.text()

                if item_text == single:
                    self.ui.listWidget_target.setItemSelected(item, True)
                else:
                    pass
        except:
            pass

    def add_object_snap_target(self):
        selection = pm.ls(sl=1, typ="transform")

        for sel in selection:
            sel_name = Utility.cut(str(sel))

            if sel_name not in self.DICT_TARGET.keys():
                self.DICT_TARGET[sel_name] = {"Node": sel, "Data": []}

        self.update_list_widget()

        # select new one
        list_widget = self.ui.listWidget_target
        (
            list_widget.setCurrentRow(list_widget.count() - 1)
            if list_widget.count()
            else None
        )

    def update_vertex_data(self):
        list_vertex = pm.ls(sl=1, fl=1)

        for vertex in list_vertex:
            if ".vtx" not in str(vertex):
                return

        keys = [item.text() for item in self.ui.listWidget_target.selectedItems()]

        if keys:
            key = keys[0]
        else:
            return

        self.DICT_TARGET[key]["Data"] = list_vertex

        current_index = self.ui.listWidget_target.currentRow()

        self.update_list_widget()

        self.ui.listWidget_target.setCurrentRow(current_index + 1)

    def update_list_widget(self):
        self.ui.listWidget_target.clear()
        self.ui.listWidget_target.addItems(self.DICT_TARGET)

        # update color
        for i in range(self.ui.listWidget_target.count()):
            item = self.ui.listWidget_target.item(i)
            item_text = item.text()

            if self.DICT_TARGET[item_text]["Data"]:
                item.setBackground(QtGui.QBrush(QtGui.QColor("green")))

    # Quick Data
    def reload_quick_data_folder(self):
        quick_data_path = QuickData.get_quick_data_dir()

        if quick_data_path:
            self.ui.lineEdit_quick_data_dir.setText(quick_data_path)
            self.ui.groupBox_import_local_rig.setEnabled(True)

        else:
            self.ui.lineEdit_quick_data_dir.setText("")
            self.ui.groupBox_import_local_rig.setEnabled(False)

        return quick_data_path

    def create_quick_data_folder(self):
        current_file_path = pm.sceneName()

        if not current_file_path:
            pm.confirmDialog(m="Please save this file before create quick data.")
            return

        dir_path = os.path.dirname(current_file_path)

        # Define the subfolder structure
        subfolders = ["QuickData/Python", "QuickData/Skin", "QuickData/Controller"]

        # Create folders
        for folder in subfolders:
            full_path = os.path.join(dir_path, folder)
            os.makedirs(full_path, exist_ok=True)

        self.reload_quick_data_folder()

    def transfer_to_combine(self):
        combine_mesh = self.list_combine_weight_target[0]
        combine_shape = pm.listRelatives(combine_mesh, c=1, s=1)[0]

        # get all vertex data
        dict_match_vertex = SkinWeight.get_closest_vertex(
            sources=self.list_combine_weight_source,
            target=combine_mesh,
            absolute_match=True,
        )

        if not dict_match_vertex:
            return

        # prepare skincluster node and add influence
        list_add_influences = []
        for source in self.list_combine_weight_source:
            list_add_influences += SkinWeight.get_skin_cluster_influence(source)

        if SkinWeight.get_skin_cluster_node(combine_mesh):
            node_combine_skin_cluster = SkinWeight.get_skin_cluster_node(combine_mesh)

            for joint in list_add_influences:
                try:
                    pm.skinCluster(
                        node_combine_skin_cluster,
                        edit=True,
                        addInfluence=joint,
                        weight=0.0,
                    )
                except:
                    pass

        else:
            node_combine_skin_cluster = pm.skinCluster(
                list_add_influences, combine_mesh, tsb=True
            )

        # transfer weight
        for ref_mesh in self.list_combine_weight_source:
            dict_pair_vertex = dict_match_vertex[str(ref_mesh)]
            target_skinCluster = SkinWeight.get_skin_cluster_node(ref_mesh)

            print("target skin cluster : ", ref_mesh, target_skinCluster)

            for ref_vtx, combine_vtx in dict_pair_vertex.items():

                print("combine vertex : ")
                influences = pm.skinPercent(target_skinCluster, ref_vtx, q=1, t=None)
                values = pm.skinPercent(
                    target_skinCluster, ref_vtx, query=True, value=True
                )

                print("vtx infs,values : ", influences, values)

                dict_weight = dict(zip(influences, values))

                for influence, value in dict_weight.items():
                    pm.skinPercent(
                        node_combine_skin_cluster,
                        combine_vtx,
                        transformValue=[(influence, value)],
                    )

    def load_source_combine_weight(self):
        selection = pm.ls(sl=1)
        self.list_combine_weight_source = selection
        self.ui.lineEdit_source_to_combine.setText(str([str(sel) for sel in selection]))

    def load_target_combine_weight(self):
        selection = pm.ls(sl=1)
        self.list_combine_weight_target = selection
        self.ui.lineEdit_target_to_combine.setText(str([str(sel) for sel in selection]))

    def import_local_rig(self):

        dict_data = File.load_json_file_to_dict(self.local_rig_file_json)
        File.add_local_rig_from_file(
            file_path=self.local_rig_file_path, parent_config=dict_data
        )

    def edit_local_rig_json(self):
        # File.open_file(file_path=)
        os.startfile(self.local_rig_file_json)

    def create_json_rig_data(self):
        # get current quick data
        quick_data_current = QuickData.get_quick_data_dir()

        if not quick_data_current:
            return

        # try to create local rig data dir if not exist
        local_rig_data_path = os.path.join(quick_data_current, "LocalRigConfig")
        path_json = os.path.join(
            local_rig_data_path, "{}.json".format(self.local_rig_file_name_only)
        )
        os.makedirs(local_rig_data_path, exist_ok=True)

        # Create Json file if not exist
        data = {
            "main_mesh_group": "Geo_Grp",
            "rig_parent": ["rig", "neck_C0_head_ctl"],
            "mesh_parent": ["FclGeo_Grp", "LocalGeo_Grp"],
            "joint_parent": ["jnt_org", "jnt_org"],
            "geo_key_name": ["Body", "EyeBrows", "Cornea_L_Geo", "Cornea_R_Geo"],
        }

        if not os.path.exists(path_json):
            with open(path_json, "w") as json_file:
                json.dump(data, json_file, indent=4)

        # Update Variables
        self.local_rig_file_json = path_json

    def browse_current(self):
        self.local_rig_file_path = pm.sceneName()
        self.local_rig_file_name_only = os.path.splitext(
            os.path.basename(self.local_rig_file_path)
        )[0]

        # update widget
        self.ui.lineEdit_local_rig_browse.setText(self.local_rig_file_name_only)

        self.create_json_rig_data()

    def browse_local_rig(self):
        scene_path = pm.sceneName()
        default_dir = (
            os.path.dirname(scene_path)
            if scene_path
            else pm.workspace(q=True, rootDirectory=True)
        )

        file_path = pm.fileDialog2(
            fileMode=1,
            dialogStyle=1,
            startingDirectory=default_dir,
            fileFilter="Maya Files (*.ma *.mb)",
        )

        if not file_path:
            return
        else:
            file_path = file_path[0]

        print("file path : ", file_path)
        self.local_rig_file_path = file_path
        self.local_rig_file_name_only = os.path.splitext(
            os.path.basename(self.local_rig_file_path)
        )[0]

        # update widget
        self.ui.lineEdit_local_rig_browse.setText(self.local_rig_file_name_only)

        self.create_json_rig_data()

    def add_blend_shape_chain(self):
        dict_data = File.load_json_file_to_dict(self.local_rig_file_json)

        list_geo_group = [dict_data["mesh_parent"][0]]
        geo_key_name = dict_data["geo_key_name"]

        BlendShape.add_multi_local_blendshape(
            list_geo_group=list_geo_group, geo_key_name=geo_key_name
        )

    def swap_weight(self):
        source_text = self.ui.lineEdit_source_keyword.text()
        target_text = self.ui.lineEdit_target_keyword.text()

        self.ui.lineEdit_source_keyword.setText(target_text)
        self.ui.lineEdit_target_keyword.setText(source_text)

    @Misc.undoable
    def move_weight(self):
        start = time.time()

        weight_percent = self.ui.doubleSpinBox_move_weight.value()
        source_text = self.ui.lineEdit_source_keyword.text()
        target_text = self.ui.lineEdit_target_keyword.text()

        selection = pm.ls(sl=1, fl=1)
        if not selection:
            return

        skin_cluster_node = SkinWeight.get_skin_cluster_node(selection[0])
        all_influence = [str(inf) for inf in SkinWeight.get_skin_cluster_influence(skin_cluster_node)]

        dict_pair = {
            src: src.replace(source_text, target_text)
            for src in all_influence
            if source_text in src and src.replace(source_text, target_text) in all_influence
        }

        if not dict_pair:
            return

        all_exist_pair_source = set(dict_pair.keys())

        skin_percent_q = pm.skinPercent

        for vtx in selection:
            list_inf_value = skin_percent_q(skin_cluster_node, vtx, query=True, v=True)
            list_inf_name = [str(n) for n in pm.skinCluster(vtx, inf=True, q=True)]
            dict_weight_data = dict(zip(list_inf_name, list_inf_value))

            for source_jnt, source_jnt_value in dict_weight_data.items():
                if source_jnt_value <= 0 or source_jnt not in all_exist_pair_source:
                    continue

                target_jnt = dict_pair[source_jnt]
                target_jnt_value = dict_weight_data.get(target_jnt, 0.0)

                sum_value = source_jnt_value + target_jnt_value
                t_val = weight_percent * sum_value
                s_val = sum_value - t_val

                skin_percent_q(
                    skin_cluster_node,
                    vtx,
                    transformValue=[[source_jnt, s_val], [target_jnt, t_val]],
                )

        print("Move Weight time:", time.time() - start, "seconds")


    def create_operated_corrective_shape(
        object_base="base",
        object_weight="weight",
        object_target="target",
        object_result="max_model_v008_body1",
    ):

        def get_vertex_positions_from_duplicate(obj_name):
            """Duplicate an object, get its vertex positions, then delete the duplicate."""
            dup = pm.duplicate(obj_name, name="tmp_vtx_extract")[0]
            positions = {}
            vtx_count = pm.polyEvaluate(dup, vertex=True)

            for i in range(vtx_count):
                pos = pm.xform(f"{dup}.vtx[{i}]", q=1, os=1, t=True)
                positions[i] = tuple(pos)

            pm.delete(dup)  # delete the temporary duplicate
            return positions

        def vector_list_operation(list1, list2, operation="add"):
            """
            Perform element-wise addition or subtraction between
            two lists of 3D vectors.

            Args:
                list1 (list of tuple): List of (x, y, z) vectors.
                list2 (list of tuple): List of (x, y, z) vectors.
                operation (str): 'add' or 'sub'.

            Returns:
                list of tuple: Resulting list of (x, y, z) vectors.
            """
            if len(list1) != len(list2):
                raise ValueError(
                    f"List lengths must match. Got {len(list1)} vs {len(list2)}."
                )

            results = []
            for v1, v2 in zip(list1, list2):
                if len(v1) != 3 or len(v2) != 3:
                    raise ValueError("All vectors must be 3D tuples/lists.")
                if operation == "add":
                    results.append((v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2]))
                elif operation == "sub":
                    results.append((v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2]))
                else:
                    raise ValueError("Operation must be 'add' or 'sub'.")
            return results

        vtxs_base = get_vertex_positions_from_duplicate("base").values()
        vtxs_weight = get_vertex_positions_from_duplicate("weight").values()
        vtxs_target = get_vertex_positions_from_duplicate("target").values()

        # get list result
        vtxs_result = vector_list_operation(vtxs_target, vtxs_weight, "sub")
        vtxs_result = vector_list_operation(vtxs_result, vtxs_base, "add")

        for i, pos in enumerate(vtxs_result):
            pm.xform("{}.vtx[{}]".format(object_result, i), os=1, t=pos)

    def convert_full_to_corrective_shape(
        object_base="base",
        object_weight="weight",
        object_target="target",
        object_result="max_model_v008_body1",
    ):
        """
        Convert Full Shape (regular blend shape mesh) to Corrective Shape (Shape that append to pose shape )

        """

        vtxs_base = get_vertex_positions_from_duplicate(object_base).values()
        vtxs_weight = get_vertex_positions_from_duplicate(object_weight).values()
        vtxs_target = get_vertex_positions_from_duplicate(object_target).values()

        # get list result
        vtxs_result = vector_list_operation(vtxs_target, vtxs_weight, "sub")
        vtxs_result = vector_list_operation(vtxs_result, vtxs_base, "add")

        for i, pos in enumerate(vtxs_result):
            pm.xform("{}.vtx[{}]".format(object_result, i), os=1, t=pos)

    def get_vertex_positions_from_duplicate(obj_name):
        print("object name : ", obj_name)

        # get shape from given name
        shape = pm.listRelatives(obj_name, c=1, s=1)[0]

        # get vertex count
        vtx_count = pm.polyEvaluate(shape, vertex=True)

        # query postion
        positions = {}
        for i in range(vtx_count):
            pos = pm.xform("{}.vtx[{}]".format(shape, i), q=1, os=1, t=True)
            positions[i] = tuple(pos)

        return positions

    def vector_list_operation(list1, list2, operation="add"):
        """
        Perform element-wise addition or subtraction between
        two lists of 3D vectors.

        Args:
            list1 (list of tuple): List of (x, y, z) vectors.
            list2 (list of tuple): List of (x, y, z) vectors.
            operation (str): 'add' or 'sub'.

        Returns:
            list of tuple: Resulting list of (x, y, z) vectors.
        """
        if len(list1) != len(list2):
            raise ValueError(
                f"List lengths must match. Got {len(list1)} vs {len(list2)}."
            )

        results = []
        for v1, v2 in zip(list1, list2):
            if len(v1) != 3 or len(v2) != 3:
                raise ValueError("All vectors must be 3D tuples/lists.")
            if operation == "add":
                results.append((v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2]))
            elif operation == "sub":
                results.append((v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2]))
            else:
                raise ValueError("Operation must be 'add' or 'sub'.")
        return results

    def exit_isolate(self):
        pm.isolateSelect("modelPanel4", state=False)

        self.grp_data.visibility.set(False)

        pm.select(cl=True)

    def isolate_object(self, obj):
        self.grp_data.visibility.set(True)

        pm.select(obj)
        pm.setAttr("{}.v".format(obj), True)

        # # Get the panel that currently has focus
        # current_panel = pm.getPanel(wf=True)
        # panel_type = pm.getPanel(to=current_panel)

        # # Only run if it's a viewport (modelPanel)
        # if panel_type == "modelPanel":
        #     is_on = pm.isolateSelect(current_panel, q=True, s=True)
        #     pm.enableIsolateSelect(current_panel, not is_on)

        return

    def load_shape(self, shape):

        selection = pm.ls(sl=1)

        if selection:

            mesh = selection[0]

            # # raise error if mesh
            # if "|" in str(mesh):
            #     pm.error("{} is too many object with duplicate name".format(mesh))
            #     return

        else:
            mesh = ""

        if shape == "LeftCtrl":
            if mesh == "":
                self.leftCtrl = mesh
            else:
                self.leftCtrl = mesh.shortName()

            self.ui.pushButton_select_left_ctrl.setText(self.leftCtrl)
            pm.setAttr("{}.leftCtrl".format(self.grp_data), self.leftCtrl)

        elif shape == "RightCtrl":
            if mesh == "":
                self.rightCtrl = mesh
            else:
                self.rightCtrl = mesh.shortName()

            self.ui.pushButton_select_right_ctrl.setText(self.rightCtrl)
            pm.setAttr("{}.rightCtrl".format(self.grp_data), self.rightCtrl)

        elif shape == "Up":
            if mesh == "":
                self.shape_Up = mesh
            else:
                self.shape_Up = mesh.shortName()

            self.ui.pushButton_select_shape_up.setText(self.shape_Up)
            pm.setAttr("{}.up".format(self.grp_data), self.shape_Up)

        elif shape == "Down":
            if mesh == "":
                self.shape_Down = mesh
            else:
                self.shape_Down = mesh.shortName()

            self.ui.pushButton_select_shape_down.setText(self.shape_Down)
            pm.setAttr("{}.down".format(self.grp_data), self.shape_Down)

        elif shape == "In":
            if mesh == "":
                self.shape_In = mesh
            else:
                self.shape_In = mesh.shortName()

            self.ui.pushButton_select_shape_in.setText(self.shape_In)
            pm.setAttr("{}.in".format(self.grp_data), self.shape_In)

        elif shape == "Out":
            if mesh == "":
                self.shape_Out = mesh
            else:
                self.shape_Out = mesh.shortName()

            self.ui.pushButton_select_shape_out.setText(self.shape_Out)
            pm.setAttr("{}.out".format(self.grp_data), self.shape_Out)

        elif shape == "OutUp":
            if mesh == "":
                self.shape_OutUp = mesh
            else:
                self.shape_OutUp = mesh.shortName()

            self.ui.pushButton_select_shape_outUp.setText(self.shape_OutUp)
            pm.setAttr("{}.outUp".format(self.grp_data), self.shape_OutUp)

        elif shape == "OutDown":
            if mesh == "":
                self.shape_OutDown = mesh
            else:
                self.shape_OutDown = mesh.shortName()

            self.ui.pushButton_select_shape_outDown.setText(self.shape_OutDown)
            pm.setAttr("{}.outDown".format(self.grp_data), self.shape_OutDown)

        elif shape == "InUp":
            if mesh == "":
                self.shape_InUp = mesh
            else:
                self.shape_InUp = mesh.shortName()

            self.ui.pushButton_select_shape_inUp.setText(self.shape_InUp)
            pm.setAttr("{}.inUp".format(self.grp_data), self.shape_InUp)

        elif shape == "InDown":
            if mesh == "":
                self.shape_InDown = mesh
            else:
                self.shape_InDown = mesh.shortName()

            self.ui.pushButton_select_shape_inDown.setText(self.shape_InDown)
            pm.setAttr("{}.inDown".format(self.grp_data), self.shape_InDown)

    @Misc.undoable
    def create_or_select_weight_split(self):
        if not self.base_mesh:
            pm.warning("require base shape mesh to create weight split")
            return

        if pm.objExists(self.weight_mesh):
            pm.select(self.weight_mesh)

            pm.inViewMessage(
                amg="<hl> Select Weight Split Mesh</hl>",
                pos="botCenter",
                fit=20,
                fts=16,
                fade=True,
            )

        else:
            # create object
            print(self.base_mesh)
            pm.duplicate(self.base_mesh, n=self.weight_mesh)[0]

            jnt_left = pm.createNode("joint", n="jnt_split_L")
            jnt_right = pm.createNode("joint", n="jnt_split_R")

            pm.parent(jnt_left, jnt_right, self.grp_data)

            try:
                pm.parent(self.weight_mesh, self.grp_data)
            except:
                pass

            pm.xform(jnt_left, t=(1, 1, 1), ws=1)
            pm.xform(jnt_right, t=(-1, 1, 1), ws=1)

            # bind skin
            pm.skinCluster(jnt_left, jnt_right, self.weight_mesh, bm=1)

            self.ui.lineEdit_weight_split.setText(self.weight_mesh)

            pm.select(self.weight_mesh)

            pm.inViewMessage(
                amg="<hl> Create New Split Mesh</hl>",
                pos="botCenter",
                fit=20,
                fts=16,
                fade=True,
            )

    @Misc.undoable
    def build_split(self):
        list_split_mesh = pm.ls(sl=1)

        if not list_split_mesh:
            pm.warning("Select Meshes Target for split first.")
        elif pm.objExists(self.weight_mesh):

            # Launch loading screen
            factor = 100 / len(list_split_mesh)
            amount = 0
            pm.progressWindow(
                title="Doing Nothing",
                progress=amount,
                status="Preparing: 0%",
                isInterruptable=True,
            )

            # update weight data to json
            pm.select(self.weight_mesh)
            QuickData.export_skin_quick()

            # get weight data
            quick_data_path = QuickData.get_quick_data_dir()
            json_path = os.path.join(
                quick_data_path, "Skin", "{}.json".format(self.weight_mesh)
            )

            # check is path exist
            if not os.path.exists(json_path):
                pm.error("Please Export Skin of {} First.".format(self.weight_mesh))

            # load json data
            dict_data = File.load_json_file_to_dict(json_path)

            # create splited shape
            output = []
            for i, shape in enumerate(list_split_mesh):
                # update progress
                amount += i * factor
                pm.progressWindow(
                    edit=True,
                    progress=amount,
                    status=(
                        "Spliting {}/{} : {}".format(i + 1, len(list_split_mesh), shape)
                    ),
                )

                # split shape
                each_output = BlendShape.split_blendshape(
                    L_joint="jnt_split_L",
                    R_joint="jnt_split_R",
                    split_weight_mesh=self.weight_mesh,
                    base_mesh=self.base_mesh,
                    target_mesh=shape,
                    custom_weight_data=dict_data,
                )

                output += each_output

            # try to parent output to world
            try:
                pm.parent(output, w=1)
            except:
                pass

            pm.select(output)

            # close progress window
            pm.progressWindow(endProgress=1)

            # display
            pm.inViewMessage(
                amg="<hl> Split Complete!</hl>",
                pos="botCenter",
                fit=20,
                fts=16,
                fade=True,
            )

        else:
            pm.warning("Required Weight Mesh Created")

    def select_node(self):
        if self.blend_shape_node and pm.objExists(self.blend_shape_node):
            pm.select(self.blend_shape_node)

            pm.inViewMessage(
                amg="<hl>Select Blend Shape Node</hl>", pos="midCenter", fade=True
            )

    def select_data_grp(self):
        if self.grp_data:
            pm.select(self.grp_data)

            pm.inViewMessage(
                amg="<hl>Select Grp Data </hl>", pos="midCenter", fade=True
            )

    def create_grp_data_attribute(self):
        pm.addAttr(self.grp_data, ln="baseMesh", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="shapeMeshes", dt="stringArray", k=True)

        pm.addAttr(self.grp_data, ln="leftCtrl", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="rightCtrl", dt="string", k=True)

        pm.addAttr(self.grp_data, ln="up", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="down", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="in", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="out", dt="string", k=True)

        pm.addAttr(self.grp_data, ln="outUp", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="outDown", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="inUp", dt="string", k=True)
        pm.addAttr(self.grp_data, ln="inDown", dt="string", k=True)

    def select_item_by_name(self, name):
        list_widget = self.ui.listWidget_target_corrective

        """Selects the item in a QListWidget that matches the given name."""
        matches = list_widget.findItems(name, QtCore.Qt.MatchExactly)
        if matches:
            list_widget.setCurrentItem(matches[0])
            return True
        return False

    def load_base_mesh(self, mesh_corrective=None):
        if mesh_corrective:
            selection = [mesh_corrective]
        elif not mesh_corrective:
            selection = pm.ls(sl=1)

        if not selection or len(selection) == 0:
            pm.inViewMessage(amg="Found", pos="midCenter", fade=True)

            return

        # assign grp data
        self.grp_data = "{}_{}".format(selection[0], self.grp_data_keyword)

        if pm.objExists(self.grp_data):
            pm.warning("You Already have {} in the scene".format(self.grp_data))
            return

        # recheck input
        if len(selection) != 1 or pm.listRelatives(selection, c=1, typ="mesh") is None:
            self.base_mesh = None
            self.ui.lineEdit_base_mesh.setText("")
            self.ui.lineEdit_blend_shape_node.setText("")

            return

        self.base_mesh = selection[0]

        # reset dict corrective
        self.dict_target_corrective = {}
        self.ui.listWidget_target_corrective.clear()

        self.blend_shape_node = BlendShape.get_blendshape_node(self.base_mesh)

        # update blend shape variables and widget
        if not self.blend_shape_node:
            result = pm.confirmDialog(
                m="Blend shape node not exist. Create new one?",
                button=["Create New", "Cancel"],
                defaultButton="Create New",
                cancelButton="Cancel",
                dismissString="Cancel",
            )

            if result == "Create New":
                result = pm.promptDialog(
                    title="Create New Corrective Blend Shape",
                    message="Enter Blend Shape Node Name:",
                    button=["OK", "Cancel"],
                    defaultButton="OK",
                    cancelButton="Cancel",
                    dismissString="Cancel",
                    tx="corrective_blendShape",
                )

                if result == "OK":
                    text = pm.promptDialog(query=True, text=True)
                    self.blend_shape_node = pm.blendShape(
                        self.base_mesh, n=text, at=True
                    )[0]
                    pm.inViewMessage(
                        amg="Created new blendShape : {}".format(self.blend_shape_node),
                        pos="midCenter",
                        fade=True,
                    )

                else:
                    return

            elif result == "Cancel":
                self.ui.lineEdit_blend_shape_node.setText("")
                self.ui.lineEdit_base_mesh.setText("")

                return

        if self.blend_shape_node:
            self.ui.lineEdit_blend_shape_node.setText(str(self.blend_shape_node))
            self.ui.lineEdit_base_mesh.setText(str(self.base_mesh))

            self.load_list_target_from_exist_group()

            # display base mesh
            self.show_base_mesh()

        self.ui.lineEdit_base_mesh.setText(str(self.base_mesh))

        # create group data
        pm.group(em=1, n=self.grp_data)
        self.create_grp_data_attribute()

        pm.setAttr(
            "{}.{}".format(self.grp_data, "baseMesh"), str(self.base_mesh), typ="string"
        )

    def load_list_target_from_exist_group(self):
        # find exist full shape grp
        if not pm.objExists("{}_Corrective_Grp".format(self.blend_shape_node)):
            return

        # reset dict corrective
        self.dict_target_corrective = {}
        self.ui.listWidget_target_corrective.clear()

        # update dict target corrective
        for obj in pm.listRelatives(self.get_corrective_grp(), c=1):
            if not "_FullShape" in str(obj):
                continue

            self.dict_target_corrective[str(obj).replace("_FullShape", "")] = obj

        # debug
        self.ui.listWidget_target_corrective.addItems(
            [str(target) for target in self.dict_target_corrective.keys()]
        )

    def text_to_dict(self, text):
        return ast.literal_eval("{" + text + "}")

    def reset_pose(self):
        """Reset all controller transform"""
        for shape in self.dict_target_corrective:
            full_shape_mesh = "{}_FullShape".format(shape)

            # set pose from pose data
            list_array_text = pm.getAttr("{}.controller_data".format(full_shape_mesh))

            if not list_array_text:
                continue

            for text_data in list_array_text:
                dict_data = self.text_to_dict(text_data)

                controller = list(dict_data.keys())[0]

                translate, rotate, scale = [(0, 0, 0), (0, 0, 0), (1, 1, 1)]

                # is controller exist
                if not pm.objExists(controller):
                    continue

                # set transform
                for attr_name, values in [
                    ("t", translate),
                    ("r", rotate),
                    ("s", scale),
                ]:
                    for i, axis in enumerate("xyz"):
                        try:
                            pm.setAttr(f"{controller}.{attr_name}{axis}", values[i])
                        except:
                            pass

        # turn off all blend shape
        for shape in self.dict_target_corrective.keys():
            pm.setAttr("{}.{}".format(self.blend_shape_node, shape), 0)

        self.show_base_mesh()
        pm.inViewMessage(amg="Pose Reset", pos="midCenter", fade=True)

    def update_pose_data(self):
        # get dict pose data
        maya_selection = pm.ls(sl=1)

        dict_pose_data = {}
        list_write_pose_data = []

        for control in maya_selection:
            dict_pose_data[str(control)] = (
                list(control.translate.get()),
                list(control.rotate.get()),
                list(control.scale.get()),
            )

        for key in dict_pose_data.keys():
            transform = dict_pose_data[key]
            list_write_pose_data.append(
                '"{}":({},{},{})'.format(key, transform[0], transform[1], transform[2])
            )

        # update pose to selected full path attribute
        selection = [
            item.text() for item in self.ui.listWidget_target_corrective.selectedItems()
        ]

        if selection:
            full_shape_mesh = selection[0] + "_FullShape"
        else:
            return

        pm.setAttr(
            "{}.controller_data".format(full_shape_mesh),
            list_write_pose_data,
            typ="stringArray",
        )

        pm.inViewMessage(
            amg="Pose Data Updated to Shape : {}".format(selection[0]),
            pos="midCenter",
            fade=True,
        )

    def create_full_shape(self, shape_name, source_mesh=None):
        if not source_mesh:
            source_mesh = self.base_mesh

        full_shape_mesh_name = shape_name + "_FullShape"

        full_shape_mesh = pm.duplicate(source_mesh, n=full_shape_mesh_name)[0]

        # parent to group
        pm.parent(full_shape_mesh, self.get_corrective_grp())

        # hide
        full_shape_mesh.visibility.set(False)

        # add attribute
        pm.addAttr(full_shape_mesh, ln="keyframe", at="long", k=1)
        pm.setAttr("{}.keyframe".format(full_shape_mesh), pm.currentTime(query=True))

        pm.addAttr(full_shape_mesh, dt="stringArray", ln="controller_data", k=1)

        return full_shape_mesh

    def create_pose_shape(self, full_shape_mesh):
        # turn blendshape off
        if self.blend_shape_node.envelope.get() == True:
            self.blend_shape_node.envelope.set(False)

        # set current time to match pose
        # pm.currentTime(pm.getAttr("{}.keyframe".format(full_shape_mesh)))

        # create pose shape
        pose_shape = pm.duplicate(
            self.base_mesh, n=full_shape_mesh.replace("_FullShape", "_PoseShape")
        )[0]
        pm.parent(pose_shape, self.get_corrective_grp())
        pose_shape.visibility.set(False)

        # set blendshape envelope back
        self.blend_shape_node.envelope.set(True)

        return pose_shape

    def create_corrective_grp(self):
        # create group for store data
        if not pm.objExists(self.get_corrective_grp()):
            pm.group(em=1, n=self.get_corrective_grp())

    def get_shape_orig(self, name="base_shape"):
        object = pm.duplicate(self.base_mesh, n=name)[0]

        pm.parent(object, w=1)

        list_orig_shape = []
        list_delete_shape = []

        list_shape = pm.listRelatives(object, c=1, s=1, typ="mesh")

        for shape in list_shape:
            if "Orig" not in str(shape):
                pm.delete(shape)
            else:
                pm.setAttr("{}.intermediateObject".format(shape), False)

        return object

    @Misc.undoable
    def apply_corrective_shape(self, selected=False):
        """
        Apply Full Shape to Corrective shape
        """

        # get target
        if selected:
            list_target_key = [
                item.text()
                for item in self.ui.listWidget_target_corrective.selectedItems()
            ]
        else:
            list_target_key = self.dict_target_corrective.keys()

        print("Applying All Corrective Shape")

        # create tmp dummy base shape
        base_shape = self.get_shape_orig()
        print("Crated Orig Shape : ", base_shape)

        # operation
        for sel in list_target_key:
            pose_shape_mesh = "{}_PoseShape".format(sel)
            full_shape_mesh = "{}_FullShape".format(sel)

            # skip if pose shape or full shape not found
            if not pm.objExists(full_shape_mesh):
                continue

            # update pose shape
            if not pm.objExists(pose_shape_mesh):
                self.create_pose_shape(full_shape_mesh=full_shape_mesh)

            # apply to corrective shape
            print("Applying : ", full_shape_mesh)
            func.convert_full_to_corrective_shape(
                object_base=base_shape,
                object_weight=pose_shape_mesh,
                object_target=full_shape_mesh,
                object_result=sel,
            )

        pm.delete(base_shape)

        print("Apply Corrective Shape Complete!")

        self.show_base_mesh()

    def get_corrective_grp(self):
        return "{}_Corrective_Grp".format(self.blend_shape_node)

    def show_base_mesh(self):
        # hide all shape
        if pm.objExists(self.get_corrective_grp()):
            for child in pm.listRelatives(self.get_corrective_grp(), c=1):
                child.visibility.set(False)

        # clear list widget selection
        self.ui.listWidget_target_corrective.clearSelection()

        # show base mesh
        self.base_mesh.visibility.set(True)

        # select base mesh
        # pm.select(self.base_mesh)

    def get_list_widget_selection(self):
        selection = [
            item.text() for item in self.ui.listWidget_target_corrective.selectedItems()
        ]

        return selection

    def remove_selected(self):
        selection = self.get_list_widget_selection()

        if not selection:
            return

        for sel in selection:
            full_shape_mesh = "{}_FullShape".format(sel)
            pose_shape_mesh = "{}_PoseShape".format(sel)

            if pm.objExists(full_shape_mesh):
                pm.delete(full_shape_mesh)

            if pm.objExists(pose_shape_mesh):
                pm.delete(pose_shape_mesh)

        self.load_list_target_from_exist_group()

        # select the last one
        list_widget = self.ui.listWidget_target_corrective
        (
            list_widget.setCurrentRow(list_widget.count() - 1)
            if list_widget.count()
            else None
        )
        self.isolate_full_shape()

        pm.inViewMessage(amg="Removed", pos="midCenter", fade=True)

    def isolate_full_shape(self):
        print("Isolate Mode")

        selection = self.get_list_widget_selection()

        if not selection:
            return

        full_shape_mesh = selection[0] + "_FullShape"

        # return if not found full shape
        if not pm.objExists(full_shape_mesh):
            return

        # hide all shape, include base shape
        if pm.objExists(self.get_corrective_grp()):
            for child in pm.listRelatives(self.get_corrective_grp(), c=1):
                child.visibility.set(False)

        self.base_mesh.visibility.set(False)

        # set visibility on for selection
        if self.ui.radioButton_edit_mode.isChecked():
            self.ui.pushButton_apply_selected_corrective_shape.setEnabled(True)
            pm.setAttr("{}.v".format(full_shape_mesh), True)
            pm.inViewMessage(
                amg="Edit Mode".format(self.blend_shape_node),
                pos="midCenter",
                fade=True,
            )

        else:
            self.ui.pushButton_apply_selected_corrective_shape.setEnabled(False)
            pm.setAttr("{}.v".format(self.base_mesh), True)
            pm.inViewMessage(
                amg="Base Shape Display".format(self.blend_shape_node),
                pos="midCenter",
                fade=True,
            )

        # set pose from pose data
        list_array_text = pm.getAttr("{}.controller_data".format(full_shape_mesh))

        if not list_array_text:
            pm.warning("Not found Pose Data")
        else:
            for text_data in list_array_text:
                dict_data = self.text_to_dict(text_data)

                controller = list(dict_data.keys())[0]

                translate, rotate, scale = list(dict_data.values())[0]

                # is controller exist
                if not pm.objExists(controller):
                    continue

                # set transform
                for attr_name, values in [
                    ("t", translate),
                    ("r", rotate),
                    ("s", scale),
                ]:
                    for i, axis in enumerate("xyz"):
                        try:
                            pm.setAttr(f"{controller}.{attr_name}{axis}", values[i])
                        except:
                            pass

        # set blendshape node
        # set all off
        all_target_name = BlendShape.query_all_blend_shape_input(
            blendshape_name=self.blend_shape_node
        )

        for shape in all_target_name:
            pm.setAttr("{}.{}".format(self.blend_shape_node, shape), 0)

        # set current on
        pm.setAttr("{}.{}".format(self.blend_shape_node, selection[0]), 1)

        # selection object
        # if self.ui.radioButton_edit_mode.isChecked():
        #     pm.select(full_shape_mesh)

    def find_exists_grp_data(self):
        """This function return exist grp data name in the scene"""

        transforms = pm.ls(typ="transform")

        for transform in transforms:
            if transform.endswith(self.grp_data_keyword):
                return transform

        if not self.grp_data:
            return None

    def refresh(self):
        # find grp exist grp data / only refresh when grp data exist
        self.grp_data = self.find_exists_grp_data()

        if not self.grp_data:
            return

        # update variable
        self.base_mesh = pm.getAttr(self.grp_data + ".baseMesh")

        self.leftCtrl = pm.getAttr(self.grp_data + ".leftCtrl")
        self.rightCtrl = pm.getAttr(self.grp_data + ".rightCtrl")

        self.shape_Up = pm.getAttr(self.grp_data + ".up")
        self.shape_Down = pm.getAttr(self.grp_data + ".down")
        self.shape_In = pm.getAttr(self.grp_data + ".in")
        self.shape_Out = pm.getAttr(self.grp_data + ".out")

        self.shape_OutUp = pm.getAttr(self.grp_data + ".outUp")
        self.shape_OutDown = pm.getAttr(self.grp_data + ".outDown")
        self.shape_InUp = pm.getAttr(self.grp_data + ".inUp")
        self.shape_InDown = pm.getAttr(self.grp_data + ".inDown")

        # find blend shape
        self.blend_shape_node = BlendShape.get_blendshape_node(
            self.base_mesh
        ).shortName()
        # print(self.blend_shape_node)
        # update widget
        self.ui.lineEdit_base_mesh.setText(self.base_mesh)
        self.ui.lineEdit_weight_split.setText(self.weight_mesh)
        self.ui.lineEdit_blend_shape_node.setText(self.blend_shape_node)

        # update widget
        self.ui.pushButton_select_left_ctrl.setText(self.leftCtrl)
        self.ui.pushButton_select_right_ctrl.setText(self.rightCtrl)

        self.ui.pushButton_select_shape_up.setText(self.shape_Up)
        self.ui.pushButton_select_shape_down.setText(self.shape_Down)
        self.ui.pushButton_select_shape_in.setText(self.shape_In)
        self.ui.pushButton_select_shape_out.setText(self.shape_Out)

        self.ui.pushButton_select_shape_outUp.setText(self.shape_OutUp)
        self.ui.pushButton_select_shape_outDown.setText(self.shape_OutDown)
        self.ui.pushButton_select_shape_inUp.setText(self.shape_InDown)
        self.ui.pushButton_select_shape_inDown.setText(self.shape_InDown)

    @Misc.undoable
    def update_blend_shape_driver(self):

        if not pm.objExists(self.weight_mesh):
            pm.error("Require weight split mesh before update shape driver")
            return

        list_shape_name = [
            "Up",
            "Down",
            "In",
            "Out",
            "OutUp",
            "OutDown",
            "InUp",
            "InDown",
        ]
        shape = [
            self.shape_Up,
            self.shape_Down,
            self.shape_In,
            self.shape_Out,
            self.shape_OutUp,
            self.shape_OutDown,
            self.shape_InUp,
            self.shape_InDown,
        ]

        # recheck the name

        for shape_name, shape in zip(list_shape_name, shape):
            print("shape : ", shape)
            if not shape:
                # use exist if shape is exist
                if pm.objExists(shape_name):
                    custom_shape = shape_name

                # create new one if shape not exist
                else:
                    custom_shape = pm.duplicate(self.base_mesh, n=shape_name)

                # update shape to attribute data
                pm.select(custom_shape)
                self.load_shape(shape=shape_name)

                # parent shape to grp data
                try:
                    pm.parent(custom_shape, self.grp_data)
                except:
                    pass

        # create split shape
        pm.select(self.weight_mesh)
        QuickData.export_skin_quick()

        # create splited shape
        list_split_mesh = []

        for name in list_shape_name:
            # check is split name exist
            each_output = BlendShape.split_blendshape(
                L_joint="jnt_split_L",
                R_joint="jnt_split_R",
                split_weight_mesh=self.weight_mesh,
                base_mesh=self.base_mesh,
                target_mesh=name,
                L_keyword="LeftTmp",
                R_keyword="RightTemp",
            )

            L_side_geo, R_side_geo = each_output
            L_side_geo_main, R_side_geo_main = "{}_Left".format(
                name
            ), "{}_Right".format(name)

            if pm.objExists(L_side_geo_main):
                Utility.morph_shape(L_side_geo, [L_side_geo_main])
                pm.delete(L_side_geo)
            else:
                pm.rename(L_side_geo, L_side_geo_main)

            if pm.objExists(R_side_geo_main):
                Utility.morph_shape(R_side_geo, [R_side_geo_main])
                pm.delete(R_side_geo)
            else:
                pm.rename(R_side_geo, R_side_geo_main)

            # add to list
            list_split_mesh.append(L_side_geo_main)
            list_split_mesh.append(R_side_geo_main)

            # set visibility off
            pm.setAttr("{}.v".format(L_side_geo_main), False)
            pm.setAttr("{}.v".format(R_side_geo_main), False)

        pm.select(list_split_mesh)

        # add blend shape
        BlendShape.add_or_create_blend_shape_node_v2(
            list_target_mesh=list_split_mesh,
            input_mesh=self.base_mesh,
            node_name=self.blend_shape_node,
        )

        # parent
        pm.parent(list_split_mesh, self.grp_data)

        # Connect diagonal
        left_diagonal_transform_name = self.base_mesh + "_LeftDiagonalNode"

        if not pm.objExists(left_diagonal_transform_name):
            left_diagonal_transform = Connection.set_diagonal_driver(
                transform_name=self.leftCtrl, name_tag=left_diagonal_transform_name
            )

        right_diagonal_transform_name = self.base_mesh + "_RightDiagonalNode"

        if not pm.objExists(right_diagonal_transform_name):
            right_diagonal_transform = Connection.set_diagonal_driver(
                transform_name=self.rightCtrl, name_tag=right_diagonal_transform_name
            )

        # force connect
        pm.connectAttr(
            "{}.Up".format(left_diagonal_transform_name),
            "{}.Up_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.Down".format(left_diagonal_transform_name),
            "{}.Down_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.In".format(left_diagonal_transform_name),
            "{}.In_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.Out".format(left_diagonal_transform_name),
            "{}.Out_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.UpOut".format(left_diagonal_transform_name),
            "{}.OutUp_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.UpIn".format(left_diagonal_transform_name),
            "{}.InUp_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.DownOut".format(left_diagonal_transform_name),
            "{}.OutDown_Left".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.DownIn".format(left_diagonal_transform_name),
            "{}.InDown_Left".format(self.blend_shape_node),
            f=True,
        )

        pm.connectAttr(
            "{}.Up".format(right_diagonal_transform_name),
            "{}.Up_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.Down".format(right_diagonal_transform_name),
            "{}.Down_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.In".format(right_diagonal_transform_name),
            "{}.In_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.Out".format(right_diagonal_transform_name),
            "{}.Out_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.UpOut".format(right_diagonal_transform_name),
            "{}.OutUp_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.UpIn".format(right_diagonal_transform_name),
            "{}.InUp_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.DownOut".format(right_diagonal_transform_name),
            "{}.OutDown_Right".format(self.blend_shape_node),
            f=True,
        )
        pm.connectAttr(
            "{}.DownIn".format(right_diagonal_transform_name),
            "{}.InDown_Right".format(self.blend_shape_node),
            f=True,
        )

        return

    def add_current_mesh(self):
        control_selection = pm.ls(sl=1)

        if not control_selection:
            pm.inViewMessage(
                amg="Please select controller to set pose", pos="midCenter", fade=True
            )
            return
        # sort mesh that influence to blend shape node
        list_target_mesh = []

        # create new blend shape
        result = pm.promptDialog(
            title="Create New Shape",
            message="Shape Name:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel",
            tx="",
        )

        if result == "OK":
            input_name = pm.promptDialog(query=True, text=True)

            if input_name == "":
                return

        else:
            return

        # ensure corrective grp is created
        self.create_corrective_grp()

        current_mesh = self.get_shape_orig(name=input_name)
        current_mesh.visibility.set(False)
        BlendShape.add_or_create_blend_shape_node([current_mesh], self.blend_shape_node)

        full_shape = self.create_full_shape(
            shape_name=input_name, source_mesh=self.base_mesh
        )
        pose_mesh = self.create_pose_shape(full_shape_mesh=full_shape)

        # create full shape
        for sel in list_target_mesh:
            full_shape_mesh = "{}_FullShape".format(sel)
            pose_shape_mesh = "{}_PoseShape".format(sel)

            # skip if already have full shape
            if pm.objExists(full_shape_mesh):
                result = pm.confirmDialog(
                    m="{} Has already created!".format(sel),
                    button=["Overwrite", "Cancel"],
                    defaultButton="Overwrite",
                    cancelButton="Cancel",
                    dismissString="Cancel",
                )

                if result == "Overwrite":
                    pm.delete(full_shape_mesh)

                    if pm.objExists(pose_shape_mesh):
                        pm.delete(full_shape_mesh)

                elif result == "Cancel":
                    continue

            # create full shape
            self.create_full_shape(shape_name=sel)

            # create pose shape
            self.create_pose_shape(full_shape_mesh=full_shape_mesh)

        # reload list widget
        self.load_list_target_from_exist_group()

        # select new one
        list_widget = self.ui.listWidget_target_corrective
        (
            list_widget.setCurrentRow(list_widget.count() - 1)
            if list_widget.count()
            else None
        )

        # update pose data
        pm.select(control_selection)
        self.update_pose_data()

    def add_exist_mesh(self):
        selection = pm.ls(sl=1)

        # return if no selection
        if not selection:
            return

        # sort mesh that influence to blendshape node
        list_target_mesh = []

        for sel in selection:
            if pm.listRelatives(sel, c=1, typ="mesh") is None:
                continue
            else:
                shape_node = pm.listRelatives(sel, c=1, typ="mesh")[0]
                list_connection = pm.listConnections(
                    "{}.worldMesh[0]".format(shape_node), d=True
                )

                if self.blend_shape_node in list_connection:
                    list_target_mesh.append(sel)

        if not list_target_mesh:
            return

        # ensure corrective grp is created
        self.create_corrective_grp()

        # create full shape
        for sel in list_target_mesh:
            full_shape_mesh = "{}_FullShape".format(sel)
            pose_shape_mesh = "{}_PoseShape".format(sel)

            # skip if already have full shape
            if pm.objExists(full_shape_mesh):
                result = pm.confirmDialog(
                    m="{} Has already created!".format(sel),
                    button=["Overwrite", "Cancel"],
                    defaultButton="Overwrite",
                    cancelButton="Cancel",
                    dismissString="Cancel",
                )

                if result == "Overwrite":
                    pm.delete(full_shape_mesh)

                    if pm.objExists(pose_shape_mesh):
                        pm.delete(full_shape_mesh)

                elif result == "Cancel":
                    continue

            # create full shape
            self.create_full_shape(shape_name=sel)

            # create pose shape
            self.create_pose_shape(full_shape_mesh=full_shape_mesh)

        # reload list widget
        self.load_list_target_from_exist_group()

        # select new one
        list_widget = self.ui.listWidget_target_corrective
        (
            list_widget.setCurrentRow(list_widget.count() - 1)
            if list_widget.count()
            else None
        )

    def load_node_corrective(self):
        return

    def update_mesh_name(self):
        self.mesh_name = self.ui.lineEdit_mesh.text()
