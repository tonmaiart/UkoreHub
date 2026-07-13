import mgear.rigbits
import mgear.shifter.custom_step as cstp
from mgear import rigbits,animbits
import pymel.core as pm
import maya.cmds as mc
from mgear.core import attribute
from TonmaiToolkit import utils
from importlib import reload

reload(utils)

class CustomShifterStep(cstp.customShifterMainStep):
    """Custom Step description
    """

    def setup(self):
        """
        Setting the name property makes the custom step accessible
        in later steps.

        i.e: Running  self.custom_step("add_corrective_finger_joints")  from steps ran after
             this one, will grant this step.
        """
        self.name = "proper_rename"


    def run(self):
        """Run method.

            i.e:  self.mgear_run.global_ctl
                gets the global_ctl from shifter rig build base

            i.e:  self.component("control_C0").ctl
                gets the ctl from shifter component called control_C0

            i.e:  self.custom_step("otherCustomStepName").ctlMesh
                gets the ctlMesh from a previous custom step called
                "otherCustomStepName"

        Returns:
            None: None
        """

        dict_rename_data = {
            "leg": [["root", "upper"], ["elbow", "knee"], ["wrist", "foot"]],
            "arm": [["root", "upper"], ["elbow", "elbow"], ["wrist", "hand"]]
        }

        controls = utils.get_objects_in_set("rig_controllers_grp")

        for ctl in controls:
            for start_keyword in dict_rename_data.keys():
                for data in dict_rename_data[start_keyword]:
                    old_name = data[0]
                    new_name = data[1]

                    if ctl.startswith(start_keyword) and old_name in utils.cut(ctl):
                        mc.rename(ctl,ctl.replace(old_name,new_name))