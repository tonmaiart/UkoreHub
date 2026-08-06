from importlib import reload

import tmlib
from tmlib.core import (
    Attribute,
    BlendShape,
    Connection,
    Controller,
    Create,
    Deformer,
    File,
    Format,
    Misc,
    QuickData,
    Scene,
    Selection,
    SkinWeight,
    System,
    Transform,
    Utility,
    Validate,
    Visualized,
    Math,
    Geometry
)

from tmlib.module import PySide
from tmlib.ui import interface_template, uitools


def reload_scripts():
    # reload module
    reload(PySide)

    # reload core
    reload(Attribute)
    reload(BlendShape)
    reload(Connection)
    reload(Create)
    reload(Deformer)
    reload(File)
    reload(Format)
    reload(Misc)
    reload(QuickData)
    reload(Scene)
    reload(Selection)
    reload(SkinWeight)
    reload(System)
    reload(Transform)
    reload(Utility)
    reload(Validate)
    reload(Visualized)
    reload(Math)
    reload(Geometry)
    reload(Controller)
    
    # reload template ui
    reload(interface_template)
    reload(uitools)
