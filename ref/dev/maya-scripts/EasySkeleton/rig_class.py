import maya.cmds as cmds
from EasySkeleton import utils, config


class Rig:
    def __init__(self):
        self.name = ""
        self.parent = ""
        self.mirror_control_scale = False
        self.debug_mode = False

    def custom_variables(self):
        self.list_before_controller = []

    def setup_hierarchy(self):
        cmds.group(em=1, n=self.grp_local_rig, p=config.grp_anim)
        cmds.group(em=1, n=self.grp_local_anim, p=self.grp_local_rig)
        cmds.group(em=1, n=self.grp_local_still, p=self.grp_local_rig)

        cmds.setAttr(self.grp_local_still + ".inheritsTransform", 0)

        cmds.parentConstraint(self.parent, self.grp_local_anim) if self.parent else None

    def variables(self):
        self.grp_local_rig = "grp_{}Rig".format(self.name)
        self.grp_local_anim = "grp_{}Anim".format(self.name)
        self.grp_local_still = "grp_{}Still".format(self.name)

    def core_build(self):
        pass

    def core_unbuild(self):
        pass

    def make_finalize(self):
        utils.finalize_visibility(self.grp_local_rig)

    def make_finalize_extra(self):
        pass

    def backup_local_joints(self):
        list_joint_global = cmds.listRelatives(config.grp_local,ad=1,typ="joint")

        if not list_joint_global:
            return

        for joint in list_joint_global:
            joint_backup = "{}_Backup".format(utils.cut(joint))

            # Delete Old Joint Backup
            if cmds.objExists(joint_backup):
                cmds.delete(joint_backup)

            # Duplicate New Joint Backup
            duplicate = cmds.duplicate(joint,name=joint_backup,po=1)

            # Parent Joint Backup
            cmds.parent(joint_backup,config.grp_local_joint_backup)

    def backup_global_joints(self):
        def duplicate_backup():
            list_joint_global = cmds.listRelatives(config.grp_skin,ad=1,typ="joint")

            if list_joint_global:
                for joint in list_joint_global:
                    duplicate_name = utils.cut(joint)+"_Backup"

                    if cmds.objExists(duplicate_name):
                        cmds.delete(duplicate_name)

                    cmds.duplicate(joint,po=1,name=duplicate_name)
                    cmds.parent(duplicate_name,config.grp_global_joint_backup)

        duplicate_backup()

    def reposition_local_joints(self):
        def reparent(joint_local):
            # ignore re-parent
            if utils.is_descendant_of(joint_local,config.grp_local):
                return

            # reparent case
            else:
                child =  cmds.listRelatives(joint_local,c=1)
                parent = cmds.listRelatives(joint_local,p=1)

                if child:
                    if parent:
                        cmds.parent(child,parent[0])
                    else:
                        cmds.parent(child,w=1)

                cmds.parent(joint_local,config.grp_local)



        list_local_joints = cmds.listRelatives(config.grp_local_joint_backup, ad=1, typ="joint")
        list_local_joints.reverse()

        if not list_local_joints:
            return

        for joint_backup in list_local_joints:
            joint_local = joint_backup.replace("_Backup","")

            # skip if joint local not exist
            if not cmds.objExists(joint_local):
                # cmds.delete(joint_backup)
                continue

            # skip if not joint local of rig module
            if not utils.is_descendant_of(joint_local,self.grp_local_rig):
                continue

            # re position
            cmds.matchTransform(joint_local, joint_backup)

            # re parent
            reparent(joint_local)

            # reset visibility
            cmds.setAttr("{}.v".format(joint_local), 1)
            cmds.setAttr("{}.drawStyle".format(joint_local), 3)

    def reposition_global_joints(self):
        list_global_joints = cmds.listRelatives(config.grp_skin, ad=1, typ="joint")
        list_global_joints.reverse()

        if list_global_joints:
            for joint in list_global_joints:
                joint_backup = "{}_Backup".format(joint)

                # reset joint orient
                if cmds.objExists(joint_backup):
                    cmds.matchTransform(joint,joint_backup)

    def verify_global_joints(self):
        list_global_joints = cmds.listRelatives(config.grp_skin,ad=1,typ="joint")

        if list_global_joints:
            for joint in list_global_joints:
                if "|" in joint:
                    cmds.confirmDialog(m="Global joint must have unique name , {}.".format(joint))
                    raise Exception("Global joint must have unique name, {}.".format(joint))

    def verify_local_joints(self):
        list_local_joints = cmds.listRelatives(config.grp_local, ad=1, typ="joint")

        if list_local_joints:
            for joint in list_local_joints:
                # check duplicate name
                if "|" in joint:
                    cmds.confirmDialog(m="Global joint must have unique name, {}.".format(joint))
                    raise Exception("Global joint must have unique name, {}.".format(joint))

                elif cmds.listRelatives(joint,c=1):
                    cmds.confirmDialog(m="Local Joint not support chained hierarchy, {}.".format(joint))
                    raise Exception("Local Joint not support chained hierarchy, {}.".format(joint))

    def save_controller_current(self):
        list_all_transform = cmds.ls(typ="transform")

        for transform in list_all_transform:
            if (transform.startswith(config.ctrl) or transform.endswith(config.ctrl)) and "bck" not in transform:
                self.list_before_controller.append(transform)

    def add_controller_to_set(self):
        list_all_transform = cmds.ls(typ="transform")

        for transform in list_all_transform:
            if transform.endswith(config.ctrl) and transform not in self.list_before_controller:
                utils.add_to_set([transform])

    def build(self):
        self.verify_local_joints()
        self.verify_global_joints()

        self.variables()
        self.custom_variables()
        self.setup_hierarchy()

        self.backup_global_joints()
        self.backup_local_joints()
        self.save_controller_current()

        self.core_build()
        self.make_finalize() if not self.debug_mode else None
        self.make_finalize_extra() if not self.debug_mode else None
        self.add_controller_to_set()

    def unbuild(self):
        def delete_node():
            # remove rig group
            if cmds.objExists(self.grp_local_rig):
                cmds.delete(self.grp_local_rig)

            # Remove rig node
            for node in cmds.ls(dag=False):
                if not cmds.objExists(node):
                    continue

                # ignore case
                if cmds.objectType(node) not in  cmds.listNodeTypes("utility") or node == self.name or utils.is_descendant_of(node,config.grp_controller_backup):
                    continue

                # delete case
                if cmds.objExists(node) and self.name in node:
                    cmds.delete(node)

        # remove module
        if not cmds.getAttr("{}.isBuild".format(self.name)):
            return None

        self.variables()
        self.reposition_local_joints()

        self.core_unbuild()

        # self.unparent_joint_local()

        delete_node()

        # set attributes
        cmds.setAttr("{}.isBuild".format(self.name), False)

        self.reposition_global_joints()

    def unparent_joint_local(self):
        # parent local joint back to grp still
        grp_data = "{}_data_grp".format(self.name)

        # if grp data exist
        if not cmds.objExists(grp_data):
            return

        # main
        list_joint_name = cmds.getAttr(grp_data + ".localJoint")

        for i, joint in enumerate(list_joint_name):
            if not cmds.objExists(joint):
                continue

            cmds.setAttr(joint+".v",1)

            joint_backup_name = joint+"_LOCAL_BACKUP"

            if not cmds.objExists(joint):
                raise Exception("{} not have backup joint, cannot find {}".format(joint,joint_backup_name))

            # break connection
            utils.break_connection(joint, rot=True, pos=True, scl=True)

            # parent back
            cmds.parent(joint,w=1)

            # reset transform
            joint_parent = cmds.listRelatives(joint,p=1,f=1)

            if joint_parent:
                utils.reset_all_transform(joint_parent[0])

            # parent to joint backup
            utils.match_parent(joint,joint_backup_name)

            # parent back
            parent_back = cmds.listRelatives(joint_backup_name,p=1,f=1)[0]
            cmds.parent(joint,parent_back)

            # delete backup joint
            cmds.delete(joint_backup_name)

        # delete child trash
        for joint in list_joint_name:
            if not cmds.objExists(joint):
                continue

            # set visibility

            # check child
            child_joint =cmds.listRelatives(joint,c=1,typ="transform")

            # if child_joint:
            if child_joint:
                cmds.delete(child_joint)

    def add_to_set(self,list_add):
        utils.add_to_set(list_add=list_add,set_name="AllController")
