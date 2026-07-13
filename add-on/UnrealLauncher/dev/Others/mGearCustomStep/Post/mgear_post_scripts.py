import mgear.rigbits
import mgear.shifter.custom_step as cstp
from mgear import rigbits, animbits
import pymel.core as pm
import maya.cmds as mc
from mgear.core import attribute
from importlib import reload
from TonmaiToolkit.core import (
    Connection,
    Controller,
    Create,
    Misc,
    Transform,
    Utility,
    QuickData,
)


class CustomShifterStep(cstp.customShifterMainStep):
    """Custom Step description"""

    def setup(self):
        """
        Setting the name property makes the custom step accessible
        in later steps.

        i.e: Running  self.custom_step("add_corrective_finger_joints")  from steps ran after
             this one, will grant this step.
        """
        self.name = "post_durian"

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

        self.blend_enum_space()
        self.add_corrective_joints()

        # self.set_proper_name()

        # QuickData.apply_controller_and_skin()

        self.finalize()

        ##########################
        ### Add Skirt Auto Rot ###
        ##########################

        leg_data = Create.create_world_vector("leg_L0_up_1_jnt", "leg_L0_up_2_jnt")

        for a in ["A", "B", "C"]:
            grp_rot = Create.create_freeze_group(["skirt{}_L0_ctl".format(a)])[0]
            Create.create_skirt_auto_rot(
                leg_data,
                "skirt{}_L0_ik_cns".format(a),
                None,
                "{}.rx".format(grp_rot),
                axis="x",
                invert=False,
                clamp_value=[0, 115],
                intensity=1.1,
            )

        for a in ["D", "E"]:
            grp_rot = Create.create_freeze_group(["skirt{}_L0_ctl".format(a)])[0]
            Create.create_skirt_auto_rot(
                leg_data,
                "skirt{}_L0_ik_cns".format(a),
                None,
                "{}.rx".format(grp_rot),
                axis="x",
                invert=False,
                clamp_value=[0, 110],
                intensity=1.1,
            )

        leg_data = Create.create_world_vector("leg_R0_up_1_jnt", "leg_R0_up_2_jnt")

        for a in ["A", "B", "C"]:
            grp_rot = Create.create_freeze_group(["skirt{}_R0_ctl".format(a)])[0]
            Create.create_skirt_auto_rot(
                leg_data,
                "skirt{}_R0_ik_cns".format(a),
                None,
                "{}.rx".format(grp_rot),
                axis="x",
                offset_amount=120,
                invert=True,
                clamp_value=[0, 115],
                intensity=1.1,
            )
        for a in ["D", "E"]:
            grp_rot = Create.create_freeze_group(["skirt{}_R0_ctl".format(a)])[0]
            Create.create_skirt_auto_rot(
                leg_data,
                "skirt{}_R0_ik_cns".format(a),
                None,
                "{}.rx".format(grp_rot),
                axis="x",
                offset_amount=120,
                invert=True,
                clamp_value=[0, 110],
                intensity=1.1,
            )

    def finalize(self):
        if pm.objExists("rig"):
            try:
                pm.setAttr("rig.ctl_vis_on_playback", False)
                # pm.setAttr("rig.jnt_vis",False)

            except:
                pass

    def blend_enum_space(self):
        dict_enum_space = {
            "Head": {
                "object_driven": "neck_C0_head_ctl",
                "list_target": [
                    "global_C0_ctl",
                    "torso_C0_chest_ik_ctl",
                    "torso_C0_cog_ctl",
                    "neck_C0_head_ctl_npo",
                ],
                "list_target_name": ["Global", "Chest", "Root", "Parent"],
                "object_attribute": "neck_C0_head_ctl",
                "type": "orient",
            },
            "armIkElbow": {
                "object_driven": "arm_L0_low_ik_ctl",
                "list_target": [
                    "global_C0_ctl",
                    "torso_C0_chest_ik_ctl",
                    "torso_C0_cog_ctl",
                    "clav_L0_ctl",
                ],
                "list_target_name": ["Global", "Chest", "Root", "clav"],
                "object_attribute": "arm_L0_low_ik_ctl",
                "type": "parent",
            },
            "armIkWrist": {
                "object_driven": "arm_L0_end_ik_ctl",
                "list_target": [
                    "global_C0_ctl",
                    "torso_C0_chest_ik_ctl",
                    "torso_C0_cog_ctl",
                    "clav_L0_ctl",
                ],
                "list_target_name": ["Global", "Chest", "Root", "clav"],
                "object_attribute": "arm_L0_end_ik_ctl",
                "type": "parent",
            },
            "armFkRoot": {
                "object_driven": "arm_L0_root_fk_ctl",
                "list_target": [
                    "global_C0_ctl",
                    "torso_C0_chest_ik_ctl",
                    "torso_C0_cog_ctl",
                    "clav_L0_ctl",
                ],
                "list_target_name": ["Global", "Chest", "Root", "clav"],
                "object_attribute": "arm_L0_root_fk_ctl",
                "type": "orient",
            },
            "LegIkWrist": {
                "object_driven": "leg_L0_end_ik_ctl",
                "list_target": ["global_C0_ctl", "torso_C0_cog_ctl"],
                "list_target_name": ["Global", "Root"],
                "object_attribute": "leg_L0_end_ik_ctl",
                "type": "parent",
            },
            "legIkPoleVector": {
                "object_driven": "leg_L0_low_ik_ctl",
                "list_target": ["global_C0_ctl", "torso_C0_cog_ctl"],
                "list_target_name": ["Global", "Root"],
                "object_attribute": "leg_L0_low_ik_ctl",
                "type": "parent",
            },
            "LegFkRoot": {
                "object_driven": "leg_L0_root_fk_ctl",
                "list_target": ["global_C0_ctl", "torso_C0_cog_ctl"],
                "list_target_name": ["Global", "Root"],
                "object_attribute": "leg_L0_root_fk_ctl",
                "type": "orient",
            },
        }

        for key, data in zip(dict_enum_space.keys(), dict_enum_space.values()):
            L = "_L0_"
            R = "_R0_"

            for side in [L, R]:
                object_driven = data["object_driven"].replace(L, side)
                object_attribute = data["object_attribute"].replace(L, side)
                list_target = [each.replace(L, side) for each in data["list_target"]]
                list_target_name = [
                    each.replace(L, side) for each in data["list_target_name"]
                ]
                type = data["type"]

                if pm.objExists(object_attribute) and pm.objExists(object_attribute):
                    Connection.create_switch_enum(
                        object_attribute=object_attribute,
                        list_target=list_target,
                        list_target_name=list_target_name,
                        object_driven=object_driven,
                        type=type,
                    )
                else:
                    pm.warning(
                        "{} data is skipped, error to create enum space.".format(
                            key, side
                        )
                    )

                # don't do twice if not side suffix in given object driven (for center object , like neck and torso)
                if L not in object_driven and R not in object_driven:
                    break

    def set_proper_name(self):
        dict_rename_data = {
            "leg": [["root", "upper"], ["low", "knee"], ["wrist", "foot"]],
            "arm": [["root", "upper"], ["low", "low"], ["wrist", "hand"]],
        }

        controls = Utility.get_objects_in_set("rig_controllers_grp")

        for ctl in controls:
            for start_keyword in dict_rename_data.keys():
                for data in dict_rename_data[start_keyword]:
                    old_name = data[0]
                    new_name = data[1]

                    if ctl.startswith(start_keyword) and old_name in Utility.cut(ctl):
                        mc.rename(ctl, ctl.replace(old_name, new_name))

    def add_corrective_joints(self):
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

        #####################
        ###### L wrist ######
        #####################

        joint_target = "arm_L0_end_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=0.1,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=0.1,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="x",
            rotate=30,
        )

        #################
        #### R wrist ####
        #################
        joint_target = "arm_R0_end_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=0.1,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=0.1,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="x",
            rotate=30,
        )

        ###########################
        ###### L low Volume #####
        ###########################
        joint_target = "arm_L0_low_1_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=0.2,
            axis_push="z",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=-0.3,
            axis_push="z",
            axis_aim="x",
            rotate=-30,
        )

        ###########################
        ###### R low Volume #####
        ###########################

        joint_target = "arm_R0_low_1_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=0.2,
            axis_push="z",
            axis_aim="x",
            rotate=30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=-0.3,
            axis_push="z",
            axis_aim="x",
            rotate=30,
        )

        ###################
        ### L Shoulder ####
        ###################

        Create.create_volume_joint(
            "arm_L0_up_1_jnt",
            offset=1,
            intensity=-0.1,
            axis_push="y",
            axis_aim="x",
            rotate=-60,
        )

        ###################
        ### R Shoulder ####
        ###################

        Create.create_volume_joint(
            "arm_R0_up_1_jnt",
            offset=1,
            intensity=-0.1,
            axis_push="y",
            axis_aim="x",
            rotate=-60,
        )

        #################
        #### L Knee #####
        #################

        Create.create_volume_joint(
            "leg_L0_low_1_jnt",
            offset=1,
            intensity=0.1,
            axis_push="z",
            axis_aim="y",
            rotate=60,
        )

        ###############
        ### R Knee ####
        ###############

        Create.create_volume_joint(
            "leg_R0_low_1_jnt",
            offset=-1,
            intensity=0.1,
            axis_push="z",
            axis_aim="y",
            rotate=-60,
        )

        ##############
        #### L Hip ###
        ##############
        joint_target = "leg_L0_up_1_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=0.15,
            axis_push="z",
            axis_aim="y",
            rotate=-60,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=-0.4,
            axis_push="z",
            axis_aim="y",
            rotate=-60,
        )
        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=0.4,
            axis_push="x",
            axis_aim="y",
            rotate=60,
        )

        ##############
        #### R Hip ###
        ##############
        joint_target = "leg_R0_up_1_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=0.15,
            axis_push="z",
            axis_aim="y",
            rotate=60,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=-0.4,
            axis_push="z",
            axis_aim="y",
            rotate=60,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=0.4,
            axis_push="x",
            axis_aim="y",
            rotate=60,
        )

        ###########################
        ###### Ankle L Volume #####
        ###########################
        joint_target = "leg_L0_end_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="y",
            rotate=-30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="y",
            rotate=30,
        )

        ###########################
        ###### Ankle R Volume #####
        ###########################
        joint_target = "leg_R0_end_jnt"
        joint_blend, node_pair_blend = Create.create_blend_joint(joint_target)

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=-1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="y",
            rotate=30,
        )

        Create.create_support_joint(
            joint_blend=joint_blend,
            node_pair_blend=node_pair_blend,
            joint=joint_target,
            offset=1,
            intensity=-0.1,
            axis_push="z",
            axis_aim="y",
            rotate=-30,
        )

        #######################################
        ##### Fingers L Volume ################
        #######################################

        Create.create_volume_joint(
            "thumb_L0_0_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "thumb_L0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "thumb_L0_2_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "index_L0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "index_L0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "index_L0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "middle_L0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "middle_L0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "middle_L0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "ring_L0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "ring_L0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "ring_L0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "pinky_L0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "pinky_L0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "pinky_L0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        #######################################
        ##### Fingers R Volume ################
        #######################################

        Create.create_volume_joint(
            "thumb_R0_0_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "thumb_R0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "thumb_R0_2_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "index_R0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "index_R0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "index_R0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "middle_R0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "middle_R0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "middle_R0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "ring_R0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "ring_R0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "ring_R0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )

        Create.create_volume_joint(
            "pinky_R0_1_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "pinky_R0_2_jnt",
            offset=1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=-30,
        )

        Create.create_volume_joint(
            "pinky_R0_3_jnt",
            offset=-1,
            intensity=-0.02,
            axis_push="y",
            axis_aim="x",
            rotate=30,
        )
