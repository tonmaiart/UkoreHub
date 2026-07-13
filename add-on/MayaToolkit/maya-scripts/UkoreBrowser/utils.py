import maya.cmds as mc
import os
import json
import logging
import subprocess
from functools import partial
import tmlib
import re


def open_directory(path):
    """Use to open path"""

    subprocess.Popen(f'explorer "{os.path.normpath(path)}"')


def create_reference(path):
    filename = os.path.basename(path)

    if "publish" in path:
        split_name = os.path.normpath(path).split(os.sep)
        namespace = f"{split_name[-5]}_{split_name[-4]}_{split_name[-3]}"
        group_name = namespace

    else:
        namespace = os.path.splitext(filename)[0]
        group_name = os.path.basename(os.path.dirname(path))

    try:
        # Reference file
        mc.file(
            path,
            reference=True,
            namespace=namespace,
            ignoreVersion=True,
            mergeNamespacesOnClash=False,
        )

        print("# Import Reference Info")
        print("- Namespaces : {}".format(namespace))

        # หา top-level objects ทั้งหมด
        top_nodes = mc.ls(assemblies=True, long=True)

        # เอาเฉพาะ nodes ที่มี namespace ตรงกับ reference
        to_parent = []
        for node in top_nodes:
            short_name = node.split("|")[-1]  # last segment
            if short_name.startswith(namespace + ":"):
                to_parent.append(node)
        print("To Parent : ", to_parent)

        # Parent เข้า group
        if len(to_parent) > 1:
            # สร้าง group
            if not mc.objExists(group_name):
                top_grp = mc.group(em=True, name=group_name)
            else:
                top_grp = group_name

            for obj in to_parent:
                try:
                    mc.parent(obj, top_grp)
                except:
                    pass

        mc.inViewMessage(
            amg=f"<hl>Referenced :</hl> {group_name}",
            pos="midCenter",
            fade=True,
        )

    except Exception as e:
        mc.confirmDialog(title="Error", message=str(e))
