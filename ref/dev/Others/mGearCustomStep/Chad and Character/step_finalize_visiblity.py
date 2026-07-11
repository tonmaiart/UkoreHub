import mgear.rigbits
import mgear.shifter.custom_step as cstp
from mgear import rigbits,animbits
import pymel.core as pm
import maya.cmds as mc
from mgear.core import attribute
from TonmaiToolkit import utils,polish
from TonmaiToolkit.toolkits.ControllerEditor import func
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
        self.name = "step_finalize"

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

        # backup controller
        func.backup_recall()


        # hide index ctrl
        list_finalize = ["index_L0_fk0_ctlShape"]

        for obj in list_finalize:
            for side in ["_L0_", "_R0_"]:
                target_obj = obj.replace("_L0_", side)

                if not mc.objExists(target_obj):
                    raise Exception("{} not found in finalize".format(target_obj))

                # function
                pm.setAttr("{}.v".format(target_obj),0)

        # hide attribute
        # List of attributes to lock and hide
        attributes = [
            "IkPivot",
            "roll",
            "sideRoll",
            "middleRoll",
            "baseTwist",
            "tipTwist",
            "rollBallEnd"
        ]

        # Target control
        control = "arm_L0_hand_ik_ctl"

        # Iterate and apply setAttr for each attribute
        for obj in [control]:
            for side in ["_L0_", "_R0_"]:
                target_obj = obj.replace("_L0_", side)

                # main function
                for attr in attributes:
                    full_attr = f"{target_obj}.{attr}"
                    mc.setAttr(full_attr, lock=True, keyable=False, channelBox=False)

        # Remove all mgear node
        polish.clean_mgear_mult_matrix()
        polish.clean_mgear_matrix_constraint()

