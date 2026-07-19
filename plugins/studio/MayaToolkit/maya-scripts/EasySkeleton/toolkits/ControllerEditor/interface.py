from EasySkeleton import config,rig_class,utils,utils_tool
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtWidgets, QtCore, QtUiTools, QtGui
import maya.cmds as cmds
import os, importlib, webbrowser, inspect, configparser
import maya.mel as mel

class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    dir_config_interface = config.root_file + "/interface_config.ini"
    controller_file = config.root_file + "/controller.ma"

    dict_curve_color = {}
    dict_curve_color_button = {}
    dict_curve_shape = {}

    WINDOW_TITLE = "Controller Editor"
    WINDOW_OBJECT = "CtrlToolkit"

    base_file_path = ""
    save_directory_path = ""

    list_add_model = []
    list_add_global = []
    list_add_local = []

    def __init__(self):
        # Set-up Interface
        super(MainWindow, self).__init__(parent=None)
        utils_tool.deleteControl(self.WINDOW_OBJECT + "WorkspaceControl")

        self.ui = utils_tool.load_ui("{}\\ControllerEditor\\CtrlToolkit.ui".format(config.toolkit_path))

        self.setCentralWidget(self.ui)
        self.setFixedSize(self.ui.size())

        self.setObjectName(self.WINDOW_OBJECT)
        self.setWindowTitle(self.WINDOW_TITLE)

        # connect widget
        self.ui.listWidget_controller.itemDoubleClicked.connect(self.replace_shape)

        self.reload_controller()

        self.reload_curve_type()

        self.ui.pushButton_color_editor.clicked.connect(self.change_curve_color)
        self.ui.pushButton_line_width_apply.clicked.connect(utils.set_width)

        # isolate edit
        self.ui.pushButton_isolateEdit.clicked.connect(lambda x: utils.isolate_edit(False, False))
        self.ui.pushButton_isolateClear.clicked.connect(lambda x: utils.isolate_clear())

        # multiple replace function
        self.ui.pushButton_replace.clicked.connect(utils.clone_shape)

        # another function
        self.ui.pushButton_mirror_replace.clicked.connect(utils.clone_to_opposite)

        # flip function
        self.ui.pushButton_flipX.clicked.connect(lambda x: utils.flip_shape("x"))
        self.ui.pushButton_flipY.clicked.connect(lambda x: utils.flip_shape("y"))
        self.ui.pushButton_flipZ.clicked.connect(lambda x: utils.flip_shape("z"))

        # backup function
        self.ui.comboBox_filter.currentIndexChanged.connect(self.reload_list_widget)

        self.ui.pushButton_color_delete.clicked.connect(self.clear_color)

    @utils.undoable
    def clear_color(self):
        utils.set_curve_color(cmds.ls(sl=1), clear=True)
        self.reload_controller()

        cmds.select(cl=1)

    def select_color_history(self):
        rgb = self.dict_curve_color_button[self.sender()]
        # selection = cmds.ls(sl=1)

        list_shape = self.dict_curve_color[rgb]
        list_transform = []

        for shape in list_shape:
            transform = cmds.listRelatives(shape,p=1,typ="transform")
            utils_tool.debug(transform)
            if transform and "bck_" not in transform:
                list_transform.append(transform[0])

        cmds.select( list_transform)

    def replace_shape(self):
        recent_name = self.ui.listWidget_controller.currentItem().text()
        selection  = cmds.ls(sl=1)

        if not selection:
            return

        for list_curve in self.dict_curve_shape.values():
            for curve in list_curve:
                if recent_name == curve.split("_")[-1]:
                    cmds.undoInfo(ock=1)

                    utils.clone_shape(selection+[curve])
                    cmds.select(selection)

                    print(curve)
                    cmds.undoInfo(cck=1)

                    return

    def reload_controller(self):
        def reload_color_history():
            def get_curve_color():
                list_curve_shape_in_scene = cmds.ls(typ="nurbsCurve")

                for shape in list_curve_shape_in_scene:
                    if not cmds.getAttr("{}.overrideEnabled".format(shape)):
                        continue

                    if cmds.getAttr("{}.overrideRGBColors".format(shape)):
                        red = cmds.getAttr("{}.overrideColorR".format(shape))
                        green = cmds.getAttr("{}.overrideColorG".format(shape))
                        blue = cmds.getAttr("{}.overrideColorB".format(shape))

                        rgb = (red, green, blue)

                        if rgb not in self.dict_curve_color:
                            self.dict_curve_color[rgb] = []

                        self.dict_curve_color[rgb].append(shape)

            def add_button():
                utils.clear_layout(self.ui.layout_color_scene)

                for key in self.dict_curve_color.keys():
                    button = QtWidgets.QPushButton()
                    button.setMaximumWidth(20)

                    self.dict_curve_color_button[button] = key

                    key_norm = [value * 255 for value in key]
                    button.setStyleSheet("background-color: rgb({}, {}, {});".format(key_norm[0], key_norm[1], key_norm[2]))

                    button.clicked.connect(self.select_color_history)

                    self.ui.layout_color_scene.addWidget(button)

                spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
                self.ui.layout_color_scene.addSpacerItem(spacer)

            self.dict_curve_color = {}
            self.dict_curve_color_button = {}

            # clear layout
            get_curve_color()
            add_button()

        def reload_shape():
            if cmds.objExists(config.grp_controller_reference):
                return

            # # import group
            # cmds.file(
            #     self.controller_file,
            #     i=True,  # Import file
            #     type="mayaAscii",  # Specify file type
            #     gr=True,  # Group under a transform
            #     ignoreVersion=True,  # Ignore version mismatch
            #     ra=True,  # Resolve all
            #     mergeNamespacesOnClash=False,  # Do not merge namespaces
            #     rpr="New_CurveShape",  # Root prefix for references
            #     options="v=0;",  # Options string
            #     pr=True,  # Preserve references
            #     importFrameRate=True,  # Import frame rate
            #     importTimeRange="override", # Import time range override,
            #     gn=config.grp_controller_reference
            # )

            # cmds.parent(config.grp_controller_reference,config.grp_still)
            # for curve in cmds.listRelatives(config.grp_controller_reference,c=1,f=1):
            #     cmds.rename(curve,utils.cut(curve).replace("New_CurveShape_",""))
            #
            # # hide group
            # cmds.setAttr(config.grp_controller_reference+".v",0)

        # reload_color_history()
        reload_shape()
    def change_curve_color(self):
        selection = cmds.ls(sl=1)

        cmds.undoInfo(ock=1)
        cmds.select(cl=1)
        cmds.colorEditor()

        if cmds.colorEditor(query=True, result=True):
            rgb = cmds.colorEditor(query=True, rgb=True)

            # utils_tool.debug(rgb,hsc,alpha)
            utils.set_curve_color(selection, rgb=rgb)
            self.reload_controller()
        else:
            pass

        cmds.undoInfo(cck=1)

    def reload_curve_type(self):
        self.dict_curve_shape = {}

        for curve in cmds.listRelatives(config.grp_controller_reference,c=1,f=1):
            type = utils.cut(curve).split("_")[0]

            if type not in self.dict_curve_shape:
                self.dict_curve_shape[type] = []

            self.dict_curve_shape[type].append(utils.cut(curve))

        # add to combobox
        self.ui.comboBox_filter.clear()

        for item in self.dict_curve_shape.keys():
            self.ui.comboBox_filter.addItem(item)

        self.reload_list_widget()

    def reload_list_widget(self):
        # reload list widget
        self.ui.listWidget_controller.clear()

        key = self.ui.comboBox_filter.currentText()

        for curve in self.dict_curve_shape[key]:
            curve_nice_name=  curve.replace(key+"_","")
            self.ui.listWidget_controller.addItem(curve_nice_name)