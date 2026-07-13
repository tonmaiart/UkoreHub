import maya.cmds as cmds
import os
import maya.mel
from TonmaiToolkit.core import Utility, Misc
from TonmaiToolkit.ui.interface_template import ToolkitWindow
from TonmaiToolkit.module.PySide import QtCore, QtGui, QtWidgets, QAction


class MainWindow(ToolkitWindow):
    def __init__(self):
        # load and setup widget
        super(MainWindow, self).__init__("CFXTools")

        self.ui.pushButton_template.clicked.connect(lambda x: self.create_groups())
        self.ui.pushButton_cleanMesh.clicked.connect(lambda x: self.clean_model())
        self.ui.pushButton_addBlendshape.clicked.connect(
            lambda x: self.add_blendshape()
        )
        self.ui.pushButton_addWrap.clicked.connect(self.add_wrap)
        self.ui.pushButton_createTrackCam.clicked.connect(
            lambda x: self.create_track_camera()
        )
        self.ui.pushButton_create_nrigid.clicked.connect(self.create_passive_collider)
        self.ui.pushButton_create_ncloth.clicked.connect(self.create_ncloth)
        self.ui.pushButton_cfx_template_v2.clicked.connect(self.create_template_v2)

    def create_template_v2(self):
        grp_anim = cmds.group(em=1, n="ANIM")
        cmds.group(em=1, n="anim_grp", p=grp_anim)
        cmds.group(em=1, n="blend_anim_grp", p=grp_anim)
        cmds.group(em=1, n="anim_extra_grp", p=grp_anim)

        grp_sim = cmds.group(em=1, n="SIM")
        cmds.group(em=1, n="fx_node_grp", p=grp_sim)
        cmds.group(em=1, n="mesh_collide_grp", p=grp_sim)
        cmds.group(em=1, n="mesh_nCloth_grp", p=grp_sim)
        cmds.group(em=1, n="sim_extra_grp", p=grp_sim)

        cmds.group(em=1, n="RENDER")

    def add_wrap(self):
        list_selection = cmds.ls(sl=1)

        list_wrap_deformers = cmds.ls(type="wrap")

        cmds.CreateWrap()

        list_new_wrap_deformers = cmds.ls(type="wrap")

        unique_items = list(set(list_wrap_deformers) ^ set(list_new_wrap_deformers))

        cmds.select(unique_items[0])

        cmds.rename(unique_items[0], list_selection[1] + "_wrap")

    def create_ncloth(self):
        selection = cmds.ls(sl=1)

        if not selection:
            return

        maya.mel.eval("createNCloth 0;")

        collider_shape = cmds.ls(sl=1)
        list_collider_transform = cmds.listRelatives(
            collider_shape, p=1, typ="transform"
        )

        # rename transform node
        for i, transform in enumerate(list_collider_transform):
            new_name = selection[i] + "_nCloth"

            cmds.rename(transform, new_name)

        cmds.inViewMessage(amg="nCloth Created", pos="midCenter", fade=True)

    def create_passive_collider(self):
        selection = cmds.ls(sl=1)

        if not selection:
            return

        maya.mel.eval("makeCollideNCloth;")

        collider_shape = cmds.ls(sl=1)
        list_collider_transform = cmds.listRelatives(
            collider_shape, p=1, typ="transform"
        )

        # rename transform node
        for i, transform in enumerate(list_collider_transform):
            new_name = selection[i] + "_nRigid"

            cmds.rename(transform, new_name)

        cmds.inViewMessage(amg="nRigid Created", pos="midCenter", fade=True)

    @Misc.undoable
    def create_groups(self):
        grp_clothRig = cmds.group(n="grp_ClothRig", em=1)

        [
            cmds.parent(cmds.group(n=name, em=1), grp_clothRig)
            for name in [
                "grp_Alembic",
                "grp_Cin",
                "grp_Col",
                "grp_ColAdd",
                "grp_Dyn",
                "grp_Sim",
            ]
        ]
        [
            cmds.parent(cmds.group(n=name, em=1), "grp_Sim")
            for name in ["grp_Rbd", "grp_nCloth", "grp_DynCons"]
        ]

        grp_wrapRig = cmds.group(n="grp_WrapRig", em=1)

        [
            cmds.parent(cmds.group(n=name, em=1), grp_wrapRig)
            for name in ["grp_getWrap", "grp_getDynBsp"]
        ]

        grp_output = cmds.group(n="grp_Output", em=1)

        cmds.select(cl=1)

    @Misc.undoable
    def clean_model(self):
        sel = cmds.ls(sl=1, l=1)
        list_child = cmds.listRelatives(sel, ad=1, typ="transform", f=1)
        list_target = sel + list_child if list_child is not None else sel

        # unlock attributes
        for target in list_target:
            list_attr = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
            [cmds.setAttr("{}.{}".format(target, attr), k=1, l=0) for attr in list_attr]

        # delete history
        [cmds.delete(list_target, ch=1) for target in list_target]

        # delete orig shape
        for target in list_target:
            list_shapes = cmds.listRelatives(target, c=1, s=1, typ="mesh", f=1)

            if list_shapes:
                # delete orig
                for shape in list_shapes:
                    if "Orig" in shape:
                        cmds.delete(shape)

                # rename all shape
                for shape in list_shapes:
                    parent_name = cmds.listRelatives(shape, p=1, typ="transform")[0]
                    parent_name = (
                        parent_name.split("|")[-1]
                        if "|" in parent_name
                        else parent_name
                    )

                    cmds.rename(shape, parent_name + "Shape")

        cmds.select(cl=1)

    @Misc.undoable
    def create_track_camera(self):
        selection = cmds.ls(sl=1)
        flc_target, grp_abc = selection

        loc_fwd = cmds.spaceLocator(n="loc_fwd")[0]
        loc_bwd = cmds.spaceLocator(n="loc_bwd")[0]

        # match locator to follicle
        cons_fwd = cmds.pointConstraint(flc_target, loc_fwd)
        cons_bwd = cmds.pointConstraint(flc_target, loc_bwd)

        # bake simulation
        time_range = (
            cmds.playbackOptions(q=True, min=True),
            cmds.playbackOptions(q=True, max=True),
        )
        print(time_range, type(time_range))
        cmds.bakeResults(
            loc_bwd,
            loc_fwd,
            sm=1,
            t=time_range,
            dic=1,
            pok=1,
            ral=0,
            rba=0,
            bol=0,
            mr=1,
            cp=0,
            s=1,
        )

        cmds.delete(cons_bwd, cons_fwd)

        # delete all key except translate for bwd
        list_attr = ["rx", "ry", "rz", "sx", "sy", "sz"]
        [cmds.cutKey("{}.{}".format(loc_bwd, attr)) for attr in list_attr]
        cmds.setAttr(loc_bwd + ".s", 1, 1, 1, typ="double3")

        [cmds.setAttr(loc_bwd + "." + attr, l=0, k=0) for attr in list_attr]

        # reverse scale graph of bwd locator
        cmds.scaleKey(
            "{}.tx".format(loc_bwd),
            "{}.ty".format(loc_bwd),
            "{}.tz".format(loc_bwd),
            asp=0,
            t=(None, None),
            ts=1,
            tp=0,
            fs=1,
            fp=0,
            vs=-1,
            vp=0,
            hi="none",
            cp=0,
            s=1,
        )

        # parent grp abc to bwd locator
        cmds.parent(grp_abc, loc_bwd)
        cmds.group(grp_abc, n="grp_bwd")

        # create camera
        cam_track = cmds.camera(n="cam_track")
        cmds.parent(cam_track, loc_bwd)

    @Misc.undoable
    def add_blendshape(self):
        selection = cmds.ls(sl=1)
        node_bshp = cmds.blendShape(selection, n="bsn_{}".format(selection[-1]))
        cmds.select(node_bshp)


def show():
    window = MainWindow()
    window.show()
