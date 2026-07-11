from EasySkeleton import config,rig_class,utils,utils_tool
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtWidgets, QtCore, QtUiTools, QtGui
import maya.cmds as cmds
import maya.mel as mel
import traceback
import os
import importlib, webbrowser, inspect, configparser

from EasySkeleton.rigs import BodyGlobal, FacialGlobal, FacialLocal,Other

version = "1.4.4"

class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    dir_config_interface = config.root_file + "/interface_config.ini"

    WINDOW_TITLE = "Easy Skeleton {}".format(version)
    WINDOW_OBJECT = "easySkeleton"

    dict_class_module = {}

    # ram
    recent_tab_setting_name = ""
    recent_tab_scroll_value = 0

    listWidgets_template = []
    list_all_modules_instance = [BodyGlobal, FacialGlobal, FacialLocal,Other]

    # store the dictionary data : dict_attribute_ram[object.attribute] = {} *it's up on individual type
    dict_attribute_ram = {"path": [], "string": [], "stringArray": [], "long": [], "script": [], "enum": [], "float": [], "bool": []}

    # dict_convert_type = {"string": str, "bool": bool, "double": float, "stringArrays": list, "long": int}
    dict_color = {"red": (150, 50, 50), "green": (50, 150, 50), "blue": (50, 50, 150), "grey": (100, 100, 100)}
    dict_lock = {}
    dict_action_button_module = {}
    dict_action_button_template = {}

    def __init__(self):
        def connect_rig_module_widget():
            # connect functions
            self.ui.pushButton_module_toggle.clicked.connect(self.module_toggle)
            self.ui.pushButton_build_selected.clicked.connect(lambda x : self.execute_build(build_mode=True))
            self.ui.pushButton_script_editor.clicked.connect(lambda x: mel.eval("ScriptEditor;"))
            self.ui.pushButton_parent_fill.clicked.connect(self.update_parent_value)

            self.ui.lineEdit_search.textChanged.connect(self.update_module_setting)
            self.ui.listWidget_rigModule.itemClicked.connect(self.update_module_setting)

            self.ui.lineEdit_module_name.textChanged.connect(self.module_rename)

            self.menu_add_module = QtWidgets.QMenu(self)
            self.menu_add_template = QtWidgets.QMenu(self)
            self.menu_setting = QtWidgets.QMenu(self)
            self.menu_toolkit = QtWidgets.QMenu(self)

            # Assign menu to tool button
            self.ui.pushButton_add_module.setMenu(self.menu_add_module)
            self.ui.pushButton_add_template.setMenu(self.menu_add_template)
            self.ui.pushButton_setting_more.setMenu(self.menu_setting)
            self.ui.pushButton_toolkit.setMenu(self.menu_toolkit)

            action = QtWidgets.QAction("Duplicate", self)
            action.triggered.connect(self.module_duplicate)
            self.menu_setting.addAction(action)

            action = QtWidgets.QAction("Delete", self)
            action.triggered.connect(self.module_remove)
            self.menu_setting.addAction(action)

            action = QtWidgets.QAction("Select Node", self)
            action.triggered.connect(lambda x: cmds.select(self.ui.listWidget_rigModule.selectedItems()[0].text()))
            self.menu_setting.addAction(action)

            # Menu Rig Button
            self.menu_rig = QtWidgets.QMenu(self)
            self.ui.pushButton_rig.setMenu(self.menu_rig)

            separator_label = QtWidgets.QAction("----- Rig -----", self)
            separator_label.setEnabled(False)
            self.menu_rig.addAction(separator_label)

            action = QtWidgets.QAction("Create a new rig", self)
            action.triggered.connect(utils_tool.create_rig)
            self.menu_rig.addAction(action)

            action = QtWidgets.QAction("Remove a rig", self)
            action.triggered.connect(utils_tool.delete_rig)
            self.menu_rig.addAction(action)

            separator_label = QtWidgets.QAction("----- Mesh -----", self)
            separator_label.setEnabled(False)
            self.menu_rig.addAction(separator_label)

            action = QtWidgets.QAction("Add Mesh", self)
            action.triggered.connect(utils_tool.add_mesh)
            self.menu_rig.addAction(action)

            separator_label = QtWidgets.QAction("----- Joints -----", self)
            separator_label.setEnabled(False)
            self.menu_rig.addAction(separator_label)

            action = QtWidgets.QAction("Add Global Joint", self)
            action.triggered.connect(utils_tool.add_global_joint)
            self.menu_rig.addAction(action)

            action = QtWidgets.QAction("Add Local Joint", self)
            action.triggered.connect(utils_tool.add_local_joint)
            self.menu_rig.addAction(action)

            action = QtWidgets.QAction("Toggle Visibility", self)
            action.triggered.connect(lambda x: utils_tool.rig_manage(toggle_joint_vis=1))
            self.menu_rig.addAction(action)

            action = QtWidgets.QAction("Toggle Axis", self)
            action.triggered.connect(lambda x: utils_tool.rig_manage(toggle_joint_axis=1))
            self.menu_rig.addAction(action)

            separator_label = QtWidgets.QAction("----- Other -----", self)
            separator_label.setEnabled(False)
            self.menu_rig.addAction(separator_label)

            action = QtWidgets.QAction("Open Gumroad...", self)
            action.triggered.connect(lambda x: webbrowser.open("tonmairig.gumroad.com/l/ksuijg"))
            self.menu_rig.addAction(action)

            # Menu Toolkit
            action = QtWidgets.QAction("Select Module by Selected Controller", self)
            action.triggered.connect(self.auto_select_module)
            self.menu_toolkit.addAction(action)

            separator_label = QtWidgets.QAction("----- Tools -----", self)
            separator_label.setEnabled(False)
            self.menu_toolkit.addAction(separator_label)

            action = QtWidgets.QAction("Controller Editor", self)
            action.triggered.connect(self.launch_controller_editor)
            self.menu_toolkit.addAction(action)

            action = QtWidgets.QAction("Skin Weight Manager", self)
            action.triggered.connect(self.launch_weight_importer)
            self.menu_toolkit.addAction(action)

            action = QtWidgets.QAction("Joint Placement Helper", self)
            action.triggered.connect(self.launch_joint_placement_helper)
            self.menu_toolkit.addAction(action)

            separator_label = QtWidgets.QAction("----- Scripts -----", self)
            separator_label.setEnabled(False)
            self.menu_toolkit.addAction(separator_label)

            action = QtWidgets.QAction("Mirror Selected Joints", self)
            action.triggered.connect(self.mirror_selected_joints)
            self.menu_toolkit.addAction(action)

            separator_label = QtWidgets.QAction("----- Controller -----", self)
            separator_label.setEnabled(False)
            self.menu_toolkit.addAction(action)

            action = QtWidgets.QAction("Resize Controller to Selected Module", self)
            action.triggered.connect(self.rescale_module_controller)
            self.menu_toolkit.addAction(action)

            action = QtWidgets.QAction("Clone Selected to Opposite", self)
            action.triggered.connect(utils.clone_shape)
            self.menu_toolkit.addAction(action)

            action = QtWidgets.QAction("Clone Selected by reference last one", self)
            action.triggered.connect(utils.clone_to_opposite)
            self.menu_toolkit.addAction(action)

            # Menu Build
            self.menu_build = QtWidgets.QMenu(self)
            self.ui.pushButton_build_selected.setMenu(self.menu_build)

            self.action_unbuild = QtWidgets.QAction("Unbuild", self)
            self.action_unbuild.triggered.connect(lambda x : self.execute_build(build_mode=False))
            self.menu_build.addAction(self.action_unbuild)

            action = QtWidgets.QAction("Reload", self)
            action.triggered.connect(self.update_module_setting)
            self.menu_build.addAction(action)


        # Set-up Interface
        super(MainWindow, self).__init__(parent=None)
        utils_tool.deleteControl(self.WINDOW_OBJECT + "WorkspaceControl")

        self.ui = utils_tool.load_ui("{}\\interface\\Modular.ui".format(config.root_file))

        self.setCentralWidget(self.ui)
        self.setMinimumSize(self.ui.size())

        self.setObjectName(self.WINDOW_OBJECT)
        self.setWindowTitle(self.WINDOW_TITLE)

        # connect widget
        connect_rig_module_widget()
        # first state check
        self.load_starter()

        # Create the script job
        cmds.scriptJob(event=["NewSceneOpened", self.update_module_setting], protected=True)
        cmds.scriptJob(event=["Redo", self.update_module_setting], protected=True)
        cmds.scriptJob(event=["Undo", self.update_module_setting], protected=True)

    def mirror_selected_joints(self):
        selection = cmds.ls(sl=1,typ="joint")

        if not selection:
            return

        for joint in selection:
            opposite_joint = joint.replace(config.L,config.R)

            if config.L in joint and cmds.objExists(opposite_joint):
                # cmds.select(joint,r=1)

                mirror_name = cmds.mirrorJoint(joint,sr=[config.L,config.R],myz=1,mb=1)
                cmds.matchTransform(opposite_joint,mirror_name)
                cmds.makeIdentity(opposite_joint,a=1,r=1)
                cmds.delete(mirror_name)
            else:
                mirror_name = cmds.mirrorJoint(joint,sr=[config.L,config.R],myz=1,mb=1)

            cmds.select(opposite_joint)


    def launch_weight_importer(self):
        import EasySkeleton.toolkits.WeightImporter.interface
        importlib.reload(EasySkeleton.toolkits.WeightImporter.interface)

        window = EasySkeleton.toolkits.WeightImporter.interface.MainWindow()
        window.show()

    def launch_joint_placement_helper(self):
        import EasySkeleton.toolkits.JointPlacementHelper.interface
        importlib.reload(EasySkeleton.toolkits.JointPlacementHelper.interface)

        window = EasySkeleton.toolkits.JointPlacementHelper.interface.MainWindow()
        window.show()

    def launch_controller_editor(self):
        if not utils_tool.is_rig_structures():
            cmds.confirmDialog(m="Rig Base Must Be Create.")
        else:
            import EasySkeleton.toolkits.ControllerEditor.interface
            importlib.reload(EasySkeleton.toolkits.ControllerEditor.interface)
            window = EasySkeleton.toolkits.ControllerEditor.interface.MainWindow()
            window.show()

    def auto_select_module(self):
        selection = cmds.ls(sl=1)
        list_node_reference = cmds.ls(typ="network")
        list_node_return = []

        for sel in selection:
            # find node reference
            for node_name in list_node_reference:
                rig_group_name = "{}_{}Rig".format(config.grp, node_name)

                if utils.is_descendant_of(sel, rig_group_name) and rig_group_name not in list_node_return:
                    list_node_return.append(node_name)

        # re select
        for i in range( self.ui.listWidget_rigModule.count() ):
            text = self.ui.listWidget_rigModule.item(i).text()

            if text in list_node_return:
                self.ui.listWidget_rigModule.item(i).setSelected(True)
            else:
                self.ui.listWidget_rigModule.item(i).setSelected(False)

        self.update_module_setting()

    def execute_build(self,build_mode=True):
        def build_unbuild_item(item_name, build=True):
            # build
            class_path = cmds.getAttr(item_name + ".class")
            class_path = utils_tool.convert_class_path_to_class_instance(class_path)
            instance = class_path()

            # update instance attribute by maya attribute
            for attr in cmds.listAttr(item_name, ud=1):
                try:
                    value = cmds.getAttr(item_name + "." + attr)
                    setattr(instance, attr, value)
                except Exception as e:
                    cmds.progressWindow(endProgress=1)
                    print(e)

            # build a rig modules
            self.ui.pushButton_script_editor.setText("")

            cmds.undoInfo(ock=1)

            try:
                if build:
                    instance.build()
                    cmds.setAttr(item_name + ".isBuild", True)
                else:
                    instance.unbuild()
                    cmds.setAttr(item_name + ".isBuild", False)

                del instance

                cmds.undoInfo(cck=1)

                self.ui.pushButton_script_editor.setText("✅ Complete")

            except Exception as e:
                # UNDO
                cmds.undoInfo(cck=1)
                cmds.undo()

                traceback.print_exc()
                self.ui.pushButton_script_editor.setText("❌ Error")

                cmds.progressWindow(endProgress=1)
                cmds.confirmDialog(m="Build Error : {}".format(e))


        def recall_selection():
            # reselect user selection
            cmds.select(cl=1)
            for obj in list_selected_objects:
                if cmds.objExists(obj):
                    cmds.select(obj, add=1)

        def get_list_item():
            list_build = []
            list_unbuild = []

            # error handle : not create rig structure yet
            if not utils_tool.is_rig_structures():
                cmds.confirmDialog(
                    m="ERROR | A rig structure not exist in scene!. Go to Menu bar [Rig > Create a new Rig]")
                raise Exception("ERROR | A rig structure not exist in scene!. Go to Menu bar [Rig > Create a new Rig]")

            # filter for build mode
            for item_name in list_selected_module:
                # ignore locked
                if cmds.getAttr("{}.enable".format(item_name)) is False:
                    continue

                # add un-build list
                if cmds.getAttr("{}.isBuild".format(item_name)):
                    list_unbuild.append(item_name)

                # add build list
                if build_mode:
                    list_build.append(item_name)

            return list_build,list_unbuild

        list_selected_objects = cmds.ls(sl=1, l=1) # store user selection
        list_selected_module = self.get_current_selected_module_name()

        cmds.progressWindow(title='Building Module',
                            progress=0,
                            status='Preparing : 0%',
                            isInterruptable=True)

        list_build,list_unbuild = get_list_item()

        cmds.undoInfo(ock=1)

        cmds.progressWindow(edit=True, progress=20, status='Backing up controller : 20%')
        utils.backup_control(typ="update")

        cmds.progressWindow(edit=True, progress=50, status='Main Progress : 50%')

        if build_mode:
            for module in list_unbuild:
                build_unbuild_item(module,build=False)

            for module in list_build:
                build_unbuild_item(module,build=True)

        elif not build_mode:
            for module in list_unbuild:
                build_unbuild_item(module,build=False)

        cmds.progressWindow(edit=True, progress=70, status='Recalling Controller : 70%')
        utils.backup_control(typ="recall")
        cmds.undoInfo(cck=1)

        cmds.progressWindow(edit=True, progress=90, status='Updating setting attributes : 90%'.format(list_unbuild))
        recall_selection()
        self.update_module_setting()

        cmds.progressWindow(endProgress=1)

    def set_auto_flip_keyword(self):
        pass


    def load_starter(self):
        self.load_menu_template()
        self.load_menu_module()
        self.load_popup_rebuild_setting()
        self.update_module_setting()
        self.ui.listWidget_rigModule.setCurrentRow(0)
        self.update_module_setting()

    def load_popup_rebuild_setting(self):
        config = configparser.ConfigParser()
        config.read(self.dir_config_interface)

        value = config["interface"]["PopupRebuildConfirm"]

        if value == "True":
            self.ui.actionIgnore_Confirm_Rebuild.setChecked(True)
        elif value == "False":
            self.ui.actionIgnore_Confirm_Rebuild.setChecked(False)

    def load_menu_module(self):
        self.menu_add_module.clear()

        for module_instance in self.list_all_modules_instance:
            module_path = module_instance.__name__
            module_name = module_path.split(".")[-1]
            module_name_nice = utils_tool.generate_nice_name(module_name)

            list_class_data = [[member_name, member] for member_name, member in inspect.getmembers(module_instance) if inspect.isclass(member)]

            # add type menu bar
            menu = self.menu_add_module.addMenu(module_name_nice)

            for class_data in list_class_data:
                class_name, class_instance = class_data

                # add new action to menu
                action = QtWidgets.QAction(utils_tool.generate_nice_name(class_name),self)
                action.triggered.connect(self.module_add)
                self.dict_action_button_module[action] = class_instance
                menu.addAction(action)


    def load_menu_template(self):
        self.menu_add_template.clear()

        template_folder_path = config.root_file+"/templates"

        for template_file in os.listdir(template_folder_path):
            if ".ma" not in template_file:
                continue

            # add new action to menu
            action = QtWidgets.QAction(utils_tool.generate_nice_name(template_file.split(".")[0]),self)
            action.triggered.connect(self.add_template)
            self.dict_action_button_template[action] = "{}/{}".format(template_folder_path,template_file)
            self.menu_add_template.addAction(action)

    def add_template(self):
        if not utils_tool.is_rig_structures():
            cmds.confirmDialog(m="Create Rig Structure First Before add any rig.")
            raise Exception("Not Create Rig Yet")

        template_file_path = self.dict_action_button_template[self.sender()]
        template_nice_name = template_file_path.split("/")[-1].replace(".ma","")

        grp_local_full_path = cmds.ls(config.grp_local,l=1)[0]
        grp_global_full_path = cmds.ls(config.grp_skin,l=1)[0]


        # temp_group = "TempTemplateGrp"

        cmds.file(template_file_path,i=1,rpr="Temp")


        # parent global joint
        list_global_joint = cmds.listRelatives("{}_{}|{}".format("Temp",config.default_rig_name,config.grp_skin),c=1,f=1)

        if list_global_joint:
            cmds.parent(list_global_joint,grp_global_full_path)

        # parent local joint
        list_local_joint = cmds.listRelatives("{}_{}|{}".format("Temp",config.default_rig_name,config.grp_local),c=1,f=1)

        if list_local_joint:
            cmds.parent(list_local_joint,grp_local_full_path)

        cmds.delete("{}_{}".format("Temp",config.default_rig_name))

        self.update_module_setting()

    def get_node_in_scene(self):
        list_network = cmds.ls(typ="network")

        # debug ---------------------
        utils_tool.debug("▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁")
        utils_tool.debug("Network Node in Scene")

        for node in list_network:
            utils_tool.debug("- {}".format(node))

        return list_network

    def update_module_setting(self):
        def update_setting_group_box():
            def load_missing_widget():
                def update_class_path():
                    new_path = line_input.text()

                    for name in cmds.ls(typ="network"):
                        try:
                            path = cmds.getAttr(name + ".class")
                        except:
                            continue

                        if path == old_class_path:
                            cmds.setAttr(name + ".class", new_path, typ="string")

                old_class_path = cmds.getAttr("{}.class".format(self.get_current_selected_module_name_single()))

                line_edit = QtWidgets.QPlainTextEdit(
                    "Not Found Module Please Click Node and change Class Attribute in extra attributes to a new one")

                label1 = QtWidgets.QLabel("Old Path :")
                label2 = QtWidgets.QLabel("New Path :")

                line_input_old = QtWidgets.QLineEdit(old_class_path)

                line_input = QtWidgets.QLineEdit(old_class_path)

                line_input_old.setReadOnly(True)

                button_update = QtWidgets.QPushButton("Update")

                button_update.clicked.connect(update_class_path)

                # add widget
                self.ui.layout_setting.addWidget(line_edit)
                self.ui.layout_setting.addWidget(label1)

                self.ui.layout_setting.addWidget(line_input_old)
                self.ui.layout_setting.addWidget(label2)

                self.ui.layout_setting.addWidget(line_input)
                self.ui.layout_setting.addWidget(button_update)

            def load_setting_widget():
                def update_tap_recent_name():
                    # update toolbox tab name
                    for i in range(tab_widget.count()):
                        if tab_widget.tabText(i) == self.recent_tab_setting_name:
                            tab_widget.setCurrentIndex(i)

                    def update_current_setting_name():
                        self.recent_tab_setting_name = tab_widget.tabText(tab_widget.currentIndex())

                    tab_widget.currentChanged.connect(lambda x: update_current_setting_name())

                def update_main_setting():
                    # disable all setting at first
                    self.ui.pushButton_parent_fill.setEnabled(False)
                    self.ui.checkBox_debug_mode.setEnabled(False)
                    self.ui.checkBox_mirror_scale_control.setEnabled(False)
                    self.ui.lineEdit_parent.setText("")

                    for list_variables in dict_tab_name.values():
                        if "parent" in list_variables:
                            attr_value = cmds.getAttr("{}.parent".format(item_name))
                            self.ui.lineEdit_parent.setText(attr_value)
                            self.ui.pushButton_parent_fill.setEnabled(True)

                        if "debug_mode" in list_variables:
                            try:
                                self.ui.checkBox_debug_mode.stateChanged.disconnect()
                            except:
                                pass

                            self.ui.checkBox_debug_mode.setEnabled(True)

                            check_value = cmds.getAttr("{}.debug_mode".format(item_name))
                            self.ui.checkBox_debug_mode.setChecked(check_value)
                            self.ui.checkBox_debug_mode.stateChanged.connect(self.update_debug_mode_value)

                        if "mirror_control_scale" in list_variables:
                            try:
                                self.ui.checkBox_mirror_scale_control.stateChanged.disconnect()
                            except:
                                pass

                            self.ui.checkBox_mirror_scale_control.setEnabled(True)

                            check_value = cmds.getAttr("{}.mirror_control_scale".format(item_name))
                            self.ui.checkBox_mirror_scale_control.setChecked(check_value)
                            self.ui.checkBox_mirror_scale_control.stateChanged.connect(self.update_mirror_control_scale)

                def update_attribute_setting():
                    def add_info_tip_widget(custom_attr_name=None):
                        if custom_attr_name:
                            attribute_name = custom_attr_name
                        else:
                            attribute_name = attr_name

                        info_tip = dict_docs[attribute_name][1] if dict_docs and attribute_name in dict_docs else None

                        if info_tip:
                            widget_info = QtWidgets.QLabel("❔")
                            widget_info.setToolTip(info_tip)
                            sub_layout.addWidget(widget_info)
                        else:
                            widget_info = QtWidgets.QLabel("⚠️")
                            sub_layout.addWidget(widget_info)
                            widget_info.setEnabled(False)

                        return widget_info

                    def add_label_widget():
                        # add label widget
                        label = QtWidgets.QLabel(utils_tool.generate_nice_name(attr_name))
                        sub_layout.addWidget(label)
                        return label

                    def add_blank_widget():
                        line = QtWidgets.QFrame()
                        line.setFrameShape(QtWidgets.QFrame.HLine)
                        line.setFrameShadow(QtWidgets.QFrame.Sunken)
                        line.setFixedHeight(2)
                        sub_layout.addWidget(line)

                    def add_head_label_widget():
                        # add label widget
                        label_text = attr_name.replace("label:", "")
                        label_text.strip()

                        label = QtWidgets.QLabel(label_text)
                        label.setFixedHeight(20)
                        label.setStyleSheet("background-color: LightGray; color: black;font-weight: bold;")
                        sub_layout.addWidget(label)

                    def add_pattern_stringArray():
                        # widget info
                        widget_info = add_info_tip_widget()
                        sub_layout.addWidget(widget_info)

                        label = QtWidgets.QLabel(utils_tool.generate_nice_name(attr_name))
                        label.setMinimumWidth(150)
                        label.setMaximumWidth(150)
                        sub_layout.addWidget(label)

                        line_edit_widget = QtWidgets.QLineEdit()
                        line_edit_widget.setPlaceholderText("Multiple")

                        line_edit_widget.setText("")

                        if attr_value:
                            line_edit_widget.setText(str(attr_value))

                        line_edit_widget.setClearButtonEnabled(True)
                        line_edit_widget.textChanged.connect(self.update_value_stringArray)
                        sub_layout.addWidget(line_edit_widget)

                        fill_widget = QtWidgets.QPushButton("◀")
                        fill_widget.clicked.connect(self.auto_fill_stringArray)
                        fill_widget.setToolTip("""Replace Input by Selection""")
                        fill_widget.setMinimumWidth(25)
                        fill_widget.setMaximumWidth(25)
                        sub_layout.addWidget(fill_widget)

                        self.dict_attribute_ram[attr_type].append({"line_edit_widget": line_edit_widget,
                                                                   "fill_widget": fill_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_long():
                        widget_info = add_info_tip_widget()
                        label = add_label_widget()
                        label.setMinimumWidth(150)
                        label.setMaximumWidth(150)

                        long_widget = QtWidgets.QSpinBox()
                        long_widget.setRange(-1000, 1000)
                        long_widget.setValue(attr_value)
                        long_widget.valueChanged.connect(self.update_value_long)
                        sub_layout.addWidget(long_widget)

                        # add spacer to keep attribute on top
                        spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding,
                                                       QtWidgets.QSizePolicy.Minimum)
                        sub_layout.addSpacerItem(spacer)

                        # line_edit_widget.setMaximumHeight(30)
                        # label.setMaximumHeight(30)
                        # widget_info.setMaximumHeight(30)

                        self.dict_attribute_ram[attr_type].append({"long_widget": long_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_float():
                        widget_info = add_info_tip_widget()
                        label = add_label_widget()
                        label.setMinimumWidth(150)
                        label.setMaximumWidth(150)

                        float_widget = QtWidgets.QDoubleSpinBox()
                        float_widget.setRange(-1000.00, 1000.00)
                        float_widget.setValue(attr_value)
                        float_widget.valueChanged.connect(self.update_value_float)
                        sub_layout.addWidget(float_widget)

                        # add spacer to keep attribute on top
                        spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding,
                                                       QtWidgets.QSizePolicy.Minimum)
                        sub_layout.addSpacerItem(spacer)

                        # line_edit_widget.setMaximumHeight(30)
                        # label.setMaximumHeight(30)
                        # widget_info.setMaximumHeight(30)

                        self.dict_attribute_ram[attr_type].append({"float_widget": float_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_bool():
                        # widget info
                        widget_info = add_info_tip_widget()
                        sub_layout.addWidget(widget_info)

                        label = QtWidgets.QLabel(utils_tool.generate_nice_name(attr_name))
                        label.setMinimumWidth(150)
                        label.setMaximumWidth(150)
                        sub_layout.addWidget(label)

                        checkbox_widget = QtWidgets.QCheckBox()
                        checkbox_widget.setChecked(attr_value)
                        checkbox_widget.stateChanged.connect(self.update_value_bool)

                        sub_layout.addWidget(checkbox_widget)

                        # add spacer to keep attribute on top
                        spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding,
                                                       QtWidgets.QSizePolicy.Minimum)
                        sub_layout.addSpacerItem(spacer)

                        self.dict_attribute_ram[attr_type].append({"checkbox_widget": checkbox_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_string():
                        widget_info = add_info_tip_widget()

                        label = add_label_widget()
                        label.setMinimumWidth(150)
                        label.setMaximumWidth(150)

                        line_edit_widget = QtWidgets.QLineEdit()
                        line_edit_widget.setPlaceholderText("Single")
                        line_edit_widget.setText(str(attr_value))
                        line_edit_widget.setClearButtonEnabled(True)
                        line_edit_widget.textChanged.connect(self.update_value_string)
                        sub_layout.addWidget(line_edit_widget)

                        fill_widget = QtWidgets.QPushButton("<")
                        fill_widget.clicked.connect(self.auto_fill_string)
                        fill_widget.setToolTip("""Replace Input by Selection""")
                        fill_widget.setMinimumWidth(25)
                        fill_widget.setMaximumWidth(25)
                        sub_layout.addWidget(fill_widget)

                        # line_edit_widget.setMaximumHeight(30)
                        # label.setMaximumHeight(30)
                        # widget_info.setMaximumHeight(30)

                        self.dict_attribute_ram[attr_type].append({"line_edit_widget": line_edit_widget,
                                                                   "fill_widget": fill_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_path():
                        widget_info = add_info_tip_widget()
                        # widget_info.setMaximumHeight(30)

                        # add label widget
                        label_widget = QtWidgets.QLabel(utils_tool.generate_nice_name(attr_name))
                        #                 label_widget.setMaximumHeight(30)
                        sub_layout.addWidget(label_widget)

                        # add line edit widget
                        line_edit_widget = QtWidgets.QLineEdit()
                        line_edit_widget.setPlaceholderText("Text")
                        line_edit_widget.setText(attr_value)
                        line_edit_widget.setClearButtonEnabled(True)
                        line_edit_widget.textChanged.connect(self.update_value_path)
                        #                 line_edit_widget.setMaximumHeight(30)
                        sub_layout.addWidget(line_edit_widget)

                        # add browse widget
                        browse_widget = QtWidgets.QPushButton("📂")
                        browse_widget.clicked.connect(self.popup_browse_directory)
                        browse_widget.setMinimumWidth(30)
                        browse_widget.setMaximumWidth(30)
                        sub_layout.addWidget(browse_widget)

                        # utils_tool.debug("line edit : ",line_edit_widget)
                        self.dict_attribute_ram[attr_type].append({"line_edit_widget": line_edit_widget,
                                                                   "browse_widget": browse_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_invalid():
                        widget_info = add_info_tip_widget()
                        # widget_info.setMaximumHeight(30)

                        # add label widget
                        label_widget = QtWidgets.QLabel(utils_tool.generate_nice_name(attr_name))
                        #                 label_widget.setMaximumHeight(30)
                        sub_layout.addWidget(label_widget)

                        # add line edit widget
                        line_edit_widget = QtWidgets.QLineEdit()
                        line_edit_widget.setPlaceholderText("Invalid Type")
                        line_edit_widget.setClearButtonEnabled(True)
                        line_edit_widget.textChanged.connect(self.update_value_path)
                        #                 line_edit_widget.setMaximumHeight(30)
                        line_edit_widget.setEnabled(False)
                        sub_layout.addWidget(line_edit_widget)

                    def add_pattern_enum():
                        widget_info = add_info_tip_widget()

                        # add label widget
                        label_widget = QtWidgets.QLabel(utils_tool.generate_nice_name(attr_name))
                        label_widget.setMinimumWidth(150)
                        label_widget.setMaximumWidth(150)
                        sub_layout.addWidget(label_widget)

                        # add QComboBox
                        combo_box_widget = QtWidgets.QComboBox()
                        enum_values = cmds.attributeQuery(attr_name, node=item_name, listEnum=True)[0]

                        enum_list = enum_values.split(":")

                        for enum_text in enum_list:
                            combo_box_widget.addItem(enum_text)

                        combo_box_widget.currentIndexChanged.connect(self.update_value_enum)
                        combo_box_widget.setCurrentIndex(cmds.getAttr("{}.{}".format(item_name, attr_name)))
                        sub_layout.addWidget(combo_box_widget)

                        spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding,
                                                       QtWidgets.QSizePolicy.Minimum)
                        sub_layout.addSpacerItem(spacer)

                        self.dict_attribute_ram[attr_type].append({"combo_box_widget": combo_box_widget,
                                                                   "attribute": attr_name,
                                                                   "layout": sub_layout})

                    def add_pattern_script():
                        script_name = attr_name.replace("script:", "")

                        widget_info = add_info_tip_widget(custom_attr_name=script_name)

                        spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding,
                                                       QtWidgets.QSizePolicy.Minimum)
                        sub_layout.addSpacerItem(spacer)

                        # add QComboBox
                        button_widget = QtWidgets.QPushButton(utils_tool.generate_nice_name(script_name))
                        button_widget.clicked.connect(self.run_mini_script)
                        sub_layout.addWidget(button_widget)

                        self.dict_attribute_ram["script"].append({"button_widget": button_widget,
                                                                  "attribute": script_name,
                                                                  "layout": sub_layout,
                                                                  "class": class_path,
                                                                  "network_name": item_name})

                    list_ignore_attribute = ["name", "parent", "mirror_control_scale", "debug_mode"]
                    utils_tool.debug("▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁")
                    utils_tool.debug("Update Rig Attribute Setting")

                    # update setting widget and create interfaces
                    for tab_name in list(dict_tab_name.keys()):
                        utils_tool.debug("■ {}".format(tab_name))

                        # create scroll area widget and layout
                        scroll_layout = QtWidgets.QVBoxLayout()
                        scroll_area_widget = QtWidgets.QWidget()
                        scroll_area_widget.setLayout(scroll_layout)

                        # scroll area
                        scroll_area = QtWidgets.QScrollArea()
                        scroll_area.setWidget(scroll_area_widget)
                        scroll_area.setWidgetResizable(True)

                        # create tab member widget
                        tab_widget.addTab(scroll_area, tab_name)

                        # add several widget inside v_layout
                        list_exist_attributes = cmds.listAttr(item_name, ud=1)

                        # add attribute for tab
                        for attr_name in dict_tab_name[tab_name]:
                            if attr_name in list_ignore_attribute:
                                continue

                            sub_layout = QtWidgets.QHBoxLayout()
                            scroll_layout.addLayout(sub_layout)

                            # seperator case
                            if attr_name == "blank":
                                add_blank_widget()

                            # label case
                            elif attr_name.startswith("label:"):
                                add_head_label_widget()

                            elif attr_name.startswith("script:"):
                                add_pattern_script()

                            # valid attribute
                            elif attr_name in list_exist_attributes:
                                if attr_name not in dict_docs.keys():  # invalid case
                                    utils_tool.debug("- {} <INVALID>".format(attr_name))
                                    add_pattern_invalid()

                                else:  # valid case
                                    utils_tool.debug("- {}".format(attr_name))

                                    attr_type = dict_docs[attr_name][0]
                                    attr_value = cmds.getAttr("{}.{}".format(item_name, attr_name))

                                    # attribute type : string
                                    if attr_type == "string":
                                        add_pattern_string()

                                    # attribute type : class_instance
                                    elif attr_type == "path":
                                        add_pattern_path()

                                    # attribute type : string Array
                                    elif attr_type == "stringArray":
                                        add_pattern_stringArray()

                                    # attribute type : bool
                                    elif attr_type == "bool":
                                        add_pattern_bool()

                                    # attribute type : long
                                    elif attr_type == "long":
                                        add_pattern_long()

                                    # attribute type : float
                                    elif attr_type == "float":
                                        add_pattern_float()

                                    # attribute type : enum
                                    elif attr_type == "enum":
                                        add_pattern_enum()


                                    # attribute type : invalid (try to reference by value type)
                                    else:
                                        add_pattern_invalid()

                                        # attr_value = cmds.getAttr("{}.{}".format(item_name, attr_name))
                                        # attr_type = type(attr_value)
                                        #
                                        # # attribute type : list
                                        # if attr_type is list:
                                        #     add_pattern_invalid()
                                        #     # add_pattern_stringArray()
                                        # elif attr_type is str:
                                        #     add_pattern_string()
                                        # elif attr_type is int:
                                        #     add_pattern_long()
                                        # elif attr_type is float:
                                        #     add_pattern_float()
                                        # elif attr_type is bool:
                                        #     add_pattern_bool()
                                        # else:

                        # add spacer to keep attribute on top
                        spacer = QtWidgets.QSpacerItem(20, 500, QtWidgets.QSizePolicy.Minimum,
                                                       QtWidgets.QSizePolicy.Maximum)
                        scroll_layout.addSpacerItem(spacer)

                # reset dict attribute ram and assign variable
                self.dict_attribute_ram = {"path": [], "string": [], "stringArray": [], "long": [], "script": [],
                                           "enum": [], "float": [], "bool": []}
                item_name = self.get_current_selected_module_name_single()
                instance_path = utils_tool.convert_class_path_to_class_instance(
                    cmds.getAttr("{}.class".format(item_name)))

                dict_tab_name, dict_lock = utils_tool.get_variables_from_class(
                    instance_path)  # get tab name and dict lock
                dict_docs = utils_tool.get_dict_attribute_by_class(
                    instance_path)  # get attribute data (name , type and description)
                self.dict_lock = dict_lock  # get attribute data that can be locked

                # Build ------------------------------------------
                # create and add tab widget
                tab_widget = QtWidgets.QTabWidget()
                self.ui.layout_setting.addWidget(tab_widget)

                update_main_setting()
                update_attribute_setting()
                update_tap_recent_name()

                self.lock_layout_by_checkbox()

            def update_name_bar_visual(name):
                self.ui.lineEdit_module_name.setText(name)
                self.ui.lineEdit_module_name.setEnabled(True)

                if not name:
                    return

                self.action_unbuild.setEnabled(cmds.getAttr(name + ".isBuild"))
                self.ui.lineEdit_module_name.setEnabled(not cmds.getAttr(name + ".isBuild"))

                if cmds.getAttr(name + ".isBuild"):  # grey
                    self.ui.lineEdit_module_name.setStyleSheet(
                        "background-color: rgb{};".format(self.dict_color["green"]))
                    self.ui.lineEdit_module_name.setEnabled(False)
                elif not cmds.getAttr(name + ".enable"):  # green
                    self.ui.lineEdit_module_name.setStyleSheet(
                        "background-color: rgb{};".format(self.dict_color["grey"]))

            def update_list_module_color():
                count_items = self.ui.listWidget_rigModule.count()

                # handle empty list
                if count_items == 0:
                    return None

                # iterate and update color for each module
                for index in range(count_items):
                    item = self.ui.listWidget_rigModule.item(index)
                    item_name = item.text()

                    # Has Built - Green
                    if cmds.getAttr("{}.isBuild".format(item_name)):
                        item.setBackground(QtGui.QBrush(
                            QtGui.QColor(self.dict_color["green"][0], self.dict_color["green"][1],
                                         self.dict_color["green"][2])))
                        utils_tool.debug("- {} | Build".format(item_name))
                    # Disable Status - Grey
                    elif not cmds.getAttr("{}.enable".format(item_name)):
                        item.setBackground(QtGui.QBrush(
                            QtGui.QColor(self.dict_color["grey"][0], self.dict_color["grey"][1],
                                         self.dict_color["grey"][2])))
                        utils_tool.debug("- {} | Lock".format(item_name))
                    else:  # Reset
                        item.setBackground(QtGui.QBrush())  # Reset background to default
                        utils_tool.debug("- {} | Enable".format(item_name))

            def set_default_setting():
                update_name_bar_visual(name="")
                update_list_module_color()
                utils.clear_layout(self.ui.layout_setting)
                self.ui.lineEdit_module_name.setStyleSheet("")

            set_default_setting()

            # get utils class_instance from input name
            item_name = self.get_current_selected_module_name_single()

            # not load setting if no selected
            if not item_name:
                return

            update_name_bar_visual(name=item_name)

            # get all variables
            old_class_path = cmds.getAttr("{}.class".format(item_name))

            class_path = utils_tool.convert_class_path_to_class_instance(old_class_path)

            if class_path:
                load_setting_widget()  # class class_instance not found
            else:
                load_missing_widget()  # found class class_instance

        def reload_python_modules():
            importlib.reload(utils)
            importlib.reload(rig_class)
            importlib.reload(config)
            importlib.reload(utils_tool)

            # reload all module
            for modules in self.list_all_modules_instance:
                importlib.reload(modules)

        reload_python_modules()

        search_keyword = self.ui.lineEdit_search.text()

        # get current selection
        selected_indexes = [self.ui.listWidget_rigModule.row(item) for item in self.ui.listWidget_rigModule.selectedItems()]

        # clear widget
        self.ui.listWidget_rigModule.clear()

        list_network = self.get_node_in_scene()

        if not list_network:
            return None

        for node in list_network:
            utils_tool.add_attribute_to_node_name(node)

            if search_keyword and search_keyword.lower() in node.lower():
                self.ui.listWidget_rigModule.addItem(node)

            elif not search_keyword:
                self.ui.listWidget_rigModule.addItem(node)

        # re-select
        for i in selected_indexes:
            self.ui.listWidget_rigModule.item(i).setSelected(True)


        # update module setting
        update_setting_group_box()

    def update_load_popup_rebuild_setting(self):
        # Create a ConfigParser instance
        config = configparser.ConfigParser()

        # Read the existing config.ini file
        config.read(self.dir_config_interface)

        value = self.ui.actionIgnore_Confirm_Rebuild.isChecked()
        # Modify or set a value in a section

        if value is True:
            config['interface']['PopupRebuildConfirm'] = "True"
        elif value is False:
            config['interface']['PopupRebuildConfirm'] = "False"

        # Save changes back to the config.ini file
        with open(self.dir_config_interface, 'w') as configfile:
            config.write(configfile)


    def update_parent_value(self):
        selected = cmds.ls(sl=1)
        list_item = self.get_current_selected_module_name()

        if selected:
            text = selected[0]
        else:
            text = ""

        for item in list_item:
            cmds.setAttr("{}.parent".format(item),text,typ="string")

            self.ui.lineEdit_parent.setText(text)

    def update_debug_mode_value(self):
        check_value = self.ui.checkBox_debug_mode.isChecked()
        list_item = self.get_current_selected_module_name()

        for item in list_item:
            cmds.setAttr("{}.debug_mode".format(item),check_value)

    def update_mirror_control_scale(self):
        check_value = self.ui.checkBox_mirror_scale_control.isChecked()

        list_item = self.get_current_selected_module_name()

        for item in list_item:
            cmds.setAttr("{}.mirror_control_scale".format(item),check_value)

    def popup_browse_directory(self):
        # popup browse window
        browse_path = cmds.fileDialog2(fileMode=1, dialogStyle=2, fileFilter="XML Files (*.xml)")

        if not browse_path:
            return

        # main function
        for each_dict in self.dict_attribute_ram["path"]:
            if each_dict["browse_widget"] == self.sender():
                each_dict["line_edit_widget"].setText(browse_path[0])

    # @utils.undoable
    def run_mini_script(self):
        for each_dict in self.dict_attribute_ram["script"]:
            if each_dict["button_widget"] == self.sender():
                instance = each_dict["class"]()
                func_name =  each_dict["attribute"]
                item_name =  each_dict["network_name"]

                # Debugging steps
                method = getattr(instance, func_name, None)

                # update instance attribute by maya attribute
                for attr in cmds.listAttr(item_name, ud=1):
                    try:
                        value = cmds.getAttr(item_name + "." + attr)
                        setattr(instance, attr, value)
                    except Exception as e:
                        print(e)

                cmds.undoInfo(ock=1)

                if method:
                    return_value = method()  # Should call the function

                    if return_value is True:
                        self.update_module_setting()

                cmds.undoInfo(cck=1)

                del instance

    def update_value_stringArray(self):
        for each_dict in self.dict_attribute_ram["stringArray"]:
            if each_dict["line_edit_widget"] == self.sender():

                # update maya attribute by text input
                update_string = each_dict["line_edit_widget"].text()
                attr_name = each_dict["attribute"]
                input_list = utils_tool.convert_string_to_list(update_string)

                for item_name in self.get_current_selected_module_name():
                    if not cmds.attributeQuery(attr_name,n=item_name,ex=1):
                        continue

                    cmds.setAttr("{}.{}".format(item_name, attr_name), type="stringArray", *([len(input_list)] + input_list))

    def update_value_enum(self):
        for each_dict in self.dict_attribute_ram["enum"]:
            if each_dict["combo_box_widget"] == self.sender():
                # update maya attribute by text input
                current_index = each_dict["combo_box_widget"].currentIndex()
                attr_name = each_dict["attribute"]

                for item_name in self.get_current_selected_module_name():
                    if not cmds.attributeQuery(attr_name, n=item_name, ex=1):
                        continue
                    cmds.setAttr("{}.{}".format(item_name,attr_name),current_index)


    def update_value_string(self):
        for each_dict in self.dict_attribute_ram["string"]:
            if each_dict["line_edit_widget"] == self.sender():

                # update maya attribute by text input
                update_string = each_dict["line_edit_widget"].text()

                for item_name in self.get_current_selected_module_name():
                    cmds.setAttr("{}.{}".format(item_name,each_dict["attribute"]), update_string, typ="string")

    def update_value_long(self):
        for each_dict in self.dict_attribute_ram["long"]:
            if each_dict["long_widget"] == self.sender():

                # update maya attribute by text input
                value =  each_dict["long_widget"].value()

                for item_name in self.get_current_selected_module_name():
                    cmds.setAttr("{}.{}".format(item_name,each_dict["attribute"]),  value)

    def update_value_float(self):
        for each_dict in self.dict_attribute_ram["float"]:
            if each_dict["float_widget"] == self.sender():

                # update maya attribute by text input
                value =  each_dict["float_widget"].value()

                for item_name in self.get_current_selected_module_name():
                    cmds.setAttr("{}.{}".format(item_name,each_dict["attribute"]),  value)

    def update_value_bool(self):
        for each_dict in self.dict_attribute_ram["bool"]:
            if each_dict["checkbox_widget"] == self.sender():

                # update maya attribute by text input
                update_bool =  each_dict["checkbox_widget"].isChecked()

                for item_name in self.get_current_selected_module_name():
                    cmds.setAttr("{}.{}".format(item_name,each_dict["attribute"]),  update_bool)

        self.lock_layout_by_checkbox()
    def update_value_path(self):
        for each_dict in self.dict_attribute_ram["path"]:
            if each_dict["line_edit_widget"] == self.sender():

                # update maya attribute by text input
                update_string = each_dict["line_edit_widget"].text()

                for item_name in self.get_current_selected_module_name():
                    cmds.setAttr("{}.{}".format(item_name,each_dict["attribute"]), update_string, typ="string")

    def get_current_selected_module_name_single(self):
        list_item_name = self.get_current_selected_module_name()

        if list_item_name:
            return list_item_name[0]
        else:
            return
    def get_current_selected_module_name(self):
        return [item.text() for item in self.ui.listWidget_rigModule.selectedItems()]


    def module_rename(self, new_name):
        list_selected = self.ui.listWidget_rigModule.selectedItems()

        # handling
        if not list_selected:
            return None

        item = list_selected[0]
        item_name = item.text()

        # update name
        if not cmds.objExists(new_name) and new_name != "":
            item.setText(new_name)
            cmds.setAttr(item_name + ".name", new_name, typ="string")
            cmds.rename(item_name, new_name)

    def auto_fill_string(self):
        for list_data in self.dict_attribute_ram["string"]:
            if list_data["fill_widget"] == self.sender():
                selection = cmds.ls(sl=1)
                if selection:
                    text = selection[0]
                else:
                    text = ""

                list_data["line_edit_widget"].setText(text)

    def auto_fill_stringArray(self):
        for list_data in self.dict_attribute_ram["stringArray"]:
            if list_data["fill_widget"] == self.sender():
                selection = cmds.ls(sl=1)

                if selection:
                    text = str(selection)
                else:
                    text = ""

                list_data["line_edit_widget"].setText(text)

    def module_duplicate(self):
        list_duplicate_name = []
        list_selected_items = self.ui.listWidget_rigModule.selectedItems()

        if list_selected_items is None:
            return None

        for item in list_selected_items:
            # get module name
            name = item.text()

            # duplicate new instance
            node_copy = utils.flip_keyword(name, ignore=True)
            node_copy = cmds.duplicate(name, n=node_copy)[0]
            cmds.setAttr(node_copy + ".name", node_copy, typ="string")
            cmds.setAttr(node_copy + ".isBuild", False)
            cmds.setAttr(node_copy + ".enable", True)

            list_duplicate_name.append(node_copy)

            # rename all value in attributes and update
            for attr in cmds.listAttr(node_copy, userDefined=True):
                # Construct the full attribute names
                source_attr = f"{name}.{attr}"
                target_attr = f"{node_copy}.{attr}"

                # Check if the attribute exists on both source and target
                if not cmds.objExists(source_attr) or not cmds.objExists(target_attr):
                    utils_tool.debug(f"Skipping: {attr} - Attribute does not exist on source or target.")
                    continue

                # Check if the attribute is of type 'string' or 'stringArray'
                try:
                    attr_type = cmds.getAttr(source_attr, type=True)
                except RuntimeError:
                    utils_tool.debug(f"Skipping: {attr} - Unable to determine attribute type.")
                    continue

                if attr_type == 'string':
                    try:
                        # Get the value of the attribute
                        value = cmds.getAttr(source_attr)
                        if value is None:
                            continue

                        cmds.setAttr(target_attr, utils.flip_keyword(value, ignore=True), type='string')
                    except RuntimeError:
                        utils_tool.debug(f"Skipping: {attr} - Unable to get or set string value.")

                elif attr_type == 'stringArray':
                    # Get the value of the stringArray attribute
                    value_list = cmds.getAttr(source_attr)


                    # Set the flipped value list to the target attribute
                    list_value_flip = [utils.flip_keyword(item, ignore=True) for item in value_list]

                    cmds.setAttr("{}.{}".format(node_copy, attr), type="stringArray", *([len(list_value_flip)] + list_value_flip))

            self.ui.listWidget_rigModule.addItem(node_copy)

        # re-select the duplicates
        self.ui.listWidget_rigModule.clearSelection()

        for index in range(self.ui.listWidget_rigModule.count()):
            item = self.ui.listWidget_rigModule.item(index)

            # Check if the item's text is in the list of target names

            if item.text() in list_duplicate_name:
                item.setSelected(True)
                # Optionally, make sure the item is visible if needed
                self.ui.listWidget_rigModule.scrollToItem(item)

        self.update_module_setting()


    def module_remove(self):
        list_selected_item = self.ui.listWidget_rigModule.selectedItems()
        list_item_name = []

        # remove module
        for item in list_selected_item:
            item_name = item.text()
            list_item_name.append(item_name)

            if cmds.objExists(item_name):
                cmds.delete(item_name)

            # Remove rig widget
            self.ui.listWidget_rigModule.takeItem(self.ui.listWidget_rigModule.row(item))

        # align list widget
        total_items = self.ui.listWidget_rigModule.count()

        if total_items > 0:
            self.ui.listWidget_rigModule.setCurrentRow(total_items - 1)

        self.update_module_setting()

    def module_add(self):
        def add_item():
            # rename if already have the name in listWidget
            node_name = utils_tool.create_network_node(class_instance)

            # add attribute to network node
            utils_tool.add_attribute_to_node_name(node_name)

            # add new item widget
            item = QtWidgets.QListWidgetItem(node_name)
            self.ui.listWidget_rigModule.addItem(item)

            # add tool tips if exist
            doc_string = class_instance.__doc__
            item.setStatusTip(doc_string.split("Variables:")[0]) if doc_string else None

        def refine_item():
            # auto select item and load setting
            created_item_widget = self.ui.listWidget_rigModule.item(self.ui.listWidget_rigModule.count() - 1)
            self.ui.listWidget_rigModule.clearSelection()
            self.ui.listWidget_rigModule.setCurrentItem(created_item_widget)
            self.ui.listWidget_rigModule.scrollToItem(created_item_widget)
            self.update_module_setting()

        if not utils_tool.is_rig_structures():
            cmds.confirmDialog(m="Create Rig Structure First Before add any rig.")
            raise Exception("Not Create Rig Yet")

        selection = cmds.ls(sl=1)
        class_instance = self.dict_action_button_module[self.sender()]

        add_item()
        refine_item()

        cmds.select(selection)

        # debug
        self.get_node_in_scene()

    def module_toggle(self):
        selected = self.ui.listWidget_rigModule.selectedItems()

        if selected is None:
            return None

        list_enable = [cmds.getAttr(item.text() + ".enable") for item in selected]

        if True in list_enable:
            update_value = False
        elif False in list_enable:
            update_value = True

        [cmds.setAttr(item.text() + ".enable", update_value) for item in selected]

        self.update_module_setting()

    def rescale_module_controller(self):
        def get_percentage():
            def get_default_value():
                if cmds.attributeQuery("default_size",node=list_target_item[0],ex=1):
                    default_value = cmds.getAttr("{}.default_size".format(list_target_item[0]))

                else:
                    cmds.addAttr(list_target_item[0],ln="default_size",dv=20,at="long")
                    default_value = 20

                return default_value

            result = cmds.promptDialog(
                title='Enter Scale Size Percentage (1-100)',
                message='Enter Scale Size Percentage (1-100):',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel',
                tx=get_default_value())

            if result == 'OK':
                text = cmds.promptDialog(query=True, text=True)
            else:
                raise Exception("was Canceled")

            if not text.isdigit():
                cmds.confirmDialog(m="Invalid Input, Required Amount, Get {}".format(text))
                raise Exception("Invalid Input, Required Amount, Get {}".format(text))

            return_value = int(text)*0.01

            cmds.setAttr("{}.default_size".format(list_target_item[0]),int(text))

            return return_value

        def get_bounding_box_size(obj):
            xmin, ymin, zmin, xmax, ymax, zmax = cmds.exactWorldBoundingBox(obj)
            return [xmax - xmin, ymax - ymin, zmax - zmin]

        def get_mesh_size_max():
            max_mesh = None

            for mesh in list_meshes:
                bb_mesh = get_bounding_box_size(mesh)
                local_max_mesh = max(bb_mesh)

                # get uniform scale value
                if max_mesh is None:
                    max_mesh = local_max_mesh
                elif max_mesh < local_max_mesh:
                    max_mesh = local_max_mesh

            return max_mesh


        def match_bounding_box(list_control, list_meshes, percent=0.2):

            max_mesh_size = get_mesh_size_max()

            for control in list_control:
                # get max control
                control_size = get_bounding_box_size(control)

                max_control = max(control_size)

                # get scale factor to match the bounding box
                scale_factor = max_mesh_size / max_control

                # apply scale
                cmds.makeIdentity(control, a=1, s=1)
                scale_factor = percent * scale_factor
                cmds.setAttr(control + ".s", scale_factor, scale_factor, scale_factor, typ="double3")
                cmds.makeIdentity(control, a=1, s=1)

        def get_list_controller():
            list_return = []

            for item_name in list_target_item:
                list_each_return = []
                rig_group_name = "{}_{}Rig".format(config.grp,item_name)

                for transform in cmds.listRelatives(rig_group_name, ad=1, typ="transform"):
                    if ( transform.startswith(config.ctrl) or transform.endswith(config.ctrl) ) and not config.grp in transform:
                        list_each_return.append(transform)

                list_return.append(list_each_return)

            return list_return

        def get_list_meshes():
            list_return = []
            list_grp_mesh_child = cmds.listRelatives(config.grp_mesh, ad=1, typ="transform")

            for transform in list_grp_mesh_child:
                list_mesh_child = cmds.listRelatives(transform, c=1, typ="mesh")
                if list_mesh_child:
                    list_return.append(transform)

            return list_return

        def get_list_target_node():
            list_item_name = self.get_current_selected_module_name()

            list_return = []
            for item_name in list_item_name:
                if cmds.getAttr(item_name + ".isBuild") is True:
                    list_return.append(item_name)

            # handle not build
            if not list_return:
                cmds.confirmDialog(m="Selected Modules have not build yet.")
                return None

            return list_return


        def get_scale_normalize_factor(list_input_control):
            max_mesh_size = get_mesh_size_max()

            list_control_size = []
            for control in list_input_control:
                control_size = max(get_bounding_box_size(control))
                list_control_size.append(control_size)


            # avg_size_control = 0
            # for size in list_control_size:
            #     avg_size_control+= size
            #
            # avg_size_control = avg_size_control/len(list_control_size)

            avg_size_control = max(list_control_size)

            # get scale factor to match the bounding box
            scale_factor = max_mesh_size / avg_size_control

            return scale_factor

        def create_temp_controller_list(list_controller):
            def create_each_tmp_controller(source, tmp_controller):
                cmds.duplicate(source, n=tmp_controller)
                utils.lock_attributes(tmp_controller, l=0, t=1, r=1, s=1, v=1)

                if cmds.listRelatives(tmp_controller, p=1):
                    cmds.parent(tmp_controller, w=1)

                # delete tmp controller child transform
                tmp_controller_child = cmds.listRelatives(tmp_controller, c=1, typ="transform", f=1)
                if tmp_controller_child:
                    cmds.delete(tmp_controller_child)

                # Get the bounding box of the controller
                utils.reset_all_transform(tmp_controller)
                cmds.setAttr(tmp_controller + ".ty", 1)

            list_return = []

            for control in list_controller:
                # Apply the scale to the controller using the world space
                tmp_controller = "{}_scale_tmp".format(control)
                create_each_tmp_controller(control, tmp_controller)

                list_return.append(tmp_controller)

            return list_return

        list_grp_mesh_child = cmds.listRelatives(config.grp_mesh, ad=1, typ="transform")

        if not list_grp_mesh_child:
            cmds.confirmDialog(m="Not Found Meshes, Please Add Meshes to a Rig.")
            return None

        cmds.undoInfo(ock=1)

        list_target_item = get_list_target_node()

        match_percent = get_percentage()

        # get list controller and list mesh
        list_controller_sets = get_list_controller()
        list_meshes = get_list_meshes()

        for list_controller in list_controller_sets:
            print("List Controller : ",list_controller)

            list_temp_controller = create_temp_controller_list(list_controller)
            scale_normalize = get_scale_normalize_factor(list_temp_controller)

            for i in range(len(list_controller)):
                control = list_controller[i]
                control_tmp = list_temp_controller[i]

                # apply scale normalize
                cmds.makeIdentity(control_tmp, a=1, s=1)
                cmds.setAttr("{}.s".format(control_tmp), scale_normalize, scale_normalize, scale_normalize, typ="double3")
                cmds.makeIdentity(control_tmp, a=1, s=1)

                # apply new scale
                cmds.setAttr(control_tmp+".s",match_percent,match_percent,match_percent,typ="double3")
                cmds.makeIdentity(control_tmp, a=1, s=1)

                utils.clone_shape([control,control_tmp])
                cmds.delete(control_tmp)

        cmds.undoInfo(cck=1)

    def lock_layout_by_checkbox(self):
        def get_dict_by_given_attribute(attribute):
            for list_data in self.dict_attribute_ram.values():
                for dict_data in list_data:
                    if attribute == dict_data["attribute"]:
                        return dict_data
            return None

        for attribute in self.dict_lock.keys():
            # get channel box dict
            dict_attr_lock  = get_dict_by_given_attribute(attribute)
            list_dict_attr_child = [get_dict_by_given_attribute(attr) for attr in self.dict_lock[attribute]]
            list_layout_child = []

            list_child_attr = [attr for attr in self.dict_lock[attribute]]

            if not dict_attr_lock:
                continue

            check_value = dict_attr_lock["checkbox_widget"].isChecked()


            # get layout widget list
            for attr_dict in list_dict_attr_child:
                if not attr_dict:
                    continue

                for attr_child in list_child_attr:
                    if attr_dict["attribute"] == attr_child:
                        layout = attr_dict["layout"]

                        utils.set_layout_disabled(layout, check_value)



class LauncherWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    dir_config_interface = config.root_file + "/interface_config.ini"

    WINDOW_TITLE = "Easy Skeleton Launcher {}".format(version)
    WINDOW_OBJECT = "EasySkeletonLauncher"

    base_file_path = ""
    save_directory_path = ""

    list_add_model = []
    list_add_global = []
    list_add_local = []

    def __init__(self):
        # Set-up Interface
        super(LauncherWindow, self).__init__(parent=None)
        utils_tool.deleteControl(self.WINDOW_OBJECT + "WorkspaceControl")

        loader = QtUiTools.QUiLoader()
        self.ui = utils_tool.load_ui(QtCore.QFile("{}\\interface\\Launcher.ui".format(config.root_file)))

        self.setCentralWidget(self.ui)
        self.setFixedSize(self.ui.size())

        self.setObjectName(self.WINDOW_OBJECT)
        self.setWindowTitle(self.WINDOW_TITLE)

        self.ui.pushButton_start.clicked.connect(self.launcher_builder)

        self.ui.pushButton_meshes.clicked.connect(self.add_model)
        self.ui.pushButton_global.clicked.connect(self.add_global_joint)
        self.ui.pushButton_local.clicked.connect(self.add_local_joint)

    def add_model(self):
        self.ui.lineEdit_meshes.setText(str(cmds.ls(sl=1)))
        self.list_add_model = cmds.ls(sl=1)
    def add_global_joint(self):
        self.ui.lineEdit_global.setText(str(cmds.ls(sl=1)))
        self.list_add_global = cmds.ls(sl=1)

    def add_local_joint(self):
        self.ui.lineEdit_local.setText(str(cmds.ls(sl=1)))
        self.list_add_local = cmds.ls(sl=1)

    def launcher_builder(self):
        utils_tool.create_rig()

        cmds.select(self.list_add_global)
        utils.rig_manage(add_joint=True)

        cmds.select(self.list_add_model)
        utils.rig_manage(add_model=True)

        cmds.select(self.list_add_local)
        utils.rig_manage(add_joint_local=True)

        # launch ui builder
        window = MainWindow()
        window.show(dockable=True)

        self.close()
