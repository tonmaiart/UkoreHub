import pymel.core as pm
from pymel.core import datatypes
import maya.cmds as mc
import mgear.rigbits
from mgear.rigbits.facial_rigger.constraints import namePrefix
from mgear.shifter import component, log_window
import math
import maya.api.OpenMaya as om
from mgear.core import node, applyop, vector
from mgear.core import attribute, transform, primitive
import math
from TonmaiToolkit.core import Utility,Misc,Create,Connection,Transform
from importlib import reload
from TonmaiToolkit.mgear_scripts import limb_component

reload(limb_component)

class Component(limb_component.Limb):
    def __init__(self, rig, guide):
        super().__init__(rig=rig,guide=guide,is_arm=False)